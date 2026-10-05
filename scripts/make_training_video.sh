#!/usr/bin/env bash
#
# make_training_video.sh
# -------------------------------------------------------------------
# Bir ders dosyasindan (content/dersler/*.yml) AAE egitim videosu render eder.
# Cikti: 1080x1920 dikey, acilis karti + ust/alt bant + zamanli adimlar +
# kapanis karti. Kurallar: KURALLAR.md
#
# Kullanim:
#   ./scripts/make_training_video.sh                       # ilk dersi render et
#   ./scripts/make_training_video.sh content/dersler/01-acil-fren.yml
#   ./scripts/make_training_video.sh <ders.yml> <cikti.mp4>
#
# Ortam degiskenleri:
#   FONT       .ttf font yolu (otomatik bulunur)
#   INTRO      acilis karti suresi sn (varsayilan 2.6)
#   OUTRO      kapanis karti suresi sn (varsayilan 3)
#   KAYNAK     ders dosyasindaki kaynagi gecersiz kilar
# -------------------------------------------------------------------
set -euo pipefail

TURUNCU="0xFF5A1F"
KREM="0xF5F0E8"
ZEMIN="0x07090E"
INTRO="${INTRO:-2.6}"
OUTRO="${OUTRO:-3}"
# Platformlar sesi ~-14 LUFS'a normalize eder. Miksi bu hedefe getirmezsek
# platform sesi yukseltirken gurultuyu de yukseltir. Oran (motor/muzik)
# kaynak_ses ve muzik_ses ile kurulur; bu sadece toplam seviyeyi oturtur.
HEDEF_LUFS="${HEDEF_LUFS:--14}"
LOUDNORM="loudnorm=I=${HEDEF_LUFS}:TP=-1.5:LRA=11"

command -v ffmpeg >/dev/null 2>&1 || { echo "HATA: ffmpeg yok (sudo apt install ffmpeg)." >&2; exit 1; }
command -v jq     >/dev/null 2>&1 || { echo "HATA: jq yok (sudo apt install jq)." >&2; exit 1; }

DERS="${1:-}"
if [[ -z "${DERS}" ]]; then
  DERS="$(python3 scripts/lesson.py --ilk)"
fi
[[ -f "${DERS}" ]] || { echo "HATA: ders dosyasi yok: ${DERS}" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

# Ders dosyasi dogrulanir, drawtext metinleri yazilir, punto plani alinir.
python3 scripts/lesson.py "${DERS}" --metinler "${TMP}/m" > "${TMP}/plan.json"
j() { jq -r "$1" "${TMP}/plan.json"; }

KAYNAK="${KAYNAK:-$(j '.ders.kaynak')}"
CIKTI="${2:-$(j '.ders.cikti')}"
SURE="$(j '.ders.sure')"
MUZIK="$(j '.ders.muzik')"
MUZIK_SES="$(j '.ders.muzik_ses')"
BASLANGIC="$(j '.ders.baslangic')"
KAYNAK_SES="$(j '.ders.kaynak_ses')"
M="${TMP}/m"

SAHNE="$(j '.ders.sahne')"
if [[ -z "${KAYNAK}" && -n "${SAHNE}" ]]; then
  # Ham cekim verilmediyse ders dosyasindaki sahne cizimle uretilir.
  # Gercek cekim koymak icin ders dosyasina 'kaynak:' yazmak yeterli.
  KAYNAK="${TMP}/sahne_${SAHNE}.mp4"
  echo ">> Sahne uretiliyor: ${SAHNE}"
  python3 scripts/sahne_uret.py --sahne "${SAHNE}" \
          --sure "$(python3 -c "print(${SURE} + ${BASLANGIC} + 2)")" \
          --fazlar "$(j '.ders.sahne_fazlari')" \
          --cikti "${KAYNAK}" >/dev/null
fi
if [[ -z "${KAYNAK}" || ! -f "${KAYNAK}" ]]; then
  echo "HATA: kaynak video bulunamadi: '${KAYNAK}'" >&2
  echo "      Ham cekimi videos/ icine koyun, ders dosyasinda 'kaynak:' verin" >&2
  echo "      ya da 'sahne: fren|viraj' yazip cizimle uretilmesini saglayin." >&2
  exit 1
fi

# --- Turkce karakterli bir font bul ---------------------------------------
if [[ -z "${FONT:-}" ]]; then
  for f in \
    /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf \
    /usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf \
    /System/Library/Fonts/Supplemental/Arial\ Bold.ttf \
    /usr/share/fonts/TTF/DejaVuSans-Bold.ttf ; do
    [[ -f "$f" ]] && { FONT="$f"; break; }
  done
fi
[[ -n "${FONT:-}" && -f "${FONT}" ]] || { echo "HATA: Turkce destekli font bulunamadi (fonts-dejavu-core kurun)." >&2; exit 1; }

# --- Sure: kaynak ile ders siniri hangisi kucukse ---------------------------
KAYNAK_SURE="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${KAYNAK}" | cut -d. -f1)"
[[ -z "${KAYNAK_SURE}" || "${KAYNAK_SURE}" == "N/A" ]] && KAYNAK_SURE=0
# 'baslangic' verildiyse klibin o anindan itibaren kullanilir (uzun surus
# cekiminden konuya uyan parcayi secmek icin).
KALAN="$(python3 -c "print(max(0, int(${KAYNAK_SURE} - ${BASLANGIC})))")"
if (( KALAN == 0 )); then
  echo "HATA: 'baslangic' (${BASLANGIC}s) kaynagin suresinden (${KAYNAK_SURE}s) buyuk." >&2
  exit 1
