"""Animasi Clawd untuk Argument Battle Royale.

Satu sumber kebenaran untuk semua tampilan:
  - sprite pixel art (Clawd, topi penyihir, tongkat, roket, detonator, piala)
  - adegan per fase turnamen, dideskripsikan sebagai *lapisan* (sprite + posisi)
    per frame, sehingga Python (terminal) dan JavaScript (arena HTML) merender
    frame yang identik dari data yang sama
  - perender: ANSI half-block (terminal live), teks mini (flipbook di chat),
    dan satu baris status line

Tidak ada dependensi di luar pustaka standar.
"""

import time

from . import config as C

CANVAS_W, CANVAS_H = 60, 30
FPS = 6

PALETTE = {
    "O": "#F4784A",  # tubuh Clawd
    "D": "#C8552F",  # bayangan tubuh
    "K": "#141414",  # mata, nozel
    "N": "#23478C",  # biru navy (topi, roket)
    "n": "#15295A",  # navy gelap
    "C": "#F6DEB0",  # pita krem topi
    "c": "#D9B98A",  # bayangan pita
    "W": "#F4F4F2",  # badan roket
    "G": "#B9BCC4",  # abu-abu
    "L": "#BFDAF4",  # kaca jendela
    "Y": "#F9C23C",  # kuning (percikan, api, piala)
    "y": "#F28C28",  # api jingga
    "R": "#E0412A",  # merah (tombol, tanda seru)
    "B": "#5A3325",  # tongkat sihir
    "A": "#2C2D33",  # kotak detonator
    "P": "#B06AD8",  # konfeti ungu
    "E": "#3FBF7F",  # konfeti hijau
    "S": "#FFFFFF",  # kilau putih
}

# ---------------------------------------------------------------------------
# Sprite dasar. '.' = transparan. Proporsi diambil dari karakter referensi:
# tubuh 19 piksel, lengan menonjol kiri-kanan, empat kaki.
# ---------------------------------------------------------------------------
_BODY = [
    "...DDOOOOOOOOOOOOOOOOO...",
    "...DDOOOOOOOOOOOOOOOOO...",
    "...DDOOOOOOOOOOOOOOOOO...",
    "...DDOOOOOOOOOOOOOOOOO...",
    "...DDOOOOOOOOOOOOOOOOO...",
    ".DDDDOOOOOOOOOOOOOOOOOOO.",
    "DDOOOOOOOOOOOOOOOOOOOOOOO",
    "DDOOOOOOOOOOOOOOOOOOOOOOD",
    ".DDDDOOOOOOOOOOOOOOOOODD.",
    "...DDOOOOOOOOOOOOOOOOO...",
    "...DDOOOOOOOOOOOOOOOOO...",
    "...DDOOOOOOOOOOOOOOOOO...",
    ".....DO.DOO.....DO.DOO...",
    ".....DO.DOO.....DO.DOO...",
    ".....DO.DOO.....DO.DOO...",
]
PAD = 4  # baris kosong di atas tubuh untuk lengan terangkat
BODY_W = 25

_EYES = {
    "open": [(7, 3), (8, 3), (7, 4), (8, 4), (16, 3), (17, 3), (16, 4), (17, 4)],
    "blink": [(7, 4), (8, 4), (16, 4), (17, 4)],
    "wink": [(7, 3), (8, 3), (7, 4), (8, 4), (16, 4), (17, 4)],
    "angry": [(8, 3), (7, 4), (8, 4), (16, 3), (16, 4), (17, 4)],
    "happy": [(7, 4), (8, 3), (9, 4), (15, 4), (16, 3), (17, 4)],
}

_HAT = [
    "......NNNNN............",
    ".....NNNNNNN...........",
    "....NNnnNNNNN..........",
    "....nn.nnNNNNN.........",
    ".......nnNNNNNN........",
    ".......nNNNNNNN........",
    "......nnnNNNNNNN.......",
    "......nnNNNNNNNN.......",
    ".....nnNNNNNNNNNN......",
    ".....ncCCCCCCCCCC......",
    ".....ccCCCCCCCCCCC.....",
    "...nnnnNNNNNNNNNNNNN...",
    ".nnnnNNNNNNNNNNNNNNNNN.",
    "nnnnnnnnnnnnnnnnnnnnnnn",
]

