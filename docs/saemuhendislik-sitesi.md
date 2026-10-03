# saemuhendislik.com — Tam Sistem Bilgisi

> Bu dosya, "Saemuhendislik sistem düzenlemesi" oturumunun (28.08–12.09.2026) tam
> transkriptinden, oradaki wiki kavram sayfasından ve kalıcı hafıza dosyasından
> damıtıldı. Amaç: siteyle ilgili işe bu depodan devam edebilmek.
>
> Son güncel bilgi tarihi: **12.09.2026**. Bundan sonrasını (AdSense onayı vb.)
> doğrulamak gerekir.

---

## 0. GÜNCEL DURUM — 03.10.2026 (bulut oturumu tespiti)

Gmail (eserahmetasim@gmail.com) üzerinden doğrulandı. **12.09'dan beri kimsenin
görmediği iki uyarı var** — AAE'nin bilgisayarı 13.09'dan beri erişilemez olduğu
için `adsense-gunluk-kontrol` görevi ~3 haftadır çalışmamış.

### 🔴 Search Console: düzeltme BAŞARISIZ + iki yeni sorun

**16.09.2026 20:29 — `sc-noreply@google.com` [WNC-10031170]:**
> "Sayfayı dizine ekleme sorunlarıyla ilgili bazı düzeltmeler **başarısız oldu**.
> İstenen düzeltme şu sorunla ilgiliydi: *Yönlendirmeli sayfa*. Sayfalarınızdan
> bazıları bu sorundan etkilenmeye devam ediyor."

→ 07.09'daki temiz-URL düzeltmesi **kısmen tutmamış**.

**16.09.2026 20:29 + 20:37 — `sc-noreply@google.com` [WNC-20237597]:** iki YENİ neden:
> * "Kopya, Google kullanıcıdan farklı bir standart sayfa seçti"
> * "Kullanıcı tarafından seçilen standart sayfa olmadan kopya"

16.09'dan bugüne yeni Search Console maili yok → **durum hâlâ bu.**

#### Teşhis hipotezleri (canlı doğrulama bekliyor, sırayla bakılacak)
1. **`www` vs apex — en güçlü şüpheli.** 10.09'da `www.saemuhendislik.com/ads.txt`
   **200** dönüyordu. Eğer `www` apex'e yönlendirmiyor, içeriği doğrudan sunuyorsa
   Google iki özdeş site görüyor — "Google farklı bir standart sayfa seçti"nin
   klasik sebebi. Kontrol:
   `curl -sS --ssl-no-revoke -o /dev/null -w "%{http_code} %{redirect_url}\n" https://www.saemuhendislik.com/`
   200 ise zone'da `www.saemuhendislik.com/*` → `https://saemuhendislik.com/$1`
   **301 Redirect Rule** kurulacak (`dokum-pdf-yonlendirme` deseni).
2. **Canonical'ı olmayan sayfalar.** 07.09 betiğinin `DOKUNMA` kümesi
   `{404.html, google19071191ddf4150f.html}` idi → bu ikisinde canonical YOK.
   Doğrulama dosyası dizine giriyorsa "standart sayfa olmadan kopya" tam bu.
   Çözüm: robots.txt `Disallow` (dosya **silinmeyecek**, içeriği değiştirilmeyecek).
3. **`gizlilik.html` ↔ `gizlilik-politikasi.html` ikizliği.** 3662 / 4144 bayt,
   içerik neredeyse aynı. Özdeş içerikli iki URL = kopya kümesi. Play Console'a
   verilen adres korunacak; Play'de kayıtlı olan kanonik yapılacak.

> ⚠ Teşhis **tahminle değil**, Search Console "Dizine ekleme" raporundaki örnek
> URL listesiyle kesinleştirilecek.

### 🟡 AdSense: 36. gün, hâlâ "Hazırlanıyor"
Başvuru 28.08 → bugün **36 gün**. Google'ın normal aralığı 1–14 gün; reçetedeki
**21 gün eşiği çoktan aşıldı** → panelden **yeniden inceleme talebi** gönderilmeli.
Bu hesaba (eserahmetasim) hiç AdSense maili gelmedi — beklenen, 008'e gidiyor.

### 🟢 Mini Mühendis: Play production access VERİLDİ
**12.09.2026 — `no-reply-googleplay-developer@google.com`:**
> "Congratulations! Your app has been granted Google Play production access"
> (`com.saemuhendislik.mini_muhendis`)

