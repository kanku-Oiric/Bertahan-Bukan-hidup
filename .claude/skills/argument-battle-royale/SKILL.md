---
name: argument-battle-royale
description: Menjalankan "Battle Royale Argumen" untuk topik atau pertanyaan apa pun — memetakan ruang argumen, menghasilkan hingga 1000 argumen petarung, menghapus duplikat, memvalidasi, men-seed, lalu mengadu mereka dalam bracket eliminasi (duel, deep review panel juri, Final 4, semifinal, final dengan debat) sampai tersisa satu pemenang yang kemudian diuji falsifikasi, dan menulis laporan akhir yang dapat diaudit. Gunakan skill ini setiap kali pengguna memanggil /argument-battle-royale, meminta argumen terkuat atau paling tahan uji untuk suatu pertanyaan, ingin mengadu posisi-posisi yang bersaing (filsafat, sains, sosial, politik, teknologi, hukum, ekonomi, konseptual), meminta turnamen/debat/uji tahan argumen, atau ingin melanjutkan run battle royale yang sudah ada — bahkan bila kata "battle royale" tidak disebut.
---

# Argument Battle Royale

Skill ini mengubah **topik apa pun** menjadi turnamen argumen yang dapat diaudit:

```
TOPIK → PEMETAAN RUANG ARGUMEN → GENERASI PETARUNG → DEDUPLIKASI → VALIDASI → SEEDING → BRACKET
→ ELIMINASI → DEEP REVIEW → FINAL 4 → SEMIFINAL → FINAL → PEMENANG → FALSIFICATION TEST → LAPORAN AKHIR
```

Hasilnya **bukan** klaim kebenaran. Selalu gunakan formulasi:

> "Pemenang adalah argumen yang paling tahan terhadap rubrik pengujian yang diterapkan dalam simulasi ini."

Jangan pernah menyamakan kemenangan turnamen dengan kebenaran metafisik, baik di laporan maupun di balasan Anda.

## Arsitektur: wasit deterministik + juri LLM

- **Engine** (`scripts/abr.py`, Python standar, tanpa dependensi) adalah *wasit*: menyimpan state dan checkpoint, merencanakan alokasi petarung, deduplikasi leksikal, kalibrasi skor, seeding, bracket, agregasi suara panel, ledger berantai-hash, laporan, dan verifikasi integritas. Engine **tidak pernah** memanggil LLM.
- **Anda (orkestrator)** menjalankan engine dan mendistribusikan kerja.
- **Worker** (subagent, atau Anda sendiri bila subagent tidak tersedia) mengerjakan **paket kerja**: satu file `packet.md` mandiri berisi instruksi, rubrik, dan data → satu file `output.json`. Worker memvalidasi output-nya sendiri dengan `abr.py check`.

Semua keputusan kalah/menang dihitung ulang oleh engine dari skor rubrik juri (bukan dari klaim juri), sehingga dapat diverifikasi kapan pun.

## Lokasi skrip

`SKILL_DIR` = direktori tempat file ini berada (base directory skill ini; pada instalasi proyek: `.claude/skills/argument-battle-royale`). Semua perintah di bawah memakai:

```bash
ABR="python3 SKILL_DIR/scripts/abr.py"   # ganti SKILL_DIR dengan path sebenarnya
```

## 1. Baca input

Ambil **topik** dari argumen pemanggilan (teks setelah `/argument-battle-royale`) atau dari permintaan pengguna. Parameter opsional boleh ditulis sebagai `key=value` di mana saja dalam argumen; teruskan apa adanya ke `init` (engine yang mem-parse dan memvalidasi).

| Parameter | Default | Keterangan |
|---|---|---|
| `topic` | — (wajib) | Pertanyaan/topik yang dipertarungkan |
| `mode` | `balanced` | `efficient` \| `balanced` \| `full` (lihat `references/modes.md`) |
| `population` | `1000` | Jumlah petarung target (8–5000) |
| `deep_round_threshold` | per mode (16/32/64) | Babak dengan jumlah slot ≤ nilai ini memakai panel deep review |
| `max_parallel` | `5` | Maksimum worker paralel |
| `random_seed` | turunan hash topik | Menentukan alokasi, pengacakan X/Y, jangkar kalibrasi, pemecah seri |
| `evidence_mode` | `internal` | `internal` \| `web_if_available` |
| `language` | `id` | Bahasa konten keluaran (laporan: `id`/`en`) |
| `output_dir` | `argument-battle-royale-runs/<slug>-<hash>` | Direktori run |
| `resume` | `true` | `true`: lanjutkan run yang sudah ada untuk topik/direktori sama; `false`: paksa run baru |

