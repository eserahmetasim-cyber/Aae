#!/usr/bin/env python3
"""Konu cakismasi kontrolu.

Iki icerik fabrikasi ayni kanala uretiyor: bu depo ve D:\\IcerikFabrikasi.
Otekinin kutuphanesi buradan gorunmedigi icin yayinladigi basliklar
content/dis_yayinlar.yml icinde elle tutuluyor. Bu betik dersleri hem
birbirine hem o listeye karsi tarar.

Eslesme anahtar kelime uzerinden, yani KESIN DEGIL: ipucu verir, karari
insan verir. Yanlis pozitif de yanlis negatif de mumkun.

Kullanim:
  python3 scripts/cakisma.py                     # tum dersleri tara
  python3 scripts/cakisma.py --metin "yokusta kalkis debriyaj"
"""

from __future__ import annotations

import argparse
import os
import sys
import unicodedata

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lesson  # noqa: E402

DIS_YOL = "content/dis_yayinlar.yml"


def _sade(metin: str) -> str:
    """Kucuk harfe indirir ve Turkce aksanlari duzler: 'BASINÇ' ile
    'basinc' eslesebilsin."""
    metin = metin.replace("ı", "i").replace("İ", "i").lower()
    ayri = unicodedata.normalize("NFKD", metin)
    return "".join(k for k in ayri if not unicodedata.combining(k))


def dis_yayinlar(yol: str = DIS_YOL) -> dict:
    if not os.path.exists(yol):
        return {"yayinlar": [], "eksik_olabilir": True}
    with open(yol, encoding="utf-8") as f:
        return yaml.safe_load(f) or {"yayinlar": []}


def _ders_metni(d: dict) -> str:
    parcalar = [d["baslik"], d.get("alt_baslik", "")]
    parcalar += [a["metin"] for a in d.get("adimlar", [])]
    yt = d.get("youtube") or {}
    parcalar.append(yt.get("baslik", ""))
    return _sade(" ".join(p for p in parcalar if p))


def _gecer(anahtar: str, metin: str, kelimeler: set) -> bool:
    """Tek kelimelik anahtar TAM KELIME eslesmeli. Alt dizi aramasi 'el'
    anahtarini 'elde', 'gelir', 'serit' icinde bulup her dersi isaretliyordu.
    Cok kelimeli anahtarlarda alt dizi aramasi yeterli."""
    a = _sade(anahtar)
    return (a in metin) if " " in a else (a in kelimeler)


def tara(metin_sade: str, veri: dict) -> list:
    kelimeler = {k.strip(".,:;!?·—-()") for k in metin_sade.split()}
    bulunan = []
    for y in veri.get("yayinlar", []):
        eslesen = [a for a in y.get("anahtarlar", [])
                   if _gecer(a, metin_sade, kelimeler)]
        if eslesen:
            bulunan.append((y, eslesen))
    return bulunan


def main() -> None:
    ap = argparse.ArgumentParser(description="Konu cakismasi kontrolu")
    ap.add_argument("--metin", default="", help="ders yerine serbest metin tara")
    args = ap.parse_args()

    veri = dis_yayinlar()
    if veri.get("eksik_olabilir"):
        print("UYARI: dis yayin listesi eksik olabilir "
              f"(kaynak: {veri.get('kaynak', 'bilinmiyor')}).\n")

    if args.metin:
        for y, es in tara(_sade(args.metin), veri):
            print(f"  ! '{y['baslik']}' ({y['tarih']}, {y['durum']}) "
                  f"— ortak: {', '.join(es)}")
        else:
            if not tara(_sade(args.metin), veri):
                print("  temiz: dis yayinlarla ortak anahtar yok.")
        return

    dersler = []
    for yol in sorted(lesson.dersleri_bul()):
        try:
            dersler.append(lesson.yukle(yol))
        except Exception:
            continue

    sorun = 0
    print("DIS YAYINLARLA KARSILASTIRMA")
    for d in dersler:
        bulunan = tara(_ders_metni(d), veri)
        if bulunan:
            sorun += 1
            print(f"\n  Ders {d['no']:02d} · {d['baslik']}")
            for y, es in bulunan:
                print(f"    ! '{y['baslik']}' ({y['tarih']}, {y['durum']}) "
                      f"— ortak: {', '.join(es)}")
    if not sorun:
        print("  temiz.")

    print("\nDERSLER ARASI TEKRAR")
    ikili = 0
    for i, a in enumerate(dersler):
        for b in dersler[i + 1:]:
            ortak = set(_sade(a["baslik"]).split()) & set(_sade(b["baslik"]).split())
            ortak = {k for k in ortak if len(k) > 4}
            if ortak:
                ikili += 1
                print(f"  ? {a['no']:02d} ve {b['no']:02d} — ortak: "
                      f"{', '.join(sorted(ortak))}")
    if not ikili:
        print("  temiz.")


if __name__ == "__main__":
    main()
