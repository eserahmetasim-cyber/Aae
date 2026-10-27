# Bilgisayardaki Claude'a yapıştırılacak iş emri

> Son güncelleme: **27.10.2026**
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

Merhaba. Aşağıdaki altı işi bu sırayla yap, her birini bitirince bana tek satır bildir. ⛔ 2. madde salt-okunur: Mini Mühendis'te hiçbir şey gönderilmeyecek, gerekçesi orada yazılı. ⚠ 5. madde (www→apex 301) artık en acil olanı — Search Console doğrulaması 12.10'da onun yüzünden başarısız döndü. Hepsi tarayıcı/konsol işi; Chrome'da Google hesaplarım açık. Sormadan yap, yetkiyi veriyorum. Şifre gerekirse bana sor, sen girmeye çalışma. Yapamadığın bir madde olursa sebebini yaz, uydurma.

**1) ⚠ EN ÖNCE — AdSense onayı geldi, reklamları yayına al.**
Konsol: `https://adsense.google.com/adsense/u/1/pub-8433209614215281/sites`
Hesap **ahmetasimeser008@gmail.com** (`u/1`). Panel geç yüklenir ve ekran görüntüsü sık sık hata verir → **JS / sayfa metni** ile oku.
- **Durumu teyit et:** panelde site "Hazır"/onaylı mı? Onaylıysa devam. Hâlâ "Hazırlanıyor" ise Auto ads'i yine aç (zararsız) ve durumu bana yaz.
- **Auto ads — MAKSİMUM:** Reklamlar → Siteye göre → `saemuhendislik.com` → düzenle → **Otomatik reklamlar AÇIK**, **tüm formatlar açık** (sayfa içi, **vignette**, **anchor**, **yan panel**), **yoğunluk kaydırıcısı en yükseğe**, sayfa hariç tutma varsa temizle (**ana sayfa dahil**) → Siteye uygula / Kaydet.
- **Rıza mesajını yayınla:** Gizlilik ve mesajlaşma → Avrupa tüzükleri → mesaj oluştur → **Yayınla**. Bilgiler hesapta kayıtlı: site adı "SAE Mühendislik", gizlilik URL'si `https://saemuhendislik.com/cerez-politikasi`, logo `images/sae-logo-yatay.png`, 198 iş ortağı. 30.08'de kurulmuştu ama hesap onayı beklediği için "Yayınla" pasifti.
- **ads.txt:** panelde "Yetkili"ye dönmeli. Dönmezse 24-48 saat normal, uğraşma. İçerik doğru olmalı: `google.com, pub-8433209614215281, DIRECT, f08c47fec0942fa0`
- **Kod kontrolü:** `C:\SAE-yukleme` içinde ara → `pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8433209614215281` 22 içerik sayfasının `<head>`'inde mi? Eksikse Python + UTF-8 ile ekle (PowerShell `-replace` Türkçe karakteri bozuyor), sonra dağıt (aşağıdaki dağıtım reçetesi).

⚠ **Üç sayfa reklamsız KALACAK** — bu bir tercih değil, zorunluluk. Maksimum ayarı bunları kapsamıyor:
- `gizlilik.html` ve `gizlilik-politikasi.html` → Play Store'a verdiğim uygulama gizlilik politikaları; reklam koymak uygulama incelemesinde sorun çıkarır.
- `404.html` → içeriksiz sayfa, AdSense politikası reklam istemiyor.

Bu üçünde AdSense script'i hiç yok ve **eklenmeyecek**. `google19071191ddf4150f.html` (Search Console doğrulama dosyası) da silinmeyecek, değiştirilmeyecek.

**2) ⛔ Mini Mühendis — HİÇBİR ŞEY GÖNDERME, sadece oku.**
Paket `com.saemuhendislik.mini_muhendis`. **Uygulama şu anda incelemede ve Google incelemeyi hızlandırdı.**
07.10'da destek kaydı `[3-2357000041354]` açıldı, Google aynı gün cevapladı:

> *"We've expedited your app to the Google Play Review Team… **Please refrain from submitting any further versions until the current review is finished and the issue is resolved.** Please be advised that each new submission will **reset the review turnaround time**, as the evaluation period is counted from the date of the most recent change."*

