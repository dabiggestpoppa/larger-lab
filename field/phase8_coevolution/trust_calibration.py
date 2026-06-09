"""
8_coevolution.trust_calibration
================================
Dynamic trust calibration system for field operators and agents.

Maintains trust scores for each operator/agent based on their
historical accuracy, consistency, and feedback. Trust scores
influence autonomous operation permissions and suggestion weighting.

Trust dimensions:
- accuracy: correctness of outputs and decisions
- consistency: stability of behavior over time
- responsiveness: timeliness of actions and feedback
- recovery: ability to recover from errors

Trust is dynamic — it increases with good outcomes and decreases
with errors, with configurable decay and floor/ceiling values.
"""

import logging
import math
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.coevolution.trust_calibration")


class TrustDimension(BaseModel):
    """Trust score for a single dimension."""
    score: float = 0.5  # 0.0 to 1.0
    observations: int = 0
    last_updated: str = ""


class TrustEntry(BaseModel):
    """Trust record for a single operator/agent."""
    entity_id: str
    dimensions: Dict[str, TrustDimension] = Field(default_factory=dict)
    overall_trust: float = 0.5
    trust_tier: str = "unverified"  # unverified, low, medium, high, core
    created_at: str = ""
    updated_at: str = ""
    history: List[Dict[str, Any]] = Field(default_factory=list)


class TrustCalibrationConfig(BaseModel):
    """Configuration for trust_calibration."""
    enabled: bool = True
    max_history: int = 500
    accuracy_weight: float = 0.35
    consistency_weight: float = 0.25
    responsiveness_weight: float = 0.20
    recovery_weight: float = 0.20
    decay_rate: float = 0.995
    floor: float = 0.05
    ceiling: float = 0.99
    high_threshold: float = 0.8
    medium_threshold: float = 0.5
    low_threshold: float = 0.25


DEFAULT_DIMENSIONS = ["accuracy", "consistency", "responsiveness", "recovery"]

TIER_THRESHOLDS = {
    "core": 0.90,
    "high": 0.80,
    "medium": 0.50,
    "low": 0.25,
    "unverified": 0.0,
}


