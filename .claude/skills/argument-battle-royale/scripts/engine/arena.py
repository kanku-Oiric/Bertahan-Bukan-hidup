"""Arena HTML: tontonan pertarungan argumen yang live.

Engine menghasilkan daftar *acara* (tahap selesai, babak dimulai, duel dengan
"pukulan" setiap juri, uji falsifikasi, pemenang). Halaman arena memutar acara
yang belum pernah ditonton penonton sebagai animasi pixel art: dua Clawd masuk
arena, setiap juri memukul dengan keberatan yang sebenarnya, bar ketahanan
turun sesuai suara juri, yang kalah KO, pemenang maju.

Cara menonton secara live:
  - artifact (Claude Code di aplikasi/web): halaman diterbitkan sekali
    (`abr.py live`), lalu orkestrator menulis arena-live.json ke database
    artifact setiap ada acara baru; halaman berlangganan dokumen itu
  - `abr.py serve --run DIR`  : server lokal; halaman menarik arena-data.json
                                setiap 3 detik tanpa memuat ulang
  - membuka arena.html langsung: halaman memuat ulang sendiri saat senggang
                                dan melanjutkan dari acara terakhir yang ditonton
Setelah run selesai, halaman yang sama menjadi tayangan ulang seluruh turnamen.
"""

import json
import os
import re

from . import anim
from . import config as C
from .util import atomic_write_text, sha256_text

TEMPLATE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "templates", "arena.html")
LIVE_FILE = "arena-live.json"          # dokumen untuk database artifact
ARTIFACT_FILE = "arena-artifact.html"  # halaman tanpa kerangka dokumen, untuk diterbitkan
LIVE_COLLECTION, LIVE_DOC_ID = "arena", "live"
LIVE_LIMIT = 240000     # byte; dokumen database artifact maksimal 256 KiB
FULL_ROUND_MAX = 8      # babak dengan duel sebanyak ini atau kurang diputar seluruhnya
FEATURED_PER_ROUND = 3  # babak besar: hanya duel pilihan yang diputar penuh


def _clip(text, n):
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _rounds(run):
    out, r = [], 1
    while True:
        rd = run.load_round(r)
        if not rd:
            return out
        out.append(rd)
        r += 1


def _votes(m):
    v = m.get("votes")
    if not (m.get("winner") and v and m.get("winner_side")):
        return ""
    other = "b" if m["winner_side"] == "a" else "a"
    return "%d–%d" % (v.get(m["winner_side"], 0), v.get(other, 0))


def _bracket(rounds):
    cols = []
    for slots in (8, 4, 2):
        rd = next((x for x in rounds if x["slots"] == slots), None)
        col = []
        for m in (rd["matches"] if rd else []):
            col.append({"mid": m["match_id"], "a": m["a"], "b": m["b"], "winner": m.get("winner"), "votes": _votes(m)})
        cols.append(col)
    return cols


def _match_event(m, rd):
    hits = []
    for j in m.get("judgments", []):
        by = j["rule_winner"]
        other = "b" if by == "a" else "a"
        pres = j.get("presentation")
        if j.get("judge") == "SCOUT":
            text = "Diputus dengan skor scouting terkalibrasi: %.1f lawan %.1f." % (j["totals"][by], j["totals"][other])
            hits.append({"j": "SKOR", "lens": "Skor scouting", "by": by, "ta": j["totals"]["a"], "tb": j["totals"]["b"], "obj": text, "fx": j.get("basis", ""), "xy": ""})
            continue
        hits.append({
            "j": j["judge"],
            "lens": j.get("lens", ""),
            "by": by,
            "ta": j["totals"]["a"],
            "tb": j["totals"]["b"],
            "obj": _clip((j.get("objections") or {}).get("%s_to_%s" % (by, other), ""), 240),
            "fx": _clip(j.get("decisive_factor", ""), 110),
            "xy": ("X = %s, Y = %s" % (m[pres["X"]], m[pres["Y"]])) if pres else "",
        })
    return {
        "id": "m:" + m["match_id"],
        "t": "match",
        "mid": m["match_id"],
        "r": rd["round"],
        "label": rd["label"],
        "stage": rd["stage"],
        "a": m["a"],
        "b": m["b"],
        "w": m["winner"],
        "votes": _votes(m),
        "basis": m.get("basis", ""),
        "upset": bool(m.get("upset")),
        "hits": hits,
    }


