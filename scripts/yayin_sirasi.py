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


PLATFORMLAR = ("youtube", "instagram")


def yapilanlar(veri: dict, platform: str = "youtube") -> dict:
    """{ders anahtari: kayit} - YALNIZCA o platformda yayinlanmis olanlar.

    Eskiden platformdan bagimsizdi: kayitta ders adi gecen her sey
    "yayinlandi" sayiliyordu. Instagram'i baska bir oturum Business
    Suite'ten yurutuyor; o bir dersi kaydettigi anda YouTube is akisi o
    dersi ATLIYORDU ve ders YouTube'a hic gitmiyordu. Iki platform iki
    ayri kuyruk."""
    if platform not in PLATFORMLAR:
        raise SystemExit(f"HATA: bilinmeyen platform '{platform}'")
    return {k["ders"]: k for k in veri["yayinlananlar"] if k.get(platform)}


def sonraki(veri: dict, platform: str = "youtube") -> dict | None:
    """O PLATFORMDA henuz yayinlanmamis en kucuk numarali ders."""
    yapildi = yapilanlar(veri, platform)
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


ISTANBUL = dt.timezone(dt.timedelta(hours=3))   # Turkiye yil boyu UTC+3
# GUNDE IKI DERS: 10:00 ve 14:00 (Istanbul). AAE 19.11'de boyle istedi;
# oncesinde gunde bir ders, 09:00'daydi. Saatler artan sirada olmali,
# cunku plan() gunu bu sirayla dolduruyor.
GUNLUK_SAATLER = (10, 14)


def plan(veri: dict, platform: str = "youtube", baslangic: str = "") -> list:
    """[(tarih, ders)] - sirasi gelmemis dersleri gunluk takvime dizer.

    Is akisi videoyu publishAt ile bir sonraki 09:00'a programliyor, yani
    kuyruktaki her ders bir sonraki gune dusuyor. Bu liste onu gosterir.
    baslangic bos ise ilk slot SIMDIDEN sonraki 09:00."""
    if baslangic:
        try:
            gun = dt.datetime.strptime(baslangic, "%Y-%m-%d").replace(
                tzinfo=ISTANBUL)
        except ValueError:
            raise SystemExit(f"HATA: tarih YYYY-AA-GG olmali, '{baslangic}' degil")
        simdi = None
    else:
        simdi = dt.datetime.now(ISTANBUL)
        gun = simdi
    # Gunu GUNLUK_SAATLER ile dolduran sonsuz slot uretici. Tek saat
    # varsayan eski surum gunde bir ders diziyordu; artik gun basina
    # len(GUNLUK_SAATLER) ders var.
    def slotlar():
        g = gun
        while True:
            for saat in GUNLUK_SAATLER:
                an = g.replace(hour=saat, minute=0, second=0, microsecond=0)
                if simdi is None or an > simdi:
                    yield an
            g += dt.timedelta(days=1)
    yapildi = yapilanlar(veri, platform)
    uret = slotlar()
    cikti = []
    for d in dersler():
        if _anahtar(d["dosya"]) in yapildi:
            continue
        cikti.append((next(uret), d))
    return cikti