_ROCKET = [
    "......N......",
    ".....nNN.....",
    "....nNNNN....",
    "...nNNNNNN...",
    "...GWWWWWW...",
    "...GWWWWWW...",
    "...GWnNNWW...",
    "...GnLLLNW...",
    "...GnLLLNW...",
    "...GWnNNWW...",
    "...GWWWWWW...",
    ".N.GWWWWWW.N.",
    "NN.GWWWWWW.NN",
    "NNNGWWWWWWNNN",
    "NN.GGGGGGG.NN",
    "N...AKKKA...N",
]

_FLAMES = [
    [".....yYy.....", "....yYYYy....", ".....YYY.....", "......Y......"],
    ["....yYYYy....", "....yYYYy....", ".....yYy.....", "......y......"],
    [".....yYy.....", ".....YYY.....", "......Y......", "..Y.......Y.."],
]

_BOX = ["..RR..", "AAAAAA", "AAAAAA", ".AAAA."]
_BOX_PRESSED = ["......", "AARRAA", "AAAAAA", ".AAAA."]

_TROPHY = [
    "YYYYYYYYY",
    "Y.YYYYY.Y",
    "Y.YYYYY.Y",
    ".YYYYYYY.",
    "..YYYYY..",
    "....Y....",
    "...YYY...",
    "..BBBBB..",
]

_PODIUM = [
    "GGGGGGGGGGGGG",
    "GWWWWWYWWWWWG",
    "GWWWWYYWWWWWG",
    "GWWWWWYWWWWWG",
    "GGGGGGGGGGGGG",
]

_BANG = ["RR", "RR", "RR", "..", "RR"]
_QUESTION = [".YYY.", "Y...Y", "...Y.", "..Y..", ".....", "..Y.."]


def _clawd(eyes="open", arms="side"):
    g = [list("." * BODY_W) for _ in range(PAD)] + [list(r) for r in _BODY]
    for x, y in _EYES["open"]:
        g[PAD + y][x] = "O"
    for x, y in _EYES[eyes]:
        g[PAD + y][x] = "K"
    if arms in ("up", "wave"):
        # lengan kiri terangkat miring ke kiri-atas, seperti melambai
        for y in range(5, 9):
            for x in range(0, 3):
                g[PAD + y][x] = "."
        for dy, x0 in ((4, 1), (3, 1), (2, 0), (1, 0), (0, 0), (-1, 0)):
            g[PAD + dy][x0], g[PAD + dy][x0 + 1] = "D", "O"
        g[PAD + 4][3] = "D"
    if arms == "up":
        for y in range(5, 9):
            for x in range(22, 25):
                g[PAD + y][x] = "."
        for dy, x0 in ((4, 22), (3, 22), (2, 23), (1, 23), (0, 23), (-1, 23)):
            g[PAD + dy][x0], g[PAD + dy][x0 + 1] = "O", "D"
    return ["".join(r) for r in g]


def _sprites():
    lib = {
        "hat": _HAT,
        "rocket": _ROCKET,
        "box": _BOX,
        "box_on": _BOX_PRESSED,
        "trophy": _TROPHY,
        "podium": _PODIUM,
        "bang": _BANG,
        "question": _QUESTION,
    }
    for i, f in enumerate(_FLAMES):
        lib["flame%d" % i] = f
    for eyes in _EYES:
        for arms in ("side", "up", "wave"):
            lib["clawd_%s_%s" % (eyes, arms)] = _clawd(eyes, arms)
    return lib


SPRITES = _sprites()

