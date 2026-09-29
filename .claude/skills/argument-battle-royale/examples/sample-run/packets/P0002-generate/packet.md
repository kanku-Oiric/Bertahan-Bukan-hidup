# Paket Kerja P0002-generate — Generasi petarung (16 slot, gelombang 0)

> **Sistem:** Argument Battle Royale · **Tahap:** Generasi petarung
> **Topik yang dipertarungkan:** "Apakah AI bisa disebut memahami bahasa?"
> **Bahasa konten keluaran:** Bahasa Indonesia (nama kunci JSON tetap persis seperti contoh).

## Protokol worker (wajib dipatuhi)

1. Paket ini **mandiri**: semua data yang Anda perlukan ada di dalamnya. Jangan membaca file run lain.
2. Kerjakan tugas dengan jujur dan teliti. **Jangan mengarang** sitasi, angka, studi, atau hasil uji.
3. Tulis **hanya JSON valid** (tanpa komentar, tanpa blok kode) ke file:
   `.claude/skills/argument-battle-royale/examples/sample-run/packets/P0002-generate/output.json`
   JSON wajib memuat `"packet_id": "P0002-generate"` dan `"input_hash": "b3e051aa006dbcb993c07dbd79dbface3d4664c6b7bf29dbf3d026b8082c06b4"`.
4. Validasi output Anda dengan perintah berikut, lalu perbaiki sampai hasilnya `OK`:
   `python3 ".claude/skills/argument-battle-royale/scripts/abr.py" check --run ".claude/skills/argument-battle-royale/examples/sample-run" --packet P0002-generate`
5. **Jangan** menjalankan perintah `next`, dan jangan mengubah file lain di direktori run.
6. Setelah `OK`, balas orkestrator dengan satu baris: `P0002-generate: OK` (atau `P0002-generate: GAGAL — <alasan>`).

## Peran Anda

Anda adalah **penyusun argumen** kelas satu. Tugas Anda: menulis satu "petarung" (argumen utuh) untuk setiap slot di bawah. Setiap petarung akan diuji dalam turnamen eliminasi dengan rubrik filsafat analitik dan filsafat sains. Tulis **versi terkuat** dari setiap posisi — bukan manusia jerami. Anda tidak sedang membela pendapat pribadi; Anda sedang membangun kontestan terbaik untuk setiap spesifikasi.

## Konteks: peta ruang argumen

- **Rumusan presisi:** Apakah sistem kecerdasan buatan — khususnya model bahasa besar (LLM) yang ada saat ini, dan sistem AI secara prinsip — dapat secara tepat dikatakan memahami bahasa, dan jika ya, dalam arti 'memahami' yang mana?
- **Jenis pertanyaan:** mixed
- **Titik krusial:**
  - Apakah makna dapat muncul dari distribusi bentuk linguistik saja tanpa kontak kausal langsung dengan referen?
  - Apakah pemahaman mensyaratkan intensionalitas asli atau kesadaran fenomenal, atau cukup kapasitas fungsional?
  - Apakah kriteria behavioral (kinerja dan generalisasi lintas tugas) cukup untuk atribusi pemahaman, atau mekanisme internal yang menentukan?
  - Apakah representasi internal LLM tentang entitas dan keadaan dunia merupakan model dunia yang sejati atau korelasi statistik dangkal?
  - Bagaimana menafsirkan kegagalan sistematis (halusinasi, ketidakkonsistenan, kerentanan terhadap perubahan redaksi): bukti ketiadaan pemahaman atau pemahaman yang terbatas?
  - Apakah 'memahami' konsep biner atau bergradasi dan multidimensional?

