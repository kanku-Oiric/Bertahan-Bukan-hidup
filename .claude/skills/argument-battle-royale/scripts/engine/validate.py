"""Validator output paket. Setiap validator mengembalikan daftar pesan galat.

Validator sengaja ditulis tanpa dependensi (tanpa jsonschema) agar skill
berjalan di lingkungan Python standar mana pun. Pesan galat ditulis agar
dapat langsung dipakai worker untuk memperbaiki output-nya.
"""

from . import config as C
from .util import word_count


class Errors(list):
    def add(self, path, msg):
        self.append("%s: %s" % (path, msg))


def _is_str(v, min_len=1):
    return isinstance(v, str) and len(v.strip()) >= min_len


def _req_str(obj, key, path, errs, min_len=1):
    v = obj.get(key) if isinstance(obj, dict) else None
    if not _is_str(v, min_len):
        errs.add("%s.%s" % (path, key), "wajib string minimal %d karakter" % min_len)
        return None
    return v


def _req_list(obj, key, path, errs, min_n=0, max_n=None):
    v = obj.get(key) if isinstance(obj, dict) else None
    if not isinstance(v, list):
        errs.add("%s.%s" % (path, key), "wajib berupa list")
        return []
    if len(v) < min_n:
        errs.add("%s.%s" % (path, key), "minimal %d item (ada %d)" % (min_n, len(v)))
    if max_n is not None and len(v) > max_n:
        errs.add("%s.%s" % (path, key), "maksimal %d item (ada %d)" % (max_n, len(v)))
    return v


def _req_enum(obj, key, allowed, path, errs):
    v = obj.get(key) if isinstance(obj, dict) else None
    if v not in allowed:
        errs.add("%s.%s" % (path, key), "harus salah satu dari %s (didapat %r)" % (allowed, v))
        return None
    return v


def _scores(obj, key, path, errs):
    v = obj.get(key) if isinstance(obj, dict) else None
    if not isinstance(v, list) or len(v) != len(C.RUBRIC_KEYS):
        errs.add("%s.%s" % (path, key), "wajib list %d angka (urutan: %s)" % (len(C.RUBRIC_KEYS), ", ".join(C.RUBRIC_KEYS)))
        return None
    for i, s in enumerate(v):
        if isinstance(s, bool) or not isinstance(s, (int, float)) or s < 0 or s > 10:
            errs.add("%s.%s[%d]" % (path, key, i), "skor harus angka 0-10")
            return None
    return v


def _flaws(obj, key, path, errs):
    v = obj.get(key, [])
    if not isinstance(v, list):
        errs.add("%s.%s" % (path, key), "wajib list kode cacat fatal (boleh kosong)")
        return []
    for code in v:
        if code not in C.FATAL_FLAWS:
            errs.add("%s.%s" % (path, key), "kode tidak dikenal %r; pilihan: %s" % (code, ", ".join(C.FATAL_FLAWS)))
    return v


def _envelope(output, record, errs):
    if not isinstance(output, dict):
        errs.add("$", "output harus objek JSON")
        return False
    if output.get("packet_id") != record["id"]:
        errs.add("$.packet_id", "harus %r" % record["id"])
    if output.get("input_hash") != record["input_hash"]:
        errs.add("$.input_hash", "harus %r (salin persis dari paket)" % record["input_hash"])
    return True


def _evidence(obj, path, errs):
    ev = obj.get("evidence", [])
    if not isinstance(ev, list):
        errs.add(path + ".evidence", "harus list")
        return
    for i, e in enumerate(ev):
        if not isinstance(e, dict) or not _is_str(e.get("claim")):
            errs.add("%s.evidence[%d]" % (path, i), "setiap bukti wajib punya 'claim' (dan opsional 'source', 'note')")


