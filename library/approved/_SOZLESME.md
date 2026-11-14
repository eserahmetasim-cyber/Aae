# Onaylı kütüphane — iki oturum arasındaki devir sözleşmesi

Bu klasör **üretim** ile **paylaşım** arasındaki tek devir noktasıdır.

| Taraf | Rol |
|---|---|
| **Kanka AAE video üretimi** (bu depo, `claude/kanka-aae-video-uretimi-yccuq1`) | Ders üretir, onaylar, buraya koyar, push eder. |
| **Onaylanmış dersleri sosyal medyada paylaş** | Buradan okur, YouTube ve Instagram'a paylaşır, sonucu geri yazar. |

## Neden depoda, `D:\IcerikFabrikasi` içinde değil

İki oturum ayrı makinelerde çalışıyor. Üretim tarafı Linux bir bulut
konteynerinde; oradan Windows'taki `D:\` sürücüsü görünmüyor. Depo ikisinin de
gördüğü tek ortak zemin, bu yüzden devir buradan yapılıyor.

Yerelde `D:\IcerikFabrikasi\library\approved\` altında istiyorsan, paylaşım
tarafı depoyu çektikten sonra aynalasın:

```powershell
robocopy ".\library\approved" "D:\IcerikFabrikasi\library\approved" /MIR
```

## Yapı

```
library/approved/
  index.json                      tüm onaylı dersler — önce buna bak
  01-acil-fren/
    01-acil-fren.mp4              yayına hazır video (1080x1920, 55 sn, -14 LUFS)
    meta.json                     bu dersin her şeyi
  02-viraj-bakisi/
  ...
```

## `index.json`

Paylaşım tarafı yeni onay var mı diye **sadece bu dosyaya** bakar:

```json
{
  "guncelleme": "2026-10-08T...",
  "dersler": [
    {
      "klasor": "01-acil-fren",
      "ders_no": 1,
      "baslik": "Acil Frende Ağırlık Transferi",
      "video": "library/approved/01-acil-fren/01-acil-fren.mp4",
      "meta":  "library/approved/01-acil-fren/meta.json",
      "onay_tarihi": "2026-10-08T...",
      "durum": "onaylandi"
    }
  ]
}
```

## `meta.json`

Paylaşım için gereken her şey burada — başka hiçbir dosyayı okumana gerek yok:

- `baslik`, `alt_baslik`, `seri`, `handle`
- `video`, `genislik`, `yukseklik`, `sure_sn`
- `youtube`: `baslik`, `aciklama` (zaman damgalı), `etiketler`, `kategori`, `gizlilik`
- `instagram`: `caption` (hashtag'ler dahil), `feed_de_paylas`
- `adimlar`: videodaki zamanlı adımlar (altyazı/alt metin üretmek istersen)

## Kurallar

1. **Paylaşım tarafı bu klasörü değiştirmez.** Yalnız okur. Üretim tarafının
   alanı burası.
2. **Yayın sonucu `content/yayin_kaydi.json`'a yazılır**, buraya değil.
   `scripts/yayin_sirasi.py --isaretle <ders> --youtube <id> --instagram <id>`
3. **Instagram Reel yayınlandığı anda herkese açıktır ve geri alınamaz.**
   Önce YouTube, sonra Instagram.
4. Videolar Git LFS ile tutulur (`.gitattributes`). Klonlarken `git lfs pull`.
5. Bir ders yeniden üretilirse üretim tarafı aynı klasörü günceller ve
   `onay_tarihi` yenilenir — paylaşım tarafı bunu "değişti" sinyali sayar.

## Üretim tarafı nasıl ekler

```bash
bash scripts/make_training_video.sh content/dersler/05-xxx.yml
python3 scripts/onayla.py content/dersler/05-xxx.yml
git add library/approved && git commit && git push
```
