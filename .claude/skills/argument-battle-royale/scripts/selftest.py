#!/usr/bin/env python3
"""Uji end-to-end engine dengan worker SINTETIS (tanpa LLM).

Menguji: pemetaan -> generasi -> dedup (otomatis + review) -> validasi/kalibrasi
-> refill -> seeding -> bracket -> eliminasi -> deep review -> Final 4 ->
semifinal/final (debat + panel) -> falsifikasi (termasuk fallback ke runner-up)
-> laporan -> verifikasi integritas; juga output ditolak, paket ditinggalkan,
resume dari disk, dan deteksi manipulasi file.

Konten sintetis TIDAK bermakna filosofis; ia hanya menguji mesin.

Contoh:
  python3 selftest.py                      # rangkaian uji standar (3 mode)
  python3 selftest.py --mode balanced --population 1000 --keep
"""

import argparse
import json
import os
import random
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import config as C  # noqa: E402
from engine import integrity  # noqa: E402
from engine.phases import Engine, check_packet  # noqa: E402
from engine.store import Run  # noqa: E402
from engine.util import atomic_write_json, sha256_text  # noqa: E402

SYL = ["ka", "ri", "mo", "tu", "le", "sa", "no", "pi", "de", "ga", "lu", "ve", "zo", "ha", "ne", "bi", "ro", "ta", "mi", "ku"]
VOCAB = sorted({a + b + c for a in SYL for b in SYL for c in SYL[:8]})


def words(rng, n):
    return " ".join(rng.choice(VOCAB) for _ in range(n))


def quality(fid_or_text):
    return int(sha256_text(fid_or_text)[:4], 16) % 60 / 10.0 + 3.0  # 3.0 .. 8.9


def scores_for(key, rng, noise=0.8):
    q = quality(key)
    return [round(max(0, min(10, q + rng.uniform(-noise, noise))), 1) for _ in C.RUBRIC_KEYS]


def fake_fighter(rng, slot_id, map_ids):
    return {
        "slot_id": slot_id,
        "title": "Argumen " + words(rng, 3),
        "thesis": "Tesis " + words(rng, 12),
        "term_readings": [rng.choice(map_ids)],
        "definitions": [{"term": "istilah", "definition": "definisi " + words(rng, 6)}],
        "premises": [
            {"id": "P%d" % (i + 1), "text": "Premis " + words(rng, 14), "type": rng.choice(C.PREMISE_TYPES), "support": "dukungan " + words(rng, 5)}
            for i in range(rng.randint(2, 4))
        ],
        "inference_type": rng.choice(C.INFERENCE_TYPES),
        "inference": "Inferensi " + words(rng, 10),
        "conclusion": "Kesimpulan " + words(rng, 10),
        "empirical_commitments": ["komitmen " + words(rng, 5)],
        "falsifiers": ["falsifier " + words(rng, 6)],
        "anticipated_objection": "keberatan " + words(rng, 8),
        "reply": "balasan " + words(rng, 8),
        "scope": "cakupan " + words(rng, 5),
    }


