"""QL-EXEC-R3 — crash/restart + exit tests (50-59).

Crash windows are injected via ``CrashPoint``; restart constructs a NEW runtime
object over the SAME store + SAME SimBrokerSession (its in-memory truth is the
persistent broker fixture). After a simulated crash we release the old
runtime's singleton lock to emulate dead-process lock reclaim.
"""
from __future__ import annotations

import pytest

from execution_runtime.brokers.sim_broker import SimBrokerSession
from execution_runtime.enums import BrokerErrorCategory
from execution_runtime.runtime import CrashPoint, SimulatedCrash
from execution_runtime.runtime.adapters import (
    ScriptedStrategyAdapter,
    entry_event,
    exit_event,
)
from execution_runtime.runtime.intent import IntentState, PositionState
from execution_runtime.runtime.state import RuntimeState
from execution_runtime.types import CloseResult

from r3_harness import make_account, make_profile, make_runtime, make_store


def _build(tmp_path, *, events, crash_point=CrashPoint.NONE, broker=None, fail_mode="FULL_FILL"):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = broker or SimBrokerSession()
    broker.set_fail_mode(fail_mode)
    rt, broker = make_runtime(
        profile, account, store, broker=broker, events=events, crash_point=crash_point
    )
    return profile, account, store, broker, rt


def _run_entry(tmp_path, *, crash_point=CrashPoint.NONE, fail_mode="FULL_FILL"):
    profile, account, store, broker, rt = _build(
        tmp_path, events=(entry_event("ev-1"),), crash_point=crash_point, fail_mode=fail_mode
    )
    rt.start()
    try:
        rt.step()
    except SimulatedCrash:
        pass
    return profile, account, store, broker, rt


# ── CRASH / RESTART (50-54) ──────────────────────────────────────────────


def test_50_crash_after_intent_before_submit_safe_retry(tmp_path):
    profile, account, store, broker, rt = _run_entry(
        tmp_path, crash_point=CrashPoint.AFTER_INTENT_COMMIT
    )
    assert broker.position_count() == 0  # crashed before submit
    intents = store.intents()
    assert len(intents) == 1 and intents[0].state == IntentState.INTENT_CREATED.value

    rt._release_singleton()
    rt2, _ = make_runtime(profile, account, store, broker=broker, events=(entry_event("ev-1"),))
    assert rt2.start() is RuntimeState.RUNNING
    rt2.step()
    # Safe retry: exactly one position now exists, intent filled.
    assert broker.position_count() == 1
    assert store.intents()[0].state == IntentState.INTENT_FILLED.value


def test_51_crash_after_broker_submit_no_duplicate(tmp_path):
    profile, account, store, broker, rt = _run_entry(
        tmp_path, crash_point=CrashPoint.AFTER_BROKER_SUBMIT
    )
    assert broker.position_count() == 1  # broker accepted before crash
    assert broker.order_count() == 1
    assert store.intents()[0].state == IntentState.INTENT_CREATED.value  # result not recorded

    rt._release_singleton()
    rt2, _ = make_runtime(profile, account, store, broker=broker, events=(entry_event("ev-1"),))
    assert rt2.start() is RuntimeState.RUNNING
    rt2.step()
    # Reconstructed WITHOUT resubmit: still exactly one order + one position.
    assert broker.order_count() == 1
    assert broker.position_count() == 1
    assert store.intents()[0].state == IntentState.INTENT_FILLED.value


def test_52_restart_with_open_verified_reconstructs(tmp_path):
    profile, account, store, broker, rt = _run_entry(tmp_path)
    assert store.owned_positions()[0].state == PositionState.FILLED.value
    rt._release_singleton()
    rt2, _ = make_runtime(profile, account, store, broker=broker, events=(entry_event("ev-1"),))
    assert rt2.start() is RuntimeState.RUNNING
    rt2.step()
    assert store.owned_positions()[0].state == PositionState.FILLED.value
    assert broker.position_count() == 1


def test_53_restart_with_closed_verifies_flat(tmp_path):
    profile, account, store, broker, rt = _run_entry(tmp_path)
    # Add an exit event and process it (close).
    rt._strategy = ScriptedStrategyAdapter(events=(entry_event("ev-1"), exit_event("ev-2")))
    rt.step()
    assert store.owned_positions()[0].state == PositionState.CLOSED.value
    assert broker.position_count() == 0

    rt._release_singleton()
    rt2, _ = make_runtime(profile, account, store, broker=broker)
    assert rt2.start() is RuntimeState.RUNNING
    t = rt2.step()
    assert t.reconciliation_clean
    assert broker.position_count() == 0