# ---------------------------------------------------------------------------
# Adegan: fungsi frame(i) -> {"l": [[sprite, x, y, mirror]], "p": [[x, y, c]]}
# ---------------------------------------------------------------------------
BODY_TOP = 15            # baris kanvas untuk atas tubuh Clawd
CLAWD_Y = BODY_TOP - PAD


def _star(cx, cy, c="Y", big=False):
    pts = [(cx, cy, "S" if big else c), (cx - 1, cy, c), (cx + 1, cy, c), (cx, cy - 1, c), (cx, cy + 1, c)]
    if big:
        pts += [(cx - 2, cy, c), (cx + 2, cy, c), (cx, cy - 2, c), (cx, cy + 2, c)]
    return pts


def _wizard(i):
    x = 12
    eyes = "blink" if i % 8 == 7 else "wink"
    layers = [["clawd_%s_side" % eyes, x, CLAWD_Y, 0], ["hat", x + 1, BODY_TOP - 14, 0]]
    t = BODY_TOP
    px = [[x + 25, t + 4, "O"], [x + 25, t + 5, "O"]]
    for dx, dy in ((26, 4), (26, 3), (27, 2), (27, 1), (28, 0), (28, -1), (29, -2)):
        px.append([x + dx, t + dy, "B"])
    px += [[a, b, c] for a, b, c in _star(x + 30, t - 4, big=(i % 2 == 0))]
    dots = [
        [(28, -9), (34, -7), (33, -1), (25, -6)],
        [(31, -10), (26, -5), (35, -4), (32, 0)],
        [(29, -8), (35, -8), (34, -2), (26, -7)],
        [(32, -11), (27, -8), (36, -5), (31, -1)],
    ][i % 4]
    px += [[x + a, t + b, "Y"] for a, b in dots]
    return {"l": layers, "p": px}


def _battle(i):
    up_a = 1 if i % 2 == 0 else 0
    up_b = 1 - up_a
    layers = [["clawd_angry_side", 3, CLAWD_Y - up_a, 0], ["clawd_angry_side", 32, CLAWD_Y - up_b, 1]]
    cx, cy = 29, BODY_TOP + 6
    px = []
    if i % 4 in (0, 2):
        px += [[a, b, c] for a, b, c in _star(cx, cy, "Y", big=(i % 4 == 0))]
    else:
        px += [[cx - 1, cy - 1, "R"], [cx + 1, cy + 1, "R"], [cx + 1, cy - 1, "R"], [cx - 1, cy + 1, "R"], [cx, cy, "S"]]
    dust = [(6, 29), (9, 29)] if up_a else [(51, 29), (54, 29)]
    px += [[a, b, "G"] for a, b in dust]
    return {"l": layers, "p": px}


def _rocket(i):
    x = 3
    layers = [["clawd_angry_wave", x, CLAWD_Y, 0], ["box_on" if i % 8 >= 1 else "box", x + 24, BODY_TOP + 4, 0]]
    rise = 0 if i % 8 < 2 else (i % 8 - 1) * 2
    ry = 10 - rise
    layers.append(["rocket", 40, ry, 0])
    if i % 8 >= 1:
        layers.append(["flame%d" % (i % 3), 40, ry + 16, 0])
    px = [[a, 29, "G"] for a in range(39, 54)]
    if i % 8 >= 2:
        sparks = [(38, 28), (43, 29), (51, 28), (55, 29), (40, 27), (53, 27)]
        px += [[a, b, "Y" if (a + i) % 2 else "y"] for a, b in sparks[(i % 3):(i % 3) + 4]]
    return {"l": layers, "p": px}


