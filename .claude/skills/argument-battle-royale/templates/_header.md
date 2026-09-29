# Paket Kerja {{PACKET_ID}} — {{PACKET_TITLE}}

> **Sistem:** Argument Battle Royale · **Tahap:** {{STAGE_LABEL}}
> **Topik yang dipertarungkan:** "{{TOPIC}}"
> **Bahasa konten keluaran:** {{LANGUAGE_NAME}} (nama kunci JSON tetap persis seperti contoh).

## Protokol worker (wajib dipatuhi)

1. Paket ini **mandiri**: semua data yang Anda perlukan ada di dalamnya. Jangan membaca file run lain.
2. Kerjakan tugas dengan jujur dan teliti. **Jangan mengarang** sitasi, angka, studi, atau hasil uji.
3. Tulis **hanya JSON valid** (tanpa komentar, tanpa blok kode) ke file:
   `{{OUTPUT_PATH}}`
   JSON wajib memuat `"packet_id": "{{PACKET_ID}}"` dan `"input_hash": "{{INPUT_HASH}}"`.
4. Validasi output Anda dengan perintah berikut, lalu perbaiki sampai hasilnya `OK`:
   `{{CHECK_CMD}}`
5. **Jangan** menjalankan perintah `next`, dan jangan mengubah file lain di direktori run.
6. Setelah `OK`, balas orkestrator dengan satu baris: `{{PACKET_ID}}: OK` (atau `{{PACKET_ID}}: GAGAL — <alasan>`).

