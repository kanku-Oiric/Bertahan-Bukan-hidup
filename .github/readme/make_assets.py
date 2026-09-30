#!/usr/bin/env python3
"""Bangun visual README (SVG) dari data sprite dan contoh run skill.

    python3 .github/readme/make_assets.py
    python3 .github/readme/make_assets.py --static banner-static.svg

Menulis banner.svg, pipeline.svg, dan bracket.svg di folder ini. Varian
--static (tanpa animasi) dipakai untuk merender social-preview.png. Sprite Clawd
diambil dari engine skill (scripts/engine/anim.py) dan bracket dari contoh run
nyata (examples/sample-run/arena-data.json), jadi visual selalu sesuai kode.
Judul memakai font pixel 5x7 yang digambar sebagai kotak, sehingga tidak
bergantung pada font apa pun di browser pembaca.
"""

import json
import os
import sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SKILL = os.path.join(ROOT, ".claude", "skills", "argument-battle-royale")
sys.path.insert(0, os.path.join(SKILL, "scripts"))

from engine import anim  # noqa: E402

WEB = anim.web_data()
PAL = WEB["palette"]

# Palet arena (sama dengan templates/arena.html).
BG, BG2 = "#111830", "#182142"
LINE = "#2A3458"
INK, DIM, SOFT = "#E8ECF8", "#8C96B8", "#C9D0EA"
ACCENT, GOLD, LOW, OK = "#F4784A", "#F9C23C", "#E0412A", "#3FBF7F"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

# Font pixel 5x7 (huruf kapital, angka, tanda baca yang dipakai).
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10011", "10101", "10101", "10101", "11001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000"] * 7,
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    "?": ["01110", "10001", "00001", "00010", "00100", "00000", "00100"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "·": ["00000", "00000", "00000", "01100", "01100", "00000", "00000"],
}


def pixel_width(text, s, gap=1):
    return len(text) * (5 + gap) * s - gap * s


def pixel_text(text, x, y, s, fill, gap=1, anchor="start"):
    """Teks font pixel sebagai satu <path> (kotak-kotak s x s)."""
    if anchor == "middle":
        x -= pixel_width(text, s, gap) / 2
    elif anchor == "end":
        x -= pixel_width(text, s, gap)
    d = []
    for i, ch in enumerate(text.upper()):
        rows = FONT.get(ch, FONT["?"])
        ox = x + i * (5 + gap) * s
        for ry, row in enumerate(rows):
            rx = 0
            while rx < 5:
                if row[rx] == "1":
                    run = 1
                    while rx + run < 5 and row[rx + run] == "1":
                        run += 1
                    d.append("M%g %gh%gv%gh-%gz" % (ox + rx * s, y + ry * s, run * s, s, run * s))
                    rx += run
                else:
                    rx += 1
    return '<path fill="%s" d="%s"/>' % (fill, "".join(d))


def sprite(name, x, y, s, mirror=False, cls=None):
    """Sprite dari anim.py sebagai <g> berisi satu <path> per warna."""
    rows = WEB["sprites"][name]
    by_color = {}
    for ry, row in enumerate(rows):
        if mirror:
            row = row[::-1]
        rx = 0
        while rx < len(row):
            ch = row[rx]
            if ch == ".":
                rx += 1
                continue
            run = 1
            while rx + run < len(row) and row[rx + run] == ch:
                run += 1
            by_color.setdefault(ch, []).append("M%g %gh%gv%gh-%gz" % (x + rx * s, y + ry * s, run * s, s, run * s))
            rx += run
    attr = ' class="%s"' % cls if cls else ""
    body = "".join('<path fill="%s" d="%s"/>' % (PAL[c], "".join(p)) for c, p in by_color.items())
    return "<g%s>%s</g>" % (attr, body)


BURST = [
    "....Y....",
    ".Y..Y..Y.",
    "..Y.S.Y..",
    "...SSS...",
    "YYSSSSSYY",
    "...SSS...",
    "..Y.S.Y..",
    ".Y..Y..Y.",
    "....Y....",
]
WEB["sprites"]["burst"] = BURST


def sprite_size(name, s):
    rows = WEB["sprites"][name]
    return len(rows[0]) * s, len(rows) * s


def text(x, y, s, size, fill, family=MONO, anchor="start", weight=None, opacity=None):
    extra = ""
    if weight:
        extra += ' font-weight="%s"' % weight
    if opacity:
        extra += ' opacity="%s"' % opacity
    return '<text x="%g" y="%g" font-family="%s" font-size="%g" fill="%s" text-anchor="%s"%s>%s</text>' % (
        x, y, escape(family, {'"': "&quot;"}), size, fill, anchor, extra, escape(s))


