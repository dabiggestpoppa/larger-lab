"""Budget domain and enforcement (P2-C08; Book V 12.7, directive §27-28).

Budget law:

- budgets are explicit, hierarchical, and dimensioned (LLM tokens/cost,
  tool/API calls, search pages, candidate count, sandbox time, wall-clock,
  artifact bytes, attempt count — canon 12.7 Budget Dimensions, subset P2);
- child allocations cannot exceed the parent's remaining budget;
- retries consume budget; recovery never resets consumed budget;
- exhaustion is explicit state + event, never silent continuation;
- only an explicit, durable approval can raise a budget, and the increase
  cannot exceed the approval's scope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Dict, Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import require_identifier, require_non_empty_str

__all__ = [
    "BudgetDimension",
    "BudgetState",
    "Budget",
    "BudgetLedgerPort",
    "BudgetExhaustedError",
]


class BudgetDimension(StrEnum):
    """P2-supported dimensions (canon 12.7 subset; extensible via policy)."""

    ATTEMPTS = "attempts"
    TOOL_CALLS = "tool_calls"
    NETWORK_REQUESTS = "network_requests"
    SANDBOX_EXECUTIONS = "sandbox_executions"
    WALL_CLOCK_SECONDS = "wall_clock_seconds"
    ARTIFACT_BYTES = "artifact_bytes"
    COST_UNITS = "cost_units"


class BudgetState(StrEnum):
    ACTIVE = "ACTIVE"
    EXHAUSTED = "EXHAUSTED"
    EXCEEDED = "EXCEEDED"


class BudgetExhaustedError(QcaeValidationError):
    """Raised when an action would exceed a budget; exhaustion is explicit."""


@dataclass(frozen=True)
class Budget(SerializableRecord):
    """One budget scope (job or step) across dimensions."""

    SCHEMA_VERSION = 1

    budget_id: str
    owner_kind: str  # "job" | "step"
    owner_id: str
    parent_budget_id: str = ""

    allocation: Dict[str, int] = field(default_factory=dict)
    used: Dict[str, int] = field(default_factory=dict)

    state: BudgetState = BudgetState.ACTIVE

    _COERCIONS = {"state": lambda v: coerce_enum(v, BudgetState)}

    def validate(self) -> None:
        require_identifier(self.budget_id, "budget_id")
        if self.owner_kind not in ("job", "step"):
            raise QcaeValidationError("owner_kind must be 'job' or 'step'")
        require_identifier(self.owner_id, "owner_id")
        if not isinstance(self.allocation, dict) or not isinstance(self.used, dict):
            raise QcaeValidationError("allocation/used must be dicts")
        for dim, amount in self.allocation.items():
            require_non_empty_str(dim, "dimension")
            if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
                raise QcaeValidationError(
                    f"allocation for {dim!r} must be a non-negative int"
                )
        for dim, amount in self.used.items():
            if dim not in self.allocation:
                raise QcaeValidationError(
                    f"used dimension {dim!r} is not allocated"
                )
            if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
                raise QcaeValidationError(f"used for {dim!r} must be a non-negative int")
            if amount > self.allocation[dim]:
                raise QcaeValidationError(
                    f"used {amount} exceeds allocation {self.allocation[dim]} for {dim!r}"
                )
        # State/used consistency: any dimension at its limit means exhausted.
        if self.state is BudgetState.ACTIVE and self.allocation:
            for dim, limit in self.allocation.items():
                if limit > 0 and self.used.get(dim, 0) >= limit:
                    raise QcaeValidationError(
                        f"budget dimension {dim!r} is exhausted but state is ACTIVE"
                    )


def make_budget(**kwargs) -> Budget:
    budget = Budget(**kwargs)
    budget.validate()
    return budget
