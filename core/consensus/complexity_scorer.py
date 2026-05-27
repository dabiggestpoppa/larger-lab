"""
O2-B4: ComplexityScorer
========================
Estimate operational complexity (4 levels: low, medium, high, critical).
"""

from __future__ import annotations

import re
from typing import Any


# Complexity scoring weights
COMPLEXITY_SIGNALS: dict[str, list[tuple[str, float]]] = {
    "critical": [
        (r"\b(critical|urgent|emergency|production.?outage)\b", 3.0),
        (r"\b(multiple|several|all|every|entire)\b.*\b(fail|error|broken|issue)\b", 2.5),
        (r"\b(architecture|redesign|rewrite|migrat)\b", 2.5),
        (r"\b(data\s*loss|corrupt|security\s*breach)\b", 3.0),
    ],
    "high": [
        (r"\b(complex|advanced|comprehensive|full|complete)\b", 1.5),
        (r"\b(integrat|connect|combin|merge)\b", 1.5),
        (r"\b(optimiz|improve|enhance|upgrade)\b", 1.0),
        (r"\b(refactor|restructure|reorganize)\b", 1.5),
        (r"\b(multi|many|multiple)\b.*\b(file|module|component|service)\b", 1.5),
    ],
    "medium": [
        (r"\b(update|modify|change|add|remove|edit)\b", 0.5),
        (r"\b(config|setup|install|create)\b", 0.5),
        (r"\b(test|verify|validate|check)\b", 0.5),
        (r"\b(review|audit|inspect)\b", 0.5),
    ],
    "low": [
        (r"\b(fix|patch|tweak|adjust)\b", 0.3),
        (r"\b(small|minor|quick|simple)\b", 0.2),
        (r"\b(single|one|just)\b", 0.2),
    ],
}

# Task type base complexity
TASK_TYPE_BASE: dict[str, str] = {
    "coding": "medium",
    "research": "low",
    "architecture": "high",
    "repair": "medium",
    "debugging": "medium",
    "orchestration": "high",
    "visualization": "low",
    "automation": "medium",
    "system_analysis": "low",
    "general": "low",
}


class ComplexityScorer:
    """
    Estimates operational complexity on 4 levels.

    Combines keyword signals with task type base complexity
    and contextual factors.
    """

    def score(
        self, user_input: str, task_type: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Score the complexity of a task.

        Returns:
            {
                "level": str,
                "score": float,  # 0.0-1.0
                "signals": list[str],
                "factors": dict[str, float],
            }
        """
        text = user_input.lower().strip()
        signals: list[str] = []
        factor_scores: dict[str, float] = {}

        # Score each complexity level
        level_scores: dict[str, float] = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for level, patterns in COMPLEXITY_SIGNALS.items():
            for pattern, weight in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    level_scores[level] += weight
                    signals.append(f"{level}: {pattern}")

        # Add task type base
        base = TASK_TYPE_BASE.get(task_type, "low")
        level_scores[base] += 0.5
        signals.append(f"base_type: {task_type}={base}")

        # Context factors
        if context:
            if context.get("active_errors", 0) > 0:
                level_scores["high"] += 0.5
                signals.append("context: active_errors")
            if context.get("concurrent_tasks", 0) > 3:
                level_scores["high"] += 0.3
                signals.append("context: high_concurrency")

        # Determine level
        max_level = max(level_scores, key=level_scores.get)
        raw_score = level_scores[max_level]

        # Normalize to 0-1
        max_possible = 5.0  # Approximate max
        normalized = min(1.0, raw_score / max_possible)

        return {
            "level": max_level,
            "score": round(normalized, 3),
            "signals": signals,
            "factors": {k: round(v, 2) for k, v in level_scores.items()},
        }
