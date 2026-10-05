#!/usr/bin/env python3
"""
lesson.py
-------------------------------------------------------------------
Ders dosyasini (content/dersler/*.yml) okur, dogrular ve normalize eder.
Render betigi ve her iki yayinci da ayni kaynaktan beslenir ki
YouTube ile Instagram'daki metinler birbirinden ayrismasin.

Kullanim:
  python3 scripts/lesson.py content/dersler/01-acil-fren.yml --json
  python3 scripts/lesson.py --liste          # tum dersleri listele
  python3 scripts/lesson.py --ilk            # en kucuk numarali dersin yolu

KURALLAR.md'deki sinirlar burada uygulanir (sure, caption, etiket sayisi).
-------------------------------------------------------------------
"""
import argparse
import datetime as dt
import glob
import json
import os
import sys

DERS_DIZINI = "content/dersler"
MAKS_SURE = 90          # KURALLAR.md: ust sinir 90 sn
VARSAYILAN_SURE = 60
IG_CAPTION_SINIR = 2200
IG_ETIKET_SINIR = 30
YT_BASLIK_SINIR = 100
SERI_VARSAYILAN = "MOTOSİKLET YOL OKULU"
HANDLE = "@aae_motorcycle"
VIDEO_UZANTI = (".mp4", ".mov", ".mkv", ".m4v", ".webm", ".MP4", ".MOV")


class DersHatasi(Exception):
    pass


def _yaml_yukle(yol: str) -> dict:
    try:
        import yaml
    except ImportError:
        raise DersHatasi("PyYAML yok. Kurun: pip install -r requirements-publish.txt")
    with open(yol, encoding="utf-8") as fh:
        veri = yaml.safe_load(fh)
    if not isinstance(veri, dict):
        raise DersHatasi(f"{yol}: dosyanin kokunde bir sozluk (key: value) olmali.")
    return veri


def _kaynak_bul(belirtilen: str) -> str:
    """Ders dosyasinda kaynak verilmediyse videos/ icindeki ilk videoyu sec."""
    if belirtilen:
        return belirtilen
    adaylar = sorted(
        p for p in glob.glob("videos/*")
        if os.path.isfile(p) and p.endswith(VIDEO_UZANTI)
    )
    return adaylar[0] if adaylar else ""


def _adimlar(ham) -> list:
    if not ham:
        return []
    if not isinstance(ham, list):
        raise DersHatasi("'adimlar' bir liste olmali.")
    cikti = []
    for i, a in enumerate(ham, 1):
        if not isinstance(a, dict) or "metin" not in a:
            raise DersHatasi(f"adimlar[{i}]: en az 'metin' alani gerekli.")
        t = float(a.get("t", 0))
        sure = float(a.get("sure", 4))
        if t < 0 or sure <= 0:
            raise DersHatasi(f"adimlar[{i}]: 't' negatif olamaz, 'sure' pozitif olmali.")
        cikti.append({
            "t": t,
            "bitis": round(t + sure, 3),
            "metin": str(a["metin"]).strip(),
        })
    return cikti


def _etiket_sayisi(metin: str) -> int:
    return sum(1 for kelime in metin.split() if kelime.startswith("#"))


