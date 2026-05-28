"""
O-4-B10: OperationalScoring
=============================
Quantify orchestration quality.

Scores orchestration decisions and outcomes to enable
data-driven improvement of the observer field.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("core.learning.operational_scoring")


@dataclass
class ScoreEntry:
    """A single operational score."""
    timestamp: str
    dimension: str
    score: float  # 0.0 - 1.0
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


class OperationalScoring:
    """
    Quantifies orchestration quality across multiple dimensions.
    
    Tracks scores for: routing accuracy, context quality,
    execution efficiency, and outcome success.
    """

    DIMENSIONS = [
        "routing_accuracy",
        "context_quality",
        "execution_efficiency",
        "outcome_success",
        "resource_efficiency",
        "continuity_preservation",
    ]

    def __init__(self):
        self._scores: list[ScoreEntry] = []

    def score(
        self,
        dimension: str,
        score: float,
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record a score for a dimension."""
        if dimension not in self.DIMENSIONS:
            logger.warning(f"Unknown scoring dimension: {dimension}")
        entry = ScoreEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            dimension=dimension,
            score=max(0.0, min(1.0, score)),
            weight=weight,
            metadata=metadata or {},
        )
        self._scores.append(entry)

    def get_dimension_score(self, dimension: str) -> float:
        """Get the weighted average score for a dimension."""
        entries = [s for s in self._scores if s.dimension == dimension]
        if not entries:
            return 0.5  # Default neutral score
        total_weight = sum(s.weight for s in entries)
        if total_weight == 0:
            return 0.5
        return sum(s.score * s.weight for s in entries) / total_weight

    def get_overall_score(self) -> float:
        """Get the overall weighted score across all dimensions."""
        if not self._scores:
            return 0.5
        total_weight = sum(s.weight for s in self._scores)
        if total_weight == 0:
            return 0.5
        return sum(s.score * s.weight for s in self._scores) / total_weight

    def get_dimension_breakdown(self) -> dict[str, Any]:
        """Get a breakdown of scores by dimension."""
        return {
            dim: {
                "score": round(self.get_dimension_score(dim), 3),
                "entries": len([s for s in self._scores if s.dimension == dim]),
            }
            for dim in self.DIMENSIONS
        }

    def get_trend(self, dimension: str, window: int = 10) -> list[float]:
        """Get recent score trend for a dimension."""
        entries = [s for s in self._scores if s.dimension == dimension][-window:]
        return [s.score for s in entries]

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_scores": len(self._scores),
            "overall_score": round(self.get_overall_score(), 3),
            "dimensions": self.get_dimension_breakdown(),
        }
