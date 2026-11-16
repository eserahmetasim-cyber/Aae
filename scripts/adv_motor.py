#!/usr/bin/env python3
"""
adv_motor.py
-------------------------------------------------------------------
AAE'nin KENDI motoru (adventure) + AAE kiyafetli surucu, uc_boyut.py icin.
AAE'nin onayladigi Blender modelinden (14 Kas 2026) aktarildi, ~7300 ucgen.
Motoru YENIDEN MODELLEME: bu dosyayi kullan.

  assets/adv_motor/adv_motor_ucgen.npz  -> bu dosyanin okudugu ucgen listesi
  assets/adv_motor/adv_motor.glb        -> ayni modelin GLB hali (baska program icin)
  assets/adv_motor/adv_ucgen_disa.py    -> npz'yi ureten Blender betigi (KASKAFA oturumu)

KULLANIM (sahne3b.motosiklet ile ayni imza, yerine takilir):
    from adv_motor import motosiklet
    s_motor, cokme, kask_n = motosiklet(fren, tekerlek_aci, direksiyon, surucu=True)

Eksen (uc_boyut ile ayni): X sag, Y yukari, Z ileri. Orijin = iki tekerin
yere degdigi hattin ortasi (y=0). Arka aks z=-0.73 (r=0.322), on aks z=+0.74 (r=0.345).
tekerlek_aci: ileri gidiste artar (aci = alinan_yol / yaricap).
direksiyon: radyan, Y ekseni etrafinda; on takim + on teker birlikte doner.
fren 0-1: on catal cokmesi (govde + surucu arka aks etrafinda burun asagi egilir).
Marka logosu / model numarasi YOK.
-------------------------------------------------------------------
"""
import math
import os

import numpy as np

from uc_boyut import Sahne, donus

_YOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "adv_motor", "adv_motor_ucgen.npz")
_V = np.load(_YOL)
ON_AKS = _V["teker_on_aks"].astype(float)
ARKA_AKS = _V["teker_arka_aks"].astype(float)
ON_R, ARKA_R = float(ON_AKS[1]), float(ARKA_AKS[1])
_S = _V["surucu_ucgen"].reshape(-1, 3)
_ust = _S[:, 1] > _S[:, 1].max() - 0.22
KASK_N = _S[_ust].mean(axis=0).astype(float)          # kask merkezi (kamera hedefi icin)


def _x_donus(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)


def _ekle(s, grup, R=None, t=None):
    uc = _V[grup + "_ucgen"].astype(float)
    if R is not None:
        uc = uc @ np.asarray(R).T
    if t is not None:
        uc = uc + t
    for p, rk, isk in zip(uc, _V[grup + "_renk"], _V[grup + "_isiksiz"]):
        s.yuzey(p, (int(rk[0]), int(rk[1]), int(rk[2])), isiksiz=bool(isk))



# ---------------------------------------------------------------- arka bolum
# Blender modelinde arka tekerlek ile sele arasi bos kaliyordu: gercek bir
# adventure motorda o ucgende monoamortisor, yan panel, lastigin ustune oturan
# camurluk, susturucu ve zincir muhafazasi bulunur. Model dosyasina
# dokunmadan, ayni renk paletiyle burada kuruluyor.
KOYU = (40, 40, 42)
KOYU2 = (48, 49, 53)
METAL = (153, 148, 148)
AMBER = (243, 178, 63)

AKS_Y, AKS_Z = 0.322, -0.73          # arka aks
TEKER_R = 0.322


def _yay_kabuk(s, merkez, r0, r1, a0, a1, yari_en, renk, n=9):
    """Aks etrafinda donen ince kabuk (camurluk). Aci 0 = ileri, +pi/2 = yukari."""
    cy, cz = merkez
    for i in range(n):
        t0 = a0 + (a1 - a0) * i / n
        t1 = a0 + (a1 - a0) * (i + 1) / n
        for rr, isaret in ((r1, 1), (r0, -1)):
            p = [[-yari_en, cy + rr * math.sin(t0), cz + rr * math.cos(t0)],
                 [yari_en, cy + rr * math.sin(t0), cz + rr * math.cos(t0)],
                 [yari_en, cy + rr * math.sin(t1), cz + rr * math.cos(t1)],
                 [-yari_en, cy + rr * math.sin(t1), cz + rr * math.cos(t1)]]
            s.yuzey(p if isaret > 0 else p[::-1], renk)
        for yan in (-1, 1):                                   # yan duvarlar
            p = [[yan * yari_en, cy + r0 * math.sin(t0), cz + r0 * math.cos(t0)],
                 [yan * yari_en, cy + r1 * math.sin(t0), cz + r1 * math.cos(t0)],
                 [yan * yari_en, cy + r1 * math.sin(t1), cz + r1 * math.cos(t1)],
                 [yan * yari_en, cy + r0 * math.sin(t1), cz + r0 * math.cos(t1)]]
            s.yuzey(p if yan > 0 else p[::-1], KOYU)


