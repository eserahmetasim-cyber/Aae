#!/usr/bin/env python3
"""
muzik_uret.py
-------------------------------------------------------------------
AAE eğitim videoları için fon müziği üretir. Parça tamamen burada
sentezlenir — hiçbir yerden örnek alınmaz, telif sorunu çıkmaz.

Stil: koyu, ağır tempolu phonk/trap yatağı (808 bas + cowbell motif).
Anlatımın önüne geçmesin diye tiz bölge sönük, orta bant boş bırakılır.

Kullanım:
  python3 scripts/muzik_uret.py                      # varsayılan parça
  python3 scripts/muzik_uret.py --sure 90 --bpm 76
  python3 scripts/muzik_uret.py --cikti assets/muzik/baska.mp3
-------------------------------------------------------------------
"""
import argparse
import math
import os
import subprocess
import tempfile
import wave

import numpy as np

SR = 44100
# A minor: dörder barlık döngü — i, i, VI, VII
AKOR_KOKU = [55.00, 55.00, 43.65, 49.00]        # A1, A1, F1, G1
PENTATONIK = {"A": 440.00, "C": 523.25, "D": 587.33, "E": 659.25, "G": 783.99}
# Dort barlik sabit ezgi (A minor pentatonik) — (vurus, nota, vurgu)
MOTIF = [
    [(0.0, "A", 1.0), (1.5, "C", 0.7), (2.5, "A", 0.8), (3.0, "E", 0.6)],
    [(0.5, "G", 0.8), (1.5, "E", 0.7), (3.0, "D", 0.6)],
    [(0.0, "C", 1.0), (1.5, "D", 0.7), (2.5, "C", 0.8), (3.0, "A", 0.6)],
    [(0.5, "E", 0.9), (1.5, "D", 0.7), (2.5, "C", 0.6), (3.5, "A", 0.8)],
]


def zarf(n, atak, dusus, surdurme=0.0, birakma=0.25):
    """Basit ADSR; n örnek uzunluğunda."""
    a = max(1, int(atak * SR))
    d = max(1, int(dusus * SR))
    r = max(1, int(birakma * SR))
    s = max(0, n - a - d - r)
    return np.concatenate([
        np.linspace(0, 1, a),
        np.linspace(1, surdurme, d),
        np.full(s, surdurme),
        np.linspace(surdurme, 0, r),
    ])[:n]


def ton(frekans, n, dalga="sin"):
    """frekans skaler ya da n uzunlugunda dizi olabilir (glide icin)."""
    f = np.full(n, frekans, dtype=float) if np.isscalar(frekans) else frekans[:n]
    faz = np.cumsum(2 * np.pi * f / SR)
    if dalga == "kare":
        return np.sign(np.sin(faz))
    if dalga == "testere":
        return 2 * (faz / (2 * np.pi) % 1.0) - 1.0
    return np.sin(faz)


def bas_808(kok, sure, n=None):
    """Baslangicta bir oktav yukaridan kayan, yumusak kirpilmis 808."""
    n = n or int(sure * SR)
    glide = np.concatenate([
        np.geomspace(kok * 2.2, kok, max(1, int(0.07 * SR))),
        np.full(max(0, n - int(0.07 * SR)), kok),
    ])[:n]
    s = ton(glide, n)
    s *= zarf(n, 0.004, 0.30, 0.55, 0.45)
    return np.tanh(s * 2.1) * 0.9          # yumusak doyma -> govde


def kick(n=None):
    n = n or int(0.22 * SR)
    glide = np.geomspace(140, 48, n)
    return ton(glide, n) * zarf(n, 0.001, 0.09, 0.0, 0.12)


def trampet(n=None):
    n = n or int(0.19 * SR)
    gurultu = np.random.default_rng(7).normal(0, 1, n)
    govde = ton(185, n) * 0.35
    return (gurultu * 0.65 + govde) * zarf(n, 0.001, 0.07, 0.0, 0.11)


def hihat(acik=False):
    """Gurultuyu tek kutuplu fark filtresiyle tizlestirir: hat tiz bantta
    kalir, orta bandi doldurup anlatimin onune gecmez."""
    n = int((0.16 if acik else 0.045) * SR)
    g = np.random.default_rng(11).normal(0, 1, n + 1)
    g = np.diff(g)                       # birinci fark = +6 dB/oktav tizlestirme
    g /= max(1e-9, np.abs(g).max())
    return g * zarf(n, 0.001, 0.02 if not acik else 0.07, 0.0, 0.03)


