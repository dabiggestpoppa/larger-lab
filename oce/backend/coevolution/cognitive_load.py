"""
V3 Phase 8 — Cognitive Load Optimizer
Reduces operator burden, not increases it.

The system should make the operator's job easier, not create more work.
This module tracks and optimizes the cognitive load the system places on the operator.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LoadMeasurement:
    """A measurement of cognitive load on the operator."""
    measurement_id: str
    load_type: str           # "decision", "information", "interaction", "monitoring"
    estimated_load: float    # 0-1
    context: str = ""
    timestamp: float = field(default_factory=time.time)


class CognitiveLoadOptimizer:
    """
    Optimizes the cognitive load the system places on the operator.
    
    Principles:
    - Reduce decisions the operator needs to make
    - Filter information to what's essential
    - Minimize unnecessary interactions
    - Automate monitoring where possible
    
    The system should be proactive, not reactive. Anticipate needs
    instead of asking the operator to figure things out.
    """

    def __init__(self):
        self._load_history: list[LoadMeasurement] = []
        self._optimization_actions: list[dict] = []

    def measure_load(self, load_type: str, estimated_load: float, context: str = "") -> LoadMeasurement:
        """Record a cognitive load measurement."""
        m = LoadMeasurement(
            measurement_id=f"load_{int(time.time())}",
            load_type=load_type,
            estimated_load=estimated_load,
            context=context,
        )
        self._load_history.append(m)
        return m

    def get_current_load(self) -> float:
        """Estimate current cognitive load on the operator."""
        if not self._load_history:
            return 0.0

        recent = self._load_history[-20:]
        return sum(m.estimated_load for m in recent) / len(recent)

    def should_reduce_load(self) -> bool:
        """Should the system reduce its demands?"""
        return self.get_current_load() > 0.6

    def should_increase_engagement(self) -> bool:
        """Should the system increase engagement (operator has capacity)?"""
        return self.get_current_load() < 0.3

    def record_optimization(self, action: str, load_reduction: float) -> None:
        """Record an optimization action taken."""
        self._optimization_actions.append({
            "action": action,
            "load_reduction": load_reduction,
            "timestamp": time.time(),
        })

    def get_optimization_recommendations(self) -> list[str]:
        """Get recommendations for reducing cognitive load."""
        recs = []
        current_load = self.get_current_load()

        if current_load > 0.7:
            recs.append("HIGH LOAD: Reduce non-essential notifications")
            recs.append("HIGH LOAD: Batch updates instead of real-time")
            recs.append("HIGH LOAD: Automate routine decisions")

        if current_load > 0.5:
            recs.append("MEDIUM LOAD: Summarize instead of detail")
            recs.append("MEDIUM LOAD: Prioritize critical items only")

        # Check load by type
        by_type = {}
        for m in self._load_history[-50:]:
            by_type[m.load_type] = by_type.get(m.load_type, 0) + m.estimated_load

        for ltype, total in by_type.items():
            if total > 2.0:
                recs.append(f"HIGH {ltype.upper()} LOAD: Reduce {ltype}-related interactions")

        if not recs:
            recs.append("OK: Cognitive load within acceptable range")

        return recs

    @property
    def stats(self) -> dict:
        return {
            "current_load": round(self.get_current_load(), 4),
            "total_measurements": len(self._load_history),
            "optimizations_applied": len(self._optimization_actions),
            "total_load_reduced": round(
                sum(a["load_reduction"] for a in self._optimization_actions), 4
            ),
        }
