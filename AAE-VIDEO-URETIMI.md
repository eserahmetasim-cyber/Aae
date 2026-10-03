# AAE · Video Üretimi — Tek Dosya Bağlam

> Bu dosya, dağınık duran AAE video üretimi işinin tamamını tek yere toplar:
> kanal kimliği, Drive'daki ham/işlenmiş malzeme, bu depodaki otomatik üretim
> hattı ve haftalık raporlar. **Oyun (Motosiklet Yol Okulu) ayrı başlıkta** —
> buraya sadece video tarafı alındı.
>
> Son güncelleme: **3 Ekim 2026** (Drive verileri o gün canlı okundu).

---

## 1. Kanal ve kimlik

| | |
|---|---|
| Kanal / Drive hesabı | `aaemotovlog@gmail.com` |
| Sosyal kullanıcı adı | `@aae_motorcycle` |
| Logo | Mavi daire içinde `AAE` yazısı |
| Format | Dikey **1080×1920** (Reels / TikTok / YouTube Shorts) |
| Marka renkleri | Turuncu `#FF5A1F` · Krem `#F5F0E8` · Zemin `#07090E` · Mavi `#19D3FF` · Kırmızı `#E23B2E` · Yeşil `#2ECC71` |
| Tipografi | Başlık: Arial Black / Impact · Metin: Arial |
| İçerik ekseni | Motovlog + motosiklet sürüş eğitimi (ör. "Yoldaki Tuzak" serisi) |

Alt bant düzeni (üretilen görsellerde yerleşik): sol altta seri adı bandı,
sağ altta AAE amblemi, altta ortada `@aae_motorcycle`.

---

## 2. Google Drive düzeni

| Klasör / konum | ID | İşlevi |
|---|---|---|
| `Hazır olmayanlar` | `148GXoz2IE6IlWz0x0wmjVaqoPQbFdBjU` | Kurgulanmamış ham çekim — **kurgu kuyruğu** |
| `AAE_onay` | `1yqK-9dfskEwB7cQYkwXbfjKcnZmhlLTl` | Render edilmiş, **onay bekleyen** kurgular |
| My Drive kökü | `0ABwDWvq4GFNYUk9PVA` | Buraya düşen klipler kuyruğa taşınmalı |

**Render dosyası isimlendirme kuralı** (`AAE_onay` içinde yerleşmiş):

```
YYYY-MM-DD_HHMM_video_<konu>_v<N>.mp4
örn. 2026-09-05_1100_video_egitim10_birlikte_surus_v1.mp4
```

---

## 3. Güncel durum — 3 Ekim 2026

### 3.1 Kurgu kuyruğu (`Hazır olmayanlar`) — 5 klip · ~613 MB

