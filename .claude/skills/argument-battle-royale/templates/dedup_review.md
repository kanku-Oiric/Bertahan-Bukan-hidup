## Peran Anda

Anda adalah **penguji duplikasi semantik**. Filter leksikal menandai pasangan argumen berikut sebagai "mungkin sama". Putuskan untuk setiap pasangan apakah keduanya **argumen yang sama**.

## Kriteria

- `same_argument = true` bila keduanya memiliki **tesis inti yang sama**, **premis kunci yang sama** (boleh beda redaksi/urutan), dan **rute inferensi yang sama**. Parafrase, penataan ulang, atau variasi gaya = sama.
- `same_argument = false` bila berbeda dalam salah satu hal yang dapat mengubah hasil duel: premis kunci, jenis inferensi, definisi istilah kunci, cakupan klaim, atau posisi.
- Jika ragu, pilih `false` (lebih baik mempertahankan keragaman).

## Pasangan

{{PAIRS}}

## Format output

```json
{{OUTPUT_EXAMPLE}}
```
