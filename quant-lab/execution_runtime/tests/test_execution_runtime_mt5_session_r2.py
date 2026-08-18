"""QL-EXEC-R2 — MT5BrokerSession auth/connection/identity/symbol tests.

Pure: FakeMT5 only. No real MetaTrader5, no terminal, no orders.
"""  # noqa: E501
from __future__ import annotations

from execution_runtime.brokers.fake_mt5 import ox_observed_execution_profile
from execution_runtime.brokers.mt5 import MT5BrokerSession, normalize_trade_mode
from execution_runtime.enums import Environment, FillPolicy


# ── AUTH / CONNECTION (1-5) ───────────────────────────────────────────────


def test_01_external_session_connect_success(fake_mt5):
    s = MT5BrokerSession(fake_mt5)
    assert s.connect() is True
    assert s.health()["connected"] is True


def test_02_connect_failure(fake_mt5):
    fake_mt5.initialize_result = False
    s = MT5BrokerSession(fake_mt5)
    assert s.connect() is False
    assert s.health()["connected"] is False


def test_03_disconnect_idempotent(fake_mt5):
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    s.disconnect()
    s.disconnect()
    assert s.health()["connected"] is False


def test_04_terminal_unavailable(fake_mt5):
    fake_mt5.clear_terminal_info()
    s = MT5BrokerSession(fake_mt5)
    assert s.connect() is False


def test_05_account_unavailable(fake_mt5):
    fake_mt5.clear_account_info()
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    assert s.account_state().currency == ""
    assert s.identity().account_identifier == ""


# ── IDENTITY (6-15) ───────────────────────────────────────────────────────


def test_06_identity_correct_broker_company(session):
    assert session.identity().broker_company == "Ox Securities"


def test_07_identity_correct_server(session):
    assert session.identity().server == "OxSecurities-Demo"


def test_08_identity_correct_account_id(session):
    assert session.identity().account_identifier == "12345678"


def test_09_identity_correct_currency(session):
    assert session.identity().currency == "USD"


def test_10_trade_mode_normalization():
    assert normalize_trade_mode(0) is Environment.DEMO
    assert normalize_trade_mode(1) is Environment.CONTEST
    assert normalize_trade_mode(2) is Environment.REAL
    assert normalize_trade_mode(3) is Environment.UNKNOWN
    assert normalize_trade_mode(None) is Environment.UNKNOWN


def test_11_wrong_company_surfaced(fake_mt5):
    fake_mt5.set_terminal_info(company="Wrong Broker", trade_allowed=True, tradeapi_disabled=False)
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    assert s.identity().broker_company == "Wrong Broker"


def test_12_wrong_server_surfaced(fake_mt5):
    fake_mt5.set_account_info(server="OtherServer-Live", trade_mode=0, currency="USD", login=9)
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    assert s.identity().server == "OtherServer-Live"


def test_13_real_surfaced_distinctly(fake_mt5):
    fake_mt5.set_account_info(trade_mode=2, currency="USD", login=9, server="OxSecurities-Live")
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    assert s.identity().environment is Environment.REAL
    assert s.identity().account_mode == "REAL"


def test_14_terminal_trading_disabled_surfaced(fake_mt5):
    fake_mt5.set_terminal_info(company="Ox Securities", trade_allowed=False, tradeapi_disabled=False)
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    assert s.identity().terminal_trade_allowed is False


def test_15_trade_api_disabled_surfaced(fake_mt5):
    fake_mt5.set_terminal_info(company="Ox Securities", trade_allowed=True, tradeapi_disabled=True)
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    assert s.identity().tradeapi_disabled is True


# ── SYMBOL (16-25) ────────────────────────────────────────────────────────


def test_16_symbol_info(session):
    info = session.symbol_info("EURUSD")
    assert info is not None
    assert info.symbol == "EURUSD"


def test_17_symbol_activation_success(fake_mt5):
    fake_mt5.symbol_select_results["EURUSD"] = True
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    assert s.ensure_symbol("EURUSD") is True
    assert fake_mt5.symbol_select_calls[-1] == ("EURUSD", True)


def test_18_symbol_activation_failure(session):
    assert session.ensure_symbol("EURUSD") is False


def test_19_missing_symbol(session):
    assert session.symbol_info("NOPE") is None


def test_20_volume_min(session):
    assert session.symbol_info("EURUSD").volume_min == 0.01


def test_21_volume_step(session):
    assert session.symbol_info("EURUSD").volume_step == 0.01


def test_22_volume_max(session):
    assert session.symbol_info("EURUSD").volume_max == 100.0


def test_23_contract_size(session):
    assert session.symbol_info("EURUSD").contract_size == 100000.0


def test_24_point(session):
    assert session.symbol_info("EURUSD").point == 0.00001


def test_25_digits(session):
    assert session.symbol_info("EURUSD").digits == 5


def test_symbol_declared_fill_policies(fake_mt5):
    # generic default: standard MT5 bits (FOK + IOC; standard bit 4 = BOC is
    # deliberately unmapped in the provider-neutral default).
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    info = s.symbol_info("EURUSD")
    assert list(info.declared_fill_policies) == [
        FillPolicy.FILL_OR_KILL,
        FillPolicy.IMMEDIATE_OR_CANCEL,
    ]

    # Ox-observed bit interpretation (bit 4 -> RETURN) requires explicit profile
    s_ox = MT5BrokerSession(fake_mt5, profile=ox_observed_execution_profile())
    s_ox.connect()
    info_ox = s_ox.symbol_info("EURUSD")
    assert len(info_ox.declared_fill_policies) == 3
