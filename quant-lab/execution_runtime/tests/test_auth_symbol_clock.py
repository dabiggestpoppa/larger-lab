"""QL-EXEC-R1.1 — auth / symbol-activation / clock contract repair tests.

Pure fixtures only. No MT5 import, no broker connection, no broker orders.
"""  # noqa: E501
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from execution_runtime.authority import (
    authentication_satisfied,
    derive_execution_authority,
    requires_secret,
)
from execution_runtime.capabilities import BrokerCapabilities
from execution_runtime.compatibility import CompatibilityState, CompatibilityStatus
from execution_runtime.enums import (
    AccountRole,
    AuthenticationMode,
    CapabilityState,
    ClockStatus,
    Environment,
    ExecutionTransport,
    SecretKind,
)
from execution_runtime.interfaces import BrokerSession
from execution_runtime.profiles import RuntimeState
from execution_runtime.types import (
    Bar,
    BrokerClockState,
    SecretReference,
    Tick,
)

PKG_DIR = Path(__file__).resolve().parents[1]


def _auth(profile, observed, runtime=None, compat=None):
    return derive_execution_authority(
        profile,
        observed,
        runtime or RuntimeState(runtime_id=profile.account_id),
        compat
        or CompatibilityState(
            account_id=profile.account_id,
            status=CompatibilityStatus.SUPPORTED,
            mode_compatible=True,
        ),
    )


def _package_sources() -> str:
    return "\n".join(
        sorted(p.read_text(encoding="utf-8") for p in PKG_DIR.glob("*.py"))
    )


# ── AUTH (R1.1 checks 1-14) ───────────────────────────────────────────────


def test_auth_01_mt5_external_session_no_secret_required(mt5_profile_factory, observed_factory):
    p = mt5_profile_factory(
        authentication_mode=AuthenticationMode.EXTERNAL_SESSION,
        secret_reference=None,
    )
    assert requires_secret(p) is False
    ok, blockers = authentication_satisfied(p, observed_factory(authenticated=True))
    assert ok is True
    assert blockers == []


def test_auth_02_mt5_runtime_credentials_requires_secret(mt5_profile_factory):
    p = mt5_profile_factory(
        authentication_mode=AuthenticationMode.RUNTIME_CREDENTIALS,
        secret_reference=SecretReference(kind=SecretKind.ENV_VAR, reference="TB_DEMO_SECRET"),
    )
    assert requires_secret(p) is True
    # transport is MT5 but auth mode (not transport) drives the requirement
    assert p.transport is ExecutionTransport.MT5


def test_auth_03_sim_none_no_secret(mt5_profile_factory):
    p = mt5_profile_factory(
        transport=ExecutionTransport.SIM,
        authentication_mode=AuthenticationMode.NONE,
        secret_reference=None,
    )
    assert requires_secret(p) is False


def test_auth_04_replay_none_no_secret(mt5_profile_factory):
    p = mt5_profile_factory(
        transport=ExecutionTransport.REPLAY,
        authentication_mode=AuthenticationMode.NONE,
        secret_reference=None,
    )
    assert requires_secret(p) is False


def test_auth_05_external_session_not_authenticated_denies(mt5_profile_factory, observed_factory):
    p = mt5_profile_factory(
        authentication_mode=AuthenticationMode.EXTERNAL_SESSION,
        secret_reference=None,
    )
    o = observed_factory(authenticated=False)
    ok, blockers = authentication_satisfied(p, o)
    assert ok is False
    assert any("external session not authenticated" in b for b in blockers)
    d = _auth(p, o)
    assert d.can_submit_new_risk is False


def test_auth_06_runtime_credentials_missing_secret_denies(mt5_profile_factory, observed_factory):
    p = mt5_profile_factory(
        authentication_mode=AuthenticationMode.RUNTIME_CREDENTIALS,
        secret_reference=None,
    )
    ok, blockers = authentication_satisfied(p, observed_factory(authenticated=True))
    assert ok is False
    assert any("missing secret reference" in b for b in blockers)
    d = _auth(p, observed_factory(authenticated=True))
    assert d.can_submit_new_risk is False


