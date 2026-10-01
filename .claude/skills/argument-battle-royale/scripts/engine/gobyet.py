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
CHAMPION_LABEL = "TOURNAMENT WINNER"

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
        for cid, c in res.chars.items():
            states = {}
            wanted = list(CORE) + list(ROLE_STATES.get(cid, ())) + [s for (sc, s) in SCENES.values() if sc == cid]
            for s in wanted:
                got = res.resolve(cid, s)
                if not got or got["character"] != cid or got["state"] in states:
                    continue
                states[got["state"]] = {"n": got["frames"], "ms": got["ms"], "loop": got["loop"],
                                        "src": _data_uri(os.path.join(root, got["sheet"]))}
            if states:
                chars[cid] = {"name": c["name"], "core": {k: v for k, v in c.get("core", {}).items() if v in states},
                              "fallback": c.get("fallback"), "acc": c.get("acc_anchor"), "states": states}
        if res.root_id not in chars:
            return None
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
            "topic": {"char": pick["primary"], "acc": pick["accessory"], "reason": pick["reason"]},
            "source": res.reg.get("source", {}),
        }
    except (OSError, ValueError, KeyError):
        return None


def describe(summary, root=ASSETS):
    """Ringkasan teks (untuk log/terminal): karakter tiap petarung dan alasannya."""
    c = cast(summary)
    return json.dumps(c, ensure_ascii=False, indent=1)
