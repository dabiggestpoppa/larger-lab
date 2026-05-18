"""
V3 Phase 5 — Temporal Entropy Governance
Prevents entropy from accumulating across time.

Monitors: drift, memory bloat, mission fragmentation,
symbolic corruption, topology instability.
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EntropyAssessment:
    """Assessment of temporal entropy across the field."""
    timestamp: float
    drift_score: float = 0.0
    memory_bloat_score: float = 0.0
    mission_fragmentation: float = 0.0
    symbolic_corruption: float = 0.0
    topology_instability: float = 0.0
    overall_entropy: float = 0.0

    @property
    def is_critical(self) -> bool:
        return self.overall_entropy > 0.7

    @property
    def needs_attention(self) -> bool:
        return self.overall_entropy > 0.4


class TemporalEntropyGovernance:
    """
    Governs entropy accumulation across time.
    
    Prevents:
    - Drift (gradual loss of coherence)
    - Memory bloat (uncontrolled growth)
    - Mission fragmentation (goals diverging)
    - Symbolic corruption (glyphs losing meaning)
    - Topology instability (field structure degrading)
    """

    def __init__(self):
        self._assessments: list[EntropyAssessment] = []
        self._drift_history: list[float] = []
        self._memory_sizes: list[int] = []

    def assess(
        self, drift_score: float = 0.0, memory_size: int = 0,
        mission_count: int = 0, glyph_count: int = 0,
        topology_changes: int = 0,
    ) -> EntropyAssessment:
        """
        Assess current temporal entropy.
        
        Args:
            drift_score: Current drift measurement (0-1)
            memory_size: Current memory entry count
            mission_count: Number of active missions
            glyph_count: Number of active glyphs
            topology_changes: Recent topology change count
        """
        # Memory bloat: logarithmic scale, >1000 entries = high
        memory_bloat = min(1.0, math.log(max(memory_size, 1)) / math.log(10000))

        # Mission fragmentation: >5 active missions = high
        mission_frag = min(1.0, mission_count / 10.0)

        # Symbolic corruption: >50 glyphs = potential corruption
        symbolic = min(1.0, glyph_count / 50.0)

        # Topology instability: >10 recent changes = unstable
        topo = min(1.0, topology_changes / 10.0)

        overall = (
            drift_score * 0.3 +
            memory_bloat * 0.2 +
            mission_frag * 0.2 +
            symbolic * 0.15 +
            topo * 0.15
        )

        assessment = EntropyAssessment(
            timestamp=time.time(),
            drift_score=round(drift_score, 4),
            memory_bloat_score=round(memory_bloat, 4),
            mission_fragmentation=round(mission_frag, 4),
            symbolic_corruption=round(symbolic, 4),
            topology_instability=round(topo, 4),
            overall_entropy=round(min(1.0, overall), 4),
        )

        self._assessments.append(assessment)
        self._drift_history.append(drift_score)
        if memory_size > 0:
            self._memory_sizes.append(memory_size)

        return assessment

    def get_trend(self, window: int = 10) -> float:
        """Get entropy trend (positive = increasing entropy)."""
        if len(self._assessments) < 2:
            return 0.0
        recent = self._assessments[-window:]
        if len(recent) < 2:
            return 0.0
        values = [a.overall_entropy for a in recent]
        return (values[-1] - values[0]) / len(values)

    def get_recommendations(self) -> list[str]:
        """Get entropy reduction recommendations."""
        if not self._assessments:
            return ["No entropy data available"]

        latest = self._assessments[-1]
        recs = []

        if latest.drift_score > 0.5:
            recs.append("HIGH: Significant drift detected — reinforce identity anchors")
        if latest.memory_bloat_score > 0.5:
            recs.append("MEDIUM: Memory bloat detected — compress into attractors")
        if latest.mission_fragmentation > 0.5:
            recs.append("MEDIUM: Mission fragmentation — prioritize and prune")
        if latest.symbolic_corruption > 0.5:
            recs.append("LOW: Glyph count high — review for unused symbols")
        if latest.topology_instability > 0.5:
            recs.append("MEDIUM: Topology unstable — reduce unnecessary changes")

        if not recs:
            recs.append("OK: Entropy within acceptable range")

        return recs

    @property
    def stats(self) -> dict:
        if not self._assessments:
            return {"total_assessments": 0, "avg_entropy": 0.0}
        critical = sum(1 for a in self._assessments if a.is_critical)
        return {
            "total_assessments": len(self._assessments),
            "critical_count": critical,
            "avg_entropy": round(
                sum(a.overall_entropy for a in self._assessments) / len(self._assessments), 4
            ),
            "trend": round(self.get_trend(), 4),
        }