def cowbell(frekans, sure=0.16):
    """Klasik 808 cowbell: iki kare dalga + kisa sönüm."""
    n = int(sure * SR)
    s = ton(frekans, n, "kare") * 0.5 + ton(frekans * 1.48, n, "kare") * 0.5
    return s * zarf(n, 0.001, 0.05, 0.1, 0.09)


def pad(kok, n):
    """Çok kısık, hafif detone yaylı yatak — boşluğu doldurur."""
    s = np.zeros(n)
    for carpan, detune in ((2, 0.0), (3, 0.6)):
        s += ton(kok * carpan + detune, n, "testere") / carpan
    return s * zarf(n, 1.2, 0.6, 0.85, 1.4) * 0.13


def ekle(hedef, parca, konum):
    i = int(konum * SR)
    son = min(len(hedef), i + len(parca))
    if son > i:
        hedef[i:son] += parca[: son - i]


def uret(bpm: float, sure: float, tohum: int) -> np.ndarray:
    rng = np.random.default_rng(tohum)
    vurus = 60.0 / bpm
    bar = 4 * vurus
    n = int(sure * SR)
    davul = np.zeros(n)
    bas = np.zeros(n)
    melodi = np.zeros(n)
    yatak = np.zeros(n)

    bar_sayisi = int(np.ceil(sure / bar))
    notalar = list(PENTATONIK.values())

    for b in range(bar_sayisi):
        t0 = b * bar
        kok = AKOR_KOKU[b % len(AKOR_KOKU)]

        # --- davul: yarim tempo phonk hissi ---
        ekle(davul, kick() * 0.95, t0)
        ekle(davul, kick() * 0.75, t0 + 2.5 * vurus)
        ekle(davul, trampet() * 0.55, t0 + 2 * vurus)
        seyrek = (b % 8 == 4)                    # arada nefes alsin
        for i in range(8):                       # 1/8 hi-hat
            if seyrek and i % 2:
                continue
            v = 0.10 if i % 2 else 0.17
            ekle(davul, hihat() * v, t0 + i * vurus / 2)
        if b % 4 == 3:                           # bar sonu 1/16 roll
            for i in range(4):
                ekle(davul, hihat() * 0.13, t0 + 3.5 * vurus + i * vurus / 4)
        if b % 8 == 7:
            ekle(davul, hihat(acik=True) * 0.15, t0 + 3 * vurus)

        # --- 808 bas ---
        ekle(bas, bas_808(kok, 1.6 * vurus) * 0.52, t0)
        ekle(bas, bas_808(kok, 0.9 * vurus) * 0.40, t0 + 2.5 * vurus)

        # --- cowbell motifi: ilk iki barda sus, sonra gir ---
        if b >= 2:
            for konum, nota, vurgu in MOTIF[b % len(MOTIF)]:
                ekle(melodi, cowbell(PENTATONIK[nota]) * 0.10 * vurgu, t0 + konum * vurus)

        # --- yaylı yatak ---
        ekle(yatak, pad(kok, int(bar * SR)), t0)

    # Hafif insan hissi: hi-hat katmanina cok kucuk zamanlama/seviye sapmasi
    davul *= 1.0 + rng.normal(0, 0.012, n)

    mix = davul * 0.55 + bas * 1.0 + melodi * 0.9 + yatak * 1.0
    # NOT: burada hareketli ortalama ile yumusatma YAPILMAZ — 7 katsayili
    # kutu filtre 6.3 kHz ve katlarinda tarak centigi aciyor (spektrogramda
    # goruldu). Ton sekillendirme asagida ffmpeg'in dogru filtreleriyle.
    mix /= max(1e-9, np.abs(mix).max())
    mix *= 0.63                                   # tepe ~ -4 dBFS, kafa payi kalsin

    # Dongu dikisi duyulmasin: basta ve sonda kisa gecis
    gecis = int(0.9 * SR)
    mix[:gecis] *= np.linspace(0, 1, gecis)
    mix[-gecis:] *= np.linspace(1, 0, gecis)
    return mix


