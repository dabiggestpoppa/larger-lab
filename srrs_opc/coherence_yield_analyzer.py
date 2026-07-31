"""
Coherence Yield Analyzer
==========================
Phase 9 Component 1: Quantify coherence-per-resource efficiency.

Measures how much coherence each operation produces relative to its
entropy and resource cost. Wraps existing CollarMetrics to provide
economic optimization signals.

Integration: CollarTopologyEngine, ReinforcementEngine
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class YieldRecord:
    """A single coherence yield measurement."""

    def __init__(self, operation: str, coherence_delta: float,
                 entropy_cost: float, resource_cost: float,
                 source: str = "system"):
        self.operation = operation
        self.coherence_delta = coherence_delta
        self.entropy_cost = max(0.0, entropy_cost)
        self.resource_cost = max(0.0, resource_cost)
        self.source = source
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.yield_value = self._compute_yield()

    def _compute_yield(self) -> float:
        """Coherence yield = coherence_delta / (entropy_cost + resource_cost)."""
        denominator = self.entropy_cost + self.resource_cost
        if denominator < 1e-10:
            return float('inf') if self.coherence_delta > 0 else 0.0
        return self.coherence_delta / denominator

    def to_dict(self) -> dict:
        return {
            "operation": self.operation,
            "coherence_delta": round(self.coherence_delta, 4),
            "entropy_cost": round(self.entropy_cost, 4),
            "resource_cost": round(self.resource_cost, 4),
            "yield_value": round(self.yield_value, 4) if self.yield_value != float('inf') else "inf",
            "source": self.source,
            "timestamp": self.timestamp,
        }


class CoherenceYieldAnalyzer:
    """
    Analyzes coherence yield across all operations.

    Coherence yield = (Coherence × Recoverability × Adaptability) /
                      (Entropy × Sync Cost × Resource Consumption)

    Higher yield = more efficient operation.
    """

    def __init__(self, min_observations: int = 5):
        self._records: List[YieldRecord] = []
        self._operation_yields: Dict[str, List[float]] = defaultdict(list)
        self._min_observations = min_observations

    def measure_yield(self, operation: str, coherence_delta: float,
                      entropy_cost: float, resource_cost: float,
                      source: str = "system") -> YieldRecord:
        """Measure and record coherence yield for an operation."""
        record = YieldRecord(operation, coherence_delta, entropy_cost,
                             resource_cost, source)
        self._records.append(record)
        if record.yield_value != float('inf'):
            self._operation_yields[operation].append(record.yield_value)
        return record

    def rank_operations(self, operations: Optional[List[str]] = None) -> List[dict]:
        """
        Rank operations by average coherence yield.
        Highest yield first. Only includes operations with min_observations.
        """
        rankings = []
        ops = operations or list(self._operation_yields.keys())
        for op in ops:
            yields = self._operation_yields.get(op, [])
            if len(yields) < self._min_observations:
                continue
            avg = sum(yields) / len(yields)
            rankings.append({
                "operation": op,
                "avg_yield": round(avg, 4),
                "observations": len(yields),
                "max_yield": round(max(yields), 4),
                "min_yield": round(min(yields), 4),
            })
        rankings.sort(key=lambda r: r["avg_yield"], reverse=True)
        return rankings

    def get_operation_stats(self, operation: str) -> Optional[dict]:
        """Get yield statistics for a specific operation."""
        yields = self._operation_yields.get(operation, [])
        if not yields:
            return None
        return {
            "operation": operation,
            "avg_yield": round(sum(yields) / len(yields), 4),
            "max_yield": round(max(yields), 4),
            "min_yield": round(min(yields), 4),
            "observations": len(yields),
        }

    def identify_inefficient(self, threshold: float = 0.1) -> List[dict]:
        """Identify operations with yield below threshold."""
        inefficient = []
        for op, yields in self._operation_yields.items():
            if len(yields) < self._min_observations:
                continue
            avg = sum(yields) / len(yields)
            if avg < threshold:
                inefficient.append({
                    "operation": op,
                    "avg_yield": round(avg, 4),
                    "recommendation": "optimize_or_deprecate",
                })
        return inefficient

    def system_yield_score(self) -> float:
        """Overall system coherence yield score."""
        all_yields = []
        for yields in self._operation_yields.values():
            all_yields.extend(yields)
        if not all_yields:
            return 0.0
        return round(sum(all_yields) / len(all_yields), 4)

    def get_stats(self) -> dict:
        return {
            "total_records": len(self._records),
            "tracked_operations": len(self._operation_yields),
            "system_yield_score": self.system_yield_score(),
            "top_operations": self.rank_operations()[:5],
            "inefficient_operations": self.identify_inefficient(),
        }