def clip(s, n):
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def wrap(s, n):
    lines, cur = [], ""
    for word in s.split():
        if cur and len(cur) + 1 + len(word) > n:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    return lines + ([cur] if cur else [])


def frame(w, h, body, title, desc, style=""):
    grid = ('<pattern id="g" width="32" height="32" patternUnits="userSpaceOnUse">'
            '<path d="M32 0H0V32" fill="none" stroke="#FFFFFF" stroke-opacity="0.04"/></pattern>')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-labelledby="t d">'
        '<title id="t">%s</title><desc id="d">%s</desc>'
        '<defs>%s<clipPath id="r"><rect width="%d" height="%d" rx="20"/></clipPath></defs>%s'
        '<g clip-path="url(#r)"><rect width="%d" height="%d" fill="%s"/><rect width="%d" height="%d" fill="url(#g)"/>%s</g>'
        "</svg>\n" % (w, h, w, h, escape(title), escape(desc), grid, w, h,
                      ("<style>%s</style>" % style) if style else "", w, h, BG, w, h, body)
    )


def sample_run():
    with open(os.path.join(SKILL, "examples", "sample-run", "arena-data.json"), encoding="utf-8") as fh:
        return json.load(fh)["run"]


# ---------------------------------------------------------------- banner
def banner(static=False):
    """static=True: tanpa animasi, percikan pukulan terlihat (untuk social-preview.png)."""
    W, H = 1280, 640
    run = sample_run()
    final = [e for e in run["events"] if e["t"] == "match"][-1]
    a, b = final["a"], final["b"]
    fa, fb = run["fighters"][a], run["fighters"][b]
    # Keberatan juri pertama yang memukul si kalah (dari final contoh run).
    hit = next(h for h in final["hits"] if (h["by"] == "a") == (final["w"] == a) and h.get("obj"))
    s = 9
    cw, ch = sprite_size("clawd_angry_side", s)
    floor = 470
    lx, rx = 300, W - 300 - cw
    parts = []
    parts.append(pixel_text("CLAUDE CODE SKILL", W / 2, 44, 3, GOLD, anchor="middle"))
    title = "ARGUMENT BATTLE ROYALE"
    parts.append(pixel_text(title, W / 2 + 5, 89, 8, ACCENT, anchor="middle"))
    parts.append(pixel_text(title, W / 2, 84, 8, INK, anchor="middle"))
    parts.append(text(W / 2, 176, "1000 argumen masuk arena. Hanya satu yang keluar sebagai yang paling tahan uji.", 23, SOFT, SANS, "middle"))

    # Kartu petarung (seperti HUD arena) dengan bar ketahanan.
    def card(x, fid, f, anchor_right, bar_cls):
        cx = x
        out = ['<rect x="%g" y="214" width="360" height="74" rx="10" fill="%s" stroke="%s"/>' % (cx, BG2, LINE)]
        out.append(text(cx + 18, 242, "%s · SEED %s" % (fid, f["seed"]), 15, GOLD, MONO, weight="600"))
        out.append(text(cx + 18, 265, clip(f["title"], 38), 15, INK, SANS))
        out.append('<rect x="%g" y="276" width="324" height="6" rx="3" fill="#0B1024"/>' % (cx + 18))
        out.append('<rect class="%s" x="%g" y="276" width="324" height="6" rx="3" fill="%s"/>' % (bar_cls, cx + 18, ACCENT if bar_cls == "hpA" else OK))
        return "".join(out)

    parts.append(card(120, a, fa, False, "hpA"))
    parts.append(card(W - 120 - 360, b, fb, True, "hpB"))
    parts.append(pixel_text("VS", W / 2, 230, 5, INK, anchor="middle"))
    parts.append(text(W / 2, 282, "FINAL · %s" % final["votes"], 15, DIM, MONO, "middle"))

    # Lantai dan dua Clawd.
    parts.append('<rect x="0" y="%d" width="%d" height="4" fill="%s"/>' % (floor, W, PAL["G"]))
    parts.append('<g class="ja">%s</g>' % sprite("clawd_angry_side", lx, floor - ch, s))
    parts.append('<g class="jb">%s</g>' % sprite("clawd_open_side", rx, floor - ch, s, mirror=True))
    bw, bh = sprite_size("burst", 7)
    parts.append('<g class="spark">%s</g>' % sprite("burst", rx - bw / 2 + 10, floor - ch + 30, 7))

    # Ticker juri dengan keberatan yang sebenarnya.
    parts.append('<rect x="120" y="496" width="%d" height="90" rx="10" fill="%s" stroke="%s"/>' % (W - 240, BG2, LINE))
    loser = b if final["w"] == a else a
    parts.append(text(142, 524, "JURI %s · %s  →  %s TERKENA" % (hit["j"], hit["lens"].upper(), loser), 14, GOLD, MONO, weight="600"))
    for k, ln in enumerate(wrap("“%s”" % hit["obj"].replace("\n", " "), 118)[:2]):
        parts.append(text(142, 550 + k * 21, ln, 16, INK, SANS))

    parts.append(text(W / 2, 618, "Pemenang = argumen paling tahan terhadap rubrik pengujian dalam simulasi ini, bukan kebenaran final.", 14, DIM, MONO, "middle"))

    style = (
        "@keyframes lunge{0%,60%,100%{transform:translateX(0)}66%,74%{transform:translateX(34px)}}"
        "@keyframes hurt{0%,64%,82%,100%{transform:translateX(0)}68%{transform:translateX(10px)}72%{transform:translateX(-6px)}76%{transform:translateX(6px)}}"
        "@keyframes spark{0%,63%,79%,100%{opacity:0}65%,77%{opacity:1}}"
        "@keyframes hpB{0%,66%{transform:scaleX(1)}70%,100%{transform:scaleX(.4)}}"
        ".ja{animation:lunge 3.2s steps(1,end) infinite}"
        ".jb{animation:hurt 3.2s steps(1,end) infinite}"
        ".spark{opacity:0;animation:spark 3.2s steps(1,end) infinite}"
        ".hpB{transform-box:fill-box;transform-origin:left;animation:hpB 3.2s steps(1,end) infinite}"
        "@media (prefers-reduced-motion:reduce){.ja,.jb,.spark,.hpB{animation:none}.spark{opacity:1}}"
    )
    if static:
        style = ".spark{opacity:1}"
    return frame(W, H, "".join(parts), "Argument Battle Royale",
                 "Dua Clawd pixel art beradu di arena: final contoh run, %s melawan %s." % (a, b), style)


