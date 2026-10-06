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
from sahne_uret import yumusak                       # noqa: E402

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
DISK = (104, 112, 120)
KROM = (196, 206, 214)


def _tekerlek(s, z, aci, yaricap=0.31, disk=True, on=True):
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
    if disk:
        # Disk daha KUCUK ve KOYU; ayrica arka tekerlekte tek disk var ve o da
        # kameranin ters tarafinda. Onceki parlak buyuk disk janti kapatiyor,
        # tekerlege bir sey saplanmis gibi gorunuyordu.
        yanlar = (-1, 1) if on else (-1,)
        for yan in yanlar:
            s.silindir([yan * 0.098, yaricap, z], [yan * 0.112, yaricap, z],
                       yaricap * (0.54 if on else 0.44), DISK, segment=18)
            s.kutu([yan * 0.125, yaricap + 0.17, z - 0.03], [0.055, 0.12, 0.09], TURUNCU)
    s.silindir([-0.05, yaricap, z], [0.05, yaricap, z], 0.062, KROM, segment=10)  # gobek


def motosiklet(fren, tekerlek_aci=0.0, direksiyon=0.0):
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
    # Egzoz arka tekerlegin YANINDAN gecer. Onceki guzergah tekerlek duzlemine
    # cok yakindi (x~0.17) ve aks hizasindaydi; lastige saplanmis gibi duruyordu.
    s.silindir([0.10, 0.40, 0.02], [0.19, 0.46, -0.30], 0.032, (150, 158, 164))  # egzoz borusu
    s.silindir([0.19, 0.46, -0.30], [0.26, 0.58, -0.58], 0.034, (150, 158, 164))
    s.silindir([0.26, 0.58, -0.58], [0.28, 0.62, -1.00], 0.065, (124, 132, 140)) # susturucu
    s.silindir([0.28, 0.62, -1.00], [0.285, 0.62, -1.03], 0.052, (40, 40, 44))   # cikis

    # --- on takim (direksiyonla birlikte doner) ---------------------------
    # Kontra dersi icin on takim AYRI bir sahnede kurulur: catal, teker,
    # camurluk, far, cam, gosterge, gidon ve aynalar birlikte donmeli.
    onk = Sahne()
    ucgen_y = 0.98 - cokme
    for yan in (-1, 1):
        onk.silindir([yan * 0.105, 0.31, on_z], [yan * 0.095, ucgen_y, on_z - 0.11],
                   0.040, JANT)                                                  # catal
    onk.kutu([0, ucgen_y + 0.03, on_z - 0.13], [0.24, 0.08, 0.13], (62, 72, 84))   # ucgen
    onk.kutu([0, ucgen_y + 0.12, on_z - 0.22], [0.17, 0.09, 0.05], (24, 26, 30),
           R=donus([1, 0, 0], 0.5))                                              # gosterge govdesi
    onk.kutu([0, ucgen_y + 0.133, on_z - 0.195], [0.14, 0.06, 0.015], (30, 150, 180),
           R=donus([1, 0, 0], 0.5))                                              # ekran
    onk.kutu([0, 0.62 - cokme, on_z + 0.06], [0.17, 0.05, 0.48], TURUNCU)         # camurluk
    onk.kutu([0, 0.98 - cokme, on_z + 0.12], [0.26, 0.24, 0.14], (46, 50, 56))    # far govdesi
    onk.kutu([0, 0.98 - cokme, on_z + 0.195], [0.22, 0.19, 0.02], KREM)           # far cami
    onk.kutu([0, 1.09 - cokme, on_z + 0.02], [0.19, 0.10, 0.03], (146, 176, 196),
           R=donus([1, 0, 0], 0.45))                                             # on cam
    # Gidon: daha UZUN ve disa dogru — kask kamerasindan gorulebilsin
    gid_y, gid_z = 1.07 - cokme, on_z - 0.16
    onk.silindir([-0.42, gid_y, gid_z], [0.42, gid_y, gid_z], 0.022, KROM)
    for yan in (-1, 1):
        onk.silindir([yan * 0.26, gid_y, gid_z], [yan * 0.42, gid_y, gid_z + 0.03],
                   0.032, (32, 32, 34))                                          # tutamak
        onk.kutu([yan * 0.455, gid_y, gid_z + 0.03], [0.05, 0.05, 0.05], KROM)     # agirlik
        onk.silindir([yan * 0.30, gid_y, gid_z + 0.02],
                   [yan * 0.40, gid_y - 0.01, gid_z + 0.14], 0.012, (190, 190, 190))
        onk.silindir([yan * 0.34, gid_y + 0.02, gid_z],                             # ayna kolu
                   [yan * 0.46, gid_y + 0.30, gid_z - 0.02], 0.016, (40, 40, 44))
        onk.kutu([yan * 0.47, gid_y + 0.33, gid_z - 0.02], [0.05, 0.13, 0.17],
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

    _tekerlek(s, arka_z, tekerlek_aci, on=False)
    _tekerlek(onk, on_z, tekerlek_aci, on=True)

    # Direksiyon ekseni ucgen klempten gecer; kucuk acilarda Y ekseni etrafinda
    # dondurmek yeterli dogrulukta.
    if abs(direksiyon) > 1e-4:
        eksen = np.array([0.0, 0.0, on_z - 0.13])
        R = donus([0, 1, 0], direksiyon)
        s.ekle(onk, R=R, t=eksen - R @ eksen)
    else:
        s.ekle(onk)
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
#  KONTRA (counter-steering) - onden gorunum
# ---------------------------------------------------------------------------
KONTRA_DONGU = 8.0          # ders adimlarinin ritmi (3. sn'den itibaren)
KONTRA_OFSET = 3.0


def kontra_evre(t):
    """(direksiyon, yatis, itis, yon) dondurur.
    yon: -1 sola, +1 saga. direksiyon + ise on teker SAGA bakar.
    Sola gitmek icin SOL gidon ileri itilir -> teker bir an SAGA doner."""
    gecen = max(0.0, t - KONTRA_OFSET)
    dongu = int(gecen // KONTRA_DONGU)
    u = (gecen % KONTRA_DONGU) / KONTRA_DONGU
    # Parite, 11. sn'de baslayan dongu SOLA olacak sekilde secildi:
    # 2. adim metni ("Sola gitmek icin SOL gidonu ileri it") o aralikta.
    yon = -1.0 if dongu % 2 == 1 else 1.0

    if u < 0.12:                                   # duz git
        return 0.0, 0.0, 0.0, yon
    if u < 0.26:                                   # ITIS: teker ters yone
        p = yumusak((u - 0.12) / 0.14)
        return -yon * 0.17 * p, -yon * 0.40 * (p ** 2), p, yon
    if u < 0.58:                                   # yatik seyir
        p = yumusak((u - 0.26) / 0.32)
        return (-yon * 0.17 * (1 - p) + yon * 0.05 * p), -yon * 0.40, 1.0 - p, yon
    if u < 0.76:                                   # duzeltme itisi
        p = yumusak((u - 0.58) / 0.18)
        return yon * (0.05 + 0.12 * p), -yon * 0.40 * (1 - p), -p, yon
    p = yumusak((u - 0.76) / 0.24)                 # duzeldi
    return yon * 0.17 * (1 - p), 0.0, 0.0, yon


def kare_kontra3b(t):
    gok, cim, asfalt = _palet()
    direksiyon, yatis, itis, yon = kontra_evre(t)
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    global _yol_k, _tek_k
    _yol_k = (globals().get("_yol_k", 0.0) + 0.58) % 8.0
    _tek_k = (globals().get("_tek_k", 0.0) + 0.42) % (2 * math.pi)

    z = -150.0
    while z < 60:
        z2 = z + 6.0
        s.yuzey([[-60, 0, z], [60, 0, z], [60, 0, z2], [-60, 0, z2]], cim, katman=0)
        s.yuzey([[-4.2, 0.01, z], [4.2, 0.01, z], [4.2, 0.01, z2], [-4.2, 0.01, z2]],
                asfalt, katman=1)
        for yan in (-1, 1):
            s.yuzey([[yan * 4.0, 0.02, z], [yan * 3.86, 0.02, z],
                     [yan * 3.86, 0.02, z2], [yan * 4.0, 0.02, z2]],
                    (205, 205, 200), katman=2)
        z = z2
    for i in range(-20, 9):
        z = i * 8.0 - _yol_k
        s.yuzey([[-0.11, 0.02, z], [0.11, 0.02, z], [0.11, 0.02, z + 3.6],
                 [-0.11, 0.02, z + 3.6]], (210, 210, 205), katman=2)
    for i in range(-14, 6):
        za = i * 12.0 - _yol_k * 0.9
        for yan in (-1, 1):
            _agac(s, yan * (8.5 + (i % 3) * 2.0), za, 5.0 + ((i * 5 + yan) % 4) * 1.3,
                  (84, 66, 48) if GUNDUZ else (34, 30, 26),
                  (54, 104, 52) if GUNDUZ else (24, 38, 26))
    if GUNDUZ:
        for i in range(6):
            _tepe(s, -200 + i * 86, -300 - (i % 3) * 40, 150, 90, 32 + (i % 4) * 10,
                  (104, 132, 140))

    gx = FREN_SERIT + yatis * 0.55                      # golge yatisla kayar
    golge = [[gx + 0.40 * math.cos(a), 0.012, 1.15 * math.sin(a)]
             for a in (math.pi * 2 * i / 10 for i in range(10))]
    s.yuzey(golge, (64, 74, 62) if GUNDUZ else (20, 25, 22), isiksiz=True, katman=2)

    model, _, _ = motosiklet(0.0, _tek_k, direksiyon)
    s.ekle(model, R=donus([0, 0, 1], yatis), t=[FREN_SERIT, 0.0, 0.0])

    # Motosiklet karenin ~%42'sini kaplasin: 1.85 m boy, 46 derece dikey aci
    # -> hedefe yaklasik 5.2 m mesafe. 7.4 m'de kucuk kaliyordu.
    # Kamera ARKADA: onden bakinca motosikletin solu ekranin sagina dusuyor,
    # "MOTOSIKLET SOLA" yazarken goruntu saga yatiyormus gibi okunuyordu.
    kamera = Kamera([FREN_SERIT + 0.95, 1.98, -4.9],
                    [FREN_SERIT + 0.05, 1.10, 0.6], G, Y, fov=44)
    s.ciz(d, kamera, gok)

    # --- 2B anlatim: itisin yonu ile yatisin yonu ayni karede --------------
    sol_itiliyor = (itis > 0.05 and yon < 0) or (itis < -0.05 and yon > 0)
    sag_itiliyor = (itis > 0.05 and yon > 0) or (itis < -0.05 and yon < 0)
    # Paneller ust banda toplanir (300-520), motosiklet 560'tan asagida kalir
    for etiket, aktif, x0 in (("SOL GİDON", sol_itiliyor, 62),
                              ("SAĞ GİDON", sag_itiliyor, G - 62 - 330)):
        renk = TURUNCU if aktif else (86, 92, 100)
        d.rounded_rectangle([x0, 300, x0 + 330, 392], 14,
                            fill=(0, 0, 0, 175 if aktif else 95),
                            outline=renk, width=5 if aktif else 3)
        s2.yazi(d, (x0 + 165, 310), etiket, 36, renk, ortala=True)
        s2.yazi(d, (x0 + 165, 350), "İTİLİYOR" if aktif else "—", 28, renk, ortala=True)

    kutular = []
    if abs(itis) > 0.05 and abs(direksiyon) > 0.03:
        kutular.append((f"ÖN TEKER {'SAĞA' if direksiyon > 0 else 'SOLA'}", TURUNCU))
    if abs(yatis) > 0.02:
        yon_ad = "SOLA" if yatis > 0 else "SAĞA"
        kutular.append((f"MOTOSİKLET {yon_ad} {int(abs(math.degrees(yatis)))}°", MAVI))
    for i, (metin, renk) in enumerate(kutular):
        gen = 470
        x0 = G / 2 - (len(kutular) * gen + (len(kutular) - 1) * 18) / 2 + i * (gen + 18)
        d.rounded_rectangle([x0, 418, x0 + gen, 500], 14,
                            fill=(0, 0, 0, 180), outline=renk, width=4)
        s2.yazi(d, (x0 + gen / 2, 432), metin, 34, renk, ortala=True)

    return im



# ---------------------------------------------------------------------------
#  GAZ (virajda gaz kontrolu) - havadan takip
# ---------------------------------------------------------------------------
GAZ_R = 42.0                 # viraj orta cizgi yaricapi (m)
GAZ_YARIM = 3.9              # yol yari genisligi

# Her faz: (gaz, serit_ofseti, yatis_carpani, etiket, renk)
# serit_ofseti: orta cizgiden disa dogru metre. Sag serit 0..3.9 arasi,
# 3.9'u gecmek seritten TASMAK demek.
GAZ_DURUM = {
    "fren":    (0.00, 1.9, 0.00, "FREN · DÜZ ÇİZGİDE", MAVI),
    "yatis":   (0.18, 2.7, 1.00, "YATIŞ", MAVI),
    "sabit":   (0.32, 1.9, 1.00, "SABİT GAZ", YESIL),
    "kesik":   (0.00, 5.3, 0.40, "GAZ KESİLDİ · DIŞARI TAŞIYOR", KIRMIZI),
    "duzelt":  (0.30, 2.2, 1.18, "İÇ GİDONA BAS", TURUNCU),
    "cikis":   (0.78, 3.0, 0.50, "GAZ AÇILIYOR", YESIL),
}
GAZ_FAZLAR = None


def gaz_fazlari_ayarla(metin):
    global GAZ_FAZLAR
    if not metin:
        GAZ_FAZLAR = [(0.0, "sabit")]
        return
    f = []
    for parca in metin.split(","):
        t_str, _, durum = parca.strip().partition(":")
        durum = durum.strip()
        if durum not in GAZ_DURUM:
            raise SystemExit(f"HATA: bilinmeyen gaz fazi '{durum}'")
        f.append((float(t_str), durum))
    GAZ_FAZLAR = sorted(f)


def gaz_evre(t, toplam):
    """Deger onceki fazin biraktigi yerden bu fazin hedefine suruklenir."""
    i, bas, bitis = 0, GAZ_FAZLAR[0][0], toplam
    for j, (b, _) in enumerate(GAZ_FAZLAR):
        if t >= b:
            i, bas = j, b
            bitis = GAZ_FAZLAR[j + 1][0] if j + 1 < len(GAZ_FAZLAR) else toplam
    durum = GAZ_FAZLAR[i][1]
    g1, o1, y1, etiket, renk = GAZ_DURUM[durum]
    g0, o0, y0 = GAZ_DURUM[GAZ_FAZLAR[i - 1][1]][:3] if i > 0 else (g1, o1, y1)
    p = yumusak((t - bas) / max(0.5, bitis - bas))
    return (g0 + (g1 - g0) * p, o0 + (o1 - o0) * p, y0 + (y1 - y0) * p,
            etiket, renk, durum)


def _gaz_konum(s, ofset):
    """s < 0 duz giris, s >= 0 daire. (konum, tegeti, disa_birim, sapma) verir."""
    if s < 0:
        return (np.array([GAZ_R + ofset, 0.0, s]), np.array([0.0, 0.0, 1.0]),
                np.array([1.0, 0.0, 0.0]), 0.0)
    th = s / GAZ_R
    disa = np.array([math.cos(th), 0.0, math.sin(th)])
    teget = np.array([-math.sin(th), 0.0, math.cos(th)])
    return (GAZ_R + ofset) * disa, teget, disa, th


def kare_gaz3b(t, toplam=55.0):
    gok, cim, asfalt = _palet()
    gaz, ofset, yatis_k, etiket, renk, durum = gaz_evre(t, toplam)
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    hiz_kmh = 44.0 + 30.0 * gaz
    global _gaz_s, _gaz_tek
    _gaz_s = globals().get("_gaz_s", -140.0) + (hiz_kmh / 3.6) / FPS
    if _gaz_s > 2 * math.pi * GAZ_R:
        _gaz_s -= 2 * math.pi * GAZ_R
    _gaz_tek = (globals().get("_gaz_tek", 0.0) + 0.5) % (2 * math.pi)

    # --- zemin, daire yol ve duz giris ------------------------------------
    s.yuzey([[-200, 0, -260], [200, 0, -260], [200, 0, 200], [-200, 0, 200]],
            cim, katman=0)
    N = 84
    for i in range(N):
        a0, a1 = 2 * math.pi * i / N, 2 * math.pi * (i + 1) / N
        for ri, ro, renk_y, kat in ((-GAZ_YARIM, GAZ_YARIM, asfalt, 1),
                                    (GAZ_YARIM - 0.16, GAZ_YARIM, (208, 208, 202), 2),
                                    (-GAZ_YARIM, -GAZ_YARIM + 0.16, (208, 208, 202), 2)):
            s.yuzey([[(GAZ_R + ri) * math.cos(a0), 0.01, (GAZ_R + ri) * math.sin(a0)],
                     [(GAZ_R + ro) * math.cos(a0), 0.01, (GAZ_R + ro) * math.sin(a0)],
                     [(GAZ_R + ro) * math.cos(a1), 0.01, (GAZ_R + ro) * math.sin(a1)],
                     [(GAZ_R + ri) * math.cos(a1), 0.01, (GAZ_R + ri) * math.sin(a1)]],
                    renk_y, katman=kat)
        if i % 3 == 0:                                   # kesikli orta cizgi
            s.yuzey([[(GAZ_R - 0.11) * math.cos(a0), 0.02, (GAZ_R - 0.11) * math.sin(a0)],
                     [(GAZ_R + 0.11) * math.cos(a0), 0.02, (GAZ_R + 0.11) * math.sin(a0)],
                     [(GAZ_R + 0.11) * math.cos(a1), 0.02, (GAZ_R + 0.11) * math.sin(a1)],
                     [(GAZ_R - 0.11) * math.cos(a1), 0.02, (GAZ_R - 0.11) * math.sin(a1)]],
                    (212, 212, 206), katman=2)
    z = -200.0 if _gaz_s < 70 else 1.0                    # duz giris (yalniz basta)
    while z < 0:
        z2 = min(0.0, z + 6.0)
        s.yuzey([[GAZ_R - GAZ_YARIM, 0.01, z], [GAZ_R + GAZ_YARIM, 0.01, z],
                 [GAZ_R + GAZ_YARIM, 0.01, z2], [GAZ_R - GAZ_YARIM, 0.01, z2]],
                asfalt, katman=1)
        for yan in (-1, 1):
            s.yuzey([[GAZ_R + yan * GAZ_YARIM, 0.02, z],
                     [GAZ_R + yan * (GAZ_YARIM - 0.16), 0.02, z],
                     [GAZ_R + yan * (GAZ_YARIM - 0.16), 0.02, z2],
                     [GAZ_R + yan * GAZ_YARIM, 0.02, z2]], (208, 208, 202), katman=2)
        if int(z / 6) % 2 == 0:
            s.yuzey([[GAZ_R - 0.11, 0.02, z], [GAZ_R + 0.11, 0.02, z],
                     [GAZ_R + 0.11, 0.02, z2], [GAZ_R - 0.11, 0.02, z2]],
                    (212, 212, 206), katman=2)
        z = z2
    for i in range(26):                                   # agaclar
        a = 2 * math.pi * i / 26
        for rr in (GAZ_R - 11, GAZ_R + 11):
            _agac(s, rr * math.cos(a), rr * math.sin(a), 5.0 + (i % 4) * 1.2,
                  (84, 66, 48) if GUNDUZ else (34, 30, 26),
                  (54, 104, 52) if GUNDUZ else (24, 38, 26))

    # --- motosiklet --------------------------------------------------------
    konum, teget, disa, th = _gaz_konum(_gaz_s, ofset)
    # YATIS ISARETI: lambda > 0 = SOLA yatis (gorsel testle dogrulandi).
    # Daha once negatif veriliyordu: sol virajda motosiklet SAGA yatiyordu.
    yatis = 0.42 * yatis_k
    golge = [konum + np.array([0.40 * math.cos(a), -konum[1] + 0.012, 1.15 * math.sin(a)])
             for a in (math.pi * 2 * i / 10 for i in range(10))]
    s.yuzey(golge, (64, 74, 62) if GUNDUZ else (20, 25, 22), isiksiz=True, katman=2)
    model, _, _ = motosiklet(0.0, _gaz_tek, 0.0)
    R = donus([0, 1, 0], -th) @ donus([0, 0, 1], yatis)
    s.ekle(model, R=R, t=konum)

    # --- havadan takip kamerasi -------------------------------------------
    # Daha alcak ve yakin: 21 m yukseklikte motosiklet pul kadar kaliyordu.
    goz = konum + np.array([0.0, 11.5, 0.0]) - teget * 10.5 + disa * 1.5
    kamera = Kamera(goz, konum + teget * 2.5, G, Y, fov=44)
    s.ciz(d, kamera, gok)

    # --- 2B gostergeler ----------------------------------------------------
    d.rounded_rectangle([70, 470, 188, 790], 10, fill=(255, 255, 255, 22))
    yuk = int(316 * gaz)
    d.rounded_rectangle([70, 786 - yuk, 188, 786], 10,
                        fill=KIRMIZI if gaz < 0.03 else TURUNCU)
    s2.yazi(d, (129, 418), "GAZ", 32, (160, 165, 172), ortala=True)
    s2.yazi(d, (129, 800), f"%{int(gaz * 100)}", 40,
            KIRMIZI if gaz < 0.03 else TURUNCU, ortala=True)
    d.rounded_rectangle([G - 320, 470, G - 72, 612], 18, fill=(0, 0, 0, 160),
                        outline=(92, 102, 112), width=4)
    s2.yazi(d, (G - 196, 482), f"{int(hiz_kmh)}", 82, KREM, ortala=True)
    s2.yazi(d, (G - 196, 572), "km/h", 28, (150, 155, 160), ortala=True)

    f = s2.font(36)
    tw = d.textlength(etiket, font=f)
    d.rounded_rectangle([(G - tw) / 2 - 28, 300, (G + tw) / 2 + 28, 376], 14,
                        fill=(0, 0, 0, 180), outline=renk, width=5)
    s2.yazi(d, (G / 2, 312), etiket, 36, renk, ortala=True)

    if ofset > GAZ_YARIM - 0.3:                           # seritten tasti
        uyari = "ŞERİDİN DIŞINDA"
        f2 = s2.font(40)
        tw2 = d.textlength(uyari, font=f2)
        d.rounded_rectangle([(G - tw2) / 2 - 30, 392, (G + tw2) / 2 + 30, 474], 14,
                            fill=(120, 20, 16, 210), outline=KIRMIZI, width=5)
        s2.yazi(d, (G / 2, 404), uyari, 40, (255, 220, 215), ortala=True)
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
    # derinlik -> egrilik. Araligi genislettik: 0.02 ~ dumduz (R~500 m),
    # 0.36 ~ keskin viraj (R~28 m). Eskisi en acik halde bile kavisli kaliyordu.
    egri = -(0.08 + derinlik * 8.0)
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
    # Serit ici konum virajin KESKINLIGINE gore: viraj ne kadar keskinse
    # o kadar disa (sola donen virajda seridin sagina) cikilir, duzlukte
    # seridin soluna donulur. Seridin solu 1.78, ortasi ~2.3, sagi 2.90.
    k = min(1.0, abs(egri) / 2.4)
    hedef_serit = 1.78 + 1.12 * k
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

    # Kamera motosikleti kadrajda tutmali: cok ileriye nisan alinca keskin
    # virajda bakis yana savruluyor ve motosiklet kareden cikiyordu. Hedef,
    # motosiklet ile yolun ilerisi arasinda harmanlanir.
    bx = _merkez_x(mz, egri) + _serit
    ax = _merkez_x(22, egri) + _serit * 0.8
    goz = np.array([_merkez_x(-6, egri) + _serit + 0.4, 3.05, -6.0])
    bak = np.array([0.62 * bx + 0.38 * ax, 1.05, 18.0])
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
    ap.add_argument("--sahne", choices=("fren", "viraj", "kontra", "gaz"), required=True)
    ap.add_argument("--sure", type=float, default=60.0)
    ap.add_argument("--fazlar", default="")
    ap.add_argument("--cikti", default=None)
    ap.add_argument("--sessiz", action="store_true")
    ap.add_argument("--kamera", default="yan",
                    choices=("yan", "kask", "takip", "degisken", "onden", "tepeden"))
    ap.add_argument("--gunduz", default="")
    args = ap.parse_args()

    global KAMERA_MODU, GUNDUZ
    KAMERA_MODU = args.kamera
    GUNDUZ = str(args.gunduz).lower() in ("1", "true", "evet", "yes")
    # Faz adlari sahneye gore farkli; viraj disindaki sahnelerde viraj
    # dogrulayicisina gondermek "bilinmeyen faz" hatasi veriyordu.
    if args.sahne == "viraj":
        s2.fazlari_ayarla(args.fazlar)
    cikti = args.cikti or f"videos/sahne3b_{args.sahne}.mp4"
    os.makedirs(os.path.dirname(cikti) or ".", exist_ok=True)
    if args.sahne == "fren":
        cizer = kare_fren3b
    elif args.sahne == "kontra":
        cizer = kare_kontra3b
    elif args.sahne == "gaz":
        gaz_fazlari_ayarla(args.fazlar)

        def cizer(t):
            return kare_gaz3b(t, args.sure)
    else:
        def cizer(t):
            return kare_viraj3b(t, args.sure)
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
