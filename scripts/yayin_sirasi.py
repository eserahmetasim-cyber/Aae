#!/usr/bin/env python3
"""Yayin sirasi: hangi ders yayinlandi, sirada hangisi var.

Gunluk yayin is akisi bunu kullanir. Kayit content/yayin_kaydi.json icinde
durur ve her yayindan sonra depoya geri yazilir; "en kucuk numarali ders"
mantigi her gun ayni videoyu yayinlardi.

Kullanim:
  python3 scripts/yayin_sirasi.py --sonraki
  python3 scripts/yayin_sirasi.py --durum
  python3 scripts/yayin_sirasi.py --isaretle content/dersler/01-acil-fren.yml \
      --youtube VIDEO_ID --instagram MEDIA_ID
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lesson  # noqa: E402

KAYIT_YOLU = "content/yayin_kaydi.json"


def kaydi_oku(yol: str = KAYIT_YOLU) -> dict:
    if not os.path.exists(yol):
        return {"yayinlananlar": []}
    with open(yol, encoding="utf-8") as f:
        veri = json.load(f)
    veri.setdefault("yayinlananlar", [])
    return veri


def kaydi_yaz(veri: dict, yol: str = KAYIT_YOLU) -> None:
    os.makedirs(os.path.dirname(yol) or ".", exist_ok=True)
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
        f.write("\n")


def dersler(bekletilenler: bool = False) -> list:
    """Gecerli dersler, YAYIN SIRASINDA (yayin_oncelik, sonra ders no).

    bekletilenler=False ise yayin_beklet: true olanlar dislanir. Bir ders
    baska bir kanalda ayni konu yayinlandigi icin bekletilebiliyor."""
    cikti = []
    for yol in lesson.dersleri_bul():
        try:
            d = lesson.yukle(yol)
        except Exception:
            continue
        if d.get("yayin_beklet") and not bekletilenler:
            continue
        cikti.append(d)
    return sorted(cikti, key=lambda d: (d.get("yayin_oncelik", d["no"]), d["no"]))


def _anahtar(yol: str) -> str:
    return os.path.splitext(os.path.basename(yol))[0]


def sonraki(veri: dict) -> dict | None:
    """Henuz yayinlanmamis en kucuk numarali ders."""
    yapildi = {k["ders"] for k in veri["yayinlananlar"]}
    for d in dersler():
        if _anahtar(d["dosya"]) not in yapildi:
            return d
    return None


def isaretle(veri: dict, ders_yolu: str, youtube: str = "",
             instagram: str = "") -> dict:
    kayit = {
        "ders": _anahtar(ders_yolu),
        "tarih": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    if youtube:
        kayit["youtube"] = youtube
    if instagram:
        kayit["instagram"] = instagram
    veri["yayinlananlar"] = [k for k in veri["yayinlananlar"]
                             if k["ders"] != kayit["ders"]]
    veri["yayinlananlar"].append(kayit)
    veri["yayinlananlar"].sort(key=lambda k: k["ders"])
    return veri


def main() -> None:
    ap = argparse.ArgumentParser(description="AAE gunluk yayin sirasi")
    ap.add_argument("--sonraki", action="store_true",
                    help="sirada bekleyen dersin yolunu bas (yoksa cikis kodu 3)")
    ap.add_argument("--durum", action="store_true", help="tum dersleri durumuyla listele")
    ap.add_argument("--isaretle", metavar="DERS", help="dersi yayinlandi olarak isaretle")
    ap.add_argument("--youtube", default="", help="--isaretle ile: YouTube video id")
    ap.add_argument("--instagram", default="", help="--isaretle ile: Instagram media id")
    ap.add_argument("--kayit", default=KAYIT_YOLU)
    args = ap.parse_args()

    veri = kaydi_oku(args.kayit)

    if args.isaretle:
        kaydi_yaz(isaretle(veri, args.isaretle, args.youtube, args.instagram),
                  args.kayit)
        print(f"isaretlendi: {_anahtar(args.isaretle)}")
        return

    if args.durum:
        yapildi = {k["ders"]: k for k in veri["yayinlananlar"]}
        for i, d in enumerate(dersler(), 1):
            a = _anahtar(d["dosya"])
            k = yapildi.get(a)
            durum = f"yayinda  {k['tarih'][:10]}" if k else "bekliyor"
            print(f"  {i:>2}. sira  ders {d['no']:02d}  {a:<24} {durum}")
        kalan = sum(1 for d in dersler() if _anahtar(d["dosya"]) not in yapildi)
        print(f"\n  {kalan} ders sirada.")
        tutulan = [d for d in dersler(True) if d.get("yayin_beklet")]
        if tutulan:
            print("\n  BEKLETILEN:")
            for d in tutulan:
                not_ = d.get("yayin_beklet_notu") or "sebep yazilmamis"
                print(f"    ders {d['no']:02d}  {d['baslik']} — {not_}")
        return

    if args.sonraki:
        d = sonraki(veri)
        if d is None:
            print("Sirada ders yok: hepsi yayinlandi.", file=sys.stderr)
            raise SystemExit(3)
        print(d["dosya"])
        return

    ap.print_help()


if __name__ == "__main__":
    main()
