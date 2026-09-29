# Paket Kerja P0036-falsification — Uji falsifikasi F0005 — penguji T1

> **Sistem:** Argument Battle Royale · **Tahap:** Uji falsifikasi
> **Topik yang dipertarungkan:** "Apakah AI bisa disebut memahami bahasa?"
> **Bahasa konten keluaran:** Bahasa Indonesia (nama kunci JSON tetap persis seperti contoh).

## Protokol worker (wajib dipatuhi)

1. Paket ini **mandiri**: semua data yang Anda perlukan ada di dalamnya. Jangan membaca file run lain.
2. Kerjakan tugas dengan jujur dan teliti. **Jangan mengarang** sitasi, angka, studi, atau hasil uji.
3. Tulis **hanya JSON valid** (tanpa komentar, tanpa blok kode) ke file:
   `.claude/skills/argument-battle-royale/examples/sample-run/packets/P0036-falsification/output.json`
   JSON wajib memuat `"packet_id": "P0036-falsification"` dan `"input_hash": "2e070abd36eef2959d782a51cdb77b8a531d36e92341b1e44bea893f2f38932f"`.
4. Validasi output Anda dengan perintah berikut, lalu perbaiki sampai hasilnya `OK`:
   `python3 ".claude/skills/argument-battle-royale/scripts/abr.py" check --run ".claude/skills/argument-battle-royale/examples/sample-run" --packet P0036-falsification`
5. **Jangan** menjalankan perintah `next`, dan jangan mengubah file lain di direktori run.
6. Setelah `OK`, balas orkestrator dengan satu baris: `P0036-falsification: OK` (atau `P0036-falsification: GAGAL — <alasan>`).

## Peran Anda

Anda adalah **penguji falsifikasi** (penguji T1). Argumen di bawah adalah **juara bracket**. Kemenangan turnamen **bukan** bukti kebenaran; tugas Anda adalah mencoba **menjatuhkannya** dengan sungguh-sungguh, dalam semangat Popper (mencari sanggahan, bukan konfirmasi) dan Lakatos (membedakan inti keras dari sabuk pelindung, serta mendeteksi penyelamatan ad hoc).
Penekanan Anda: prediksi empiris dan kontra-contoh konkret

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

## Argumen yang diuji

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

## Dosir Final 4

**Dosir argumen ini**

- Bentuk baku:
  - P1: LLM berhasil pada inferensi komposisional baru dan implikatur yang tidak dapat dipecahkan dengan pencocokan literal.
  - P2: LLM menunjukkan kegagalan sistematis (relasi terbalik, kepekaan redaksi, menjilat) yang jarang terjadi pada penutur yang memahami.
  - P3 (tersirat): Pemahaman terdiri dari beberapa dimensi yang dapat berdisosiasi.
  - P4: Hipotesis pemahaman penuh tidak menjelaskan P2; hipotesis pencocokan pola dangkal tidak menjelaskan P1.
  - P5: Hipotesis pemahaman parsial memprediksi profil campuran per dimensi.
  - P6 (tersirat): Hipotesis yang menjelaskan semua data relevan dan membuat prediksi yang dapat diuji lebih layak diterima.
  - C: AI kontemporer memahami bahasa secara parsial dan bergradasi.
