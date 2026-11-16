# Secret'ları nereden alacaksın — adım adım

> Yazılma tarihi: **16.11.2026**. Günlük yayın iş akışı artık varsayılan dalda
> ve her sabah **09:00 İstanbul**'da çalışıyor. Tek eksik: aşağıdaki beş değer.
> Girilmezse iş akışı çalışır, videoyu üretir, ama **hiçbir yere yüklemez**.

Hepsi **tek seferlik**. İkisi ayrı iş: YouTube (3 değer), Instagram (2 değer).
Birini bitirip diğerine geçebilirsin; YouTube girilirse YouTube yayınlanır,
Instagram beklemeye devam eder.

**Değerleri yazacağın yer (her ikisi için aynı):**
GitHub → `eserahmetasim-cyber/Aae` deposu → üstte **Settings** → sol menüde
**Secrets and variables** → **Actions** → yeşil **New repository secret** →
*Name* kutusuna adı, *Secret* kutusuna değeri → **Add secret**.

⚠ Bu değerler şifre gibidir. Bana, sohbete, hiçbir dosyaya yazma — sadece o
kutulara. Ben de göremem, görmem gerekmiyor.

---

## A) YouTube — 3 değer

`YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`

### 1. Google Cloud'da proje aç ve API'yi aç
1. https://console.cloud.google.com/ → üstteki proje seçicisinden **New Project**
   → ad ver (örn. "SAE Yayin") → **Create**.
2. Sol menü **APIs & Services → Library** → arama kutusuna `YouTube Data API v3`
   → sonuca gir → **Enable**.

### 2. İzin ekranını ayarla
1. **APIs & Services → OAuth consent screen**.
2. **External** seç → **Create**.
3. Zorunlu alanları doldur (uygulama adı, destek e-postası, iletişim e-postası).
   İsim önemli değil, sadece sana görünecek.
4. **⚠ EN ÖNEMLİ ADIM — "Publishing status":** ekranı kaydettikten sonra
   OAuth consent screen sayfasında **"Publishing status: Testing"** yazıyorsa
   **"PUBLISH APP"** düğmesine bas ve onayla, durum **"In production"** olsun.
   - **Neden:** uygulama "Testing" kalırsa Google'ın verdiği refresh token
     **7 gün sonra geçersiz oluyor** ve yayın bir hafta sonra sessizce durur.
     "In production" olunca bu süre sınırı kalkar.
   - Google doğrulama (verification) istemeyecek, çünkü uygulamayı sadece sen
     kullanıyorsun. Yetki verirken "Google bu uygulamayı doğrulamadı" uyarısı
     çıkarsa normal: **Advanced → Go to … (unsafe)** ile devam et. Uygulama
     senin, risk yok.

### 3. OAuth istemcisi oluştur
1. **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
2. *Application type*: **Desktop app** → **Create**.
3. Çıkan pencerede **DOWNLOAD JSON**. İnen dosyanın adını
   **`client_secret.json`** yap ve depo klasörünün köküne koy
   (kendi bilgisayarında, `C:\...\Aae\client_secret.json`).
   - Bu dosya `.gitignore`'da, yani commit edilmez. Öyle kalsın.

### 4. Token'ı al (kendi bilgisayarında, tarayıcı açılacak)
Depo klasöründe komut satırını aç ve sırayla:
```
pip install -r requirements-publish.txt
python scripts/get_youtube_token.py
```
- Tarayıcı açılır → **kanalın sahibi olan Google hesabıyla** giriş yap → izin ver.
- Betik ekrana üç değer basar. Diske yazmaz, sadece gösterir.

### 5. Üç değeri Secrets'a gir
Ekranda ne yazıyorsa aynı adla: `YT_CLIENT_ID`, `YT_CLIENT_SECRET`,
`YT_REFRESH_TOKEN`.

---

## B) Instagram — 2 değer

`IG_USER_ID`, `IG_ACCESS_TOKEN`

