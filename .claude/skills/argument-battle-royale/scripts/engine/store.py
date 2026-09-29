"""Penyimpanan run: state (checkpoint), ledger berantai-hash, registri paket, petarung."""

import os
import shutil

from . import config as C
from .util import (
    RunLock,
    atomic_write_json,
    canonical_json,
    hash_obj,
    now_iso,
    read_json,
    read_jsonl,
    sha256_file,
    sha256_text,
    write_jsonl,
)

GENESIS = "0" * 64


class Run:
    """Satu direktori run. Semua perubahan state melewati kelas ini."""

    def __init__(self, run_dir):
        self.dir = os.path.abspath(run_dir)
        self._state = None

    # ------------------------------------------------------------------ paths
    def path(self, *parts):
        return os.path.join(self.dir, *parts)

    @property
    def state_path(self):
        return self.path("state.json")

    @property
    def ledger_path(self):
        return self.path("ledger.jsonl")

    def exists(self):
        return os.path.exists(self.state_path)

    def lock(self):
        return RunLock(self.path(".lock"))

    # ------------------------------------------------------------------ state
    @property
    def state(self):
        if self._state is None:
            self._state = read_json(self.state_path)
            if self._state is None:
                raise FileNotFoundError("Tidak ada run di %s (state.json tidak ditemukan)." % self.dir)
        return self._state

    def save_state(self):
        self._state["updated_at"] = now_iso()
        atomic_write_json(self.state_path, self._state)

    @property
    def cfg(self):
        return self.state["config"]

    def create(self, config):
        os.makedirs(self.dir, exist_ok=True)
        for sub in ("packets", "rounds"):
            os.makedirs(self.path(sub), exist_ok=True)
        self._state = {
            "schema_version": C.SCHEMA_VERSION,
            "engine_version": C.ENGINE_VERSION,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "config": config,
            "phase": "init",
            "phase_history": [],
            "packet_seq": 0,
            "packets": {},
            "generation_round": 0,
            "dedup_round_done": -1,
            "anchors": [],
            "current_round": 0,
            "blocked": None,
            "flags": [],
        }
        self.save_state()
        self.log("run_initialized", {"config": config})

    def set_phase(self, phase, note=None):
        st = self.state
        if st["phase"] == phase:
            return
        st["phase_history"].append({"from": st["phase"], "to": phase, "at": now_iso(), "note": note})
        st["phase"] = phase
        self.save_state()
        self.log("phase_changed", {"to": phase, "note": note})

    def flag(self, code, detail):
        entry = {"code": code, "detail": detail, "at": now_iso()}
        self.state["flags"].append(entry)
        self.log("flag", entry)

    # ----------------------------------------------------------------- ledger
    def _last_hash(self):
        rows = read_jsonl(self.ledger_path)
        return (rows[-1]["hash"], rows[-1]["seq"]) if rows else (GENESIS, -1)

    def log(self, event, data):
        prev, seq = self._last_hash()
        entry = {"seq": seq + 1, "ts": now_iso(), "event": event, "data": data, "prev": prev}
        entry["hash"] = sha256_text(prev + canonical_json({k: entry[k] for k in ("seq", "ts", "event", "data", "prev")}))
        with open(self.ledger_path, "a", encoding="utf-8") as fh:
            fh.write(canonical_json(entry) + "\n")
        return entry

    # ---------------------------------------------------------------- packets
    def packet_dir(self, packet_id):
        return self.path("packets", packet_id)

    def packet_output_path(self, packet_id):
        return self.path("packets", packet_id, "output.json")

    def packet_prompt_path(self, packet_id):
        return self.path("packets", packet_id, "packet.md")

    def new_packet_id(self, ptype):
        self.state["packet_seq"] += 1
        return "P%04d-%s" % (self.state["packet_seq"], ptype)

    def register_packet(self, ptype, stage_key, payload, prompt_text, meta=None):
        """Mendaftarkan paket kerja baru. `payload` = data input yang di-hash."""
        pid = self.new_packet_id(ptype)
        input_hash = hash_obj(payload)
        pdir = self.packet_dir(pid)
        os.makedirs(pdir, exist_ok=True)
        prompt_text = prompt_text.replace("{{PACKET_ID}}", pid).replace("{{INPUT_HASH}}", input_hash)
        with open(self.packet_prompt_path(pid), "w", encoding="utf-8") as fh:
            fh.write(prompt_text)
        record = {
            "id": pid,
            "type": ptype,
            "stage": stage_key,
            "status": "pending",
            "attempts": 0,
            "input_hash": input_hash,
            "created_at": now_iso(),
            "meta": meta or {},
            "errors": [],
        }
        atomic_write_json(self.path("packets", pid, "meta.json"), {"record": record, "payload": payload})
        self.state["packets"][pid] = record
        self.log("packet_created", {"id": pid, "type": ptype, "stage": stage_key, "input_hash": input_hash})
        return pid

    def packet_payload(self, packet_id):
        return read_json(self.path("packets", packet_id, "meta.json"))["payload"]

    def packets_for(self, stage_key):
        return [p for p in self.state["packets"].values() if p["stage"] == stage_key]

    def packet_output(self, packet_id):
        return read_json(self.packet_output_path(packet_id))

    def mark_packet_done(self, packet_id):
        rec = self.state["packets"][packet_id]
        rec["status"] = "done"
        rec["done_at"] = now_iso()
        rec["output_sha256"] = sha256_file(self.packet_output_path(packet_id))
        self.log("packet_ingested", {"id": packet_id, "output_sha256": rec["output_sha256"]})

    def reject_packet_output(self, packet_id, errors):
        rec = self.state["packets"][packet_id]
        rec["attempts"] += 1
        rec["errors"] = errors[:30]
        src = self.packet_output_path(packet_id)
        dst = self.path("packets", packet_id, "output.rejected.%d.json" % rec["attempts"])
        shutil.move(src, dst)
        self.log("packet_rejected", {"id": packet_id, "attempt": rec["attempts"], "errors": errors[:10]})
        if rec["attempts"] >= C.MAX_ATTEMPTS:
            self.abandon_packet(packet_id, "gagal validasi %d kali" % rec["attempts"])

    def abandon_packet(self, packet_id, reason):
        rec = self.state["packets"][packet_id]
        rec["status"] = "abandoned"
        rec["abandon_reason"] = reason
        self.log("packet_abandoned", {"id": packet_id, "reason": reason})

    # --------------------------------------------------------------- fighters
    @property
    def fighters_path(self):
        return self.path("fighters.jsonl")

    def load_fighters(self):
        return {f["id"]: f for f in read_jsonl(self.fighters_path)}

    def append_fighters(self, new_fighters):
        rows = read_jsonl(self.fighters_path) + new_fighters
        write_jsonl(self.fighters_path, rows)

    def load_population(self):
        return read_json(self.path("population.json"), {})

    def save_population(self, pop):
        atomic_write_json(self.path("population.json"), pop)

    # ------------------------------------------------------------------ misc
    def load(self, name, default=None):
        return read_json(self.path(name), default)

    def save(self, name, obj):
        atomic_write_json(self.path(name), obj)

    def round_path(self, rnd):
        return self.path("rounds", "R%02d.json" % rnd)

    def load_round(self, rnd):
        return read_json(self.round_path(rnd))

    def save_round(self, rnd, obj):
        atomic_write_json(self.round_path(rnd), obj)

    def file_hash(self, name):
        p = self.path(name)
        return sha256_file(p) if os.path.exists(p) else None
