"""Verifikasi integritas hasil turnamen.

Semua pemeriksaan bersifat deterministik dan dapat dijalankan ulang kapan pun
(`abr.py verify`). Pemeriksaan:
  1. ledger_chain        rantai hash ledger utuh (tidak ada entri yang diubah/dihapus)
  2. packet_outputs      setiap output paket yang diserap tidak berubah sejak diserap
  3. locked_population   fighters.jsonl & population.json tidak berubah sejak seeding
  4. seeding             urutan unggulan = hasil hitung ulang dari skor scouting
  5. bracket             ronde 1 dibangun dari seeding; ronde berikutnya dari pemenang
  6. verdicts            setiap putusan juri & panel dihitung ulang dari skor mentah
  7. round_files         file ronde tidak berubah sejak ronde ditutup
  8. champion            juara = pemenang final
  9. falsification       agregasi uji falsifikasi & penetapan pemenang dihitung ulang
 10. population_counts   status populasi konsisten dengan jumlah petarung
 11. report              (opsional) laporan konsisten dengan state & memuat formula pemenang
"""

import os

from . import bracket as B
from . import config as C
from . import judging as J
from .util import canonical_json, now_iso, read_jsonl, sha256_file, sha256_text


class Checker:
    def __init__(self):
        self.checks = []

    def add(self, name, ok, detail=""):
        self.checks.append({"name": name, "ok": bool(ok), "detail": detail})
        return ok


def _ledger(run, ck):
    rows = read_jsonl(run.ledger_path)
    prev = "0" * 64
    for i, e in enumerate(rows):
        body = {k: e[k] for k in ("seq", "ts", "event", "data", "prev")}
        h = sha256_text(e["prev"] + canonical_json(body))
        if e["seq"] != i or e["prev"] != prev or e["hash"] != h:
            ck.add("ledger_chain", False, "rantai putus pada seq %d" % i)
            return rows
        prev = e["hash"]
    ck.add("ledger_chain", True, "%d entri, hash terakhir %s" % (len(rows), prev[:16]))
    return rows


def _packet_outputs(run, ck, rows):
    ingested = {e["data"]["id"]: e["data"]["output_sha256"] for e in rows if e["event"] == "packet_ingested"}
    bad = []
    for pid, h in ingested.items():
        path = run.packet_output_path(pid)
        if not os.path.exists(path) or sha256_file(path) != h:
            bad.append(pid)
        rec = run.state["packets"].get(pid)
        if rec is None or rec.get("output_sha256") != h or rec["status"] != "done":
            bad.append(pid + "(state)")
    ck.add("packet_outputs", not bad, "%d output diperiksa%s" % (len(ingested), (", berubah: " + ", ".join(bad[:10])) if bad else ""))


def _locked(run, ck, rows):
    ev = [e for e in rows if e["event"] == "seeding_locked"]
    if not ev:
        ck.add("locked_population", True, "belum seeding")
        return False
    d = ev[-1]["data"]
    ok = (
        sha256_file(run.fighters_path) == d["fighters_sha256"]
        and sha256_file(run.path("population.json")) == d["population_sha256"]
        and run.file_hash("seeding.json") == d["seeding_sha256"]
    )
    ck.add("locked_population", ok, "petarung, populasi, dan seeding %s sejak dikunci" % ("tidak berubah" if ok else "BERUBAH"))
    return True


def _seeding(run, ck):
    from .phases import seeding_order

    pop = run.load_population()
    seeding = run.load("seeding.json")
    valid_or_cut = {i: p for i, p in pop.items() if p["status"] in ("valid", "cut_capacity")}
    tmp = {i: dict(p, status="valid") for i, p in valid_or_cut.items()}
    order = seeding_order(tmp, run.cfg["random_seed"])[: run.cfg["population"]]
    ok = order == seeding["order"] and all(seeding["seeds"][f] == i + 1 for i, f in enumerate(order))
    ck.add("seeding", ok, "%d unggulan dihitung ulang dari skor scouting" % len(order))
    return seeding


