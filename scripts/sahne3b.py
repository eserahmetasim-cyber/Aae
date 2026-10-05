#!/usr/bin/env python3
"""
sahne3b.py
-------------------------------------------------------------------
Eğitim videolarının arka plan sahnelerini 3 BOYUTLU üretir.
Perspektif kamera, ışıklı yüzeyler, derinlik sisi — hepsi
scripts/uc_boyut.py içindeki yazılımsal motorla çizilir.

  fren   · Motosikletin 3/4 görünümü. Frende çatal çöker, motosiklet
           burun aşağı yatar, sürücü öne yüklenir. Yol ve binalar akar.
  viraj  · Sürücü gözünden gerçek 3B yol. Viraj döner, kayboluş noktası
           uzaklaşıp yaklaşır; iç taraftaki tepe uzağı kapatır.

Kullanım:
  python3 scripts/sahne3b.py --sahne fren --sure 60 --cikti /tmp/a.mp4
  python3 scripts/sahne3b.py --sahne viraj --fazlar "0:sabit,19:acilir"
-------------------------------------------------------------------
"""
import argparse
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uc_boyut import Kamera, Sahne, donus            # noqa: E402
import sahne_uret as s2                              # ses + 2B yardimcilar  # noqa: E402

G, Y, FPS = s2.G, s2.Y, s2.FPS
GOK = (13, 18, 26)
ASFALT3 = (68, 72, 78)
CIM = (30, 40, 32)
TURUNCU, KREM, MAVI, KIRMIZI, YESIL = s2.TURUNCU, s2.KREM, s2.MAVI, s2.KIRMIZI, s2.YESIL
LASTIK = (26, 26, 28)
JANT = (205, 170, 85)
GOVDE = (58, 70, 84)
MONT = (96, 112, 130)


# ---------------------------------------------------------------------------
#  Motosiklet modeli (yerel: X yan, Y yukari, Z ileri; orijin yerde, aks arasi)
# ---------------------------------------------------------------------------
def _tekerlek(s, z, aci, yaricap=0.31):
    s.silindir([-0.07, yaricap, z], [0.07, yaricap, z], yaricap, LASTIK, segment=18)
    s.silindir([-0.075, yaricap, z], [0.075, yaricap, z], yaricap * 0.55, (40, 40, 42), segment=14)
    R = donus([1, 0, 0], aci)
    for i in range(5):                                  # jant kollari: donus gorunur
        a = 2 * math.pi * i / 5
        yon = np.array([0.0, math.cos(a), math.sin(a)])
        s.kutu([0, yaricap, z] + (R @ yon) * yaricap * 0.42,
               [0.10, yaricap * 0.80, 0.045], JANT,
               R=R @ donus([1, 0, 0], -a))


