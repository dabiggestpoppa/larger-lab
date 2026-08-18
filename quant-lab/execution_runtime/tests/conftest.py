"""QL-EXEC-R1 test fixtures (pure domain; no broker calls)."""
from __future__ import annotations

import sys
from pathlib import Path

_QL = Path(__file__).resolve().parents[2]  # quant-lab/
if str(_QL) not in sys.path:
    sys.path.insert(0, str(_QL))

import pytest  # noqa: E402

from execution_runtime.account import AccountObservedState, AccountProfile  # noqa: E402
from execution_runtime.compatibility import (  # noqa: E402
    CompatibilityState,
    CompatibilityStatus,
)
from execution_runtime.enums import (  # noqa: E402
    AccountRole,
    AuthenticationMode,
    DesiredState,
    Environment,
    ExecutionTransport,
    HedgingNetting,
    SecretKind,
)
from execution_runtime.profiles import RuntimeState  # noqa: E402
from execution_runtime.types import (  # noqa: E402
    BrokerAdapterId,
    BrokerCompanyId,
    SecretReference,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def mt5_profile_factory():
    def _make(**overrides):
        defaults = dict(
            account_id="tb-master-01",
            broker_company=BrokerCompanyId("Ox Securities"),
            transport=ExecutionTransport.MT5,
            authentication_mode=AuthenticationMode.EXTERNAL_SESSION,
            adapter_id=BrokerAdapterId("MT5BrokerSession"),
            expected_environment=Environment.DEMO,
            account_role=AccountRole.EXCLUSIVE_STRATEGY_MASTER,
            metadata_version=1,
            expected_server="OxSecurities-Demo",
            expected_currency="USD",
            operator_execution_requested=True,
            secret_reference=None,
            strategy_allowlist=("STRAT-A",),
        )
        defaults.update(overrides)
        return AccountProfile(**defaults)

    return _make


@pytest.fixture
def observed_factory():
    def _make(**overrides):
        defaults = dict(
            account_id="tb-master-01",
            transport_connected=True,
            authenticated=True,
            observed_broker_company="Ox Securities",
            observed_server="OxSecurities-Demo",
            observed_environment=Environment.DEMO,
            observed_currency="USD",
            hedging_or_netting=HedgingNetting.HEDGING,
            reconciled=True,
        )
        defaults.update(overrides)
        return AccountObservedState(**defaults)

    return _make


@pytest.fixture
def runtime_factory():
    def _make(**overrides):
        defaults = dict(
            runtime_id="tb-master-01",
            desired_state=DesiredState.RUNNING,
            safety_blocked=False,
        )
        defaults.update(overrides)
        return RuntimeState(**defaults)

    return _make


@pytest.fixture
def compat_factory():
    def _make(**overrides):
        defaults = dict(
            account_id="tb-master-01",
            status=CompatibilityStatus.SUPPORTED,
            mode_compatible=True,
        )
        defaults.update(overrides)
        return CompatibilityState(**defaults)

    return _make


# ── R2 MT5 broker-session fixtures (pure; no real MetaTrader5) ───────────

import time as _time  # noqa: E402


@pytest.fixture
def fake_mt5():
    from execution_runtime.brokers.fake_mt5 import FakeMT5

    fake = FakeMT5.ox_demo()
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
        filling_mode=7,
    )
    fake.set_tick(
        "EURUSD",
        bid=1.10000,
        ask=1.10005,
        last=1.10005,
        time=_time.time() + 3 * 3600,  # UTC+3-style source clock
    )
    return fake


@pytest.fixture
def session(fake_mt5):
    from execution_runtime.brokers.mt5 import MT5BrokerSession

    s = MT5BrokerSession(fake_mt5)
    s.connect()
    return s
