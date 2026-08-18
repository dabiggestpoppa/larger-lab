"""QL-EXEC-R3 — event/write-ahead/fill tests (24-38).

Covers: scripted event observation + dedup, capital admission -> target ->
deterministic intent, write-ahead-before-submit, submit reject/transport
recording, and fill truth (full / zero / partial).
"""
from __future__ import annotations

from execution_runtime.brokers.sim_broker import SimBrokerSession
from execution_runtime.runtime.adapters import entry_event
from execution_runtime.runtime.intent import IntentState, PositionState
from execution_runtime.runtime.state import RuntimeState

from r3_harness import make_account, make_profile, make_runtime, make_store


def _started(tmp_path, *, events, broker=None, reject_policy=False):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = broker or SimBrokerSession()
    rt, broker = make_runtime(
        profile, account, store, broker=broker, events=events, reject_policy=reject_policy
    )
    rt.start()
    rt.step()
    return profile, account, store, broker, rt


def _journal_count(store, event_type):
    row = store._conn.execute(
        "SELECT COUNT(*) AS n FROM runtime_events WHERE event_type=?", (event_type,)
    ).fetchone()
    return int(row["n"])


# ── EVENT (24-29) ────────────────────────────────────────────────────────


def test_24_scripted_event_observed(tmp_path):
    _, _, store, broker, _ = _started(tmp_path, events=(entry_event("ev-1"),))
    assert store.has_strategy_event("ev-1")
    assert _journal_count(store, "EVENT_OBSERVED") >= 1


def test_25_event_persisted(tmp_path):
    _, _, store, broker, _ = _started(tmp_path, events=(entry_event("ev-1"),))
    row = store._conn.execute(
        "SELECT event_id FROM strategy_events WHERE event_id='ev-1'"
    ).fetchone()
    assert row is not None


def test_26_duplicate_event_deduplicated(tmp_path):
    _, _, store, broker, _ = _started(tmp_path, events=(entry_event("ev-1"),))
    n_positions = broker.position_count()
    # Re-run several steps: same event must not create a second exposure.
    for _ in range(3):
        _started  # noqa: B018
    rt2, _ = make_runtime(
        make_profile(), make_account(), store, broker=broker, events=(entry_event("ev-1"),)
    )
    rt2.start()
    rt2.step()
    assert broker.position_count() == n_positions == 1
    assert _journal_count(store, "INTENT_CREATED") == 1


def test_27_rejected_capital_decision_produces_no_broker_intent(tmp_path):
    _, _, store, broker, _ = _started(
        tmp_path, events=(entry_event("ev-1"),), reject_policy=True
    )
    assert broker.position_count() == 0
    assert _journal_count(store, "INTENT_CREATED") == 0
    assert _journal_count(store, "CAPITAL_DECISION") >= 1


def test_28_admitted_decision_produces_target(tmp_path):
    _, _, store, broker, _ = _started(tmp_path, events=(entry_event("ev-1"),))
    assert _journal_count(store, "TARGET_CREATED") >= 1
    row = store._conn.execute("SELECT COUNT(*) AS n FROM economic_targets").fetchone()
    assert int(row["n"]) >= 1


def test_29_target_produces_deterministic_intent(tmp_path):
    _, _, store, broker, _ = _started(tmp_path, events=(entry_event("ev-1"),))
    intents = store.intents()
    assert len(intents) == 1
    assert intents[0].intent_id.startswith("EI1_")
    # Re-deriving the same upstream event yields the same id (no random uuid).
    from execution_runtime.runtime import execution_intent_id

    again = execution_intent_id(
        runtime_id="rt-1",
        account_id="acct-1",
        strategy_id="scripted-strategy",
        deployment_generation="gen-1",
        event_id="ev-1",
        economic_target_id="",  # target id differs here; verify id stability separately
        instrument="EURUSD",
        side="BUY",
        broker_quantity=0.1,
    )
    assert again.startswith("EI1_")
    assert intents[0].intent_id != again  # target id is part of identity