fi
KAYNAK_SURE="${KALAN}"
SS_ARG=()
if python3 -c "import sys; sys.exit(0 if ${BASLANGIC} > 0 else 1)"; then
  SS_ARG=(-ss "${BASLANGIC}")
  echo ">> Baslangic: ${BASLANGIC}s"
fi
if (( KAYNAK_SURE > 0 && KAYNAK_SURE < SURE )); then SON="${KAYNAK_SURE}"; else SON="${SURE}"; fi
(( SON < 2 )) && { echo "HATA: kaynak video cok kisa (${KAYNAK_SURE}s)." >&2; exit 1; }
FADE_OUT=$(( SON - 1 ))
if [[ "$(j '.plan.kapanis_var')" == "true" ]]; then
  OUTRO_BAS="$(python3 -c "print(max(0, ${SON} - ${OUTRO}))")"
else
  OUTRO_BAS="${SON}"
fi
# Govde katmani (bantlar + adimlar) yalnizca acilis ve kapanis kartlari
# ARASINDA gorunur; yoksa kartlarin altindan sizip okunakligi bozuyor.
GOVDE="enable='between(t,${INTRO},${OUTRO_BAS})'"

# --- Yerlesim ---------------------------------------------------------------
P_SERI="$(j '.plan.punto_seri')"
P_UST="$(j '.plan.punto_ustbant')"
P_HANDLE="$(j '.plan.punto_handle')"
UST_SATIR="$(j '.plan.ustbant_satir')"
UST_H="$(python3 -c "print(int(104 + ${UST_SATIR} * ${P_UST} * 1.28 + 20))")"
ALT_H=140

dt() { # dt <dosya> <renk> <punto> <x> <y> [ek]
  printf "drawtext=fontfile='%s':textfile='%s/%s':fontcolor=%s:fontsize=%s:x=%s:y=%s:line_spacing=12:expansion=none%s" \
    "${FONT}" "${M}" "$1" "$2" "$3" "$4" "$5" "${6:-}"
}

VF="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1"

# ust bant
VF+=",drawbox=x=0:y=0:w=iw:h=${UST_H}:color=${ZEMIN}@0.62:t=fill:${GOVDE}"
VF+=",$(dt seri.txt    "${TURUNCU}" "${P_SERI}" 56 46  ":${GOVDE}")"
VF+=",$(dt ustbant.txt "${KREM}"    "${P_UST}"  56 104 ":${GOVDE}")"