| Klip | Tür | Boyut | Eklendi | Bekleme |
|---|---|---|---|---|
| [0804.mp4](https://drive.google.com/file/d/1euw79F8530I1gOtTIXcroG0Yw_2ag5pl/view) | sürüş | 224.0 MB | 4 Ağu | 60 gün |
| [804805785…093.MP4](https://drive.google.com/file/d/1kaYzmE0fEvTkGjiSWUDRH1Sp4qGTGrUD/view) | sürüş | 205.3 MB | 6 Ağu | 58 gün |
| [1783454928225.MOV](https://drive.google.com/file/d/1OuJZaImkGUS68KhHVVsQH-TYsmxs2Xm2/view) | sürüş | 72.4 MB | 6 Ağu | 58 gün |
| [motor sehir phonk.mp4](https://drive.google.com/file/d/1UcRVAt_Y2zF48lZ2FQ83mGDTlHQ6Pmis/view) | kurgu / müzik | 61.0 MB | 5 Ağu | 59 gün |
| [ScreenRecording 09-34-20](https://drive.google.com/file/d/1E2Y7syQ3Pu4PSPwYoYD0LcHJx41d6HCt/view) | ekran kaydı | 50.0 MB | 10 Tem | **85 gün** |

### 3.2 21 Eylül'den bu yana ne değişti

- **Kuyruk 9 klipten 5'e düştü: ~468 MB temizlendi.** Giden dosyalar:
  215 MB'lık sürüş klibi (`807778139…354.mp4`) ve üç ekran kaydı (172 / 43 / 38 MB).
  Bu, üst üste üç haftalık "hiç kıpırdamadı" serisini kıran ilk ilerleme —
  ama **28 Eylül'deki haftalık rapor çalışmadığı için hiçbir yere yazılmadı** (bkz. §5).
- Kuyrukta kalan 5 klibin hepsi 45 günü aşmış durumda; en yaşlısı 85 güne çıktı.
- Drive'a **iki haftadan fazladır yeni çekim girmedi** (son sürüş klibi 6 Ağustos).

### 3.3 Bekleyen diğer malzeme

- **`AAE_onay` — 5 render, ~237 MB, 4–5 Eylül'den beri onay bekliyor (~28 gün):**
  `egitim10_birlikte_surus_v1` (112.2 MB) · `gece_dji_hizlanma_v1` (30.8 MB) ·
  `gece_tek_cumle_v2` (45.2 MB) · `cuma_racon_v1` (39.0 MB) · `evli_arkadas_maymun_v1` (9.9 MB)
- **Kökte duran klip:** [“Evde yeğenvar sessiz çıkış”](https://drive.google.com/file/d/1U_7Rs1T1IwKJQhGfHuWsyiuYW1FsNrKt/view)
  — 188 MB, 1 Eylül (32 gün), hâlâ My Drive kökünde, kuyruk klasöründe değil.

---

## 4. Otomatik üretim hattı (bu depo)

Elindeki dikey videoyu "Cuma Mübarek" temalı, paylaşıma hazır MP4'e çeviren ve
isteğe bağlı olarak YouTube'a Short yükleyen hat. Ayrıntılı kullanım: [README.md](README.md).

```
videos/                          → ham video buraya
output/                          → işlenmiş video buraya
assets/                          → fon müziği, logo
scripts/make_friday_video.sh     → ffmpeg render (1080×1920, şeritler, yazı, fade, süre kırpma, fon müziği)
scripts/youtube_upload.py        → YouTube Data API v3 ile yükleme
scripts/get_youtube_token.py     → refresh token alma (tek seferlik, yerelde)
youtube_meta.json                → başlık / açıklama / etiket
requirements-youtube.txt          → Python paketleri
.github/workflows/friday-video.yml → otomatik render + yükleme iş akışı
.gitattributes                   → videos/*.mp4 için Git LFS
```

**Akış:** `videos/`'a video push → Actions tetiklenir → render → `cuma-videosu`
artifact'ı + (secret'lar tanımlıysa) YouTube'a **private** yükleme.
Secret'lar yoksa iş akışı yine çalışır, sadece yükleme adımı atlanır.

**Render parametreleri** (ortam değişkeni / workflow girdisi):
`TOP_TEXT` (varsayılan `Cuma Mubarek`) · `BOTTOM_TEXT` (`Hayirli Cumalar`) ·
`DURATION` (60 sn) · `MUSIC` · `MUSIC_VOL` (0.6) · `privacy` (private).

**Durum:** Kod tarafı bitti ve doğrulandı (commit `146d4ec`; py/yaml/json/bash
sözdizimi kontrolleri geçti). Tek eksik senin yapacağın **tek seferlik yetki adımı**:

1. Google Cloud'da proje + **YouTube Data API v3** → Enable
2. OAuth consent screen: External, test user olarak kanal Gmail'i
3. OAuth client ID → **Desktop app** → `client_secret.json`
4. Yerelde `python scripts/get_youtube_token.py` → izin ver
5. Çıkan 3 değeri depo Secrets'a ekle: `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`

> ⚠️ Büyük dosya sınırı: GitHub web yüklemesi 25 MB, normal `git push` 100 MB.
> Kuyruktaki klipler 50–224 MB → **Git LFS** (zaten `.gitattributes`'ta tanımlı)
> ya da önce ~50–80 MB'a sıkıştırma gerekir.

---

## 5. Haftalık / günlük otomatik raporlar

| Rutin | Takvim | Çıktı | Son çalıştırma |
|---|---|---|---|
| **Edit Bay Monday** (`trig_01TnCG4Cg3tTQJ1VQbMmjN2L`) | Pazartesi 09:00 (UTC+3) | [Edit Bay Monday sayfası](https://claude.ai/artifact/GV76Ez3mGcw9UWMsHGLNF2) — kuyruk sayısı/boyutu, klip yaşları, Drive'a yeni gireni, YouTube haberleri, tek cümlelik dürtü | **28 Eyl — BAŞARISIZ** |
| **Morning brief** (`trig_018XsQ44nX1cntRK46kvgYNE`) | Hafta içi 08:00 (UTC+3) | Günlük brief; içinde **"Trend motosiklet videosu"** bölümü (trend videoyu bul, neden tuttuğunu yaz, AAE'ye uyarlanacak tek açı) | **1 Eki — BAŞARISIZ** |

**⚠️ Dikkat edilmesi gereken:** Her iki rutin de (ve üçüncü, video dışı olan
literatür taraması da) son çalıştırmalarında başarısız oldu — üçü de tetiklendikten
~8–11 saniye sonra `UNSPECIFIED` hatasıyla düştü. Prompt hatası gibi değil, oturum
başlatma / altyapı tarafında duran bir sorun gibi görünüyor. Bu yüzden 28 Eylül
ve sonrasındaki kuyruk hareketi (468 MB'lık temizlik) rapora hiç yansımadı.

### Sektör notu (son rapordan, hâlâ geçerli)
- **1 Şubat 2027**'den itibaren YouTube Partner Program'a **yeni** başvuranlar için
  çubuk ikiye katlanıyor: **8.000 izlenme saati/yıl veya 20M Shorts izlenmesi/90 gün**.
  Programa önceden girenler muaf → **Şubat'tan önce mevcut 4.000 saat barajını
  geçmek** küçük kanal için en yüksek getirili hamle.
- **Hayran desteği 500 abone / 3.000 izlenme saatinde kalıyor** (Super Chat, üyelik,
  Super Thanks) → niş motovlog için yakın vadede gerçekçi olan para kazanma yolu bu.

---

## 6. Açık işler

- [ ] **Onay kuyruğunu boşalt:** `AAE_onay`'daki 5 render 28 gündür bekliyor — yayınla ya da arşivle.
- [ ] **85 günlük ekran kaydını bitir** (50 MB) — kuyruktaki en yaşlı dosya.
- [ ] **Kökteki klibi taşı:** "Evde yeğenvar sessiz çıkış" → `Hazır olmayanlar`.
- [ ] **Yeni çekim:** Drive'a 6 Ağustos'tan beri yeni sürüş klibi girmedi.
- [ ] **YouTube Secrets'ı tamamla** (§4, 5 adım) → hat uçtan uca otomatik çalışsın.
- [ ] **Rutinlerin başarısızlığını çöz** (§5) — raporlar 28 Eylül'den beri üretilmiyor.
- [ ] 4.000 izlenme saati barajı için Şubat 2027 öncesi plan.

---

## 7. Kaynaklar

- Üretim hattı kullanım rehberi: [README.md](README.md)
- Haftalık kurgu raporu: https://claude.ai/artifact/GV76Ez3mGcw9UWMsHGLNF2
- Kurgu kuyruğu (Drive): https://drive.google.com/drive/folders/148GXoz2IE6IlWz0x0wmjVaqoPQbFdBjU
- Onay klasörü (Drive): https://drive.google.com/drive/folders/1yqK-9dfskEwB7cQYkwXbfjKcnZmhlLTl
- Oyun tarafı (**ayrı başlık**): Motosiklet Yol Okulu — https://claude.ai/artifact/GJDuTFnL2YBXvLaR6VfdQd
