"""
V3 Phase 4 — Compute Economics Engine
Coherence-aware compute budgeting.

Compute is NOT primary — coherence is primary.
Track: token waste, routing inefficiency, topology inefficiency,
unnecessary recursion, synchronization waste, memory redundancy.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ComputeBudget:
    """Current compute budget state."""
    total_budget: float = 1.0        # 0-1 scale
    used_budget: float = 0.0
    wasted_budget: float = 0.0
    coherence_yield: float = 0.0     # coherence achieved per unit compute
    timestamp: float = field(default_factory=time.time)

    @property
    def remaining(self) -> float:
        return max(0.0, self.total_budget - self.used_budget)

    @property
    def efficiency(self) -> float:
        if self.used_budget == 0:
            return 1.0
        return self.coherence_yield / self.used_budget


@dataclass
class WasteReport:
    """Report of compute waste sources."""
    token_waste: float = 0.0
    routing_inefficiency: float = 0.0
    topology_inefficiency: float = 0.0
    unnecessary_recursion: float = 0.0
    sync_waste: float = 0.0
    memory_redundancy: float = 0.0
    total_waste: float = 0.0
    timestamp: float = field(default_factory=time.time)


class ComputeEconomicsEngine:
    """
    Tracks and optimizes compute usage for maximum coherence yield.
    
    Key metric: coherence_yield = (coherence × resonance × alignment) / (entropy × sync_cost × redundancy)
    """

    def __init__(self, total_budget: float = 1.0):
        self.budget = ComputeBudget(total_budget=total_budget)
        self._waste_history: list[WasteReport] = []
        self._operation_log: list[dict] = []

    def record_operation(
        self, operation_type: str, tokens_used: int = 0,
        coherence_delta: float = 0.0, entropy_delta: float = 0.0,
    ) -> None:
        """Record a compute operation."""
        self.budget.used_budget += tokens_used / 100000.0  # Normalize
        self.budget.coherence_yield += coherence_delta
        self.budget.timestamp = time.time()

        self._operation_log.append({
            "type": operation_type,
            "tokens": tokens_used,
            "coherence_delta": coherence_delta,
            "entropy_delta": entropy_delta,
            "timestamp": time.time(),
        })

    def analyze_waste(self) -> WasteReport:
        """Analyze current compute waste."""
        recent = self._operation_log[-100:]

        token_waste = sum(
            op["tokens"] for op in recent
            if op["coherence_delta"] < 0.1 and op["tokens"] > 100
        ) / max(len(recent), 1)

        recursion_count = sum(
            1 for i in range(len(recent) - 1)
            if recent[i]["type"] == recent[i + 1]["type"]
        )

        report = WasteReport(
            token_waste=round(token_waste / 1000, 4),
            routing_inefficiency=round(
                sum(1 for op in recent if op["type"] == "route" and op["coherence_delta"] < 0.2) / max(len(recent), 1), 4
            ),
            unnecessary_recursion=round(recursion_count / max(len(recent), 1), 4),
            total_waste=round(token_waste / 1000 + recursion_count * 0.01, 4),
        )

        self._waste_history.append(report)
        self.budget.wasted_budget += report.total_waste
        return report

    def get_recommendations(self) -> list[str]:
        """Get compute optimization recommendations."""
        recs = []
        report = self.analyze_waste()

        if report.token_waste > 0.5:
            recs.append("HIGH: Token waste detected — reduce redundant operations")
        if report.unnecessary_recursion > 0.3:
            recs.append("MEDIUM: Unnecessary recursion detected — add loop detection")
        if report.routing_inefficiency > 0.3:
            recs.append("MEDIUM: Routing inefficiency — optimize resonance scoring")
        if self.budget.efficiency < 0.5:
            recs.append("HIGH: Low coherence yield per compute unit — review field topology")

        if not recs:
            recs.append("OK: Compute efficiency within acceptable range")

        return recs

    @property
    def stats(self) -> dict:
        return {
            "budget_remaining": round(self.budget.remaining, 4),
            "efficiency": round(self.budget.efficiency, 4),
            "coherence_yield": round(self.budget.coherence_yield, 4),
            "wasted": round(self.budget.wasted_budget, 4),
            "operations": len(self._operation_log),
        }