# ---------------------------------------------------------------- fighter
def validate_fighter_body(f, path, errs):
    _req_str(f, "title", path, errs, 5)
    _req_str(f, "thesis", path, errs, 20)
    defs = _req_list(f, "definitions", path, errs, 1, 8)
    for i, d in enumerate(defs):
        p = "%s.definitions[%d]" % (path, i)
        if not isinstance(d, dict):
            errs.add(p, "harus objek {term, definition}")
            continue
        _req_str(d, "term", p, errs)
        _req_str(d, "definition", p, errs, 10)
    prem = _req_list(f, "premises", path, errs, 2, 7)
    seen = set()
    for i, pr in enumerate(prem):
        p = "%s.premises[%d]" % (path, i)
        if not isinstance(pr, dict):
            errs.add(p, "harus objek {id, text, type, support}")
            continue
        pid = _req_str(pr, "id", p, errs)
        if pid in seen:
            errs.add(p + ".id", "id premis duplikat")
        seen.add(pid)
        _req_str(pr, "text", p, errs, 15)
        _req_enum(pr, "type", C.PREMISE_TYPES, p, errs)
        _req_str(pr, "support", p, errs, 5)
    _req_enum(f, "inference_type", C.INFERENCE_TYPES, path, errs)
    _req_str(f, "inference", path, errs, 20)
    _req_str(f, "conclusion", path, errs, 20)
    ec = f.get("empirical_commitments", [])
    if not isinstance(ec, list) or not all(_is_str(x) for x in ec):
        errs.add(path + ".empirical_commitments", "harus list string (boleh kosong)")
    fals = _req_list(f, "falsifiers", path, errs, 1, 6)
    if not all(_is_str(x, 10) for x in fals):
        errs.add(path + ".falsifiers", "setiap falsifier minimal 10 karakter")
    _req_str(f, "anticipated_objection", path, errs, 15)
    _req_str(f, "reply", path, errs, 15)
    _req_str(f, "scope", path, errs, 10)
    tr = f.get("term_readings", [])
    if not isinstance(tr, list):
        errs.add(path + ".term_readings", "harus list id bacaan istilah (boleh kosong)")
    words = word_count(fighter_text(f))
    if words > C.MAX_FIGHTER_WORDS:
        errs.add(path, "terlalu panjang (%d kata; maksimal %d)" % (words, C.MAX_FIGHTER_WORDS))


def fighter_text(f):
    parts = [f.get("title", ""), f.get("thesis", "")]
    parts += ["%s: %s" % (d.get("term", ""), d.get("definition", "")) for d in f.get("definitions", []) if isinstance(d, dict)]
    parts += ["%s %s" % (p.get("text", ""), p.get("support", "")) for p in f.get("premises", []) if isinstance(p, dict)]
    parts += [f.get("inference", ""), f.get("conclusion", "")]
    parts += list(f.get("empirical_commitments", []) or []) + list(f.get("falsifiers", []) or [])
    parts += [f.get("anticipated_objection", ""), f.get("reply", ""), f.get("scope", "")]
    return "\n".join(str(p) for p in parts)


# ---------------------------------------------------------------- per type
def v_map(output, record, payload):
    errs = Errors()
    if not _envelope(output, record, errs):
        return errs
    _req_str(output, "topic_restated", "$", errs, 10)
    _req_enum(output, "question_type", C.QUESTION_TYPES, "$", errs)
    _req_list(output, "presuppositions", "$", errs, 0, 10)
    terms = _req_list(output, "key_terms", "$", errs, 1, 6)
    reading_ids = set()
    for i, t in enumerate(terms):
        p = "$.key_terms[%d]" % i
        _req_str(t, "term", p, errs)
        rds = _req_list(t, "readings", p, errs, 1, 6)
        for j, r in enumerate(rds):
            pp = "%s.readings[%d]" % (p, j)
            rid = _req_str(r, "id", pp, errs)
            if rid in reading_ids:
                errs.add(pp + ".id", "id bacaan duplikat (harus unik lintas istilah)")
            reading_ids.add(rid)
            _req_str(r, "label", pp, errs)
            _req_str(r, "definition", pp, errs, 10)
    for key, lo, hi in (("stances", 3, 6), ("frameworks", 3, 12), ("strategies", 3, 8)):
        items = _req_list(output, key, "$", errs, lo, hi)
        ids = set()
        for i, it in enumerate(items):
            p = "$.%s[%d]" % (key, i)
            iid = _req_str(it, "id", p, errs)
            if iid in ids:
                errs.add(p + ".id", "id duplikat")
            ids.add(iid)
            _req_str(it, "label", p, errs)
            _req_str(it, "description", p, errs, 10)
    stance_ids = {s.get("id") for s in output.get("stances", []) if isinstance(s, dict)}
    for i, k in enumerate(output.get("frameworks", []) or []):
        cs = k.get("compatible_stances", None) if isinstance(k, dict) else None
        if cs is not None:
            if not isinstance(cs, list) or not cs or any(s not in stance_ids for s in cs):
                errs.add("$.frameworks[%d].compatible_stances" % i, "harus list id stance yang ada (atau hilangkan field ini)")
    _req_list(output, "cruxes", "$", errs, 2, 12)
    _req_list(output, "evidence_domains", "$", errs, 0, 12)
    return errs


