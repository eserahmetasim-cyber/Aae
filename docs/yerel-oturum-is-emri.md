# Yerel oturuma yapıştırılacak iş emri

> Hazırlanma tarihi: **06.10.2026**. Bilgisayardaki Claude oturumuna
> ("Saemuhendislik sistem düzenlemesi") açılınca yapıştır.
>
> Not: Bu emir bulut oturumundan `send_message` ile 03.10 ve 06.10'da zaten
> kuyruğa alındı — bilgisayar bağlanınca kendiliğinden düşmesi gerekir. Bu dosya
> yedek: kuyruk düşmezse ya da yeni bir oturum açarsan aşağıdaki bloğu yapıştır.

---

## Yapıştırılacak metin (aşağıdaki çizgiler arası)

---

Beş işi bu sırayla yap, sonucu bana tek mesajda özetle.

**0) ⚠ ÖNCE BU — Android geliştirici doğrulaması, son tarih GEÇTİ.**
04.09'daki "[Son hatırlatma]" maili: *"Tüm Google Play uygulamalarının ... **30
Eylül 2026'ya kadar kaydedilmesi gerekir. Kaydedilmeyen tüm Google Play
uygulamaları dünya genelinde Google Play'den kaldırılacak.**"* Bugün 06.10 —
son tarih 6 gün önce geçti. Kaldırma bildirimi gelmedi (muhtemelen otomatik
kaydedildi) ama doğrulanmalı.
- Play Console → `https://play.google.com/console/android-developer-verification`
- `com.saemuhendislik.mini_muhendis` ve varsa Malzeme Bilgisi / Moto Bakım
  paketleri **kayıtlı** mı?
- Console ana sayfasında "kaydedilmemiş" filtresini uygula; çıkan varsa kaydet.
- Yarım kalmış **paket adı kaydı taslağı** varsa tamamla.

**1) AdSense — başvuru 39. günde (28.08.2026'da yapıldı).**
Konsol: `https://adsense.google.com/adsense/u/1/pub-8433209614215281/sites`
(hesap `ahmetasimeser008@gmail.com`, `u/1`). Panel geç yüklenir; ekran görüntüsü
sık sık hata verdiği için **JS / get_page_text** ile oku.
- Durum hâlâ **"Hazırlanıyor"** ise → site detayından **yeniden inceleme talebi
  gönder**. 21 gün eşiği 18 gün önce aşıldı.
- Durum **"Hazır"/onaylı** ise → bana sormadan (a) Reklamlar → **Auto ads'i AÇ**,
  (b) **CMP / AB rıza mesajını yayınla**. Site adı, gizlilik URL'si ve logo
  hesapta kayıtlı. Bu yetkiyi 12.09'da verdim.
- Oturum düşmüşse **şifre girme** — bana "Chrome'da 008 ile AdSense'i aç" de ve dur.

**2) Search Console — kopya/dizine ekleme sorunu.**
Dizine ekleme raporunu aç. 16.09'da üç şey bildirildi:
- "Yönlendirmeli sayfa" düzeltmesi **BAŞARISIZ** oldu (bazı sayfalar hâlâ etkilenmiş)
- Yeni: **"Kopya, Google kullanıcıdan farklı bir standart sayfa seçti"**
- Yeni: **"Kullanıcı tarafından seçilen standart sayfa olmadan kopya"**

Her üçü için **örnek URL listesini çıkar**. Teşhisi tahminle değil bu listeyle yap.

**3) www → apex yönlendirmesini doğrula.**
```
curl -sS --ssl-no-revoke -o /dev/null -w "%{http_code} %{redirect_url}\n" https://www.saemuhendislik.com/
```
- **301 + `https://saemuhendislik.com/`** bekleniyor → sorun burada değil.
- **200 dönüyorsa** kopya sorununun en güçlü sebebi budur: Google iki özdeş site
  görüyor. Çözüm: Cloudflare zone'da Redirect Rule —
  `www.saemuhendislik.com/*` → `https://saemuhendislik.com/$1`, **301**, Active
  (mevcut `dokum-pdf-yonlendirme` kuralının deseni).

### Yedek şüpheliler (1–3 sonuç vermezse)
- 07.09 temiz-URL betiğinin `DOKUNMA` kümesi `{404.html,
  google19071191ddf4150f.html}` idi → bu ikisinde **canonical yok**. Google
  doğrulama dosyası dizine giriyorsa "standart sayfa olmadan kopya" tam bu.
  Çözüm robots.txt `Disallow` — **dosyayı silme, içeriğini değiştirme.**
- `gizlilik.html` (3662 B) ile `gizlilik-politikasi.html` (4144 B) içerik olarak
  neredeyse aynı → kopya kümesi. Play Console'a verilmiş olan adres korunacak,
  **o kanonik yapılacak.**

### Düzeltme çıkarsa
`C:\SAE-yukleme` → .NET ZipFile (**girdi adları düz bölü**, Compress-Archive
kullanma) → Pages `deployments/new` → gizli zip input'u → "N/N files uploaded" →
**Save and deploy** (ilk tık işlemezse koordinatla) → "Success!" → **alan adı
üzerinden** `/`, `/hasar`, `/en/`, `/cerez-politikasi`, `/sitemap.xml`,
`/ads.txt` **200** doğrula → Search Console'da sitemap'i yeniden gönder ve üç
sorun için **"Düzeltmeyi doğrula"** başlat.

⚠ Temiz URL kuralı: link / canonical / sitemap'te **`.html` yazılmaz**.

**4) Mini Mühendis yayın durumu — rozete dokunmadan önce doğrula.**
12.09'daki mail **yayınlama İZNİ** verdiğini söylüyor, uygulamanın yayında
olduğunu DEĞİL: *"this has now been granted. Production is where you make your
app available... **Before you release to production** we recommend testing..."*
12.09'dan beri "yayınlandı" maili de gelmedi.
- Play Console → Mini Mühendis → production track'te **canlı** mı, yoksa izin
  verilmiş ama sürüm hiç yayınlanmamış mı?
- `https://play.google.com/store/apps/details?id=com.saemuhendislik.mini_muhendis`
  gerçekten açılıyor mu?
- **Canlıysa** → ana sayfadaki "Uygulamalarımız" bandındaki rozeti gerçek Play
  linkine çevir (TR + EN), aynı dağıtıma dahil et.
- **Canlı değilse** → **"YAKINDA GOOGLE PLAY'DE" rozeti doğrudur, KALSIN.**
  (Ölü linke gitmek AdSense/SEO açısından zarar.) Bunun yerine bana yayına almak
  için ne gerektiğini bildir.

### Bitince
Wiki kavram sayfası `saemuhendislik-sitesi.md` ve kalıcı hafızayı güncelle.
`adsense-gunluk-kontrol` görevinin 13.09–06.10 arasında hiç çalışmadığını not et.

---

## Buluttan doğrulanmış arka plan (06.10.2026)

- Gmail (`eserahmetasim@gmail.com`): **16.09'dan beri yeni Search Console /
  AdSense maili YOK** → durum değişmemiş.
- AdSense maili bu hesaba gelmez, `ahmetasimeser008@gmail.com`'a gelir.
- Bulut oturumunun siteye **ağ erişimi yok** (egress engelli) ve
  `C:\SAE-yukleme`'ye **dosya erişimi yok** → dağıtımı yalnızca yerel oturum yapar.
  "İki oturum aynı anda dağıtım yapmasın" kuralı bu şekilde korunuyor.
