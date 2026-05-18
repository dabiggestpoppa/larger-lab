"""
V3 Phase 8 — Operator Model
Identifies recurring strategic behavior patterns from operational evidence.

NOT a personality model — a trajectory model.
Tracks what the operator consistently prioritizes, not emotional vulnerabilities.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OperatorPattern:
    """A recurring strategic behavior pattern."""
    pattern_id: str
    pattern_type: str       # "priority", "timing", "focus", "decision"
    description: str
    evidence_count: int = 0
    confidence: float = 0.5
    first_observed: float = field(default_factory=time.time)
    last_observed: float = field(default_factory=time.time)
    tags: list[str] = field(default_factory=list)

    @property
    def is_reliable(self) -> bool:
        return self.confidence > 0.6 and self.evidence_count >= 3

    def record_evidence(self) -> None:
        self.evidence_count += 1
        self.last_observed = time.time()
        self.confidence = min(1.0, self.confidence + 0.1)


class OperatorModel:
    """
    Models operator strategic behavior patterns from operational evidence.
    
    Key principles:
    - Model strategic behavior, NOT emotional vulnerabilities
    - Track operational evidence, NOT speculative psychology
    - Patterns emerge from repeated observations
    - The model is always probabilistic, never certain
    """

    def __init__(self):
        self.patterns: dict[str, OperatorPattern] = {}
        self._observation_log: list[dict] = []

    def record_observation(
        self, observation_type: str, description: str,
        context: str = "", tags: list[str] = None,
    ) -> None:
        """Record an observation about operator behavior."""
        self._observation_log.append({
            "type": observation_type,
            "description": description,
            "context": context,
            "tags": tags or [],
            "timestamp": time.time(),
        })

        # Check if this observation reinforces an existing pattern
        for pid, pattern in self.patterns.items():
            if pattern.pattern_type == observation_type:
                pattern.record_evidence()
                return

        # Create new pattern if enough observations
        similar = [o for o in self._observation_log
                   if o["type"] == observation_type]
        if len(similar) >= 2:
            pid = f"pattern_{observation_type}_{int(time.time())}"
            self.patterns[pid] = OperatorPattern(
                pattern_id=pid,
                pattern_type=observation_type,
                description=f"Recurring {observation_type}: {description}",
                evidence_count=len(similar),
                confidence=min(0.5 + len(similar) * 0.1, 0.9),
                tags=tags or [],
            )

    def get_reliable_patterns(self) -> list[OperatorPattern]:
        """Get all reliable patterns."""
        return sorted(
            [p for p in self.patterns.values() if p.is_reliable],
            key=lambda p: p.confidence,
            reverse=True,
        )

    def predict_focus(self) -> Optional[str]:
        """Predict what the operator is likely to focus on next."""
        reliable = self.get_reliable_patterns()
        if reliable:
            # Return the most confident pattern's type
            return reliable[0].pattern_type
        return None

    def get_model_summary(self) -> dict:
        """Get a summary of the operator model."""
        reliable = self.get_reliable_patterns()
        return {
            "total_patterns": len(self.patterns),
            "reliable_patterns": len(reliable),
            "total_observations": len(self._observation_log),
            "pattern_types": list(set(p.pattern_type for p in self.patterns.values())),
        }

    @property
    def stats(self) -> dict:
        return self.get_model_summary()
