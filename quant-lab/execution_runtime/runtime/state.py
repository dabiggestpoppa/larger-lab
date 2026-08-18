"""QL-EXEC-R3 — generic runtime state machine.

A single, frozen, explicit state set for the GenericRuntime lifecycle.
Transitions are validated against a frozen graph; an invalid transition
raises ``InvalidStateTransition`` (fail closed). ``BLOCKED`` is NOT ``FAILED``:
BLOCKED means the runtime is alive but new-risk authority is denied for an
explicit condition; FAILED means the runtime itself cannot operate coherently.

No strategy science, no broker imports, no capital routing math.
"""
from __future__ import annotations

from enum import Enum

from ..exceptions import InvalidStateTransition


class RuntimeState(str, Enum):
    """Frozen R3 runtime lifecycle states."""

    CREATED = "CREATED"
    STARTING = "STARTING"
    CONNECTING = "CONNECTING"
    WAITING_FOR_BROKER = "WAITING_FOR_BROKER"
    IDENTITY_CHECK = "IDENTITY_CHECK"
    RECONCILING = "RECONCILING"
    WARMING = "WARMING"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


# Frozen transition graph. Every edge was chosen fail-closed: ambiguous
# situations route to BLOCKED / WAITING_FOR_BROKER / FAILED, never a silent
# action. FAILED and STOPPED are terminal (nothing proceeds from them except
# explicit operator/human handling, out of scope for R3 automation).
VALID_TRANSITIONS: dict[tuple[RuntimeState, RuntimeState], str] = {
    (RuntimeState.CREATED, RuntimeState.STARTING): "begin startup",
    (RuntimeState.STARTING, RuntimeState.CONNECTING): "connect broker",
    (RuntimeState.STARTING, RuntimeState.BLOCKED): "config/generation drift or store gate",
    (RuntimeState.STARTING, RuntimeState.STOPPED): "desired state is STOPPED_BY_USER",
    (RuntimeState.STARTING, RuntimeState.FAILED): "store/profile validation failed",
    (RuntimeState.CONNECTING, RuntimeState.WAITING_FOR_BROKER): "broker unavailable",
    (RuntimeState.CONNECTING, RuntimeState.IDENTITY_CHECK): "broker connected",
    (RuntimeState.CONNECTING, RuntimeState.FAILED): "unrecoverable connect failure",
    (RuntimeState.WAITING_FOR_BROKER, RuntimeState.CONNECTING): "broker retry",
    (RuntimeState.WAITING_FOR_BROKER, RuntimeState.STOPPING): "operator stop",
    (RuntimeState.WAITING_FOR_BROKER, RuntimeState.FAILED): "unrecoverable broker failure",
    (RuntimeState.IDENTITY_CHECK, RuntimeState.BLOCKED): "identity mismatch blocks",
    (RuntimeState.IDENTITY_CHECK, RuntimeState.RECONCILING): "identity verified",
    (RuntimeState.IDENTITY_CHECK, RuntimeState.FAILED): "identity evaluation failed",
    (RuntimeState.RECONCILING, RuntimeState.BLOCKED): "reconciliation ambiguous",
    (RuntimeState.RECONCILING, RuntimeState.WARMING): "reconciled (startup)",
    (RuntimeState.RECONCILING, RuntimeState.RUNNING): "reconciled clean (steady state)",
    (RuntimeState.RECONCILING, RuntimeState.FAILED): "reconciliation errored",
    (RuntimeState.RUNNING, RuntimeState.RECONCILING): "periodic reconcile pass",
    (RuntimeState.BLOCKED, RuntimeState.RECONCILING): "re-evaluate blocker via reconcile",
    (RuntimeState.WARMING, RuntimeState.BLOCKED): "strategy warm/restore failed",
    (RuntimeState.WARMING, RuntimeState.RUNNING): "warm complete",
    (RuntimeState.WARMING, RuntimeState.FAILED): "warm failed unrecoverably",
    (RuntimeState.RUNNING, RuntimeState.BLOCKED): "new-risk gate denied",
    (RuntimeState.RUNNING, RuntimeState.WAITING_FOR_BROKER): "broker unavailable",
    (RuntimeState.RUNNING, RuntimeState.STOPPING): "operator stop",
    (RuntimeState.RUNNING, RuntimeState.FAILED): "unrecoverable runtime error",
    (RuntimeState.BLOCKED, RuntimeState.RUNNING): "blocker cleared / recovered",
    (RuntimeState.BLOCKED, RuntimeState.WAITING_FOR_BROKER): "broker unavailable",
    (RuntimeState.BLOCKED, RuntimeState.STOPPING): "operator stop",
    (RuntimeState.BLOCKED, RuntimeState.FAILED): "unrecoverable runtime error",
    (RuntimeState.STOPPING, RuntimeState.STOPPED): "clean stop",
    (RuntimeState.STOPPING, RuntimeState.FAILED): "stop errored",
}

TERMINAL_STATES = frozenset({RuntimeState.STOPPED, RuntimeState.FAILED})


def is_valid_transition(prior: RuntimeState, new: RuntimeState) -> bool:
    return (prior, new) in VALID_TRANSITIONS


def reason_for(prior: RuntimeState, new: RuntimeState) -> str:
    return VALID_TRANSITIONS.get((prior, new), "")


def validate_transition(prior: RuntimeState, new: RuntimeState) -> bool:
    """Validate a transition; raise ``InvalidStateTransition`` on any invalid pair."""
    if not is_valid_transition(prior, new):
        raise InvalidStateTransition(
            f"INVALID RUNTIME TRANSITION {prior.value} -> {new.value}"
        )
    return True
