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
from uc_boyut import Kamera, Sahne, donus, isik_ayarla   # noqa: E402
import sahne_uret as s2                              # ses + 2B yardimcilar  # noqa: E402

G, Y, FPS = s2.G, s2.Y, s2.FPS
GOK = (13, 18, 26)
ASFALT3 = (68, 72, 78)
CIM = (30, 40, 32)
TURUNCU, KREM, MAVI, KIRMIZI, YESIL = s2.TURUNCU, s2.KREM, s2.MAVI, s2.KIRMIZI, s2.YESIL
LASTIK = (26, 26, 28)
JANT = (205, 170, 85)
GOVDE = (58, 70, 84)
KAMERA_MODU = "yan"       # yan | kask | takip | degisken
FREN_SERIT = 2.0          # fren sahnesinde motosikletin serit ici konumu (m)
GUNDUZ = False

# Gunduz paleti: gokyuzu acik, sis cok daha geride baslar ki UZAK secilir kalsin.
GOK_GUNDUZ = (150, 188, 222)
CIM_GUNDUZ = (94, 130, 78)
ASFALT_GUNDUZ = (124, 128, 134)


def _palet():
    """Sahne renklerini ve isigi gunduz/gece durumuna gore ayarlar."""
    if GUNDUZ:
        isik_ayarla(yon=[0.30, 0.94, -0.16], ortam=0.64, sis=(120, 520))
        return GOK_GUNDUZ, CIM_GUNDUZ, ASFALT_GUNDUZ
    isik_ayarla(yon=[0.45, 0.82, -0.35], ortam=0.42, sis=(22, 95))
    return GOK, CIM, ASFALT3
MONT = (96, 112, 130)


# ---------------------------------------------------------------------------
#  Motosiklet modeli (yerel: X yan, Y yukari, Z ileri; orijin yerde, aks arasi)
# ---------------------------------------------------------------------------
DISK = (168, 176, 184)
KROM = (196, 206, 214)


def _tekerlek(s, z, aci, yaricap=0.31, disk=True):
    """aci: tekerlegin donme acisi (radyan). Daha once sabit 0 geciliyordu,
    bu yuzden tekerlekler hic donmuyordu."""
    s.silindir([-0.075, yaricap, z], [0.075, yaricap, z], yaricap, LASTIK, segment=20)
    s.silindir([-0.085, yaricap, z], [0.085, yaricap, z], yaricap * 0.72, (34, 34, 36),
               segment=18)                                        # lastik yanagi
    s.silindir([-0.07, yaricap, z], [0.07, yaricap, z], yaricap * 0.50, (44, 44, 48),
               segment=16)                                        # jant tabani
    R = donus([1, 0, 0], aci)
    for i in range(6):                                            # jant kollari
        a = 2 * math.pi * i / 6
        yon = np.array([0.0, math.cos(a), math.sin(a)])
        s.kutu([0, yaricap, z] + (R @ yon) * yaricap * 0.33,
               [0.085, yaricap * 0.62, 0.05], JANT,
               R=R @ donus([1, 0, 0], -a))
    s.silindir([-0.045, yaricap, z], [0.045, yaricap, z], 0.055, KROM, segment=10)  # gobek
    if disk:
        for yan in (-1, 1):                                       # fren diski
            s.silindir([yan * 0.10, yaricap, z], [yan * 0.115, yaricap, z],
                       yaricap * 0.62, DISK, segment=18)
        s.kutu([0.13, yaricap + 0.19, z - 0.03], [0.07, 0.13, 0.10], TURUNCU)  # kaliper
        s.kutu([-0.13, yaricap + 0.19, z - 0.03], [0.07, 0.13, 0.10], TURUNCU)