Jika topik terlalu kabur untuk diperdebatkan (mis. hanya satu kata), ajukan satu pertanyaan klarifikasi singkat. Jika tidak, langsung mulai — jangan menanyakan parameter opsional.

## 2. Mulai atau lanjutkan run

```bash
$ABR init "TOPIK" [key=value ...]
```

Output JSON memuat `run_dir`. Bila `resumed: true`, Anda melanjutkan run lama dari checkpoint terakhir. Untuk mencari run yang ada: `$ABR list-runs`.

Sebelum run baru dengan `population` ≥ 200, beri tahu pengguna dalam satu kalimat perkiraan skala kerja (tabel di §6), lalu lanjutkan tanpa menunggu kecuali pengguna meminta konfirmasi.

## 3. Loop orkestrasi

Ulangi sampai `action` = `done`:

```bash
$ABR next --run RUN_DIR
```

`next` menyerap output yang sudah ditulis, menjalankan semua langkah deterministik, lalu mengembalikan JSON:

- `action: "execute_packets"` → kerjakan setiap item di `packets` (lihat §4). Item dengan `last_errors` adalah percobaan ulang: pastikan worker membaca galat tersebut.
- `action: "blocked"` → baca `blocked.reason`/`blocked.hint`, jelaskan ke pengguna, dan ikuti petunjuknya.
- `action: "done"` → lanjut ke §5.

`next` aman dijalankan kapan saja dan berulang kali (idempoten): paket tanpa output tetap pending. **Hanya orkestrator** yang menjalankan `next`; worker tidak boleh.

Setelah setiap gelombang, beri pengguna satu baris progres dari field `progress` (mis. "Babak 256 besar (Eliminasi): 3/11 paket juri selesai").

### Animasi progres (Clawd)

`next` juga mengembalikan objek `anim` agar progres tidak membosankan:

- **Flipbook di chat.** Bila `anim.show` bernilai `true` (tahap atau babak baru dimulai), tampilkan `anim.frame` apa adanya di dalam blok kode `text`: Clawd berganti pose per tahap (penyihir saat persiapan, duel saat bracket, roket saat uji falsifikasi, piala saat selesai). Bila `show` bernilai `false`, cukup satu baris progres dari `anim.caption` dan `anim.percent`.
- **Arena pertarungan (HTML).** `anim.arena` menunjuk `arena.html` di direktori run, diperbarui setiap `next`. Halaman ini memutar turnamen sebagai pertarungan: dua Clawd masuk arena, setiap juri memukul dengan keberatannya yang sebenarnya, bar ketahanan turun sesuai suara juri, yang kalah KO, pemenang maju di bracket. Penonton hanya memutar acara yang belum ditontonnya; setelah run selesai halaman yang sama menjadi tayangan ulang. Lihat "Arena live" di bawah untuk cara menampilkannya.
- **Terminal live.** Output tool tidak ditampilkan secara live, jadi jangan menjalankan `watch` sendiri. Bila pengguna memakai Claude Code di mesin lokal, sebutkan sekali bahwa mereka dapat membuka terminal lain dan menjalankan `python3 SKILL_DIR/scripts/abr.py watch --run RUN_DIR`.
- Bila pengguna meminta tanpa animasi, lewati flipbook dan arena, lalu tampilkan baris progres saja.

### Arena live

Siapkan arena tepat setelah `next` pertama sebuah run (juga saat melanjutkan run yang belum punya arena), tanpa menunggu diminta. Pilih **satu** jalur berdasarkan tool yang Anda miliki:

**A. Tool `Artifact` tersedia** (Claude Code di aplikasi desktop, web, atau sesi cloud). Ini jalur utama; arena tampil di panel samping aplikasi dan memutar setiap babak baru sendiri.

