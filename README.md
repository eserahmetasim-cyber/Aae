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
| `sahne` | Çekim yoksa arka planı çizimle üret: `fren` · `viraj` · `kontra` · `gaz` |
| `boyut` | `3` = 3 boyutlu sahne (varsayılan), `2` = düz çizim |
| `kamera` | `yan` · `kask` · `takip` · `onden` · `tepeden` · `degisken` (dönüşümlü) |
| `gunduz` | `true` = gündüz ışığı, uzak daha net; `false` = gece |
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

Elinde uygun çekim yoksa arka planı hat kendisi çizer — **varsayılan olarak
3 boyutlu**: perspektif kamera, ışıklı yüzeyler, derinlik sisi. Motor
`scripts/uc_boyut.py` içinde, dışarıdan 3B kütüphanesi gerekmez. Düz çizim
istersen ders dosyasına `boyut: 2` yaz.

Ders dosyasına `sahne: fren` ya da `sahne: viraj` yazman yeterli — `kaynak` boşsa sahne
render sırasında üretilir. Her şey çizimle oluşur, telif sorunu yoktur.

| Sahne | Ne gösterir |
|---|---|
| `fren` | Motosikletin 3/4 görünümü. Frene basınca çatal çöker, motosiklet öne yüklenir, ön lastiğin temas alanı büyür; soldaki çubuklar ön/arka yük dağılımını %50/%50'den %82/%17'ye canlı taşır, sağda hız düşer. |
| `viraj` | Viraja giren motosikletin arkadan görünümü. Yolun iki kenarının birleştiği **kayboluş noktası** uzaklaşır (viraj açılıyor), yaklaşır (kapanıyor) ya da sabit kalır; hedef sabitlemesi anında engel ve kaçış boşluğu belirir. |
| `kontra` | Önden görünüm. Gidona verilen itiş, ön tekerin ters yöne dönmesi ve motosikletin yatması aynı karede: paneller "SOL GİDON İTİLİYOR · ÖN TEKER SAĞA · MOTOSİKLET SOLA 22°" olarak okunur. Yalnızca 3 boyutlu üretilir. |
| `gaz` | Havadan takip. Motosiklet sabit yarıçaplı bir virajı dönerken gaz çubuğu, hız ve faz etiketi görünür; gaz kesilince motosiklet doğrulup şerit çizgisinin dışına taşar ("ŞERİDİN DIŞINDA"). Fazlar `sahne_fazlari` ile adımlara bağlanır: `fren` · `yatis` · `sabit` · `kesik` · `duzelt` · `cikis`. Yalnızca 3 boyutlu. |

**Kamera açıları.** `kamera: kask` sürücünün kaskından bakar — gidon, aynalar,
gösterge paneli kadrajda, frende burun aşağı yattığında görüntü de yatar.
`degisken` her fren denemesinde yan görünüm ile kask kamerası arasında geçiş
yapar. `takip` motosikleti arkadan izler (viraj sahnesinin varsayılanı).

**Gündüz / gece.** `gunduz: true` mavi gökyüzü, yeşil çim, açık asfalt,
ufukta dağlar ve yol kenarında ağaçlar verir; sis çok daha geride başladığı
için uzak seçilir kalır. Varsayılan gece.

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

Parçaların **hepsi `scripts/muzik_uret.py` ile sentezlendi** — hiçbir yerden
örnek alınmadı, YouTube ve Instagram'da telif iddiası yemezsin.

| Dosya | Karakter |
|---|---|
| `aae_piyano.mp3` | **Varsayılan.** 64 BPM; sakin piyano ezgisi (kısmi sesleri hafif akortsuz, başta çekiç gürültüsü) + çok kısık yaylı + oda yankısı. Ritim yok. |
| `aae_sade.mp3` | 70 BPM; Karplus-Strong telli çalgı + bas hattı + fırça vuruşu. Boş başlar, açılır, sonda incelir. |
| `aae_yol_okulu.mp3` | 82 BPM; koyu phonk/trap yatağı (808 bas + cowbell). |
| `aae_lofi.mp3` ✻ | 76 BPM; Rhodes benzeri akorlar + yumuşak beat + plak çatırtısı. |
| `aae_atmosfer.mp3` ✻ | 60 BPM; sadece derin pad + bas, ritimsiz. En arkada durur. |

✻ Depoda hazır gelmez, aşağıdaki komutla üretilir.

```bash
pip install numpy
python3 scripts/muzik_uret.py --stil lofi --sure 70
python3 scripts/muzik_uret.py --stil piyano --bpm 60 --tohum 9 \
        --cikti assets/muzik/aae_yavas.mp3
```

`--stil` (piyano / sade / lofi / atmosfer / phonk) karakteri, `--tohum`
varyasyonu, `--bpm` tempoyu değiştirir. Ürettiğin dosyayı ders dosyasındaki
`muzik:` alanına yaz. Her parça -16 LUFS'a oturtulur, böylece stiller arasında
seviye farkı olmaz.

**Ses dengesi:** motorun gerçek sesi `kaynak_ses` ile çok geride tutulur
(derslerin varsayılanı **0.035** — zar zor duyulan bir uğultu), müzik
`muzik_ses` (0.36) ile üstte durur, toplam miks otomatik olarak -14 LUFS'a
oturtulur. Motoru tamamen susturmak için `kaynak_ses: 0`.

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
assets/muzik/           → fon müziği (aae_piyano.mp3 varsayılan)
scripts/
  lesson.py                 → ders dosyasını okur/doğrular, drawtext metinlerini üretir
  make_training_video.sh    → ffmpeg render
  publish_youtube.py        → YouTube (Shorts) yükleme
  publish_instagram.py      → Instagram (Reels) yükleme
  get_youtube_token.py      → YT refresh token (tek seferlik, yerelde)
  get_instagram_ids.py      → IG user id + uzun ömürlü jeton (tek seferlik, yerelde)
  muzik_uret.py             → telifsiz fon müziği besteler (numpy gerekir)
  sahne_uret.py             → düz (2B) sahne + motor sesi (numpy, pillow)
  sahne3b.py                → 3 boyutlu sahne (fren / viraj)
  uc_boyut.py               → yazılımsal 3B motor: kamera, ışık, derinlik
.github/workflows/egitim-videosu.yml
KURALLAR.md             → format, marka, yayın ve sır kuralları
```
