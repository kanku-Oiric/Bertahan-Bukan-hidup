"""Arena HTML: halaman mandiri beranimasi yang menampilkan progres turnamen.

Ditulis ulang setiap kali `next` dijalankan (dan lewat `abr.py arena`). Bisa
dibuka di browser, panel pratinjau aplikasi Claude, atau ditampilkan sebagai
artifact di Claude.ai. Sprite dan adegan diambil dari engine/anim.py sehingga
identik dengan tampilan terminal.
"""

import json
import os

from . import anim
from . import config as C
from .util import atomic_write_text

TEMPLATE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "templates", "arena.html")

PREVIEWS = {
    "wizard": "Persiapan: pemetaan, generasi, deduplikasi, validasi, dan seeding petarung",
    "battle": "Bracket: eliminasi, deep review, Final 4, semifinal, dan final",
    "rocket": "Uji falsifikasi: juara diluncurkan ke pengujian terberat",
    "trophy": "Pemenang tahan-uji diumumkan",
    "idle": "Menunggu langkah berikutnya",
    "blocked": "Run terhenti dan menunggu tindakan",
    "nowinner": "Semua kandidat gugur dalam uji falsifikasi",
}


def _brief(fighters, fid):
    f = fighters.get(fid) or {}
    return {"id": fid, "title": f.get("title", fid)}


def _bracket(run, fighters):
    cols = []
    for slots in (8, 4, 2):
        rd = None
        r = 1
        while True:
            x = run.load_round(r)
            if not x:
                break
            if x["slots"] == slots:
                rd = x
            r += 1
        col = []
        if rd:
            for m in rd["matches"]:
                item = {"a": _brief(fighters, m["a"]), "b": _brief(fighters, m["b"]) if m["b"] else None, "winner": m.get("winner"), "votes": ""}
                v = m.get("votes")
                if m.get("winner") and v and m.get("winner_side"):
                    other = "b" if m["winner_side"] == "a" else "a"
                    item["votes"] = "%d–%d" % (v.get(m["winner_side"], 0), v.get(other, 0))
                col.append(item)
        cols.append(col)
    return cols


def run_summary(run):
    st = run.state
    cfg = st["config"]
    info = anim.status_info(run)
    fighters = run.load_fighters()
    map_obj = run.load("map.json") or {}
    seeding = run.load("seeding.json")
    pk = list(st["packets"].values())
    done_pk = sum(1 for p in pk if p["status"] != "pending")
    size = 0
    if st.get("current_round"):
        r1 = run.load_round(1)
        size = r1["slots"] if r1 else 0
    total_rounds = size.bit_length() - 1 if size else 0
    stats = [
        ["Petarung dihasilkan", str(len(fighters)) if fighters else "—"],
        ["Masuk bracket", str(len(seeding["order"])) if seeding else "—"],
        ["Babak", "%d dari %d" % (st["current_round"], total_rounds) if total_rounds else "—"],
        ["Paket kerja selesai", "%d / %d" % (done_pk, len(pk))],
    ]
    winner = st.get("winner")
    champ = st.get("champion")
    lang = cfg.get("language", "id")
    return {
        "demo": False,
        "topic": cfg["topic"],
        "restated": map_obj.get("topic_restated", ""),
        "info": info,
        "stages": anim.STAGES,
        "stats": stats,
        "bracket": _bracket(run, fighters),
        "champion": _brief(fighters, champ) if champ else None,
        "winner": dict(_brief(fighters, winner), thesis=fighters[winner]["thesis"]) if winner else None,
        "winner_status": st.get("winner_falsification"),
        "done": st["phase"] == "done",
        "formula": anim.formula(lang),
        "previews": PREVIEWS,
        "foot": "Mode %s · populasi %d · seed %d · diperbarui %s · %s" % (
            cfg["mode"], cfg["population"], cfg["random_seed"], st.get("updated_at", ""), os.path.basename(run.dir)),
    }


def demo_summary():
    return {
        "demo": True,
        "topic": "Pratinjau animasi Clawd",
        "restated": "Adegan berganti setiap empat detik; pilih chip untuk memutar adegan tertentu.",
        "info": {"scene": "wizard", "stage_index": 2, "stage": anim.STAGES[2], "stage_count": len(anim.STAGES),
                 "percent": 18, "caption": "Menyihir 1000 petarung", "round": 0, "key": "demo", "done": False},
        "stages": anim.STAGES,
        "stats": [["Petarung dihasilkan", "—"], ["Masuk bracket", "—"], ["Babak", "—"], ["Paket kerja selesai", "—"]],
        "bracket": [[], [], []],
        "champion": None,
        "winner": None,
        "winner_status": None,
        "done": False,
        "formula": C.WINNER_FORMULA["id"],
        "previews": PREVIEWS,
        "foot": "Pratinjau tanpa run. Jalankan abr.py arena --run DIR untuk arena sebuah run.",
    }


def render(summary):
    with open(TEMPLATE, "r", encoding="utf-8") as fh:
        html = fh.read()
    data = {"anim": anim.web_data(), "run": summary}
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    refresh = "" if (summary["demo"] or summary["done"]) else '<meta http-equiv="refresh" content="20">'
    return html.replace("__ABR_REFRESH__", refresh).replace("__ABR_DATA__", payload)


def write(run, path=None):
    path = path or run.path("arena.html")
    atomic_write_text(path, render(run_summary(run)))
    return path


def write_demo(path):
    atomic_write_text(path, render(demo_summary()))
    return path
