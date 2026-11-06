#!/usr/bin/env python3
"""Render edilmis bir dersi ONAYLI KUTUPHANE'ye alir.

Kutuphane iki oturum arasindaki devir noktasidir: bu oturum ders uretir ve
buraya koyar, sosyal medya oturumu buradan okuyup paylasir. Devir deponun
icinden yapilir cunku iki oturum ayri makinelerde calisiyor; birinin yerel
diski (ornegin D:\\IcerikFabrikasi) digerinden gorunmuyor.

Yapi:
  library/approved/<ders-adi>/<ders-adi>.mp4
  library/approved/<ders-adi>/meta.json      tek dersin tum bilgisi
  library/approved/index.json                onayli derslerin listesi

Kullanim:
  python3 scripts/onayla.py content/dersler/01-acil-fren.yml
  python3 scripts/onayla.py --hepsi
  python3 scripts/onayla.py --liste
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lesson  # noqa: E402

KUTUPHANE = "library/approved"
DIZIN = "index.json"


def _ad(ders: dict) -> str:
    """Klasor adi: ders dosyasinin adiyla ayni (01-acil-fren)."""
    return os.path.splitext(os.path.basename(ders["dosya"]))[0]


def _son_video(ders: dict) -> str | None:
    """Bu derse ait en yeni render. cikti alani tarihi bugunden urettigi icin
    dunku render'i da bulabilmek gerekiyor."""
    kalip = f"output/*_ders{ders['no']:02d}_{ders['slug']}_v*.mp4"
    adaylar = sorted(glob.glob(kalip), key=os.path.getmtime)
    return adaylar[-1] if adaylar else None


def _video_bilgisi(yol: str) -> dict:
    """ffprobe ile sure ve boyut; ffprobe yoksa bos doner."""
    try:
        c = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,duration",
             "-of", "json", yol],
            capture_output=True, text=True, check=True)
        a = json.loads(c.stdout)["streams"][0]
        return {"genislik": a.get("width"), "yukseklik": a.get("height"),
                "sure_sn": round(float(a.get("duration", 0)), 1)}
    except Exception:
        return {}


def onayla(ders_yolu: str, video: str = "") -> dict:
    ders = lesson.yukle(ders_yolu)
    ad = _ad(ders)
    video = video or _son_video(ders) or ""
    if not video or not os.path.exists(video):
        raise SystemExit(f"HATA: {ad} icin render bulunamadi. Once uret.")

    klasor = os.path.join(KUTUPHANE, ad)
    os.makedirs(klasor, exist_ok=True)
    hedef = os.path.join(klasor, f"{ad}.mp4")
    shutil.copy2(video, hedef)

    meta = {
        "klasor": ad,
        "ders_no": ders["no"],
        "slug": ders["slug"],
        "seri": ders["seri"],
        "baslik": ders["baslik"],
        "alt_baslik": ders["alt_baslik"],
        "handle": ders["handle"],
        "video": f"{ad}.mp4",
        "kaynak_render": video,
        "onay_tarihi": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "durum": "onaylandi",
        "adimlar": ders["adimlar"],
        "youtube": ders["youtube"],
        "instagram": ders["instagram"],
    }
    meta.update(_video_bilgisi(hedef))
    with open(os.path.join(klasor, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return meta


def dizini_yaz() -> list:
    """Tek dosyadan tum kutuphane okunabilsin: sosyal medya oturumu bunu
    yoklayarak yeni onay var mi anlar."""
    kayitlar = []
    for yol in sorted(glob.glob(os.path.join(KUTUPHANE, "*", "meta.json"))):
        with open(yol, encoding="utf-8") as f:
            m = json.load(f)
        kayitlar.append({
            "klasor": m["klasor"],
            "ders_no": m["ders_no"],
            "baslik": m["baslik"],
            "video": os.path.join(KUTUPHANE, m["klasor"], m["video"]),
            "meta": os.path.join(KUTUPHANE, m["klasor"], "meta.json"),
            "onay_tarihi": m["onay_tarihi"],
            "durum": m.get("durum", "onaylandi"),
        })
    kayitlar.sort(key=lambda k: k["ders_no"])
    os.makedirs(KUTUPHANE, exist_ok=True)
    with open(os.path.join(KUTUPHANE, DIZIN), "w", encoding="utf-8") as f:
        json.dump({"guncelleme": dt.datetime.now(dt.timezone.utc)
                                   .isoformat(timespec="seconds"),
                   "dersler": kayitlar}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return kayitlar


def main() -> None:
    ap = argparse.ArgumentParser(description="Dersi onayli kutuphaneye al")
    ap.add_argument("ders", nargs="?", help="content/dersler/*.yml")
    ap.add_argument("--video", default="", help="belirli bir mp4 (bos = en yeni render)")
    ap.add_argument("--hepsi", action="store_true", help="render'i olan tum dersler")
    ap.add_argument("--liste", action="store_true", help="kutuphaneyi listele")
    args = ap.parse_args()

    if args.liste:
        for k in dizini_yaz():
            print(f"  {k['ders_no']:>2}  {k['klasor']:<24} {k['onay_tarihi'][:10]}  {k['baslik']}")
        return

    if args.hepsi:
        for yol in lesson.dersleri_bul():
            try:
                ders = lesson.yukle(yol)
            except SystemExit:
                continue
            if _son_video(ders):
                m = onayla(yol)
                print(f"onaylandi: {m['klasor']}")
    elif args.ders:
        m = onayla(args.ders, args.video)
        print(f"onaylandi: {m['klasor']}")
    else:
        ap.print_help()
        return

    dizini_yaz()
    print(f"dizin guncellendi: {os.path.join(KUTUPHANE, DIZIN)}")


if __name__ == "__main__":
    main()