# ---------------------------------------------------------------- pipeline
ACTS = [
    ("PERSIAPAN", "hat", ["TOPIK", "PEMETAAN", "GENERASI", "DEDUPLIKASI", "VALIDASI", "SEEDING", "BRACKET"],
     ["Petakan ruang argumen, sihir sampai", "1000 petarung, buang duplikat,", "validasi, lalu seed ke bracket."]),
    ("TURNAMEN", "duel", ["ELIMINASI", "DEEP REVIEW", "FINAL 4", "SEMIFINAL", "FINAL"],
     ["Duel eliminasi, panel juri dengan", "7 lensa, dosir Final 4, lalu debat", "semifinal dan final."]),
    ("PUTUSAN", "trophy", ["PEMENANG", "UJI FALSIFIKASI", "LAPORAN"],
     ["Juara diuji falsifikasi; bila gugur,", "runner-up yang diuji berikutnya.", "Laporan + ledger berantai hash."]),
]


def pipeline():
    W, H = 1280, 560
    parts = [pixel_text("PIPELINE 15 TAHAP", 56, 44, 4, INK)]
    parts.append(text(56, 102, "Engine Python (tanpa LLM) jadi wasit: menjadwalkan paket kerja, menghitung ulang putusan, dan mencatat semuanya.", 17, SOFT, SANS))
    col_w, gap, top = 368, 32, 132
    n = 0
    for i, (name, icon, stages, lines) in enumerate(ACTS):
        x = 56 + i * (col_w + gap)
        parts.append('<rect x="%g" y="%g" width="%g" height="388" rx="14" fill="%s" stroke="%s"/>' % (x, top, col_w, BG2, LINE))
        if icon == "duel":
            iw, ih = sprite_size("clawd_angry_side", 2)
            parts.append(sprite("clawd_angry_side", x + col_w - 2 * iw - 22, top + 22, 2))
            parts.append(sprite("clawd_open_side", x + col_w - iw - 18, top + 22, 2, mirror=True))
        else:
            iw, ih = sprite_size(icon, 3)
            parts.append(sprite(icon, x + col_w - iw - 18, top + 18, 3))
        parts.append(pixel_text("BABAK %d" % (i + 1), x + 22, top + 24, 2, DIM))
        parts.append(pixel_text(name, x + 22, top + 46, 4, ACCENT if i == 1 else GOLD if i == 2 else INK))
        y = top + 100
        for st in stages:
            n += 1
            parts.append('<rect x="%g" y="%g" width="%g" height="24" rx="6" fill="#0E1429" stroke="%s"/>' % (x + 22, y, col_w - 44, LINE))
            parts.append(text(x + 34, y + 17, "%02d" % n, 13, OK, MONO, weight="600"))
            parts.append(text(x + 64, y + 17, st, 13, INK, MONO))
            y += 30
        ly = top + 100 + 7 * 30 + 16
        for j, ln in enumerate(lines):
            parts.append(text(x + 22, ly + j * 20, ln, 14, SOFT, SANS))
        if i < 2:
            ax = x + col_w + 4
            parts.append('<path d="M%g %gh20l-8 -8m8 8l-8 8" fill="none" stroke="%s" stroke-width="3"/>' % (ax, top + 194, ACCENT))
    return frame(W, H, "".join(parts), "Pipeline 15 tahap", "Tiga babak pipeline: persiapan, turnamen, putusan.")


