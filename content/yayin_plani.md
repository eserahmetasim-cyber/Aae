<!-- URETILMIS DOSYA - elle duzenlemeyin.
     python3 scripts/yayin_sirasi.py --plan-md > content/yayin_plani.md -->
# Yayın planı · her sabah 09:00 (İstanbul)

Üretildi: 19.11.2026 09:36 · kaynak: `content/yayin_kaydi.json` + `content/dersler/`

| Ders | Başlık | YouTube | Instagram | Dosyalar |
|---:|---|---|---|---|
| 01 | Acil Frende Ağırlık Transferi | 20.11.2026 Cum | 20.11.2026 Cum | `library/approved/01-acil-fren/` |
| 02 | Virajda Bakış | 21.11.2026 Cmt | 21.11.2026 Cmt | `library/approved/02-viraj-bakisi/` |
| 03 | Kontra: Motosiklet Nasıl Döner | 22.11.2026 Paz | 22.11.2026 Paz | `library/approved/03-kontra/` |
| 04 | Virajda Gaz: Yavaş Gir, Hızlı Çık | 23.11.2026 Pzt | 23.11.2026 Pzt | `library/approved/04-viraj-gazi/` |
| 05 | Islak Zeminde Sürüş | 24.11.2026 Sal | 24.11.2026 Sal | `library/approved/05-islak-zemin/` |
| 06 | Kör Nokta: Seni Neden Görmüyorlar | 25.11.2026 Car | 25.11.2026 Car | `library/approved/06-kor-nokta/` |
| 07 | Düşük Hızda Manevra | 26.11.2026 Per | 26.11.2026 Per | `library/approved/07-dusuk-hiz-manevra/` |
| 08 | Gece Sürüşü | 27.11.2026 Cum | 27.11.2026 Cum | `library/approved/08-gece-surusu/` |
| 09 | Binmeden Önce: T-CLOCS | 28.11.2026 Cmt | 28.11.2026 Cmt | `library/approved/09-on-kontrol/` |
| 10 | Kaçınma Manevrası | 29.11.2026 Paz | 29.11.2026 Paz | `library/approved/10-kacinma/` |
| 11 | Yolcu ile Sürüş | 30.11.2026 Pzt | 30.11.2026 Pzt | `library/approved/11-yolcu/` |
| 12 | Kavşakta Sola Dönen Araç | 01.12.2026 Sal | 01.12.2026 Sal | `library/approved/12-kavsak/` |
| 13 | Takip Mesafesi: İki Saniye | 02.12.2026 Car | 02.12.2026 Car | `library/approved/13-takip-mesafesi/` |
| 14 | Şerit İçi Konum | 03.12.2026 Per | 03.12.2026 Per | `library/approved/14-serit-ici-konum/` |
| 15 | Sollama | 04.12.2026 Cum | 04.12.2026 Cum | `library/approved/15-sollama/` |
| 16 | Kaygan Yamalar | 05.12.2026 Cmt | 05.12.2026 Cmt | `library/approved/16-kaygan-yamalar/` |
| 17 | Viraja Fazla Hızlı Girdin | 06.12.2026 Paz | 06.12.2026 Paz | `library/approved/17-viraja-hizli-girmek/` |
| 18 | Hız: İki Katı Değil, Dört Katı | 07.12.2026 Pzt | 07.12.2026 Pzt | `library/approved/18-durma-mesafesi/` |
| 19 | Ne Kadar İleri Bakıyorsun? | 08.12.2026 Sal | 08.12.2026 Sal | `library/approved/19-ne-kadar-ileri-bakiyorsun/` |
| 20 | Eğim: Yokuş Aşağı, Yokuş Yukarı | 09.12.2026 Car | 09.12.2026 Car | `library/approved/20-egim/` |
| 21 | Yan Rüzgâr ve TIR | 10.12.2026 Per | 10.12.2026 Per | `library/approved/21-yan-ruzgar/` |
| 22 | Motosikleti Yüklemek | 11.12.2026 Cum | 11.12.2026 Cum | `library/approved/22-yuk/` |
| 23 | Tutuş Dairesi | 12.12.2026 Cmt | 12.12.2026 Cmt | `library/approved/23-tutus/` |

**YouTube**: `gunluk-yayin.yml` iş akışı otomatik yürütür; video `publishAt` ile 09:00'a programlanır.

**Instagram**: bu tablo Business Suite'ten planlayan oturumun çalışma listesidir. `gunluk-yayin.yml` zamanlanmış çalışmada Instagram'a **yayınlamaz**; iki kez paylaşılmasın diye `IG_USER_ID` ve `IG_ACCESS_TOKEN` secret'ları girilmez.

Bir ders bir platformda yayınlandığında o platformun sütunundan düşer, diğerininkinden düşmez — iki ayrı kuyruk.

Her klasörde video (`<ders>.mp4`) ve `meta.json` var; Instagram açıklaması `meta.json` → `instagram.caption` alanında hazır duruyor, elle yazmaya gerek yok.
