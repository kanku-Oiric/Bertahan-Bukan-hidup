"""Lapisan visual Gobyet untuk arena HTML. Terpisah dari logika turnamen.

Modul turnamen (phases, judging, bracket, validate, ...) tidak mengimpor modul ini; hanya arena.py yang memakainya
untuk dua hal:
  - cast(summary): memilih karakter Gobyet per petarung dari teks argumennya (judul, posisi, tesis), dengan topik
    sebagai cadangan; satu karakter primer + paling banyak satu ikon aksesori (gobyet_context.select). Bila dua
    petarung satu duel mendapat karakter sama, arena menampilkan varian tukar peran petarung kedua (karakter domain
    sekundernya + ikon domain primernya), supaya duel tidak tampak seperti cermin. Hanya tampilan.
  - web_data(summary): menyematkan sprite sheet (data URI PNG) + registry ringkas ke halaman arena.
Peran turnamen tetap: wasit = referee, juri = judge, uji falsifikasi = skeptic, pemenang = champion
(label "TOURNAMENT WINNER", bukan kebenaran mutlak), yang kalah memakai animasi defeat kelasnya sendiri.

Berserker Hero (tokoh utama Gobyet, kanvas 128x96) tampil di dua tempat, keduanya hanya tampilan:
  - pembuka arena (INTRO): sekali di awal tayangan, lari masuk lalu mengamuk; tidak ikut bertarung atau dinilai;
  - petarung bila teks argumen atau topiknya bertema pahlawan, perang, naga, monster, atau prajurit (domain "hero").
Karakter berkanvas sendiri membawa `canvas`, `anchor`, `px` (skala gambar relatif Gobyet 64x64) dan durasi per frame
(`durs`); karakter 64x64 tetap memakai kanvas, jangkar, dan ms seragam global.

Bila aset tidak ada atau rusak, web_data() mengembalikan None dan arena memakai sprite Clawd seperti sebelumnya;
karakter atau state yang hilang turun lewat rantai fallback (gobyet_resolve) dan tidak pernah tampil sebagai
gambar rusak. Hanya pustaka standar.
"""
import base64
import json
import os

from . import gobyet_context as ctx
from .gobyet_resolve import Resolver

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(SKILL, "assets", "gobyet")
CORE = ("idle", "attack", "hit", "victory", "defeat")
ENTRANCE = "run"  # dipakai saat masuk duel bila karakter punya state itu sendiri (kalau tidak: idle seperti biasa)
CHAMPION_LABEL = "TOURNAMENT WINNER"
# pembuka arena: karakter, state masuk, state pose, teks ticker. None = tanpa pembuka.
INTRO = {"char": "berserker-hero", "run": "run", "pose": "rage", "title": "Berserker Hero membuka arena",
         "text": "Tokoh utama Gobyet. Hanya pembuka: tidak ikut bertarung dan tidak memengaruhi penilaian."}

# adegan arena -> (karakter, state)
SCENES = {
    "wizard": ("wizard", "cast"),
    "battle": ("referee", "signal_start"),
    "rocket": ("skeptic", "inspect"),
    "trophy": ("champion", "trophy_raise"),
    "idle": ("normal-gblk", "idle"),
    "blocked": ("normal-gblk", "confused"),
    "nowinner": ("defeated", "sit"),
}
ROLE_STATES = {
    "referee": ("signal_start", "point_winner"),
    "judge": ("finalize", "write_score"),
    "skeptic": ("inspect", "falsification"),
    "champion": ("trophy_raise", "celebrate"),
    "defeated": ("sit", "fall"),
}


def load(root=ASSETS):
    """Resolver atas aset yang benar-benar ada; None bila registry tidak terbaca."""
    try:
        return Resolver.load(root)
    except (OSError, ValueError, KeyError):
        return None


def _fighter_text(f):
    return " ".join(str(f.get(k) or "") for k in ("title", "stance", "thesis"))


