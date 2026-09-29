# Contoh Input

Skill menerima topik apa pun yang dapat dirumuskan sebagai masalah argumentatif. Parameter opsional ditulis sebagai `key=value` setelah topik; tanpa parameter, run memakai `mode=balanced population=1000`.

## Penggunaan minimal

```text
/argument-battle-royale "Apakah AI benar-benar memahami bahasa?"
```

## Lintas domain

| Domain | Contoh pemanggilan |
|---|---|
| Filsafat pikiran | `/argument-battle-royale "Apakah kesadaran dapat direduksi menjadi proses fisik?"` |
| Etika / filsafat agama | `/argument-battle-royale "Apakah moralitas membutuhkan Tuhan?" mode=full` |
| Teori politik | `/argument-battle-royale "Apakah demokrasi selalu menghasilkan keputusan yang lebih baik?" population=500` |
| Ekonomi | `/argument-battle-royale "Apakah kapitalisme merupakan sistem ekonomi yang efisien?" evidence_mode=web_if_available` |
| Teknologi / AI | `/argument-battle-royale "Apakah AI bisa disebut memahami bahasa?" mode=efficient population=200` |
| Filsafat sains | `/argument-battle-royale "Apakah teori yang tidak dapat difalsifikasi tetap ilmiah?"` |
| Hukum | `/argument-battle-royale "Apakah hukuman mati dapat dibenarkan secara moral dan konstitusional?" deep_round_threshold=64` |
| Sosial | `/argument-battle-royale "Apakah media sosial menurunkan kualitas deliberasi publik?" evidence_mode=web_if_available` |
| Epistemologi | `/argument-battle-royale "Apakah pengetahuan membutuhkan kepastian?" language=en` |
| Konseptual | `/argument-battle-royale "Apakah matematika ditemukan atau diciptakan?"` |

## Kombinasi parameter

```text
# Uji cepat untuk melihat bentuk ruang argumen
/argument-battle-royale "Apakah kehendak bebas kompatibel dengan determinisme?" population=32 mode=efficient

# Run mendalam, reproduktif, dengan direktori eksplisit
/argument-battle-royale "Apakah hewan memiliki hak moral?" mode=full random_seed=42 output_dir=runs/hak-hewan

# Batasi paralelisme (mis. kuota API terbatas)
/argument-battle-royale "Apakah UBI mengurangi insentif kerja?" max_parallel=2 evidence_mode=web_if_available

# Lanjutkan run yang terputus (resume=true adalah default)
/argument-battle-royale "Apakah AI benar-benar memahami bahasa?"

# Paksa run baru untuk topik yang sama
/argument-battle-royale "Apakah AI benar-benar memahami bahasa?" resume=false
```

## Bahasa alami juga diterima

```text
Tolong adu argumen-argumen tentang apakah pasar bebas adil, pakai mode efficient dengan 100 petarung.
```

Orkestrator menerjemahkannya menjadi `init "Apakah pasar bebas adil?" mode=efficient population=100`.

## Topik yang perlu dirumuskan ulang

| Input | Masalah | Tindakan |
|---|---|---|
| `"AI"` | Bukan pertanyaan | Orkestrator meminta klarifikasi satu kalimat |
| `"Berapa suhu didih air di Bandung?"` | Pertanyaan faktual murni, tidak argumentatif | Orkestrator menyarankan perumusan argumentatif atau menjawab langsung |
| `"Apakah X baik?"` (X ambigu) | Ambigu | Tahap pemetaan merumuskan ulang secara presisi dan mencatat ambiguitas di `presuppositions` |

## Langsung lewat engine (tanpa Claude)

```bash
ABR="python3 .claude/skills/argument-battle-royale/scripts/abr.py"
$ABR init "Apakah AI benar-benar memahami bahasa?" mode=efficient population=64
$ABR next --run argument-battle-royale-runs/apakah-ai-benar-benar-memahami-bahasa-XXXXXX
```
