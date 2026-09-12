"""Free-only access gate (01 §23 / 03 §12, SENSOR-B3-I02).

Hard requirement: the gate executes BEFORE any transport/network call.  If the
frozen F9 policy (Bloc 1) or the adapter auth vocabulary (Bloc 3) is not
satisfied, the adapter FAILS CLOSED with `AccessClassViolation` and no request
is sent.

Two inputs are combined:

1. `FreeOnlyPolicy` (Bloc 1 frozen gate): cost_usd_required == 0,
   payment_method_required == False, staking_required == False,
   transaction_required == False, access_class in {FREE_AUTOMATED,
   FREE_LIMITED_AUTOMATED}.
2. `AdapterAuthMode` (Bloc 3): must be in ALLOWED_AUTH_MODES
   (NO_AUTH / FREE_API_KEY / OPTIONAL_PUBLIC_KEY).  PAID_KEY, TRADING_KEY,
   WITHDRAWAL_PERMISSION, SIGNING_SECRET, WALLET_SIGNATURE, STAKING_UNLOCK
   and TRANSACTION_REQUIRED are hard blocks.

Uncertain access classification (UNVERIFIED) also fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...contracts.access import FreeOnlyPolicy, free_only_violations
from ...contracts.enums import SensorFamily
from .enums import ALLOWED_AUTH_MODES, AdapterAuthMode, Retryability
from .errors import AccessClassViolation


@dataclass(frozen=True)
class AccessDecision:
    """Result of an access-gate evaluation."""

    provider_id: str
    allowed: bool
    violations: tuple[str, ...] = ()
    auth_mode: AdapterAuthMode = AdapterAuthMode.UNVERIFIED


def evaluate_access(
    provider_id: str,
    policy: FreeOnlyPolicy,
    auth_mode: AdapterAuthMode,
) -> AccessDecision:
    """Evaluate the free-only gate.  Raises nothing; returns a decision.

    Callers must use `assert_free_only_access` for the raise-on-failure path.
    """
    violations: list[str] = []

    for violation in free_only_violations(policy):
        violations.append(f"free-only: {violation}")

    if policy.access_class.value == "UNVERIFIED":
        violations.append("free-only: access_class UNVERIFIED (fail closed)")
    if auth_mode not in ALLOWED_AUTH_MODES:
        violations.append(
            f"auth: {auth_mode.value} is not an allowed acquisition auth mode "
            f"(allowed={sorted(a.value for a in ALLOWED_AUTH_MODES)})"
        )

    return AccessDecision(
        provider_id=provider_id,
        allowed=not violations,
        violations=tuple(violations),
        auth_mode=auth_mode,
    )


def assert_free_only_access(
    provider_id: str,
    policy: FreeOnlyPolicy,
    auth_mode: AdapterAuthMode,
    sensor_family: SensorFamily | None = None,
) -> None:
    """Free-only gate that raises `AccessClassViolation` when not satisfied.

    MUST run before any transport call.  No paid/trading/staking path is ever
    used; uncertainty fails closed.
    """
    decision = evaluate_access(provider_id, policy, auth_mode)
    if not decision.allowed:
        raise AccessClassViolation(
            provider_id=provider_id,
            sensor_family=sensor_family or SensorFamily.MECHANICAL_TRADE,
            detail="; ".join(decision.violations),
            retryability=Retryability.TERMINAL,
        )
