"""QL-EXEC-R3 — lifecycle tests.

Covers: singleton (10-13), desired state (14-17), startup lifecycle (18-23),
market recovery (70-71), and the state machine (72-74).
"""
from __future__ import annotations

import pytest

from execution_runtime.brokers.sim_broker import SimBrokerSession
from execution_runtime.enums import DesiredState
from execution_runtime.exceptions import InvalidStateTransition
from execution_runtime.runtime import (
    RuntimeState,
    SingletonConflict,
    SingletonLock,
    is_valid_transition,
    validate_transition,
)
from execution_runtime.runtime.adapters import ScriptedStrategyAdapter
from execution_runtime.runtime.engine import GenericRuntime

from r3_harness import make_account, make_profile, make_runtime, make_store


# ── SINGLETON (10-13) ────────────────────────────────────────────────────


def test_10_first_runtime_acquires(tmp_path):
    lock = SingletonLock(tmp_path / "rt-1.lock")
    assert lock.acquire("rt-1:instance") is True
    assert lock.held


def test_11_same_runtime_id_second_instance_blocked(tmp_path):
    lock = SingletonLock(tmp_path / "rt-1.lock")
    lock.acquire("rt-1:instance")
    second = SingletonLock(tmp_path / "rt-1.lock")
    with pytest.raises(SingletonConflict):
        second.acquire("rt-1:other-instance")


def test_12_different_runtime_id_allowed(tmp_path):
    a = SingletonLock(tmp_path / "rt-1.lock")
    b = SingletonLock(tmp_path / "rt-2.lock")
    assert a.acquire("rt-1:instance")
    assert b.acquire("rt-2:instance")


def test_13_released_lock_can_be_reacquired(tmp_path):
    lock = SingletonLock(tmp_path / "rt-1.lock")
    lock.acquire("rt-1:instance")
    lock.release()
    assert lock.acquire("rt-1:instance-2")


