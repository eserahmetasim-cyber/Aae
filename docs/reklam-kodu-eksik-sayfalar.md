# Reklam kodu eksik sayfalar — dağıtım yaması

> Ölçüm tarihi: **25.11.2026**. Canlı sitenin `sitemap.xml`'indeki **88 sayfanın
> tamamı** tek tek çekilip `adsbygoogle` ve `ca-pub-` araması yapıldı.
>
> Sonuç: **86 sayfada** reklam kodu var ve hepsinde doğru yayıncı kimliği
> (`ca-pub-7223494011776010`) geçiyor. Canlı sitede eski yayıncı kimliği
> **hiç yok**. İki sayfada kod yok; bu not o iki sayfa için.

⚠ Bu bir **dağıtım** işi, panelden yapılmaz. Site kaynağı `Aae` deposunda
**değil** — yalnız `C:\SAE-yukleme` klasöründe. Yama orada uygulanır, sonra
zip'lenip Cloudflare Pages'e yüklenir (reçete: `docs/saemuhendislik-sitesi.md`
§4 "Dağıtım reçetesi").

⚠ Reklam onayı gelmeden bu yamanın görünür etkisi olmaz (site 22.11'de
reddedildi). Yani **acil değil** — onay geldiğinde yapılacak işler listesinde
dursun, ayrı bir dağıtım için site riske atılmasın.

---

## 1. `/kesim-plani/` — EKLENMELİ

| | |
|---|---|
| Durum | HTTP 200, **2341 kelime** |
| Reklam kodu | **YOK** |
| Değerlendirme | Sitenin en uzun sayfalarından biri; reklamsız duruyor. Gerçek kayıp. |

**Yapılacak:** diğer içerik sayfalarıyla **aynı** AdSense parçacığı `<head>`
içine eklenecek:

```html
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7223494011776010" crossorigin="anonymous"></script>
```

Kendi başına yazma — `C:\SAE-yukleme` içindeki çalışan bir içerik sayfasından
(örn. `triboloji`) satırı **kopyala**, böylece biçim ve konum birebir aynı olur.

**Not:** adresin sonunda bölü var (`/kesim-plani/`), diğer sayfalarda yok. Yani
bu sayfa klasör içinde bir `index.html` olabilir. Dosyayı bulurken buna dikkat.

## 2. `/cerez-politikasi` — EKLENMESİN (öneri)

| | |
|---|---|
| Durum | HTTP 200, 473 kelime |
| Reklam kodu | YOK |
| Öneri | **Böyle kalsın** |

Gerekçe: bu sitenin kendi çerez/gizlilik politikası sayfası. Zaten üç politika
sayfası (`gizlilik.html`, `gizlilik-politikasi.html`, `404.html`) bilinçli
olarak reklamsız. Bunu da reklamsız bırakmak tutarlı olur ve 473 kelimelik bir
politika metninden kayda değer gelir gelmez.

⚠ Ayrıca bu sayfa AdSense'in AB rıza mesajında **gizlilik URL'si** olarak
kayıtlı (`https://saemuhendislik.com/cerez-politikasi`). Dokunmak gerekirse
oradaki kaydın da bozulmadığı doğrulanmalı.

---

## Dağıtımdan sonra doğrulama

```
curl -sL https://saemuhendislik.com/kesim-plani/ | grep -c adsbygoogle    # 1 olmalı
curl -sL https://saemuhendislik.com/kesim-plani/ | grep -o 'ca-pub-[0-9]*' # 7223494011776010
```

Ve dağıtım reçetesinin zorunlu kontrolü unutulmasın: `/`, `/hasar`, `/en/`,
`/cerez-politikasi`, `/sitemap.xml`, `/ads.txt` → hepsi 200.

⛔ Dağıtımda korunacaklar: `gizlilik.html`, `gizlilik-politikasi.html`,
`404.html` reklamsız kalır; `google19071191ddf4150f.html` silinmez (Search
Console sahiplik doğrulaması); link/canonical/sitemap'te `.html` yazılmaz.
