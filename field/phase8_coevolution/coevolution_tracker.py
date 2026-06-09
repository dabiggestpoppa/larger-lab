"""
8_coevolution.coevolution_tracker
==================================
Tracks coevolution between operators and the field over time.

Measures how operator behavior and field behavior mutually influence
each other. Detects coevolution patterns such as:
- adaptation: field adapts to operator habits
- learning: operator learns field capabilities
- divergence: operator and field drift apart
- convergence: operator and field align over time

Maintains a coevolution history with scores for each operator-field
pair, tracking the mutual influence trajectory.
"""

import logging
import math
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger("field.coevolution.coevolution_tracker")


class CoevolutionPattern(str, Enum):
    ADAPTATION = "adaptation"
    LEARNING = "learning"
    DIVERGENCE = "divergence"
    CONVERGENCE = "convergence"


class CoevolutionSnapshot(BaseModel):
    """A single coevolution measurement."""
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    operator_id: str
    field_region: str
    operator_behavior_score: float = 0.5  # 0-1, how operator behaves
    field_behavior_score: float = 0.5     # 0-1, how field responds
    mutual_influence: float = 0.0         # -1 to 1, negative=divergence, positive=convergence
    pattern: str = "stable"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CoevolutionTrackerConfig(BaseModel):
    """Configuration for coevolution_tracker."""
    enabled: bool = True
    max_snapshots_per_pair: int = 1000
    influence_window: int = 50
    convergence_threshold: float = 0.6
    divergence_threshold: float = -0.3
    decay_rate: float = 0.99