# ---------------------------------------------------------------------------
#  SADE stil — sakin, anlatimin onune gecmeyen yatak.
#  Telli ses gercek bir tel gibi uretilir (Karplus-Strong: gurultu patlamasi
#  bir gecikme hattinda donerken her turda yumusar), ustune bas hatti, yumusak
#  yayli ve oda yankisi gelir. Duzenleme de var: parca bos baslar, acilir,
#  sonda incelir — tek dongunun 64 saniye aynen tekrari cansiz duruyordu.
# ---------------------------------------------------------------------------
SADE_ILERLEME = [                  # Am7 - Fmaj7 - Cmaj7 - G6  (kok, akor notalari)
    (110.00, [220.00, 261.63, 329.63, 392.00]),
    (87.31,  [174.61, 261.63, 329.63, 392.00]),
    (130.81, [196.00, 261.63, 329.63, 440.00]),
    (98.00,  [196.00, 246.94, 293.66, 392.00]),
]
SADE_DESEN = [(0.0, 0), (1.0, 2), (1.75, 1), (2.5, 3), (3.25, 2)]   # (vurus, akor notasi)


def tel_cal(frekans, sure, parlaklik=0.42, tohum=0):
    """Karplus-Strong: tel sesi. Donguyu periyot periyot vektorize ederiz,
    ornek ornek Python dongusu cok yavas olurdu."""
    n = int(sure * SR)
    N = max(8, int(round(SR / frekans)))
    rng = np.random.default_rng(1000 + tohum)
    tohum_blok = rng.uniform(-1, 1, N)
    # Baslangic patlamasini yumusat: tiz tirmik sesi azalsin
    tohum_blok = np.convolve(tohum_blok, np.ones(3) / 3, mode="same") * parlaklik \
        + tohum_blok * (1 - parlaklik)
    cikti = np.zeros(n + N)
    cikti[:N] = tohum_blok
    sonum = 0.994
    i = N
    while i < len(cikti):
        uzunluk = min(N, len(cikti) - i)
        onceki = cikti[i - N:i - N + uzunluk]
        kaydirilmis = cikti[i - N - 1:i - N - 1 + uzunluk] if i - N - 1 >= 0 else onceki
        cikti[i:i + uzunluk] = 0.5 * (onceki + kaydirilmis) * sonum
        i += uzunluk
    s = cikti[:n]
    return s * np.exp(-np.linspace(0, sure, n) * 1.15)


def bas_cal(frekans, sure):
    n = int(sure * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * frekans * t) * 0.8
         + np.sin(2 * np.pi * frekans * 2 * t) * 0.14
         + np.sin(2 * np.pi * frekans * 3 * t) * 0.05)
    return s * zarf(n, 0.02, 0.35, 0.55, 0.5)


def yayli(frekanslar, n):
    """Hafif detone yigin — tek frekans duz ve sentetik duruyor."""
    s = np.zeros(n)
    for k, f in enumerate(frekanslar):
        for detune in (-0.5, 0.0, 0.6):
            s += np.sin(2 * np.pi * (f + detune) * np.arange(n) / SR) / (len(frekanslar) * 3)
        s += np.sin(2 * np.pi * (f * 2 + 0.3) * np.arange(n) / SR) * 0.12 / len(frekanslar)
    return s * zarf(n, 1.1, 0.7, 0.85, 1.3) * 0.5


def firca(n=None):
    """Yumusak firca vurusu: beyaz gurultu yerine sunmus, kisik."""
    n = n or int(0.22 * SR)
    g = np.random.default_rng(23).normal(0, 1, n)
    g = np.convolve(g, np.ones(5) / 5, mode="same")
    return g * zarf(n, 0.006, 0.10, 0.0, 0.10)


def oda_yankisi(sure=1.9):
    """Sentetik oda tepkisi: sonumlenen gurultu + birkac erken yansima."""
    n = int(sure * SR)
    rng = np.random.default_rng(77)
    ir = rng.normal(0, 1, n) * np.exp(-np.linspace(0, 1, n) * 5.2)
    ir = np.convolve(ir, np.ones(9) / 9, mode="same")       # tizleri sondur
    for gecikme, kazanc in ((0.011, 0.5), (0.023, 0.38), (0.037, 0.3), (0.053, 0.22)):
        i = int(gecikme * SR)
        ir[i] += kazanc
    ir[0] = 1.0
    return ir / np.abs(ir).max()