def cast(summary):
    """Peta id petarung -> {char, acc, reason}. Deterministik: hanya bergantung pada teks."""
    topic = "%s %s" % (summary.get("topic", ""), summary.get("restated", ""))
    fighters = summary.get("fighters", {}) or {}
    ids = sorted(fighters)
    picks = ctx.cast_for(topic, [_fighter_text(fighters[i]) for i in ids])
    out = {}
    for fid, p in zip(ids, picks):
        e = {"char": p["primary"], "acc": p["accessory"], "reason": p["reason"]}
        if p.get("alt"):
            e["alt"], e["alt_acc"] = p["alt"], p.get("alt_accessory")
        out[fid] = e
    return out


def _data_uri(path):
    with open(path, "rb") as fh:
        return "data:image/png;base64," + base64.b64encode(fh.read()).decode("ascii")


def web_data(summary, root=ASSETS):
    """Data sprite untuk arena. Menyematkan semua karakter yang punya aset (supaya petarung baru dari pembaruan live
    tetap punya sprite); tiap state diperiksa lewat resolver, jadi berkas yang hilang diganti fallback-nya."""
    res = load(root)
    if res is None:
        return None
    try:
        chars = {}
        intro = INTRO if INTRO and INTRO["char"] in res.chars else None
        for cid, c in res.chars.items():
            states = {}
            wanted = list(CORE) + list(ROLE_STATES.get(cid, ())) + [s for (sc, s) in SCENES.values() if sc == cid] + [ENTRANCE]
            wanted += [s for v in c.get("variants", {}).values() for s in v]
            if intro and cid == intro["char"]:
                wanted += [intro["run"], intro["pose"]]
            for s in wanted:
                got = res.resolve(cid, s)
                if not got or got["character"] != cid or got["state"] in states:
                    continue
                st = {"n": got["frames"], "ms": got["ms"], "loop": got["loop"], "src": _data_uri(os.path.join(root, got["sheet"]))}
                durs = got.get("durations") or []
                if len(durs) == got["frames"] and len(set(durs)) > 1:
                    st["durs"] = durs
                states[got["state"]] = st
            if states:
                e = {"name": c["name"], "core": {k: v for k, v in c.get("core", {}).items() if v in states},
                     "fallback": c.get("fallback"), "acc": c.get("acc_anchor"), "states": states}
                if c.get("canvas") and c["canvas"] != res.reg["canvas"]:
                    e["canvas"], e["anchor"], e["px"] = c["canvas"], c.get("anchor", res.reg["anchor"]), c.get("px")
                var = {k: [s for s in v if s in states] for k, v in c.get("variants", {}).items()}
                var = {k: v for k, v in var.items() if len(v) > 1}
                if var:
                    e["variants"] = var
                chars[cid] = e
        if res.root_id not in chars:
            return None
        if intro and not {intro["run"], intro["pose"]} <= set(chars.get(intro["char"], {}).get("states", {})):
            intro = None
        icons = {}
        for name, rel in res.reg.get("icons", {}).items():
            p = os.path.join(root, rel)
            if os.path.exists(p):
                icons[name] = _data_uri(p)
        topic = "%s %s" % (summary.get("topic", ""), summary.get("restated", ""))
        pick = ctx.select(topic)
        return {
            "v": 1,
            "canvas": res.reg["canvas"],
            "anchor": res.reg["anchor"],
            "root": res.root_id,
            "chars": chars,
            "icons": icons,
            "scenes": SCENES,
            "roles": {"referee": "referee", "judge": "judge", "skeptic": "skeptic", "champion": "champion", "defeated": "defeated"},
            "champion_label": CHAMPION_LABEL,
            "intro": intro,
            "topic": {"char": pick["primary"], "acc": pick["accessory"], "reason": pick["reason"]},
            "source": res.reg.get("source", {}),
        }
    except (OSError, ValueError, KeyError):
        return None


def describe(summary, root=ASSETS):
    """Ringkasan teks (untuk log/terminal): karakter tiap petarung dan alasannya."""
    c = cast(summary)
    return json.dumps(c, ensure_ascii=False, indent=1)
