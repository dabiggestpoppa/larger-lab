"""
V3 Phase 6 — Self-Reflection Loop
System analyzes its own repair patterns.

The field can observe: what repairs were attempted, what worked,
what failed, and what patterns emerge from its own self-repair behavior.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RepairRecord:
    """A record of a repair action taken by the field."""
    record_id: str
    repair_type: str
    trigger: str
    action_taken: str
    success: bool = False
    coherence_before: float = 0.5
    coherence_after: float = 0.5
    timestamp: float = field(default_factory=time.time)

    @property
    def improvement(self) -> float:
        return self.coherence_after - self.coherence_before


class SelfReflectionLoop:
    """
    Analyzes the field's own repair patterns.
    
    Tracks:
    - What repairs were attempted
    - What worked and what failed
    - Repair success rates by type
    - Patterns in repair triggers
    - Effectiveness trends over time
    """

    def __init__(self):
        self._repair_history: list[RepairRecord] = []

    def record_repair(
        self, repair_type: str, trigger: str, action: str,
        success: bool, coherence_before: float, coherence_after: float,
    ) -> RepairRecord:
        """Record a repair action."""
        record = RepairRecord(
            record_id=f"repair_{int(time.time())}",
            repair_type=repair_type,
            trigger=trigger,
            action_taken=action,
            success=success,
            coherence_before=coherence_before,
            coherence_after=coherence_after,
        )
        self._repair_history.append(record)
        return record

    def analyze_patterns(self) -> dict:
        """Analyze repair patterns."""
        if not self._repair_history:
            return {"status": "no_data"}

        by_type = {}
        for r in self._repair_history:
            if r.repair_type not in by_type:
                by_type[r.repair_type] = {"attempts": 0, "successes": 0, "avg_improvement": 0.0}
            by_type[r.repair_type]["attempts"] += 1
            if r.success:
                by_type[r.repair_type]["successes"] += 1
            by_type[r.repair_type]["avg_improvement"] += r.improvement

        for t in by_type:
            n = by_type[t]["attempts"]
            by_type[t]["avg_improvement"] = round(by_type[t]["avg_improvement"] / max(n, 1), 4)
            by_type[t]["success_rate"] = round(by_type[t]["successes"] / max(n, 1), 4)

        return {
            "total_repairs": len(self._repair_history),
            "by_type": by_type,
            "overall_success_rate": round(
                sum(1 for r in self._repair_history if r.success) / len(self._repair_history), 4
            ),
        }

    def get_recommendations(self) -> list[str]:
        """Get recommendations based on repair analysis."""
        patterns = self.analyze_patterns()
        if "status" in patterns:
            return ["No repair data available"]

        recs = []
        for rtype, data in patterns.get("by_type", {}).items():
            if data["success_rate"] < 0.5:
                recs.append(f"LOW SUCCESS: {rtype} repairs only {data['success_rate']*100:.0f}% successful — review approach")
            if data["avg_improvement"] < 0:
                recs.append(f"NEGATIVE IMPACT: {rtype} repairs reduce coherence — stop using this approach")

        if not recs:
            recs.append("OK: Repair patterns are healthy")

        return recs

    @property
    def stats(self) -> dict:
        return self.analyze_patterns()
