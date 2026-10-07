# AAE · Eğitim Videosu Kuralları

Bu başlık **motosiklet eğitim içeriği video üretimi**. Her ders tek bir dosyadan
(`content/dersler/*.yml`) sürülür; render ve yayın bu kurallara uyar.

## Format
- **1080×1920** dikey (Reels / Shorts), `yuv420p`, H.264 + AAC, `+faststart` (moov başta).
- Süre: **60 sn varsayılan**, üst sınır 90 sn. Instagram Reels ≤ 300 MB, Stories ≤ 100 MB.
- Kare hızı kaynaktan korunur (Instagram 23–60 fps ister).

## Marka
| | |
|---|---|
| Kanal | `aaemotovlog` · `@aae_motorcycle` |
| Seri adı | `MOTOSİKLET YOL OKULU` (üst bantta, turuncu) |
| Turuncu | `#FF5A1F` — vurgular, seri adı, ders numarası |
| Krem | `#F5F0E8` — ana metin |
| Zemin | `#07090E` — açılış/kapanış kartı, bantlar |
| Font | DejaVu Sans Bold (Türkçe karakterler tam) |

## Anlatım düzeni (her ders)
1. **Açılış kartı** (0–2.6 sn): seri adı + ders no + başlık + alt başlık.
2. **Gövde:** ham çekim üzerinde üst bant (ders no + başlık) ve alt bant (`@aae_motorcycle`).
3. **Adımlar:** ekranda zamanlı geçen 3–6 madde (`adimlar:` listesi). Eğitim içeriğinin özü bu.
4. **Kapanış** (son 3 sn): tek cümle çıkarım + takip çağrısı.

## Ses
- Son miks **-14 LUFS**'a normalize edilir (platformların normalize ettiği hedef),
  tepe -1.5 dBTP. Daha kısık bırakırsan platform sesi yükseltirken gürültüyü de yükseltir.
- **Motorun gerçek sesi çok geride kalır** (`kaynak_ses`, varsayılan 0.035), müzik
  üstte (`muzik_ses`, varsayılan 0.36). Oranı sen kurarsın, toplam seviyeyi render oturtur.
- Kaynakta ses yoksa sessiz ses kanalı eklenir — platformlar ses kanalı bekler.
- **Müzik telifi:** yalnızca `scripts/muzik_uret.py` ile üretilmiş parçalar ya da
  hakkı net şekilde temizlenmiş müzik kullanılır. Hazır parça indirip koyma —
  YouTube ve Instagram'da ayrı ayrı iddia yersin.

## Sahne
- Uygun ham çekim yoksa arka plan `sahne:` ile çizilir (`fren` / `viraj`),
  varsayılan **3 boyutlu** (`boyut: 3`).
- **Sahnedeki durum, o anda ekranda yazan adımla aynı şeyi anlatmalı.**
  Viraj sahnesinde `sahne_fazlari` ile hizalanır; aksi halde animasyon
  "KAPANIYOR" derken yazı "açılıyor" diyebiliyor.
- İçerik 300–1400 px bandında durur: üstte ders bandı, altta adım kutuları var.
- **Motosiklet orta çizginin üzerinde gitmez**, sağ şeritte durur. Viraj sahnesinde
  şerit içi konum virajla değişir: sola dönen virajda şeridin sağına, sağa dönende
  soluna kayar — görüşü açan gerçek sürüş tekniği budur.
- **Yatış yönü dönüş yönüyle aynıdır.** 3B motorda `yatis > 0` = SOLA yatış
  (`uc_boyut` yuvarlanma ekseninde ölçülüp kareyle doğrulandı). Sola dönen
  sahnede yatış pozitif, sağa dönende negatif olmalı; HUD'daki "MOTOSİKLET
  SOLA/SAĞA" etiketi de bu işaretten türetilir. Kontra sahnesinde kamera
  motorun **arkasında** durur: önden bakan kamerada sola yatış ekranın sağına
  düşüyor ve yazıyla çelişiyormuş gibi okunuyor.
- **Yatan motosikletin yolu da bükülür.** Yatış varsa yol düz kalamaz; dönüş
  yarıçapı fizikten gelir (`R = v² / (g · tan λ)`) ve yol yatışla aynı yöne
  kıvrılır. Sabit hız seçilirken kadraj gözetilir: çok düşük hız virajı öyle
  sertleştirir ki yol birkaç metrede kadrajdan çıkar.
