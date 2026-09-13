"""Bloc 1 access classes and the frozen free-only runtime dependency gate.

The gate (F9 / Bloc 1 §7, B1-T20..T24) is:

    access_class ∈ {FREE_AUTOMATED, FREE_LIMITED_AUTOMATED}
    cost_usd_required == 0
    payment_method_required == False
    staking_required == False
    transaction_required == False

A free API key alone (`api_key_required=True`) does NOT make a source paid
(B1-T24).  If a free endpoint changes to paid, the operator must run an
ACCESS_REVIEW_REQUIRED review; this code never pays.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .enums import AccessClass

#: Access classes eligible for required automated ingestion (Bloc 1 §7).
REQUIRED_AUTOMATED_ELIGIBLE: frozenset[AccessClass] = frozenset(
    {AccessClass.FREE_AUTOMATED, AccessClass.FREE_LIMITED_AUTOMATED}
)


class FreeOnlyPolicy(BaseModel):
    """Cost/access contract for a provider or provider capability."""

    model_config = ConfigDict(extra="forbid")

    access_class: AccessClass = AccessClass.UNVERIFIED
    verified_at: datetime | None = None
    verification_method: str | None = None
    cost_usd_required: int = 0
    payment_method_required: bool = False
    staking_required: bool = False
    transaction_required: bool = False
    api_key_required: bool | None = None
    rate_limit: str | None = None
    historical_access_claimed: bool = False
    historical_access_verified: bool = False
    terms_reference: str | None = None

    @property
    def is_eligible_required_automated(self) -> bool:
        """True when this policy satisfies the frozen F9 gate."""
        return is_free_only_eligible(self)


def free_only_violations(policy: FreeOnlyPolicy) -> list[str]:
    """Return a list of F9 violations; empty list means the policy is eligible."""
    violations: list[str] = []
    if policy.access_class not in REQUIRED_AUTOMATED_ELIGIBLE:
        violations.append(
            f"access_class={policy.access_class.value} not in "
            "{FREE_AUTOMATED, FREE_LIMITED_AUTOMATED}"
        )
    if policy.cost_usd_required != 0:
        violations.append(f"cost_usd_required={policy.cost_usd_required} != 0")
    if policy.payment_method_required:
        violations.append("payment_method_required=True")
    if policy.staking_required:
        violations.append("staking_required=True")
    if policy.transaction_required:
        violations.append("transaction_required=True")
    return violations


def is_free_only_eligible(policy: FreeOnlyPolicy) -> bool:
    """Frozen F9 eligibility predicate (B1-T20..T24)."""
    return not free_only_violations(policy)
