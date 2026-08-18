"""QL-EXEC-R4 — restart reconstruction, crash windows, and idempotency.

The generic multi-leg path must survive the dangerous windows without duplicate
exposure: intent written before submit, submit before local acknowledgement,
crash mid-basket, close-in-progress. On restart a fresh orchestrator over the
same broker + durable store reconstructs truth and NEVER resubmits blindly.
"""
from __future__ import annotations

import pytest

from execution_runtime.tb.harness import (
    GenericTBHarness,
    make_control_fixture,
    make_snapshot,
    BASKET_NOTIONAL_USD,
)
from execution_runtime.tb.basket import SimulatedBasketCrash


@pytest.fixture
def fix():
    return make_control_fixture()


def _open_generic(tmp_path, broker=None, crash_point=None):
    h = GenericTBHarness(
        basket_notional_usd=BASKET_NOTIONAL_USD,
        db_path=str(tmp_path / "rt.sqlite"),
        broker=broker,
        crash_point=crash_point,
    )
    return h


def _step_signal(h):
    fix = make_control_fixture()
    h.warm(fix.bars[: fix.signal_index])
    h.step(make_snapshot(fix.bars[fix.signal_index]))
    return fix


def test_restart_flat(tmp_path):
    h1 = _open_generic(tmp_path)
    h1.recover()
    assert h1.snapshot()["basket_state"] in ("ABORTED_FLAT",)
    assert h1.snapshot()["owned_positions"] == []
    assert h1.snapshot()["order_send_count"] == 0


def test_restart_open_no_duplicate(tmp_path):
    h1 = _open_generic(tmp_path)
    _step_signal(h1)
    assert h1.snapshot()["basket_state"] == "OPEN"
    assert len(h1.snapshot()["owned_positions"]) == 3

    # restart: same broker (in-memory truth) + same durable store
    h2 = _open_generic(tmp_path, broker=h1.broker)
    h2.recover()
    assert h2.snapshot()["basket_state"] == "OPEN"
    assert len(h2.snapshot()["owned_positions"]) == 3
    assert h2.snapshot()["order_send_count"] == 0  # no resubmission
    # broker still holds exactly the original 3 positions (no duplicate)
    assert h1.broker.position_count() == 3


def test_restart_after_crash_after_leg1(tmp_path):
    """Crash after leg1 fill -> recover must flatten the partial, not duplicate."""
    broker = None
    h1 = _open_generic(tmp_path, crash_point="AFTER_LEG1_SEND")
    with pytest.raises(SimulatedBasketCrash):
        _step_signal(h1)
    # broker has leg1 only; ledger has 3 intents (leg1 submitted)
    assert h1.broker.position_count() == 1

    h2 = _open_generic(tmp_path, broker=h1.broker)
    h2.recover()
    assert h2.snapshot()["owned_positions"] == []  # partial flattened
    assert h2.snapshot()["basket_state"] in ("ABORTED_FLAT", "BROKEN_HEDGE")


def test_restart_after_crash_before_verify(tmp_path):
    """Crash after all sends before fill verify -> recover adopts OPEN (no dup)."""
    h1 = _open_generic(tmp_path, crash_point="AFTER_ALL_SENDS_BEFORE_VERIFY")
    with pytest.raises(SimulatedBasketCrash):
        _step_signal(h1)
    # broker has all 3 positions; local verify never ran
    assert h1.broker.position_count() == 3

    h2 = _open_generic(tmp_path, broker=h1.broker)
    h2.recover()
    assert h2.snapshot()["basket_state"] == "OPEN"
    assert len(h2.snapshot()["owned_positions"]) == 3
    assert h2.snapshot()["order_send_count"] == 0
    assert h1.broker.position_count() == 3


def test_restart_after_crash_after_plan_commit(tmp_path):
    """Crash after write-ahead before any send -> no broker exposure, no dup."""
    h1 = _open_generic(tmp_path, crash_point="AFTER_PLAN_COMMIT")
    with pytest.raises(SimulatedBasketCrash):
        _step_signal(h1)
    assert h1.broker.position_count() == 0

    h2 = _open_generic(tmp_path, broker=h1.broker)
    h2.recover()
    assert h2.snapshot()["owned_positions"] == []
    assert h2.snapshot()["order_send_count"] == 0


def test_restart_after_close(tmp_path):
    h1 = _open_generic(tmp_path)
    fix = _step_signal(h1)
    h1.step(make_snapshot(fix.bars[fix.exit_index]))
    assert h1.snapshot()["basket_state"] == "CLOSED"
    assert h1.broker.position_count() == 0

    h2 = _open_generic(tmp_path, broker=h1.broker)
    h2.recover()
    assert h2.snapshot()["owned_positions"] == []
    assert h2.snapshot()["order_send_count"] == 0


def test_duplicate_event_no_duplicate_exposure(tmp_path):
    """Replaying the same basket event must not create a second exposure."""
    from execution_runtime.tb.basket import (
        LegPlan,
        MultiLegExecutionPlan,
        leg_intent_id,
    )
    h1 = _open_generic(tmp_path)
    _step_signal(h1)
    assert h1.broker.position_count() == 3
    assert len(h1.store.intents()) == 3
    plan_ids = h1.store.distinct_plan_ids()
    assert len(plan_ids) == 1

    # deterministic leg intent id is a pure function of immutable inputs
    assert leg_intent_id("P", "L1", "GBPAUD.PRO", "SELL", 0.07) == leg_intent_id(
        "P", "L1", "GBPAUD.PRO", "SELL", 0.07
    )

    # Replay the SAME plan (same id + same legs) -> idempotent no-op.
    positions = sorted(h1.broker.positions(), key=lambda p: p.symbol)
    legs = tuple(
        LegPlan(
            leg_id=f"L{i}", instrument=p.symbol.split(".")[0],
            broker_symbol=p.symbol,
            side="BUY" if p.side == "LONG" else "SELL",
            quantity=p.volume,
        )
        for i, p in enumerate(positions, start=1)
    )
    plan = MultiLegExecutionPlan(
        plan_id=plan_ids[0], strategy_id="TB-FROZEN-CONTROL",
        runtime_id="tb-runtime", account_id="tb-master",
        deployment_generation="gen-1", legs=legs,
    )
    res = h1.orchestrator.open_plan(plan)
    assert "DUPLICATE_PLAN_NOOP" in res.trace
    assert res.order_send_count == 0
    assert h1.broker.position_count() == 3  # no duplicate exposure
