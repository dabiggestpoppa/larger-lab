"""
O3-B9: SpawnReplay
===================
Replay spawned agent behavior.

Records and replays spawn decisions for debugging, testing,
and consensus replay (O2-B10).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("spawn.replay")


@dataclass
class SpawnRecord:
    """Record of a spawn decision and its outcome."""
    record_id: str
    timestamp: str
    task_type: str
    complexity: str
    model: str
    context_keys: list[str]
    tools: list[str]
    consensus_confidence: float = 0.0
    status: str = "pending"
    duration_seconds: float = 0.0
    tokens_used: int = 0
    error: str | None = None


class SpawnReplay:
    """
    Records and replays spawn decisions.
    
    Enables debugging of routing decisions, testing of spawn
    configurations, and feeds into consensus replay.
    """

    def __init__(self):
        self._records: list[SpawnRecord] = []

    def record_spawn(
        self,
        record_id: str,
        task_type: str,
        complexity: str,
        model: str,
        context_keys: list[str],
        tools: list[str],
        consensus_confidence: float = 0.0,
    ) -> SpawnRecord:
        """Record a spawn decision."""
        record = SpawnRecord(
            record_id=record_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_type=task_type,
            complexity=complexity,
            model=model,
            context_keys=context_keys,
            tools=tools,
            consensus_confidence=consensus_confidence,
        )
        self._records.append(record)
        return record

    def update_record(
        self, record_id: str, status: str, **kwargs: Any
    ) -> bool:
        """Update a spawn record with outcome data."""
        for r in self._records:
            if r.record_id == record_id:
                r.status = status
                for k, v in kwargs.items():
                    if hasattr(r, k):
                        setattr(r, k, v)
                return True
        return False

    def replay(self, record_id: str) -> dict[str, Any]:
        """Replay a spawn decision — returns the original decision context."""
        for r in self._records:
            if r.record_id == record_id:
                return {
                    "record_id": r.record_id,
                    "timestamp": r.timestamp,
                    "task_type": r.task_type,
                    "complexity": r.complexity,
                    "model": r.model,
                    "context_keys": r.context_keys,
                    "tools": r.tools,
                    "consensus_confidence": r.consensus_confidence,
                    "outcome": {
                        "status": r.status,
                        "duration_seconds": r.duration_seconds,
                        "tokens_used": r.tokens_used,
                        "error": r.error,
                    },
                }
        return {"error": "Record not found"}

    def replay_all(
        self, task_type: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        """Replay all matching spawn records."""
        records = self._records
        if task_type:
            records = [r for r in records if r.task_type == task_type]
        if status:
            records = [r for r in records if r.status == status]
        return [self.replay(r.record_id) for r in records]

    def get_stats(self) -> dict[str, Any]:
        """Get replay statistics."""
        total = len(self._records)
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_model: dict[str, int] = {}
        for r in self._records:
            by_type[r.task_type] = by_type.get(r.task_type, 0) + 1
            by_status[r.status] = by_status.get(r.status, 0) + 1
            by_model[r.model] = by_model.get(r.model, 0) + 1

        return {
            "total_records": total,
            "by_type": by_type,
            "by_status": by_status,
            "by_model": by_model,
        }