1. Jalankan `$ABR live --run RUN_DIR`. Outputnya memuat `artifact_page`, `capabilities`, `icon`, dan `description`.
2. Terbitkan `artifact_page` dengan tool `Artifact` memakai `capabilities`, `icon`, dan `description` dari output itu. Terbitkan `arena-artifact.html` ini, bukan `arena.html` (yang memuat kerangka dokumen sendiri).
3. Catat alamatnya: `$ABR live --run RUN_DIR --url URL_ARTIFACT`. Mulai saat ini `anim.live.url` terisi di setiap `next`, juga setelah konteks dipadatkan.
4. Beri tahu pengguna dalam satu kalimat bahwa arena terbuka di panel samping (atau lewat tautannya) dan akan memutar setiap babak begitu selesai.
5. Setiap kali `next` mengembalikan `anim.live.push: true` dan `anim.live.url` terisi, tulis dokumen live ke database artifact dengan tool `ArtifactData` (muat lewat ToolSearch `select:ArtifactData` bila masih tertunda): `action: "set"`, `url` = `anim.live.url`, `collection` = `anim.live.collection`, `doc_id` = `anim.live.doc_id`, `file_path` = `anim.live.file`. Tulisan pertama tanpa `if_version`; berikutnya pakai `if_version` = `version` dari hasil tulisan sebelumnya. Bila ditolak karena versinya berbeda, ulangi sekali dengan versi yang disebut penolakan itu. Jangan membaca isi file itu ke konteks dan jangan menerbitkan ulang halaman setiap babak.
6. Bila `ArtifactData` tidak tersedia, terbitkan ulang artifact yang sama (`Artifact` dengan `url`, dari `artifact_page` hasil `$ABR live` terbaru) paling banyak sekali per tahap atau babak; penonton yang membuka halaman menerima versi baru secara otomatis.
7. Kegagalan menerbitkan atau menulis tidak boleh menghentikan turnamen. Sebutkan sekali kepada pengguna, lalu lanjutkan.

**B. Tanpa tool `Artifact`, dan Claude Code berjalan langsung di komputer pengguna** (CLI di terminal atau IDE mereka; `$ABR live` melaporkan `cloud_session: false`). Jalankan `$ABR serve --run RUN_DIR` sebagai proses latar belakang (Bash dengan `run_in_background: true`; jangan di latar depan karena perintah ini tidak pernah selesai), lalu beri alamat `http://localhost:8765` untuk dibuka di browser pengguna. Halaman menarik data baru setiap 3 detik tanpa memuat ulang.

**C. Selain itu** (mis. chat Claude.ai, atau sandbox yang tidak dapat dijangkau browser pengguna). Katakan sekali di awal bahwa arena akan tampil di akhir sebagai tayangan ulang penuh, lalu serahkan `arena.html` saat run selesai (di chat Claude.ai sebagai artifact HTML agar animasinya berjalan).

Jangan pernah memberi alamat `localhost` kecuali proses `serve` benar-benar berjalan di komputer yang sama dengan browser pengguna. Panel browser bawaan aplikasi desktop Claude tidak dapat membuka server yang Anda jalankan, dan pengguna tidak dapat membuka localhost sesi cloud.

## 4. Mengerjakan paket

### Jalur paralel (bila tool Agent/subagent tersedia)

Kirim hingga `max_parallel` panggilan Agent **dalam satu pesan**, satu paket per agent. Pakai `subagent_type: "battle-royale-worker"` bila tersedia (didefinisikan di `.claude/agents/battle-royale-worker.md`), jika tidak `general-purpose`. Prompt untuk setiap worker:

```
Kerjakan paket kerja Argument Battle Royale.
Baca seluruh file: PACKET_PATH
Ikuti "Protokol worker" di dalamnya persis: tulis JSON valid ke OUTPUT_PATH, lalu jalankan
perintah check yang tertera sampai hasilnya OK. Jangan menjalankan `next` dan jangan mengubah file lain.
Balas hanya satu baris: "PACKET_ID: OK" atau "PACKET_ID: GAGAL — alasan".
```

Jangan membaca isi `packet.md` sendiri saat mendelegasikan — cukup teruskan path-nya; ini menjaga konteks orkestrator tetap kecil. Setelah semua worker dalam gelombang selesai, jalankan `next` lagi. Jika agent berjalan di latar belakang, tunggu notifikasi selesai sebelum gelombang berikutnya.

### Jalur sekuensial (fallback)

Bila tidak ada kemampuan subagent: untuk setiap paket, baca `packet_path`, kerjakan tugasnya sendiri dengan standar yang sama, tulis `output_path`, jalankan perintah `check` di paket sampai `OK`, lalu lanjut ke paket berikutnya. Jalankan `next` setelah setiap beberapa paket. Karena semua state ada di disk, pekerjaan tetap aman bila konteks dipadatkan atau sesi terputus — cukup jalankan `init ... resume=true` atau `next` lagi.

**Lingkungan chat tanpa subagent (mis. Claude.ai).** Semua paket dikerjakan dalam satu percakapan, sehingga panjang konteks menjadi batas nyata. Bila pengguna tidak menyebut `population`, sebelum `init` sampaikan dalam satu atau dua kalimat bahwa default 1000 petarung (~80–290 paket) terlalu besar untuk satu percakapan, lalu tawarkan skala yang layak — `population=16`–`32` untuk run lengkap dengan semua tahap, atau hingga `64` dengan `mode=efficient` — dan ikuti pilihan pengguna. File sandbox belum tentu bertahan antar-percakapan: bila lingkungan menyediakan cara memberikan file kepada pengguna, serahkan `report.md` dan `arena.html` saat selesai (di Claude.ai, arena dapat ditampilkan sebagai artifact HTML agar animasinya berjalan), dan tawarkan arsip direktori run bila pengguna ingin melanjutkan atau mengaudit di tempat lain.

