"""
8.1 Operator Profiles — Coevolution
=====================================
Tracks operator (human/agent) interaction preferences, expertise areas,
and behavioral patterns for personalized field adaptation.

Maintains per-operator profiles with expertise scores, preferred
interaction modes, and activity history.
"""

import logging
import math
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.coevolution.operator_profiles")


class OperatorProfileEntry(BaseModel):
    """Profile for a single operator."""
    operator_id: str
    expertise_areas: Dict[str, float] = Field(default_factory=dict)  # area -> score 0-1
    interaction_count: int = 0
    preferred_modes: Dict[str, int] = Field(default_factory=dict)  # mode -> count
    last_active: str = ""
    trust_score: float = 0.5
    activity_history: List[str] = Field(default_factory=list)  # last N timestamps


class OperatorProfilesConfig(BaseModel):
    """Configuration for operator_profiles."""
    enabled: bool = True
    max_history: int = 100
    expertise_decay: float = 0.95
    min_interactions: int = 5


class OperatorProfilesModule:
    """Tracks operator interaction preferences and expertise."""

    def __init__(self):
        self.config = OperatorProfilesConfig()
        self.running = False
        self._lock = Lock()
        self._profiles: Dict[str, OperatorProfileEntry] = {}
        self._total_interactions: int = 0

    def start(self) -> None:
        self.running = True
        logger.info("OperatorProfilesModule started")

    def stop(self) -> None:
        self.running = False
        logger.info("OperatorProfilesModule stopped")

    def record_interaction(self, operator_id: str, expertise_area: str = "",
                           interaction_mode: str = "default") -> None:
        """Record an interaction for an operator.

        Args:
            operator_id: Unique operator identifier.
            expertise_area: Area of expertise demonstrated.
            interaction_mode: Type of interaction (chat, edit, review, etc.).
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            if operator_id not in self._profiles:
                self._profiles[operator_id] = OperatorProfileEntry(operator_id=operator_id)

            profile = self._profiles[operator_id]
            profile.interaction_count += 1
            profile.last_active = now
            profile.activity_history.append(now)

            # Trim history
            if len(profile.activity_history) > self.config.max_history:
                profile.activity_history = profile.activity_history[-self.config.max_history:]

            # Update expertise
            if expertise_area:
                current = profile.expertise_areas.get(expertise_area, 0.0)
                profile.expertise_areas[expertise_area] = min(1.0, current + 0.05)

            # Update preferred modes
            profile.preferred_modes[interaction_mode] = profile.preferred_modes.get(interaction_mode, 0) + 1

            self._total_interactions += 1

        logger.debug("Interaction recorded for operator %s: area=%s mode=%s",
                     operator_id, expertise_area, interaction_mode)

    def get_profile(self, operator_id: str) -> Optional[OperatorProfileEntry]:
        """Get the profile for a specific operator."""
        with self._lock:
            return self._profiles.get(operator_id)

    def get_top_experts(self, area: str, n: int = 5) -> List[Dict[str, Any]]:
        """Get the top N experts in a given area.

        Args:
            area: Expertise area to query.
            n: Number of experts to return.

        Returns:
            List of {operator_id, expertise_score, interaction_count} sorted by score desc.
        """
        with self._lock:
            ranked = [
                {
                    "operator_id": pid,
                    "expertise_score": round(data.expertise_areas.get(area, 0.0), 4),
                    "interaction_count": data.interaction_count,
                }
                for pid, data in self._profiles.items()
                if area in data.expertise_areas
            ]
            ranked.sort(key=lambda x: x["expertise_score"], reverse=True)
            return ranked[:n]

    def get_preferred_mode(self, operator_id: str) -> str:
        """Get the most preferred interaction mode for an operator."""
        with self._lock:
            profile = self._profiles.get(operator_id)
            if not profile or not profile.preferred_modes:
                return "default"
            return max(profile.preferred_modes, key=profile.preferred_modes.get)

    def decay_expertise(self) -> None:
        """Apply decay to all expertise scores (call periodically)."""
        with self._lock:
            decay = self.config.expertise_decay
            for profile in self._profiles.values():
                for area in profile.expertise_areas:
                    profile.expertise_areas[area] *= decay
                # Remove negligible scores
                profile.expertise_areas = {
                    k: round(v, 4) for k, v in profile.expertise_areas.items() if v > 0.01
                }
        logger.info("Expertise decay applied to %d profiles", len(self._profiles))

    def get_stats(self) -> Dict[str, Any]:
        """Get module statistics."""
        with self._lock:
            all_areas = set()
            for p in self._profiles.values():
                all_areas.update(p.expertise_areas.keys())
            return {
                "total_operators": len(self._profiles),
                "total_interactions": self._total_interactions,
                "unique_expertise_areas": len(all_areas),
                "expertise_areas": sorted(all_areas),
                "avg_interactions_per_operator": (
                    self._total_interactions / len(self._profiles) if self._profiles else 0.0
                ),
            }