def test_auth_07_runtime_credentials_secret_present_but_not_auth_denies(
    mt5_profile_factory, observed_factory
):
    p = mt5_profile_factory(
        authentication_mode=AuthenticationMode.RUNTIME_CREDENTIALS,
        secret_reference=SecretReference(kind=SecretKind.ENV_VAR, reference="TB_DEMO_SECRET"),
    )
    o = observed_factory(authenticated=False)
    ok, blockers = authentication_satisfied(p, o)
    assert ok is False
    assert any("not authenticated" in b for b in blockers)
    d = _auth(p, o)
    assert d.can_submit_new_risk is False


def test_auth_08_positive_external_session_passes(mt5_profile_factory, observed_factory):
    p = mt5_profile_factory(
        authentication_mode=AuthenticationMode.EXTERNAL_SESSION,
        secret_reference=None,
    )
    d = _auth(p, observed_factory())
    assert d.can_submit_new_risk is True
    assert d.can_observe is True


def test_auth_09_identity_mismatch_still_denies(mt5_profile_factory, observed_factory):
    p = mt5_profile_factory(authentication_mode=AuthenticationMode.EXTERNAL_SESSION, secret_reference=None)
    d = _auth(p, observed_factory(observed_broker_company="Wrong Broker"))
    assert d.can_submit_new_risk is False
    assert any("broker company" in r for r in d.reasons)


def test_auth_10_wrong_server_still_denies(mt5_profile_factory, observed_factory):
    p = mt5_profile_factory(authentication_mode=AuthenticationMode.EXTERNAL_SESSION, secret_reference=None)
    d = _auth(p, observed_factory(observed_server="OtherServer-Live"))
    assert d.can_submit_new_risk is False
    assert any("server" in r for r in d.reasons)


def test_auth_11_wrong_environment_still_denies(mt5_profile_factory, observed_factory):
    p = mt5_profile_factory(authentication_mode=AuthenticationMode.EXTERNAL_SESSION, secret_reference=None)
    d = _auth(p, observed_factory(observed_environment=Environment.REAL))
    assert d.can_submit_new_risk is False
    assert any("environment" in r for r in d.reasons)


def test_auth_12_wrong_currency_still_denies(mt5_profile_factory, observed_factory):
    p = mt5_profile_factory(authentication_mode=AuthenticationMode.EXTERNAL_SESSION, secret_reference=None)
    d = _auth(p, observed_factory(observed_currency="EUR"))
    assert d.can_submit_new_risk is False
    assert any("currency" in r for r in d.reasons)


def test_auth_13_follower_still_denies(mt5_profile_factory, observed_factory):
    p = mt5_profile_factory(
        account_role=AccountRole.FOLLOWER,
        authentication_mode=AuthenticationMode.EXTERNAL_SESSION,
        secret_reference=None,
    )
    d = _auth(p, observed_factory())
    assert d.can_submit_new_risk is False
    assert any("FOLLOWER" in r for r in d.reasons)


def test_auth_14_mirror_still_denies(mt5_profile_factory, observed_factory):
    p = mt5_profile_factory(
        account_role=AccountRole.MIRROR,
        authentication_mode=AuthenticationMode.EXTERNAL_SESSION,
        secret_reference=None,
    )
    d = _auth(p, observed_factory())
    assert d.can_submit_new_risk is False
    assert any("MIRROR" in r for r in d.reasons)


# ── SYMBOL ACTIVATION (R1.1 checks 15-17) ─────────────────────────────────


def test_symbol_15_broker_session_exposes_generic_symbol_activation():
    assert hasattr(BrokerSession, "ensure_symbol")
    assert "ensure_symbol" in BrokerSession.__abstractmethods__ or hasattr(
        BrokerSession, "ensure_symbol"
    )


def test_symbol_16_capability_represented():
    caps = BrokerCapabilities(supports_symbol_activation=CapabilityState.SUPPORTED)
    assert caps.supports_symbol_activation is CapabilityState.SUPPORTED
    unknown = BrokerCapabilities()
    assert unknown.supports_symbol_activation is CapabilityState.UNKNOWN


