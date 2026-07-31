"""
O-4-B9: WorkflowMemory
========================
Track long-horizon operational continuity.

Stores and retrieves workflow patterns across long time spans,
enabling the system to remember and build upon prior work sessions.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("core.learning.workflow_memory")


@dataclass
class WorkflowEntry:
    """A single workflow memory entry."""
    entry_id: str
    timestamp: str
    task_type: str
    description: str
    outcome: str  # success, partial, failure
    context_keys: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowMemory:
    """
    Long-horizon workflow memory for operational continuity.
    
    Stores workflow outcomes, patterns, and context across sessions.
    Enables the system to remember what worked and what didn't
    over extended time periods.
    """

    def __init__(self, persistence_path: str = ""):
        self._entries: list[WorkflowEntry] = []
        self._persistence_path = persistence_path

    def record_workflow(
        self,
        entry_id: str,
        task_type: str,
        description: str,
        outcome: str,
        context_keys: list[str] | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowEntry:
        """Record a workflow outcome."""
        entry = WorkflowEntry(
            entry_id=entry_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_type=task_type,
            description=description,
            outcome=outcome,
            context_keys=context_keys or [],
            tags=tags or [],
            metadata=metadata or {},
        )
        self._entries.append(entry)
        logger.info(f"Workflow recorded: {entry_id} ({task_type}, {outcome})")
        return entry

    def search(
        self,
        task_type: str | None = None,
        outcome: str | None = None,
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> list[WorkflowEntry]:
        """Search workflow memory with optional filters."""
        results = self._entries
        if task_type:
            results = [r for r in results if r.task_type == task_type]
        if outcome:
            results = [r for r in results if r.outcome == outcome]
        if tags:
            results = [r for r in results if any(t in r.tags for t in tags)]
        return results[-limit:]

    def get_patterns(self) -> dict[str, Any]:
        """Extract stable patterns from workflow history."""
        if not self._entries:
            return {"total": 0, "patterns": []}

        by_type: dict[str, dict[str, int]] = {}
        for entry in self._entries:
            if entry.task_type not in by_type:
                by_type[entry.task_type] = {"success": 0, "partial": 0, "failure": 0, "total": 0}
            by_type[entry.task_type][entry.outcome] = by_type[entry.task_type].get(entry.outcome, 0) + 1
            by_type[entry.task_type]["total"] += 1

        patterns = []
        for task_type, counts in by_type.items():
            total = counts["total"]
            success_rate = counts["success"] / total if total > 0 else 0
            patterns.append({
                "task_type": task_type,
                "total": total,
                "success_rate": round(success_rate, 2),
                "recommendation": "preferred" if success_rate > 0.7 else "avoid" if success_rate < 0.3 else "neutral",
            })

        return {
            "total": len(self._entries),
            "by_type": by_type,
            "patterns": sorted(patterns, key=lambda p: p["success_rate"], reverse=True),
        }

    def get_stats(self) -> dict[str, Any]:
        total = len(self._entries)
        if total == 0:
            return {"total": 0}
        outcomes = {"success": 0, "partial": 0, "failure": 0}
        for e in self._entries:
            outcomes[e.outcome] = outcomes.get(e.outcome, 0) + 1
        return {
            "total": total,
            "outcomes": outcomes,
            "success_rate": round(outcomes["success"] / total, 2),
            "unique_task_types": len(set(e.task_type for e in self._entries)),
        }

    def save(self) -> None:
        if self._persistence_path:
            data = {
                "entries": [
                    {
                        "entry_id": e.entry_id,
                        "timestamp": e.timestamp,
                        "task_type": e.task_type,
                        "description": e.description,
                        "outcome": e.outcome,
                        "context_keys": e.context_keys,
                        "tags": e.tags,
                        "metadata": e.metadata,
                    }
                    for e in self._entries
                ]
            }
            with open(self._persistence_path, "w") as f:
                json.dump(data, f, indent=2)

    def load(self) -> None:
        if self._persistence_path:
            try:
                with open(self._persistence_path, "r") as f:
                    data = json.load(f)
                self._entries = [
                    WorkflowEntry(**e) for e in data.get("entries", [])
                ]
            except FileNotFoundError:
                pass