class TrustCalibrationModule:
    """Dynamic trust calibration for operators and agents."""

    def __init__(self):
        self.config = TrustCalibrationConfig()
        self.running = False
        self._lock = Lock()
        self._entries: Dict[str, TrustEntry] = {}
        self._total_observations: int = 0

    def start(self) -> None:
        self.running = True
        logger.info("TrustCalibrationModule started")

    def stop(self) -> None:
        self.running = False
        logger.info("TrustCalibrationModule stopped")

    def _get_or_create(self, entity_id: str) -> TrustEntry:
        """Get or lazily create a trust entry."""
        if entity_id not in self._entries:
            now = datetime.now(timezone.utc).isoformat()
            entry = TrustEntry(
                entity_id=entity_id,
                created_at=now,
                updated_at=now,
            )
            for dim_name in DEFAULT_DIMENSIONS:
                entry.dimensions[dim_name] = TrustDimension()
            self._entries[entity_id] = entry
            logger.debug("Created trust entry for %s", entity_id)
        return self._entries[entity_id]

    def record_observation(self, entity_id: str, dimension: str,
                           success: bool, weight: float = 1.0,
                           context: str = "") -> Dict[str, float]:
        """
        Record a trust observation for an entity along a dimension.

        Args:
            entity_id: Operator or agent identifier.
            dimension: Trust dimension (accuracy, consistency, responsiveness, recovery).
            success: Whether the observation was positive.
            weight: Weight of this observation (0.0-1.0).
            context: Optional context description.

        Returns:
            Dict with current dimension score and overall trust.
        """
        with self._lock:
            entry = self._get_or_create(entity_id)

            if dimension not in entry.dimensions:
                entry.dimensions[dimension] = TrustDimension()

            dim = entry.dimensions[dimension]
            dim.observations += 1

            # Bayesian-like update: move score toward 1.0 (success) or 0.0 (failure)
            delta = weight * 0.1 if success else -weight * 0.15  # penalize failures more
            dim.score = max(self.config.floor, min(self.config.ceiling, dim.score + delta))
            dim.last_updated = datetime.now(timezone.utc).isoformat()

            # Recalculate overall trust
            self._recalculate_overall(entry)

            # Record history
            entry.history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "dimension": dimension,
                "success": success,
                "weight": weight,
                "context": context,
                "score_after": round(dim.score, 4),
            })
            if len(entry.history) > self.config.max_history:
                entry.history = entry.history[-self.config.max_history:]

            entry.updated_at = datetime.now(timezone.utc).isoformat()
            self._total_observations += 1

            logger.debug("Trust observation: %s [%s] success=%.1f score=%.3f overall=%.3f",
                         entity_id, dimension, success, dim.score, entry.overall_trust)

            return {
                "dimension": dimension,
                "dimension_score": round(dim.score, 4),
                "overall_trust": round(entry.overall_trust, 4),
                "trust_tier": entry.trust_tier,
            }

    def _recalculate_overall(self, entry: TrustEntry) -> None:
        """Recalculate overall trust from dimension scores."""
        weights = {
            "accuracy": self.config.accuracy_weight,
            "consistency": self.config.consistency_weight,
            "responsiveness": self.config.responsiveness_weight,
            "recovery": self.config.recovery_weight,
        }

        total_weight = 0.0
        weighted_sum = 0.0

        for dim_name, w in weights.items():
            if dim_name in entry.dimensions:
                dim = entry.dimensions[dim_name]
                # Require minimum observations for full weight
                confidence = min(1.0, dim.observations / 10.0)
                effective_weight = w * confidence
                weighted_sum += dim.score * effective_weight
                total_weight += effective_weight

        if total_weight > 0:
            entry.overall_trust = max(self.config.floor,
                                       min(self.config.ceiling, weighted_sum / total_weight))
        else:
            entry.overall_trust = 0.5

        # Update tier
        entry.trust_tier = self._tier_for_score(entry.overall_trust)

    def _tier_for_score(self, score: float) -> str:
        """Determine trust tier from score."""
        for tier, threshold in TIER_THRESHOLDS.items():
            if score >= threshold:
                return tier
        return "unverified"

    def decay_trust(self) -> None:
        """Apply trust decay toward neutral (0.5) for all entries."""
        with self._lock:
            decay = self.config.decay_rate
            for entry in self._entries.values():
                for dim in entry.dimensions.values():
                    # Decay toward 0.5 (neutral)
                    dim.score = 0.5 + decay * (dim.score - 0.5)
                    dim.score = max(self.config.floor, min(self.config.ceiling, dim.score))
                self._recalculate_overall(entry)
                entry.updated_at = datetime.now(timezone.utc).isoformat()
        logger.info("Trust decay applied to %d entries", len(self._entries))

    def get_trust(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get trust record for an entity."""
        with self._lock:
            entry = self._entries.get(entity_id)
            if not entry:
                return None
            return {
                "entity_id": entry.entity_id,
                "overall_trust": round(entry.overall_trust, 4),
                "trust_tier": entry.trust_tier,
                "dimensions": {
                    name: {"score": round(d.score, 4), "observations": d.observations}
                    for name, d in entry.dimensions.items()
                },
                "total_observations": sum(d.observations for d in entry.dimensions.values()),
                "created_at": entry.created_at,
                "updated_at": entry.updatedated_at,
            }

    def is_trusted(self, entity_id: str, min_tier: str = "medium") -> bool:
        """Check if an entity meets a minimum trust tier."""
        tier_order = ["unverified", "low", "medium", "high", "core"]
        with self._lock:
            entry = self._entries.get(entity_id)
            if not entry:
                return False
            entity_idx = tier_order.index(entry.trust_tier) if entry.trust_tier in tier_order else 0
            min_idx = tier_order.index(min_tier) if min_tier in tier_order else 0
            return entity_idx >= min_idx

    def get_trusted_entities(self, min_tier: str = "medium") -> List[Dict[str, Any]]:
        """Get all entities that meet a minimum trust tier."""
        tier_order = ["unverified", "low", "medium", "high", "core"]
        min_idx = tier_order.index(min_tier) if min_tier in tier_order else 0
        with self._lock:
            results = []
            for entry in self._entries.values():
                entity_idx = tier_order.index(entry.trust_tier) if entry.trust_tier in tier_order else 0
                if entity_idx >= min_idx:
                    results.append({
                        "entity_id": entry.entity_id,
                        "overall_trust": round(entry.overall_trust, 4),
                        "trust_tier": entry.trust_tier,
                    })
            results.sort(key=lambda x: x["overall_trust"], reverse=True)
            return results

    def get_stats(self) -> Dict[str, Any]:
        """Get trust calibration statistics."""
        with self._lock:
            tier_counts: Dict[str, int] = defaultdict(int)
            for entry in self._entries.values():
                tier_counts[entry.trust_tier] += 1

            all_trust = [e.overall_trust for e in self._entries.values()]
            avg_trust = round(sum(all_trust) / len(all_trust), 4) if all_trust else 0.0

            return {
                "total_entities": len(self._entries),
                "total_observations": self._total_observations,
                "average_trust": avg_trust,
                "tier_distribution": dict(tier_counts),
                "dimension_averages": {
                    dim: round(sum(
                        e.dimensions[dim].score for e in self._entries.values()
                        if dim in e.dimensions
                    ) / max(1, len(self._entries)), 4)
                    for dim in DEFAULT_DIMENSIONS
                },
            }