def test_singleton_engine_conflict(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    rt1, _ = make_runtime(profile, account, store)
    assert rt1.start() is RuntimeState.RUNNING
    # second runtime over same store/runtime_id cannot acquire authority
    rt2, _ = make_runtime(profile, account, store)
    assert rt2.start() is RuntimeState.FAILED


# ── DESIRED STATE (14-17) ────────────────────────────────────────────────


def test_14_default_desired_state_running(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    rt, _ = make_runtime(profile, account, store)
    assert rt.start() is RuntimeState.RUNNING
    assert rt.desired_state is DesiredState.RUNNING


def test_15_stopped_by_user_persists(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    rt, _ = make_runtime(profile, account, store)
    rt.start()
    rt.stop()
    assert store.read_desired_state() == DesiredState.STOPPED_BY_USER.value


def test_16_restart_respects_stopped_by_user(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    rt, _ = make_runtime(profile, account, store)
    rt.start()
    rt.stop()
    # New runtime over same store must NOT become RUNNING.
    rt2, _ = make_runtime(profile, account, store)
    assert rt2.start() is RuntimeState.STOPPED


def test_17_unexpected_crash_does_not_change_desired_state(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    rt, _ = make_runtime(profile, account, store)
    rt.start()
    # simulate crash: release singleton, do NOT call stop()
    rt._release_singleton()
    assert store.read_desired_state() == ""
    rt2, _ = make_runtime(profile, account, store)
    assert rt2.start() is RuntimeState.RUNNING  # still RUNNING (crash != stop)


# ── STARTUP LIFECYCLE (18-23) ────────────────────────────────────────────


def test_18_valid_startup_reaches_running(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    rt, _ = make_runtime(profile, account, store)
    assert rt.start() is RuntimeState.RUNNING


def test_19_broker_unavailable_waits(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession()
    broker.set_connect_ok(False)
    rt, _ = make_runtime(profile, account, store, broker=broker)
    assert rt.start() is RuntimeState.WAITING_FOR_BROKER


def test_20_identity_mismatch_blocks(tmp_path):
    profile = make_profile()
    account = make_account()  # expected_server = SIM-Demo
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession(server="WRONG-Server")
    rt, _ = make_runtime(profile, account, store, broker=broker)
    assert rt.start() is RuntimeState.BLOCKED
    assert "identity mismatch" in rt.blocking_reason


def test_21_reconciliation_required_before_running(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    # Seed a FILLED owned position with no broker match -> AMBIGUOUS -> BLOCK.
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
        state="FILLED",
        broker_position_id="missing",
        broker_order_id="order-1",
        ownership_tag="TAG-1",
        fill_price=1.1,
    )
    rt, _ = make_runtime(profile, account, store)
    assert rt.start() is RuntimeState.BLOCKED


def test_22_strategy_warm_failure_blocks(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    strategy = ScriptedStrategyAdapter(events=())
    strategy.set_warm_failure(True)
    from execution_runtime.runtime.adapters import (
        PassThroughCapitalPolicyAdapter,
        TestCapitalTranslationAdapter,
    )

    rt = GenericRuntime(
        profile=profile,
        account_profile=account,
        strategy=strategy,
        capital_policy=PassThroughCapitalPolicyAdapter(),
        capital_translation=TestCapitalTranslationAdapter(),
        broker=SimBrokerSession(),
        store=store,
    )
    assert rt.start() is RuntimeState.BLOCKED


def test_23_config_drift_blocks(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    # Same generation, different profile -> config drift -> BLOCKED.
    drifted = make_profile(runtime_id="rt-1", account_id="acct-1", metadata_version=99)
    rt, _ = make_runtime(drifted, account, store)
    assert rt.start() is RuntimeState.BLOCKED
    assert "CONFIG_DRIFT" in rt.blocking_reason


# ── MARKET / BROKER RECOVERY (70-71) ─────────────────────────────────────


def test_70_broker_unavailable_then_recovers(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession()
    rt, _ = make_runtime(profile, account, store, broker=broker)
    assert rt.start() is RuntimeState.RUNNING
    broker.disconnect()
    rt.step()
    assert rt.state is RuntimeState.WAITING_FOR_BROKER
    broker.set_connect_ok(True)
    rt.step()
    assert rt.state is RuntimeState.RUNNING


def test_71_fresh_observation_replaces_stale_status(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession()
    rt, _ = make_runtime(profile, account, store, broker=broker)
    rt.start()
    broker.disconnect()
    rt.step()
    assert rt.state is RuntimeState.WAITING_FOR_BROKER
    # Fresh healthy observation returns -> state recomputed, not latched.
    broker.set_connected(True)
    rt.step()
    assert rt.state is RuntimeState.RUNNING


# ── STATE MACHINE (72-74) ────────────────────────────────────────────────


def test_72_valid_transitions_accepted():
    for (prior, new) in (
        (RuntimeState.CREATED, RuntimeState.STARTING),
        (RuntimeState.STARTING, RuntimeState.CONNECTING),
        (RuntimeState.RECONCILING, RuntimeState.WARMING),
        (RuntimeState.WARMING, RuntimeState.RUNNING),
        (RuntimeState.RUNNING, RuntimeState.BLOCKED),
        (RuntimeState.BLOCKED, RuntimeState.RUNNING),
        (RuntimeState.RUNNING, RuntimeState.STOPPING),
        (RuntimeState.STOPPING, RuntimeState.STOPPED),
    ):
        assert is_valid_transition(prior, new)
        assert validate_transition(prior, new)


def test_73_invalid_transitions_rejected():
    for (prior, new) in (
        (RuntimeState.CREATED, RuntimeState.RUNNING),
        (RuntimeState.STOPPED, RuntimeState.RUNNING),
        (RuntimeState.FAILED, RuntimeState.RUNNING),
        (RuntimeState.RUNNING, RuntimeState.CREATED),
        (RuntimeState.CONNECTING, RuntimeState.WARMING),
    ):
        assert not is_valid_transition(prior, new)
        with pytest.raises(InvalidStateTransition):
            validate_transition(prior, new)


def test_74_blocked_is_not_failed():
    assert RuntimeState.BLOCKED is not RuntimeState.FAILED
    # BLOCKED can recover to RUNNING; FAILED is terminal.
    assert is_valid_transition(RuntimeState.BLOCKED, RuntimeState.RUNNING)
    assert not is_valid_transition(RuntimeState.FAILED, RuntimeState.RUNNING)
