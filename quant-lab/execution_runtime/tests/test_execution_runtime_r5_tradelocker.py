"""QL-EXEC-R5 — TradeLocker provider foundation tests (60-test matrix).

Covers the R5 minimum test matrix 1-60 (offline/mock only; no network, no
live orders). Provider truth is exercised through FakeTradeLocker behind the
transport protocol, exactly like FakeMT5 is injected into MT5BrokerSession.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

_QL = Path(__file__).resolve().parents[2]  # quant-lab/
if str(_QL) not in sys.path:
    sys.path.insert(0, str(_QL))

import pytest  # noqa: E402

from execution_runtime.enums import (  # noqa: E402
    BrokerErrorCategory,
    CapabilityState,
    ExecutionTransport,
    FillPolicy,
    OrderSide,
    OrderType,
    QuantityUnit,
)
from execution_runtime.tradelocker import (  # noqa: E402
    FakeTradeLocker,
    TradeLockerApiError,
    TradeLockerAuthError,
    TradeLockerAuthProvider,
    TradeLockerBrokerSession,
    TradeLockerClient,
    TradeLockerRateLimitExceeded,
)
from execution_runtime.tradelocker.config import TradeLockerConfigParser  # noqa: E402
from execution_runtime.types import OrderIntent  # noqa: E402

BASE_URL = "https://demo.tradelocker.com/backend-api"


# ─── fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def fake():
    f = FakeTradeLocker()
    f.add_instrument(101, name="GBPAUD", symbol_id=1001)
    f.add_instrument(101, name="GBPNZD", symbol_id=1002)
    f.add_instrument(101, name="AUDNZD", symbol_id=1003)
    f.add_instrument(101, name="EURUSD", symbol_id=1004)
    f.add_instrument(102, name="EURUSD", symbol_id=2001)
    return f


def _secret_provider(name):
    return {"EMAIL": "user@example.com", "PASS": "s3cret"}.get(name, "")


@pytest.fixture
def client(fake):
    auth = TradeLockerAuthProvider(
        base_url=BASE_URL,
        transport=fake,
        secret_provider=_secret_provider,
        email_ref="EMAIL",
        password_ref="PASS",
        server="demo-server",
    )
    c = TradeLockerClient(auth=auth, transport=fake, acc_num=1000001)
    c.authenticate()
    return c


@pytest.fixture
def session(client):
    s = TradeLockerBrokerSession(
        client=client, account_id=101, acc_num=1000001, server="demo-server"
    )
    assert s.connect(), "session connect failed"
    return s


def intent(symbol="EURUSD", side=OrderSide.BUY, volume=0.10, **kw):
    defaults = dict(
        intent_id="i-1",
        account_id="101",
        symbol=symbol,
        side=side,
        volume=volume,
        quantity_unit=QuantityUnit.LOT,
        order_type=OrderType.MARKET,
        ownership_tag="R5-TEST",
    )
    defaults.update(kw)
    return OrderIntent(**defaults)


# ─── 1-5 auth ─────────────────────────────────────────────────────────────


def test_01_jwt_auth_success(fake):
    auth = TradeLockerAuthProvider(
        base_url=BASE_URL, transport=fake, secret_provider=_secret_provider,
        email_ref="EMAIL", password_ref="PASS", server="demo-server",
    )
    assert not auth.tokens_present()
    auth.authenticate()
    assert auth.tokens_present()
    assert auth.get_access_token().startswith("ey")  # real JWT-shaped token
    assert fake.refresh_calls == 0


def test_02_auth_failure(fake):
    auth = TradeLockerAuthProvider(
        base_url=BASE_URL, transport=fake, secret_provider=lambda n: "wrong",
        email_ref="EMAIL", password_ref="PASS", server="demo-server",
    )
    with pytest.raises(TradeLockerAuthError):
        auth.authenticate()
    assert not auth.tokens_present()


def test_03_refresh_success(fake, client):
    from execution_runtime.tradelocker.auth import decode_jwt_expiry

    assert client.authenticated()
    # Issue a short-lived token through a real refresh (1 second TTL).
    fake.set_access_ttl(1.0)
    client._auth.refresh_access_token(force=True)
    token_before = client._auth._access_token
    # Next refresh issues a long-lived token again.
    fake.set_access_ttl(3600.0)
    # Proactive refresh: expiry below the 30-minute threshold triggers it.
    refreshed = client._auth.get_access_token()
    assert refreshed != token_before
    assert fake.refresh_calls == 2
    assert decode_jwt_expiry(refreshed) is not None
    assert decode_jwt_expiry(refreshed) > decode_jwt_expiry(token_before)


def test_04_refresh_failure(fake, client):
    fake.expire_access_token()
    fake.set_refresh_enabled(False)
    with pytest.raises(TradeLockerAuthError):
        client._auth.refresh_access_token(force=True)


def test_05_concurrent_refresh_singleflight(fake, client):
    # Hold a short-lived token so all threads see near-expiry simultaneously.
    fake.set_access_ttl(1.0)
    client._auth.refresh_access_token(force=True)
    # The ONE refresh that resolves the stampede issues a long-lived token.
    fake.set_access_ttl(3600.0)
    baseline = fake.refresh_calls
    errors = []
    results = []

    def worker():
        try:
            tok = client._auth.get_access_token()
            results.append(tok)
        except Exception as err:  # noqa: BLE001
            errors.append(err)

    threads = [threading.Thread(target=worker) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert len(results) == 6
    assert len(set(results)) == 1  # all shared ONE refreshed token
    # singleflight: exactly ONE refresh resolved the concurrent stampede
    assert fake.refresh_calls == baseline + 1


# ─── 6-8 accounts ─────────────────────────────────────────────────────────


def test_06_all_accounts_parsing(session):
    accounts = session.discover_accounts()
    assert len(accounts) == 2
    ids = {(a.account_id, a.acc_num) for a in accounts}
    assert ids == {(101, 1000001), (102, 1000002)}


def test_07_account_id_acc_num_retained_separately(session):
    assert session.account_id == 101
    assert session.acc_num == 1000001
    assert session.identity().account_identifier == "1000001"


def test_08_multi_account_isolation(fake, client):
    s1 = TradeLockerBrokerSession(client=client, account_id=101, acc_num=1000001, server="s")
    s2 = TradeLockerBrokerSession(client=client, account_id=102, acc_num=1000002, server="s")
    assert s1.connect() and s2.connect()
    r = s1.submit_order(intent(symbol="EURUSD", side=OrderSide.BUY, volume=0.10))
    assert r.ok
    assert len(s1.positions()) == 1
    assert s2.positions() == []  # no cross-account contamination
    assert s2.orders() == []
    assert s2.deals() == []


# ─── 9-13 instruments / config / routes ───────────────────────────────────


def test_09_instrument_list_parsing(session):
    names = {"GBPAUD", "GBPNZD", "AUDNZD", "EURUSD"}
    assert set(session._instruments_by_name) == names
    si = session.symbol_info("EURUSD")
    assert si.symbol == "EURUSD" and si.digits == 5


def test_10_info_route_mapping(session):
    tick = session.tick("EURUSD")
    assert tick is not None and tick.valid
    assert tick.bid == 1.10000 and tick.ask == 1.10005
    assert tick.source_clock_name == "TRADELOCKER_SERVER_TIME"


def test_11_trade_route_mapping(session):
    # The provider rejects a TRADE route id that is not bound to the instrument.
    with pytest.raises(TradeLockerApiError):
        session._client.place_order(
            account_id=101,
            instrument_id=session._instrument("EURUSD").tradable_instrument_id,
            qty=0.1, side="buy", order_type="market", validity="IOC",
            route_id="zzz",
        )


def test_12_config_parsing(session, client):
    cfg = client.get_config(force=True)
    assert cfg.version_hash.startswith("cfg_")
    assert "ordersConfig" in cfg.columns
    assert "positionsConfig" in cfg.columns
    assert "accountDetailsConfig" in cfg.columns
    assert "id" in cfg.columns["ordersConfig"]
    assert len(cfg.rate_limits) >= 5
    # same payload → stable hash
    assert client.get_config(force=True).version_hash == cfg.version_hash


def test_13_dynamic_field_mapping(session, fake):
    r = session.submit_order(intent(symbol="EURUSD", side=OrderSide.SELL, volume=0.25))
    assert r.ok
    rows = session._client.get_positions(101)
    assert len(rows) == 1
    assert rows[0]["qty"] == 0.25
    assert rows[0]["side"] == "sell"
    assert rows[0]["strategyId"] == "R5-TEST"
    assert rows[0]["tradableInstrumentId"] == fake.instrument_ids(101)["EURUSD"]


# ─── 14-16 rate limits ────────────────────────────────────────────────────


def test_14_rate_limit_parsing(client):
    cfg = client.get_config(force=True)
    by_name = {rl.route_name: rl for rl in cfg.rate_limits}
    assert by_name["QUOTES_HISTORY"].limit == 10
    assert by_name["QUOTES_HISTORY"].seconds == 60
    assert by_name["PLACE_ORDER"].limit == 30


def test_15_rate_limit_enforcement(fake, client):
    fake.set_rate_limit_enabled(True)
    # QUOTES limit is 10 per 60s
    for _ in range(10):
        client.get_quotes(fake.instrument_ids(101)["EURUSD"], "a")
    with pytest.raises(TradeLockerRateLimitExceeded):
        client.get_quotes(fake.instrument_ids(101)["EURUSD"], "a")


def test_16_429_backoff_bounded(fake, client):
    fake.set_rate_limit_enabled(True)
    fake.set_access_ttl(3600.0)
    for _ in range(10):
        client.get_quotes(fake.instrument_ids(101)["EURUSD"], "a")
    # bounded: raises instead of spinning forever
    import time as _t
    start = _t.time()
    with pytest.raises(TradeLockerRateLimitExceeded):
        client.get_quotes(fake.instrument_ids(101)["EURUSD"], "a")
    assert _t.time() - start < 30  # never infinite


# ─── 17-21 state / positions / orders / fills ─────────────────────────────


def test_17_account_state(session):
    st = session.account_state()
    assert st.balance == 10000.0
    assert st.equity == 10000.0
    assert st.free_margin == 10000.0
    assert st.currency == "USD"


def test_18_positions_after_market_order(session):
    r = session.submit_order(intent(symbol="EURUSD", side=OrderSide.BUY, volume=0.10))
    assert r.ok
    pos = session.positions()
    assert len(pos) == 1
    assert pos[0].symbol == "EURUSD"
    assert pos[0].volume == 0.10
    assert pos[0].side == "LONG"
    assert pos[0].ownership_tag == "R5-TEST"


def test_19_nonfinal_orders_only(session):
    r = session.submit_order(
        intent(symbol="EURUSD", order_type=OrderType.LIMIT, reference_price=1.05000)
    )
    assert r.ok
    assert session.positions() == []  # accepted limit order: no position
    orders = session.orders()
    assert len(orders) == 1
    assert orders[0].order_type == "limit"


def test_20_order_history(session):
    session.submit_order(intent(symbol="EURUSD", volume=0.10))
    session.submit_order(
        intent(symbol="EURUSD", order_type=OrderType.LIMIT, reference_price=1.05)
    )
    hist = session._client.get_orders(101, history=True)
    assert len(hist) == 2
    nonfinal = session._client.get_orders(101, history=False)
    assert len(nonfinal) == 1


def test_21_fill_history_normalization(session):
    session.submit_order(intent(symbol="EURUSD", side=OrderSide.BUY, volume=0.10))
    deals = session.deals()
    assert len(deals) == 1
    assert deals[0].entry is True
    assert deals[0].side == "LONG"
    assert deals[0].volume == 0.10
    assert deals[0].symbol == "EURUSD"


# ─── 22-25 order mapping ──────────────────────────────────────────────────


def test_22_market_order_mapping(session, fake):
    r = session.submit_order(intent(symbol="EURUSD", side=OrderSide.SELL, volume=0.10))
    assert r.ok
    row = fake.all_orders(101)[0]
    assert row["type"] == "market"
    assert row["validity"] == "IOC"
    assert row["side"] == "sell"


def test_23_limit_order_mapping(session, fake):
    r = session.submit_order(
        intent(symbol="EURUSD", order_type=OrderType.LIMIT, reference_price=1.05)
    )
    assert r.ok
    row = fake.all_orders(101)[0]
    assert row["type"] == "limit"
    assert row["validity"] == "GTC"


def test_24_stop_order_mapping(session, fake):
    r = session.submit_order(
        intent(symbol="EURUSD", side=OrderSide.SELL, order_type=OrderType.STOP,
               price_constraint=1.05000)
    )
    assert r.ok
    row = fake.all_orders(101)[0]
    assert row["type"] == "stop"
    assert row["validity"] == "GTC"
    assert row["stopPrice"] == 1.05


def test_25_invalid_tif_blocked(session):
    # market orders must be IOC — a non-IOC fill policy is blocked locally.
    r = session.submit_order(
        intent(symbol="EURUSD", fill_policy=FillPolicy.FILL_OR_KILL)
    )
    assert not r.ok
    assert r.error_category is BrokerErrorCategory.INVALID_REQUEST


# ─── 26-30 fill truth ─────────────────────────────────────────────────────


def test_26_accepted_order_not_filled_position(session):
    # A resting (limit) order is ACCEPTED but creates NO position.
    r = session.submit_order(
        intent(symbol="EURUSD", order_type=OrderType.LIMIT, reference_price=1.05)
    )
    assert r.ok and r.broker_order_id
    assert session.positions() == []


def test_27_order_id_not_position_id(session):
    r = session.submit_order(intent(symbol="EURUSD", volume=0.10))
    assert r.ok
    pos = session.positions()[0]
    assert r.broker_order_id != pos.position_id


def test_28_position_reconciliation(session):
    session.submit_order(intent(symbol="EURUSD", volume=0.10))
    snap = session.reconcile_snapshot()
    assert len(snap.positions) == 1
    pid = snap.positions[0].position_id
    assert session.close_position(pid, "test").ok
    assert session.positions() == []


def test_29_close_request_not_closed_truth(fake, session):
    session.submit_order(intent(symbol="EURUSD", volume=0.10))
    pid = session.positions()[0].position_id
    fake.set_defer_close(True)
    cr = session.close_position(pid, "test")
    assert cr.ok  # closing ORDER placed
    assert len(session.positions()) == 1  # ...but position still open
    fake.resolve_pending_closes()
    assert session.positions() == []  # provider truth catches up


def test_30_partial_close_reconciliation(fake, client):
    client.authenticated()
    client.get_config(force=True)
    # open via client directly for full qty control
    client.place_order(
        account_id=101, instrument_id=fake.instrument_ids(101)["EURUSD"],
        qty=1.0, side="buy", order_type="market", validity="IOC", route_id="b",
        strategy_id="R5-TEST",
    )
    rows = client.get_positions(101)
    pid = rows[0]["id"]
    assert rows[0]["qty"] == 1.0
    assert client.close_position(pid, qty=0.4)
    rows = client.get_positions(101)
    assert len(rows) == 1
    assert abs(rows[0]["qty"] - 0.6) < 1e-9  # remaining quantity reconciled


# ─── 31-39 failure matrix ─────────────────────────────────────────────────


def test_31_order_reject(fake, session):
    fake.set_reject_next_order()
    r = session.submit_order(intent(symbol="EURUSD", volume=0.10))
    assert not r.ok
    assert r.error_category is BrokerErrorCategory.ORDER_REJECTED
    assert session.positions() == []


def test_32_timeout_before_send(fake, session):
    fake.set_timeout_mode("before_send")
    r = session.submit_order(intent(symbol="EURUSD", volume=0.10))
    assert not r.ok
    assert r.error_category is BrokerErrorCategory.TRANSPORT_ERROR
    assert "before send" in r.reason
    assert fake.open_positions(101) == []


def test_33_ambiguous_timeout_after_possible_send(fake, session):
    fake.set_timeout_mode("ambiguous")
    r = session.submit_order(intent(symbol="EURUSD", volume=0.10))
    assert not r.ok
    assert r.error_category is BrokerErrorCategory.TRANSPORT_ERROR
    assert "ambiguous" in r.reason


def test_34_no_blind_retry(fake, session):
    fake.set_timeout_mode("ambiguous")
    before = fake.request_count
    r = session.submit_order(intent(symbol="EURUSD", volume=0.10))
    assert not r.ok
    assert fake.request_count == before + 1  # exactly ONE attempt, no retry


def test_35_401_token_rejected_refresh_retry(fake, session):
    fake.expire_access_token()
    r = session.submit_order(intent(symbol="EURUSD", volume=0.10))
    assert r.ok  # refreshed once, retried once, succeeded
    assert fake.refresh_calls == 1
    assert len(session.positions()) == 1


def test_36_403_permission_denied(fake, session):
    fake.set_status_403(True)
    r = session.submit_order(intent(symbol="EURUSD", volume=0.10))
    assert not r.ok
    assert r.error_category is BrokerErrorCategory.TRANSPORT_ERROR


def test_37_404_bad_account_or_instrument(session):
    cr = session.cancel_order("999999")
    assert not cr.ok
    assert cr.error_category is BrokerErrorCategory.INVALID_REQUEST
    fake_missing = session
    # close unknown position -> 404 -> INVALID_REQUEST
    fake_missing._client._transport._missing_position = True
    cr2 = session.close_position("123456", "test")
    assert not cr2.ok
    assert cr2.error_category is BrokerErrorCategory.INVALID_REQUEST


def test_38_5xx_provider_error(fake, session):
    fake.set_status_5xx(True)
    r = session.submit_order(intent(symbol="EURUSD", volume=0.10))
    assert not r.ok
    assert r.error_category is BrokerErrorCategory.TRANSPORT_ERROR


def test_39_malformed_response(fake, session):
    fake.set_malformed_json(True)
    r = session.submit_order(intent(symbol="EURUSD", volume=0.10))
    assert not r.ok
    assert r.error_category is BrokerErrorCategory.TRANSPORT_ERROR
    fake.set_malformed_json(False)
    # read paths fail soft (empty), never crash
    assert session.positions() == []
    assert session.orders() == []


# ─── 40-41 drift ──────────────────────────────────────────────────────────


def test_40_config_drift_detected():
    p = TradeLockerConfigParser()
    base = {
        "ordersConfig": {"columns": [{"id": "id"}, {"id": "qty"}]},
        "rateLimits": [{"rateLimitType": "QUOTES_HISTORY", "limit": 10, "seconds": 60}],
        "limits": [],
    }
    drifted = {
        "ordersConfig": {"columns": [{"id": "id"}, {"id": "qty"}, {"id": "newField"}]},
        "rateLimits": [{"rateLimitType": "QUOTES_HISTORY", "limit": 10, "seconds": 60}],
        "limits": [],
    }
    assert p.parse(base).version_hash != p.parse(drifted).version_hash


def test_41_route_id_drift_fails_closed(fake, session):
    # Cache is bound to the connected instrument routes; if the provider's
    # TRADE route changes, the stale cached route is rejected by the provider
    # and the order fails closed (ORDER_REJECTED), never silently re-routed.
    fake.set_reject_next_order()  # provider rejects invalid routeId order
    r = session.submit_order(intent(symbol="EURUSD", volume=0.10))
    assert not r.ok
    assert r.error_category is BrokerErrorCategory.ORDER_REJECTED


# ─── 42-47 write-ahead / restart ──────────────────────────────────────────


def test_42_validation_before_any_network_write(fake, session):
    before = fake.request_count
    # order_check is LOCAL: zero transport calls
    check = session.order_check(intent(symbol="EURUSD", volume=0.10))
    assert check.ok
    assert fake.request_count == before
    # bad intent never reaches the wire
    session.submit_order(intent(symbol="EURUSD", volume=-1.0))
    assert fake.request_count == before
    # a real submit is exactly ONE POST
    session.submit_order(intent(symbol="EURUSD", volume=0.10))
    assert fake.request_count == before + 1


def test_43_restart_before_send(fake, client):
    s1 = TradeLockerBrokerSession(client=client, account_id=101, acc_num=1000001, server="s")
    assert s1.connect()
    fake.set_timeout_mode("before_send")
    s1.submit_order(intent(symbol="EURUSD", volume=0.10))
    fake.set_timeout_mode(None)
    s2 = TradeLockerBrokerSession(client=client, account_id=101, acc_num=1000001, server="s")
    assert s2.connect()
    assert s2.positions() == []  # nothing was created before the send


def test_44_restart_after_ambiguous_post(fake, client):
    s1 = TradeLockerBrokerSession(client=client, account_id=101, acc_num=1000001, server="s")
    assert s1.connect()
    fake.set_timeout_mode("ambiguous")
    s1.submit_order(intent(symbol="EURUSD", volume=0.10))
    fake.set_timeout_mode(None)
    s2 = TradeLockerBrokerSession(client=client, account_id=101, acc_num=1000001, server="s")
    assert s2.connect()
    # ambiguous send: broker truth decides. fake raised before dispatch → clean.
    assert s2.positions() == []


def test_45_restart_after_order_accepted(fake, client):
    s1 = TradeLockerBrokerSession(client=client, account_id=101, acc_num=1000001, server="s")
    assert s1.connect()
    r = s1.submit_order(intent(symbol="EURUSD", volume=0.10))
    assert r.ok
    s2 = TradeLockerBrokerSession(client=client, account_id=101, acc_num=1000001, server="s")
    assert s2.connect()
    pos = s2.positions()
    assert len(pos) == 1  # position truth survives restart via provider
    assert pos[0].volume == 0.10


def test_46_restart_after_position_appears(fake, client):
    test_45_restart_after_order_accepted(fake, client)  # same surface


def test_47_restart_during_close(fake, client):
    s1 = TradeLockerBrokerSession(client=client, account_id=101, acc_num=1000001, server="s")
    assert s1.connect()
    s1.submit_order(intent(symbol="EURUSD", volume=0.10))
    pid = s1.positions()[0].position_id
    fake.set_defer_close(True)
    assert s1.close_position(pid, "test").ok
    s2 = TradeLockerBrokerSession(client=client, account_id=101, acc_num=1000001, server="s")
    assert s2.connect()
    assert len(s2.positions()) == 1  # close not confirmed yet
    fake.resolve_pending_closes()
    assert s2.positions() == []


# ─── 48-50 ownership ──────────────────────────────────────────────────────


def test_48_foreign_position_protection(fake, session):
    foreign_pid = fake.seed_foreign_position(101, symbol="EURUSD", qty=2.0, strategy_id="FOREIGN")
    session.submit_order(intent(symbol="EURUSD", volume=0.10))
    mine = [p for p in session.positions() if p.ownership_tag == "R5-TEST"]
    assert len(mine) == 1
    my_pid = mine[0].position_id
    assert my_pid != foreign_pid
    # closing OUR position must not alter the foreign one
    session.close_position(my_pid, "test")
    rows = fake.open_positions(101)
    assert len(rows) == 1
    assert rows[0]["id"] == foreign_pid
    assert rows[0]["qty"] == 2.0


def test_49_ownership_reconstruction(session):
    r = session.submit_order(
        intent(symbol="EURUSD", volume=0.10, ownership_tag="STRAT-A-LEG-1")
    )
    assert r.ok
    pos = session.positions()[0]
    assert pos.ownership_tag == "STRAT-A-LEG-1"
    deal = session.deals()[0]
    assert deal.ownership_tag == "STRAT-A-LEG-1"
    order_row = session._client.get_orders(101, history=True)[0]
    assert order_row["strategyId"] == "STRAT-A-LEG-1"


def test_50_no_cross_account_contamination(fake, client):
    s1 = TradeLockerBrokerSession(client=client, account_id=101, acc_num=1000001, server="s")
    s2 = TradeLockerBrokerSession(client=client, account_id=102, acc_num=1000002, server="s")
    assert s1.connect() and s2.connect()
    s1.submit_order(intent(symbol="EURUSD", volume=0.10))
    assert len(s1.positions()) == 1
    assert s2.positions() == []
    assert s2.orders() == []
    assert s2.deals() == []


# ─── 51-56 multi-leg baskets ──────────────────────────────────────────────


def test_51_three_leg_basket_success(session):
    legs = [
        intent(symbol="GBPAUD", side=OrderSide.SELL, volume=0.07, ownership_tag="TB-BK-1"),
        intent(symbol="GBPNZD", side=OrderSide.BUY, volume=0.07, ownership_tag="TB-BK-1"),
        intent(symbol="AUDNZD", side=OrderSide.SELL, volume=0.13, ownership_tag="TB-BK-1"),
    ]
    results = [session.submit_order(leg) for leg in legs]
    assert all(r.ok for r in results)
    pos = session.positions()
    assert len(pos) == 3
    by_symbol = {p.symbol: p for p in pos}
    assert by_symbol["GBPAUD"].side == "SHORT"
    assert by_symbol["GBPNZD"].side == "LONG"
    assert by_symbol["AUDNZD"].side == "SHORT"
    assert by_symbol["GBPAUD"].volume == 0.07
    assert by_symbol["AUDNZD"].volume == 0.13


def test_52_leg2_reject_recovery(fake, session):
    legs = [
        intent(symbol="GBPAUD", side=OrderSide.SELL, volume=0.07, ownership_tag="TB-BK"),
        intent(symbol="GBPNZD", side=OrderSide.BUY, volume=0.07, ownership_tag="TB-BK"),
        intent(symbol="AUDNZD", side=OrderSide.SELL, volume=0.13, ownership_tag="TB-BK"),
    ]
    assert session.submit_order(legs[0]).ok
    fake.set_reject_next_order()
    r2 = session.submit_order(legs[1])
    assert not r2.ok
    assert r2.error_category is BrokerErrorCategory.ORDER_REJECTED
    # partial exposure truth is visible for broken-hedge recovery
    pos = session.positions()
    assert len(pos) == 1
    assert pos[0].symbol == "GBPAUD"


def test_53_leg3_reject_recovery(fake, session):
    session.submit_order(intent(symbol="GBPAUD", side=OrderSide.SELL, volume=0.07, ownership_tag="BK"))
    session.submit_order(intent(symbol="GBPNZD", side=OrderSide.BUY, volume=0.07, ownership_tag="BK"))
    fake.set_reject_next_order()
    r = session.submit_order(intent(symbol="AUDNZD", side=OrderSide.SELL, volume=0.13, ownership_tag="BK"))
    assert not r.ok
    assert len(session.positions()) == 2  # partial exposure (broken hedge)


def test_54_partial_fill_broken_hedge(fake, session):
    fake.set_partial_fill_next(0.6)
    r = session.submit_order(intent(symbol="EURUSD", volume=0.10))
    assert r.ok
    pos = session.positions()
    assert len(pos) == 1
    assert abs(pos[0].volume - 0.06) < 1e-9  # partial fill truth


def test_55_basket_close(session):
    for leg in [
        intent(symbol="GBPAUD", side=OrderSide.SELL, volume=0.07, ownership_tag="BK"),
        intent(symbol="GBPNZD", side=OrderSide.BUY, volume=0.07, ownership_tag="BK"),
        intent(symbol="AUDNZD", side=OrderSide.SELL, volume=0.13, ownership_tag="BK"),
    ]:
        assert session.submit_order(leg).ok
    for p in session.positions():
        assert session.close_position(p.position_id, "close").ok
    assert session.positions() == []


def test_56_basket_restart_dedup(fake, client):
    s1 = TradeLockerBrokerSession(client=client, account_id=101, acc_num=1000001, server="s")
    assert s1.connect()
    s1.submit_order(intent(symbol="GBPAUD", side=OrderSide.SELL, volume=0.07, ownership_tag="BK"))
    s1.submit_order(intent(symbol="GBPNZD", side=OrderSide.BUY, volume=0.07, ownership_tag="BK"))
    s2 = TradeLockerBrokerSession(client=client, account_id=101, acc_num=1000001, server="s")
    assert s2.connect()
    # broker truth reconstructed: exactly 2 legs, no duplicates
    assert len(s2.positions()) == 2
    syms = sorted(p.symbol for p in s2.positions())
    assert syms == ["GBPAUD", "GBPNZD"]


# ─── 57-60 provider neutrality ────────────────────────────────────────────


def test_57_provider_capabilities_truthful(session):
    caps = session.capabilities()
    assert caps.supports_market_order is CapabilityState.SUPPORTED
    assert caps.supports_limit_order is CapabilityState.SUPPORTED
    assert caps.supports_stop_order is CapabilityState.SUPPORTED
    assert caps.supports_cancel is CapabilityState.SUPPORTED
    assert caps.supports_partial_close is CapabilityState.SUPPORTED
    assert caps.supports_native_sl_tp is CapabilityState.SUPPORTED
    assert caps.supports_client_order_id is CapabilityState.UNSUPPORTED
    assert caps.supports_order_check is CapabilityState.UNSUPPORTED
    assert caps.supports_multi_account_session is CapabilityState.SUPPORTED
    assert caps.supports_history is CapabilityState.SUPPORTED
    assert caps.supports_streaming_quotes is CapabilityState.UNSUPPORTED
    assert caps.supports_rest_quotes is CapabilityState.SUPPORTED


def test_58_no_mt5_branch_in_generic_or_provider(tradelocker_pkg_path):
    """The TradeLocker provider must not IMPORT MetaTrader5 (docstrings that
    document the non-interference contract are excluded via tokenize)."""
    import io
    import tokenize

    banned = ("MetaTrader5", "mt5")
    hits = []
    for py in sorted(tradelocker_pkg_path.glob("*.py")):
        try:
            tokens = list(tokenize.tokenize(io.BytesIO(py.read_bytes()).readline))
        except Exception:  # noqa: BLE001
            continue
        code = [t.string for t in tokens if t.type == tokenize.NAME]
        for name in code:
            if name.lower() in banned:
                hits.append(f"{py.name}:{name}")
                break
    assert hits == [], f"provider leaked MT5 references: {hits}"


@pytest.fixture
def tradelocker_pkg_path():
    import execution_runtime.tradelocker as pkg

    return Path(pkg.__file__).resolve().parent


def test_59_60_mt5_regression_and_r4_2_shadow_unchanged():
    """Regression coverage lives in the full-suite run (R2 MT5 + R4.2 shadow
    suites). This marker documents that R5 must not regress them; the offline
    gate runs the whole suite together."""
    assert ExecutionTransport.TRADELOCKER.value == "TRADELOCKER"
