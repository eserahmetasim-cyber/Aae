# main dalını kurma promptu

> Yeni bir Claude Code oturumuna (bulut ya da yerel, `eserahmetasim-cyber/Aae`
> deposunda) aşağıdaki çizgiler arasını yapıştır.

---

`eserahmetasim-cyber/Aae` deposunda `main` dalını kur ve çalışmayı oraya taşı.

## Önce durumu bil (07.10.2026 itibarıyla doğrulandı)

- **`main` dalı YOK.** Deponun varsayılan dalı `claude/friday-video-prep-vbqyxy`
  (commit `146d4ec`). Üç dal var, hepsi bu commit'ten ayrılıyor:
  - `claude/friday-video-prep-vbqyxy` — **varsayılan dal**, ortak ata, video altyapısı
  - `claude/amazing-knuth-iv3906` — 11 commit, **yalnızca `docs/` altına** 5 dosya
    ekliyor (saemuhendislik.com sistem bilgisi, günlük durum dosyası, iş emirleri)
  - `claude/kanka-aae-video-uretimi-yccuq1` — 19 commit, `scripts/`, `.github/`,
    `content/`, `assets/`, `README.md`, `KURALLAR.md` değiştiriyor
- **İki özellik dalı hiç aynı dosyaya dokunmuyor → çakışma beklenmiyor.**
- ⚠ `claude/kanka-aae-video-uretimi-yccuq1` dalında **başka bir Claude oturumu hâlâ
  çalışıyor** (son durumu: `gunluk-yayin.yml` için push izni bekliyordu). Yani o
  dalın başı hareket edebilir.

## Yap

**1. `main`'i oluştur.** `claude/amazing-knuth-iv3906` zaten varsayılan dalın tüm
geçmişini içeriyor, o yüzden en temiz yol onun üzerinden gitmek:

```bash
git fetch origin
git checkout -B main origin/claude/amazing-knuth-iv3906
git push -u origin main
```

**2. Video çalışmasını da `main`'e al.** Çakışma yok, ama o dal hâlâ aktif —
birleştirmeden önce son hâlini çek:

```bash
git fetch origin claude/kanka-aae-video-uretimi-yccuq1
git merge --no-ff origin/claude/kanka-aae-video-uretimi-yccuq1 \
  -m "Video uretim hattini main'e al"
git push origin main
```

Beklenmedik bir çakışma çıkarsa **kendi başına çözmeye kalkışma** — hangi
dosyalarda olduğunu bildir ve dur; o dalda çalışan oturum var, onun işini ezme.

**3. `main`'i varsayılan dal yap.** Bu bir depo ayarı:
GitHub → repo → **Settings → General → Default branch** → `main` olarak değiştir.
(Komut satırından: `gh repo edit eserahmetasim-cyber/Aae --default-branch main`
— `gh` yoksa ya da yetki vermezse ayarı elle değiştir, zorlamaya çalışma.)

**4. Eski dalları SİLME.** Özellikle `claude/friday-video-prep-vbqyxy` şu an
varsayılan dal; varsayılan `main` olarak değişmeden silinemez. Ayrıca iki
oturum hâlâ kendi dallarına push ediyor. Silme kararını sahibine bırak.

## Doğrulama

```bash
git ls-remote --symref origin HEAD          # ref: refs/heads/main olmali
git log --oneline -5 main
git diff --stat origin/claude/amazing-knuth-iv3906..main
git diff --stat origin/claude/kanka-aae-video-uretimi-yccuq1..main
```

Son iki komut boş dönerse (ya da yalnızca birleştirme commit'ini gösterirse) her
iki dalın içeriği `main`'de demektir. Ayrıca şu dosyaların `main`'de bulunduğunu
teyit et:

- `docs/saemuhendislik-sitesi.md`
- `docs/gunluk-durum.json`
- `docs/yerel-oturum-is-emri.md`
- `docs/play-destek-mesaji.md`
- `docs/chrome-adsense-yapistir.md`
- `scripts/lesson.py`, `content/dersler/01-acil-fren.yml`,
  `.github/workflows/egitim-videosu.yml`

## Kurallar

- `git push --force` kullanma.
- Başkasının dalında geçmişi yeniden yazma (rebase/amend/force-push yok).
- Pull request isteyen bir akış yoksa PR açma; doğrudan `main`'e push et.
- İşin sonunda tek paragrafla özetle: `main` hangi commit'te, hangi dallar
  birleştirildi, varsayılan dal değişti mi, silinen bir şey var mı (olmamalı).
