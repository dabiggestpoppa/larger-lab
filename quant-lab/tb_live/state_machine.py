"""
TB-R3 — Explicit Basket State Machine
======================================

The durable truth layer of the TB forward engine needs an EXPLICIT, frozen
basket lifecycle — never informal booleans. Every persisted event carries a
(prior_state, new_state) pair and every transition must be valid from a known
prior state. An invalid transition FAILS CLOSED.

States are the frozen R3 set:

    NO_BASKET, SIGNAL_DETECTED, INTENT_CREATED, ENTRY_SUBMITTING,
    PARTIALLY_FILLED, OPEN_VERIFIED, CLOSE_REQUESTED, CLOSE_SUBMITTING,
    PARTIALLY_CLOSED, CLOSED_VERIFIED, BROKEN_HEDGE, FLATTENING,
    FLAT_VERIFIED, RECONCILIATION_REQUIRED, BLOCKED_UNKNOWN_STATE

These are the PERSISTENCE / RECONCILIATION lifecycle states. They are distinct
from (and coexist with) the ADOPTED atomic-execution layer's internal
BasketState (PENDING/PRECHECK/SENDING/VERIFYING/OPEN/...) — the execution
layer expresses broker-order mechanics; this machine expresses durable basket
truth across restarts.

SCIENTIFIC INVARIANT: this module contains NO basis/z/entry/exit/weight math
and no broker-call code. It only defines the lifecycle graph.

Mechanical change only (R3 mandate): no alpha, no thresholds, no session or
cost semantics are touched.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, FrozenSet, Tuple


class BasketLifecycleState(str, Enum):
    """Frozen R3 durable basket states."""

    NO_BASKET = "NO_BASKET"
    SIGNAL_DETECTED = "SIGNAL_DETECTED"
    INTENT_CREATED = "INTENT_CREATED"
    ENTRY_SUBMITTING = "ENTRY_SUBMITTING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    OPEN_VERIFIED = "OPEN_VERIFIED"
    CLOSE_REQUESTED = "CLOSE_REQUESTED"
    CLOSE_SUBMITTING = "CLOSE_SUBMITTING"
    PARTIALLY_CLOSED = "PARTIALLY_CLOSED"
    CLOSED_VERIFIED = "CLOSED_VERIFIED"
    BROKEN_HEDGE = "BROKEN_HEDGE"
    FLATTENING = "FLATTENING"
    FLAT_VERIFIED = "FLAT_VERIFIED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    BLOCKED_UNKNOWN_STATE = "BLOCKED_UNKNOWN_STATE"


# ─── VALID TRANSITIONS ────────────────────────────────────────────────────
# Frozen transition graph. EVERY edge here was chosen to be safe under the
# fail-closed mandate: an unknown/ambiguous situation routes to
# RECONCILIATION_REQUIRED or BLOCKED_UNKNOWN_STATE, never to a silent action.

TRANSITIONS: Dict[Tuple[BasketLifecycleState, BasketLifecycleState], str] = {
    # --- entry lifecycle ---
    (BasketLifecycleState.NO_BASKET, BasketLifecycleState.SIGNAL_DETECTED):
        "strategy entry signal observed on a closed M5 bar",
    (BasketLifecycleState.SIGNAL_DETECTED, BasketLifecycleState.NO_BASKET):
        "signal rejected (session/quality/neutrality gate)",
    (BasketLifecycleState.SIGNAL_DETECTED, BasketLifecycleState.INTENT_CREATED):
        "basket intent durably persisted (write-ahead before any order)",
    (BasketLifecycleState.INTENT_CREATED, BasketLifecycleState.ENTRY_SUBMITTING):
        "entry attempt started (first broker order sent)",
    (BasketLifecycleState.INTENT_CREATED, BasketLifecycleState.FLAT_VERIFIED):
        "entry never submitted (aborted before any order)",
    (BasketLifecycleState.ENTRY_SUBMITTING, BasketLifecycleState.ENTRY_SUBMITTING):
        "bounded retry / duplicate-response idempotent no-op",
    (BasketLifecycleState.ENTRY_SUBMITTING, BasketLifecycleState.OPEN_VERIFIED):
        "all three legs filled + broker-verified",
    (BasketLifecycleState.ENTRY_SUBMITTING, BasketLifecycleState.PARTIALLY_FILLED):
        "1-2 of 3 legs filled",
    (BasketLifecycleState.ENTRY_SUBMITTING, BasketLifecycleState.FLAT_VERIFIED):
        "zero fills, aborted flat",

    # --- broken hedge / flatten ---
    (BasketLifecycleState.PARTIALLY_FILLED, BasketLifecycleState.BROKEN_HEDGE):
        "partial triangle detected",
    (BasketLifecycleState.BROKEN_HEDGE, BasketLifecycleState.FLATTENING):
        "flatten started for filled legs",
    (BasketLifecycleState.FLATTENING, BasketLifecycleState.FLAT_VERIFIED):
        "all filled legs confirmed flat",
    (BasketLifecycleState.FLATTENING, BasketLifecycleState.BLOCKED_UNKNOWN_STATE):
        "flatten unresolved",

    # --- open / close ---
    (BasketLifecycleState.OPEN_VERIFIED, BasketLifecycleState.CLOSE_REQUESTED):
        "canonical exit signal observed",
    (BasketLifecycleState.CLOSE_REQUESTED, BasketLifecycleState.CLOSE_SUBMITTING):
        "close attempt started",
    (BasketLifecycleState.CLOSE_SUBMITTING, BasketLifecycleState.CLOSED_VERIFIED):
        "all three legs confirmed flat",
    (BasketLifecycleState.CLOSE_SUBMITTING, BasketLifecycleState.PARTIALLY_CLOSED):
        "1-2 of 3 legs closed",
    (BasketLifecycleState.PARTIALLY_CLOSED, BasketLifecycleState.CLOSE_SUBMITTING):
        "bounded close retry",
    (BasketLifecycleState.CLOSED_VERIFIED, BasketLifecycleState.NO_BASKET):
        "basket lifecycle complete (re-entry allowed)",

    # --- reconciliation / recovery ---
    (BasketLifecycleState.RECONCILIATION_REQUIRED, BasketLifecycleState.OPEN_VERIFIED):
        "reconciled: all expected legs present at broker",
    (BasketLifecycleState.RECONCILIATION_REQUIRED, BasketLifecycleState.FLAT_VERIFIED):
        "reconciled: broker confirmed flat",
    (BasketLifecycleState.RECONCILIATION_REQUIRED, BasketLifecycleState.BROKEN_HEDGE):
        "reconciled: partial triangle confirmed",
    (BasketLifecycleState.OPEN_VERIFIED, BasketLifecycleState.RECONCILIATION_REQUIRED):
        "broker/local divergence (manual intervention or unknown change)",
    (BasketLifecycleState.CLOSE_SUBMITTING, BasketLifecycleState.RECONCILIATION_REQUIRED):
        "close cannot complete; reconcile before any action",

    # --- fail-closed escape hatch ---
    (BasketLifecycleState.RECONCILIATION_REQUIRED, BasketLifecycleState.BLOCKED_UNKNOWN_STATE):
        "reconciliation cannot determine truth",
}

# Terminal (absorbing) states: nothing may proceed from them except explicit
# human/unblock handling which is out of scope for automation.
TERMINAL_STATES: FrozenSet[BasketLifecycleState] = frozenset({
    BasketLifecycleState.BLOCKED_UNKNOWN_STATE,
})

ALL_STATES: FrozenSet[BasketLifecycleState] = frozenset(BasketLifecycleState)


def is_valid_transition(prior: BasketLifecycleState,
                        new: BasketLifecycleState) -> bool:
    """Return True when the (prior, new) pair is an allowed transition."""
    return (prior, new) in TRANSITIONS


def validate_transition(prior: BasketLifecycleState,
                        new: BasketLifecycleState) -> None:
    """Validate a transition, raising ValueError on any invalid pair.

    This is the fail-closed gate: persistence refuses to record an event
    whose state transition is not in the frozen graph.
    """
    if prior == new and (prior, new) not in TRANSITIONS:
        raise ValueError(
            f"INVALID STATE TRANSITION {prior.value} -> {new.value}: "
            f"not in frozen graph"
        )
    if not is_valid_transition(prior, new):
        raise ValueError(
            f"INVALID STATE TRANSITION {prior.value} -> {new.value}: "
            f"not in frozen graph"
        )


def reason_for(prior: BasketLifecycleState, new: BasketLifecycleState) -> str:
    """Return the frozen reason string for a transition (or '' if invalid)."""
    return TRANSITIONS.get((prior, new), "")