class FakeWorker:
    def __init__(self, seed, falsify_champion=True, bad_first=True, dq_rate=0.04):
        self.rng = random.Random(seed)
        self.dq_threshold = int(dq_rate * 256)
        self.falsify_champion = falsify_champion
        self.bad_first = bad_first
        self.bad_done = set()
        self.fals_calls = 0

    def work(self, run, rec):
        payload = run.packet_payload(rec["id"])
        t = rec["type"]
        base = {"packet_id": rec["id"], "input_hash": rec["input_hash"]}
        # Uji jalur penolakan: output pertama untuk tipe tertentu sengaja rusak.
        if self.bad_first and t not in self.bad_done and t in ("generate", "judge"):
            self.bad_done.add(t)
            return dict(base, broken=True)
        out = getattr(self, "w_" + t)(run, rec, payload)
        out.update(base)
        return out

    def w_map(self, run, rec, payload):
        return {
            "topic_restated": "Rumusan sintetis untuk pengujian mesin",
            "question_type": "mixed",
            "presuppositions": ["presuposisi uji"],
            "key_terms": [{"term": "istilah", "readings": [{"id": "T1a", "label": "bacaan a", "definition": "definisi bacaan a"}, {"id": "T1b", "label": "bacaan b", "definition": "definisi bacaan b"}]}],
            "stances": [{"id": "S%d" % i, "label": "Posisi %d" % i, "description": "deskripsi posisi %d" % i} for i in range(1, 5)],
            "frameworks": [{"id": "K%d" % i, "label": "Kerangka %d" % i, "description": "deskripsi kerangka %d" % i} for i in range(1, 6)]
            + [{"id": "K6", "label": "Kerangka khusus", "description": "hanya cocok untuk S1 dan S2", "compatible_stances": ["S1", "S2"]}],
            "strategies": [{"id": "M%d" % i, "label": "Strategi %d" % i, "description": "deskripsi strategi %d" % i} for i in range(1, 5)],
            "cruxes": ["krusial satu", "krusial dua"],
            "evidence_domains": ["domain uji"],
        }

    def w_generate(self, run, rec, payload):
        out = []
        prev = None
        for i, s in enumerate(payload["slots"]):
            f = fake_fighter(self.rng, s["slot_id"], payload["reading_ids"])
            if prev is not None and i % 23 == 7:  # duplikat persis -> dedup otomatis
                f = dict(prev, slot_id=s["slot_id"])
            elif prev is not None and i % 23 == 15:  # hampir duplikat -> kandidat review
                f = json.loads(json.dumps(prev))
                f["slot_id"] = s["slot_id"]
                for p in f["premises"]:
                    toks = p["text"].split()
                    for k in range(0, len(toks), 3):
                        toks[k] = self.rng.choice(VOCAB)
                    p["text"] = " ".join(toks)
                f["inference"] = "Inferensi " + words(self.rng, 10)
            out.append(f)
            prev = f
        return {"fighters": out}

    def w_dedup_review(self, run, rec, payload):
        return {"decisions": [{"pair_id": p["pair_id"], "same_argument": p["similarity"] >= 0.55, "reason": "uji sintetis"} for p in payload["pairs"]]}

    def w_scout(self, run, rec, payload):
        evals = []
        for fid in payload["fighter_ids"]:
            invalid = int(sha256_text(fid + "dq")[:2], 16) < self.dq_threshold
            evals.append({
                "fighter_id": fid,
                "valid": not invalid,
                "dq_codes": ["DQ_NOT_ARGUMENT"] if invalid else [],
                "scores": scores_for(fid, self.rng),
                "fatal_flaws": ["FF_NON_SEQUITUR"] if int(sha256_text(fid + "ff")[:2], 16) < 15 else [],
                "strongest_point": "titik kuat " + fid,
                "weakest_point": "titik lemah " + fid,
            })
        return {"evaluations": evals}

    def _verdicts(self, payload, full):
        vs = []
        for d in payload["duels"]:
            x = d[d["presentation"]["X"]]
            y = d[d["presentation"]["Y"]]
            sx, sy = scores_for(x, self.rng, 1.5), scores_for(y, self.rng, 1.5)
            wx = sum(a * b for a, b in zip(sx, C.RUBRIC_WEIGHTS)) >= sum(a * b for a, b in zip(sy, C.RUBRIC_WEIGHTS))
            v = {
                "duel_id": d["duel_id"], "scores_x": sx, "scores_y": sy, "fatal_x": [], "fatal_y": [],
                "winner": "X" if wx else "Y", "decisive_factor": "faktor uji",
                "rationale": "alasan sintetis untuk pengujian mesin",
                "objection_x_to_y": "keberatan X ke Y %s" % y, "objection_y_to_x": "keberatan Y ke X %s" % x,
            }
            if full:
                v.update({"steelman_x": "steelman sintetis X panjang", "steelman_y": "steelman sintetis Y panjang",
                          "reply_quality_x": "sebagian", "reply_quality_y": "sebagian", "confidence": 0.6,
                          "dissent_risk": "bila premis dua gugur", "evidence": []})
            vs.append(v)
        return vs

    def w_duel(self, run, rec, payload):
        return {"verdicts": self._verdicts(payload, False)}

    def w_judge(self, run, rec, payload):
        return {"judge_lens": payload["lens"]["id"], "evidence_mode_used": "internal", "verdicts": self._verdicts(payload, True)}

    def w_dossier(self, run, rec, payload):
        return {
            "fighter_id": payload["fighter_id"],
            "standard_form": ["P1 sintetis", "P2 sintetis", "C sintetis"],
            "formal_skeleton": "P1, P2 maka C",
            "hard_core": ["inti"], "protective_belt": ["sabuk"], "key_definitions": [],
            "empirical_commitments": ["komitmen"], "falsifiers": ["falsifier"],
            "strongest_objections": [{"objection": "keberatan sintetis %d" % i, "source": "new", "severity": "medium", "status": "answered"} for i in range(3)],
            "vulnerabilities": ["rentan"], "strengths": ["kuat"],
            "assessment": "penilaian sintetis yang cukup panjang untuk lolos validasi",
        }

    def w_debate(self, run, rec, payload):
        return {
            "match_id": payload["match_id"], "exchange": payload["exchange"],
            "statement": "Pernyataan debat sintetis. " * 8,
            "points": [{"claim": "butir serangan sintetis", "target": "P1"}],
            "concessions": [], "clarifications": [],
        }

    def w_falsification(self, run, rec, payload):
        self.fals_calls += 1
        fail = self.falsify_champion and payload["candidate_index"] == 0
        tests = []
        for i, kind in enumerate(C.FALSIFICATION_REQUIRED_KINDS + ["conceptual_stress"]):
            res = "passed"
            if fail and i == 0:
                res = "failed"
            elif not fail and i == 1:
                res = "damaged"
            tests.append({"id": "T%d" % (i + 1), "kind": kind, "target_commitment": "C1" if i == 0 else "C2",
                          "description": "uji sintetis jenis %s" % kind, "result": res, "reasoning": "penalaran sintetis hasil uji"})
        return {
            "fighter_id": payload["fighter_id"], "evidence_mode_used": "internal",
            "commitments": [{"id": "C1", "claim": "komitmen inti sintetis", "type": "conceptual", "core": True},
                            {"id": "C2", "claim": "komitmen bantu sintetis", "type": "empirical", "core": False}],
            "tests": tests, "immunization_detected": False,
            "verdict": "FALSIFIED" if fail else "SURVIVED_WITH_DAMAGE",
            "required_qualifications": [] if fail else ["kualifikasi sintetis"],
            "residual_confidence": 0.2 if fail else 0.6,
            "summary": "ringkasan sintetis uji falsifikasi yang cukup panjang",
        }


