#!/usr/bin/env python3
"""
sahne_uret.py
-------------------------------------------------------------------
Eğitim videoları için arka plan sahnesi üretir. Her şey burada çizilir —
dışarıdan görüntü alınmaz, telif sorunu olmaz.

İki sahne:
  fren   · Yandan görünüm. Motosiklet frene basar; çatal çöker, ağırlık öne
           gider, ön lastiğin temas alanı büyür. Soldaki çubuklar ön/arka
           yük dağılımını canlı gösterir. (Ders 01)
  viraj  · Sürücü gözünden yol. Yolun iki kenarının birleştiği kayboluş
           noktası uzaklaşır / yaklaşır / sabit kalır; hedef sabitlemesi
           anında engel ve kaçış boşluğu belirir. (Ders 02)

Ses de sentezlenir: silindir ateşlemelerinden kurulmuş motor sesi, sahnenin
gaz/fren durumuna göre devir değiştirir. Üstüne rüzgâr uğultusu.

Kullanım:
  python3 scripts/sahne_uret.py --sahne fren  --cikti videos/sahne_fren.mp4
  python3 scripts/sahne_uret.py --sahne viraj --sure 60
-------------------------------------------------------------------
"""
import argparse
import math
import os
import subprocess
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

G, Y = 1080, 1920          # genişlik, yükseklik
FPS = 30
SR = 44100

ZEMIN = (7, 9, 14)
TURUNCU = (255, 90, 31)
KREM = (245, 240, 232)
MAVI = (25, 211, 255)
KIRMIZI = (226, 59, 46)
YESIL = (46, 204, 113)
ASFALT = (48, 51, 56)
SERIT = (190, 190, 185)
GOLD = (217, 164, 65)
KROM = (200, 210, 217)

FONT_YOLU = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_font_onbellek = {}


def font(punto):
    if punto not in _font_onbellek:
        _font_onbellek[punto] = ImageFont.truetype(FONT_YOLU, punto)
    return _font_onbellek[punto]


