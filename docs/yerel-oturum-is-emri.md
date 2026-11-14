# Bilgisayardaki Claude'a yapıştırılacak iş emri

> Son güncelleme: **14.11.2026**
>
> **Nasıl kullanılır:** Bilgisayarındaki Claude uygulamasını aç → **yeni bir
> sohbet** başlat → aşağıdaki çizgiler arasındaki metni olduğu gibi yapıştır.
> Claude tarayıcı/ekran izni isterse **İzin Ver**'e bas. Gerisini o yapar.
>
> Not: Bu emir bulut oturumundan eski "Saemuhendislik sistem düzenlemesi"
> oturumunun kuyruğuna da gönderildi, ama o oturum bilgisayarda **Remote
> Control** çalışmasını gerektiriyor (13.09'dan beri kapalı). Yeni sohbete
> yapıştırmak daha kolay yol.

---

## ⬇ YAPIŞTIRILACAK METİN ⬇

---

Merhaba. 06.11'de siteyi ve Play sayfalarını canlı test ettim; eski iş emrinin yarısı geçersiz kaldı, bu güncel liste. Sırayla yap, her biri bitince bana tek satır bildir. Sormadan yap, yetkiyi veriyorum. Şifre gerekirse bana sor, sen girmeye çalışma. Yapamadığın madde olursa sebebini yaz, uydurma.

**Önce bilmen gerekenler (hepsi ölçüldü, tahmin değil):**
- İki oyun da **Google Play'de yayında** (`com.saemuhendislik.mini_muhendis`, `com.saemuhendislik.yol_okulu_3b` — mağaza sayfaları anonim olarak 200 dönüyor).
- `www` → apex **301 çalışıyor**. Cloudflare Redirect Rule işine gerek yok.
- `ads.txt` ve AdSense script'i canlıda var — **ama 14.11'de ölçtüm: site artık `pub-7223494011776010` (AdMob/eserahmetasim hesabı) üzerinden reklam veriyor**, eski `pub-8433209614215281` değil. Aşağıdaki 4. madde bununla ilgili.
- Sitemap'teki 87 adresin hepsi 200.

**1) Ana sayfaya Yol Okulu'nu ekle — hazır yama var, uydurma.**
Oyun yayında ama sitede hiç geçmiyor. **Birebir yapıştırılacak yama: `docs/yol-okulu-yamasi.md`** — TR ve EN kartları, güncellenmiş giriş cümleleri, ikon talimatı ve dağıtım adımları orada. Kart metni oyunun kendi Play açıklamasından alındı, yeniden yazma.
- Önce ikon: oyunun ikonunu `C:\SAE-yukleme\images\yol-okulu-ikon.png` olarak kaydet (sitede yok, 404).
- Sonra `index.html` ve `en/index.html` için yamadaki BUL/YERİNE bloklarını uygula. EN tarafında görsel yolu `../images/` — atlama.
- Türkçe metinde PowerShell `-replace` kullanma, Python + UTF-8.
- Dağıt, sonra bana haber ver; doğrulamayı ben yapacağım.
- ⚠ Not: site 06.11–14.11 arasında reklam değişikliği için **bir kez yeniden dağıtıldı**, ama bu kart konmadı. Yani dağıtım yolu çalışıyor; eksik olan sadece bu yama.

**2) AdMob'u iki oyuna da ekle.** (Yasak kalktı: inceleme bitti, ikisi de yayında.)
Yayıncı `pub-7223494011776010`, hesap `eserahmetasim@gmail.com`.
- AdMob konsolunda her iki uygulamayı oluştur, reklam birimlerini tanımla, test reklamlarıyla doğrula.
- ⚠ **Konum toplamayı KAPAT.** GMA SDK Android 1.7.0 / iOS 13.12.0+ sürümlerinde konum izni varsa kaba konum topluyor ve kapatmazsan varsayılan açık geliyor. Yapılandırma bayrağıyla kapat — açık bırakırsan gizlilik politikası + Play "Veri güvenliği" formu güncellemesi gerekir, hedef kitle çocuk/aile ise Families politikasıyla da sürtüşür.
- ⚠ Hedef kitle çocuk/aile ise **Families Self-Certified Ads SDK** listesinde olan bir AdMob sürümü kullan.
- Play Console'da **"reklam içerir" beyanını** işaretle (artık doğru beyan).
- Güncellemeleri gönder, sonra bana durumu yaz.