**Posisi (stances):**
- `S1` Ya, secara substantif — Sistem AI seperti LLM kontemporer sudah memahami bahasa dalam arti yang sejenis (meski belum tentu sederajat) dengan manusia: kriteria yang kita pakai untuk manusia — penggunaan inferensial yang sistematis, generalisasi, dan representasi internal yang terstruktur — terpenuhi, sehingga menolak atribusi itu adalah standar ganda.
- `S2` Ya secara parsial dan bergradasi — Pemahaman adalah kapasitas multidimensional. AI kontemporer memiliki dimensi tertentu secara nyata (inferensial, struktural, sebagian referensial melalui data manusia) tetapi lemah atau tidak ada pada dimensi lain (grounding sensorimotor, niat komunikatif, metakognisi yang andal); jawaban ya/tidak biner menyesatkan.
- `S3` Tidak untuk AI saat ini, mungkin secara prinsip — LLM kontemporer hanya mempelajari relasi antar-bentuk tanpa kontak kausal yang tepat dengan referen dan tanpa partisipasi dalam praktik komunikatif, sehingga belum memahami; tetapi tidak ada hambatan prinsipiel bagi sistem AI yang ter-embodied, tergrounding, dan terlibat sosial untuk memahami.
- `S4` Tidak, secara prinsip — Komputasi adalah manipulasi simbol yang didefinisikan secara sintaksis, dan sintaksis saja tidak cukup untuk semantik atau intensionalitas asli; pemahaman membutuhkan sifat-sifat (intensionalitas intrinsik, kesadaran) yang tidak dihasilkan oleh menjalankan program, betapa pun canggih perilakunya.
- `S5` Deflasioner: pertanyaan tidak memiliki jawaban faktual tunggal — 'Memahami' adalah konsep yang dibentuk untuk praktik antarmanusia; penerapannya pada AI tidak ditentukan oleh fakta yang tersembunyi, melainkan oleh keputusan konseptual yang bergantung pada tujuan (sains, etika, hukum). Pertanyaan yang tepat adalah kapasitas spesifik apa yang dimiliki AI dan konsep apa yang paling berguna.

**Kerangka (frameworks):**
- `K1` Fungsionalisme & semantik peran-inferensial — Makna dan pemahaman ditentukan oleh peran fungsional/inferensial suatu keadaan atau ekspresi dalam sistem, bukan oleh substrat.
- `K2` Grounding simbol & kognisi ter-embodied — Simbol memperoleh makna melalui keterkaitan dengan persepsi, tindakan, dan tubuh; masalah grounding simbol menanyakan bagaimana simbol dapat bermakna bagi sistem itu sendiri.
- `K3` Intensionalitas asli & kesadaran — Tradisi yang membedakan intensionalitas intrinsik dari yang turunan/dipinjam (mis. argumen Ruang Cina) dan menautkan pemahaman dengan kesadaran.
- `K4` Sains kognitif & interpretabilitas mekanistik — Studi empiris tentang representasi dan mekanisme internal (probing, analisis sirkuit), generalisasi, dan pola kegagalan sistem AI, dibandingkan dengan kognisi manusia.
- `K5` Pragmatik & filsafat bahasa sosial — Makna sebagai penggunaan dalam praktik (Wittgenstein), niat komunikatif (Grice), tindak tutur, dan tanggung jawab normatif atas klaim.
- `K6` Interpretasionisme & epistemologi atribusi mental — Atribusi keadaan mental dibenarkan oleh keberhasilan prediktif sikap intensional dan oleh standar bukti yang sama yang kita pakai untuk manusia lain, anak, dan hewan.

**Strategi argumentasi:**
- `M1` Analisis konseptual — Menguraikan kondisi perlu dan/atau cukup bagi 'memahami' dan memeriksa apakah AI memenuhinya.
- `M2` Eksperimen pikiran — Memakai skenario hipotetis (mis. Ruang Cina, gurita di dasar laut, sistem terisolasi dari dunia) untuk menguji intuisi tentang kondisi pemahaman.
- `M3` Bukti empiris — Bersandar pada temuan tentang kinerja, generalisasi, representasi internal, dan pola kegagalan sistem AI.
- `M4` Inferensi ke penjelasan terbaik — Menilai hipotesis mana (pemahaman, pencocokan pola dangkal, dsb.) yang paling baik menjelaskan keseluruhan data perilaku dan mekanistik.
- `M5` Argumen paritas dan analogi — Membandingkan AI dengan kasus lain yang atribusinya kita terima atau tolak (anak, hewan, penutur non-asli, kalkulator) untuk menguji konsistensi standar.