- **YENİ SÜRÜM / AAB GÖNDERME. Yeni üretim sürümü OLUŞTURMA. "İncelemeye gönder"e BASMA.** Bunlardan biri yapılırsa inceleme sayacı sıfırlanır ve her şey baştan başlar.
- **Yeni destek kaydı AÇMA** — kayıt zaten açık ve cevaplanmış.
- Yapılacak tek şey: Play Console → Mini Mühendis → **Üretim** track'inde durumu **oku** ve bana tek satır bildir (İncelemede mi, Yayında mı, Reddedildi mi; kaç gündür öyle).
- **Reddedilmişse** gerekçeyi oku ve bana yaz — düzeltmeyi birlikte kararlaştıracağız, kendi başına yeniden gönderme.
- Eksik zorunlu bölüm (içerik derecelendirmesi, veri güvenliği, hedef kitle, gizlilik URL'si) görürsen **doldur** ama **sürüm gönderme**; sadece bana haber ver.
- ⛔ **AdMob'u bu uygulamaya ŞİMDİ EKLEME.** AdMob hesabı 13.10'da onaylandı (`pub-7223494011776010`), ama reklam göstermek SDK ekleyip yeni sürüm yüklemeyi gerektirir — yukarıdaki yasağa girer. Önce inceleme bitsin, uygulama yayına girsin; reklamlı sürüm ayrı bir güncelleme olarak çıkar.
- ⛔ **"Reklam içerir" beyanını da şimdi işaretleme** — uygulamada henüz reklam yok, yanlış beyan olur.

**3) AAE Motosiklet Yol Okulu — üretim izni GELDİ, sıralamaya dikkat.**
Paket `com.saemuhendislik.yol_okulu_3b`. **27.10 02:57'de üretim izni verildi** ("production access has now been granted"). Kapalı test şartı tuttu. Ama **izin yayın değil** — üretim sürümü oluşturulup yayına alınması gerekiyor.

⚠ **AdMob'u yayından ÖNCE ekle. Sıra önemli.** Mini Mühendis'ten öğrendik: sürüm bir kez incelemeye girince yeni sürüm gönderilemiyor (sayaç sıfırlanıyor) ve inceleme haftalarca sürebiliyor. Yol Okulu şu an incelemede **değil**, şimdi serbest. Bu sırayla git:

1. **AdMob SDK'sını ekle** — yayıncı `pub-7223494011776010`, hesap `eserahmetasim@gmail.com`. AdMob konsolunda uygulamayı oluştur, reklam birimlerini (banner / geçiş / ödüllü — hangisi oyuna uygunsa) tanımla, SDK'yı projeye bağla, **test reklamlarıyla** çalıştığını doğrula.
2. **Play Console → "reklam içerir" beyanını işaretle.** Artık doğru beyan; bundan önce işaretlenmeyecekti.
3. **Üretim sürümünü oluştur ve BİR KEZ incelemeye gönder.** Gönderdikten sonra yeni sürüm gönderme.

Eksik zorunlu bölüm (içerik derecelendirmesi, veri güvenliği, hedef kitle, gizlilik politikası URL'si) varsa 3. adımdan önce tamamla.

Bitince bana tek satır yaz: AdMob eklendi mi, beyan işaretlendi mi, sürüm gönderildi mi.

**4) Android geliştirici doğrulaması — son tarih geçti.**
`https://play.google.com/console/android-developer-verification`
04.09'daki "[Son hatırlatma]" maili: *"Kaydedilmeyen tüm Google Play uygulamaları 30 Eylül 2026'dan sonra dünya genelinde Play'den kaldırılacak."* Bugün 07.10 — kaldırma bildirimi gelmedi ama doğrulanması gerek.
- `com.saemuhendislik.mini_muhendis` ve `com.saemuhendislik.yol_okulu_3b` **kayıtlı** mı?
- Console ana sayfasında "kaydedilmemiş" filtresini uygula; çıkan varsa kaydet.
- Yarım kalmış **paket adı kaydı taslağı** varsa tamamla.

**5) ⚠ EN ACİL — www → apex 301 yönlendirmesini kur.**
**12.10'da Search Console doğrulaması BAŞARISIZ döndü:** *"Kopya, Google kullanıcıdan farklı bir standart sayfa seçti… Sayfalarınızdan bazıları bu sorundan etkilenmeye devam ediyor"* (WNC-10031170). Aynı gün ikinci bir sorun (*"kullanıcı tarafından seçilen standart sayfa olmadan kopya"*) **başarıyla düzeltildi** (3 sayfa, WNC-10030335) — yani konsolda doğru şeyler yapılmış, ama bu sorunun kökü hâlâ duruyor.