def _featured(matches, seeds):
    def gap(m):
        return abs((m.get("seed_a") or 0) - (m.get("seed_b") or 0))

    def closeness(m):
        js = m.get("judgments", [])
        if not js:
            return 1e9
        return sum(abs(j["totals"]["a"] - j["totals"]["b"]) for j in js) / len(js)

    upsets = sorted((m for m in matches if m.get("upset")), key=lambda m: -gap(m))
    close = sorted((m for m in matches if not m.get("upset")), key=closeness)
    picked = (upsets + close)[:FEATURED_PER_ROUND]
    order = {m["match_id"]: i for i, m in enumerate(matches)}
    return sorted(picked, key=lambda m: order[m["match_id"]])


def events(run):
    st = run.state
    ev = []
    map_obj = run.load("map.json")
    fighters = run.load_fighters()
    pop = run.load_population()
    if map_obj:
        ev.append({"id": "s:map", "t": "stage", "scene": "wizard", "title": "Ruang argumen dipetakan",
                   "text": "%d posisi, %d kerangka, %d strategi argumentasi" % (len(map_obj["stances"]), len(map_obj["frameworks"]), len(map_obj["strategies"]))})
    if st.get("generation_ingested", -1) >= 0 and fighters:
        ev.append({"id": "s:gen%d" % st["generation_ingested"], "t": "stage", "scene": "wizard", "title": "%d petarung dipanggil" % len(fighters),
                   "text": "Setiap posisi mendapat kuota yang sama; turnamen yang menentukan siapa bertahan"})
    if st.get("validated_round", -1) >= 0 and pop:
        cnt = {}
        for p in pop.values():
            cnt[p["status"]] = cnt.get(p["status"], 0) + 1
        ev.append({"id": "s:val%d" % st["validated_round"], "t": "stage", "scene": "wizard", "title": "Validasi dan scouting selesai",
                   "text": "%d valid, %d duplikat dihapus, %d didiskualifikasi" % (cnt.get("valid", 0) + cnt.get("cut_capacity", 0), cnt.get("duplicate", 0), cnt.get("dq", 0))})
    seeding = run.load("seeding.json")
    rounds = _rounds(run)
    if seeding and rounds:
        top = seeding["order"][0]
        ev.append({"id": "s:seed", "t": "stage", "scene": "wizard", "title": "Bracket %d slot siap" % rounds[0]["slots"],
                   "text": "Unggulan 1: %s — %s" % (top, _clip(fighters[top]["title"], 90))})
    dossiers = run.load("dossiers.json")
    for rd in rounds:
        if rd["stage"] == "semifinal" and dossiers:
            ids = [x for m in rd["matches"] for x in (m["a"], m["b"])]
            ev.append({"id": "s:final4", "t": "stage", "scene": "battle", "title": "Final 4",
                       "text": "Dosir disusun untuk %s; semifinal dimulai dengan debat" % ", ".join(ids)})
        if rd.get("status") != "done":
            continue
        real = [m for m in rd["matches"] if not m["bye"]]
        full = len(real) <= FULL_ROUND_MAX
        shown = real if full else _featured(real, seeding["seeds"] if seeding else {})
        ev.append({"id": "r:%d" % rd["round"], "t": "round", "label": rd["label"], "stage": rd["stage"], "n": len(real),
                   "byes": sum(1 for m in rd["matches"] if m["bye"]), "upsets": sum(1 for m in real if m.get("upset")),
                   "full": full, "shown": len(shown), "method": rd["method"], "panel": rd["panel_size"]})
        ev += [_match_event(m, rd) for m in shown]
    fs = st.get("falsification")
    if fs:
        for idx, cand in enumerate(fs["queue"]):
            res = fs["results"].get(cand)
            if not res:
                continue
            testers = []
            for rep in res["verdicts"]:
                out = run.packet_output(rep["packet_id"]) or {}
                testers.append({"t": rep["tester"], "v": rep["verdict"], "s": _clip(out.get("summary", ""), 220)})
            ev.append({"id": "f:%d" % idx, "t": "fals", "fighter": cand, "agg": res["aggregate"], "testers": testers})
    if st["phase"] in ("report", "done"):
        ev.append({"id": "w", "t": "winner", "fighter": st.get("winner"), "status": st.get("winner_falsification")})
    return ev