def motosiklet(fren, tekerlek_aci=0.0):
    """fren 0-1: catal cokmesi + surucunun one yuklenmesi."""
    s = Sahne()
    cokme = 0.085 * fren
    arka_z, on_z = -0.70, 0.70

    # --- sasi / motor -----------------------------------------------------
    s.kutu([0.095, 0.45, arka_z + 0.33], [0.05, 0.10, 0.80], (62, 72, 84))      # salincak
    s.kutu([-0.095, 0.45, arka_z + 0.33], [0.05, 0.10, 0.80], (62, 72, 84))
    s.silindir([0.0, 0.52, -0.52], [0.0, 0.86, -0.30], 0.045, (190, 70, 60))     # amortisor
    s.silindir([0.11, 0.31, arka_z], [0.11, 0.31, arka_z], 0.12, (60, 60, 64))   # disli
    for yan in (0.105, -0.105):                                                  # zincir
        s.kutu([yan, 0.40, arka_z + 0.34], [0.02, 0.025, 0.72], (96, 100, 104))
    s.kutu([0, 0.55, -0.02], [0.33, 0.44, 0.58], (72, 82, 94))                   # motor
    s.kutu([0, 0.62, 0.26], [0.30, 0.34, 0.10], (108, 116, 124))                 # radyator
    s.kutu([0, 0.33, 0.02], [0.30, 0.14, 0.46], (58, 64, 72))                    # karter
    s.kutu([0, 0.84, 0.10], [0.30, 0.26, 0.66], TURUNCU)                         # depo
    s.kutu([0, 0.95, 0.10], [0.22, 0.06, 0.52], (255, 128, 80))                  # depo ustu
    s.kutu([0, 0.82, -0.44], [0.25, 0.10, 0.52], (28, 28, 30))                   # sele
    s.kutu([0, 0.88, -0.76], [0.21, 0.13, 0.30], (28, 28, 30))                   # kuyruk
    s.kutu([0, 0.89, -0.91], [0.15, 0.07, 0.05], KIRMIZI)                        # stop
    s.kutu([0, 0.74, -0.95], [0.16, 0.11, 0.02], (222, 222, 216))                # plaka
    s.silindir([0.11, 0.44, -0.12], [0.16, 0.48, -0.62], 0.033, (150, 158, 164)) # egzoz borusu
    s.silindir([0.16, 0.48, -0.62], [0.18, 0.50, -0.93], 0.058, (124, 132, 140)) # susturucu

    # --- on takim ---------------------------------------------------------
    ucgen_y = 0.98 - cokme
    for yan in (-1, 1):
        s.silindir([yan * 0.105, 0.31, on_z], [yan * 0.095, ucgen_y, on_z - 0.11],
                   0.040, JANT)                                                  # catal
    s.kutu([0, ucgen_y + 0.03, on_z - 0.13], [0.24, 0.08, 0.13], (62, 72, 84))   # ucgen
    s.kutu([0, ucgen_y + 0.12, on_z - 0.22], [0.17, 0.09, 0.05], (24, 26, 30),
           R=donus([1, 0, 0], 0.5))                                              # gosterge govdesi
    s.kutu([0, ucgen_y + 0.133, on_z - 0.195], [0.14, 0.06, 0.015], (30, 150, 180),
           R=donus([1, 0, 0], 0.5))                                              # ekran
    s.kutu([0, 0.62 - cokme, on_z + 0.06], [0.17, 0.05, 0.48], TURUNCU)         # camurluk
    s.kutu([0, 0.98 - cokme, on_z + 0.12], [0.26, 0.24, 0.14], (46, 50, 56))    # far govdesi
    s.kutu([0, 0.98 - cokme, on_z + 0.195], [0.22, 0.19, 0.02], KREM)           # far cami
    s.kutu([0, 1.09 - cokme, on_z + 0.02], [0.19, 0.10, 0.03], (146, 176, 196),
           R=donus([1, 0, 0], 0.45))                                             # on cam
    # Gidon: daha UZUN ve disa dogru — kask kamerasindan gorulebilsin
    gid_y, gid_z = 1.07 - cokme, on_z - 0.16
    s.silindir([-0.42, gid_y, gid_z], [0.42, gid_y, gid_z], 0.022, KROM)
    for yan in (-1, 1):
        s.silindir([yan * 0.26, gid_y, gid_z], [yan * 0.42, gid_y, gid_z + 0.03],
                   0.032, (32, 32, 34))                                          # tutamak
        s.kutu([yan * 0.455, gid_y, gid_z + 0.03], [0.05, 0.05, 0.05], KROM)     # agirlik
        s.silindir([yan * 0.30, gid_y, gid_z + 0.02],
                   [yan * 0.40, gid_y - 0.01, gid_z + 0.14], 0.012, (190, 190, 190))
        s.silindir([yan * 0.34, gid_y + 0.02, gid_z],                             # ayna kolu
                   [yan * 0.46, gid_y + 0.30, gid_z - 0.02], 0.016, (40, 40, 44))
        s.kutu([yan * 0.47, gid_y + 0.33, gid_z - 0.02], [0.05, 0.13, 0.17],
               (70, 86, 104), R=donus([0, 1, 0], yan * 0.35))                    # ayna

    # --- surucu -----------------------------------------------------------
    one = 0.12 * fren
    omuz_y, omuz_z = 1.50 - 0.10 * fren, -0.12 + one
    kalca_n = np.array([0.0, 1.02, -0.40])
    omuz_n = np.array([0.0, omuz_y, omuz_z])
    s.kure(kalca_n, 0.19, MONT, dilim=12, halka=7)
    s.silindir(kalca_n, omuz_n, 0.185, MONT, segment=14)
    s.kure(omuz_n, 0.19, MONT, dilim=12, halka=7)
    for yan in (-1, 1):
        s.silindir([yan * 0.19, omuz_y, omuz_z], [yan * 0.30, gid_y + 0.03, gid_z],
                   0.055, MONT)                                                  # kol
        s.kure([yan * 0.32, gid_y + 0.02, gid_z + 0.01], 0.055, (34, 34, 36))    # eldiven
        s.silindir([yan * 0.17, 0.98, -0.34], [yan * 0.25, 0.64, 0.10], 0.075, MONT)
        s.silindir([yan * 0.25, 0.64, 0.10], [yan * 0.23, 0.36, -0.02], 0.065, MONT)
        s.kutu([yan * 0.23, 0.30, 0.02], [0.10, 0.09, 0.26], (26, 26, 28))       # bot
    boyun = omuz_n + np.array([0.0, 0.13, 0.05])
    s.silindir(omuz_n, boyun, 0.085, (70, 80, 92), segment=10)
    kask_n = np.array([0.0, omuz_y + 0.27, omuz_z + 0.07])
    s.kure(kask_n, 0.148, KREM, dilim=16, halka=10)
    s.kutu([0, kask_n[1] - 0.01, kask_n[2] + 0.12], [0.18, 0.11, 0.06], (52, 64, 78))
    s.kutu([0, kask_n[1] + 0.12, kask_n[2] + 0.01], [0.17, 0.05, 0.17], TURUNCU)

    _tekerlek(s, arka_z, tekerlek_aci)
    _tekerlek(s, on_z, tekerlek_aci)
    return s, cokme, kask_n