**3) ⏰ Satıcı (trader) durumu beyanı — son tarih 1 Şubat 2027.**
Yapılmazsa güncelleme gönderilemez ve iki oyun da Play'den kaldırılır.
⚠ **BANA SORMADAN DOLDURMA.** Satıcı beyanı bireysel geliştiricinin **telefon numarasını ve adresini Play'de herkese açık** yapıyor. AAE'ye seçenekleri göster (satıcı / işletme kaydı / AEA-BK'de dağıtmama), ne diyeceğini sor, sonra onun dediğini uygula.
Yol: Hesabı yönet → Hesap ayrıntıları → Hakkınızda → Satıcı durumu. Sonra her uygulama için ayrı: Tüm uygulamalar → uygulama → İzleyin ve geliştirin → Politika ve programlar → Uygulama içeriği.

**4) ⚠ AdSense profilini tamamla — ÖDEME BUNA BAĞLI.**
13.11'de `eserahmetasim@gmail.com`'a "AdSense'e hoş geldiniz" maili geldi; yayıncı **`pub-7223494011776010`**, "Sitenizi eklediniz" diyor. 14.11 canlı ölçümü bunu doğruluyor: `ads.txt` ve sayfa script'i artık bu kimliği taşıyor (06.11'de `pub-8433209614215281`'di). Yani site eski AdSense hesabından AdMob hesabına taşınmış.
Mailin saydığı iki eksik adım — **bunlar bitmeden hiç ödeme çıkmaz**:
- **Geçerli ödeme adresi** ekle.
- **Telefon numarasını doğrula.**
Konsol: `https://adsense.google.com/adsense/u/1/pub-7223494011776010/`
Ayrıca aynı hesapta teyit et:
- Gizlilik ve mesajlaşma → Avrupa tüzükleri → rıza mesajı **"Yayında"** mı? Değilse yayınla.
- Siteler listesinde `saemuhendislik.com` **"Hazır"** mı, `ads.txt` satırı **"Yetkili"** mi?
- ⚠ **AAE'ye sor:** eski hesap `pub-8433209614215281` (`ahmetasimeser008@gmail.com`) ne durumda? Aynı kişinin iki ayrı AdSense hesabı tutması AdSense politikasına aykırı. Kapandıysa/siteden çıkarıldıysa sorun yok; hâlâ açıksa ve siteyi tanımlıyorsa bunu çözmek gerek. **Kendi başına hesap kapatma.**

**5) Search Console — üç sorunun örnek URL listesi.**
Açık: "Yönlendirmeli sayfa", "Kopya, Google farklı standart sayfa seçti" (WNC-10031170), "Bulunamadı (404)" (WNC-20237597).
Ölçtüklerim: sitemap'teki 87 adresin hepsi 200, yani 404'ler **eski/dış bağlantılardan** geliyor. `.html` adresleri 308 ile temiz URL'ye gidiyor — "Yönlendirmeli sayfa" bundan.
- Dizine ekleme raporundan **üç sorunun da örnek URL listesini** çıkar ve bana yaz. Asıl teşhis bu listeyle yapılacak.

**6) Android geliştirici doğrulaması.**
`https://play.google.com/console/android-developer-verification` — iki paket de kayıtlı mı? Değilse kaydet.

---

### Dağıtım reçetesi (site dosyası değişirse)
1. Değişiklikler **`C:\SAE-yukleme`** içine (tek kaynak; OneDrive klasöründen dağıtım yapma).
2. **.NET ZipFile** ile zip'le — girdi adları **düz bölü** olmalı. PowerShell `Compress-Archive` KULLANMA.
3. Cloudflare dash → `pages/view/saemuhendislik/deployments/new` → zip'i yükle → **"N/N files uploaded"** bekle → **Save and deploy** → **"Success!"**.
4. Doğrulama **alan adı üzerinden**: `/`, `/hasar`, `/en/`, `/ads.txt` → hepsi 200.

### Değişmez kurallar
- Link / canonical / sitemap'te **`.html` yazılmaz**.
- `gizlilik.html`, `gizlilik-politikasi.html`, `google19071191ddf4150f.html` **silinmez**.
- `gizlilik.html`, `gizlilik-politikasi.html`, `404.html` **reklamsız kalır**, AdSense script'i bu üçüne eklenmez.
- Hiçbir panele **şifre girilmez**.
- Türkçe metin düzenlemede PowerShell `-replace` kullanılmaz; Python + UTF-8.
- Bitince `docs/saemuhendislik-sitesi.md` ve `docs/gunluk-durum.json` güncellenir.
