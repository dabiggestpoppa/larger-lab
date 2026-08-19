"""QL-EXEC-R5 — BrokerSession conformance suite.

The SAME generic-contract behaviors run against two peer providers:

- SimBrokerSession (deterministic in-memory)
- TradeLockerBrokerSession over FakeTradeLocker

Any behavior that only works because the provider is MT5-shaped is a design
defect; these tests only use the BrokerSession protocol surface. Providers are
allowed documented semantic differences (e.g. TradeLocker market orders are
IOC and do not linger in non-final orders), so the suite asserts COMMON
semantics: position truth after market submit, close truth via positions,
ownership tagging, foreign-position protection, fail-closed preconditions.
"""
from __future__ import annotations

import sys
from pathlib import Path

_QL = Path(__file__).resolve().parents[2]  # quant-lab/
if str(_QL) not in sys.path:
    sys.path.insert(0, str(_QL))

import pytest  # noqa: E402

from execution_runtime.brokers.sim_broker import SimBrokerSession  # noqa: E402
from execution_runtime.enums import (  # noqa: E402
    BrokerErrorCategory,
    OrderSide,
    QuantityUnit,
)
from execution_runtime.interfaces import BrokerSession  # noqa: E402
from execution_runtime.tradelocker import (  # noqa: E402
    FakeTradeLocker,
    TradeLockerAuthProvider,
    TradeLockerBrokerSession,
    TradeLockerClient,
)
from execution_runtime.types import OrderIntent  # noqa: E402


def _tl_session() -> TradeLockerBrokerSession:
    fake = FakeTradeLocker()
    fake.set_credentials("u@e.com", "p", "demo-server")
    fake.add_instrument(101, name="EURUSD", symbol_id=1001)
    fake.add_instrument(101, name="GBPUSD", symbol_id=1002)
    auth = TradeLockerAuthProvider(
        base_url="https://demo.tradelocker.com/backend-api",
        transport=fake,
        secret_provider=lambda n: {"EMAIL": "u@e.com", "PASS": "p"}.get(n, ""),
        email_ref="EMAIL",
        password_ref="PASS",
        server="demo-server",
    )
    client = TradeLockerClient(auth=auth, transport=fake, acc_num=1000001)
    session = TradeLockerBrokerSession(
        client=client, account_id=101, acc_num=1000001, server="demo-server"
    )
    assert session.connect()
    session._fake = fake
    return session


def _sim_session() -> SimBrokerSession:
    sim = SimBrokerSession()
    sim.connect()
    sim.add_symbol("EURUSD", contract_size=100000.0, volume_min=0.01, volume_step=0.01)
    sim.add_symbol("GBPUSD", contract_size=100000.0, volume_min=0.01, volume_step=0.01)
    return sim


@pytest.fixture(
    params=[
        pytest.param(_tl_session, id="tradelocker"),
        pytest.param(_sim_session, id="sim"),
    ]
)
def provider(request):
    session = request.param()
    yield session
    session.disconnect()


def _intent(symbol="EURUSD", side=OrderSide.BUY, volume=0.10, tag="CONFORM"):
    return OrderIntent(
        intent_id=f"c-{symbol}-{side.value}-{volume}",
        account_id="a1",
        symbol=symbol,
        side=side,
        volume=volume,
        quantity_unit=QuantityUnit.LOT,
        ownership_tag=tag,
    )


def test_conform_market_submit_creates_position(provider):
    r = provider.submit_order(_intent())
    assert r.ok
    assert r.broker_order_id
    positions = provider.positions()
    assert len(positions) == 1
    assert positions[0].symbol == "EURUSD"
    assert positions[0].volume == pytest.approx(0.10, abs=1e-6)
    assert positions[0].side == "LONG"


def test_conform_short_direction(provider):
    assert provider.submit_order(_intent(side=OrderSide.SELL)).ok
    pos = provider.positions()[0]
    assert pos.side == "SHORT"


def test_conform_zero_quantity_rejected(provider):
    r = provider.submit_order(_intent(volume=0.0))
    assert not r.ok
    assert r.error_category is BrokerErrorCategory.INVALID_REQUEST


def test_conform_ownership_tag_preserved(provider):
    assert provider.submit_order(_intent(tag="STRAT-A")).ok
    assert provider.positions()[0].ownership_tag == "STRAT-A"


def test_conform_close_removes_position(provider):
    assert provider.submit_order(_intent()).ok
    pid = provider.positions()[0].position_id
    cr = provider.close_position(pid, "close")
    assert cr.ok
    # flatness confirmed from broker truth, not from the close result alone
    assert provider.positions() == []


def test_conform_reconcile_snapshot_matches(provider):
    assert provider.submit_order(_intent()).ok
    snap = provider.reconcile_snapshot()
    assert len(snap.positions) == 1
    assert len(snap.positions[0].position_id) > 0
    # deals: at least one normalized fill record exists
    assert len(snap.deals) >= 1


def test_conform_foreign_position_untouched(provider):
    # seed a foreign position via provider-specific plumbing
    if isinstance(provider, SimBrokerSession):
        provider.seed_foreign_position("f1", symbol="GBPUSD", volume=2.0, side="LONG")
        foreign_id = "f1"
    else:
        fake = provider._fake
        foreign_id = str(fake.seed_foreign_position(101, symbol="GBPUSD", qty=2.0, strategy_id="FOREIGN"))

    assert provider.submit_order(_intent(symbol="EURUSD")).ok
    my_positions = [p for p in provider.positions() if p.symbol == "EURUSD"]
    assert len(my_positions) == 1
    # close only our own position
    provider.close_position(my_positions[0].position_id, "close")
    remaining = {p.position_id: p for p in provider.positions()}
    assert foreign_id in remaining
    assert remaining[foreign_id].volume == pytest.approx(2.0, abs=1e-6)


def test_conform_not_connected_fails_closed(provider):
    provider.disconnect()
    r = provider.submit_order(_intent())
    assert not r.ok
    assert r.error_category is BrokerErrorCategory.NOT_CONNECTED
    assert provider.positions() == []


def test_conform_disconnect_then_reconnect(provider):
    provider.disconnect()
    assert provider.connect()
    assert provider.health().get("connected") is True
    assert provider.submit_order(_intent()).ok
    assert len(provider.positions()) == 1


def test_conform_identity_present(provider):
    ident = provider.identity()
    assert ident.broker_company
    assert ident.account_identifier
    assert ident.environment is not None