def v_generate(output, record, payload):
    errs = Errors()
    if not _envelope(output, record, errs):
        return errs
    fighters = _req_list(output, "fighters", "$", errs)
    expected = [s["slot_id"] for s in payload["slots"]]
    got = [f.get("slot_id") for f in fighters if isinstance(f, dict)]
    missing = [s for s in expected if s not in got]
    extra = [s for s in got if s not in expected]
    if missing:
        errs.add("$.fighters", "slot belum diisi: %s" % ", ".join(missing))
    if extra:
        errs.add("$.fighters", "slot tidak dikenal: %s" % ", ".join(str(x) for x in extra))
    if len(got) != len(set(got)):
        errs.add("$.fighters", "slot_id duplikat")
    reading_ids = set(payload.get("reading_ids", []))
    for i, f in enumerate(fighters):
        p = "$.fighters[%d]" % i
        if not isinstance(f, dict):
            errs.add(p, "harus objek")
            continue
        validate_fighter_body(f, p, errs)
        for rid in f.get("term_readings", []) or []:
            if reading_ids and rid not in reading_ids:
                errs.add(p + ".term_readings", "id bacaan tidak dikenal: %r" % rid)
    return errs


def v_dedup_review(output, record, payload):
    errs = Errors()
    if not _envelope(output, record, errs):
        return errs
    decisions = _req_list(output, "decisions", "$", errs)
    expected = {p["pair_id"] for p in payload["pairs"]}
    got = set()
    for i, d in enumerate(decisions):
        p = "$.decisions[%d]" % i
        pid = d.get("pair_id") if isinstance(d, dict) else None
        if pid not in expected:
            errs.add(p + ".pair_id", "pair_id tidak dikenal: %r" % pid)
        got.add(pid)
        if not isinstance(d.get("same_argument"), bool):
            errs.add(p + ".same_argument", "wajib boolean")
        _req_str(d, "reason", p, errs, 5)
    if expected - got:
        errs.add("$.decisions", "pasangan belum diputuskan: %s" % ", ".join(sorted(expected - got)))
    return errs


def v_scout(output, record, payload):
    errs = Errors()
    if not _envelope(output, record, errs):
        return errs
    evals = _req_list(output, "evaluations", "$", errs)
    expected = set(payload["fighter_ids"])
    got = set()
    for i, e in enumerate(evals):
        p = "$.evaluations[%d]" % i
        fid = e.get("fighter_id") if isinstance(e, dict) else None
        if fid not in expected:
            errs.add(p + ".fighter_id", "id tidak dikenal: %r" % fid)
            continue
        got.add(fid)
        valid = e.get("valid")
        if not isinstance(valid, bool):
            errs.add(p + ".valid", "wajib boolean")
        dq = e.get("dq_codes", [])
        if not isinstance(dq, list) or any(c not in C.DQ_CODES for c in dq):
            errs.add(p + ".dq_codes", "kode DQ tidak dikenal; pilihan: %s" % ", ".join(C.DQ_CODES))
        elif valid is False and not dq:
            errs.add(p + ".dq_codes", "petarung tidak valid wajib punya minimal satu kode DQ")
        elif valid is True and dq:
            errs.add(p + ".dq_codes", "petarung valid tidak boleh punya kode DQ")
        _scores(e, "scores", p, errs)
        _flaws(e, "fatal_flaws", p, errs)
        _req_str(e, "strongest_point", p, errs, 5)
        _req_str(e, "weakest_point", p, errs, 5)
    if expected - got:
        errs.add("$.evaluations", "belum dinilai: %s" % ", ".join(sorted(expected - got)))
    return errs


