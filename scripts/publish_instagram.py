#!/usr/bin/env python3
"""
publish_instagram.py
-------------------------------------------------------------------
Render edilmis egitim videosunu Instagram'a Reel olarak yukler.
Metinler ders dosyasindan okunur (YouTube ile ayni kaynak).

DIKKAT: Instagram'da yayinlanan Reel ANINDA HERKESE ACIKTIR ve geri alinamaz.
KURALLAR.md geregi bu betik kendiliginden calismaz; bilincli olarak cagrilir.

Kimlik bilgileri ORTAM DEGISKENLERINDEN gelir (kodda sir yok):
  IG_USER_ID       Instagram Business/Creator hesap id'si
  IG_ACCESS_TOKEN  Uzun omurlu Page/IG erisim jetonu
  IG_API_SURUM     (ops.) varsayilan v23.0
    -> scripts/get_instagram_ids.py ile bir kez alinir, GitHub Secrets'a girilir.

Iki yukleme yolu:
  1) resumable (varsayilan) — yerel dosya dogrudan rupload.facebook.com'a gider,
     videoyu internette bir yerde yayinlamaya gerek yok.
  2) --video-url  — Meta videoyu verdiginiz PUBLIC adresten kendisi indirir.
     Resumable'in calismadigi uygulamalarda bu yolu kullanin (README).

Kullanim:
  python3 scripts/publish_instagram.py output/....mp4 --ders content/dersler/01-acil-fren.yml
  python3 scripts/publish_instagram.py --ders ... --video-url https://.../video.mp4
  python3 scripts/publish_instagram.py --ders ... --kuru          # istek gondermez
  python3 scripts/publish_instagram.py --ders ... --sadece-hazirla  # yayinlamadan birakir
-------------------------------------------------------------------
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lesson import DersHatasi, dersleri_bul, yukle  # noqa: E402

GRAPH = "https://graph.facebook.com"
RUPLOAD = "https://rupload.facebook.com/ig-api-upload"
VARSAYILAN_SURUM = "v23.0"
BOYUT_SINIR_MB = 300          # Reels ust siniri
BEKLEME_ARALIK = 5            # saniye
BEKLEME_AZAMI = 15 * 60       # 15 dakika


def die(msg: str) -> None:
    print(f"HATA: {msg}", file=sys.stderr)
    sys.exit(1)


def _cagir(url: str, veri=None, basliklar=None, yontem=None):
    """JSON donen Graph API cagrisi; hata govdesini okunur sekilde yuzeye cikarir."""
    govde = urllib.parse.urlencode(veri).encode() if isinstance(veri, dict) else veri
    istek = urllib.request.Request(url, data=govde, headers=basliklar or {}, method=yontem)
    try:
        with urllib.request.urlopen(istek, timeout=300) as yanit:
            ham = yanit.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        ham = exc.read().decode("utf-8", "replace")
        try:
            hata = json.loads(ham).get("error", {})
            die("Instagram API: {} (tur={} kod={})".format(
                hata.get("message", ham), hata.get("type", "?"), hata.get("code", "?")))
        except ValueError:
            die(f"Instagram API {exc.code}: {ham[:500]}")
    except urllib.error.URLError as exc:
        die(f"Baglanti hatasi: {exc.reason}")
    try:
        return json.loads(ham)
    except ValueError:
        die(f"Beklenmeyen yanit: {ham[:500]}")


def kap_olustur(surum, kullanici, jeton, caption, feed_de_paylas, video_url, kapak_url):
    alanlar = {
        "media_type": "REELS",
        "caption": caption,
        "share_to_feed": "true" if feed_de_paylas else "false",
        "access_token": jeton,
    }
    if video_url:
        alanlar["video_url"] = video_url
    else:
        alanlar["upload_type"] = "resumable"
    if kapak_url:
        alanlar["cover_url"] = kapak_url
    return _cagir(f"{GRAPH}/{surum}/{kullanici}/media", alanlar)


def dosyayi_yukle(surum, kap_id, jeton, video):
    """Yerel dosyayi rupload'a tek parcada gonderir (offset=0)."""
    boyut = os.path.getsize(video)
    url = f"{RUPLOAD}/{surum}/{kap_id}"
    print(f">> Yukleniyor: {boyut / 1e6:.1f} MB -> {url}")
    with open(video, "rb") as fh:
        _cagir(url, fh, {
            "Authorization": f"OAuth {jeton}",
            "offset": "0",
            "file_size": str(boyut),
            "Content-Type": "application/octet-stream",
            "Content-Length": str(boyut),
        }, yontem="POST")
    print("   yukleme tamam")


def durumu_bekle(surum, kap_id, jeton):
    """status_code: IN_PROGRESS | FINISHED | ERROR | EXPIRED | PUBLISHED"""
    basladi = time.time()
    while True:
        sorgu = urllib.parse.urlencode({"fields": "status_code,status", "access_token": jeton})
        yanit = _cagir(f"{GRAPH}/{surum}/{kap_id}?{sorgu}")
        durum = yanit.get("status_code", "?")
        if durum == "FINISHED":
            print("   islendi ✓")
            return
        if durum in ("ERROR", "EXPIRED"):
            die(f"Kap durumu {durum}: {yanit.get('status', '')}")
        gecen = int(time.time() - basladi)
        if gecen > BEKLEME_AZAMI:
            die(f"Zaman asimi: {BEKLEME_AZAMI // 60} dk sonra hala {durum}.")
        print(f"   durum={durum} ({gecen}s)")
        time.sleep(BEKLEME_ARALIK)


