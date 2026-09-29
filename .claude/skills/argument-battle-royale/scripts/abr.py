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

Animasi (Clawd):
  watch     [--run DIR] [--demo] [--once] [--fps N] [--colors truecolor|256]
                                 Animasi live di terminal Anda sendiri (Ctrl+C untuk keluar).
  frame     [--run DIR] [--style mini|ansi] [--i N] [--scene S]
                                 Cetak satu frame (flipbook chat atau ANSI).
  arena     [--run DIR] [--out FILE] [--demo]
                                 Tulis arena HTML beranimasi (juga diperbarui otomatis oleh next).
  statusline                     Satu baris untuk status line Claude Code (baca JSON dari stdin).
  serve     [--run DIR] [--port 8765] [--host 127.0.0.1]
                                 Tonton arena secara live di browser (http://localhost:8765).

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
FLAGS = {"once", "demo"}
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
            elif body in FLAGS:
                k, v = body, "true"
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


def _latest_run(base=DEFAULT_BASE):
    best = None
    if os.path.isdir(base):
        for name in os.listdir(base):
            run = Run(os.path.join(base, name))
            if run.exists():
                key = run.state.get("updated_at", "")
                if best is None or key > best[0]:
                    best = (key, run)
    return best[1] if best else None


def _pick_run(opts, allow_none=False):
    if "run" in opts:
        return _run_from(opts)
    run = _latest_run(opts.get("base", DEFAULT_BASE))
    if run is None and not allow_none:
        fail("Tidak ada run. Pakai --run DIR, atau --demo untuk pratinjau.")
    return run


def _color_mode(opts):
    mode = opts.get("colors")
    if mode in ("truecolor", "256"):
        return mode
    return "truecolor" if os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit") else "256"


DEMO_INFO = {
    "wizard": ("GENERASI", 2, 18, "Menyihir 1000 petarung"),
    "battle": ("ELIMINASI", 7, 55, "Babak 256 besar (Eliminasi): duel berlangsung"),
    "rocket": ("UJI FALSIFIKASI", 13, 90, "Uji falsifikasi: meluncurkan pengujian terhadap juara"),
    "trophy": ("LAPORAN", 14, 100, "Pemenang tahan-uji diumumkan"),
}


def _demo_info(scene):
    from engine import anim

    stage, idx, pct, cap = DEMO_INFO.get(scene, ("TOPIK", 0, 0, "Menunggu"))
    return {"scene": scene, "stage": stage, "stage_index": idx, "stage_count": len(anim.STAGES),
            "percent": pct, "caption": cap, "round": 0, "key": scene, "done": False}


def cmd_watch(argv):
    import time
    from engine import anim

    opts, _ = parse_kv(argv)
    demo = _bool(opts.get("demo", False))
    once = _bool(opts.get("once", False))
    mode = _color_mode(opts)
    fps = max(1.0, min(20.0, float(opts.get("fps", anim.FPS))))
    run_dir = None if demo else _pick_run(opts).dir
    order = ["wizard", "battle", "rocket", "trophy"]
    info, topic, polled, i, t0 = None, "", 0.0, 0, time.time()
    if not once:
        sys.stdout.write("\x1b[?25l\x1b[2J")
    try:
        while True:
            now = time.time()
            if demo:
                scene = order[int((now - t0) // 4) % len(order)]
                info, topic = _demo_info(scene), "Pratinjau animasi Clawd"
            elif info is None or now - polled > 1.0:
                run = Run(run_dir)
                info, topic, polled = anim.status_info(run), run.state["config"]["topic"], now
            frames = anim.frames(info["scene"])
            art = anim.ansi(anim.rasterize(frames[i % len(frames)]), mode)
            orange = anim._fg(anim.PALETTE["O"], mode)
            text = [
                "",
                "  %sARGUMENT BATTLE ROYALE%s · %s" % (orange, anim.RESET, topic[:70]),
                "  %s" % info["caption"][:90],
                "  %s %3d%%  tahap %d/%d %s" % (anim.bar(info["percent"], 30), info["percent"], info["stage_index"] + 1, info["stage_count"], info["stage"]),
                "  " + " ".join(("■" if (k < info["stage_index"] or info.get("done")) else "▣" if k == info["stage_index"] else "□") for k in range(info["stage_count"])),
            ]
            if once:
                print("\n".join(art + text))
                return
            text.append("  Ctrl+C untuk keluar")
            sys.stdout.write("\x1b[H" + "\n".join(line + "\x1b[K" for line in art + text) + "\x1b[J")
            sys.stdout.flush()
            i += 1
            time.sleep(1.0 / fps)
    except KeyboardInterrupt:
        pass
    finally:
        if not once:
            sys.stdout.write(anim.RESET + "\x1b[?25h\n")


def cmd_frame(argv):
    from engine import anim

    opts, _ = parse_kv(argv)
    scene = opts.get("scene")
    if scene and scene not in anim.SCENES:
        fail("Adegan tidak dikenal: %s. Pilihan: %s" % (scene, ", ".join(anim.SCENES)))
    run = None if scene else _pick_run(opts)
    info = _demo_info(scene) if scene else anim.status_info(run)
    i = _int("i", opts.get("i", 0), 0)
    if opts.get("style", "mini") == "ansi":
        frames = anim.frames(info["scene"])
        print("\n".join(anim.ansi(anim.rasterize(frames[i % len(frames)]), _color_mode(opts))))
    else:
        print(anim.mini(info, i))


def cmd_arena(argv):
    from engine import arena

    opts, _ = parse_kv(argv)
    if _bool(opts.get("demo", False)):
        path = arena.write_demo(os.path.abspath(opts.get("out", "arena-demo.html")))
    else:
        run = _pick_run(opts)
        path = arena.write(run, os.path.abspath(opts["out"]) if "out" in opts else None)
    emit({"arena": path})


def cmd_serve(argv):
    import http.server
    import socketserver
    from engine import arena

    opts, _ = parse_kv(argv)
    run_dir = _pick_run(opts).dir
    host = opts.get("host", "127.0.0.1")
    port = _int("port", opts.get("port", 8765), 0, 65535)

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?", 1)[0]
            try:
                summary = arena.run_summary(Run(run_dir))
                if path in ("/", "/index.html", "/arena.html"):
                    body, ctype = arena.render(summary).encode("utf-8"), "text/html; charset=utf-8"
                elif path == "/arena-data.json":
                    body = json.dumps({"run": summary}, ensure_ascii=False).encode("utf-8")
                    ctype = "application/json; charset=utf-8"
                else:
                    self.send_error(404)
                    return
            except Exception as exc:  # state sedang ditulis; penonton akan mencoba lagi
                self.send_error(503, str(exc)[:200])
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    socketserver.ThreadingTCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.daemon_threads = True
    with socketserver.ThreadingTCPServer((host, port), Handler) as srv:
        shown = "localhost" if host in ("0.0.0.0", "127.0.0.1") else host
        print(json.dumps({"serve": "http://%s:%d/" % (shown, srv.server_address[1]), "run_dir": run_dir}), flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass


def cmd_statusline(argv):
    import datetime as dt
    from engine import anim

    data = {}
    if not sys.stdin.isatty():
        try:
            data = json.loads(sys.stdin.read() or "{}")
        except ValueError:
            data = {}
    base = (data.get("workspace") or {}).get("current_dir") or data.get("cwd") or os.getcwd()
    mode = "truecolor" if os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit") else "256"
    run = _latest_run(os.path.join(base, DEFAULT_BASE))
    if run is not None:
        st = run.state
        try:
            age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(st["updated_at"])).total_seconds()
        except (KeyError, ValueError):
            age = 0
        if st["phase"] != "done" or age < 900:
            print(anim.statusline(anim.status_info(run), mode))
            return
    model = (data.get("model") or {}).get("display_name", "")
    print("%s▐▛███▜▌%s %s · %s" % (anim._fg(anim.PALETTE["O"], mode), anim.RESET, model or "Claude", os.path.basename(base.rstrip("/")) or base))


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
    "watch": cmd_watch,
    "frame": cmd_frame,
    "arena": cmd_arena,
    "statusline": cmd_statusline,
    "serve": cmd_serve,
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