def _trophy(i):
    x = 9
    hop = 1 if i % 2 else 0
    layers = [["clawd_happy_wave", x, CLAWD_Y - hop, 0], ["podium", 38, 25, 0], ["trophy", 40, 17, 0]]
    seed = 17 + i * 7
    colors = "YRNPEO"
    px = []
    for k in range(18):
        seed = (seed * 1103515245 + 12345) % 2147483648
        cx = seed % CANVAS_W
        cy = (seed // CANVAS_W + i * 2) % 14
        px.append([cx, cy, colors[k % len(colors)]])
    return {"l": layers, "p": px}


def _idle(i, mark=None):
    eyes = "blink" if i % 6 == 5 else "open"
    layers = [["clawd_%s_side" % eyes, 17, CLAWD_Y, 0]]
    if mark == "bang" and i % 2 == 0:
        layers.append(["bang", 28, BODY_TOP - 7, 0])
    if mark == "question":
        layers.append(["question", 27, BODY_TOP - 8 - (i % 2), 0])
    return {"l": layers, "p": []}


SCENES = {
    "wizard": (_wizard, 8),
    "battle": (_battle, 4),
    "rocket": (_rocket, 8),
    "trophy": (_trophy, 4),
    "idle": (lambda i: _idle(i), 6),
    "blocked": (lambda i: _idle(i, "bang"), 4),
    "nowinner": (lambda i: _idle(i, "question"), 6),
}

SCENE_LABEL = {
    "wizard": "Sihir",
    "battle": "Duel",
    "rocket": "Peluncuran",
    "trophy": "Juara",
    "idle": "Santai",
    "blocked": "Terhenti",
    "nowinner": "Tanpa pemenang",
}


def frames(scene):
    fn, n = SCENES[scene]
    return [fn(i) for i in range(n)]


def rasterize(frame):
    grid = [["."] * CANVAS_W for _ in range(CANVAS_H)]
    for name, x, y, mirror in frame["l"]:
        rows = SPRITES[name]
        w = len(rows[0])
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row[::-1] if mirror else row):
                if ch == "." or not (0 <= y + dy < CANVAS_H and 0 <= x + dx < CANVAS_W):
                    continue
                grid[y + dy][x + dx] = ch
        del w
    for x, y, ch in frame["p"]:
        if 0 <= y < CANVAS_H and 0 <= x < CANVAS_W:
            grid[y][x] = ch
    return grid


def web_data():
    """Data kompak untuk arena HTML: palet, sprite, dan lapisan tiap frame."""
    scenes = {name: frames(name) for name in SCENES}
    used = sorted({layer[0] for fr in scenes.values() for f in fr for layer in f["l"]})
    return {
        "w": CANVAS_W,
        "h": CANVAS_H,
        "fps": FPS,
        "palette": PALETTE,
        "sprites": {name: SPRITES[name] for name in used},
        "scenes": scenes,
        "labels": SCENE_LABEL,
    }


# ---------------------------------------------------------------------------
# Status turnamen -> adegan, tahap, persentase, keterangan
# ---------------------------------------------------------------------------
STAGES = [
    "TOPIK", "PEMETAAN", "GENERASI", "DEDUPLIKASI", "VALIDASI", "SEEDING", "BRACKET",
    "ELIMINASI", "DEEP REVIEW", "FINAL 4", "SEMIFINAL", "FINAL", "PEMENANG",
    "UJI FALSIFIKASI", "LAPORAN",
]
_ROUND_STAGE = {"elimination": 7, "deep_review": 8, "semifinal": 10, "final": 11}