# alt bant
VF+=",drawbox=x=0:y=ih-${ALT_H}:w=iw:h=${ALT_H}:color=${ZEMIN}@0.62:t=fill:${GOVDE}"
VF+=",$(dt handle.txt "${KREM}" "${P_HANDLE}" '(w-text_w)/2' "h-96" ":${GOVDE}")"

# zamanli adimlar
while read -r satir; do
  [[ -z "${satir}" ]] && continue
  A_DOSYA="$(jq -r '.dosya' <<<"${satir}")"
  A_T="$(jq -r '.t'      <<<"${satir}")"
  A_BIT="$(jq -r '.bitis' <<<"${satir}")"
  A_PUNTO="$(jq -r '.punto' <<<"${satir}")"
  A_SATIR="$(jq -r '.satir' <<<"${satir}")"
  A_Y="$(python3 -c "print(int(1920 - ${ALT_H} - 60 - ${A_SATIR} * ${A_PUNTO} * 1.3))")"
  # Adim penceresi acilis/kapanis kartlarinin disina tasmasin
  A_T="$(python3 -c "print(round(max(${A_T}, ${INTRO}), 2))")"
  A_BIT="$(python3 -c "print(round(min(${A_BIT}, ${OUTRO_BAS}), 2))")"
  if ! python3 -c "import sys; sys.exit(0 if ${A_BIT} - ${A_T} >= 0.5 else 1)"; then
    echo "   (atlandi: '${A_DOSYA}' penceresi kart disinda kalmiyor)" >&2
    continue
  fi
  VF+=",$(dt "${A_DOSYA}" "${KREM}" "${A_PUNTO}" 56 "${A_Y}" \
        ":box=1:boxcolor=${ZEMIN}@0.80:boxborderw=22:enable='between(t,${A_T},${A_BIT})'")"
done < <(jq -c '.plan.adimlar[]' "${TMP}/plan.json")

# acilis karti
VF+=",drawbox=x=0:y=0:w=iw:h=ih:color=${ZEMIN}@0.88:t=fill:enable='lt(t,${INTRO})'"
VF+=",$(dt seri.txt         "${TURUNCU}" "${P_SERI}"                    '(w-text_w)/2' 560 ":enable='lt(t,${INTRO})'")"
VF+=",$(dt intro_ders.txt   "${TURUNCU}" "$(j '.plan.punto_intro_ders')"   '(w-text_w)/2' 650 ":enable='lt(t,${INTRO})'")"
VF+=",$(dt intro_baslik.txt "${KREM}"    "$(j '.plan.punto_intro_baslik')" '(w-text_w)/2' 790 ":enable='lt(t,${INTRO})'")"
if [[ "$(j '.plan.intro_alt_var')" == "true" ]]; then
  INTRO_ALT_Y="$(python3 -c "print(int(790 + $(j '.plan.intro_baslik_satir') * $(j '.plan.punto_intro_baslik') * 1.3 + 50))")"
  VF+=",$(dt intro_alt.txt "${TURUNCU}" "$(j '.plan.punto_intro_alt')" '(w-text_w)/2' "${INTRO_ALT_Y}" ":enable='lt(t,${INTRO})'")"
fi

# kapanis karti
if [[ "$(j '.plan.kapanis_var')" == "true" ]]; then
  VF+=",drawbox=x=0:y=0:w=iw:h=ih:color=${ZEMIN}@0.82:t=fill:enable='gt(t,${OUTRO_BAS})'"
  VF+=",$(dt kapanis.txt "${KREM}"    "$(j '.plan.punto_kapanis')" '(w-text_w)/2' '(h-text_h)/2-60' ":enable='gt(t,${OUTRO_BAS})'")"
  VF+=",$(dt handle.txt  "${TURUNCU}" "$(j '.plan.punto_handle')"  '(w-text_w)/2' '(h-text_h)/2+180' ":enable='gt(t,${OUTRO_BAS})'")"
