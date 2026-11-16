#!/usr/bin/env python3
"""
sistem_kontrol.py
-------------------------------------------------------------------
AAE oturum sisteminin tek denetim noktasi.

Alti oturum ayni kanala calisiyor ve birbirlerini goremiyorlar. Bu betik
depodaki kayitlara bakip "kim ne yapmis, nerede cakisma var" sorusunu tek
ekranda cevaplar.

  python3 scripts/sistem_kontrol.py            tam rapor
  python3 scripts/sistem_kontrol.py --kisa      yalniz uyarilar
  python3 scripts/sistem_kontrol.py --platform instagram

Cikis kodu: 0 temiz, 1 uyari var, 2 CAKISMA var.
-------------------------------------------------------------------
"""
from __future__ import annotations

import argparse
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cakisma  # noqa: E402
import lesson  # noqa: E402
import yayin_sirasi as ys  # noqa: E402

OTURUM_YOLU = "content/oturumlar.yml"

AG, SARI, KIRMIZI, YESIL, SON = "\033[90m", "\033[33m", "\033[31m", "\033[32m", "\033[0m"


def _renk(metin, kod):
    return f"{kod}{metin}{SON}" if sys.stdout.isatty() else metin


class Rapor:
    def __init__(self):
        self.uyari, self.cakisma = [], []

    def u(self, metin):
        self.uyari.append(metin)

    def c(self, metin):
        self.cakisma.append(metin)

    def kod(self):
        return 2 if self.cakisma else (1 if self.uyari else 0)


def oturumlari_oku(yol=OTURUM_YOLU):
    if not os.path.exists(yol):
        return None
    with open(yol, encoding="utf-8") as f:
        return yaml.safe_load(f)


def baslik(metin):
    print(f"\n{_renk('━━ ' + metin, AG)}")


def platform_tablosu(veri, dersler, r):
    """Hangi ders hangi platformda yayinlanmis — ve iki kuyruk ne kadar ayrismis."""
    baslik("YAYIN DURUMU")
    yt = ys.yapilanlar(veri, "youtube")
    ig = ys.yapilanlar(veri, "instagram")
    print(f"  {'ders':<28} {'YOUTUBE':<13} INSTAGRAM")
    for d in dersler:
        a = ys._anahtar(d["dosya"])
        y = yt[a]["tarih"][:10] if a in yt else "-"
        g = ig[a]["tarih"][:10] if a in ig else "-"
        print(f"  {a:<28} {y:<13} {g}")
    print()
    for pl, tab in (("youtube", yt), ("instagram", ig)):
        kalan = [d for d in dersler if ys._anahtar(d["dosya"]) not in tab]
        print(f"  {pl:<10}: {len(tab)} yayinda, {len(kalan)} sirada")

    # Iki platform ne kadar ayrismis
    fark = set(yt) ^ set(ig)
    if fark:
        r.u(f"iki platform {len(fark)} derste ayrismis durumda "
            f"(birinde yayinda, otekinde degil) — bu normal olabilir, "
            f"ama kasitli mi diye bak")
    return yt, ig


def ayni_ders_iki_kez(veri, r):
    """Ayni derse ayni platformda birden fazla kayit."""
    baslik("CIFT YAYIN KONTROLU")
    sayac = {}
    for k in veri.get("yayinlananlar", []):
        for pl in ys.PLATFORMLAR:
            if k.get(pl):
                sayac.setdefault((k["ders"], pl), []).append(k.get("tarih", "?"))
    cift = {k: v for k, v in sayac.items() if len(v) > 1}
    if cift:
        for (ders, pl), tarihler in cift.items():
            r.c(f"{ders} {pl} platformunda {len(tarihler)} kez kayitli: "
                f"{', '.join(t[:10] for t in tarihler)}")
        print(f"  {_renk('CAKISMA', KIRMIZI)}: {len(cift)} ders iki kez yayinlanmis")
    else:
        print(f"  {_renk('temiz', YESIL)} — hicbir ders ayni platformda iki kez yok")


def platform_sahipligi(otr, r):
    """Her platformun tek sahibi var mi, yasaklar yerinde mi."""
    baslik("PLATFORM SAHIPLIGI")
    if not otr:
        r.u(f"{OTURUM_YOLU} yok — oturum kayit defteri olmadan sahiplik denetlenemez")
        print(f"  {_renk('kayit defteri yok', SARI)}")
        return
    for ad, p in (otr.get("platformlar") or {}).items():
        sahip = p.get("sahip", "?")
        dg = p.get("dogrulama", "?")
        im = _renk("dogrulandi", YESIL) if dg == "dogrulandi" else _renk(dg, SARI)
        print(f"  {ad:<12} sahip: {sahip}")
        print(f"  {'':<12} kayit: {p.get('kayit', '?')}   [{im}]")
        if p.get("yasak"):
            print(f"  {'':<12} {_renk('YASAK: ' + ' '.join(p['yasak'].split()), SARI)}")
        if dg != "dogrulandi":
            r.u(f"platform '{ad}' sahipligi dogrulanmamis ({dg})")