def main() -> None:
    ap = argparse.ArgumentParser(description="AAE gunluk yayin sirasi")
    ap.add_argument("--sonraki", action="store_true",
                    help="sirada bekleyen dersin yolunu bas (yoksa cikis kodu 3)")
    ap.add_argument("--durum", action="store_true", help="tum dersleri durumuyla listele")
    ap.add_argument("--isaretle", metavar="DERS", help="dersi yayinlandi olarak isaretle")
    ap.add_argument("--youtube", default="", help="--isaretle ile: YouTube video id")
    ap.add_argument("--instagram", default="", help="--isaretle ile: Instagram media id")
    ap.add_argument("--kayit", default=KAYIT_YOLU)
    ap.add_argument("--plan", nargs="?", const="", metavar="YYYY-AA-GG",
                    help="tarihli yayin takvimi (bos = bir sonraki 09:00'dan)")
    ap.add_argument("--platform", default="youtube", choices=PLATFORMLAR,
                    help="hangi platformun kuyrugu (varsayilan youtube)")
    ap.add_argument("--plan-md", nargs="?", const="", metavar="YYYY-AA-GG",
                    dest="plan_md",
                    help="iki platformu yan yana gosteren markdown takvim")
    args = ap.parse_args()

    veri = kaydi_oku(args.kayit)

    if args.isaretle:
        kaydi_yaz(isaretle(veri, args.isaretle, args.youtube, args.instagram),
                  args.kayit)
        print(f"isaretlendi: {_anahtar(args.isaretle)}")
        return

    if args.plan_md is not None:
        # Iki kuyruk AYRI. Bugun ayni tarihler cikiyor cunku hicbir ders
        # yayinlanmadi; biri digerinden once ilerlerse tablo ayrisir.
        # Bu dosya Business Suite'i yuruten oturumun calisma listesidir.
        tablo = {}
        for pl in PLATFORMLAR:
            for g, d in plan(veri, pl, args.plan_md):
                tablo.setdefault(d["no"], {"ders": d})[pl] = g
        gunler = ("Pzt", "Sal", "Car", "Per", "Cum", "Cmt", "Paz")
        ur = dt.datetime.now(ISTANBUL)
        print("<!-- URETILMIS DOSYA - elle duzenlemeyin.")
        print("     python3 scripts/yayin_sirasi.py --plan-md "
              "> content/yayin_plani.md -->")
        saatler = " ve ".join(f"{h:02d}:00" for h in GUNLUK_SAATLER)
        print(f"# Yayın planı · her gün {saatler} (İstanbul)\n")
        print(f"Üretildi: {ur:%d.%m.%Y %H:%M} · "
              f"kaynak: `{KAYIT_YOLU}` + `content/dersler/`\n")
        print("| Ders | Başlık | YouTube | Instagram | Dosyalar |")
        print("|---:|---|---|---|---|")
        for no in sorted(tablo):
            satir = tablo[no]
            d = satir["ders"]
            hucre = []
            for pl in PLATFORMLAR:
                g = satir.get(pl)
                hucre.append("— *(yayınlandı)*" if g is None
                             else f"{g:%d.%m.%Y} {gunler[g.weekday()]} "
                                  f"{g:%H:%M}")
            # Business Suite'ten planlayan oturumun ihtiyaci olan her sey
            # burada: video + caption (meta.json icinde instagram.caption).
            klasor = _anahtar(d["dosya"])
            yol = f"library/approved/{klasor}/"
            kutu = (f"`{yol}`" if os.path.isdir(yol) else "*(onaylanmadı)*")
            print(f"| {no:02d} | {d['baslik']} | {hucre[0]} | {hucre[1]} "
                  f"| {kutu} |")
        print(f"\n**YouTube**: `gunluk-yayin.yml` iş akışı otomatik yürütür. "
              f"Günde {len(GUNLUK_SAATLER)} çalışma var; her biri videoyu "
              f"`publishAt` ile kendi saatine ({saatler}) programlar, yani "
              f"cron gecikse bile video tam saatinde açılır.")
        print("\n**Instagram**: bu tablo Business Suite'ten planlayan oturumun "
              "çalışma listesidir. `gunluk-yayin.yml` zamanlanmış çalışmada "
              "Instagram'a **yayınlamaz**; iki kez paylaşılmasın diye "
              "`IG_USER_ID` ve `IG_ACCESS_TOKEN` secret'ları girilmez.")
        print("\nBir ders bir platformda yayınlandığında o platformun "
              "sütunundan düşer, diğerininkinden düşmez — iki ayrı kuyruk.")
        print("\nHer klasörde video (`<ders>.mp4`) ve `meta.json` var; "
              "Instagram açıklaması `meta.json` → `instagram.caption` "
              "alanında hazır duruyor, elle yazmaya gerek yok.")
        return

    if args.plan is not None:
        satirlar = plan(veri, args.platform, args.plan)
        if not satirlar:
            print(f"  {args.platform}: sirada ders yok.")
            return
        ilk, son = satirlar[0][0], satirlar[-1][0]
        saatler = " ve ".join(f"{h:02d}:00" for h in GUNLUK_SAATLER)
        print(f"  YAYIN PLANI · {args.platform} · her gun {saatler} "
              f"(Istanbul)\n")
        gunler = ("Pzt", "Sal", "Car", "Per", "Cum", "Cmt", "Paz")
        for g, d in satirlar:
            print(f"  {g:%d.%m.%Y}  {gunler[g.weekday()]}  {g:%H:%M}  "
                  f"ders {d['no']:02d}  {d['baslik']}")
        print(f"\n  {len(satirlar)} ders · {ilk:%d.%m.%Y} - {son:%d.%m.%Y}")
        print("  (secret'lar girilene kadar hicbiri yayinlanmaz)")
        return

    if args.durum:
        yt = yapilanlar(veri, "youtube")
        ig = yapilanlar(veri, "instagram")
        print(f"  (kuyruk: {args.platform})\n")
        print(f"  {'sira':<6} {'ders':<26} {'YOUTUBE':<12} INSTAGRAM")
        for i, d in enumerate(dersler(), 1):
            a = _anahtar(d["dosya"])
            y = yt[a]["tarih"][:10] if a in yt else "-"
            g = ig[a]["tarih"][:10] if a in ig else "-"
            print(f"  {i:>2}.    {a:<26} {y:<12} {g}")
        for pl, tab in (("youtube", yt), ("instagram", ig)):
            kalan = sum(1 for d in dersler() if _anahtar(d["dosya"]) not in tab)
            print(f"\n  {pl:<10}: {kalan} ders sirada")
        tutulan = [d for d in dersler(True) if d.get("yayin_beklet")]
        if tutulan:
            print("\n  BEKLETILEN:")
            for d in tutulan:
                not_ = d.get("yayin_beklet_notu") or "sebep yazilmamis"
                print(f"    ders {d['no']:02d}  {d['baslik']} — {not_}")
        return

    if args.sonraki:
        d = sonraki(veri, args.platform)
        if d is None:
            print("Sirada ders yok: hepsi yayinlandi.", file=sys.stderr)
            raise SystemExit(3)
        print(d["dosya"])
        return

    ap.print_help()


if __name__ == "__main__":
    main()