def _arka_bolum(s):
    """Sele ile arka tekerlek arasindaki ucgeni dolduran parcalar.

    Olculer kucuk tutuldu: ilk denemede yan panel selenin hizasina kadar
    cikinca siluet tek bir kara levhaya donusuyor ve amortisoru de kapatiyordu.
    Panel artik selenin ALTINDA kaliyor, amortisor onunde acikta duruyor."""
    # 1) MONOAMORTISOR: salincaktan sasiye, panelin onunde acikta. Yay amber.
    alt = np.array([0.0, 0.46, -0.49])
    ust = np.array([0.0, 0.92, -0.37])
    s.silindir(alt, ust, 0.026, KOYU, segment=10)             # mil
    s.silindir(alt, alt + (ust - alt) * 0.20, 0.048, KOYU2, segment=10)
    s.kure(alt, 0.036, KOYU2, dilim=8, halka=5)
    s.kure(ust, 0.034, KOYU2, dilim=8, halka=5)
    for i in range(7):                                        # yay sarimlari
        a = 0.24 + 0.68 * i / 7.0
        s.silindir(alt + (ust - alt) * a, alt + (ust - alt) * (a + 0.048),
                   0.054, AMBER, segment=10, kapak=False)

    # 2) YAN PANEL: selenin ALTINDA, arkaya dogru daralan ince levha
    for yan in (-1, 1):
        x = yan * 0.185
        kose = [(0.94, -0.52), (0.95, -0.78), (0.72, -0.79), (0.69, -0.54)]
        p = [[x, y, z] for y, z in kose]
        s.yuzey(p if yan > 0 else p[::-1], KOYU2)
        serit = [(0.79, -0.53), (0.81, -0.77), (0.76, -0.775), (0.745, -0.535)]
        q = [[x + yan * 0.004, y, z] for y, z in serit]
        s.yuzey(q if yan > 0 else q[::-1], AMBER)

    # 3) CAMURLUK: lastigin ustune oturur (0 = ileri, +pi/2 = yukari)
    _yay_kabuk(s, (AKS_Y, AKS_Z), TEKER_R + 0.028, TEKER_R + 0.048,
               1.25, 2.45, 0.098, KOYU2, n=7)

    # 4) SUSTURUCU: sag yan, yukari egimli. Parlak krom yerine koyu metal -
    #    acik renk birakilinca kucuk kadrajda tum arkayi yutuyor.
    e0 = np.array([0.125, 0.50, -0.42])
    e1 = np.array([0.215, 0.60, -0.88])
    s.silindir(e0, e1, 0.026, KOYU, segment=10)               # baglanti borusu
    s.silindir(e0 + (e1 - e0) * 0.36, e1, 0.055, (92, 92, 96), segment=12)
    s.silindir(e1, e1 + (e1 - e0) * 0.05, 0.044, (26, 26, 28), segment=12)

    # 5) ZINCIR MUHAFAZASI: sol yan, zincirin ustunde
    s.kutu([-0.112, 0.46, -0.52], [0.014, 0.050, 0.30], KOYU2)

    # 6) ARKA SINYALLER
    for yan in (-1, 1):
        s.kure([yan * 0.170, 0.950, -0.87], 0.028, AMBER, dilim=8, halka=5)


def adv_motosiklet(tekerlek_aci=0.0, direksiyon=0.0, surucu=True):
    """Duz (frensiz) model; sadece Sahne dondurur."""
    return motosiklet(0.0, tekerlek_aci, direksiyon, surucu)[0]


def motosiklet(fren=0.0, tekerlek_aci=0.0, direksiyon=0.0, surucu=True):
    """sahne3b.motosiklet ile ayni donus: (sahne, cokme, kask_n)."""
    cokme = 0.085 * fren
    ust = Sahne()
    _ekle(ust, "govde")
    _arka_bolum(ust)
    if surucu:
        _ekle(ust, "surucu")
    on = Sahne()
    _ekle(on, "on_takim")
    _ekle(on, "teker_on", _x_donus(tekerlek_aci), ON_AKS)
    s = Sahne()
    _ekle(s, "teker_arka", _x_donus(tekerlek_aci * ON_R / ARKA_R), ARKA_AKS)
    # direksiyon: on takim, on aksin 13 cm gerisinden gecen dikey eksen etrafinda
    if abs(direksiyon) > 1e-4:
        eksen = np.array([0.0, 0.0, ON_AKS[2] - 0.13])
        R = donus([0, 1, 0], direksiyon)
        on2 = Sahne(); on2.ekle(on, R=R, t=eksen - R @ eksen); on = on2
    # fren: govde + surucu + on takimin ust kismi arka aks etrafinda burun asagi
    kask_n = KASK_N.copy()
    if cokme > 0:
        a = math.atan2(cokme, ON_AKS[2] - ARKA_AKS[2])      # pozitif = burun asagi
        R = _x_donus(a)
        piv = ARKA_AKS
        ust2 = Sahne(); ust2.ekle(ust, R=R, t=piv - R @ piv); ust = ust2
        kask_n = R @ (kask_n - piv) + piv
    s.ekle(ust)
    s.ekle(on)
    return s, cokme, kask_n


if __name__ == "__main__":
    # Hizli test: python scripts/adv_motor.py -> output/adv_motor_test.png
    from PIL import Image, ImageDraw
    from uc_boyut import Kamera
    gor = []
    for konum, fren, dr in (((4.5, 1.2, 0.0), 0.0, 0.0), ((-3.0, 1.8, -3.6), 0.0, 0.25), ((3.0, 1.4, 3.6), 1.0, 0.0)):
        s, _, kn = motosiklet(fren, 0.3, dr)
        im = Image.new("RGB", (540, 960), (200, 205, 210))
        k = Kamera(np.array(konum, float), np.array([0, 0.8, 0], float), 540, 960, fov=40)
        s.ciz(ImageDraw.Draw(im), k, (200, 205, 210))
        gor.append(im)
    out = Image.new("RGB", (1620, 960))
    for i, im in enumerate(gor):
        out.paste(im, (540 * i, 0))
    os.makedirs("output", exist_ok=True)
    out.save("output/adv_motor_test.png")
    print("output/adv_motor_test.png  kask_n", np.round(KASK_N, 3))
