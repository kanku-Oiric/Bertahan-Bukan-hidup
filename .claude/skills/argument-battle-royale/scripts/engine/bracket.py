"""Seeding dan bracket eliminasi tunggal.

Ukuran bracket = pangkat dua terkecil >= jumlah petarung. Bye diberikan ke
unggulan teratas. Penempatan memakai urutan unggulan standar sehingga unggulan
1 dan 2 hanya dapat bertemu di final.
"""


def next_pow2(n):
    size = 1
    while size < n:
        size *= 2
    return size


def seed_positions(size):
    order = [1]
    while len(order) < size:
        total = len(order) * 2 + 1
        order = [x for s in order for x in (s, total - s)]
    return order


def stage_for(slots, threshold):
    if slots == 2:
        return "final"
    if slots == 4:
        return "semifinal"
    if slots <= threshold:
        return "deep_review"
    return "elimination"


def first_round(seeded_ids, round_no=1):
    """seeded_ids: list id terurut unggulan (indeks 0 = unggulan 1)."""
    n = len(seeded_ids)
    size = next_pow2(n)
    pos = seed_positions(size)
    matches = []
    for i in range(0, size, 2):
        sa, sb = pos[i], pos[i + 1]
        a = seeded_ids[sa - 1] if sa <= n else None
        b = seeded_ids[sb - 1] if sb <= n else None
        if a is None:
            a, b, sa, sb = b, a, sb, sa
        matches.append(
            {
                "match_id": "R%02d-M%04d" % (round_no, i // 2 + 1),
                "a": a,
                "b": b,
                "seed_a": sa,
                "seed_b": sb if b is not None else None,
                "bye": b is None,
            }
        )
    return size, matches


def next_round(prev_matches, seeds, round_no):
    winners = [m["winner"] for m in prev_matches]
    matches = []
    for i in range(0, len(winners), 2):
        a, b = winners[i], winners[i + 1]
        matches.append(
            {
                "match_id": "R%02d-M%04d" % (round_no, i // 2 + 1),
                "a": a,
                "b": b,
                "seed_a": seeds[a],
                "seed_b": seeds[b],
                "bye": False,
            }
        )
    return matches
