# AAE — iki tık ve bir ekran görüntüsü

> 25.11.2026. Her şey hazır, üç küçük iş bekliyor ve üçü de **senin
> tarayıcında**. Toplam beş dakika. Sırayla git, her biri bitince bana "tamam"
> demen yeter.
>
> Not: Google konsolu hesabının diline göre bazen İngilizce bazen Türkçe
> çıkıyor. O yüzden her düğmenin iki adını da yazdım. Göremezsen ekran
> görüntüsü at, nerede olduğunu söylerim.

---

## İŞ 1 — YouTube API'sini aç (≈2 dakika)

**Neden:** 21 Kasım'dan beri sistem her gün iki kez video yayınlamaya çalışıyor
ve her seferinde tam son adımda duruyor. Sebep tek: bu API kapalı. **Sekiz
deneme boş gitti, 25 ders sırada bekliyor.**

### Adımlar

**1.** Şu adrese gir (tarayıcıya yapıştır):

```
https://console.developers.google.com/apis/api/youtube.googleapis.com/overview?project=846148797554
```

**2.** Sayfanın tepesinde büyük harflerle **YouTube Data API v3** yazdığını
gör. Yazmıyorsa yanlış sayfadasın, linki tekrar yapıştır.

**3. ⚠ Proje kontrolü — bu adımı atlama.** Sayfanın en üstünde, Google
logosunun sağında proje adı yazar. Orada **SAE Yayin** ya da **846148797554**
görmelisin.
- Doğruysa devam et.
- Başka bir proje adı yazıyorsa: o yazıya tıkla, açılan listeden **SAE Yayin**
  projesini seç, sonra linki tekrar yapıştır. (Yanlış projede ENABLE'a basmak
  işe yaramaz — asıl sorun tam olarak bu: API başka bir projede açılmış olabilir.)

**4.** Sayfanın ortasında mavi bir düğme var: **ENABLE** (ya da
**ETKİNLEŞTİR**). Ona bas.

**5.** Birkaç saniye sonra sayfa değişir. Artık mavi düğme yerine **MANAGE /
YÖNET** yazar, üstte de "API enabled" benzeri bir ibare olur. **Bitti.**

### Zaten açıksa ne olur?

4. adımda mavi **ENABLE** düğmesi yoksa, onun yerine **MANAGE / YÖNET**
görüyorsan: API zaten açık demektir. O zaman **3. adıma geri dön ve proje
adını kontrol et** — büyük ihtimalle API başka bir projede açık ve bizim
kullandığımız proje (`846148797554`) kapalı.

---

## İŞ 2 — "In production" yap (≈1 dakika, aynı konsolda)

**Neden:** Google'ın verdiği erişim anahtarı, uygulama "Testing" modunda
kalırsa **7 gün sonra kendiliğinden ölüyor** ve yayın sessizce duruyor —
hata vermez, sadece durur. Anahtar 21 Kasım'da alındı, yani **bu hafta içinde**
bitebilir. Bir dakikalık iş, şimdi yaparsan bir daha uğraşmayız.

### Adımlar

**1.** Aynı konsolda sol menüden: **APIs & Services** → **OAuth consent
screen** (Türkçe: **API'ler ve Hizmetler** → **OAuth izin ekranı**).

**2.** Açılan sayfada **Publishing status** (Yayınlama durumu) diye bir satır
var. Yanında ne yazıyor?

| Yazan | Ne yapacaksın |
|---|---|
| **In production** | Hiçbir şey. Bu iş zaten tamam, 3. işe geç. |
| **Testing** | Devam et ↓ |

**3.** "Testing" yazıyorsa, aynı sayfada **PUBLISH APP** (ya da **UYGULAMAYI
YAYINLA**) düğmesi olacak. Ona bas.

**4.** Bir onay penceresi çıkar, onayla. Durum **In production**'a döner.
**Bitti.**

> Google doğrulama/verification istemez, çünkü uygulamayı sadece sen
> kullanıyorsun. Eğer ileride bir yerde "doğrulanmamış uygulama" uyarısı
> görürsen normaldir, **Advanced → Go to… (unsafe)** ile geçilir. Uygulama
> senin kendi uygulaman.

---

## İŞ 3 — AdSense'in red gerekçesi (≈1 dakika, ekran görüntüsü)

**Neden:** 22 Kasım'da Google siteyi inceledi ve **reddetti** — yani
saemuhendislik.com şu anda reklam göstermiyor, hesap değişikliğinden beri
yaklaşık **12 gündür** böyle. Sebep mailde yazmıyor, sadece panelde yazıyor.
O gerekçeyi görmeden yanlış şeyi düzeltme riski var; doğrusunu görürsem sana
birebir yapıştırılacak bir düzeltme hazırlarım.

### Adımlar

**1.** `https://adsense.google.com` adresine gir. Hesap:
**eserahmetasim@gmail.com** (yeni hesap, eski 008'li olan değil).

**2.** Sol menüden **Siteler** (İngilizce: **Sites**).

**3.** Listede **saemuhendislik.com** satırını bul. Yanında bir durum
göreceksin — "Hazır değil", "İlgilenilmesi gerekiyor", "Needs attention" gibi.

**4.** O satıra tıkla. Altında ya da açılan panelde **neyin düzeltilmesi
gerektiği** yazar.

**5.** **O ekranın görüntüsünü al ve bana at.** Ya da orada ne yazıyorsa tek
satırla yaz. İkisi de olur.

---

## Bitince

Bana sadece **"API'yi açtım"** demen yeterli.

- Sistemi elle çalıştırıp **yayın yapmadan** sınarım, ~20 dakikada sonucu
  söylerim. Gerçekten açılmış mı, anahtar sağlam mı — ikisini de ölçer.
- Sonra ilk gerçek yayın kendiliğinden akar: günde iki ders, 10:00 ve 14:00.
- AdSense gerekçesini attığında da ona göre düzeltmeyi yazarım.

**Takılırsan uğraşma, ekran görüntüsü at.** Hangi adımda olduğunu ve ne
yapacağını söylerim.
