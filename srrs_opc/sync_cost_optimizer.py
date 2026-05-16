"""
Sync Cost Optimizer
=====================
Phase 9 Component 5: Synchronize only when coherence gain exceeds entropy cost.

Uses information-theoretic cost model:
- Sync cost = bits of entropy reduced per sync operation
- Sync approved only when coherence_gain > entropy_cost * threshold

Integration: DynamicCouplingEngine, DistributedConsensus, CollarTopologyEngine
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class SyncDecision:
    """A synchronization decision."""

    def __init__(self, obs_a: str, obs_b: str, coherence_gain: float,
                 entropy_cost: float, approved: bool, reason: str):
        self.obs_a = obs_a
        self.obs_b = obs_b
        self.coherence_gain = coherence_gain
        self.entropy_cost = entropy_cost
        self.approved = approved
        self.reason = reason
        self.yield_value = coherence_gain / max(entropy_cost, 1e-10)
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "obs_a": self.obs_a,
            "obs_b": self.obs_b,
            "coherence_gain": round(self.coherence_gain, 4),
            "entropy_cost": round(self.entropy_cost, 4),
            "yield_value": round(self.yield_value, 4),
            "approved": self.approved,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


class SyncCostOptimizer:
    """
    Optimizes synchronization decisions based on coherence yield.

    Key principle: Synchronization should occur ONLY when
    coherence gain exceeds entropy cost.
    """

    def __init__(self, sync_threshold: float = 1.0,
                 max_sync_frequency: float = 1.0):
        self.sync_threshold = sync_threshold
        self.max_sync_frequency = max_sync_frequency
        self._decisions: List[SyncDecision] = []
        self._sync_counts: Dict[str, int] = defaultdict(int)
        self._last_sync: Dict[str, str] = {}

    def should_sync(self, obs_a: str, obs_b: str,
                    coherence_gain: float, entropy_cost: float) -> SyncDecision:
        """
        Determine if synchronization should occur.

        Returns a SyncDecision with approval status and reasoning.
        """
        pair_key = f"{min(obs_a, obs_b)}-{max(obs_a, obs_b)}"

        # Check if coherence gain exceeds cost
        if entropy_cost < 1e-10:
            approved = coherence_gain > 0
            reason = "No entropy cost, sync approved" if approved else "No coherence gain"
        else:
            yield_value = coherence_gain / entropy_cost
            approved = yield_value > self.sync_threshold
            reason = (
                f"Yield {yield_value:.3f} > threshold {self.sync_threshold}"
                if approved else
                f"Yield {yield_value:.3f} <= threshold {self.sync_threshold}"
            )

        decision = SyncDecision(obs_a, obs_b, coherence_gain, entropy_cost,
                                approved, reason)
        self._decisions.append(decision)

        if approved:
            self._sync_counts[pair_key] += 1
            self._last_sync[pair_key] = datetime.now(timezone.utc).isoformat()

        return decision

    def optimal_sync_frequency(self, cluster: List[str]) -> float:
        """
        Calculate optimal sync frequency for a cluster.
        Based on historical yield data for the cluster's pairs.
        """
        if len(cluster) < 2:
            return 0.0

        pair_yields = []
        for i in range(len(cluster)):
            for j in range(i + 1, len(cluster)):
                pair_key = f"{min(cluster[i], cluster[j])}-{max(cluster[i], cluster[j])}"
                pair_decisions = [
                    d for d in self._decisions
                    if f"{min(d.obs_a, d.obs_b)}-{max(d.obs_a, d.obs_b)}" == pair_key
                    and d.approved
                ]
                if pair_decisions:
                    avg_yield = sum(d.yield_value for d in pair_decisions) / len(pair_decisions)
                    pair_yields.append(avg_yield)

        if not pair_yields:
            return self.max_sync_frequency

        avg_yield = sum(pair_yields) / len(pair_yields)
        # Higher yield = can sync more frequently
        return min(self.max_sync_frequency, avg_yield / self.sync_threshold)

    def sync_efficiency(self) -> float:
        """Ratio of approved syncs to total sync decisions."""
        if not self._decisions:
            return 1.0
        approved = sum(1 for d in self._decisions if d.approved)
        return round(approved / len(self._decisions), 3)

    def avg_yield(self) -> float:
        """Average coherence yield across approved syncs."""
        approved = [d for d in self._decisions if d.approved]
        if not approved:
            return 0.0
        return round(sum(d.yield_value for d in approved) / len(approved), 3)

    def get_over_syncing_pairs(self, threshold: float = 0.5) -> List[dict]:
        """Identify pairs that sync too frequently relative to yield."""
        over_syncing = []
        for pair_key, count in self._sync_counts.items():
            pair_decisions = [
                d for d in self._decisions
                if f"{min(d.obs_a, d.obs_b)}-{max(d.obs_a, d.obs_b)}" == pair_key
            ]
            if pair_decisions:
                avg_yield = sum(d.yield_value for d in pair_decisions) / len(pair_decisions)
                if avg_yield < threshold:
                    over_syncing.append({
                        "pair": pair_key,
                        "sync_count": count,
                        "avg_yield": round(avg_yield, 3),
                        "recommendation": "reduce_sync_frequency",
                    })
        return over_syncing

    def get_stats(self) -> dict:
        return {
            "total_decisions": len(self._decisions),
            "approved_syncs": sum(1 for d in self._decisions if d.approved),
            "sync_efficiency": self.sync_efficiency(),
            "avg_yield": self.avg_yield(),
            "unique_pairs": len(self._sync_counts),
            "over_syncing_pairs": len(self.get_over_syncing_pairs()),
        }
