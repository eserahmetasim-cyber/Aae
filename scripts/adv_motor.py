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


def adv_motosiklet(tekerlek_aci=0.0, direksiyon=0.0, surucu=True):
    """Duz (frensiz) model; sadece Sahne dondurur."""
    return motosiklet(0.0, tekerlek_aci, direksiyon, surucu)[0]


def motosiklet(fren=0.0, tekerlek_aci=0.0, direksiyon=0.0, surucu=True):
    """sahne3b.motosiklet ile ayni donus: (sahne, cokme, kask_n)."""
    cokme = 0.085 * fren
    ust = Sahne()
    _ekle(ust, "govde")
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
