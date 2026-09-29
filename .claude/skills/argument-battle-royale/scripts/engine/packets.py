"""Pembuat paket kerja (work packets).

Setiap paket = satu file `packet.md` mandiri + `meta.json` (payload yang di-hash).
Worker (Claude utama atau subagent) membaca packet.md dan menulis output.json.
"""

import json
import os
import sys

from . import config as C
from .util import rng_for

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DIR = os.path.join(SKILL_DIR, "templates")
SCRIPT_PATH = os.path.join(SKILL_DIR, "scripts", "abr.py")

LANGUAGE_NAMES = {"id": "Bahasa Indonesia", "en": "English", "ms": "Bahasa Melayu", "jv": "Basa Jawa"}
PREMISE_TYPE_LABEL = {
    "empirical": "empiris",
    "conceptual": "konseptual",
    "normative": "normatif",
    "metaphysical": "metafisis",
    "methodological": "metodologis",
}
INFERENCE_LABEL = {
    "deductive": "deduktif",
    "inductive": "induktif",
    "abductive": "abduktif",
    "analogical": "analogis",
    "transcendental": "transendental",
    "pragmatic": "pragmatis",
    "probabilistic": "probabilistik",
}
STAGE_LABEL = {
    "map": "Pemetaan ruang argumen",
    "generate": "Generasi petarung",
    "dedup_review": "Deduplikasi semantik",
    "scout": "Validasi & scouting",
    "duel": "Eliminasi",
    "judge": "Panel juri",
    "dossier": "Final 4 — dosir",
    "debate": "Debat",
    "falsification": "Uji falsifikasi",
}
EXCHANGE_LABEL = {"attack": "Serangan", "defense": "Pembelaan", "closing": "Penutup"}
EXCHANGE_TASK = {
    "attack": "Ajukan keberatan-keberatan terkuat terhadap **argumen lawan** (2–5 butir). Targetkan premis atau inferensi tertentu. Jangan membela argumen Anda dulu.",
    "defense": "Jawab serangan lawan terhadap **argumen saya** (lihat pertukaran sebelumnya). Untuk setiap butir serangan: tunjukkan mengapa ia gagal, atau akui bagian yang benar dan jelaskan mengapa argumen tetap bertahan.",
    "closing": "Pernyataan penutup: berdasarkan seluruh pertukaran, jelaskan mengapa **argumen saya** lebih tahan terhadap rubrik pengujian daripada argumen lawan. Akui kelemahan yang masih tersisa secara jujur.",
}


def _tpl(name):
    with open(os.path.join(TEMPLATE_DIR, name), "r", encoding="utf-8") as fh:
        return fh.read()


def _fill(text, mapping):
    for key, value in mapping.items():
        text = text.replace("{{%s}}" % key, str(value))
    return text


def _check_cmd(run, pid):
    return 'python3 "%s" check --run "%s" --packet %s' % (SCRIPT_PATH, run.dir, pid)


def render(run, ptype, pid_placeholder_title, body_template, mapping, output_example):
    """Merender header + badan paket. PACKET_ID/INPUT_HASH diisi saat registrasi."""
    cfg = run.cfg
    header = _tpl("_header.md")
    body = _tpl(body_template)
    text = header + body
    base = {
        "PACKET_TITLE": pid_placeholder_title,
        "STAGE_LABEL": STAGE_LABEL.get(ptype, ptype),
        "TOPIC": cfg["topic"].replace('"', "'"),
        "LANGUAGE_NAME": LANGUAGE_NAMES.get(cfg["language"], cfg["language"]),
        "OUTPUT_EXAMPLE": json.dumps(output_example, ensure_ascii=False, indent=2),
        "RUBRIC": rubric_block(),
        "EVIDENCE": evidence_block(cfg),
    }
    base.update(mapping)
    return _fill(text, base)


def finalize_prompt(run, pid):
    """Isi placeholder yang bergantung pada id paket (path output, perintah cek)."""
    path = run.packet_prompt_path(pid)
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    text = _fill(text, {"OUTPUT_PATH": run.packet_output_path(pid), "CHECK_CMD": _check_cmd(run, pid)})
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def register(run, ptype, stage_key, payload, title, template, mapping, example, meta=None):
    example = dict({"packet_id": "{{PACKET_ID}}", "input_hash": "{{INPUT_HASH}}"}, **example)
    text = render(run, ptype, title, template, mapping, example)
    pid = run.register_packet(ptype, stage_key, payload, text, meta)
    finalize_prompt(run, pid)
    return pid


