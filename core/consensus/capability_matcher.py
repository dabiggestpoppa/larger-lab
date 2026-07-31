"""
O2-B7: CapabilityMatcher
=========================
Determine required capabilities for a task.

Matches task requirements against available observer capabilities.
"""

from __future__ import annotations

from typing import Any


# Observer capabilities registry
OBSERVER_CAPABILITIES: dict[str, list[str]] = {
    "planner": [
        "task_decomposition", "goal_setting", "strategy",
        "prioritization", "dependency_analysis", "planning",
    ],
    "execution": [
        "code_generation", "file_operations", "command_execution",
        "testing", "deployment", "automation",
    ],
    "memory": [
        "context_retrieval", "pattern_recognition", "knowledge_storage",
        "continuity_tracking", "history_analysis",
    ],
    "repair": [
        "error_detection", "self_healing", "consistency_checking",
        "rollback", "recovery", "diagnostics",
    ],
}

# Task type -> required capabilities mapping
TASK_CAPABILITIES: dict[str, list[str]] = {
    "coding": ["code_generation", "file_operations", "testing", "planning"],
    "research": ["context_retrieval", "pattern_recognition", "knowledge_storage"],
    "architecture": ["planning", "strategy", "dependency_analysis", "goal_setting"],
    "repair": ["error_detection", "self_healing", "diagnostics", "recovery"],
    "debugging": ["error_detection", "diagnostics", "context_retrieval"],
    "orchestration": ["task_decomposition", "prioritization", "planning", "automation"],
    "visualization": ["code_generation", "file_operations"],
    "automation": ["command_execution", "deployment", "automation", "planning"],
    "system_analysis": ["context_retrieval", "pattern_recognition", "continuity_tracking"],
    "general": ["planning"],
}


class CapabilityMatcher:
    """
    Matches task requirements against available observer capabilities.
    """

    def match(
        self,
        task_type: str,
        complexity: str,
        routing_path: list[str],
        available_observers: dict[str, list[str]] | None = None,
    ) -> dict[str, Any]:
        """
        Determine required capabilities and match against observers.

        Returns:
            {
                "required": list[str],
                "available": list[str],
                "gaps": list[str],
                "coverage": float,  # 0.0-1.0
                "requires_multi_agent": bool,
                "observer_assignments": dict[str, list[str]],
            }
        """
        if available_observers is None:
            available_observers = OBSERVER_CAPABILITIES

        required = TASK_CAPABILITIES.get(task_type, ["planning"])

        # Gather all available capabilities
        all_available: set[str] = set()
        for caps in available_observers.values():
            all_available.update(caps)

        # Find gaps
        gaps = [cap for cap in required if cap not in all_available]
        covered = [cap for cap in required if cap in all_available]

        coverage = len(covered) / len(required) if required else 1.0

        # Assign capabilities to observers
        assignments: dict[str, list[str]] = {}
        for observer_id in routing_path:
            obs_caps = available_observers.get(observer_id, [])
            matched = [c for c in required if c in obs_caps]
            if matched:
                assignments[observer_id] = matched

        # Multi-agent if coverage < 1.0 or complexity is high
        requires_multi = len(gaps) > 0 or complexity in ("critical", "high")

        return {
            "required": required,
            "available": list(all_available),
            "gaps": gaps,
            "coverage": round(coverage, 2),
            "requires_multi_agent": requires_multi,
            "observer_assignments": assignments,
        }
