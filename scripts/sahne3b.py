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
from uc_boyut import Kamera, Sahne, birim, donus, isik_ayarla   # noqa: E402
import sahne_uret as s2                              # ses + 2B yardimcilar  # noqa: E402
import adv_motor                                  # AAE'nin onayli motoru  # noqa: E402
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


def _pahli(s, merkez, boyut, renk, pah=0.26, on_olcek=1.0, arka_olcek=1.0,
           R=None, katman=3):
    """Kose yontulmus (pahli) ve ucu daralabilen govde parcasi.

    Motor, depo, sele ve kuyruk duz kutulardan kuruluydu; dik koseler
    motosikleti oyuncak gibi gosteriyordu. Kesit dikdortgen yerine sekizgen:
    dort kose kesiliyor. on_olcek/arka_olcek ile parca one ya da arkaya
    dogru daralabiliyor (depo one dogru incelir, kuyruk arkaya)."""
    merkez = np.asarray(merkez, dtype=float)
    sx, sy, sz = np.asarray(boyut, dtype=float) / 2.0
    c = pah * min(sx, sy)
    kesit = [(sx - c, sy), (sx, sy - c), (sx, -(sy - c)), (sx - c, -sy),
             (-(sx - c), -sy), (-sx, -(sy - c)), (-sx, sy - c), (-(sx - c), sy)]

    def halka(z, olcek):
        p = [np.array([x * olcek, y * olcek, z]) for x, y in kesit]
        if R is not None:
            p = [np.asarray(R) @ q for q in p]
        return [merkez + q for q in p]

    on, arka = halka(sz, on_olcek), halka(-sz, arka_olcek)
    n = len(kesit)
    for i in range(n):
        j = (i + 1) % n
        s.yuzey([arka[i], arka[j], on[j], on[i]], renk, katman=katman)
    koyu = tuple(int(k * 0.88) for k in renk)
    s.yuzey(on, koyu, katman=katman)
    s.yuzey(arka[::-1], koyu, katman=katman)


def _tekerlek(s, z, aci, yaricap=0.31, disk=True, on=True):
    """aci: tekerlegin donme acisi (radyan). Daha once sabit 0 geciliyordu,
    bu yuzden tekerlekler hic donmuyordu.

    Lastik tek silindirdi ve yandan duz bir disk gibi duruyordu. Motosiklet
    lastiginin sirti YUVARLAKTIR (arabanınki gibi duz degil): profil ust uste
    binen uc silindirle veriliyor, uzerine de dis blogu geciyor."""
    R = donus([1, 0, 0], aci)

    # --- lastik: yuvarlak sirt profili -----------------------------------
    for yari_g, r_k in ((0.082, 1.000), (0.062, 0.998), (0.030, 0.993)):
        s.silindir([-yari_g, yaricap, z], [yari_g, yaricap, z],
                   yaricap * r_k, LASTIK, segment=22)
    # Yanak 0.80 yaricaptaydi ve janti tamamen orluyordu.
    s.silindir([-0.086, yaricap, z], [0.086, yaricap, z], yaricap * 0.68,
               (30, 30, 32), segment=20)                          # yanak

    # --- dis blogu: cevrede, sirta hafif cikintili ------------------------
    # Dis: ince kanal izleri. Ilk denemede bloklar 3.5 cm yuksekti ve lastik
    # traktor lastigi gibi duruyordu; yol lastiginin disi neredeyse duzdur.
    N = 26
    for i in range(N):
        a = 2 * math.pi * i / N
        yon = np.array([0.0, math.cos(a), math.sin(a)])
        s.kutu([0, yaricap, z] + (R @ yon) * yaricap * 0.995,
               [0.090 if i % 2 else 0.052, 0.010, 0.018], (22, 22, 24),
               R=R @ donus([1, 0, 0], -a))

    # --- jant: tabani, bilezik dudaklari ve kollari -----------------------
    s.silindir([-0.062, yaricap, z], [0.062, yaricap, z], yaricap * 0.52,
               (46, 46, 50), segment=18)
    for yan in (-1, 1):                                           # bilezik dudagi
        s.silindir([yan * 0.070, yaricap, z], [yan * 0.082, yaricap, z],
                   yaricap * 0.74, JANT, segment=20)
    for i in range(5):                                            # kollar
        a = 2 * math.pi * i / 5
        yon = np.array([0.0, math.cos(a), math.sin(a)])
        s.kutu([0, yaricap, z] + (R @ yon) * yaricap * 0.36,
               [0.062, yaricap * 0.60, 0.042], JANT,
               R=R @ donus([1, 0, 0], -a))
    sup = np.array([0.0, math.cos(aci + 1.1), math.sin(aci + 1.1)])
    s.kutu([0, yaricap, z] + sup * yaricap * 0.60, [0.030, 0.055, 0.030],
           (28, 28, 30))                                          # sibop

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
    s.silindir([-0.125, yaricap, z], [0.125, yaricap, z], 0.018, (170, 172, 176),
               segment=8)                                         # aks


def _camurluk(s, z, yaricap=0.31, renk=TURUNCU):
    """Tekerlegin yayini izleyen kavisli camurluk. Duz bir kutu olarak
    konulunca tekerlegin uzerinde duran bir tahta gibi duruyordu.

    Camurluk catal ayagina baglidir, ayak da aksi tasir: bu yuzden tekerlekle
    birlikte durur, suspansiyon cokmesiyle asagi inmez."""
    # Ilk denemede R1 = yaricap + 0.085 ve yay -0.35..1.75 idi: camurluk
    # tekerlekten kopuk, kalin bir kemer gibi duruyordu.
    R0, R1 = yaricap + 0.020, yaricap + 0.042
    A0, A1, N = -0.10, 1.45, 10                # radyan: on-alttan arka-uste
    def p(a, r, x):
        return [x, yaricap + r * math.sin(a), z + r * math.cos(a)]
    for i in range(N):
        a0 = A0 + (A1 - A0) * i / N
        a1 = A0 + (A1 - A0) * (i + 1) / N
        s.yuzey([p(a0, R1, -0.074), p(a0, R1, 0.074),
                 p(a1, R1, 0.074), p(a1, R1, -0.074)], renk)       # ust yuz
        for yan in (-1, 1):                                        # yan etek
            s.yuzey([p(a0, R1, yan * 0.074), p(a0, R0, yan * 0.074),
                     p(a1, R0, yan * 0.074), p(a1, R1, yan * 0.074)],
                    tuple(int(k * 0.80) for k in renk))


# ---------------------------------------------------------------------------
#  KASK YAZISI  (marka: AAE)
# ---------------------------------------------------------------------------
# Her harf, birim kutuda (0..1 genislik, 0..1 yukseklik) cizgi parcalarindan
# kurulur. Motor dokuyu desteklemiyor, yazi da kalin dortgenlerle ciziliyor.
_HARF = {
    "A": [((0.50, 1.00), (0.06, 0.00)), ((0.50, 1.00), (0.94, 0.00)),
          ((0.22, 0.38), (0.78, 0.38))],
    "E": [((0.10, 1.00), (0.10, 0.00)), ((0.06, 1.00), (0.92, 1.00)),
          ((0.06, 0.52), (0.74, 0.52)), ((0.06, 0.00), (0.92, 0.00))],
}


def _kask_sar(merkez, yaricap, bakis, yukari, pay=0.015):
    """Kaskin uzerine oturan yerel 2B duzlem: (u, v) -> 3B nokta dondurur.
    Hem yazi hem bayrak bunu kullanir."""
    # Duzleme BAKAN gozun sagi: cross(bakis, yukari). Ters sirada yazilinca
    # metin aynalaniyor ve "AAE" ekranda "EAA" olarak okunuyordu.
    bakis = birim(np.asarray(bakis, dtype=float))
    sag = birim(np.cross(bakis, np.asarray(yukari, dtype=float)))
    ust = np.cross(sag, bakis)
    merkez = np.asarray(merkez, dtype=float)

    def nokta(u, v):
        """Duz duzlem yerine kabugun UZERINE sarar. Duz birakilinca cizimin
        kenarlari kaskin siluetinden tasip lekeler biraktiriyordu."""
        if yaricap <= 0.0:
            return list(merkez + bakis * pay + sag * u + ust * v)
        # Pay belirgin: ressam algoritmasi yuzleri derinlige gore siraliyor,
        # kucuk pay verilince komsu kabuk yuzleri cizimin uzerine biniyordu.
        d = birim(bakis * yaricap + sag * u + ust * v)
        return list(merkez + d * (yaricap + pay))

    return nokta


def _cember(merkez, yaricap, aci0, aci1, adim=26):
    """Yay uzerinde 2B nokta listesi."""
    return [(merkez[0] + yaricap * math.cos(a), merkez[1] + yaricap * math.sin(a))
            for a in np.linspace(aci0, aci1, adim)]


def _kask_bayrak(s, merkez, yaricap, bakis, yukari, yuk=0.050, pay=0.014):
    """Turk bayragi: kirmizi zemin + ay + bes koseli yildiz.

    Hilal iki cemberin farki; motorda boolean yok, bu yuzden kesisim
    noktalarindan gecen tek bir icbukey cokgen olarak kuruluyor."""
    KIRMIZI_B, BEYAZ = (227, 10, 23), (248, 248, 246)
    gen = yuk * 1.5
    zemin = _kask_sar(merkez, yaricap, bakis, yukari, pay)
    uzeri = _kask_sar(merkez, yaricap, bakis, yukari, pay + 0.005)

    s.yuzey([zemin(u, v) for u, v in ((-gen / 2, -yuk / 2), (gen / 2, -yuk / 2),
                                      (gen / 2, yuk / 2), (-gen / 2, yuk / 2))],
            KIRMIZI_B, katman=3)

    # --- hilal: dis cember Ro, ic cember Ri, merkezleri d kadar ayrik ------
    Ro, Ri, d = 0.26 * yuk, 0.215 * yuk, 0.075 * yuk
    Co = (-0.16 * gen, 0.0)
    Ci = (Co[0] + d, 0.0)
    x = (d * d + Ro * Ro - Ri * Ri) / (2 * d)          # kesisim, Co merkezli
    y = math.sqrt(max(0.0, Ro * Ro - x * x))
    t_dis = math.atan2(y, x)
    t_ic = math.atan2(y, x - d)
    hilal = _cember(Co, Ro, t_dis, 2 * math.pi - t_dis) \
        + _cember(Ci, Ri, 2 * math.pi - t_ic, t_ic)
    s.yuzey([uzeri(u, v) for u, v in hilal], BEYAZ, katman=3)

    # --- yildiz: bir ucu sancak tarafina (saga) bakar ----------------------
    Ry, Ciz = 0.115 * yuk, (0.02 * gen, 0.0)
    yildiz = []
    for i in range(10):
        r = Ry if i % 2 == 0 else Ry * 0.42
        a = i * math.pi / 5
        yildiz.append((Ciz[0] + r * math.cos(a), Ciz[1] + r * math.sin(a)))
    s.yuzey([uzeri(u, v) for u, v in yildiz], BEYAZ, katman=3)


def _kask_yazi(s, merkez, yaricap, bakis, yukari, metin="AAE",
               yuk=0.066, kalin=0.012, renk=(24, 28, 36)):
    """Kaska tegetlik bir duzlemde metni yazar. Harfler kucuk oldugu icin
    duzlem yaklasimi kavis bozulmasi yaratmiyor."""
    nokta = _kask_sar(merkez, yaricap, bakis, yukari)
    harf_g, bosluk = yuk * 0.74, yuk * 0.22
    genislik = len(metin) * harf_g + (len(metin) - 1) * bosluk
    x = -genislik / 2.0
    for ch in metin:
        for (ax, ay), (bx, by) in _HARF[ch]:
            a = np.array([x + ax * harf_g, (ay - 0.5) * yuk])
            b = np.array([x + bx * harf_g, (by - 0.5) * yuk])
            yon = b - a
            boy = float(np.hypot(*yon))
            if boy < 1e-9:
                continue
            yon /= boy
            dik = np.array([-yon[1], yon[0]]) * (kalin / 2.0)
            kose = (a - dik, a + dik, b + dik, b - dik)
            s.yuzey([nokta(u[0], u[1]) for u in kose], renk, katman=3)
        x += harf_g + bosluk


# Gercek kask olculeri. Kafa kaliplari "ara oval" (en yaygin), "uzun oval" ve
# "yuvarlak oval"; ara oval onden arkaya yanlardan uzundur - kure degil yumurta.
# Kapali kaskin arkadan gorunusunde dort sey okunur: yukari dogru daralan
# kabuk, tepeye yakin duran spoiler, onun altinda egzoz delikleri ve en altta
# ense rulosu. Onde cene bari one tasar; kure bunlarin hicbirini vermiyordu.
# Arkadan bakista kask daireden daha dar ve uzundur; esit yarıcap verince
# top gibi duruyordu.
KASK_R = (0.131, 0.159, 0.163)          # (yan, yukseklik, on-arka)
KASK_KOYU, KASK_METAL = (38, 41, 47), (62, 66, 74)
VIZ_A, VIZ_T0, VIZ_T1 = 1.20, -0.32, 0.21     # vizor acikligi


def _kask_olcu(t, a):
    """Cene bari one tasar, agiz hizasinda kabuk yanlardan hafif daralir."""
    rx, ry, rz = KASK_R
    on = max(0.0, math.cos(a)) ** 1.5
    alt = min(1.0, max(0.0, (VIZ_T0 + 0.14 - t) / 0.80))
    return (rx * (1.0 - 0.10 * alt * on), ry, rz * (1.0 + 0.36 * alt * on))


def _kask_p(merkez, t, a, pay=1.0):
    r = _kask_olcu(t, a)
    return [merkez[0] + math.cos(t) * math.sin(a) * r[0] * pay,
            merkez[1] + math.sin(t) * r[1] * pay,
            merkez[2] + math.cos(t) * math.cos(a) * r[2] * pay]


def _kask_alt(a):
    """Kabugun alt kenari: onde cene barina iner, yanlarda kulagi orter,
    arkada ense hareket edebilsin diye yukari kivrilir."""
    return -0.80 - 0.26 * math.cos(a)


def _kask_yama(s, merkez, t0, t1, a0, a1, renk, pay=1.0, na=4, nt=3):
    """Kabuga oturan dikdortgen yama (havalandirma agzi, vizor, cerceve)."""
    for j in range(na):
        aa0 = a0 + (a1 - a0) * j / na
        aa1 = a0 + (a1 - a0) * (j + 1) / na
        for i in range(nt):
            tt0 = t0 + (t1 - t0) * i / nt
            tt1 = t0 + (t1 - t0) * (i + 1) / nt
            c = renk(i / max(1, nt - 1)) if callable(renk) else renk
            s.yuzey([_kask_p(merkez, tt0, aa0, pay), _kask_p(merkez, tt0, aa1, pay),
                     _kask_p(merkez, tt1, aa1, pay), _kask_p(merkez, tt1, aa0, pay)], c)


def _kask(s, merkez, kabuk=KREM, aksan=TURUNCU):
    """Kapali (full face) kask."""
    merkez = np.asarray(merkez, dtype=float)
    NA, NT = 28, 9

    for j in range(NA):                                   # --- kabuk ---
        a0, a1 = 2 * math.pi * j / NA, 2 * math.pi * (j + 1) / NA
        b0, b1 = _kask_alt(a0), _kask_alt(a1)
        for i in range(NT):
            u0, u1 = i / NT, (i + 1) / NT
            s.yuzey([_kask_p(merkez, b0 + (math.pi / 2 - b0) * u0, a0),
                     _kask_p(merkez, b1 + (math.pi / 2 - b1) * u0, a1),
                     _kask_p(merkez, b1 + (math.pi / 2 - b1) * u1, a1),
                     _kask_p(merkez, b0 + (math.pi / 2 - b0) * u1, a0)], kabuk)

    for j in range(NA):                                   # --- ense rulosu ---
        a0, a1 = 2 * math.pi * j / NA, 2 * math.pi * (j + 1) / NA
        b0, b1 = _kask_alt(a0), _kask_alt(a1)
        s.yuzey([_kask_p(merkez, b0, a0), _kask_p(merkez, b1, a1),
                 _kask_p(merkez, b1 - 0.13, a1, 0.90),
                 _kask_p(merkez, b0 - 0.13, a0, 0.90)], KASK_KOYU)

    # --- vizor: koyu cerceve + icine oturan camlar (ustte gok yansimasi) ---
    _kask_yama(s, merkez, VIZ_T0 - 0.05, VIZ_T1 + 0.05, -VIZ_A - 0.05, VIZ_A + 0.05,
               KASK_KOYU, pay=1.004, na=14, nt=2)
    _kask_yama(s, merkez, VIZ_T0, VIZ_T1, -VIZ_A, VIZ_A,
               lambda u: tuple(min(255, int(v * (0.78 + 1.25 * u * u)))
                               for v in (47, 59, 77)), pay=1.016, na=14, nt=5)

    # --- tepe seridi: on-arka, kutupta genisleyerek tam kapanir ------------
    # Sabit azimut genisligi verilince serit kutupta sivri bir uca donusuyordu.
    def _da(t):
        return math.asin(min(1.0, 0.032 / max(0.012, _kask_olcu(t, 0.0)[0] * math.cos(t))))

    for sektor, t_bas in ((0.0, VIZ_T1 + 0.09), (math.pi, -0.10)):
        for i in range(8):
            u0 = t_bas + (math.pi / 2 - t_bas) * i / 8
            u1 = t_bas + (math.pi / 2 - t_bas) * (i + 1) / 8
            d0, d1 = _da(u0), _da(u1)
            for j in range(4):
                a00 = sektor - d0 + 2 * d0 * j / 4
                a01 = sektor - d0 + 2 * d0 * (j + 1) / 4
                a10 = sektor - d1 + 2 * d1 * j / 4
                a11 = sektor - d1 + 2 * d1 * (j + 1) / 4
                s.yuzey([_kask_p(merkez, u0, a00, 1.006),
                         _kask_p(merkez, u0, a01, 1.006),
                         _kask_p(merkez, u1, a11, 1.006),
                         _kask_p(merkez, u1, a10, 1.006)], aksan)

    # --- arka spoiler: ortada kalinlasip kenarlarda kabuga karisan ordek
    #     kuyrugu. Kutu olarak konunca arkadan "T" gibi cikinti yapiyordu.
    SP, ST0, ST1 = 0.50, -0.02, 0.30
    def _sp(a):
        return 1.0 + 0.085 * math.cos((a - math.pi) / SP * (math.pi / 2))
    for j in range(10):
        a0 = math.pi - SP + 2 * SP * j / 10
        a1 = math.pi - SP + 2 * SP * (j + 1) / 10
        p0, p1 = _sp(a0), _sp(a1)
        for i in range(3):
            t0 = ST0 + (ST1 - ST0) * i / 3
            t1 = ST0 + (ST1 - ST0) * (i + 1) / 3
            s.yuzey([_kask_p(merkez, t0, a0, p0), _kask_p(merkez, t0, a1, p1),
                     _kask_p(merkez, t1, a1, p1), _kask_p(merkez, t1, a0, p0)], kabuk)
        s.yuzey([_kask_p(merkez, ST0, a0, p0), _kask_p(merkez, ST0, a1, p1),
                 _kask_p(merkez, ST0 - 0.13, a1), _kask_p(merkez, ST0 - 0.13, a0)],
                KASK_KOYU)

    # --- havalandirma agizlari: kabuga gomulu koyu yamalar ------------------
    _kask_yama(s, merkez, -0.46, -0.30, -0.26, 0.26, KASK_KOYU, 1.004, na=5, nt=2)
    for yan in (-1, 1):                                   # arka egzozlar
        _kask_yama(s, merkez, -0.17, -0.03, yan * (math.pi - 0.52),
                   yan * (math.pi - 0.26), KASK_KOYU, 1.004, na=3, nt=2)
    for yan in (-1, 1):                                   # tepe girisleri
        _kask_yama(s, merkez, 0.52, 0.80, yan * 0.16, yan * 0.42,
                   KASK_KOYU, 1.004, na=3, nt=2)
    for yan in (-1, 1):                                   # vizor mentesesi
        s.kutu(merkez + [yan * 0.126, -0.034, 0.056], [0.016, 0.040, 0.042],
               KASK_METAL)

    _kask_yazi(s, merkez, 0.158, [0, -0.46, -1], [0, 1, 0], yuk=0.042)
    for yan in (-1, 1):
        _kask_yazi(s, merkez, 0.140, [yan, 0.30, -0.42], [0, 1, 0], yuk=0.036)
        # Bayrak sakakta: onde vizor cercevesi, arkada AAE var, arasi bos.
        _kask_bayrak(s, merkez, 0.140, [yan, 0.45, 0.25], [0, 1, 0], yuk=0.046)



def motosiklet(fren, tekerlek_aci=0.0, direksiyon=0.0, surucu=True):
    """AAE'nin KENDI motoru: Blender'da kurulup 14 Kas'ta onaylanan adventure
    model (assets/adv_motor/). Asagidaki _motosiklet_yaklasik() o model elime
    ulasmadan once elle kurulmus yaklasiktir; artik hicbir sahne kullanmiyor,
    sadece referans icin duruyor."""
    return adv_motor.motosiklet(fren, tekerlek_aci, direksiyon, surucu)