def status_info(run):
    st = run.state
    cfg = st["config"]
    ph = st["phase"]
    rd = run.load_round(st["current_round"]) if st.get("current_round") else None
    gr = st.get("generation_round", 0)
    idx = {"init": 0, "map": 1, "generate": 2, "dedup": 3, "validate": 4, "seed": 5,
           "final4": 9, "falsification": 13, "report": 14, "done": 15}.get(ph, 0)
    stage_key = {"map": "map", "generate": "gen:%d" % gr, "dedup": "dedup:%d" % gr,
                 "validate": "scout:%d" % gr, "final4": "final4", "falsification": "falsify:"}.get(ph)
    if ph == "round" and rd:
        idx = _ROUND_STAGE.get(rd["stage"], 7)
        stage_key = "round:%d:" % rd["round"]
    frac = 0.0
    if stage_key:
        pk = [p for p in st["packets"].values() if p["stage"] == stage_key or (stage_key.endswith(":") and p["stage"].startswith(stage_key))]
        if pk:
            frac = sum(1 for p in pk if p["status"] != "pending") / float(len(pk))
    pct = 100 if ph == "done" else int(100 * (idx + frac) / len(STAGES))
    n_f = len(run.load_fighters()) if ph not in ("init", "map") else 0
    label = rd["label"] if rd else ""
    winner = st.get("winner")
    if st.get("blocked"):
        scene, caption = "blocked", "Terhenti: %s" % st["blocked"]["reason"]
    elif ph in ("init", "map"):
        scene, caption = "wizard", "Clawd memetakan ruang argumen"
    elif ph == "generate":
        scene, caption = "wizard", "Menyihir %d petarung" % (cfg["population"] if gr == 0 else len(run.load("plan.json", {}).get("refills", [{}])[-1].get("slots", [])))
    elif ph == "dedup":
        scene, caption = "wizard", "Menyaring kembaran di antara %d petarung" % n_f
    elif ph == "validate":
        scene, caption = "wizard", "Scouting dan validasi %d petarung" % n_f
    elif ph == "seed":
        scene, caption = "wizard", "Menyusun unggulan bracket"
    elif ph == "round" and rd:
        scene = "battle"
        caption = {
            "elimination": "%s: duel berlangsung",
            "deep_review": "%s: panel juri menimbang",
            "semifinal": "%s: debat berlangsung",
            "final": "%s: dua argumen terakhir",
        }[rd["stage"]] % label
    elif ph == "final4":
        scene, caption = "battle", "Final 4: menyusun dosir para finalis"
    elif ph == "falsification":
        scene, caption = "rocket", "Uji falsifikasi: meluncurkan pengujian terhadap juara"
    elif ph in ("report", "done") and winner:
        scene, caption = "trophy", "Pemenang tahan-uji: %s" % run.load_fighters()[winner]["title"]
    elif ph in ("report", "done"):
        scene, caption = "nowinner", "Tidak ada pemenang tahan-uji"
    else:
        scene, caption = "idle", ph
    shown_idx = min(idx, len(STAGES) - 1)
    return {
        "done": ph == "done",
        "scene": scene,
        "stage_index": shown_idx,
        "stage": STAGES[shown_idx],
        "stage_count": len(STAGES),
        "percent": pct,
        "caption": caption,
        "round": rd["round"] if rd else 0,
        "key": "%s|%d|%d|%s" % (scene, shown_idx, rd["round"] if rd else 0, ph),
    }


def bar(pct, width=15, on="▰", off="▱"):
    k = int(round(width * pct / 100.0))
    return on * k + off * (width - k)


# ---------------------------------------------------------------------------
# Perender teks mini (flipbook di chat): memakai glyph Clawd dari Claude Code
# ditambah properti emoji berwarna. Murah token dan aman di terminal maupun web.
# ---------------------------------------------------------------------------
_MB = [" ▐▛███▜▌", "▝▜█████▛▘", "  ▘▘ ▝▝"]
_MB_WALK = "  ▝▘ ▘▝"


def _width(text):
    w = 0
    for ch in text:
        o = ord(ch)
        if o == 0xFE0F:
            continue
        w += 2 if (o >= 0x1F000 or ch in "⚡❗❓") else 1
    return w


def _pad(text, col):
    return text + " " * max(0, col - _width(text))