def run_case(mode, population, keep=False, threshold=None, dq_rate=0.04):
    tmp = tempfile.mkdtemp(prefix="abr-selftest-")
    run_dir = os.path.join(tmp, "run")
    t0 = time.time()
    cfg = {
        "topic": "Topik uji sintetis %s %d" % (mode, population),
        "mode": mode, "population": population,
        "deep_round_threshold": threshold or C.MODES[mode]["deep_round_threshold"],
        "max_parallel": 4, "random_seed": 12345, "evidence_mode": "internal", "language": "id",
        "output_dir": run_dir,
    }
    for k in ("gen_batch", "scout_batch", "early_method", "duel_batch", "deep_panel", "deep_batch", "semifinal_panel",
              "final_panel", "falsification_panel", "dedup_review", "max_refill_rounds"):
        cfg[k] = C.MODES[mode][k]
    Run(run_dir).create(cfg)
    worker = FakeWorker(7, dq_rate=dq_rate)
    abandoned_one = False
    iterations = 0
    scenes_seen = set()
    while True:
        iterations += 1
        run = Run(run_dir)  # muat ulang dari disk setiap iterasi = uji resume
        summary = Engine(run).next()
        a = summary.get("anim") or {}
        assert "scene" in a and 0 <= a["percent"] <= 100, a
        if a.get("show"):
            assert a["frame"].strip(), "frame flipbook kosong"
        scenes_seen.add(a["scene"])
        assert os.path.exists(run.path("arena.html")), "arena.html tidak ditulis"
        if summary["action"] == "done":
            break
        assert summary["action"] == "execute_packets", summary
        assert summary["packets"], "tidak ada paket pending tetapi belum selesai: %s" % summary
        for pk in summary["packets"]:
            rec = run.state["packets"][pk["packet_id"]]
            # Uji fallback: tinggalkan satu paket juri eliminasi/deep review.
            if not abandoned_one and rec["type"] in ("duel", "judge") and rec["stage"].startswith("round:1:"):
                abandoned_one = True
                with run.lock():
                    run.abandon_packet(rec["id"], "uji fallback")
                    run.save_state()
                continue
            out = worker.work(run, rec)
            atomic_write_json(run.packet_output_path(rec["id"]), out)
            errs = check_packet(run, rec["id"])
            if "broken" not in out:
                assert not errs, (rec["id"], errs[:5])
        assert iterations < 500, "loop tidak konvergen"
    run = Run(run_dir)
    res = integrity.verify(run)
    assert res["ok"], json.dumps([c for c in res["checks"] if not c["ok"]], indent=2)
    st = run.state
    rejected = sum(1 for e in open(run.ledger_path) if '"packet_rejected"' in e)
    assert rejected >= 1, "jalur penolakan output tidak teruji"
    assert st["winner"] == st["runner_up"], "fallback falsifikasi ke runner-up tidak terjadi"
    if dq_rate > 0.15:
        assert st["generation_round"] >= 1, "jalur refill tidak teruji"
    # Uji deteksi manipulasi: ubah pemenang final lalu verifikasi harus gagal.
    rpath = run.round_path(st["current_round"])
    original = open(rpath, encoding="utf-8").read()
    rd = json.loads(original)
    m = rd["matches"][0]
    m["winner"], m["loser"] = m["loser"], m["winner"]
    atomic_write_json(rpath, rd)
    tampered = integrity.verify(Run(run_dir))
    failed = sorted(c["name"] for c in tampered["checks"] if not c["ok"])
    assert not tampered["ok"] and "round_files" in failed, failed
    with open(rpath, "w", encoding="utf-8") as fh:
        fh.write(original)
    assert integrity.verify(Run(run_dir))["ok"]
    assert {"wizard", "battle", "rocket", "trophy"} <= scenes_seen, scenes_seen
    html = open(run.path("arena.html"), encoding="utf-8").read()
    assert "abr-data" in html and '"done":true' in html
    arena_run = json.load(open(run.path("arena-data.json"), encoding="utf-8"))["run"]
    kinds = [e["t"] for e in arena_run["events"]]
    assert kinds.count("winner") == 1 and "fals" in kinds and kinds.count("round") == st["current_round"], kinds
    for e in arena_run["events"]:
        if e["t"] == "match":
            assert e["w"] in (e["a"], e["b"]) and e["hits"], e["id"]
            assert all(h["by"] in ("a", "b") for h in e["hits"])
            for fid in (e["a"], e["b"]):
                assert fid in arena_run["fighters"], fid
    pop = run.load_population()
    counts = {}
    for p in pop.values():
        counts[p["status"]] = counts.get(p["status"], 0) + 1
    info = {
        "mode": mode, "population": population, "dq_rate": dq_rate, "seconds": round(time.time() - t0, 1),
        "packets": len(st["packets"]), "iterations": iterations, "status_counts": counts,
        "generation_rounds": st["generation_round"] + 1, "rounds": st["current_round"],
        "champion": st["champion"], "winner": st["winner"], "tamper_detected_by": failed,
        "flags": sorted({f["code"] for f in st["flags"]}), "run_dir": run_dir if keep else None,
    }
    if not keep:
        shutil.rmtree(tmp)
    return info