def _motosiklet_yaklasik(fren, tekerlek_aci=0.0, direksiyon=0.0, surucu=True):
    """fren 0-1: catal cokmesi + surucunun one yuklenmesi."""
    s = Sahne()
    cokme = 0.085 * fren
    # ADVENTURE olculer: aks arasi uzun, ON TEKER BUYUK (19-21 inc), uzun
    # suspansiyon yuzunden yuksek durus. Onceki olculer naked motosiklete
    # aitti ve AAE'nin adventure motoruna benzemiyordu.
    arka_z, on_z = -0.76, 0.80
    ON_R, ARKA_R = 0.385, 0.330

    # --- sasi / motor -----------------------------------------------------
    s.kutu([0.095, 0.44, arka_z + 0.36], [0.05, 0.10, 0.86], (62, 72, 84))      # salincak
    s.kutu([-0.095, 0.44, arka_z + 0.36], [0.05, 0.10, 0.86], (62, 72, 84))
    s.silindir([0.0, 0.48, -0.56], [0.0, 0.98, -0.26], 0.045, (190, 70, 60))     # amortisor
    s.silindir([0.11, 0.33, arka_z], [0.11, 0.33, arka_z], 0.12, (60, 60, 64))   # disli
    for yan in (0.105, -0.105):                                                  # zincir
        s.kutu([yan, 0.40, arka_z + 0.36], [0.02, 0.025, 0.78], (96, 100, 104))
    # Govde parcalari pahli: duz kutularin dik koseleri motosikleti oyuncak
    # gibi gosteriyordu. Depo one dogru incelir, kuyruk arkaya dogru daralir.
    # Blok daha dar ve kisa: eskisi govdenin ortasinda kalin bir levha
    # gibi duruyordu, sasi hic gorunmuyordu.
    _pahli(s, [0, 0.66, -0.02], [0.27, 0.40, 0.50], (72, 82, 94),
           on_olcek=0.86, arka_olcek=0.92)                                       # motor
    _pahli(s, [0, 0.72, 0.26], [0.30, 0.34, 0.10], (108, 116, 124), pah=0.20)    # radyator
    _pahli(s, [0, 0.42, 0.02], [0.30, 0.14, 0.46], (58, 64, 72),
           on_olcek=0.82, arka_olcek=0.88)                                       # karter
    for yan in (-1, 1):                                                          # koruma demiri
        s.silindir([yan * 0.17, 0.80, 0.30], [yan * 0.26, 0.52, 0.12], 0.022, (190, 70, 60))
        s.silindir([yan * 0.26, 0.52, 0.12], [yan * 0.22, 0.38, -0.20], 0.022, (190, 70, 60))
    # Depo iki parcali: ust kabuk genis, alt etek dizlerin degdigi yerde dar.
    _pahli(s, [0, 0.99, 0.12], [0.31, 0.21, 0.70], TURUNCU,
           pah=0.34, on_olcek=0.78)                                              # depo
    _pahli(s, [0, 0.84, 0.16], [0.22, 0.14, 0.54], (228, 112, 68),
           pah=0.30, on_olcek=0.84)                                              # depo etegi
    _pahli(s, [0, 1.08, 0.10], [0.21, 0.05, 0.52], (255, 142, 96),
           pah=0.40, on_olcek=0.76)                                              # depo ustu
    _pahli(s, [0, 0.95, -0.46], [0.25, 0.09, 0.56], (28, 28, 30),
           pah=0.36, on_olcek=0.84, arka_olcek=0.92)                             # sele
    _pahli(s, [0, 1.00, -0.80], [0.22, 0.13, 0.32], (28, 28, 30),
           pah=0.32, arka_olcek=0.68)                                            # kuyruk
    # Bagaj tasiyici: adventure motorun ikinci isareti.
    for yan in (-1, 1):
        s.silindir([yan * 0.17, 1.06, -0.62], [yan * 0.17, 1.06, -0.96], 0.016, KROM)
    s.silindir([-0.17, 1.06, -0.96], [0.17, 1.06, -0.96], 0.016, KROM)
    s.kutu([0, 0.89, -0.91], [0.15, 0.07, 0.05], KIRMIZI)                        # stop
    s.kutu([0, 0.74, -0.95], [0.16, 0.11, 0.02], (222, 222, 216))                # plaka
    # Egzoz arka tekerlegin YANINDAN gecer. Onceki guzergah tekerlek duzlemine
    # cok yakindi (x~0.17) ve aks hizasindaydi; lastige saplanmis gibi duruyordu.
    s.silindir([0.10, 0.40, 0.02], [0.19, 0.46, -0.30], 0.032, (150, 158, 164))  # egzoz borusu
    s.silindir([0.19, 0.46, -0.30], [0.26, 0.58, -0.58], 0.034, (150, 158, 164))
    # Susturucu 0.065 yaricaptaydi ve top gibi duruyordu.
    s.silindir([0.25, 0.56, -0.58], [0.27, 0.60, -0.98], 0.048,
               (124, 132, 140))                                                 # susturucu
    s.silindir([0.27, 0.60, -0.98], [0.275, 0.60, -1.01], 0.040, (40, 40, 44))   # cikis

    # --- on takim (direksiyonla birlikte doner) ---------------------------
    # Kontra dersi icin on takim AYRI bir sahnede kurulur: catal, teker,
    # camurluk, far, cam, gosterge, gidon ve aynalar birlikte donmeli.
    onk = Sahne()
    ucgen_y = 1.09 - cokme
    # Catal tek silindirdi, duz bir cubuk gibi duruyordu. Gercek catal iki
    # kademeli: ustte ince ic boru, altta kalin ayak, arasinda toz kecesi.
    for yan in (-1, 1):
        ust = np.array([yan * 0.095, ucgen_y, on_z - 0.11])
        alt = np.array([yan * 0.105, ON_R, on_z])
        orta = alt + (ust - alt) * 0.46
        onk.silindir(list(orta), list(ust), 0.030, KROM)               # ic boru
        onk.silindir(list(alt), list(orta + (ust - alt) * 0.04), 0.042,
                     (52, 56, 64))                                     # ayak
        onk.silindir(list(orta), list(orta + (ust - alt) * 0.05), 0.047,
                     (28, 30, 34))                                     # toz kecesi
        onk.kutu(list(alt + np.array([yan * 0.022, 0.085, -0.055])),
                 [0.045, 0.13, 0.10], (64, 70, 80))                    # kaliper kulagi
    onk.kutu([0, ucgen_y + 0.03, on_z - 0.13], [0.24, 0.08, 0.13], (62, 72, 84))   # ucgen
    onk.kutu([0, ucgen_y + 0.12, on_z - 0.22], [0.17, 0.09, 0.05], (24, 26, 30),
           R=donus([1, 0, 0], 0.5))                                              # gosterge govdesi
    onk.kutu([0, ucgen_y + 0.133, on_z - 0.195], [0.14, 0.06, 0.015], (30, 150, 180),
           R=donus([1, 0, 0], 0.5))                                              # ekran
    _camurluk(onk, on_z, yaricap=ON_R)                                           # camurluk
    # GAGA: adventure motorun en belirgin isareti, one uzanan burun. Once
    # elle yay kurulmaya calisildi ve ters yone bakan bozuk bir kanat cikti;
    # one dogru daralan pahli bir takoz hem dogru hem temiz duruyor.
    _pahli(onk, [0, 0.80 - cokme, on_z + 0.32], [0.27, 0.10, 0.52], TURUNCU,
           pah=0.42, on_olcek=0.52, arka_olcek=1.0,
           R=donus([1, 0, 0], -0.22))
    onk.kutu([0, 0.98 - cokme, on_z + 0.12], [0.26, 0.24, 0.14], (46, 50, 56))    # far govdesi
    onk.kutu([0, 0.98 - cokme, on_z + 0.195], [0.22, 0.19, 0.02], KREM)           # far cami
    onk.kutu([0, 1.09 - cokme, on_z + 0.02], [0.19, 0.10, 0.03], (146, 176, 196),
           R=donus([1, 0, 0], 0.45))                                             # on cam
    # Gidon: daha UZUN ve disa dogru — kask kamerasindan gorulebilsin
    gid_y, gid_z = 1.22 - cokme, on_z - 0.20
    onk.silindir([-0.42, gid_y, gid_z], [0.42, gid_y, gid_z], 0.022, KROM)
    for yan in (-1, 1):
        onk.silindir([yan * 0.26, gid_y, gid_z], [yan * 0.42, gid_y, gid_z + 0.03],
                   0.032, (32, 32, 34))                                          # tutamak
        onk.kutu([yan * 0.455, gid_y, gid_z + 0.03], [0.05, 0.05, 0.05], KROM)     # agirlik
        onk.kutu([yan * 0.385, gid_y + 0.05, gid_z + 0.13], [0.04, 0.20, 0.27],
                 TURUNCU, R=donus([0, 0, 1], yan * 0.26))                          # el korumasi
        onk.silindir([yan * 0.30, gid_y, gid_z + 0.02],
                   [yan * 0.40, gid_y - 0.01, gid_z + 0.14], 0.012, (190, 190, 190))
        onk.silindir([yan * 0.34, gid_y + 0.02, gid_z],                             # ayna kolu
                   [yan * 0.46, gid_y + 0.30, gid_z - 0.02], 0.016, (40, 40, 44))
        onk.kutu([yan * 0.47, gid_y + 0.33, gid_z - 0.02], [0.05, 0.13, 0.17],
               (70, 86, 104), R=donus([0, 1, 0], yan * 0.35))                    # ayna

    # On kontrol dersinde motosiklet surucusuz cizilir: kontrol
    # motordan inmis halde yapilir.
    kask_n = np.array([0.0, 1.0, 0.0])
    if surucu:
        # --- surucu -----------------------------------------------------------
        # Sasi adventure olculerine yukselince surucu eski yukseklikte kaldi
        # ve selenin icinde duruyordu: kalca, omuz ve bacaklar sele/basamak
        # hizasina tasindi. Kollar zaten gidonun degiskenine bagli.
        one = 0.12 * fren
        omuz_y, omuz_z = 1.63 - 0.10 * fren, -0.14 + one
        kalca_n = np.array([0.0, 1.15, -0.44])
        omuz_n = np.array([0.0, omuz_y, omuz_z])
        s.kure(kalca_n, 0.19, MONT, dilim=12, halka=7)
        s.silindir(kalca_n, omuz_n, 0.185, MONT, segment=14)
        s.kure(omuz_n, 0.19, MONT, dilim=12, halka=7)
        for yan in (-1, 1):
            s.silindir([yan * 0.19, omuz_y, omuz_z], [yan * 0.30, gid_y + 0.03, gid_z],
                       0.055, MONT)                                                  # kol
            s.kure([yan * 0.32, gid_y + 0.02, gid_z + 0.01], 0.055, (34, 34, 36))    # eldiven
            s.silindir([yan * 0.17, 1.11, -0.38], [yan * 0.26, 0.76, 0.08], 0.075, MONT)
            s.silindir([yan * 0.26, 0.76, 0.08], [yan * 0.24, 0.50, -0.04], 0.065, MONT)
            s.kutu([yan * 0.24, 0.44, 0.00], [0.10, 0.09, 0.26], (26, 26, 28))       # bot
            s.kutu([yan * 0.215, 0.39, 0.00], [0.09, 0.03, 0.14], KROM)              # basamak
        boyun = omuz_n + np.array([0.0, 0.13, 0.05])
        s.silindir(omuz_n, boyun, 0.085, (70, 80, 92), segment=10)
        kask_n = np.array([0.0, omuz_y + 0.27, omuz_z + 0.07])
        _kask(s, kask_n)

    _tekerlek(s, arka_z, tekerlek_aci, yaricap=ARKA_R, on=False)
    _tekerlek(onk, on_z, tekerlek_aci, yaricap=ON_R, on=True)

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
#  ISLAK ZEMIN  (yagmurda surus)
# ---------------------------------------------------------------------------
# Kaynaklar: Pirelli ve Honda HART yagmur rehberleri, RideApart, Ontario MTO
# motosiklet el kitabi. Tutunma kaybi icin kaynaklar %30 ile %50 arasinda
# ayrisiyor, bu yuzden sahne SAYI vermez: kuru ve islak fren mesafesini
# goreli olarak karsilastirir. Uzerinde hepsi hemfikir.
ISLAK_DONGU = 13.0


def _islak_palet():
    """Islak asfalt koyu ve yansiticidir, gok kursuni."""
    # Yagmurlu gunduz: kursuni ama okunur. Daha koyu degerlerde sahne gece
    # gibi duruyordu.
    return (152, 160, 170), (76, 98, 72), (78, 82, 90)


def _yagmur(d, t, adet=150):
    """Egik yagmur cizgileri. Her damla kendi hizinda duser."""
    rng = np.random.default_rng(17)
    for x0, y0, h in rng.random((adet, 3)):
        x = (x0 * (G + 220) - 110 + t * 70) % (G + 220) - 110
        y = (y0 * Y + t * (820 + h * 760)) % Y
        uz = 40 + h * 54
        d.line([(x, y), (x - 10, y + uz)], fill=(208, 222, 238, 64), width=2)


def _sprey(d, kamera, konum, guc):
    """Arka tekerin savurdugu su. Kameraya gore ekrana yansitilir."""
    if guc <= 0.02:
        return
    rng = np.random.default_rng(29)
    for dx, dy, dz, bb in rng.random((22, 4)):
        p = np.array([[konum[0] + (dx - 0.5) * 0.5,
                       0.05 + dy * 0.55 * guc,
                       konum[2] - 0.5 - dz * 2.2 * guc]])
        kn = kamera.kameraya(p)
        if kn[0, 2] <= 0.3:
            continue
        ex, ey = kamera.ekrana(kn)[0]
        r = (3 + bb * 7) * guc
        d.ellipse([ex - r, ey - r, ex + r, ey + r],
                  fill=(200, 212, 226, int(70 * guc)))


def kare_islak3b(t):
    """Islak zeminde fren: ayni hiz, cok daha uzun mesafe."""
    hiz, fren = s2.fren_evre(t)
    gok, cim, asfalt = _islak_palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    global _islak_s, _islak_tek
    _islak_s = (globals().get("_islak_s", 0.0) + hiz * 0.62) % 8.0
    _islak_tek = (globals().get("_islak_tek", 0.0) + hiz * 0.45) % (2 * math.pi)

    z = -30.0
    while z < 150:
        z2 = z + 6.0
        s.yuzey([[-60, 0, z], [60, 0, z], [60, 0, z2], [-60, 0, z2]], cim, katman=0)
        s.yuzey([[-4.2, 0.01, z], [4.2, 0.01, z], [4.2, 0.01, z2], [-4.2, 0.01, z2]],
                asfalt, katman=1)
        # Islak asfalt gogu yansitir: tekerlek izleri disinda parlak seritler.
        for x0, x1 in ((-3.9, -2.6), (-0.6, 0.6), (2.6, 3.9)):
            s.yuzey([[x0, 0.012, z], [x1, 0.012, z], [x1, 0.012, z2], [x0, 0.012, z2]],
                    (108, 118, 130), katman=1)
        for yan in (-1, 1):
            s.yuzey([[yan * 4.0, 0.02, z], [yan * 3.86, 0.02, z],
                     [yan * 3.86, 0.02, z2], [yan * 4.0, 0.02, z2]],
                    (188, 190, 190), katman=2)
        z = z2
    for i in range(-3, 22):                      # kesikli orta cizgi
        z = i * 8.0 - _islak_s
        s.yuzey([[-0.11, 0.02, z], [0.11, 0.02, z], [0.11, 0.02, z + 3.6],
                 [-0.11, 0.02, z + 3.6]], (198, 200, 198), katman=2)

    # --- kaygan yuzeyler: rogar kapagi ve yol boyasi ----------------------
    for i in range(-1, 8):
        zr = i * 26.0 - _islak_s * 0.98
        s.yuzey([[FREN_SERIT - 0.45, 0.025, zr], [FREN_SERIT + 0.45, 0.025, zr],
                 [FREN_SERIT + 0.45, 0.025, zr + 0.9],
                 [FREN_SERIT - 0.45, 0.025, zr + 0.9]], (122, 126, 132), katman=2)
    for i in range(-1, 6):                       # yaya gecidi benzeri boya
        zb = i * 38.0 - _islak_s * 0.98 + 14.0
        for k in range(4):
            s.yuzey([[-3.6 + k * 2.0, 0.024, zb], [-2.8 + k * 2.0, 0.024, zb],
                     [-2.8 + k * 2.0, 0.024, zb + 2.6],
                     [-3.6 + k * 2.0, 0.024, zb + 2.6]], (216, 218, 214), katman=2)

    # Bina kutleleri yoldan uzakta ve alcak: genis kamerada yakin ve yuksek
    # birakilinca kadrajin onune gecip motosikleti kapatiyorlardi.
    for i in range(-2, 18):
        z = i * 13.0 - _islak_s * 0.92
        for yan in (-1, 1):
            h = 3.4 + ((i * 7 + (yan + 1) * 3) % 9) * 1.1
            s.kutu([yan * (13.5 + (i % 3) * 2.6), h / 2, z + 4], [4.4, h, 5.4],
                   (92, 100, 114), katman=3)

    model, _, kask_n = motosiklet(fren, _islak_tek)
    yat = donus([1, 0, 0], 0.085 * fren)
    pivot = np.array([0, 0.31, 0.70])
    s.ekle(model, R=yat,
           t=pivot - yat @ pivot + np.array([FREN_SERIT, 0.0, 0.0]))

    # Fren sahnesinin kamerasi cok yakin: islak derste ileriyi, yani fren
    # mesafesini de gormek gerekiyor. Kask modu aynen korunur.
    if KAMERA_MODU == "kask":
        kamera, mod = _fren_kamera(t, fren, kask_n, yat, pivot)
    else:
        mod = "yan"
        kamera = Kamera([FREN_SERIT + 2.85 + 0.14 * math.sin(t * 0.21),
                         2.48 + 0.07 * math.sin(t * 0.13),
                         -6.1 + 0.20 * math.cos(t * 0.17)],
                        [FREN_SERIT + 0.15, 0.88, 3.1], G, Y, fov=50)
    s.ciz(d, kamera, gok)
    _sprey(d, kamera, np.array([FREN_SERIT, 0.0, 0.0]), hiz)
    _yagmur(d, t)

    # --- 2B gostergeler ----------------------------------------------------
    d.rounded_rectangle([G - 320, 470, G - 72, 612], 18, fill=(0, 0, 0, 170),
                        outline=(92, 102, 112), width=4)
    s2.yazi(d, (G - 196, 482), f"{int(hiz * 52)}", 82,
            KREM if hiz > 0.02 else YESIL, ortala=True)
    s2.yazi(d, (G - 196, 572), "km/h", 28, (150, 155, 160), ortala=True)

    # Fren mesafesi: kuru ve islak yan yana. Kaynaklar tutunma kaybini %30 ile
    # %50 arasinda verdigi icin sayi yazilmaz, oran gosterilir.
    # Blok saga yaslanir: ortada birakilinca motosikletin uzerine biniyordu.
    x0, yb = 430, 1150
    tam = G - x0 - 70
    s2.yazi(d, (x0, yb - 52), "FREN MESAFESİ", 34, (160, 168, 178))
    for i, (etiket, oran, renk) in enumerate(
            (("KURU", 0.54, YESIL), ("ISLAK", 1.00, KIRMIZI))):
        yy = yb + i * 76
        d.rounded_rectangle([x0, yy, x0 + tam, yy + 46], 10, fill=(255, 255, 255, 18))
        dolu = tam * oran * min(1.0, fren * 1.25 + 0.12)
        d.rounded_rectangle([x0, yy, x0 + dolu, yy + 46], 10, fill=renk)
        s2.yazi(d, (x0 + 14, yy + 6), etiket, 34, (16, 18, 20))
    if mod == "kask":
        s2.yazi(d, (G - 320, 636), "KASK KAMERASI", 26, TURUNCU)
    return im


# ---------------------------------------------------------------------------
#  KOR NOKTA  (SMIDSY: "pardon, seni gormedim")
# ---------------------------------------------------------------------------
# Kaynaklar: Motorcycle Safety CA, Bennetts BikeSocial, Motorcycle.com serit
# konumu rehberi, RideApart, webBikeWorld SMIDSY yazilari.
# Olcut: "surucunun gozlerini aynasinda goremiyorsan muhtemelen kor
# noktadasin." Kor nokta bir aracin YANINDA ve biraz ARKASINDA, komsu
# seritte olusur; kamyon ve SUV'de daha buyuktur.
KOR_DONGU = 14.0
KOR_ARABA_X = -2.0            # araba sol seritte
# Kor nokta kamasi, arabanin kendi cercevesinde (x, z) kose noktalari.
# Arabanin tam arkasi ic aynadan gorunur, o yuzden kama x=0.2'den baslar.
KOR_KAMA = [(0.2, 0.4), (0.2, -3.2), (4.5, -4.4), (4.5, 1.2)]


def kor_evre(t):
    """(bagil_z, durum) dondurur. Bagil z: motorun arabaya gore boyuna yeri."""
    u = (t % KOR_DONGU) / KOR_DONGU
    if u < 0.25:                       # arkadan yaklasir
        z = -12.0 + 7.0 * s2.yumusak(u / 0.25)
    elif u < 0.54:                     # kor noktada oyalanir
        z = -5.0 + 3.5 * s2.yumusak((u - 0.25) / 0.29)
    elif u < 0.72:                     # gecip gider
        z = -1.5 + 7.5 * s2.yumusak((u - 0.54) / 0.18)
    else:                              # onde, aynada net
        z = 6.0 + 7.0 * s2.yumusak((u - 0.72) / 0.28)
    return z, "gorunur" if not _kor_nokta_mi(z) else "kor"


def _kor_nokta_mi(bagil_z, bagil_x=None):
    """Motor kor nokta kamasinin icinde mi? Kamanin x=bagil_x kesitinde
    z araligi dogrusal aradegerlemeyle bulunur."""
    if bagil_x is None:
        bagil_x = FREN_SERIT - KOR_ARABA_X
    (x0, z_on0), (_, z_ar0), (x1, z_ar1), (_, z_on1) = KOR_KAMA
    if not x0 <= bagil_x <= x1:
        return False
    p = (bagil_x - x0) / (x1 - x0)
    return (z_ar0 + (z_ar1 - z_ar0) * p) <= bagil_z <= (z_on0 + (z_on1 - z_on0) * p)


def _araba(s, x, z, renk=(58, 92, 150)):
    """Basit binek arac: govde, kabin, camlar, tekerlekler, aynalar."""
    s.kutu([x, 0.62, z], [1.82, 0.74, 4.40], renk)
    s.kutu([x, 1.22, z - 0.25], [1.66, 0.52, 2.30],
           tuple(int(k * 0.82) for k in renk))
    for dz, boy in ((1.00, 1.58), (-1.45, 1.52)):            # on ve arka cam
        s.kutu([x, 1.24, z + dz], [boy, 0.44, 0.10], (36, 46, 60))
    for yan in (-1, 1):                                      # yan camlar
        s.kutu([x + yan * 0.84, 1.26, z - 0.25], [0.06, 0.40, 2.10], (36, 46, 60))
        s.kutu([x + yan * 1.02, 1.08, z + 0.95], [0.26, 0.14, 0.12],
               (30, 34, 40))                                 # dis ayna
        for dz in (1.35, -1.45):                             # tekerlekler
            s.kutu([x + yan * 0.86, 0.32, z + dz], [0.22, 0.60, 0.68], (26, 26, 28))
    s.kutu([x, 0.74, z + 2.22], [1.60, 0.26, 0.10], (236, 236, 228))   # far
    s.kutu([x, 0.78, z - 2.22], [1.56, 0.24, 0.10], (198, 52, 44))     # stop


def kare_kornokta3b(t):
    """Kusbakisi: motor arabanin kor noktasina girer ve cikar."""
    bagil_z, durum = kor_evre(t)
    gok, cim, asfalt = _palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    global _kor_s, _kor_tek
    _kor_s = (globals().get("_kor_s", 0.0) + 0.58) % 8.0
    _kor_tek = (globals().get("_kor_tek", 0.0) + 0.45) % (2 * math.pi)

    # Araba sabit sayilir, yol ve motor ona gore hareket eder.
    araba_z = 0.0
    motor_z = araba_z + bagil_z

    z = motor_z - 40.0
    while z < motor_z + 70:
        z2 = z + 5.0
        s.yuzey([[-90, 0, z], [90, 0, z], [90, 0, z2], [-90, 0, z2]], cim, katman=0)
        s.yuzey([[-4.2, 0.01, z], [4.2, 0.01, z], [4.2, 0.01, z2], [-4.2, 0.01, z2]],
                asfalt, katman=1)
        for yan in (-1, 1):
            s.yuzey([[yan * 4.0, 0.02, z], [yan * 3.86, 0.02, z],
                     [yan * 3.86, 0.02, z2], [yan * 4.0, 0.02, z2]],
                    (205, 205, 200), katman=2)
        z = z2
    for i in range(int((motor_z - 40) / 8), int((motor_z + 70) / 8) + 1):
        zc = i * 8.0 - _kor_s
        s.yuzey([[-0.11, 0.02, zc], [0.11, 0.02, zc], [0.11, 0.02, zc + 3.6],
                 [-0.11, 0.02, zc + 3.6]], (210, 210, 205), katman=2)

    # --- kor nokta kamasi: yola boyanir, durum rengini alir ---------------
    kama_renk = (226, 59, 46) if durum == "kor" else (46, 204, 113)
    s.yuzey([[KOR_ARABA_X + kx, 0.03, araba_z + kz] for kx, kz in KOR_KAMA],
            kama_renk, isiksiz=True, katman=2)

    _araba(s, KOR_ARABA_X, araba_z)
    model, _, _ = motosiklet(0.0, _kor_tek, 0.0)
    s.ekle(model, t=[FREN_SERIT, 0.0, motor_z])

    # --- kusbakisi takip kamerasi -----------------------------------------
    kamera = Kamera([FREN_SERIT - 1.4, 16.5, motor_z - 12.0],
                    [FREN_SERIT - 1.6, 0.0, motor_z + 2.0], G, Y, fov=46)
    s.ciz(d, kamera, gok)

    # --- 2B gostergeler ----------------------------------------------------
    etiket = "KÖR NOKTADA" if durum == "kor" else "AYNADA GÖRÜNÜYOR"
    renk = KIRMIZI if durum == "kor" else YESIL
    f = s2.font(44)
    tw = d.textlength(etiket, font=f)
    d.rounded_rectangle([(G - tw) / 2 - 32, 320, (G + tw) / 2 + 32, 404], 16,
                        fill=(0, 0, 0, 185), outline=renk, width=5)
    s2.yazi(d, (G / 2, 332), etiket, 44, renk, ortala=True)

    # Surucunun aynasi: motor ancak gorunurken ayna icinde belirir. Olcut
    # "gozlerini aynasinda goremiyorsan kor noktadasin" bunun gorsel karsiligi.
    # Panel SAGDA: araba sol seritte, solda birakilinca uzerine biniyordu.
    aw, ah = 300, 182
    ax, ay = G - 72 - aw, 470
    d.rounded_rectangle([ax, ay, ax + aw, ay + ah], 14, fill=(22, 26, 32, 210),
                        outline=(96, 106, 118), width=4)
    s2.yazi(d, (ax + 14, ay + 10), "SÜRÜCÜNÜN AYNASI", 26, (158, 166, 176))
    if durum == "gorunur":
        mx, my = ax + aw / 2, ay + 108
        d.ellipse([mx - 13, my - 42, mx + 13, my - 16], fill=KREM)      # kask
        d.rounded_rectangle([mx - 19, my - 18, mx + 19, my + 26], 8, fill=(108, 122, 140))
        d.rounded_rectangle([mx - 7, my + 22, mx + 7, my + 46], 5, fill=(32, 32, 36))
        s2.yazi(d, (mx, my + 52), "görünüyorsun", 24, YESIL, ortala=True)
    else:
        s2.yazi(d, (ax + aw / 2, ay + 76), "BOŞ", 52, KIRMIZI, ortala=True)
        s2.yazi(d, (ax + aw / 2, ay + 132), "seni göremiyor", 24, KIRMIZI, ortala=True)
    return im


