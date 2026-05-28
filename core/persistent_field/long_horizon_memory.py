"""
O7-B11: LongHorizonMemory
==========================
Multi-week operational memory.

Maintains persistent operational identity across weeks, months,
project evolution. Stores workflow evolution, orchestration evolution,
topology history, adaptation trends, repair history.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
MEMORY_DIR = REPO_ROOT / "data" / "persistent_field" "memory"

logger = logging.getLogger("persistent_field.long_horizon_memory")


@dataclass
class MemoryEntry:
    """A long-horizon memory entry."""
    entry_id: str
    category: str  # workflow, orchestration, topology, adaptation, repair
    data: dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5  # 0.0-1.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class LongHorizonMemory:
    """
    Multi-week operational memory.

    Stores: workflow evolution, orchestration evolution, topology history,
    adaptation trends, repair history.
    """

    MAX_ENTRIES = 1000

    def __init__(self):
        self._lock = threading.Lock()
        self._entries: list[MemoryEntry] = []
        self._load()

    def store(self, category: str, data: dict[str, Any], importance: float = 0.5) -> MemoryEntry:
        """Store a memory entry."""
        with self._lock:
            entry = MemoryEntry(
                entry_id=f"mem_{category}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                category=category,
                data=data,
                importance=importance,
            )
            self._entries.append(entry)

            # Prune if over limit — keep highest importance
            if len(self._entries) > self.MAX_ENTRIES:
                self._entries.sort(key=lambda e: e.importance, reverse=True)
                self._entries = self._entries[:self.MAX_ENTRIES]

            self._persist_entry(entry)
            return entry

    def recall(self, category: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """Recall memory entries."""
        with self._lock:
            entries = self._entries
            if category:
                entries = [e for e in entries if e.category == category]
            # Sort by importance then recency
            entries.sort(key=lambda e: (e.importance, e.timestamp), reverse=True)
            return [
                {
                    "entry_id": e.entry_id,
                    "category": e.category,
                    "data": e.data,
                    "importance": e.importance,
                    "timestamp": e.timestamp,
                }
                for e in entries[:limit]
            ]

    def get_summary(self) -> dict[str, Any]:
        """Get long-horizon memory summary."""
        by_category: dict[str, int] = {}
        for e in self._entries:
            by_category[e.category] = by_category.get(e.category, 0) + 1

        return {
            "total_entries": len(self._entries),
            "by_category": by_category,
            "max_entries": self.MAX_ENTRIES,
            "oldest_entry": self._entries[0].timestamp if self._entries else None,
            "newest_entry": self._entries[-1].timestamp if self._entries else None,
        }

    def _persist_entry(self, entry: MemoryEntry) -> None:
        """Persist a memory entry to disk."""
        try:
            MEMORY_DIR.mkdir(parents=True, exist_ok=True)
            file_path = MEMORY_DIR / f"{entry.entry_id}.json"
            file_path.write_text(json.dumps({
                "entry_id": entry.entry_id,
                "category": entry.category,
                "data": entry.data,
                "importance": entry.importance,
                "timestamp": entry.timestamp,
            }, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to persist memory entry: {e}")

    def _load(self) -> None:
        """Load persisted memory entries."""
        try:
            if MEMORY_DIR.exists():
                for file_path in sorted(MEMORY_DIR.glob("*.json")):
                    try:
                        data = json.loads(file_path.read_text(encoding="utf-8"))
                        self._entries.append(MemoryEntry(**data))
                    except Exception:
                        pass
        except Exception:
            pass