def test_54_restart_with_unresolved_intent_blocks(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    store.upsert_owned_position(
        "logical-1",
        runtime_id="rt-1",
        account_id="acct-1",
        strategy_id="scripted-strategy",
        intent_id="intent-1",
        event_id="ev-1",
        symbol="EURUSD",
        side="BUY",
        requested_quantity=0.1,
        filled_quantity=0.1,
        state=PositionState.FILLED.value,
        broker_position_id="missing",
        broker_order_id="order-1",
        ownership_tag="TAG-1",
        fill_price=1.1,
    )
    rt, _ = make_runtime(profile, account, store)
    # Broker flat but local open -> AMBIGUOUS -> BLOCKED until reconciled.
    assert rt.start() is RuntimeState.BLOCKED


# ── EXIT (55-59) ─────────────────────────────────────────────────────────


def test_55_exit_creates_durable_close_intent(tmp_path):
    profile, account, store, broker, rt = _run_entry(tmp_path)
    rt._strategy = ScriptedStrategyAdapter(events=(entry_event("ev-1"), exit_event("ev-2")))
    rt.step()
    assert store.owned_positions()[0].state == PositionState.CLOSED.value
    rows = store._conn.execute(
        "SELECT COUNT(*) AS n FROM runtime_events WHERE event_type='EXIT_REQUESTED'"
    ).fetchone()
    assert int(rows["n"]) >= 1


def test_56_close_success_closed_verified(tmp_path):
    profile, account, store, broker, rt = _run_entry(tmp_path)
    rt._strategy = ScriptedStrategyAdapter(events=(entry_event("ev-1"), exit_event("ev-2")))
    rt.step()
    assert broker.position_count() == 0
    assert store.owned_positions()[0].state == PositionState.CLOSED.value
    rows = store._conn.execute(
        "SELECT COUNT(*) AS n FROM runtime_events WHERE event_type='POSITION_CLOSED_VERIFIED'"
    ).fetchone()
    assert int(rows["n"]) >= 1


def test_57_close_reject_recorded(tmp_path):
    class _RejectCloseBroker(SimBrokerSession):
        def close_position(self, position_id, reason=""):
            return CloseResult(
                ok=False, reason="close rejected",
                error_category=BrokerErrorCategory.ORDER_REJECTED,
            )

    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = _RejectCloseBroker()
    rt, broker = make_runtime(profile, account, store, broker=broker, events=(entry_event("ev-1"),))
    rt.start()
    rt.step()
    rt._strategy = ScriptedStrategyAdapter(events=(entry_event("ev-1"), exit_event("ev-2")))
    rt.step()
    rows = store._conn.execute(
        "SELECT COUNT(*) AS n FROM runtime_events WHERE event_type='CLOSE_REJECTED'"
    ).fetchone()
    assert int(rows["n"]) >= 1


def test_58_crash_during_close_recovered(tmp_path):
    profile, account, store, broker, rt = _run_entry(tmp_path)
    rt._strategy = ScriptedStrategyAdapter(events=(entry_event("ev-1"), exit_event("ev-2")))
    rt._crash_point = CrashPoint.AFTER_CLOSE_SUBMIT
    with pytest.raises(SimulatedCrash):
        rt.step()
    # Broker close already happened (position gone); local is CLOSE_PENDING.
    assert broker.position_count() == 0
    assert store.owned_positions()[0].state == PositionState.CLOSE_PENDING.value

    rt._release_singleton()
    rt2, _ = make_runtime(profile, account, store, broker=broker)
    assert rt2.start() is RuntimeState.RUNNING
    rt2.step()
    assert store.owned_positions()[0].state == PositionState.CLOSED.value


def test_59_foreign_position_unaffected(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession()
    broker.seed_foreign_position("foreign-1", symbol="GBPUSD", ownership_tag="FOREIGN", magic=999999)
    rt, broker = make_runtime(
        profile, account, store, broker=broker, events=(entry_event("ev-1"), exit_event("ev-2"))
    )
    rt.start()
    rt.step()
    rt.step()
    # Foreign position never closed/removed.
    assert broker.broker_position("foreign-1") is not None