- Kerangka formal: D1 ∧ D2; H_penuh ⊬ D2; H_pola ⊬ D1; (M ∧ H_parsial) ⊢ D1 ∧ D2; ⇒ (IBE, P6) terima H_parsial, dengan M = asumsi multidimensionalitas (P3).
- Inti keras: Pemahaman bersifat multidimensional dan bergradasi.; LLM memiliki sebagian dimensi pemahaman secara nyata, bukan semata hafalan.
- Sabuk pelindung: Daftar dimensi spesifik (inferensial, pragmatik lokal, pelacakan komitmen, grounding referensial).; Tafsiran bahwa kegagalan tertentu (relasi terbalik, menjilat) mencerminkan dimensi yang hilang, bukan batas kinerja sementara.
- Falsifier: Kegagalan sistematis hilang sepenuhnya dengan skala atau pelatihan tanpa perubahan arsitektur.; Keberhasilan pada inferensi baru terbukti berasal dari kontaminasi.; Kegagalan tersebar acak dan tidak mengikuti garis dimensi mana pun.
- Keberatan terkuat:
  - [high/partially_answered] Pengelompokan kegagalan ke dalam 'dimensi' dapat dilakukan setelah melihat data, sehingga prediksi per dimensi tidak benar-benar berisiko.
  - [medium/unanswered] Apa yang membuat sesuatu menjadi satu dimensi pemahaman, bukan sekadar satu jenis tugas? Tanpa analisis konseptual, 'dimensi' hanya label untuk kelompok tugas.
  - [medium/partially_answered] Jika pemahaman penuh mensyaratkan kesadaran, 'pemahaman fungsional' hanyalah pemrosesan dan label 'parsial' menyesatkan.
  - [medium/partially_answered] Tanpa ambang minimum, hampir semua sistem pemroses informasi (bahkan termostat) memahami 'sebagian', sehingga label itu kehilangan daya pembeda.
  - [low/answered] Jika kegagalan komitmen hilang karena pelatihan yang berbeda, tidak jelas apakah pemahaman bertambah atau hanya perilaku yang dipoles.
- Kerentanan: Daftar dimensi belum dikunci secara eksplisit sebelum pengujian.; Tidak ada kriteria ambang yang memisahkan 'parsial' dari 'tidak ada'.; Bergantung pada karakterisasi empiris kegagalan yang dapat berubah antar-generasi model.
- Kekuatan: Menjelaskan data keberhasilan dan kegagalan sekaligus, termasuk data yang dipakai lawan.; Membuat prediksi yang dapat diuji dan menyebut falsifier yang jelas.; Cakupan klaim sesuai dengan dukungannya; adil terhadap kedua kubu.
- Penilaian penguji: Argumen ini paling kokoh secara empiris di antara finalis karena menyerap data yang dipakai lawan-lawannya ke dalam satu penjelasan. Titik rawannya konseptual, bukan empiris: 'dimensi' belum dianalisis dan belum dikunci sebelum data dilihat, sehingga keunggulan abduktifnya dapat dituduh post hoc. Jika penyerang berhasil menunjukkan bahwa label 'parsial' tidak memiliki ambang, posisi ini dapat terlihat seperti kompromi yang tidak berisiko. Pembela perlu menunjukkan bahwa dimensi dapat diidentifikasi secara independen dari hasil tugas.

## Riwayat serangan

- [scouting] Batas 'dimensi' pemahaman tidak didefinisikan secara presisi sebelum data dilihat, sehingga ada risiko pengelompokan kegagalan ke dimensi dilakukan secara post hoc.
- [R01-M0001/L7] Jika pemahaman penuh mensyaratkan kesadaran, maka 'pemahaman fungsional' Y hanyalah pemrosesan dan label 'parsial' menyesatkan.
- [R02-M0001/L1] X tidak menentukan sebelum melihat data dimensi mana yang seharusnya berhasil, sehingga pengelompokan kegagalan dapat dilakukan setelah fakta.
- [R02-M0001/L2] Y tidak mengatakan apa yang terjadi jika kegagalan komitmen menghilang dengan pelatihan yang berbeda — apakah itu berarti pemahaman bertambah atau hanya perilaku yang dipoles?
- [R02-M0001/L3] Konsep 'dimensi pemahaman' X tidak dianalisis: apa yang membuat sesuatu menjadi satu dimensi, bukan sekadar satu jenis tugas?
- [R03-M0001/L1] Menerapkan 'memahami' secara bergradasi pada profil yang terdisosiasi adalah keputusan konseptual yang diakui lawan sendiri, sehingga jawaban 'sebagian' bukan temuan faktual.
- [R04-M0001/L1] Hipotesis jarak-distribusi melemahkan komitmen empiris lawan bahwa kegagalan berkelompok menurut dimensi, dan vonis lawan bergantung pada pembobotan yang tidak ditetapkan.

## Hipotesis rival (untuk uji perbandingan)

#### Rival 1 — Uji dunia kontrafaktual

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

#### Rival 2 — Paritas mekanistik: representasi dunia internal

