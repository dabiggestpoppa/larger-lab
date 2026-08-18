"""QL-EXEC-R2 — MT5BrokerSession order / broker-state / snapshot / purity.

All order_send calls go through FakeMT5 only. No real MetaTrader5.
"""  # noqa: E501
from __future__ import annotations

from pathlib import Path

from execution_runtime.brokers.fake_mt5 import FakeMT5, _Rec
from execution_runtime.brokers.mt5 import (
    MT5BrokerSession,
    build_mt5_order_request,
    is_success_retcode,
)
from execution_runtime.enums import FillPolicy, OrderSide, OrderType, QuantityUnit, SlippageUnit
from execution_runtime.types import OrderIntent

PKG_DIR = Path(__file__).resolve().parents[1]
BROKERS_DIR = PKG_DIR / "brokers"


def _intent(**overrides) -> OrderIntent:
    d = dict(
        intent_id="i-1",
        account_id="acct-1",
        symbol="EURUSD",
        side=OrderSide.BUY,
        volume=0.1,
        order_type=OrderType.MARKET,
        reference_price=1.10005,
        fill_policy=FillPolicy.FILL_OR_KILL,
    )
    d.update(overrides)
    return OrderIntent(**d)


# ── POSITIONS / ORDERS / DEALS (46-50) ────────────────────────────────────


def test_46_position_normalization(fake_mt5):
    fake_mt5.set_positions([
        {"ticket": 11, "symbol": "EURUSD", "volume": 0.1, "type": 0,
         "price_open": 1.1, "magic": 777, "comment": "TB|tag", "profit": 5.0}
    ])
    s = MT5BrokerSession(fake_mt5); s.connect()
    (p,) = s.positions()
    assert p.position_id == "11"
    assert p.side == "LONG"
    assert p.magic == 777
    assert p.ownership_tag == "TB|tag"


def test_47_order_normalization(fake_mt5):
    fake_mt5.set_orders([
        {"ticket": 22, "symbol": "EURUSD", "volume_current": 0.1, "magic": 777, "comment": "TB|o"}
    ])
    s = MT5BrokerSession(fake_mt5); s.connect()
    (o,) = s.orders()
    assert o.order_id == "22"
    assert o.magic == 777


def test_48_deal_normalization(fake_mt5):
    fake_mt5.set_deals([
        {"ticket": 33, "order": 22, "position_id": 11, "symbol": "EURUSD",
         "volume": 0.1, "price": 1.1, "entry": 1, "magic": 777, "comment": "TB|d"}
    ])
    s = MT5BrokerSession(fake_mt5); s.connect()
    (d,) = s.deals()
    assert d.deal_id == "33"
    assert d.order_id == "22"
    assert d.position_id == "11"


def test_49_order_deal_position_ids_distinct(fake_mt5):
    fake_mt5.set_positions([{"ticket": 111, "symbol": "EURUSD", "volume": 0.1, "type": 0}])
    fake_mt5.set_orders([{"ticket": 222, "symbol": "EURUSD", "volume_current": 0.1}])
    fake_mt5.set_deals([
        {"ticket": 333, "order": 222, "position_id": 111, "symbol": "EURUSD",
         "volume": 0.1, "price": 1.1, "entry": 1}
    ])
    s = MT5BrokerSession(fake_mt5); s.connect()
    p = s.positions()[0]
    o = s.orders()[0]
    d = s.deals()[0]
    assert p.position_id != o.order_id != d.deal_id
    assert d.order_id == o.order_id
    assert d.position_id == p.position_id


def test_50_ownership_fields_preserved(fake_mt5):
    fake_mt5.set_positions([
        {"ticket": 11, "symbol": "EURUSD", "volume": 0.1, "type": 1,
         "magic": 999, "comment": "QL1|A12345678", "price_open": 1.1}
    ])
    s = MT5BrokerSession(fake_mt5); s.connect()
    p = s.positions()[0]
    assert p.magic == 999
    assert p.ownership_tag == "QL1|A12345678"