def _fren_kamera(t, fren, kask_n, yat, pivot):
    """kamera modu: yan (3/4) | kask (kask kamerasi) | degisken (donusumlu)."""
    mod = KAMERA_MODU
    if mod == "degisken":
        mod = "kask" if int(max(0.0, t - 4.0) // 7.5) % 2 == 1 else "yan"
    if mod == "kask":
        # Gercek kask kamerasi gibi: biraz asagi bakar, genis acilidir. Daha
        # dar aci ve yatay bakisla gidon kadrajin disinda kaliyordu.
        kask_d = yat @ kask_n + (pivot - yat @ pivot) + np.array([FREN_SERIT, 0.0, 0.0])
        goz = kask_d + np.array([0.0, 0.05, 0.06])
        ileri = yat @ np.array([0.0, -0.28, 1.0])
        return Kamera(goz, goz + ileri * 12.0, G, Y, fov=76), mod
    # Motosiklet sag seritte (x = FREN_SERIT); kamera da onunla kayar, yoksa
    # motosiklet kadrajin disinda kaliyor.
    return Kamera([FREN_SERIT + 2.72 + 0.18 * math.sin(t * 0.21),
                   1.94 + 0.08 * math.sin(t * 0.13),
                   -3.45 + 0.24 * math.cos(t * 0.17)],
                  [FREN_SERIT + 0.02, 0.78, 0.10], G, Y, fov=53), mod


def kare_fren3b(t):
    hiz, fren = s2.fren_evre(t)
    gok, cim, asfalt = _palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    global _yol_s, _tek_aci
    _yol_s = (globals().get("_yol_s", 0.0) + hiz * 0.62) % 8.0
    _tek_aci = (globals().get("_tek_aci", 0.0) + hiz * 0.45) % (2 * math.pi)

    z = -30.0
    while z < 150:
        z2 = z + 6.0
        s.yuzey([[-60, 0, z], [60, 0, z], [60, 0, z2], [-60, 0, z2]], cim, katman=0)
        s.yuzey([[-4.2, 0.01, z], [4.2, 0.01, z], [4.2, 0.01, z2], [-4.2, 0.01, z2]],
                asfalt, katman=1)
        for yan in (-1, 1):
            s.yuzey([[yan * 4.0, 0.02, z], [yan * 3.86, 0.02, z],
                     [yan * 3.86, 0.02, z2], [yan * 4.0, 0.02, z2]],
                    (205, 205, 200), katman=2)
        z = z2
    for i in range(-3, 22):
        z = i * 8.0 - _yol_s
        s.yuzey([[-0.11, 0.02, z], [0.11, 0.02, z], [0.11, 0.02, z + 3.6],
                 [-0.11, 0.02, z + 3.6]], (210, 210, 205), katman=2)
    for i in range(-2, 16):
        z = i * 11.0 - _yol_s * 0.92
        for yan in (-1, 1):
            h = 5 + ((i * 7 + (yan + 1) * 3) % 9) * 1.7
            s.kutu([yan * (7.5 + (i % 3) * 1.6), h / 2, z + 4], [5.0, h, 6.5],
                   (26, 32, 42) if not GUNDUZ else (86, 96, 112), katman=3)

    model, _, kask_n = motosiklet(fren, _tek_aci)
    yat = donus([1, 0, 0], 0.085 * fren)
    pivot = np.array([0, 0.31, 0.70])
    s.ekle(model, R=yat,
           t=pivot - yat @ pivot + np.array([FREN_SERIT, 0.0, 0.0]))

    kamera, mod = _fren_kamera(t, fren, kask_n, yat, pivot)
    s.ciz(d, kamera, gok)

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
    if mod == "kask":
        s2.yazi(d, (G - 320, 636), "KASK KAMERASI", 26, TURUNCU)
    return im


# ---------------------------------------------------------------------------
#  VIRAJ (surucu gozunden, gercek 3B yol)
# ---------------------------------------------------------------------------
# Orta cizgi parabolik: x = k*z^2, k = egri*0.006. Virajin yaricapi R = 1/(2k):
# egri 0.35 -> R ~ 240 m (genis kavis), egri 2.0 -> R ~ 42 m (keskin viraj).
# Eski katsayi (0.0019) her virajı otoyol kavisine cevirir, keskin viraj cikmazdi.
VIRAJ_K = 0.006


def _merkez_x(z, egri):
    """Yolun orta cizgisinin mesafeye gore yanal kaymasi."""
    return egri * (z ** 2) * VIRAJ_K


def _egim(z, egri):
    """Orta cizginin o noktadaki yonu (radyan)."""
    return math.atan(egri * 2 * z * VIRAJ_K)


def _limit_mesafe(goz_x, egri, ic, azami=150.0):
    """Gercek limit noktasi: yolun hala gorunen EN UZAK noktasi. Bakis cizgisi
    virajin IC tarafindaki yamaci kesiyorsa oradan otesi gorunmez.
    Onceki surumde bu bir parametreyle elle kaydiriliyordu — bu yuzden tepe
    sahnede ileri geri yuruyordu."""
    d, son = 6.0, 6.0
    while d < azami:
        px = _merkez_x(d, egri)
        kapali = False
        for z in np.linspace(1.0, d * 0.97, 26):
            x_cizgi = goz_x + (px - goz_x) * (z / d)
            if (x_cizgi - (_merkez_x(z, egri) + ic * 4.3)) * ic > 0:
                kapali = True
                break
        if kapali:
            break
        son = d
        d += 2.0
    return son


def _yamac(s, egri, ic, kayma, renk, ust_renk):
    """Virajin ic tarafini izleyen SUREKLI sed. Sahneye sabit cakili durur,
    yolla birlikte akar; kaybolus noktasini yaratan sey budur."""
    z = -12.0
    while z < 150:
        z2 = z + 7.0
        for zz, zn in ((z, z2),):
            x1 = _merkez_x(zz, egri) + ic * 4.5
            x2 = _merkez_x(zn, egri) + ic * 4.5
            h = 9.5
            w = ic * 13.0
            s.yuzey([[x1, 0, zz], [x1 + w, h, zz], [x2 + w, h, zn], [x2, 0, zn]],
                    renk, katman=3)                                  # egim
            s.yuzey([[x1 + w, h, zz], [x1 + w * 2.4, h + 1.5, zz],
                     [x2 + w * 2.4, h + 1.5, zn], [x2 + w, h, zn]],
                    ust_renk, katman=3)                              # tepe duzlugu
        z = z2


def _tepe(s, x, z, genislik, derinlik, yukseklik, renk):
    """Sirt seklinde tepe: kutu kullaninca gunduzde dumduz bir pano gibi
    goruluyordu, gercek bir tepe gibi egimli olmali."""
    x0, x1 = x - genislik / 2, x + genislik / 2
    z0, z1 = z - derinlik / 2, z + derinlik / 2
    xm = x
    s.yuzey([[x0, 0, z0], [xm, yukseklik, z0], [xm, yukseklik, z1], [x0, 0, z1]], renk)
    s.yuzey([[x1, 0, z0], [x1, 0, z1], [xm, yukseklik, z1], [xm, yukseklik, z0]], renk)
    s.yuzey([[x0, 0, z0], [x1, 0, z0], [xm, yukseklik, z0]], renk)
    s.yuzey([[x0, 0, z1], [xm, yukseklik, z1], [x1, 0, z1]], renk)


def _agac(s, x, z, h, govde, yaprak):
    s.kutu([x, h * 0.22, z], [0.26, h * 0.44, 0.26], govde)
    tepe_y = h * 0.42
    for i in range(4):                       # dort yuzlu basit tac
        a0 = math.pi / 2 * i
        a1 = a0 + math.pi / 2
        s.yuzey([[x + math.cos(a0) * 0.95, tepe_y, z + math.sin(a0) * 0.95],
                 [x + math.cos(a1) * 0.95, tepe_y, z + math.sin(a1) * 0.95],
                 [x, h, z]], yaprak)


def kare_viraj3b(t, toplam=55.0):
    if s2.VIRAJ_FAZLAR:
        derinlik, bukum, (etiket, renk) = s2.viraj_evre_fazli(t, toplam)
        engel = etiket.startswith("ENGELE")
    else:
        derinlik, bukum, (etiket, renk) = s2.viraj_evre(t)
        engel = (t % s2.VIRAJ_DONGU) >= 11.0

    # derinlik -> EGRILIK. Viraj keskinlestikce kaybolus noktasi kendiliginden
    # yaklasir; artik elle kaydirilan bir "gorus mesafesi" yok.
    egri = -(0.30 + derinlik * 5.6)          # 0.08 -> 0.75 ;  0.34 -> 2.2
    ic = -1 if egri < 0 else 1

    gok, cim, asfalt = _palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    zc = -10.0                      # cim de seritlere bolunur (sis dogru calissin)
    while zc < 240:
        s.yuzey([[-200, 0, zc], [200, 0, zc], [200, 0, zc + 12], [-200, 0, zc + 12]],
                cim, katman=0)
        zc += 12.0
    global _vy
    _vy = (globals().get("_vy", 0.0) + 0.60) % 9.0

    adim = 2.6
    z = -40.0
    while z < 185:
        z2 = z + adim
        x1, x2 = _merkez_x(z, egri), _merkez_x(z2, egri)
        s.yuzey([[x1 - 3.9, 0.01, z], [x1 + 3.9, 0.01, z],
                 [x2 + 3.9, 0.01, z2], [x2 - 3.9, 0.01, z2]], asfalt, katman=1)
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
            s.kutu([x, 0.45, z0], [0.10, 0.90, 0.10],
                   (225, 228, 225) if GUNDUZ else (150, 155, 150), katman=3)
            s.kutu([x, 0.80, z0], [0.13, 0.16, 0.12],
                   TURUNCU if yan > 0 else KREM, katman=3)

    _yamac(s, egri, ic, _vy,
           (72, 104, 62) if GUNDUZ else (24, 34, 26),
           (96, 128, 80) if GUNDUZ else (28, 40, 30))

    # Motosiklet sahnede: viraja giren surucuyu ARKADAN gormek konuyu
    # seviye POV'dan cok daha iyi anlatiyor. Seviye kamerada yakin asfalt
    # karenin %60'ini yutuyordu.
    # SERIT ICI KONUM: yol +-3.9 m, orta cizgi 0'da -> sag serit 0..3.9.
    # Orta cizginin uzerinde gitmek yanlisti. Konum ayrica viraja gore degisir:
    # sola donen virajda sagda durmak gorusu acar, saga donende tersi.
    # 1.0 = seridin solu, 1.95 = ortasi, 2.9 = sagi.
    mz = 7.0
    hedef_serit = 1.95 - np.sign(egri) * 0.95 if abs(egri) > 0.05 else 1.95
    global _serit
    _serit = globals().get("_serit", 1.95)
    _serit += (hedef_serit - _serit) * 0.022          # yumusak gecis
    mx = _merkez_x(mz, egri) + _serit
    yon = _egim(mz, egri)
    yatis = -yon * 1.5                       # viraja yatis
    R = donus([0, 1, 0], yon) @ donus([0, 0, 1], yatis)
    global _vtek
    _vtek = (globals().get("_vtek", 0.0) + 0.42) % (2 * math.pi)
    model, _, _ = motosiklet(0.0, _vtek)
    s.ekle(model, R=R, t=[mx, 0.0, mz])

    for i in range(-2, 16):                               # yol kenari agaclari
        za = i * 13.0 - _vy * 0.8
        if za < -20:
            continue
        for yan in (-1, 1):
            xa = _merkez_x(za, egri) + yan * (9.0 + (i % 3) * 2.5)
            _agac(s, xa, za, 5.0 + ((i * 5 + yan) % 4) * 1.4,
                  (84, 66, 48) if GUNDUZ else (34, 30, 26),
                  (54, 104, 52) if GUNDUZ else (24, 38, 26))
    if GUNDUZ:                                            # ufuktaki daglar
        for i in range(7):
            mx2 = -220 + i * 78
            _tepe(s, mx2, 330 + (i % 3) * 40, 150, 90, 34 + (i % 4) * 11,
                  (104, 132, 140))

    goz = np.array([_merkez_x(-6, egri) + _serit + 0.4, 3.05, -6.0])
    bak = np.array([_merkez_x(34, egri) + _serit * 0.55, 1.05, 34.0])
    kamera = Kamera(goz, bak, G, Y, fov=52)
    s.ciz(d, kamera, gok)

    # --- kaybolus noktasi isareti (3B noktanin ekrandaki yeri) ------------
    limit = _limit_mesafe(_serit, egri, ic)
    nk = np.array([[_merkez_x(limit, egri), 0.9, limit]])
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
        if engel:
            # Engel ve kacis oku kaybolus noktasinin hemen altinda beliriyor;
            # etiket orada kalirsa kirmizi carpi yaziyi kesiyordu.
            ex, ey = (G - tw - 52) / 2, 268
        else:
            ex = min(max(mx - tw / 2 - 26, 40), G - tw - 66)
            ey = my + 56
        d.rounded_rectangle([ex, ey, ex + tw + 52, ey + 64], 14,
                            fill=(0, 0, 0, 175), outline=renk, width=4)
        s2.yazi(d, (ex + 26, ey + 11), etiket, 40, renk)
        d.line([(G / 2, Y - 90), (mx, my)], fill=(255, 255, 255, 40), width=5)

    if engel:                                              # hedef sabitlemesi
        for nokta, cizim in (([_merkez_x(34, egri) + 3.0, 0.05, 34.0], "engel"),
                             ([_merkez_x(34, egri) + 0.9, 1.2, 34.0], "bosluk")):
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
    ap.add_argument("--kamera", default="yan",
                    choices=("yan", "kask", "takip", "degisken"))
    ap.add_argument("--gunduz", default="")
    args = ap.parse_args()

    global KAMERA_MODU, GUNDUZ
    KAMERA_MODU = args.kamera
    GUNDUZ = str(args.gunduz).lower() in ("1", "true", "evet", "yes")
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