class CoevolutionTrackerModule:
    """Tracks coevolution between operators and the field."""

    def __init__(self):
        self.config = CoevolutionTrackerConfig()
        self.running = False
        self._lock = Lock()
        # (operator_id, field_region) -> list of snapshots
        self._history: Dict[Tuple[str, str], List[CoevolutionSnapshot]] = defaultdict(list)
        self._current_scores: Dict[Tuple[str, str], float] = {}  # pair -> latest mutual_influence
        self._pattern_counts: Dict[str, int] = defaultdict(int)
        self._total_snapshots: int = 0

    def start(self) -> None:
        self.running = True
        logger.info("CoevolutionTracker started")

    def stop(self) -> None:
        self.running = False
        logger.info("CoevolutionTracker stopped with %d total snapshots", self._total_snapshots)

    def record_snapshot(self, operator_id: str, field_region: str,
                        operator_score: float, field_score: float) -> CoevolutionSnapshot:
        """
        Record a coevolution snapshot for an operator-field pair.

        Computes mutual influence from the alignment between operator
        and field behavior scores, and classifies the coevolution pattern.

        Args:
            operator_id: Unique operator identifier.
            field_region: Field region or capability area.
            operator_score: Operator behavior metric (0-1).
            field_score: Field response metric (0-1).

        Returns:
            The created CoevolutionSnapshot with pattern classification.
        """
        pair = (operator_id, field_region)
        now = datetime.now(timezone.utc).isoformat()

        # Compute mutual influence: positive when both move together
        influence = 1.0 - abs(operator_score - field_score)
        if operator_score < 0.5 and field_score < 0.5:
            # Both low = divergence
            influence = -influence

        # Apply decay to previous score
        with self._lock:
            prev = self._current_scores.get(pair, 0.0)
            decay = self.config.decay_rate
            smoothed_influence = decay * prev + (1 - decay) * influence

            # Classify pattern
            if smoothed_influence >= self.config.convergence_threshold:
                pattern = "convergence"
            elif smoothed_influence <= self.config.divergence_threshold:
                pattern = "divergence"
            elif abs(operator_score - field_score) < 0.15:
                pattern = "adaptation"
            else:
                pattern = "learning"

            snapshot = CoevolutionSnapshot(
                operator_id=operator_id,
                field_region=field_region,
                operator_behavior_score=round(max(0.0, min(1.0, operator_score)), 4),
                field_behavior_score=round(max(0.0, min(1.0, field_score)), 4),
                mutual_influence=round(smoothed_influence, 4),
                pattern=pattern,
                timestamp=now,
            )

            self._history[pair].append(snapshot)
            self._current_scores[pair] = smoothed_influence
            self._pattern_counts[pattern] += 1
            self._total_snapshots += 1

            # Trim history
            if len(self._history[pair]) > self.config.max_snapshots_per_pair:
                self._history[pair] = self._history[pair][-self.config.max_snapshots_per_pair:]

        logger.debug("Coevolution snapshot: %s/%s — influence=%.3f pattern=%s",
                     operator_id, field_region, smoothed_influence, pattern)
        return snapshot

    def get_coevolution_score(self, operator_id: str, field_region: str) -> float:
        """
        Get the current coevolution score for an operator-field pair.

        Returns:
            Mutual influence score from -1.0 (divergent) to 1.0 (convergent).
        """
        pair = (operator_id, field_region)
        with self._lock:
            return self._current_scores.get(pair, 0.0)

    def get_history(self, operator_id: str, field_region: str,
                    limit: int = 100) -> List[Dict]:
        """
        Get coevolution history for an operator-field pair.

        Args:
            operator_id: Operator identifier.
            field_region: Field region.
            limit: Max snapshots to return.

        Returns:
            List of snapshot dicts, most recent first.
        """
        pair = (operator_id, field_region)
        with self._lock:
            snapshots = list(reversed(self._history.get(pair, [])))
            return [s.model_dump() for s in snapshots[:limit]]

    def get_diverging_pairs(self) -> List[Dict[str, Any]]:
        """
        Get all operator-field pairs that are currently diverging.

        Returns:
            List of {operator_id, field_region, influence, pattern}.
        """
        with self._lock:
            result = []
            for pair, score in self._current_scores.items():
                if score <= self.config.divergence_threshold:
                    # Get latest pattern
                    history = self._history.get(pair, [])
                    latest_pattern = history[-1].pattern if history else "unknown"
                    result.append({
                        "operator_id": pair[0],
                        "field_region": pair[1],
                        "influence": round(score, 4),
                        "pattern": latest_pattern,
                    })
            result.sort(key=lambda x: x["influence"])
            return result

    def get_converging_pairs(self) -> List[Dict[str, Any]]:
        """
        Get all operator-field pairs that are currently converging.

        Returns:
            List of {operator_id, field_region, influence, pattern}.
        """
        with self._lock:
            result = []
            for pair, score in self._current_scores.items():
                if score >= self.config.convergence_threshold:
                    history = self._history.get(pair, [])
                    latest_pattern = history[-1].pattern if history else "unknown"
                    result.append({
                        "operator_id": pair[0],
                        "field_region": pair[1],
                        "influence": round(score, 4),
                        "pattern": latest_pattern,
                    })
            result.sort(key=lambda x: x["influence"], reverse=True)
            return result

    def get_trend(self, operator_id: str, field_region: str) -> str:
        """
        Get the coevolution trend direction for a pair.

        Analyzes recent snapshots to determine if coevolution is
        improving, worsening, or stable.

        Returns:
            'improving', 'worsening', or 'stable'.
        """
        pair = (operator_id, field_region)
        with self._lock:
            history = self._history.get(pair, [])
            if len(history) < 5:
                return "stable"

            recent = history[-self.config.influence_window:]
            half = len(recent) // 2
            if half == 0:
                return "stable"

            first_half_avg = sum(s.mutual_influence for s in recent[:half]) / half
            second_half_avg = sum(s.mutual_influence for s in recent[half:]) / (len(recent) - half)

            diff = second_half_avg - first_half_avg
            if diff > 0.05:
                return "improving"
            elif diff < -0.05:
                return "worsening"
            return "stable"

    def get_stats(self) -> Dict[str, Any]:
        """Get coevolution tracker statistics."""
        with self._lock:
            active_pairs = len(self._history)
            diverging = sum(1 for s in self._current_scores.values()
                           if s <= self.config.divergence_threshold)
            converging = sum(1 for s in self._current_scores.values()
                            if s >= self.config.convergence_threshold)
            avg_influence = (
                sum(self._current_scores.values()) / len(self._current_scores)
                if self._current_scores else 0.0
            )
            return {
                "total_snapshots": self._total_snapshots,
                "active_pairs": active_pairs,
                "diverging_pairs": diverging,
                "converging_pairs": converging,
                "stable_pairs": active_pairs - diverging - converging,
                "average_influence": round(avg_influence, 4),
                "pattern_distribution": dict(self._pattern_counts),
            }