# ---------------------------------------------------------------------------
#  DUSUK HIZDA MANEVRA  (U donusu)
# ---------------------------------------------------------------------------
# Kaynaklar: Team Arizona (motorcycletraining.com) dusuk hiz serisi, Rider
# Magazine (Quinn Redeker arka fren yazisi), Riding in the Zone, Women
# Riders Now. Hepsi ayni uc seyi soyluyor: bas ve gozler cikis noktasinda,
# debriyaj surtunme bolgesinde, arka fren hafif basili - on frene DOKUNMA.
MAN_DONGU = 13.0
MAN_R = 3.4                   # U donusu yaricapi (m) - yol genisligine sigar


def man_evre(t):
    """(konum, sapma, yatis, bakis_noktasi, durum) dondurur."""
    u = (t % MAN_DONGU) / MAN_DONGU
    if u < 0.23:                                   # duz giris
        p = u / 0.23
        konum = np.array([MAN_R, 0.0, -10.0 + 10.0 * s2.yumusak(p)])
        sapma, yatis = 0.0, 0.0
        hedef = np.array([MAN_R, 0.0, konum[2] + 9.0])
        durum = "bak" if p > 0.45 else "giris"
        if durum == "bak":                         # bas once doner
            hedef = np.array([-MAN_R, 0.0, 1.2])
    elif u < 0.69:                                 # U donusu
        p = s2.yumusak((u - 0.23) / 0.46)
        th = math.pi * p
        konum = np.array([MAN_R * math.cos(th), 0.0, MAN_R * math.sin(th)])
        sapma = -th
        yatis = 0.34 * min(1.0, p * 4.0) * min(1.0, (1 - p) * 4.0)
        ileri = min(math.pi, th + 1.25)            # bakis donusun ilerisinde
        hedef = np.array([MAN_R * math.cos(ileri) * 1.25, 0.0,
                          MAN_R * math.sin(ileri) * 1.25 - 1.5])
        durum = "donus"
    else:                                          # duz cikis
        p = s2.yumusak((u - 0.69) / 0.31)
        # Cikis kisa tutulur: 9.5 m gidince hem motosiklet hem bakis halkasi
        # kadrajin altindan cikiyordu.
        konum = np.array([-MAN_R, 0.0, -6.2 * p])
        sapma, yatis = -math.pi, 0.0
        hedef = np.array([-MAN_R, 0.0, max(konum[2] - 6.5, -10.4)])
        durum = "cikis"
    return konum, sapma, yatis, hedef, durum


MAN_DURUM = {
    "giris": ("YAVAŞLA, DEBRİYAJI AYIR", MAVI),
    "bak":   ("ÖNCE BAŞINI ÇEVİR", TURUNCU),
    "donus": ("SÜRTÜNME BÖLGESİ + ARKA FREN", YESIL),
    "cikis": ("BAKIŞ ÇIKIŞTA", MAVI),
}


def _bakis_oku(d, kamera, bas, uc, renk):
    """Yoldaki bakis cizgisi ve ucundaki halka."""
    n = 14
    nokta = np.array([bas + (uc - bas) * (i / n) + np.array([0, 0.05, 0])
                      for i in range(n + 1)])
    kn = kamera.kameraya(nokta)
    if kn[:, 2].min() <= 0.3:
        return
    ek = kamera.ekrana(kn)
    for i in range(0, n, 2):                       # kesikli
        d.line([tuple(ek[i]), tuple(ek[i + 1])], fill=(*renk, 150), width=7)
    ux, uy = ek[-1]
    d.ellipse([ux - 26, uy - 26, ux + 26, uy + 26], outline=(*renk, 235), width=7)


def kare_manevra3b(t):
    """Kusbakisi U donusu: bakis, surtunme bolgesi, arka fren."""
    konum, sapma, yatis, hedef, durum = man_evre(t)
    etiket, renk = MAN_DURUM[durum]
    gok, cim, asfalt = _palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    global _man_tek
    _man_tek = (globals().get("_man_tek", 0.0) + 0.16) % (2 * math.pi)

    s.yuzey([[-70, 0, -70], [70, 0, -70], [70, 0, 70], [-70, 0, 70]], cim, katman=0)
    z = -26.0
    while z < 26:
        z2 = z + 4.0
        s.yuzey([[-4.2, 0.01, z], [4.2, 0.01, z], [4.2, 0.01, z2], [-4.2, 0.01, z2]],
                asfalt, katman=1)
        for yan in (-1, 1):
            s.yuzey([[yan * 4.0, 0.02, z], [yan * 3.86, 0.02, z],
                     [yan * 3.86, 0.02, z2], [yan * 4.0, 0.02, z2]],
                    (205, 205, 200), katman=2)
        z = z2

    # --- donus cemberi: manevranin yol genisligine sigdigini gosterir ------
    N = 56
    for i in range(N):
        a0, a1 = math.pi * i / N, math.pi * (i + 1) / N
        for r0, r1 in ((MAN_R - 0.07, MAN_R + 0.07),):
            s.yuzey([[r0 * math.cos(a0), 0.022, r0 * math.sin(a0)],
                     [r1 * math.cos(a0), 0.022, r1 * math.sin(a0)],
                     [r1 * math.cos(a1), 0.022, r1 * math.sin(a1)],
                     [r0 * math.cos(a1), 0.022, r0 * math.sin(a1)]],
                    (156, 164, 174), katman=2)

    model, _, _ = motosiklet(0.0, _man_tek, 0.0)
    R = donus([0, 1, 0], sapma) @ donus([0, 0, 1], yatis)
    s.ekle(model, R=R, t=konum)

    kamera = Kamera([0.0, 19.5, -13.5], [0.0, 0.0, 0.6], G, Y, fov=47)
    s.ciz(d, kamera, gok)
    _bakis_oku(d, kamera, konum + np.array([0, 1.4, 0]),
               hedef + np.array([0, 0.1, 0]), TURUNCU)

    # --- 2B gostergeler ----------------------------------------------------
    f = s2.font(42)
    tw = d.textlength(etiket, font=f)
    d.rounded_rectangle([(G - tw) / 2 - 30, 318, (G + tw) / 2 + 30, 398], 16,
                        fill=(0, 0, 0, 185), outline=renk, width=5)
    s2.yazi(d, (G / 2, 330), etiket, 42, renk, ortala=True)

    # Uc kumanda: donuste debriyaj surtunme bolgesinde, arka fren hafif,
    # on fren hic. Kaynaklarin uzerinde birlestigi tek sey bu.
    aktif = durum == "donus"
    satirlar = (("DEBRİYAJ", "sürtünme bölgesi" if aktif else "ayrık", YESIL if aktif else (120, 128, 138)),
                ("ARKA FREN", "hafif basılı" if aktif else "serbest", YESIL if aktif else (120, 128, 138)),
                ("ÖN FREN", "DOKUNMA", KIRMIZI))
    px, py, pw = 70, 470, 420
    d.rounded_rectangle([px, py, px + pw, py + 266], 16, fill=(18, 22, 28, 205),
                        outline=(92, 102, 112), width=4)
    for i, (ad, deger, c) in enumerate(satirlar):
        yy = py + 22 + i * 80
        d.rounded_rectangle([px + 18, yy + 6, px + 28, yy + 54], 5, fill=c)
        s2.yazi(d, (px + 46, yy), ad, 36, KREM)
        s2.yazi(d, (px + 46, yy + 42), deger, 28, c)
    return im


# ---------------------------------------------------------------------------
#  GECE SURUSU  (farini asma)
# ---------------------------------------------------------------------------
# Kaynaklar: webBikeWorld "10 tips better night rider", RideApart gece
# surusu, Foremost, Dairyland, Brixton. Hepsinin ortak kurali: FARINI ASMA -
# farin gosterdigi mesafe icinde durabilmelisin.
# Sahnedeki durma mesafesi fizikten: tepki yolu + fren yolu,
# d = v*t_tepki + v^2 / (2a). Varsayimlar ekranda yaziyor cunku ikisi de
# surucuye ve zemine gore degisir.
GECE_DONGU = 14.0
FAR_MENZIL = 55.0             # kisa huzme yaklasik menzili (m)
GECE_TEPKI = 1.0              # saniye
GECE_YAVASLAMA = 7.0          # m/s^2, kuru asfalt


def gece_evre(t):
    """(hiz_kmh, durma_mesafesi_m) dondurur."""
    u = (t % GECE_DONGU) / GECE_DONGU
    if u < 0.46:                                   # hizlanir
        hiz = 50.0 + 45.0 * s2.yumusak(u / 0.46)
    elif u < 0.60:                                 # tepe hizda kalir
        hiz = 95.0
    else:                                          # yavaslar
        hiz = 95.0 - 45.0 * s2.yumusak((u - 0.60) / 0.40)
    v = hiz / 3.6
    return hiz, v * GECE_TEPKI + v * v / (2 * GECE_YAVASLAMA)


def _yol_cubugu(s, z, renk, yari=4.2, kalin=1.3):
    """Yola enlemesine isaret cubugu."""
    s.yuzey([[-yari, 0.04, z], [yari, 0.04, z],
             [yari, 0.04, z + kalin], [-yari, 0.04, z + kalin]],
            renk, isiksiz=True, katman=2)


def kare_gece3b(t):
    """Gece: far menzili ile durma mesafesi yan yana."""
    hiz, durma = gece_evre(t)
    asiyor = durma > FAR_MENZIL
    gok, cim, asfalt = (10, 13, 20), (18, 26, 20), (30, 32, 37)
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    global _gece_s, _gece_tek
    _gece_s = (globals().get("_gece_s", 0.0) + hiz / 3.6 / FPS) % 8.0
    _gece_tek = (globals().get("_gece_tek", 0.0) + 0.45) % (2 * math.pi)

    z = -14.0
    while z < 130:
        z2 = z + 5.0
        s.yuzey([[-70, 0, z], [70, 0, z], [70, 0, z2], [-70, 0, z2]], cim, katman=0)
        s.yuzey([[-4.2, 0.01, z], [4.2, 0.01, z], [4.2, 0.01, z2], [-4.2, 0.01, z2]],
                asfalt, katman=1)
        z = z2

    # --- far huzmesi: motordan baslar, menzilde biter ---------------------
    # Isiksiz cizilir, yoksa sahne isigiyla sonuyor ve "aydinlatma" hissi
    # kayboluyordu. Yakin uc parlak, uzak uc sonuk: huzme dagiliyor.
    DILIM = 10
    for i in range(DILIM):
        z0 = 1.2 + (FAR_MENZIL - 1.2) * i / DILIM
        z1 = 1.2 + (FAR_MENZIL - 1.2) * (i + 1) / DILIM
        # Far yaklasik 12 derece yayilir: 55 m'de yaklasik +-6 m.
        # 0.055 katsayisi cok dardi, huzme yolda seritten dar bir hali
        # gibi duruyordu.
        g0, g1 = 0.65 + z0 * 0.105, 0.65 + z1 * 0.105
        k = 1.0 - i / DILIM
        c = (int(46 + 150 * k), int(45 + 144 * k), int(36 + 112 * k))
        s.yuzey([[FREN_SERIT - g0, 0.03, z0], [FREN_SERIT + g0, 0.03, z0],
                 [FREN_SERIT + g1, 0.03, z1], [FREN_SERIT - g1, 0.03, z1]],
                c, isiksiz=True, katman=2)

    for i in range(-2, 24):                        # kesikli orta cizgi
        zc = i * 8.0 - _gece_s
        s.yuzey([[-0.11, 0.02, zc], [0.11, 0.02, zc], [0.11, 0.02, zc + 3.6],
                 [-0.11, 0.02, zc + 3.6]], (120, 120, 116), katman=2)

    # Mesafe karsilastirmasi 3B isaret cubuklariyla denendi: 55 ve 76 m'de
    # cubuklar ufka yakin, ince birer cizgi olarak kaliyor ve okunmuyordu.
    # Karsilastirma 2B cubuk grafige tasindi (ders 05'teki duzen).
    _yol_cubugu(s, FAR_MENZIL, (240, 236, 212), yari=5.6, kalin=1.6)

    model, _, _ = motosiklet(0.0, _gece_tek, 0.0)
    s.ekle(model, t=[FREN_SERIT, 0.0, 0.0])

    # Kamera motorun TAM ARKASINDA ve yuksekte: yandan bakinca motosiklet
    # kendi huzmesinin disinda kaliyor gibi duruyordu, uzaktaki isaret
    # cubuklari da goze carpmiyordu.
    # Kamera huzme EKSENINDE: yanal kayma huzmeyi carpik bir paralelkenar
    # gibi gosteriyordu.
    kamera = Kamera([FREN_SERIT, 5.2, -10.6],
                    [FREN_SERIT, 0.4, 26.0], G, Y, fov=47)
    s.ciz(d, kamera, gok)

    # --- 2B gostergeler ----------------------------------------------------
    d.rounded_rectangle([G - 320, 470, G - 72, 612], 18, fill=(0, 0, 0, 180),
                        outline=(92, 102, 112), width=4)
    s2.yazi(d, (G - 196, 482), f"{int(hiz)}", 82, KREM, ortala=True)
    s2.yazi(d, (G - 196, 572), "km/h", 28, (150, 155, 160), ortala=True)

    # Iki mesafe yan yana cubuk olarak. Olcek ikisinin buyugune gore,
    # boylece durma mesafesi farin otesine gectiginde bu gozle goruluyor.
    olcek = max(FAR_MENZIL, durma) * 1.08
    px, pw, yb = 70, G - 140, 1010
    s2.yazi(d, (px, yb - 48), "FAR MENZİLİ / DURMA MESAFESİ", 30, (158, 166, 176))
    for i, (ad, deger, c) in enumerate(
            ((f"FAR  {FAR_MENZIL:.0f} m", FAR_MENZIL, (240, 236, 212)),
             (f"DURMA  {durma:.0f} m", durma, KIRMIZI if asiyor else YESIL))):
        yy = yb + i * 78
        d.rounded_rectangle([px, yy, px + pw, yy + 56], 10, fill=(255, 255, 255, 20))
        d.rounded_rectangle([px, yy, px + pw * min(1.0, deger / olcek), yy + 56],
                            10, fill=c)
        s2.yazi(d, (px + 16, yy + 10), ad, 36, (16, 18, 20))
    s2.yazi(d, (px, yb + 166), f"{GECE_TEPKI:.0f} sn tepki + "
            f"{GECE_YAVASLAMA:.0f} m/s² fren varsayildi", 24, (120, 128, 138))

    if asiyor:
        uyari = "FARINI AŞIYORSUN"
        f = s2.font(46)
        tw = d.textlength(uyari, font=f)
        d.rounded_rectangle([(G - tw) / 2 - 32, 318, (G + tw) / 2 + 32, 404], 16,
                            fill=(118, 20, 16, 215), outline=KIRMIZI, width=5)
        s2.yazi(d, (G / 2, 330), uyari, 46, (255, 220, 215), ortala=True)
    return im


# ---------------------------------------------------------------------------
#  ON KONTROL ve LASTIK BASINCI  (MSF T-CLOCS)
# ---------------------------------------------------------------------------
# Kaynaklar: MSF T-CLOCS kontrol listesi, US Tire Manufacturers / MIC
# Motorcycle Tire Guide, Harley-Davidson T-CLOCS rehberi, Haynes.
# T-CLOCS: Tires, Controls, Lights, Oil, Chassis, Stands.
# Kritik nokta: yan duvardaki sayi lastigin AZAMI basincidir, motorun
# onerilen basinci degil. Onerilen deger el kitabinda ve sasi/salincak
# etiketindedir; basinc SOGUKKEN olculur.
# Isaret noktalari. Anahtar ders dosyasindaki sahne_fazlari ile eslesir.
KONTROL_NOKTA = {
    "lastik":  ("LASTİK ve JANT", (0.0, 0.33, 0.70), "diş, çatlak, cisim"),
    "kumanda": ("KUMANDALAR", (0.30, 1.07, 0.54), "kol, pedal, kablo, gaz"),
    "isik":    ("IŞIKLAR", (0.0, 0.98, 0.82), "far, stop, sinyal, korna"),
    "yag":     ("YAĞ ve SIVILAR", (0.0, 0.40, 0.02), "seviye ve kaçak"),
    "zincir":  ("ŞASİ ve ZİNCİR", (0.11, 0.31, -0.62), "gerginlik ve yağ"),
    "sehpa":   ("SEHPA", (0.14, 0.20, -0.26), "yay ve kilit"),
}
KONTROL_SIRA = list(KONTROL_NOKTA)
# Isaretin hangi saniyede hangi noktaya gectigi. Sabit dongu kullanilinca
# sahne ile ekrandaki adim kayiyordu: 6. saniyede yazi "basinci olc" derken
# halka IŞIKLAR'daydi. Zamanlar ders dosyasindan geliyor. Ders 09 v2'de
# adimlar T-CLOCS'un alti harfi oldugu icin eslesme artik 1:1.
KONTROL_FAZ = [(4.0, "lastik")]


def kontrol_zaman_ayarla(metin):
    """sahne_fazlari: "4:lastik, 35:kumanda, 37:isik, ..." """
    global KONTROL_FAZ
    if not metin:
        return
    f = []
    for parca in metin.split(","):
        t_str, _, ad = parca.strip().partition(":")
        ad = ad.strip()
        if ad not in KONTROL_NOKTA:
            raise SystemExit(f"HATA: bilinmeyen kontrol noktasi '{ad}'")
        try:
            f.append((float(t_str), ad))
        except ValueError:
            raise SystemExit(f"HATA: kontrol fazi zamani sayi olmali: '{t_str}'")
    KONTROL_FAZ = sorted(f)


def kontrol_evre(t):
    """(anahtar, gecis) dondurur. gecis: halkanin yerlesme carpani."""
    ad, bas = KONTROL_FAZ[0][1], KONTROL_FAZ[0][0]
    for z, a in KONTROL_FAZ:
        if t >= z:
            ad, bas = a, z
    return ad, s2.yumusak((t - bas) / 0.5)


def kare_kontrol3b(t):
    """On kontrol: motosikletin etrafinda T-CLOCS turu, sirayla alti nokta."""
    anahtar, gecis = kontrol_evre(t)
    ad, nokta, aciklama = KONTROL_NOKTA[anahtar]
    gok, cim, asfalt = _palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    s.yuzey([[-40, 0, -40], [40, 0, -40], [40, 0, 40], [-40, 0, 40]], asfalt,
            katman=1)
    for k in range(-6, 7):                         # zemin dokusu: park cizgileri
        s.yuzey([[k * 3.0 - 0.06, 0.01, -14], [k * 3.0 + 0.06, 0.01, -14],
                 [k * 3.0 + 0.06, 0.01, 14], [k * 3.0 - 0.06, 0.01, 14]],
                (92, 96, 102), katman=2)

    model, _, _ = motosiklet(0.0, 0.0, 0.0, surucu=False)   # motordan inilmis
    s.ekle(model)

    # Alti nokta da AYNI genis cercevede: bu bir tur dersi, isaret halkasi
    # motosikletin etrafinda dolasiyor. v1'de lastik fazinda kamera one
    # yaklasiyordu (ders lastik basinci dersiydi ve gostergeye yer gerekiyordu);
    # v2'de lastik alti maddeden biri, tek basina yakinlasmasi hata gibi
    # duruyordu.
    kamera = Kamera([5.15, 2.30, 3.95], [0.0, 0.72, 0.0], G, Y, fov=48)
    s.ciz(d, kamera, gok)

    # --- isaret halkasi: 3B noktanin ekrandaki yeri -----------------------
    kn = kamera.kameraya(np.array([nokta]))
    if kn[0, 2] > 0.3:
        hx, hy = kamera.ekrana(kn)[0]
        r = (46 + 10 * math.sin(t * 5)) * (0.4 + 0.6 * gecis)
        d.ellipse([hx - r, hy - r, hx + r, hy + r], outline=TURUNCU, width=8)
        d.ellipse([hx - r * 0.3, hy - r * 0.3, hx + r * 0.3, hy + r * 0.3],
                  fill=(*TURUNCU, 120))

    # --- 2B gostergeler ----------------------------------------------------
    f = s2.font(46)
    tw = d.textlength(ad, font=f)
    d.rounded_rectangle([(G - tw) / 2 - 32, 318, (G + tw) / 2 + 32, 404], 16,
                        fill=(0, 0, 0, 190), outline=TURUNCU, width=5)
    s2.yazi(d, (G / 2, 330), ad, 46, TURUNCU, ortala=True)
    s2.yazi(d, (G / 2, 416), aciklama, 34, (190, 198, 208), ortala=True)

    # Sol sutun: alti baslik, sirasi gelen vurgulanir. Arkasinda panel var,
    # yoksa motosikletin uzerine dustugunde okunmuyor.
    d.rounded_rectangle([56, 470, 392, 486 + len(KONTROL_NOKTA) * 52], 14,
                        fill=(14, 18, 24, 190), outline=(78, 86, 96), width=3)
    for k, nk in enumerate(KONTROL_SIRA):
        kad = KONTROL_NOKTA[nk][0]
        yy = 486 + k * 52
        aktif = nk == anahtar
        d.rounded_rectangle([64, yy, 76, yy + 34], 4,
                            fill=TURUNCU if aktif else (72, 80, 90))
        s2.yazi(d, (92, yy), kad, 30,
                KREM if aktif else (124, 132, 142))

    # Basinc gostergesi (DUSUK/DOGRU/AZAMI cubugu) v1'den kalmaydi ve dersi
    # hala bir lastik basinci videosu gibi gosteriyordu; v2'de kaldirildi.
    # Basincla ilgili ayrinti ders dosyasinin aciklamasinda duruyor.
    return im


# ---------------------------------------------------------------------------
#  KACINMA MANEVRASI  (swerve)
# ---------------------------------------------------------------------------
# Kaynaklar: TEAM Arizona kacinma yazilari, Women Riders Now "Avoiding
# Hazards", BC/Oregon motosiklet el kitaplari, MSF tabanli alistirma notlari.
# Uzerinde hepsinin birlestigi uc sey:
#   1. Kacinma IKI ayri gidon itisidir: biri yatirir, otekisi dogrultur.
#      Ikinci itis olmazsa motosiklet donmeye devam eder ve karsi seride cikar.
#   2. Kacinirken FREN YAPILMAZ. Once biri, sonra oteki.
#   3. Bakis engele degil, kacis bosluguna.
# NOT: Kaynaklarda gecen "su hizin ustunde kacinma frenden kisa surer" turu
# rakamlar ikincil kaynaklara dayaniyor, dogrulanamadigi icin kullanilmiyor.
KACINMA_DONGU = 13.0
KACINMA_HIZ = 50.0 / 3.6          # m/s
# Kacis SERIT ICINDE: engel seridin solunda, motosiklet saga kaciyor.
# Ilk kurulumda engel serit ortasindaydi ve motosiklet 2.5 m sola kacip
# orta cizgiyi geciyordu - KURALLAR.md bunu yasakliyor.
KACINMA_KAYMA = 1.55              # yanal kacis mesafesi (m, saga)
KACINMA_ENGEL_X = FREN_SERIT - 1.05


