"""Laporan akhir (report.md + report.json)."""

from collections import Counter, OrderedDict

from . import config as C
from . import packets as P
from .phases import STAGE_NAME
from .util import now_iso

T = {
    "id": {
        "title": "Laporan Argument Battle Royale",
        "disclaimer_head": "Cara membaca hasil ini",
        "disclaimer": (
            "Hasil turnamen ini **bukan** klaim kebenaran mutlak. Kemenangan menunjukkan ketahanan relatif sebuah "
            "argumen terhadap rubrik, protokol, dan populasi lawan dalam simulasi ini — bukan kebenaran metafisik. "
            "Argumen lain yang tidak pernah dihasilkan, rubrik lain, atau bukti baru dapat mengubah hasil."
        ),
        "summary": "Ringkasan eksekutif",
        "winner": "Pemenang tahan-uji",
        "champion": "Juara bracket",
        "runner_up": "Runner-up",
        "no_survivor": (
            "Tidak ada kandidat yang lolos uji falsifikasi. Simulasi ini **tidak** menghasilkan pemenang tahan-uji; "
            "sikap epistemik yang paling dapat dipertanggungjawabkan berdasarkan simulasi ini adalah penangguhan penilaian."
        ),
        "params": "Parameter run",
        "map": "Peta ruang argumen",
        "population": "Statistik populasi",
        "seeding": "Seeding (16 teratas)",
        "journey": "Perjalanan bracket",
        "stance_survival": "Ketahanan posisi per babak",
        "final4": "Final 4",
        "sf_final": "Semifinal & Final",
        "winner_arg": "Argumen pemenang",
        "falsification": "Uji falsifikasi",
        "ranking": "Peringkat akhir",
        "dynamics": "Dinamika turnamen",
        "limits": "Keterbatasan & bias yang diketahui",
        "integrity": "Integritas hasil",
        "repro": "Reproduksi",
    },
    "en": {
        "title": "Argument Battle Royale Report",
        "disclaimer_head": "How to read this result",
        "disclaimer": (
            "This tournament result is **not** a claim of absolute truth. Winning shows an argument's relative "
            "resistance to the rubric, protocol, and opponent population of this simulation — not metaphysical truth. "
            "Arguments never generated, a different rubric, or new evidence could change the outcome."
        ),
        "summary": "Executive summary",
        "winner": "Test-surviving winner",
        "champion": "Bracket champion",
        "runner_up": "Runner-up",
        "no_survivor": (
            "No candidate survived the falsification test. This simulation produced **no** test-surviving winner; "
            "the most defensible epistemic stance based on it is suspension of judgment."
        ),
        "params": "Run parameters",
        "map": "Argument-space map",
        "population": "Population statistics",
        "seeding": "Seeding (top 16)",
        "journey": "Bracket journey",
        "stance_survival": "Stance survival by round",
        "final4": "Final 4",
        "sf_final": "Semifinals & Final",
        "winner_arg": "Winning argument",
        "falsification": "Falsification test",
        "ranking": "Final ranking",
        "dynamics": "Tournament dynamics",
        "limits": "Known limitations & biases",
        "integrity": "Result integrity",
        "repro": "Reproduction",
    },
}

LIMITS_ID = [
    "**LLM sebagai juri.** Semua penilaian dibuat oleh model bahasa. Bias model (mis. terhadap argumen yang fasih, panjang, atau sesuai konsensus populer) dapat memengaruhi hasil meskipun ada pengacakan urutan, anonimisasi, dan panel multi-lensa.",
    "**Populasi tertutup.** Pemenang hanya lebih tahan daripada petarung yang *dihasilkan* dalam run ini. Argumen yang tidak terpikirkan oleh generator tidak ikut bertanding.",
    "**Generator dan juri berasal dari keluarga model yang sama.** Kesalahan sistematis dapat berkorelasi antar-tahap.",
    "**Rubrik adalah pilihan normatif.** Bobot kriteria (lihat bagian Parameter run) mencerminkan nilai-nilai filsafat analitik dan filsafat sains; rubrik lain dapat menghasilkan pemenang lain.",
    "**Eliminasi tunggal bersifat path-dependent.** Satu kekalahan mengakhiri perjalanan argumen; argumen kuat dapat tersingkir lebih awal oleh lawan yang lebih kuat. Seeding berbasis scouting mengurangi, bukan menghapus, efek ini.",
    "**Bukti empiris** dinilai dengan pengetahuan model (mode `internal`) atau pencarian web terbatas; klaim empiris kunci layak diverifikasi secara independen.",
]
LIMITS_EN = [
    "**LLM as judge.** All judgments are made by a language model. Model biases (e.g., toward fluent, long, or consensus-aligned arguments) may affect results despite order randomization, anonymization, and multi-lens panels.",
    "**Closed population.** The winner is only more resistant than the fighters *generated* in this run.",
    "**Generator and judges share a model family.** Systematic errors may correlate across stages.",
    "**The rubric is a normative choice.** Criterion weights (see Run parameters) reflect analytic-philosophy and philosophy-of-science values.",
    "**Single elimination is path-dependent.** Score-based seeding reduces but does not remove this effect.",
    "**Empirical evidence** is assessed with model knowledge (`internal`) or limited web search; key empirical claims deserve independent verification.",
]


