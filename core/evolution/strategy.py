"""Phase 1.7.5 — Strategy Mutation Engine. Evolves reasoning strategies."""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.evolution.strategy")


class StrategyMutationEngine:
    """Evolves reasoning strategies based on performance."""

    STRATEGIES = [
        "chain_of_thought",
        "tree_of_thought",
        "debate_reasoning",
        "reflection_reasoning",
        "self_consistency",
    ]

    def __init__(self):
        self._strategy_scores: Dict[str, float] = {s: 0.5 for s in self.STRATEGIES}
        self._usage_count: Dict[str, int] = {s: 0 for s in self.STRATEGIES}

    def record_result(self, strategy: str, success: bool, quality_score: float = 0.5):
        if strategy not in self._strategy_scores:
            return
        self._usage_count[strategy] = self._usage_count.get(strategy, 0) + 1
        # Exponential moving average
        alpha = 0.3
        self._strategy_scores[strategy] = (1 - alpha) * self._strategy_scores[strategy] + alpha * quality_score

    def get_best_strategy(self) -> str:
        return max(self._strategy_scores, key=self._strategy_scores.get)

    def suggest_mutation(self) -> Optional[str]:
        """Suggest trying a different strategy if current one is underperforming."""
        best = self.get_best_strategy()
        worst = min(self._strategy_scores, key=self._strategy_scores.get)
        if self._strategy_scores[worst] < 0.3 and self._usage_count.get(worst, 0) > 5:
            return f"Consider retiring '{worst}' strategy (score={self._strategy_scores[worst]:.2f})"
        return None

    def get_stats(self) -> Dict[str, Any]:
        return {
            "strategy_scores": dict(self._strategy_scores),
            "usage_counts": dict(self._usage_count),
            "best_strategy": self.get_best_strategy(),
        }