def kacinma_evre(t):
    """(engel_z, yanal, yatis, durum) dondurur."""
    u = t % KACINMA_DONGU
    engel_z = 56.0 - KACINMA_HIZ * u
    if u < 2.6:
        return engel_z, 0.0, 0.0, "karar"
    if u < 4.3:                                    # 1. itis: yatir
        p = s2.yumusak((u - 2.6) / 1.7)
        return engel_z, KACINMA_KAYMA * p, -0.34 * math.sin(math.pi * p), "itis1"
    if u < 5.6:                                    # 2. itis: dogrult
        p = s2.yumusak((u - 4.3) / 1.3)
        return engel_z, KACINMA_KAYMA, 0.26 * math.sin(math.pi * p), "itis2"
    if u < 9.0:
        return engel_z, KACINMA_KAYMA, 0.0, "duz"
    return engel_z, KACINMA_KAYMA, 0.0, "fren"


KACINMA_DURUM = {
    "karar": ("FREN YA DA KAÇIN — İKİSİ BİRDEN DEĞİL", TURUNCU),
    "itis1": ("1. İTİŞ · YATIR", MAVI),
    "itis2": ("2. İTİŞ · DOĞRULT", YESIL),
    "duz":   ("ENGEL GEÇİLDİ", YESIL),
    "fren":  ("ŞİMDİ FREN — DÜZ ÇİZGİDE", MAVI),
}


def _engel(s, x, z):
    """Yolda duran engel: koyu govde, uzerinde uyari seritleri."""
    s.kutu([x, 0.22, z], [1.30, 0.44, 0.90], (46, 46, 50))
    for i in range(3):
        s.kutu([x - 0.45 + i * 0.45, 0.45, z], [0.22, 0.04, 0.92], TURUNCU)


def kare_kacinma3b(t):
    """Kusbakisi: engel, iki itis ve ayri fren."""
    engel_z, yanal, yatis, durum = kacinma_evre(t)
    etiket, renk = KACINMA_DURUM[durum]
    gok, cim, asfalt = _palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    global _kac_s, _kac_tek
    _kac_s = (globals().get("_kac_s", 0.0) + KACINMA_HIZ / FPS) % 8.0
    _kac_tek = (globals().get("_kac_tek", 0.0) + 0.45) % (2 * math.pi)

    z = -16.0
    while z < 74:
        z2 = z + 5.0
        s.yuzey([[-80, 0, z], [80, 0, z], [80, 0, z2], [-80, 0, z2]], cim, katman=0)
        s.yuzey([[-4.2, 0.01, z], [4.2, 0.01, z], [4.2, 0.01, z2], [-4.2, 0.01, z2]],
                asfalt, katman=1)
        for yan in (-1, 1):
            s.yuzey([[yan * 4.0, 0.02, z], [yan * 3.86, 0.02, z],
                     [yan * 3.86, 0.02, z2], [yan * 4.0, 0.02, z2]],
                    (205, 205, 200), katman=2)
        z = z2
    for i in range(-2, 12):
        zc = i * 8.0 - _kac_s
        s.yuzey([[-0.11, 0.02, zc], [0.11, 0.02, zc], [0.11, 0.02, zc + 3.6],
                 [-0.11, 0.02, zc + 3.6]], (210, 210, 205), katman=2)

    if -3.0 < engel_z < 70.0:
        _engel(s, KACINMA_ENGEL_X, engel_z)

    motor_x = FREN_SERIT + yanal
    model, _, _ = motosiklet(0.0, _kac_tek, 0.0)
    s.ekle(model, R=donus([0, 0, 1], yatis), t=[motor_x, 0.0, 0.0])

    kamera = Kamera([FREN_SERIT + 0.5, 11.0, -13.0],
                    [FREN_SERIT + 0.35, 0.0, 10.0], G, Y, fov=46)
    s.ciz(d, kamera, gok)

    # Bakis engele degil kacis bosluguna: hedef, engelin YANINDAKI bosluk.
    if -3.0 < engel_z < 60.0 and durum in ("karar", "itis1", "itis2"):
        _bakis_oku(d, kamera, np.array([motor_x, 1.4, 0.4]),
                   np.array([FREN_SERIT + KACINMA_KAYMA, 0.1,
                             max(engel_z + 6.0, 8.0)]), TURUNCU)

    # --- 2B gostergeler ----------------------------------------------------
    f = s2.font(40)
    tw = d.textlength(etiket, font=f)
    d.rounded_rectangle([(G - tw) / 2 - 28, 318, (G + tw) / 2 + 28, 396], 16,
                        fill=(0, 0, 0, 190), outline=renk, width=5)
    s2.yazi(d, (G / 2, 330), etiket, 40, renk, ortala=True)

    # Iki kumanda asla ayni anda yanmaz: dersin butun mesaji bu.
    kacin = durum in ("itis1", "itis2")
    frende = durum == "fren"
    px, py, pw = 70, 466, 440
    d.rounded_rectangle([px, py, px + pw, py + 196], 16, fill=(16, 20, 26, 205),
                        outline=(92, 102, 112), width=4)
    for i, (ad, acik, c) in enumerate((("KAÇINMA", kacin, YESIL),
                                       ("FREN", frende, MAVI))):
        yy = py + 24 + i * 84
        d.rounded_rectangle([px + 20, yy, px + 34, yy + 52], 6,
                            fill=c if acik else (64, 70, 80))
        s2.yazi(d, (px + 52, yy), ad, 36, KREM if acik else (118, 126, 136))
        s2.yazi(d, (px + 52, yy + 40), "AÇIK" if acik else "kapalı", 26,
                c if acik else (104, 112, 122))
    return im


# ---------------------------------------------------------------------------
#  YOLCU ILE SURUS  (cift kisilik)
# ---------------------------------------------------------------------------
# Kaynaklar: Rider Magazine "Riding With A Passenger", Bennetts BikeSocial
# pillion rehberi, RevZilla, SGI (Saskatchewan) ve WA Road Safety el
# kitaplari, uretici kullanim kilavuzlari (on yuk ayari ve azami yuk).
# Uzerinde birlestikleri noktalar: on yuk artirilir, durma mesafesi uzar,
# yolcu ONCEDEN bilgilendirilir, ayaklar durakta bile basamakta kalir,
# yolcu motosikletle birlikte yatar, surucunun her hareketi yumusar.
# NOT: "tanka yaslanma" gibi tavsiyeler tek tek surucu gorusu; kullanilmadi.
YOLCU_DONGU = 13.2
YOLCU_NOKTA = {
    "onyuk":  ("ARKA ÖN YÜK", (0.0, 0.70, -0.42), "yolcu için artır"),
    "eller":  ("YOLCUNUN ELLERİ", (0.17, 1.16, -0.44), "bel ya da tutamak"),
    "ayak":   ("AYAKLAR BASAMAKTA", (0.23, 0.52, -0.52), "durakta bile inmez"),
    "yatis":  ("BİRLİKTE YATAR", (0.0, 1.66, -0.56), "kendi başına kaymaz"),
    "fren":   ("ERKEN VE YUMUŞAK", (0.0, 0.33, 0.70), "mesafe uzar"),
}
YOLCU_SIRA = list(YOLCU_NOKTA)
YOLCU_FAZ = [(4.0, "onyuk")]


def yolcu_faz_ayarla(metin):
    """sahne_fazlari: "4:onyuk, 11:eller, ..." """
    global YOLCU_FAZ
    if not metin:
        return
    f = []
    for parca in metin.split(","):
        t_str, _, ad = parca.strip().partition(":")
        ad = ad.strip()
        if ad not in YOLCU_NOKTA:
            raise SystemExit(f"HATA: bilinmeyen yolcu noktasi '{ad}'")
        f.append((float(t_str), ad))
    YOLCU_FAZ = sorted(f)


def yolcu_evre(t):
    ad, bas = YOLCU_FAZ[0][1], YOLCU_FAZ[0][0]
    for z, a in YOLCU_FAZ:
        if t >= z:
            ad, bas = a, z
    return ad, s2.yumusak((t - bas) / 0.5)


def _yolcu(s, mont=(96, 110, 128)):
    """Sele arkasinda oturan yolcu: kalca, govde, kask, kollar ve bacaklar."""
    # AAE'nin onayli ADV modeline gore olculdu (adv_motor):
    #   arka sele yuzeyi  y = 1.00, z = -0.85..-0.55
    #   surucunun govdesi z = -0.49..0.29, kaski y = 1.83
    #   arka bagaj/canta  z = -1.10..-0.70, y = 1.34'e kadar
    # Eski degerler (kalca z=-0.84) yaklasik motora aitti; yolcu bagajin
    # icinde oturuyor, bacaklari da bosluga sarkiyordu.
    kalca = np.array([0.0, 1.15, -0.70])
    omuz = np.array([0.0, 1.53, -0.60])
    s.kure(kalca, 0.18, mont, dilim=12, halka=7)
    s.silindir(kalca, omuz, 0.175, mont, segment=14)
    s.kure(omuz, 0.18, mont, dilim=12, halka=7)
    _kask(s, omuz + np.array([0.0, 0.27, 0.06]), kabuk=(216, 220, 226),
          aksan=(58, 150, 196))
    for yan in (-1, 1):
        # eller surucunun belinde (surucunun govdesi z = -0.40 civarinda)
        s.silindir([yan * 0.17, 1.51, -0.58], [yan * 0.20, 1.22, -0.33],
                   0.052, mont)                                   # kol
        s.kure([yan * 0.20, 1.21, -0.31], 0.052, (34, 34, 36))    # eldiven
        # Kalca (1.08, -0.66) ile basamak (0.48, -0.38) arasi 66 cm; 45+43 cm'lik
        # iki uzuv bu araligi ancak diz ONE cikarak kapatir. Diz duz hat uzerinde
        # birakilinca bacak tek bir boru gibi gorunuyordu.
        s.silindir([yan * 0.17, 1.08, -0.66], [yan * 0.30, 0.91, -0.25],
                   0.072, mont)                                   # ust bacak
        s.silindir([yan * 0.30, 0.91, -0.25], [yan * 0.28, 0.54, -0.36],
                   0.060, mont)                                   # alt bacak
        s.kure([yan * 0.30, 0.91, -0.25], 0.072, mont, dilim=10, halka=6)  # diz
        s.kutu([yan * 0.28, 0.48, -0.33], [0.10, 0.09, 0.24], (26, 26, 28))
        s.kutu([yan * 0.255, 0.43, -0.36], [0.09, 0.03, 0.12], KROM)  # basamak


def kare_yolcu3b(t):
    """Yan gorunum: yolcuyla birlikte duran motosiklet, sirayla kurallar."""
    anahtar, gecis = yolcu_evre(t)
    ad, nokta, aciklama = YOLCU_NOKTA[anahtar]
    gok, cim, asfalt = _palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    global _yol_tek
    _yol_tek = (globals().get("_yol_tek", 0.0) + 0.42) % (2 * math.pi)

    z = -24.0
    while z < 90:
        z2 = z + 5.0
        s.yuzey([[-60, 0, z], [60, 0, z], [60, 0, z2], [-60, 0, z2]], cim, katman=0)
        s.yuzey([[-4.2, 0.01, z], [4.2, 0.01, z], [4.2, 0.01, z2], [-4.2, 0.01, z2]],
                asfalt, katman=1)
        for yan in (-1, 1):
            s.yuzey([[yan * 4.0, 0.02, z], [yan * 3.86, 0.02, z],
                     [yan * 3.86, 0.02, z2], [yan * 4.0, 0.02, z2]],
                    (205, 205, 200), katman=2)
        z = z2

    # Yolcu yuku arkayi cokertir: suspansiyon farki gozle gorulsun.
    cokme = 0.055
    model, _, _ = motosiklet(0.0, _yol_tek, 0.0)
    _yolcu(model)
    s.ekle(model, R=donus([1, 0, 0], -0.030), t=[FREN_SERIT, -cokme, 0.0])

    # 4.35 m'de motosiklet kadraja sigmiyor, kasklar ustten tekerlekler
    # alttan kesiliyordu. Iki kisi birden gorunmeli.
    kamera = Kamera([FREN_SERIT + 6.9, 2.15, 1.30],
                    [FREN_SERIT - 0.05, 0.95, -0.35], G, Y, fov=45)
    s.ciz(d, kamera, gok)

    kn = kamera.kameraya(np.array([[FREN_SERIT + nokta[0], nokta[1] - cokme,
                                    nokta[2]]]))
    if kn[0, 2] > 0.3:
        hx, hy = kamera.ekrana(kn)[0]
        r = (44 + 9 * math.sin(t * 5)) * (0.4 + 0.6 * gecis)
        d.ellipse([hx - r, hy - r, hx + r, hy + r], outline=TURUNCU, width=8)

    # --- 2B gostergeler ----------------------------------------------------
    f = s2.font(44)
    tw = d.textlength(ad, font=f)
    d.rounded_rectangle([(G - tw) / 2 - 30, 318, (G + tw) / 2 + 30, 400], 16,
                        fill=(0, 0, 0, 190), outline=TURUNCU, width=5)
    s2.yazi(d, (G / 2, 330), ad, 44, TURUNCU, ortala=True)
    s2.yazi(d, (G / 2, 414), aciklama, 32, (190, 198, 208), ortala=True)

    d.rounded_rectangle([56, 480, 408, 496 + len(YOLCU_SIRA) * 52], 14,
                        fill=(14, 18, 24, 190), outline=(78, 86, 96), width=3)
    for k, nk in enumerate(YOLCU_SIRA):
        yy = 496 + k * 52
        aktif = nk == anahtar
        d.rounded_rectangle([64, yy, 76, yy + 34], 4,
                            fill=TURUNCU if aktif else (72, 80, 90))
        s2.yazi(d, (92, yy), YOLCU_NOKTA[nk][0], 28,
                KREM if aktif else (124, 132, 142))
    return im


# ---------------------------------------------------------------------------
#  NE KADAR ILERI BAKIYORSUN
# ---------------------------------------------------------------------------
# Dis kaynak rakami YOK. Varsayimlar ekranda ve ders 08/18 ile ayni:
# 1 sn tepki, 7 m/s^2 fren (kuru asfalt).
#
# BAKIS MESAFESI (n saniye ileri bakmak)  = n * v
# DURMA MESAFESI (ders 18)                = v*t_tepki + v^2/(2a)
# Bakis hizla DOGRUSAL buyur, durma hizin KARESIYLE. Yani sabit bir
# "x saniye ileri bak" aliskanligi hiz arttikca yetersizlesir.
#
# Esik noktasi kapali formulle cikiyor:
#   n*v = v*t_tepki + v^2/(2a)  ->  v = 2a*(n - t_tepki) = 14*(n-1)
#     2 saniye -> 14,0 m/s =  50,4 km/h'ye kadar yeter
#     3 saniye -> 28,0 m/s = 100,8 km/h'ye kadar
#     4 saniye -> 42,0 m/s = 151,2 km/h'ye kadar
#   Tersi: gereken saniye = 1 + v/14
#
# 90 km/h'de durma 69,6 m. Iki saniyelik bakis 50 m: 19,6 m EKSIK, yani
# gordugun yere duramiyorsun. Uc saniye 75 m, payin yalnizca 5,4 m.
#
# Sahne: yola iki sey ciziliyor - kirmizi kesikli bant DURMA mesafesi,
# parlak kapi ise NEREYE BAKTIGIN. Kapi bandin icinde kaliyorsa
# gordugun yere duramiyorsun demektir.
BAKIS_TEPKI = 1.0
BAKIS_IVME = 7.0
BAKIS_ESIK = ((2, 50.4), (3, 100.8), (4, 151.2))

BAKIS_NOKTA = {
    "metre":  ("SANİYEDE 25 METRE", "90 km/h böyle bir şey", 90.0, 2.0),
    "durma":  ("DURMAN 69,6 METRE", "1 sn tepki + 7 m/s² fren", 90.0, 2.0),
    "eksik":  ("2 SANİYE YETMİYOR", "50 m bakış, 69,6 m durma", 90.0, 2.0),
    "elli":   ("2 SANİYE 50 km/h'YE KADAR", "tam tamına yeter", 50.0, 2.0),
    "uc":     ("3 SANİYE 100'E KADAR", "90'da payın 5,4 m", 90.0, 3.0),
    "tara":   ("4 SANİYE VE TARAMA", "uzak → yakın → ayna → uzak", 90.0, 4.0),
}
BAKIS_SIRA = list(BAKIS_NOKTA)
BAKIS_FAZ = [(4.0, "metre")]


def bakis_faz_ayarla(metin):
    """sahne_fazlari: "4:metre, 11:durma, ..." """
    global BAKIS_FAZ
    if not metin:
        return
    f = []
    for parca in metin.split(","):
        t_str, _, ad = parca.strip().partition(":")
        ad = ad.strip()
        if ad not in BAKIS_NOKTA:
            raise SystemExit(f"HATA: bilinmeyen bakis noktasi '{ad}'")
        f.append((float(t_str), ad))
    BAKIS_FAZ = sorted(f)


def bakis_evre(t):
    ad, bas = BAKIS_FAZ[0][1], BAKIS_FAZ[0][0]
    for z, a in BAKIS_FAZ:
        if t >= z:
            ad, bas = a, z
    return ad, bas


def bakis_durma(kmh):
    v = kmh / 3.6
    return v * BAKIS_TEPKI + v * v / (2 * BAKIS_IVME)


def _bakis_kapi(s, x, z, renk):
    """Yolun uzerine kurulan parlak kapi: suan NEREYE baktigin.

    Ilk surum ince ve alcakti; 50-100 m'de ufka karisip hic okunmuyordu.
    Direkler kalinlasti, yukseldi ve yola enine parlak bir bant eklendi -
    uzakta kapiyi degil banti goruyorsun."""
    for yan in (-1, 1):
        s.kutu([x + yan * 1.90, 1.30, z], [0.26, 2.60, 0.26], renk)
    s.kutu([x, 2.52, z], [4.06, 0.26, 0.22], renk)
    s.yuzey([[x - 1.95, 0.032, z - 0.35], [x + 1.95, 0.032, z - 0.35],
             [x + 1.95, 0.032, z + 0.35], [x - 1.95, 0.032, z + 0.35]],
            renk, katman=2)


def kare_bakis3b(t):
    """Yolda iki olcu: kirmizi bant DURMA mesafesi, parlak kapi BAKIS mesafesi."""
    anahtar, _ = bakis_evre(t)
    etiket, aciklama, kmh, saniye = BAKIS_NOKTA[anahtar]
    v = kmh / 3.6
    durma = bakis_durma(kmh)
    bakis = v * saniye
    pay = bakis - durma
    yeterli = pay >= 0.0
    gok, cim, asfalt = _palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    global _bak_s, _bak_tek
    _bak_s = (globals().get("_bak_s", 0.0) + v / FPS) % 8.0
    _bak_tek = (globals().get("_bak_tek", 0.0)
                + v / (FPS * adv_motor.ON_R)) % (2 * math.pi)

    z = -20.0
    while z < 400:
        z2 = z + (6.0 if z < 90 else 30.0)
        s.yuzey([[-95, 0, z], [95, 0, z], [95, 0, z2], [-95, 0, z2]], cim,
                katman=0)
        s.yuzey([[-4.2, 0.01, z], [4.2, 0.01, z], [4.2, 0.01, z2],
                 [-4.2, 0.01, z2]], asfalt, katman=1)
        z = z2
    for yan in (-1, 1):
        zz = -20.0
        while zz < 160:
            z2 = zz + 4.0
            s.yuzey([[yan * 4.0, 0.02, zz], [yan * 3.86, 0.02, zz],
                     [yan * 3.86, 0.02, z2], [yan * 4.0, 0.02, z2]],
                    (205, 205, 200), katman=2)
            zz = z2
    for i in range(-3, 26):
        zc = i * 8.0 - _bak_s
        s.yuzey([[-0.11, 0.02, zc], [0.11, 0.02, zc], [0.11, 0.02, zc + 3.6],
                 [-0.11, 0.02, zc + 3.6]], (210, 210, 205), katman=2)

    # DURMA mesafesi: serit ortasinda kirmizi kesikli bant.
    # Duz boyarsak yolu yeniden boyamis gibi oluyor; kesikli olunca olcu
    # oldugu okunuyor.
    zz = 1.5
    while zz < durma:
        z2 = min(zz + 1.3, durma)
        s.yuzey([[FREN_SERIT - 0.95, 0.03, zz], [FREN_SERIT + 0.95, 0.03, zz],
                 [FREN_SERIT + 0.95, 0.03, z2], [FREN_SERIT - 0.95, 0.03, z2]],
                (178, 54, 46), katman=2)
        zz += 2.6
    # Bandin bittigi yer: enine cizgi
    s.yuzey([[FREN_SERIT - 1.9, 0.031, durma],
             [FREN_SERIT + 1.9, 0.031, durma],
             [FREN_SERIT + 1.9, 0.031, durma + 0.40],
             [FREN_SERIT - 1.9, 0.031, durma + 0.40]], (226, 86, 74), katman=2)

    if bakis < 320.0:
        _bakis_kapi(s, FREN_SERIT, bakis, YESIL if yeterli else KIRMIZI)

    model, _, _ = motosiklet(0.0, _bak_tek, 0.0)
    s.ekle(model, t=[FREN_SERIT, 0.0, 0.0])

    # Kamera yuksek: bu dersin butun olayi 50-100 m'deki kapinin kirmizi
    # bandin icinde mi disinda mi oldugunu GORMEK. Alcak kamerada o mesafe
    # ufka sikisip okunmuyordu.
    # 12,5 m'ye cikarilinca kapi okundu ama motosiklet alt yazi bandinin
    # altina dustu. Kapi zaten buyutuldugu icin o kadar yuksege gerek yok:
    # 6,4 m hem motosikleti bandin ustunde tutuyor hem 100 m'yi gosteriyor.
    kamera = Kamera([FREN_SERIT + 0.7, 6.4, -18.5], [FREN_SERIT - 0.4, 0.7, 36.0],
                    G, Y, fov=46)
    s.ciz(d, kamera, gok)

    # --- 2B gostergeler -----------------------------------------------------
    ust_renk = KIRMIZI if not yeterli else (
        TURUNCU if pay < 10.0 else YESIL)
    f = s2.font(40)
    tw = d.textlength(etiket, font=f)
    d.rounded_rectangle([(G - tw) / 2 - 28, 318, (G + tw) / 2 + 28, 396], 16,
                        fill=(0, 0, 0, 190), outline=ust_renk, width=5)
    s2.yazi(d, (G / 2, 330), etiket, 40, ust_renk, ortala=True)
    s2.yazi(d, (G / 2, 404), aciklama, 28, (176, 182, 190), ortala=True)

    d.rounded_rectangle([G - 330, 470, G - 72, 612], 18, fill=(0, 0, 0, 178),
                        outline=(92, 102, 112), width=4)
    s2.yazi(d, (G - 201, 482), f"{kmh:.0f}", 76, KREM, ortala=True)
    s2.yazi(d, (G - 201, 572), "km/h", 26, (150, 155, 160), ortala=True)

    px, py, pw = 62, 470, 480
    d.rounded_rectangle([px, py, px + pw, py + 352], 16, fill=(16, 20, 26, 210),
                        outline=(92, 102, 112), width=4)
    s2.yazi(d, (px + 22, py + 12), "BAKIŞ ↔ DURMA", 26, (150, 155, 162))
    s2.yazi(d, (px + 22, py + 42), "1 sn tepki · 7 m/s² fren varsayıldı", 22,
            (124, 132, 142))

    bx, bw = px + 22, pw - 44
    olcek = max(durma, bakis) * 1.12
    for i, (ad, deger, c) in enumerate(
            ((f"DURMA", durma, (200, 70, 60)),
             (f"BAKIŞ  {saniye:.0f} sn", bakis, YESIL if yeterli else KIRMIZI))):
        yy = py + 84 + i * 72
        s2.yazi(d, (bx, yy), ad, 26, (190, 196, 204))
        g = d.textlength(f"{deger:.1f} m".replace(".", ","), font=s2.font(26))
        s2.yazi(d, (bx + bw - g, yy), f"{deger:.1f} m".replace(".", ","), 26, c)
        d.rounded_rectangle([bx, yy + 32, bx + bw * deger / olcek, yy + 56], 5,
                            fill=c)

    etik = (f"PAY +{pay:.1f} m" if yeterli else f"EKSİK {-pay:.1f} m")
    s2.yazi(d, (bx, py + 234), etik.replace(".", ","), 36,
            YESIL if yeterli else KIRMIZI)
    if not yeterli:
        uyari = "GÖRDÜĞÜNE DURAMAZSIN"
        ux = bx + d.textlength(etik.replace(".", ","), font=s2.font(36)) + 22
        ug = d.textlength(uyari, font=s2.font(24))
        d.rounded_rectangle([ux, py + 238, ux + ug + 22, py + 274], 8,
                            fill=(120, 26, 22, 235), outline=KIRMIZI, width=3)
        s2.yazi(d, (ux + 11, py + 243), uyari, 24, (255, 214, 210))

    s2.yazi(d, (bx, py + 288), "kaç saniye, hangi hıza kadar yeter:", 23,
            (140, 148, 158))
    pars = []
    for sn, lim in BAKIS_ESIK:
        pars.append(f"{sn} sn → {lim:.0f}".replace(".", ","))
    s2.yazi(d, (bx, py + 314), "   ·   ".join(pars) + " km/h", 24, KREM)
    return im