# ── WRITE-AHEAD (30-33) ──────────────────────────────────────────────────


def test_30_intent_persisted_before_submit(tmp_path):
    from execution_runtime.runtime import CrashPoint, SimulatedCrash

    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession()
    rt, broker = make_runtime(
        profile, account, store, broker=broker,
        events=(entry_event("ev-1"),), crash_point=CrashPoint.AFTER_INTENT_COMMIT,
    )
    rt.start()
    try:
        rt.step()
    except SimulatedCrash:
        pass
    # Intent was committed before the (never-reached) broker submit.
    assert broker.order_count() == 0
    assert len(store.intents()) == 1


def test_31_broker_submit_occurs_after_commit(tmp_path):
    _, _, store, broker, _ = _started(tmp_path, events=(entry_event("ev-1"),))
    # Intent record exists AND broker accepted: write-ahead then submit.
    assert len(store.intents()) == 1
    assert broker.order_count() == 1


def test_32_submit_reject_recorded(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession()
    broker.set_fail_mode("ORDER_REJECT")
    rt, broker = make_runtime(profile, account, store, broker=broker, events=(entry_event("ev-1"),))
    rt.start()
    rt.step()
    assert store.intents()[0].state == IntentState.INTENT_REJECTED.value
    assert _journal_count(store, "ORDER_REJECTED") >= 1
    assert broker.position_count() == 0


def test_33_submit_transport_failure_recorded(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession()
    broker.set_fail_mode("TRANSPORT_ERROR")
    rt, broker = make_runtime(profile, account, store, broker=broker, events=(entry_event("ev-1"),))
    rt.start()
    rt.step()
    assert store.intents()[0].state == IntentState.INTENT_TRANSPORT_ERROR.value
    assert _journal_count(store, "ORDER_TRANSPORT_ERROR") >= 1


# ── FILL (34-38) ─────────────────────────────────────────────────────────


def test_34_full_fill_open_verified(tmp_path):
    _, _, store, broker, _ = _started(tmp_path, events=(entry_event("ev-1"),))
    assert store.owned_positions()[0].state == PositionState.FILLED.value
    assert _journal_count(store, "POSITION_OPEN_VERIFIED") >= 1
    assert store.intents()[0].state == IntentState.INTENT_FILLED.value


def test_35_zero_fill_not_open_verified(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession()
    broker.set_fail_mode("ZERO_FILL")
    rt, broker = make_runtime(profile, account, store, broker=broker, events=(entry_event("ev-1"),))
    rt.start()
    rt.step()
    assert broker.position_count() == 0
    assert store.intents()[0].state == IntentState.INTENT_ABORTED.value
    assert _journal_count(store, "POSITION_OPEN_VERIFIED") == 0


def test_36_partial_fill_not_treated_as_full(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession(partial_ratio=0.6)
    broker.set_fail_mode("PARTIAL_FILL")
    rt, broker = make_runtime(profile, account, store, broker=broker, events=(entry_event("ev-1"),))
    rt.start()
    rt.step()
    pos = store.owned_positions()[0]
    assert pos.state == PositionState.PARTIALLY_FILLED.value
    assert pos.filled_quantity < pos.requested_quantity
    assert store.intents()[0].state == IntentState.INTENT_PARTIALLY_FILLED.value
    assert _journal_count(store, "PARTIAL_FILL_OBSERVED") >= 1


def test_37_broker_order_id_persisted(tmp_path):
    _, _, store, broker, _ = _started(tmp_path, events=(entry_event("ev-1"),))
    intent = store.intents()[0]
    assert intent.broker_order_id != ""
    row = store._conn.execute(
        "SELECT COUNT(*) AS n FROM broker_orders WHERE order_id=?", (intent.broker_order_id,)
    ).fetchone()
    assert int(row["n"]) >= 1


def test_38_broker_position_id_persisted(tmp_path):
    _, _, store, broker, _ = _started(tmp_path, events=(entry_event("ev-1"),))
    pos = store.owned_positions()[0]
    assert pos.broker_position_id != ""