def main() -> None:
    ap = argparse.ArgumentParser(description="AAE egitim videosunu Instagram'a Reel olarak yukle")
    ap.add_argument("video", nargs="?", help="mp4 yolu (bos = ders dosyasindaki cikti)")
    ap.add_argument("--ders", help="content/dersler/*.yml (bos = ilk ders)")
    ap.add_argument("--video-url", help="PUBLIC video adresi (resumable yerine)")
    ap.add_argument("--kuru", action="store_true", help="istek gondermeden ne yapilacagini goster")
    ap.add_argument("--id-dosyasi", default="",
                    help="basarili yayinda media id'sini bu dosyaya yaz")
    ap.add_argument("--sadece-hazirla", action="store_true",
                    help="kabi hazirla ama YAYINLAMA (creation_id basilir)")
    args = ap.parse_args()

    try:
        yol = args.ders or (dersleri_bul() or [None])[0]
        if not yol:
            die("Ders dosyasi yok (content/dersler/*.yml).")
        ders = yukle(yol)
    except DersHatasi as exc:
        die(str(exc))

    video = args.video or ders["cikti"]
    video_url = args.video_url or os.getenv("IG_VIDEO_URL") or ""
    caption = ders["instagram"]["caption"]
    surum = os.getenv("IG_API_SURUM", VARSAYILAN_SURUM)

    print(f">> Ders     : {ders['no']:02d} · {ders['baslik']}")
    print(f">> Kaynak   : {video_url or video}")
    print(f">> Yol      : {'public video_url' if video_url else 'resumable (yerel dosya)'}")
    print(f">> Feed'de  : {ders['instagram']['feed_de_paylas']}")
    print(">> Caption  :")
    for satir in caption.splitlines():
        print(f"   | {satir}")
    print("\n!! Yayinlanan Reel ANINDA HERKESE ACIK olur ve geri alinamaz.")

    if args.kuru:
        print("\n[kuru calistirma] Instagram'a istek GONDERILMEDI.")
        return

    if not video_url:
        if not os.path.isfile(video):
            die(f"Video yok: {video}\n      Once render adimi calismali.")
        mb = os.path.getsize(video) / 1e6
        if mb > BOYUT_SINIR_MB:
            die(f"Video {mb:.0f} MB — Reels siniri {BOYUT_SINIR_MB} MB.")

    kullanici = os.getenv("IG_USER_ID")
    jeton = os.getenv("IG_ACCESS_TOKEN")
    eksik = [ad for ad, d in (("IG_USER_ID", kullanici), ("IG_ACCESS_TOKEN", jeton)) if not d]
    if eksik:
        die("Su secret'lar eksik: " + ", ".join(eksik) +
            "\n      README'deki 'Instagram kurulumu' bolumune bakin.")

    print("\n>> 1/4 kap olusturuluyor")
    kap = kap_olustur(surum, kullanici, jeton, caption,
                      ders["instagram"]["feed_de_paylas"], video_url,
                      ders["instagram"]["kapak_url"])
    kap_id = kap.get("id") or die(f"Kap id gelmedi: {kap}")
    print(f"   kap id: {kap_id}")

    if not video_url:
        print(">> 2/4 dosya yukleniyor")
        dosyayi_yukle(surum, kap_id, jeton, video)
    else:
        print(">> 2/4 Meta videoyu kendisi indirecek (video_url)")

    print(">> 3/4 islenmesi bekleniyor")
    durumu_bekle(surum, kap_id, jeton)

    if args.sadece_hazirla:
        print(f"\n[sadece hazirla] YAYINLANMADI. creation_id={kap_id}")
        print("   Yayinlamak icin: "
              f"curl -X POST '{GRAPH}/{surum}/{kullanici}/media_publish' "
              f"-d 'creation_id={kap_id}' -d 'access_token=***'")
        return

    print(">> 4/4 yayinlaniyor")
    sonuc = _cagir(f"{GRAPH}/{surum}/{kullanici}/media_publish",
                   {"creation_id": kap_id, "access_token": jeton})
    medya_id = sonuc.get("id") or die(f"media_publish yaniti beklenmedik: {sonuc}")

    sorgu = urllib.parse.urlencode({"fields": "permalink", "access_token": jeton})
    baglanti = _cagir(f"{GRAPH}/{surum}/{medya_id}?{sorgu}").get("permalink", "")
    if args.id_dosyasi:            # gunluk yayin is akisi id'yi buradan okur
        with open(args.id_dosyasi, "w", encoding="utf-8") as f:
            f.write(medya_id or "")
    print(f"\nTAMAM ✓  Reel yayinda: {baglanti or medya_id}")


if __name__ == "__main__":
    main()
