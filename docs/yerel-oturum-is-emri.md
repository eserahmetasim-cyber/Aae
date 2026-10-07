# Yerel oturuma yapıştırılacak iş emri

> Son güncelleme: **07.10.2026** (AdSense onayı geldi, sıra değişti).
> Bilgisayardaki Claude oturumuna ("Saemuhendislik sistem düzenlemesi") açılınca
> yapıştır.
>
> Not: Bu emir bulut oturumundan `send_message` ile 03.10, 06.10 ve 07.10'da
> zaten kuyruğa alındı — bilgisayar bağlanınca kendiliğinden düşmesi gerekir. Bu
> dosya yedek: kuyruk düşmezse ya da yeni bir oturum açarsan aşağıdaki bloğu
> yapıştır.

---

## Yapıştırılacak metin (aşağıdaki çizgiler arası)

---

Bu işleri bu sırayla yap, sonucu bana tek mesajda özetle.

**00) ⚠⚠ EN ÖNCE — AdSense ONAYI GELDİ, reklamları yayına al (07.10).**
Panelde "site için reklam onayı alındı" görüldü. İlk iş durumu teyit etmek:
`https://adsense.google.com/adsense/u/1/pub-8433209614215281/sites` (008, `u/1`;
screenshot yerine JS / `get_page_text`).
- Onaylıysa: **Reklamlar → Siteye göre → `saemuhendislik.com` → düzenle**
  - Otomatik reklamlar **AÇIK**
  - **Tüm formatlar açık**: sayfa içi (in-article, in-feed, multiplex),
    **vignette**, **anchor**, **yan panel** — hiçbirini kapatma
  - **Yoğunluk kaydırıcısı en yükseğe**
  - Sayfa hariç tutma varsa temizle — **ana sayfa dahil** her yerde reklam
  - Siteye uygula / Kaydet
- Sonra **Gizlilik ve mesajlaşma → Avrupa tüzükleri → mesaj oluştur → Yayınla**
  (bilgiler kayıtlı: "SAE Mühendislik", `/cerez-politikasi`, logo, 198 ortak).
- `ads.txt` durumu "Yetkili"ye dönmeli; dönmezse 24-48 saat normal.
- `C:\SAE-yukleme` içinde grep: AdSense script'i 22 içerik sayfasının
  `<head>`'inde duruyor mu? Eksikse Python+UTF-8 ile ekle, zip → dağıt → 200 doğrula.

⚠ **Üç sayfa reklamsız KALACAK** (tercih değil, zorunluluk): `gizlilik.html` ve
`gizlilik-politikasi.html` (Play Store'a verilen uygulama gizlilik politikaları —
reklam koymak uygulama incelemesinde sorun çıkarır) ve `404.html` (içeriksiz
sayfa, AdSense politikası). Bu üçünde script hiç yok, **eklenmeyecek**.
`google19071191ddf4150f.html` de dokunulmaz.

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

**3b) Mini Mühendis'i YAYINA AL — AAE "artık yayınlasınlar" diyor.**
⚠ Önce şunu anla: 12.09 maili **yayınlama izni** verdi, yayına almadı. 12.09'dan
07.10'a kadar Play Console'dan **hiç** "sürüm incelemede / yayınlandı / reddedildi"
maili gelmedi (Gmail'den 30 gün tarandı). Bu, **production sürümünün hiç
yayınlanmadığını** gösteriyor — Google bir şeyi bekletmiyor, rollout adımı eksik.
- Play Console → Mini Mühendis → **Üretim (Production)** track'i. Orada yayınlanmış
  bir sürüm var mı, yoksa sadece kapalı/iç test mi var?
- **Sürüm yoksa:** yeni üretim sürümü oluştur (mevcut AAB'yi seç) → sürüm notları →
  **İncelemeye gönder / Yayınla**. Eksik kalan zorunlu alan varsa (içerik
  derecelendirmesi, veri güvenliği formu, hedef kitle, gizlilik URL'si) tamamla.
  Gizlilik URL'si: `https://saemuhendislik.com/gizlilik` (veya Play'de kayıtlı olan).
- **Sürüm varsa ve "İncelemede" ise:** kaç gündür incelemede olduğunu söyle.
  **7 günü geçmişse** `docs/play-destek-mesaji.md` dosyasındaki hazır metinle
  Play Console → **Yardım ve geri bildirim → Destek ekibiyle iletişime geç**
  üzerinden destek kaydı aç (Play desteğinin açık bir e-posta adresi yok, form
  üzerinden gidiliyor). 7 günün altındaysa destek kaydı AÇMA, bekle.
- **Reddedilmişse:** ret gerekçesini oku, düzeltilebiliyorsa düzelt ve yeniden gönder.
- Sonucu AAE'ye net yaz: hangi aşamada, ne yapıldı, ne bekleniyor.

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
