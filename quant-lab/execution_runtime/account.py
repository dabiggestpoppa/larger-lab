"""QL-EXEC-R1 — static account profile vs observed account truth.

STATIC (configured expectation) is deliberately separate from DYNAMIC
(observed runtime truth). A config row can never declare itself READY.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .enums import (
    AccountRole,
    AuthenticationMode,
    Environment,
    ExecutionTransport,
    HedgingNetting,
    MarketStatus,
    RuntimeHealth,
)
from .types import BrokerAdapterId, BrokerCompanyId, SecretReference


@dataclass(frozen=True)
class AccountProfile:
    """Static / configured expectation for one logical execution account.

    Contains NO runtime truth (no READY/CONNECTED/RECONCILING) and NO
    credentials. `secret_reference` is a reference only.
    """

    account_id: str
    broker_company: BrokerCompanyId
    transport: ExecutionTransport
    authentication_mode: AuthenticationMode
    adapter_id: BrokerAdapterId
    expected_environment: Environment
    account_role: AccountRole
    metadata_version: int

    expected_server: str = ""
    expected_currency: str = ""
    expected_account_mode: str = ""
    expected_account_identifier: str = ""
    expected_hedging_netting: HedgingNetting = HedgingNetting.UNKNOWN

    portfolio_group_id: str | None = None
    strategy_allowlist: tuple[str, ...] = ()
    operator_execution_requested: bool = False
    copier_role: str | None = None
    terminal_or_session_binding: str | None = None
    secret_reference: SecretReference | None = None

    def __post_init__(self) -> None:
        if not self.account_id or not self.account_id.strip():
            raise ValueError("account_id must be non-empty")
        if not self.broker_company or not self.broker_company.strip():
            raise ValueError("broker_company must be non-empty")
        if not self.adapter_id or not self.adapter_id.strip():
            raise ValueError("adapter_id must be non-empty")
        if self.metadata_version < 1:
            raise ValueError("metadata_version must be >= 1")


@dataclass(frozen=True)
class AccountObservedState:
    """Dynamic runtime/broker truth for an account.

    Never committed as operator configuration. It is a runtime record.
    """

    account_id: str
    observed_at: str = ""

    transport_connected: bool = False
    authenticated: bool = False

    observed_broker_company: str = ""
    observed_server: str = ""
    observed_account_identifier: str = ""
    observed_environment: Environment | None = None
    observed_currency: str = ""
    observed_account_mode: str = ""
    hedging_or_netting: HedgingNetting = HedgingNetting.UNKNOWN
    observed_terminal_binding: str = ""

    equity: float | None = None
    balance: float | None = None
    margin: float | None = None
    free_margin: float | None = None
    buying_power: float | None = None

    market_status: MarketStatus = MarketStatus.UNKNOWN
    reconciled: bool = False
    runtime_health: RuntimeHealth = RuntimeHealth.UNKNOWN
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.account_id or not self.account_id.strip():
            raise ValueError("account_id must be non-empty")
