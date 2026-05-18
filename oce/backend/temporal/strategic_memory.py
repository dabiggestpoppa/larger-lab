"""
V3 Phase 5 — Strategic Memory Engine
Moves beyond episodic memory into structural wisdom.

Learns: what consistently works, what repeatedly fails,
which structures scale, which trajectories collapse.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StrategicInsight:
    """A piece of structural wisdom learned from experience."""
    insight_id: str
    insight_type: str       # "success_pattern", "failure_pattern", "scaling_law", "collapse_signal"
    description: str
    confidence: float = 0.5
    evidence_count: int = 0
    first_observed: float = field(default_factory=time.time)
    last_confirmed: float = field(default_factory=time.time)
    tags: list[str] = field(default_factory=list)

    @property
    def is_reliable(self) -> bool:
        return self.confidence > 0.7 and self.evidence_count >= 3

    def confirm(self) -> None:
        self.evidence_count += 1
        self.last_confirmed = time.time()
        self.confidence = min(1.0, self.confidence + 0.1)


class StrategicMemoryEngine:
    """
    Accumulates structural wisdom from field operation.
    
    Instead of storing every event, stores:
    - Success patterns (what consistently works)
    - Failure patterns (what repeatedly fails)
    - Scaling laws (which structures scale)
    - Collapse signals (early warning signs)
    """

    def __init__(self):
        self.insights: dict[str, StrategicInsight] = {}
        self._pattern_evidence: dict[str, list[bool]] = {}  # pattern -> [success, failure, ...]

    def record_outcome(self, pattern: str, success: bool, context: str = "") -> None:
        """Record the outcome of a pattern."""
        if pattern not in self._pattern_evidence:
            self._pattern_evidence[pattern] = []
        self._pattern_evidence[pattern].append(success)

        # Check if pattern should become an insight
        evidence = self._pattern_evidence[pattern]
        if len(evidence) >= 3:
            success_rate = sum(1 for e in evidence if e) / len(evidence)
            if success_rate > 0.7:
                self._create_insight(pattern, "success_pattern", success_rate, context)
            elif success_rate < 0.3:
                self._create_insight(pattern, "failure_pattern", 1.0 - success_rate, context)

    def _create_insight(self, pattern: str, insight_type: str, confidence: float, context: str) -> None:
        """Create a strategic insight from a pattern."""
        iid = f"insight_{pattern[:20]}"
        if iid not in self.insights:
            self.insights[iid] = StrategicInsight(
                insight_id=iid,
                insight_type=insight_type,
                description=f"Pattern '{pattern}' → {insight_type} (from {context})",
                confidence=confidence,
                evidence_count=len(self._pattern_evidence.get(pattern, [])),
                tags=[pattern[:10]],
            )
        else:
            self.insights[iid].confirm()

    def get_reliable_insights(self, insight_type: str = None) -> list[StrategicInsight]:
        """Get all reliable insights, optionally filtered by type."""
        insights = [i for i in self.insights.values() if i.is_reliable]
        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]
        return sorted(insights, key=lambda i: i.confidence, reverse=True)

    def get_failure_patterns(self) -> list[StrategicInsight]:
        """Get known failure patterns to avoid."""
        return self.get_reliable_insights("failure_pattern")

    def get_success_patterns(self) -> list[StrategicInsight]:
        """Get known success patterns to replicate."""
        return self.get_reliable_insights("success_pattern")

    def predict_outcome(self, pattern: str) -> Optional[float]:
        """Predict the success probability of a pattern."""
        evidence = self._pattern_evidence.get(pattern)
        if evidence and len(evidence) >= 2:
            return sum(1 for e in evidence if e) / len(evidence)
        return None

    @property
    def stats(self) -> dict:
        reliable = sum(1 for i in self.insights.values() if i.is_reliable)
        return {
            "total_insights": len(self.insights),
            "reliable_insights": reliable,
            "patterns_tracked": len(self._pattern_evidence),
            "success_patterns": sum(1 for i in self.insights.values() if i.insight_type == "success_pattern"),
            "failure_patterns": sum(1 for i in self.insights.values() if i.insight_type == "failure_pattern"),
        }