- **Motosiklet şeritten taşmaz.** "Dışarı taşıyor" gibi hata anlatan fazlarda
  bile kenar çizgisine yanaşılır, çizgi geçilmez — hatayı şerit içinde göster.
- **Kask kapalı (full face) kasktır, küre değil.** Kafa kalıbı "ara oval":
  önden arkaya yanlardan uzun, arkadan bakışta daireden dar ve yüksek. Arkadan
  dört şey okunmalı — yukarı daralan kabuk, tepeye yakın spoiler, altında egzoz
  delikleri, en altta ense rulosu. Önde çene barı öne taşar, vizör açıklığı
  gözleri kapsar.
- **Sürücünün kaskında AAE yazar.** Yazı arkaya ve iki yana, kabuk yüzeyine
  sarılarak konur; düz düzlemde bırakılırsa kaskın siluetinden taşıyor.
  Teğet düzlemin sağ ekseni `cross(bakış, yukarı)` — ters sırada yazı aynalanır.
  Kabuğa oturan koyu yamalar (havalandırma ağzı, vizör çerçevesi) kabuğun
  **dışında** durmalı; içeride bırakılınca ressam sıralaması onları siluet
  kenarına taşıyor.
- **Viraj sahnesi kapalı daire değil.** Yol üç parçalı: düz giriş, yay, düz
  çıkış. "Gazı kademeli aç" adımında viraj biter ve yol düzleşir; motosiklet
  teğet noktasına varmadan doğrulmaya başlar — yol düzken yatık duramaz.
- Kayboluş noktası elle kaydırılmaz; bakış çizgisinin virajın iç yamacını nerede
  kestiğinden **hesaplanır**. Yamaç sahnede sabit durur, ileri geri yürümez.
- Kamera açısı `kamera:` ile seçilir (`yan` / `kask` / `takip` / `degisken`).
- `gunduz: true` uzağı okunur kılar; gece sahnede sis yakında başlar.
- Dışarıdan görüntü alınmaz. Stok klip kullanılacaksa lisansı ticari kullanıma
  ve her iki platforma açık olmalı.

## İsimlendirme
```
output/YYYY-MM-DD_ders<NN>_<slug>_v<N>.mp4
örn. 2026-10-03_ders01_acil-fren_v1.mp4
```

## Yayın kuralları
- **YouTube:** varsayılan `private`. Başlık/açıklamaya `#Shorts` otomatik eklenir.
  Herkese açmak ayrı ve bilinçli bir adım.
- **Instagram:** yayınlanan Reel **anında herkese açıktır** — geri alınamaz.
  `egitim-videosu` iş akışında Instagram **hiçbir zaman kendiliğinden çalışmaz**;
  her seferinde elle seçilir (`yayin: instagram` veya `hepsi`).
- **Günlük yayın bu kuralın bilinçli istisnasıdır.** `gunluk-yayin` iş akışı her
  sabah 10:00'da (Istanbul) sıradaki dersi YouTube'a `public`, Instagram'a Reel
  olarak yayınlar. Tek freni Secret'ların varlığıdır: Secret yoksa o platform
  atlanır ve ders sırada kalır. Durdurmak için iş akışını GitHub Actions'tan
  devre dışı bırak ya da ilgili Secret'ı sil.
- Sıra `content/yayin_kaydi.json` içinde tutulur ve her yayından sonra depoya
  geri yazılır. "En küçük numaralı ders" mantığı her gün aynı videoyu yayınlardı.
- Elle yüklerken: önce YouTube'a private yükle, videoyu orada izle, sonra
  Instagram'a gönder.
- Caption ≤ 2200 karakter, ≤ 30 etiket, ≤ 20 `@` anma.

## Sırlar
Kod içine **hiçbir** anahtar yazılmaz. Hepsi GitHub Secrets:
`YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`, `IG_USER_ID`, `IG_ACCESS_TOKEN`.
`client_secret.json`, `.env` ve token dosyaları `.gitignore`'da.

## Büyük dosyalar
`videos/` altındaki ham çekim **Git LFS** ile takip edilir (`.gitattributes`).
GitHub web yüklemesi 25 MB, normal `git push` 100 MB sınırlıdır.