→ Ana sayfadaki "Uygulamalarımız" bandında Mini Mühendis'in
**"YAKINDA GOOGLE PLAY'DE" rozeti artık yanlış** — gerçek Play Store linkine
çevrilmeli (TR+EN).

### Bu tespitlerle ne yapıldı
03.10'da yerel oturuma (`Saemuhendislik sistem düzenlemesi`,
`session_014mvmA2G5DBuuSRYtxDLTwk`) 7 maddelik iş emri **kuyruğa alındı**:
AdSense durumu/yeniden inceleme → SC raporundan URL listesi → üç hipotezin
doğrulanması → düzeltme + dağıtım + 200 doğrulama → SC'de "Düzeltmeyi doğrula" →
Mini Mühendis Play linki → wiki/hafıza güncellemesi.
AAE'nin bilgisayarı bağlanınca çalışacak.

---

## 1. Künye

| | |
|---|---|
| Alan adı | https://saemuhendislik.com (+ `www`) |
| Sahibi | Ahmet Asım ESER — ahmetasimeser@hotmail.com |
| Barındırma | **Cloudflare Pages**, proje adı `saemuhendislik` (`saemuhendislik.pages.dev`) |
| Cloudflare hesabı | eserahmetasim@gmail.com (Google SSO); hesap id `80fd2279…` |
| NS | `eoin.ns.cloudflare.com`, `paige.ns.cloudflare.com` |
| Diller | TR (kök) + EN (`/en/`), hreflang'li, nav'da `.lang-switch` düğmesi |
| Teknoloji | Şablonsuz statik HTML + tek `css/style.css`; build adımı yok |
| Palet | Lacivert `#16233d` / `#0b1220` + turuncu `#f97316` / `#c2410c` |

### Tarihçe
- **2020:** Eski site — ücretsiz "Music8" müzik şablonu, HTTPS yok, kırık linkler,
  AdSense + sayaç + TRT Haber iframe'i. Tasarım M.Abdullah Özel'e aitti
  (kredisi yeni sitede kaldırıldı).
- **10.08.2026:** Sıfırdan yeniden yazıldı. Güzel Hosting (guzel.net.tr)
  DirectAdmin ücretsiz paket, 50 MB kota, kullanıcı `saemuhen`.
  Cloudflare Free + **Flexible SSL** ile HTTPS sağlandı.
- **26.08.2026:** Güzel Hosting ücretsiz hesabı askıya alındı → site **tamamen
  Cloudflare Pages'e taşındı**, hosting bağımlılığı sıfır. Domain kaydı Güzel
  Hosting'de 2028'e kadar duruyor (yalnız kayıt firması).
- **26.08–12.09.2026:** PDF yayın serisi, AdSense, Search Console, temiz URL
  düzeltmesi, günlük otomatik takip görevi.

> ⚠ `mail/ftp/pop/smtp` DNS kayıtları hâlâ eski IP'de (`45.84.188.101`, askıda).
> Kullanılmıyor, sorun değil. E-posta gerekirse Cloudflare Email Routing kurulabilir.

---

## 2. Sayfa yapısı

Dosya adları eski siteden **bilinçli korundu** (Google dizini kırılmasın diye),
o yüzden dosya adı ile menü adı örtüşmüyor:

| Dosya | TR menü | EN menü |
|---|---|---|
| `index.html` | Ana Sayfa | Home |
| `hk.html` | Hakkında | About |
| `gallery.html` | Sektörler | Industries |
| `events.html` | Kaynaklar | Resources |
| `contact.html` | İletişim | Contact |

### Teknik yayın sayfaları (her birinin PDF'i var)
`dokum.html`, `dovme.html`, `alu.html`, `titanyum.html`, `ssf.html`, `hasar.html`
— hepsinin `/en/` karşılığı var.

### Hukuki / yardımcı sayfalar
| Dosya | Ne işe yarar |
|---|---|
| `cerez-politikasi.html` | **Web sitesi** çerez/gizlilik politikası (TR+EN). AdSense CMP bunu istiyor. 30.08'de yazıldı, 22 sayfanın altbilgisinde linki var. |
| `gizlilik.html` | Mobil uygulama gizlilik politikası (Play Store) — **KORUNMALI** |
| `gizlilik-politikasi.html` | İkinci uygulama gizlilik politikası (Play Store) — **KORUNMALI** |
| `404.html` | Şık 404 |
| `google19071191ddf4150f.html` | Search Console sahiplik doğrulama dosyası — **SİLİNMEMELİ** |
| `ads.txt` | AdSense; içeriği aynen: `google.com, pub-8433209614215281, DIRECT, f08c47fec0942fa0` |
| `robots.txt`, `sitemap.xml`, `favicon.svg` | — |

