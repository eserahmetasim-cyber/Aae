<!-- URETILMIS DOSYA - elle duzenlemeyin.
     python3 scripts/yayin_sirasi.py --plan-md > content/yayin_plani.md -->
# Yayın planı · her gün 10:00 ve 14:00 (İstanbul)

Üretildi: 26.11.2026 09:36 · kaynak: `content/yayin_kaydi.json` + `content/dersler/`

| Ders | Başlık | YouTube | Instagram | Dosyalar |
|---:|---|---|---|---|
| 01 | Acil Frende Ağırlık Transferi | — *(yayınlandı)* | 26.11.2026 Per 10:00 | `library/approved/01-acil-fren/` |
| 02 | Virajda Bakış | 26.11.2026 Per 10:00 | 26.11.2026 Per 14:00 | `library/approved/02-viraj-bakisi/` |
| 03 | Kontra: Motosiklet Nasıl Döner | 26.11.2026 Per 14:00 | 27.11.2026 Cum 10:00 | `library/approved/03-kontra/` |
| 04 | Virajda Gaz: Yavaş Gir, Hızlı Çık | 27.11.2026 Cum 10:00 | 27.11.2026 Cum 14:00 | `library/approved/04-viraj-gazi/` |
| 05 | Islak Zeminde Sürüş | 27.11.2026 Cum 14:00 | 28.11.2026 Cmt 10:00 | `library/approved/05-islak-zemin/` |
| 06 | Kör Nokta: Seni Neden Görmüyorlar | 28.11.2026 Cmt 10:00 | 28.11.2026 Cmt 14:00 | `library/approved/06-kor-nokta/` |
| 07 | Düşük Hızda Manevra | 28.11.2026 Cmt 14:00 | 29.11.2026 Paz 10:00 | `library/approved/07-dusuk-hiz-manevra/` |
| 08 | Gece Sürüşü | 29.11.2026 Paz 10:00 | 29.11.2026 Paz 14:00 | `library/approved/08-gece-surusu/` |
| 09 | Binmeden Önce: T-CLOCS | 29.11.2026 Paz 14:00 | 30.11.2026 Pzt 10:00 | `library/approved/09-on-kontrol/` |
| 10 | Kaçınma Manevrası | 30.11.2026 Pzt 10:00 | 30.11.2026 Pzt 14:00 | `library/approved/10-kacinma/` |
| 11 | Yolcu ile Sürüş | 30.11.2026 Pzt 14:00 | 01.12.2026 Sal 10:00 | `library/approved/11-yolcu/` |
| 12 | Kavşakta Sola Dönen Araç | 01.12.2026 Sal 10:00 | 01.12.2026 Sal 14:00 | `library/approved/12-kavsak/` |
| 13 | Takip Mesafesi: İki Saniye | 01.12.2026 Sal 14:00 | 02.12.2026 Car 10:00 | `library/approved/13-takip-mesafesi/` |
| 14 | Şerit İçi Konum | 02.12.2026 Car 10:00 | 02.12.2026 Car 14:00 | `library/approved/14-serit-ici-konum/` |
| 15 | Sollama | 02.12.2026 Car 14:00 | 03.12.2026 Per 10:00 | `library/approved/15-sollama/` |
| 16 | Kaygan Yamalar | 03.12.2026 Per 10:00 | 03.12.2026 Per 14:00 | `library/approved/16-kaygan-yamalar/` |
| 17 | Viraja Fazla Hızlı Girdin | 03.12.2026 Per 14:00 | 04.12.2026 Cum 10:00 | `library/approved/17-viraja-hizli-girmek/` |
| 18 | Hız: İki Katı Değil, Dört Katı | 04.12.2026 Cum 10:00 | 04.12.2026 Cum 14:00 | `library/approved/18-durma-mesafesi/` |
| 19 | Ne Kadar İleri Bakıyorsun? | 04.12.2026 Cum 14:00 | 05.12.2026 Cmt 10:00 | `library/approved/19-ne-kadar-ileri-bakiyorsun/` |
| 20 | Eğim: Yokuş Aşağı, Yokuş Yukarı | 05.12.2026 Cmt 10:00 | 05.12.2026 Cmt 14:00 | `library/approved/20-egim/` |
| 21 | Yan Rüzgâr ve TIR | 05.12.2026 Cmt 14:00 | 06.12.2026 Paz 10:00 | `library/approved/21-yan-ruzgar/` |
| 22 | Motosikleti Yüklemek | 06.12.2026 Paz 10:00 | 06.12.2026 Paz 14:00 | `library/approved/22-yuk/` |
| 23 | Tutuş Dairesi | 06.12.2026 Paz 14:00 | 07.12.2026 Pzt 10:00 | `library/approved/23-tutus/` |
| 24 | Kamber: Virajın Yana Eğimi | 07.12.2026 Pzt 10:00 | 07.12.2026 Pzt 14:00 | `library/approved/24-kamber/` |
| 25 | Virajın Çizgisi | 07.12.2026 Pzt 14:00 | 08.12.2026 Sal 10:00 | `library/approved/25-cizgi/` |
| 26 | Kör Virajda Görüş | 08.12.2026 Sal 10:00 | 08.12.2026 Sal 14:00 | `library/approved/26-gorus/` |

**YouTube**: `gunluk-yayin.yml` iş akışı otomatik yürütür. Günde 2 çalışma var; her biri videoyu `publishAt` ile kendi saatine (10:00 ve 14:00) programlar, yani cron gecikse bile video tam saatinde açılır.

**Saat garanti, tarih değil.** GitHub zamanlanmış işleri saatlerce geciktirebiliyor; `publishAt` "bir sonraki" 10:00 ya da 14:00'ı hedeflediği için çalışma geç başlarsa ders ertesi güne düşer. Sıra bozulmaz, takvim bir gün kayabilir. Gerçekte ne yayınlandı: `content/yayin_kaydi.json`.

**Instagram**: bu tablo Business Suite'ten planlayan oturumun çalışma listesidir. `gunluk-yayin.yml` zamanlanmış çalışmada Instagram'a **yayınlamaz**; iki kez paylaşılmasın diye `IG_USER_ID` ve `IG_ACCESS_TOKEN` secret'ları girilmez.

Bir ders bir platformda yayınlandığında o platformun sütunundan düşer, diğerininkinden düşmez — iki ayrı kuyruk.

Her klasörde video (`<ders>.mp4`) ve `meta.json` var; Instagram açıklaması `meta.json` → `instagram.caption` alanında hazır duruyor, elle yazmaya gerek yok.
