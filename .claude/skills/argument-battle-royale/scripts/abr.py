#!/usr/bin/env python3
"""Argument Battle Royale — engine CLI (hanya pustaka standar Python 3.8+).

Perintah:
  init <topik> [key=value ...]   Buat run baru (atau lanjutkan run yang ada, resume=true).
  next      --run DIR            Serap output, jalankan langkah deterministik, tampilkan paket pending.
  status    --run DIR            Ringkasan progres yang mudah dibaca.
  check     --run DIR --packet ID   Validasi output.json sebuah paket (dipakai worker).
  abandon   --run DIR --packet ID [--reason TEKS]   Tinggalkan paket (engine memakai fallback).
  retry     --run DIR --packet ID   Ulangi paket yang ditinggalkan saat run terhenti (blocked).
  verify    --run DIR            Verifikasi integritas penuh; exit code 0 bila lulus.
  report    --run DIR            Bangun ulang laporan untuk run yang sudah selesai.
  show      --run DIR --fighter ID  Tampilkan satu petarung.
  list-runs [--base DIR]         Daftar run yang ada.

Parameter init (semua opsional kecuali topik):
  mode=full|balanced|efficient  population=1000  deep_round_threshold=N  max_parallel=N
  random_seed=N  evidence_mode=internal|web_if_available  language=id  output_dir=PATH
  resume=true|false
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import config as C  # noqa: E402
from engine.phases import Engine, check_packet  # noqa: E402
from engine.store import Run  # noqa: E402
from engine.util import default_seed, sha256_text, slugify  # noqa: E402

DEFAULT_BASE = "argument-battle-royale-runs"
INIT_KEYS = [
    "topic",
    "mode",
    "population",
    "deep_round_threshold",
    "max_parallel",
    "random_seed",
    "evidence_mode",
    "language",
    "output_dir",
    "resume",
]


def emit(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def fail(msg, code=2):
    emit({"error": msg})
    sys.exit(code)


def parse_kv(argv):
    """Menerima `--key value`, `--key=value`, dan `key=value`; sisanya = kata topik."""
    opts, words = {}, []
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok.startswith("--"):
            body = tok[2:].replace("-", "_")
            if "=" in body:
                k, v = body.split("=", 1)
            else:
                k = body
                if i + 1 >= len(argv):
                    fail("Nilai untuk --%s tidak ada." % k)
                v = argv[i + 1]
                i += 1
            opts[k] = v
        elif "=" in tok and tok.split("=", 1)[0].replace("-", "_") in INIT_KEYS:
            k, v = tok.split("=", 1)
            opts[k.replace("-", "_")] = v
        else:
            words.append(tok)
        i += 1
    return opts, words


def _bool(v):
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "ya", "y", "on"):
        return True
    if s in ("0", "false", "no", "tidak", "n", "off"):
        return False
    fail("Nilai boolean tidak dikenal: %r" % v)


def _int(name, v, lo=None, hi=None):
    try:
        n = int(str(v).strip())
    except ValueError:
        fail("%s harus bilangan bulat (didapat %r)" % (name, v))
    if lo is not None and n < lo:
        fail("%s minimal %d" % (name, lo))
    if hi is not None and n > hi:
        fail("%s maksimal %d" % (name, hi))
    return n


def resolve_config(opts, words):
    unknown = [k for k in opts if k not in INIT_KEYS]
    if unknown:
        fail("Parameter tidak dikenal: %s. Yang didukung: %s" % (", ".join(unknown), ", ".join(INIT_KEYS)))
    topic = (opts.get("topic") or " ".join(words)).strip().strip('"').strip("'").strip()
    if len(topic) < 5:
        fail("Topik wajib diisi (minimal 5 karakter). Contoh: abr.py init \"Apakah AI memahami bahasa?\"")
    mode = opts.get("mode", C.DEFAULTS["mode"]).strip().lower()
    if mode not in C.MODES:
        fail("mode harus salah satu dari: %s" % ", ".join(C.MODES))
    profile = C.MODES[mode]
    evidence = opts.get("evidence_mode", C.DEFAULTS["evidence_mode"]).strip().lower()
    if evidence not in ("internal", "web_if_available"):
        fail("evidence_mode harus 'internal' atau 'web_if_available'")
    language = opts.get("language", C.DEFAULTS["language"]).strip().lower()
    cfg = {
        "topic": topic,
        "mode": mode,
        "population": _int("population", opts.get("population", C.DEFAULTS["population"]), C.POPULATION_MIN, C.POPULATION_MAX),
        "deep_round_threshold": _int("deep_round_threshold", opts.get("deep_round_threshold", profile["deep_round_threshold"]), 4, 4096),
        "max_parallel": _int("max_parallel", opts.get("max_parallel", C.DEFAULTS["max_parallel"]), 1, 64),
        "random_seed": _int("random_seed", opts["random_seed"], 0) if "random_seed" in opts else default_seed(topic),
        "evidence_mode": evidence,
        "language": language,
    }
    for key in ("gen_batch", "scout_batch", "early_method", "duel_batch", "deep_panel", "deep_batch",
                "semifinal_panel", "final_panel", "falsification_panel", "dedup_review", "max_refill_rounds"):
        cfg[key] = profile[key]
    return cfg


def cmd_init(argv):
    opts, words = parse_kv(argv)
    cfg = resolve_config(opts, words)
    resume = _bool(opts.get("resume", C.DEFAULTS["resume"]))
    if opts.get("output_dir"):
        run_dir = os.path.abspath(opts["output_dir"])
    else:
        run_dir = os.path.abspath(os.path.join(DEFAULT_BASE, "%s-%s" % (slugify(cfg["topic"]), sha256_text(cfg["topic"])[:6])))
    run = Run(run_dir)
    if run.exists():
        if resume:
            stored = run.state["config"]
            conflicts = [
                "%s: tersimpan=%r, diminta=%r" % (k, stored.get(k), cfg[k])
                for k in opts
                if k in cfg and k not in ("max_parallel",) and stored.get(k) != cfg[k]
            ]
            if stored["topic"] != cfg["topic"]:
                conflicts.append("topic berbeda")
            if conflicts:
                fail("Run di %s memakai konfigurasi berbeda (%s). Gunakan resume=false untuk run baru atau output_dir lain." % (run_dir, "; ".join(conflicts)))
            if "max_parallel" in opts:
                run.state["config"]["max_parallel"] = cfg["max_parallel"]
                run.save_state()
            emit({"run_dir": run.dir, "created": False, "resumed": True, "phase": run.state["phase"],
                  "next": 'python3 "%s" next --run "%s"' % (os.path.abspath(__file__), run.dir)})
            return
        base, n = run_dir, 2
        while os.path.exists(os.path.join("%s-r%d" % (base, n), "state.json")):
            n += 1
        run_dir = "%s-r%d" % (base, n)
        run = Run(run_dir)
    rel = os.path.relpath(run_dir)
    cfg["output_dir"] = rel if not rel.startswith("..") else run_dir
    run.create(cfg)
    emit({"run_dir": run.dir, "created": True, "resumed": False, "config": cfg,
          "next": 'python3 "%s" next --run "%s"' % (os.path.abspath(__file__), run.dir)})


def _run_from(opts):
    if "run" not in opts:
        fail("--run DIR wajib diisi.")
    run = Run(opts["run"])
    if not run.exists():
        fail("Tidak ada run di %s" % run.dir)
    return run


def cmd_next(argv):
    opts, _ = parse_kv(argv)
    run = _run_from(opts)
    try:
        emit(Engine(run).next())
    except RuntimeError as exc:
        fail(str(exc))


def cmd_status(argv):
    opts, _ = parse_kv(argv)
    run = _run_from(opts)
    eng = Engine(run)
    st = run.state
    pop = run.load_population()
    counts = {}
    for p in pop.values():
        counts[p["status"]] = counts.get(p["status"], 0) + 1
    by_status = {}
    for p in st["packets"].values():
        by_status[p["status"]] = by_status.get(p["status"], 0) + 1
    lines = [
        "Topik     : %s" % st["config"]["topic"],
        "Direktori : %s" % run.dir,
        "Mode      : %s · populasi %d · seed %d" % (st["config"]["mode"], st["config"]["population"], st["config"]["random_seed"]),
        "Progres   : %s" % eng.progress_line(),
        "Paket     : %s" % ", ".join("%s=%d" % kv for kv in sorted(by_status.items())),
        "Petarung  : %s" % (", ".join("%s=%d" % kv for kv in sorted(counts.items())) or "-"),
    ]
    if st.get("champion"):
        lines.append("Juara     : %s" % st["champion"])
    if st["phase"] == "done":
        lines.append("Pemenang  : %s (%s)" % (st.get("winner"), st.get("winner_falsification")))
        lines.append("Laporan   : %s" % run.path("report.md"))
    if st.get("blocked"):
        lines.append("TERHENTI  : %s — %s" % (st["blocked"]["reason"], st["blocked"]["hint"]))
    print("\n".join(lines))


def cmd_check(argv):
    opts, _ = parse_kv(argv)
    run = _run_from(opts)
    if "packet" not in opts:
        fail("--packet ID wajib diisi.")
    errors = check_packet(run, opts["packet"])
    if errors:
        print("TIDAK VALID (%d galat):" % len(errors))
        for e in errors[:40]:
            print("  - " + e)
        sys.exit(1)
    print("OK")


def cmd_abandon(argv):
    opts, _ = parse_kv(argv)
    run = _run_from(opts)
    pid = opts.get("packet")
    with run.lock():
        rec = run.state["packets"].get(pid)
        if not rec or rec["status"] != "pending":
            fail("Paket %s tidak ada atau tidak pending." % pid)
        run.abandon_packet(pid, opts.get("reason", "ditinggalkan oleh orkestrator"))
        run.save_state()
    emit({"abandoned": pid})


def cmd_retry(argv):
    opts, _ = parse_kv(argv)
    run = _run_from(opts)
    pid = opts.get("packet")
    with run.lock():
        st = run.state
        rec = st["packets"].get(pid)
        if not rec or rec["status"] != "abandoned":
            fail("Paket %s tidak ada atau tidak berstatus abandoned." % pid)
        if not st.get("blocked"):
            fail("Retry hanya diizinkan saat run terhenti (blocked); paket lain sudah ditangani fallback.")
        rec.update({"status": "pending", "attempts": 0, "errors": []})
        st["blocked"] = None
        run.log("packet_retry", {"id": pid})
        run.save_state()
    emit({"retry": pid})


def cmd_verify(argv):
    from engine import integrity

    opts, _ = parse_kv(argv)
    run = _run_from(opts)
    res = integrity.verify(run, include_report=True)
    emit(res)
    sys.exit(0 if res["ok"] else 1)


def cmd_report(argv):
    from engine import integrity, report

    opts, _ = parse_kv(argv)
    run = _run_from(opts)
    if run.state["phase"] not in ("report", "done"):
        fail("Laporan hanya dapat dibuat setelah uji falsifikasi selesai (fase sekarang: %s)." % run.state["phase"])
    with run.lock():
        pre = integrity.verify(run, include_report=False)
        report.write_report(run, Engine(run), pre)
        full = integrity.verify(run, include_report=True)
        run.save("integrity.json", full)
        run.log("report_regenerated", {"report_sha256": run.file_hash("report.md"), "integrity_ok": full["ok"], "digest": full["digest"]})
    emit({"report_md": run.path("report.md"), "integrity_ok": full["ok"], "digest": full["digest"]})


def cmd_show(argv):
    from engine import packets as P

    opts, _ = parse_kv(argv)
    run = _run_from(opts)
    fid = opts.get("fighter")
    fighters = run.load_fighters()
    if fid not in fighters:
        fail("Petarung %s tidak ada." % fid)
    pop = run.load_population().get(fid, {})
    print(P.fighter_md(fighters[fid], fid))
    print("")
    print("Status: %s · posisi %s · kerangka %s · strategi %s" % (pop.get("status"), fighters[fid]["stance_id"], fighters[fid]["framework_id"], fighters[fid]["strategy_id"]))
    if pop.get("scout"):
        print("Skor scouting terkalibrasi: %.1f · cacat fatal: %s" % (pop["scout"]["calibrated_total"], pop["scout"]["fatal_flaws"] or "-"))
    if pop.get("seed"):
        print("Unggulan: %d" % pop["seed"])


def cmd_list_runs(argv):
    opts, _ = parse_kv(argv)
    base = opts.get("base", DEFAULT_BASE)
    rows = []
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            run = Run(os.path.join(base, name))
            if run.exists():
                st = run.state
                rows.append({"run_dir": run.dir, "topic": st["config"]["topic"], "phase": st["phase"], "updated_at": st["updated_at"]})
    emit({"base": os.path.abspath(base), "runs": rows})


COMMANDS = {
    "init": cmd_init,
    "next": cmd_next,
    "status": cmd_status,
    "check": cmd_check,
    "abandon": cmd_abandon,
    "retry": cmd_retry,
    "verify": cmd_verify,
    "report": cmd_report,
    "show": cmd_show,
    "list-runs": cmd_list_runs,
}


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return
    cmd = argv[0]
    if cmd not in COMMANDS:
        fail("Perintah tidak dikenal: %s. Pilihan: %s" % (cmd, ", ".join(COMMANDS)))
    COMMANDS[cmd](argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