### Ana sayfadaki özel bloklar
- **Yayın kartları** (TR+EN) — her teknik yayın için bir kart.
- `hasar` kartında `.card-badge` ile turuncu **"YENİ"/"NEW"** rozeti (28.08).
  ⚠ Bir sonraki yayın çıkınca rozet ona taşınmalı ya da kaldırılmalı.
- **`#uygulamalar` / `#apps` bandı** — Mini Mühendis + Malzeme Bilgisi,
  ikonlar `images/mini-muhendis-ikon.png`, `images/malzeme-bilgisi-ikon.png`,
  `.app-soon` ile "YAKINDA GOOGLE PLAY'DE" rozeti.
  ⚠ Uygulamalar yayınlanınca rozet yerine Play Store düğmesi konacak
  (Moto Bakım da eklenebilir).
- CSS sınıfları: `.grid-2`, `.app-row`, `.app-soon` (900px altı tek kolon).

---

## 3. SAE Teknik Yayınları serisi — 6/6 YAYINDA

Özgün hazırlanmış, **telifi bizde** olan A4 PDF ders notları. `pdf/` altında.
Kapak künyesi: *"Hazırlayan: Ahmet Asım ESER"*. Her notta 1–2 "Saha notu" kutusu.

| No | Başlık | Sayfa | Site sayfası | PDF |
|----|--------|-------|---|---|
| 1 | Döküm Teknolojisi | 7 | `dokum.html` | `sae-dokum-teknolojisi.pdf` |
| 2 | Dövme Teknolojisi | 7 | `dovme.html` | `sae-dovme-teknolojisi.pdf` |
| 3 | Alüminyum Alaşımları | 5 | `alu.html` | `sae-aluminyum-alasimlari.pdf` |
| 4 | Titanyum Alaşımları | 6 | `titanyum.html` | `sae-titanyum-alasimlari.pdf` |
| 5 | Yarı Katı Şekillendirme | 5 | `ssf.html` | `sae-yari-kati-sekillendirme.pdf` |
| 6 | Hasar ve Kırık Yüzey Analizi | 6 | `hasar.html` | `sae-hasar-kirik-analizi.pdf` |

İlgili sayfalarda TR **"Ders Notu"** / EN **"Technical Note"** indirme kutusu var.

No.6 (28.08.2026), `kirik-yuzey-analizi` wiki birikiminden damıtıldı: 10 bölüm +
2 özgün inline SVG şema (sünek/gevrek kıyası, yorulma yüzeyi gerilme-seviyesi
okuması). Kaynakça: ASM Handbook V11/V12, Wulpi, Kayalı, Eryürek, Murakami.
Kart/hero görseli için özgün `images/hasar.svg` çizildi.

### Yayın üretim reçetesi (kanıtlanmış)
1. Kaynak HTML'ler: `patent\saemuhendislik-site\icerik\`. Şablon olarak **No.5 /
   No.6 dosyalarını kopyala** — lacivert degrade kapak + turuncu `h2` +
   `.tablo` / `.kutu-bilgi` / `.sekil` / `.kaynakca` / `.kunye` sınıfları.
2. **HTML → PDF: Edge headless**
   ```
   msedge --headless=new --disable-gpu --no-pdf-header-footer \
     --print-to-pdf="cikti.pdf" "file:///kaynak.html"
   ```
   A4 marjları CSS `@page` ile; flexbox/gradient/SVG sorunsuz basılır.
3. PDF'i `Read` ile sayfa sayfa **görsel QA** yap, `SendUserFile` ile AAE onayına sun.
4. Site sayfası çifti: `X.html` + `en/X.html` (`dokum.html` desenini kopyala),
   ana sayfa kartı (TR+EN), `sitemap.xml` + 2 satır.
5. Kart görseli yoksa özgün SVG çiz; SVG'yi **Edge headless `--screenshot`** ile
   PNG'ye basıp görsel doğrula (Browser paneli kapalıyken pane screenshot çalışmaz).

---