**Kök sebep neredeyse kesin:** `www.saemuhendislik.com` apex'e 301 yönlendirmiyor, Google iki özdeş site görüyor. (10.09'da `www/ads.txt` 200 dönüyordu.)

```
curl -sS --ssl-no-revoke -o /dev/null -w "%{http_code} %{redirect_url}\n" https://www.saemuhendislik.com/
```
- **301 + `https://saemuhendislik.com/`** dönüyorsa yönlendirme zaten var → bana söyle, başka yere bakacağız (sonraki şüpheliler: `404.html` ve `google19071191ddf4150f.html` canonical'sız; `gizlilik.html` ile `gizlilik-politikasi.html` neredeyse aynı).
- **200 dönüyorsa** (beklenen): Cloudflare dash → `saemuhendislik.com` zone → **Rules → Redirect Rules → Create rule**:
  - Eşleşme: Hostname **equals** `www.saemuhendislik.com`
  - Hedef: **Dynamic** → `concat("https://saemuhendislik.com", http.request.uri.path)`
  - Durum kodu: **301**, **Preserve query string** açık, kural **Active**
  - (Mevcut `dokum-pdf-yonlendirme` kuralı örnek alınabilir.)
- Kural kaydedildikten sonra `curl`'ü tekrar çalıştır, **301** gördüğünü teyit et ve bana yaz.
- Sonra Search Console → Dizine ekleme → *"Kopya, Google kullanıcıdan farklı bir standart sayfa seçti"* → **Düzeltmeyi doğrula**'ya bas.

**6) Search Console — ÜÇ açık sorunun URL listesi.**
Açık kalanlar: yukarıdaki kopya sorunu + **"Yönlendirmeli sayfa"** (16.09'da başarısız bildirilmişti) + **"Bulunamadı (404)"** (26.10'da gelen YENİ sorun, WNC-20237597).
- Dizine ekleme raporunu aç, **her üç sorunun örnek URL listesini** çıkar ve bana yaz. 404 listesi özellikle önemli — hangi adreslerin kaybolduğunu bilmeden düzeltilemez. Teşhisi tahminle değil bu listeyle yapacağız.
- "Yönlendirmeli sayfa" listesinde `.html` uzantılı adres görürsen söyle — Cloudflare Pages uzantılı adresi 308 yönlendiriyor, link/canonical/sitemap'te `.html` olmamalı.

**Son: rozetler.** Bir oyunun Play store sayfası **gerçekten 200 döndüğü doğrulandıktan sonra** ana sayfadaki "YAKINDA GOOGLE PLAY'DE" rozetini gerçek Play linkine çevir (TR + EN). Yayında değilken link koyma, ölü sayfaya gider.

---

### Dağıtım reçetesi (site dosyası değişirse)
1. Değişiklikler **`C:\SAE-yukleme`** içine (tek kaynak; OneDrive klasöründen dağıtım yapma).
2. **.NET ZipFile** ile zip'le — girdi adları **düz bölü** olmalı. PowerShell `Compress-Archive` KULLANMA, ters bölü yazıyor ve bozuyor. Zip'i scratchpad'e yaz.
3. Cloudflare dash → `pages/view/saemuhendislik/deployments/new` → gizli zip input'u (sayfada `button type="file"` olarak görünür) → zip'i yükle → **"N/N files uploaded"** bekle (aradaki "Unzipped N" mesajları yanıltıcı; takılırsa sayfayı yenile ve aynı zip'i tekrar yükle) → **Save and deploy** (ilk tık sık sık işlemez; ref çalışmazsa ekran görüntüsünden koordinatla tıkla) → **"Success!"**.
4. Doğrulama **alan adı üzerinden** (pages.dev Türk ISS'lerinde engelli): `/`, `/hasar`, `/en/`, `/cerez-politikasi`, `/sitemap.xml`, `/ads.txt` → hepsi **200**.

### Değişmez kurallar
- Link / canonical / sitemap'te **`.html` yazılmaz** — Cloudflare Pages uzantılı adresi 308 yönlendiriyor, Google "yönlendirmeli sayfa" diyip dizine almıyor.
- `gizlilik.html`, `gizlilik-politikasi.html`, `google19071191ddf4150f.html` **silinmez**.
- Hiçbir panele **şifre girilmez**.
- Türkçe metin düzenlemede PowerShell `-replace` kullanılmaz; Python + UTF-8.
- Bitince wiki kavram sayfası `saemuhendislik-sitesi.md` ve kalıcı hafıza güncellenir.
