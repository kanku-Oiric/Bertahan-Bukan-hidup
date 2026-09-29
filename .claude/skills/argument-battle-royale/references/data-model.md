# Model Data

Semua file berada di direktori run (`output_dir`). JSON ditulis atomik; `fighters.jsonl` dan `ledger.jsonl` berformat satu objek per baris.

## Daftar isi

1. [Tata letak direktori run](#tata-letak-direktori-run)
2. [Petarung (fighter)](#petarung-fighter)
3. [Entri populasi](#entri-populasi)
4. [Ronde dan duel](#ronde-dan-duel)
5. [Penilaian juri (judgment)](#penilaian-juri-judgment)
6. [State dan registri paket](#state-dan-registri-paket)
7. [Ledger](#ledger)
8. [Format output paket](#format-output-paket)

## Tata letak direktori run

```
RUN_DIR/
├── state.json            checkpoint utama: fase, konfigurasi, registri paket, flags
├── ledger.jsonl          log peristiwa berantai-hash (append-only)
├── map.json              peta ruang argumen
├── plan.json             sel, kuota posisi, slot (termasuk gelombang refill)
├── fighters.jsonl        semua petarung (imutabel setelah seeding)
├── population.json       status, skor scouting, unggulan per petarung
├── dedup_<g>.json        pasangan kandidat, kluster, dan duplikat per gelombang
├── scouting.json         jangkar, median jangkar, offset kalibrasi per paket
├── seeding.json          urutan unggulan + hash petarung/populasi saat dikunci
├── rounds/R01.json ...   satu file per babak (hasil per duel, penilaian, debat)
├── dossiers.json         dosir Final 4
├── packets/<id>/
│   ├── packet.md         instruksi mandiri untuk worker
│   ├── meta.json         rekaman paket + payload (input yang di-hash)
│   ├── output.json       output worker (setelah diserap: tidak boleh berubah)
│   └── output.rejected.N.json   output yang gagal validasi (untuk audit)
├── report.md / report.json   laporan akhir
├── arena.html            halaman beranimasi (progres, bracket, hasil); ditulis ulang setiap `next`
└── integrity.json        hasil verifikasi integritas + digest
```

## Petarung (fighter)

Satu baris `fighters.jsonl`. Field konten ditulis generator; field metadata diisi engine.

| Field | Tipe | Keterangan |
|---|---|---|
| `id` | string | `F0001`, … (engine) |
| `slot_id`, `cell_id` | string | Slot/sel asal (engine) |
| `stance_id`, `framework_id`, `strategy_id`, `variant` | string/int | Spesifikasi slot (engine) |
| `generation_round`, `packet_id` | int/string | Gelombang & paket asal (engine) |
| `content_sha256` | string | Hash konten (engine) |
| `title` | string | Nama pendek argumen |
| `thesis` | string | Jawaban satu kalimat terhadap topik |
| `term_readings` | string[] | ID bacaan istilah dari peta |
| `definitions` | `{term, definition}[]` (1–8) | Definisi istilah kunci |
| `premises` | `{id, text, type, support}[]` (2–7) | `type` ∈ empirical, conceptual, normative, metaphysical, methodological |
| `inference_type` | enum | deductive, inductive, abductive, analogical, transcendental, pragmatic, probabilistic |
| `inference` | string | Bagaimana kesimpulan mengikuti |
| `conclusion` | string | Kesimpulan (harus sesuai posisi slot) |
| `empirical_commitments` | string[] | Klaim yang dapat diperiksa |
| `falsifiers` | string[] (1–6) | Apa yang akan menunjukkan argumen salah |
| `anticipated_objection`, `reply` | string | Keberatan terkuat + balasan |
| `scope` | string | Batas dan kualifikasi |

Batas panjang: maksimal 900 kata per petarung.

## Entri populasi

`population.json` = `{ fighter_id: entri }`.

```json
{
  "status": "valid",                      // generated | unique | duplicate | valid | dq | cut_capacity
  "generation_round": 0,
  "duplicate_of": null, "dedup_method": null,   // untuk status duplicate: auto | review | cluster
  "dq_codes": [],
  "scout": {
    "packets": ["P0012-scout"], "scores": [7, 6, 6, 5, 5, 6, 6, 7, 6, 6],
    "raw_total": 61.5, "offset": -1.25, "calibrated_total": 60.25,
    "fatal_flaws": [], "strongest_point": "...", "weakest_point": "...", "anchor": false
  },
  "seed": 17
}
```

## Ronde dan duel

`rounds/Rnn.json`:

```json
{
  "round": 3, "slots": 256, "stage": "elimination",     // elimination | deep_review | semifinal | final
  "label": "Babak 256 besar (Eliminasi)",
  "method": "llm_single",       // score | llm_single | llm_single_full | panel | panel_debate
  "panel_size": 1, "status": "done",   // pending | debate:<babak> | judging | done
  "matches": [ DUEL, ... ]
}
```

DUEL:

```json
{
  "match_id": "R03-M0007", "a": "F0412", "b": "F0088", "seed_a": 9, "seed_b": 120, "bye": false,
  "winner": "F0412", "loser": "F0088", "winner_side": "a",
  "basis": "majority",          // majority | score_sum_tiebreak | seeded_coin | fatal_flaw | scout_total | seed_order | bye
  "votes": {"a": 2, "b": 1},
  "method": "panel",            // metode aktual; score_fallback bila semua juri gagal
  "upset": false,
  "judgments": [ JUDGMENT, ... ],
  "debate": { "attack": {"a": DEBATE_TURN, "b": DEBATE_TURN}, "defense": {...}, "closing": {...} }   // semifinal/final
}
```

## Penilaian juri (judgment)

Disimpan dalam sisi `a`/`b` (sudah dipetakan balik dari X/Y).

```json
{
  "packet_id": "P0140-judge", "judge": "L2", "lens": "Filsuf sains",
  "presentation": {"X": "b", "Y": "a"},
  "scores": {"a": [..10..], "b": [..10..]},
  "totals": {"a": 71.5, "b": 64.0},
  "fatal": {"a": [], "b": ["FF_NON_SEQUITUR"]},
  "stated_winner": "a", "rule_winner": "a", "basis": "fatal_flaw", "consistent": true,
  "decisive_factor": "...", "rationale": "...",
  "objections": {"a_to_b": "...", "b_to_a": "..."},
  "steelman": {"a": "...", "b": "..."}, "reply_quality": {"a": "...", "b": "..."},   // protokol lengkap
  "confidence": 0.7, "dissent_risk": "...", "evidence": []
}
```

Penilaian berbasis skor (`judge: "SCOUT"`) hanya memuat `totals`, `fatal`, `rule_winner`, `basis`.

## State dan registri paket

`state.json` (ringkas):

```json
{
  "schema_version": 1, "engine_version": "1.0.0",
  "config": { "...parameter terselesaikan + profil mode..." },
  "phase": "round", "phase_history": [...],
  "packet_seq": 142, "packets": { "P0001-map": PACKET_RECORD, ... },
  "generation_round": 0, "generation_ingested": 0, "dedup_round_done": 0,
  "scout_created": 0, "validated_round": 0, "anchors": ["F0107", "F0533", "F0871"],
  "current_round": 4, "champion": null, "runner_up": null,
  "falsification": {"queue": [...], "index": 0, "results": {...}},
  "winner": null, "winner_falsification": null,
  "blocked": null, "flags": [{"code": "panel_reduced", "detail": "...", "at": "..."}]
}
```

PACKET_RECORD:

```json
{
  "id": "P0042-duel", "type": "duel", "stage": "round:2:judge",
  "status": "pending",            // pending | done | abandoned
  "attempts": 0, "input_hash": "sha256 payload", "created_at": "...",
  "errors": [], "output_sha256": "... (setelah diserap)"
}
```

## Ledger

Setiap baris: `{seq, ts, event, data, prev, hash}` dengan `hash = sha256(prev + canonical_json({seq, ts, event, data, prev}))`. Peristiwa utama: `run_initialized`, `packet_created`, `packet_ingested` (hash output), `packet_rejected`, `packet_abandoned`, `phase_changed`, `plan_created`, `fighters_ingested`, `dedup_done`, `validation_applied`, `refill_planned`, `seeding_locked` (hash petarung, populasi, seeding), `round_created`, `round_completed` (hash file ronde), `final4_dossiers`, `champion_decided`, `falsification_result`, `winner_declared`, `report_generated`, `flag`, `blocked`.

## Objek `anim` pada output `next`

```json
{
  "scene": "battle",            // wizard | battle | rocket | trophy | idle | blocked | nowinner
  "stage": "ELIMINASI", "stage_index": 7, "stage_count": 15,
  "percent": 52, "caption": "Babak 256 besar (Eliminasi): duel berlangsung",
  "round": 3, "done": false,
  "show": true,                 // true sekali per tahap/babak baru
  "frame": "…teks flipbook…",   // hanya ada bila show = true
  "arena": "/…/RUN_DIR/arena.html"
}
```

State menyimpan `anim_key` dan `anim_n` agar flipbook hanya muncul saat tahap atau babak berganti. Keduanya tidak memengaruhi hasil turnamen dan tidak termasuk digest integritas.

## Format output paket

Setiap `packet.md` memuat contoh output yang persis. Semua output wajib memuat `packet_id` dan `input_hash`.

| Tipe | Field utama | Validator |
|---|---|---|
| `map` | `topic_restated`, `question_type`, `presuppositions`, `key_terms[{term, readings[{id,label,definition}]}]`, `stances[3–6]`, `frameworks[3–12]` (+`compatible_stances`), `strategies[3–8]`, `cruxes[2–12]`, `evidence_domains` | `v_map` |
| `generate` | `fighters[]` — satu per `slot_id`, field konten petarung | `v_generate` |
| `dedup_review` | `decisions[{pair_id, same_argument, reason}]` | `v_dedup_review` |
| `scout` | `evaluations[{fighter_id, valid, dq_codes, scores[10], fatal_flaws, strongest_point, weakest_point}]` | `v_scout` |
| `duel` | `verdicts[{duel_id, scores_x, scores_y, fatal_x, fatal_y, winner: X\|Y, decisive_factor, rationale, objection_x_to_y, objection_y_to_x}]` | `v_duel` |
| `judge` | `judge_lens`, `verdicts[...]` seperti `duel` + `steelman_x/y`, `reply_quality_x/y`, `confidence`, `dissent_risk`, `evidence` | `v_judge` |
| `dossier` | `fighter_id`, `standard_form`, `formal_skeleton`, `hard_core`, `protective_belt`, `empirical_commitments`, `falsifiers`, `strongest_objections[{objection, severity, status}]`, `vulnerabilities`, `strengths`, `assessment` | `v_dossier` |
| `debate` | `match_id`, `exchange`, `statement`, `points[{claim, target}]`, `concessions`, `clarifications` | `v_debate` |
| `falsification` | `fighter_id`, `commitments[{id, claim, type, core}]`, `tests[{id, kind, target_commitment, description, result, reasoning}]`, `immunization_detected`, `verdict`, `required_qualifications`, `residual_confidence`, `summary`, `evidence` | `v_falsification` |

Validator ada di `scripts/engine/validate.py`; pesan galatnya menunjuk path JSON yang salah (mis. `$.verdicts[3].scores_y[7]: skor harus angka 0-10`).
