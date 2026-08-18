"""QL-EXEC-R1 — derived execution authority (pure, fail-closed, DEFAULT DENY).

A config profile can never declare itself READY. Effective authority is
derived from static profile + observed truth + runtime state + compatibility.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .account import AccountObservedState, AccountProfile
from .compatibility import CompatibilityState
from .enums import AccountRole, DesiredState, ExecutionTransport
from .hashing import config_hash
from .profiles import RuntimeState
from .types import utcnow_iso


def transport_requires_authentication(transport: ExecutionTransport) -> bool:
    """Externally authenticated transports must prove identity."""
    return transport in (
        ExecutionTransport.MT5,
        ExecutionTransport.TRADELOCKER_FUTURE,
    )


def transport_requires_secret(transport: ExecutionTransport) -> bool:
    """Externally authenticated transports require a secret reference."""
    return transport_requires_authentication(transport)


def identity_gate(profile: AccountProfile, observed: AccountObservedState) -> tuple[bool, list[str]]:
    """Explicit identity comparison. Never infer identity from connection.

    Returns (matched, blockers). Empty blockers == matched.
    """
    blockers: list[str] = []
    needs_auth = transport_requires_authentication(profile.transport)

    # Broker company (required field; compared case-insensitively).
    if observed.observed_broker_company:
        if profile.broker_company.casefold() != observed.observed_broker_company.casefold():
            blockers.append("identity mismatch: broker company")
    elif needs_auth:
        blockers.append("identity not verifiable: broker company missing")

    # Server.
    if profile.expected_server:
        if observed.observed_server and observed.observed_server != profile.expected_server:
            blockers.append("identity mismatch: server")
        elif not observed.observed_server:
            blockers.append("identity not verifiable: server missing")
    elif needs_auth:
        blockers.append("missing identity expectation: server")

    # Environment.
    if observed.observed_environment is None:
        if needs_auth:
            blockers.append("identity not verifiable: environment missing")
    elif observed.observed_environment != profile.expected_environment:
        blockers.append("identity mismatch: environment")

    # Currency (compared when expected).
    if profile.expected_currency:
        if observed.observed_currency and observed.observed_currency != profile.expected_currency:
            blockers.append("identity mismatch: currency")
        elif not observed.observed_currency:
            blockers.append("identity not verifiable: currency missing")

    # Account mode (compared when expected).
    if profile.expected_account_mode:
        if observed.observed_account_mode and observed.observed_account_mode != profile.expected_account_mode:
            blockers.append("identity mismatch: account mode")
        elif not observed.observed_account_mode:
            blockers.append("identity not verifiable: account mode missing")

    # Account identifier (compared when expected).
    if profile.expected_account_identifier:
        if (
            observed.observed_account_identifier
            and observed.observed_account_identifier != profile.expected_account_identifier
        ):
            blockers.append("identity mismatch: account identifier")
        elif not observed.observed_account_identifier:
            blockers.append("identity not verifiable: account identifier missing")

    # Terminal / session binding (compared when expected).
    if profile.terminal_or_session_binding:
        if (
            observed.observed_terminal_binding
            and observed.observed_terminal_binding != profile.terminal_or_session_binding
        ):
            blockers.append("identity mismatch: terminal/session binding")
        elif not observed.observed_terminal_binding:
            blockers.append("identity not verifiable: terminal binding missing")

    return (not blockers), blockers


@dataclass(frozen=True)
class ExecutionAuthorityDecision:
    """Effective execution authority. DEFAULT DENY."""

    can_observe: bool = False
    can_manage_owned_existing_risk: bool = False
    can_submit_new_risk: bool = False
    can_close_owned_risk: bool = False
    can_modify_foreign_risk: bool = False  # always False
    reasons: tuple[str, ...] = field(default_factory=tuple)
    decision_timestamp: str = ""
    profile_hash: str = ""


_DIRECT_EXECUTION_ROLES = (
    AccountRole.EXCLUSIVE_STRATEGY_MASTER,
    AccountRole.PORTFOLIO_MASTER,
)


def derive_execution_authority(
    profile: AccountProfile,
    observed_state: AccountObservedState,
    runtime_state: RuntimeState,
    compatibility_state: CompatibilityState,
) -> ExecutionAuthorityDecision:
    """Pure fail-closed derivation of effective execution authority."""

    identity_ok, identity_blockers = identity_gate(profile, observed_state)

    can_observe = observed_state.transport_connected

    runtime_running = runtime_state.desired_state is DesiredState.RUNNING
    not_safety_blocked = not runtime_state.safety_blocked

    # Managing/closing owned existing risk requires connection, auth, identity,
    # and an alive, unblocked runtime. It does NOT require new-risk admission.
    can_manage_owned = (
        observed_state.transport_connected
        and observed_state.authenticated
        and identity_ok
        and runtime_running
        and not_safety_blocked
    )

    # New risk requires everything above plus operator intent, role, secret,
    # reconciliation, and compatibility.
    blockers: list[str] = []

    if not profile.operator_execution_requested:
        blockers.append("operator execution not requested")
    if profile.account_role not in _DIRECT_EXECUTION_ROLES:
        blockers.append(
            f"account role {profile.account_role.value} cannot submit direct orders"
        )
    if transport_requires_secret(profile.transport) and (
        profile.secret_reference is None or not profile.secret_reference.is_present()
    ):
        blockers.append("missing secret reference for authenticated transport")
    if not observed_state.transport_connected:
        blockers.append("transport not connected")
    if not observed_state.authenticated:
        blockers.append("not authenticated")
    blockers.extend(identity_blockers)
    if not runtime_running:
        blockers.append("runtime intentionally stopped")
    if not not_safety_blocked:
        blockers.append("runtime safety blocked")
    if not observed_state.reconciled:
        blockers.append("reconciliation not clean")
    if not compatibility_state.mode_compatible:
        blockers.extend(
            compatibility_state.blocking_reasons
            or ("hedging/netting compatibility gate failed",)
        )

    can_submit_new = can_manage_owned and not blockers

    return ExecutionAuthorityDecision(
        can_observe=can_observe,
        can_manage_owned_existing_risk=can_manage_owned,
        can_submit_new_risk=can_submit_new,
        can_close_owned_risk=can_manage_owned,
        can_modify_foreign_risk=False,
        reasons=tuple(blockers),
        decision_timestamp=utcnow_iso(),
        profile_hash=config_hash(profile),
    )
