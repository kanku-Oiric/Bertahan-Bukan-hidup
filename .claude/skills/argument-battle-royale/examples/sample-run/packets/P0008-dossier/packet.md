# Paket Kerja P0008-dossier — Dosir Final 4 (F0005)

> **Sistem:** Argument Battle Royale · **Tahap:** Final 4 — dosir
> **Topik yang dipertarungkan:** "Apakah AI bisa disebut memahami bahasa?"
> **Bahasa konten keluaran:** Bahasa Indonesia (nama kunci JSON tetap persis seperti contoh).

## Protokol worker (wajib dipatuhi)

1. Paket ini **mandiri**: semua data yang Anda perlukan ada di dalamnya. Jangan membaca file run lain.
2. Kerjakan tugas dengan jujur dan teliti. **Jangan mengarang** sitasi, angka, studi, atau hasil uji.
3. Tulis **hanya JSON valid** (tanpa komentar, tanpa blok kode) ke file:
   `.claude/skills/argument-battle-royale/examples/sample-run/packets/P0008-dossier/output.json`
   JSON wajib memuat `"packet_id": "P0008-dossier"` dan `"input_hash": "5f70921b5c859c64668fac14c93253fbf29f78a52e2bbca4b6ac50804c5d8443"`.
4. Validasi output Anda dengan perintah berikut, lalu perbaiki sampai hasilnya `OK`:
   `python3 ".claude/skills/argument-battle-royale/scripts/abr.py" check --run ".claude/skills/argument-battle-royale/examples/sample-run" --packet P0008-dossier`
5. **Jangan** menjalankan perintah `next`, dan jangan mengubah file lain di direktori run.
6. Setelah `OK`, balas orkestrator dengan satu baris: `P0008-dossier: OK` (atau `P0008-dossier: GAGAL — <alasan>`).

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

#### Argumen — Profil campuran pragmatik: penjelasan terbaik adalah pemahaman parsial

- **Tesis:** Pola keberhasilan dan kegagalan LLM yang khas — kuat pada semantik literal dan banyak implikatur, rapuh pada komitmen jangka panjang, referensi dunia nyata, dan konsistensi — paling baik dijelaskan oleh hipotesis pemahaman parsial, bukan oleh pemahaman penuh maupun pencocokan pola belaka.
- **Definisi:** *pemahaman parsial*: Keadaan di mana sebuah sistem memiliki sebagian dimensi pemahaman (mis. inferensial, pragmatik lokal) tetapi tidak dimensi lain (mis. pelacakan komitmen, grounding referensial).
- **Premis:**
  - **P1** (empiris): LLM berhasil pada banyak inferensi komposisional baru dan implikatur percakapan yang tidak dapat dipecahkan dengan pencocokan literal. — *dukungan:* Evaluasi generalisasi dan pragmatik; kinerja pada kalimat dan skenario yang dibuat baru.
  - **P2** (empiris): LLM juga menunjukkan kegagalan sistematis yang jarang terjadi pada penutur yang memahami: kesulitan membalik relasi yang dipelajari satu arah, kepekaan tinggi terhadap perubahan redaksi yang tidak mengubah isi, dan menyetujui pandangan pengguna walau bertentangan dengan jawaban sebelumnya. — *dukungan:* Pola kegagalan ini dilaporkan berulang kali dalam literatur evaluasi.
  - **P3** (metodologis): Hipotesis 'pemahaman penuh' tidak menjelaskan P2, dan hipotesis 'pencocokan pola dangkal' tidak menjelaskan P1. — *dukungan:* Masing-masing hipotesis memprediksi profil yang seragam, bukan profil campuran.
  - **P4** (metodologis): Hipotesis pemahaman parsial memprediksi profil campuran secara spesifik: berhasil di dimensi yang terlatih melalui distribusi teks, gagal di dimensi yang memerlukan komitmen stabil dan kontak dengan referen. — *dukungan:* Prediksi ini dapat diuji dan sesuai dengan data P1 dan P2.
- **Inferensi (abduktif):** Dari tiga hipotesis bersaing, hanya pemahaman parsial yang menjelaskan P1 dan P2 sekaligus (P3, P4); maka ia penjelasan terbaik.
- **Kesimpulan:** AI kontemporer memahami bahasa secara parsial dan bergradasi; jawaban ya-atau-tidak yang biner salah menggambarkan keadaannya.
- **Komitmen empiris:** Profil keberhasilan-kegagalan LLM memang campuran dan terstruktur per dimensi, bukan acak.
- **Falsifier:** Kegagalan dalam P2 lenyap sepenuhnya dengan skala atau pelatihan tambahan tanpa perubahan arsitektur (mendukung pemahaman penuh).; Keberhasilan dalam P1 terbukti berasal dari kontaminasi data latih (mendukung pencocokan pola).; Kegagalan tersebar acak tanpa struktur per dimensi.
- **Keberatan terkuat yang diantisipasi:** 'Pemahaman parsial' adalah kompromi yang tidak dapat difalsifikasi: setiap data bisa disebut 'sebagian'.
- **Balasan:** Hipotesis ini memprediksi dimensi mana yang berhasil dan gagal; ia akan salah bila keberhasilan dan kegagalan tidak mengikuti garis dimensi yang diprediksi, sebagaimana tertulis di falsifier.
- **Cakupan & kualifikasi:** Klaim tentang LLM kontemporer; tidak mengklaim batas prinsipiel bagi AI.

## Riwayat serangan yang pernah diterima

Keberatan yang diajukan lawan/juri pada ronde-ronde sebelumnya, dan titik terlemah dari scouting:

- [scouting] Batas 'dimensi' pemahaman tidak didefinisikan secara presisi sebelum data dilihat, sehingga ada risiko pengelompokan kegagalan ke dimensi dilakukan secara post hoc.
- [R01-M0001/L7] Jika pemahaman penuh mensyaratkan kesadaran, maka 'pemahaman fungsional' Y hanyalah pemrosesan dan label 'parsial' menyesatkan.
- [R02-M0001/L1] X tidak menentukan sebelum melihat data dimensi mana yang seharusnya berhasil, sehingga pengelompokan kegagalan dapat dilakukan setelah fakta.
- [R02-M0001/L2] Y tidak mengatakan apa yang terjadi jika kegagalan komitmen menghilang dengan pelatihan yang berbeda — apakah itu berarti pemahaman bertambah atau hanya perilaku yang dipoles?
- [R02-M0001/L3] Konsep 'dimensi pemahaman' X tidak dianalisis: apa yang membuat sesuatu menjadi satu dimensi, bukan sekadar satu jenis tugas?

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
  "packet_id": "P0008-dossier",
  "input_hash": "5f70921b5c859c64668fac14c93253fbf29f78a52e2bbca4b6ac50804c5d8443",
  "fighter_id": "F0005",
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