# ---------------------------------------------------------------------------
#  DURMA MESAFESI: HIZ IKIYE KATLANINCA
# ---------------------------------------------------------------------------
# Varsayimlar EKRANDA yazili ve ders 08 ile ayni: 1 sn tepki suresi,
# 7 m/s^2 fren ivmesi (kuru asfalt, yetkin surucu).
#
#   d = v*t_tepki + v^2/(2a)
#   Tepki parcasi hizla ORANTILI, fren parcasi hizin KARESIYLE buyur.
#     50 km/h -> 13,89 + 13,78 = 27,67 m
#     70 km/h -> 19,44 + 27,01 = 46,45 m
#     90 km/h -> 25,00 + 44,64 = 69,64 m
#
# DERSIN VURUCU RAKAMI:
#   50 ile giden tam 27,67 m'de duruyor. Ayni noktada 70 ile giden:
#     tepkide 19,44 m harcamis, frende 8,22 m kalmis
#     v = sqrt(19,44^2 - 2*7*8,22) = 16,22 m/s = 58,4 km/h
#   Yani 50'nin TAM DURDUGU yerde 70 hala 58 km/h yapiyor. Hiz %40 artti,
#   ama o noktadaki hiz sifirdan 58'e cikti.
#
# Sahne engeli tam 27,67 m'ye koyuyor: 50 ile giden burnu degdirmeden
# duruyor, 70 ile giden 58 km/h ile variyor.
DURMA_TEPKI = 1.0
DURMA_IVME = 7.0
DURMA_HEDEF = 27.67                     # 50 km/h'nin durma mesafesi (m)
DURMA_DONGU = 7.0

DURMA_NOKTA = {
    "iki":    ("İKİ PARÇA", "tepki + fren", 50.0),
    "kare":   ("FREN HIZIN KARESİYLE", "tepki ise orantılı", 50.0),
    "elli":   ("50 km/h → 27,7 m", "13,9 tepki + 13,8 fren", 50.0),
    "yetmis": ("70 km/h → 46,5 m", "19,4 tepki + 27,0 fren", 70.0),
    "carpma": ("50'NİN DURDUĞU YERDE", "70 hâlâ 58 km/h", 70.0),
    "secim":  ("HIZI GÖRÜŞÜNE GÖRE SEÇ", "göremediğin yere hız yok", 50.0),
}
DURMA_SIRA = list(DURMA_NOKTA)
DURMA_FAZ = [(4.0, "iki")]


def durma_faz_ayarla(metin):
    """sahne_fazlari: "4:iki, 11:kare, ..." """
    global DURMA_FAZ
    if not metin:
        return
    f = []
    for parca in metin.split(","):
        t_str, _, ad = parca.strip().partition(":")
        ad = ad.strip()
        if ad not in DURMA_NOKTA:
            raise SystemExit(f"HATA: bilinmeyen durma noktasi '{ad}'")
        f.append((float(t_str), ad))
    DURMA_FAZ = sorted(f)


def durma_evre(t):
    ad, bas = DURMA_FAZ[0][1], DURMA_FAZ[0][0]
    for z, a in DURMA_FAZ:
        if t >= z:
            ad, bas = a, z
    return ad, bas


def durma_mesafe(kmh):
    """(tepki yolu, fren yolu, toplam) - varsayimlar ekranda yazili."""
    v = kmh / 3.6
    return v * DURMA_TEPKI, v * v / (2 * DURMA_IVME), \
        v * DURMA_TEPKI + v * v / (2 * DURMA_IVME)


def _durma_an(kmh, u):
    """(engele kalan mesafe, hiz m/s, evre). Engel tam DURMA_HEDEF'te."""
    v0 = kmh / 3.6
    if u < 1.2:                                   # yaklasma
        return DURMA_HEDEF + v0 * (1.2 - u), v0, "seyir"
    if u < 1.2 + DURMA_TEPKI:                     # tepki: hiz dusmuyor
        return DURMA_HEDEF - v0 * (u - 1.2), v0, "tepki"
    s = u - 1.2 - DURMA_TEPKI                     # fren
    dur_s = v0 / DURMA_IVME
    s = min(s, dur_s)
    v = v0 - DURMA_IVME * s
    kalan = DURMA_HEDEF - v0 * DURMA_TEPKI - (v0 * s - DURMA_IVME * s * s / 2)
    if kalan <= 0.0:                              # engele vardi
        carp = math.sqrt(max(0.0, v0 * v0 - 2 * DURMA_IVME
                             * (DURMA_HEDEF - v0 * DURMA_TEPKI)))
        return 0.0, carp, "carpma"
    return kalan, v, "fren"


def kare_durma3b(t):
    """Engel 27,7 m'de: 50 ile giden duruyor, 70 ile giden 58 km/h ile variyor."""
    anahtar, faz_bas = durma_evre(t)
    etiket, aciklama, kmh = DURMA_NOKTA[anahtar]
    u = (t - faz_bas) % DURMA_DONGU
    kalan, v, evre = _durma_an(kmh, u)
    gok, cim, asfalt = _palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    global _dur_s, _dur_tek
    _dur_s = (globals().get("_dur_s", 0.0) + v / FPS) % 8.0
    _dur_tek = (globals().get("_dur_tek", 0.0)
                + v / (FPS * adv_motor.ON_R)) % (2 * math.pi)

    z = -20.0
    while z < 200:
        z2 = z + (6.0 if z < 90 else 20.0)
        s.yuzey([[-95, 0, z], [95, 0, z], [95, 0, z2], [-95, 0, z2]], cim,
                katman=0)
        s.yuzey([[-4.2, 0.01, z], [4.2, 0.01, z], [4.2, 0.01, z2],
                 [-4.2, 0.01, z2]], asfalt, katman=1)
        z = z2
    for yan in (-1, 1):
        zz = -20.0
        while zz < 110:
            z2 = zz + 4.0
            s.yuzey([[yan * 4.0, 0.02, zz], [yan * 3.86, 0.02, zz],
                     [yan * 3.86, 0.02, z2], [yan * 4.0, 0.02, z2]],
                    (205, 205, 200), katman=2)
            zz = z2
    for i in range(-3, 16):
        zc = i * 8.0 - _dur_s
        s.yuzey([[-0.11, 0.02, zc], [0.11, 0.02, zc], [0.11, 0.02, zc + 3.6],
                 [-0.11, 0.02, zc + 3.6]], (210, 210, 205), katman=2)

    # 50'nin durma noktasi yola isaretli: karsilastirmanin capasi bu
    isaret_z = kalan + 2.6
    if 0.0 < isaret_z < 90.0:
        for yan in (-1, 1):
            s.yuzey([[yan * 1.6, 0.03, isaret_z], [yan * 3.9, 0.03, isaret_z],
                     [yan * 3.9, 0.03, isaret_z + 0.45],
                     [yan * 1.6, 0.03, isaret_z + 0.45]], (96, 170, 110),
                    katman=2)

    # 4.4'te duran motosiklet, kamera acisindan aracin icine girmis gibi
    # goruluyordu ve "burnunu degdirmeden durur" mesajini zayiflatiyordu.
    arac_z = kalan + 5.6                       # engelin arkasi burnumuzdan
    if arac_z < 95.0:
        a = Sahne()
        _araba(a, 0.0, 0.0, (150, 56, 48))
        s.ekle(a, t=[FREN_SERIT, 0.0, arac_z])

    fren_g = 0.0 if evre in ("seyir", "tepki") else 1.0
    model, _, _ = motosiklet(fren_g, _dur_tek, 0.0)
    s.ekle(model, t=[FREN_SERIT, 0.0, 0.0])

    kamera = Kamera([FREN_SERIT + 0.6, 5.6, -15.5], [FREN_SERIT - 0.5, 0.8, 13.0],
                    G, Y, fov=46)
    s.ciz(d, kamera, gok)

    # --- 2B gostergeler -----------------------------------------------------
    carpti = evre == "carpma"
    ust_renk = KIRMIZI if (carpti or anahtar in ("yetmis", "carpma")) else TURUNCU
    f = s2.font(40)
    tw = d.textlength(etiket, font=f)
    d.rounded_rectangle([(G - tw) / 2 - 28, 318, (G + tw) / 2 + 28, 396], 16,
                        fill=(0, 0, 0, 190), outline=ust_renk, width=5)
    s2.yazi(d, (G / 2, 330), etiket, 40, ust_renk, ortala=True)
    s2.yazi(d, (G / 2, 404), aciklama, 28, (176, 182, 190), ortala=True)

    h_renk = KIRMIZI if carpti else (YESIL if v < 0.3 else KREM)
    d.rounded_rectangle([G - 330, 470, G - 72, 648], 18, fill=(0, 0, 0, 178),
                        outline=(92, 102, 112), width=4)
    s2.yazi(d, (G - 201, 478), "HIZ", 26, (150, 155, 162), ortala=True)
    s2.yazi(d, (G - 201, 506), f"{v * 3.6:.0f}", 62, h_renk, ortala=True)
    s2.yazi(d, (G - 201, 578), "engele kalan", 24, (150, 155, 162), ortala=True)
    s2.yazi(d, (G - 201, 604), f"{kalan:.1f} m".replace(".", ","), 38,
            h_renk, ortala=True)

    px, py, pw = 62, 470, 470
    d.rounded_rectangle([px, py, px + pw, py + 326], 16, fill=(16, 20, 26, 210),
                        outline=(92, 102, 112), width=4)
    s2.yazi(d, (px + 22, py + 12), "DURMA MESAFESİ", 26, (150, 155, 162))
    s2.yazi(d, (px + 22, py + 42), "1 sn tepki · 7 m/s² fren varsayıldı", 22,
            (124, 132, 142))

    bx, bw, olcek = px + 22, pw - 44, 50.0
    for i, hh in enumerate((50.0, 70.0)):
        tep, fre, top = durma_mesafe(hh)
        yy = py + 86 + i * 78
        aktif = abs(hh - kmh) < 1.0
        s2.yazi(d, (bx, yy), f"{hh:.0f} km/h", 27,
                KREM if aktif else (138, 146, 156))
        s2.yazi(d, (bx + 150, yy), f"{top:.1f} m".replace(".", ","), 27,
                TURUNCU if aktif else (138, 146, 156))
        yb = yy + 34
        d.rounded_rectangle([bx, yb, bx + bw * tep / olcek, yb + 26], 5,
                            fill=(92, 110, 132) if not aktif else (120, 146, 176))
        d.rounded_rectangle([bx + bw * tep / olcek, yb,
                             bx + bw * top / olcek, yb + 26], 5,
                            fill=(140, 60, 52) if not aktif else TURUNCU)
    # 50'nin durdugu nokta: iki cubugun uzerinden gecen dikey cizgi
    cx = bx + bw * DURMA_HEDEF / olcek
    d.line([(cx, py + 110), (cx, py + 230)], fill=(120, 220, 150, 245), width=4)
    s2.yazi(d, (bx, py + 250), "tepki", 23, (150, 170, 196))
    s2.yazi(d, (bx + 90, py + 250), "fren", 23, (214, 132, 120))
    if carpti:
        uyari = f"{v * 3.6:.0f} km/h ile ÇARPAR"
        ug = d.textlength(uyari, font=s2.font(27))
        d.rounded_rectangle([bx, py + 282, bx + ug + 26, py + 320], 8,
                            fill=(120, 26, 22, 235), outline=KIRMIZI, width=3)
        s2.yazi(d, (bx + 13, py + 287), uyari, 27, (255, 214, 210))
    elif v < 0.3:
        s2.yazi(d, (bx, py + 286), "DURDU", 30, YESIL)
    return im




# ---------------------------------------------------------------------------
#  VIRAJA FAZLA HIZLI GIRDIN
# ---------------------------------------------------------------------------
# Butun rakamlar turevdir, varsayimlar ekranda yazili (60 km/h, viraj 30
# derecelik yatisa gore kurulmus: R = v^2/(g*tan30) = 49 m).
#
# 1) YARICAP:  R = v^2 / (g * tan(yatis))
#      10 -> 160,6 m   20 -> 77,8 m   30 -> 49,0 m   40 -> 33,7 m
#    30'dan 10'a DOGRULMAK yaricapi 3,3 KATINA cikarir (49 -> 161 m).
#    30'dan 40'a YATMAK viraji %31 DARALTIR (49 -> 34 m).
#    Yani motosiklet hala donebilir - surucu birakmazsa.
#
# 2) PANIKTE DISARI KAYMA (ders 16'daki ayni formul):
#    a = g * (tan(tasarim) - tan(suanki)),  y = a*t^2/2,  HIZDAN BAGIMSIZ.
#      30 -> 20 : a=2,09  -> 1 sn 1,05 m
#      30 -> 10 : a=3,93  -> 1 sn 1,97 m, 1,5 sn 4,43 m
#    Serit 4 m, motosiklet orta cizgiden 2 m icerde: 10 dereceye dusmek
#    BIR SANIYEDE karsi seride tasirir. Panik zincirinin tamami bu.
#
# SAGA DONEN VIRAJ. Saga donende DISARI = SOLA, yani karsi serit tarafi -
# bu yuzden "disari kacmak" burada en tehlikeli yondur.
# Yatis isareti uc_boyut kuralina uyar: yatis > 0 SOLA. Saga yatista eksi.
HIZLI_V = 60.0 / 3.6
HIZLI_TASARIM = math.radians(30.0)      # virajin kuruldugu yatis
HIZLI_KAPPA = math.tan(HIZLI_TASARIM) * 9.81 / (HIZLI_V ** 2)
HIZLI_R = 1.0 / HIZLI_KAPPA             # ~49 m
HIZLI_ACI = {10: 160.6, 20: 77.8, 30: 49.0, 40: 33.7}

HIZLI_NOKTA = {
    "panik":  ("PANİK ZİNCİRİ", "gazı kes → doğrulur → dışarı"),
    "uc":     ("DOĞRULMAK VİRAJI AÇAR", "30°→10°: yarıçap 3,3 katı"),
    "daralt": ("YATMAK VİRAJI DARALTIR", "30°→40°: %31 daha dar"),
    "bakis":  ("BAKIŞINI ÇIKIŞA TAK", "oraya gidersin"),
    "fren":   ("YATIKKEN ÖN FREN YOK", "tutuşun 0,58'i zaten virajda"),
    "giris":  ("ASIL ÇÖZÜM GİRİŞTE", "yavaş gir, hızlı çık"),
}
HIZLI_SIRA = list(HIZLI_NOKTA)
HIZLI_FAZ = [(4.0, "panik")]


def hizli_faz_ayarla(metin):
    """sahne_fazlari: "4:panik, 11:uc, ..." """
    global HIZLI_FAZ
    if not metin:
        return
    f = []
    for parca in metin.split(","):
        t_str, _, ad = parca.strip().partition(":")
        ad = ad.strip()
        if ad not in HIZLI_NOKTA:
            raise SystemExit(f"HATA: bilinmeyen hizli noktasi '{ad}'")
        f.append((float(t_str), ad))
    HIZLI_FAZ = sorted(f)


def hizli_evre(t):
    ad, bas = HIZLI_FAZ[0][1], HIZLI_FAZ[0][0]
    for z, a in HIZLI_FAZ:
        if t >= z:
            ad, bas = a, z
    return ad, bas


def _hizli_aci(anahtar, gecen):
    """O anki yatis (derece). Adim ne anlatiyorsa motosiklet onu yapar."""
    if anahtar == "panik":                  # gazi kesti, motor dogruluyor
        return 30.0 + (10.0 - 30.0) * yumusak(min(1.0, (gecen - 1.2) / 1.3))
    if anahtar == "daralt":                 # daha cok yatiyor
        return 30.0 + (40.0 - 30.0) * yumusak(min(1.0, (gecen - 1.2) / 1.3))
    return 30.0


def _hizli_kayma(anahtar, gecen):
    """Tasarim cizgisinden yanal sapma (m). + = DISARI (karsi serit yonu).

    a = g*(tan(tasarim) - tan(suanki)) sayisal olarak iki kez integre
    ediliyor; yatis zamanla degistigi icin kapali formul yok."""
    if anahtar not in ("panik", "daralt"):
        return 0.0
    # Sapma gercekten boyle buyuyor ama adim 7 saniye surdugu icin
    # motosiklet kadrajdan cikiyordu (7,8 m). Gosterim suresi sinirli:
    # panik 3,2 sn'de 3,9 m (karsi seridin icinde), daralt 2,6 sn'de
    # 0,9 m (ice dogru). Sonrasi donuyor - mesaj zaten dusmus oluyor.
    gecen = min(gecen, 3.2 if anahtar == "panik" else 2.6)
    dt, t, h, y = 0.02, 0.0, 0.0, 0.0
    tan0 = math.tan(HIZLI_TASARIM)
    while t < gecen:
        a = 9.81 * (tan0 - math.tan(math.radians(_hizli_aci(anahtar, t))))
        h += a * dt
        y += h * dt
        t += dt
    return y


def kare_hizli3b(t):
    """Saga donen viraj: panik zinciri ve motosikletin hala donebildigi."""
    anahtar, faz_bas = hizli_evre(t)
    etiket, aciklama = HIZLI_NOKTA[anahtar]
    gecen = max(0.0, t - faz_bas)
    aci = _hizli_aci(anahtar, gecen)
    kayma = _hizli_kayma(anahtar, gecen)
    gok, cim, asfalt = _palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    x0 = FREN_SERIT - kayma            # disari = sola = karsi serit yonu
    tasti = x0 < 0.0
    yaricap = HIZLI_V ** 2 / (9.81 * math.tan(math.radians(max(2.0, aci))))

    global _hiz_s, _hiz_tek
    _hiz_s = (globals().get("_hiz_s", 0.0) + HIZLI_V / FPS) % 8.0
    _hiz_tek = (globals().get("_hiz_tek", 0.0)
                + HIZLI_V / (FPS * adv_motor.ON_R)) % (2 * math.pi)

    def kx(z):
        return 0.0 if z <= 0 else HIZLI_KAPPA * z * z / 2.0

    z = -14.0
    while z < 66:
        z2 = z + 3.0
        a, b = kx(z), kx(z2)
        s.yuzey([[-95, 0, z], [95, 0, z], [95, 0, z2], [-95, 0, z2]], cim,
                katman=0)
        s.yuzey([[a - 4.2, 0.01, z], [a + 4.2, 0.01, z],
                 [b + 4.2, 0.01, z2], [b - 4.2, 0.01, z2]], asfalt, katman=1)
        for yan in (-1, 1):
            s.yuzey([[a + yan * 4.0, 0.02, z], [a + yan * 3.86, 0.02, z],
                     [b + yan * 3.86, 0.02, z2], [b + yan * 4.0, 0.02, z2]],
                    (205, 205, 200), katman=2)
        z = z2
    for i in range(-2, 14):
        zc = i * 8.0 - _hiz_s
        a, b = kx(zc), kx(zc + 3.6)
        s.yuzey([[a - 0.11, 0.02, zc], [a + 0.11, 0.02, zc],
                 [b + 0.11, 0.02, zc + 3.6], [b - 0.11, 0.02, zc + 3.6]],
                (210, 210, 205), katman=2)

    # Tasarim cizgisi: sapma ancak bir referansa gore okunur
    zz = 2.0
    while zz < 58.0:
        z2 = zz + 1.8
        s.yuzey([[kx(zz) + FREN_SERIT - 0.13, 0.03, zz],
                 [kx(zz) + FREN_SERIT + 0.13, 0.03, zz],
                 [kx(z2) + FREN_SERIT + 0.13, 0.03, z2],
                 [kx(z2) + FREN_SERIT - 0.13, 0.03, z2]],
                (86, 150, 96), katman=2)
        zz += 3.6

    model, _, _ = motosiklet(0.0, _hiz_tek, 0.0)
    s.ekle(model, R=donus([0, 0, 1], -math.radians(aci)), t=[x0, 0.0, 0.0])

    # Kamera motosikletin yanal kaymasini kismen takip eder. Sabit hedefle
    # bakilinca panikte motosiklet kadrajin sol kenarina yapisiyordu; tamamen
    # takip edilse bu sefer kayma hic okunmuyor.
    kamera = Kamera([0.6 + 0.6 * x0, 7.4, -20.0],
                    [kx(15.0) + 1.3 - 0.45 * kayma, 1.3, 15.0], G, Y, fov=46)
    s.ciz(d, kamera, gok)

    if anahtar == "bakis":                 # bakis virajin CIKISINA
        _bakis_oku(d, kamera, np.array([x0, 1.5, 1.2]),
                   np.array([kx(34.0) + 1.6, 0.1, 34.0]), YESIL)

    # --- 2B gostergeler -----------------------------------------------------
    ust_renk = KIRMIZI if anahtar in ("panik", "uc", "fren") else YESIL
    f = s2.font(40)
    tw = d.textlength(etiket, font=f)
    d.rounded_rectangle([(G - tw) / 2 - 28, 318, (G + tw) / 2 + 28, 396], 16,
                        fill=(0, 0, 0, 190), outline=ust_renk, width=5)
    s2.yazi(d, (G / 2, 330), etiket, 40, ust_renk, ortala=True)
    s2.yazi(d, (G / 2, 404), aciklama, 28, (176, 182, 190), ortala=True)

    # Sag: yatis ve o yatisin cizdigi yaricap
    d.rounded_rectangle([G - 340, 470, G - 72, 658], 18, fill=(0, 0, 0, 178),
                        outline=(92, 102, 112), width=4)
    a_renk = YESIL if aci >= 28 else (TURUNCU if aci >= 18 else KIRMIZI)
    s2.yazi(d, (G - 206, 478), "YATIŞ", 26, (150, 155, 162), ortala=True)
    s2.yazi(d, (G - 206, 508), f"{aci:.0f}°", 60, a_renk, ortala=True)
    s2.yazi(d, (G - 206, 580), "çizdiği yarıçap", 24, (150, 155, 162),
            ortala=True)
    s2.yazi(d, (G - 206, 608), f"{yaricap:.0f} m", 42, a_renk, ortala=True)

    # Sol: yatis -> yaricap tablosu ve cizgiden sapma
    # Panel 404 genisti: "ÇİZGİDEN SAPMA" ile "KARŞI ŞERİT" ayni satira
    # sigmiyordu, uyariyi nereye koysam bir seyin ustune biniyordu.
    px, py, pw = 62, 470, 470
    d.rounded_rectangle([px, py, px + pw, py + 336], 16, fill=(16, 20, 26, 210),
                        outline=(92, 102, 112), width=4)
    s2.yazi(d, (px + 22, py + 12), "YATIŞ → YARIÇAP", 26, (150, 155, 162))
    s2.yazi(d, (px + 22, py + 40), "60 km/h · viraj 30° için kurulmuş", 22,
            (124, 132, 142))
    for i, (a_deg, rr) in enumerate(sorted(HIZLI_ACI.items())):
        yy = py + 78 + i * 40
        c = KIRMIZI if a_deg < 20 else (YESIL if a_deg >= 30 else TURUNCU)
        vurgu = abs(aci - a_deg) < 5
        s2.yazi(d, (px + 22, yy), f"{a_deg}°", 27,
                KREM if vurgu else (150, 158, 168))
        d.rounded_rectangle([px + 78, yy + 5, px + 78 + 150 * (33.7 / rr),
                             yy + 27], 5, fill=c if vurgu else (62, 68, 76))
        s2.yazi(d, (px + 240, yy), f"{rr:.0f} m".replace(".0", ""), 27,
                c if vurgu else (150, 158, 168))

    sapma_renk = KIRMIZI if (tasti or kayma > 1.2) else (
        TURUNCU if kayma > 0.4 else YESIL)
    s2.yazi(d, (px + 22, py + 252), "ÇİZGİDEN SAPMA", 24, (150, 155, 162))
    deger = f"{kayma:+.2f} m".replace(".", ",")
    s2.yazi(d, (px + 22, py + 280), deger, 36, sapma_renk)
    if tasti:
        # Uyariyi once sabit x'e, sonra saga dayali koydum; ikisinde de bir
        # seyin ustune bindi. Artik DEGERIN genisligi olculup hemen
        # arkasina konuyor - cakismasi mumkun degil.
        uyari = "KARŞI ŞERİT"
        ux = px + 22 + d.textlength(deger, font=s2.font(36)) + 24
        ug = d.textlength(uyari, font=s2.font(26))
        d.rounded_rectangle([ux, py + 282, ux + ug + 24, py + 320], 8,
                            fill=(120, 26, 22, 235), outline=KIRMIZI, width=3)
        s2.yazi(d, (ux + 12, py + 287), uyari, 26, (255, 214, 210))
    return im