# ------------------------------------------------------------------ blocks
def rubric_block():
    flaws = "\n".join("- `%s` — %s" % (k, v) for k, v in C.FATAL_FLAWS.items())
    return _fill(_tpl("_rubric.md"), {"FATAL_FLAWS": flaws, "NEAR_TIE": C.NEAR_TIE})


def evidence_block(cfg):
    name = "_evidence_web.md" if cfg["evidence_mode"] == "web_if_available" else "_evidence_internal.md"
    return _tpl(name)


def topic_context(map_obj):
    if not map_obj:
        return "(peta belum tersedia)"
    lines = ["- **Rumusan presisi:** %s" % map_obj["topic_restated"], "- **Jenis pertanyaan:** %s" % map_obj["question_type"]]
    if map_obj.get("cruxes"):
        lines.append("- **Titik krusial:**")
        lines += ["  - %s" % c for c in map_obj["cruxes"]]
    return "\n".join(lines)


def map_summary(map_obj):
    out = [topic_context(map_obj), "", "**Posisi (stances):**"]
    out += ["- `%s` %s — %s" % (s["id"], s["label"], s["description"]) for s in map_obj["stances"]]
    out += ["", "**Kerangka (frameworks):**"]
    out += ["- `%s` %s — %s" % (k["id"], k["label"], k["description"]) for k in map_obj["frameworks"]]
    out += ["", "**Strategi argumentasi:**"]
    out += ["- `%s` %s — %s" % (m["id"], m["label"], m["description"]) for m in map_obj["strategies"]]
    out += ["", "**Bacaan istilah kunci:**"]
    for t in map_obj["key_terms"]:
        out.append("- *%s*: " % t["term"] + "; ".join("`%s` %s (%s)" % (r["id"], r["label"], r["definition"]) for r in t["readings"]))
    return "\n".join(out)


def fighter_md(f, label):
    lines = ["#### %s — %s" % (label, f["title"]), "", "- **Tesis:** %s" % f["thesis"]]
    lines.append("- **Definisi:** " + "; ".join("*%s*: %s" % (d["term"], d["definition"]) for d in f["definitions"]))
    lines.append("- **Premis:**")
    for p in f["premises"]:
        lines.append("  - **%s** (%s): %s — *dukungan:* %s" % (p["id"], PREMISE_TYPE_LABEL.get(p["type"], p["type"]), p["text"], p["support"]))
    lines.append("- **Inferensi (%s):** %s" % (INFERENCE_LABEL.get(f["inference_type"], f["inference_type"]), f["inference"]))
    lines.append("- **Kesimpulan:** %s" % f["conclusion"])
    if f.get("empirical_commitments"):
        lines.append("- **Komitmen empiris:** " + "; ".join(f["empirical_commitments"]))
    lines.append("- **Falsifier:** " + "; ".join(f["falsifiers"]))
    lines.append("- **Keberatan terkuat yang diantisipasi:** %s" % f["anticipated_objection"])
    lines.append("- **Balasan:** %s" % f["reply"])
    lines.append("- **Cakupan & kualifikasi:** %s" % f["scope"])
    return "\n".join(lines)


def dossier_md(d, label):
    if not d:
        return "*(Dosir %s tidak tersedia.)*" % label
    lines = ["**Dosir %s**" % label, "", "- Bentuk baku:"]
    lines += ["  - %s" % s for s in d["standard_form"]]
    lines.append("- Kerangka formal: %s" % d["formal_skeleton"])
    lines.append("- Inti keras: " + "; ".join(d["hard_core"]))
    if d.get("protective_belt"):
        lines.append("- Sabuk pelindung: " + "; ".join(d["protective_belt"]))
    lines.append("- Falsifier: " + "; ".join(d["falsifiers"]))
    lines.append("- Keberatan terkuat:")
    lines += ["  - [%s/%s] %s" % (o["severity"], o["status"], o["objection"]) for o in d["strongest_objections"]]
    lines.append("- Kerentanan: " + "; ".join(d["vulnerabilities"]))
    lines.append("- Kekuatan: " + "; ".join(d["strengths"]))
    lines.append("- Penilaian penguji: %s" % d["assessment"])
    return "\n".join(lines)


def presentation_for(seed, match_id, judge_id):
    r = rng_for(seed, "present", match_id, judge_id)
    return {"X": "a", "Y": "b"} if r.random() < 0.5 else {"X": "b", "Y": "a"}