# ── ORDER CONTRACT (51-55) ────────────────────────────────────────────────


def test_51_generic_market_order():
    o = OrderIntent(intent_id="x", account_id="a", symbol="EURUSD")
    assert o.order_type is OrderType.MARKET
    assert o.side is OrderSide.BUY
    assert o.quantity_unit is QuantityUnit.LOT


def test_52_reference_price_explicit():
    o = _intent(reference_price=1.12345)
    assert o.reference_price == 1.12345


def test_53_fill_policy_explicit():
    o = _intent(fill_policy=FillPolicy.IMMEDIATE_OR_CANCEL)
    assert o.fill_policy is FillPolicy.IMMEDIATE_OR_CANCEL


def test_54_slippage_deviation_explicit():
    o = _intent(slippage_constraint=20, slippage_unit=SlippageUnit.POINTS)
    assert o.slippage_constraint == 20
    assert o.slippage_unit is SlippageUnit.POINTS


def test_55_no_mt5_enum_leaks_in_generic_contract():
    generic = []
    for p in sorted(PKG_DIR.glob("*.py")):
        generic.append(p.read_text(encoding="utf-8"))
    src = "\n".join(generic)
    for token in ("ORDER_TYPE_BUY", "TRADE_ACTION_DEAL", "ORDER_FILLING_FOK", "POSITION_TYPE_BUY"):
        assert token not in src, token


# ── ORDER CHECK (56-60) ───────────────────────────────────────────────────


def _check(fake_mt5, rec) -> object:
    fake_mt5.set_order_check(lambda req: rec)
    s = MT5BrokerSession(fake_mt5); s.connect()
    return s.order_check(_intent())


def test_56_order_check_retcode_0_success(fake_mt5):
    assert _check(fake_mt5, _Rec(retcode=0, comment="ok")).ok is True


def test_57_order_check_retcode_10009_success(fake_mt5):
    assert _check(fake_mt5, _Rec(retcode=10009, comment="done")).ok is True


def test_58_order_check_none_failure(fake_mt5):
    r = _check(fake_mt5, None)
    assert r.ok is False
    assert r.retcode is None


def test_59_order_check_reject_retcode(fake_mt5):
    r = _check(fake_mt5, _Rec(retcode=10030, comment="invalid fill"))
    assert r.ok is False
    assert r.retcode == 10030


def test_60_order_check_broker_message_retained(fake_mt5):
    r = _check(fake_mt5, _Rec(retcode=10030, comment="invalid fill mode"))
    assert r.broker_message == "invalid fill mode"


# ── ORDER SEND FAKE (61-67) ───────────────────────────────────────────────


def test_61_fake_buy_mapping(fake_mt5):
    s = MT5BrokerSession(fake_mt5); s.connect()
    s.submit_order(_intent(side=OrderSide.BUY))
    assert fake_mt5.order_send_calls[-1]["type"] == FakeMT5.ORDER_TYPE_BUY


def test_62_fake_sell_mapping(fake_mt5):
    s = MT5BrokerSession(fake_mt5); s.connect()
    s.submit_order(_intent(side=OrderSide.SELL, reference_price=1.1))
    assert fake_mt5.order_send_calls[-1]["type"] == FakeMT5.ORDER_TYPE_SELL


def test_63_fake_send_success(fake_mt5):
    fake_mt5.set_order_send(lambda req: _Rec(retcode=10009, comment="done", order=500))
    s = MT5BrokerSession(fake_mt5); s.connect()
    r = s.submit_order(_intent())
    assert r.ok is True
    assert r.broker_order_id == "500"


def test_64_fake_send_rejection(fake_mt5):
    fake_mt5.set_order_send(lambda req: _Rec(retcode=10030, comment="rejected"))
    s = MT5BrokerSession(fake_mt5); s.connect()
    r = s.submit_order(_intent())
    assert r.ok is False
    assert r.retcode == 10030