### 0. Ön koşul (bu olmadan hiçbiri çalışmaz)
- Instagram hesabı **Business** ya da **Creator** olmalı
  (Instagram uygulaması → Ayarlar → Hesap türü).
- Ve bir **Facebook Sayfasına bağlı** olmalı.
- **Kişisel hesaptan API ile paylaşım yapılamaz**, Meta izin vermiyor.

### 1. Meta uygulaması oluştur
1. https://developers.facebook.com/ → **My Apps → Create App**.
2. Kullanım amacı sorulursa "Other" / işletme tipini seç, ad ver.
3. Uygulama panelinde **Instagram** ürününü ekle.
4. **Settings → Basic** sayfasından şunları bir yere al:
   - **App ID** → bu `FB_APP_ID`
   - **App Secret** (*Show* düğmesi, Facebook şifresini isteyebilir) → `FB_APP_SECRET`

### 2. Kısa ömürlü jeton üret
1. https://developers.facebook.com/tools/explorer
2. Sağ üstten **kendi uygulamanı** seç.
3. **Permissions** kısmına şu dört izni ekle:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`
4. **Generate Access Token** → Facebook hesabınla onayla, Sayfayı ve Instagram
   hesabını seçtiğinden emin ol.
5. Çıkan uzun metin → bu `FB_SHORT_TOKEN`. (Kısa ömürlü, bir-iki saat geçerli;
   hemen sonraki adımı yap.)

### 3. Kalıcı değerleri çıkar (kendi bilgisayarında)
Depo klasöründe, üç değeri kendi değerlerinle değiştirerek:

**Windows PowerShell:**
```
$env:FB_APP_ID="..."; $env:FB_APP_SECRET="..."; $env:FB_SHORT_TOKEN="..."
python scripts/get_instagram_ids.py
```

**Mac/Linux:**
```
FB_APP_ID=... FB_APP_SECRET=... FB_SHORT_TOKEN=... python3 scripts/get_instagram_ids.py
```

Betik kısa jetonu uzun ömürlüye çevirir, Sayfalarını listeler ve bağlı Instagram
hesabı için `IG_USER_ID` + `IG_ACCESS_TOKEN` basar.

### 4. İki değeri Secrets'a gir
`IG_USER_ID` ve `IG_ACCESS_TOKEN`.

> Bu `IG_ACCESS_TOKEN` bir **Sayfa jetonu** ve uzun ömürlü kullanıcı jetonundan
> türetiliyor; kendiliğinden süresi dolmaz. Yalnızca Meta uygulamasının iznini
> kaldırırsan, şifreni değiştirirsen ya da hesap türünü kişiseliye çevirirsen
> geçersiz olur.

---

## Girdikten sonra

1. Beklemek istemezsen elle tetikle: GitHub → **Actions** → sol menüde
   **Gunluk Yayin** → **Run workflow**. İlk denemede `kuru` seçeneğini **evet**
   yaparsan hiçbir şey yayınlanmaz, sadece boru hattı test edilir — önce bunu
   yapmanı öneririm.
2. Sonra gerçeğini çalıştır. Çalışma özetinde YouTube bağlantısı ve Instagram
   id'si görünür.
3. Gerçekten yayınlandıysa iş akışı `content/yayin_kaydi.json` dosyasını
   oluşturup depoya yazar. O dosya doluyorsa hat çalışıyor demektir.

⚠ **Instagram Reel yayınlandığı anda herkese açık olur ve API'den geri
alınamaz.** Sırada 18 ders var, günde bir tanesi çıkacak. YouTube tarafı
`public` ayarlı; istersen elle tetiklerken `gizlilik` seçeneğini `unlisted`
yapıp önce kendin bakabilirsin.

## Hiçbiri olmazsa

Secret girmezsen bir şey bozulmuyor: iş akışı her sabah çalışır, videoyu üretir,
**Actions → ilgili çalışma → Artifacts** altında 30 gün durur. Oradan indirip
elle paylaşabilirsin. Yayın kaydı yazılmaz, yani ders sırada kalır ve secret
girildiği gün ilk çalışmada yayınlanır.
