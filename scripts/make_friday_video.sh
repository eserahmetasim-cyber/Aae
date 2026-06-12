#!/usr/bin/env bash
#
# make_friday_video.sh
# -------------------------------------------------------------------
# Bir videoyu Instagram Reels / TikTok icin "Cuma Mubarek" temali
# dikey (1080x1920) bir videoya donusturur.
#
# Kullanim:
#   ./scripts/make_friday_video.sh [GIRDI_VIDEO] [CIKTI_VIDEO]
#
# Ortam degiskenleri (opsiyonel):
#   TOP_TEXT     Ust yazi      (varsayilan: "Cuma Mubarek")
#   BOTTOM_TEXT  Alt yazi      (varsayilan: "Hayirli Cumalar")
#   DURATION     Maks. sure sn (varsayilan: 60 -> Reels siniri)
#   FONT         .ttf font yolu (otomatik bulunur)
#   MUSIC        Fon muzigi dosyasi (opsiyonel, .mp3/.m4a)
#   MUSIC_VOL    Muzik ses seviyesi (varsayilan: 0.6)
# -------------------------------------------------------------------
set -euo pipefail

INPUT="${1:-${INPUT:-}}"
OUTPUT="${2:-${OUTPUT:-output/cuma_video.mp4}}"

TOP_TEXT="${TOP_TEXT:-Cuma Mubarek}"
BOTTOM_TEXT="${BOTTOM_TEXT:-Hayirli Cumalar}"
DURATION="${DURATION:-60}"
MUSIC="${MUSIC:-}"
MUSIC_VOL="${MUSIC_VOL:-0.6}"

# --- ffmpeg var mi? ---------------------------------------------------------
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "HATA: ffmpeg bulunamadi. Lutfen ffmpeg kurun (ornek: 'sudo apt install ffmpeg')." >&2
  exit 1
fi

# --- Girdi videoyu bul ------------------------------------------------------
if [[ -z "${INPUT}" ]]; then
  # videos/ klasorundeki ilk video dosyasini otomatik sec
  INPUT="$(find videos -maxdepth 1 -type f \( -iname '*.mp4' -o -iname '*.mov' -o -iname '*.mkv' -o -iname '*.m4v' -o -iname '*.webm' \) 2>/dev/null | sort | head -n1 || true)"
fi

if [[ -z "${INPUT}" || ! -f "${INPUT}" ]]; then
  echo "HATA: Girdi video bulunamadi." >&2
  echo "      Videonuzu 'videos/' klasorune koyun ya da yolu parametre verin:" >&2
  echo "      ./scripts/make_friday_video.sh videos/benim_videom.mp4" >&2
  exit 1
fi

echo ">> Girdi : ${INPUT}"
echo ">> Cikti : ${OUTPUT}"

mkdir -p "$(dirname "${OUTPUT}")"

# --- Turkce karakter destekli bir font bul ----------------------------------
if [[ -z "${FONT:-}" ]]; then
  for f in \
    /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf \
    /usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf \
    /System/Library/Fonts/Supplemental/Arial\ Bold.ttf \
    /Library/Fonts/Arial\ Bold.ttf \
    /usr/share/fonts/TTF/DejaVuSans-Bold.ttf ; do
    if [[ -f "$f" ]]; then FONT="$f"; break; fi
  done
fi
if [[ -z "${FONT:-}" || ! -f "${FONT}" ]]; then
  echo "UYARI: Uygun bir font bulunamadi, ffmpeg varsayilanini deniyorum." >&2
  FONT=""
fi

# --- Sure hesabi (fade-out icin) -------------------------------------------
SRC_DUR="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${INPUT}" 2>/dev/null | cut -d. -f1 || echo 0)"
[[ -z "${SRC_DUR}" || "${SRC_DUR}" == "N/A" ]] && SRC_DUR=0
if [[ "${SRC_DUR}" -gt "${DURATION}" ]]; then
  END="${DURATION}"
else
  END="${SRC_DUR}"
fi
# Cok kisa videolarda fade-out'u guvene al
FADE_OUT_START=$(( END > 1 ? END - 1 : 0 ))

# --- Yazilari gecici dosyalara yaz (kacis sorunlarini onler) ----------------
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT
printf '%s' "${TOP_TEXT}"    > "${TMP_DIR}/top.txt"
printf '%s' "${BOTTOM_TEXT}" > "${TMP_DIR}/bottom.txt"

FONT_ARG=""
[[ -n "${FONT}" ]] && FONT_ARG="fontfile='${FONT}':"

# --- Video filtre zinciri ---------------------------------------------------
VF="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,"
VF+="drawbox=x=0:y=0:w=iw:h=260:color=black@0.45:t=fill,"
VF+="drawbox=x=0:y=ih-220:w=iw:h=220:color=black@0.45:t=fill,"
VF+="drawtext=${FONT_ARG}textfile='${TMP_DIR}/top.txt':fontcolor=white:fontsize=90:x=(w-text_w)/2:y=95:borderw=4:bordercolor=black@0.7,"
VF+="drawtext=${FONT_ARG}textfile='${TMP_DIR}/bottom.txt':fontcolor=white:fontsize=58:x=(w-text_w)/2:y=h-160:borderw=3:bordercolor=black@0.7,"
VF+="fade=t=in:st=0:d=1,fade=t=out:st=${FADE_OUT_START}:d=1,format=yuv420p"

echo ">> Sure  : ${END}s (kaynak ${SRC_DUR}s, limit ${DURATION}s)"
echo ">> Render basliyor..."

if [[ -n "${MUSIC}" && -f "${MUSIC}" ]]; then
  echo ">> Fon muzigi: ${MUSIC} (vol=${MUSIC_VOL})"
  # Orijinal sesi koru + fon muzigini karistir
  ffmpeg -y -i "${INPUT}" -i "${MUSIC}" \
    -filter_complex "[0:v]${VF}[v];[1:a]volume=${MUSIC_VOL},afade=t=out:st=${FADE_OUT_START}:d=1[m];[0:a][m]amix=inputs=2:duration=shortest:dropout_transition=2[a]" \
    -map "[v]" -map "[a]" -t "${END}" \
    -c:v libx264 -profile:v high -preset medium -crf 20 -pix_fmt yuv420p \
    -c:a aac -b:a 160k -ar 44100 -movflags +faststart "${OUTPUT}"
else
  ffmpeg -y -i "${INPUT}" \
    -vf "${VF}" -t "${END}" \
    -c:v libx264 -profile:v high -preset medium -crf 20 -pix_fmt yuv420p \
    -c:a aac -b:a 160k -ar 44100 -movflags +faststart "${OUTPUT}"
fi

echo ""
echo "TAMAM ✓  Hazir video: ${OUTPUT}"
