#!/usr/bin/env python3
"""
publish_youtube.py
-------------------------------------------------------------------
Render edilmis egitim videosunu YouTube'a (Short) yukler.
Metinler ders dosyasindan okunur — YouTube ile Instagram ayni kaynaktan beslenir.

Kimlik bilgileri ORTAM DEGISKENLERINDEN gelir (kodda sir yok):
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
    -> scripts/get_youtube_token.py ile bir kez alinir, GitHub Secrets'a girilir.

Kullanim:
  python3 scripts/publish_youtube.py output/....mp4 --ders content/dersler/01-acil-fren.yml
  python3 scripts/publish_youtube.py --ders content/dersler/01-acil-fren.yml   # cikti yolunu dersten al
  python3 scripts/publish_youtube.py ... --gizlilik unlisted
  python3 scripts/publish_youtube.py ... --kuru                 # istek gondermeden goster

KURALLAR.md: varsayilan gizlilik 'private'. Herkese acmak ayri, bilincli bir adim.
-------------------------------------------------------------------
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lesson import DersHatasi, dersleri_bul, yukle  # noqa: E402

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_URI = "https://oauth2.googleapis.com/token"
BASLIK_SINIR = 100


def die(msg: str) -> None:
    print(f"HATA: {msg}", file=sys.stderr)
    sys.exit(1)


def shorts_isaretle(baslik: str, aciklama: str) -> tuple:
    """Dikey <=60 sn videolar Short olarak islenir; etiketi de ekleyelim."""
    if "#shorts" not in baslik.lower():
        kisa = baslik[: BASLIK_SINIR - len(" #Shorts")]
        baslik = f"{kisa} #Shorts"
    if "#shorts" not in aciklama.lower():
        aciklama = f"{aciklama}\n\n#Shorts".strip()
    return baslik[:BASLIK_SINIR], aciklama


def servis_kur():
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        die("Paketler yok. Kurun: pip install -r requirements-publish.txt")

    kimlik = {ad: os.getenv(ad) for ad in
              ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")}
    eksik = [ad for ad, deger in kimlik.items() if not deger]
    if eksik:
        die("Su secret'lar eksik: " + ", ".join(eksik) +
            "\n      README'deki 'YouTube kurulumu' bolumune bakin.")

    creds = Credentials(
        token=None,
        refresh_token=kimlik["YT_REFRESH_TOKEN"],
        client_id=kimlik["YT_CLIENT_ID"],
        client_secret=kimlik["YT_CLIENT_SECRET"],
        token_uri=TOKEN_URI,
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def main() -> None:
    ap = argparse.ArgumentParser(description="AAE egitim videosunu YouTube'a yukle")
    ap.add_argument("video", nargs="?", help="mp4 yolu (bos = ders dosyasindaki cikti)")
    ap.add_argument("--ders", help="content/dersler/*.yml (bos = ilk ders)")
    ap.add_argument("--gizlilik", choices=("private", "unlisted", "public"),
                    help="ders dosyasindaki gizliligi gecersiz kilar")
    ap.add_argument("--kuru", action="store_true", help="istek gondermeden ne yapilacagini goster")
    ap.add_argument("--id-dosyasi", default="",
                    help="basarili yuklemede video id'sini bu dosyaya yaz")
    args = ap.parse_args()

    try:
        yol = args.ders or (dersleri_bul() or [None])[0]
        if not yol:
            die("Ders dosyasi yok (content/dersler/*.yml).")
        ders = yukle(yol)
    except DersHatasi as exc:
        die(str(exc))

    video = args.video or ders["cikti"]
    gizlilik = args.gizlilik or os.getenv("YT_GIZLILIK") or ders["youtube"]["gizlilik"]
    if gizlilik not in ("private", "unlisted", "public"):
        die(f"gecersiz gizlilik: {gizlilik}")

    baslik, aciklama = shorts_isaretle(ders["youtube"]["baslik"], ders["youtube"]["aciklama"])
    govde = {
        "snippet": {
            "title": baslik,
            "description": aciklama,
            "tags": ders["youtube"]["etiketler"],
            "categoryId": str(ders["youtube"]["kategori"]),
        },
        "status": {"privacyStatus": gizlilik, "selfDeclaredMadeForKids": False},
    }

    print(f">> Ders     : {ders['no']:02d} · {ders['baslik']}")
    print(f">> Video    : {video}")
    print(f">> Baslik   : {baslik}")
    print(f">> Gizlilik : {gizlilik}")
    print(f">> Etiket   : {', '.join(govde['snippet']['tags']) or '(yok)'}")

    if args.kuru:
        print("\n[kuru calistirma] YouTube'a istek GONDERILMEDI.")
        return

    if not os.path.isfile(video):
        die(f"Video yok: {video}\n      Once render adimi calismali.")

    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    servis = servis_kur()
    medya = MediaFileUpload(video, mimetype="video/*", chunksize=-1, resumable=True)
    istek = servis.videos().insert(part="snippet,status", body=govde, media_body=medya)

    yanit = None
    try:
        while yanit is None:
            durum, yanit = istek.next_chunk()
            if durum:
                print(f"   ... %{int(durum.progress() * 100)}")
    except HttpError as exc:
        die(f"YouTube API hatasi: {exc}")

    vid = yanit.get("id")
    if args.id_dosyasi:            # gunluk yayin is akisi id'yi buradan okur
        with open(args.id_dosyasi, "w", encoding="utf-8") as f:
            f.write(vid or "")
    print(f"\nTAMAM ✓  https://youtu.be/{vid}")
    print(f"         Studio: https://studio.youtube.com/video/{vid}/edit")
    if gizlilik == "private":
        print("         (gizli yuklendi — once izle, sonra herkese ac.)")


if __name__ == "__main__":
    main()