def motosiklet(fren):
    """fren 0-1: catal cokmesi + surucunun one yuklenmesi."""
    s = Sahne()
    cokme = 0.085 * fren
    arka_z, on_z = -0.70, 0.70

    s.silindir([0.10, 0.44, arka_z + 0.02], [0.14, 0.46, -0.05], 0.05, GOVDE)   # salincak
    s.silindir([-0.10, 0.44, arka_z + 0.02], [-0.14, 0.46, -0.05], 0.05, GOVDE)
    s.kutu([0, 0.55, -0.02], [0.34, 0.46, 0.60], (74, 86, 97))                  # motor
    s.kutu([0, 0.86, 0.14], [0.30, 0.24, 0.62], TURUNCU)                        # depo
    s.kutu([0, 0.84, -0.44], [0.26, 0.11, 0.55], (30, 30, 32))                  # sele
    s.kutu([0, 0.88, -0.76], [0.22, 0.13, 0.30], (30, 30, 32))                  # kuyruk
    s.kutu([0, 0.89, -0.90], [0.16, 0.07, 0.06], KIRMIZI)                       # stop
    s.silindir([0.12, 0.44, -0.10], [0.21, 0.47, -0.92], 0.06, (168, 176, 182)) # egzoz
    for yan in (-1, 1):                                                          # catal
        s.silindir([yan * 0.11, 0.31, on_z],
                   [yan * 0.10, 0.98 - cokme, on_z - 0.10], 0.038, JANT)
    s.kutu([0, 1.00 - cokme, on_z - 0.12], [0.26, 0.09, 0.14], GOVDE)           # triple
    s.silindir([-0.30, 1.06 - cokme, on_z - 0.18], [0.30, 1.06 - cokme, on_z - 0.18],
               0.022, (190, 198, 205))                                           # gidon
    s.kutu([0, 0.96 - cokme, on_z + 0.10], [0.24, 0.20, 0.12], KREM)            # far
    s.kutu([0, 0.64 - cokme, on_z + 0.04], [0.17, 0.05, 0.46], TURUNCU)         # camurluk

    # --- surucu -----------------------------------------------------------
    one = 0.12 * fren
    omuz_y, omuz_z = 1.50 - 0.10 * fren, -0.12 + one
    kalca_n = np.array([0.0, 1.02, -0.40])
    omuz_n = np.array([0.0, omuz_y, omuz_z])
    s.kure(kalca_n, 0.19, MONT, dilim=12, halka=7)                              # kalca
    s.silindir(kalca_n, omuz_n, 0.185, MONT, segment=14)                        # govde
    s.kure(omuz_n, 0.19, MONT, dilim=12, halka=7)                               # omuz
    for yan in (-1, 1):
        s.silindir([yan * 0.19, omuz_y, omuz_z],
                   [yan * 0.29, 1.07 - cokme, on_z - 0.18], 0.055, MONT)        # kol
        s.silindir([yan * 0.17, 0.98, -0.34], [yan * 0.25, 0.64, 0.10], 0.075, MONT)
        s.silindir([yan * 0.25, 0.64, 0.10], [yan * 0.23, 0.36, -0.02], 0.065, MONT)
    boyun = omuz_n + np.array([0.0, 0.13, 0.05])
    s.silindir(omuz_n, boyun, 0.085, (70, 80, 92), segment=10)                  # boyun
    s.kure([0, omuz_y + 0.26, omuz_z + 0.06], 0.145, KREM, dilim=14, halka=9)   # kask
    s.kutu([0, omuz_y + 0.25, omuz_z + 0.19], [0.17, 0.11, 0.05], (58, 70, 82)) # vizor
    s.kutu([0, omuz_y + 0.38, omuz_z + 0.02], [0.16, 0.05, 0.16], TURUNCU)      # seritt

    _tekerlek(s, arka_z, 0.0)
    _tekerlek(s, on_z, 0.0)
    return s, cokme


