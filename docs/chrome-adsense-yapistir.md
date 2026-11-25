# Tarayıcıdaki Claude'a yapıştır — AdSense red gerekçesini çöz

> **Yazılma tarihi:** 16.11.2026 · **baştan yazıldı 25.11.2026**
>
> ⚠ **25.11'deki değişiklik — önemli:** bu kağıdın eski hâli **kapatılmış olan
> eski hesabı** (`ahmetasimeser008@gmail.com`, `pub-8433209614215281`) işaret
> ediyordu. Onu takip eden ölü hesapta çalışıyordu. Hesap 14.11'de değişti,
> kağıt şimdi doğru hesaba bakıyor.
>
> ⚠ **İkinci değişiklik:** eski kağıt "Auto ads'i aç" diye başlıyordu. Oysa
> **22.11'de AdSense siteyi reddetti** — onay gelmeden Auto ads'in hiçbir
> hükmü yok. Yeni sıra: önce **red gerekçesini oku**, sonra çöz, sonra
> inceleme iste. Auto ads en sona taşındı.

## AAE, senin yapacağın tek şey

Brave'de (ya da Chrome'da) **Claude yan panelini** aç → aşağıdaki çizgiler
arasındaki metni **olduğu gibi yapıştır**. Panelden şifre istenirse **şifreyi
sen gir**, hiçbir Claude giremez. Gerisini o panel yapacak.