def _v_verdicts(output, payload, errs, full):
    verdicts = _req_list(output, "verdicts", "$", errs)
    expected = [m["duel_id"] for m in payload["duels"]]
    got = set()
    for i, v in enumerate(verdicts):
        p = "$.verdicts[%d]" % i
        did = v.get("duel_id") if isinstance(v, dict) else None
        if did not in expected:
            errs.add(p + ".duel_id", "duel_id tidak dikenal: %r" % did)
            continue
        got.add(did)
        _scores(v, "scores_x", p, errs)
        _scores(v, "scores_y", p, errs)
        _flaws(v, "fatal_x", p, errs)
        _flaws(v, "fatal_y", p, errs)
        _req_enum(v, "winner", ["X", "Y"], p, errs)
        _req_str(v, "decisive_factor", p, errs, 5)
        _req_str(v, "rationale", p, errs, 20)
        _req_str(v, "objection_x_to_y", p, errs, 10)
        _req_str(v, "objection_y_to_x", p, errs, 10)
        if full:
            _req_str(v, "steelman_x", p, errs, 20)
            _req_str(v, "steelman_y", p, errs, 20)
            _req_str(v, "reply_quality_x", p, errs, 5)
            _req_str(v, "reply_quality_y", p, errs, 5)
            _req_str(v, "dissent_risk", p, errs, 5)
            conf = v.get("confidence")
            if isinstance(conf, bool) or not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
                errs.add(p + ".confidence", "wajib angka 0-1")
            _evidence(v, p, errs)
    missing = [d for d in expected if d not in got]
    if missing:
        errs.add("$.verdicts", "duel belum diputus: %s" % ", ".join(missing))


def v_duel(output, record, payload):
    errs = Errors()
    if _envelope(output, record, errs):
        _v_verdicts(output, payload, errs, full=False)
    return errs


def v_judge(output, record, payload):
    errs = Errors()
    if _envelope(output, record, errs):
        if output.get("judge_lens") != payload["lens"]["id"]:
            errs.add("$.judge_lens", "harus %r" % payload["lens"]["id"])
        _v_verdicts(output, payload, errs, full=True)
    return errs


def v_dossier(output, record, payload):
    errs = Errors()
    if not _envelope(output, record, errs):
        return errs
    if output.get("fighter_id") != payload["fighter_id"]:
        errs.add("$.fighter_id", "harus %r" % payload["fighter_id"])
    _req_list(output, "standard_form", "$", errs, 3, 12)
    _req_str(output, "formal_skeleton", "$", errs, 10)
    _req_list(output, "hard_core", "$", errs, 1, 6)
    _req_list(output, "protective_belt", "$", errs, 0, 8)
    _req_list(output, "empirical_commitments", "$", errs, 0, 10)
    _req_list(output, "falsifiers", "$", errs, 1, 8)
    objs = _req_list(output, "strongest_objections", "$", errs, 3, 8)
    for i, o in enumerate(objs):
        p = "$.strongest_objections[%d]" % i
        _req_str(o, "objection", p, errs, 10)
        _req_enum(o, "severity", ["low", "medium", "high", "critical"], p, errs)
        _req_enum(o, "status", ["answered", "partially_answered", "unanswered"], p, errs)
    _req_list(output, "vulnerabilities", "$", errs, 1, 8)
    _req_list(output, "strengths", "$", errs, 1, 8)
    _req_str(output, "assessment", "$", errs, 30)
    return errs


def v_debate(output, record, payload):
    errs = Errors()
    if not _envelope(output, record, errs):
        return errs
    if output.get("match_id") != payload["match_id"]:
        errs.add("$.match_id", "harus %r" % payload["match_id"])
    if output.get("exchange") != payload["exchange"]:
        errs.add("$.exchange", "harus %r" % payload["exchange"])
    _req_str(output, "statement", "$", errs, 80)
    pts = _req_list(output, "points", "$", errs, 1, 8)
    for i, pt in enumerate(pts):
        _req_str(pt, "claim", "$.points[%d]" % i, errs, 10)
    for key in ("concessions", "clarifications"):
        v = output.get(key, [])
        if not isinstance(v, list):
            errs.add("$." + key, "harus list (boleh kosong)")
    return errs