fi

VF+=",fade=t=in:st=0:d=0.8,fade=t=out:st=${FADE_OUT}:d=1,format=yuv420p"

# --- Ses: kaynakta ses var mi, muzik var mi --------------------------------
SES_VAR=0
if ffprobe -v error -select_streams a:0 -show_entries stream=codec_type -of csv=p=0 "${KAYNAK}" 2>/dev/null | grep -q audio; then
  SES_VAR=1
fi
MUZIK_VAR=0
[[ -n "${MUZIK}" && -f "${MUZIK}" ]] && MUZIK_VAR=1

mkdir -p "$(dirname "${CIKTI}")"
echo ">> Ders   : $(j '.ders.no') · $(j '.ders.baslik')"
echo ">> Kaynak : ${KAYNAK} (${KAYNAK_SURE}s)"
echo ">> Cikti  : ${CIKTI}"
echo ">> Sure   : ${SON}s · $(jq -r '.plan.adimlar | length' "${TMP}/plan.json") adim"
echo ">> Ses    : motor=${KAYNAK_SES} (var=${SES_VAR}) · muzik=${MUZIK_SES} (var=${MUZIK_VAR})"

VIDEO_KODEK=(-c:v libx264 -profile:v high -preset medium -crf 20 -pix_fmt yuv420p
             -c:a aac -b:a 160k -ar 44100 -ac 2 -movflags +faststart)

if (( SES_VAR && MUZIK_VAR )); then
  ffmpeg -y -v warning -stats "${SS_ARG[@]}" -i "${KAYNAK}" -stream_loop -1 -i "${MUZIK}" \
    -filter_complex "[0:v]${VF}[v];[0:a]volume=${KAYNAK_SES}[k];[1:a]volume=${MUZIK_SES},afade=t=out:st=${FADE_OUT}:d=1[m];[k][m]amix=inputs=2:duration=first:dropout_transition=2:normalize=0,${LOUDNORM}[a]" \
    -map "[v]" -map "[a]" -t "${SON}" "${VIDEO_KODEK[@]}" "${CIKTI}"
elif (( MUZIK_VAR )); then
  ffmpeg -y -v warning -stats "${SS_ARG[@]}" -i "${KAYNAK}" -stream_loop -1 -i "${MUZIK}" \
    -filter_complex "[0:v]${VF}[v];[1:a]volume=${MUZIK_SES},afade=t=out:st=${FADE_OUT}:d=1,${LOUDNORM}[a]" \
    -map "[v]" -map "[a]" -t "${SON}" "${VIDEO_KODEK[@]}" "${CIKTI}"
elif (( SES_VAR )); then
  ffmpeg -y -v warning -stats "${SS_ARG[@]}" -i "${KAYNAK}" \
    -filter_complex "[0:v]${VF}[v];[0:a]volume=${KAYNAK_SES},afade=t=out:st=${FADE_OUT}:d=1,${LOUDNORM}[a]" \
    -map "[v]" -map "[a]" -t "${SON}" "${VIDEO_KODEK[@]}" "${CIKTI}"
else
  # Sessiz kaynak: platformlar ses kanali bekler, sessiz pist ekle
  echo "   (kaynakta ses yok — sessiz ses kanali eklendi)"
  ffmpeg -y -v warning -stats "${SS_ARG[@]}" -i "${KAYNAK}" -f lavfi -i anullsrc=r=44100:cl=stereo \
    -filter_complex "[0:v]${VF}[v]" \
    -map "[v]" -map 1:a -t "${SON}" "${VIDEO_KODEK[@]}" "${CIKTI}"
fi

echo ""
echo "TAMAM ✓  ${CIKTI}"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate \
        -show_entries format=duration,size -of default=nw=1 "${CIKTI}"
