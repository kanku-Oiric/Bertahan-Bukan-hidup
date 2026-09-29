"""Perencanaan generasi: peta ruang argumen -> sel -> slot petarung.

Prinsip alokasi netral: setiap posisi (stance) mendapat kuota setara, sehingga
turnamen, bukan generator, yang menentukan posisi mana yang bertahan.
Di dalam satu posisi, slot disebar merata lintas kerangka (framework) dan
strategi argumentasi agar populasi beragam sejak awal.
"""

from collections import defaultdict

from .util import rng_for


def build_cells(map_obj):
    stances = map_obj["stances"]
    frameworks = map_obj["frameworks"]
    strategies = map_obj["strategies"]
    cells = []
    for s in stances:
        fws = [k for k in frameworks if not k.get("compatible_stances") or s["id"] in k["compatible_stances"]]
        if not fws:
            fws = frameworks
        for k in fws:
            for m in strategies:
                cells.append(
                    {
                        "cell_id": "%s-%s-%s" % (s["id"], k["id"], m["id"]),
                        "stance_id": s["id"],
                        "framework_id": k["id"],
                        "strategy_id": m["id"],
                    }
                )
    return cells


def _split_even(total, keys, rng):
    base, rem = divmod(total, len(keys))
    order = list(keys)
    rng.shuffle(order)
    quota = {k: base for k in keys}
    for k in order[:rem]:
        quota[k] += 1
    return quota


def _interleaved_cells(cells, rng):
    """Urutkan sel satu posisi agar kerangka bergiliran dan strategi bervariasi."""
    by_fw = defaultdict(list)
    for c in cells:
        by_fw[c["framework_id"]].append(c)
    fw_ids = sorted(by_fw)
    rng.shuffle(fw_ids)
    for fid in fw_ids:
        rng.shuffle(by_fw[fid])
    ordered = []
    depth = max(len(v) for v in by_fw.values())
    for i in range(depth):
        for fid in fw_ids:
            if i < len(by_fw[fid]):
                ordered.append(by_fw[fid][i])
    return ordered


def allocate(cells, stance_quota, seed, gen_round, existing_counts=None):
    """Bagi kuota per posisi ke sel. existing_counts: jumlah petarung valid per sel
    (dipakai saat refill agar sel yang kurang terisi diprioritaskan)."""
    existing_counts = existing_counts or {}
    by_stance = defaultdict(list)
    for c in cells:
        by_stance[c["stance_id"]].append(c)
    slots = []
    variant_counter = defaultdict(int)
    for stance_id in sorted(stance_quota):
        n = stance_quota[stance_id]
        if n <= 0 or stance_id not in by_stance:
            continue
        rng = rng_for(seed, "allocate", gen_round, stance_id)
        ordered = _interleaved_cells(by_stance[stance_id], rng)
        if existing_counts:
            ordered.sort(key=lambda c: existing_counts.get(c["cell_id"], 0))
        for i in range(n):
            cell = ordered[i % len(ordered)]
            variant_counter[cell["cell_id"]] += 1
            slots.append(dict(cell, variant=variant_counter[cell["cell_id"]]))
    slots.sort(key=lambda s: (s["stance_id"], s["framework_id"], s["strategy_id"], s["variant"]))
    for i, s in enumerate(slots):
        s["slot_id"] = "G%d-S%04d" % (gen_round, i + 1)
    return slots


def initial_plan(map_obj, population, seed):
    cells = build_cells(map_obj)
    stance_ids = [s["id"] for s in map_obj["stances"]]
    quota = _split_even(population, stance_ids, rng_for(seed, "quota", 0))
    slots = allocate(cells, quota, seed, 0)
    return {"cells": cells, "stance_quota": quota, "slots": slots}


def refill_plan(plan, valid_by_stance, valid_by_cell, target, margin, seed, gen_round):
    quota = plan["stance_quota"]
    deficits = {s: max(0, quota[s] - valid_by_stance.get(s, 0)) for s in quota}
    total_def = sum(deficits.values())
    shortfall = max(0, target - sum(valid_by_stance.values()))
    want = int(round(shortfall * margin + 0.4999))
    if want <= 0 or total_def <= 0:
        return []
    alloc = {}
    remaining = want
    keys = sorted(deficits, key=lambda s: -deficits[s])
    for s in keys:
        alloc[s] = int(want * deficits[s] / float(total_def))
        remaining -= alloc[s]
    for s in keys:
        if remaining <= 0:
            break
        if deficits[s] > 0:
            alloc[s] += 1
            remaining -= 1
    return allocate(plan["cells"], alloc, seed, gen_round, existing_counts=valid_by_cell)
