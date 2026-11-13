#!/usr/bin/env python3
"""Instagram Story karti: 1080x1920, 15 saniye.

Seriyi duyuran kisa dikey video. Arka planda viraj sahnesi doner, uzerine
Story guvenli alaninda metin gelir.

Instagram Story'de ustteki ~250 px profil/ilerleme cubugu, alttaki ~250 px
yanit kutusu tarafindan ortulur; icerik bu bandin disina tasmaz.

Kullanim:
  python3 scripts/story_uret.py
  python3 scripts/story_uret.py --sure 15 --cikti output/story.mp4
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lesson  # noqa: E402
import sahne_uret as s2  # noqa: E402
import sahne3b as s3  # noqa: E402

G, Y, FPS = s2.G, s2.Y, s2.FPS
UST_GUVENLI, ALT_GUVENLI = 250, Y - 250      # Story arayuzunun ortmedigi bant
MUZIK = "assets/muzik/aae_okul.mp3"


def _yumusak(p: float) -> float:
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def _gir(t: float, bas: float, sure: float = 0.45) -> float:
    """0 -> 1 arasi giris carpani."""
    return _yumusak((t - bas) / sure)


def _perde(im: Image.Image) -> None:
    """Ust ve altta koyu gecis: metin okunur olsun, orta acik kalsin."""
    perde = Image.new("RGBA", (1, Y), (0, 0, 0, 0))
    d = ImageDraw.Draw(perde)
    for y in range(Y):
        if y < 620:
            a = int(205 * (1 - y / 620) ** 1.25)
        elif y > 1080:
            a = int(232 * ((y - 1080) / (Y - 1080)) ** 0.95)
        else:
            a = 0
        d.point((0, y), fill=(6, 10, 16, a))
    im.alpha_composite(perde.resize((G, Y)))


def _dersler() -> list:
    cikti = []
    for yol in sorted(lesson.dersleri_bul()):
        try:
            d = lesson.yukle(yol)
        except Exception:          # sablon ve yarim dosyalar atlanir
            continue
        cikti.append((d["no"], d["baslik"]))
    return sorted(cikti)[:4]


def kare(t: float, sure: float, dersler: list) -> Image.Image:
    # Arka plan: viraj sahnesi, HUD'suz. Sahne 55 sn'lik kurguya gore
    # ilerliyor; Story icin en hareketli bolumden (10. sn) basliyoruz.
    arka = s3.kare_viraj3b(10.0 + t, 55.0, gosterge=False).convert("RGBA")
    _perde(arka)
    d = ImageDraw.Draw(arka, "RGBA")

    # --- ust blok: marka ---------------------------------------------------
    g = _gir(t, 0.25)
    if g > 0:
        y0 = UST_GUVENLI + 40 - int(30 * (1 - g))
        s2.yazi(d, (G / 2, y0), "CUMA", 44, s2.TURUNCU, ortala=True)
        s2.yazi(d, (G / 2, y0 + 62), "MOTOSİKLET", 84, s2.KREM, ortala=True)
        s2.yazi(d, (G / 2, y0 + 168), "YOL OKULU", 84, s2.KREM, ortala=True)
        d.rounded_rectangle([G / 2 - 90, y0 + 288, G / 2 + 90, y0 + 296], 4,
                            fill=s2.TURUNCU)

    # --- alt blok: dersler -------------------------------------------------
    g2 = _gir(t, 2.3)
    if g2 > 0:
        s2.yazi(d, (G / 2, 1072), "4 DERS YAYINDA", 50, s2.MAVI, ortala=True)

    for i, (no, baslik) in enumerate(dersler):
        gi = _gir(t, 3.6 + i * 1.25, 0.5)
        if gi <= 0:
            continue
        yy = 1152 + i * 88
        x0 = 96 - int(40 * (1 - gi))
        d.rounded_rectangle([x0, yy, x0 + 64, yy + 64], 12,
                            fill=(*s2.TURUNCU, int(235 * gi)))
        s2.yazi(d, (x0 + 32, yy + 10), f"{no}", 40, (18, 18, 20), ortala=True)
        s2.yazi(d, (x0 + 88, yy + 12), baslik, 40,
                (*s2.KREM, int(255 * gi)))

    # --- kapanis -----------------------------------------------------------
    g3 = _gir(t, 10.6, 0.6)
    if g3 > 0:
        # Son ders kutusu 1480'de bitiyor; kapanis 60 px asagidan basliyor.
        s2.yazi(d, (G / 2, 1540), "Profilde hepsi hazır", 42,
                (*s2.KREM, int(235 * g3)), ortala=True)
        s2.yazi(d, (G / 2, 1596), "@aae_motorcycle", 44,
                (*s2.TURUNCU, int(255 * g3)), ortala=True)

    # --- acilis / kapanis karartmasi ---------------------------------------
    kar = 0.0
    if t < 0.6:
        kar = 1.0 - _yumusak(t / 0.6)
    elif t > sure - 0.7:
        kar = _yumusak((t - (sure - 0.7)) / 0.7)
    if kar > 0:
        d.rectangle([0, 0, G, Y], fill=(0, 0, 0, int(255 * kar)))
    return arka.convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser(description="AAE Instagram Story karti")
    ap.add_argument("--sure", type=float, default=15.0, help="saniye (Story siniri 15)")
    ap.add_argument("--cikti", default="")
    args = ap.parse_args()

    dersler = _dersler()
    if not dersler:
        raise SystemExit("HATA: content/dersler icinde ders yok.")
    cikti = args.cikti or (f"output/{dt.date.today():%Y-%m-%d}_story_yol-okulu.mp4")
    os.makedirs(os.path.dirname(cikti) or ".", exist_ok=True)

    s3.GUNDUZ = True
    s2.fazlari_ayarla("0:sabit, 8:uzak, 16:acilir, 26:kapanir, 38:engel")

    toplam = int(args.sure * FPS)
    print(f">> Story: {args.sure:.0f} sn · {toplam} kare · {len(dersler)} ders")
    with tempfile.TemporaryDirectory() as gecici:
        for f in range(toplam):
            kare(f / FPS, args.sure, dersler).save(
                os.path.join(gecici, f"k{f:05d}.png"))
            if f % 60 == 0:
                print(f"   kare {f}/{toplam}")
        ses = ["-i", MUZIK] if os.path.exists(MUZIK) else []
        sesli = ["-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k",
                 "-af", (f"afade=t=in:st=0:d=1.2,"
                         f"afade=t=out:st={args.sure - 1.0:.2f}:d=1.0,"
                         "loudnorm=I=-14:TP=-1.5:LRA=11"),
                 "-shortest"] if ses else []
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error",
             "-framerate", str(FPS), "-i", os.path.join(gecici, "k%05d.png")]
            + ses + ["-t", f"{args.sure:.2f}",
                     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                     "-movflags", "+faststart"] + sesli + [cikti],
            check=True)
    mb = os.path.getsize(cikti) / 1e6
    print(f"TAMAM ✓  {cikti} ({mb:.1f} MB)")


if __name__ == "__main__":
    main()