def yanki_uygula(x, ir, islak=0.26):
    """FFT ile konvolusyon — np.convolve bu uzunlukta cok yavas kalir."""
    uzunluk = len(x) + len(ir) - 1
    boyut = 1 << (uzunluk - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, boyut) * np.fft.rfft(ir, boyut), boyut)[:len(x)]
    y /= max(1e-9, np.abs(y).max())
    return x * (1 - islak) + y * islak


def uret_sade(bpm: float, sure: float, tohum: int) -> np.ndarray:
    rng = np.random.default_rng(tohum)
    vurus_s = 60.0 / bpm
    bar = 4 * vurus_s
    n = int(sure * SR)
    yatak = np.zeros(n)        # yayli + tel (yanki buraya)
    alt = np.zeros(n)          # bas + vurus (kuru kalir, bulanmasin)
    bar_sayisi = int(np.ceil(sure / bar))

    for b in range(bar_sayisi):
        t0 = b * bar
        kok, akor = SADE_ILERLEME[b % len(SADE_ILERLEME)]
        kalan = bar_sayisi - b

        ekle(yatak, yayli(akor, int(bar * SR)), t0)                     # yayli hep var

        if b >= 1:                                                      # tel 2. bardan
            guc = min(1.0, (b - 1) / 3.0) * (0.55 if kalan <= 2 else 1.0)
            for k, (konum, idx) in enumerate(SADE_DESEN):
                if kalan <= 2 and k % 2:
                    continue                                            # sonda incel
                nota = akor[idx] * (2.0 if (b + k) % 7 == 3 else 1.0)
                ekle(yatak, tel_cal(nota, 2.2, tohum=b * 7 + k)
                     * 0.30 * guc * (0.78 if k % 2 else 1.0),
                     t0 + konum * vurus_s)

        if 3 <= b < bar_sayisi - 1:                                     # bas 4. bardan
            ekle(alt, bas_cal(kok, bar * 0.62) * 0.46, t0)
            ekle(alt, bas_cal(kok * 1.5, bar * 0.22) * 0.26, t0 + 2.6 * vurus_s)
            ekle(alt, firca() * 0.11, t0 + vurus_s)
            ekle(alt, firca() * 0.14, t0 + 3 * vurus_s)

    yatak = yanki_uygula(yatak, oda_yankisi(), islak=0.30)
    mix = yatak * 0.92 + alt
    mix *= 1.0 + rng.normal(0, 0.004, n)
    mix /= max(1e-9, np.abs(mix).max())
    mix *= 0.62
    gecis = int(1.6 * SR)
    mix[:gecis] *= np.linspace(0, 1, gecis) ** 1.5
    mix[-gecis:] *= np.linspace(1, 0, gecis) ** 1.5
    return mix