def yukle(yol: str) -> dict:
    """Ders dosyasini normalize edilmis bir sozluge cevirir."""
    if not os.path.isfile(yol):
        raise DersHatasi(f"Ders dosyasi bulunamadi: {yol}")
    ham = _yaml_yukle(yol)

    no = ham.get("ders_no")
    if not isinstance(no, int) or no < 1:
        raise DersHatasi(f"{yol}: 'ders_no' 1 veya daha buyuk bir tamsayi olmali.")
    baslik = str(ham.get("baslik", "")).strip()
    if not baslik:
        raise DersHatasi(f"{yol}: 'baslik' bos olamaz.")
    slug = str(ham.get("slug") or "").strip()
    if not slug:
        raise DersHatasi(f"{yol}: 'slug' bos olamaz (dosya adinda kullanilir).")

    sure = int(ham.get("sure", VARSAYILAN_SURE))
    if not 1 <= sure <= MAKS_SURE:
        raise DersHatasi(f"{yol}: 'sure' 1-{MAKS_SURE} sn arasinda olmali (KURALLAR.md).")

    yt = ham.get("youtube") or {}
    ig = ham.get("instagram") or {}
    if not isinstance(yt, dict) or not isinstance(ig, dict):
        raise DersHatasi(f"{yol}: 'youtube' ve 'instagram' birer sozluk olmali.")

    yt_baslik = str(yt.get("baslik") or f"Ders {no}: {baslik}").strip()
    yt_aciklama = str(yt.get("aciklama") or "").strip()
    etiketler = yt.get("etiketler") or []
    if not isinstance(etiketler, list):
        raise DersHatasi(f"{yol}: 'youtube.etiketler' bir liste olmali.")
    gizlilik = str(yt.get("gizlilik") or "private").strip()
    if gizlilik not in ("private", "unlisted", "public"):
        raise DersHatasi(f"{yol}: 'youtube.gizlilik' private|unlisted|public olmali.")

    caption = str(ig.get("caption") or f"{baslik}\n\n{HANDLE}").strip()
    if len(caption) > IG_CAPTION_SINIR:
        raise DersHatasi(
            f"{yol}: 'instagram.caption' {len(caption)} karakter — sinir {IG_CAPTION_SINIR}.")
    if _etiket_sayisi(caption) > IG_ETIKET_SINIR:
        raise DersHatasi(
            f"{yol}: caption'da {_etiket_sayisi(caption)} etiket var — sinir {IG_ETIKET_SINIR}.")

    boyut = int(ham.get("boyut", 3))
    if boyut not in (2, 3):
        raise DersHatasi(f"{yol}: 'boyut' 2 ya da 3 olmali.")
    sahne = str(ham.get("sahne") or "").strip()
    if sahne and sahne not in ("fren", "viraj"):
        raise DersHatasi(f"{yol}: 'sahne' fren|viraj olmali (ya da bos).")
    kaynak = _kaynak_bul(str(ham.get("kaynak") or "").strip())
    baslangic = float(ham.get("baslangic", 0))
    if baslangic < 0:
        raise DersHatasi(f"{yol}: 'baslangic' negatif olamaz.")
    kaynak_ses = float(ham.get("kaynak_ses", 1.0))
    if not 0.0 <= kaynak_ses <= 2.0:
        raise DersHatasi(f"{yol}: 'kaynak_ses' 0-2 arasinda olmali.")
    surum = int(ham.get("surum", 1))
    tarih = str(ham.get("tarih") or dt.date.today().isoformat())
    cikti_adi = f"{tarih}_ders{no:02d}_{slug}_v{surum}.mp4"

    return {
        "dosya": yol,
        "no": no,
        "slug": slug,
        "baslik": baslik,
        "alt_baslik": str(ham.get("alt_baslik") or "").strip(),
        "seri": str(ham.get("seri") or SERI_VARSAYILAN).strip(),
        "handle": HANDLE,
        "kapanis": str(ham.get("kapanis") or "").strip(),
        "kaynak": kaynak,
        "sahne": sahne,
        "boyut": boyut,
        "sahne_fazlari": str(ham.get("sahne_fazlari") or "").strip(),
        "baslangic": baslangic,
        "kaynak_ses": kaynak_ses,
        "sure": sure,
        "muzik": str(ham.get("muzik") or "").strip(),
        "muzik_ses": float(ham.get("muzik_ses", 0.25)),
        "adimlar": _adimlar(ham.get("adimlar")),
        "cikti": os.path.join("output", cikti_adi),
        "youtube": {
            "baslik": yt_baslik[:YT_BASLIK_SINIR],
            "aciklama": yt_aciklama,
            "etiketler": [str(e).strip() for e in etiketler if str(e).strip()],
            "kategori": str(yt.get("kategori") or "2"),   # 2 = Autos & Vehicles
            "gizlilik": gizlilik,
        },
        "instagram": {
            "caption": caption,
            "feed_de_paylas": bool(ig.get("feed_de_paylas", True)),
            "kapak_url": str(ig.get("kapak_url") or "").strip(),
        },
    }



# ---------------------------------------------------------------------------
# Render metinleri: drawtext dosyalari + punto hesabi
# Metin isleri (Turkce buyuk harf, satir sarma, punto) burada kalir; ffmpeg
# betigi yalnizca hazir dosyalari okur. Boylece kacis/escape derdi olmaz.
# ---------------------------------------------------------------------------
TR_BUYUK = str.maketrans("ıi", "Iİ")
GENISLIK_PX = 980          # 1080 - 2x50 kenar bosluk


def tr_upper(metin: str) -> str:
    return metin.translate(TR_BUYUK).upper()


def _sar(metin: str, genislik: int) -> list:
    import textwrap
    return textwrap.wrap(metin, genislik) or [""]


def _punto(satirlar: list, maks_punto: int, kat: float = 0.60) -> int:
    """DejaVu Sans Bold icin kaba genislik tahmini: karakter ~ 0.60 em."""
    en_uzun = max((len(s) for s in satirlar), default=1) or 1
    return max(22, min(maks_punto, int(GENISLIK_PX / (en_uzun * kat))))


