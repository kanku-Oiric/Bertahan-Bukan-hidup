# Pipeline Argument Battle Royale

Dokumen ini menjelaskan apa yang terjadi di setiap tahap, siapa yang mengerjakannya (engine atau LLM), aturan keputusannya, dan fallback bila ada yang gagal. Semua angka default ada di `scripts/engine/config.py`.

## Daftar isi

1. [Prinsip desain](#prinsip-desain)
2. [Fase dan paket kerja](#fase-dan-paket-kerja)
3. [Tahap demi tahap](#tahap-demi-tahap)
4. [Aturan keputusan](#aturan-keputusan)
5. [Fallback](#fallback)
6. [Checkpoint, resume, dan konkurensi](#checkpoint-resume-dan-konkurensi)
7. [Integritas](#integritas)

## Prinsip desain

- **Pemisahan wasit dan juri.** LLM menghasilkan konten dan skor; engine deterministik menghitung semua keputusan dari skor itu. Setiap putusan dapat dihitung ulang (`verify`).
- **Netralitas alokasi.** Setiap posisi (stance) mendapat kuota petarung yang sama. Turnamen, bukan generator, yang menentukan posisi mana yang bertahan.
- **Independensi juri.** Setiap anggota panel adalah paket terpisah (idealnya subagent terpisah) yang tidak melihat penilaian juri lain.
- **Anti-bias posisi.** Urutan X/Y diacak per (duel, juri) dengan seed; identitas, unggulan, dan skor scouting tidak ditampilkan kepada juri duel.
- **Kejujuran epistemik.** Pemenang turnamen masih harus lolos uji falsifikasi; laporan memakai bahasa ketahanan relatif, bukan kebenaran.

## Fase dan paket kerja

| Fase engine | Tahap pipeline | Paket LLM | Kunci stage |
|---|---|---|---|
| `init` → `map` | PEMETAAN RUANG ARGUMEN | `map` ×1 | `map` |
| `generate` | GENERASI PETARUNG | `generate` × ⌈slot/gen_batch⌉ | `gen:<gelombang>` |
| `dedup` | DEDUPLIKASI | `dedup_review` (opsional) | `dedup:<gelombang>` |
| `validate` | VALIDASI (+ scouting) | `scout` × ⌈unik/scout_batch⌉ | `scout:<gelombang>` |
| `seed` | SEEDING + BRACKET | — | — |
| `round` (eliminasi) | ELIMINASI | `duel` atau `judge` (1 juri) — atau tanpa paket di mode efficient | `round:<r>:judge` |
| `round` (deep review) | DEEP REVIEW | `judge` × lensa × ⌈duel/deep_batch⌉ | `round:<r>:judge` |
| `final4` | FINAL 4 | `dossier` ×4 | `final4` |
| `round` (semifinal) | SEMIFINAL | `debate` (serangan, pembelaan) ×2 per duel per babak; `judge` × panel | `round:<r>:debate:<babak>`, `round:<r>:judge` |
| `round` (final) | FINAL → PEMENANG | `debate` (serangan, pembelaan, penutup); `judge` × panel | sama |
| `falsification` | FALSIFICATION TEST | `falsification` × penguji per kandidat | `falsify:<i>` |
| `report` → `done` | LAPORAN AKHIR | — | — |

## Tahap demi tahap

### 1. Pemetaan ruang argumen (`map`)
Satu paket menghasilkan: rumusan presisi, jenis pertanyaan, presuposisi, istilah kunci beserta bacaan alternatif, 3–6 **posisi**, 3–12 **kerangka** (dengan `compatible_stances` opsional), 3–8 **strategi argumentasi**, titik krusial, dan domain bukti. Disimpan di `map.json`. Tanpa peta, run berhenti (`blocked`) setelah 3 percobaan — gunakan `retry`.

### 2. Generasi petarung (`generate`)
Engine membangun **sel** = posisi × kerangka yang kompatibel × strategi (`plan.json`). Kuota per posisi dibagi rata; di dalam posisi, slot diputar merata lintas kerangka lalu strategi. Slot di sel yang sama diberi nomor `variant` dan dikelompokkan dalam paket yang sama agar generator dapat membedakannya. Setiap slot → satu petarung (struktur di `data-model.md`). Engine memberi ID `F0001…` dan hash konten.

### 3. Deduplikasi (`dedup`)
- **Leksikal (engine):** kemiripan = ½·Jaccard(unigram) + ½·Jaccard(bigram) atas tesis, premis, inferensi, dan kesimpulan yang dinormalisasi. ≥ 0,70 → duplikat otomatis. 0,45–0,70 → kandidat review (maks. 300 pasangan termirip).
- **Semantik (LLM, mode balanced/full):** paket `dedup_review` memutuskan apakah pasangan memiliki tesis inti, premis kunci, dan rute inferensi yang sama. Ragu → berbeda.
- **Kluster:** union-find; wakil = generasi paling awal, lalu paling lengkap, lalu ID terkecil. Petarung gelombang sebelumnya tidak pernah dihapus oleh gelombang refill.

### 4. Validasi & scouting (`validate`)
Setiap petarung unik dinilai **mandiri** oleh paket `scout`: valid/tidak (kode DQ), skor rubrik, cacat fatal, titik terkuat & terlemah.
- **Kalibrasi jangkar:** bila ada ≥ 2 paket scouting, 3 petarung jangkar (dipilih dengan seed) disisipkan ke setiap paket. Offset paket = rata-rata (median skor jangkar − skor jangkar di paket itu), dibatasi ±15. Skor terkalibrasi = skor mentah + offset. Jangkar sendiri memakai median per kriteria dan mayoritas untuk validitas/cacat fatal.
- **Refill:** bila petarung valid < 90% target dan masih ada jatah (`max_refill_rounds`), engine membuat gelombang generasi baru sebesar defisit × 1,15, dialokasikan ke posisi yang paling banyak kehilangan petarung dan sel yang paling sedikit terisi. Gelombang baru melalui dedup dan validasi yang sama.

### 5. Seeding & bracket (`seed`)
Urutan unggulan: (1) jumlah cacat fatal scouting menaik, (2) skor terkalibrasi menurun, (3) pemecah seri acak ber-seed. Petarung di atas kapasitas `population` dipotong (`cut_capacity`). Pada saat ini `fighters.jsonl`, `population.json`, dan `seeding.json` **dikunci** (hash dicatat di ledger).
Bracket eliminasi tunggal berukuran pangkat dua terkecil ≥ jumlah petarung; bye untuk unggulan teratas; penempatan standar (unggulan 1 dan 2 hanya bisa bertemu di final).

### 6. Eliminasi, deep review, semifinal, final (`round`)
Tahap sebuah babak ditentukan oleh jumlah slot babak itu:

| Slot | Tahap | Metode |
|---|---|---|
| > `deep_round_threshold` | Eliminasi | `score` (efficient), `llm_single` (balanced), `llm_single_full` (full) |
| ≤ `deep_round_threshold`, ≥ 8 | Deep review | panel `deep_panel` juri berlensa berbeda, protokol lengkap |
| 4 | Semifinal | debat (serangan → pembelaan) + panel `semifinal_panel` |
| 2 | Final | debat (serangan → pembelaan → penutup) + panel `final_panel` |

Protokol juri lengkap: steelman kedua argumen → pemeriksaan silang (keberatan terkuat X→Y dan Y→X, kualitas jawaban) → cacat fatal → skor rubrik → putusan dengan keyakinan, faktor penentu, alasan, dan risiko dissent. Di semifinal/final juri juga membaca dosir Final 4 dan transkrip debat, serta menghukum "pemindahan tiang gawang".

### 7. Final 4 (`final4`)
Sebelum semifinal, setiap finalis mendapat **dosir**: bentuk baku (premis tersirat dieksplisitkan), kerangka formal, inti keras vs sabuk pelindung (Lakatos), komitmen empiris, falsifier, 3–8 keberatan terkuat (dari riwayat serangan + keberatan baru) dengan tingkat keparahan dan status jawaban, kerentanan, kekuatan, dan penilaian. Dosir dipakai oleh pembela, juri, dan penguji falsifikasi.

### 8. Uji falsifikasi (`falsification`)
Antrean kandidat: juara → runner-up → dua semifinalis (diurutkan menurut rata-rata skor semifinal). Untuk setiap kandidat, `falsification_panel` penguji independen (penekanan berbeda: prediksi empiris; reductio & kasus batas; rival & imunisasi) wajib menjalankan ≥ 6 uji termasuk kontra-contoh, reductio, perbandingan rival, kasus batas, deteksi imunisasi, dan uji empiris/konseptual. Rival = lawan final/semifinal kandidat + petarung terbaik dari posisi berbeda.
- Verdict per penguji divalidasi terhadap hasil ujinya (lihat `rubric.md`).
- Agregasi **konservatif-mayoritas**: urutkan verdict dari yang terberat, ambil indeks ⌈k/2⌉−1 (k=1: verdict itu; k=2: terberat; k=3: median).
- Kandidat pertama yang tidak `FALSIFIED` menjadi **pemenang tahan-uji**. Bila semua gugur: tidak ada pemenang, dan laporan menyarankan penangguhan penilaian.

### 9. Laporan (`report`)
`report.md` + `report.json` + `integrity.json`. Lihat `README.md` untuk struktur laporan.

## Aturan keputusan

**Satu juri** (dihitung engine dari skor juri):
1. Lebih sedikit cacat fatal menang.
2. Seri cacat fatal → total tertimbang lebih tinggi menang.
3. Selisih total < 1,0 (skala 0–100) → pilihan holistik juri (`winner`).
Pilihan juri yang bertentangan dengan aturan dicatat sebagai `judge_inconsistency`; aturan rubrik tetap berlaku.

**Panel:** mayoritas; seri (panel genap karena ada juri gugur) → jumlah selisih total lintas juri; masih seri → undian ber-seed.

**Duel berbasis skor** (mode efficient / fallback): cacat fatal scouting, lalu skor terkalibrasi, lalu urutan unggulan.

## Fallback

| Kegagalan (setelah 3 percobaan atau `abandon`) | Perlakuan | Flag laporan |
|---|---|---|
| Paket peta | run `blocked`; `retry` | — |
| Paket generasi | slot hilang; bisa tertutup refill | `generation_slots_lost` |
| Paket review duplikasi | pasangan dianggap berbeda | `dedup_review_abandoned` |
| Paket scouting | petarung di dalamnya DQ `DQ_UNSCORED` | — |
| Satu juri panel | panel mengecil | `panel_reduced` |
| Semua juri sebuah duel | diputus dengan skor scouting | `score_fallback` |
| Giliran debat | tercatat "tidak ada pernyataan" | `debate_turn_missing` |
| Dosir | juri/penguji bekerja tanpa dosir | `dossier_missing` |
| Semua penguji falsifikasi | kandidat ditetapkan dengan status `INCONCLUSIVE` | `falsification_inconclusive` |
| Petarung valid < 4 | run `blocked` | — |

## Checkpoint, resume, dan konkurensi

- **State** (`state.json`) ditulis atomik (tulis-sementara + rename) setelah setiap langkah. Semua artefak lain juga ditulis atomik.
- **Resume:** `init ... resume=true` (default) atau langsung `next --run DIR`. `next` idempoten: ia menyerap output yang ada, melanjutkan langkah deterministik yang tertunda, dan mencantumkan ulang paket yang belum selesai. Tidak ada kerja yang hilang karena konteks dipadatkan atau sesi terputus.
- **Konkurensi:** worker hanya menulis `packets/<id>/output.json` miliknya sendiri. Hanya `next`/`abandon`/`retry` yang mengubah state, dan ketiganya memegang kunci file `.lock` (kunci basi > 10 menit dibersihkan).

## Integritas

`abr.py verify` menjalankan 11 pemeriksaan (lihat docstring `scripts/engine/integrity.py`): rantai hash ledger, output paket tidak berubah sejak diserap, populasi terkunci sejak seeding, seeding & bracket dihitung ulang, setiap putusan juri dan panel dihitung ulang dari skor mentah, file ronde tidak berubah sejak ditutup, juara = pemenang final, agregasi falsifikasi dihitung ulang, konsistensi hitungan populasi, dan konsistensi laporan (termasuk memuat formula pemenang). Digest run dicetak di laporan.