# ---------------------------------------------------------------------------
#  Baska karakterler: piyano / lofi / atmosfer
# ---------------------------------------------------------------------------
def piyano_nota(frekans, sure, guc=1.0):
    """Toplamsal piyano: kismi sesler hafif akortsuz (inharmonisite) ve
    yukseklere gidildikce daha hizli soner; basta cekic gurultusu var."""
    n = int(sure * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    B = 0.0004
    for h in range(1, 13):
        f = frekans * h * math.sqrt(1 + B * h * h)
        if f > 12000:
            break
        a = (1.0 / h ** 1.35) * (0.85 if h % 2 == 0 else 1.0)
        s += a * np.sin(2 * np.pi * f * t) * np.exp(-t * (1.1 + 0.42 * h))
    cekic = np.random.default_rng(int(frekans) % 97).normal(0, 1, n) * np.exp(-t * 150)
    s = s / 2.1 + cekic * 0.05
    return s * zarf(n, 0.002, 0.03, 0.92, 0.12) * guc


def uret_piyano(bpm, sure, tohum):
    vurus_s, n = 60.0 / bpm, int(sure * SR)
    bar = 4 * vurus_s
    yatak = np.zeros(n)
    ezgi = [(0.0, 0), (1.0, 2), (2.0, 1), (3.0, 3), (3.5, 2)]
    for b in range(int(np.ceil(sure / bar))):
        t0 = b * bar
        kok, akor = SADE_ILERLEME[b % len(SADE_ILERLEME)]
        ekle(yatak, yayli(akor, int(bar * SR)) * 0.55, t0)            # cok kisik yayli
        ekle(yatak, piyano_nota(kok / 2, bar * 0.9, 0.5), t0)          # sol el
        if b >= 1:
            for k, (konum, idx) in enumerate(ezgi):
                if b % 4 == 3 and k > 2:
                    continue
                ekle(yatak, piyano_nota(akor[idx] * (2 if (b + k) % 5 == 2 else 1),
                                        2.6, 0.30 if k % 2 else 0.38),
                     t0 + konum * vurus_s)
    mix = yanki_uygula(yatak, oda_yankisi(2.2), islak=0.34)
    mix /= max(1e-9, np.abs(mix).max())
    return mix * 0.62


def uret_lofi(bpm, sure, tohum):
    rng = np.random.default_rng(tohum)
    vurus_s, n = 60.0 / bpm, int(sure * SR)
    bar = 4 * vurus_s
    yatak, alt = np.zeros(n), np.zeros(n)
    for b in range(int(np.ceil(sure / bar))):
        t0 = b * bar
        kok, akor = SADE_ILERLEME[b % len(SADE_ILERLEME)]
        # Rhodes benzeri: sinus + hafif can kismi, yavas tremolo
        m = int(bar * SR)
        tt = np.arange(m) / SR
        rh = np.zeros(m)
        for f in akor:
            rh += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 1.3)
            rh += 0.18 * np.sin(2 * np.pi * f * 4.1 * tt) * np.exp(-tt * 3.4)
        rh *= (1 + 0.16 * np.sin(2 * np.pi * 4.6 * tt)) / len(akor)     # tremolo
        ekle(yatak, rh * 0.5, t0)
        ekle(alt, bas_cal(kok / 2, bar * 0.55) * 0.5, t0)
        ekle(alt, kick() * 0.5, t0)
        ekle(alt, kick() * 0.34, t0 + 2.5 * vurus_s)
        ekle(alt, trampet() * 0.26, t0 + 2 * vurus_s)
        for i in range(8):
            ekle(alt, hihat() * (0.05 if i % 2 else 0.08), t0 + i * vurus_s / 2)
    catirti = rng.normal(0, 1, n) * (rng.random(n) < 0.0016) * 0.35     # plak catirtisi
    mix = yanki_uygula(yatak, oda_yankisi(1.3), islak=0.2) * 0.9 + alt + catirti
    mix /= max(1e-9, np.abs(mix).max())
    return mix * 0.62


def uret_atmosfer(bpm, sure, tohum):
    n = int(sure * SR)
    t = np.arange(n) / SR
    mix = np.zeros(n)
    bar = 8.0
    for b in range(int(np.ceil(sure / bar))):
        kok, akor = SADE_ILERLEME[b % len(SADE_ILERLEME)]
        m = int(bar * 1.7 * SR)
        tt = np.arange(m) / SR
        kat = np.zeros(m)
        for f in akor:
            for d in (-0.7, 0.0, 0.8):
                kat += np.sin(2 * np.pi * (f / 2 + d) * tt) / (len(akor) * 3)
            kat += 0.25 * np.sin(2 * np.pi * (f * 2) * tt) / len(akor)
        kat *= zarf(m, 2.2, 1.6, 0.7, 2.6)
        ekle(mix, kat * 0.55, b * bar)
        ekle(mix, bas_cal(kok / 2, bar * 0.8) * 0.3, b * bar)
    mix = np.convolve(mix, np.ones(12) / 12, mode="same")               # tizleri kis
    mix = yanki_uygula(mix, oda_yankisi(2.8), islak=0.42)
    mix *= 0.85 + 0.15 * np.sin(2 * np.pi * t / 26.0)                   # yavas nefes
    mix /= max(1e-9, np.abs(mix).max())
    return mix * 0.6


