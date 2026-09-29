# Paket Kerja P0001-map — Peta ruang argumen

> **Sistem:** Argument Battle Royale · **Tahap:** Pemetaan ruang argumen
> **Topik yang dipertarungkan:** "Apakah AI bisa disebut memahami bahasa?"
> **Bahasa konten keluaran:** Bahasa Indonesia (nama kunci JSON tetap persis seperti contoh).

## Protokol worker (wajib dipatuhi)

1. Paket ini **mandiri**: semua data yang Anda perlukan ada di dalamnya. Jangan membaca file run lain.
2. Kerjakan tugas dengan jujur dan teliti. **Jangan mengarang** sitasi, angka, studi, atau hasil uji.
3. Tulis **hanya JSON valid** (tanpa komentar, tanpa blok kode) ke file:
   `.claude/skills/argument-battle-royale/examples/sample-run/packets/P0001-map/output.json`
   JSON wajib memuat `"packet_id": "P0001-map"` dan `"input_hash": "d254642821e1e7a1aa70b836c29f702dfb191f1170bc3101e7acc9bddf40af91"`.
4. Validasi output Anda dengan perintah berikut, lalu perbaiki sampai hasilnya `OK`:
   `python3 ".claude/skills/argument-battle-royale/scripts/abr.py" check --run ".claude/skills/argument-battle-royale/examples/sample-run" --packet P0001-map`
5. **Jangan** menjalankan perintah `next`, dan jangan mengubah file lain di direktori run.
6. Setelah `OK`, balas orkestrator dengan satu baris: `P0001-map: OK` (atau `P0001-map: GAGAL — <alasan>`).

## Peran Anda

Anda adalah **kartografer argumen**: filsuf analitik yang memetakan seluruh ruang jawaban yang dapat dipertahankan secara rasional untuk topik di atas. Peta Anda akan dipakai untuk menghasilkan 16 "petarung" (argumen) yang beragam, lalu mengadu mereka dalam turnamen eliminasi. Kualitas turnamen bergantung pada **kelengkapan dan netralitas** peta ini.

## Tugas

1. **Rumuskan ulang topik** secara presisi (`topic_restated`) sebagai pertanyaan yang dapat dijawab dengan argumen. Jika topik ambigu, rumuskan versi yang paling bermakna dan catat ambiguitasnya di `presuppositions`/`notes`.
2. **Jenis pertanyaan** (`question_type`): `conceptual`, `empirical`, `normative`, `metaphysical`, atau `mixed`.
3. **Presuposisi** (`presuppositions`): asumsi yang dibawa oleh pertanyaan. Presuposisi yang dapat digugat membuka posisi "melarutkan/mendeflasi pertanyaan".
4. **Istilah kunci** (`key_terms`, 1–6): untuk setiap istilah yang menentukan jawaban, berikan 1–6 **bacaan** (definisi alternatif) dengan `id` unik lintas semua istilah (mis. `T1a`, `T1b`, `T2a`).
5. **Posisi** (`stances`, 3–6): jawaban-jawaban yang saling dapat dibedakan dan bersama-sama sedekat mungkin mencakup seluruh ruang (mis. afirmatif kuat, afirmatif bersyarat, negatif, negatif bersyarat, deflasioner/pelarut pertanyaan). Beri id `S1`, `S2`, ...
6. **Kerangka** (`frameworks`, 3–12): tradisi teoretis atau disiplin yang relevan (filsafat maupun sains/bidang terkait). Beri id `K1`, `K2`, ... Isi `compatible_stances` (list id posisi) hanya bila sebuah kerangka jelas tidak dapat mendukung posisi tertentu; jika tidak, hilangkan field itu.
7. **Strategi argumentasi** (`strategies`, 3–8): metode pembuktian, mis. analisis konseptual, eksperimen pikiran, bukti empiris, inferensi ke penjelasan terbaik, reductio ad absurdum, analogi, argumen transendental, argumen pragmatis/teori keputusan, genealogi historis, model formal. Beri id `M1`, `M2`, ...
8. **Titik krusial** (`cruxes`, 2–12): butir ketidaksepakatan yang, jika diselesaikan, paling menentukan jawaban.
9. **Domain bukti** (`evidence_domains`): bidang ilmu/data yang relevan.

## Aturan netralitas

- Deskripsikan setiap posisi dalam versi **terkuatnya** (steelman), bukan karikatur.
- Jangan memasukkan preferensi Anda. Peta harus dapat diterima oleh pendukung setiap posisi sebagai deskripsi yang adil.
- Jangan membuat posisi yang hanya berbeda redaksi; setiap posisi harus berbeda secara substantif.

## Format output

```json
{
  "packet_id": "P0001-map",
  "input_hash": "d254642821e1e7a1aa70b836c29f702dfb191f1170bc3101e7acc9bddf40af91",
  "topic_restated": "<rumusan presisi topik>",
  "question_type": "conceptual",
  "presuppositions": [
    "<presuposisi>"
  ],
  "key_terms": [
    {
      "term": "<istilah>",
      "readings": [
        {
          "id": "T1a",
          "label": "<nama bacaan>",
          "definition": "<definisi>"
        }
      ]
    }
  ],
  "stances": [
    {
      "id": "S1",
      "label": "<posisi>",
      "description": "<versi terkuat posisi>"
    }
  ],
  "frameworks": [
    {
      "id": "K1",
      "label": "<kerangka>",
      "description": "<deskripsi>",
      "compatible_stances": [
        "S1",
        "S2"
      ]
    }
  ],
  "strategies": [
    {
      "id": "M1",
      "label": "<strategi>",
      "description": "<deskripsi>"
    }
  ],
  "cruxes": [
    "<titik krusial>"
  ],
  "evidence_domains": [
    "<bidang>"
  ],
  "notes": "<catatan opsional>"
}
```
