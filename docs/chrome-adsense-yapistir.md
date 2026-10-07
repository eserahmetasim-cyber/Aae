# Chrome'daki Claude paneline yapıştır — AdSense reklamlarını aç

> **Nasıl:** Chrome'da AdSense paneli ve Claude yan paneli açıkken, aşağıdaki
> çizgiler arasındaki metni Claude paneline yapıştır. O panel ekrandaki AdSense
> sekmesini görüyor ve tıklayabiliyor — bulut oturumunun yapamadığı tam olarak bu.
>
> Bu yalnızca **reklam** işi. Mini Mühendis ve Yol Okulu için Play Console
> gerekiyor; onların metni `docs/yerel-oturum-is-emri.md` içinde.

---

Bu Chrome'da açık olan AdSense panelinde şunları yap. Hesap `ahmetasimeser008@gmail.com`, yayıncı `pub-8433209614215281`.

1. Sol menü **Reklamlar** → **Siteye göre** sekmesi → `saemuhendislik.com` satırındaki **kalem** ikonuna bas.
2. **Otomatik reklamlar** anahtarını **AÇ**.
3. Reklam formatlarının **hepsini açık** bırak: sayfa içi, **vignette** (tam sayfa geçiş), **anchor** (yapışkan çubuk), **yan panel**. Hiçbirini kapatma.
4. **Reklam yükü** kaydırıcısını **en yükseğe** çek.
5. Sayfa hariç tutma / URL grubu varsa temizle — **ana sayfa dahil** her sayfada reklam olsun.
6. **Siteye uygula**'ya bas ve kaydedildiğini doğrula.
7. Sonra sol menü **Gizlilik ve mesajlaşma** → **Avrupa tüzükleri** → kayıtlı mesajı aç → **Yayınla**'ya bas. Bilgiler kayıtlı: site adı "SAE Mühendislik", gizlilik URL'si `https://saemuhendislik.com/cerez-politikasi`, logo yüklü. Daha önce hesap onayı beklediği için bu düğme pasifti, onay geldiğine göre artık basmalı.
8. Bitince bana dört şeyi söyle: Auto ads açık mı, yoğunluk ne, rıza mesajı yayında mı, panelde `ads.txt` durumu ne yazıyor.

Şifre isterse bana sor, sen girmeye çalışma.

---

## Panel bitirince beklenen sonuç

| Ne | Olmalı |
|---|---|
| Reklamlar → `saemuhendislik.com` | Otomatik reklamlar: **Açık** |
| Yoğunluk | En yüksek |
| Formatlar | Hepsi açık (vignette + anchor + yan panel dahil) |
| Gizlilik ve mesajlaşma | AB rıza mesajı **Yayında** |
| ads.txt | "Yetkili" — hemen dönmezse 24-48 saat normal |

Reklamların sitede görünmesi onaydan sonra **birkaç saat** sürebilir. Hemen boş
görünürse Ctrl+Shift+R ile sert yenile ve 2-3 saat bekle.

⚠ Üç sayfa reklamsız kalacak ve bu doğru: `gizlilik.html`,
`gizlilik-politikasi.html` (Play Store'a verilen uygulama gizlilik politikaları)
ve `404.html` (içeriksiz sayfa). Bu üçünde AdSense kodu hiç yok, eklenmeyecek.