def oturum_listesi(otr, r):
    baslik("OTURUMLAR")
    if not otr:
        return
    for o in otr.get("oturumlar") or []:
        ul = "ulasilabilir" if o.get("ulasilabilir") else "ULASILAMAZ"
        dg = o.get("dogrulama", "?")
        im = _renk(ul, YESIL if o.get("ulasilabilir") else SARI)
        print(f"  {o['ad']:<42} {im}  [{dg}]")
        print(f"  {'':<42} {_renk(o.get('isi', ''), AG)}")
        if dg != "dogrulandi":
            r.u(f"oturum '{o['ad']}' tanimi dogrulanmamis — kendisi teyit etmeli")
    ulasilmaz = [o["ad"] for o in (otr.get("oturumlar") or [])
                 if not o.get("ulasilabilir")]
    if ulasilmaz:
        r.u(f"{len(ulasilmaz)} oturuma mesaj atilamiyor "
            f"({', '.join(ulasilmaz)}) — koordinasyon yalnizca bu depo uzerinden")


def konu_cakismasi(r):
    baslik("KONU CAKISMASI (dis yayinlarla)")
    veri = cakisma.dis_yayinlar()
    if veri.get("eksik_olabilir"):
        r.u(f"dis yayin listesi EKSIK OLABILIR (kaynak: {veri.get('kaynak','?')}) "
            f"— cakisma kontrolu ancak bu liste kadar guvenilir")
    sorun = 0
    for yol in sorted(lesson.dersleri_bul()):
        try:
            d = lesson.yukle(yol)
        except Exception:
            continue
        for y, konu, deginme in cakisma.tara(*cakisma._ders_metinleri(d), veri):
            if konu:
                sorun += 1
                r.c(f"ders {d['no']:02d} '{d['baslik']}' ile "
                    f"'{y['baslik']}' ({y['tarih']}) ayni konu: {', '.join(konu)}")
    print(f"  {_renk('temiz', YESIL) if not sorun else _renk(str(sorun) + ' CAKISMA', KIRMIZI)}")


def kutuphane_tutarliligi(dersler, r):
    """Onaylanmis derslerle kutuphane ortusuyor mu."""
    baslik("KUTUPHANE TUTARLILIGI")
    idx = "library/approved/index.json"
    if not os.path.exists(idx):
        r.u(f"{idx} yok")
        print(f"  {_renk('dizin yok', SARI)}")
        return
    import json
    with open(idx, encoding="utf-8") as f:
        kayit = json.load(f)
    onayli = {k["klasor"] for k in kayit.get("dersler", [])}
    ders_ad = {ys._anahtar(d["dosya"]) for d in dersler}
    eksik = ders_ad - onayli
    fazla = onayli - ders_ad
    print(f"  ders dosyasi: {len(ders_ad)}   onayli video: {len(onayli)}")
    if eksik:
        r.u(f"onaylanmamis ders: {', '.join(sorted(eksik))}")
    if fazla:
        r.u(f"kutuphanede olup ders dosyasi olmayan: {', '.join(sorted(fazla))}")
    if not eksik and not fazla:
        print(f"  {_renk('temiz', YESIL)}")


def main():
    ap = argparse.ArgumentParser(description="AAE oturum sistemi denetimi")
    ap.add_argument("--kisa", action="store_true", help="yalniz uyari ve cakismalar")
    ap.add_argument("--platform", default="youtube", choices=ys.PLATFORMLAR)
    args = ap.parse_args()

    r = Rapor()
    otr = oturumlari_oku()
    veri = ys.kaydi_oku()
    dersler = ys.dersler()

    if not args.kisa:
        print(_renk("AAE SISTEM KONTROLU", AG))
        if otr:
            print(_renk(f"kayit defteri: {OTURUM_YOLU} ({otr.get('guncelleme','?')})", AG))
        platform_sahipligi(otr, r)
        oturum_listesi(otr, r)
        platform_tablosu(veri, dersler, r)
        ayni_ders_iki_kez(veri, r)
        kutuphane_tutarliligi(dersler, r)
        konu_cakismasi(r)
    else:
        platform_sahipligi(otr, Rapor())
        ayni_ders_iki_kez(veri, r)
        konu_cakismasi(r)

    baslik("SONUC")
    for c in r.cakisma:
        print(f"  {_renk('CAKISMA', KIRMIZI)}  {c}")
    for u in r.uyari:
        print(f"  {_renk('uyari  ', SARI)}  {u}")
    if not r.cakisma and not r.uyari:
        print(f"  {_renk('sistem temiz', YESIL)}")
    print()
    sys.exit(r.kod())


if __name__ == "__main__":
    main()
