"""
V3 Phase 9 — Resonance Engine
Measures coherence across the field system.
Calculates resonance scores between field states and detects alignment patterns.
"""

from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResonanceState:
    """A resonance measurement between field elements."""
    state_id: str
    element_a: str
    element_b: str
    resonance_score: float  # 0-1, how resonant the two elements are
    phase_alignment: float  # 0-1, how aligned in phase
    timestamp: float = field(default_factory=time.time)

    @property
    def is_resonant(self) -> bool:
        return self.resonance_score > 0.6

    @property
    def is_aligned(self) -> bool:
        return self.phase_alignment > 0.5


class ResonanceEngine:
    """
    Measures coherence across the field system.
    
    Calculates resonance scores between field states and detects
    alignment patterns. Resonance is the degree to which field
    elements amplify each other constructively.
    """

    def __init__(self):
        self._states: list[ResonanceState] = []
        self._coherence_history: list[float] = []

    def measure_resonance(self, element_a: str, element_b: str,
                           amplitude_a: float, amplitude_b: float,
                           phase_a: float, phase_b: float) -> ResonanceState:
        """Measure resonance between two field elements."""
        # Resonance = amplitude product × phase alignment
        phase_diff = abs(phase_a - phase_b)
        phase_alignment = 1.0 - min(phase_diff / math.pi, 1.0)
        resonance_score = amplitude_a * amplitude_b * phase_alignment

        state = ResonanceState(
            state_id=f"res_{int(time.time() * 1000)}",
            element_a=element_a, element_b=element_b,
            resonance_score=round(resonance_score, 4),
            phase_alignment=round(phase_alignment, 4),
        )
        self._states.append(state)
        return state

    def get_field_coherence(self) -> float:
        """Get overall field coherence (average of recent resonance scores)."""
        if not self._states:
            return 0.5  # neutral default
        recent = self._states[-20:]
        return sum(s.resonance_score for s in recent) / len(recent)

    def get_alignment_pattern(self) -> dict:
        """Detect alignment patterns across recent measurements."""
        if not self._states:
            return {"aligned": 0, "misaligned": 0, "total": 0}

        recent = self._states[-50:]
        aligned = sum(1 for s in recent if s.is_aligned)
        return {
            "aligned": aligned,
            "misaligned": len(recent) - aligned,
            "total": len(recent),
            "alignment_rate": round(aligned / len(recent), 4),
        }

    def find_resonant_pairs(self, threshold: float = 0.6) -> list[ResonanceState]:
        """Find all resonant pairs above threshold."""
        return [s for s in self._states if s.resonance_score >= threshold]

    def record_coherence(self, coherence: float) -> None:
        """Record a field coherence measurement."""
        self._coherence_history.append(coherence)

    def get_coherence_trend(self, window: int = 20) -> float:
        """Get coherence trend (positive = improving)."""
        if len(self._coherence_history) < 2:
            return 0.0
        recent = self._coherence_history[-window:]
        if len(recent) < 2:
            return 0.0
        return (recent[-1] - recent[0]) / len(recent)

    @property
    def stats(self) -> dict:
        return {
            "total_measurements": len(self._states),
            "field_coherence": round(self.get_field_coherence(), 4),
            "resonant_pairs": len(self.find_resonant_pairs()),
            "coherence_trend": round(self.get_coherence_trend(), 4),
        }
