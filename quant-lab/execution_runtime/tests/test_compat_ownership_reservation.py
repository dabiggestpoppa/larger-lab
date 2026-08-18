"""R1 checks 34-49 (hedging/netting, ownership, reservation)."""
from __future__ import annotations

import pytest

from execution_runtime.compatibility import evaluate_compatibility
from execution_runtime.enums import (
    AccountRole,
    CompatibilityStatus,
    HedgingNetting,
    ReservationState,
)
from execution_runtime.exceptions import InvalidStateTransition
from execution_runtime.ownership import (
    LogicalOwnershipId,
    OwnershipNamespace,
    encode_broker_ownership,
    magic_for_namespace,
)
from execution_runtime.reservation import (
    reservation_id_for,
    validate_reservation_transition,
)


# ── HEDGING / NETTING ─────────────────────────────────────────────────────


def test_34_exclusive_hedging_allowed():
    c = evaluate_compatibility(AccountRole.EXCLUSIVE_STRATEGY_MASTER, HedgingNetting.HEDGING)
    assert c.mode_compatible is True
    assert c.status is CompatibilityStatus.SUPPORTED


def test_35_exclusive_netting_supported_only_when_unambiguous():
    c = evaluate_compatibility(AccountRole.EXCLUSIVE_STRATEGY_MASTER, HedgingNetting.NETTING, same_symbol_overlap=False)
    assert c.mode_compatible is True
    c2 = evaluate_compatibility(AccountRole.EXCLUSIVE_STRATEGY_MASTER, HedgingNetting.NETTING, same_symbol_overlap=True)
    assert c2.mode_compatible is False


def test_36_portfolio_hedging_supportable():
    c = evaluate_compatibility(AccountRole.PORTFOLIO_MASTER, HedgingNetting.HEDGING)
    assert c.mode_compatible is True
    assert c.status is CompatibilityStatus.SUPPORTABLE_WITH_WORK


def test_37_portfolio_netting_same_symbol_overlap_blocked():
    c = evaluate_compatibility(AccountRole.PORTFOLIO_MASTER, HedgingNetting.NETTING, same_symbol_overlap=True)
    assert c.mode_compatible is False
    assert c.status is CompatibilityStatus.BLOCKED_PENDING_VIRTUAL_LEDGER


def test_38_unknown_mode_fail_closed():
    c = evaluate_compatibility(AccountRole.PORTFOLIO_MASTER, HedgingNetting.UNKNOWN)
    assert c.mode_compatible is False
    assert c.status is CompatibilityStatus.FAIL_CLOSED


# ── OWNERSHIP ─────────────────────────────────────────────────────────────


def _logical(**overrides):
    d = dict(
        account_id="acct-1",
        runtime_id="rt-1",
        strategy_id="STRAT-A",
        deployment_generation="GEN-1",
        intent_id="evt-1",
    )
    d.update(overrides)
    return LogicalOwnershipId(**d)


def test_39_deterministic_logical_ownership():
    a = _logical().id()
    b = _logical().id()
    assert a == b


def test_40_different_account_different_id():
    assert _logical().id() != _logical(account_id="acct-2").id()


def test_41_different_runtime_different_id():
    assert _logical().id() != _logical(runtime_id="rt-2").id()


def test_42_different_generation_different_id():
    assert _logical().id() != _logical(deployment_generation="GEN-2").id()


def test_43_broker_compact_tag_deterministic():
    a = encode_broker_ownership(_logical())
    b = encode_broker_ownership(_logical())
    assert a == b
    assert a.magic > 0
    assert a.comment.startswith("QL1|")


def test_44_no_raw_secret_in_tag_or_hash_material():
    # ownership encoding takes no secret; the comment cannot contain one.
    tag = encode_broker_ownership(_logical())
    assert "SECRET" not in tag.comment.upper()
    assert "PASSWORD" not in tag.comment.upper()


# ── RESERVATION ───────────────────────────────────────────────────────────


def test_45_valid_state_transitions():
    assert validate_reservation_transition(
        ReservationState.PROPOSED, ReservationState.ADMITTED_RESERVED
    )
    assert validate_reservation_transition(
        ReservationState.ADMITTED_RESERVED, ReservationState.ORDER_SUBMITTED
    )
    assert validate_reservation_transition(
        ReservationState.FILLED_ACTIVE, ReservationState.EXIT_PENDING
    )
    assert validate_reservation_transition(
        ReservationState.EXIT_PENDING, ReservationState.CLOSED_RELEASED
    )


def test_46_invalid_transition_rejected():
    with pytest.raises(InvalidStateTransition):
        validate_reservation_transition(
            ReservationState.CLOSED_RELEASED, ReservationState.FILLED_ACTIVE
        )


def test_47_deterministic_reservation_id():
    a = reservation_id_for("pg-1", "acct-1", "STRAT-A", "evt-1", "GEN-1")
    b = reservation_id_for("pg-1", "acct-1", "STRAT-A", "evt-1", "GEN-1")
    assert a == b


def test_48_generation_changes_reservation_id():
    a = reservation_id_for("pg-1", "acct-1", "STRAT-A", "evt-1", "GEN-1")
    b = reservation_id_for("pg-1", "acct-1", "STRAT-A", "evt-1", "GEN-2")
    assert a != b


def test_49_duplicate_replay_idempotent_at_identity_level():
    a = reservation_id_for("pg-1", "acct-1", "STRAT-A", "evt-1", "GEN-1")
    b = reservation_id_for("pg-1", "acct-1", "STRAT-A", "evt-1", "GEN-1")
    assert a == b


def test_magic_scoped_by_binding_not_strategy_alone():
    ns1 = OwnershipNamespace("acct-1", "rt-1", "STRAT-A", "GEN-1")
    ns2 = OwnershipNamespace("acct-1", "rt-1", "STRAT-A", "GEN-2")
    assert magic_for_namespace(ns1) != magic_for_namespace(ns2)
