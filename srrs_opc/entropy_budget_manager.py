"""
Entropy Budget Manager
========================
Phase 9 Component 2: Explicit entropy budgeting per observer, per collar, per global.

Hierarchical budget enforcement:
- Global budget (system-wide entropy cap)
- Per-collar budget (overlap region entropy cap)
- Per-observer budget (individual observer entropy cap)

Over-budget operations are compressed, delayed, or rejected.

Integration: LongTermDriftTracker, CollarMetrics
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class EntropyBudget:
    """Entropy budget for a single entity (observer, collar, or global)."""

    def __init__(self, entity_id: str, initial_budget: float = 100.0,
                 replenish_rate: float = 1.0, min_budget: float = 10.0):
        self.entity_id = entity_id
        self.budget = initial_budget
        self.max_budget = initial_budget
        self.consumed = 0.0
        self.replenish_rate = replenish_rate
        self.min_budget = min_budget
        self._history: List[dict] = []

    def consume(self, amount: float) -> Tuple[bool, float]:
        """
        Consume entropy budget.
        Returns: (within_budget, remaining_budget)
        """
        actual = min(amount, self.budget - self.min_budget)
        if actual < 0:
            actual = 0
        self.budget -= actual
        self.consumed += actual
        self._history.append({
            "action": "consume",
            "requested": amount,
            "actual": actual,
            "remaining": self.budget,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        within = actual >= amount * 0.9  # Allow 10% overage
        return within, self.budget

    def replenish(self, coherence_contribution: float):
        """Replenish budget proportional to coherence contribution."""
        amount = self.replenish_rate * max(0, coherence_contribution)
        old_budget = self.budget
        self.budget = min(self.max_budget, self.budget + amount)
        actual_replenish = self.budget - old_budget
        if actual_replenish > 0:
            self._history.append({
                "action": "replenish",
                "amount": round(actual_replenish, 4),
                "budget_after": self.budget,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    def utilization(self) -> float:
        """Current budget utilization (0.0 = full, 1.0 = depleted)."""
        if self.max_budget <= self.min_budget:
            return 1.0
        usable = self.max_budget - self.min_budget
        used = self.max_budget - self.budget
        return min(1.0, max(0.0, used / usable))

    def is_critical(self, threshold: float = 0.8) -> bool:
        """Check if budget is critically low."""
        return self.utilization() > threshold

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "budget": round(self.budget, 2),
            "max_budget": self.max_budget,
            "consumed": round(self.consumed, 2),
            "utilization": round(self.utilization(), 3),
            "is_critical": self.is_critical(),
        }


class EntropyBudgetManager:
    """
    Hierarchical entropy budget management.

    Three tiers:
    - Global: system-wide entropy cap
    - Collar: per-overlap-region entropy cap
    - Observer: per-observer entropy cap
    """

    def __init__(self, global_budget: float = 1000.0,
                 collar_budget: float = 100.0,
                 observer_budget: float = 50.0):
        self._global = EntropyBudget("global", global_budget)
        self._collar_budgets: Dict[str, EntropyBudget] = {}
        self._observer_budgets: Dict[str, EntropyBudget] = {}
        self._default_collar_budget = collar_budget
        self._default_observer_budget = observer_budget

    def _get_or_create_collar(self, collar_id: str) -> EntropyBudget:
        if collar_id not in self._collar_budgets:
            self._collar_budgets[collar_id] = EntropyBudget(
                collar_id, self._default_collar_budget)
        return self._collar_budgets[collar_id]

    def _get_or_create_observer(self, observer_id: str) -> EntropyBudget:
        if observer_id not in self._observer_budgets:
            self._observer_budgets[observer_id] = EntropyBudget(
                observer_id, self._default_observer_budget)
        return self._observer_budgets[observer_id]

    def consume(self, entropy_cost: float, observer_id: Optional[str] = None,
                collar_id: Optional[str] = None) -> dict:
        """
        Consume entropy budget at all applicable levels.
        Returns status dict showing budget state after consumption.
        """
        result = {"global": None, "collar": None, "observer": None, "approved": True}

        # Global consumption
        within, remaining = self._global.consume(entropy_cost)
        result["global"] = {"within_budget": within, "remaining": round(remaining, 2)}
        if not within:
            result["approved"] = False

        # Collar consumption
        if collar_id:
            collar_budget = self._get_or_create_collar(collar_id)
            within, remaining = collar_budget.consume(entropy_cost)
            result["collar"] = {"within_budget": within, "remaining": round(remaining, 2), "id": collar_id}
            if not within:
                result["approved"] = False

        # Observer consumption
        if observer_id:
            obs_budget = self._get_or_create_observer(observer_id)
            within, remaining = obs_budget.consume(entropy_cost)
            result["observer"] = {"within_budget": within, "remaining": round(remaining, 2), "id": observer_id}
            if not within:
                result["approved"] = False

        return result

    def replenish(self, coherence_contribution: float,
                  observer_id: Optional[str] = None,
                  collar_id: Optional[str] = None):
        """Replenish budgets proportional to coherence contribution."""
        self._global.replenish(coherence_contribution)
        if collar_id:
            self._get_or_create_collar(collar_id).replenish(coherence_contribution)
        if observer_id:
            self._get_or_create_observer(observer_id).replenish(coherence_contribution)

    def get_budget_state(self, observer_id: Optional[str] = None,
                         collar_id: Optional[str] = None) -> dict:
        """Get current budget state."""
        state = {"global": self._global.to_dict()}
        if collar_id and collar_id in self._collar_budgets:
            state["collar"] = self._collar_budgets[collar_id].to_dict()
        if observer_id and observer_id in self._observer_budgets:
            state["observer"] = self._observer_budgets[observer_id].to_dict()
        return state

    def get_critical_budgets(self, threshold: float = 0.8) -> List[dict]:
        """Get all budgets that are critically low."""
        critical = []
        if self._global.is_critical(threshold):
            critical.append(self._global.to_dict())
        for budget in self._collar_budgets.values():
            if budget.is_critical(threshold):
                critical.append(budget.to_dict())
        for budget in self._observer_budgets.values():
            if budget.is_critical(threshold):
                critical.append(budget.to_dict())
        return critical

    def get_stats(self) -> dict:
        return {
            "global": self._global.to_dict(),
            "total_collar_budgets": len(self._collar_budgets),
            "total_observer_budgets": len(self._observer_budgets),
            "critical_budgets": len(self.get_critical_budgets()),
        }