### Standar kerja (berlaku untuk worker mana pun)

- Kerjakan tugas paket dengan sungguh-sungguh; paket sudah memuat rubrik, aturan anti-bias, dan format output.
- **Jangan mengarang** isi output, skor, sitasi, atau hasil uji; jangan menyalin output paket lain; jangan menulis output untuk paket yang belum dikerjakan.
- Bila sebuah paket benar-benar tidak dapat dikerjakan, tinggalkan secara eksplisit: `$ABR abandon --run RUN_DIR --packet ID --reason "..."`. Engine memakai fallback yang tercatat di laporan (mis. skor scouting untuk duel, panel yang lebih kecil).
- Output yang gagal validasi 3 kali otomatis ditinggalkan.

## 5. Menyelesaikan

Saat `action: "done"`:

1. Jalankan `$ABR verify --run RUN_DIR` dan pastikan `ok: true`. Jika gagal, laporkan pemeriksaan yang gagal apa adanya — jangan menyembunyikannya.
2. Baca bagian ringkasan `report.md` (bukan seluruh file) dan sampaikan kepada pengguna:
   - formula pemenang (kutipan di atas),
   - **pemenang tahan-uji** (judul + tesis) dan status uji falsifikasinya (`SURVIVED`, `SURVIVED_WITH_DAMAGE`, atau tidak ada pemenang),
   - juara bracket dan runner-up bila berbeda dari pemenang tahan-uji,
   - kualifikasi wajib dari uji falsifikasi,
   - 2–3 keterbatasan terpenting,
   - path `report.md`, `report.json`, dan status integritas.
3. Jangan menyebut pemenang sebagai "benar" atau "terbukti". Gunakan bahasa ketahanan relatif.

## 6. Skala kerja per mode

Perkiraan jumlah paket (termasuk satu kandidat gagal falsifikasi):

| Mode | 200 petarung | 1000 petarung | Ronde awal diputus oleh |
|---|---:|---:|---|
| `efficient` | ~45 | ~80 | skor scouting terkalibrasi (tanpa duel LLM) |
| `balanced` | ~80 | ~180 | duel LLM ringkas, 1 juri, 20 duel/paket |
| `full` | ~120 | ~290 | duel LLM lengkap (steelman + pemeriksaan silang), 8 duel/paket |

Untuk uji cepat gunakan `population=32 mode=efficient`. Rincian profil mode ada di `references/modes.md`.

## Referensi (baca bila perlu)

- `references/pipeline.md` — setiap tahap pipeline, aturan keputusan, fallback, dan checkpoint.
- `references/rubric.md` — rubrik filsafat analitik & filsafat sains, cacat fatal, kode diskualifikasi, lensa juri.
- `references/data-model.md` — struktur data petarung, duel, ronde, state, ledger, dan format output setiap paket.
- `references/modes.md` — profil mode dan parameter.
- `README.md` — dokumentasi penggunaan untuk manusia, contoh input/output.
- `examples/` — contoh input, dan di repository sumber juga contoh run lengkap.

## Perintah engine lainnya

| Perintah | Fungsi |
|---|---|
| `$ABR status --run DIR` | Ringkasan progres yang mudah dibaca |
| `$ABR check --run DIR --packet ID` | Validasi output sebuah paket |
| `$ABR show --run DIR --fighter F0001` | Tampilkan satu petarung |
| `$ABR retry --run DIR --packet ID` | Ulangi paket saat run `blocked` |
| `$ABR report --run DIR` | Bangun ulang laporan run yang selesai |
| `$ABR verify --run DIR` | Verifikasi integritas penuh (exit 0 = lulus) |
| `$ABR arena --run DIR` | Tulis ulang `arena.html` (atau `--demo` untuk turnamen contoh tanpa run) |
| `$ABR live --run DIR [--url URL]` | Siapkan `arena-artifact.html` + `arena-live.json` untuk Artifact live; `--url` mencatat alamat artifact |
| `$ABR serve --run DIR` | Server lokal untuk menonton arena di browser pada komputer yang sama (`http://localhost:8765`) |
| `$ABR frame --run DIR` | Cetak frame flipbook saat ini |
| `$ABR watch --run DIR` | Animasi live di terminal pengguna sendiri (bukan untuk dijalankan lewat tool) |
| `python3 SKILL_DIR/scripts/selftest.py` | Uji engine end-to-end dengan worker sintetis |
