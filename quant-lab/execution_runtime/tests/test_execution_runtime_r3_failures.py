"""QL-EXEC-R3 — authority / heartbeat / telemetry / purity tests (60-69, 75-80).

No real broker is ever contacted: the runtime is driven only through
SimBrokerSession (in-memory). Purity assertions guard the runtime package from
strategy-science / capital-routing / MetaTrader5 imports.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

from execution_runtime.authority import derive_execution_authority
from execution_runtime.brokers.sim_broker import SimBrokerSession
from execution_runtime.compatibility import evaluate_compatibility
from execution_runtime.enums import AccountRole, DesiredState, Environment, HedgingNetting
from execution_runtime.runtime.adapters import entry_event, exit_event
from execution_runtime.runtime.intent import PositionState
from execution_runtime.runtime.state import RuntimeState

from r3_harness import make_account, make_profile, make_runtime, make_store


def _started(tmp_path, *, events, broker=None):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = broker or SimBrokerSession()
    rt, broker = make_runtime(profile, account, store, broker=broker, events=events)
    rt.start()
    rt.step()
    return profile, account, store, broker, rt


# ── AUTHORITY (60-64) ────────────────────────────────────────────────────


def test_60_new_risk_denied_before_reconciliation(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    store.upsert_owned_position(
        "logical-1", runtime_id="rt-1", account_id="acct-1",
        strategy_id="scripted-strategy", intent_id="intent-1", event_id="ev-1",
        symbol="EURUSD", side="BUY", requested_quantity=0.1, filled_quantity=0.1,
        state=PositionState.FILLED.value, broker_position_id="missing",
        broker_order_id="o-1", ownership_tag="TAG-1", fill_price=1.1,
    )
    rt, _ = make_runtime(profile, account, store)
    assert rt.start() is RuntimeState.BLOCKED
    t = rt.telemetry()
    assert t.new_risk_authorized is False


def test_61_new_risk_denied_when_desired_stopped(tmp_path):
    profile, account, store, broker, rt = _started(tmp_path, events=(entry_event("ev-1"),))
    rt.stop()
    t = rt.telemetry()
    assert t.desired_state == DesiredState.STOPPED_BY_USER.value
    assert t.runtime_state == RuntimeState.STOPPED.value
    assert t.new_risk_authorized is False


def test_62_new_risk_denied_on_identity_mismatch(tmp_path):
    profile = make_profile()
    account = make_account()  # expected_server = SIM-Demo
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession(server="WRONG-Server")
    rt, _ = make_runtime(profile, account, store, broker=broker)
    assert rt.start() is RuntimeState.BLOCKED
    assert rt.telemetry().new_risk_authorized is False


def test_63_close_existing_risk_separately_evaluable():
    from execution_runtime.account import AccountObservedState
    from execution_runtime.hashing import config_hash
    from execution_runtime.profiles import RuntimeState as AuthorityRuntimeState
    from execution_runtime.types import utcnow_iso

    profile = make_account(operator_execution_requested=False)  # new risk denied
    observed = AccountObservedState(
        account_id="acct-1",
        observed_at=utcnow_iso(),
        transport_connected=True,
        authenticated=True,
        observed_broker_company="SIM-BROKER",
        observed_server="SIM-Demo",
        observed_environment=Environment.SIM,
        observed_currency="USD",
        hedging_or_netting=profile.expected_hedging_netting,
        reconciled=True,
    )
    runtime_state = AuthorityRuntimeState(
        runtime_id="rt-1", desired_state=DesiredState.RUNNING, safety_blocked=False
    )
    compat = evaluate_compatibility(
        profile.account_role, HedgingNetting.HEDGING, account_id="acct-1"
    )
    authority = derive_execution_authority(profile, observed, runtime_state, compat)
    assert authority.can_submit_new_risk is False  # operator did not request new risk
    assert authority.can_close_owned_risk is True  # closing owned risk stays evaluable


def test_64_follower_direct_execution_denied():
    from execution_runtime.account import AccountObservedState
    from execution_runtime.profiles import RuntimeState as AuthorityRuntimeState
    from execution_runtime.types import utcnow_iso

    profile = make_account(account_role=AccountRole.FOLLOWER, operator_execution_requested=True)
    observed = AccountObservedState(
        account_id="acct-1",
        observed_at=utcnow_iso(),
        transport_connected=True,
        authenticated=True,
        observed_broker_company="SIM-BROKER",
        observed_server="SIM-Demo",
        observed_environment=Environment.SIM,
        observed_currency="USD",
        hedging_or_netting=HedgingNetting.HEDGING,
        reconciled=True,
    )
    runtime_state = AuthorityRuntimeState(
        runtime_id="rt-1", desired_state=DesiredState.RUNNING, safety_blocked=False
    )
    compat = evaluate_compatibility(
        AccountRole.FOLLOWER, HedgingNetting.HEDGING, account_id="acct-1"
    )
    authority = derive_execution_authority(profile, observed, runtime_state, compat)
    assert authority.can_submit_new_risk is False
    assert authority.can_modify_foreign_risk is False


# ── HEARTBEAT / TELEMETRY (65-69) ────────────────────────────────────────


def test_65_heartbeat_persisted(tmp_path):
    _, _, store, _, _ = _started(tmp_path, events=(entry_event("ev-1"),))
    assert store.heartbeat_count() >= 1
    assert store.last_heartbeat() is not None


def test_66_telemetry_contains_identity(tmp_path):
    _, _, store, _, rt = _started(tmp_path, events=(entry_event("ev-1"),))
    t = rt.telemetry()
    assert t.runtime_id == "rt-1"
    assert t.account_id == "acct-1"
    assert t.strategy_id == "scripted-strategy"


def test_67_blocker_visible(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession(server="WRONG-Server")
    rt, _ = make_runtime(profile, account, store, broker=broker)
    rt.start()
    t = rt.telemetry()
    assert t.runtime_state == RuntimeState.BLOCKED.value
    assert t.blocking_reason != ""


def test_68_foreign_and_owned_counts_correct(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession()
    broker.seed_foreign_position("foreign-1", symbol="GBPUSD", ownership_tag="FOREIGN", magic=999999)
    rt, broker = make_runtime(profile, account, store, broker=broker, events=(entry_event("ev-1"),))
    rt.start()
    rt.step()
    t = rt.telemetry()
    assert t.owned_positions_count == 1
    assert t.foreign_positions_count == 1


def test_69_no_secret_leaked(tmp_path):
    _, _, store, _, rt = _started(tmp_path, events=(entry_event("ev-1"),))
    blob = __import__("json").dumps(rt.telemetry().to_dict(), sort_keys=True)
    assert "secret" not in blob.lower()
    assert "password" not in blob.lower()
    assert "credential" not in blob.lower()


# ── PURITY (75-80) ───────────────────────────────────────────────────────


def test_75_no_tb_strategy_import():
    import execution_runtime.runtime.engine as engine

    src = inspect.getsource(engine)
    assert "tb_live" not in src
    assert "triangular" not in src
    assert "tb_forward" not in src


def test_76_no_capital_routing_science():
    import execution_runtime.runtime.engine as engine

    src = inspect.getsource(engine)
    assert "capital_routing" not in src
    assert "capital-routing" not in src
    assert "70/30" not in src
    assert "pos_t" not in src


def test_77_no_metatrader5_import_in_runtime():
    import execution_runtime.runtime.engine as engine

    src = inspect.getsource(engine)
    # No import statement pulls in the real MetaTrader5 module.
    assert "import MetaTrader5" not in src
    assert "from MetaTrader5" not in src
    assert "MetaTrader5" not in sys.modules


def test_78_broker_session_only_transport_boundary():
    import execution_runtime.runtime.engine as engine

    src = inspect.getsource(engine)
    # The engine only talks to the injected broker object; no direct MT5 calls.
    assert "order_send" not in src
    assert "positions_get" not in src
    assert "symbol_info_tick" not in src


def test_79_no_real_broker_connection():
    # SimBrokerSession performs no network/terminal interaction.
    b = SimBrokerSession()
    assert b.connect() is True
    assert b.health()["connected"] is True
    # No MetaTrader5 module is ever loaded by the runtime package.
    assert "MetaTrader5" not in sys.modules


def test_80_no_real_broker_order(tmp_path):
    profile = make_profile()
    account = make_account()
    store = make_store(tmp_path, profile, account)
    broker = SimBrokerSession()
    broker.set_fail_mode("ORDER_REJECT")
    rt, broker = make_runtime(profile, account, store, broker=broker, events=(entry_event("ev-1"),))
    rt.start()
    rt.step()
    assert broker.position_count() == 0
    assert "MetaTrader5" not in sys.modules
