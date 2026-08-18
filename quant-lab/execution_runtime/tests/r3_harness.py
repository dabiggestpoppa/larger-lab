"""QL-EXEC-R3 — shared test harness builders (not collected as tests).

Builds a deterministic GenericRuntime over a SimBrokerSession + temp SQLite
store. All tests use this so the runtime lifecycle is exercised identically.
"""
from __future__ import annotations

from pathlib import Path

from execution_runtime.account import AccountProfile
from execution_runtime.brokers.sim_broker import SimBrokerSession
from execution_runtime.enums import (
    AccountRole,
    AuthenticationMode,
    Environment,
    ExecutionTransport,
)
from execution_runtime.hashing import config_hash
from execution_runtime.profiles import MachineProfile, RuntimeProfile
from execution_runtime.runtime import GenericRuntime, RuntimeStore
from execution_runtime.runtime.adapters import (
    PassThroughCapitalPolicyAdapter,
    ScriptedStrategyAdapter,
    TestCapitalTranslationAdapter,
)
from execution_runtime.types import BrokerAdapterId, BrokerCompanyId

RUNTIME_ID = "rt-1"
ACCOUNT_ID = "acct-1"
GENERATION = "gen-1"


def make_profile(runtime_id: str = RUNTIME_ID, **overrides) -> RuntimeProfile:
    d = dict(
        runtime_id=runtime_id,
        machine_profile=MachineProfile.LOCAL_WINDOWS,
        account_id=ACCOUNT_ID,
        metadata_version=1,
        deployment_generation=GENERATION,
        strategy_adapter_ids=("scripted-strategy",),
    )
    d.update(overrides)
    return RuntimeProfile(**d)


def make_account(**overrides) -> AccountProfile:
    d = dict(
        account_id=ACCOUNT_ID,
        broker_company=BrokerCompanyId("SIM-BROKER"),
        transport=ExecutionTransport.SIM,
        authentication_mode=AuthenticationMode.NONE,
        adapter_id=BrokerAdapterId("SimBrokerSession"),
        expected_environment=Environment.SIM,
        account_role=AccountRole.EXCLUSIVE_STRATEGY_MASTER,
        metadata_version=1,
        expected_server="SIM-Demo",
        operator_execution_requested=True,
    )
    d.update(overrides)
    return AccountProfile(**d)


def make_store(tmp_path: Path, profile: RuntimeProfile, account: AccountProfile) -> RuntimeStore:
    store = RuntimeStore(str(tmp_path / "runtime.sqlite"))
    store.open()
    store.initialize(
        runtime_id=profile.runtime_id,
        deployment_generation=profile.deployment_generation,
        profile_hash=config_hash(profile),
        account_hash=config_hash(account),
    )
    return store


def make_runtime(
    profile: RuntimeProfile,
    account: AccountProfile,
    store: RuntimeStore,
    *,
    broker: SimBrokerSession | None = None,
    events=(),
    reject_policy: bool = False,
    **kwargs,
):
    """Return (runtime, broker). Broker defaults to a fresh SimBrokerSession."""
    broker = broker or SimBrokerSession()
    strategy = ScriptedStrategyAdapter(events=tuple(events))
    policy = PassThroughCapitalPolicyAdapter(reject=reject_policy)
    translation = TestCapitalTranslationAdapter(default_quantity=0.1)
    runtime = GenericRuntime(
        profile=profile,
        account_profile=account,
        strategy=strategy,
        capital_policy=policy,
        capital_translation=translation,
        broker=broker,
        store=store,
        **kwargs,
    )
    return runtime, broker
