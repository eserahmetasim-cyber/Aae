# Yol Okulu'nu ana sayfaya ekleme yaması

> Hazırlandı: **07.11.2026**. Canlı sayfanın kendi markup'ından çıkarıldı,
> kart metni oyunun **Play mağaza açıklamasından** alındı (uydurulmadı).
>
> ⚠ Bu değişiklik **dağıtım gerektiriyor** ve dağıtım yalnızca AAE'nin
> bilgisayarından yapılabiliyor (`C:\SAE-yukleme` → Cloudflare Pages). Bulut
> oturumu site dosyalarına erişemiyor.

## Neden

AAE Motosiklet Yol Okulu (`com.saemuhendislik.yol_okulu_3b`) **Google Play'de
yayında** — 06.11'de anonim olarak doğrulandı, mağaza sayfası 200 dönüyor. Ama
sitede hiç geçmiyor: ana sayfadaki uygulama bandında yalnızca Mini Mühendis var.

Bandın kabı zaten `grid grid-2`, yani **ikinci kart için tasarlanmış**; şu anda
yarısı boş duruyor. Yama tam olarak o boşluğu dolduruyor.

---

## 0. Önce ikon dosyası

Sitede Yol Okulu ikonu **yok** (`images/yol-okulu-ikon.png` → 404).

- Oyunun ikonunu **`C:\SAE-yukleme\images\yol-okulu-ikon.png`** olarak kaydet.
- Mini Mühendis ikonuyla aynı ölçüde kare PNG olsun (`images/mini-muhendis-ikon.png`
  örnek alınabilir).
- İkon Play Console'daki uygulama varlıklarında zaten var.

---

## 1. TR — `index.html`

`<section class="section" id="uygulamalar">` içinde.

### 1a. Giriş cümlesini değiştir

**BUL:**
```html
      <p>SAE Mühendislik'in kendi geliştirdiği mobil uygulamalar. Mini Mühendis Google Play'de yayında.</p>
```

**YERİNE:**
```html
      <p>SAE Mühendislik'in kendi geliştirdiği mobil uygulamalar. İkisi de Google Play'de yayında.</p>
```

### 1b. İkinci kartı ekle

Mini Mühendis kartının kapanışından hemen sonra, `</div>` ile `</div>` arasına.

**BUL** (Mini Mühendis kartının sonu):
```html
          <a class="app-live" href="https://play.google.com/store/apps/details?id=com.saemuhendislik.mini_muhendis" target="_blank" rel="noopener">GOOGLE PLAY'DE &#8594;</a>
        </div>
      </div>
```

**YERİNE** (aynı satırlar + yeni kart):
```html
          <a class="app-live" href="https://play.google.com/store/apps/details?id=com.saemuhendislik.mini_muhendis" target="_blank" rel="noopener">GOOGLE PLAY'DE &#8594;</a>
        </div>
      </div>
      <div class="app-row">
        <img src="images/yol-okulu-ikon.png" alt="AAE Motosiklet Yol Okulu — motosiklet sürüş eğitimi oyunu">
        <div>
          <h3>AAE Motosiklet Yol Okulu</h3>
          <p>Motosiklet süren ya da sürmeye hazırlanan herkes için karar oyunu: ıslak yolda takip mesafesi, tırın arkasında görüş, tünele giriş, dönel kavşakta öncelik. Üç saniyede karar ver, sonucu gerçek fren mesafesiyle izle.</p>
          <a class="app-live" href="https://play.google.com/store/apps/details?id=com.saemuhendislik.yol_okulu_3b" target="_blank" rel="noopener">GOOGLE PLAY'DE &#8594;</a>
        </div>
      </div>
```

---

## 2. EN — `en/index.html`

`<section class="section" id="apps">` içinde. **Görsel yolu `../images/`** (sayfa
`/en/` altında) — bunu atlama.

### 2a. Giriş cümlesini değiştir

**BUL:**
```html
      <p>Mobile apps developed by SAE Engineering. Mini M&uuml;hendis is live on Google Play.</p>
```

**YERİNE:**
```html
      <p>Mobile apps developed by SAE Engineering. Both are live on Google Play.</p>
```

### 2b. İkinci kartı ekle

**BUL:**
```html
          <a class="app-live" href="https://play.google.com/store/apps/details?id=com.saemuhendislik.mini_muhendis" target="_blank" rel="noopener">GET IT ON GOOGLE PLAY &#8594;</a>
        </div>
      </div>
```

**YERİNE:**
```html
          <a class="app-live" href="https://play.google.com/store/apps/details?id=com.saemuhendislik.mini_muhendis" target="_blank" rel="noopener">GET IT ON GOOGLE PLAY &#8594;</a>
        </div>
      </div>
      <div class="app-row">
        <img src="../images/yol-okulu-ikon.png" alt="AAE Motorcycle Road School — motorcycle riding training game">
        <div>
          <h3>AAE Motorcycle Road School</h3>
          <p>A decision game for anyone who rides a motorcycle or is preparing to: following distance on wet roads, visibility behind a truck, entering a tunnel, priority at a roundabout. Decide in three seconds and watch the outcome play out with real braking distances. (Turkish, English and Spanish)</p>
          <a class="app-live" href="https://play.google.com/store/apps/details?id=com.saemuhendislik.yol_okulu_3b" target="_blank" rel="noopener">GET IT ON GOOGLE PLAY &#8594;</a>
        </div>
      </div>
```

---

## 3. Dağıtım

1. Değişiklikler **`C:\SAE-yukleme`** içine (tek kaynak; OneDrive klasöründen
   dağıtım yapma). Türkçe metin düzenlemede **PowerShell `-replace` kullanma**,
   Python + UTF-8 kullan — aksi halde Türkçe karakterler bozulur.
2. **.NET ZipFile** ile zip'le, girdi adları **düz bölü** olsun.
   `Compress-Archive` KULLANMA (ters bölü yazıp bozuyor).
3. Cloudflare dash → `pages/view/saemuhendislik/deployments/new` → zip'i yükle →
   **"N/N files uploaded"** bekle → **Save and deploy** → **"Success!"**.

## 4. Doğrulama

Dağıtımdan sonra bana haber ver, buradan ölçeceğim:

```
curl -sS https://saemuhendislik.com/     | grep -c yol_okulu     → 0'dan büyük
curl -sS https://saemuhendislik.com/en/  | grep -c yol_okulu     → 0'dan büyük
curl -I  https://saemuhendislik.com/images/yol-okulu-ikon.png    → 200
curl -I  https://saemuhendislik.com/ ve /en/                     → 200
```

Günlük kontrol zaten ana sayfada `yol_okulu` arıyor; belirdiği gün kendiliğinden
yakalanır.