- **Tesis:** LLM mutakhir memahami bahasa dalam arti yang sejenis dengan manusia, karena jenis bukti yang kita terima untuk atribusi pemahaman pada manusia — penggunaan inferensial yang sistematis ditambah representasi internal terstruktur yang secara kausal mengendalikan perilaku — juga ada pada LLM.
- **Definisi:** *memahami*: Memiliki kapasitas fungsional-inferensial untuk memakai ekspresi secara tepat lintas konteks baru, yang dimediasi representasi internal yang terstruktur dan dipakai secara kausal.; *relevansi perbedaan*: Sebuah perbedaan antara dua sistem relevan bagi atribusi pemahaman hanya jika perbedaan itu mengubah kapasitas fungsional yang menjadi kriteria atribusi.
- **Premis:**
  - **P1** (metodologis): Kita mengatribusikan pemahaman kepada manusia lain berdasarkan bukti perilaku (penggunaan tepat, inferensi, generalisasi) dan, dalam sains kognitif, bukti representasi internal yang memediasi perilaku; kita tidak pernah mengakses pemahaman orang lain secara langsung. — *dukungan:* Ini praktik standar psikologi, linguistik, dan kehidupan sehari-hari; masalah pikiran-lain menunjukkan tidak ada akses lain.
  - **P2** (empiris): LLM mutakhir memakai bahasa secara tepat pada situasi yang tidak ada dalam data latihnya: memparafrasekan, menarik inferensi, menerjemahkan, dan menjawab pertanyaan baru yang komposisional. — *dukungan:* Didokumentasikan luas dalam evaluasi dan pemakaian sehari-hari berskala besar.
  - **P3** (empiris): Riset interpretabilitas menemukan representasi internal terstruktur pada model bahasa — misalnya struktur sintaksis, keadaan entitas dalam cerita, relasi geografis dan temporal, serta keadaan papan permainan pada model yang hanya dilatih dengan urutan langkah — dan intervensi pada representasi itu mengubah output sesuai prediksi. — *dukungan:* Temuan probing dan intervensi kausal yang direplikasi oleh beberapa kelompok riset.
  - **P4** (metodologis): Prinsip konsistensi: jika bukti jenis E cukup untuk mengatribusikan H pada satu sistem, E juga cukup untuk sistem lain kecuali ditunjukkan ada perbedaan yang relevan. — *dukungan:* Tanpa prinsip ini atribusi menjadi sewenang-wenang (standar ganda).
  - **P5** (konseptual): Substrat fisik (silikon vs neuron) dan cara perolehan (pelatihan statistik vs perkembangan) bukan perbedaan yang relevan bagi pemahaman sebagai kapasitas fungsional. — *dukungan:* Kapasitas fungsional dapat direalisasikan secara berganda; kita tidak menolak pemahaman penutur yang belajar bahasa lewat cara yang tidak lazim.
- **Inferensi (deduktif):** Dari P1 dan P4: bukti jenis perilaku-plus-representasi cukup untuk atribusi pemahaman kecuali ada perbedaan relevan. P2 dan P3 menunjukkan LLM memiliki bukti jenis itu; P5 menolak dua kandidat perbedaan relevan yang paling sering diajukan. Maka atribusi pemahaman kepada LLM dibenarkan.
- **Kesimpulan:** LLM mutakhir memahami bahasa dalam arti substantif yang sejenis dengan pemahaman manusia, walaupun derajat dan cakupannya dapat lebih rendah di domain tertentu.
- **Komitmen empiris:** Representasi internal LLM dipakai secara kausal oleh model (intervensi mengubah perilaku secara terprediksi).; Kinerja LLM tergeneralisasi ke komposisi baru, bukan hanya mengulang data latih.
- **Falsifier:** Intervensi terkontrol menunjukkan representasi yang ditemukan probing tidak dipakai secara kausal oleh model.; Kinerja runtuh secara sistematis pada distribusi baru dengan cara yang tidak terjadi pada manusia yang dianggap memahami.; Ditunjukkan perbedaan relevan yang prinsipiel, misalnya bahwa kapasitas fungsional yang sama tidak cukup untuk pemahaman pada manusia pula.
- **Keberatan terkuat yang diantisipasi:** Representasi LLM adalah tentang distribusi kata, bukan tentang dunia; tanpa grounding, kesamaan fungsional hanyalah kesamaan di permukaan.
- **Balasan:** Representasi keadaan papan dan relasi geografis yang dipulihkan dari teks bersifat isomorfik dengan struktur dunia dan dipakai kausal; manusia pun memperoleh banyak pengetahuan (sejarah, sains abstrak) hanya melalui bahasa, dan penyandang tunanetra sejak lahir menunjukkan pengetahuan semantik yang kaya tentang kata warna yang dipelajari dari bahasa.
- **Cakupan & kualifikasi:** Klaim terbatas pada pemahaman dalam arti fungsional-inferensial dan pada LLM mutakhir; tidak mengklaim kesadaran, dan mengakui derajat pemahaman dapat bervariasi per domain.

