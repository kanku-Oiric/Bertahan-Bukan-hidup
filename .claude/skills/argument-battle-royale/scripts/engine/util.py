"""Utilitas umum: hashing, I/O atomik, RNG deterministik, normalisasi teks."""

import datetime as _dt
import hashlib
import json
import os
import random
import re
import tempfile
import time
import unicodedata


def now_iso():
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_obj(obj):
    return sha256_text(canonical_json(obj))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_write_text(path, text):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".tmp-", suffix=".part")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def atomic_write_json(path, obj):
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False) + "\n")


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path, rows):
    atomic_write_text(path, "".join(canonical_json(r) + "\n" for r in rows))


def rng_for(seed, *context):
    """RNG deterministik yang diturunkan dari seed global + konteks lokal."""
    material = canonical_json([seed] + [str(c) for c in context])
    return random.Random(int(sha256_text(material)[:16], 16))


def default_seed(topic):
    return int(sha256_text(topic.strip())[:8], 16)


def slugify(text, max_len=48):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return (text[:max_len].rstrip("-")) or "topik"


# --------------------------------------------------------------------------
# Normalisasi teks untuk deduplikasi leksikal
# --------------------------------------------------------------------------
_STOPWORDS = set(
    """
    yang dan di ke dari untuk dengan pada adalah ini itu atau dalam tidak bukan juga
    karena sebagai oleh akan dapat bisa lebih harus ada jika maka namun tetapi tapi
    sehingga agar bahwa para suatu sebuah seorang setiap semua hanya sudah telah
    masih saat secara yaitu yakni kita kami mereka ia dia kalau apabila bila hal
    tersebut dia nya pun lah kah
    the a an and or of to in on for with by is are was were be been being this that
    these those it its as at from not no but if then than so such which who whom
    whose what when where why how can could would should may might must do does did
    has have had will shall into onto about over under between also only more most
    """.split()
)


def normalize_tokens(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii").lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


def shingles(tokens):
    uni = set(tokens)
    bi = {tokens[i] + " " + tokens[i + 1] for i in range(len(tokens) - 1)}
    return uni, bi


def jaccard(a, b):
    if not a and not b:
        return 1.0
    inter = len(a & b)
    if inter == 0:
        return 0.0
    return inter / float(len(a) + len(b) - inter)


def word_count(text):
    return len(re.findall(r"\S+", text or ""))


class RunLock:
    """Kunci berbasis file agar hanya satu orkestrator yang mengubah state."""

    STALE_SECONDS = 600

    def __init__(self, path):
        self.path = path
        self.fd = None

    def __enter__(self):
        for _ in range(2):
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, str(os.getpid()).encode())
                return self
            except FileExistsError:
                try:
                    age = time.time() - os.path.getmtime(self.path)
                except FileNotFoundError:
                    continue
                if age > self.STALE_SECONDS:
                    os.unlink(self.path)
                    continue
                raise RuntimeError(
                    "Run sedang dikunci oleh proses lain (%s). Hanya orkestrator yang boleh menjalankan "
                    "'next'. Jika yakin tidak ada proses lain, hapus file tersebut." % self.path
                )
        raise RuntimeError("Tidak dapat memperoleh kunci run: %s" % self.path)

    def __exit__(self, *exc):
        if self.fd is not None:
            os.close(self.fd)
        if os.path.exists(self.path):
            os.unlink(self.path)
        return False
