"""
Hash-chained append-only audit ledger.

Every entry contains the hash of the previous entry, forming a chain.
Modifying any historical entry breaks the chain and is detectable.

This is the tamper-evident guarantee required by the PS:
  'Maintain a complete audit trail of document activities'
  'Prevent unauthorized modifications'
"""
import os
import json
import hashlib
from datetime import datetime


GENESIS_HASH = "0" * 64


def _canonical(obj):
    """Stable JSON serialization for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_entry_hash(index, timestamp, prev_hash, event_type, payload, actor):
    """Compute SHA-256 over the canonical form of the entry's core fields."""
    data = {
        "index": index,
        "timestamp": timestamp,
        "prev_hash": prev_hash,
        "event_type": event_type,
        "payload": payload,
        "actor": actor,
    }
    return hashlib.sha256(_canonical(data)).hexdigest()


class AuditLedger:
    """Append-only, hash-chained audit log persisted as JSON."""

    def __init__(self, path):
        self.path = path
        self.entries = []
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.entries = json.load(f)
        else:
            self.entries = []

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, indent=2)

    def append(self, event_type, payload, actor):
        """Add a new entry to the chain."""
        index = len(self.entries)
        timestamp = datetime.utcnow().isoformat() + "Z"
        prev_hash = self.entries[-1]["hash"] if self.entries else GENESIS_HASH

        entry_hash = compute_entry_hash(
            index, timestamp, prev_hash, event_type, payload, actor
        )

        entry = {
            "index": index,
            "timestamp": timestamp,
            "prev_hash": prev_hash,
            "event_type": event_type,
            "payload": payload,
            "actor": actor,
            "hash": entry_hash,
        }
        self.entries.append(entry)
        self._save()
        return entry

    def verify(self):
        """Recompute the chain and detect any tampering."""
        problems = []
        prev = GENESIS_HASH
        for i, e in enumerate(self.entries):
            if e["index"] != i:
                problems.append("Entry {}: index mismatch ({})".format(i, e["index"]))
            if e["prev_hash"] != prev:
                problems.append("Entry {}: prev_hash mismatch".format(i))
            recomputed = compute_entry_hash(
                e["index"], e["timestamp"], e["prev_hash"],
                e["event_type"], e["payload"], e["actor"],
            )
            if recomputed != e["hash"]:
                problems.append("Entry {}: hash mismatch (tampered)".format(i))
            prev = e["hash"]
        return {
            "intact": len(problems) == 0,
            "entries": len(self.entries),
            "problems": problems,
        }

    def find_by_payload_key(self, key, value):
        for e in self.entries:
            if e.get("payload", {}).get(key) == value:
                return e
        return None

    def all(self):
        return list(self.entries)