def _mini_art(scene, i):
    legs = _MB[2] if i % 2 == 0 else _MB_WALK
    if scene == "wizard":
        props = ["🪄✨", "🪄 ✨✨", "🪄  ✨"][i % 3]
        return [_MB[0] + " " + props, _MB[1], legs]
    if scene == "battle":
        mid = ["⚡", "💥"][i % 2]
        x = 14  # kolom awal Clawd kedua
        return [_pad(_MB[0], x) + _MB[0], _pad(_MB[1] + "  " + mid, x) + _MB[1], _pad(legs, x) + legs]
    if scene == "rocket":
        sky = ["", "            🚀", "              🚀"][i % 3]
        return ([sky] if sky else []) + [_MB[0] + "  🔴", _MB[1] + "    " + ("🚀🔥" if not sky else "🔥"), legs]
    if scene == "trophy":
        return ["   🏆  🎉" if i % 2 == 0 else "   🏆 🎊", _MB[0], _MB[1], legs]
    if scene == "blocked":
        return ["    ❗", _MB[0], _MB[1], _MB[2]]
    if scene == "nowinner":
        return ["    ❓", _MB[0], _MB[1], _MB[2]]
    return [_MB[0] + " 💤", _MB[1], _MB[2]]


def mini(info, i):
    art = _mini_art(info["scene"], i)
    lines = art + [
        "%s · tahap %d/%d" % (info["stage"], info["stage_index"] + 1, info["stage_count"]),
        "%s %d%% · %s" % (bar(info["percent"]), info["percent"], info["caption"]),
    ]
    return "\n".join(line.rstrip() for line in lines)


# ---------------------------------------------------------------------------
# Perender ANSI (terminal live) dengan karakter setengah-blok
# ---------------------------------------------------------------------------
def _rgb(hexcolor):
    h = hexcolor.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _xterm256(r, g, b):
    def q(v):
        return 0 if v < 48 else 1 if v < 115 else (v - 35) // 40
    return 16 + 36 * q(r) + 6 * q(g) + q(b)


def _fg(hexcolor, mode):
    r, g, b = _rgb(hexcolor)
    return "\x1b[38;2;%d;%d;%dm" % (r, g, b) if mode == "truecolor" else "\x1b[38;5;%dm" % _xterm256(r, g, b)


def _bg(hexcolor, mode):
    r, g, b = _rgb(hexcolor)
    return "\x1b[48;2;%d;%d;%dm" % (r, g, b) if mode == "truecolor" else "\x1b[48;5;%dm" % _xterm256(r, g, b)


RESET = "\x1b[0m"


def ansi(grid, mode="truecolor"):
    """Dua baris piksel per baris terminal; kode warna hanya ditulis saat berubah."""
    out = []
    for y in range(0, len(grid), 2):
        top, bot = grid[y], grid[y + 1] if y + 1 < len(grid) else ["."] * len(grid[y])
        cells = list(zip(top, bot))
        while cells and cells[-1] == (".", "."):
            cells.pop()
        line, state = [], None
        for t, b in cells:
            if t == "." and b == ".":
                want, ch = ("reset",), " "
            elif b == ".":
                want, ch = ("fg", t), "▀"
            elif t == ".":
                want, ch = ("fg", b), "▄"
            else:
                want, ch = ("fgbg", t, b), "▀"
            if want != state:
                code = RESET
                if want[0] == "fg":
                    code += _fg(PALETTE[want[1]], mode)
                elif want[0] == "fgbg":
                    code += _fg(PALETTE[want[1]], mode) + _bg(PALETTE[want[2]], mode)
                line.append(code)
                state = want
            line.append(ch)
        out.append("".join(line) + RESET)
    return out


def statusline(info, mode="truecolor"):
    i = int(time.time() * 2)
    prop = {
        "wizard": "🪄✨" if i % 2 else "🪄 ✨",
        "battle": "⚡" if i % 2 else "💥",
        "rocket": "🚀" if i % 2 else "🔥",
        "trophy": "🏆",
        "blocked": "❗",
        "nowinner": "❓",
        "idle": "💤",
    }[info["scene"]]
    clawd = _fg(PALETTE["O"], mode) + ("▐▛███▜▌" if i % 4 else "▐▙███▟▌") + RESET
    return "%s %s ABR %s %s %d%% · %s" % (clawd, prop, info["stage"], bar(info["percent"], 10), info["percent"], info["caption"])


def formula(lang):
    return C.WINNER_FORMULA.get(lang, C.WINNER_FORMULA["id"])
