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
- `examples/` — contoh input dan contoh run lengkap.

## Perintah engine lainnya

| Perintah | Fungsi |
|---|---|
| `$ABR status --run DIR` | Ringkasan progres yang mudah dibaca |
| `$ABR check --run DIR --packet ID` | Validasi output sebuah paket |
| `$ABR show --run DIR --fighter F0001` | Tampilkan satu petarung |
| `$ABR retry --run DIR --packet ID` | Ulangi paket saat run `blocked` |
| `$ABR report --run DIR` | Bangun ulang laporan run yang selesai |
| `$ABR verify --run DIR` | Verifikasi integritas penuh (exit 0 = lulus) |
| `python3 SKILL_DIR/scripts/selftest.py` | Uji engine end-to-end dengan worker sintetis |
