# Bilgisayardaki Claude'a yapıştırılacak iş emri

> Son güncelleme: **07.10.2026**
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

Merhaba. Aşağıdaki altı işi bu sırayla yap, her birini bitirince bana tek satır bildir. Hepsi tarayıcı/konsol işi; Chrome'da Google hesaplarım açık. Sormadan yap, yetkiyi veriyorum. Şifre gerekirse bana sor, sen girmeye çalışma. Yapamadığın bir madde olursa sebebini yaz, uydurma.

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

**2) Mini Mühendis'i yayına al.**
Paket `com.saemuhendislik.mini_muhendis`. 12.09'da **yayınlama izni** (production access) verildi ama o mail uygulamayı yayına almıyor. 12.09–07.10 arası Play Console'dan hiç "sürüm incelemede / yayınlandı / reddedildi" maili gelmedi → **üretim sürümü muhtemelen hiç yayınlanmadı.**
- Play Console → Mini Mühendis → **Üretim (Production)** track'i. Sürüm var mı?
- **Yoksa:** yeni üretim sürümü oluştur → mevcut AAB'yi seç → sürüm notu yaz → **incelemeye gönder**. Eksik zorunlu bölüm varsa tamamla: içerik derecelendirmesi, veri güvenliği formu, hedef kitle ve içerik, reklam beyanı, gizlilik politikası URL'si.
- **Varsa ve "İncelemede" ise:** kaç gündür incelemede olduğunu söyle. 7 günün altındaysa bekle, destek kaydı açma. Üstündeyse Play Console → **Yardım ve geri bildirim → Destek ekibiyle iletişime geç** üzerinden kayıt aç (Play desteğinin e-posta adresi yok, form üzerinden gidiliyor).
- **Reddedilmişse:** gerekçeyi oku, düzeltilebiliyorsa düzelt ve yeniden gönder.

**3) AAE Motosiklet Yol Okulu — üretime geçiş başvurusu.**
Paket `com.saemuhendislik.yol_okulu_3b`. Kapalı test daveti 22.09'da 14 kişiye gönderildi, **14 günlük sayaç 06.10'da doldu.**
- Play Console → kapalı test track'i → kaç test kullanıcısının **kesintisiz opt-in kaldığını** oku. Google kişisel hesaplar için **12** istiyor; bu sayı yalnızca konsolda görünür.
- **12 veya üzeriyse → üretime geçiş başvurusunu gönder.**
- Altındaysa kaç kişi eksik olduğunu söyle, yeni davet göndereyim.

**4) Android geliştirici doğrulaması — son tarih geçti.**
`https://play.google.com/console/android-developer-verification`
04.09'daki "[Son hatırlatma]" maili: *"Kaydedilmeyen tüm Google Play uygulamaları 30 Eylül 2026'dan sonra dünya genelinde Play'den kaldırılacak."* Bugün 07.10 — kaldırma bildirimi gelmedi ama doğrulanması gerek.
- `com.saemuhendislik.mini_muhendis` ve `com.saemuhendislik.yol_okulu_3b` **kayıtlı** mı?
- Console ana sayfasında "kaydedilmemiş" filtresini uygula; çıkan varsa kaydet.
- Yarım kalmış **paket adı kaydı taslağı** varsa tamamla.

**5) Search Console — üç açık sorun.**
16.09'da bildirildi: "Yönlendirmeli sayfa" düzeltmesi **başarısız oldu** + "Kopya, Google kullanıcıdan farklı bir standart sayfa seçti" + "Kullanıcı tarafından seçilen standart sayfa olmadan kopya".
- Dizine ekleme raporunu aç, üç sorunun **örnek URL listelerini** çıkar. Teşhisi tahminle değil bu listeyle yap.

**6) www → apex yönlendirmesini doğrula (kopya sorununun baş şüphelisi).**
```
curl -sS --ssl-no-revoke -o /dev/null -w "%{http_code} %{redirect_url}\n" https://www.saemuhendislik.com/
```
- **301 + `https://saemuhendislik.com/`** bekleniyor → sorun burada değil.
- **200 dönüyorsa** Google iki özdeş site görüyor demektir, kopya sorununun en güçlü sebebi bu. Çözüm: Cloudflare zone'da Redirect Rule — `www.saemuhendislik.com/*` → `https://saemuhendislik.com/$1`, **301**, Active (mevcut `dokum-pdf-yonlendirme` kuralının deseni).

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
