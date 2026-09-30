"""State machine turnamen.

`Engine.next()` bersifat idempoten dan dapat dilanjutkan (resume) kapan pun:
  1. menyerap output paket yang sudah ditulis worker (validasi -> done/rejected),
  2. menjalankan semua langkah deterministik yang bisa dijalankan,
  3. berhenti ketika dibutuhkan kerja LLM, lalu mengembalikan daftar paket pending.

Fase: init -> map -> generate -> dedup -> validate -> (refill: generate ...) ->
seed -> round (eliminasi / deep review) -> final4 -> round (semifinal) ->
round (final) -> falsification -> report -> done
"""

import json
import os

from . import bracket as B
from . import config as C
from . import dedup as D
from . import judging as J
from . import packets as P
from . import planner
from .util import hash_obj, now_iso, rng_for, sha256_file
from .validate import validate_output

PHASE_LABEL = {
    "init": "Inisialisasi",
    "map": "Pemetaan ruang argumen",
    "generate": "Generasi petarung",
    "dedup": "Deduplikasi",
    "validate": "Validasi & scouting",
    "seed": "Seeding",
    "round": "Bracket",
    "final4": "Final 4 (dosir)",
    "falsification": "Uji falsifikasi",
    "report": "Laporan akhir",
    "done": "Selesai",
    "blocked": "Terhenti",
}
STAGE_NAME = {
    "elimination": "Eliminasi",
    "deep_review": "Deep review",
    "semifinal": "Semifinal",
    "final": "Final",
}


def round_label(slots, stage):
    if stage == "final":
        return "Final"
    if stage == "semifinal":
        return "Semifinal"
    return "Babak %d besar (%s)" % (slots, STAGE_NAME[stage])


