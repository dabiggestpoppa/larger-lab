"""
O2-B10: ConsensusReplay
=========================
Replay observer decisions from history.

Enables analysis and debugging of past consensus decisions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.consensus.consensus_memory import ConsensusMemory


class ConsensusReplay:
    """
    Replays observer decisions from consensus history.

    Useful for debugging, analysis, and testing.
    """

    def __init__(self, memory: ConsensusMemory | None = None):
        self.memory = memory or ConsensusMemory()

    def replay(
        self,
        task_type: str | None = None,
        complexity: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Replay consensus decisions matching criteria.

        Args:
            task_type: Filter by task type (optional)
            complexity: Filter by complexity (optional)
            limit: Maximum records to return

        Returns:
            List of matching consensus records
        """
        records = self.memory.get_recent(limit=limit * 3)  # Get extra for filtering

        filtered = []
        for record in records:
            if task_type and record.get("task_type") != task_type:
                continue
            if complexity and record.get("complexity") != complexity:
                continue
            filtered.append(record)
            if len(filtered) >= limit:
                break

        return filtered

    def get_decision_chain(self, timestamp: str) -> list[dict[str, Any]]:
        """
        Get the full decision chain for a specific timestamp.

        Returns all records within 5 seconds of the given timestamp.
        """
        records = self.memory.get_recent(limit=100)
        matching = [r for r in records if r.get("timestamp") == timestamp]

        if not matching:
            return []

        # Get records within 5 seconds
        target = matching[0]
        target_time = target.get("timestamp", "")
        chain = [r for r in records if abs(
            self._time_diff(r.get("timestamp", ""), target_time)
        ) < 5.0]

        return sorted(chain, key=lambda r: r.get("timestamp", ""))

    def _time_diff(self, t1: str, t2: str) -> float:
        """Calculate time difference in seconds."""
        try:
            dt1 = datetime.fromisoformat(t1)
            dt2 = datetime.fromisoformat(t2)
            return abs((dt1 - dt2).total_seconds())
        except Exception:
            return float("inf")

    def get_stats(self) -> dict[str, Any]:
        """Get replay statistics."""
        records = self.memory.get_recent(limit=1000)
        return {
            "total_records": len(records),
            "task_types": list(set(r.get("task_type", "unknown") for r in records)),
            "complexities": list(set(r.get("complexity", "unknown") for r in records)),
            "avg_agreement": self.memory.avg_agreement,
            "task_distribution": self.memory.task_type_distribution,
        }