# ---------------------------------------------------------------------------
#  KEMAN + HIPHOP
# ---------------------------------------------------------------------------
# A minor, boom-bap kalip. Keman toplamali sentezle: harmonikler + vibrato +
# yay gurultusu. Tek sinus "keman" gibi duymuyor; govdeyi veren sey harmonik
# agirliklarindaki formant tepeleri (~300 Hz ve ~700 Hz).
KEMAN_ILERLEME = [                       # (bas koku, keman akoru)
    (55.00, (440.00, 523.25, 659.25)),   # Am
    (43.65, (349.23, 440.00, 523.25)),   # F
    (65.41, (392.00, 523.25, 659.25)),   # C
    (49.00, (392.00, 493.88, 587.33)),   # G
]
# (vurus, frekans, sure_vurus) - dort barlik ezgi
KEMAN_EZGI = [
    [(0.0, 659.25, 1.5), (1.5, 523.25, 1.0), (2.5, 587.33, 1.5)],
    [(0.0, 523.25, 2.0), (2.0, 440.00, 2.0)],
    [(0.0, 783.99, 1.5), (1.5, 659.25, 1.0), (2.5, 523.25, 1.5)],
    [(0.0, 587.33, 1.5), (1.5, 493.88, 1.0), (2.5, 440.00, 1.5)],
]


def keman_nota(frekans, sure, guc=1.0, vibrato=5.6, tohum=0):
    """Yayli calgi: 16 harmonik, formant agirlikli; vibrato faz uzerinden
    uygulanir ki frekans gercekten salinsin, genlik degil."""
    n = int(sure * SR)
    t = np.arange(n) / SR
    # vibrato ilk 120 ms'de yok, sonra aciliyor - gercek yay boyle calar
    derinlik = 0.004 * np.clip((t - 0.12) / 0.25, 0.0, 1.0)
    faz = 2 * np.pi * frekans * (t + derinlik / (2 * np.pi * vibrato)
                                 * np.sin(2 * np.pi * vibrato * t))
    s = np.zeros(n)
    for h in range(1, 17):
        fh = frekans * h
        if fh > 11000:
            break
        a = h ** -1.15
        a *= 1.0 + 0.9 * np.exp(-((fh - 300.0) / 130.0) ** 2) \
                 + 0.7 * np.exp(-((fh - 720.0) / 230.0) ** 2)
        s += a * np.sin(faz * h + (h % 3))
    s /= max(1e-9, np.abs(s).max())
    # yay gurultusu: atakta duyulur, sonra siniri
    rng = np.random.default_rng(500 + tohum)
    g = np.diff(rng.normal(0, 1, n + 1))
    g /= max(1e-9, np.abs(g).max())
    s += g * 0.05 * np.exp(-t * 7.0)
    return s * zarf(n, 0.055, 0.18, 0.80, 0.30) * guc


def uret_keman(bpm, sure, tohum):
    """Keman + hiphop: boom-bap davul, 808, pizzicato ve keman ezgi."""
    vurus, n = 60.0 / bpm, int(sure * SR)
    bar = 4 * vurus
    davul, enstruman = np.zeros(n), np.zeros(n)
    rng = np.random.default_rng(tohum)

    for b in range(int(np.ceil(sure / bar))):
        t0 = b * bar
        kok, akor = KEMAN_ILERLEME[b % len(KEMAN_ILERLEME)]

        # --- boom-bap: 1 ve 3-ten hemen sonra kick, 2 ve 4-te trampet ------
        for v in (0.0, 1.75, 2.5):
            ekle(davul, kick() * 0.95, t0 + v * vurus)
        for v in (1.0, 3.0):
            ekle(davul, trampet() * 0.62, t0 + v * vurus)
        for k in range(8):                                  # 8-lik hatlar
            acik = (k == 7 and b % 2 == 1)
            ekle(davul, hihat(acik) * (0.17 if k % 2 else 0.26),
                 t0 + k * vurus / 2)
        ekle(enstruman, bas_808(kok, bar * 0.92) * 0.60, t0)

        # --- pizzicato: olcunun ikinci yarisinda akor arpeji --------------
        for k, f in enumerate(akor):
            ekle(enstruman, tel_cal(f / 2, 1.1, 0.5, tohum + k) * 0.17,
                 t0 + (2.0 + k * 0.5) * vurus)

        # --- keman ezgi: ilk bar bos, kulagi davula alistirir -------------
        if b >= 1:
            for v, f, uz in KEMAN_EZGI[b % len(KEMAN_EZGI)]:
                oktav = 0.5 if b % 8 >= 4 else 1.0          # ikinci devir pes
                ekle(enstruman, keman_nota(f * oktav, uz * vurus, 0.42,
                                           tohum=b * 7 + int(v * 2)),
                     t0 + v * vurus)
            ekle(enstruman, yayli([f * 0.5 for f in akor], int(bar * SR)) * 0.30, t0)

    enstruman = yanki_uygula(enstruman, oda_yankisi(1.7), islak=0.26)
    mix = davul * 0.52 + enstruman
    mix /= max(1e-9, np.abs(mix).max())
    return mix * 0.72


