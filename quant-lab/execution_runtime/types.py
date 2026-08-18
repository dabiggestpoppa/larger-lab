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
    BrokerErrorCategory,
    CapitalDecisionKind,
    ClockStatus,
    Environment,
    FillPolicy,
    HedgingNetting,
    OrderSide,
    OrderType,
    QuantityUnit,
    SecretKind,
    SlippageUnit,
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
    trade_allowed: bool = True
    terminal_trade_allowed: bool = True
    tradeapi_disabled: bool = False


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
    """Broker-neutral symbol contract.

    ``declared_fill_policies`` is the broker's DECLARED capability; it is NOT
    a guarantee of accepted behavior (TB R6 showed declared and accepted fill
    modes can differ).
    """

    symbol: str
    digits: int = 0
    point: float = 0.0
    contract_size: float = 0.0
    volume_min: float = 0.0
    volume_max: float = 0.0
    volume_step: float = 0.0
    visible: bool = True
    trade_mode: str = "UNKNOWN"
    trade_tick_size: float = 0.0
    trade_tick_value: float = 0.0
    declared_fill_policies: tuple = ()


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
    keys must be preserved as-is. ``valid`` is False for an unusable quote
    (zero/negative or crossed bid/ask); raw values are preserved, not invented.
    """

    symbol: str
    bid: float = 0.0
    ask: float = 0.0
    time: float = 0.0  # raw source timestamp, never silently normalized
    observed_at_utc: float = 0.0  # local observation/received time
    source_clock_name: str = ""  # which source clock ``time`` is in
    offset_seconds: float = 0.0  # calibrated source-minus-UTC offset
    valid: bool = True


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
    volume: float = 0.0  # real_volume with tick_volume fallback
    observed_at_utc: float = 0.0  # local observation/received time
    source_clock_name: str = ""
    offset_seconds: float = 0.0  # calibrated source-minus-UTC offset


@dataclass(frozen=True)
class Position:
    """Normalized open position. Broker truth; ownership is evaluated later."""

    position_id: str
    symbol: str
    volume: float = 0.0
    side: str = ""  # LONG / SHORT
    price_open: float = 0.0
    current_price: float | None = None
    magic: int = 0
    ownership_tag: str = ""
    time: float = 0.0
    profit: float | None = None


@dataclass(frozen=True)
class Order:
    """Normalized pending order (NOT a filled position)."""

    order_id: str
    symbol: str
    volume: float = 0.0
    order_type: str = ""
    magic: int = 0
    ownership_tag: str = ""
    time: float = 0.0


@dataclass(frozen=True)
class Deal:
    """Normalized history deal. order/deal/position IDs remain distinct."""

    deal_id: str
    symbol: str
    volume: float = 0.0
    price: float = 0.0
    entry: bool = True
    order_id: str = ""
    position_id: str = ""
    side: str = ""
    magic: int = 0
    ownership_tag: str = ""
    time: float = 0.0
    profit: float | None = None
    commission: float | None = None
    swap: float | None = None
    fee: float | None = None


@dataclass(frozen=True)
class OrderIntent:
    """Broker-neutral order intent (R2-amended: no opaque critical fields).

    ``volume`` is the BROKER-NATIVE quantity (MT5 lots) at the BrokerSession
    boundary; ``quantity_unit`` makes that explicit. Economic notional -> lots
    conversion is upstream, NOT part of the broker session.
    """

    intent_id: str
    account_id: str
    symbol: str
    side: OrderSide = OrderSide.BUY
    volume: float = 0.0
    quantity_unit: QuantityUnit = QuantityUnit.LOT
    order_type: OrderType = OrderType.MARKET
    reference_price: float | None = None
    price_constraint: float | None = None
    fill_policy: FillPolicy = FillPolicy.BROKER_DEFAULT
    slippage_constraint: float | None = None
    slippage_unit: SlippageUnit = SlippageUnit.POINTS
    broker_magic: int = 0
    ownership_tag: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class CheckResult:
    """Normalized order_check result. ``retcode`` is adapter-normalized.

    ``error_category`` is ``NONE`` when ``ok`` is True; a successful check
    never carries a failure reason or error.
    """

    ok: bool = False
    retcode: int | None = None
    broker_message: str = ""
    reason: str = ""
    detail: dict = field(default_factory=dict)
    error_category: BrokerErrorCategory = BrokerErrorCategory.NONE


@dataclass(frozen=True)
class SubmitResult:
    ok: bool = False
    broker_order_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class OrderResult:
    """Normalized order-submission result (no raw mutable broker objects).

    Truth invariant: ``ok == True`` => ``error_category`` is ``NONE``.
    ``ok == False`` => a meaningful non-success category (never ``NONE``).
    """

    ok: bool = False
    broker_order_id: str = ""
    retcode: int | None = None
    broker_message: str = ""
    reason: str = ""
    error_category: BrokerErrorCategory = BrokerErrorCategory.NONE


@dataclass(frozen=True)
class CancelResult:
    """Normalized cancel result. ``error_category`` is ``NONE`` on success."""

    ok: bool = False
    reason: str = ""
    error_category: BrokerErrorCategory = BrokerErrorCategory.NONE


@dataclass(frozen=True)
class CloseResult:
    """Normalized close result. ``error_category`` is ``NONE`` on success."""

    ok: bool = False
    reason: str = ""
    error_category: BrokerErrorCategory = BrokerErrorCategory.NONE


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