def _judgment_ok(j):
    if j["judge"] == "SCOUT":
        return True
    ta, tb = J.weighted_total(j["scores"]["a"]), J.weighted_total(j["scores"]["b"])
    if abs(ta - j["totals"]["a"]) > 1e-6 or abs(tb - j["totals"]["b"]) > 1e-6:
        return False
    w, basis, cons = J.judge_decision(j["scores"]["a"], j["scores"]["b"], j["fatal"]["a"], j["fatal"]["b"], j["stated_winner"])
    return w == j["rule_winner"] and basis == j["basis"] and cons == j["consistent"]


def _rounds(run, ck, rows, seeding):
    pop = run.load_population()
    seeds = seeding["seeds"]
    errors = []
    verdicts = 0
    r = 1
    prev = None
    completed = {e["data"]["round"]: e["data"]["round_sha256"] for e in rows if e["event"] == "round_completed"}
    round_file_bad = []
    last = None
    while True:
        rd = run.load_round(r)
        if not rd:
            break
        if r == 1:
            _, expect = B.first_round(seeding["order"], 1)
        else:
            expect = B.next_round(prev["matches"], seeds, r)
        got = [(m["a"], m["b"]) for m in rd["matches"]]
        if got != [(m["a"], m["b"]) for m in expect]:
            errors.append("R%02d: pasangan tidak sesuai bracket" % r)
        if len(rd["matches"]) * 2 != rd["slots"]:
            errors.append("R%02d: jumlah slot tidak konsisten" % r)
        entrants = [x for m in rd["matches"] for x in (m["a"], m["b"]) if x]
        if len(entrants) != len(set(entrants)):
            errors.append("R%02d: petarung muncul dua kali" % r)
        if rd["status"] == "done":
            if r in completed and sha256_file(run.round_path(r)) != completed[r]:
                round_file_bad.append("R%02d" % r)
            if r not in completed:
                round_file_bad.append("R%02d(tanpa ledger)" % r)
            for m in rd["matches"]:
                if m["bye"]:
                    if m["winner"] != m["a"] or m["b"] is not None:
                        errors.append("%s: bye tidak sah" % m["match_id"])
                    continue
                if m["winner"] not in (m["a"], m["b"]) or m["loser"] not in (m["a"], m["b"]) or m["winner"] == m["loser"]:
                    errors.append("%s: pemenang/kalah tidak sah" % m["match_id"])
                    continue
                js = m.get("judgments", [])
                if not js:
                    errors.append("%s: tanpa penilaian" % m["match_id"])
                    continue
                for j in js:
                    verdicts += 1
                    if not _judgment_ok(j):
                        errors.append("%s: putusan juri %s tidak dapat dihitung ulang" % (m["match_id"], j["judge"]))
                if m["method"] in ("score", "score_fallback"):
                    j2 = J.score_judgment(pop[m["a"]]["scout"], pop[m["b"]]["scout"])
                    side = j2["rule_winner"]
                else:
                    side, basis, votes = J.aggregate_panel(js, run.cfg["random_seed"], m["match_id"])
                    if votes != m["votes"] or basis != m["basis"]:
                        errors.append("%s: suara panel tidak cocok" % m["match_id"])
                if m[side] != m["winner"]:
                    errors.append("%s: pemenang tidak sesuai agregasi" % m["match_id"])
        prev = rd
        last = rd
        r += 1
    ck.add("bracket", not [e for e in errors if "bracket" in e or "slot" in e or "dua kali" in e], "; ".join(e for e in errors if "bracket" in e or "slot" in e or "dua kali" in e) or "%d ronde konsisten" % (r - 1))
    verr = [e for e in errors if not ("bracket" in e or "slot" in e or "dua kali" in e)]
    ck.add("verdicts", not verr, "; ".join(verr[:10]) or "%d penilaian juri dihitung ulang" % verdicts)
    ck.add("round_files", not round_file_bad, ", ".join(round_file_bad) or "semua ronde tertutup cocok dengan ledger")
    return last