def wav_yaz(yol: str, mono: np.ndarray) -> None:
    # Hafif genislik: sag kanali 11 ms geciktir
    gecikme = int(0.011 * SR)
    sag = np.concatenate([np.zeros(gecikme), mono])[: len(mono)]
    stereo = np.stack([mono, sag * 0.93], axis=1)
    veri = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(yol, "wb") as fh:
        fh.setnchannels(2)
        fh.setsampwidth(2)
        fh.setframerate(SR)
        fh.writeframes(veri.tobytes())


# Stile gore ton sekillendirme. Keman ustte daha genis birakilir, yoksa
# yayli parlakligini kaybedip sentetik duyuluyor.
TON_ZINCIRI = {
    "sade": "highpass=f=38,lowpass=f=11000,equalizer=f=2800:t=q:w=1.4:g=-2.5,"
            "alimiter=limit=0.92",
    "keman": "highpass=f=32,lowpass=f=12500,equalizer=f=2600:t=q:w=1.3:g=-2.5,"
             "alimiter=limit=0.92",
    "_": "highpass=f=30,lowpass=f=9500,equalizer=f=2500:t=q:w=1.2:g=-3,"
         "alimiter=limit=0.92",
}


def main() -> None:
    ap = argparse.ArgumentParser(description="AAE fon muzigi uretici")
    ap.add_argument("--stil",
                    choices=("sade", "phonk", "piyano", "lofi", "atmosfer",
                             "keman"),
                    default="sade",
                    help="sade | piyano | lofi | atmosfer | phonk | keman")
    ap.add_argument("--bpm", type=float, default=0.0, help="0 = stile gore secilir")
    ap.add_argument("--sure", type=float, default=64.0, help="saniye")
    ap.add_argument("--tohum", type=int, default=3, help="varyasyon icin")
    ap.add_argument("--cikti", default="")
    args = ap.parse_args()

    VARSAYILAN_BPM = {"sade": 70.0, "piyano": 64.0, "lofi": 76.0,
                      "atmosfer": 60.0, "phonk": 82.0, "keman": 88.0}
    URETICI = {"sade": uret_sade, "piyano": uret_piyano, "lofi": uret_lofi,
               "atmosfer": uret_atmosfer, "phonk": uret, "keman": uret_keman}
    bpm = args.bpm or VARSAYILAN_BPM[args.stil]
    cikti = args.cikti or f"assets/muzik/aae_{args.stil}.mp3"
    print(f">> Besteleniyor: {args.stil} · {bpm:.0f} BPM · {args.sure:.0f} sn · A minor")
    mix = URETICI[args.stil](bpm, args.sure, args.tohum)
    args.cikti = cikti

    os.makedirs(os.path.dirname(args.cikti) or ".", exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        gecici = tmp.name
    try:
        wav_yaz(gecici, mix)
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", gecici,
             # 30 Hz alti gereksiz, 9.5 kHz ustu tiz anlatimla cakisiyor;
             # 2.5 kHz civarini da biraz acalim ki konusma bandi bos kalsin.
             # Tek zincir: once ton sekillendirme, sonra seviye. Daha once
             # -af iki kez veriliyordu ve ikincisi birincisini eziyordu, yani
             # highpass/lowpass hic uygulanmiyordu.
             # Stiller arasi seviye farki karsilastirmayi bozuyordu: hepsi
             # ayni hedefe (-16 LUFS) oturtulur, son miks zaten -14'e normalize.
             "-af", TON_ZINCIRI.get(args.stil, TON_ZINCIRI["_"])
                    + ",loudnorm=I=-16:TP=-1.5:LRA=11",
             "-c:a", "libmp3lame", "-b:a", "192k", args.cikti],
            check=True)
    finally:
        os.unlink(gecici)

    mb = os.path.getsize(args.cikti) / 1e6
    print(f"TAMAM ✓  {args.cikti} ({mb:.1f} MB)")
    print("   Telif: bu parca tamamen sentezle uretildi, serbestce kullanilabilir.")


if __name__ == "__main__":
    main()
