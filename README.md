# 🏍️ AAE · Motosiklet Eğitim Videosu Üretimi

Ham sürüş çekimini, **tek bir ders dosyasından** okunan metinlerle dikey (1080×1920)
bir eğitim videosuna dönüştürür ve **YouTube (Shorts)** ile **Instagram (Reels)**
platformlarına yükler.

Kurallar: [KURALLAR.md](KURALLAR.md) · Her ders tek dosya: `content/dersler/*.yml`

---

## 🚀 Akış

```
videos/ham_cekim.mp4  +  content/dersler/01-acil-fren.yml
                    │
                    ▼  scripts/make_training_video.sh  (ffmpeg)
     output/2026-10-03_ders01_acil-fren_v1.mp4
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
  YouTube (private)       Instagram Reels
 publish_youtube.py     publish_instagram.py
```

**Tek kaynak kuralı:** başlık, açıklama, caption, etiketler, ekrandaki adımlar —
hepsi ders dosyasından gelir. İki platformun metni birbirinden ayrışmaz.

---

## 1️⃣ Yeni ders ekle

```bash
cp content/dersler/_sablon.yml content/dersler/02-viraj-bakisi.yml
```

Doldurulacak alanlar:

| Alan | Ne işe yarar |
|---|---|
| `ders_no`, `slug`, `baslik` | Zorunlu. Açılış kartı, üst bant ve dosya adı. (`no` YAML'da boolean olduğu için `ders_no`) |
| `alt_baslik` | Açılış kartında tek cümlelik özet |
| `kaynak` | Ham çekim yolu — boş bırakılırsa `videos/` içindeki ilk video |
| `sahne` | Çekim yoksa arka planı çizimle üret: `fren` veya `viraj` |
| `sahne_fazlari` | Viraj sahnesindeki durumları adımlarla hizalar (aşağıda) |
| `baslangic` | Uzun çekimden parça seç: kaçıncı saniyeden başlasın (örn. `150`) |
| `sure` | Saniye (1–90) |
| `kaynak_ses` | Motorun gerçek ses seviyesi (0 = sustur, 1 = olduğu gibi) |
| `muzik` / `muzik_ses` | Fon müziği dosyası ve seviyesi |
| `adimlar` | **Eğitimin özü:** `t` saniyesinde başlayıp `sure` saniye ekranda kalan maddeler |
| `kapanis` | Son 3 saniyedeki çıkarım + takip çağrısı |
| `youtube:` | başlık, açıklama, etiketler, gizlilik |
| `instagram:` | caption, `feed_de_paylas` |

Doğrula:

```bash
python3 scripts/lesson.py --liste                              # tüm dersler
python3 scripts/lesson.py content/dersler/02-viraj-bakisi.yml  # tek ders özeti
```

Hatalı süre, çok uzun caption ya da 30'dan fazla etiket **render'dan önce** yakalanır.

---

## 2️⃣ Render

**GitHub üzerinden (önerilen, bilgisayara kurulum yok):**
Ham videoyu `videos/` klasörüne yükle → **Actions** sekmesinde iş otomatik çalışır →
bitince **Artifacts → `egitim-videosu`** dosyasını indir.

> ⚠️ Büyük dosya: GitHub web yüklemesi **25 MB**, normal `git push` **100 MB** sınırlı.
> `videos/` için **Git LFS** zaten tanımlı (`.gitattributes`):
> ```bash
> git lfs install
> git add videos/benim_cekimim.mp4 && git commit -m "Ham cekim" && git push
> ```

**Bilgisayarda:**

```bash
sudo apt install ffmpeg jq fonts-dejavu-core     # ya da: brew install ffmpeg jq
pip install -r requirements-publish.txt

./scripts/make_training_video.sh                                   # ilk ders
./scripts/make_training_video.sh content/dersler/01-acil-fren.yml  # belirli ders
KAYNAK=videos/baska.mp4 ./scripts/make_training_video.sh content/dersler/01-acil-fren.yml
```

Videonun ne ürettiği: açılış kartı (2.6 sn) → üst bant (ders no + başlık) ve alt bant
(`@aae_motorcycle`) üzerinde zamanlı adımlar → kapanış kartı (3 sn). Kaynakta ses yoksa
sessiz ses kanalı eklenir (platformlar ses kanalı bekler).

---

## 3️⃣ Yayınla

**Actions → Egitim Videosu → Run workflow** ile:

| Girdi | Seçenekler | Varsayılan |
|---|---|---|
| `ders` | ders dosyası yolu | boş = ilk ders |
| `yayin` | `yok` · `youtube` · `instagram` · `hepsi` | `youtube` |
| `gizlilik` | `private` · `unlisted` · `public` | `private` |
| `ig_yolu` | `resumable` · `release-url` | `resumable` |

> **Instagram asla kendiliğinden yayınlanmaz.** `videos/`'a push ettiğinde yalnızca
> render + (secret varsa) YouTube'a **private** yükleme olur. Instagram için işi elle
> başlatıp `yayin` değerini seçmen gerekir — çünkü yayınlanan Reel **anında herkese
> açıktır ve geri alınamaz**.

Komut satırından:

```bash
python3 scripts/publish_youtube.py   --ders content/dersler/01-acil-fren.yml --kuru
python3 scripts/publish_instagram.py --ders content/dersler/01-acil-fren.yml --kuru
```

`--kuru` hiçbir istek göndermeden ne yapılacağını gösterir.
`publish_instagram.py --sadece-hazirla` videoyu yükleyip işletir ama **yayınlamaz**.

---

## 🎬 Çizilen sahneler

Elinde uygun çekim yoksa arka planı hat kendisi çizer. Ders dosyasına
`sahne: fren` ya da `sahne: viraj` yazman yeterli — `kaynak` boşsa sahne
render sırasında üretilir. Her şey çizimle oluşur, telif sorunu yoktur.

| Sahne | Ne gösterir |
|---|---|
| `fren` | Yandan görünüm. Frene basınca çatal çöker, motosiklet öne yüklenir, ön lastiğin temas alanı büyür; soldaki çubuklar ön/arka yük dağılımını %50/%50'den %82/%17'ye canlı taşır, sağda hız düşer. |
| `viraj` | Sürücü gözünden yol. Yolun iki kenarının birleştiği **kayboluş noktası** uzaklaşır (viraj açılıyor), yaklaşır (kapanıyor) ya da sabit kalır; hedef sabitlemesi anında engel ve kaçış boşluğu belirir. |

**Sahneyi adımlarla hizala.** Ekranda "nokta uzaklaşıyorsa açılıyor" yazarken
animasyonun "KAPANIYOR" demesi izleyeni şaşırtır. `sahne_fazlari` bunu önler:

```yaml
sahne: viraj
sahne_fazlari: "0:sabit, 11:uzak, 19:acilir, 27:kapanir, 35:engel, 42:uzak"
```

Her giriş `saniye:durum` biçiminde. Durumlar: `sabit`, `uzak`, `acilir`,
`kapanir`, `engel`. Adımlarının saatlerini değiştirirsen bunu da güncelle.

Sahneyi tek başına üretmek (denemek için):

```bash
python3 scripts/sahne_uret.py --sahne fren --sure 60 --cikti /tmp/dene.mp4
```

**Motor sesi de sentezlenir:** silindir ateşlemelerinden kurulmuş bir motor
sesi, sahnenin gaz/fren durumuna göre devir değiştirir; üstüne rüzgâr uğultusu
biner. Gerçek çekim koyduğunda onun kendi sesi kullanılır.

---

## 🎵 Müzik

Fon müziği depoda hazır: `assets/muzik/aae_yol_okulu.mp3` — 82 BPM, A minor,
koyu phonk/trap yatağı. **Parça tamamen `scripts/muzik_uret.py` ile sentezlendi**,
hiçbir yerden örnek alınmadı; YouTube ve Instagram'da telif iddiası yemezsin.

Yeni varyasyon üretmek için:

```bash
pip install numpy
python3 scripts/muzik_uret.py --bpm 76 --sure 90 --tohum 9         --cikti assets/muzik/aae_yavas.mp3
```

`--tohum` değeri varyasyonu, `--bpm` tempoyu değiştirir. Ürettiğin dosyayı ders
dosyasındaki `muzik:` alanına yaz.

**Ses dengesi:** motorun gerçek sesi `kaynak_ses` (varsayılan 0.30) ile altta
tutulur, müzik `muzik_ses` (0.35) ile üstte durur, toplam miks otomatik olarak
-14 LUFS'a oturtulur. Motor sesini tamamen susturmak için `kaynak_ses: 0`.

---

## ▶️ YouTube kurulumu (tek seferlik)

1. [Google Cloud Console](https://console.cloud.google.com/) → yeni proje →
   **APIs & Services → Library → YouTube Data API v3 → Enable**
2. **OAuth consent screen** → External → Test users'a kanalın Gmail'ini ekle
3. **Credentials → Create Credentials → OAuth client ID → Desktop app** →
   inen JSON'u `client_secret.json` adıyla depo köküne koy (kendi bilgisayarında)
4. Token'ı al:
   ```bash
   pip install -r requirements-publish.txt
   python3 scripts/get_youtube_token.py
   ```
5. Ekrana basılan üç değeri **Settings → Secrets and variables → Actions** altına ekle:
   `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`

> `client_secret.json` ve token'lar `.gitignore`'da — asla commit etme.
> YouTube Data API'nin günlük yükleme kotası vardır; yeni projelerde düşüktür.

---

## 📸 Instagram kurulumu (tek seferlik)

**Ön koşul:** Instagram hesabı **Business ya da Creator** olmalı ve bir **Facebook
Sayfasına bağlı** olmalı. Kişisel hesaptan API ile paylaşım yapılamaz.

1. [Meta for Developers](https://developers.facebook.com/) → uygulama oluştur →
   **Instagram** ürününü ekle
2. **Graph API Explorer**'dan şu izinlerle kısa ömürlü bir jeton üret:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`
3. Uzun ömürlü jetonu ve hesap id'sini bul:
   ```bash
   FB_APP_ID=... FB_APP_SECRET=... FB_SHORT_TOKEN=... \
   python3 scripts/get_instagram_ids.py
   ```
4. Çıkan iki değeri Secrets'a ekle: `IG_USER_ID`, `IG_ACCESS_TOKEN`

### İki yükleme yolu

| Yol | Nasıl çalışır | Ne zaman |
|---|---|---|
| `resumable` (varsayılan) | Dosya doğrudan `rupload.facebook.com`'a gider; videoyu internette yayınlamaya gerek yok | Normalde bunu kullan |
| `release-url` | Video önce GitHub Release'e yüklenir, Meta o **public** adresten indirir | Resumable uygulamanda çalışmıyorsa |

> `release-url` yolunu seçersen video, Instagram'a gitmeden önce depo Release'inde
> **herkese açık** indirilebilir olur. Zaten yayınlayacağın video için sorun değil,
> ama bilerek seç.

### Instagram sınırları
Reels: MP4/MOV, H.264/HEVC + AAC, 23–60 fps, **≤ 300 MB**, 9:16 önerilir, `moov` başta
(render bunu `+faststart` ile zaten yapıyor). Caption ≤ 2200 karakter, ≤ 30 etiket.

---

## 📁 Klasör yapısı

```
content/dersler/        → ders dosyaları (_sablon.yml kopyala)
videos/                 → ham çekimler (Git LFS)
output/                 → render edilmiş videolar
assets/muzik/           → fon müziği (aae_yol_okulu.mp3 hazır gelir)
scripts/
  lesson.py                 → ders dosyasını okur/doğrular, drawtext metinlerini üretir
  make_training_video.sh    → ffmpeg render
  publish_youtube.py        → YouTube (Shorts) yükleme
  publish_instagram.py      → Instagram (Reels) yükleme
  get_youtube_token.py      → YT refresh token (tek seferlik, yerelde)
  get_instagram_ids.py      → IG user id + uzun ömürlü jeton (tek seferlik, yerelde)
  muzik_uret.py             → telifsiz fon müziği besteler (numpy gerekir)
  sahne_uret.py             → arka plan sahnesi + motor sesi çizer (numpy, pillow)
.github/workflows/egitim-videosu.yml
KURALLAR.md             → format, marka, yayın ve sır kuralları
```
