"""Append-only, hash-chained audit log.

Every registry mutation and verification decision appends one JSONL record.
Each record embeds the hash of the previous record, so any edit, deletion, or
reordering of history is detectable with `verify_chain`. Hash chaining makes
tampering *detectable*; it does not replace secure storage (guide section 26.11).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

GENESIS_HASH = "0" * 64


def _canonical(record: dict) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _record_hash(record: dict) -> str:
    body = {k: v for k, v in record.items() if k != "record_hash"}
    return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()


class AuditLog:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        last = GENESIS_HASH
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        last = json.loads(line).get("record_hash", last)
        return last

    def append(self, actor: str, action: str, payload: dict[str, Any]) -> dict:
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "action": action,
            "payload": payload,
            "previous_hash": self._last_hash(),
        }
        record["record_hash"] = _record_hash(record)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(_canonical(record) + "\n")
        return record

    def records(self) -> Iterator[dict]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def verify_chain(self) -> tuple[bool, list[str]]:
        """Check hash continuity and per-record integrity."""
        problems: list[str] = []
        previous = GENESIS_HASH
        for index, record in enumerate(self.records()):
            expected = _record_hash(record)
            if record.get("record_hash") != expected:
                problems.append(f"record {index}: content hash mismatch (tampered or corrupted)")
            if record.get("previous_hash") != previous:
                problems.append(f"record {index}: chain broken (previous_hash mismatch)")
            previous = record.get("record_hash", expected)
        return (not problems, problems)
