"""
V3 Phase 8 — Alignment Tracking
Tracks alignment between system and operator over weeks/months.

Is the system staying aligned with the operator's strategic direction over time?
This module tracks alignment metrics across long time horizons.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AlignmentMeasurement:
    """A measurement of system-operator alignment."""
    measurement_id: str
    alignment_score: float  # 0-1, how aligned the system is with operator direction
    context: str = ""
    timestamp: float = field(default_factory=time.time)


class AlignmentTracker:
    """
    Tracks alignment between the system and operator over time.
    
    Measures:
    - Strategic alignment (is the system pursuing the right goals?)
    - Tactical alignment (is the system executing in the right way?)
    - Temporal alignment (is the system timing its actions appropriately?)
    
    Alignment is measured through:
    - Operator feedback (explicit corrections or approvals)
    - Behavioral evidence (does the operator use the system's output?)
    - Outcome correlation (do system actions lead to operator-desired outcomes?)
    """

    def __init__(self):
        self._measurements: list[AlignmentMeasurement] = []

    def record_alignment(
        self, alignment_score: float, context: str = "",
    ) -> AlignmentMeasurement:
        """Record an alignment measurement."""
        m = AlignmentMeasurement(
            measurement_id=f"align_{int(time.time())}",
            alignment_score=max(0.0, min(1.0, alignment_score)),
            context=context,
        )
        self._measurements.append(m)
        return m

    def get_current_alignment(self) -> float:
        """Get the most recent alignment score."""
        if not self._measurements:
            return 0.5  # Neutral default
        return self._measurements[-1].alignment_score

    def get_alignment_trend(self, window: int = 20) -> float:
        """Get alignment trend (positive = improving, negative = degrading)."""
        if len(self._measurements) < 2:
            return 0.0
        recent = self._measurements[-window:]
        if len(recent) < 2:
            return 0.0
        values = [m.alignment_score for m in recent]
        return (values[-1] - values[0]) / len(values)

    def is_aligned(self, threshold: float = 0.6) -> bool:
        """Is the system currently aligned with the operator?"""
        return self.get_current_alignment() >= threshold

    def is_drifting(self, threshold: float = -0.1) -> bool:
        """Is alignment degrading over time?"""
        return self.get_alignment_trend() < threshold

    def get_misalignment_events(self) -> list[AlignmentMeasurement]:
        """Get measurements where alignment was low."""
        return [m for m in self._measurements if m.alignment_score < 0.4]

    @property
    def stats(self) -> dict:
        if not self._measurements:
            return {"total_measurements": 0, "current_alignment": 0.5}

        return {
            "total_measurements": len(self._measurements),
            "current_alignment": round(self.get_current_alignment(), 4),
            "trend": round(self.get_alignment_trend(), 4),
            "is_aligned": self.is_aligned(),
            "is_drifting": self.is_drifting(),
            "misalignment_events": len(self.get_misalignment_events()),
        }
