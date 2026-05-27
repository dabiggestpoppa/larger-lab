"""
O2-B8: ConsensusMemory
=======================
Store orchestration outcome history.

Persists consensus decisions for learning and replay.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
MEMORY_DIR = REPO_ROOT / "data" / "consensus"
MEMORY_FILE = MEMORY_DIR / "consensus_history.json"


class ConsensusMemory:
    """
    Persistent storage for consensus decisions.

    Records consensus outcomes for learning, replay, and analysis.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._records: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        """Load records from disk."""
        try:
            if MEMORY_FILE.exists():
                data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
                self._records = data.get("records", [])
        except Exception:
            self._records = []

    def _save(self) -> None:
        """Save records to disk."""
        try:
            MEMORY_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "records": self._records[-1000:],  # Keep last 1000
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            MEMORY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass  # Non-critical

    def record_consensus(self, result: Any) -> None:
        """Record a consensus result."""
        with self._lock:
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_type": result.task_type,
                "complexity": result.complexity,
                "confidence": result.confidence,
                "routing_path": result.routing_path,
                "recommended_model": result.recommended_model,
                "spawn_required": result.spawn_required,
                "agreement_score": result.agreement_score,
                "voter_count": result.voter_count,
            }
            self._records.append(record)
            self._save()

    def get_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent consensus records."""
        with self._lock:
            return self._records[-limit:]

    @property
    def total_records(self) -> int:
        return len(self._records)

    @property
    def avg_agreement(self) -> float:
        if not self._records:
            return 0.0
        scores = [r.get("agreement_score", 0) for r in self._records]
        return round(sum(scores) / len(scores), 3)

    @property
    def task_type_distribution(self) -> dict[str, int]:
        dist: dict[str, int] = {}
        for r in self._records:
            tt = r.get("task_type", "unknown")
            dist[tt] = dist.get(tt, 0) + 1
        return dist

    @property
    def model_distribution(self) -> dict[str, int]:
        dist: dict[str, int] = {}
        for r in self._records:
            m = r.get("recommended_model", "unknown")
            dist[m] = dist.get(m, 0) + 1
        return dist
