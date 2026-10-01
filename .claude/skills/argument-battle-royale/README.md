# Argument Battle Royale — Claude Code Skill

Skill Claude Code yang menerima **topik atau pertanyaan apa pun** lalu menjalankan turnamen argumen yang dapat diaudit untuk menemukan argumen yang **paling tahan** terhadap pengujian filsafat analitik dan filsafat sains.

> Pemenang adalah argumen yang paling tahan terhadap rubrik pengujian yang diterapkan dalam simulasi ini.

Hasilnya bukan klaim kebenaran mutlak; laporan akhir selalu menyatakan batas ini.

```
TOPIK → PEMETAAN RUANG ARGUMEN → GENERASI 1000 PETARUNG → DEDUPLIKASI → VALIDASI → SEEDING → BRACKET
→ ELIMINASI → DEEP REVIEW → FINAL 4 → SEMIFINAL → FINAL → PEMENANG → FALSIFICATION TEST → LAPORAN AKHIR
```

## Daftar isi

1. [Pemakaian cepat](#pemakaian-cepat)
2. [Parameter](#parameter)
3. [Cara kerja](#cara-kerja)
4. [Animasi Clawd](#animasi-clawd)
5. [Paralelisasi dan fallback](#paralelisasi-dan-fallback)
6. [Checkpoint dan resume](#checkpoint-dan-resume)
7. [Integritas hasil](#integritas-hasil)
8. [Keluaran](#keluaran)
9. [Contoh](#contoh)
10. [CLI engine](#cli-engine)
11. [Pengujian](#pengujian)
12. [Memasang di repository lain](#memasang-di-repository-lain)
13. [Struktur berkas](#struktur-berkas)
14. [Keterbatasan](#keterbatasan)

## Pemakaian cepat

Di Claude Code, dari root repository ini:

```text
/argument-battle-royale "Apakah AI benar-benar memahami bahasa?"
```

Skill juga terpicu oleh permintaan bahasa alami seperti *"adu argumen-argumen tentang apakah moralitas membutuhkan Tuhan"*. Untuk uji cepat:

```text
/argument-battle-royale "Apakah kehendak bebas kompatibel dengan determinisme?" population=32 mode=efficient
```

Lihat [`examples/inputs.md`](examples/inputs.md) untuk contoh lintas domain (filsafat, sains, sosial, politik, teknologi, hukum, ekonomi).

## Parameter

Semua opsional kecuali topik; tulis sebagai `key=value` setelah topik.

| Parameter | Default | Keterangan |
|---|---|---|
| `mode` | `balanced` | `efficient` \| `balanced` \| `full` — lihat [`references/modes.md`](references/modes.md) |
| `population` | `1000` | Jumlah petarung target (8–5000) |
| `deep_round_threshold` | 16 / 32 / 64 (per mode) | Babak dengan slot ≤ nilai ini memakai panel deep review |
| `max_parallel` | `5` | Maksimum worker paralel |
| `random_seed` | turunan hash topik | Alokasi slot, pengacakan X/Y, jangkar kalibrasi, pemecah seri |
| `evidence_mode` | `internal` | `internal` \| `web_if_available` |
| `language` | `id` | Bahasa konten; label laporan tersedia untuk `id` dan `en` |
| `output_dir` | `argument-battle-royale-runs/<slug>-<hash>` | Direktori run |
| `resume` | `true` | Lanjutkan run yang ada; `false` memaksa run baru (`-r2`, `-r3`, …) |

Perkiraan skala kerja (jumlah paket LLM): 1000 petarung ≈ 80 (`efficient`), 180 (`balanced`), 290 (`full`).

## Cara kerja

Skill memisahkan **wasit** dan **juri**:

| Peran | Siapa | Tugas |
|---|---|---|
| Wasit | `scripts/abr.py` (Python standar, tanpa dependensi, tanpa LLM) | State & checkpoint, alokasi petarung, deduplikasi leksikal, kalibrasi skor, seeding, bracket, pengacakan X/Y, agregasi panel, ledger berantai-hash, laporan, verifikasi |
| Orkestrator | Claude (sesi utama) | Menjalankan `next`, membagikan paket ke worker, melaporkan progres |
| Worker | Subagent `battle-royale-worker` / `general-purpose`, atau Claude sendiri | Mengerjakan satu paket: `packet.md` → `output.json`, lalu `check` |

Setiap **paket kerja** mandiri: berisi peran, rubrik, aturan anti-bias, data, format output, dan perintah validasi. Semua keputusan menang/kalah dihitung ulang engine dari skor rubrik juri — bukan dari klaim juri — dengan aturan: (1) lebih sedikit cacat fatal, (2) total tertimbang lebih tinggi, (3) pilihan holistik juri hanya bila seri praktis (< 1 poin).

Tahap-tahap penting:

- **Pemetaan**: posisi (stance), kerangka teoretis, strategi argumentasi, bacaan istilah kunci, titik krusial.
- **Generasi**: kuota setara per posisi (netral), disebar lintas kerangka dan strategi.
- **Deduplikasi**: Jaccard unigram+bigram (otomatis ≥ 0,70) + review semantik LLM untuk kasus perbatasan.
- **Validasi & scouting**: diskualifikasi hanya untuk cacat tertentu; skor rubrik dikalibrasi antar-paket dengan petarung jangkar; refill otomatis bila petarung valid < 90% target.
- **Bracket**: eliminasi tunggal berunggulan; bye untuk unggulan teratas.
- **Eliminasi → deep review**: juri tunggal di babak besar; panel juri berlensa (logikawan, filsuf sains, analis konseptual, …) mulai ambang deep review.
- **Final 4**: dosir per finalis (bentuk baku, kerangka formal, inti keras vs sabuk pelindung Lakatos, keberatan terkuat).
- **Semifinal & final**: debat antar-pembela (serangan → pembelaan → penutup), lalu panel 5–7 juri.
- **Falsifikasi**: juara diuji penguji independen (kontra-contoh, reductio, rival, kasus batas, imunisasi, prediksi empiris); bila `FALSIFIED`, runner-up diuji, dan seterusnya.

Rincian lengkap: [`references/pipeline.md`](references/pipeline.md), rubrik: [`references/rubric.md`](references/rubric.md), struktur data: [`references/data-model.md`](references/data-model.md).

## Animasi Clawd

![Clawd sebagai penyihir, petarung, peluncur roket, dan juara](examples/clawd-preview.gif)

Turnamen besar bisa berjalan lama, jadi progresnya ditemani Clawd. Adegan mengikuti tahap pipeline:

| Tahap | Adegan |
|---|---|
| Pemetaan, generasi, deduplikasi, validasi, seeding | Penyihir: topi, tongkat, dan percikan sihir |
| Eliminasi, deep review, Final 4, semifinal, final | Duel: dua Clawd berhadapan, percikan di tengah |
| Uji falsifikasi | Peluncuran: Clawd menekan tombol, roket lepas landas |
| Selesai | Juara: piala di podium dan konfeti (atau tanda tanya bila tidak ada pemenang tahan-uji) |

Tampilannya menyesuaikan tempat skill dijalankan:

| Tempat | Bentuk | Bergerak? |
|---|---|---|
| Chat (Claude Code maupun Claude.ai) | **Flipbook**: glyph Clawd dari Claude Code plus properti emoji, satu pose per tahap baru, beserta bar progres | Berganti per tahap (output tool Claude Code tidak live) |
| Panel samping aplikasi Claude (artifact), browser, artifact Claude.ai | **Arena pertarungan** (`RUN_DIR/arena.html`): setiap duel diputar sebagai pertarungan pixel art — dua karakter Gobyet sesuai topik masuk, setiap juri "memukul" dengan keberatan argumen yang sebenarnya, bar ketahanan turun sesuai suara juri, Judge mengetuk palu, yang kalah memutar animasi kalah kelasnya, pemenang maju di bracket; plus jalur 15 tahap, statistik, dan kartu pemenang (lihat [Karakter Gobyet di arena](#karakter-gobyet-di-arena)) | Ya: live selama run berjalan, lalu menjadi tayangan ulang |
| Terminal Anda sendiri | **`watch`**: pixel art berwarna dengan karakter setengah-blok, bar progres, jalur tahap | Ya |
| Status line Claude Code (opsional) | Satu baris: Clawd oranye, properti beranimasi, tahap, dan persen | Diperbarui setiap kali percakapan berubah |

### Arena pertarungan live

Arena memutar acara turnamen yang belum Anda tonton: tahap persiapan (penyihir), awal setiap babak, setiap duel (babak besar: tiga duel pilihan — upset terbesar dan duel terketat — plus hitungan cepat sisanya), uji falsifikasi (roket), dan pemenang (piala). Kontrolnya: putar dari awal, jeda, lewati, kecepatan 1×/2×/4×. Hasil bracket dan pemenang baru ditampilkan setelah duelnya ditonton, jadi tayangan ulang tidak spoiler.

"Ketahanan" pada kartu petarung berkurang setiap kali seorang juri memenangkan lawan (porsi suara panel); ini visualisasi suara juri, bukan skor tambahan.

Cara menonton selama run berjalan (Claude memilih sendiri sesuai lingkungannya):

| Lingkungan | Cara | Pembaruan |
|---|---|---|
| Claude Code di aplikasi desktop, web, atau sesi cloud (ada tool `Artifact`) | Claude menerbitkan `arena-artifact.html` sebagai artifact dengan database (`abr.py live`), lalu menulis `arena-live.json` ke database itu setiap ada acara baru | Live di panel samping atau tautan artifact, tanpa memuat ulang |
| Claude Code CLI di komputer Anda sendiri | Claude menjalankan `$ABR serve --run DIR` di latar belakang; buka `http://localhost:8765` di browser Anda | Menarik `arena-data.json` setiap 3 detik tanpa memuat ulang |
| Anda membuka file langsung | buka `DIR/arena.html` di browser | Memuat ulang sendiri saat senggang, melanjutkan dari acara terakhir yang ditonton |
| Chat Claude.ai | Claude menyerahkan arena di akhir run | Tayangan ulang penuh |

### Karakter Gobyet di arena

Arena memakai karakter [Gobyet](https://github.com/kanku-Oiric/Gobyet) (sistem sprite v2). Lapisan ini hanya visual: modul turnamen tidak bergantung padanya, dan hasil turnamen tidak berubah karena karakter.

- **Pemilihan per topik.** `scripts/engine/gobyet.py` memilih karakter tiap petarung dari judul, posisi, dan tesisnya (mis. kata *etika* → Philosopher, *algoritma* → Hacker, *undang-undang* → Lawyer, *ksatria* → Fantasy Knight). Tanpa kecocokan, karakter mengikuti topik; tanpa kecocokan sama sekali, Normal GBLK. Topik dua domain memakai satu karakter primer dan paling banyak satu ikon aksesori (mis. Philosopher + laptop untuk "AI dan kesadaran").
- **Peran tetap.** Referee membuka babak, Judge mengetuk palu saat putusan, Skeptic memimpin uji falsifikasi, Champion memegang piala dengan label "TOURNAMENT WINNER" (pemenang turnamen, bukan kebenaran mutlak). Yang kalah memutar animasi kalah kelasnya sendiri.
- **Teologi.** Hanya kata yang jelas merujuk tradisi tertentu yang memilih Pak Haji atau Priest; kata umum (agama, Tuhan, teologi) memilih Philosopher. Kedua tokoh diperlakukan identik.
- **Fallback.** Karakter atau state yang tidak tersedia turun lewat rantai karakter → basis faksi → Normal GBLK; state → alias inti → idle. Bila seluruh aset Gobyet tidak ada, arena kembali ke sprite Clawd. Tidak pernah tampil gambar rusak.
- **Aset.** `assets/gobyet/` adalah subset yang disalin dari repo Gobyet (`v2/tools/vendor_skill.py`), sama seperti `scripts/engine/gobyet_context.py` dan `gobyet_resolve.py`. Ubah di repo Gobyet lalu salin ulang; jangan edit salinannya.

`localhost` hanya bekerja bila `serve` berjalan di komputer yang sama dengan browser Anda. Panel browser bawaan aplikasi desktop Claude tidak dapat membuka server yang dijalankan Claude, dan localhost sesi cloud tidak dapat dijangkau dari luar; karena itu di aplikasi Claude arena selalu tampil sebagai artifact.

Pil di pojok arena menunjukkan sumbernya: **Live** (terhubung ke run), **Cuplikan** (keadaan saat halaman dibuat, belum terhubung), **Tayangan ulang** (run selesai), **Contoh** (data fiktif).

Riwayat tontonan disimpan di `localStorage` browser per run; tanpa penyimpanan, halaman tetap berjalan tetapi memutar dari awal saat dibuka ulang.

```bash
ABR="python3 .claude/skills/argument-battle-royale/scripts/abr.py"
$ABR live --run DIR           # siapkan arena untuk Artifact live (arena-artifact.html + arena-live.json)
$ABR serve --run DIR          # tonton arena live di http://localhost:8765 (komputer yang sama)
$ABR arena --demo --out arena-demo.html   # turnamen contoh 4 argumen fiktif
$ABR watch --run DIR          # animasi live di terminal lain (Ctrl+C untuk keluar)
$ABR watch --demo             # putar semua adegan tanpa run
$ABR frame --scene battle     # cetak satu frame flipbook
```

`watch` memakai warna 24-bit bila `COLORTERM=truecolor`, selain itu 256 warna (paksa dengan `--colors 256`).

Status line (opsional, di `.claude/settings.json` proyek atau `~/.claude/settings.json`):

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 .claude/skills/argument-battle-royale/scripts/abr.py statusline"
  }
}
```

Status line menampilkan run terbaru di `argument-battle-royale-runs/` pada direktori kerja; tanpa run aktif ia hanya menampilkan Clawd, nama model, dan nama folder.

## Paralelisasi dan fallback

- **Paralel**: bila tool Agent tersedia, orkestrator mengirim hingga `max_parallel` paket sekaligus ke subagent. Worker hanya menulis `output.json` miliknya; hanya orkestrator yang mengubah state (dengan kunci file), sehingga paralelisme aman.
- **Sekuensial**: tanpa subagent, Claude mengerjakan paket satu per satu dengan standar yang sama. Contoh run di repository ini dibuat lewat jalur ini.

## Checkpoint dan resume

Setiap langkah ditulis atomik ke disk (`state.json`, file ronde, output paket). Bila sesi terputus atau konteks dipadatkan, jalankan ulang perintah yang sama (`resume=true` adalah default) atau `abr.py next --run DIR`. `next` bersifat idempoten: ia menyerap output yang sudah ada dan melanjutkan dari titik terakhir.

## Integritas hasil

`abr.py verify --run DIR` menjalankan 11 pemeriksaan: rantai hash ledger, output paket tidak berubah sejak diserap, populasi terkunci sejak seeding, seeding & bracket dihitung ulang, setiap putusan juri & panel dihitung ulang dari skor mentah, file ronde cocok dengan ledger, juara = pemenang final, agregasi falsifikasi, konsistensi hitungan populasi, dan konsistensi laporan (termasuk formula pemenang). Mengubah satu hasil duel secara manual langsung terdeteksi (diuji di `selftest.py`).

## Keluaran

| File | Isi |
|---|---|
| `report.md` | Laporan akhir: formula pemenang, ringkasan, parameter, peta ruang argumen, statistik populasi, seeding, perjalanan bracket, ketahanan posisi per babak, diagram bracket (Mermaid), Final 4, semifinal & final (suara panel, alasan mayoritas, dissent), argumen pemenang dalam bentuk baku, uji falsifikasi, peringkat akhir, dinamika turnamen, keterbatasan, integritas, reproduksi |
| `report.json` | Ringkasan terstruktur untuk dipakai program lain |
| `arena.html`, `arena-data.json`, `arena-live.json` | Arena pertarungan beranimasi dan datanya untuk penonton live (server lokal atau database artifact); diperbarui setiap `next` |
| `arena-artifact.html` | Halaman arena tanpa kerangka dokumen untuk diterbitkan sebagai Artifact (`abr.py live`) |
| `integrity.json` | Hasil verifikasi dan digest run |
| `fighters.jsonl`, `population.json`, `rounds/`, `dossiers.json`, `ledger.jsonl`, `packets/` | Data mentah yang dapat diaudit |

## Contoh

- [`examples/inputs.md`](examples/inputs.md) — contoh pemanggilan lintas domain dan kombinasi parameter.
- [`examples/sample-run/`](examples/sample-run/) — run nyata lengkap untuk *"Apakah AI bisa disebut memahami bahasa?"* (16 petarung, `balanced`, `deep_round_threshold=8`) yang melewati semua tahap; baca [`examples/sample-run/report.md`](examples/sample-run/report.md) dan [`examples/README.md`](examples/README.md).

## CLI engine

```bash
ABR="python3 .claude/skills/argument-battle-royale/scripts/abr.py"
$ABR init "TOPIK" [key=value ...]          # buat / lanjutkan run
$ABR next    --run DIR                      # langkah berikutnya + daftar paket pending
$ABR status  --run DIR                      # progres
$ABR check   --run DIR --packet ID          # validasi output paket (untuk worker)
$ABR abandon --run DIR --packet ID [--reason TEKS]
$ABR retry   --run DIR --packet ID          # hanya saat run terhenti (blocked)
$ABR show    --run DIR --fighter F0001
$ABR report  --run DIR                      # bangun ulang laporan
$ABR verify  --run DIR                      # verifikasi integritas (exit 0 = lulus)
$ABR list-runs
$ABR watch   [--run DIR] [--demo] [--once] [--fps N] [--colors truecolor|256]
$ABR frame   [--run DIR] [--scene S] [--style mini|ansi] [--i N]
$ABR arena   [--run DIR] [--out FILE] [--demo]
$ABR live    --run DIR [--url URL]         # arena untuk Artifact live; --url mencatat alamatnya
$ABR serve   [--run DIR] [--port 8765] [--host 127.0.0.1]
$ABR statusline                             # untuk status line Claude Code (JSON via stdin)
```

## Pengujian

```bash
python3 .claude/skills/argument-battle-royale/scripts/selftest.py
```

Menjalankan turnamen end-to-end dengan worker **sintetis** (tanpa LLM) untuk ketiga mode, termasuk skala 1000 petarung, dan menguji: output yang ditolak lalu diperbaiki, paket yang ditinggalkan (fallback skor), refill, resume dari disk setiap iterasi, fallback falsifikasi ke runner-up, serta deteksi manipulasi file ronde. Opsi: `--mode`, `--population`, `--dq-rate`, `--keep`.

## Memasang di repository lain

Salin dua lokasi berikut ke repository tujuan (atau ke `~/.claude/` untuk pemakaian pribadi di semua proyek):

```
.claude/skills/argument-battle-royale/     # skill + engine + template + referensi
.claude/agents/battle-royale-worker.md     # subagent worker (opsional; tanpa ini dipakai general-purpose)
```

Kebutuhan: Python 3.8+ (hanya pustaka standar). Direktori run default `argument-battle-royale-runs/` dibuat di direktori kerja; tambahkan ke `.gitignore` bila tidak ingin ikut ter-commit.

## Struktur berkas

```
.claude/skills/argument-battle-royale/
├── SKILL.md                 instruksi orkestrator untuk Claude
├── README.md                dokumen ini
├── scripts/
│   ├── abr.py               CLI engine
│   ├── selftest.py          uji end-to-end sintetis (termasuk semua adegan animasi)
│   ├── make_preview_gif.py  alat pengembang opsional (butuh Pillow) untuk GIF pratinjau
│   └── engine/              config, util, store, validate, planner, dedup,
│                            bracket, judging, packets, phases, integrity, report,
│                            anim (sprite & perender), arena (halaman HTML)
├── templates/               template paket kerja (map, generate, dedup_review, scout,
│                            duel, judge, dossier, debate, falsification, rubrik, bukti)
│                            dan arena.html
├── references/              pipeline.md, rubric.md, data-model.md, modes.md
└── examples/                inputs.md, README.md, clawd-preview.gif, sample-run/
.claude/agents/battle-royale-worker.md
```

## Keterbatasan

- Semua penilaian dibuat model bahasa; pengacakan X/Y, anonimisasi, panel multi-lensa, dan aturan keputusan berbasis skor mengurangi — bukan menghapus — bias juri.
- Pemenang hanya lebih tahan daripada populasi yang dihasilkan dalam run itu.
- Rubrik adalah pilihan normatif yang eksplisit; bobotnya dicetak di setiap laporan.
- Output LLM tidak deterministik; reproduksi persis memerlukan output paket yang tersimpan.