# ---------------------------------------------------------------------------
#  KAYGAN YAMALAR (yol yuzeyi tuzaklari)
# ---------------------------------------------------------------------------
# DERSTE YUZEYLER ICIN SURTUNME RAKAMI YOK - bilerek.
# Kaynaklar (FEMA yol guvenligi bolumu, Tayvan rogar kapagi calismalari,
# pavement marking skid resistance derlemeleri) ayni NITEL seyde birlesiyor:
# ince boya cizgileri ve dokme/pik demir rogar kapaklari ISLAKKEN cevre
# asfalttan daha az tutar. Ama olcu birimleri tutmuyor (kimi BPN, kimi DFT,
# kimi mu) ve ayni yuzey icin kaynaktan kaynaga cok degisiyor; "islak boyada
# mu=0,3" gibi bir sayi KULLANILMIYOR.
#
# KULLANILAN RAKAMLARIN HEPSI TUREVDIR:
# 1) Sabit virajda yanal kuvvet W*tan(yatis), dusey yuk W. Yolun vermesi
#    gereken tutunma katsayisi tam tan(yatis)'tir - agirliktan, lastikten,
#    hizdan BAGIMSIZ.  0->0,00  10->0,18  20->0,36  30->0,58  40->0,84
# 2) "Virajda motoru dikleştir" tavsiyesinin bedeli. Yatista kappa =
#    tan(L)*g/v^2 oldugu icin diklesince kaybolan yanal ivme
#        a = kappa*v^2 = g*tan(L)
#    yani HIZDAN BAGIMSIZ. y = a*t^2/2:
#        15 derece -> 1,31 m   20 -> 1,79 m   25 -> 2,29 m   30 -> 2,83 m
#    Hangi hizda olursan ol, 20 dereceden dik durusa gecmek bir saniyede
#    1,8 m disari atar. Bu yuzden dogru cevap "virajin ortasinda dikleş"
#    degil, "cizgini virajdan ONCE sec"tir.
#
# SAHNE KURALA UYAR: motosiklet DUZ yolda DIK gider (KURALLAR.md: yatan
# motosikletin yolu da bukulur - duz yolda yatirmak yanlis olurdu).
# Yerel yamalardan serit icinde kayarak kacinir, serit boyu uzanan
# yamalardan (yaya cizgisi, cakil) dik gecer. Yatis-mu iliskisi HUD'daki
# cubuk grafiginde duruyor.
# Hiz 60'tan 45'e indirildi: 60 km/h'de yama yakin kadrajda saniyede bir
# gecip gidiyor, okunacak zaman kalmiyordu.
ZEMIN_DONGU = 3.6                       # yamalar arasi sure (sn)
ZEMIN_HIZ = 45.0 / 3.6
ZEMIN_ARA = ZEMIN_DONGU * ZEMIN_HIZ     # iki yama arasi mesafe (m)
ZEMIN_KAYMA = 1.15                      # serit ici kacinma mesafesi (m)
ZEMIN_MU = ((0, 0.00), (10, 0.18), (20, 0.36), (30, 0.58), (40, 0.84))

ZEMIN_TUZAK = ("rogar", "boya", "mazot", "cakil", "plaka")
ZEMIN_AD = {
    "rogar": ("RÖGAR KAPAĞI", True),
    "boya":  ("YOL ÇİZGİSİ", False),
    "mazot": ("MAZOT / YAĞ", True),
    "cakil": ("ÇAKIL", False),
    "plaka": ("DEMİR PLAKA", True),
}

ZEMIN_NOKTA = {
    "gor":   ("ERKEN GÖR", "rögar · boya · plaka · mazot · çakıl"),
    "cizgi": ("ÇİZGİNİ ÖNCEDEN SEÇ", "üstünde düzeltme yapma"),
    "ister": ("YATIŞ TUTUŞ İSTER", "gereken μ = tan(yatış)"),
    "dik":   ("DİK DURUŞTA 0,00", "20°'de 0,36 ister"),
    "bedel": ("DİKLEŞMENİN BEDELİ", "20°'den: 1 saniye = 1,8 m dışarı"),
    "sabit": ("ÜSTÜNDE SABİT KAL", "gaz sabit · fren yok · kavrama gevşek"),
}
ZEMIN_SIRA = list(ZEMIN_NOKTA)
ZEMIN_FAZ = [(4.0, "gor")]


def zemin_faz_ayarla(metin):
    """sahne_fazlari: "4:gor, 11:cizgi, ..." """
    global ZEMIN_FAZ
    if not metin:
        return
    f = []
    for parca in metin.split(","):
        t_str, _, ad = parca.strip().partition(":")
        ad = ad.strip()
        if ad not in ZEMIN_NOKTA:
            raise SystemExit(f"HATA: bilinmeyen zemin noktasi '{ad}'")
        f.append((float(t_str), ad))
    ZEMIN_FAZ = sorted(f)


def zemin_evre(t):
    ad, bas = ZEMIN_FAZ[0][1], ZEMIN_FAZ[0][0]
    for z, a in ZEMIN_FAZ:
        if t >= z:
            ad, bas = a, z
    return ad, bas


def _disk(s, x, z, r, renk, n=16, y=0.021):
    p = [[x + r * math.cos(2 * math.pi * i / n), y,
          z + r * math.sin(2 * math.pi * i / n)] for i in range(n)]
    s.yuzey(p, renk, katman=2)


def _tuzak(s, tur, x, z):
    """Seride dusen kaygan yama. Hepsi asfaltin ustune cizilir (katman 2)."""
    if tur == "rogar":
        _disk(s, x, z, 0.42, (70, 66, 62))
        _disk(s, x, z, 0.34, (98, 94, 88), y=0.022)
        for i in range(6):
            a = 2 * math.pi * i / 6
            _disk(s, x + 0.20 * math.cos(a), z + 0.20 * math.sin(a), 0.045,
                  (60, 56, 52), n=8, y=0.023)
    elif tur == "boya":                     # yaya gecidi: serit boyu uzanir
        for i in range(5):
            zz = z - 1.8 + i * 0.95
            s.yuzey([[x - 2.1, 0.021, zz], [x + 2.1, 0.021, zz],
                     [x + 2.1, 0.021, zz + 0.50], [x - 2.1, 0.021, zz + 0.50]],
                    (230, 230, 224), katman=2)
    elif tur == "mazot":
        p = [(0.0, 1.9), (0.9, 1.0), (1.1, -0.5), (0.4, -1.8), (-0.6, -1.4),
             (-1.0, 0.1), (-0.8, 1.3)]
        s.yuzey([[x + a, 0.021, z + b] for a, b in p], (42, 42, 46), katman=2)
        p2 = [(0.0, 1.1), (0.5, 0.4), (0.36, -0.8), (-0.4, -0.6), (-0.5, 0.5)]
        s.yuzey([[x + a, 0.022, z + b] for a, b in p2], (58, 50, 66), katman=2)
    elif tur == "cakil":                    # serit boyu serpilmis
        rnd = 12345
        for i in range(130):
            rnd = (rnd * 1103515245 + 12345) % 2147483648
            ax = ((rnd >> 7) % 1000) / 1000.0 * 3.8 - 1.9
            rnd = (rnd * 1103515245 + 12345) % 2147483648
            az = ((rnd >> 7) % 1000) / 1000.0 * 4.4 - 2.2
            _disk(s, x + ax, z + az, 0.055, (152, 146, 134), n=6)
    else:                                   # plaka
        s.yuzey([[x - 1.25, 0.021, z - 1.5], [x + 1.25, 0.021, z - 1.5],
                 [x + 1.25, 0.021, z + 1.5], [x - 1.25, 0.021, z + 1.5]],
                (130, 132, 136), katman=2)
        for ax in (-1.05, 1.05):
            for az in (-1.28, 1.28):
                _disk(s, x + ax, z + az, 0.08, (90, 92, 96), n=8, y=0.022)


def _zemin_kayma(z, kacinilir):
    """Yerel yamaya yaklasirken serit ici yanal kacinma (0..1)."""
    if not kacinilir:
        return 0.0
    if z > 26.0 or z < -7.0:
        return 0.0
    if z > 16.0:
        return yumusak((26.0 - z) / 10.0)
    if z > -2.0:
        return 1.0
    return yumusak((z + 7.0) / 5.0)