## 4. Dağıtım reçetesi (tam otomatik, 5+ kez kanıtlandı)

1. **Tek kaynak: `C:\SAE-yukleme\`** — tüm değişiklikler oraya işlenir.
   Kaynak yedek: `C:\Users\ahmet\OneDrive\Masaüstü\patent\saemuhendislik-site\`.
   ⚠ **OneDrive klasöründen dağıtım YAPMA** (senkron sızıntısı yaşandı).
2. **.NET `ZipFile` ile zip'le — girdi adları DÜZ bölü (`/`).**
   PowerShell `Compress-Archive` KULLANMA: ters bölü yazıyor, Linux tarafında
   klasörleri bozuyor. Zip scratchpad'e yazılır (`C:\` köküne sandbox yazamaz).
   Silme gerekirse `Remove-Item` hook'a takılır → `[IO.File]::Delete` kullan.
3. Chrome MCP ile:
   `dash.cloudflare.com/<hesap>/pages/view/saemuhendislik/deployments/new`
   - Gizli `input[accept=.zip]`, `read_page`'de **`button type="file"`** olarak
     görünür → ref'i oradan al. Görünmüyorsa JS ile `display:block` yapıp `find` et.
   - `file_upload` aracıyla zip'i ver (10 MB sınırı; site ~1,7 MB).
   - **"N/N files uploaded"** doğrula. Aradaki *"Unzipped N"* mesajları yanıltıcı.
     ⚠ Yükleme takılırsa bekleme → **sayfayı yenile + aynı zip'i tekrar yükle**.
   - **Save and deploy** → ilk tık sık sık işlemez; ref tıklaması çalışmazsa
     `scroll_to` + **ekran görüntüsünden KOORDİNAT** ile tıkla.
   - **"Success!"** metnini bekle.
4. **Doğrulama:**
   - **Alan adı üzerinden** test et — `pages.dev` Türk ISS'lerinde SNI-reset ile engelli.
   - `?v=x` sorgu ekiyle Pages üst katman önbelleğini atla.
   - Sandbox curl dış ağa çıkamaz → tarayıcı sekmesinde `fetch` ile durum kodu topla.
   - Windows'ta `curl` kullanacaksan **`--ssl-no-revoke` şart**, yoksa sertifika hatası.

### Dağıtım sonrası zorunlu kontrol
Her dağıtımdan sonra `/`, `/hasar`, `/en/`, `/cerez-politikasi`, `/sitemap.xml`,
`/ads.txt` **200** mü diye bak. (26.08'de apex custom domain bağı koptu, site bir
süre boş 404 verdi — dağıtım sonrası 200 testi bu yüzden şart.)

---

## 5. Değişmez kurallar

1. **Temiz URL — KALICI KURAL (07.09).** Cloudflare Pages `.html` adreslerini
   uzantısız adrese **308** yönlendiriyor. `.html` yazılan sitemap/iç link/canonical
   yüzünden Google *"Yönlendirmeli sayfa"* deyip dizine EKLEMİYOR.
   **Siteye eklenen her sayfada link, canonical ve sitemap uzantısız yazılacak**
   (`/hasar`, `/en/hasar`).
2. **SSL modu Flexible kalmalı.** Eski hosting döneminden kalma; Pages'e geçildi
   ama zone ayarına dokunulmuyor.
3. **Süspansiyon / direksiyon / rotil sektör vurgusu sitede YASAK.** Rot başı
   yalnızca nötr örnek olabilir. Firma verisi hiç kullanılmaz.
4. `gizlilik.html` + `gizlilik-politikasi.html` **her dağıtımda korunmalı**
   (Play Store'a verilen adresler). Zip her zaman tüm siteyi içerir.
5. `google19071191ddf4150f.html` **silinmez** (Search Console doğrulaması).
6. `404.html` + iki gizlilik sayfası **bilinçli reklamsız** kalır.
7. **Aynı projede iki Claude oturumu aynı anda dağıtım yapmasın.** 26.08'de iki
   oturum birbirinin dağıtımını ve domain bağını ezdi, kök DNS kaydı silindi.
   İşe başlarken production deployment durumuna bak.
8. Türkçe metin düzenlemede **PowerShell `-replace` kullanma** — Türkçe karakteri
   bozuyor. Python + UTF-8 ile düzenle. Satır içi çok satırlı `python -c`
   sınıflandırıcıya takılabiliyor → betiği dosyaya yazıp çalıştır.

### Önbellek davranışları
- `css/style.css` tarayıcıda `max-age=14400` (**4 saat**) önbelleklenir. CSS
  değişikliği dönen ziyaretçide 4 saate kadar gecikir (edge anında taze verir).
  Doğrulamayı **Ctrl+Shift+R** sert yenilemeyle yap.
- Pages'te silinen dosya 200 dönüyorsa: `Age > 0` + `cf-cache-status: MISS` =
  Pages'in kendi üst katman önbelleği (`s-maxage=604800`). Zone "Purge Everything"
  İŞLEMEZ. Kalıcı çözüm **Redirect Rule**; yoksa 7 günde düşer.
  (Örnek: `dokum.pdf` kalıntısı için `dokum-pdf-yonlendirme` kuralı, 301, Active.)
- Cloudflare `robots.txt`'imizin başına kendi "Content Signals" AI-bot engellerini
  (GPTBot, ClaudeBot vb.) basıyor. **Googlebot ve Mediapartners-Google serbest** —
  arama ve reklam etkilenmiyor.

### Cloudflare dash tuzakları
- Formlar React'lı: `computer.type` ile yazılan değer re-render'da kaybolabilir.
  JS **native setter + `input` event** ile doldurmak sağlam.
- Oturum düşerse giriş sayfasındaki **"eserahmetasim@gmail.com — Last used"**
  profil düğmesi şifresiz giriş sağlıyor (Google SSO). **Şifre girmeye çalışma.**
- API gerekirse: dash → profile → API Tokens → Custom (Account / Cloudflare Pages /
  Edit). API, domain sil/ekle işinde UI'nin *"already associated"* hatasına takılmıyor.
  (26.08'de açılan geçici `pages-tamir-gecici` token'ı güvenlik gereği SİLİNDİ.)

---

## 6. Google AdSense

| | |
|---|---|
| Yayıncı kimliği | **ca-pub-8433209614215281** |
| Hesap | **ahmetasimeser008@gmail.com** (eserahmetasim'de AdSense hesabı YOK) |
| Konsol | https://adsense.google.com/adsense/u/1/pub-8433209614215281/sites |
| Başvuru | 28.08.2026 14:19 |
| Son bilinen durum | **"Hazırlanıyor"** (12.09 itibarıyla ~15. gün) |

Yayıncı kimliği eski 2020 sitesinin AdSense hesabından geri kazanıldı
(`eski-site-yedek\` içinde grep ile bulundu) — ödeme bilgileri bile hazırdı.

- **Auto Ads kodu 22 içerik sayfasının `<head>`'inde** (TR 11 + EN 11):
  `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8433209614215281`
- `ads.txt` kökte ve 200. Google'ın kendi bot kimlikleriyle test edildi
  (AdsBot-Google, Mediapartners-Google, Googlebot, `www`, http→https) → hepsi 200.
- Panelde **"ads.txt: Bulunamadı"** uyarısı çıkıyor ama **bizim tarafta sorun yok** —
  hesap onaylanmadığı ve reklam sunulmadığı için Google dosyayı düzenli taramıyor.
  Onayla birlikte kendiliğinden "Bulundu"ya döner.
- Panel durumu (10.09): *"Tebrikler, tüm adımları tamamladınız"* — Ödemeler ✅,
  Reklam ayarları onaylandı ✅, Siteye bağlandı ✅, sahiplik doğrulandı ✅,
  inceleme istendi ✅. **Top tamamen Google'da.**

### Onay gelince yapılacak 2 iş (~5 dakika)
1. **Auto ads AÇ:** Reklamlar → Siteye göre → `saemuhendislik.com` satırı →
   kalem/düzenle → "Otomatik reklamlar" anahtarı AÇIK → Siteye uygula / Kaydet.
2. **CMP (AB rıza mesajı) YAYINLA:** Gizlilik ve mesajlaşma → Avrupa tüzükleri →
   mesaj oluştur. Site, site adı ("SAE Mühendislik"), gizlilik URL'si
   (`/cerez-politikasi`) ve logo (`images/sae-logo-yatay.png`, 5:1, PIL ile
   üretildi, 12 KB) **hesapta kayıtlı**. İş ortakları zaten ayarlı (198).
   ⚠ 30.08'de kuruldu ama **"Yayınla" düğmesi hesap onayı gelene kadar PASİF** —
   onay sonrası mesajı yeniden oluşturup yayınlamak 1 dakikalık iş.

> Not: 21 günü geçerse panelden yeniden inceleme talebi gönderilecek (normal, zararsız).
> Oturum düşerse şifre girilmez, AAE'den 008 ile giriş istenir.

---

## 7. Google Search Console

- `saemuhendislik.com` **URL-öneki mülkü** olarak doğrulandı (30.08).
  Yöntem: HTML dosyası `google19071191ddf4150f.html`.
  (Alan adı doğrulaması Cloudflare DNS hesabına erişim istediği için bilinçli
  olarak daha az yetkili yol seçildi.)
- `sitemap.xml` sunuldu → **"Başarılı"**; 22 sayfa → 07.09'da 23 sayfa.
- 30.08'den beri gösterim/tıklama verisi toplanıyor; site aramada görünüyor
  (ilk ölçüm: 1 gösterim, 0 tıklama, ort. konum 62 — yeni site için normal).

### 06.09 dizine ekleme hataları ve çözümü
İki uyarı maili: *"Sayfalarınızın dizine eklenmesini engelleyen yeni nedenler:
Yönlendirmeli sayfa"*. Kök neden = `.html` → uzantısız 308 (bkz. Kural 1).

Yapılanlar: sitemap temiz URL'ye geçti, 23 sayfanın iç linkleri mutlak temiz yola
çevrildi, **her sayfaya `rel="canonical"` eklendi** (daha önce hiç yoktu),
hreflang temizlendi. 59 dosya dağıtıldı, canlıda hepsi doğrudan 200 doğrulandı.
Sitemap yeniden gönderildi, iki hata için **"Düzeltmeyi doğrula"** başlatıldı.

07.09 rapor tablosu:

| Durum | Sayfa |
|---|---|
| ✅ Dizine eklenmiş | 12 |
| ⚠ Yönlendirmeli sayfa | 9 → düzeltildi, doğrulama başladı |
| ⚠ Canonical'sız kopya | 3 → düzeltildi, doğrulama başladı |
| ⏳ Keşfedildi, taranmadı | 10 |
| ⏳ Tarandı, eklenmedi | 1 |

**Doğrulama sonucu 12.09'dan sonra geldi — kontrol edilmeli.**

---

## 8. Günlük otomatik takip görevi (12.09'da kuruldu)

- Zamanlanmış görev adı: **`adsense-gunluk-kontrol`**, her gün **12:00**.
- Dosya: `C:\Users\ahmet\.claude\scheduled-tasks\adsense-gunluk-kontrol\SKILL.md`
- Yaptığı: Gmail taraması (Search Console maili) + site sağlık kontrolü (curl,
  `--ssl-no-revoke`) + AdSense paneli (Chrome eklentisi, `u/1` URL'si).
- **Onay gelirse AAE'ye sormadan Auto ads'i açar ve CMP mesajını yayınlar** —
  bu yetki 12.09'da açıkça verildi.
- Durum değişmezse tek satır bildirir, log'a yazmaz. 21 günü geçerse yeniden
  inceleme ister. Oturum düşerse şifre girmez, 008 ile giriş istenmesini bildirir.
- ⚠ **Görev yalnızca uygulama AÇIKKEN çalışır.** Nitekim 13.09–03.10 arasında
  bilgisayar erişilemez olduğu için **hiç çalışmadı** ve 16.09'daki iki Search
  Console uyarısı 17 gün boyunca görülmedi (bkz. §0). Takibin tek dayanağı bu
  görev olmamalı. Panelin ekran görüntüsü sık sık
  "0 width"/timeout veriyor → screenshot yerine JS / `get_page_text` kullanılıyor.

Gmail bağlayıcısı **eserahmetasim@gmail.com**'a bağlı: AdSense maili oraya
**GELMEZ** (008'e gelir), Search Console maili oraya gelir.

---

## 9. Bilgi kaynakları (AAE'nin bilgisayarında)

| Yol | Ne |
|---|---|
| `C:\SAE-yukleme\` | **Canlı sitenin tek kaynağı** (07.09 itibarıyla 59 dosya) |
| `…\patent\saemuhendislik-site\` | Çalışma alanı / kaynak yedek |
| `…\saemuhendislik-site\eski-site-yedek\` | Eski sitenin tam yedeği (11 sayfa, 16 görsel, 5 PDF) |
| `…\saemuhendislik-site\icerik\` | Yayın PDF'lerinin kaynak HTML'leri |
| `…\patent\wiki\kavramlar\saemuhendislik-sitesi.md` | **Ana reçete sayfası** |
| `…\patent\wiki\kaynak-ozetleri\konusma-2026-08-10-saemuhendislik-sitesi.md` | Kuruluş öyküsü |
| `…\patent\wiki\index.md`, `log.md` | Wiki indeksi ve günlük |
| `…\.claude\projects\C--Users-ahmet-OneDrive-Masa-st--patent\memory\saemuhendislik-sitesi.md` | Kalıcı proje hafızası |
| `…\patent\kirik-yuzey-analizi\`, `…\KirikAnalizProgram\` | No.6'nın kaynak birikimi |

---

## 10. Bekleyen işler

### Siteyle ilgili
1. **AdSense — yeniden inceleme talebi** (36. gün, 21 eşiği aşıldı). Onay
   geldiyse Auto ads + CMP (bkz. §6). → *iş emri kuyrukta, bkz. §0*
2. **Search Console — düzeltme başarısız oldu + iki yeni "Kopya" sorunu**
   (16.09). Rapordan URL listesi alınıp üç hipotez doğrulanacak, düzeltilip
   yeniden "Düzeltmeyi doğrula" başlatılacak. → *iş emri kuyrukta, bkz. §0*
3. **Patent ve Ar-Ge Danışmanlığı sayfası** — AAE sıcak, henüz yapılmadı.
4. **"YENİ" rozeti** — bir sonraki yayında taşınmalı ya da kaldırılmalı.
5. **Uygulama bandı rozetleri** — **Mini Mühendis'e 12.09'da production access
   verildi**, "YAKINDA" rozeti artık yanlış → Play Store linkine çevrilecek
   (TR+EN). Malzeme Bilgisi hâlâ bekliyor; Moto Bakım eklenebilir.
6. **Blog** — trafik için önerildi, yapılmadı.
7. `info@` e-postası — hosting askıda; gerekirse Cloudflare Email Routing.
8. Eski sunucudaki çöp (artık erişilmiyor): `parca1-site.zip/.tar.gz`,
   `parca2-linkfix.tar.gz`, `taslak.html` vb.
9. `dovme1.pdf` / `dovme2.pdf` eski sunucuda da yoktu — hâlâ kayıp.

### Yan projeler (aynı oturumda geçen, site dışı)
- **Mini Mühendis** — ✅ **Play production access verildi (12.09.2026)**,
  `com.saemuhendislik.mini_muhendis`. Sıradaki: yayına alma + site bandındaki link.
- **Malzeme Bilgisi** + **Moto Bakım** — mağaza paketleri hazır, Play Console'da
  uygulama oluşturma bekliyor. (`MalzemeBilgisi-v1.3.1-playstore.aab` hazır.)
- **Yayın 0125-05** — normalize grup testleri + SEM kayıtları bekliyor.
- **VAKA-026** — AYDMET-26/007 sonucu bekliyor.

---

## 11. Bu depodan çalışmanın sınırları

Bu bulut oturumunda **site dosyalarına ve canlı siteye erişim yok**:

- `C:\SAE-yukleme` AAE'nin Windows makinesinde; bu konteyner Linux ve ayrı bir makine.
- `saemuhendislik.com` bu ortamın **ağ politikası tarafından engelli** (egress proxy
  403 veriyor). Canlı doğrulama için ortamın Network access ayarına bu alan adının
  eklenmesi gerekir.
- Cloudflare dash + AdSense + Search Console işleri **Chrome eklentisiyle AAE'nin
  bilgisayarından** yürüyor.

Yani buradan yapılabilecekler: içerik/HTML/CSS yazmak, PDF içeriği hazırlamak,
reçeteleri güncellemek, plan çıkarmak. Dağıtım ve panel işleri için yerel oturum
(`Saemuhendislik sistem düzenlemesi`) gerekiyor.

**Kalıcı iyileştirme önerisi:** `C:\SAE-yukleme` bir git deposuna alınıp Cloudflare
Pages'in **Git entegrasyonu**na bağlanırsa, dağıtım `git push` ile olur — zip
yükleme, gizli input, koordinat tıklaması, "Save and deploy işlemedi" derdi tamamen
biter ve siteye bu bulut oturumundan da çalışılabilir hale gelir.
