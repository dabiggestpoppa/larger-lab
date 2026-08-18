"""QL-EXEC-R1 — shared value objects.

These are pure, broker-neutral, strategy-neutral contracts. No MetaTrader5,
no Capital Routing math, no TB science.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import NewType

from .enums import (
    AccountRole,
    CapitalDecisionKind,
    ClockStatus,
    Environment,
    HedgingNetting,
    SecretKind,
)

# Explicit concepts (NOT a tiny provider enum): a broker company is an
# unbounded identity string; the transport is the execution platform.
BrokerCompanyId = NewType("BrokerCompanyId", str)
BrokerAdapterId = NewType("BrokerAdapterId", str)


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def stable_hash(prefix: str, *parts: str, n: int = 24) -> str:
    """Deterministic, collision-resistant, versioned hash over canonical parts."""
    canonical = "|".join(str(p) for p in parts)
    return f"{prefix}_{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:n]}"


# ─── SECRETS ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SecretReference:
    """A reference to a credential. NEVER a credential value."""

    kind: SecretKind = SecretKind.NONE
    reference: str = ""  # env-var name / keyring entry / store id

    def is_present(self) -> bool:
        return self.kind is not SecretKind.NONE and bool(self.reference)


# ─── BROKER VALUE OBJECTS (BrokerSession return types) ────────────────────


@dataclass(frozen=True)
class BrokerIdentity:
    """Broker-reported identity for fail-closed identity matching."""

    broker_company: str = ""
    server: str = ""
    account_identifier: str = ""
    environment: Environment | None = None
    currency: str = ""
    account_mode: str = ""
    hedging_netting: HedgingNetting = HedgingNetting.UNKNOWN


@dataclass(frozen=True)
class AccountState:
    """Normalized broker account state (broker truth)."""

    currency: str = ""
    equity: float | None = None
    balance: float | None = None
    margin: float | None = None
    free_margin: float | None = None
    buying_power: float | None = None
    account_mode: str = ""


@dataclass(frozen=True)
class SymbolInfo:
    symbol: str
    digits: int = 0
    point: float = 0.0
    contract_size: float = 0.0
    volume_min: float = 0.0
    volume_max: float = 0.0
    volume_step: float = 0.0


@dataclass(frozen=True)
class BrokerClockState:
    """Broker/server clock truth (source time vs local observation time).

    ``source_offset_seconds`` is source-clock minus UTC and is ALWAYS
    observed/calibrated — never a hardcoded value such as UTC+3.
    """

    source_clock_name: str = ""
    source_offset_seconds: float = 0.0
    calibrated: bool = False
    calibration_age_seconds: float | None = None
    status: ClockStatus = ClockStatus.UNKNOWN
    observed_at_utc: str = ""
    failure_reason: str = ""


@dataclass(frozen=True)
class Tick:
    """Quote tick. ``time`` is the RAW source timestamp (provider clock).

    The generic runtime never normalizes ``time`` into UTC; strategy parity
    keys must be preserved as-is.
    """

    symbol: str
    bid: float = 0.0
    ask: float = 0.0
    time: float = 0.0  # raw source timestamp, never silently normalized
    observed_at_utc: float = 0.0  # local observation/received time
    source_clock_name: str = ""  # which source clock ``time`` is in
    offset_seconds: float = 0.0  # calibrated source-minus-UTC offset


@dataclass(frozen=True)
class Bar:
    """OHLC bar. ``time`` is the RAW source timestamp.

    For MT5 this is the BAR OPEN time and is canonical strategy parity.
    Closure/freshness uses a separately calibrated server-time reference.
    """

    symbol: str
    time: float = 0.0  # raw source timestamp (MT5 = bar open time)
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    observed_at_utc: float = 0.0  # local observation/received time
    source_clock_name: str = ""
    offset_seconds: float = 0.0  # calibrated source-minus-UTC offset


@dataclass(frozen=True)
class Position:
    position_id: str
    symbol: str
    volume: float = 0.0
    side: str = ""  # LONG / SHORT
    price_open: float = 0.0
    ownership_tag: str = ""


@dataclass(frozen=True)
class Order:
    order_id: str
    symbol: str
    volume: float = 0.0
    order_type: str = ""
    ownership_tag: str = ""


@dataclass(frozen=True)
class Deal:
    deal_id: str
    symbol: str
    volume: float = 0.0
    price: float = 0.0
    entry: bool = True
    ownership_tag: str = ""


@dataclass(frozen=True)
class OrderIntent:
    """Broker-neutral order intent. Filled by execution translation later."""

    intent_id: str
    account_id: str
    symbol: str
    side: str = ""
    volume: float = 0.0
    order_type: str = "MARKET"
    ownership_tag: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class CheckResult:
    ok: bool = False
    reason: str = ""
    detail: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SubmitResult:
    ok: bool = False
    broker_order_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class CancelResult:
    ok: bool = False
    reason: str = ""


@dataclass(frozen=True)
class CloseResult:
    ok: bool = False
    reason: str = ""


@dataclass(frozen=True)
class BrokerSnapshot:
    """Read-only broker truth snapshot used by reconciliation."""

    account_state: AccountState = field(default_factory=AccountState)
    positions: tuple = ()
    orders: tuple = ()
    deals: tuple = ()


# ─── CAPITAL FLOW VALUE OBJECTS (broker-neutral) ──────────────────────────


@dataclass(frozen=True)
class StrategyEvent:
    """A strategy signal/decision, opaque to the generic runtime."""

    event_id: str
    strategy_id: str
    event_kind: str = ""
    signal_time: str = ""
    deployment_generation: str = ""
    payload: dict = field(default_factory=dict)


@dataclass(frozen=True)
class CapitalRequest:
    """Admission request handed to a CapitalPolicyAdapter."""

    request_id: str
    event_id: str
    strategy_id: str
    family: str = ""
    requested_f: float = 0.0
    portfolio_group_id: str = ""
    account_id: str = ""
    policy_id: str = ""


@dataclass(frozen=True)
class CapitalDecision:
    """Admission decision. Carries an idempotent reservation id when admitted."""

    decision_id: str
    kind: CapitalDecisionKind = CapitalDecisionKind.REJECTED
    family: str = ""
    admitted_f: float = 0.0
    reservation_id: str = ""
    policy_id: str = ""
    reason: str = ""
    decided_at: str = ""

    @property
    def admitted(self) -> bool:
        return self.kind is CapitalDecisionKind.ADMITTED


@dataclass(frozen=True)
class BoundAccountSnapshot:
    """Account truth available only AFTER account routing/binding."""

    account_id: str
    account_role: AccountRole = AccountRole.FOLLOWER
    portfolio_group_id: str = ""
    equity: float | None = None
    account_currency: str = ""
    observed_at: str = ""


@dataclass(frozen=True)
class StrategyExposureContext:
    """Strategy-native description of how a decision maps to instruments."""

    strategy_id: str
    exposure_kind: str = ""
    instruments: tuple = ()
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class MarketReference:
    """Optional market reference for translation (prices etc.)."""

    symbols: tuple = ()
    reference_prices: dict = field(default_factory=dict)
    observed_at: str = ""


@dataclass(frozen=True)
class InstrumentTarget:
    """One instrument in an EconomicTarget (no broker order syntax yet)."""

    instrument_id: str
    broker_symbol: str = ""
    side: str = ""
    target_notional: float | None = None
    target_quantity: float | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class EconomicTarget:
    """Economic exposure target. Pre-broker, may be multi-leg."""

    event_id: str
    strategy_id: str
    account_id: str
    instruments: tuple = ()
    currency: str = ""
    model_heat_reference: str = ""
    translation_version: str = ""
    known_time: str = ""
    metadata: dict = field(default_factory=dict)