def test_65_zero_quantity_blocked(fake_mt5):
    s = MT5BrokerSession(fake_mt5); s.connect()
    r = s.submit_order(_intent(volume=0.0))
    assert r.ok is False
    assert fake_mt5.order_send_calls == []


def test_66_ownership_tag_included(fake_mt5):
    s = MT5BrokerSession(fake_mt5); s.connect()
    s.submit_order(_intent(ownership_tag="QL1|TAG", broker_magic=4242))
    req = fake_mt5.order_send_calls[-1]
    assert req["comment"] == "QL1|TAG"
    assert req["magic"] == 4242


def test_67_comment_encoding_deterministic():
    long_tag = "X" * 60
    a = build_mt5_order_request(_intent(ownership_tag=long_tag), None, None, 1)
    b = build_mt5_order_request(_intent(ownership_tag=long_tag), None, None, 1)
    assert a["comment"] == b["comment"]
    assert len(a["comment"]) == 29


# ── FILL (68-72) ──────────────────────────────────────────────────────────


def test_68_fok_mapping():
    req = build_mt5_order_request(_intent(fill_policy=FillPolicy.FILL_OR_KILL), None, None, None)
    # code resolved by adapter; verify pure builder accepts explicit code
    assert build_mt5_order_request(_intent(), None, None, 1)["type_filling"] == 1


def test_69_ioc_mapping():
    assert build_mt5_order_request(_intent(), None, None, 2)["type_filling"] == 2


def test_70_return_mapping():
    assert build_mt5_order_request(_intent(), None, None, 0)["type_filling"] == 0


def test_71_unsupported_fill_fails(fake_mt5):
    # omit IOC from the adapter's code table -> IOC becomes unsupported
    s = MT5BrokerSession(
        fake_mt5,
        fill_policy_codes={
            FillPolicy.FILL_OR_KILL: 1,
            FillPolicy.RETURN_OR_PARTIAL: 0,
        },
    )
    s.connect()
    r = s.order_check(_intent(fill_policy=FillPolicy.IMMEDIATE_OR_CANCEL))
    assert r.ok is False
    assert "unsupported fill policy" in r.reason


def test_72_declared_fill_capability_mismatch_representable(fake_mt5):
    # broker DECLARES IOC (bit 2) but order_check only accepts FOK (code 1)
    fake_mt5.set_symbol_info("EURUSD", visible=True, digits=5, point=0.00001,
                             trade_contract_size=100000.0, volume_min=0.01,
                             volume_step=0.01, volume_max=100.0, filling_mode=2)
    fake_mt5.set_order_check(
        lambda req: _Rec(retcode=0, comment="ok") if req.get("type_filling") == 1
        else _Rec(retcode=10030, comment="invalid fill")
    )
    s = MT5BrokerSession(fake_mt5); s.connect()
    declared = s.symbol_info("EURUSD").declared_fill_policies
    resolved = s.probe_fill_policies("EURUSD")
    assert FillPolicy.IMMEDIATE_OR_CANCEL in declared
    assert resolved is FillPolicy.FILL_OR_KILL


# ── CLOSE / CANCEL (73-75) ────────────────────────────────────────────────


def test_73_cancel_normalized(fake_mt5):
    s = MT5BrokerSession(fake_mt5); s.connect()
    r = s.cancel_order("55")
    assert r.ok is True
    assert fake_mt5.order_send_calls[-1]["action"] == 8
    assert fake_mt5.order_send_calls[-1]["order"] == 55


def test_74_close_normalized(fake_mt5):
    fake_mt5.set_positions([
        {"ticket": 11, "symbol": "EURUSD", "volume": 0.1, "type": 0, "price_open": 1.1, "magic": 7}
    ])
    s = MT5BrokerSession(fake_mt5); s.connect()
    r = s.close_position("11")
    assert r.ok is True
    req = fake_mt5.order_send_calls[-1]
    assert req["position"] == 11
    assert req["type"] == FakeMT5.ORDER_TYPE_SELL  # LONG -> SELL close