## Prosedur

1. **Komitmen** (`commitments`, 2–12): daftar klaim yang menjadi tanggungan argumen. Tandai `core: true` untuk inti keras (bila jatuh, posisi jatuh) dan `core: false` untuk hipotesis bantu.
2. **Uji** (`tests`, 6–16). Wajib mencakup minimal satu dari setiap jenis: `counterexample`, `reductio`, `rival_comparison`, `edge_case`, `immunization_check`, dan minimal satu `empirical_prediction` atau `conceptual_stress`. Setiap uji menargetkan satu komitmen (`target_commitment`) dan diberi hasil:
   - `passed`: argumen bertahan tanpa kerusakan berarti;
   - `damaged`: argumen bertahan hanya dengan kualifikasi/pembatasan cakupan;
   - `failed`: komitmen yang ditarget terbukti tidak dapat dipertahankan.
   Jalankan uji dengan jujur — jangan membuat uji yang sengaja mudah, dan jangan menggagalkan tanpa alasan yang kuat.
3. **Deteksi imunisasi** (`immunization_detected`): apakah argumen (atau pembelaannya di riwayat) menyelamatkan diri dengan manuver ad hoc yang membuatnya kebal uji?
4. **Verdict** (konsisten dengan hasil uji — divalidasi engine):
   - `FALSIFIED` ⇔ ada uji `failed` pada komitmen `core`;
   - `SURVIVED_WITH_DAMAGE` ⇔ tidak ada `failed` pada core, tetapi ada `damaged` atau `failed` non-core;
   - `SURVIVED` ⇔ semua uji `passed`.
5. `required_qualifications`: kualifikasi yang wajib ditambahkan agar argumen tetap dapat dipertahankan. `residual_confidence` (0–1): seberapa yakin Anda argumen ini tetap dapat dipertahankan setelah uji. `summary`: 3–6 kalimat.

## Mode bukti: `internal`

Gunakan pengetahuan internal Anda saja. Bila Anda merujuk temuan empiris, jelaskan secara umum (mis. "eksperimen priming sosial banyak yang gagal direplikasi") dan tandai ketidakpastian. **Dilarang** mengarang judul studi, penulis, tahun, angka, atau URL. Isi `evidence_mode_used` dengan `"internal"` bila field itu diminta.



## Format output

```json
{
  "packet_id": "P0036-falsification",
  "input_hash": "2e070abd36eef2959d782a51cdb77b8a531d36e92341b1e44bea893f2f38932f",
  "fighter_id": "F0005",
  "evidence_mode_used": "internal",
  "commitments": [
    {
      "id": "C1",
      "claim": "<komitmen>",
      "type": "conceptual",
      "core": true
    }
  ],
  "tests": [
    {
      "id": "T1",
      "kind": "counterexample",
      "target_commitment": "C1",
      "description": "<uji>",
      "result": "passed",
      "reasoning": "<penalaran hasil uji>"
    }
  ],
  "immunization_detected": false,
  "ad_hoc_notes": "<opsional>",
  "verdict": "SURVIVED",
  "required_qualifications": [],
  "residual_confidence": 0.6,
  "summary": "<ringkasan 3-6 kalimat>",
  "evidence": []
}
```
