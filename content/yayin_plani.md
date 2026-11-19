<!-- URETILMIS DOSYA - elle duzenlemeyin.
     python3 scripts/yayin_sirasi.py --plan-md > content/yayin_plani.md -->
# Yayın planı · her gün 10:00 ve 14:00 (İstanbul)

Üretildi: 19.11.2026 14:14 · kaynak: `content/yayin_kaydi.json` + `content/dersler/`

| Ders | Başlık | YouTube | Instagram | Dosyalar |
|---:|---|---|---|---|
| 01 | Acil Frende Ağırlık Transferi | 20.11.2026 Cum 10:00 | 20.11.2026 Cum 10:00 | `library/approved/01-acil-fren/` |
| 02 | Virajda Bakış | 20.11.2026 Cum 14:00 | 20.11.2026 Cum 14:00 | `library/approved/02-viraj-bakisi/` |
| 03 | Kontra: Motosiklet Nasıl Döner | 21.11.2026 Cmt 10:00 | 21.11.2026 Cmt 10:00 | `library/approved/03-kontra/` |
| 04 | Virajda Gaz: Yavaş Gir, Hızlı Çık | 21.11.2026 Cmt 14:00 | 21.11.2026 Cmt 14:00 | `library/approved/04-viraj-gazi/` |
| 05 | Islak Zeminde Sürüş | 22.11.2026 Paz 10:00 | 22.11.2026 Paz 10:00 | `library/approved/05-islak-zemin/` |
| 06 | Kör Nokta: Seni Neden Görmüyorlar | 22.11.2026 Paz 14:00 | 22.11.2026 Paz 14:00 | `library/approved/06-kor-nokta/` |
| 07 | Düşük Hızda Manevra | 23.11.2026 Pzt 10:00 | 23.11.2026 Pzt 10:00 | `library/approved/07-dusuk-hiz-manevra/` |
| 08 | Gece Sürüşü | 23.11.2026 Pzt 14:00 | 23.11.2026 Pzt 14:00 | `library/approved/08-gece-surusu/` |
| 09 | Binmeden Önce: T-CLOCS | 24.11.2026 Sal 10:00 | 24.11.2026 Sal 10:00 | `library/approved/09-on-kontrol/` |
| 10 | Kaçınma Manevrası | 24.11.2026 Sal 14:00 | 24.11.2026 Sal 14:00 | `library/approved/10-kacinma/` |
| 11 | Yolcu ile Sürüş | 25.11.2026 Car 10:00 | 25.11.2026 Car 10:00 | `library/approved/11-yolcu/` |
| 12 | Kavşakta Sola Dönen Araç | 25.11.2026 Car 14:00 | 25.11.2026 Car 14:00 | `library/approved/12-kavsak/` |
| 13 | Takip Mesafesi: İki Saniye | 26.11.2026 Per 10:00 | 26.11.2026 Per 10:00 | `library/approved/13-takip-mesafesi/` |
| 14 | Şerit İçi Konum | 26.11.2026 Per 14:00 | 26.11.2026 Per 14:00 | `library/approved/14-serit-ici-konum/` |
| 15 | Sollama | 27.11.2026 Cum 10:00 | 27.11.2026 Cum 10:00 | `library/approved/15-sollama/` |
| 16 | Kaygan Yamalar | 27.11.2026 Cum 14:00 | 27.11.2026 Cum 14:00 | `library/approved/16-kaygan-yamalar/` |
| 17 | Viraja Fazla Hızlı Girdin | 28.11.2026 Cmt 10:00 | 28.11.2026 Cmt 10:00 | `library/approved/17-viraja-hizli-girmek/` |
| 18 | Hız: İki Katı Değil, Dört Katı | 28.11.2026 Cmt 14:00 | 28.11.2026 Cmt 14:00 | `library/approved/18-durma-mesafesi/` |
| 19 | Ne Kadar İleri Bakıyorsun? | 29.11.2026 Paz 10:00 | 29.11.2026 Paz 10:00 | `library/approved/19-ne-kadar-ileri-bakiyorsun/` |
| 20 | Eğim: Yokuş Aşağı, Yokuş Yukarı | 29.11.2026 Paz 14:00 | 29.11.2026 Paz 14:00 | `library/approved/20-egim/` |
| 21 | Yan Rüzgâr ve TIR | 30.11.2026 Pzt 10:00 | 30.11.2026 Pzt 10:00 | `library/approved/21-yan-ruzgar/` |
| 22 | Motosikleti Yüklemek | 30.11.2026 Pzt 14:00 | 30.11.2026 Pzt 14:00 | `library/approved/22-yuk/` |
| 23 | Tutuş Dairesi | 01.12.2026 Sal 10:00 | 01.12.2026 Sal 10:00 | `library/approved/23-tutus/` |

**YouTube**: `gunluk-yayin.yml` iş akışı otomatik yürütür. Günde 2 çalışma var; her biri videoyu `publishAt` ile kendi saatine (10:00 ve 14:00) programlar, yani cron gecikse bile video tam saatinde açılır.

**Instagram**: bu tablo Business Suite'ten planlayan oturumun çalışma listesidir. `gunluk-yayin.yml` zamanlanmış çalışmada Instagram'a **yayınlamaz**; iki kez paylaşılmasın diye `IG_USER_ID` ve `IG_ACCESS_TOKEN` secret'ları girilmez.

Bir ders bir platformda yayınlandığında o platformun sütunundan düşer, diğerininkinden düşmez — iki ayrı kuyruk.

Her klasörde video (`<ders>.mp4`) ve `meta.json` var; Instagram açıklaması `meta.json` → `instagram.caption` alanında hazır duruyor, elle yazmaya gerek yok.