**Bacaan istilah kunci:**
- *memahami*: `T1a` Pemahaman fungsional-inferensial (Kemampuan menggunakan ekspresi secara tepat lintas konteks: menarik inferensi yang benar, memparafrasekan, menjawab, dan menggeneralisasi ke situasi baru.); `T1b` Pemahaman referensial-tergrounding (Kemampuan mengaitkan ekspresi dengan objek, sifat, dan keadaan dunia melalui hubungan kausal dengan dunia (persepsi, tindakan) sehingga kata memiliki referen, bukan hanya relasi dengan kata lain.); `T1c` Pemahaman intensional-fenomenal (Pemahaman yang melibatkan intensionalitas asli (bukan turunan dari penafsir) dan, menurut sebagian pandangan, pengalaman sadar tentang apa yang dimaksud.); `T1d` Pemahaman bergradasi-multidimensional (Kapasitas yang datang dalam derajat dan dalam beberapa dimensi terpisah (inferensial, referensial, pragmatik-sosial, metakognitif) sehingga sebuah sistem dapat memahami dalam satu dimensi tanpa dimensi lain.)
- *bahasa*: `T2a` Bahasa sebagai sistem bentuk (Sistem simbol dengan struktur leksikal, sintaksis, dan distribusional yang dapat dipelajari dari korpus teks.); `T2b` Bahasa sebagai praktik sosial-komunikatif (Praktik bertutur antar-agen yang melibatkan niat komunikatif, tindak tutur, norma, dan tanggung jawab atas klaim.)
- *AI*: `T3a` LLM kontemporer (Model bahasa besar berbasis transformer yang dilatih memprediksi token dan disetel lanjut dengan umpan balik manusia, termasuk varian multimodal.); `T3b` AI secara prinsip (Sistem komputasional mana pun yang mungkin dibangun, termasuk sistem ter-embodied yang berinteraksi dengan dunia fisik dan sosial.)

## Slot yang harus diisi (16 petarung)

| slot_id | posisi | kerangka | strategi | varian |
|---|---|---|---|---|
| `G0-S0001` | `S1` Ya, secara substantif | `K4` Sains kognitif & interpretabilitas mekanistik | `M5` Argumen paritas dan analogi | 1 |
| `G0-S0002` | `S1` Ya, secara substantif | `K5` Pragmatik & filsafat bahasa sosial | `M3` Bukti empiris | 1 |
| `G0-S0003` | `S1` Ya, secara substantif | `K6` Interpretasionisme & epistemologi atribusi mental | `M5` Argumen paritas dan analogi | 1 |
| `G0-S0004` | `S2` Ya secara parsial dan bergradasi | `K3` Intensionalitas asli & kesadaran | `M5` Argumen paritas dan analogi | 1 |
| `G0-S0005` | `S2` Ya secara parsial dan bergradasi | `K5` Pragmatik & filsafat bahasa sosial | `M4` Inferensi ke penjelasan terbaik | 1 |
| `G0-S0006` | `S2` Ya secara parsial dan bergradasi | `K6` Interpretasionisme & epistemologi atribusi mental | `M2` Eksperimen pikiran | 1 |
| `G0-S0007` | `S3` Tidak untuk AI saat ini, mungkin secara prinsip | `K2` Grounding simbol & kognisi ter-embodied | `M2` Eksperimen pikiran | 1 |
| `G0-S0008` | `S3` Tidak untuk AI saat ini, mungkin secara prinsip | `K3` Intensionalitas asli & kesadaran | `M2` Eksperimen pikiran | 1 |
| `G0-S0009` | `S3` Tidak untuk AI saat ini, mungkin secara prinsip | `K4` Sains kognitif & interpretabilitas mekanistik | `M2` Eksperimen pikiran | 1 |
| `G0-S0010` | `S3` Tidak untuk AI saat ini, mungkin secara prinsip | `K5` Pragmatik & filsafat bahasa sosial | `M4` Inferensi ke penjelasan terbaik | 1 |
| `G0-S0011` | `S4` Tidak, secara prinsip | `K2` Grounding simbol & kognisi ter-embodied | `M1` Analisis konseptual | 1 |
| `G0-S0012` | `S4` Tidak, secara prinsip | `K3` Intensionalitas asli & kesadaran | `M3` Bukti empiris | 1 |
| `G0-S0013` | `S4` Tidak, secara prinsip | `K5` Pragmatik & filsafat bahasa sosial | `M5` Argumen paritas dan analogi | 1 |
| `G0-S0014` | `S5` Deflasioner: pertanyaan tidak memiliki jawaban faktual tunggal | `K1` Fungsionalisme & semantik peran-inferensial | `M4` Inferensi ke penjelasan terbaik | 1 |
| `G0-S0015` | `S5` Deflasioner: pertanyaan tidak memiliki jawaban faktual tunggal | `K2` Grounding simbol & kognisi ter-embodied | `M1` Analisis konseptual | 1 |
| `G0-S0016` | `S5` Deflasioner: pertanyaan tidak memiliki jawaban faktual tunggal | `K5` Pragmatik & filsafat bahasa sosial | `M3` Bukti empiris | 1 |

