"""Budget enforcement service (P2-C08; directive §28 conservation law).

The enforcement service is engine-agnostic (port-based; SQLite adapter in
infrastructure per the architecture guard). Conservation rules:

- a child allocation is admissible only against the parent's remaining budget;
- charging consumes allocation; retry charges accumulate (recovery never
  resets consumed budget);
- approving an increase is a durable, scoped change recorded through the
  ledger, not a silent reset;
- exhaustion raises BudgetExhaustedError, which the engine turns into an
  explicit BUDGET_EXHAUSTED failure state + event.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Protocol

from qcae.core.errors import QcaeValidationError
from qcae.orchestration.orchestrator.budgets import (
    Budget,
    BudgetDimension,
    BudgetExhaustedError,
    BudgetState,
)

__all__ = ["BudgetLedger", "BudgetLedgerPort", "BudgetService"]


class BudgetLedgerPort(Protocol):
    """Durable budget persistence port (engine adapter in infrastructure)."""

    def save(self, budget: Budget) -> None: ...

    def get(self, budget_id: str) -> Optional[Budget]: ...

    def delete(self, budget_id: str) -> None: ...


class BudgetService:
    """Hierarchical budget enforcement over a durable ledger."""

    def __init__(self, ledger: BudgetLedgerPort) -> None:
        self._ledger = ledger

    # -- creation ------------------------------------------------------------

    def create_job_budget(
        self, budget_id: str, job_id: str, allocation: Dict[str, int]
    ) -> Budget:
        budget = Budget(
            budget_id=budget_id, owner_kind="job", owner_id=job_id,
            allocation=dict(allocation), used={},
        )
        budget.validate()
        self._ledger.save(budget)
        return budget

    def create_step_budget(
        self, budget_id: str, step_id: str, job_budget_id: str,
        allocation: Dict[str, int],
    ) -> Budget:
        parent = self._require(job_budget_id)
        remaining = self.remaining(parent)
        for dim, amount in allocation.items():
            if amount > remaining.get(dim, 0):
                raise BudgetExhaustedError(
                    f"step allocation {amount} for {dim!r} exceeds parent "
                    f"remaining {remaining.get(dim, 0)} (conservation law)"
                )
        budget = Budget(
            budget_id=budget_id, owner_kind="step", owner_id=step_id,
            parent_budget_id=job_budget_id, allocation=dict(allocation), used={},
        )
        budget.validate()
        self._ledger.save(budget)
        return budget

    # -- charging ------------------------------------------------------------

    def remaining(self, budget: Budget) -> Dict[str, int]:
        return {
            dim: limit - budget.used.get(dim, 0)
            for dim, limit in budget.allocation.items()
        }

    def charge(self, budget_id: str, dimension: str, amount: int) -> Budget:
        """Consume budget; raises BudgetExhaustedError on overrun."""
        if amount < 0:
            raise QcaeValidationError("charge amount must be non-negative")
        budget = self._require(budget_id)
        limit = budget.allocation.get(dimension)
        if limit is None:
            raise QcaeValidationError(
                f"dimension {dimension!r} is not allocated in {budget_id!r}"
            )
        used = budget.used.get(dimension, 0)
        if used + amount > limit:
            new_used = dict(budget.used)
            new_used[dimension] = limit
            exhausted = Budget(
                budget_id=budget.budget_id,
                owner_kind=budget.owner_kind,
                owner_id=budget.owner_id,
                parent_budget_id=budget.parent_budget_id,
                allocation=budget.allocation,
                used=new_used,
                state=BudgetState.EXHAUSTED,
            )
            self._ledger.save(exhausted)
            raise BudgetExhaustedError(
                f"charge of {amount} {dimension!r} exceeds remaining "
                f"{limit - used} in {budget_id!r}"
            )
        new_used = dict(budget.used)
        new_used[dimension] = used + amount
        charged = Budget(
            budget_id=budget.budget_id,
            owner_kind=budget.owner_kind,
            owner_id=budget.owner_id,
            parent_budget_id=budget.parent_budget_id,
            allocation=budget.allocation,
            used=new_used,
            state=BudgetState.EXHAUSTED
            if new_used[dimension] >= limit and limit > 0
            else BudgetState.ACTIVE,
        )
        self._ledger.save(charged)
        return charged

    def charge_job_for_step(self, job_budget_id: str, step_budget_id: str) -> None:
        """Roll a step's consumption up into its job budget (attempt charge)."""
        step = self._require(step_budget_id)
        job = self._require(job_budget_id)
        for dim, amount in step.used.items():
            job_limit = job.allocation.get(dim)
            if job_limit is None:
                raise QcaeValidationError(
                    f"job budget {job_budget_id!r} does not allocate {dim!r}"
                )
            job_used = job.used.get(dim, 0)
            if job_used + amount > job_limit:
                # Job-level exhaustion wins; persist the cap and raise.
                new_used = dict(job.used)
                new_used[dim] = job_limit
                self._ledger.save(Budget(
                    budget_id=job.budget_id, owner_kind=job.owner_kind,
                    owner_id=job.owner_id,
                    parent_budget_id=job.parent_budget_id,
                    allocation=job.allocation, used=new_used,
                    state=BudgetState.EXHAUSTED,
                ))
                raise BudgetExhaustedError(
                    f"step consumption of {amount} {dim!r} exceeds job budget "
                    f"remaining {job_limit - job_used}"
                )
            new_used = dict(job.used)
            new_used[dim] = job_used + amount
            self._ledger.save(Budget(
                budget_id=job.budget_id, owner_kind=job.owner_kind,
                owner_id=job.owner_id,
                parent_budget_id=job.parent_budget_id,
                allocation=job.allocation, used=new_used,
                state=BudgetState.EXHAUSTED
                if new_used[dim] >= job_limit and job_limit > 0
                else BudgetState.ACTIVE,
            ))

    # -- approved increases --------------------------------------------------

    def apply_approved_increase(
        self, budget_id: str, dimension: str, additional: int,
        *, approval_ref: str,
    ) -> Budget:
        """Raise a limit only through a durable approval reference."""
        if not approval_ref:
            raise QcaeValidationError(
                "budget increase requires a durable approval_ref (no silent resets)"
            )
        if additional <= 0:
            raise QcaeValidationError("increase must be positive")
        budget = self._require(budget_id)
        new_allocation = dict(budget.allocation)
        new_allocation[dimension] = budget.allocation.get(dimension, 0) + additional
        increased = Budget(
            budget_id=budget.budget_id,
            owner_kind=budget.owner_kind,
            owner_id=budget.owner_id,
            parent_budget_id=budget.parent_budget_id,
            allocation=new_allocation,
            used=dict(budget.used),
            state=BudgetState.ACTIVE,
        )
        increased.validate()
        self._ledger.save(increased)
        return increased

    # -- recovery ------------------------------------------------------------

    def restore(self, budget: Budget) -> None:
        """Restore exact budget state after backup/restore; no resets."""
        budget.validate()
        self._ledger.save(budget)

    def snapshot(self, budget_id: str) -> Optional[Budget]:
        return self._ledger.get(budget_id)

    def delete(self, budget_id: str) -> None:
        self._ledger.delete(budget_id)

    def _require(self, budget_id: str) -> Budget:
        budget = self._ledger.get(budget_id)
        if budget is None:
            raise QcaeValidationError(f"unknown budget {budget_id!r}")
        return budget