def test_symbol_17_no_mt5_symbol_select_name():
    src = _package_sources()
    assert "symbol_select" not in src
    assert "mt5_symbol_select" not in src
    assert "ensure_symbol" in src


# ── CLOCK (R1.1 checks 18-25) ─────────────────────────────────────────────


def test_clock_18_broker_clock_state_exists():
    c = BrokerClockState()
    assert c.calibrated is False
    assert c.status is ClockStatus.UNKNOWN


def test_clock_19_calibrated_state_representable():
    c = BrokerClockState(
        source_clock_name="MT5_SERVER",
        source_offset_seconds=10800.0,
        calibrated=True,
        status=ClockStatus.CALIBRATED,
        observed_at_utc="2026-08-18T12:00:00.000+00:00",
    )
    assert c.calibrated is True
    assert c.status is ClockStatus.CALIBRATED
    assert c.source_offset_seconds == 10800.0


def test_clock_20_uncalibrated_state_representable():
    c = BrokerClockState(
        source_clock_name="MT5_SERVER",
        calibrated=False,
        status=ClockStatus.UNCALIBRATED,
    )
    assert c.calibrated is False
    assert c.status is ClockStatus.UNCALIBRATED


def test_clock_21_positive_negative_offsets():
    assert BrokerClockState(source_offset_seconds=+10800.0).source_offset_seconds == 10800.0
    assert BrokerClockState(source_offset_seconds=-18000.0).source_offset_seconds == -18000.0


def test_clock_22_no_utc3_hardcoding():
    src = _package_sources()
    # No hardcoded numeric offset constants (e.g. 10800s == UTC+3) in code;
    # the offset is always an observed/calibrated data field.
    for token in ("10800", "7200", "14400", "18000"):
        assert token not in src, token
    assert "source_offset_seconds" in src


def test_clock_23_source_timestamp_preserved():
    raw = 1789632000.0
    bar = Bar(symbol="GBPAUD.PRO", time=raw, open=1.0, high=2.0, low=0.5, close=1.5)
    assert bar.time == raw


def test_clock_24_observation_time_distinguished():
    tick = Tick(
        symbol="GBPAUD.PRO",
        time=1789632000.0,  # source clock
        observed_at_utc=1789631995.0,  # local observation, different
        source_clock_name="MT5_SERVER",
        offset_seconds=10800.0,
    )
    assert tick.time != tick.observed_at_utc
    assert tick.source_clock_name == "MT5_SERVER"
    assert tick.offset_seconds == 10800.0


def test_clock_25_strategy_key_not_normalized():
    # The raw source timestamp must round-trip untouched; there is no generic
    # normalization function that rewrites Bar.time / Tick.time into UTC.
    raw = 1789632000.0
    bar = Bar(symbol="X", time=raw)
    assert bar.time == raw
    assert "normalize" not in " ".join(f for f in dir(Bar))


# ── PURITY (R1.1 checks 26-30) ────────────────────────────────────────────