class Engine:
    def __init__(self, run):
        self.run = run

    @property
    def st(self):
        return self.run.state

    @property
    def cfg(self):
        return self.run.cfg

    # ================================================================ public
    def next(self):
        with self.run.lock():
            for _ in range(1000):
                self._ingest()
                if self.st.get("blocked"):
                    break
                handler = getattr(self, "_phase_" + self.st["phase"])
                progressed = handler()
                self.run.save_state()
                if not progressed:
                    break
            self._anim = self._anim_update()
            self.run.save_state()
            summary = self._write_arena()
            if summary is not None:
                self._anim["live"] = self._live_update(summary)
            return self.summary()

    def _anim_update(self):
        """Frame flipbook untuk chat: tampil sekali per tahap/babak baru."""
        from . import anim

        try:
            info = anim.status_info(self.run)
        except Exception as exc:  # animasi tidak boleh menghentikan turnamen
            return {"show": False, "error": str(exc)}
        show = info["key"] != self.st.get("anim_key")
        if show:
            self.st["anim_key"] = info["key"]
            self.st["anim_n"] = self.st.get("anim_n", 0) + 1
        out = {k: v for k, v in info.items() if k != "key"}
        out["show"] = show
        out["arena"] = self.run.path("arena.html")
        if show:
            out["frame"] = anim.mini(info, self.st["anim_n"])
        return out

    def _write_arena(self):
        from . import arena

        try:
            return arena.write(self.run)
        except Exception as exc:
            import sys

            sys.stderr.write("peringatan: arena.html tidak diperbarui: %s\n" % exc)
            return None

    def _live_update(self, summary):
        """Untuk arena di Artifact: `push` bernilai true bila ada acara baru sejak
        laporan terakhir, artinya arena-live.json perlu ditulis ke database artifact."""
        from . import arena

        key = arena.live_key(summary)
        push = key != self.st.get("live_key")
        if push:
            self.st["live_key"] = key
            self.run.save_state()
        return {"push": push, "url": self.st.get("live_url"), "file": self.run.path(arena.LIVE_FILE),
                "collection": arena.LIVE_COLLECTION, "doc_id": arena.LIVE_DOC_ID}

    def summary(self):
        st = self.st
        pending = [p for p in st["packets"].values() if p["status"] == "pending"]
        pending.sort(key=lambda p: p["id"])
        out = {
            "run_dir": self.run.dir,
            "phase": st["phase"],
            "phase_label": PHASE_LABEL.get(st["phase"], st["phase"]),
            "progress": self.progress_line(),
            "max_parallel": self.cfg["max_parallel"],
        }
        if st.get("blocked"):
            out["action"] = "blocked"
            out["blocked"] = st["blocked"]
        elif st["phase"] == "done":
            out["action"] = "done"
            out["report_md"] = self.run.path("report.md")
            out["report_json"] = self.run.path("report.json")
            out["integrity"] = self.run.path("integrity.json")
        else:
            out["action"] = "execute_packets"
        if getattr(self, "_anim", None):
            out["anim"] = self._anim
        out["pending_count"] = len(pending)
        out["packets"] = [
            {
                "packet_id": p["id"],
                "type": p["type"],
                "packet_path": self.run.packet_prompt_path(p["id"]),
                "output_path": self.run.packet_output_path(p["id"]),
                "attempt": p["attempts"] + 1,
                "last_errors": p["errors"][:10],
            }
            for p in pending
        ]
        return out

    def progress_line(self):
        st = self.st
        ph = st["phase"]
        pk = st["packets"].values()
        done = sum(1 for p in pk if p["status"] in ("done", "abandoned"))
        base = "%s · paket selesai %d/%d" % (PHASE_LABEL.get(ph, ph), done, len(st["packets"]))
        if ph == "round" and st["current_round"]:
            rd = self.run.load_round(st["current_round"])
            if rd:
                base += " · %s (%s)" % (round_label(rd["slots"], rd["stage"]), rd["status"])
        return base

    # ================================================================ ingest
    def _ingest(self):
        changed = False
        for rec in list(self.st["packets"].values()):
            if rec["status"] != "pending":
                continue
            out_path = self.run.packet_output_path(rec["id"])
            if not os.path.exists(out_path):
                continue
            errors = check_packet(self.run, rec["id"])
            if errors:
                self.run.reject_packet_output(rec["id"], errors)
            else:
                self.run.mark_packet_done(rec["id"])
                rec["errors"] = []
            changed = True
        if changed:
            self.run.save_state()

    def _stage_state(self, stage_key):
        pk = self.run.packets_for(stage_key)
        pending = [p for p in pk if p["status"] == "pending"]
        done = [p for p in pk if p["status"] == "done"]
        abandoned = [p for p in pk if p["status"] == "abandoned"]
        return pk, pending, done, abandoned

    def _block(self, reason, hint):
        self.st["blocked"] = {"reason": reason, "hint": hint, "at": now_iso()}
        self.run.log("blocked", self.st["blocked"])

    # ================================================================ phases
    def _phase_init(self):
        example = {
            "topic_restated": "<rumusan presisi topik>",
            "question_type": "conceptual",
            "presuppositions": ["<presuposisi>"],
            "key_terms": [
                {"term": "<istilah>", "readings": [{"id": "T1a", "label": "<nama bacaan>", "definition": "<definisi>"}]}
            ],
            "stances": [{"id": "S1", "label": "<posisi>", "description": "<versi terkuat posisi>"}],
            "frameworks": [
                {"id": "K1", "label": "<kerangka>", "description": "<deskripsi>", "compatible_stances": ["S1", "S2"]}
            ],
            "strategies": [{"id": "M1", "label": "<strategi>", "description": "<deskripsi>"}],
            "cruxes": ["<titik krusial>"],
            "evidence_domains": ["<bidang>"],
            "notes": "<catatan opsional>",
        }
        payload = {"topic": self.cfg["topic"], "population": self.cfg["population"], "language": self.cfg["language"]}
        P.register(
            self.run, "map", "map", payload, "Peta ruang argumen", "map.md",
            {"POPULATION": self.cfg["population"]}, example,
        )
        self.run.set_phase("map")
        return True

    def _phase_map(self):
        pk, pending, done, abandoned = self._stage_state("map")
        if pending:
            return False
        if not done:
            self._block(
                "Paket peta ruang argumen gagal %d kali." % C.MAX_ATTEMPTS,
                "Periksa galat di packets/<id>/meta.json, lalu jalankan: abr.py retry --run <dir> --packet <id>",
            )
            return False
        out = self.run.packet_output(done[0]["id"])
        map_obj = {k: v for k, v in out.items() if k not in ("packet_id", "input_hash")}
        self.run.save("map.json", map_obj)
        plan = planner.initial_plan(map_obj, self.cfg["population"], self.cfg["random_seed"])
        self.run.save("plan.json", plan)
        self.run.log("plan_created", {"cells": len(plan["cells"]), "slots": len(plan["slots"]), "stance_quota": plan["stance_quota"]})
        self._make_generate_packets(plan["slots"], 0)
        self.run.set_phase("generate")
        return True

    def _make_generate_packets(self, slots, gen_round):
        map_obj = self.run.load("map.json")
        reading_ids = [r["id"] for t in map_obj["key_terms"] for r in t["readings"]]
        labels = {x["id"]: x["label"] for key in ("stances", "frameworks", "strategies") for x in map_obj[key]}
        batch = self.cfg["gen_batch"]
        for i in range(0, len(slots), batch):
            chunk = slots[i : i + batch]
            table = ["| slot_id | posisi | kerangka | strategi | varian |", "|---|---|---|---|---|"]
            for s in chunk:
                table.append(
                    "| `%s` | `%s` %s | `%s` %s | `%s` %s | %d |"
                    % (
                        s["slot_id"], s["stance_id"], labels[s["stance_id"]], s["framework_id"],
                        labels[s["framework_id"]], s["strategy_id"], labels[s["strategy_id"]], s["variant"],
                    )
                )
            payload = {"slots": chunk, "reading_ids": reading_ids, "generation_round": gen_round}
            example = {"fighters": [P.example_fighter(chunk[0]["slot_id"])]}
            P.register(
                self.run, "generate", "gen:%d" % gen_round, payload,
                "Generasi petarung (%d slot, gelombang %d)" % (len(chunk), gen_round), "generate.md",
                {
                    "MAP_SUMMARY": P.map_summary(map_obj),
                    "SLOT_COUNT": len(chunk),
                    "SLOT_TABLE": "\n".join(table),
                    "MAX_WORDS": C.MAX_FIGHTER_WORDS,
                },
                example,
            )

    def _phase_generate(self):
        gr = self.st["generation_round"]
        pk, pending, done, abandoned = self._stage_state("gen:%d" % gr)
        if pending:
            return False
        if self.st.get("generation_ingested", -1) >= gr:
            self.run.set_phase("dedup")
            return True
        existing = self.run.load_fighters()
        next_no = len(existing) + 1
        new = []
        for rec in sorted(done, key=lambda p: p["id"]):
            payload = self.run.packet_payload(rec["id"])
            slots = {s["slot_id"]: s for s in payload["slots"]}
            out = self.run.packet_output(rec["id"])
            for body in sorted(out["fighters"], key=lambda f: f["slot_id"]):
                slot = slots[body["slot_id"]]
                f = dict(body)
                f.update(
                    {
                        "id": "F%04d" % next_no,
                        "cell_id": slot["cell_id"],
                        "stance_id": slot["stance_id"],
                        "framework_id": slot["framework_id"],
                        "strategy_id": slot["strategy_id"],
                        "variant": slot["variant"],
                        "generation_round": gr,
                        "packet_id": rec["id"],
                    }
                )
                f.setdefault("term_readings", [])
                f.setdefault("empirical_commitments", [])
                f["content_sha256"] = hash_obj({k: v for k, v in body.items() if k != "slot_id"})
                new.append(f)
                next_no += 1
        lost = sum(len(self.run.packet_payload(p["id"])["slots"]) for p in abandoned)
        if lost:
            self.run.flag("generation_slots_lost", "%d slot hilang karena paket generasi gagal (gelombang %d)" % (lost, gr))
        self.run.append_fighters(new)
        pop = self.run.load_population()
        for f in new:
            pop[f["id"]] = {"status": "generated", "generation_round": gr}
        self.run.save_population(pop)
        self.st["generation_ingested"] = gr
        self.run.log("fighters_ingested", {"generation_round": gr, "count": len(new), "lost_slots": lost})
        self.run.set_phase("dedup")
        return True

    # ------------------------------------------------------------- dedup
    def _phase_dedup(self):
        gr = self.st["generation_round"]
        stage = "dedup:%d" % gr
        fighters = self.run.load_fighters()
        pop = self.run.load_population()
        if self.st["dedup_round_done"] < gr and not self.st.get("dedup_started") == gr:
            new_ids = [i for i, p in pop.items() if p["generation_round"] == gr and p["status"] == "generated"]
            pool_ids = [i for i, p in pop.items() if p["generation_round"] < gr and p["status"] != "duplicate"]
            auto, review, overflow = D.candidate_pairs(new_ids, pool_ids, fighters)
            use_review = self.cfg["dedup_review"]
            record = {
                "generation_round": gr,
                "auto_pairs": auto,
                "review_pairs": review if use_review else [],
                "unreviewed_borderline": (overflow + ([] if use_review else review)),
            }
            self.run.save("dedup_%d.json" % gr, record)
            if use_review and review:
                self._make_dedup_packets(review, fighters, gr)
            self.st["dedup_started"] = gr
            self.run.log("dedup_candidates", {"generation_round": gr, "auto": len(auto), "review": len(record["review_pairs"]), "unreviewed": len(record["unreviewed_borderline"])})
            return True
        if self.st["dedup_round_done"] >= gr:
            self.run.set_phase("validate")
            return True
        pk, pending, done, abandoned = self._stage_state(stage)
        if pending:
            return False
        record = self.run.load("dedup_%d.json" % gr)
        confirmed = [(a, b) for a, b, _ in record["auto_pairs"]]
        methods = {}
        for a, b, _ in record["auto_pairs"]:
            methods[(a, b)] = "auto"
        decisions = {}
        for rec in done:
            for d in self.run.packet_output(rec["id"])["decisions"]:
                decisions[d["pair_id"]] = d
        pair_index = {}
        for rec in pk:
            for p in self.run.packet_payload(rec["id"])["pairs"]:
                pair_index[p["pair_id"]] = (p["a"], p["b"], rec["status"])
        for pid, (a, b, status) in sorted(pair_index.items()):
            if status == "done" and decisions.get(pid, {}).get("same_argument"):
                confirmed.append((a, b))
                methods[(a, b)] = "review"
        if abandoned:
            self.run.flag("dedup_review_abandoned", "%d paket review duplikasi gagal; pasangan terkait dianggap berbeda." % len(abandoned))
        protected = {i for i, p in pop.items() if p["generation_round"] < gr and p["status"] != "duplicate"}
        mapping, clusters = D.resolve_clusters(confirmed, fighters, protected)
        for fid, p in pop.items():
            if p["generation_round"] != gr or p["status"] != "generated":
                continue
            if fid in mapping:
                p["status"] = "duplicate"
                p["duplicate_of"] = mapping[fid]
                rep = mapping[fid]
                p["dedup_method"] = methods.get((fid, rep)) or methods.get((rep, fid)) or "cluster"
            else:
                p["status"] = "unique"
        self.run.save_population(pop)
        record["clusters"] = clusters
        record["duplicates"] = mapping
        self.run.save("dedup_%d.json" % gr, record)
        self.st["dedup_round_done"] = gr
        self.run.log("dedup_done", {"generation_round": gr, "duplicates": len(mapping), "clusters": len(clusters)})
        self.run.set_phase("validate")
        return True

    def _make_dedup_packets(self, pairs, fighters, gr):
        batch = C.DEDUP_REVIEW_BATCH
        for i in range(0, len(pairs), batch):
            chunk = pairs[i : i + batch]
            items, blocks = [], []
            for j, (a, b, s) in enumerate(chunk):
                pid = "D%d-%04d" % (gr, i + j + 1)
                items.append({"pair_id": pid, "a": a, "b": b, "similarity": s})
                blocks.append(
                    "### Pasangan `%s` (kemiripan leksikal %.2f)\n\n%s\n\n%s\n"
                    % (pid, s, P.fighter_md(fighters[a], "Argumen 1"), P.fighter_md(fighters[b], "Argumen 2"))
                )
            example = {"decisions": [{"pair_id": items[0]["pair_id"], "same_argument": False, "reason": "<alasan singkat>"}]}
            P.register(
                self.run, "dedup_review", "dedup:%d" % gr, {"pairs": items},
                "Review duplikasi (%d pasangan)" % len(items), "dedup_review.md",
                {"PAIRS": "\n".join(blocks)}, example,
            )

    # ---------------------------------------------------------- validate
    def _phase_validate(self):
        gr = self.st["generation_round"]
        stage = "scout:%d" % gr
        fighters = self.run.load_fighters()
        pop = self.run.load_population()
        if self.st.get("scout_created", -1) < gr:
            ids = sorted(i for i, p in pop.items() if p["generation_round"] == gr and p["status"] == "unique")
            batch = self.cfg["scout_batch"]
            n_packets = (len(ids) + batch - 1) // batch
            if gr == 0 and n_packets >= 2 and not self.st["anchors"]:
                r = rng_for(self.cfg["random_seed"], "anchors")
                self.st["anchors"] = sorted(r.sample(ids, min(C.ANCHOR_COUNT, len(ids))))
                self.run.log("anchors_selected", {"anchors": self.st["anchors"]})
            anchors = self.st["anchors"] if (n_packets >= 2 or gr > 0) else []
            map_obj = self.run.load("map.json")
            stance_label = {s["id"]: s["label"] for s in map_obj["stances"]}
            for i in range(0, len(ids), batch):
                chunk = ids[i : i + batch]
                members = chunk + [a for a in anchors if a not in chunk]
                rr = rng_for(self.cfg["random_seed"], "scout-order", gr, i)
                rr.shuffle(members)
                blocks = [
                    "%s\n- *Posisi yang ditugaskan:* `%s` %s\n"
                    % (P.fighter_md(fighters[fid], "Petarung `%s`" % fid), fighters[fid]["stance_id"], stance_label.get(fighters[fid]["stance_id"], ""))
                    for fid in members
                ]
                example = {
                    "evaluations": [
                        {
                            "fighter_id": members[0],
                            "valid": True,
                            "dq_codes": [],
                            "scores": P._scores_example(),
                            "fatal_flaws": [],
                            "strongest_point": "<titik terkuat>",
                            "weakest_point": "<titik terlemah, spesifik>",
                            "notes": "<opsional>",
                        }
                    ]
                }
                P.register(
                    self.run, "scout", stage, {"fighter_ids": members, "anchors": [a for a in anchors if a in members]},
                    "Validasi & scouting (%d petarung)" % len(members), "scout.md",
                    {
                        "TOPIC_CONTEXT": P.topic_context(map_obj),
                        "DQ_CODES": "\n".join("   - `%s` — %s" % (k, v) for k, v in C.DQ_CODES.items()),
                        "FIGHTER_COUNT": len(members),
                        "FIGHTERS": "\n\n".join(blocks),
                    },
                    example,
                )
            self.st["scout_created"] = gr
            return True
        if self.st.get("validated_round", -1) >= gr:
            return self._after_validation()
        pk, pending, done, abandoned = self._stage_state(stage)
        if pending:
            return False
        self._apply_scouting(pop, fighters)
        self.st["validated_round"] = gr
        return self._after_validation()

    def _apply_scouting(self, pop, fighters):
        """Hitung ulang skor scouting semua gelombang (kalibrasi global via jangkar)."""
        anchors = self.st["anchors"]
        per_packet_totals = {}
        evals = {}  # fighter -> list of (packet_id, eval)
        scout_packets = [p for p in self.st["packets"].values() if p["type"] == "scout"]
        for rec in sorted(scout_packets, key=lambda p: p["id"]):
            if rec["status"] == "done":
                out = self.run.packet_output(rec["id"])
                per_packet_totals[rec["id"]] = {}
                for e in out["evaluations"]:
                    per_packet_totals[rec["id"]][e["fighter_id"]] = J.weighted_total(e["scores"])
                    evals.setdefault(e["fighter_id"], []).append((rec["id"], e))
        offsets, medians = J.calibrate(per_packet_totals, anchors)
        scouted = set(evals)
        for fid, p in pop.items():
            if p["status"] not in ("unique", "valid", "dq"):
                continue
            if fid not in scouted:
                if p["status"] == "unique":
                    in_abandoned = any(
                        fid in self.run.packet_payload(r["id"])["fighter_ids"]
                        for r in scout_packets if r["status"] == "abandoned"
                    )
                    if in_abandoned:
                        p["status"] = "dq"
                        p["dq_codes"] = ["DQ_UNSCORED"]
                continue
            items = evals[fid]
            if len(items) == 1:
                pid, e = items[0]
                raw = J.weighted_total(e["scores"])
                offset = offsets.get(pid, 0.0) if fid not in anchors else 0.0
                scores = e["scores"]
                fatal = e["fatal_flaws"]
                valid = e["valid"]
                dq = e["dq_codes"]
                strongest, weakest = e["strongest_point"], e["weakest_point"]
            else:  # jangkar: median per kriteria, mayoritas untuk validitas/cacat
                n = len(items)
                scores = []
                for k in range(len(C.RUBRIC_KEYS)):
                    vals = sorted(e["scores"][k] for _, e in items)
                    scores.append(vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2.0)
                raw = J.weighted_total(scores)
                offset = 0.0
                valid = sum(1 for _, e in items if e["valid"]) * 2 > n
                flaw_counts = {}
                for _, e in items:
                    for fl in set(e["fatal_flaws"]):
                        flaw_counts[fl] = flaw_counts.get(fl, 0) + 1
                fatal = sorted(fl for fl, c in flaw_counts.items() if c * 2 > n)
                dq_counts = {}
                for _, e in items:
                    for c in e["dq_codes"]:
                        dq_counts[c] = dq_counts.get(c, 0) + 1
                dq = sorted(dq_counts, key=lambda c: -dq_counts[c])[:3] if not valid else []
                if not valid and not dq:
                    dq = ["DQ_NOT_ARGUMENT"]
                strongest, weakest = items[0][1]["strongest_point"], items[0][1]["weakest_point"]
            p["scout"] = {
                "packets": [pid for pid, _ in items],
                "scores": scores,
                "raw_total": raw,
                "offset": offset,
                "calibrated_total": round(max(0.0, min(100.0, raw + offset)), 3),
                "fatal_flaws": fatal,
                "strongest_point": strongest,
                "weakest_point": weakest,
                "anchor": fid in anchors,
            }
            p["status"] = "valid" if valid else "dq"
            p["dq_codes"] = [] if valid else dq
        self.run.save_population(pop)
        self.run.save("scouting.json", {"anchors": anchors, "anchor_medians": medians, "packet_offsets": offsets})
        counts = {}
        for p in pop.values():
            counts[p["status"]] = counts.get(p["status"], 0) + 1
        self.run.log("validation_applied", {"counts": counts, "offsets": offsets})

    def _after_validation(self):
        pop = self.run.load_population()
        fighters = self.run.load_fighters()
        valid = [i for i, p in pop.items() if p["status"] == "valid"]
        target = self.cfg["population"]
        gr = self.st["generation_round"]
        if len(valid) < target * C.MIN_FILL_RATIO and gr < self.cfg["max_refill_rounds"]:
            plan = self.run.load("plan.json")
            by_stance, by_cell = {}, {}
            for i in valid:
                f = fighters[i]
                by_stance[f["stance_id"]] = by_stance.get(f["stance_id"], 0) + 1
                by_cell[f["cell_id"]] = by_cell.get(f["cell_id"], 0) + 1
            slots = planner.refill_plan(plan, by_stance, by_cell, target, C.REFILL_MARGIN, self.cfg["random_seed"], gr + 1)
            if slots:
                self.st["generation_round"] = gr + 1
                plan.setdefault("refills", []).append({"generation_round": gr + 1, "slots": slots})
                self.run.save("plan.json", plan)
                self.run.log("refill_planned", {"generation_round": gr + 1, "slots": len(slots), "valid": len(valid)})
                self._make_generate_packets(slots, gr + 1)
                self.run.set_phase("generate", "refill gelombang %d" % (gr + 1))
                return True
        self.run.set_phase("seed")
        return True

    # -------------------------------------------------------------- seed
    def _phase_seed(self):
        pop = self.run.load_population()
        valid = [i for i, p in pop.items() if p["status"] == "valid"]
        if len(valid) < C.MIN_VALID_FOR_BRACKET:
            self._block(
                "Hanya %d petarung valid (minimum %d)." % (len(valid), C.MIN_VALID_FOR_BRACKET),
                "Naikkan population atau mulai run baru; periksa alasan DQ di population.json.",
            )
            return False
        order = seeding_order(pop, self.cfg["random_seed"])
        cap = self.cfg["population"]
        for fid in order[cap:]:
            pop[fid]["status"] = "cut_capacity"
        order = order[:cap]
        seeds = {fid: i + 1 for i, fid in enumerate(order)}
        for fid, s in seeds.items():
            pop[fid]["seed"] = s
        self.run.save_population(pop)
        seeding = {
            "order": order,
            "seeds": seeds,
            "fighters_sha256": sha256_file(self.run.fighters_path),
            "population_sha256": sha256_file(self.run.path("population.json")),
            "locked_at": now_iso(),
        }
        self.run.save("seeding.json", seeding)
        self.run.log(
            "seeding_locked",
            {
                "entrants": len(order),
                "fighters_sha256": seeding["fighters_sha256"],
                "population_sha256": seeding["population_sha256"],
                "seeding_sha256": self.run.file_hash("seeding.json"),
            },
        )
        size, matches = B.first_round(order, 1)
        self._create_round(1, size, matches)
        return True

    def _create_round(self, rnd, slots, matches):
        stage = B.stage_for(slots, self.cfg["deep_round_threshold"])
        if stage == "elimination":
            method = self.cfg["early_method"]
            panel = 1
        elif stage == "deep_review":
            method, panel = "panel", self.cfg["deep_panel"]
        elif stage == "semifinal":
            method, panel = "panel_debate", self.cfg["semifinal_panel"]
        else:
            method, panel = "panel_debate", self.cfg["final_panel"]
        rd = {
            "round": rnd,
            "slots": slots,
            "stage": stage,
            "label": round_label(slots, stage),
            "method": method,
            "panel_size": panel,
            "status": "pending",
            "created_at": now_iso(),
            "matches": matches,
        }
        self.run.save_round(rnd, rd)
        self.st["current_round"] = rnd
        self.run.log("round_created", {"round": rnd, "slots": slots, "stage": stage, "method": method, "panel": panel})
        if stage == "semifinal":
            self.run.set_phase("final4")
        else:
            self.run.set_phase("round")

    # ------------------------------------------------------------- round
    def _phase_round(self):
        r = self.st["current_round"]
        rd = self.run.load_round(r)
        fighters = self.run.load_fighters()
        if rd["status"] == "pending":
            for m in rd["matches"]:
                if m["bye"]:
                    m.update({"winner": m["a"], "loser": None, "method": "bye", "judgments": [], "votes": None, "basis": "bye", "upset": False})
            if rd["method"] == "score":
                pop = self.run.load_population()
                for m in rd["matches"]:
                    if not m["bye"]:
                        self._resolve_by_score(m, pop, fallback=False)
                return self._finish_round(rd)
            if rd["method"] == "panel_debate":
                self._make_debate_packets(rd, "attack", fighters)
                rd["status"] = "debate:attack"
            else:
                self._make_judge_packets(rd, fighters)
                rd["status"] = "judging"
            self.run.save_round(r, rd)
            return True
        if rd["status"].startswith("debate:"):
            exchange = rd["status"].split(":", 1)[1]
            stage_key = "round:%d:debate:%s" % (r, exchange)
            pk, pending, done, abandoned = self._stage_state(stage_key)
            if pending:
                return False
            for rec in pk:
                payload = self.run.packet_payload(rec["id"])
                m = next(x for x in rd["matches"] if x["match_id"] == payload["match_id"])
                deb = m.setdefault("debate", {}).setdefault(exchange, {})
                if rec["status"] == "done":
                    out = self.run.packet_output(rec["id"])
                    deb[payload["side"]] = {k: out.get(k) for k in ("statement", "points", "concessions", "clarifications")}
                    deb[payload["side"]]["packet_id"] = rec["id"]
                else:
                    deb[payload["side"]] = None
                    self.run.flag("debate_turn_missing", "%s %s sisi %s" % (payload["match_id"], exchange, payload["side"]))
            seq = C.DEBATE_EXCHANGES[rd["stage"]]
            idx = seq.index(exchange)
            if idx + 1 < len(seq):
                self._make_debate_packets(rd, seq[idx + 1], fighters)
                rd["status"] = "debate:" + seq[idx + 1]
            else:
                self._make_judge_packets(rd, fighters)
                rd["status"] = "judging"
            self.run.save_round(r, rd)
            return True
        if rd["status"] == "judging":
            stage_key = "round:%d:judge" % r
            pk, pending, done, abandoned = self._stage_state(stage_key)
            if pending:
                return False
            by_match = {}
            for rec in sorted(done, key=lambda p: p["id"]):
                payload = self.run.packet_payload(rec["id"])
                out = self.run.packet_output(rec["id"])
                pres = {d["duel_id"]: d["presentation"] for d in payload["duels"]}
                for v in out["verdicts"]:
                    j = J.build_judgment(v, pres[v["duel_id"]], rec["id"], payload["lens"]["id"], payload["lens"]["label"])
                    by_match.setdefault(v["duel_id"], []).append(j)
            pop = None
            for m in rd["matches"]:
                if m["bye"]:
                    continue
                js = by_match.get(m["match_id"], [])
                if not js:
                    pop = pop or self.run.load_population()
                    self._resolve_by_score(m, pop, fallback=True)
                    continue
                if len(js) < rd["panel_size"]:
                    self.run.flag("panel_reduced", "%s: %d dari %d juri" % (m["match_id"], len(js), rd["panel_size"]))
                side, basis, votes = J.aggregate_panel(js, self.cfg["random_seed"], m["match_id"])
                self._set_result(m, side, basis, votes, js, method=rd["method"])
                for j in js:
                    if not j["consistent"]:
                        self.run.flag("judge_inconsistency", "%s juri %s memilih %s tetapi skor menunjuk %s" % (m["match_id"], j["judge"], j["stated_winner"], j["rule_winner"]))
            return self._finish_round(rd)
        return False

    def _set_result(self, m, side, basis, votes, judgments, method):
        other = "b" if side == "a" else "a"
        m["winner"] = m[side]
        m["loser"] = m[other]
        m["winner_side"] = side
        m["basis"] = basis
        m["votes"] = votes
        m["judgments"] = judgments
        m["method"] = method
        seed_w = m["seed_a"] if side == "a" else m["seed_b"]
        seed_l = m["seed_b"] if side == "a" else m["seed_a"]
        m["upset"] = bool(seed_w and seed_l and seed_w > seed_l)

    def _resolve_by_score(self, m, pop, fallback):
        j = J.score_judgment(pop[m["a"]]["scout"], pop[m["b"]]["scout"])
        side = j["rule_winner"]
        self._set_result(m, side, j["basis"], {"a": int(side == "a"), "b": int(side == "b")}, [j], method="score_fallback" if fallback else "score")
        if fallback:
            self.run.flag("score_fallback", "%s diputus dengan skor scouting karena semua paket juri gagal" % m["match_id"])

    def _finish_round(self, rd):
        rd["status"] = "done"
        rd["completed_at"] = now_iso()
        self.run.save_round(rd["round"], rd)
        self.run.log(
            "round_completed",
            {
                "round": rd["round"],
                "stage": rd["stage"],
                "round_sha256": sha256_file(self.run.round_path(rd["round"])),
                "winners": [m["winner"] for m in rd["matches"]],
            },
        )
        if rd["stage"] == "final":
            m = rd["matches"][0]
            self.st["champion"] = m["winner"]
            self.st["runner_up"] = m["loser"]
            self.run.log("champion_decided", {"champion": m["winner"], "runner_up": m["loser"]})
            self.run.set_phase("falsification")
            return True
        seeds = self.run.load("seeding.json")["seeds"]
        matches = B.next_round(rd["matches"], seeds, rd["round"] + 1)
        self._create_round(rd["round"] + 1, rd["slots"] // 2, matches)
        return True

    # ------------------------------------------------- judge/duel packets
    def _make_judge_packets(self, rd, fighters):
        r = rd["round"]
        stage_key = "round:%d:judge" % r
        map_obj = self.run.load("map.json")
        matches = [m for m in rd["matches"] if not m["bye"]]
        seed = self.cfg["random_seed"]
        if rd["method"] == "llm_single":
            lenses = [C.LENS_BY_ID[C.SINGLE_JUDGE_LENS]]
            batch, ptype, template, full = self.cfg["duel_batch"], "duel", "duel.md", False
        elif rd["method"] == "llm_single_full":
            lenses = [C.LENS_BY_ID[C.SINGLE_JUDGE_LENS]]
            batch, ptype, template, full = self.cfg["duel_batch"], "judge", "judge.md", True
        else:
            lenses = C.LENSES[: rd["panel_size"]]
            batch = self.cfg["deep_batch"] if rd["stage"] == "deep_review" else len(matches)
            ptype, template, full = "judge", "judge.md", True
        dossiers = self.run.load("dossiers.json", {}) if rd["stage"] in ("semifinal", "final") else {}
        for lens in lenses:
            for i in range(0, len(matches), batch):
                chunk = matches[i : i + batch]
                duel_entries, blocks = [], []
                for m in chunk:
                    pres = P.presentation_for(seed, m["match_id"], lens["id"])
                    duel_entries.append({"duel_id": m["match_id"], "a": m["a"], "b": m["b"], "presentation": pres})
                    block = P.duel_md(fighters, m, pres, "")
                    if rd["stage"] in ("semifinal", "final"):
                        block += "\n" + P.dossier_md(dossiers.get(m[pres["X"]]), "X")
                        block += "\n\n" + P.dossier_md(dossiers.get(m[pres["Y"]]), "Y")
                        block += "\n\n#### Transkrip debat\n\n" + P.transcript_md(m.get("debate"), presentation=pres) + "\n"
                    blocks.append(block)
                payload = {"round": r, "lens": lens, "duels": duel_entries, "stage": rd["stage"]}
                example = {"verdicts": [P.verdict_example(chunk[0]["match_id"], full)]}
                if ptype == "judge":
                    example = {"judge_lens": lens["id"], "evidence_mode_used": "internal", "verdicts": example["verdicts"]}
                stage_extra = ""
                if rd["stage"] in ("semifinal", "final"):
                    stage_extra = (
                        "6. **Debat.** Baca dosir dan transkrip debat. Hargai pembelaan yang berhasil dan konsesi jujur; "
                        "hukum klarifikasi yang sebenarnya mengubah tesis (memindahkan tiang gawang). Nilai argumen "
                        "**setelah** pertukaran: apakah ia masih berdiri?"
                    )
                mapping = {
                    "TOPIC_CONTEXT": P.topic_context(map_obj),
                    "ROUND_LABEL": rd["label"],
                    "DUEL_COUNT": len(chunk),
                    "DUELS": "\n".join(blocks),
                    "LENS_ID": lens["id"],
                    "LENS_LABEL": lens["label"],
                    "LENS_FOCUS": lens["focus"],
                    "STAGE_EXTRA": stage_extra,
                }
                title = "%s — %s (%d duel)" % (rd["label"], lens["label"] if ptype == "judge" else "juri tunggal", len(chunk))
                P.register(self.run, ptype, stage_key, payload, title, template, mapping, example)

    def _make_debate_packets(self, rd, exchange, fighters):
        r = rd["round"]
        stage_key = "round:%d:debate:%s" % (r, exchange)
        map_obj = self.run.load("map.json")
        dossiers = self.run.load("dossiers.json", {})
        for m in rd["matches"]:
            for side in ("a", "b"):
                other = "b" if side == "a" else "a"
                payload = {"round": r, "match_id": m["match_id"], "side": side, "exchange": exchange, "me": m[side], "opponent": m[other]}
                example = {
                    "match_id": m["match_id"],
                    "exchange": exchange,
                    "statement": "<pernyataan 150-500 kata>",
                    "points": [{"claim": "<butir>", "target": "<P2 argumen lawan>"}],
                    "concessions": [],
                    "clarifications": [],
                }
                mapping = {
                    "TOPIC_CONTEXT": P.topic_context(map_obj),
                    "MATCH_LABEL": "%s (`%s`)" % (rd["label"], m["match_id"]),
                    "EXCHANGE_LABEL": P.EXCHANGE_LABEL[exchange],
                    "EXCHANGE_TASK": P.EXCHANGE_TASK[exchange],
                    "MY_FIGHTER": P.fighter_md(fighters[m[side]], "Argumen saya"),
                    "MY_DOSSIER": P.dossier_md(dossiers.get(m[side]), "argumen saya"),
                    "OPP_FIGHTER": P.fighter_md(fighters[m[other]], "Argumen lawan"),
                    "OPP_DOSSIER": P.dossier_md(dossiers.get(m[other]), "argumen lawan"),
                    "TRANSCRIPT": P.transcript_md(m.get("debate"), me=side),
                }
                title = "%s — debat %s (%s)" % (rd["label"], P.EXCHANGE_LABEL[exchange].lower(), m["match_id"])
                P.register(self.run, "debate", stage_key, payload, title, "debate.md", mapping, example)

    # ------------------------------------------------------------ final 4
    def _phase_final4(self):
        r = self.st["current_round"]
        rd = self.run.load_round(r)
        ids = [x for m in rd["matches"] for x in (m["a"], m["b"])]
        pk, pending, done, abandoned = self._stage_state("final4")
        if not pk:
            fighters = self.run.load_fighters()
            map_obj = self.run.load("map.json")
            for fid in ids:
                hist = self.history(fid)
                example = {
                    "fighter_id": fid,
                    "standard_form": ["P1 ...", "P2 ...", "P3 (tersirat) ...", "C ..."],
                    "formal_skeleton": "<kerangka logis>",
                    "hard_core": ["<klaim inti>"],
                    "protective_belt": ["<hipotesis bantu>"],
                    "key_definitions": ["<istilah: definisi>"],
                    "empirical_commitments": ["<komitmen>"],
                    "falsifiers": ["<falsifier>"],
                    "strongest_objections": [{"objection": "<keberatan>", "source": "history", "severity": "high", "status": "partially_answered"}],
                    "vulnerabilities": ["<kerentanan>"],
                    "strengths": ["<kekuatan>"],
                    "assessment": "<penilaian 3-6 kalimat>",
                }
                P.register(
                    self.run, "dossier", "final4", {"fighter_id": fid, "history": hist},
                    "Dosir Final 4 (%s)" % fid, "dossier.md",
                    {
                        "TOPIC_CONTEXT": P.topic_context(map_obj),
                        "FIGHTER": P.fighter_md(fighters[fid], "Argumen"),
                        "HISTORY": history_md(hist),
                    },
                    example,
                )
            return True
        if pending:
            return False
        dossiers = {}
        for rec in pk:
            fid = self.run.packet_payload(rec["id"])["fighter_id"]
            if rec["status"] == "done":
                out = self.run.packet_output(rec["id"])
                dossiers[fid] = {k: v for k, v in out.items() if k not in ("packet_id", "input_hash")}
                dossiers[fid]["packet_id"] = rec["id"]
            else:
                dossiers[fid] = None
                self.run.flag("dossier_missing", "Dosir %s gagal dibuat" % fid)
        self.run.save("dossiers.json", dossiers)
        self.run.log("final4_dossiers", {"fighters": ids, "sha256": self.run.file_hash("dossiers.json")})
        self.run.set_phase("round")
        return True

    def history(self, fid):
        """Kumpulan keberatan yang pernah diarahkan ke petarung ini."""
        items = []
        pop = self.run.load_population()
        sc = pop.get(fid, {}).get("scout")
        if sc:
            items.append({"round": 0, "source": "scouting", "text": sc["weakest_point"]})
        r = 1
        while True:
            rd = self.run.load_round(r)
            if not rd:
                break
            for m in rd["matches"]:
                if m.get("bye") or fid not in (m["a"], m["b"]):
                    continue
                me = "a" if m["a"] == fid else "b"
                opp = "b" if me == "a" else "a"
                for j in m.get("judgments", []):
                    obj = j.get("objections", {}).get("%s_to_%s" % (opp, me))
                    if obj:
                        # Juri menulis dengan label X/Y miliknya; catat label argumen ini.
                        pres = j.get("presentation")
                        label = (" (argumen ini = %s)" % ("X" if pres["X"] == me else "Y")) if pres else ""
                        items.append({"round": r, "source": "%s/%s%s" % (m["match_id"], j["judge"], label), "text": obj})
            r += 1
        seen, uniq = set(), []
        for it in items:
            key = it["text"].strip().lower()
            if key not in seen:
                seen.add(key)
                uniq.append(it)
        return uniq[:15]

    # ------------------------------------------------------ falsification
    def _phase_falsification(self):
        fs = self.st.get("falsification")
        if fs is None:
            queue = self._falsification_queue()
            fs = self.st["falsification"] = {"queue": queue, "index": 0, "results": {}}
            self.run.log("falsification_queue", {"queue": queue})
        idx = fs["index"]
        cand = fs["queue"][idx]
        stage_key = "falsify:%d" % idx
        pk, pending, done, abandoned = self._stage_state(stage_key)
        if not pk:
            self._make_falsification_packets(cand, idx)
            return True
        if pending:
            return False
        verdicts, reports = [], []
        for rec in sorted(done, key=lambda p: p["id"]):
            out = self.run.packet_output(rec["id"])
            verdicts.append(out["verdict"])
            reports.append({"packet_id": rec["id"], "tester": self.run.packet_payload(rec["id"])["tester"], "verdict": out["verdict"]})
        agg = J.aggregate_falsification(verdicts, self.cfg["falsification_panel"])
        fs["results"][cand] = {"verdicts": reports, "aggregate": agg, "rule": "konservatif-mayoritas"}
        self.run.log("falsification_result", {"candidate": cand, "aggregate": agg, "verdicts": verdicts})
        if agg == "INCONCLUSIVE":
            self.run.flag("falsification_inconclusive", "Uji falsifikasi %s tidak dapat dijalankan" % cand)
        if agg != "FALSIFIED":
            self.st["winner"] = cand
            self.st["winner_falsification"] = agg
        else:
            fs["index"] += 1
            if fs["index"] < len(fs["queue"]):
                return True
            self.st["winner"] = None
            self.st["winner_falsification"] = "NO_SURVIVOR"
        self.run.log("winner_declared", {"winner": self.st["winner"], "status": self.st["winner_falsification"]})
        self.run.set_phase("report")
        return True

    def _falsification_queue(self):
        queue = [self.st["champion"], self.st["runner_up"]]
        r = self.st["current_round"]
        sf = self.run.load_round(r - 1)
        if sf and sf["stage"] == "semifinal":
            losers = []
            for m in sf["matches"]:
                js = m.get("judgments", [])
                side = "b" if m["winner_side"] == "a" else "a"
                mean = sum(j["totals"][side] for j in js) / float(len(js)) if js else 0.0
                losers.append((-mean, m["loser"]))
            queue += [fid for _, fid in sorted(losers)]
        return queue[: C.MAX_FALSIFICATION_CANDIDATES]

    def reach(self):
        """Ronde terjauh yang dicapai setiap petarung (juara mendapat +1)."""
        reach = {}
        r = 1
        while True:
            rd = self.run.load_round(r)
            if not rd:
                break
            for m in rd["matches"]:
                for fid in (m["a"], m["b"]):
                    if fid:
                        reach[fid] = r
            r += 1
        if self.st.get("champion"):
            reach[self.st["champion"]] = r
        return reach

    def _rivals(self, cand):
        rivals = []
        final = self.run.load_round(self.st["current_round"])
        fm = final["matches"][0]
        if cand in (fm["a"], fm["b"]):
            rivals.append(fm["b"] if fm["a"] == cand else fm["a"])
        else:
            sf = self.run.load_round(self.st["current_round"] - 1)
            for m in sf["matches"]:
                if cand in (m["a"], m["b"]):
                    rivals.append(m["winner"])
        fighters = self.run.load_fighters()
        seeds = self.run.load("seeding.json")["seeds"]
        reach = self.reach()
        ranked = sorted(reach, key=lambda f: (-reach[f], seeds.get(f, 10 ** 6)))
        for fid in ranked:
            if fid != cand and fid not in rivals and fighters[fid]["stance_id"] != fighters[cand]["stance_id"]:
                rivals.append(fid)
                break
        return rivals

    def _make_falsification_packets(self, cand, idx):
        fighters = self.run.load_fighters()
        map_obj = self.run.load("map.json")
        dossiers = self.run.load("dossiers.json", {})
        rivals = self._rivals(cand)
        hist = self.history(cand)
        role = {
            0: "adalah **juara bracket**",
            1: "adalah **runner-up** (juara bracket gagal uji falsifikasi)",
        }.get(idx, "adalah **semifinalis** (kandidat di atasnya gagal uji falsifikasi)")
        focus = [
            "prediksi empiris dan kontra-contoh konkret",
            "reductio, kasus batas, dan tekanan konseptual",
            "perbandingan dengan rival dan deteksi imunisasi ad hoc",
        ]
        rivals_md = "\n\n".join(P.fighter_md(fighters[r], "Rival %d" % (i + 1)) for i, r in enumerate(rivals)) or "*(tidak ada)*"
        for t in range(self.cfg["falsification_panel"]):
            payload = {"fighter_id": cand, "candidate_index": idx, "tester": "T%d" % (t + 1), "rivals": rivals, "history": hist}
            example = {
                "fighter_id": cand,
                "evidence_mode_used": "internal",
                "commitments": [{"id": "C1", "claim": "<komitmen>", "type": "conceptual", "core": True}],
                "tests": [
                    {
                        "id": "T1",
                        "kind": "counterexample",
                        "target_commitment": "C1",
                        "description": "<uji>",
                        "result": "passed",
                        "reasoning": "<penalaran hasil uji>",
                    }
                ],
                "immunization_detected": False,
                "ad_hoc_notes": "<opsional>",
                "verdict": "SURVIVED",
                "required_qualifications": [],
                "residual_confidence": 0.6,
                "summary": "<ringkasan 3-6 kalimat>",
                "evidence": [],
            }
            P.register(
                self.run, "falsification", "falsify:%d" % idx, payload,
                "Uji falsifikasi %s — penguji T%d" % (cand, t + 1), "falsification.md",
                {
                    "TESTER_LABEL": "penguji T%d" % (t + 1),
                    "TESTER_FOCUS": focus[t % len(focus)],
                    "CANDIDATE_ROLE": role,
                    "TOPIC_CONTEXT": P.topic_context(map_obj),
                    "FIGHTER": P.fighter_md(fighters[cand], "Argumen"),
                    "DOSSIER": P.dossier_md(dossiers.get(cand), "argumen ini"),
                    "HISTORY": history_md(hist),
                    "RIVALS": rivals_md,
                },
                example,
            )

    # ------------------------------------------------------------ report
    def _phase_report(self):
        from . import integrity, report

        pre = integrity.verify(self.run, include_report=False)
        report.write_report(self.run, self, pre)
        full = integrity.verify(self.run, include_report=True)
        self.run.save("integrity.json", full)
        self.run.log("report_generated", {"report_sha256": self.run.file_hash("report.md"), "integrity_ok": full["ok"], "digest": full["digest"]})
        self.run.set_phase("done")
        return True

    def _phase_done(self):
        return False


def seeding_order(pop, seed):
    valid = [i for i, p in pop.items() if p["status"] == "valid"]
    tie = {fid: rng_for(seed, "seed-tiebreak", fid).random() for fid in valid}
    return sorted(valid, key=lambda f: (len(pop[f]["scout"]["fatal_flaws"]), -pop[f]["scout"]["calibrated_total"], tie[f]))


def history_md(hist):
    if not hist:
        return "*(Belum ada riwayat serangan.)*"
    return "\n".join("- [%s] %s" % (h["source"], h["text"]) for h in hist)


def check_packet(run, packet_id):
    """Validasi output.json sebuah paket. Mengembalikan list galat (kosong = OK)."""
    rec = run.state["packets"].get(packet_id)
    if rec is None:
        return ["Paket %s tidak dikenal." % packet_id]
    path = run.packet_output_path(packet_id)
    if not os.path.exists(path):
        return ["File output belum ada: %s" % path]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            output = json.load(fh)
    except (ValueError, UnicodeDecodeError) as exc:
        return ["JSON tidak valid: %s" % exc]
    payload = run.packet_payload(packet_id)
    return validate_output(rec["type"], output, rec, payload)