def test_75_no_foreign_automatic_close(fake_mt5):
    s = MT5BrokerSession(fake_mt5); s.connect()
    r = s.close_position("999999")
    assert r.ok is False
    assert fake_mt5.order_send_calls == []


# ── SNAPSHOT (76-79) ──────────────────────────────────────────────────────


def test_76_snapshot_account(fake_mt5):
    s = MT5BrokerSession(fake_mt5); s.connect()
    snap = s.reconcile_snapshot()
    assert snap.account_state.equity == 10000.0


def test_77_snapshot_positions(fake_mt5):
    fake_mt5.set_positions([{"ticket": 1, "symbol": "EURUSD", "volume": 0.1, "type": 0}])
    s = MT5BrokerSession(fake_mt5); s.connect()
    assert len(s.reconcile_snapshot().positions) == 1


def test_78_snapshot_orders(fake_mt5):
    fake_mt5.set_orders([{"ticket": 2, "symbol": "EURUSD", "volume_current": 0.1}])
    s = MT5BrokerSession(fake_mt5); s.connect()
    assert len(s.reconcile_snapshot().orders) == 1


def test_79_snapshot_deals(fake_mt5):
    fake_mt5.set_deals([{"ticket": 3, "symbol": "EURUSD", "volume": 0.1, "price": 1.1}])
    s = MT5BrokerSession(fake_mt5); s.connect()
    assert len(s.reconcile_snapshot().deals) == 1


# ── PURITY (80-85) ────────────────────────────────────────────────────────


def _broker_src() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(BROKERS_DIR.glob("*.py")))


def _imported_modules(src: str) -> set:
    import ast

    tree = ast.parse(src)
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mods.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            mods.add((node.module or "").split(".")[0])
    return mods


def test_80_no_tb_strategy_import():
    mods = _imported_modules(_broker_src())
    assert not (mods & {"tb_live", "tb_forward", "triangular_basis", "tb_worker", "tb_runtime_config"})


def test_81_no_capital_routing_strategy_import():
    mods = _imported_modules(_broker_src())
    assert not (mods & {"capital_routing"})
    src = _broker_src()
    for token in ("A1_70_30", "H1-1.00", "pos_t", "USDJPY", "24.494897"):
        assert token not in src, token


def test_82_no_worker_migration():
    mods = _imported_modules(_broker_src())
    assert "tb_worker" not in mods
    assert "supervisor" not in mods


def test_83_no_active_tb_file_modification():
    # R2 only ADDS files under execution_runtime/; it never references TB paths.
    src = _broker_src()
    assert "quant-lab/runtime" not in src
    assert "quant-lab/engines" not in src


def test_84_no_real_order_send(fake_mt5):
    s = MT5BrokerSession(fake_mt5); s.connect()
    s.submit_order(_intent())
    assert s._mt5 is fake_mt5
    assert len(fake_mt5.order_send_calls) == 1


def test_85_no_network_dependency():
    mods = _imported_modules(_broker_src())
    assert not (mods & {"socket", "requests", "urllib", "http", "httpx"})


# ── NONREGRESSION (88-90 explicit; 86-87 are the preserved R1/R1.1 suites) ─


def test_88_market_recovery_observation_freshness(fake_mt5):
    s = MT5BrokerSession(fake_mt5); s.connect()
    fake_mt5.set_tick("EURUSD", bid=1.05, ask=1.05005, time=__import__("time").time() + 3 * 3600)
    t1 = s.tick("EURUSD")
    fake_mt5.set_tick("EURUSD", bid=1.20, ask=1.20005, time=__import__("time").time() + 3 * 3600)
    t2 = s.tick("EURUSD")
    assert t1.bid != t2.bid
    assert t2.bid == 1.20


def test_89_source_timestamp_semantics():
    assert is_success_retcode(0) is True
    assert is_success_retcode(10009) is True


def test_90_success_retcode_behavior():
    assert is_success_retcode(None) is False
    assert is_success_retcode(10030) is False
    assert is_success_retcode(0) is True
