#!/usr/bin/env python3
"""
uc_boyut.py
-------------------------------------------------------------------
Küçük bir yazılımsal 3B motor. Dışarıdan motor/kütüphane gerekmez:
perspektif kamera, yüzey normalinden ışık, derinliğe göre sıralama
(ressam algoritması) ve yakın düzlem kırpması. Yüzeyleri Pillow doldurur,
rasterleştirme C tarafında olduğu için hızlıdır.

Eksen düzeni: X sağ, Y yukarı, Z ileri (gidiş yönü).
-------------------------------------------------------------------
"""
import math

import numpy as np

def birim(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


ISIK = np.array([0.45, 0.82, -0.35])
ISIK = ISIK / np.linalg.norm(ISIK)
ORTAM = 0.42                      # ortam ışığı payı
SIS_BASLANGIC, SIS_BITIS = 22.0, 95.0


def isik_ayarla(yon=None, ortam=None, sis=None):
    """Gunduz/gece gibi farkli isik duzenleri icin. sis = (baslangic, bitis);
    gunduzde uzagin secilir kalmasi icin sis cok daha geride baslatilir."""
    global ISIK, ORTAM, SIS_BASLANGIC, SIS_BITIS
    if yon is not None:
        ISIK = birim(np.asarray(yon, dtype=float))
    if ortam is not None:
        ORTAM = float(ortam)
    if sis is not None:
        SIS_BASLANGIC, SIS_BITIS = float(sis[0]), float(sis[1])


def donus(eksen, aci):
    """Rodrigues: eksen etrafında aci radyan döndüren 3x3 matris."""
    k = birim(np.asarray(eksen, dtype=float))
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(aci) * K + (1 - math.cos(aci)) * (K @ K)


class Kamera:
    def __init__(self, konum, hedef, genislik, yukseklik, fov=52.0, yukari=(0, 1, 0)):
        self.konum = np.asarray(konum, dtype=float)
        ileri = birim(np.asarray(hedef, dtype=float) - self.konum)
        sag = birim(np.cross(ileri, np.asarray(yukari, dtype=float)))
        self.taban = np.stack([sag, np.cross(sag, ileri), ileri])   # 3x3
        self.cx, self.cy = genislik / 2, yukseklik / 2
        # fov DIKEY kenardan olculur. Yatay kenardan olculunce 9:16 karede
        # dikey aci devlesiyor ve yol butun ekrani yutuyordu.
        self.F = (yukseklik / 2) / math.tan(math.radians(fov) / 2)

    def kameraya(self, noktalar):
        return (np.asarray(noktalar, dtype=float) - self.konum) @ self.taban.T

    def ekrana(self, kamera_noktalari):
        z = np.maximum(kamera_noktalari[:, 2], 1e-4)
        x = self.cx + kamera_noktalari[:, 0] * self.F / z
        y = self.cy - kamera_noktalari[:, 1] * self.F / z
        return np.stack([x, y], axis=1)


YAKIN = 0.25


def _yakin_kirp(noktalar):
    """Kamera arkasına taşan yüzeyi yakın düzlemde keser (Sutherland-Hodgman)."""
    cikti = []
    n = len(noktalar)
    for i in range(n):
        a, b = noktalar[i], noktalar[(i + 1) % n]
        a_ic, b_ic = a[2] >= YAKIN, b[2] >= YAKIN
        if a_ic:
            cikti.append(a)
        if a_ic != b_ic:
            t = (YAKIN - a[2]) / (b[2] - a[2])
            cikti.append(a + (b - a) * t)
    return np.array(cikti) if len(cikti) >= 3 else None


class Sahne:
    """Yüzey torbası: (noktalar, renk, parlaklik_carpani)."""

    def __init__(self):
        self.yuzeyler = []

    def yuzey(self, noktalar, renk, isiksiz=False, katman=3):
        """katman: 0 cim, 1 asfalt, 2 cizgiler, 3 cisimler. Once katman, sonra derinlik
        siralanir. Sadece derinlige bakinca yol cizgileri cisimlerin onune
        basabiliyordu (ressam algoritmasinin bilinen kusuru)."""
        self.yuzeyler.append((np.asarray(noktalar, dtype=float), renk, isiksiz, katman))

    # --- ilkel cisimler ---------------------------------------------------
    def ekle(self, diger, R=None, t=None):
        """Baska bir sahnenin yuzeylerini donusturerek ekler (model yerlestirme)."""
        for noktalar, renk, isiksiz, katman in diger.yuzeyler:
            p = noktalar if R is None else noktalar @ np.asarray(R).T
            if t is not None:
                p = p + np.asarray(t, dtype=float)
            self.yuzeyler.append((p, renk, isiksiz, katman))

    def kutu(self, merkez, boyut, renk, R=None, katman=3):
        m = np.asarray(merkez, dtype=float)
        sx, sy, sz = (np.asarray(boyut, dtype=float) / 2)
        k = np.array([[-sx, -sy, -sz], [sx, -sy, -sz], [sx, sy, -sz], [-sx, sy, -sz],
                      [-sx, -sy, sz], [sx, -sy, sz], [sx, sy, sz], [-sx, sy, sz]])
        if R is not None:
            k = k @ np.asarray(R).T
        k = k + m
        for yuz in ((0, 1, 2, 3), (5, 4, 7, 6), (4, 0, 3, 7),
                    (1, 5, 6, 2), (3, 2, 6, 7), (4, 5, 1, 0)):
            self.yuzey(k[list(yuz)], renk, katman=katman)

    def silindir(self, bas, son, yaricap, renk, segment=14, kapak=True):
        bas, son = np.asarray(bas, float), np.asarray(son, float)
        eksen = birim(son - bas)
        gecici = np.array([0, 0, 1.0]) if abs(eksen[2]) < 0.9 else np.array([1.0, 0, 0])
        u = birim(np.cross(eksen, gecici))
        v = np.cross(eksen, u)
        halka_b, halka_s = [], []
        for i in range(segment):
            a = 2 * math.pi * i / segment
            d = (math.cos(a) * u + math.sin(a) * v) * yaricap
            halka_b.append(bas + d)
            halka_s.append(son + d)
        for i in range(segment):
            j = (i + 1) % segment
            self.yuzey([halka_b[i], halka_b[j], halka_s[j], halka_s[i]], renk)
        if kapak:
            self.yuzey(halka_b[::-1], renk)
            self.yuzey(halka_s, renk)

    def kure(self, merkez, yaricap, renk, dilim=12, halka=8):
        m = np.asarray(merkez, dtype=float)
        for i in range(halka):
            t0 = math.pi * i / halka - math.pi / 2
            t1 = math.pi * (i + 1) / halka - math.pi / 2
            for j in range(dilim):
                a0 = 2 * math.pi * j / dilim
                a1 = 2 * math.pi * (j + 1) / dilim
                p = [[math.cos(t) * math.cos(a), math.sin(t), math.cos(t) * math.sin(a)]
                     for t, a in ((t0, a0), (t0, a1), (t1, a1), (t1, a0))]
                self.yuzey(m + np.array(p) * yaricap, renk)

    # --- çizim ------------------------------------------------------------
    def ciz(self, d, kamera, arka_renk):
        hazir = []
        for noktalar, renk, isiksiz, katman in self.yuzeyler:
            kn = kamera.kameraya(noktalar)
            if kn[:, 2].max() < YAKIN:
                continue
            if kn[:, 2].min() < YAKIN:
                kn = _yakin_kirp(kn)
                if kn is None:
                    continue
            if isiksiz:
                parlaklik = 1.0
            else:
                n = np.cross(noktalar[1] - noktalar[0], noktalar[2] - noktalar[0])
                nn = np.linalg.norm(n)
                if nn < 1e-9:
                    continue
                lam = abs(float(np.dot(n / nn, ISIK)))
                parlaklik = ORTAM + (1 - ORTAM) * lam
            derinlik = float(kn[:, 2].mean())
            # sis: uzaktaki yuzeyler arka plana karisir, derinlik hissi verir
            sis = min(1.0, max(0.0, (derinlik - SIS_BASLANGIC) / (SIS_BITIS - SIS_BASLANGIC)))
            c = tuple(int(min(255, k * parlaklik) * (1 - sis) + a * sis)
                      for k, a in zip(renk, arka_renk))
            hazir.append((katman, derinlik, kamera.ekrana(kn), c))
        hazir.sort(key=lambda s: (s[0], -s[1]))      # once katman, sonra arkadan one
        for _, _, ekran, c in hazir:
            d.polygon([tuple(p) for p in ekran], fill=c)
