"""QL-EXEC-R3 — ownership + reconciliation tests.

Covers: owned vs foreign recognition (39-42) and the reconciliation taxonomy
(43-49). Pure Reconciler calls plus runtime-level reconstruction behavior.
"""
from __future__ import annotations

from execution_runtime.brokers.sim_broker import SimBrokerSession
from execution_runtime.runtime import Reconciler, ReconciliationState
from execution_runtime.runtime.intent import IntentState, PositionState
from execution_runtime.runtime.state import RuntimeState
from execution_runtime.types import Position

from r3_harness import make_account, make_profile, make_runtime, make_store


def _owned(**kw):
    d = dict(
        logical_ownership_id="logical-1",
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
        broker_position_id="bp-1",
        broker_order_id="bo-1",
        ownership_tag="TAG-1",
        fill_price=1.1,
    )
    d.update(kw)
    from execution_runtime.runtime.store import OwnedPositionRecord

    return OwnedPositionRecord(**d)


def _intent(**kw):
    d = dict(
        intent_id="intent-1",
        state=IntentState.INTENT_CREATED.value,
        event_id="ev-1",
        ownership_tag="TAG-1",
        broker_order_id="",
        broker_position_id="",
        broker_quantity=0.1,
        filled_quantity=0.0,
    )
    d.update(kw)
    from execution_runtime.runtime.store import IntentRecord

    return IntentRecord(**d)


def _pos(position_id, ownership_tag, magic=0):
    return Position(
        position_id=position_id,
        symbol="EURUSD",
        volume=0.1,
        side="LONG",
        price_open=1.1,
        magic=magic,
        ownership_tag=ownership_tag,
        time=0.0,
    )


def _reconcile(broker_positions, owned=(), intents=()):
    return Reconciler().reconcile(
        broker_positions=tuple(broker_positions), owned_positions=owned, intents=intents
    )


# ── OWNERSHIP (39-42) ────────────────────────────────────────────────────


def test_39_runtime_owned_position_recognized():
    rec = _reconcile([_pos("bp-1", "TAG-1")], owned=[_owned()], intents=[])
    assert rec.state is ReconciliationState.OPEN_MATCH
    assert rec.owned_count == 1
    assert rec.foreign_count == 0


def test_40_foreign_position_not_claimed():
    rec = _reconcile([_pos("bp-9", "FOREIGN", magic=999999)], owned=[], intents=[])
    assert rec.state is ReconciliationState.FOREIGN_ONLY
    assert rec.foreign_count == 1
    assert rec.owned_count == 0


def test_41_foreign_position_never_closed(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession()
    broker.seed_foreign_position("foreign-1", symbol="GBPUSD", ownership_tag="FOREIGN", magic=999999)
    rt, _ = make_runtime(profile, account, store, broker=broker)
    rt.start()
    rt.step()
    # The foreign position must still be present and untouched.
    assert "foreign-1" in broker.positions()[0].position_id or broker.position_count() == 1
    assert broker.broker_position("foreign-1") is not None


def test_42_duplicate_owned_exposure_flagged():
    owned = _owned()
    intents = _intent()
    rec = _reconcile(
        [_pos("bp-1", "TAG-1"), _pos("bp-2", "TAG-1")],
        owned=[owned],
        intents=[intents],
    )
    assert rec.state is ReconciliationState.DUPLICATE_OWNED_EXPOSURE
    assert not rec.clean


# ── RECONCILIATION (43-49) ───────────────────────────────────────────────


def test_43_flat_flat_flat_match():
    rec = _reconcile([], owned=[], intents=[])
    assert rec.state is ReconciliationState.FLAT_MATCH
    assert rec.clean


def test_44_open_matching_open_match():
    rec = _reconcile([_pos("bp-1", "TAG-1")], owned=[_owned()], intents=[])
    assert rec.state is ReconciliationState.OPEN_MATCH
    assert rec.clean


def test_45_intent_pending_broker_position_reconstruct_without_resubmit(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession()
    # Seed a pending intent + a matching broker position (crash-after-submit).
    from execution_runtime.runtime.intent import ExecutionIntent

    store.create_intent(
        ExecutionIntent(
            intent_id="intent-1",
            runtime_id="rt-1",
            account_id="acct-1",
            strategy_id="scripted-strategy",
            deployment_generation="gen-1",
            event_id="ev-1",
            economic_target_id="tgt-1",
            instrument="EURUSD",
            broker_symbol="EURUSD",
            side="BUY",
            broker_quantity=0.1,
            logical_ownership_id="logical-1",
            ownership_tag="TAG-1",
            broker_magic=1,
        )
    )
    broker.seed_foreign_position("bp-1", symbol="EURUSD", ownership_tag="TAG-1", magic=1)
    rt, _ = make_runtime(profile, account, store, broker=broker, events=())
    rt.start()
    # Broker position must be reconstructed WITHOUT a new submit (still 1 order).
    assert store.get_intent("intent-1").state == IntentState.INTENT_FILLED.value
    assert broker.order_count() == 0  # no resubmit occurred


def test_46_local_open_broker_missing_ambiguity():
    rec = _reconcile([], owned=[_owned()], intents=[])
    assert rec.state is ReconciliationState.AMBIGUOUS
    assert not rec.clean


def test_47_broker_owned_local_missing_reconstruct():
    rec = _reconcile([_pos("bp-1", "TAG-1")], owned=[], intents=[_intent()])
    assert rec.state is ReconciliationState.BROKER_OWNED_LOCAL_MISSING
    assert rec.recoverable
    assert rec.action == "RECONSTRUCT"


def test_48_foreign_only_clean_but_foreign():
    rec = _reconcile([_pos("bp-9", "FOREIGN", magic=999999)], owned=[], intents=[])
    assert rec.state is ReconciliationState.FOREIGN_ONLY
    assert rec.clean
    assert rec.foreign_count == 1


def test_49_duplicate_owned_broker_positions_blocks():
    rec = _reconcile(
        [_pos("bp-1", "TAG-1"), _pos("bp-2", "TAG-1")],
        owned=[_owned()],
        intents=[_intent()],
    )
    assert rec.state is ReconciliationState.DUPLICATE_OWNED_EXPOSURE
    assert not rec.clean
    assert rec.action == "BLOCK"
