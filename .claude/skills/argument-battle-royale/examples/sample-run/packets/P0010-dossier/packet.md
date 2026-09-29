# Paket Kerja P0010-dossier — Dosir Final 4 (F0009)

> **Sistem:** Argument Battle Royale · **Tahap:** Final 4 — dosir
> **Topik yang dipertarungkan:** "Apakah AI bisa disebut memahami bahasa?"
> **Bahasa konten keluaran:** Bahasa Indonesia (nama kunci JSON tetap persis seperti contoh).

## Protokol worker (wajib dipatuhi)

1. Paket ini **mandiri**: semua data yang Anda perlukan ada di dalamnya. Jangan membaca file run lain.
2. Kerjakan tugas dengan jujur dan teliti. **Jangan mengarang** sitasi, angka, studi, atau hasil uji.
3. Tulis **hanya JSON valid** (tanpa komentar, tanpa blok kode) ke file:
   `.claude/skills/argument-battle-royale/examples/sample-run/packets/P0010-dossier/output.json`
   JSON wajib memuat `"packet_id": "P0010-dossier"` dan `"input_hash": "bcd0b8a061a482822b383f73e0929a7e5dd69978207b2391199d8bd17927fc30"`.
4. Validasi output Anda dengan perintah berikut, lalu perbaiki sampai hasilnya `OK`:
   `python3 ".claude/skills/argument-battle-royale/scripts/abr.py" check --run ".claude/skills/argument-battle-royale/examples/sample-run" --packet P0010-dossier`
5. **Jangan** menjalankan perintah `next`, dan jangan mengubah file lain di direktori run.
6. Setelah `OK`, balas orkestrator dengan satu baris: `P0010-dossier: OK` (atau `P0010-dossier: GAGAL — <alasan>`).

## Peran Anda

Anda adalah **penguji Final 4**. Argumen di bawah telah bertahan sampai empat besar. Susun **dosir pengujian** yang jujur dan tajam: Anda bukan pembelanya, melainkan pemeriksanya. Dosir ini dipakai oleh panel juri semifinal/final dan oleh uji falsifikasi.

## Konteks topik

- **Rumusan presisi:** Apakah sistem kecerdasan buatan — khususnya model bahasa besar (LLM) yang ada saat ini, dan sistem AI secara prinsip — dapat secara tepat dikatakan memahami bahasa, dan jika ya, dalam arti 'memahami' yang mana?
- **Jenis pertanyaan:** mixed
- **Titik krusial:**
  - Apakah makna dapat muncul dari distribusi bentuk linguistik saja tanpa kontak kausal langsung dengan referen?
  - Apakah pemahaman mensyaratkan intensionalitas asli atau kesadaran fenomenal, atau cukup kapasitas fungsional?
  - Apakah kriteria behavioral (kinerja dan generalisasi lintas tugas) cukup untuk atribusi pemahaman, atau mekanisme internal yang menentukan?
  - Apakah representasi internal LLM tentang entitas dan keadaan dunia merupakan model dunia yang sejati atau korelasi statistik dangkal?
  - Bagaimana menafsirkan kegagalan sistematis (halusinasi, ketidakkonsistenan, kerentanan terhadap perubahan redaksi): bukti ketiadaan pemahaman atau pemahaman yang terbatas?
  - Apakah 'memahami' konsep biner atau bergradasi dan multidimensional?

## Argumen

#### Argumen — Uji dunia kontrafaktual

- **Tesis:** Memahami sebuah konsep mencakup kemampuan menerapkannya kembali ketika konvensi atau dunia diubah secara eksplisit; LLM saat ini merosot tajam pada varian kontrafaktual tugas yang mereka kuasai, menandakan ketergantungan pada pola hafalan, sehingga belum memahami — meski sistem yang lulus uji ini akan memahami.
- **Definisi:** *uji dunia kontrafaktual*: Uji yang mengubah secara eksplisit satu aturan atau fakta (mis. aritmetika basis sembilan, aturan permainan yang dimodifikasi) lalu memeriksa apakah sistem dapat menerapkan konsep yang sama pada dunia yang diubah.; *memahami konsep*: Menguasai struktur konsep sehingga dapat menerapkannya secara fleksibel, termasuk di bawah perubahan yang dinyatakan.
- **Premis:**
  - **P1** (konseptual): Jika sebuah sistem memahami konsep C, ia mampu menerapkan C secara memadai ketika aturan latar yang tidak esensial bagi C diubah secara eksplisit. — *dukungan:* Siswa yang memahami penjumlahan dapat menjumlah dalam basis lain setelah diberi tahu aturannya; yang menghafal tabel tidak bisa.
  - **P2** (empiris): Pada banyak tugas, kinerja LLM turun tajam pada varian kontrafaktual (mis. aritmetika pada basis selain sepuluh, permainan dengan aturan yang sedikit diubah) dibandingkan versi baku, jauh lebih tajam daripada penurunan pada manusia. — *dukungan:* Temuan evaluasi tugas kontrafaktual yang dilaporkan dalam literatur.
  - **P3** (metodologis): Penurunan tajam itu paling baik dijelaskan oleh ketergantungan pada pola yang sering muncul dalam data latih, bukan oleh penguasaan struktur konsep. — *dukungan:* Penurunan berkorelasi dengan kelangkaan varian dalam data.
  - **P4** (metafisis): Tidak ada alasan prinsipiel mengapa sistem buatan tidak dapat lulus uji dunia kontrafaktual. — *dukungan:* Uji ini bersifat perilaku dan netral terhadap substrat.
