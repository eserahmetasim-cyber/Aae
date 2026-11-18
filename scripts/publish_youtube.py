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
  python3 scripts/publish_youtube.py ... --yayinla-saat 09:00   # bir sonraki 09:00'da ac

ZAMANLI YAYIN (--yayinla-saat)
GitHub cron bir SAAT GARANTISI vermez: 17 Kas'ta 06:00 UTC slotu 15:21'de
calisti, 9 saat 21 dakika gecikmeyle. Bu yuzden "her sabah 09:00" sozu
cron'un calisma anina baglanamaz. Cozum: video PRIVATE yuklenir ve
status.publishAt ile bir sonraki 09:00'a programlanir; CI ne zaman
calisirsa calissin video tam 09:00'da kendiliginden acilir.
YouTube API'si publishAt'i yalnizca privacyStatus=private ile kabul eder.

KURALLAR.md: varsayilan gizlilik 'private'. Herkese acmak ayri, bilincli bir adim.
-------------------------------------------------------------------
"""
import argparse
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lesson import DersHatasi, dersleri_bul, yukle  # noqa: E402

# Turkiye yil boyu UTC+3, yaz saati uygulamiyor (2016'dan beri). Sabit ofset
# kullaniliyor; zoneinfo/tzdata runner'da bulunmayabilir.
ISTANBUL = dt.timezone(dt.timedelta(hours=3))
ASGARI_PAY_DK = 10            # publishAt bu kadar yakinsa ertesi gune kayar

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


def sonraki_saat(hhmm: str, simdi: dt.datetime | None = None) -> dt.datetime:
    """'HH:MM' (Istanbul) -> bir SONRAKI o an, UTC olarak.

    Pay kurali: hedef ASGARI_PAY_DK'dan yakinsa ertesi gune kayar. Yukleme
    bitmeden publishAt gecerse YouTube istegi reddeder; 06:00'a bir dakika
    kala baslayan bir cron calismasi tam o tuzaga duser."""
    try:
        saat, dakika = (int(x) for x in hhmm.split(":"))
        if not (0 <= saat < 24 and 0 <= dakika < 60):
            raise ValueError
    except ValueError:
        die(f"gecersiz saat: {hhmm} (beklenen HH:MM)")
    simdi = simdi or dt.datetime.now(dt.timezone.utc)
    yerel = simdi.astimezone(ISTANBUL)
    hedef = yerel.replace(hour=saat, minute=dakika, second=0, microsecond=0)
    if hedef - yerel < dt.timedelta(minutes=ASGARI_PAY_DK):
        hedef += dt.timedelta(days=1)
    return hedef.astimezone(dt.timezone.utc)


def main() -> None:
    ap = argparse.ArgumentParser(description="AAE egitim videosunu YouTube'a yukle")
    ap.add_argument("video", nargs="?", help="mp4 yolu (bos = ders dosyasindaki cikti)")
    ap.add_argument("--ders", help="content/dersler/*.yml (bos = ilk ders)")
    ap.add_argument("--gizlilik", choices=("private", "unlisted", "public"),
                    help="ders dosyasindaki gizliligi gecersiz kilar")
    ap.add_argument("--yayinla-saat", default="", metavar="HH:MM",
                    help="bir sonraki bu saatte (Istanbul) acilacak sekilde "
                         "zamanla; video private yuklenir")
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
    zamanli = args.yayinla_saat or os.getenv("YT_YAYINLA_SAAT") or ""
    gizlilik = args.gizlilik or os.getenv("YT_GIZLILIK") or ders["youtube"]["gizlilik"]
    if gizlilik not in ("private", "unlisted", "public"):
        die(f"gecersiz gizlilik: {gizlilik}")
    yayin_an = None
    if zamanli:
        # YouTube publishAt'i yalnizca private ile kabul ediyor. Istenen
        # gizlilik public/unlisted olsa bile zamanli yayinda private'a
        # cekiliyor; video zaten hedef saatte kendiliginden aciliyor.
        yayin_an = sonraki_saat(zamanli)
        if gizlilik != "private":
            print(f">> Not      : zamanli yayin icin gizlilik "
                  f"'{gizlilik}' -> 'private' (publishAt sarti)")
        gizlilik = "private"

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
    if yayin_an:
        govde["status"]["publishAt"] = yayin_an.isoformat().replace("+00:00", "Z")

    print(f">> Ders     : {ders['no']:02d} · {ders['baslik']}")
    print(f">> Video    : {video}")
    print(f">> Baslik   : {baslik}")
    print(f">> Gizlilik : {gizlilik}")
    if yayin_an:
        yerel = yayin_an.astimezone(ISTANBUL)
        print(f">> Yayin    : {yerel:%d.%m.%Y %H:%M} Istanbul "
              f"({yayin_an:%Y-%m-%dT%H:%M:%SZ})")
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
    if yayin_an:
        yerel = yayin_an.astimezone(ISTANBUL)
        print(f"         (gizli yuklendi — {yerel:%d.%m %H:%M}'da kendiliginden acilacak.)")
    elif gizlilik == "private":
        print("         (gizli yuklendi — once izle, sonra herkese ac.)")


if __name__ == "__main__":
    main()
