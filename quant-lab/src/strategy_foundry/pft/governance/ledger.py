"""Append-only data usage ledger.

Every research-relevant data access records a ledger entry. Entries are
never modified or deleted once written. Blocked accesses are recorded
with authorized=false so the ledger itself proves protection worked.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .partitions import PARTITION_CLASSES, PartitionGuard, ProtectedPartitionError

LEDGER_ENTRY_FIELDS = (
    "entry_id",
    "dataset_id",
    "path",
    "requested_range",
    "purpose",
    "experiment_id",
    "agent",
    "timestamp",
    "partition_class",
    "authorized",
    "blocked",
    "note",
)


class LedgerError(RuntimeError):
    pass


class DataUsageLedger:
    """Append-only JSONL ledger of data accesses."""

    def __init__(self, path: Path, guard: Optional[PartitionGuard] = None) -> None:
        self._path = Path(path)
        self._guard = guard if guard is not None else PartitionGuard()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[dict] = []
        if self._path.exists():
            for line in self._path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                self._validate_entry(entry)
                self._entries.append(entry)

    @staticmethod
    def _validate_entry(entry: dict) -> None:
        if not isinstance(entry, dict):
            raise LedgerError("ledger entry must be an object")
        missing = [f for f in LEDGER_ENTRY_FIELDS if f not in entry]
        if missing:
            raise LedgerError(f"ledger entry missing fields: {missing}")
        if entry["partition_class"] not in PARTITION_CLASSES:
            raise LedgerError(
                f"ledger entry has invalid partition class {entry['partition_class']!r}"
            )
        if not isinstance(entry["authorized"], bool) or not isinstance(entry["blocked"], bool):
            raise LedgerError("ledger 'authorized' and 'blocked' must be boolean")

    def _append(self, entry: dict) -> None:
        self._validate_entry(entry)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")
        self._entries.append(entry)

    def record(
        self,
        dataset_id: str,
        path: str,
        purpose: str,
        experiment_id: str,
        partition_class: str,
        requested_range: str = "",
        agent: str = "unknown",
        note: str = "",
        entry_id: Optional[str] = None,
    ) -> dict:
        """Record a data access. Applies the partition guard; blocked access is
        still recorded, then ProtectedPartitionError is raised."""
        authorized = self._guard.is_allowed(partition_class)
        entry = {
            "entry_id": entry_id or f"LEDGER-{uuid.uuid4().hex[:12]}",
            "dataset_id": dataset_id,
            "path": path,
            "requested_range": requested_range,
            "purpose": purpose,
            "experiment_id": experiment_id,
            "agent": agent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "partition_class": partition_class,
            "authorized": authorized,
            "blocked": not authorized,
            "note": note,
        }
        self._append(entry)
        if not authorized:
            raise ProtectedPartitionError(
                f"data access to {partition_class!r} partition blocked and recorded "
                f"(entry {entry['entry_id']})"
            )
        return entry

    def entries(self) -> list:
        return [dict(e) for e in self._entries]

    def blocked_entries(self) -> list:
        return [e for e in self._entries if e["blocked"]]

    def to_json(self) -> dict:
        return {
            "schema_version": "1.0",
            "immutable": True,
            "entry_count": len(self._entries),
            "entries": self._entries,
        }