def kare_zemin3b(t):
    """Serit uzerine dusen kaygan yamalar: kacinilabilen ve kacinilamayan."""
    anahtar, _ = zemin_evre(t)
    etiket, aciklama = ZEMIN_NOKTA[anahtar]
    gok, cim, asfalt = _palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    dongu = int(t // ZEMIN_DONGU)
    u = t % ZEMIN_DONGU
    tur = ZEMIN_TUZAK[dongu % len(ZEMIN_TUZAK)]
    onceki = ZEMIN_TUZAK[(dongu - 1) % len(ZEMIN_TUZAK)]
    yama_z = ZEMIN_ARA - ZEMIN_HIZ * u
    onceki_z = yama_z - ZEMIN_ARA

    kacinilir = ZEMIN_AD[tur][1]
    kayma = ZEMIN_KAYMA * _zemin_kayma(yama_z, kacinilir)
    x0 = FREN_SERIT + kayma

    global _zem_s, _zem_tek
    _zem_s = (globals().get("_zem_s", 0.0) + ZEMIN_HIZ / FPS) % 8.0
    _zem_tek = (globals().get("_zem_tek", 0.0)
                + ZEMIN_HIZ / (FPS * adv_motor.ON_R)) % (2 * math.pi)

    z = -20.0
    while z < 200:
        z2 = z + (6.0 if z < 90 else 20.0)
        s.yuzey([[-95, 0, z], [95, 0, z], [95, 0, z2], [-95, 0, z2]], cim,
                katman=0)
        s.yuzey([[-4.2, 0.01, z], [4.2, 0.01, z], [4.2, 0.01, z2],
                 [-4.2, 0.01, z2]], asfalt, katman=1)
        z = z2
    for yan in (-1, 1):
        zz = -20.0
        while zz < 110:
            z2 = zz + 4.0
            s.yuzey([[yan * 4.0, 0.02, zz], [yan * 3.86, 0.02, zz],
                     [yan * 3.86, 0.02, z2], [yan * 4.0, 0.02, z2]],
                    (205, 205, 200), katman=2)
            zz = z2
    for i in range(-3, 16):
        zc = i * 8.0 - _zem_s
        s.yuzey([[-0.11, 0.02, zc], [0.11, 0.02, zc], [0.11, 0.02, zc + 3.6],
                 [-0.11, 0.02, zc + 3.6]], (210, 210, 205), katman=2)

    # Iki yama birden: biri yaklasirken oteki arkada kaliyor, kadraj bosalmiyor
    if -9.0 < onceki_z < 95.0:
        _tuzak(s, onceki, FREN_SERIT, onceki_z)
    if -9.0 < yama_z < 95.0:
        _tuzak(s, tur, FREN_SERIT, yama_z)

    model, _, _ = motosiklet(0.0, _zem_tek, 0.0)
    s.ekle(model, t=[x0, 0.0, 0.0])

    kamera = Kamera([FREN_SERIT + 0.6, 5.4, -16.0], [FREN_SERIT - 0.5, 0.6, 13.0],
                    G, Y, fov=46)
    s.ciz(d, kamera, gok)

    # --- 2B gostergeler -----------------------------------------------------
    ust_renk = YESIL if anahtar in ("dik", "sabit") else (
        KIRMIZI if anahtar == "bedel" else TURUNCU)
    f = s2.font(40)
    tw = d.textlength(etiket, font=f)
    d.rounded_rectangle([(G - tw) / 2 - 28, 318, (G + tw) / 2 + 28, 396], 16,
                        fill=(0, 0, 0, 190), outline=ust_renk, width=5)
    s2.yazi(d, (G / 2, 330), etiket, 40, ust_renk, ortala=True)
    s2.yazi(d, (G / 2, 404), aciklama, 28, (176, 182, 190), ortala=True)

    # Yatis -> gereken tutus cubuklari. Dersin tek rakam kaynagi bu grafik.
    gx, gy, gw = G - 372, 470, 300
    d.rounded_rectangle([gx, gy, gx + gw, gy + 286], 16, fill=(0, 0, 0, 180),
                        outline=(92, 102, 112), width=4)
    s2.yazi(d, (gx + 20, gy + 12), "GEREKEN TUTUŞ μ", 24, (150, 155, 162))
    s2.yazi(d, (gx + 20, gy + 40), "μ = tan(yatış)", 23, (124, 132, 142))
    for i, (aci, mu) in enumerate(ZEMIN_MU):
        yy = gy + 78 + i * 40
        c = YESIL if mu < 0.10 else (TURUNCU if mu < 0.50 else KIRMIZI)
        s2.yazi(d, (gx + 20, yy), f"{aci}°", 26, (190, 196, 204))
        d.rounded_rectangle([gx + 74, yy + 4, gx + 74 + 150 * mu, yy + 26], 5,
                            fill=c)
        s2.yazi(d, (gx + 232, yy), f"{mu:.2f}".replace(".", ","), 26, c)

    px, py, pw = 62, 470, 418
    d.rounded_rectangle([px, py, px + pw, py + 392], 16, fill=(16, 20, 26, 210),
                        outline=(92, 102, 112), width=4)
    s2.yazi(d, (px + 22, py + 14), "KAYGAN YAMA", 26, (150, 155, 162))
    for i, k in enumerate(ZEMIN_TUZAK):
        acik = k == tur
        yy = py + 54 + i * 52
        d.rounded_rectangle([px + 22, yy + 4, px + 34, yy + 34], 5,
                            fill=TURUNCU if acik else (58, 64, 72))
        s2.yazi(d, (px + 50, yy), ZEMIN_AD[k][0], 29,
                KREM if acik else (112, 120, 130))
    durum, dr = (("ŞERİT İÇİNDE KAÇIN", YESIL) if kacinilir
                 else ("KAÇINILMAZ — DİK GEÇ", TURUNCU))
    s2.yazi(d, (px + 22, py + 330), durum, 28, dr)
    return im


# ---------------------------------------------------------------------------
# Kaynak: Indiana DOT metrik geometrik tasarim boluму (AASHTO Green Book
# tablosundan): 90 km/h tasarim hizi icin GECIS GORUS MESAFESI 615 m,
# 100 km/h icin 670 m. Ayni belge gecilen araci 73, gecen araci 88 km/h
# alir. MUTCD'nin "sollama yasak" seridi cizme esigi daha dusuktur
# (90 km/h icin 280 m) ve tasarim degeriyle ayni sey DEGILDIR.
#
# SAHNEDEKI HESAP (varsayimlar ekranda yazili):
#   gecilecek bagil yol = 20 m geri bosluk + 16 m TIR + 20 m on bosluk = 56 m
#   sure = 56 / (hiz farki)
#   gereken bos yol = (bizim hiz + karsi hiz) * sure
#     90 ile 70'i gecerken, karsidan 90: dv=20 -> 10.1 sn -> 504 m
#     90 ile 80'i gecerken, karsidan 90: dv=10 -> 20.2 sn -> 1008 m
# Kendi hesabimiz 504 m, standart 615 m: ayni mertebe, bizimki daha cimri
# varsayimlarla. Derste ikisi birlikte veriliyor, biri otekinin yerine
# gecmiyor.
SOLLAMA_DONGU = 14.0
SOLLAMA_GERI, SOLLAMA_TIR, SOLLAMA_ON = 20.0, 16.0, 20.0
SOLLAMA_STANDART = 615.0        # 90 km/h icin yol tasarim degeri (m)

SOLLAMA_NOKTA = {
    "geri":     ("ÖNCE GERİ ÇEKİL", "hem görürsün hem hız alırsın", (90, 70, 90)),
    "hesap":    ("90 İLE 70'İ GEÇMEK", "10 saniye · 504 metre", (90, 70, 90)),
    "az":       ("HIZ FARKI 10 İSE", "20 saniye · 1 kilometre", (90, 80, 90)),
    "standart": ("YOL STANDARDI 615 m", "90 km/h için gereken görüş", (90, 70, 90)),
    "kor":      ("DÜZ ÇİZGİ VARSA YOK", "viraj · tepe · kavşak", (90, 70, 90)),
    "donus":    ("İKİ FARINI AYNADA GÖR", "sonra şeride gir", (90, 70, 90)),
}
SOLLAMA_SIRA = list(SOLLAMA_NOKTA)
SOLLAMA_FAZ = [(4.0, "geri")]


def sollama_faz_ayarla(metin):
    """sahne_fazlari: "4:geri, 11:hesap, ..." """
    global SOLLAMA_FAZ
    if not metin:
        return
    f = []
    for parca in metin.split(","):
        t_str, _, ad = parca.strip().partition(":")
        ad = ad.strip()
        if ad not in SOLLAMA_NOKTA:
            raise SystemExit(f"HATA: bilinmeyen sollama noktasi '{ad}'")
        f.append((float(t_str), ad))
    SOLLAMA_FAZ = sorted(f)


def sollama_evre(t):
    ad, bas = SOLLAMA_FAZ[0][1], SOLLAMA_FAZ[0][0]
    for z, a in SOLLAMA_FAZ:
        if t >= z:
            ad, bas = a, z
    return ad, bas


def _sollama_hesap(bizim, onun, karsi):
    """(hiz_farki, sure, bizim_yol, karsi_yol, gereken). Varsayimlar yukarida."""
    dv = (bizim - onun) / 3.6
    yol = SOLLAMA_GERI + SOLLAMA_TIR + SOLLAMA_ON
    sure = yol / dv
    biz = bizim / 3.6 * sure
    kars = karsi / 3.6 * sure
    return (bizim - onun), sure, biz, kars, biz + kars


def _sollama_hareket(u):
    """(tirin bagil z'si, bizim yanal konum). Biz z=0'da duruyoruz, TIR akiyor."""
    def ara(a, b, p):
        return a + (b - a) * yumusak(min(1.0, max(0.0, p)))

    if u < 2.5:
        tz = 12.0
    elif u < 4.5:
        tz = ara(12.0, 28.0, (u - 2.5) / 2.0)
    elif u < 6.0:
        tz = 28.0
    elif u < 10.0:
        tz = ara(28.0, -22.0, (u - 6.0) / 4.0)
    elif u < 12.0:
        tz = ara(-22.0, -44.0, (u - 10.0) / 2.0)
    else:
        tz = ara(-44.0, -72.0, (u - 12.0) / 2.0)

    if u < 4.6:
        x = FREN_SERIT
    elif u < 6.0:
        x = ara(FREN_SERIT, -FREN_SERIT, (u - 4.6) / 1.4)
    elif u < 10.6:
        x = -FREN_SERIT
    elif u < 12.0:
        x = ara(-FREN_SERIT, FREN_SERIT, (u - 10.6) / 1.4)
    else:
        x = FREN_SERIT
    return tz, x


def _tir(s, x, z, renk=(206, 207, 210)):
    """16 m'lik cekici + dorse. Sollama hesabinin '16 m'si bu."""
    s.kutu([x, 1.65, z + 6.2], [2.45, 2.30, 3.40], renk)            # cekici
    s.kutu([x, 2.70, z + 6.9], [2.30, 0.60, 1.90], (40, 44, 50))    # ust spoyler
    s.kutu([x, 1.40, z + 7.9], [2.36, 0.90, 0.10], (36, 46, 60))    # on cam
    s.kutu([x, 2.30, z - 2.2], [2.50, 2.90, 13.0], (232, 232, 228))  # dorse
    s.kutu([x, 0.72, z - 2.2], [2.30, 0.46, 12.6], (52, 54, 58))
    # Arka kapak: en cok gorulen yuz bu, duz beyaz levha gibi kaliyordu
    s.kutu([x, 2.30, z - 8.72], [0.06, 2.70, 0.06], (176, 178, 180))
    for yan in (-1, 1):
        s.kutu([x + yan * 1.14, 2.30, z - 8.72], [0.06, 2.70, 0.06],
               (176, 178, 180))
    s.kutu([x, 3.55, z - 8.72], [2.44, 0.08, 0.06], (176, 178, 180))
    s.kutu([x, 0.78, z - 8.6], [2.40, 0.40, 0.12], (198, 52, 44))   # arka stop
    # Tekerlekler once x +-1.10'daydi; dorse 2.50 genis oldugu icin yandan
    # bakista govdenin arkasinda kaliyor ve TIR tekerleksiz gorunuyordu.
    for yan in (-1, 1):
        for dz in (6.6, -0.6, -2.4, -7.4):
            s.kutu([x + yan * 1.24, 0.54, z + dz], [0.34, 1.08, 1.08],
                   (26, 26, 28))
            s.kutu([x + yan * 1.26, 0.54, z + dz], [0.04, 0.52, 0.52],
                   (148, 150, 154))                      # jant


def kare_sollama3b(t):
    """Alcak takip gorusu: TIR'i sollama ve bunun gercekten istedigi bos yol."""
    anahtar, faz_bas = sollama_evre(t)
    etiket, aciklama, hizlar = SOLLAMA_NOKTA[anahtar]
    gok, cim, asfalt = _palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    kor = anahtar == "kor"
    u = t % SOLLAMA_DONGU
    tir_z, x0 = _sollama_hareket(u)
    if kor:                       # duz cizgi varken sollama YOK: seritte kal
        tir_z, x0 = 26.0, FREN_SERIT

    dv, sure, biz_yol, kars_yol, gereken = _sollama_hesap(*hizlar)

    global _sol_s, _sol_tek
    _sol_s = (globals().get("_sol_s", 0.0) + 25.0 / FPS) % 8.0
    _sol_tek = (globals().get("_sol_tek", 0.0)
                + 25.0 / (FPS * adv_motor.ON_R)) % (2 * math.pi)

    z = -24.0
    while z < 220:
        z2 = z + (6.0 if z < 100 else 20.0)
        s.yuzey([[-95, 0, z], [95, 0, z], [95, 0, z2], [-95, 0, z2]], cim,
                katman=0)
        s.yuzey([[-4.2, 0.01, z], [4.2, 0.01, z], [4.2, 0.01, z2],
                 [-4.2, 0.01, z2]], asfalt, katman=1)
        z = z2
    for yan in (-1, 1):
        zz = -24.0
        while zz < 120:
            z2 = zz + 4.0
            s.yuzey([[yan * 4.0, 0.02, zz], [yan * 3.86, 0.02, zz],
                     [yan * 3.86, 0.02, z2], [yan * 4.0, 0.02, z2]],
                    (205, 205, 200), katman=2)
            zz = z2

    # Orta cizgi: normalde kesik, "kor" adiminda DUZ - gercek dunyadaki isaret
    if kor:
        zz = -24.0
        while zz < 130:
            z2 = zz + 6.0
            s.yuzey([[-0.13, 0.02, zz], [0.13, 0.02, zz], [0.13, 0.02, z2],
                     [-0.13, 0.02, z2]], (236, 232, 206), katman=2)
            zz = z2
    else:
        for i in range(-3, 18):
            zc = i * 8.0 - _sol_s
            s.yuzey([[-0.11, 0.02, zc], [0.11, 0.02, zc],
                     [0.11, 0.02, zc + 3.6], [-0.11, 0.02, zc + 3.6]],
                    (210, 210, 205), katman=2)

    if -30.0 < tir_z < 120.0:
        _tir(s, FREN_SERIT, tir_z)

    model, _, _ = motosiklet(0.0, _sol_tek, 0.0)
    s.ekle(model, t=[x0, 0.0, 0.0])

    kamera = Kamera([0.9 + 0.5 * x0, 5.4, -16.0], [x0 * 0.35, 0.8, 15.0],
                    G, Y, fov=46)
    s.ciz(d, kamera, gok)

    # --- 2B gostergeler -----------------------------------------------------
    ust_renk = KIRMIZI if anahtar in ("az", "kor") else TURUNCU
    f = s2.font(40)
    tw = d.textlength(etiket, font=f)
    d.rounded_rectangle([(G - tw) / 2 - 28, 318, (G + tw) / 2 + 28, 396], 16,
                        fill=(0, 0, 0, 190), outline=ust_renk, width=5)
    s2.yazi(d, (G / 2, 330), etiket, 40, ust_renk, ortala=True)
    s2.yazi(d, (G / 2, 404), aciklama, 28, (176, 182, 190), ortala=True)

    px, py, pw = 62, 470, 560
    d.rounded_rectangle([px, py, px + pw, py + 346], 16, fill=(16, 20, 26, 212),
                        outline=(92, 102, 112), width=4)
    sag = px + pw - 24

    def _sagda(metin, punto, y, c):
        g = d.textlength(metin, font=s2.font(punto))
        s2.yazi(d, (sag - g, y), metin, punto, c)

    # Hiz cifti once buyuk rakamin saginda duruyordu; "1008 m" genisleyince
    # ust uste biniyordu. Artik kendi satirinda.
    s2.yazi(d, (px + 24, py + 14), "GEREKEN BOŞ YOL", 26, (150, 155, 162))
    s2.yazi(d, (px + 24, py + 44), f"{gereken:.0f} m", 76,
            KIRMIZI if gereken > 700 else TURUNCU)
    s2.yazi(d, (px + 24, py + 124),
            f"{hizlar[0]} ile {hizlar[1]} · fark {dv:.0f} km/h · "
            f"{sure:.1f} sn".replace(".", ","), 27, KREM)

    # Semayla: gereken yolun ne kadari bizim, ne kadari karsidan gelenin
    bx, by, bw, bh = px + 24, py + 166, pw - 48, 38
    olcek = max(gereken, SOLLAMA_STANDART)
    w1 = bw * biz_yol / olcek
    w2 = bw * kars_yol / olcek
    d.rounded_rectangle([bx, by, bx + bw, by + bh], 8, fill=(30, 34, 40, 230),
                        outline=(78, 86, 96), width=3)
    d.rectangle([bx + 3, by + 3, bx + w1, by + bh - 3], fill=TURUNCU)
    d.rectangle([bx + w1, by + 3, bx + w1 + w2 - 3, by + bh - 3], fill=MAVI)
    s2.yazi(d, (bx, by + 46), f"BİZ {biz_yol:.0f} m", 26, TURUNCU)
    _sagda(f"KARŞI {kars_yol:.0f} m", 26, by + 46, MAVI)

    sy = by + 92
    d.line([(bx + bw * SOLLAMA_STANDART / olcek, by - 10),
            (bx + bw * SOLLAMA_STANDART / olcek, by + bh + 10)],
           fill=(236, 232, 206, 240), width=4)
    s2.yazi(d, (bx, sy), "yol standardı 90 km/h", 26, (190, 196, 204))
    _sagda(f"{SOLLAMA_STANDART:.0f} m", 26, sy, (236, 232, 206))
    s2.yazi(d, (bx, sy + 34),
            "20 m geri + 16 m TIR + 20 m ön", 23, (124, 132, 142))
    return im




# ---------------------------------------------------------------------------
#  SERIT ICI KONUM
# ---------------------------------------------------------------------------
# Kaynaklar: MSF surucu el kitabi (seridi uc esit parcaya bol), Florida ve
# Idaho motosiklet el kitaplari, Motorcycle Riders Hub (UK).
# Uzerinde birlestikleri:
#   1. Serit uc parcaya bolunur: sol - orta - sag.
#   2. Konumu degistirmenin sebeplerinden biri GORUS HATTINI UZATMAK'tir.
#   3. Viraja yaklasirken virajin DISINA gecilir; Florida el kitabi bunu
#      saga donen viraj icin acikca soyluyor, UK kaynagi sola donen viraj
#      icin ayna goruntusunu veriyor. Ikisi ayni ilke.
# ONEMLI DUZELTME: "seridin ortasi yaglidir, ortadan kacin" yaygin bir
# inanis ama Idaho el kitabi acikca "seridin hicbir kismindan kacinmak
# gerekmez - orta dahil" diyor. Derste kural degil, ZEMINE BAK deniyor.
#
# GEOMETRI (sahnede gosterilen rakamlar buradan):
# Yol saga R = 140 m ile kiviriliyor, gorusu kapatan ic yamac yol
# kenarinda (4.2 m). Surucunun yanal konumu x0 ise bakis cizgisi ic kenara
# TEGET oldugu yerde biter:
#     kappa*z^2/2 - m*z + (4.2 - x0) = 0  -> cift kok -> z = sqrt(2*(4.2-x0)*R)
#   sol ucte bir (x=1.0) -> 29.9 m
#   orta         (x=2.0) -> 24.8 m
#   sag ucte bir (x=3.1) -> 17.5 m
# Yani ayni virajda sol ucte bir, sag ucte birin 1.7 katini gosteriyor.
KONUM_R = 140.0                 # viraj yaricapi (m) - saga kiviriliyor
KONUM_KENAR = 4.2               # ic yamacin yol eksenine uzakligi (m)
KONUM_DONGU = 10.0              # yanal kayma dongusu (sn)
KONUM_SOL, KONUM_ORTA, KONUM_SAG = 1.0, 2.0, 3.1
KONUM_ARAC_Z = 22.0

KONUM_NOKTA = {
    "ucte":  ("ŞERİDİ ÜÇE BÖL", "sol · orta · sağ"),
    "disa":  ("VİRAJIN DIŞINA GEÇ", "görüş uzar"),
    "olcu":  ("AYNI VİRAJ, İKİ KONUM", "17 m ↔ 30 m"),
    "bedel": ("BEDELİ VAR", "karşı şeride fazla yanaşma"),
    "arka":  ("TAM ARKASINA OTURMA", "ne görürsün ne görünürsün"),
    "orta":  ("'ORTA KİRLİDİR' KURALI YOK", "zemine bak, kurala değil"),
}
KONUM_SIRA = list(KONUM_NOKTA)
KONUM_FAZ = [(4.0, "ucte")]


def konum_faz_ayarla(metin):
    """sahne_fazlari: "4:ucte, 11:disa, ..." """
    global KONUM_FAZ
    if not metin:
        return
    f = []
    for parca in metin.split(","):
        t_str, _, ad = parca.strip().partition(":")
        ad = ad.strip()
        if ad not in KONUM_NOKTA:
            raise SystemExit(f"HATA: bilinmeyen konum noktasi '{ad}'")
        f.append((float(t_str), ad))
    KONUM_FAZ = sorted(f)


def konum_evre(t):
    """(ad, fazin basladigi an). Yanal konum ADIMA bagli oldugu icin
    fazin basi lazim: kendi dongusunde kaldiginda "tam arkasina oturma"
    denirken motosiklet arkada olmayabiliyordu."""
    ad, bas = KONUM_FAZ[0][1], KONUM_FAZ[0][0]
    for z, a in KONUM_FAZ:
        if t >= z:
            ad, bas = a, z
    return ad, bas


def _konum_kx(z):
    """Yolun z metre ileride saga kaymasi."""
    return z * z / (2.0 * KONUM_R)


def _konum_gorus(x0):
    """Bakis cizgisinin ic yamaca teget oldugu uzaklik (m)."""
    pay = max(0.25, KONUM_KENAR - x0)
    return math.sqrt(2.0 * pay * KONUM_R)


def _konum_x(anahtar, gecen):
    """Yanal konum: her adim kendi konumunu gosterir."""
    def ara(a, b, p):
        return a + (b - a) * yumusak(min(1.0, max(0.0, p)))

    if anahtar == "ucte":                      # uc parca tanitiliyor
        return KONUM_ORTA
    if anahtar == "disa":                      # sagdan sola yuru
        return ara(KONUM_SAG, KONUM_SOL, (gecen - 0.6) / 3.2)
    if anahtar == "olcu":                      # iki konum arasinda git gel
        p = (gecen % 5.0) / 5.0
        return (ara(KONUM_SAG, KONUM_SOL, p / 0.5) if p < 0.5
                else ara(KONUM_SOL, KONUM_SAG, (p - 0.5) / 0.5))
    if anahtar == "bedel":                     # karsi serit dibinde kal
        return ara(KONUM_ORTA, KONUM_SOL, gecen / 1.6)
    if anahtar == "arka":                      # once tam arkasinda, sonra kay
        return (KONUM_ORTA if gecen < 3.6
                else ara(KONUM_ORTA, KONUM_SOL, (gecen - 3.6) / 1.8))
    p = (gecen % 6.0) / 6.0                    # orta: uc parcayi tara
    return (ara(KONUM_SOL, KONUM_SAG, p / 0.5) if p < 0.5
            else ara(KONUM_SAG, KONUM_SOL, (p - 0.5) / 0.5))


def _konum_ad(x0):
    if x0 < 1.45:
        return 0
    return 1 if x0 < 2.65 else 2


def _konum_yamac(s, z0, z1, renk):
    """Virajin IC tarafindaki yamac: gorusu kapatan sey bu.

    Ad "_yamac" degil: dosyada baska imzayla bir _yamac zaten var ve
    sonra tanimlandigi icin bunu golgeliyordu."""
    z = z0
    while z < z1:
        z2 = min(z + 4.0, z1)
        a, b = _konum_kx(z) + KONUM_KENAR, _konum_kx(z2) + KONUM_KENAR
        s.yuzey([[a, 0.0, z], [a + 1.5, 2.3, z], [b + 1.5, 2.3, z2],
                 [b, 0.0, z2]], renk, katman=3)
        s.yuzey([[a + 1.5, 2.3, z], [a + 7.0, 2.6, z], [b + 7.0, 2.6, z2],
                 [b + 1.5, 2.3, z2]], tuple(int(k * 0.86) for k in renk),
                katman=3)
        z = z2


def kare_konum3b(t):
    """Saga donen viraj: serit ici konum degistikce gorus hatti uzayip kisalir."""
    anahtar, faz_bas = konum_evre(t)
    etiket, aciklama = KONUM_NOKTA[anahtar]
    gok, cim, asfalt = _palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    x0 = _konum_x(anahtar, max(0.0, t - faz_bas))
    hangi = _konum_ad(x0)
    arac_var = anahtar == "arka"
    gorus = _konum_gorus(x0)
    # Onundeki arac bakisi keser: serit ortasindaysan yoldan once onu gorursun.
    if arac_var and abs(x0 - KONUM_ORTA) < 0.62:
        gorus = min(gorus, KONUM_ARAC_Z - 4.0)

    global _kon_s, _kon_tek
    _kon_s = (globals().get("_kon_s", 0.0) + 16.0 / FPS) % 8.0
    _kon_tek = (globals().get("_kon_tek", 0.0)
                + 16.0 / (FPS * adv_motor.ON_R)) % (2 * math.pi)

    z = -16.0
    while z < 150:
        z2 = z + 4.0
        a, b = _konum_kx(z), _konum_kx(z2)
        s.yuzey([[-95, 0, z], [95, 0, z], [95, 0, z2], [-95, 0, z2]], cim,
                katman=0)
        s.yuzey([[a - 4.2, 0.01, z], [a + 4.2, 0.01, z],
                 [b + 4.2, 0.01, z2], [b - 4.2, 0.01, z2]], asfalt, katman=1)
        for yan in (-1, 1):
            s.yuzey([[a + yan * 4.0, 0.02, z], [a + yan * 3.86, 0.02, z],
                     [b + yan * 3.86, 0.02, z2], [b + yan * 4.0, 0.02, z2]],
                    (205, 205, 200), katman=2)
        z = z2
    for i in range(-2, 22):
        zc = i * 8.0 - _kon_s
        a, b = _konum_kx(zc), _konum_kx(zc + 3.6)
        s.yuzey([[a - 0.11, 0.02, zc], [a + 0.11, 0.02, zc],
                 [b + 0.11, 0.02, zc + 3.6], [b - 0.11, 0.02, zc + 3.6]],
                (210, 210, 205), katman=2)

    # Seridi uce bolen soluk kilavuz cizgileri
    for pay in (4.0 / 3.0, 8.0 / 3.0):
        for i in range(0, 24):
            zc = i * 4.0 - (_kon_s % 4.0)
            if zc < -4.0:
                continue
            a, b = _konum_kx(zc) + pay, _konum_kx(zc + 1.3) + pay
            s.yuzey([[a - 0.06, 0.025, zc], [a + 0.06, 0.025, zc],
                     [b + 0.06, 0.025, zc + 1.3], [b - 0.06, 0.025, zc + 1.3]],
                    (150, 152, 148), katman=2)

    _konum_yamac(s, 0.0, 150.0, (72, 86, 62))
    if anahtar == "bedel":                 # karsi seridin dibi: uyari bandi
        zz = 2.0
        while zz < 60.0:
            z2 = zz + 2.2
            a0, b0 = _konum_kx(zz), _konum_kx(z2)
            s.yuzey([[a0 + 0.18, 0.03, zz], [a0 + 0.62, 0.03, zz],
                     [b0 + 0.62, 0.03, z2], [b0 + 0.18, 0.03, z2]],
                    KIRMIZI, katman=2)
            zz += 4.4

    if arac_var:
        a = Sahne()
        _araba(a, 0.0, 0.0, (52, 86, 142))
        s.ekle(a, t=[_konum_kx(KONUM_ARAC_Z) + KONUM_ORTA, 0.0, KONUM_ARAC_Z])

    model, _, _ = motosiklet(0.0, _kon_tek, 0.0)
    s.ekle(model, t=[x0, 0.0, 0.0])

    kam_x = 0.9 + 0.5 * x0
    kamera = Kamera([kam_x, 5.4, -16.0], [_konum_kx(13.0) + 1.4, 0.6, 13.0],
                    G, Y, fov=46)
    s.ciz(d, kamera, gok)

    # --- bakis cizgisi: ic yamaca teget bittigi yere kadar ------------------
    uc_x = (_konum_kx(gorus) + KONUM_KENAR) if not (
        arac_var and gorus < KONUM_ARAC_Z - 3.0) else (
        _konum_kx(gorus) + KONUM_ORTA)
    _bakis_oku(d, kamera, np.array([x0, 0.9, 1.2]),
               np.array([uc_x, 0.1, gorus]),
               KIRMIZI if gorus < 20.0 else YESIL)

    # --- 2B gostergeler -----------------------------------------------------
    ust_renk = KIRMIZI if anahtar in ("bedel", "arka") else TURUNCU
    f = s2.font(40)
    tw = d.textlength(etiket, font=f)
    d.rounded_rectangle([(G - tw) / 2 - 28, 318, (G + tw) / 2 + 28, 396], 16,
                        fill=(0, 0, 0, 190), outline=ust_renk, width=5)
    s2.yazi(d, (G / 2, 330), etiket, 40, ust_renk, ortala=True)
    s2.yazi(d, (G / 2, 404), aciklama, 28, (176, 182, 190), ortala=True)

    g_renk = KIRMIZI if gorus < 20.0 else YESIL
    d.rounded_rectangle([G - 340, 470, G - 72, 612], 18, fill=(0, 0, 0, 175),
                        outline=(92, 102, 112), width=4)
    s2.yazi(d, (G - 206, 478), "GÖRÜŞ", 26, (150, 155, 162), ortala=True)
    s2.yazi(d, (G - 206, 512), f"{gorus:.0f}", 72, g_renk, ortala=True)
    s2.yazi(d, (G - 206, 578), "metre", 26, (150, 155, 160), ortala=True)

    px, py, pw = 62, 470, 420
    d.rounded_rectangle([px, py, px + pw, py + 196], 16, fill=(16, 20, 26, 210),
                        outline=(92, 102, 112), width=4)
    s2.yazi(d, (px + 22, py + 14), "ŞERİT İÇİ KONUM", 26, (150, 155, 162))
    hx, hy, hw, hh = px + 22, py + 58, pw - 44, 62
    for i, ad in enumerate(("SOL", "ORTA", "SAĞ")):
        x1 = hx + hw * i / 3.0
        acik = i == hangi
        d.rounded_rectangle([x1 + 4, hy, x1 + hw / 3.0 - 4, hy + hh], 8,
                            fill=(TURUNCU if acik else (40, 46, 54)),
                            outline=(92, 102, 112), width=2)
        s2.yazi(d, (x1 + hw / 6.0, hy + 16), ad, 30,
                (12, 12, 14) if acik else (128, 136, 146), ortala=True)
    s2.yazi(d, (px + 22, py + 138),
            "iç yamaç yol kenarında · R=140 m", 24, (130, 138, 148))
    return im




# ---------------------------------------------------------------------------
#  TAKIP MESAFESI: IKI SANIYE
# ---------------------------------------------------------------------------
# Iki ayri kural var ve ikisi de dogrulandi:
#   1. Turkiye'de Karayollari Trafik Yonetmeligi takip mesafesini "kendi
#      aracinin km/saat cinsinden hizinin en az yarisi kadar metre" diye
#      tanimliyor (90 km/h -> 45 m). Kaynaklar surucu kursu ve sigorta
#      siteleri; hepsi ayni metni veriyor, madde numarasi tek kaynakta
#      geciyor, bu yuzden derste madde numarasi YAZILMIYOR.
#   2. Resmi motosiklet el kitaplari (NY DMV, Indiana surucu el kitabi)
#      en az IKI SANIYE diyor.
# Ikisi ayni seyi soyluyor: (v/2) metre / (v/3.6) m/sn = 1.8 saniye - HIZDAN
# BAGIMSIZ. Yani yonetmelik her hizda 1.8 sn'dir, iki saniye onu paylarla
# karsilar. Bu aritmetik dersin belkemigi ve ekranda gosteriliyor.
# "Islakta ikiye katla" egitim pratigi olarak yaygin ama resmi el
# kitaplarinda rakamla gecmiyor; derste kural degil TAVSIYE diye veriliyor.
TAKIP_DONGU = 12.0
TAKIP_V = 90.0 / 3.6            # m/sn - sahnedeki sabit hiz (90 km/h)
TAKIP_YAKIN, TAKIP_GUVENLI = 16.0, 50.0
TAKIP_YONETMELIK_SN = 1.8       # hizin yarisi kadar metre, her hizda bu eder
TAKIP_HEDEF_SN = 2.0
TAKIP_ISLAK_SN = 4.0

TAKIP_NOKTA = {
    "yonetmelik": ("HIZIN YARISI KADAR METRE", "90 km/h → 45 m"),
    "saniye":     ("HER HIZDA 1,8 SANİYE", "45 ÷ 25 = 1,8"),
    "say":        ("SEN 2 SANİYE SAY", "metre tahmin edilmez"),
    "isaret":     ("BİR İŞARET SEÇ", "bin bir, bin iki"),
    "katla":      ("ISLAK · GECE · YOLCU", "ikiye katla"),
    "gorus":      ("MESAFE = GÖRÜŞ", "sadece fren değil"),
}
TAKIP_SIRA = list(TAKIP_NOKTA)
TAKIP_FAZ = [(4.0, "yonetmelik")]


def takip_faz_ayarla(metin):
    """sahne_fazlari: "4:yonetmelik, 11:saniye, ..." """
    global TAKIP_FAZ
    if not metin:
        return
    f = []
    for parca in metin.split(","):
        t_str, _, ad = parca.strip().partition(":")
        ad = ad.strip()
        if ad not in TAKIP_NOKTA:
            raise SystemExit(f"HATA: bilinmeyen takip noktasi '{ad}'")
        f.append((float(t_str), ad))
    TAKIP_FAZ = sorted(f)


def takip_evre(t):
    ad, bas = TAKIP_FAZ[0][1], TAKIP_FAZ[0][0]
    for z, a in TAKIP_FAZ:
        if t >= z:
            ad, bas = a, z
    return ad, yumusak((t - bas) / 0.5)


def _takip_mesafe(u):
    """Dongu cok yakin baslar, surucu gazi birakir, mesafe guvenliye acilir."""
    if u < 2.5:
        return TAKIP_YAKIN
    if u < 7.0:
        return TAKIP_YAKIN + (TAKIP_GUVENLI - TAKIP_YAKIN) * yumusak(
            (u - 2.5) / 4.5)
    return TAKIP_GUVENLI


def _delinator(s, x, z, isaretli=False):
    """Yol kenari dikmesi: sayarken gozun takildigi sabit nokta."""
    s.kutu([x, 0.42, z], [0.10, 0.84, 0.10], (238, 238, 232))
    s.kutu([x, 0.66, z], [0.11, 0.14, 0.11],
           TURUNCU if isaretli else (196, 56, 46))
    if isaretli:
        # Sayimin basladigi dikme uzaktan da secilmeli: kucuk bayrak
        # kadrajda kayboluyordu.
        s.kutu([x, 0.95, z], [0.11, 0.46, 0.11], TURUNCU)
        s.kutu([x - 0.22, 1.28, z], [0.46, 0.34, 0.04], TURUNCU)


def _mesafe_seridi(s, x, z0, z1, renk):
    """Serit ortasinda kesikli olcu bandi: biz ile onumuzdeki arasi."""
    z = z0
    while z < z1:
        z2 = min(z + 1.7, z1)
        s.yuzey([[x - 0.17, 0.03, z], [x + 0.17, 0.03, z],
                 [x + 0.17, 0.03, z2], [x - 0.17, 0.03, z2]], renk, katman=2)
        z += 3.4


def kare_takip3b(t):
    """Alcak takip gorusu: onumuzdeki araca mesafe saniyeye cevrilir."""
    anahtar, _ = takip_evre(t)
    etiket, aciklama = TAKIP_NOKTA[anahtar]
    gok, cim, asfalt = _palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    u = t % TAKIP_DONGU
    mesafe = _takip_mesafe(u)
    saniye = mesafe / TAKIP_V
    guvenli = saniye >= TAKIP_HEDEF_SN
    renk = YESIL if guvenli else KIRMIZI

    global _tak_s, _tak_tek
    _tak_s = (globals().get("_tak_s", 0.0) + TAKIP_V / FPS) % 8.0
    _tak_d = (globals().get("_tak_s", 0.0)) % 25.0
    _tak_tek = (globals().get("_tak_tek", 0.0)
                + TAKIP_V / (FPS * adv_motor.ON_R)) % (2 * math.pi)

    z = -16.0
    while z < 220:
        z2 = z + (6.0 if z < 100 else 20.0)
        s.yuzey([[-95, 0, z], [95, 0, z], [95, 0, z2], [-95, 0, z2]], cim,
                katman=0)
        s.yuzey([[-4.2, 0.01, z], [4.2, 0.01, z], [4.2, 0.01, z2],
                 [-4.2, 0.01, z2]], asfalt, katman=1)
        z = z2
    for yan in (-1, 1):
        zz = -16.0
        while zz < 110:
            z2 = zz + 4.0
            s.yuzey([[yan * 4.0, 0.02, zz], [yan * 3.86, 0.02, zz],
                     [yan * 3.86, 0.02, z2], [yan * 4.0, 0.02, z2]],
                    (205, 205, 200), katman=2)
            zz = z2
    for i in range(-2, 16):
        zc = i * 8.0 - _tak_s
        s.yuzey([[-0.11, 0.02, zc], [0.11, 0.02, zc], [0.11, 0.02, zc + 3.6],
                 [-0.11, 0.02, zc + 3.6]], (210, 210, 205), katman=2)

    # Yol kenari dikmeleri 25 m'de bir. Bizimle onumuzdeki aracin ARASINDA
    # kalan ilki isaretli: sayim o dikmeden baslar.
    sayim_z = None
    for i in range(0, 9):
        zc = i * 25.0 - _tak_d
        if zc < -6.0:
            continue
        arada = 1.0 < zc < mesafe
        if arada and sayim_z is None:
            sayim_z = zc
        _delinator(s, 4.7, zc, isaretli=arada and sayim_z == zc)

    _mesafe_seridi(s, FREN_SERIT, 2.4, max(3.0, mesafe - 2.6), renk)

    a = Sahne()
    _araba(a, 0.0, 0.0, (52, 86, 142))
    s.ekle(a, t=[FREN_SERIT, 0.0, mesafe])

    model, _, _ = motosiklet(0.0, _tak_tek, 0.0)
    s.ekle(model, t=[FREN_SERIT, 0.0, 0.0])

    kamera = Kamera([FREN_SERIT + 0.6, 5.4, -16.0], [FREN_SERIT - 0.7, 0.6, 13.0],
                    G, Y, fov=46)
    s.ciz(d, kamera, gok)

    # --- 2B gostergeler -----------------------------------------------------
    ust_renk = YESIL if anahtar in ("say", "gorus") else TURUNCU
    f = s2.font(40)
    tw = d.textlength(etiket, font=f)
    d.rounded_rectangle([(G - tw) / 2 - 28, 318, (G + tw) / 2 + 28, 396], 16,
                        fill=(0, 0, 0, 190), outline=ust_renk, width=5)
    s2.yazi(d, (G / 2, 330), etiket, 40, ust_renk, ortala=True)
    s2.yazi(d, (G / 2, 404), aciklama, 28, (176, 182, 190), ortala=True)

    d.rounded_rectangle([G - 320, 470, G - 72, 612], 18, fill=(0, 0, 0, 170),
                        outline=(92, 102, 112), width=4)
    s2.yazi(d, (G - 196, 482), f"{int(round(TAKIP_V * 3.6))}", 82, KREM,
            ortala=True)
    s2.yazi(d, (G - 196, 572), "km/h", 28, (150, 155, 160), ortala=True)

    # Panel: degerler SAGA dayali. Ilk surumde sabit x ile yazilmislardi ve
    # "1,4 sn" ile "36 m", "ISLAK..." ile "4,0 sn" ust uste biniyordu.
    px, py, pw = 62, 470, 468
    d.rounded_rectangle([px, py, px + pw, py + 338], 16, fill=(16, 20, 26, 210),
                        outline=(92, 102, 112), width=4)
    sag = px + pw - 24

    def _sagda(metin, punto, y, c):
        g = d.textlength(metin, font=s2.font(punto))
        s2.yazi(d, (sag - g, y), metin, punto, c)

    s2.yazi(d, (px + 24, py + 14), "TAKİP", 26, (150, 155, 162))
    s2.yazi(d, (px + 24, py + 46), f"{saniye:.1f}".replace(".", ",") + " sn",
            72, renk)
    _sagda(f"{mesafe:.0f} m", 44, py + 70, KREM)
    s2.yazi(d, (px + 24, py + 128), "ÇOK YAKIN" if not guvenli else "TAMAM",
            32, renk)

    bx, by, bw, bh = px + 24, py + 180, pw - 48, 30
    d.rounded_rectangle([bx, by, bx + bw, by + bh], 8, fill=(30, 34, 40, 230),
                        outline=(78, 86, 96), width=3)
    d.rounded_rectangle([bx + 3, by + 3,
                         bx + 3 + (bw - 6) * min(1.0, saniye / TAKIP_ISLAK_SN),
                         by + bh - 3], 6, fill=renk)
    for deger, c in ((TAKIP_YONETMELIK_SN, (184, 190, 198)),
                     (TAKIP_HEDEF_SN, YESIL), (TAKIP_ISLAK_SN, MAVI)):
        xx = bx + bw * deger / TAKIP_ISLAK_SN
        d.line([(xx, by - 9), (xx, by + bh + 9)], fill=(*c, 240), width=4)
    for i, (ad, deger, c) in enumerate(
            (("YÖNETMELİK", "1,8 sn", (184, 190, 198)),
             ("HEDEF", "2,0 sn", YESIL),
             ("ISLAKTA", "4,0 sn", MAVI))):
        yy = by + 52 + i * 32
        d.rounded_rectangle([bx, yy + 3, bx + 9, yy + 25], 4, fill=c)
        s2.yazi(d, (bx + 24, yy), ad, 26, (190, 196, 204))
        _sagda(deger, 26, yy, c)
    return im


def kare_kavsak3b(t):
    """Yuksek 3/4 gorus: karsidan gelen arac kavsakta onumuze doner."""
    anahtar, _ = kavsak_evre(t)
    etiket, aciklama = KAVSAK_NOKTA[anahtar]
    gok, cim, asfalt = _palet()
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    u = t % KAVSAK_DONGU
    yol, hiz = _kavsak_yol(u)
    kz = KAVSAK_BAS - yol

    global _kav_s, _kav_tek
    _kav_s = (globals().get("_kav_s", 0.0) + hiz / FPS) % 8.0
    _kav_tek = (globals().get("_kav_tek", 0.0)
                + hiz / (FPS * adv_motor.ON_R)) % (2 * math.pi)

    # --- zemin ve ana yol ---------------------------------------------------
    # Zemin 100 m'de bitince alcak kamerada ufukta sert bir kenar kaliyordu;
    # 100 m'den sonra kaba dilimlerle 220 m'ye kadar uzatiliyor.
    z = -16.0
    while z < 220:
        z2 = z + (6.0 if z < 100 else 20.0)
        s.yuzey([[-95, 0, z], [95, 0, z], [95, 0, z2], [-95, 0, z2]], cim,
                katman=0)
        s.yuzey([[-4.2, 0.01, z], [4.2, 0.01, z], [4.2, 0.01, z2],
                 [-4.2, 0.01, z2]], asfalt, katman=1)
        z = z2

    # --- yan yol: kavsak SAGDA, arac bizim onumuzden ona doner --------------
    if -12.0 < kz < 100.0:
        # 16 m yeter: ilk denemede 32 m uzuyordu ve uzaktan bir meydan
        # gibi okunuyordu, sokak gibi degil.
        s.yuzey([[4.2, 0.012, kz - 4.2], [20.5, 0.012, kz - 4.2],
                 [20.5, 0.012, kz + 4.2], [4.2, 0.012, kz + 4.2]], asfalt,
                katman=1)

    # kenar cizgileri; sag kenar kavsak agzinda kesilir
    for yan in (-1, 1):
        zz = -16.0
        while zz < 100:
            z2 = zz + 4.0
            if not (yan > 0 and zz < kz + 4.2 and z2 > kz - 4.2):
                s.yuzey([[yan * 4.0, 0.02, zz], [yan * 3.86, 0.02, zz],
                         [yan * 3.86, 0.02, z2], [yan * 4.0, 0.02, z2]],
                        (205, 205, 200), katman=2)
            zz = z2
    for i in range(-2, 15):
        zc = i * 8.0 - _kav_s
        s.yuzey([[-0.11, 0.02, zc], [0.11, 0.02, zc], [0.11, 0.02, zc + 3.6],
                 [-0.11, 0.02, zc + 3.6]], (210, 210, 205), katman=2)

    # --- kacis boslugu ------------------------------------------------------
    if anahtar == "bosluk":
        _yol_kutusu(s, FREN_SERIT - 1.4, FREN_SERIT + 1.7, 3.0, 10.5, YESIL)

    # --- arac ---------------------------------------------------------------
    ax, az, asap = _kavsak_araba(u, kz)
    R_a = donus([0, 1, 0], asap)
    if -14.0 < az < 115.0 and ax < 42.0:
        a = Sahne()
        _araba(a, 0.0, 0.0, (152, 58, 50))
        s.ekle(a, R=R_a, t=[ax, 0.0, az])

    # --- motosiklet: kavsaga yaklasirken yavaslar, catal coker --------------
    fren = 0.55 if 3.0 <= u < 5.5 else (0.42 if 5.5 <= u < 8.0 else 0.0)
    model, _, _ = motosiklet(fren, _kav_tek, 0.0)
    s.ekle(model, t=[FREN_SERIT, 0.0, 0.0])

    # Kamera alcak ve yakin: yuksekten bakinca motosiklet kadrajin dibinde
    # kuculuyor ve kare bos asfaltla doluyordu.
    kamera = Kamera([FREN_SERIT + 0.6, 5.4, -16.0], [FREN_SERIT - 0.7, 0.6, 13.0],
                    G, Y, fov=46)
    s.ciz(d, kamera, gok)

    # --- 3B ustune isaretler ------------------------------------------------
    if anahtar == "onteker":
        _halka(d, kamera, np.array([ax, 0.0, az]) + R_a @ np.array([0, 0.40, 1.35]),
               TURUNCU)
    elif anahtar == "goz":
        g = _halka(d, kamera,
                   np.array([ax, 0.0, az]) + R_a @ np.array([0, 1.30, 1.00]),
                   KIRMIZI)
        if g:                                      # uzeri cizili goz
            gx, gy, gr = g
            d.line([(gx - gr * 0.78, gy + gr * 0.78),
                    (gx + gr * 0.78, gy - gr * 0.78)], fill=(*KIRMIZI, 235),
                   width=9)

    # --- 2B gostergeler -----------------------------------------------------
    renk = KIRMIZI if anahtar in ("goz", "duz") else TURUNCU
    f = s2.font(40)
    tw = d.textlength(etiket, font=f)
    d.rounded_rectangle([(G - tw) / 2 - 28, 318, (G + tw) / 2 + 28, 396], 16,
                        fill=(0, 0, 0, 190), outline=renk, width=5)
    s2.yazi(d, (G / 2, 330), etiket, 40, renk, ortala=True)
    s2.yazi(d, (G / 2, 404), aciklama, 28, (176, 182, 190), ortala=True)

    d.rounded_rectangle([G - 320, 470, G - 72, 612], 18, fill=(0, 0, 0, 170),
                        outline=(92, 102, 112), width=4)
    s2.yazi(d, (G - 196, 482), f"{int(round(hiz * 3.6))}", 82, KREM, ortala=True)
    s2.yazi(d, (G - 196, 572), "km/h", 28, (150, 155, 160), ortala=True)

    px, py, pw = 62, 690, 452
    d.rounded_rectangle([px, py, px + pw, py + 368], 16, fill=(16, 20, 26, 205),
                        outline=(92, 102, 112), width=4)
    for i, ad in enumerate(KAVSAK_SIRA):
        acik = ad == anahtar
        yy = py + 22 + i * 56
        c = KIRMIZI if (acik and ad in ("goz", "duz")) else TURUNCU
        d.rounded_rectangle([px + 20, yy + 4, px + 32, yy + 40], 5,
                            fill=c if acik else (60, 66, 74))
        s2.yazi(d, (px + 48, yy), KAVSAK_NOKTA[ad][0], 30,
                KREM if acik else (112, 120, 130))
    return im




# ---------------------------------------------------------------------------
#  KONTRA (counter-steering) - onden gorunum
# ---------------------------------------------------------------------------
KONTRA_HIZ = 70.0 / 3.6     # m/s - yatistan donus yaricapi bundan cikar
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

    global _yol_k, _tek_k, _agac_k
    _yol_k = (globals().get("_yol_k", 0.0) + 0.58) % 8.0
    _agac_k = (globals().get("_agac_k", 0.0) + 0.58) % 12.0
    _tek_k = (globals().get("_tek_k", 0.0) + 0.42) % (2 * math.pi)

    # --- yatis yolu buker ---------------------------------------------------
    # Motosiklet yatarak doner, o yuzden yol da yatisla ayni yone kivrilmali.
    # Donus yaricapi fizikten geliyor: R = v^2 / (g * tan(yatis)).
    # 70 km/h ve 22 derecede R ~ 93 m; daha dusuk hizda viraj o kadar sert
    # oluyor ki yol birkac metrede kadrajdan cikiyordu.
    kappa = math.tan(yatis) * 9.81 / (KONTRA_HIZ ** 2)

    def kx(z):
        """z metre ileride yolun yanal kaymasi (yatis>0 = sola = -x)."""
        return 0.0 if z <= 0.0 else -kappa * z * z / 2.0

    z = -16.0
    while z < 115:
        z2 = z + 5.0
        x1, x2 = kx(z), kx(z2)
        s.yuzey([[-240, 0, z], [240, 0, z], [240, 0, z2], [-240, 0, z2]],
                cim, katman=0)
        s.yuzey([[x1 - 4.2, 0.01, z], [x1 + 4.2, 0.01, z],
                 [x2 + 4.2, 0.01, z2], [x2 - 4.2, 0.01, z2]], asfalt, katman=1)
        for yan in (-1, 1):
            s.yuzey([[x1 + yan * 4.0, 0.02, z], [x1 + yan * 3.86, 0.02, z],
                     [x2 + yan * 3.86, 0.02, z2], [x2 + yan * 4.0, 0.02, z2]],
                    (205, 205, 200), katman=2)
        z = z2
    for i in range(-2, 16):                              # kesikli orta cizgi
        z = i * 8.0 - _yol_k
        z2 = z + 3.6
        x1, x2 = kx(z), kx(z2)
        s.yuzey([[x1 - 0.11, 0.02, z], [x1 + 0.11, 0.02, z],
                 [x2 + 0.11, 0.02, z2], [x2 - 0.11, 0.02, z2]],
                (210, 210, 205), katman=2)
    for i in range(-1, 11):                              # agaclar yolu takip eder
        za = i * 12.0 - _agac_k
        xa = kx(za)
        for yan in (-1, 1):
            _agac(s, xa + yan * (8.5 + (i % 3) * 2.0), za,
                  5.0 + ((i * 5 + yan) % 4) * 1.3,
                  (84, 66, 48) if GUNDUZ else (34, 30, 26),
                  (54, 104, 52) if GUNDUZ else (24, 38, 26))
    if GUNDUZ:
        for i in range(6):                               # tepeler ileride (+z)
            _tepe(s, -220 + i * 92, 320 + (i % 3) * 40, 150, 90, 32 + (i % 4) * 10,
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
# Viraj bu yay uzunlugundan sonra biter, yol tegete oturup duzlesir.
# Motosiklet buraya ~44.5. sn'de variyor, yani "gazi kademeli ac"
# adiminin (42. sn) hemen ardindan; duzluk kadraja birkac saniye once
# giriyor, viraj goz onunde aciliyor.
GAZ_CIKIS_S = 455.0

# Her faz: (gaz, serit_ofseti, yatis_carpani, etiket, renk)
# serit_ofseti: orta cizgiden disa dogru metre. Sag serit 0..3.9 arasi,
# 3.9'u gecmek seritten TASMAK demek.
GAZ_DURUM = {
    "fren":    (0.00, 1.9, 0.00, "FREN · DÜZ ÇİZGİDE", MAVI),
    "yatis":   (0.18, 2.7, 1.00, "YATIŞ", MAVI),
    "sabit":   (0.32, 1.9, 1.00, "SABİT GAZ", YESIL),
    # Taşıma serit ICINDE kalir: 3.5 m, kenar cizgisi 3.74-3.9 arasinda.
    # Oncesinde 5.3 verilip motosiklet yoldan cikiyordu.
    "kesik":   (0.00, 3.50, 0.40, "GAZ KESİLDİ · DIŞARI TAŞIYOR", KIRMIZI),
    "duzelt":  (0.30, 2.2, 1.18, "İÇ GİDONA BAS", TURUNCU),
    "cikis":   (0.92, 3.0, 0.50, "GAZ AÇILIYOR", YESIL),
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


def _gaz_cerceve(th):
    """Sapma acisinda (disa_birim, teget) verir."""
    return (np.array([math.cos(th), 0.0, math.sin(th)]),
            np.array([-math.sin(th), 0.0, math.cos(th)]))


def _gaz_konum(s, ofset):
    """Yol uc parcali: duz giris (s<0), yay, duz cikis (s>GAZ_CIKIS_S).
    (konum, teget, disa_birim, sapma) verir; parcalar tegette suruyor."""
    if s < 0:
        return (np.array([GAZ_R + ofset, 0.0, s]), np.array([0.0, 0.0, 1.0]),
                np.array([1.0, 0.0, 0.0]), 0.0)
    if s <= GAZ_CIKIS_S:
        th = s / GAZ_R
        disa, teget = _gaz_cerceve(th)
        return (GAZ_R + ofset) * disa, teget, disa, th
    th = GAZ_CIKIS_S / GAZ_R
    disa, teget = _gaz_cerceve(th)
    return ((GAZ_R + ofset) * disa + teget * (s - GAZ_CIKIS_S),
            teget, disa, th)


def _gaz_nokta(s, ofset, y):
    k, _, _, _ = _gaz_konum(s, ofset)
    return [float(k[0]), y, float(k[2])]


def kare_gaz3b(t, toplam=55.0):
    gok, cim, asfalt = _palet()
    gaz, ofset, yatis_k, etiket, renk, durum = gaz_evre(t, toplam)
    im = Image.new("RGB", (G, Y), gok)
    d = ImageDraw.Draw(im, "RGBA")
    s = Sahne()

    # Gaz-hiz kazanci yuksek tutuldu: cikista hizlanma goze carpmaliydi,
    # 30 km/h bandinda gaz acilsa da motosiklet ayni hizda gidiyor gibiydi.
    hiz_kmh = 42.0 + 46.0 * gaz
    global _gaz_s, _gaz_tek
    # Tur sarmasi kaldirildi: yol artik kapali daire degil, cikisi duz.
    _gaz_s = globals().get("_gaz_s", -140.0) + (hiz_kmh / 3.6) / FPS
    _gaz_tek = (globals().get("_gaz_tek", 0.0) + 0.5) % (2 * math.pi)

    # --- zemin ve yol -----------------------------------------------------
    # Yol artik tam daire olarak degil, _gaz_konum boyunca yuruyerek ciziliyor.
    # Boylece giris duzlugu, yay ve cikis duzlugu kendiliginden birbirine
    # oturuyor; ayri ayri cizilince cikis duzlugu eklenemiyordu.
    konum, teget, disa, th = _gaz_konum(_gaz_s, ofset)
    s.yuzey([list(konum + teget * a + disa * b + np.array([0, -konum[1], 0]))
             for a, b in ((-150, -150), (210, -150), (210, 150), (-150, 150))],
            cim, katman=0)

    ADIM = 3.0
    sx = _gaz_s - 24.0
    while sx < _gaz_s + 165.0:
        sx2 = sx + ADIM
        s.yuzey([_gaz_nokta(sx, -GAZ_YARIM, 0.01), _gaz_nokta(sx, GAZ_YARIM, 0.01),
                 _gaz_nokta(sx2, GAZ_YARIM, 0.01), _gaz_nokta(sx2, -GAZ_YARIM, 0.01)],
                asfalt, katman=1)
        for yan in (-1, 1):
            s.yuzey([_gaz_nokta(sx, yan * GAZ_YARIM, 0.02),
                     _gaz_nokta(sx, yan * (GAZ_YARIM - 0.16), 0.02),
                     _gaz_nokta(sx2, yan * (GAZ_YARIM - 0.16), 0.02),
                     _gaz_nokta(sx2, yan * GAZ_YARIM, 0.02)],
                    (208, 208, 202), katman=2)
        sx = sx2
    for i in range(int((_gaz_s - 24.0) / 8.0), int((_gaz_s + 165.0) / 8.0) + 1):
        sa, sb = i * 8.0, i * 8.0 + 3.6          # kesikli orta cizgi
        s.yuzey([_gaz_nokta(sa, -0.11, 0.02), _gaz_nokta(sa, 0.11, 0.02),
                 _gaz_nokta(sb, 0.11, 0.02), _gaz_nokta(sb, -0.11, 0.02)],
                (212, 212, 206), katman=2)
    for i in range(int((_gaz_s - 24.0) / 14.0), int((_gaz_s + 165.0) / 14.0) + 1):
        for yan in (-1, 1):                      # agaclar yolu takip eder
            a = _gaz_nokta(i * 14.0, yan * 11.0, 0.0)
            _agac(s, a[0], a[2], 5.0 + (i % 4) * 1.2,
                  (84, 66, 48) if GUNDUZ else (34, 30, 26),
                  (54, 104, 52) if GUNDUZ else (24, 38, 26))

    # --- motosiklet --------------------------------------------------------
    # YATIS ISARETI: lambda > 0 = SOLA yatis (gorsel testle dogrulandi).
    # Daha once negatif veriliyordu: sol virajda motosiklet SAGA yatiyordu.
    # Duz cikista yatis sifirlanir: yol duzken motosiklet yatik duramaz.
    # Dogrulma tegete varmadan 12 m once basliyor, gercek surusteki gibi.
    dik = min(1.0, max(0.0, (_gaz_s - (GAZ_CIKIS_S - 12.0)) / 30.0))
    yatis = 0.42 * yatis_k * (1.0 - dik)
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


def kare_viraj3b(t, toplam=55.0, gosterge=True):
    """gosterge=False: HUD'suz temiz kare (Story arka plani icin)."""
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

    if not gosterge:          # Story gibi kullanimlar icin temiz kare
        return im

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
    ap.add_argument("--sahne",
                    choices=("fren", "viraj", "kontra", "gaz", "islak",
                             "kornokta", "manevra", "gece", "kontrol",
                             "kacinma", "yolcu", "kavsak", "takip", "konum",
                             "sollama", "zemin", "hizli", "durma", "bakis"),
                    required=True)
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
    elif args.sahne == "islak":
        cizer = kare_islak3b
    elif args.sahne == "kornokta":
        cizer = kare_kornokta3b
    elif args.sahne == "manevra":
        cizer = kare_manevra3b
    elif args.sahne == "gece":
        cizer = kare_gece3b
    elif args.sahne == "kontrol":
        kontrol_zaman_ayarla(args.fazlar)
        cizer = kare_kontrol3b
    elif args.sahne == "kacinma":
        cizer = kare_kacinma3b
    elif args.sahne == "yolcu":
        yolcu_faz_ayarla(args.fazlar)
        cizer = kare_yolcu3b
    elif args.sahne == "bakis":
        bakis_faz_ayarla(args.fazlar)
        cizer = kare_bakis3b
    elif args.sahne == "durma":
        durma_faz_ayarla(args.fazlar)
        cizer = kare_durma3b
    elif args.sahne == "hizli":
        hizli_faz_ayarla(args.fazlar)
        cizer = kare_hizli3b
    elif args.sahne == "zemin":
        zemin_faz_ayarla(args.fazlar)
        cizer = kare_zemin3b
    elif args.sahne == "sollama":
        sollama_faz_ayarla(args.fazlar)
        cizer = kare_sollama3b
    elif args.sahne == "konum":
        konum_faz_ayarla(args.fazlar)
        cizer = kare_konum3b
    elif args.sahne == "takip":
        takip_faz_ayarla(args.fazlar)
        cizer = kare_takip3b
    elif args.sahne == "kavsak":
        kavsak_faz_ayarla(args.fazlar)
        cizer = kare_kavsak3b
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