def check_animation():
    """Semua adegan dapat dirender ke ANSI, teks mini, dan data web."""
    from engine import anim

    for scene in anim.SCENES:
        for i, fr in enumerate(anim.frames(scene)):
            grid = anim.rasterize(fr)
            assert len(grid) == anim.CANVAS_H and all(len(r) == anim.CANVAS_W for r in grid)
            assert any(ch != "." for row in grid for ch in row), (scene, i)
            assert len(anim.ansi(grid, "truecolor")) == anim.CANVAS_H // 2
            assert len(anim.ansi(grid, "256")) == anim.CANVAS_H // 2
        info = {"scene": scene, "stage": "X", "stage_index": 0, "stage_count": 15, "percent": 50, "caption": "uji"}
        assert anim.mini(info, 0) and anim.statusline(info)
    data = anim.web_data()
    for fr_list in data["scenes"].values():
        for fr in fr_list:
            for layer in fr["l"]:
                assert layer[0] in data["sprites"]
            for x, y, c in fr["p"]:
                assert c in data["palette"]
    for rows in data["sprites"].values():
        assert len({len(r) for r in rows}) == 1, "sprite tidak persegi"
        assert all(ch == "." or ch in data["palette"] for r in rows for ch in r)


def check_serve():
    """`abr.py serve` melayani halaman arena dan datanya."""
    import subprocess
    import urllib.request

    tmp = tempfile.mkdtemp(prefix="abr-serve-")
    try:
        run_dir = os.path.join(tmp, "run")
        abr = os.path.join(os.path.dirname(os.path.abspath(__file__)), "abr.py")
        subprocess.run([sys.executable, abr, "init", "Topik uji server arena", "population=8", "output_dir=" + run_dir], check=True, capture_output=True)
        subprocess.run([sys.executable, abr, "next", "--run", run_dir], check=True, capture_output=True)
        proc = subprocess.Popen([sys.executable, abr, "serve", "--run", run_dir, "--port", "0"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            url = json.loads(proc.stdout.readline().decode())["serve"]
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            page = opener.open(url, timeout=10).read().decode()
            data = json.loads(opener.open(url + "arena-data.json", timeout=10).read().decode())
            assert "abr-data" in page and data["run"]["info"]["scene"] == "wizard", data["run"]["info"]
        finally:
            proc.terminate()
            proc.wait(timeout=10)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=list(C.MODES))
    ap.add_argument("--population", type=int)
    ap.add_argument("--threshold", type=int)
    ap.add_argument("--dq-rate", type=float, default=0.04, help="proporsi petarung sintetis yang didiskualifikasi")
    ap.add_argument("--keep", action="store_true", help="simpan direktori run untuk diperiksa")
    args = ap.parse_args()
    if args.mode:
        cases = [(args.mode, args.population or 1000, args.dq_rate)]
    else:
        cases = [("efficient", 1000, 0.04), ("balanced", 150, 0.04), ("full", 40, 0.04), ("balanced", 120, 0.25)]
    check_animation()
    check_serve()
    print(json.dumps({"animation": "ok", "serve": "ok"}))
    for mode, pop, dq in cases:
        info = run_case(mode, pop, keep=args.keep, threshold=args.threshold, dq_rate=dq)
        print(json.dumps(info, ensure_ascii=False))
    print("SEMUA UJI LULUS")


if __name__ == "__main__":
    main()
