#!/usr/bin/env python3
"""Alat pengembang (opsional): buat GIF pratinjau animasi Clawd untuk dokumentasi.

Membutuhkan Pillow (`pip install pillow`). Engine skill TIDAK membutuhkannya.

  python3 make_preview_gif.py [output.gif] [--scale 6]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import anim  # noqa: E402

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    sys.exit("Pillow belum terpasang: pip install pillow")

BG = (17, 24, 48)
GRID = (26, 34, 62)


def render(frame, scale):
    w, h = anim.CANVAS_W * scale, anim.CANVAS_H * scale
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    for x in range(0, w, 2 * scale):
        d.line([(x, 0), (x, h)], fill=GRID)
    for y in range(0, h, 2 * scale):
        d.line([(0, y), (w, y)], fill=GRID)
    for y, row in enumerate(anim.rasterize(frame)):
        for x, ch in enumerate(row):
            if ch != ".":
                d.rectangle([x * scale, y * scale, (x + 1) * scale - 1, (y + 1) * scale - 1], fill=anim._rgb(anim.PALETTE[ch]))
    return img


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    scale = 6
    if "--scale" in sys.argv:
        scale = int(sys.argv[sys.argv.index("--scale") + 1])
        args = [a for a in args if a != str(scale)]
    out = args[0] if args else "clawd-preview.gif"
    images = []
    for scene, loops in (("wizard", 2), ("battle", 3), ("rocket", 2), ("trophy", 3)):
        frames = anim.frames(scene)
        for _ in range(loops):
            images += [render(f, scale) for f in frames]
    images[0].save(out, save_all=True, append_images=images[1:], duration=int(1000 / anim.FPS), loop=0, optimize=True)
    print(out, len(images), "frame")


if __name__ == "__main__":
    main()
