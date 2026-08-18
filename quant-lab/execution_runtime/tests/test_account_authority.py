"""R1 checks 1-17 (account profile / broker truth) and 58-63 (authority)."""
from __future__ import annotations

from execution_runtime.account import AccountObservedState, AccountProfile
from execution_runtime.authority import (
    derive_execution_authority,
    identity_gate,
)
from execution_runtime.enums import (
    AccountRole,
    DesiredState,
    Environment,
    ExecutionTransport,
    HedgingNetting,
    SecretKind,
)
from execution_runtime.types import (
    BrokerAdapterId,
    BrokerCompanyId,
    SecretReference,
)


def _profile(**overrides) -> AccountProfile:
    d = dict(
        account_id="tb-master-01",
        broker_company=BrokerCompanyId("Ox Securities"),
        transport=ExecutionTransport.MT5,
        adapter_id=BrokerAdapterId("MT5BrokerSession"),
        expected_environment=Environment.DEMO,
        account_role=AccountRole.EXCLUSIVE_STRATEGY_MASTER,
        metadata_version=1,
        expected_server="OxSecurities-Demo",
        expected_currency="USD",
        operator_execution_requested=True,
        secret_reference=SecretReference(kind=SecretKind.ENV_VAR, reference="TB_DEMO_SECRET"),
        strategy_allowlist=("STRAT-A",),
    )
    d.update(overrides)
    return AccountProfile(**d)


