# Rubrik Pengujian

Rubrik ini mengoperasionalkan standar **filsafat analitik** (kejelasan konseptual, validitas, analisis kontra-contoh, kejujuran dialektis) dan **filsafat sains** (kecukupan empiris, falsifiabilitas Popperian, inferensi ke penjelasan terbaik, parsimoni, program riset Lakatosian). Nilai kanonik ada di `scripts/engine/config.py`; teks yang dilihat juri ada di `templates/_rubric.md`.

## Kriteria dan bobot (total 100)

| # | Kunci | Bobot | Akar filosofis | Pertanyaan penguji |
|---|---|---:|---|---|
| 1 | `clarity` | 10 | Analisis konseptual (Frege, Carnap: eksplikasi) | Istilah kunci tegas, tanpa ekuivokasi? |
| 2 | `validity` | 15 | Logika deduktif; kekuatan induktif/abduktif | Kesimpulan mengikuti dari premis? |
| 3 | `premise_plausibility` | 15 | Soundness; beban pembuktian | Premis masuk akal bagi penalar netral yang kompeten? |
| 4 | `empirical_adequacy` | 10 | van Fraassen: kecukupan empiris | Sesuai bukti ilmiah terbaik? |
| 5 | `falsifiability` | 10 | Popper: risiko prediktif | Menyebut kondisi yang akan menjatuhkannya? |
| 6 | `counterexample_robustness` | 10 | Metode kasus/eksperimen pikiran (Gettier-style) | Bertahan terhadap kontra-contoh dan kasus batas? |
| 7 | `explanatory_power` | 10 | IBE (Harman, Lipton); konsiliensi (Whewell) | Menjelaskan lebih banyak, lebih dalam, lebih baik dari rival? |
| 8 | `parsimony` | 5 | Pisau Occam | Tanpa entitas/asumsi yang tak perlu? |
| 9 | `coherence` | 5 | Koherentisme; konsistensi dengan sains mapan | Koheren dengan pengetahuan latar? |
| 10 | `dialectical_charity` | 10 | Prinsip kemurahan (Davidson); steelmanning | Menghadapi keberatan terkuat dan membatasi cakupan klaim secara jujur? |

**Total tertimbang** = Σ(skor × bobot) / 10 → skala 0–100.

**Kalibrasi skala:** 0–2 cacat serius · 3–4 lemah · 5 rata-rata kompeten · 6–7 kuat · 8 sangat kuat · 9–10 luar biasa dan langka.

**Adaptasi per jenis pertanyaan.** Untuk klaim konseptual/normatif/metafisis, `empirical_adequacy` dibaca sebagai "tidak bertentangan dengan fakta relevan dan memanfaatkan bukti yang ada", dan `falsifiability` sebagai "keterujian konseptual": apakah posisi menyebut kontra-contoh atau implikasi yang, bila terbukti, akan menjatuhkannya. Bobot sengaja **tidak** diubah per topik agar hasil lintas run dapat dibandingkan dan tidak ada ruang untuk menyetel rubrik demi hasil tertentu.

## Cacat fatal

Argumen dengan lebih sedikit cacat fatal menang lebih dulu, sebelum total skor dibandingkan.

| Kode | Makna |
|---|---|
| `FF_CIRCULAR` | Petitio principii: kesimpulan diasumsikan dalam premis |
| `FF_CONTRADICTION` | Kontradiksi internal |
| `FF_EQUIVOCATION` | Istilah kunci berganti makna di tengah argumen |
| `FF_NON_SEQUITUR` | Inferensi sentral tidak mengikuti |
| `FF_STRAWMAN` | Posisi lawan yang menjadi tumpuan disalahrepresentasikan |
| `FF_AD_HOC` | Imunisasi: posisi dibuat kebal dari segala bukti tandingan |
| `FF_FALSE_CORE_FACT` | Klaim faktual inti yang jelas keliru |
| `FF_PERSUASIVE_DEFINITION` | Definisi yang memenangkan perdebatan secara verbal |

## Kode diskualifikasi (tahap VALIDASI)

Kelemahan biasa **bukan** alasan diskualifikasi — itu tercermin di skor.

| Kode | Makna |
|---|---|
| `DQ_NOT_ARGUMENT` | Tidak memiliki struktur inferensial |
| `DQ_OFF_TOPIC` | Tidak menjawab topik |
| `DQ_NO_POSITION` | Tidak mengambil posisi |
| `DQ_CONTRADICTION` | Kontradiksi internal yang tidak dapat diperbaiki |
| `DQ_CIRCULAR` | Sirkular secara terang-terangan |
| `DQ_UNINTELLIGIBLE` | Tidak dapat dipahami |
| `DQ_FALSE_CORE_FACT` | Bertumpu pada fakta inti yang jelas keliru |
| `DQ_STANCE_MISMATCH` | Kesimpulan bertentangan dengan posisi yang ditugaskan |
| `DQ_UNSCORED` | (engine) paket scouting gagal berulang kali |

## Lensa juri panel

Semua lensa memakai rubrik yang sama; lensa hanya menentukan apa yang diperiksa paling keras. Panel berukuran k memakai lensa L1..Lk.

| ID | Lensa | Fokus |
|---|---|---|
| L1 | Logikawan formal | Bentuk logis, validitas, sesat pikir, ekuivokasi |
| L2 | Filsuf sains | Kecukupan empiris, falsifiabilitas, IBE, parsimoni, Lakatos |
| L3 | Analis konseptual | Definisi, kondisi perlu/cukup, eksperimen pikiran, kontra-contoh |
| L4 | Skeptis / advokat setan | Serangan terkuat, beban pembuktian, asumsi tersembunyi |
| L5 | Metodolog bukti | Kualitas bukti, base rate, bias seleksi, generalisasi berlebihan |
| L6 | Hakim dialektis-integratif | Kejujuran dialektis, konsiliensi, kesesuaian cakupan klaim |
| L7 | Generalis mata-segar | Penilaian menyeluruh; juga juri tunggal babak eliminasi |

## Disiplin anti-bias (dicetak di setiap paket juri)

- Urutan X/Y diacak per (duel, juri); posisi tidak bermakna.
- Panjang ≠ mutu; nada yakin ≠ mutu; istilah teknis ≠ kedalaman.
- Nilai ketahanan terhadap rubrik, bukan persetujuan dengan kesimpulan.
- Jangan menghukum posisi yang tidak populer; hukum kelemahan penalarannya.
- Juri duel tidak melihat ID petarung, unggulan, maupun skor scouting.

## Protokol uji falsifikasi

1. **Komitmen** (2–12), masing-masing ditandai `core` (inti keras) atau bantu.
2. **Uji** (6–16), wajib mencakup `counterexample`, `reductio`, `rival_comparison`, `edge_case`, `immunization_check`, dan minimal satu `empirical_prediction` atau `conceptual_stress`. Hasil: `passed` / `damaged` / `failed`.
3. **Verdict** (divalidasi engine):
   - `FALSIFIED` ⇔ ada uji `failed` pada komitmen core;
   - `SURVIVED_WITH_DAMAGE` ⇔ tidak ada `failed` pada core, tetapi ada `damaged` atau `failed` non-core;
   - `SURVIVED` ⇔ semua uji `passed`.
4. `required_qualifications`, `residual_confidence` (0–1), `immunization_detected`, ringkasan.
