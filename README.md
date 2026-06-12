# 🎬 Cuma Videosu Hazırlayıcı

Elinizdeki videoyu (ör. Insta360 ile çekilmiş dikey video) **Instagram Reels / TikTok**
için "Cuma Mübarek" temalı, hazır paylaşılabilir bir videoya dönüştürür.

Videoyu GitHub'a yüklersiniz → GitHub kendi sunucusunda işler → hazır MP4'ü size verir.
**Bilgisayarınıza hiçbir program kurmanıza gerek yok.**

---

## 🚀 En kolay yol (GitHub üzerinden)

1. **Videonuzu yükleyin:** Videonuzu `videos/` klasörüne koyun.
   - Web'den: depo sayfasında `videos/` klasörüne girin → **Add file → Upload files** → videoyu sürükleyin → **Commit**.
   - > ⚠️ **Önemli:** Videonuz ~205 MB. GitHub web arayüzü tek dosyada **25 MB**, normal `git push` ise **100 MB** sınırı koyar.
     > Büyük dosya için **Git LFS** gerekir (aşağıda anlatıldı). LFS bu depoda zaten ayarlı (`.gitattributes`).
2. Yükleme bitince **Actions** sekmesine gidin. "Cuma Videosu Hazırla" iş akışı otomatik çalışır.
3. İş bitince (yeşil tik), o çalışmanın sayfasında **Artifacts → `cuma-videosu`** dosyasını indirin.
4. İndirdiğiniz `cuma_video.mp4`'ü Instagram / TikTok'ta paylaşın. ✅

> İsterseniz **Actions → Cuma Videosu Hazırla → Run workflow** ile yazıları (üst/alt metin)
> ve süreyi elle de değiştirebilirsiniz.

---

## 💻 Bilgisayarda çalıştırmak (alternatif)

`ffmpeg` kurulu olmalı (`brew install ffmpeg` / `sudo apt install ffmpeg`).

```bash
# Videonuzu videos/ klasörüne koyun, sonra:
./scripts/make_friday_video.sh

# veya yolu doğrudan verin:
./scripts/make_friday_video.sh videos/benim_videom.mp4 output/cuma_video.mp4
```

### Özelleştirme (ortam değişkenleri)

```bash
TOP_TEXT="Hayırlı Cumalar" \
BOTTOM_TEXT="Allah kabul etsin" \
DURATION=30 \
MUSIC=assets/ilahi.mp3 MUSIC_VOL=0.5 \
./scripts/make_friday_video.sh
```

| Değişken      | Açıklama                          | Varsayılan         |
|---------------|-----------------------------------|--------------------|
| `TOP_TEXT`    | Üstte görünen büyük yazı          | `Cuma Mubarek`     |
| `BOTTOM_TEXT` | Altta görünen küçük yazı          | `Hayirli Cumalar`  |
| `DURATION`    | Maksimum süre (sn) — Reels max 60 | `60`               |
| `MUSIC`       | Fon müziği dosyası (opsiyonel)    | (yok)              |
| `MUSIC_VOL`   | Fon müziği ses seviyesi (0–1)     | `0.6`              |

---

## 🎞️ Ne yapıyor?

- Videoyu **1080×1920** dikey formata kırpar (Reels/TikTok standardı).
- Üst ve alta yarı saydam şeritler + **"Cuma Mübarek"** / **"Hayırlı Cumalar"** yazılarını ekler.
- Başta açılış, sonda kapanış **fade** efekti uygular.
- Süreyi Reels sınırına (varsayılan 60 sn) kırpar.
- İsteğe bağlı **fon müziği** ekler (orijinal sesle karıştırır).

---

## 📦 Büyük videolar için Git LFS kurulumu (tek seferlik)

```bash
git lfs install
git lfs track "videos/*.mp4"   # zaten .gitattributes içinde tanımlı
git add .gitattributes videos/benim_videom.mp4
git commit -m "Video ekle"
git push
```

> LFS kullanmak istemiyorsanız: videoyu önce ~50–80 MB'a küçültüp (ör. telefonda
> "sıkıştır" veya `ffmpeg -crf 28`) yükleyebilirsiniz.

---

## 📁 Klasör yapısı

```
videos/    → ham videolarınızı buraya koyun
output/    → işlenmiş cuma videosu buraya çıkar
assets/    → fon müziği, logo vb.
scripts/   → make_friday_video.sh (ffmpeg betiği)
.github/   → otomatik render iş akışı
```