def _refers_to(source: str, name: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == name:
            return True
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == name:
            return True
        if isinstance(node, ast.Import) and any(a.name == name for a in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module == name:
            return True
    return False


def test_purity_26_no_metatrader5_import():
    src = _package_sources()
    assert not _refers_to(src, "MetaTrader5")
    assert not _refers_to(src, "mt5")


def test_purity_27_no_broker_connection():
    src = _package_sources()
    # A connection attempt would require the mt5 module attribute surface.
    assert "mt5." not in src
    assert "terminal_info(" not in src
    assert "account_info(" not in src


def test_purity_28_no_broker_order():
    src = _package_sources()
    for token in ("order_send", "OrderSend", "positions_get", "history_deals_get", "copy_rates_from_pos"):
        assert token not in src, token


def test_purity_29_no_tb_science_constants():
    src = _package_sources()
    for token in ("GBPAUD", "GBPNZD", "AUDNZD", "STOP_Z", "TB-B", "TB-FWD-V1", "TB-FROZEN-CONTROL"):
        assert token not in src, token


def test_purity_30_no_capital_routing_ab_constants():
    src = _package_sources()
    for token in ("24.494897", "A1_70_30", "H1-1.00", "USDJPY"):
        assert token not in src, token


# ── NONREGRESSION (R1.1 checks 31-36) ─────────────────────────────────────


def test_nonreg_31_account_registry_unchanged():
    from execution_runtime.registry import AccountRegistry

    reg = AccountRegistry()
    from execution_runtime.account import AccountProfile
    from execution_runtime.types import BrokerAdapterId, BrokerCompanyId

    p = AccountProfile(
        account_id="acct-1",
        broker_company=BrokerCompanyId("Ox Securities"),
        transport=ExecutionTransport.SIM,
        authentication_mode=AuthenticationMode.NONE,
        adapter_id=BrokerAdapterId("SimBrokerSession"),
        expected_environment=Environment.SIM,
        account_role=AccountRole.EXCLUSIVE_STRATEGY_MASTER,
        metadata_version=1,
    )
    reg.register(p)
    assert "acct-1" in reg
    assert len(reg) == 1


def test_nonreg_32_routing_unchanged():
    from execution_runtime.account import AccountProfile
    from execution_runtime.binding import StrategyAccountBinding
    from execution_runtime.enums import ExecutionMode
    from execution_runtime.routing import AccountRouter
    from execution_runtime.types import BrokerAdapterId, BrokerCompanyId

    acct = AccountProfile(
        account_id="acct-1",
        broker_company=BrokerCompanyId("Ox Securities"),
        transport=ExecutionTransport.SIM,
        authentication_mode=AuthenticationMode.NONE,
        adapter_id=BrokerAdapterId("SimBrokerSession"),
        expected_environment=Environment.SIM,
        account_role=AccountRole.EXCLUSIVE_STRATEGY_MASTER,
        metadata_version=1,
        strategy_allowlist=("STRAT-A",),
    )
    binding = StrategyAccountBinding(
        binding_id="b-1",
        strategy_id="STRAT-A",
        runtime_id="rt-1",
        account_id="acct-1",
        account_role=AccountRole.EXCLUSIVE_STRATEGY_MASTER,
        execution_mode=ExecutionMode.SHADOW,
        operator_enabled=True,
    )
    res = AccountRouter().route("STRAT-A", [binding], {}, {"acct-1": acct})
    assert res.routed is True
    assert res.account_ids == ("acct-1",)


def test_nonreg_33_ownership_unchanged():
    from execution_runtime.ownership import LogicalOwnershipId

    a = LogicalOwnershipId("a", "r", "s", "g", "e").id()
    b = LogicalOwnershipId("a", "r", "s", "g", "e").id()
    assert a == b


def test_nonreg_34_reservation_unchanged():
    from execution_runtime.enums import ReservationState
    from execution_runtime.exceptions import InvalidStateTransition
    from execution_runtime.reservation import validate_reservation_transition

    assert validate_reservation_transition(
        ReservationState.PROPOSED, ReservationState.ADMITTED_RESERVED
    )
    with pytest.raises(InvalidStateTransition):
        validate_reservation_transition(
            ReservationState.CLOSED_RELEASED, ReservationState.FILLED_ACTIVE
        )


def test_nonreg_35_config_hashing_deterministic():
    from dataclasses import dataclass

    from execution_runtime.hashing import config_hash

    @dataclass(frozen=True)
    class Probe:
        a: str
        b: int

    assert config_hash(Probe("x", 1)) == config_hash(Probe("x", 1))


def test_nonreg_36_state_path_isolation_unchanged():
    from execution_runtime.exceptions import PathCollisionError
    from execution_runtime.profiles import assert_no_path_collision, build_runtime_paths

    assert build_runtime_paths("/tmp", "rt-1") == build_runtime_paths("/tmp", "rt-1")
    with pytest.raises(PathCollisionError):
        assert_no_path_collision(["rt-1", "RT-1"])