def _fighter_map(run, ev, bracket):
    fighters = run.load_fighters()
    map_obj = run.load("map.json") or {}
    stance = {s["id"]: s["label"] for s in map_obj.get("stances", [])}
    seeds = (run.load("seeding.json") or {}).get("seeds", {})
    ids = set()
    for e in ev:
        for k in ("a", "b", "w", "fighter"):
            if e.get(k):
                ids.add(e[k])
    for col in bracket:
        for m in col:
            ids.update(x for x in (m["a"], m["b"]) if x)
    st = run.state
    for k in ("champion", "runner_up", "winner"):
        if st.get(k):
            ids.add(st[k])
    out = {}
    for fid in ids:
        f = fighters.get(fid)
        if f:
            out[fid] = {"title": f["title"], "stance": stance.get(f["stance_id"], f["stance_id"]), "seed": seeds.get(fid), "thesis": _clip(f["thesis"], 260)}
    return out


def run_summary(run):
    st = run.state
    cfg = st["config"]
    info = anim.status_info(run)
    map_obj = run.load("map.json") or {}
    seeding = run.load("seeding.json")
    rounds = _rounds(run)
    pk = list(st["packets"].values())
    done_pk = sum(1 for p in pk if p["status"] != "pending")
    size = rounds[0]["slots"] if rounds else 0
    total_rounds = size.bit_length() - 1 if size else 0
    n_fighters = len(run.load_fighters()) if st["phase"] not in ("init", "map") else 0
    stats = [
        ["Petarung dihasilkan", str(n_fighters) if n_fighters else "—"],
        ["Masuk bracket", str(len(seeding["order"])) if seeding else "—"],
        ["Babak", "%d dari %d" % (st["current_round"], total_rounds) if total_rounds else "—"],
        ["Paket kerja selesai", "%d / %d" % (done_pk, len(pk))],
    ]
    ev = events(run)
    bracket = _bracket(rounds)
    lang = cfg.get("language", "id")
    summary = {
        "demo": False,
        "run_id": "%s@%s" % (os.path.basename(run.dir), st.get("created_at", "")),
        "topic": cfg["topic"],
        "restated": map_obj.get("topic_restated", ""),
        "info": info,
        "stages": anim.STAGES,
        "stats": stats,
        "events": ev,
        "fighters": _fighter_map(run, ev, bracket),
        "bracket": bracket,
        "champion": st.get("champion"),
        "winner": st.get("winner"),
        "winner_status": st.get("winner_falsification"),
        "done": st["phase"] == "done",
        "formula": anim.formula(lang),
        "foot": "Mode %s · populasi %d · seed %d · diperbarui %s · %s" % (
            cfg["mode"], cfg["population"], cfg["random_seed"], st.get("updated_at", ""), os.path.basename(run.dir)),
        "updated_at": st.get("updated_at", ""),
    }
    summary["rev"] = sha256_text(json.dumps([info, [e["id"] for e in ev], stats], sort_keys=True, ensure_ascii=False))[:16]
    return summary


