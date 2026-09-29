# Mode dan Parameter

Semua nilai berasal dari `MODES` di `scripts/engine/config.py` dan dicetak ulang di laporan setiap run.

## Profil mode

| Parameter profil | `efficient` | `balanced` (default) | `full` |
|---|---|---|---|
| Metode babak eliminasi | `score` — skor scouting terkalibrasi | `llm_single` — 1 juri, format ringkas | `llm_single_full` — 1 juri, protokol lengkap |
| Duel per paket eliminasi | — | 20 | 8 |
| `deep_round_threshold` default | 16 | 32 | 64 |
| Panel deep review | 3 | 3 | 3 |
| Duel per paket deep review | 8 | 4 | 4 |
| Panel semifinal | 3 | 5 | 5 |
| Panel final | 3 | 5 | 7 |
| Penguji falsifikasi per kandidat | 1 | 2 | 3 |
| Review duplikasi semantik (LLM) | tidak (ambang leksikal saja) | ya | ya |
| Jatah gelombang refill | 1 | 2 | 2 |
| Petarung per paket generasi | 40 | 25 | 20 |
| Petarung per paket scouting | 40 | 25 | 20 |

**Catatan mode `efficient`.** Karena seeding dan duel eliminasi sama-sama memakai skor scouting, babak eliminasi awal setara dengan pra-seleksi berdasarkan seeding (tidak ada upset). Duel LLM sesungguhnya dimulai pada babak dengan slot ≤ `deep_round_threshold`. Laporan menyatakan hal ini secara eksplisit.

## Parameter pengguna

| Parameter | Default | Rentang/validasi | Efek |
|---|---|---|---|
| `topic` | — | ≥ 5 karakter | Pertanyaan yang dipertarungkan |
| `mode` | `balanced` | `efficient`/`balanced`/`full` | Profil di atas |
| `population` | 1000 | 8–5000 | Target petarung (juga kapasitas maksimum bracket) |
| `deep_round_threshold` | per mode | 4–4096 | Babak dengan slot ≤ nilai ini (dan ≥ 8) memakai panel deep review |
| `max_parallel` | 5 | 1–64 | Petunjuk jumlah worker paralel untuk orkestrator; boleh diubah saat resume |
| `random_seed` | 32 bit pertama SHA-256 topik | ≥ 0 | Alokasi slot, urutan X/Y, jangkar kalibrasi, pemecah seri |
| `evidence_mode` | `internal` | `internal`/`web_if_available` | Apakah worker boleh memverifikasi klaim empiris dengan web |
| `language` | `id` | kode bahasa | Bahasa konten; label laporan tersedia untuk `id` dan `en` |
| `output_dir` | `argument-battle-royale-runs/<slug>-<hash6>` | path | Direktori run |
| `resume` | `true` | boolean | Lanjutkan run yang ada; `false` membuat direktori baru berakhiran `-r2`, `-r3`, ... |

Saat resume, parameter yang ditulis eksplisit dan berbeda dari konfigurasi tersimpan (kecuali `max_parallel`) ditolak agar satu run tidak tercampur dua konfigurasi.

## Perkiraan beban kerja

Jumlah paket terukur dengan `scripts/selftest.py` (worker sintetis; termasuk satu kandidat yang gagal falsifikasi):

| Mode | 40 | 200 | 1000 |
|---|---:|---:|---:|
| `efficient` | ~35 | ~45 | ~80 |
| `balanced` | ~60 | ~80 | ~180 |
| `full` | ~70 | ~120 | ~290 |

Paket generasi, scouting, dan juri eliminasi berisi puluhan argumen; paket semifinal/final lebih sedikit tetapi lebih panjang. Untuk percobaan pertama pada topik baru, `population=32 mode=efficient` atau `population=64 mode=balanced` memberi gambaran cepat.

## Memilih mode

- **`efficient`** — eksplorasi cepat; puas dengan pra-seleksi berbasis skor.
- **`balanced`** — default; setiap duel diputus juri LLM, rigor penuh mulai 32 besar.
- **`full`** — analisis paling mendalam; protokol lengkap di setiap duel dan panel 7 di final.
