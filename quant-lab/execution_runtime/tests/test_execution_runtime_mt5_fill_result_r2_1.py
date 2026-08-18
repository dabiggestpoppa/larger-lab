"""QL-EXEC-R2.1 — fill-policy truth + result-truth repair tests.

Proves the generic MT5 adapter defaults to provider-neutral STANDARD MT5
fill constants (derived from the injected module), that broker-observed
quirks (Ox permuted codes / 29-char comments) require an EXPLICIT execution
profile, that unknown fill capability fails closed, and that a successful
order result can never carry an error category.

FakeMT5 only. No real MetaTrader5, no terminal, no real orders.
"""  # noqa: E501
from __future__ import annotations

import time

from execution_runtime.brokers.fake_mt5 import FakeMT5, _Rec, ox_observed_execution_profile
from execution_runtime.brokers.mt5 import (
    MT5BrokerSession,
    MT5ExecutionProfile,
    standard_fill_policy_codes,
)
from execution_runtime.enums import BrokerErrorCategory, FillPolicy, OrderSide, OrderType
from execution_runtime.types import OrderIntent, OrderResult


def _intent(**overrides) -> OrderIntent:
    d = dict(
        intent_id="i-r21",
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


def _set_symbol(fake: FakeMT5, filling_mode: int) -> None:
    fake.set_symbol_info(
        "EURUSD",
        visible=True,
        trade_mode=4,
        digits=5,
        point=0.00001,
        trade_contract_size=100000.0,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        filling_mode=filling_mode,
    )


def _configured_fake() -> FakeMT5:
    fake = FakeMT5.ox_demo()
    _set_symbol(fake, filling_mode=7)
    fake.set_tick("EURUSD", bid=1.10000, ask=1.10005, last=1.10005, time=time.time() + 3 * 3600)
    return fake


class _CustomConstMT5(FakeMT5):
    """Proves fill codes are derived from the INJECTED module, not hardcoded."""

    ORDER_FILLING_FOK = 10
    ORDER_FILLING_IOC = 20
    ORDER_FILLING_RETURN = 30


# ── FILL POLICY TRUTH (1-14) ──────────────────────────────────────────────


def test_01_generic_session_uses_standard_module_constants(fake_mt5):
    assert standard_fill_policy_codes(fake_mt5) == {
        FillPolicy.FILL_OR_KILL: FakeMT5.ORDER_FILLING_FOK,
        FillPolicy.IMMEDIATE_OR_CANCEL: FakeMT5.ORDER_FILLING_IOC,
        FillPolicy.RETURN_OR_PARTIAL: FakeMT5.ORDER_FILLING_RETURN,
    }
    # derived from the injected module, never a hardcoded 0/1/2
    assert standard_fill_policy_codes(_CustomConstMT5()) == {
        FillPolicy.FILL_OR_KILL: 10,
        FillPolicy.IMMEDIATE_OR_CANCEL: 20,
        FillPolicy.RETURN_OR_PARTIAL: 30,
    }


def test_02_generic_fok_resolves_to_module_constant(fake_mt5):
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    s.order_check(_intent(fill_policy=FillPolicy.FILL_OR_KILL))
    assert fake_mt5.order_check_calls[-1]["type_filling"] == FakeMT5.ORDER_FILLING_FOK


def test_03_generic_ioc_resolves_to_module_constant(fake_mt5):
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    s.order_check(_intent(fill_policy=FillPolicy.IMMEDIATE_OR_CANCEL))
    assert fake_mt5.order_check_calls[-1]["type_filling"] == FakeMT5.ORDER_FILLING_IOC


def test_04_generic_return_resolves_to_module_constant(fake_mt5):
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    s.order_check(_intent(fill_policy=FillPolicy.RETURN_OR_PARTIAL))
    assert fake_mt5.order_check_calls[-1]["type_filling"] == FakeMT5.ORDER_FILLING_RETURN


def test_05_ox_override_maps_observed_codes_explicitly(fake_mt5):
    s = MT5BrokerSession(fake_mt5, profile=ox_observed_execution_profile())
    s.connect()
    s.order_check(_intent(fill_policy=FillPolicy.FILL_OR_KILL))
    assert fake_mt5.order_check_calls[-1]["type_filling"] == 1  # Ox-observed FOK
    s.order_check(_intent(fill_policy=FillPolicy.IMMEDIATE_OR_CANCEL))
    assert fake_mt5.order_check_calls[-1]["type_filling"] == 2  # Ox-observed IOC
    s.order_check(_intent(fill_policy=FillPolicy.RETURN_OR_PARTIAL))
    assert fake_mt5.order_check_calls[-1]["type_filling"] == 0  # Ox-observed RETURN


def test_06_ox_override_not_active_without_explicit_selection(fake_mt5):
    s = MT5BrokerSession(fake_mt5)  # no profile
    s.connect()
    s.order_check(_intent(fill_policy=FillPolicy.FILL_OR_KILL))
    assert fake_mt5.order_check_calls[-1]["type_filling"] == FakeMT5.ORDER_FILLING_FOK


def test_07_two_brokers_different_mappings_simultaneously():
    fa = _configured_fake()
    fb = _configured_fake()
    a = MT5BrokerSession(fa)  # standard MT5 mapping
    b = MT5BrokerSession(fb, profile=ox_observed_execution_profile())  # Ox mapping
    a.connect()
    b.connect()
    a.order_check(_intent(fill_policy=FillPolicy.FILL_OR_KILL))
    b.order_check(_intent(fill_policy=FillPolicy.FILL_OR_KILL))
    assert fa.order_check_calls[-1]["type_filling"] == FakeMT5.ORDER_FILLING_FOK  # 0
    assert fb.order_check_calls[-1]["type_filling"] == 1  # Ox FOK


def test_08_broker_default_successful_probe_selects_proven_policy(fake_mt5):
    # probe proves IOC (standard code 1) is accepted; FOK (0) is rejected
    fake_mt5.set_order_check(
        lambda req: _Rec(retcode=0, comment="ok")
        if req.get("type_filling") == FakeMT5.ORDER_FILLING_IOC
        else _Rec(retcode=10030, comment="invalid fill")
    )
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    r = s.submit_order(_intent(fill_policy=FillPolicy.BROKER_DEFAULT))
    assert r.ok is True
    assert fake_mt5.order_send_calls[-1]["type_filling"] == FakeMT5.ORDER_FILLING_IOC


def test_09_failed_probe_declared_policy_used_if_supported(fake_mt5):
    # probe fails for every mode; symbol DECLARES FOK (bit 1) -> use FOK code
    fake_mt5.set_order_check(lambda req: _Rec(retcode=10030, comment="invalid fill"))
    _set_symbol(fake_mt5, filling_mode=1)
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    r = s.submit_order(_intent(fill_policy=FillPolicy.BROKER_DEFAULT))
    assert r.ok is True
    assert fake_mt5.order_send_calls[-1]["type_filling"] == FakeMT5.ORDER_FILLING_FOK


def test_10_failed_probe_no_declared_fails_closed(fake_mt5):
    fake_mt5.set_order_check(lambda req: _Rec(retcode=10030, comment="invalid fill"))
    _set_symbol(fake_mt5, filling_mode=0)  # no declared policy
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    r = s.submit_order(_intent(fill_policy=FillPolicy.BROKER_DEFAULT))
    assert r.ok is False
    assert r.error_category is BrokerErrorCategory.UNSUPPORTED_CAPABILITY
    assert fake_mt5.order_send_calls == []  # nothing submitted


def test_11_unknown_does_not_silently_use_return(fake_mt5):
    fake_mt5.set_order_check(lambda req: _Rec(retcode=10030, comment="invalid fill"))
    _set_symbol(fake_mt5, filling_mode=0)
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    r = s.submit_order(_intent(fill_policy=FillPolicy.UNKNOWN))
    assert r.ok is False
    assert r.error_category is BrokerErrorCategory.UNSUPPORTED_CAPABILITY
    assert fake_mt5.order_send_calls == []
    # no RETURN code was ever resolved
    assert "fill policy unresolved" in r.reason


def test_12_unsupported_explicit_fill_policy_fails(fake_mt5):
    s = MT5BrokerSession(
        fake_mt5,
        profile=MT5ExecutionProfile(
            fill_policy_codes={
                FillPolicy.FILL_OR_KILL: FakeMT5.ORDER_FILLING_FOK,
                FillPolicy.IMMEDIATE_OR_CANCEL: FakeMT5.ORDER_FILLING_IOC,
            }  # RETURN omitted
        ),
    )
    s.connect()
    r = s.submit_order(_intent(fill_policy=FillPolicy.RETURN_OR_PARTIAL))
    assert r.ok is False
    assert r.error_category is BrokerErrorCategory.UNSUPPORTED_CAPABILITY
    assert "unsupported fill policy" in r.reason
    assert fake_mt5.order_send_calls == []


def test_13_probe_does_not_order_send(fake_mt5):
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    resolved = s.probe_fill_policies("EURUSD")
    assert resolved is FillPolicy.FILL_OR_KILL  # default order_check accepts FOK
    assert fake_mt5.order_send_calls == []  # probe only order_check, never send
    assert len(fake_mt5.order_check_calls) >= 1


def test_14_declared_actual_mismatch_representable(fake_mt5):
    # symbol DECLARES FOK + IOC (bits 1|2) but order_check accepts only RETURN (2)
    fake_mt5.set_order_check(
        lambda req: _Rec(retcode=0, comment="ok")
        if req.get("type_filling") == FakeMT5.ORDER_FILLING_RETURN
        else _Rec(retcode=10030, comment="invalid fill")
    )
    _set_symbol(fake_mt5, filling_mode=3)
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    declared = s.symbol_info("EURUSD").declared_fill_policies
    resolved = s.probe_fill_policies("EURUSD")
    assert FillPolicy.FILL_OR_KILL in declared
    assert resolved is FillPolicy.RETURN_OR_PARTIAL
    assert resolved not in declared  # actual != declared, both representable


# ── RESULT TRUTH (15-24) ──────────────────────────────────────────────────


def test_15_success_retcode_0_has_no_error(fake_mt5):
    fake_mt5.set_order_send(lambda req: _Rec(retcode=0, comment="ok", order=700))
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    r = s.submit_order(_intent())
    assert r.ok is True
    assert r.retcode == 0
    assert r.error_category is BrokerErrorCategory.NONE
    assert r.reason == ""


def test_16_success_retcode_10009_has_no_error(fake_mt5):
    fake_mt5.set_order_send(lambda req: _Rec(retcode=10009, comment="done", order=701))
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    r = s.submit_order(_intent())
    assert r.ok is True
    assert r.retcode == 10009
    assert r.error_category is BrokerErrorCategory.NONE
    assert r.reason == ""


def test_17_rejected_order_is_order_rejected(fake_mt5):
    fake_mt5.set_order_send(lambda req: _Rec(retcode=10030, comment="invalid fill"))
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    r = s.submit_order(_intent())
    assert r.ok is False
    assert r.retcode == 10030
    assert r.error_category is BrokerErrorCategory.ORDER_REJECTED


def test_18_none_order_result_meaningful_error(fake_mt5):
    fake_mt5.set_order_send(lambda req: None)
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    r = s.submit_order(_intent())
    assert r.ok is False
    assert r.retcode is None
    assert r.error_category is BrokerErrorCategory.TRANSPORT_ERROR
    assert r.error_category is not BrokerErrorCategory.UNKNOWN_BROKER_ERROR


def test_19_invalid_request_category(fake_mt5):
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    r = s.submit_order(_intent(volume=0.0))
    assert r.ok is False
    assert r.error_category is BrokerErrorCategory.INVALID_REQUEST
    assert fake_mt5.order_send_calls == []


def test_20_not_connected_submit_category(fake_mt5):
    s = MT5BrokerSession(fake_mt5)  # never connected
    r = s.submit_order(_intent())
    assert r.ok is False
    assert r.error_category is BrokerErrorCategory.NOT_CONNECTED
    assert fake_mt5.order_send_calls == []


def test_21_no_state_has_ok_true_and_unknown_error(fake_mt5):
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    fake_mt5.set_order_send(lambda req: _Rec(retcode=0, comment="ok", order=1))
    r0 = s.submit_order(_intent())
    fake_mt5.set_order_send(lambda req: _Rec(retcode=10009, comment="done", order=2))
    r9 = s.submit_order(_intent())
    fake_mt5.set_order_send(lambda req: _Rec(retcode=10030, comment="rejected"))
    rej = s.submit_order(_intent())
    fake_mt5.set_order_send(lambda req: None)
    none = s.submit_order(_intent())
    for r in (r0, r9, rej, none):
        assert not (r.ok and r.error_category is BrokerErrorCategory.UNKNOWN_BROKER_ERROR)
    assert r0.error_category is BrokerErrorCategory.NONE
    assert r9.error_category is BrokerErrorCategory.NONE
    # default (unset) OrderResult is truthful, never UNKNOWN on success
    assert OrderResult().error_category is BrokerErrorCategory.NONE


def test_22_check_result_success_has_no_failure_reason(fake_mt5):
    fake_mt5.set_order_check(lambda req: _Rec(retcode=0, comment="ok"))
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    r = s.order_check(_intent())
    assert r.ok is True
    assert r.reason == ""
    assert r.error_category is BrokerErrorCategory.NONE


def test_23_cancel_success_truthful(fake_mt5):
    fake_mt5.set_order_send(lambda req: _Rec(retcode=10009, comment="done"))
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    r = s.cancel_order("55")
    assert r.ok is True
    assert r.reason == ""
    assert r.error_category is BrokerErrorCategory.NONE


def test_24_close_success_truthful(fake_mt5):
    fake_mt5.set_positions([
        {"ticket": 11, "symbol": "EURUSD", "volume": 0.1, "type": 0,
         "price_open": 1.1, "magic": 7}
    ])
    fake_mt5.set_order_send(lambda req: _Rec(retcode=10009, comment="done", order=99))
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    r = s.close_position("11")
    assert r.ok is True
    assert r.reason == ""
    assert r.error_category is BrokerErrorCategory.NONE


# ── EXTRA: fail-closed when module constants are missing ─────────────────


def test_25_missing_module_constants_fail_closed(fake_mt5):
    class _MissingConstants(FakeMT5):
        ORDER_FILLING_FOK = None
        ORDER_FILLING_IOC = None
        ORDER_FILLING_RETURN = None

    fake = _MissingConstants()
    fake.set_terminal_info(company="X", trade_allowed=True, tradeapi_disabled=False)
    fake.set_account_info(login=1, server="X-Demo", trade_mode=0, currency="USD")
    _set_symbol(fake, filling_mode=7)
    fake.set_tick("EURUSD", bid=1.1, ask=1.10005, time=time.time())
    s = MT5BrokerSession(fake)
    s.connect()
    assert s._fill_policy_codes == {}  # unresolved, not guessed
    r = s.submit_order(_intent(fill_policy=FillPolicy.FILL_OR_KILL))
    assert r.ok is False
    assert r.error_category is BrokerErrorCategory.UNSUPPORTED_CAPABILITY
    assert fake.order_send_calls == []
