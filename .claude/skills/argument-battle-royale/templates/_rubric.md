## Rubrik pengujian (filsafat analitik + filsafat sains)

Nilai setiap kriteria **0–10** (boleh desimal .5). Urutan array skor **wajib** sama dengan tabel ini.

| # | Kunci | Bobot | Pertanyaan penguji |
|---|-------|------:|--------------------|
| 1 | `clarity` | 10 | Apakah istilah kunci didefinisikan tegas, tanpa kekaburan atau ekuivokasi? Apakah klaimnya dapat dinyatakan ulang secara presisi? |
| 2 | `validity` | 15 | Apakah kesimpulan mengikuti dari premis? Deduktif: valid? Induktif/abduktif/analogis: seberapa kuat dukungan inferensialnya? Ada lompatan tersembunyi? |
| 3 | `premise_plausibility` | 15 | Seberapa masuk akal premis-premisnya bagi penalar yang kompeten dan netral? Apakah ada premis kontroversial yang dibiarkan tanpa dukungan? |
| 4 | `empirical_adequacy` | 10 | Apakah klaim empirisnya sesuai dengan bukti ilmiah terbaik yang diketahui? Untuk argumen non-empiris: apakah ia tidak bertentangan dengan fakta yang relevan? |
| 5 | `falsifiability` | 10 | Apakah argumen mengambil risiko: menyebut kondisi yang akan membuktikannya salah (observasi, kontra-contoh, implikasi yang dapat diperiksa)? Posisi yang kebal dari segala kemungkinan tandingan dinilai rendah. |
| 6 | `counterexample_robustness` | 10 | Apakah argumen bertahan terhadap kontra-contoh, eksperimen pikiran, dan kasus batas yang paling jelas? |
| 7 | `explanatory_power` | 10 | Seberapa banyak fenomena relevan yang dijelaskan, seberapa dalam, dan seberapa baik dibanding rival (inferensi ke penjelasan terbaik, konsiliensi)? |
| 8 | `parsimony` | 5 | Apakah argumen menghindari entitas, asumsi, atau mekanisme yang tidak diperlukan (pisau Occam)? |
| 9 | `coherence` | 5 | Apakah argumen koheren dengan pengetahuan latar yang mapan di bidang-bidang terkait? |
| 10 | `dialectical_charity` | 10 | Apakah argumen menghadapi keberatan terkuat (steelman), membatasi cakupan klaim sesuai dukungannya, dan menanggung beban pembuktian secara jujur? |

**Kalibrasi skala:** 0–2 cacat serius · 3–4 lemah · 5 rata-rata kompeten · 6–7 kuat · 8 sangat kuat · 9–10 luar biasa dan langka. Gunakan seluruh skala; jangan mengumpulkan semua skor di 6–8.

**Adaptasi per jenis pertanyaan:** untuk klaim konseptual/normatif/metafisis, baca `empirical_adequacy` sebagai "tidak bertentangan dengan fakta relevan dan memanfaatkan bukti yang ada bila relevan", dan `falsifiability` sebagai "keterujian konseptual": apakah posisi menyebut kontra-contoh atau implikasi yang, bila terbukti, akan menjatuhkannya. Jangan menghukum argumen konseptual hanya karena tidak eksperimental.

### Cacat fatal (kode)

Catat hanya bila benar-benar ada dan sentral bagi argumen:
{{FATAL_FLAWS}}

### Aturan keputusan (dihitung ulang oleh engine dari skor Anda)

1. Argumen dengan **lebih sedikit cacat fatal** menang.
2. Jika jumlah cacat fatal sama, **total tertimbang** (Σ skor×bobot/10, skala 0–100) lebih tinggi menang.
3. Jika selisih total < {{NEAR_TIE}} poin (seri praktis), **pilihan holistik Anda** (`winner`) yang menentukan.

Jadi skor Anda harus mencerminkan penilaian Anda yang sesungguhnya. Pilihan `winner` yang bertentangan dengan skor Anda sendiri akan dicatat sebagai inkonsistensi juri.

### Disiplin anti-bias

- Urutan X/Y diacak; posisi tidak bermakna.
- Panjang ≠ mutu. Nada yakin ≠ mutu. Istilah teknis ≠ kedalaman.
- Nilai **ketahanan argumen terhadap rubrik**, bukan apakah Anda setuju dengan kesimpulannya. Dua argumen bisa saja memiliki posisi yang sama.
- Jangan menghukum argumen karena posisinya tidak populer; hukum kelemahan penalarannya.

