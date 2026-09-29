"""Deduplikasi petarung.

Tahap 1 (deterministik): kemiripan leksikal = 0.5*Jaccard(unigram) +
0.5*Jaccard(bigram) atas tesis, premis, inferensi, dan kesimpulan setelah
normalisasi (huruf kecil, tanpa aksen/tanda baca/kata umum).
  - skor >= DEDUP_AUTO_THRESHOLD   -> duplikat otomatis
  - skor di antara ambang review   -> kandidat review semantik (LLM), bila mode mengizinkan
Tahap 2 (opsional): paket `dedup_review` memutuskan apakah dua argumen memiliki
inti yang sama (tesis + premis kunci + pola inferensi).
Kluster dibentuk dengan union-find; wakil kluster = petarung generasi paling
awal, lalu paling lengkap, lalu id terkecil.
"""

from . import config as C
from .util import jaccard, normalize_tokens, shingles, word_count
from .validate import fighter_text


def _core_text(f):
    parts = [f["thesis"], f["conclusion"], f["inference"]]
    parts += [p["text"] for p in f["premises"]]
    return " ".join(parts)


def signatures(fighters):
    sig = {}
    for fid, f in fighters.items():
        toks = normalize_tokens(_core_text(f))
        sig[fid] = shingles(toks)
    return sig


def similarity(sa, sb):
    return 0.5 * jaccard(sa[0], sb[0]) + 0.5 * jaccard(sa[1], sb[1])


def candidate_pairs(new_ids, pool_ids, fighters):
    """Bandingkan setiap petarung baru dengan semua petarung pool (unik) + sesama baru."""
    ids = sorted(set(new_ids) | set(pool_ids))
    sig = signatures({i: fighters[i] for i in ids})
    new_set = set(new_ids)
    auto, review = [], []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if a not in new_set and b not in new_set:
                continue
            sa, sb = sig[a], sig[b]
            la, lb = len(sa[0]), len(sb[0])
            if la and lb and min(la, lb) / float(max(la, lb)) < 0.3:
                continue
            s = similarity(sa, sb)
            if s >= C.DEDUP_AUTO_THRESHOLD:
                auto.append((a, b, round(s, 4)))
            elif s >= C.DEDUP_REVIEW_THRESHOLD:
                review.append((a, b, round(s, 4)))
    review.sort(key=lambda t: (-t[2], t[0], t[1]))
    overflow = review[C.DEDUP_MAX_REVIEW_PAIRS:]
    return auto, review[: C.DEDUP_MAX_REVIEW_PAIRS], overflow


def completeness(f):
    return (word_count(fighter_text(f)), len(f["premises"]))


def resolve_clusters(pairs, fighters, protected=frozenset()):
    """`protected`: petarung gelombang sebelumnya yang sudah dinilai; mereka tidak
    pernah ditandai duplikat — anggota baru di kluster mereka yang dihapus."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    groups = {}
    for x in list(parent):
        groups.setdefault(find(x), []).append(x)
    mapping = {}
    clusters = []
    for members in groups.values():
        if len(members) < 2:
            continue
        kept = sorted(m for m in members if m in protected)
        if kept:
            rep = kept[0]
        else:
            rep = sorted(
                members,
                key=lambda i: (fighters[i]["generation_round"], -completeness(fighters[i])[0], -completeness(fighters[i])[1], i),
            )[0]
            kept = [rep]
        clusters.append({"representative": rep, "members": sorted(members)})
        for m in members:
            if m not in kept:
                mapping[m] = rep
    clusters.sort(key=lambda c: c["representative"])
    return mapping, clusters
