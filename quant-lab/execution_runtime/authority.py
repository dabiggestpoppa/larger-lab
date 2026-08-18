"""QL-EXEC-R1.1 — derived execution authority (pure, fail-closed, DEFAULT DENY).

A config profile can never declare itself READY. Effective authority is
derived from static profile + observed truth + runtime state + compatibility.

R1.1 repair: authentication is separated from secret possession. The proven
TB MT5 pattern attaches to an EXTERNAL_SESSION (an already-logged-in terminal)
and therefore does NOT require the Python runtime to hold credentials. Secret
requirement now depends on AUTHENTICATION MODE, never on transport type alone.
"""  # noqa: E501
from __future__ import annotations

from dataclasses import dataclass, field

from .account import AccountObservedState, AccountProfile
from .compatibility import CompatibilityState
from .enums import AccountRole, AuthenticationMode, DesiredState
from .hashing import config_hash
from .profiles import RuntimeState
from .types import utcnow_iso


def requires_identity_verification(profile: AccountProfile) -> bool:
    """Broker identity must be matched for any externally authenticated mode.

    SIM/REPLAY (NONE) have no external broker identity to verify.
    """
    return profile.authentication_mode in (
        AuthenticationMode.EXTERNAL_SESSION,
        AuthenticationMode.RUNTIME_CREDENTIALS,
    )


def requires_secret(profile: AccountProfile) -> bool:
    """Secret possession is required ONLY for runtime-credential auth.

    This is the R1.1 repair: requires_secret(profile), not
    requires_secret(transport).
    """
    return profile.authentication_mode is AuthenticationMode.RUNTIME_CREDENTIALS


def authentication_satisfied(
    profile: AccountProfile, observed: AccountObservedState
) -> tuple[bool, list[str]]:
    """Centralized authentication satisfaction. Feeds authority derivation.

    NONE                -> no external auth; local transport/session state is
                           the only session requirement (checked as the
                           transport gate in derive_execution_authority).
    EXTERNAL_SESSION    -> observed authenticated session must be true.
    RUNTIME_CREDENTIALS -> required SecretReference present AND observed
                           authentication successful.
    """
    mode = profile.authentication_mode
    blockers: list[str] = []

    if mode is AuthenticationMode.NONE:
        # No external authentication requirement; nothing further to check.
        pass
    elif mode is AuthenticationMode.EXTERNAL_SESSION:
        if not observed.authenticated:
            blockers.append("external session not authenticated")
    elif mode is AuthenticationMode.RUNTIME_CREDENTIALS:
        if profile.secret_reference is None or not profile.secret_reference.is_present():
            blockers.append("missing secret reference for runtime credentials")
        if not observed.authenticated:
            blockers.append("not authenticated")
    else:  # defensive: never admit an unrecognized mode
        blockers.append(f"unknown authentication mode: {mode}")

    return (not blockers), blockers


def identity_gate(profile: AccountProfile, observed: AccountObservedState) -> tuple[bool, list[str]]:
    """Explicit identity comparison. Never infer identity from connection.

    Returns (matched, blockers). Empty blockers == matched.

    CONNECTED is not enough; AUTHENTICATED is not enough; identity must match
    for EXTERNAL_SESSION and RUNTIME_CREDENTIALS modes.
    """
    blockers: list[str] = []
    needs_identity = requires_identity_verification(profile)

    # Broker company (required field; compared case-insensitively).
    if observed.observed_broker_company:
        if profile.broker_company.casefold() != observed.observed_broker_company.casefold():
            blockers.append("identity mismatch: broker company")
    elif needs_identity:
        blockers.append("identity not verifiable: broker company missing")

    # Server.
    if profile.expected_server:
        if observed.observed_server and observed.observed_server != profile.expected_server:
            blockers.append("identity mismatch: server")
        elif not observed.observed_server:
            blockers.append("identity not verifiable: server missing")
    elif needs_identity:
        blockers.append("missing identity expectation: server")

    # Environment.
    if observed.observed_environment is None:
        if needs_identity:
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
    """Pure fail-closed derivation of effective execution authority.

    Policy (frozen in R1.1): closing/managing already-owned risk does NOT
    require operator new-risk permission, but DOES require transport
    connectivity, satisfied authentication, matched identity, a RUNNING
    unblocked runtime. Identity must stay strong enough to prevent acting on
    the wrong account. Foreign risk is never manageable.
    """

    identity_ok, identity_blockers = identity_gate(profile, observed_state)
    auth_ok, auth_blockers = authentication_satisfied(profile, observed_state)

    can_observe = observed_state.transport_connected

    runtime_running = runtime_state.desired_state is DesiredState.RUNNING
    not_safety_blocked = not runtime_state.safety_blocked

    # Managing/closing owned existing risk requires connection, satisfied
    # authentication, matched identity, and an alive, unblocked runtime.
    can_manage_owned = (
        observed_state.transport_connected
        and auth_ok
        and identity_ok
        and runtime_running
        and not_safety_blocked
    )

    # New risk requires everything above plus operator intent, direct-execution
    # role, reconciliation, and compatibility. Auth blockers (including the
    # RUNTIME_CREDENTIALS secret requirement) flow in here.
    blockers: list[str] = []

    if not profile.operator_execution_requested:
        blockers.append("operator execution not requested")
    if profile.account_role not in _DIRECT_EXECUTION_ROLES:
        blockers.append(
            f"account role {profile.account_role.value} cannot submit direct orders"
        )
    blockers.extend(auth_blockers)
    if not observed_state.transport_connected:
        blockers.append("transport not connected")
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
