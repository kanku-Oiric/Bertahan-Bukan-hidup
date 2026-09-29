"""Aturan keputusan yang deterministik dan dapat diaudit ulang.

Aturan keputusan satu juri (dihitung engine dari skor, bukan dari klaim juri):
  1. Argumen dengan lebih sedikit cacat fatal menang.
  2. Jika jumlah cacat fatal sama, total rubrik tertimbang lebih tinggi menang.
  3. Jika selisih total < NEAR_TIE (seri praktis), pilihan holistik juri menentukan.
Pilihan juri yang bertentangan dengan aturan dicatat sebagai inkonsistensi;
aturan rubrik yang berlaku.

Agregasi panel: suara mayoritas; bila seri (panel genap karena juri gugur),
jumlah selisih total lintas juri; bila masih seri, undian ber-seed.
"""

from . import config as C
from .util import rng_for


def weighted_total(scores):
    return round(sum(s * w for s, w in zip(scores, C.RUBRIC_WEIGHTS)) / 10.0, 3)


def judge_decision(scores_a, scores_b, fatal_a, fatal_b, stated):
    """Mengembalikan (pemenang 'a'|'b', basis, konsisten?)."""
    ta, tb = weighted_total(scores_a), weighted_total(scores_b)
    if len(fatal_a) != len(fatal_b):
        winner = "a" if len(fatal_a) < len(fatal_b) else "b"
        basis = "fatal_flaw"
    elif abs(ta - tb) >= C.NEAR_TIE:
        winner = "a" if ta > tb else "b"
        basis = "rubric_total"
    else:
        winner = stated
        basis = "holistic_tiebreak"
    return winner, basis, winner == stated


def aggregate_panel(judgments, seed, match_id):
    votes = {"a": 0, "b": 0}
    diff = 0.0
    for j in judgments:
        votes[j["rule_winner"]] += 1
        diff += j["totals"]["a"] - j["totals"]["b"]
    if votes["a"] != votes["b"]:
        return ("a" if votes["a"] > votes["b"] else "b"), "majority", votes
    if abs(diff) > 1e-9:
        return ("a" if diff > 0 else "b"), "score_sum_tiebreak", votes
    r = rng_for(seed, "coin", match_id)
    return r.choice(["a", "b"]), "seeded_coin", votes


def unmap_verdict(verdict, presentation):
    """presentation: {'X': 'a'|'b', 'Y': 'a'|'b'} -> nilai dalam sisi a/b."""
    side_of = {"X": presentation["X"], "Y": presentation["Y"]}
    scores = {side_of["X"]: verdict["scores_x"], side_of["Y"]: verdict["scores_y"]}
    fatal = {side_of["X"]: verdict.get("fatal_x", []), side_of["Y"]: verdict.get("fatal_y", [])}
    objections = {
        "%s_to_%s" % (side_of["X"], side_of["Y"]): verdict["objection_x_to_y"],
        "%s_to_%s" % (side_of["Y"], side_of["X"]): verdict["objection_y_to_x"],
    }
    stated = side_of[verdict["winner"]]
    return scores, fatal, objections, stated


def build_judgment(verdict, presentation, packet_id, judge_id, lens_label):
    scores, fatal, objections, stated = unmap_verdict(verdict, presentation)
    winner, basis, consistent = judge_decision(scores["a"], scores["b"], fatal["a"], fatal["b"], stated)
    j = {
        "packet_id": packet_id,
        "judge": judge_id,
        "lens": lens_label,
        "presentation": presentation,
        "scores": scores,
        "totals": {"a": weighted_total(scores["a"]), "b": weighted_total(scores["b"])},
        "fatal": fatal,
        "stated_winner": stated,
        "rule_winner": winner,
        "basis": basis,
        "consistent": consistent,
        "decisive_factor": verdict["decisive_factor"],
        "rationale": verdict["rationale"],
        "objections": objections,
    }
    for key in ("confidence", "dissent_risk", "evidence"):
        if key in verdict:
            j[key] = verdict[key]
    if "steelman_x" in verdict:
        sx, sy = presentation["X"], presentation["Y"]
        j["steelman"] = {sx: verdict["steelman_x"], sy: verdict["steelman_y"]}
        j["reply_quality"] = {sx: verdict["reply_quality_x"], sy: verdict["reply_quality_y"]}
    return j


def score_judgment(scout_a, scout_b):
    """Duel berbasis skor scouting (mode efficient, atau fallback)."""
    fa, fb = scout_a["fatal_flaws"], scout_b["fatal_flaws"]
    ta, tb = scout_a["calibrated_total"], scout_b["calibrated_total"]
    if len(fa) != len(fb):
        winner, basis = ("a" if len(fa) < len(fb) else "b"), "fatal_flaw"
    elif ta != tb:
        winner, basis = ("a" if ta > tb else "b"), "scout_total"
    else:
        winner, basis = "a", "seed_order"
    return {
        "judge": "SCOUT",
        "lens": "skor scouting terkalibrasi",
        "totals": {"a": ta, "b": tb},
        "fatal": {"a": fa, "b": fb},
        "rule_winner": winner,
        "basis": basis,
        "consistent": True,
    }


def aggregate_falsification(verdicts, panel_size):
    """Aturan konservatif-mayoritas: urutkan verdict dari yang terberat; ambil
    verdict pada indeks ceil(k/2)-1. k=1 -> verdict itu; k=2 -> terberat;
    k=3 -> median."""
    if not verdicts:
        return "INCONCLUSIVE"
    ordered = sorted(verdicts, key=lambda v: -C.FALSIFICATION_SEVERITY[v])
    k = len(ordered)
    idx = (k + 1) // 2 - 1
    return ordered[idx]


def calibrate(evals_by_packet, anchors):
    """Kalibrasi antar-paket scouting memakai petarung jangkar.

    evals_by_packet: {packet_id: {fighter_id: raw_total}}
    Mengembalikan ({packet_id: offset}, {anchor_id: median_total}).
    """
    anchor_totals = {}
    for pid, evals in evals_by_packet.items():
        for a in anchors:
            if a in evals:
                anchor_totals.setdefault(a, []).append(evals[a])
    medians = {}
    for a, vals in anchor_totals.items():
        vals = sorted(vals)
        n = len(vals)
        medians[a] = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2.0
    offsets = {}
    for pid, evals in evals_by_packet.items():
        diffs = [medians[a] - evals[a] for a in anchors if a in evals and a in medians and len(anchor_totals[a]) > 1]
        if diffs:
            off = sum(diffs) / len(diffs)
            off = max(-C.CALIBRATION_CLAMP, min(C.CALIBRATION_CLAMP, off))
        else:
            off = 0.0
        offsets[pid] = round(off, 3)
    return offsets, medians