# ---------------------------------------------------------------- bracket
def bracket():
    W, H = 1280, 600
    run = sample_run()
    F = run["fighters"]
    cols = run["bracket"]  # 8 besar, semifinal, final
    parts = [pixel_text("CONTOH RUN NYATA", 56, 40, 4, INK)]
    parts.append(text(56, 96, "Topik: “%s” · 16 petarung · 37 paket kerja · verify 11/11" % run["topic"], 17, SOFT, SANS))
    heads = ["8 BESAR · PANEL 3 JURI", "SEMIFINAL · DEBAT + 5 JURI", "FINAL · DEBAT + 5 JURI", "PEMENANG"]
    xs = [56, 374, 692, 1014]
    bw, bh = 282, 64
    top, span = 150, 104
    centers = []
    for c, col in enumerate(cols):
        parts.append(pixel_text(heads[c].split(" · ")[0], xs[c], 126, 2, DIM))
        parts.append(text(xs[c] + pixel_width(heads[c].split(" · ")[0], 2) + 10, 139, heads[c].split(" · ")[1], 12, DIM, MONO))
        step = span * (2 ** c)
        cc = []
        for k, m in enumerate(col):
            cy = top + step / 2 + k * step + (bh / 2) - span / 2
            y = cy - bh / 2
            cc.append(cy)
            parts.append('<rect x="%g" y="%g" width="%g" height="%g" rx="10" fill="%s" stroke="%s"/>' % (xs[c], y, bw, bh, BG2, LINE))
            for r, fid in enumerate((m["a"], m["b"])):
                won = fid == m["winner"]
                ty = y + 26 + r * 26
                parts.append(text(xs[c] + 14, ty, "%2s" % F[fid]["seed"], 12, DIM, MONO))
                parts.append(text(xs[c] + 38, ty, fid, 13, ACCENT if won else DIM, MONO, weight="600" if won else None))
                parts.append(text(xs[c] + 92, ty, clip(F[fid]["title"], 20), 13, INK if won else DIM, SANS))
            parts.append(text(xs[c] + bw - 12, y + 39, m["votes"], 13, GOLD, MONO, "end", "600"))
            if c > 0:
                prev = centers[c - 1]
                for pc in (prev[2 * k], prev[2 * k + 1]):
                    mx = xs[c] - 22
                    parts.append('<path d="M%g %gH%gV%gH%g" fill="none" stroke="%s" stroke-width="2"/>' % (xs[c - 1] + bw, pc, mx, cy, xs[c], LINE))
        centers.append(cc)
    # Pemenang dengan piala.
    champ = run["champion"]
    cy = centers[-1][0]
    parts.append('<path d="M%g %gH%g" fill="none" stroke="%s" stroke-width="2"/>' % (xs[2] + bw + 8, cy, xs[3] - 8, ACCENT))
    tw, th = sprite_size("trophy", 5)
    parts.append(sprite("trophy", xs[3] + 4, cy - th - 26, 5))
    parts.append(pixel_text(champ, xs[3], cy - 14, 4, GOLD))
    for k, ln in enumerate(wrap(F[champ]["title"], 28)[:3]):
        parts.append(text(xs[3], cy + 36 + k * 19, ln, 14, INK, SANS))
    parts.append(pixel_text("UJI FALSIFIKASI", xs[3], cy + 104, 2, DIM))
    parts.append(text(xs[3], cy + 134, run["winner_status"], 13, OK, MONO, weight="600"))
    parts.append(text(56, H - 28, "Semua argumen, putusan, dan uji ditulis model bahasa sebagai worker; ini demonstrasi mesin dan protokol, bukan hasil riset.", 13, DIM, MONO))
    return frame(W, H, "".join(parts), "Bracket contoh run",
                 "Bracket 8 besar sampai final dari contoh run: %s menjadi pemenang." % champ)


def main():
    """Argumen opsional --static FILE: tulis banner tanpa animasi (bahan social-preview.png)."""
    if len(sys.argv) == 3 and sys.argv[1] == "--static":
        with open(sys.argv[2], "w", encoding="utf-8") as fh:
            fh.write(banner(static=True))
        return
    for name, fn in (("banner.svg", banner), ("pipeline.svg", pipeline), ("bracket.svg", bracket)):
        path = os.path.join(HERE, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(fn())
        print("%s  %d byte" % (os.path.relpath(path, ROOT), os.path.getsize(path)))


if __name__ == "__main__":
    main()
