# Contoh

## `inputs.md`

Contoh pemanggilan skill lintas domain dan kombinasi parameter.

## `sample-run/` — run nyata lengkap

| | |
|---|---|
| Topik | *Apakah AI bisa disebut memahami bahasa?* |
| Parameter | `mode=balanced population=16 deep_round_threshold=8` (seed turunan topik: 3171064302) |
| Jalur eksekusi | Sekuensial: Claude bertindak sebagai orkestrator **dan** worker untuk setiap paket (jalur fallback tanpa subagent) |
| Paket kerja | 37 (1 peta, 1 generasi, 1 scouting, 1 duel eliminasi, 3 juri deep review, 4 dosir, 8 debat semifinal, 5 juri semifinal, 6 debat final, 5 juri final, 2 penguji falsifikasi) |
| Integritas | `abr.py verify` lulus 11/11 pemeriksaan |

Skala 16 petarung dipilih agar setiap tahap pipeline terwakili dengan konten sungguhan dalam ukuran yang dapat dibaca manusia: eliminasi (babak 16 besar, juri tunggal), deep review (8 besar, panel 3 lensa), Final 4 (dosir), semifinal dan final (debat + panel 5 juri), serta uji falsifikasi (2 penguji). Run 1000 petarung memakai mesin dan protokol yang sama, hanya dengan lebih banyak paket.

### Ringkasan hasil

- **Pemenang tahan-uji:** F0005 — *Profil campuran pragmatik: penjelasan terbaik adalah pemahaman parsial* (posisi "ya secara parsial dan bergradasi"), status falsifikasi `SURVIVED_WITH_DAMAGE`.
- **Final:** F0005 mengalahkan F0009 *Uji dunia kontrafaktual* (posisi "tidak untuk AI saat ini") 3–2, dengan dissent dari logikawan formal dan skeptis.
- **Semifinalis:** F0014 *Konsep klaster yang terbelah* (deflasioner) dan F0001 *Paritas mekanistik* (ya, substantif).
- Keempat finalis berasal dari empat posisi berbeda; posisi "tidak, secara prinsip" tersingkir seluruhnya di babak 16 besar.
- Uji falsifikasi menggugurkan satu komitmen bantu pemenang (kegagalan berkelompok hanya menurut dimensi) dan menuntut kualifikasi, antara lain klausul mekanisme eksplisit dan pengakuan faktor jarak dari distribusi latih.

Baca `sample-run/report.md` untuk laporan lengkap, `sample-run/arena.html` untuk arena beranimasi (buka di browser), dan `sample-run/packets/<id>/packet.md` untuk melihat persis apa yang diterima setiap worker.

### Verifikasi ulang

```bash
python3 .claude/skills/argument-battle-royale/scripts/abr.py verify --run .claude/skills/argument-battle-royale/examples/sample-run
```

### Catatan kejujuran

- Semua konten (argumen, skor, putusan, debat, uji) ditulis oleh model bahasa yang bertindak sebagai worker; ini adalah demonstrasi mesin dan protokol, bukan hasil riset yang telah ditinjau.
- Path absolut di `packets/*/packet.md` telah direlatifkan terhadap root repository agar contoh portabel. File itu tidak di-hash oleh ledger, sehingga verifikasi integritas tidak terpengaruh.
- `arena.html` dan `arena-data.json` ditambahkan setelah run selesai lewat `abr.py arena` (fitur animasi dibuat belakangan); keduanya tidak termasuk digest integritas. Buka `arena.html` untuk menonton tayangan ulang seluruh turnamen sebagai pertarungan.
- Setelah run ini selesai, engine diperbaiki dalam dua hal kosmetik: riwayat serangan di paket dosir/falsifikasi kini mencantumkan label X/Y argumen yang bersangkutan, dan kutipan alasan juri di laporan mencantumkan pemetaan X/Y. Paket dosir di run ini dibuat sebelum perbaikan pertama; laporan dibangun ulang dengan `abr.py report` (tercatat di ledger sebagai `report_regenerated`).

## `clawd-preview.gif`

Pratinjau keempat adegan animasi (penyihir, duel, peluncuran, juara), dibuat dengan `scripts/make_preview_gif.py`.