def metinleri_yaz(ders: dict, dizin: str) -> dict:
    """drawtext icin metin dosyalarini yazar, punto/zamanlamalari dondurur."""
    os.makedirs(dizin, exist_ok=True)

    def yaz(ad: str, metin: str) -> None:
        with open(os.path.join(dizin, ad), "w", encoding="utf-8") as fh:
            fh.write(metin)

    seri = tr_upper(ders["seri"])
    ders_etiketi = f"DERS {ders['no']:02d}"

    ust = _sar(f"{ders_etiketi} · {tr_upper(ders['baslik'])}", 36)
    intro_baslik = _sar(ders["baslik"], 17)
    intro_alt = _sar(ders["alt_baslik"], 28) if ders["alt_baslik"] else []
    kapanis = _sar(ders["kapanis"], 24) if ders["kapanis"] else []

    yaz("seri.txt", seri)
    yaz("ustbant.txt", "\n".join(ust))
    yaz("handle.txt", ders["handle"])
    yaz("intro_ders.txt", ders_etiketi)
    yaz("intro_baslik.txt", "\n".join(intro_baslik))
    if intro_alt:
        yaz("intro_alt.txt", "\n".join(intro_alt))
    if kapanis:
        yaz("kapanis.txt", "\n".join(kapanis))

    adimlar = []
    for i, a in enumerate(ders["adimlar"], 1):
        satirlar = _sar(a["metin"], 32)
        ad = f"adim{i}.txt"
        yaz(ad, "\n".join(satirlar))
        adimlar.append({
            "dosya": ad,
            "t": a["t"],
            "bitis": a["bitis"],
            "punto": _punto(satirlar, 52),
            "satir": len(satirlar),
        })

    return {
        "dizin": dizin,
        "punto_ustbant": _punto(ust, 50),
        "punto_seri": 34,
        "punto_handle": 42,
        "punto_intro_ders": 58,
        "punto_intro_baslik": _punto(intro_baslik, 100),
        "punto_intro_alt": _punto(intro_alt, 50) if intro_alt else 0,
        "punto_kapanis": _punto(kapanis, 66) if kapanis else 0,
        "intro_alt_var": bool(intro_alt),
        "kapanis_var": bool(kapanis),
        "ustbant_satir": len(ust),
        "intro_baslik_satir": len(intro_baslik),
        "adimlar": adimlar,
    }


def dersleri_bul() -> list:
    return sorted(
        p for p in glob.glob(os.path.join(DERS_DIZINI, "*.yml"))
        if not os.path.basename(p).startswith("_")
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="AAE ders dosyasi okuyucu")
    ap.add_argument("ders", nargs="?", help="content/dersler/*.yml")
    ap.add_argument("--json", action="store_true", help="normalize edilmis JSON bas")
    ap.add_argument("--liste", action="store_true", help="tum dersleri listele")
    ap.add_argument("--ilk", action="store_true", help="en kucuk numarali dersin yolunu bas")
    ap.add_argument("--metinler", metavar="DIZIN",
                    help="drawtext metin dosyalarini bu dizine yaz, plani JSON bas")
    args = ap.parse_args()

    try:
        if args.liste or args.ilk:
            dersler = []
            for yol in dersleri_bul():
                try:
                    dersler.append(yukle(yol))
                except DersHatasi as exc:
                    print(f"UYARI: {exc}", file=sys.stderr)
            dersler.sort(key=lambda d: d["no"])
            if not dersler:
                print(f"HATA: {DERS_DIZINI} icinde gecerli ders yok.", file=sys.stderr)
                sys.exit(1)
            if args.ilk:
                print(dersler[0]["dosya"])
            else:
                for d in dersler:
                    print(f"{d['no']:>3}  {d['baslik']:<44} {d['dosya']}")
            return

        if not args.ders:
            ap.error("bir ders dosyasi verin ya da --liste / --ilk kullanin")
        ders = yukle(args.ders)
        if args.metinler:
            plan = metinleri_yaz(ders, args.metinler)
            print(json.dumps({"ders": ders, "plan": plan}, ensure_ascii=False))
            return
        if args.json:
            print(json.dumps(ders, ensure_ascii=False, indent=2))
        else:
            print(f"Ders {ders['no']:02d} · {ders['baslik']}")
            if ders["kaynak"]:
                kaynak_satiri = ders["kaynak"]
            elif ders["sahne"]:
                kaynak_satiri = f"uretilecek sahne: {ders['sahne']} ({ders['boyut']} boyutlu)"
            else:
                kaynak_satiri = "(videos/ bos)"
            print(f"  kaynak : {kaynak_satiri}")
            print(f"  cikti  : {ders['cikti']}")
            print(f"  sure   : {ders['sure']} sn · {len(ders['adimlar'])} adim"
                  f" · baslangic {ders['baslangic']} sn")
            print(f"  ses    : motor {ders['kaynak_ses']} · muzik "
                  f"{ders['muzik_ses'] if ders['muzik'] else '(yok)'}")
            print(f"  youtube: {ders['youtube']['baslik']} [{ders['youtube']['gizlilik']}]")
    except DersHatasi as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