def _esc(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def _xy(j, m):
    """Pemetaan label X/Y yang dilihat juri ini, agar kutipan alasannya dapat dibaca."""
    pres = j.get("presentation") or {"X": "a", "Y": "b"}
    return "X = %s, Y = %s" % (m[pres["X"]], m[pres["Y"]])


def _mermaid_label(f, fid):
    t = f["title"].replace('"', "'").replace("[", "(").replace("]", ")")
    return "%s: %s" % (fid, t[:48] + ("…" if len(t) > 48 else ""))


def write_report(run, engine, pre_integrity):
    cfg = run.cfg
    lang = cfg["language"] if cfg["language"] in T else "id"
    L = T[lang]
    st = run.state
    fighters = run.load_fighters()
    pop = run.load_population()
    map_obj = run.load("map.json")
    seeding = run.load("seeding.json")
    dossiers = run.load("dossiers.json", {})
    seeds = seeding["seeds"]
    stance_label = {s["id"]: s["label"] for s in map_obj["stances"]}
    fw_label = {k["id"]: k["label"] for k in map_obj["frameworks"]}

    rounds = []
    r = 1
    while run.load_round(r):
        rounds.append(run.load_round(r))
        r += 1
    reach = engine.reach()

    champion = st.get("champion")
    runner_up = st.get("runner_up")
    winner = st.get("winner")
    wstatus = st.get("winner_falsification")
    fs = st.get("falsification") or {"queue": [], "results": {}}

    def ftitle(fid):
        return "%s — %s" % (fid, fighters[fid]["title"])

    def stance_of(fid):
        return stance_label.get(fighters[fid]["stance_id"], fighters[fid]["stance_id"])

    out = []
    w = out.append
    w("# %s" % L["title"])
    w("")
    w("**Topik:** %s  " % cfg["topic"])
    w("**Rumusan presisi:** %s  " % map_obj["topic_restated"])
    w("**Dibuat:** %s · **Mode:** `%s` · **Populasi target:** %d · **Seed acak:** %d" % (now_iso(), cfg["mode"], cfg["population"], cfg["random_seed"]))
    w("")
    w("> %s" % C.WINNER_FORMULA[lang])
    w("")
    w("## %s" % L["disclaimer_head"])
    w("")
    w(L["disclaimer"])
    w("")

    # ---------------------------------------------------------- summary
    w("## %s" % L["summary"])
    w("")
    if winner:
        f = fighters[winner]
        w("### 🏆 %s: %s" % (L["winner"], f["title"]))
        w("")
        w("- **Tesis:** %s" % f["thesis"])
        w("- **Posisi:** %s · **Kerangka:** %s" % (stance_of(winner), fw_label.get(f["framework_id"], f["framework_id"])))
        w("- **Status uji falsifikasi:** `%s`" % wstatus)
        if winner != champion:
            w("- **Catatan:** juara bracket (%s) gugur dalam uji falsifikasi; gelar pemenang tahan-uji jatuh ke kandidat berikutnya." % ftitle(champion))
    else:
        w("### %s" % L["winner"])
        w("")
        w(L["no_survivor"])
    w("")
    w("| Peran | Petarung | Posisi | Unggulan |")
    w("|---|---|---|---:|")
    w("| %s | %s | %s | %d |" % (L["champion"], _esc(ftitle(champion)), _esc(stance_of(champion)), seeds[champion]))
    w("| %s | %s | %s | %d |" % (L["runner_up"], _esc(ftitle(runner_up)), _esc(stance_of(runner_up)), seeds[runner_up]))
    sf = next((rd for rd in rounds if rd["stage"] == "semifinal"), None)
    if sf:
        for m in sf["matches"]:
            w("| Semifinalis | %s | %s | %d |" % (_esc(ftitle(m["loser"])), _esc(stance_of(m["loser"])), seeds[m["loser"]]))
    w("")

    # ---------------------------------------------------------- params
    w("## %s" % L["params"])
    w("")
    w("| Parameter | Nilai |")
    w("|---|---|")
    for key in ("mode", "population", "deep_round_threshold", "max_parallel", "random_seed", "evidence_mode", "language", "output_dir"):
        w("| `%s` | %s |" % (key, _esc(cfg.get(key))))
    for key in ("early_method", "deep_panel", "semifinal_panel", "final_panel", "falsification_panel", "gen_batch", "scout_batch", "duel_batch", "dedup_review", "max_refill_rounds"):
        w("| `%s` (profil mode) | %s |" % (key, _esc(cfg.get(key))))
    w("")
    w("**Rubrik & bobot:** " + ", ".join("%s (%d)" % (c["label"][lang], c["weight"]) for c in C.RUBRIC) + ".")
    w("")

    # ---------------------------------------------------------- map
    w("## %s" % L["map"])
    w("")
    w("- **Jenis pertanyaan:** `%s`" % map_obj["question_type"])
    if map_obj.get("presuppositions"):
        w("- **Presuposisi:** " + "; ".join(map_obj["presuppositions"]))
    w("- **Posisi:**")
    for s in map_obj["stances"]:
        w("  - `%s` **%s** — %s" % (s["id"], s["label"], s["description"]))
    w("- **Kerangka:** " + "; ".join("`%s` %s" % (k["id"], k["label"]) for k in map_obj["frameworks"]))
    w("- **Strategi:** " + "; ".join("`%s` %s" % (m["id"], m["label"]) for m in map_obj["strategies"]))
    w("- **Titik krusial:**")
    for c in map_obj["cruxes"]:
        w("  - %s" % c)
    w("")

    # ---------------------------------------------------------- population
    status_counts = Counter(p["status"] for p in pop.values())
    dq_counts = Counter(c for p in pop.values() if p["status"] == "dq" for c in p.get("dq_codes", []))
    dup_methods = Counter(p.get("dedup_method") for p in pop.values() if p["status"] == "duplicate")
    waves = Counter(p["generation_round"] for p in pop.values())
    size = rounds[0]["slots"] if rounds else 0
    byes = sum(1 for m in rounds[0]["matches"] if m["bye"]) if rounds else 0
    w("## %s" % L["population"])
    w("")
    w("| Tahap | Jumlah |")
    w("|---|---:|")
    w("| Petarung dihasilkan | %d |" % len(fighters))
    for g in sorted(waves):
        w("| — gelombang %d%s | %d |" % (g, " (awal)" if g == 0 else " (refill)", waves[g]))
    w("| Duplikat dihapus | %d |" % status_counts.get("duplicate", 0))
    for k, v in sorted(dup_methods.items(), key=lambda kv: str(kv[0])):
        w("| — metode `%s` | %d |" % (k, v))
    w("| Didiskualifikasi (validasi) | %d |" % status_counts.get("dq", 0))
    for k, v in dq_counts.most_common():
        w("| — `%s` | %d |" % (k, v))
    w("| Dipotong kapasitas | %d |" % status_counts.get("cut_capacity", 0))
    w("| **Masuk bracket** | **%d** |" % len(seeds))
    w("| Ukuran bracket / bye | %d / %d |" % (size, byes))
    w("")
    gen_by_stance = Counter(f["stance_id"] for f in fighters.values())
    valid_by_stance = Counter(fighters[i]["stance_id"] for i in seeds)
    w("| Posisi | Dihasilkan | Masuk bracket |")
    w("|---|---:|---:|")
    for s in map_obj["stances"]:
        w("| `%s` %s | %d | %d |" % (s["id"], _esc(s["label"]), gen_by_stance.get(s["id"], 0), valid_by_stance.get(s["id"], 0)))
    w("")

    # ---------------------------------------------------------- seeding
    w("## %s" % L["seeding"])
    w("")
    w("| Unggulan | Petarung | Posisi | Skor scouting | Cacat fatal | Babak terjauh |")
    w("|---:|---|---|---:|---:|---|")
    last_round = len(rounds)
    for fid in seeding["order"][:16]:
        sc = pop[fid]["scout"]
        rch = reach.get(fid, 0)
        rch_label = "Juara" if fid == champion else (rounds[rch - 1]["label"] if 0 < rch <= last_round else "-")
        w("| %d | %s | %s | %.1f | %d | %s |" % (seeds[fid], _esc(ftitle(fid)), _esc(stance_of(fid)), sc["calibrated_total"], len(sc["fatal_flaws"]), rch_label))
    w("")

    # ---------------------------------------------------------- journey
    w("## %s" % L["journey"])
    w("")
    w("| Babak | Tahap | Metode | Panel | Duel | Upset | Inkonsistensi juri |")
    w("|---|---|---|---:|---:|---:|---:|")
    round_stats = []
    for rd in rounds:
        real = [m for m in rd["matches"] if not m["bye"]]
        upsets = sum(1 for m in real if m.get("upset"))
        incons = sum(1 for m in real for j in m.get("judgments", []) if not j.get("consistent", True))
        round_stats.append({"round": rd["round"], "label": rd["label"], "stage": rd["stage"], "method": rd["method"], "panel": rd["panel_size"], "duels": len(real), "upsets": upsets, "inconsistencies": incons})
        w("| %s | %s | `%s` | %d | %d | %d | %d |" % (rd["label"], STAGE_NAME[rd["stage"]], rd["method"], rd["panel_size"], len(real), upsets, incons))
    w("")
    if cfg["early_method"] == "score":
        w("*Mode efficient: babak eliminasi awal diputus dengan skor scouting terkalibrasi (setara dengan pra-seleksi berdasarkan seeding), bukan duel langsung.*")
        w("")

    w("### %s" % L["stance_survival"])
    w("")
    head = "| Posisi | " + " | ".join(rd["label"] for rd in rounds) + " | Juara |"
    w(head)
    w("|---|" + "---:|" * (len(rounds) + 1))
    survival = OrderedDict()
    for s in map_obj["stances"]:
        row = []
        for rd in rounds:
            row.append(sum(1 for m in rd["matches"] for x in (m["a"], m["b"]) if x and fighters[x]["stance_id"] == s["id"]))
        row.append(1 if fighters[champion]["stance_id"] == s["id"] else 0)
        survival[s["id"]] = row
        w("| `%s` %s | %s |" % (s["id"], _esc(s["label"]), " | ".join(str(v) for v in row)))
    w("")

    # ---------------------------------------------------------- mermaid
    tail = [rd for rd in rounds if rd["slots"] <= 8]
    if tail:
        w("```mermaid")
        w("flowchart LR")
        for rd in tail:
            for m in rd["matches"]:
                for x in (m["a"], m["b"]):
                    if x:
                        w('  R%s_%s["%s"]' % (rd["round"], x, _mermaid_label(fighters[x], x)))
        w('  CH["🏆 %s"]' % _mermaid_label(fighters[champion], champion))
        for i, rd in enumerate(tail):
            nxt = tail[i + 1] if i + 1 < len(tail) else None
            for m in rd["matches"]:
                target = ("R%s_%s" % (nxt["round"], m["winner"])) if nxt else "CH"
                w("  R%s_%s ==> %s" % (rd["round"], m["winner"], target))
        w("```")
        w("")

    # ---------------------------------------------------------- final 4
    w("## %s" % L["final4"])
    w("")
    for fid, d in dossiers.items():
        w("### %s" % ftitle(fid))
        w("")
        w("- **Posisi:** %s · **Unggulan:** %d" % (stance_of(fid), seeds[fid]))
        w("- **Tesis:** %s" % fighters[fid]["thesis"])
        if d:
            w("- **Inti keras:** " + "; ".join(d["hard_core"]))
            crit = [o for o in d["strongest_objections"] if o["severity"] in ("high", "critical")]
            if crit:
                w("- **Keberatan berat:**")
                for o in crit:
                    w("  - [%s/%s] %s" % (o["severity"], o["status"], o["objection"]))
            w("- **Penilaian penguji:** %s" % d["assessment"])
        else:
            w("- *(dosir tidak tersedia)*")
        w("")

    # ---------------------------------------------------------- SF & final
    w("## %s" % L["sf_final"])
    w("")
    for rd in rounds:
        if rd["stage"] not in ("semifinal", "final"):
            continue
        for m in rd["matches"]:
            votes = m.get("votes") or {}
            w("### %s `%s`: %s vs %s" % (rd["label"], m["match_id"], m["a"], m["b"]))
            w("")
            w("- **Pemenang:** %s (suara %d–%d, basis `%s`)" % (ftitle(m["winner"]), votes.get(m["winner_side"], 0), votes.get("b" if m["winner_side"] == "a" else "a", 0), m["basis"]))
            w("")
            w("| Juri | Lensa | Total %s | Total %s | Pilihan (aturan) | Faktor penentu |" % (m["a"], m["b"]))
            w("|---|---|---:|---:|---|---|")
            for j in m.get("judgments", []):
                w("| %s | %s | %.1f | %.1f | %s | %s |" % (j["judge"], _esc(j["lens"]), j["totals"]["a"], j["totals"]["b"], m[j["rule_winner"]], _esc(j.get("decisive_factor", ""))))
            w("")
            dissent = [j for j in m.get("judgments", []) if j["rule_winner"] != m["winner_side"]]
            for j in m.get("judgments", []):
                if j["rule_winner"] == m["winner_side"]:
                    w("> **Alasan mayoritas (%s; %s):** %s" % (j["judge"], _xy(j, m), j["rationale"]))
                    w("")
                    break
            for j in dissent:
                w("> **Dissent (%s; %s):** %s" % (j["judge"], _xy(j, m), j["rationale"]))
                w("")

    # ---------------------------------------------------------- winner arg
    target = winner or champion
    w("## %s" % L["winner_arg"])
    w("")
    w(P.fighter_md(fighters[target], target))
    w("")
    d = dossiers.get(target)
    if d:
        w("**Bentuk baku (dosir):**")
        w("")
        for s in d["standard_form"]:
            w("1. %s" % s)
        w("")
        w("**Kerangka formal:** %s" % d["formal_skeleton"])
        w("")

    # ---------------------------------------------------------- falsification
    w("## %s" % L["falsification"])
    w("")
    w("Aturan agregasi: *konservatif-mayoritas* (verdict terberat yang didukung oleh ≥ separuh penguji). Antrean kandidat: " + ", ".join(fs["queue"]) + ".")
    w("")
    fals_json = []
    for idx, cand in enumerate(fs["queue"]):
        res = fs["results"].get(cand)
        if not res:
            continue
        w("### Kandidat %d: %s → `%s`" % (idx + 1, ftitle(cand), res["aggregate"]))
        w("")
        entry = {"fighter_id": cand, "aggregate": res["aggregate"], "testers": []}
        for rep in res["verdicts"]:
            o = run.packet_output(rep["packet_id"])
            w("**Penguji %s — `%s`** (keyakinan residual %.2f; imunisasi terdeteksi: %s)" % (rep["tester"], o["verdict"], o["residual_confidence"], "ya" if o["immunization_detected"] else "tidak"))
            w("")
            w("| Uji | Jenis | Target | Hasil | Deskripsi |")
            w("|---|---|---|---|---|")
            core = {c["id"]: c["core"] for c in o["commitments"]}
            for t in o["tests"]:
                w("| %s | %s | %s%s | **%s** | %s |" % (t["id"], t["kind"], t["target_commitment"], " (core)" if core.get(t["target_commitment"]) else "", t["result"], _esc(t["description"])))
            w("")
            w(o["summary"])
            w("")
            if o.get("required_qualifications"):
                w("**Kualifikasi yang wajib ditambahkan:**")
                for q in o["required_qualifications"]:
                    w("- %s" % q)
                w("")
            entry["testers"].append({"tester": rep["tester"], "verdict": o["verdict"], "residual_confidence": o["residual_confidence"], "required_qualifications": o.get("required_qualifications", []), "summary": o["summary"]})
        fals_json.append(entry)

    # ---------------------------------------------------------- ranking
    w("## %s" % L["ranking"])
    w("")
    ranking = [(1, champion), (2, runner_up)]
    if sf:
        for m in sf["matches"]:
            ranking.append((3, m["loser"]))
    qf = next((rd for rd in rounds if rd["slots"] == 8), None)
    if qf:
        for m in qf["matches"]:
            if m.get("loser"):
                ranking.append((5, m["loser"]))
    w("| Peringkat | Petarung | Posisi | Unggulan |")
    w("|---:|---|---|---:|")
    for rank, fid in ranking:
        w("| %s | %s | %s | %d |" % ("=%d" % rank if rank >= 3 else rank, _esc(ftitle(fid)), _esc(stance_of(fid)), seeds[fid]))
    w("")

    # ---------------------------------------------------------- dynamics
    flaw_counter = Counter()
    basis_counter = Counter()
    for rd in rounds:
        for m in rd["matches"]:
            if m["bye"]:
                continue
            basis_counter[m["basis"]] += 1
            for j in m.get("judgments", []):
                for side in ("a", "b"):
                    flaw_counter.update(j.get("fatal", {}).get(side, []))
    w("## %s" % L["dynamics"])
    w("")
    w("- **Basis keputusan duel:** " + (", ".join("`%s` %d" % kv for kv in basis_counter.most_common()) or "-"))
    w("- **Cacat fatal yang paling sering dicatat juri:** " + (", ".join("`%s` %d" % kv for kv in flaw_counter.most_common(6)) or "tidak ada"))
    total_upsets = sum(s["upsets"] for s in round_stats)
    w("- **Total upset** (unggulan lebih rendah mengalahkan yang lebih tinggi): %d" % total_upsets)
    if st.get("flags"):
        w("- **Catatan proses (flags):**")
        fc = Counter(f["code"] for f in st["flags"])
        for code, n in fc.most_common():
            w("  - `%s` × %d" % (code, n))
    w("")

    # ---------------------------------------------------------- limits
    w("## %s" % L["limits"])
    w("")
    for item in (LIMITS_ID if lang == "id" else LIMITS_EN):
        w("- %s" % item)
    w("")

    # ---------------------------------------------------------- integrity
    w("## %s" % L["integrity"])
    w("")
    w("Pemeriksaan pra-laporan: **%s** · digest: `%s`" % ("LULUS" if pre_integrity["ok"] else "GAGAL", pre_integrity["digest"]))
    w("")
    for c in pre_integrity["checks"]:
        w("- %s `%s` — %s" % ("✅" if c["ok"] else "❌", c["name"], c["detail"]))
    w("")
    w("Verifikasi lengkap (termasuk konsistensi laporan ini) tersimpan di `integrity.json` dan dapat diulang kapan pun dengan perintah `verify`.")
    w("")

    # ---------------------------------------------------------- repro
    w("## %s" % L["repro"])
    w("")
    w("```bash")
    w('python3 .claude/skills/argument-battle-royale/scripts/abr.py verify --run "%s"' % cfg["output_dir"])
    w("```")
    w("")
    w("Seed acak `%d` menentukan alokasi slot, pengacakan urutan X/Y, pemilihan jangkar kalibrasi, dan pemecah seri. Output LLM tidak deterministik; reproduksi penuh memerlukan output paket yang tersimpan di `packets/`." % cfg["random_seed"])
    w("")

    run_text = "\n".join(out)
    with open(run.path("report.md"), "w", encoding="utf-8") as fh:
        fh.write(run_text)

    def brief(fid):
        if not fid:
            return None
        f = fighters[fid]
        return {"id": fid, "title": f["title"], "thesis": f["thesis"], "stance_id": f["stance_id"], "stance": stance_of(fid), "framework_id": f["framework_id"], "seed": seeds.get(fid)}

    report_json = {
        "topic": cfg["topic"],
        "topic_restated": map_obj["topic_restated"],
        "formula": C.WINNER_FORMULA[lang],
        "generated_at": now_iso(),
        "config": cfg,
        "counts": {
            "generated": len(fighters),
            "status": dict(status_counts),
            "dq_codes": dict(dq_counts),
            "bracket_entrants": len(seeds),
            "bracket_size": size,
            "byes": byes,
        },
        "champion": brief(champion),
        "runner_up": brief(runner_up),
        "semifinalists": [brief(m["loser"]) for m in sf["matches"]] if sf else [],
        "winner": brief(winner),
        "winner_falsification_status": wstatus,
        "falsification": fals_json,
        "rounds": round_stats,
        "stance_survival": survival,
        "flags": st.get("flags", []),
        "integrity_pre_report": {"ok": pre_integrity["ok"], "digest": pre_integrity["digest"]},
    }
    run.save("report.json", report_json)
    return report_json