**Neden bulut oturumundan yapılamıyor:** o oturumda tarayıcı/ekran aracı yok
(25.11'de arandı, yok) ve sitenin kaynağı da o depoda değil. Gereken iş senin
kendi hesabında, tarayıcı tıklamaları.

---

## ⬇ YAPIŞTIRILACAK METİN ⬇

---

Merhaba. Ekrandaki tarayıcıyı kullanarak bir AdSense işi yapacaksın. AAE teknik
değil — ona adım sorma, yapabildiğin her şeyi kendin yap. Yalnızca şifre
ekranlarında ve "İzin Ver" kutularında ona dokundur. Yapamadığın madde olursa
sebebini **aynen** yaz, uydurma, tahmin yürütme.

**Hesap bilgisi (bunu doğrula, yanlış hesapta çalışma):**
- Doğru hesap: **`eserahmetasim@gmail.com`**, yayıncı **`pub-7223494011776010`**
- ⛔ Eski hesap `ahmetasimeser008@gmail.com` / `pub-8433209614215281`
  **kapatıldı.** Oraya girmeye çalışma, orada iş yapma.
- Panelde sağ üstte başka bir hesap görünüyorsa hesabı değiştir ve AAE'ye söyle.

**Durum:** 22.11.2026 saat 19:32'de Google şu postayı gönderdi: *"Sitenizin
AdSense'e hazır olması için bazı sorunların düzeltilmesi gerekiyor."* Posta
gerekçe yazmıyor, "hesabınızdaki **Siteler** sayfasına bakın" diyor. Site o
günden beri reklamsız.

**Sitede sorun aramana gerek yok — 25.11'de bulut oturumu 88 sayfanın tamamını
tek tek ölçtü ve şunları eledi:**

| Ölçülen | Sonuç |
|---|---|
| `ads.txt` | `google.com, pub-7223494011776010, DIRECT, f08c47fec0942fa0` — doğru |
| Reklam kodu | 86/88 sayfada `ca-pub-7223494011776010` var |
| Eski yayıncı kimliği | canlı sitede hiç yok (0 sayfa) |
| HTTP | 88 sayfanın hepsi 200, kırık sayfa yok |
| İçerik | sayfa ortalaması 1111 kelime; 150 kelimenin altında 0 sayfa |
| `robots.txt` | `Mediapartners-Google` engelli değil |
| Gizlilik politikası | `/cerez-politikasi` 200, iki dilde altlıkta bağlı |

Yani **eksik kod, yanlış yayıncı kimliği, bozuk `ads.txt`, kırık sayfa, ince
içerik, tarayıcı engeli ve eksik gizlilik politikası ihtimalleri elendi.**
Gerekçe panelde yazılı; işin o gerekçeyi bulmak.

### 1) ⚠ EN ÖNEMLİ ADIM — red gerekçesini oku

1. Sol menü **Siteler** (İngilizce panelde **Sites**).
2. `saemuhendislik.com` satırına bas / detayını aç.
3. Orada ne yazıyorsa **harfi harfine** yaz. "Hazır değil" demesi yetmez —
   altındaki gerekçe satırını, politika adını, kırmızı/sarı uyarıyı,
   "Neler yapmalıyım" bağlantısının arkasındaki metni de oku ve yaz.
4. Ekran görüntüsü alabiliyorsan al.

**Bu madde bitmeden aşağıdakilere geçme.** Gerekçeyi bilmeden yapılacak her
şey tahmin olur ve 12 gündür kaybedilen zamanı daha da uzatır.

### 2) Gerekçeye göre çöz — panelden çözülebilenler

Gerekçe aşağıdakilerden biriyse **sen çöz**, AAE'ye sorma (şifre hariç):

- **Hesap profili / adres / telefon doğrulaması eksik:** sol menü **Hesap** →
  **Bilgiler** / **Ödemeler**. Ödeme adresi ve telefon doğrulaması
  tamamlanmamışsa tamamla. Telefona gelen kodu AAE girsin.
  → *Bu, elenmeyen ihtimaller arasında en olası olanı: 14.11'de hesap yeni
  açıldı ve profil tamamlanmamış durumda.*
- **Site sahipliği çakışması / site başka hesapta görünüyor:** eski hesap
  kapatıldığı hâlde `saemuhendislik.com` claim'i düşmemiş olabilir. Panelde
  "bu site başka bir hesaba ait" benzeri bir şey yazıyorsa siteyi kaldırıp
  yeniden ekle; olmuyorsa metni aynen yaz.
- **`ads.txt` yetkisiz görünüyor:** dosya doğru (yukarıdaki tabloya bak),
  panelin 24-48 saatte yakalaması normal. Bir şey yapma, sadece ne yazdığını
  not et.
- **Politika ihlali (içerik):** hangi politika olduğunu **adıyla** yaz. Siteyi
  kendi kafana göre değiştirmeye çalışma — site kaynağı bu bilgisayarda
  `C:\SAE-yukleme` klasöründe ve dağıtımı ayrı bir iş; kararı AAE verir.

Gerekçe bu listede yoksa: **hiçbir şey değiştirme**, metni aynen yaz, dur.

### 3) Düzelttiysen inceleme iste

Panelde `saemuhendislik.com` için **"İnceleme isteyin" / "Request review"**
düğmesi aktifse bas. Sonuç 1-14 gün içinde e-postayla gelir.

⚠ Gerekçeyi çözmeden inceleme isteme — tekrar reddedilir ve sıra uzar.

### 4) ✅ YALNIZCA onay geldiyse — reklamları aç

Bu bölüm **site "Hazır" / "Onaylandı" olduktan sonra** geçerli. Reddedilmiş
durumdayken buradaki ayarların hükmü yok, zaman kaybetme.

1. Sol menü **Reklamlar** → **Siteye göre** → `saemuhendislik.com` satırında
   **kalem** ikonu.
2. **Otomatik reklamlar** anahtarını **AÇ**.
3. Formatların **hepsi açık** kalsın: sayfa içi, **vignette** (tam sayfa
   geçiş), **anchor** (yapışkan çubuk), **yan panel**. Hiçbirini kapatma.
4. **Reklam yükü** kaydırıcısını **en yükseğe** çek.
5. Sayfa hariç tutma / URL grubu varsa temizle — **ana sayfa dahil** her
   sayfada reklam olsun.
6. **Siteye uygula** → kaydedildiğini doğrula.
7. Sol menü **Gizlilik ve mesajlaşma** → **Avrupa tüzükleri** → kayıtlı mesajı
   aç → **Yayınla**. Bilgiler kayıtlı: site adı "SAE Mühendislik", gizlilik
   URL'si `https://saemuhendislik.com/cerez-politikasi`, logo yüklü.

### 5) Bitince dört şeyi yaz

1. **Red gerekçesi aynen ne yazıyordu?** (en önemlisi)
2. Ne yaptın / neyi düzelttin?
3. İnceleme isteği gönderildi mi?
4. Panelde `ads.txt` ne diyor?

Şifre isterse AAE'ye sor, sen girmeye çalışma.

---

## Panel bitince beklenen sonuç

**Şu an hedef bu değil** — şu an hedef gerekçeyi öğrenmek. Aşağıdaki tablo
onay geldikten sonrası için:

| Ne | Olmalı |
|---|---|
| Siteler → `saemuhendislik.com` | **Hazır / Onaylandı** |
| Reklamlar → `saemuhendislik.com` | Otomatik reklamlar: **Açık** |
| Yoğunluk | En yüksek |
| Formatlar | Hepsi açık (vignette + anchor + yan panel dahil) |
| Gizlilik ve mesajlaşma | AB rıza mesajı **Yayında** |
| `ads.txt` | "Yetkili" — hemen dönmezse 24-48 saat normal |

Onaydan sonra reklamların sitede görünmesi **birkaç saat** sürebilir. Hemen boş
görünürse Ctrl+Shift+R ile sert yenile ve 2-3 saat bekle.

⚠ Üç sayfa reklamsız kalacak ve bu **doğru**: `gizlilik.html`,
`gizlilik-politikasi.html` (Play Store'a verilen uygulama gizlilik
politikaları) ve `404.html` (içeriksiz sayfa). Bu üçünde AdSense kodu hiç yok,
eklenmeyecek.

ℹ `/cerez-politikasi` sayfasında da reklam kodu yok ve öyle kalması öneriliyor
(politika sayfası, 473 kelime). `/kesim-plani/` sayfasında ise kod yok ama
2341 kelime var — oraya eklenmeli; bu bir **dağıtım** işi, panelden yapılmaz,
bkz. `docs/reklam-kodu-eksik-sayfalar.md`.
