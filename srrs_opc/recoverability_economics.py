"""
Recoverability Economics
==========================
Phase 9 Component 3: Track and optimize recovery cost across all scales.

Measures the cost of recovery from failures at local, regional, and global
scales. Optimizes for fast local recovery and minimal global intervention.

Integration: RecoveryAnchors, DriftDetector, ReconstructionSynthesizer
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class RecoveryCostRecord:
    """Records the cost of a single recovery operation."""

    def __init__(self, scope: str, repair_complexity: float,
                 reconstruction_speed: float, continuity_restored: float,
                 sync_cost: float, source: str = "system"):
        self.scope = scope  # "local", "regional", "global"
        self.repair_complexity = max(0.0, min(1.0, repair_complexity))
        self.reconstruction_speed = max(0.0, reconstruction_speed)
        self.continuity_restored = max(0.0, min(1.0, continuity_restored))
        self.sync_cost = max(0.0, sync_cost)
        self.source = source
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.efficiency = self._compute_efficiency()

    def _compute_efficiency(self) -> float:
        """
        Recovery efficiency = continuity_restored / (repair_complexity + sync_cost).
        Higher = more efficient recovery.
        """
        denominator = self.repair_complexity + self.sync_cost
        if denominator < 1e-10:
            return 1.0
        return min(1.0, self.continuity_restored / denominator)

    def to_dict(self) -> dict:
        return {
            "scope": self.scope,
            "repair_complexity": round(self.repair_complexity, 3),
            "reconstruction_speed": round(self.reconstruction_speed, 3),
            "continuity_restored": round(self.continuity_restored, 3),
            "sync_cost": round(self.sync_cost, 3),
            "efficiency": round(self.efficiency, 3),
            "timestamp": self.timestamp,
        }


class RecoverabilityEconomics:
    """
    Tracks and optimizes recovery costs across scales.

    Key principle: Most recovery should be local.
    Global recovery is the most expensive and should be rare.
    """

    SCOPE_WEIGHTS = {
        "local": 1.0,
        "regional": 3.0,
        "global": 10.0,
    }

    def __init__(self):
        self._recovery_records: List[RecoveryCostRecord] = []
        self._scope_counts: Dict[str, int] = defaultdict(int)
        self._scope_efficiency: Dict[str, List[float]] = defaultdict(list)

    def record_recovery(self, scope: str, repair_complexity: float,
                        reconstruction_speed: float, continuity_restored: float,
                        sync_cost: float, source: str = "system") -> RecoveryCostRecord:
        """Record a recovery operation."""
        record = RecoveryCostRecord(scope, repair_complexity,
                                    reconstruction_speed, continuity_restored,
                                    sync_cost, source)
        self._recovery_records.append(record)
        self._scope_counts[scope] += 1
        self._scope_efficiency[scope].append(record.efficiency)
        return record

    def recovery_cost(self, scope: str) -> float:
        """
        Estimate recovery cost for a given scope.
        Weighted by scope (local=1, regional=3, global=10).
        """
        records = [r for r in self._recovery_records if r.scope == scope]
        if not records:
            return self.SCOPE_WEIGHTS.get(scope, 1.0)
        avg_complexity = sum(r.repair_complexity for r in records) / len(records)
        avg_sync = sum(r.sync_cost for r in records) / len(records)
        weight = self.SCOPE_WEIGHTS.get(scope, 1.0)
        return round(weight * (avg_complexity + avg_sync), 3)

    def recoverability_score(self) -> float:
        """
        Current system recoverability score (0.0 to 1.0).
        Higher = more recoverable.
        """
        if not self._recovery_records:
            return 1.0  # No failures = fully recoverable
        recent = self._recovery_records[-20:]
        avg_efficiency = sum(r.efficiency for r in recent) / len(recent)
        # Penalize global recoveries
        global_ratio = sum(1 for r in recent if r.scope == "global") / len(recent)
        return round(max(0.0, avg_efficiency * (1.0 - global_ratio * 0.5)), 3)

    def scope_efficiency(self, scope: str) -> Optional[dict]:
        """Get efficiency statistics for a scope."""
        efficiencies = self._scope_efficiency.get(scope, [])
        if not efficiencies:
            return None
        return {
            "scope": scope,
            "avg_efficiency": round(sum(efficiencies) / len(efficiencies), 3),
            "count": len(efficiencies),
            "recovery_cost": self.recovery_cost(scope),
        }

    def optimize_recovery_paths(self) -> List[dict]:
        """Suggest optimal recovery paths based on historical data."""
        suggestions = []
        for scope in ["local", "regional", "global"]:
            eff = self.scope_efficiency(scope)
            if eff and eff["avg_efficiency"] < 0.5:
                suggestions.append({
                    "scope": scope,
                    "current_efficiency": eff["avg_efficiency"],
                    "recommendation": f"Improve {scope} recovery efficiency",
                    "action": "Add redundancy" if scope == "global" else "Strengthen local repair",
                })
        return suggestions

    def escalation_ratio(self) -> float:
        """Ratio of global recoveries to total. Lower is better."""
        if not self._recovery_records:
            return 0.0
        global_count = self._scope_counts.get("global", 0)
        return round(global_count / len(self._recovery_records), 3)

    def get_stats(self) -> dict:
        return {
            "total_recoveries": len(self._recovery_records),
            "recoverability_score": self.recoverability_score(),
            "escalation_ratio": self.escalation_ratio(),
            "scope_stats": {
                scope: self.scope_efficiency(scope)
                for scope in ["local", "regional", "global"]
                if self._scope_counts.get(scope, 0) > 0
            },
        }