def karis(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def yumusak(t):
    """0-1 arasi yumusak gecis (smoothstep)."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def yazi(d, xy, metin, punto, renk, ortala=False, golge=True):
    f = font(punto)
    x, y = xy
    if ortala:
        x -= d.textlength(metin, font=f) / 2
    if golge:
        d.text((x + 3, y + 3), metin, font=f, fill=(0, 0, 0))
    d.text((x, y), metin, font=f, fill=renk)


# ===========================================================================
#  SAHNE 1 · FREN (yandan görünüm)
# ===========================================================================
# Ders adimlari 4. saniyeden baslayip ~7.5 sn araliklarla geliyor. Dongu de
# ayni ritimde doner ki her adim yeni bir fren denemesiyle acilsin.
FREN_DONGU = 7.5
FREN_OFSET = 4.0


def fren_evre(t):
    """Döngü içindeki konumdan (hız, fren miktarı, yol kayması) üretir."""
    u = (max(0.0, t - FREN_OFSET) % FREN_DONGU) / FREN_DONGU
    if u < 0.28:                      # sabit hızla yaklaşma
        hiz, fren = 1.0, 0.0
    elif u < 0.40:                    # frene ilk hafif dokunuş
        p = (u - 0.28) / 0.12
        hiz, fren = 1.0 - 0.10 * p, 0.35 * yumusak(p)
    elif u < 0.72:                    # basınç artar, asıl yavaşlama
        p = (u - 0.40) / 0.32
        hiz, fren = 0.90 * (1 - yumusak(p)), 0.35 + 0.65 * yumusak(p)
    elif u < 0.86:                    # durdu
        hiz, fren = 0.0, 1.0
    else:                             # tekrar kalkış
        p = (u - 0.86) / 0.14
        hiz, fren = yumusak(p), 1.0 - yumusak(p)
    return hiz, fren


def _tekerlek(d, cx, cy, r, aci):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(18, 18, 18), outline=ZEMIN, width=7)
    d.ellipse([cx - r + 20, cy - r + 20, cx + r - 20, cy + r - 20],
              fill=(38, 38, 38), outline=GOLD, width=5)
    for i in range(5):
        a = aci + i * (2 * math.pi / 5)
        d.line([cx + math.cos(a) * 16, cy + math.sin(a) * 16,
                cx + math.cos(a) * (r - 24), cy + math.sin(a) * (r - 24)],
               fill=KROM, width=7)
    d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=GOLD)


def kare_fren(t):
    im = Image.new("RGB", (G, Y), ZEMIN)
    d = ImageDraw.Draw(im, "RGBA")
    hiz, fren = fren_evre(t)

    ufuk = 840
    taban = 1255                     # tekerleklerin oturdugu cizgi
    # Icerik 300-1400 bandinda tutulur: ustte ders banti, altta adim kutulari var.

    for i in range(16):              # sehir silueti
        ust = ufuk - 140 - ((i * 211) % 300)
        x = (i * 84) - 30
        d.rectangle([x, ust, x + 66, ufuk], fill=(17, 21, 29))
    d.rectangle([0, ufuk, G, Y], fill=(54, 57, 63))
    d.rectangle([0, ufuk, G, ufuk + 6], fill=(96, 100, 106))

    global _fren_kayma
    _fren_kayma = (globals().get("_fren_kayma", 0.0) + hiz * 46.0) % 300
    for i in range(-1, 6):
        x = i * 300 - _fren_kayma
        d.rounded_rectangle([x, 1395, x + 150, 1412], 9, fill=(132, 132, 128))

    # --- motosiklet -------------------------------------------------------
    # Olculer gercek bir motosikletten alinip piksele cevrildi: aks arasi
    # 1400 mm = 410 px -> ol = 0.293 px/mm. Sele 800 mm, gidon 1050 mm,
    # surucunun basi 1550 mm. Gozle kestirince surucu devlesiyordu.
    mx, r = 545, 106
    OL = 0.293
    zemin_y = taban + r

    cokme = 32 * fren
    kalkma = 9 * fren

    def H(mm, dusey=0.0):
        """mm cinsinden yerden yukseklik -> ekran y'si (one dogru cokme ile)."""
        return zemin_y - mm * OL + cokme * dusey - kalkma * (1 - dusey)

    def P(mm_x, mm_y, dusey=0.0):
        return (mx + mm_x * OL, H(mm_y, dusey))

    ax, ay = mx - 205, taban - kalkma       # arka aks
    fx, fy = mx + 205, taban                # on aks (yerde kalir)

    tw = 52 + 76 * fren                     # temas alani yukle buyur
    d.ellipse([fx - tw, zemin_y - 18, fx + tw, zemin_y + 12],
              fill=(255, 90, 31, 60 + int(110 * fren)))

    ucgen = P(640, 900, 1.0)                 # triple clamp
    gidon = P(520, 1050, 1.0)

    d.line([(ax, ay), P(-190, 430, 0.2)], fill=(56, 68, 82), width=24)       # salincak
    d.line([P(100, 430, 0.5), P(-410, 470, 0.1), P(-700, 480, 0.0)],
           fill=(128, 138, 146), width=16)                                    # egzoz
    d.line([P(-205, 790, 0.1), P(205, 840, 0.6), (ucgen[0] - 26, ucgen[1] + 54)],
           fill=(52, 64, 78), width=18)                                       # sasi
    d.polygon([P(-290, 360, 0.2), P(-240, 700, 0.3), P(200, 730, 0.6), P(300, 390, 0.5)],
              fill=(74, 86, 97), outline=ZEMIN)                               # motor
    d.polygon([P(-850, 790, 0.0), P(-210, 830, 0.1), P(-200, 740, 0.1), P(-860, 700, 0.0)],
              fill=(28, 28, 28), outline=ZEMIN)                               # sele
    d.polygon([P(-200, 830, 0.1), P(355, 900, 0.7), P(415, 790, 0.8), P(-170, 740, 0.1)],
              fill=TURUNCU, outline=ZEMIN)                                    # depo
    d.line([(fx, fy - 6), ucgen], fill=GOLD, width=26)                        # catal
    d.line([ucgen, gidon], fill=KROM, width=13)
    d.polygon([(ucgen[0] + 8, ucgen[1] - 10), (ucgen[0] + 54, ucgen[1] + 4),
               (ucgen[0] + 50, ucgen[1] + 56), (ucgen[0] + 4, ucgen[1] + 42)],
              fill=KREM, outline=ZEMIN)                                       # far

    # --- surucu: frende one yuklenir -------------------------------------
    one = 90 * fren                          # mm cinsinden one kayma
    kalca = P(-430 + one * 0.3, 850, 0.1)
    omuz = P(-150 + one, 1300, 0.3)
    kask = P(10 + one * 1.1, 1550, 0.4)
    diz = P(-30, 560, 0.3)
    ayak = P(170, 380, 0.4)
    # Surucu motosiklete gore ACIK renkte: ayni koyulukta cizilince siluet
    # okunmuyor, sadece kask havada duruyormus gibi gorunuyordu.
    MONT = (96, 112, 130)
    for noktalar, kalinlik in (((kalca, diz, ayak), 34),
                               ((kalca, omuz), 54),
                               ((omuz, gidon), 26)):
        d.line(list(noktalar), fill=ZEMIN, width=kalinlik + 10)   # kontur
        d.line(list(noktalar), fill=MONT, width=kalinlik)
    d.ellipse([gidon[0] - 17, gidon[1] - 17, gidon[0] + 17, gidon[1] + 17], fill=(24, 24, 24))
    kr = 44
    d.ellipse([kask[0] - kr, kask[1] - kr, kask[0] + kr, kask[1] + kr],
              fill=KREM, outline=ZEMIN, width=8)
    d.polygon([(kask[0] + 6, kask[1] - 22), (kask[0] + kr, kask[1] - 16),
               (kask[0] + kr - 2, kask[1] + 18), (kask[0] + 6, kask[1] + 21)],
              fill=(58, 70, 82), outline=ZEMIN)                               # vizor
    d.polygon([(kask[0] - 40, kask[1] - 21), (kask[0] - 4, kask[1] - 41),
               (kask[0] - 10, kask[1] - 19)], fill=TURUNCU)                   # kask seridi

    _tekerlek(d, ax, ay, r, -t * hiz * 7)
    _tekerlek(d, fx, fy, r, -t * hiz * 7)

    if fren > 0.05:                                                           # on disk parlar
        d.ellipse([fx - r - 24, fy - r - 24, fx + r + 24, fy + r + 24],
                  outline=(255, 90, 31, int(110 + 120 * fren)), width=11)

    # --- agirlik dagilimi -------------------------------------------------
    on_yuk = 0.5 + 0.32 * fren
    for i, (etiket, deger, renk) in enumerate(
            (("ÖN", on_yuk, TURUNCU), ("ARKA", 1 - on_yuk, MAVI))):
        x0 = 72 + i * 190
        yuk = int(290 * deger)
        d.rounded_rectangle([x0, 470, x0 + 118, 760], 8, fill=(255, 255, 255, 20))
        d.rounded_rectangle([x0, 760 - yuk, x0 + 118, 760], 8, fill=renk)
        yazi(d, (x0 + 59, 772), etiket, 34, KREM, ortala=True)
        yazi(d, (x0 + 59, 812), f"%{int(deger * 100)}", 42, renk, ortala=True)
    yazi(d, (72, 418), "AĞIRLIK", 30, (150, 155, 162))

    # --- hiz --------------------------------------------------------------
    d.rounded_rectangle([G - 320, 470, G - 72, 612], 18, fill=(0, 0, 0, 160),
                        outline=(92, 102, 112), width=4)
    yazi(d, (G - 196, 482), f"{int(hiz * 52)}", 82, KREM if hiz > 0.02 else YESIL,
         ortala=True)
    yazi(d, (G - 196, 572), "km/h", 28, (150, 155, 160), ortala=True)

    return im


# ===========================================================================
#  SAHNE 2 · VİRAJ (sürücü gözünden)
# ===========================================================================
VIRAJ_DONGU = 13.0

# Sahnedeki durum, ekranda o anda yazan ders adimiyla CAKISMAMALI: etiket
# "KAPANIYOR" derken adim "aciliyor" diyorsa izleyen kafasi karisir. Bu yuzden
# fazlar disaridan (ders dosyasindan) verilebilir: "0:sabit,19:acilir,..."
# Her faz bir HEDEF egrilik verir; deger onceki fazin biraktigi yerden bu
# hedefe suruklenir. Boylece faz sinirinda ziplama olmaz ve "aciliyor" gercekten
# duzlesme, "kapaniyor" gercekten keskinlesme olarak gorunur.
VIRAJ_DURUM = {
    "sabit":   (0.30, "SABİT", MAVI),
    "uzak":    (0.05, "NOKTA UZAKTA", MAVI),
    "acilir":  (0.02, "AÇILIYOR", YESIL),
    "kapanir": (0.36, "KAPANIYOR", KIRMIZI),
    "engel":   (0.16, "ENGELE DEĞİL, BOŞLUĞA", TURUNCU),
}
VIRAJ_FAZLAR = None          # [(baslangic_sn, durum_adi), ...]


def fazlari_ayarla(metin):
    """'0:sabit, 19:acilir, 27:kapanir' -> sirali faz listesi."""
    global VIRAJ_FAZLAR
    if not metin:
        VIRAJ_FAZLAR = None
        return
    fazlar = []
    for parca in metin.split(","):
        t_str, _, durum = parca.strip().partition(":")
        durum = durum.strip()
        if durum not in VIRAJ_DURUM:
            raise SystemExit(f"HATA: bilinmeyen sahne fazi '{durum}'")
        fazlar.append((float(t_str), durum))
    VIRAJ_FAZLAR = sorted(fazlar)


def viraj_evre_fazli(t, toplam):
    """Ders adimlarina bagli faz cizelgesi."""
    aktif, bitis = VIRAJ_FAZLAR[0], toplam
    for i, (bas, durum) in enumerate(VIRAJ_FAZLAR):
        if t >= bas:
            aktif = (bas, durum)
            bitis = VIRAJ_FAZLAR[i + 1][0] if i + 1 < len(VIRAJ_FAZLAR) else toplam
    bas, durum = aktif
    hedef, etiket, renk = VIRAJ_DURUM[durum]
    # Baslangic: bir onceki fazin hedefi (ilk fazda kendi hedefi)
    sira = [d for _, d in VIRAJ_FAZLAR]
    i = sira.index(durum) if durum in sira else 0
    for j, (b2, d2) in enumerate(VIRAJ_FAZLAR):
        if b2 == bas and d2 == durum:
            i = j
            break
    baslangic = VIRAJ_DURUM[VIRAJ_FAZLAR[i - 1][1]][0] if i > 0 else hedef
    p = yumusak((t - bas) / max(0.5, bitis - bas))
    derinlik = baslangic + (hedef - baslangic) * p
    bukum = -(0.30 + derinlik * 1.6)          # 2B sahne icin geriye donuk uyum
    return derinlik, bukum, (etiket, renk)


def viraj_evre(t):
    """(kayboluş noktası derinliği, viraj bükümü, durum etiketi) üretir.
    derinlik kucuk = nokta uzakta. Nokta uzaklasiyorsa viraj aciliyor."""
    u = t % VIRAJ_DONGU
    if u < 4.0:                                     # açılıyor: nokta uzaklaşır
        p = u / 4.0
        return 0.30 - 0.22 * yumusak(p), -0.55 + 0.25 * p, ("AÇILIYOR", YESIL)
    if u < 8.0:                                     # kapanıyor: nokta yaklaşır
        p = (u - 4.0) / 4.0
        return 0.08 + 0.30 * yumusak(p), -0.30 - 0.50 * p, ("KAPANIYOR", KIRMIZI)
    if u < 11.0:                                    # sabit yarıçap
        return 0.20, -0.80 + 0.25 * ((u - 8.0) / 3.0), ("SABİT", MAVI)
    p = (u - 11.0) / 2.0                            # engel + kaçış boşluğu
    return 0.20, -0.55, ("ENGELE DEĞİL, BOŞLUĞA", TURUNCU)


def kare_viraj(t, toplam=55.0):
    im = Image.new("RGB", (G, Y), ZEMIN)
    d = ImageDraw.Draw(im, "RGBA")
    if VIRAJ_FAZLAR:
        derinlik, bukum, (etiket, etiket_renk) = viraj_evre_fazli(t, toplam)
        engel_ani = etiket.startswith("ENGELE")
    else:
        derinlik, bukum, (etiket, etiket_renk) = viraj_evre(t)
        engel_ani = (t % VIRAJ_DONGU) >= 11.0

    ufuk = 560
    yol_ust = ufuk + int(derinlik * 430)       # kaybolus noktasinin ekrandaki yeri

    d.rectangle([0, 0, G, ufuk + 30], fill=(14, 19, 27))
    for i in range(9):                          # yumusak tepeler
        x = i * 150 - 60
        h = 70 + ((i * 167) % 120)
        d.ellipse([x - 40, ufuk + 30 - h, x + 190, ufuk + 30 + h],
                  fill=(21, 28, 37))
    d.rectangle([0, ufuk + 30, G, Y], fill=(27, 35, 29))

    vp_x = G / 2 + bukum * 420

    def merkez(p):
        """p: 0 = kaybolus noktasi, 1 = on tekerlek hizasi.
        Bukum uzakta yogunlasir — gercek bir virajin gorunumu boyledir."""
        return G / 2 + (vp_x - G / 2) * (1 - p) ** 1.35

    def yari_genislik(p):
        # Perspektifte genislik ekran-y'si ile DOGRUSAL artar. Ustel verince
        # yol huni/diken gibi gorunuyordu.
        return 10 + p * 470

    adim = 70
    sol, sag = [], []
    for i in range(adim + 1):
        p = i / adim
        yy = yol_ust + (Y - yol_ust) * p
        cx, w = merkez(p), yari_genislik(p)
        sol.append((cx - w, yy))
        sag.append((cx + w, yy))
    d.polygon(sol + sag[::-1], fill=ASFALT)
    d.line(sol, fill=(205, 205, 200), width=6)
    d.line(sag, fill=(205, 205, 200), width=6)

    faz = (t * 1.2) % 1.0                        # kesikli orta cizgi akar
    for k in range(10):
        p0 = ((k + faz) / 10.0) ** 1.8
        p1 = ((k + 0.42 + faz) / 10.0) ** 1.8
        if p1 > 1.0:
            continue
        y0, y1 = yol_ust + (Y - yol_ust) * p0, yol_ust + (Y - yol_ust) * p1
        d.line([(merkez(p0), y0), (merkez(p1), y1)], fill=SERIT,
               width=int(3 + yari_genislik(p0) * 0.075))

    for k in range(9):                           # kenar dubalari — hiz hissi
        p0 = ((k + faz) / 9.0) ** 1.8
        yy = yol_ust + (Y - yol_ust) * p0
        w = yari_genislik(p0)
        h = 10 + 70 * p0
        for yon in (-1, 1):
            x = merkez(p0) + yon * (w + 16 + 30 * p0)
            d.line([(x, yy), (x, yy - h)], fill=(120, 126, 120), width=int(2 + 7 * p0))
            d.ellipse([x - 3 - 5 * p0, yy - h - 5 - 7 * p0, x + 3 + 5 * p0, yy - h + 5],
                      fill=TURUNCU if yon > 0 else KREM)

    # --- kaybolus noktasi isareti ----------------------------------------
    mx, my = merkez(0.0), yol_ust
    rr = int(34 * (1.0 + 0.12 * math.sin(t * 5)))
    d.ellipse([mx - rr, my - rr, mx + rr, my + rr], outline=etiket_renk, width=7)
    for dx, dy in ((-1, 0), (1, 0), (0, -1)):
        d.line([mx + dx * (rr + 20), my + dy * (rr + 20),
                mx + dx * (rr - 6), my + dy * (rr - 6)], fill=etiket_renk, width=5)

    f = font(40)
    tw = d.textlength(etiket, font=f)
    ex = min(max(mx - tw / 2 - 26, 40), G - tw - 66)
    ey = my + 58
    d.rounded_rectangle([ex, ey, ex + tw + 52, ey + 64], 14,
                        fill=(0, 0, 0, 175), outline=etiket_renk, width=4)
    yazi(d, (ex + 26, ey + 11), etiket, 40, etiket_renk)

    d.line([(G / 2, Y - 90), (mx, my)], fill=(255, 255, 255, 40), width=5)

    if engel_ani:                                # hedef sabitlemesi ani
        pe = 0.55
        ey2 = yol_ust + (Y - yol_ust) * pe
        ex2 = merkez(pe) - yari_genislik(pe) * 0.45
        d.ellipse([ex2 - 95, ey2 - 32, ex2 + 95, ey2 + 32], fill=(72, 64, 54))
        for i in range(8):
            d.ellipse([ex2 - 78 + i * 21, ey2 - 13, ex2 - 62 + i * 21, ey2 + 3],
                      fill=(124, 113, 98))
        d.line([ex2 - 78, ey2 - 60, ex2 + 78, ey2 + 52], fill=KIRMIZI, width=12)
        d.line([ex2 + 78, ey2 - 60, ex2 - 78, ey2 + 52], fill=KIRMIZI, width=12)
        gx = merkez(pe) + yari_genislik(pe) * 0.42
        d.line([(gx, ey2 + 130), (gx, ey2 - 30)], fill=YESIL, width=10)
        d.polygon([(gx - 28, ey2 - 26), (gx + 28, ey2 - 26), (gx, ey2 - 80)], fill=YESIL)

    return im


# ===========================================================================
#  SES · motor + rüzgâr
# ===========================================================================
def motor_sesi(sure, sahne):
    n = int(sure * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(5)

    if sahne == "fren":
        hiz = np.array([fren_evre(x)[0] for x in t[::441]])
        hiz = np.interp(t, t[::441], hiz)
    else:
        hiz = 0.72 + 0.1 * np.sin(2 * np.pi * t / VIRAJ_DONGU) + 0.03 * np.sin(t * 1.7)

    devir = 42 + 86 * hiz                          # ateşleme temel frekansı (Hz)
    faz = np.cumsum(2 * np.pi * devir / SR)
    ses = np.zeros(n)
    # Tiz harmonikler (6., 8.) metalik bir vizilti yapiyordu; kaldirildi ve
    # kalanlarin agirligi dusuruldu. Sonucta uzaktan gelen bogukca bir gurultu.
    for h, agirlik in ((1, 1.0), (2, 0.45), (3, 0.18), (4, 0.08)):
        ses += agirlik * np.sin(faz * h + h * 0.7)
    ses = np.tanh(ses * 0.55) * (0.35 + 0.5 * hiz)

    emme = rng.normal(0, 1, n)                     # emme/egzoz gürültüsü
    emme = np.convolve(emme, np.ones(90) / 90, mode="same")
    ses += emme * (0.22 + 0.26 * hiz)

    ruzgar = rng.normal(0, 1, n)
    ruzgar = np.convolve(ruzgar, np.ones(16) / 16, mode="same")
    ses += ruzgar * 0.06 * hiz ** 1.5

    # Alcak geciren: kalan tizleri de yumusat
    ses = np.convolve(ses, np.ones(28) / 28, mode="same")
    ses /= max(1e-9, np.abs(ses).max())
    ses *= 0.72
    gecis = int(0.4 * SR)
    ses[:gecis] *= np.linspace(0, 1, gecis)
    ses[-gecis:] *= np.linspace(1, 0, gecis)
    return ses


def wav_yaz(yol, mono):
    stereo = np.stack([mono, np.concatenate([np.zeros(300), mono])[:len(mono)] * 0.9], 1)
    veri = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(yol, "wb") as fh:
        fh.setnchannels(2)
        fh.setsampwidth(2)
        fh.setframerate(SR)
        fh.writeframes(veri.tobytes())


# ===========================================================================
def main():
    ap = argparse.ArgumentParser(description="AAE egitim sahnesi uretici")
    ap.add_argument("--sahne", choices=("fren", "viraj"), required=True)
    ap.add_argument("--sure", type=float, default=60.0)
    ap.add_argument("--cikti", default=None)
    ap.add_argument("--sessiz", action="store_true", help="motor sesi ekleme")
    ap.add_argument("--fazlar", default="",
                    help="viraj sahnesi faz cizelgesi, orn: '0:sabit,19:acilir,27:kapanir'")
    args = ap.parse_args()

    cikti = args.cikti or f"videos/sahne_{args.sahne}.mp4"
    os.makedirs(os.path.dirname(cikti) or ".", exist_ok=True)
    fazlari_ayarla(args.fazlar)
    if args.sahne == "fren":
        cizer = kare_fren
    else:
        cizer = lambda t: kare_viraj(t, args.sure)
    toplam = int(args.sure * FPS)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        ses_yolu = tmp.name
    try:
        if not args.sessiz:
            print(">> Motor sesi sentezleniyor")
            wav_yaz(ses_yolu, motor_sesi(args.sure, args.sahne))

        komut = ["ffmpeg", "-y", "-v", "error",
                 "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{G}x{Y}",
                 "-r", str(FPS), "-i", "-"]
        if not args.sessiz:
            komut += ["-i", ses_yolu]
        komut += ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
                  "-pix_fmt", "yuv420p"]
        if not args.sessiz:
            komut += ["-c:a", "aac", "-b:a", "160k", "-ac", "2", "-shortest"]
        komut += ["-movflags", "+faststart", cikti]

        print(f">> {args.sahne} sahnesi: {toplam} kare ({args.sure:.0f} sn)")
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
    print("   Telif: sahne tamamen cizimle uretildi, serbestce kullanilabilir.")


if __name__ == "__main__":
    main()