def _observed(**overrides) -> AccountObservedState:
    d = dict(
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
    d.update(overrides)
    return AccountObservedState(**d)


def _auth(profile=None, observed=None, runtime=None, compat=None):
    from execution_runtime.compatibility import CompatibilityState, CompatibilityStatus
    from execution_runtime.profiles import RuntimeState

    return derive_execution_authority(
        profile or _profile(),
        observed or _observed(),
        runtime or RuntimeState(runtime_id="tb-master-01"),
        compat
        or CompatibilityState(
            account_id="tb-master-01",
            status=CompatibilityStatus.SUPPORTED,
            mode_compatible=True,
        ),
    )


# ── ACCOUNT PROFILE ───────────────────────────────────────────────────────


def test_01_valid_exclusive_profile():
    p = _profile()
    assert p.account_id == "tb-master-01"
    assert p.account_role is AccountRole.EXCLUSIVE_STRATEGY_MASTER


def test_02_valid_portfolio_profile():
    p = _profile(
        account_id="portfolio-01",
        account_role=AccountRole.PORTFOLIO_MASTER,
        portfolio_group_id="pg-01",
        strategy_allowlist=("STRAT-A", "STRAT-B"),
    )
    assert p.portfolio_group_id == "pg-01"


def test_03_duplicate_account_id_rejected():
    from execution_runtime.registry import AccountRegistry
    from execution_runtime.exceptions import DuplicateAccountError

    r = AccountRegistry()
    r.register(_profile())
    try:
        r.register(_profile())
        raise AssertionError("expected DuplicateAccountError")
    except DuplicateAccountError:
        pass


def test_04_operator_execution_requested_defaults_false():
    p = _profile(operator_execution_requested=False)
    assert p.operator_execution_requested is False
    # a profile constructed without the field also defaults false
    d = dict(
        account_id="x",
        broker_company=BrokerCompanyId("Ox Securities"),
        transport=ExecutionTransport.MT5,
        adapter_id=BrokerAdapterId("MT5BrokerSession"),
        expected_environment=Environment.DEMO,
        account_role=AccountRole.EXCLUSIVE_STRATEGY_MASTER,
        metadata_version=1,
    )
    assert AccountProfile(**d).operator_execution_requested is False


def test_05_config_cannot_declare_runtime_ready():
    # There is no status/READY field on AccountProfile.
    assert not hasattr(_profile(), "status")
    assert not hasattr(_profile(), "ready")


def test_06_missing_required_identity_expectation_handled_explicitly():
    p = _profile(expected_server="")
    d = _auth(profile=p)
    assert d.can_submit_new_risk is False
    assert any("missing identity expectation" in r for r in d.reasons)


def test_07_sim_replay_do_not_require_fake_credentials():
    for transport in (ExecutionTransport.SIM, ExecutionTransport.REPLAY):
        p = _profile(transport=transport, secret_reference=None, expected_server="")
        assert p.secret_reference is None
        o = _observed(
            transport_connected=True,
            authenticated=True,
            observed_broker_company="",
            observed_server="",
            observed_environment=(
                Environment.SIM if transport is ExecutionTransport.SIM else Environment.REPLAY
            ),
        )
        d = _auth(profile=p, observed=o)
        # no secret required for SIM/REPLAY transport
        assert not any("secret reference" in r for r in d.reasons)


def test_08_authenticated_transport_without_secret_fails_authority():
    p = _profile(secret_reference=None)
    d = _auth(profile=p)
    assert d.can_submit_new_risk is False
    assert any("missing secret reference" in r for r in d.reasons)


# ── BROKER / TRUTH ────────────────────────────────────────────────────────


def test_09_broker_company_separate_from_transport():
    p1 = _profile(broker_company=BrokerCompanyId("Ox Securities"), transport=ExecutionTransport.MT5)
    p2 = _profile(broker_company=BrokerCompanyId("OTHER_BROKER"), transport=ExecutionTransport.MT5)
    assert p1.transport is p2.transport
    assert p1.broker_company != p2.broker_company


def test_10_ox_securities_mt5_fixture():
    p = _profile()
    assert p.broker_company == "Ox Securities"
    assert p.transport is ExecutionTransport.MT5
    assert p.adapter_id == "MT5BrokerSession"


def test_11_second_broker_mt5_fixture_proves_transport_reuse():
    p = _profile(broker_company=BrokerCompanyId("OTHER_BROKER"), adapter_id=BrokerAdapterId("MT5BrokerSession"))
    assert p.transport is ExecutionTransport.MT5
    assert p.broker_company == "OTHER_BROKER"


def test_12_connected_is_not_authorized():
    o = _observed(transport_connected=True, authenticated=False)
    d = _auth(observed=o)
    assert d.can_submit_new_risk is False


def test_13_identity_mismatch_denies_new_risk():
    o = _observed(observed_broker_company="Wrong Broker")
    d = _auth(observed=o)
    assert d.can_submit_new_risk is False
    assert any("broker company" in r for r in d.reasons)


def test_14_wrong_server_denies():
    d = _auth(observed=_observed(observed_server="OtherServer-Live"))
    assert d.can_submit_new_risk is False
    assert any("server" in r for r in d.reasons)


def test_15_wrong_environment_denies():
    d = _auth(observed=_observed(observed_environment=Environment.REAL))
    assert d.can_submit_new_risk is False
    assert any("environment" in r for r in d.reasons)


def test_16_wrong_currency_denies_where_expected():
    d = _auth(observed=_observed(observed_currency="EUR"))
    assert d.can_submit_new_risk is False
    assert any("currency" in r for r in d.reasons)


def test_17_unknown_shared_account_mode_denies():
    from execution_runtime.compatibility import CompatibilityState, CompatibilityStatus

    d = _auth(
        profile=_profile(account_role=AccountRole.PORTFOLIO_MASTER, portfolio_group_id="pg-01"),
        compat=CompatibilityState(
            account_id="tb-master-01",
            status=CompatibilityStatus.FAIL_CLOSED,
            mode_compatible=False,
            blocking_reasons=("unknown account hedging/netting mode",),
        ),
    )
    assert d.can_submit_new_risk is False


# ── AUTHORITY (negative injections) ───────────────────────────────────────


def test_58_positive_pure_fixture_authorization():
    d = _auth()
    assert d.can_submit_new_risk is True
    assert d.can_observe is True
    assert d.can_manage_owned_existing_risk is True
    assert d.can_close_owned_risk is True


def test_59_intentional_stop_denies_new_risk():
    from execution_runtime.profiles import RuntimeState

    d = _auth(runtime=RuntimeState(runtime_id="tb-master-01", desired_state=DesiredState.STOPPED_BY_USER))
    assert d.can_submit_new_risk is False
    assert any("intentionally stopped" in r for r in d.reasons)


def test_60_reconciliation_false_denies():
    d = _auth(observed=_observed(reconciled=False))
    assert d.can_submit_new_risk is False
    assert any("reconciliation" in r for r in d.reasons)


def test_61_safety_block_denies():
    from execution_runtime.profiles import RuntimeState

    d = _auth(runtime=RuntimeState(runtime_id="tb-master-01", safety_blocked=True))
    assert d.can_submit_new_risk is False
    assert any("safety blocked" in r for r in d.reasons)


def test_62_foreign_management_authority_always_false():
    d = _auth()
    assert d.can_modify_foreign_risk is False


def test_63_follower_authority_false():
    d = _auth(profile=_profile(account_role=AccountRole.FOLLOWER))
    assert d.can_submit_new_risk is False


def test_identity_gate_helper():
    ok, blockers = identity_gate(_profile(), _observed())
    assert ok is True
    assert blockers == []
