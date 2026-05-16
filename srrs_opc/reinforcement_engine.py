"""
Reinforcement Weighting Engine
================================
Phase 5: Anchor weight increases with recurrence, decays without reinforcement.

Principles:
- Persistence weight increases with recurrence (repeated patterns strengthen)
- Decay without reinforcement (unused anchors weaken over time)
- Strategic significance boost (operator-aligned patterns get extra weight)
- Continuity influence (anchors that help reconstruction get boosted)
"""

import json
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict


class ReinforcementRecord:
    """Tracks reinforcement history for a single anchor."""

    def __init__(self, anchor_id: str, initial_weight: float = 0.5):
        self.anchor_id = anchor_id
        self.weight = initial_weight
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.last_reinforced = self.created_at
        self.reinforcement_count = 0
        self.decay_count = 0
        self.access_count = 0

    def reinforce(self, boost: float = 0.1):
        """Increase weight due to recurrence or strategic significance."""
        self.weight = min(1.0, self.weight + boost * (1 - self.weight))
        self.reinforcement_count += 1
        self.last_reinforced = datetime.now(timezone.utc).isoformat()

    def decay(self, rate: float = 0.01):
        """Decrease weight due to lack of reinforcement."""
        self.weight = max(0.05, self.weight - rate * self.weight)
        self.decay_count += 1

    def access(self):
        """Record an access (read) of this anchor."""
        self.access_count += 1

    def to_dict(self) -> dict:
        return {
            "anchor_id": self.anchor_id,
            "weight": round(self.weight, 3),
            "reinforcement_count": self.reinforcement_count,
            "decay_count": self.decay_count,
            "access_count": self.access_count,
            "last_reinforced": self.last_reinforced,
        }


class ReinforcementEngine:
    """
    Manages anchor reinforcement weighting over time.

    Anchors that are repeatedly accessed or match operator patterns gain weight.
    Anchors that are never accessed slowly decay.
    """

    def __init__(self, decay_rate: float = 0.01, reinforcement_boost: float = 0.1,
                 strategic_boost: float = 0.15):
        self.decay_rate = decay_rate
        self.reinforcement_boost = reinforcement_boost
        self.strategic_boost = strategic_boost
        self._records: Dict[str, ReinforcementRecord] = {}
        self._operator_patterns: Dict[str, int] = defaultdict(int)

    def register(self, anchor_id: str, initial_weight: float = 0.5) -> ReinforcementRecord:
        """Register a new anchor for reinforcement tracking."""
        if anchor_id not in self._records:
            self._records[anchor_id] = ReinforcementRecord(anchor_id, initial_weight)
        return self._records[anchor_id]

    def reinforce(self, anchor_id: str, is_strategic: bool = False):
        """Reinforce an anchor (it was accessed and found useful)."""
        record = self._records.get(anchor_id)
        if not record:
            record = self.register(anchor_id)

        boost = self.strategic_boost if is_strategic else self.reinforcement_boost
        record.reinforce(boost)
        record.access()

    def decay_all(self):
        """Apply decay to all anchors (call periodically)."""
        for record in self._records.values():
            record.decay(self.decay_rate)

    def record_operator_pattern(self, pattern: str):
        """Record an operator behavior pattern for trajectory modeling."""
        self._operator_patterns[pattern] += 1

    def get_strongest(self, limit: int = 10) -> List[dict]:
        """Get the highest-weight anchors."""
        sorted_records = sorted(self._records.values(), key=lambda r: r.weight, reverse=True)
        return [r.to_dict() for r in sorted_records[:limit]]

    def get_weakest(self, limit: int = 10) -> List[dict]:
        """Get the lowest-weight anchors (candidates for pruning)."""
        sorted_records = sorted(self._records.values(), key=lambda r: r.weight)
        return [r.to_dict() for r in sorted_records[:limit]]

    def get_operator_trajectory(self) -> dict:
        """Get the operator's strategic trajectory based on pattern frequency."""
        if not self._operator_patterns:
            return {"status": "no_data"}

        sorted_patterns = sorted(self._operator_patterns.items(), key=lambda x: x[1], reverse=True)
        total = sum(self._operator_patterns.values())

        return {
            "dominant_patterns": [{"pattern": p, "count": c, "ratio": round(c / total, 2)} for p, c in sorted_patterns[:10]],
            "total_observations": total,
            "unique_patterns": len(self._operator_patterns),
        }

    def get_stats(self) -> dict:
        if not self._records:
            return {"status": "empty"}

        weights = [r.weight for r in self._records.values()]
        return {
            "total_anchors": len(self._records),
            "avg_weight": round(sum(weights) / len(weights), 3),
            "max_weight": round(max(weights), 3),
            "min_weight": round(min(weights), 3),
            "total_reinforcements": sum(r.reinforcement_count for r in self._records.values()),
            "total_decays": sum(r.decay_count for r in self._records.values()),
            "operator_patterns": len(self._operator_patterns),
        }


if __name__ == "__main__":
    engine = ReinforcementEngine()

    # Simulate reinforcement patterns
    for i in range(50):
        engine.reinforce("anchor_core_1", is_strategic=True)  # Core anchor, frequently used
        engine.reinforce("anchor_core_2")  # Regular anchor
        if i % 5 == 0:
            engine.reinforce("anchor_rare")  # Rarely used

        # Record operator patterns
        engine.record_operator_pattern("low_redundancy")
        engine.record_operator_pattern("deterministic_execution")
        if i % 3 == 0:
            engine.record_operator_pattern("mean_reversion")

        # Apply decay every cycle
        engine.decay_all()

    print("Strongest anchors:")
    for a in engine.get_strongest(5):
        print(f"  {a['anchor_id']}: weight={a['weight']}, reinforced={a['reinforcement_count']}x")

    print(f"\nOperator trajectory:")
    print(json.dumps(engine.get_operator_trajectory(), indent=2))

    print(f"\nStats: {json.dumps(engine.get_stats(), indent=2)}")
