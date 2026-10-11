# Aset Gobyet untuk arena

Disalin otomatis dari repo Gobyet (`v2/`, commit `d24d0cb`) oleh `v2/tools/vendor_skill.py`. Jangan edit berkas di sini; ubah di repo Gobyet, ekspor ulang, lalu salin ulang.

- `registry.json`: karakter, state yang dipakai arena, alias state inti, rantai fallback, jangkar.
- `sheets/<id>/<state>.png`: strip frame 64x64 berpalet, latar transparan.
- `sheets/berserker-hero/<state>.png`: Berserker Hero (tokoh utama) dari `pack/` repo Gobyet, strip frame 128x96 dengan durasi per frame; entri registry-nya punya `canvas`, `anchor`, `px` (skala gambar relatif Gobyet), `variants` (serangan bergantian), dan `hit` -> `exhaustion`.
- `icons/`: ikon aksesori 16x16 untuk topik dua domain (satu primer + satu sekunder).