def kare_fren3b(t):
    hiz, fren = s2.fren_evre(t)
    im = Image.new("RGB", (G, Y), GOK)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    global _yol_s
    _yol_s = (globals().get("_yol_s", 0.0) + hiz * 0.62) % 8.0

    # Zemin SERITLERE bolunur: tek dev yuzey verince sis onu ortalama
    # derinlige gore boyuyor ve yol arka planla ayni renge dusuyordu.
    z = -30.0
    while z < 150:
        z2 = z + 6.0
        s.yuzey([[-60, 0, z], [60, 0, z], [60, 0, z2], [-60, 0, z2]], CIM, katman=0)
        s.yuzey([[-4.2, 0.01, z], [4.2, 0.01, z], [4.2, 0.01, z2], [-4.2, 0.01, z2]],
                ASFALT3, katman=1)
        for yan in (-1, 1):
            s.yuzey([[yan * 4.0, 0.02, z], [yan * 3.86, 0.02, z],
                     [yan * 3.86, 0.02, z2], [yan * 4.0, 0.02, z2]],
                    (205, 205, 200), katman=2)
        z = z2
    for i in range(-3, 22):                                # kesikli orta cizgi
        z = i * 8.0 - _yol_s
        s.yuzey([[-0.11, 0.02, z], [0.11, 0.02, z], [0.11, 0.02, z + 3.6],
                 [-0.11, 0.02, z + 3.6]], (210, 210, 205), katman=2)
    for i in range(-2, 16):                                # binalar
        z = i * 11.0 - _yol_s * 0.92
        for yan in (-1, 1):
            h = 5 + ((i * 7 + (yan + 1) * 3) % 9) * 1.7
            s.kutu([yan * (7.5 + (i % 3) * 1.6), h / 2, z + 4], [5.0, h, 6.5],
                   (26, 32, 42), katman=3)

    model, _ = motosiklet(fren)
    # Fren: butun motosiklet on aks etrafinda burun asagi yatar
    yat = donus([1, 0, 0], 0.085 * fren)
    pivot = np.array([0, 0.31, 0.70])
    s.ekle(model, R=yat, t=pivot - yat @ pivot)

    # Dikey kadrajda motosiklet orta banda otursun, yol alti doldursun diye
    # kamera yukaridan ve geriden bakar; hafif salinim canlilik verir.
    # Motosiklet ~1.85 m; 50 derece dikey acida karenin yarisini kaplamasi icin
    # kamera hedefe yaklasik 4.5 m uzakta durmali.
    kamera = Kamera([2.62 + 0.20 * math.sin(t * 0.21), 1.92 + 0.08 * math.sin(t * 0.13),
                     -3.25 + 0.26 * math.cos(t * 0.17)],
                    [0.05, 0.80, 0.35], G, Y, fov=50)
    s.ciz(d, kamera, GOK)

    # --- 2B gostergeler ---------------------------------------------------
    on_yuk = 0.5 + 0.32 * fren
    for i, (etiket, deger, renk) in enumerate(
            (("ÖN", on_yuk, TURUNCU), ("ARKA", 1 - on_yuk, MAVI))):
        x0 = 72 + i * 190
        yuk = int(290 * deger)
        d.rounded_rectangle([x0, 470, x0 + 118, 760], 8, fill=(255, 255, 255, 20))
        d.rounded_rectangle([x0, 760 - yuk, x0 + 118, 760], 8, fill=renk)
        s2.yazi(d, (x0 + 59, 772), etiket, 34, KREM, ortala=True)
        s2.yazi(d, (x0 + 59, 812), f"%{int(deger * 100)}", 42, renk, ortala=True)
    s2.yazi(d, (72, 418), "AĞIRLIK", 30, (150, 155, 162))
    d.rounded_rectangle([G - 320, 470, G - 72, 612], 18, fill=(0, 0, 0, 160),
                        outline=(92, 102, 112), width=4)
    s2.yazi(d, (G - 196, 482), f"{int(hiz * 52)}", 82,
            KREM if hiz > 0.02 else YESIL, ortala=True)
    s2.yazi(d, (G - 196, 572), "km/h", 28, (150, 155, 160), ortala=True)
    return im


# ---------------------------------------------------------------------------
#  VIRAJ (surucu gozunden, gercek 3B yol)
# ---------------------------------------------------------------------------
def _merkez_x(z, egri):
    """Yolun orta cizgisinin mesafeye gore yanal kaymasi."""
    return egri * (z ** 2) * 0.0019


def _egim(z, egri):
    """Orta cizginin o noktadaki yonu (radyan)."""
    return math.atan(egri * 2 * z * 0.0019)