- **Inferensi (deduktif):** Modus tollens dari P1: jika LLM memahami, mereka akan lulus uji; P2 dan P3 menunjukkan mereka tidak lulus secara memadai; maka mereka belum memahami. P4 menjadikan kesimpulan kontingen, bukan prinsipiel.
- **Kesimpulan:** LLM saat ini belum memahami bahasa dan konsep yang diungkapkannya dalam arti yang kuat; sistem AI yang lulus uji dunia kontrafaktual akan layak disebut memahami.
- **Komitmen empiris:** Kesenjangan kinerja LLM antara versi baku dan kontrafaktual jauh lebih besar daripada kesenjangan pada manusia.
- **Falsifier:** LLM mutakhir menunjukkan kinerja kontrafaktual yang sebanding dengan manusia.; Manusia yang jelas memahami konsep menunjukkan penurunan kontrafaktual setajam LLM.
- **Keberatan terkuat yang diantisipasi:** Manusia juga merosot pada varian yang tidak biasa (mis. berhitung dalam basis sembilan); penurunan itu menunjukkan keterbatasan, bukan ketiadaan pemahaman.
- **Balasan:** Yang relevan adalah besarnya kesenjangan: manusia melambat tetapi tetap benar setelah memahami aturan baru, sedangkan kesenjangan LLM mengikuti frekuensi data, pola yang khas bagi hafalan.
- **Cakupan & kualifikasi:** Klaim bergradasi pada sejauh mana uji kontrafaktual gagal; bisa berubah dengan generasi model baru.

## Riwayat serangan yang pernah diterima

Keberatan yang diajukan lawan/juri pada ronde-ronde sebelumnya, dan titik terlemah dari scouting:

- [scouting] Ambang 'memadai' dalam P1 kabur: manusia juga merosot pada varian yang tidak biasa, dan argumen melompat dari 'pemahaman belum kokoh' ke 'belum memahami'; temuan kontrafaktual dapat berubah pada generasi model baru.
- [R01-M0005/L7] Kegagalan pada tugas kontrafaktual hanyalah batas kinerja; bahkan sistem yang lulus uji itu tetap tanpa penutur yang bermaksud.
- [R02-M0003/L1] Bukti Y menunjukkan penurunan, bukan ketiadaan; kesimpulan biner Y tidak mengikuti dari data yang bergradasi.
- [R02-M0003/L2] Data kontrafaktual X bergradasi (penurunan, bukan nol), sehingga ia sebenarnya mendukung pemahaman bergradasi.
- [R02-M0003/L3] Siswa yang memahami sebagian gagal pada varian kontrafaktual tanpa kita simpulkan ia tidak memahami; data Y mendukung gradasi, bukan ketiadaan.

## Isi dosir

1. `standard_form`: rekonstruksi bentuk baku (P1, P2, ..., C) — tulis premis tersembunyi yang dibutuhkan secara eksplisit dan tandai sebagai "(tersirat)".
2. `formal_skeleton`: kerangka logis ringkas (mis. "P1: ∀x(Fx→Gx); P2: Fa; ∴ Ga" atau bentuk skema abduktif/induktif).
3. `hard_core` dan `protective_belt` (Lakatos): klaim yang tidak dapat dilepas tanpa meninggalkan posisi vs. hipotesis bantu yang dapat direvisi.
4. `empirical_commitments` dan `falsifiers` yang presisi.
5. `strongest_objections` (3–8): gabungkan riwayat dan keberatan baru yang lebih kuat; beri `severity` (`low`/`medium`/`high`/`critical`) dan `status` (`answered`/`partially_answered`/`unanswered`) berdasarkan sumber daya argumen itu sendiri.
6. `vulnerabilities`, `strengths`, dan `assessment` (penilaian keseluruhan, 3–6 kalimat).

## Mode bukti: `internal`

Gunakan pengetahuan internal Anda saja. Bila Anda merujuk temuan empiris, jelaskan secara umum (mis. "eksperimen priming sosial banyak yang gagal direplikasi") dan tandai ketidakpastian. **Dilarang** mengarang judul studi, penulis, tahun, angka, atau URL. Isi `evidence_mode_used` dengan `"internal"` bila field itu diminta.



## Format output

```json
{
  "packet_id": "P0010-dossier",
  "input_hash": "bcd0b8a061a482822b383f73e0929a7e5dd69978207b2391199d8bd17927fc30",
  "fighter_id": "F0009",
  "standard_form": [
    "P1 ...",
    "P2 ...",
    "P3 (tersirat) ...",
    "C ..."
  ],
  "formal_skeleton": "<kerangka logis>",
  "hard_core": [
    "<klaim inti>"
  ],
  "protective_belt": [
    "<hipotesis bantu>"
  ],
  "key_definitions": [
    "<istilah: definisi>"
  ],
  "empirical_commitments": [
    "<komitmen>"
  ],
  "falsifiers": [
    "<falsifier>"
  ],
  "strongest_objections": [
    {
      "objection": "<keberatan>",
      "source": "history",
      "severity": "high",
      "status": "partially_answered"
    }
  ],
  "vulnerabilities": [
    "<kerentanan>"
  ],
  "strengths": [
    "<kekuatan>"
  ],
  "assessment": "<penilaian 3-6 kalimat>"
}
```