def v_falsification(output, record, payload):
    errs = Errors()
    if not _envelope(output, record, errs):
        return errs
    if output.get("fighter_id") != payload["fighter_id"]:
        errs.add("$.fighter_id", "harus %r" % payload["fighter_id"])
    commits = _req_list(output, "commitments", "$", errs, 2, 12)
    cids, core = set(), set()
    for i, c in enumerate(commits):
        p = "$.commitments[%d]" % i
        cid = _req_str(c, "id", p, errs)
        cids.add(cid)
        _req_str(c, "claim", p, errs, 10)
        _req_enum(c, "type", ["empirical", "conceptual", "normative", "metaphysical", "methodological"], p, errs)
        if not isinstance(c.get("core"), bool):
            errs.add(p + ".core", "wajib boolean")
        elif c["core"]:
            core.add(cid)
    if commits and not core:
        errs.add("$.commitments", "minimal satu komitmen harus core=true")
    tests = _req_list(output, "tests", "$", errs, 6, 16)
    kinds = set()
    # core_failed: uji 'failed' pada komitmen core (fatal).
    # nonfatal_bad: 'damaged' di mana pun, atau 'failed' pada komitmen non-core.
    core_failed = nonfatal_bad = 0
    for i, t in enumerate(tests):
        p = "$.tests[%d]" % i
        _req_str(t, "id", p, errs)
        kind = _req_enum(t, "kind", C.FALSIFICATION_TEST_KINDS, p, errs)
        kinds.add(kind)
        tgt = t.get("target_commitment")
        if tgt not in cids:
            errs.add(p + ".target_commitment", "harus id komitmen yang ada")
        _req_str(t, "description", p, errs, 20)
        res = _req_enum(t, "result", ["passed", "damaged", "failed"], p, errs)
        _req_str(t, "reasoning", p, errs, 20)
        if res == "failed" and tgt in core:
            core_failed += 1
        elif res in ("damaged", "failed"):
            nonfatal_bad += 1
    missing = [k for k in C.FALSIFICATION_REQUIRED_KINDS if k not in kinds]
    if missing:
        errs.add("$.tests", "jenis uji wajib belum ada: %s" % ", ".join(missing))
    if not ({"empirical_prediction", "conceptual_stress"} & kinds):
        errs.add("$.tests", "wajib minimal satu uji 'empirical_prediction' atau 'conceptual_stress'")
    if not isinstance(output.get("immunization_detected"), bool):
        errs.add("$.immunization_detected", "wajib boolean")
    verdict = _req_enum(output, "verdict", C.FALSIFICATION_VERDICTS, "$", errs)
    if verdict == "FALSIFIED" and core_failed == 0:
        errs.add("$.verdict", "FALSIFIED mensyaratkan minimal satu uji 'failed' pada komitmen core")
    if verdict in ("SURVIVED", "SURVIVED_WITH_DAMAGE") and core_failed > 0:
        errs.add("$.verdict", "ada uji 'failed' pada komitmen core -> verdict wajib FALSIFIED")
    if verdict == "SURVIVED" and nonfatal_bad > 0:
        errs.add("$.verdict", "ada uji 'damaged'/'failed' -> verdict minimal SURVIVED_WITH_DAMAGE")
    if verdict == "SURVIVED_WITH_DAMAGE" and nonfatal_bad == 0:
        errs.add("$.verdict", "SURVIVED_WITH_DAMAGE mensyaratkan minimal satu uji 'damaged' atau 'failed' non-core")
    rq = output.get("required_qualifications", [])
    if not isinstance(rq, list):
        errs.add("$.required_qualifications", "harus list")
    conf = output.get("residual_confidence")
    if isinstance(conf, bool) or not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
        errs.add("$.residual_confidence", "wajib angka 0-1")
    _req_str(output, "summary", "$", errs, 30)
    _evidence(output, "$", errs)
    return errs


VALIDATORS = {
    "map": v_map,
    "generate": v_generate,
    "dedup_review": v_dedup_review,
    "scout": v_scout,
    "duel": v_duel,
    "judge": v_judge,
    "dossier": v_dossier,
    "debate": v_debate,
    "falsification": v_falsification,
}


def validate_output(ptype, output, record, payload):
    return list(VALIDATORS[ptype](output, record, payload))