def _champion(run, ck, last):
    st = run.state
    if not st.get("champion"):
        ck.add("champion", True, "belum ada juara")
        return
    ok = last is not None and last["stage"] == "final" and last["status"] == "done" and last["matches"][0]["winner"] == st["champion"]
    ck.add("champion", ok, "juara %s = pemenang final" % st["champion"] if ok else "juara tidak cocok dengan final")


def _falsification(run, ck):
    st = run.state
    fs = st.get("falsification")
    if not fs or st["phase"] not in ("report", "done"):
        ck.add("falsification", True, "belum selesai")
        return
    errors = []
    winner = None
    for idx, cand in enumerate(fs["queue"][: fs["index"] + 1]):
        recs = [p for p in st["packets"].values() if p["stage"] == "falsify:%d" % idx and p["status"] == "done"]
        verdicts = [run.packet_output(p["id"])["verdict"] for p in recs]
        agg = J.aggregate_falsification(verdicts, run.cfg["falsification_panel"])
        stored = fs["results"].get(cand, {}).get("aggregate")
        if agg != stored:
            errors.append("%s: agregat %s != tersimpan %s" % (cand, agg, stored))
        if agg != "FALSIFIED" and winner is None:
            winner = cand
    if winner != st.get("winner"):
        errors.append("pemenang %s != hitung ulang %s" % (st.get("winner"), winner))
    ck.add("falsification", not errors, "; ".join(errors) or "pemenang tahan-uji: %s" % (st.get("winner") or "tidak ada"))


def _population(run, ck):
    fighters = read_jsonl(run.fighters_path)
    pop = run.load_population()
    ids = {f["id"] for f in fighters}
    ok = ids == set(pop) and len(ids) == len(fighters)
    allowed = {"generated", "unique", "duplicate", "valid", "dq", "cut_capacity"}
    bad_status = [i for i, p in pop.items() if p["status"] not in allowed]
    dup_bad = [i for i, p in pop.items() if p["status"] == "duplicate" and p.get("duplicate_of") not in ids]
    ck.add(
        "population_counts",
        ok and not bad_status and not dup_bad,
        "%d petarung; status tidak dikenal: %d; rujukan duplikat rusak: %d" % (len(ids), len(bad_status), len(dup_bad)),
    )


def _report(run, ck):
    rj = run.load("report.json")
    md_path = run.path("report.md")
    if rj is None or not os.path.exists(md_path):
        ck.add("report", False, "laporan belum ada")
        return
    st = run.state
    with open(md_path, "r", encoding="utf-8") as fh:
        md = fh.read()
    formula = C.WINNER_FORMULA.get(run.cfg["language"], C.WINNER_FORMULA["id"])
    ok = (
        rj.get("champion", {}).get("id") == st.get("champion")
        and (rj.get("winner") or {}).get("id") == st.get("winner")
        and formula in md
    )
    ck.add("report", ok, "laporan konsisten dengan state dan memuat formula pemenang" if ok else "laporan TIDAK konsisten")


def digest(run):
    parts = []
    for name in ["fighters.jsonl", "population.json", "seeding.json", "map.json", "dossiers.json"]:
        parts.append((name, run.file_hash(name)))
    rdir = run.path("rounds")
    if os.path.isdir(rdir):
        for f in sorted(os.listdir(rdir)):
            parts.append(("rounds/" + f, sha256_file(os.path.join(rdir, f))))
    fs = run.state.get("falsification")
    parts.append(("falsification", sha256_text(canonical_json(fs)) if fs else None))
    parts.append(("winner", run.state.get("winner")))
    return sha256_text(canonical_json(parts))


def verify(run, include_report=True):
    ck = Checker()
    rows = _ledger(run, ck)
    _packet_outputs(run, ck, rows)
    _population(run, ck)
    if _locked(run, ck, rows):
        seeding = _seeding(run, ck)
        last = _rounds(run, ck, rows, seeding)
        _champion(run, ck, last)
        _falsification(run, ck)
    if include_report and run.state["phase"] in ("report", "done"):
        _report(run, ck)
    return {
        "ok": all(c["ok"] for c in ck.checks),
        "checked_at": now_iso(),
        "checks": ck.checks,
        "digest": digest(run),
    }