def demo_summary():
    """Turnamen kecil fiktif (ditandai contoh) untuk memamerkan semua animasi tanpa run."""
    fighters = {
        "C01": {"title": "Contoh A: kemampuan inferensial sudah cukup", "stance": "Ya", "seed": 1, "thesis": "Argumen contoh untuk pratinjau animasi."},
        "C02": {"title": "Contoh B: tanpa grounding tidak ada makna", "stance": "Tidak untuk saat ini", "seed": 4, "thesis": "Argumen contoh untuk pratinjau animasi."},
        "C03": {"title": "Contoh C: pemahaman datang bertingkat", "stance": "Sebagian", "seed": 2, "thesis": "Argumen contoh untuk pratinjau animasi: pemahaman terdiri atas beberapa dimensi."},
        "C04": {"title": "Contoh D: pertanyaannya sengketa kata", "stance": "Deflasioner", "seed": 3, "thesis": "Argumen contoh untuk pratinjau animasi."},
    }

    def hit(j, lens, by, ta, tb, obj):
        return {"j": j, "lens": lens, "by": by, "ta": ta, "tb": tb, "obj": obj, "fx": "contoh", "xy": ""}

    ev = [
        {"id": "s:map", "t": "stage", "scene": "wizard", "title": "Ruang argumen dipetakan", "text": "Contoh: 4 posisi, 3 kerangka, 3 strategi"},
        {"id": "s:gen0", "t": "stage", "scene": "wizard", "title": "4 petarung dipanggil", "text": "Contoh populasi kecil untuk pratinjau"},
        {"id": "r:1", "t": "round", "label": "Semifinal", "stage": "semifinal", "n": 2, "byes": 0, "upsets": 0, "full": True, "shown": 2, "method": "panel", "panel": 3},
        {"id": "m:C1", "t": "match", "mid": "C1", "r": 1, "label": "Semifinal", "stage": "semifinal", "a": "C01", "b": "C02", "w": "C01", "votes": "1–0", "basis": "rubric_total", "upset": False,
         "hits": [hit("L7", "Generalis mata-segar", "a", 71.5, 62.0, "Contoh keberatan: klaim bahwa makna mustahil tanpa grounding tidak menjelaskan pengetahuan yang dipelajari dari teks saja.")]},
        {"id": "m:C2", "t": "match", "mid": "C2", "r": 1, "label": "Semifinal", "stage": "semifinal", "a": "C03", "b": "C04", "w": "C03", "votes": "2–1", "basis": "majority", "upset": False,
         "hits": [hit("L1", "Logikawan formal", "a", 74.0, 68.5, "Contoh keberatan: jika jawaban per dimensi sudah faktual, pertanyaannya tidak larut."),
                  hit("L2", "Filsuf sains", "b", 69.0, 71.5, "Contoh keberatan: batas 'dimensi' ditarik setelah data dilihat."),
                  hit("L3", "Analis konseptual", "a", 75.5, 70.0, "Contoh keberatan: status konsep klaster tidak berarti tidak ada jawaban.")]},
        {"id": "r:2", "t": "round", "label": "Final", "stage": "final", "n": 1, "byes": 0, "upsets": 0, "full": True, "shown": 1, "method": "panel_debate", "panel": 3},
        {"id": "m:C3", "t": "match", "mid": "C3", "r": 2, "label": "Final", "stage": "final", "a": "C01", "b": "C03", "w": "C03", "votes": "2–1", "basis": "majority", "upset": True,
         "hits": [hit("L1", "Logikawan formal", "a", 73.0, 72.0, "Contoh keberatan: argumen lawan mengakui dimensi fungsional, sisanya hanya soal label."),
                  hit("L2", "Filsuf sains", "b", 70.0, 76.5, "Contoh keberatan: paritas mengabaikan pola kegagalan sistematis."),
                  hit("L3", "Analis konseptual", "b", 69.5, 75.0, "Contoh keberatan: 'sejenis dengan manusia' melampaui definisi fungsional.")]},
        {"id": "f:0", "t": "fals", "fighter": "C03", "agg": "SURVIVED_WITH_DAMAGE",
         "testers": [{"t": "T1", "v": "SURVIVED_WITH_DAMAGE", "s": "Contoh: satu komitmen bantu gugur, inti bertahan."}]},
        {"id": "w", "t": "winner", "fighter": "C03", "status": "SURVIVED_WITH_DAMAGE"},
    ]
    return {
        "demo": True,
        "run_id": "demo",
        "topic": "Pratinjau arena Clawd",
        "restated": "Turnamen contoh berisi empat argumen fiktif untuk memperlihatkan animasi pertarungan.",
        "info": {"scene": "trophy", "stage_index": 14, "stage": anim.STAGES[14], "stage_count": len(anim.STAGES),
                 "percent": 100, "caption": "Contoh selesai", "round": 2, "key": "demo", "done": True},
        "stages": anim.STAGES,
        "stats": [["Petarung dihasilkan", "4 (contoh)"], ["Masuk bracket", "4"], ["Babak", "2 dari 2"], ["Paket kerja selesai", "—"]],
        "events": ev,
        "fighters": fighters,
        "bracket": [[], [{"mid": "C1", "a": "C01", "b": "C02", "winner": "C01", "votes": "1–0"}, {"mid": "C2", "a": "C03", "b": "C04", "winner": "C03", "votes": "2–1"}],
                    [{"mid": "C3", "a": "C01", "b": "C03", "winner": "C03", "votes": "2–1"}]],
        "champion": "C03",
        "winner": "C03",
        "winner_status": "SURVIVED_WITH_DAMAGE",
        "done": True,
        "formula": C.WINNER_FORMULA["id"],
        "foot": "Pratinjau dengan data contoh. Jalankan abr.py arena --run DIR untuk arena sebuah run.",
        "rev": "demo",
    }


