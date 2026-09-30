#!/usr/bin/env python3
"""Bangun argument-battle-royale.zip yang siap diunggah ke Claude.ai.

    python3 .github/scripts/package_skill.py [FOLDER_OUTPUT]   (default: dist)

Claude.ai hanya menerima zip yang SKILL.md-nya ada di folder teratas
(argument-battle-royale/SKILL.md). Zip "Download ZIP" dari GitHub berisi
seluruh repo, jadi SKILL.md terkubur beberapa folder di dalamnya dan ditolak.

Contoh run lengkap dan GIF tidak ikut dipaketkan agar unggahan tetap kecil;
skill tidak membutuhkannya untuk berjalan.
"""

import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NAME = "argument-battle-royale"
SKILL = os.path.join(ROOT, ".claude", "skills", NAME)
SKIP_DIRS = {"__pycache__", "sample-run"}
SKIP_EXT = {".gif", ".pyc"}
STAMP = (2020, 1, 1, 0, 0, 0)  # tanggal tetap: isi sama menghasilkan zip yang sama


def files():
    for dirpath, dirnames, filenames in os.walk(SKILL):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if os.path.splitext(name)[1] not in SKIP_EXT:
                yield os.path.join(dirpath, name)


def check_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---" or "---" not in [ln.strip() for ln in lines[1:]]:
        sys.exit("SKILL.md tidak diawali frontmatter YAML (---).")
    head = lines[1:[ln.strip() for ln in lines[1:]].index("---") + 1]
    fields = dict(ln.split(":", 1) for ln in head if ":" in ln)
    if fields.get("name", "").strip() != NAME or not fields.get("description", "").strip():
        sys.exit("Frontmatter SKILL.md harus memuat name: %s dan description." % NAME)


def main():
    out_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "dist")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, NAME + ".zip")
    with open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8") as fh:
        check_frontmatter(fh.read())
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for path in files():
            info = zipfile.ZipInfo(NAME + "/" + os.path.relpath(path, SKILL).replace(os.sep, "/"), STAMP)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(path, "rb") as fh:
                z.writestr(info, fh.read())
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
    if NAME + "/SKILL.md" not in names:
        sys.exit("SKILL.md tidak berada di folder teratas zip.")
    print("%s  %d file, %d KB" % (os.path.relpath(out, os.getcwd()), len(names), os.path.getsize(out) // 1024))


if __name__ == "__main__":
    main()