def transcript_md(debate, presentation=None, me=None):
    """Render transkrip. `presentation` -> label X/Y untuk juri; `me` -> label saya/lawan untuk pembela."""
    if not debate:
        return "*(Belum ada pertukaran.)*"
    lines = []
    for ex in ("attack", "defense", "closing"):
        if ex not in debate:
            continue
        for side in ("a", "b"):
            entry = debate[ex].get(side)
            if me is not None:
                who = "argumen saya" if side == me else "argumen lawan"
                other = "argumen lawan" if side == me else "argumen saya"
            else:
                who = "X" if presentation["X"] == side else "Y"
                other = "Y" if who == "X" else "X"
            action = {
                "attack": "Serangan terhadap %s" % other,
                "defense": "Pembelaan atas serangan %s" % other,
                "closing": "Penutup",
            }[ex]
            lines.append("**Pembela %s — %s**" % (who, action))
            if not entry:
                lines.append("*(tidak ada pernyataan — paket gagal)*")
                lines.append("")
                continue
            lines.append(entry["statement"])
            for pt in entry.get("points", []):
                lines.append("- %s%s" % (pt.get("claim", ""), (" *(target: %s)*" % pt["target"]) if pt.get("target") else ""))
            if entry.get("concessions"):
                lines.append("- *Konsesi:* " + "; ".join(str(c) for c in entry["concessions"]))
            if entry.get("clarifications"):
                lines.append("- *Klarifikasi:* " + "; ".join(str(c) for c in entry["clarifications"]))
            lines.append("")
    return "\n".join(lines).strip()


# ------------------------------------------------------------ examples
def _scores_example():
    return [6, 5, 6, 5, 4, 5, 6, 7, 6, 5]


def example_fighter(slot_id):
    return {
        "slot_id": slot_id,
        "title": "<judul pendek yang menamai argumen>",
        "thesis": "<satu kalimat: jawaban argumen terhadap topik>",
        "term_readings": ["<id bacaan istilah dari peta, mis. T1a>"],
        "definitions": [{"term": "<istilah>", "definition": "<definisi yang dipakai argumen ini>"}],
        "premises": [
            {"id": "P1", "text": "<premis>", "type": "conceptual", "support": "<mengapa premis layak diterima>"},
            {"id": "P2", "text": "<premis>", "type": "empirical", "support": "<dukungan>"},
        ],
        "inference_type": "deductive",
        "inference": "<bagaimana kesimpulan mengikuti dari P1-P2>",
        "conclusion": "<kesimpulan yang sesuai posisi slot>",
        "empirical_commitments": ["<klaim empiris yang dapat diperiksa>"],
        "falsifiers": ["<apa yang akan menunjukkan argumen ini salah>"],
        "anticipated_objection": "<keberatan terkuat>",
        "reply": "<balasan>",
        "scope": "<batas dan kualifikasi klaim>",
    }


def duel_md(fighters, match, presentation, label):
    x_id = match[presentation["X"]]
    y_id = match[presentation["Y"]]
    return "\n".join(
        [
            "### Duel `%s` %s" % (match["match_id"], label),
            "",
            fighter_md(fighters[x_id], "Argumen X"),
            "",
            fighter_md(fighters[y_id], "Argumen Y"),
            "",
        ]
    )


def verdict_example(duel_id, full):
    v = {
        "duel_id": duel_id,
        "scores_x": _scores_example(),
        "scores_y": [7, 6, 6, 6, 6, 6, 6, 6, 6, 7],
        "fatal_x": [],
        "fatal_y": [],
        "winner": "Y",
        "decisive_factor": "<faktor penentu, satu frasa>",
        "rationale": "<alasan putusan>",
        "objection_x_to_y": "<keberatan terkuat X terhadap Y>",
        "objection_y_to_x": "<keberatan terkuat Y terhadap X>",
    }
    if full:
        v.update(
            {
                "steelman_x": "<rekonstruksi terkuat X>",
                "steelman_y": "<rekonstruksi terkuat Y>",
                "reply_quality_x": "<kemampuan X menjawab keberatan Y>",
                "reply_quality_y": "<kemampuan Y menjawab keberatan X>",
                "confidence": 0.7,
                "dissent_risk": "<apa yang dapat membalik putusan>",
                "evidence": [],
            }
        )
    return v


def python_exe():
    return sys.executable or "python3"