def kare_viraj3b(t, toplam=55.0):
    if s2.VIRAJ_FAZLAR:
        derinlik, bukum, (etiket, renk) = s2.viraj_evre_fazli(t, toplam)
        engel = etiket.startswith("ENGELE")
    else:
        derinlik, bukum, (etiket, renk) = s2.viraj_evre(t)
        engel = (t % s2.VIRAJ_DONGU) >= 11.0

    # derinlik kucuk = nokta uzakta. Gorus mesafesine cevir.
    gorus = 95.0 - 230.0 * derinlik
    gorus = max(16.0, gorus)
    egri = bukum * 1.15

    im = Image.new("RGB", (G, Y), GOK)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    zc = -10.0                      # cim de seritlere bolunur (sis dogru calissin)
    while zc < 240:
        s.yuzey([[-200, 0, zc], [200, 0, zc], [200, 0, zc + 12], [-200, 0, zc + 12]],
                CIM, katman=0)
        zc += 12.0
    global _vy
    _vy = (globals().get("_vy", 0.0) + 0.60) % 9.0

    adim = 2.6
    z = -40.0
    while z < 185:
        z2 = z + adim
        x1, x2 = _merkez_x(z, egri), _merkez_x(z2, egri)
        s.yuzey([[x1 - 3.9, 0.01, z], [x1 + 3.9, 0.01, z],
                 [x2 + 3.9, 0.01, z2], [x2 - 3.9, 0.01, z2]], ASFALT3, katman=1)
        for yan in (-1, 1):
            s.yuzey([[x1 + yan * 3.9, 0.02, z], [x1 + yan * 3.74, 0.02, z],
                     [x2 + yan * 3.74, 0.02, z2], [x2 + yan * 3.9, 0.02, z2]],
                    (208, 208, 202), katman=2)
        z = z2
    for i in range(-5, 24):                               # kesikli orta cizgi
        z0 = i * 9.0 - _vy
        if z0 < -38:
            continue
        z1 = z0 + 4.0
        x1, x2 = _merkez_x(z0, egri), _merkez_x(z1, egri)
        s.yuzey([[x1 - 0.11, 0.02, z0], [x1 + 0.11, 0.02, z0],
                 [x2 + 0.11, 0.02, z1], [x2 - 0.11, 0.02, z1]], (212, 212, 206), katman=2)
    for i in range(-4, 22):                               # kenar dubalari
        z0 = i * 9.0 - _vy
        if z0 < -36:
            continue
        for yan in (-1, 1):
            x = _merkez_x(z0, egri) + yan * 4.6
            s.kutu([x, 0.45, z0], [0.10, 0.90, 0.10], (150, 155, 150), katman=3)
            s.kutu([x, 0.80, z0], [0.13, 0.16, 0.12],
                   TURUNCU if yan > 0 else KREM, katman=3)

    # Gorus mesafesini kapatan ic taraf tepesi: kaybolus noktasini yaratir
    tx = _merkez_x(gorus + 10, egri) + (-1 if egri < 0 else 1) * 10.0
    s.kutu([tx, 5.0, gorus + 12], [26, 10.0, 16], (22, 30, 24), katman=3)

    # Motosiklet sahnede: viraja giren surucuyu ARKADAN gormek konuyu
    # seviye POV'dan cok daha iyi anlatiyor. Seviye kamerada yakin asfalt
    # karenin %60'ini yutuyordu.
    mz = 7.0
    mx = _merkez_x(mz, egri) - 1.1
    yon = _egim(mz, egri)
    yatis = -yon * 1.5                       # viraja yatis
    R = donus([0, 1, 0], yon) @ donus([0, 0, 1], yatis)
    model, _ = motosiklet(0.0)
    s.ekle(model, R=R, t=[mx, 0.0, mz])

    goz = np.array([_merkez_x(-6, egri) - 1.5, 3.05, -6.0])
    bak = np.array([_merkez_x(34, egri) - 0.9, 1.05, 34.0])
    kamera = Kamera(goz, bak, G, Y, fov=52)
    s.ciz(d, kamera, GOK)

    # --- kaybolus noktasi isareti (3B noktanin ekrandaki yeri) ------------
    nk = np.array([[_merkez_x(gorus, egri), 0.9, gorus]])
    kn = kamera.kameraya(nk)
    if kn[0, 2] > 0.3:
        mx, my = kamera.ekrana(kn)[0]
        mx, my = float(np.clip(mx, 90, G - 90)), float(np.clip(my, 260, 1300))
        rr = int(34 * (1.0 + 0.12 * math.sin(t * 5)))
        d.ellipse([mx - rr, my - rr, mx + rr, my + rr], outline=renk, width=7)
        for dx, dy in ((-1, 0), (1, 0), (0, -1)):
            d.line([mx + dx * (rr + 20), my + dy * (rr + 20),
                    mx + dx * (rr - 6), my + dy * (rr - 6)], fill=renk, width=5)
        f = s2.font(40)
        tw = d.textlength(etiket, font=f)
        ex = min(max(mx - tw / 2 - 26, 40), G - tw - 66)
        ey = my + 56
        d.rounded_rectangle([ex, ey, ex + tw + 52, ey + 64], 14,
                            fill=(0, 0, 0, 175), outline=renk, width=4)
        s2.yazi(d, (ex + 26, ey + 11), etiket, 40, renk)
        d.line([(G / 2, Y - 90), (mx, my)], fill=(255, 255, 255, 40), width=5)

    if engel:                                              # hedef sabitlemesi
        for nokta, cizim in (([_merkez_x(30, egri) - 2.2, 0.05, 30.0], "engel"),
                             ([_merkez_x(30, egri) + 2.0, 1.2, 30.0], "bosluk")):
            kn = kamera.kameraya(np.array([nokta]))
            if kn[0, 2] <= 0.3:
                continue
            px, py = kamera.ekrana(kn)[0]
            if cizim == "engel":
                d.ellipse([px - 110, py - 34, px + 110, py + 34], fill=(74, 66, 56))
                d.line([px - 86, py - 62, px + 86, py + 56], fill=KIRMIZI, width=13)
                d.line([px + 86, py - 62, px - 86, py + 56], fill=KIRMIZI, width=13)
            else:
                d.line([(px, py + 150), (px, py - 20)], fill=YESIL, width=11)
                d.polygon([(px - 30, py - 16), (px + 30, py - 16), (px, py - 76)], fill=YESIL)
    return im


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="AAE 3 boyutlu sahne uretici")
    ap.add_argument("--sahne", choices=("fren", "viraj"), required=True)
    ap.add_argument("--sure", type=float, default=60.0)
    ap.add_argument("--fazlar", default="")
    ap.add_argument("--cikti", default=None)
    ap.add_argument("--sessiz", action="store_true")
    args = ap.parse_args()

    s2.fazlari_ayarla(args.fazlar)
    cikti = args.cikti or f"videos/sahne3b_{args.sahne}.mp4"
    os.makedirs(os.path.dirname(cikti) or ".", exist_ok=True)
    cizer = kare_fren3b if args.sahne == "fren" else (lambda t: kare_viraj3b(t, args.sure))
    toplam = int(args.sure * FPS)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        ses_yolu = tmp.name
    try:
        if not args.sessiz:
            print(">> Motor sesi sentezleniyor")
            s2.wav_yaz(ses_yolu, s2.motor_sesi(args.sure, args.sahne))
        komut = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                 "-s", f"{G}x{Y}", "-r", str(FPS), "-i", "-"]
        if not args.sessiz:
            komut += ["-i", ses_yolu]
        komut += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p"]
        if not args.sessiz:
            komut += ["-c:a", "aac", "-b:a", "160k", "-ac", "2", "-shortest"]
        komut += ["-movflags", "+faststart", cikti]

        print(f">> {args.sahne} sahnesi (3B): {toplam} kare")
        p = subprocess.Popen(komut, stdin=subprocess.PIPE)
        for k in range(toplam):
            p.stdin.write(cizer(k / FPS).tobytes())
            if k % (FPS * 10) == 0 and k:
                print(f"   ... {k // FPS} sn")
        p.stdin.close()
        if p.wait() != 0:
            raise SystemExit("ffmpeg hata verdi")
    finally:
        if os.path.exists(ses_yolu):
            os.unlink(ses_yolu)
    print(f"TAMAM ✓  {cikti} ({os.path.getsize(cikti) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
