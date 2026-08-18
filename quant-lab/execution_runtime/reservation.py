"""QL-EXEC-R1 — heat reservation contract (data types + state validation only).

No SQLite transaction engine here; R6 implements operational shared
reservation. This module freezes identity + lifecycle semantics.
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import ReservationState
from .exceptions import InvalidStateTransition
from .types import stable_hash


@dataclass(frozen=True)
class ReservationRecord:
    """One durable heat reservation."""

    reservation_id: str
    portfolio_group_id: str
    account_id: str
    strategy_id: str
    event_id: str
    deployment_generation: str
    state: ReservationState = ReservationState.PROPOSED
    requested_f: float | None = None
    admitted_f: float | None = None
    created_ts: str = ""
    released_ts: str = ""


def reservation_id_for(
    portfolio_group_id: str,
    account_id: str,
    strategy_id: str,
    event_id: str,
    deployment_generation: str,
) -> str:
    """Deterministic reservation key (replay of the same event -> same id).

    Includes deployment_generation so a replayed event across generations can
    never collide.
    """
    return stable_hash(
        "RSV1",
        portfolio_group_id,
        account_id,
        strategy_id,
        event_id,
        deployment_generation,
        n=32,
    )


# Frozen transition graph. Fail-closed: an unknown transition is invalid.
VALID_TRANSITIONS: dict[ReservationState, frozenset[ReservationState]] = {
    ReservationState.PROPOSED: frozenset(
        {ReservationState.ADMITTED_RESERVED, ReservationState.REJECTED}
    ),
    ReservationState.ADMITTED_RESERVED: frozenset(
        {ReservationState.ORDER_SUBMITTED, ReservationState.RELEASED_ABORTED}
    ),
    ReservationState.ORDER_SUBMITTED: frozenset(
        {ReservationState.FILLED_ACTIVE, ReservationState.RELEASED_ABORTED}
    ),
    ReservationState.FILLED_ACTIVE: frozenset(
        {ReservationState.EXIT_PENDING, ReservationState.RESERVATION_UNRESOLVED}
    ),
    ReservationState.EXIT_PENDING: frozenset(
        {ReservationState.CLOSED_RELEASED, ReservationState.RESERVATION_UNRESOLVED}
    ),
    ReservationState.RESERVATION_UNRESOLVED: frozenset(
        {ReservationState.CLOSED_RELEASED, ReservationState.RELEASED_ABORTED}
    ),
    ReservationState.CLOSED_RELEASED: frozenset(),
    ReservationState.REJECTED: frozenset(),
    ReservationState.RELEASED_ABORTED: frozenset(),
}


def validate_reservation_transition(
    old: ReservationState, new: ReservationState
) -> bool:
    """Return True when (old -> new) is in the frozen graph; else raise."""
    allowed = VALID_TRANSITIONS.get(old)
    if allowed is None or new not in allowed:
        raise InvalidStateTransition(
            f"INVALID RESERVATION TRANSITION {old.value} -> {new.value}"
        )
    return True
