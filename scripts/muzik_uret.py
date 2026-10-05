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
#  SADE stil: anlatimin onune gecmeyen, sakin bir yatak.
#  Yumusak yayli + tek tek dusen tel sesi + cok hafif vurus. 808, cowbell,
#  distortion yok — egitim videosunda phonk fazla one cikiyordu.
# ---------------------------------------------------------------------------
SADE_AKOR = [                      # Am - F - C - G
    [220.00, 261.63, 329.63],
    [174.61, 220.00, 261.63],
    [261.63, 329.63, 392.00],
    [196.00, 246.94, 293.66],
]


def tel(frekans, sure):
    """Piyano/telli hissi: harmonikler farkli hizda soner."""
    n = int(sure * SR)
    s = np.zeros(n)
    for h, agirlik, hiz in ((1, 1.0, 1.0), (2, 0.42, 1.7), (3, 0.20, 2.6), (5, 0.08, 4.0)):
        zarf_h = np.exp(-np.linspace(0, sure, n) * 2.3 * hiz)
        s += agirlik * np.sin(2 * np.pi * frekans * h * np.arange(n) / SR) * zarf_h
    vurus = np.exp(-np.linspace(0, sure, n) * 60) * 0.25      # tirnak sesi
    return (s / 1.7 + np.random.default_rng(3).normal(0, 1, n) * vurus) * zarf(
        n, 0.004, 0.02, 0.9, 0.05)


def yayli(frekanslar, n):
    s = np.zeros(n)
    for f in frekanslar:
        for h, a in ((1, 1.0), (2, 0.3), (3, 0.14)):
            s += a * np.sin(2 * np.pi * (f * h + 0.4) * np.arange(n) / SR) / len(frekanslar)
    return s * zarf(n, 0.9, 0.5, 0.8, 1.1) * 0.3


def uret_sade(bpm: float, sure: float, tohum: int) -> np.ndarray:
    rng = np.random.default_rng(tohum)
    vurus_s = 60.0 / bpm
    bar = 4 * vurus_s
    n = int(sure * SR)
    mix = np.zeros(n)
    desen = [0.0, 1.5, 2.0, 3.0, 3.5]

    for b in range(int(np.ceil(sure / bar))):
        t0 = b * bar
        akor = SADE_AKOR[b % len(SADE_AKOR)]
        ekle(mix, yayli(akor, int(bar * SR)), t0)
        for k, konum in enumerate(desen):
            nota = akor[(b + k) % len(akor)] * (2.0 if k % 3 == 1 else 1.0)
            ekle(mix, tel(nota, 1.5) * (0.17 if k % 2 else 0.22), t0 + konum * vurus_s)
        ekle(mix, kick() * 0.30, t0)                       # cok hafif vurus
        ekle(mix, kick() * 0.20, t0 + 2 * vurus_s)
        for i in range(8):                                  # shaker
            ekle(mix, hihat() * (0.045 if i % 2 else 0.065), t0 + i * vurus_s / 2)

    mix *= 1.0 + rng.normal(0, 0.006, n)
    mix /= max(1e-9, np.abs(mix).max())
    mix *= 0.6
    gecis = int(1.2 * SR)
    mix[:gecis] *= np.linspace(0, 1, gecis)
    mix[-gecis:] *= np.linspace(1, 0, gecis)
    return mix


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


def main() -> None:
    ap = argparse.ArgumentParser(description="AAE fon muzigi uretici")
    ap.add_argument("--stil", choices=("sade", "phonk"), default="sade",
                    help="sade = sakin yatak (varsayilan), phonk = koyu ritim")
    ap.add_argument("--bpm", type=float, default=0.0, help="0 = stile gore secilir")
    ap.add_argument("--sure", type=float, default=64.0, help="saniye")
    ap.add_argument("--tohum", type=int, default=3, help="varyasyon icin")
    ap.add_argument("--cikti", default="")
    args = ap.parse_args()

    bpm = args.bpm or (72.0 if args.stil == "sade" else 82.0)
    cikti = args.cikti or (f"assets/muzik/aae_{'sade' if args.stil == 'sade' else 'yol_okulu'}.mp3")
    print(f">> Besteleniyor: {args.stil} · {bpm:.0f} BPM · {args.sure:.0f} sn · A minor")
    mix = (uret_sade if args.stil == "sade" else uret)(bpm, args.sure, args.tohum)
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
             "-af", ("highpass=f=38,lowpass=f=11000,equalizer=f=2800:t=q:w=1.4:g=-2.5,"
                     "alimiter=limit=0.92") if args.stil == "sade" else
                    ("highpass=f=30,lowpass=f=9500,equalizer=f=2500:t=q:w=1.2:g=-3,"
                     "alimiter=limit=0.92"),
             "-c:a", "libmp3lame", "-b:a", "192k", args.cikti],
            check=True)
    finally:
        os.unlink(gecici)

    mb = os.path.getsize(args.cikti) / 1e6
    print(f"TAMAM ✓  {args.cikti} ({mb:.1f} MB)")
    print("   Telif: bu parca tamamen sentezle uretildi, serbestce kullanilabilir.")


if __name__ == "__main__":
    main()
