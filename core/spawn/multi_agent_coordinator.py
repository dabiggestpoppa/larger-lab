"""
O3-B7: MultiAgentCoordinator
=============================
Coordinate multiple agents.

Manages concurrent spawned agents working on related tasks.
Handles task decomposition, result aggregation, and conflict resolution.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("spawn.coordinator")


@dataclass
class CoordinationGroup:
    """A group of agents working on related tasks."""
    group_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task_description: str = ""
    agent_ids: list[str] = field(default_factory=list)
    status: str = "active"  # active, complete, failed
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    results: dict[str, Any] = field(default_factory=dict)


class MultiAgentCoordinator:
    """
    Coordinates multiple spawned agents working on related tasks.
    
    Handles:
    - Task decomposition into parallel subtasks
    - Result aggregation from multiple agents
    - Conflict detection and resolution
    - Coordination group lifecycle
    """

    def __init__(self):
        self._groups: dict[str, CoordinationGroup] = {}

    def create_group(
        self,
        task_description: str,
        agent_ids: list[str] | None = None,
    ) -> CoordinationGroup:
        """Create a new coordination group."""
        group = CoordinationGroup(
            task_description=task_description,
            agent_ids=agent_ids or [],
        )
        self._groups[group.group_id] = group
        logger.info(f"Coordination group created: {group.group_id}")
        return group

    def add_agent(self, group_id: str, agent_id: str) -> bool:
        """Add an agent to a coordination group."""
        group = self._groups.get(group_id)
        if not group:
            return False
        if agent_id not in group.agent_ids:
            group.agent_ids.append(agent_id)
        return True

    def record_result(
        self, group_id: str, agent_id: str, result: dict[str, Any]
    ) -> None:
        """Record a result from an agent in a group."""
        group = self._groups.get(group_id)
        if not group:
            return
        group.results[agent_id] = {
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def check_complete(self, group_id: str) -> bool:
        """Check if all agents in a group have reported results."""
        group = self._groups.get(group_id)
        if not group:
            return False
        return all(aid in group.results for aid in group.agent_ids)

    def aggregate_results(self, group_id: str) -> dict[str, Any]:
        """Aggregate results from all agents in a group."""
        group = self._groups.get(group_id)
        if not group:
            return {"error": "Group not found"}

        results = {aid: data["result"] for aid, data in group.results.items()}
        return {
            "group_id": group.group_id,
            "task": group.task_description,
            "agent_count": len(group.agent_ids),
            "results_collected": len(results),
            "complete": self.check_complete(group_id),
            "results": results,
        }

    def detect_conflicts(self, group_id: str) -> list[dict[str, str]]:
        """Detect conflicting results between agents in a group."""
        group = self._groups.get(group_id)
        if not group or len(group.results) < 2:
            return []

        conflicts = []
        agent_ids = list(group.results.keys())
        for i in range(len(agent_ids)):
            for j in range(i + 1, len(agent_ids)):
                a1, a2 = agent_ids[i], agent_ids[j]
                r1 = group.results[a1]["result"]
                r2 = group.results[a2]["result"]
                if self._results_conflict(r1, r2):
                    conflicts.append({
                        "agent_1": a1,
                        "agent_2": a2,
                        "type": "result_mismatch",
                    })
        return conflicts

    def _results_conflict(self, r1: dict[str, Any], r2: dict[str, Any]) -> bool:
        """Simple conflict detection: check if outputs differ significantly."""
        # Check for contradictory status
        s1 = r1.get("status", "")
        s2 = r2.get("status", "")
        if s1 and s2 and s1 != s2:
            return True
        # Check for contradictory conclusions
        c1 = str(r1.get("conclusion", "")).lower()
        c2 = str(r2.get("conclusion", "")).lower()
        if c1 and c2 and c1 != c2:
            # Simple heuristic: if conclusions are very different
            return True
        return False

    def get_group(self, group_id: str) -> CoordinationGroup | None:
        return self._groups.get(group_id)

    def get_active_groups(self) -> list[CoordinationGroup]:
        return [g for g in self._groups.values() if g.status == "active"]

    def get_stats(self) -> dict[str, Any]:
        total = len(self._groups)
        active = sum(1 for g in self._groups.values() if g.status == "active")
        complete = sum(1 for g in self._groups.values() if g.status == "complete")
        total_agents = sum(len(g.agent_ids) for g in self._groups.values())
        return {
            "total_groups": total,
            "active_groups": active,
            "complete_groups": complete,
            "total_coordinated_agents": total_agents,
        }
