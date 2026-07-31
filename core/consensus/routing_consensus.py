"""
O2-B3: RoutingConsensus
========================
Determine best orchestration path through the observer field.

Decides which observers should handle a task and in what order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Observer routing map: which observers handle which task types
OBSERVER_ROUTING: dict[str, list[str]] = {
    "coding": ["planner", "execution", "repair"],
    "research": ["planner", "memory"],
    "architecture": ["planner", "memory", "execution"],
    "repair": ["repair", "planner", "execution"],
    "debugging": ["repair", "planner", "memory"],
    "orchestration": ["planner", "execution", "memory", "repair"],
    "visualization": ["planner", "execution"],
    "automation": ["execution", "planner"],
    "system_analysis": ["planner", "memory", "repair"],
    "general": ["planner"],
}

# Complexity-based routing adjustments
COMPLEXITY_OVERRIDES: dict[str, dict[str, list[str]]] = {
    "critical": {
        "coding": ["planner", "repair", "execution", "memory"],
        "orchestration": ["planner", "repair", "execution", "memory"],
    },
    "high": {
        "coding": ["planner", "repair", "execution"],
        "architecture": ["planner", "memory", "repair", "execution"],
    },
}


@dataclass
class RoutingDecision:
    """Routing decision for a task."""
    path: list[str]
    primary_observer: str
    fallback_observers: list[str]
    strategy: str  # "direct", "cascade", "parallel", "consensus"
    estimated_steps: int


class RoutingConsensus:
    """
    Determines the best orchestration path for a task.

    Uses task type, complexity, and current observer availability
    to route tasks through the observer field.
    """

    def __init__(self):
        self._routing_history: list[dict[str, Any]] = []

    def determine_path(
        self,
        task_type: str,
        complexity: str,
        signals: list[dict[str, Any]] | None = None,
        observer_availability: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        """
        Determine the best routing path for a task.

        Returns:
            {
                "path": list[str],
                "primary": str,
                "fallbacks": list[str],
                "strategy": str,
                "estimated_steps": int,
            }
        """
        # Get base routing
        base_path = OBSERVER_ROUTING.get(task_type, ["planner"])

        # Apply complexity overrides
        if complexity in COMPLEXITY_OVERRIDES:
            overrides = COMPLEXITY_OVERRIDES[complexity]
            if task_type in overrides:
                base_path = overrides[task_type]

        # Filter by availability
        if observer_availability:
            available_path = [
                obs for obs in base_path
                if observer_availability.get(obs, True)
            ]
            if available_path:
                base_path = available_path

        # Determine strategy
        strategy = self._determine_strategy(task_type, complexity, base_path)

        # Build result
        result = {
            "path": base_path,
            "primary": base_path[0] if base_path else "planner",
            "fallbacks": base_path[1:] if len(base_path) > 1 else [],
            "strategy": strategy,
            "estimated_steps": len(base_path),
        }

        self._routing_history.append({
            "task_type": task_type,
            "complexity": complexity,
            "result": result,
        })

        return result

    def _determine_strategy(
        self, task_type: str, complexity: str, path: list[str]
    ) -> str:
        """Determine routing strategy."""
        if len(path) == 1:
            return "direct"
        if complexity in ("critical", "high"):
            return "cascade"
        if task_type in ("orchestration", "automation"):
            return "parallel"
        if len(path) >= 3:
            return "consensus"
        return "cascade"

    def get_routing_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent routing history."""
        return self._routing_history[-limit:]