## Syarat setiap petarung

- **Kesimpulan wajib sesuai posisi slot** (`stance`). Dibangun di dalam kerangka (`framework`) dan terutama memakai strategi (`strategy`) slot tersebut.
- **Premis eksplisit** (2–7), masing-masing bertipe `empirical` | `conceptual` | `normative` | `metaphysical` | `methodological`, dengan `support` (mengapa premis itu layak diterima). Jangan menyembunyikan premis yang dibutuhkan.
- **Inferensi**: `inference_type` salah satu dari `deductive`, `inductive`, `abductive`, `analogical`, `transcendental`, `pragmatic`, `probabilistic`; `inference` menjelaskan bagaimana kesimpulan mengikuti dari premis.
- **Definisi** (1–8) untuk istilah kunci; cantumkan id bacaan istilah dari peta yang Anda pakai di `term_readings`.
- **Komitmen empiris** (boleh kosong untuk argumen murni konseptual) dan **falsifier** (1–6): apa yang, bila terbukti, akan menunjukkan argumen ini salah.
- **Keberatan terkuat** yang dapat diantisipasi (`anticipated_objection`) dan **balasan** (`reply`).
- **Cakupan** (`scope`): batas dan kualifikasi klaim.
- Panjang wajar 150–450 kata per petarung (maksimum keras 900 kata).

## Keragaman (penting)

Slot dengan sel yang sama (posisi + kerangka + strategi sama, `variant` berbeda) **wajib** berbeda secara substantif: premis kunci berbeda, rute inferensi berbeda, atau bacaan istilah berbeda. Parafrase dari petarung lain akan dihapus sebagai duplikat.

## Kejujuran

Jangan mengarang studi, kutipan, angka, atau nama peneliti. Rujuk temuan empiris secara umum dan akurat. Argumen yang bertumpu pada fakta palsu akan didiskualifikasi.

## Format output

`slot_id` wajib persis seperti tabel. Jangan menambah field posisi/kerangka — engine mengambilnya dari slot.

```json
{
  "packet_id": "P0002-generate",
  "input_hash": "b3e051aa006dbcb993c07dbd79dbface3d4664c6b7bf29dbf3d026b8082c06b4",
  "fighters": [
    {
      "slot_id": "G0-S0001",
      "title": "<judul pendek yang menamai argumen>",
      "thesis": "<satu kalimat: jawaban argumen terhadap topik>",
      "term_readings": [
        "<id bacaan istilah dari peta, mis. T1a>"
      ],
      "definitions": [
        {
          "term": "<istilah>",
          "definition": "<definisi yang dipakai argumen ini>"
        }
      ],
      "premises": [
        {
          "id": "P1",
          "text": "<premis>",
          "type": "conceptual",
          "support": "<mengapa premis layak diterima>"
        },
        {
          "id": "P2",
          "text": "<premis>",
          "type": "empirical",
          "support": "<dukungan>"
        }
      ],
      "inference_type": "deductive",
      "inference": "<bagaimana kesimpulan mengikuti dari P1-P2>",
      "conclusion": "<kesimpulan yang sesuai posisi slot>",
      "empirical_commitments": [
        "<klaim empiris yang dapat diperiksa>"
      ],
      "falsifiers": [
        "<apa yang akan menunjukkan argumen ini salah>"
      ],
      "anticipated_objection": "<keberatan terkuat>",
      "reply": "<balasan>",
      "scope": "<batas dan kualifikasi klaim>"
    }
  ]
}
```