def data(summary):
    return {"anim": anim.web_data(), "run": summary}


def render(summary):
    with open(TEMPLATE, "r", encoding="utf-8") as fh:
        html = fh.read()
    payload = json.dumps(data(summary), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return html.replace("__ABR_DATA__", payload)


def fragment(html):
    """Isi halaman tanpa doctype/html/head/body: Artifact menambahkan kerangkanya sendiri."""
    html = re.sub(r"(?is)<!doctype[^>]*>|</?html[^>]*>|</?head>|</?body[^>]*>|<meta charset=[^>]*>|<meta name=\"viewport\"[^>]*>", "", html)
    return html.strip() + "\n"


def live_key(summary):
    """Berubah hanya bila ada acara baru untuk ditonton (atau run selesai)."""
    return sha256_text(json.dumps([[e["id"] for e in summary["events"]], summary["done"], summary.get("winner_status")]))[:16]


def _dump(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def live_doc(summary, limit=LIVE_LIMIT):
    """Dokumen untuk database artifact. Ringkasan disimpan sebagai string JSON
    (tanpa larik bersarang di dokumen) dan dipangkas bila melebihi batas ukuran:
    keberatan duel paling awal dikosongkan lebih dulu, lalu tesis petarung."""
    s = json.loads(_dump(summary))
    body = _dump(s)
    if len(body.encode("utf-8")) > limit:
        for e in s["events"]:
            for h in e.get("hits", []):
                h["obj"] = ""
            body = _dump(s)
            if len(body.encode("utf-8")) <= limit:
                break
    if len(body.encode("utf-8")) > limit:
        for f in s["fighters"].values():
            f["thesis"] = ""
        body = _dump(s)
    while len(body.encode("utf-8")) > limit and len(s["events"]) > 1:
        s["events"] = s["events"][max(1, len(s["events"]) // 4):]
        body = _dump(s)
    return {"format": "abr-arena-live/1", "run_id": s["run_id"], "updated_at": s.get("updated_at", ""),
            "rev": s["rev"], "done": s["done"], "summary": body}


def write(run, path=None):
    """Tulis arena.html, arena-data.json (penonton lewat serve), dan
    arena-live.json (penonton lewat artifact). Mengembalikan ringkasannya."""
    path = path or run.path("arena.html")
    summary = run_summary(run)
    atomic_write_text(path, render(summary))
    folder = os.path.dirname(path)
    atomic_write_text(os.path.join(folder, "arena-data.json"), _dump({"run": summary}))
    atomic_write_text(os.path.join(folder, LIVE_FILE), _dump(live_doc(summary)))
    return summary


def write_artifact(run):
    """Tulis arena-artifact.html (untuk diterbitkan sebagai Artifact) dan kembalikan path-nya."""
    summary = write(run)
    out = run.path(ARTIFACT_FILE)
    atomic_write_text(out, fragment(render(summary)))
    return out, summary


def write_demo(path):
    atomic_write_text(path, render(demo_summary()))
    return path
