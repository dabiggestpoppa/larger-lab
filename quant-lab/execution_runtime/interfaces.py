"""QL-EXEC-R1 — adapter protocols (interfaces only; no implementations).

- StrategyAdapter is broker-neutral (no MT5/TradeLocker types).
- CapitalPolicyAdapter owns admission/reservation/release ONLY; it must NOT
  translate heat into notional.
- CapitalTranslationAdapter is a separate bridge (economic target only).
- BrokerSession is broker-neutral; no MetaTrader5 import here.
"""
from __future__ import annotations

from typing import Protocol

from .types import (
    AccountState,
    Bar,
    BrokerIdentity,
    BrokerSnapshot,
    BoundAccountSnapshot,
    CancelResult,
    CapitalDecision,
    CapitalRequest,
    CheckResult,
    CloseResult,
    Deal,
    EconomicTarget,
    MarketReference,
    Order,
    OrderIntent,
    Position,
    StrategyEvent,
    StrategyExposureContext,
    SubmitResult,
    SymbolInfo,
    Tick,
)
from .reservation import ReservationRecord


class StrategyAdapter(Protocol):
    """Broker-neutral strategy adapter. No MT5 types, no capital math."""

    strategy_id: str

    def required_market_data(self) -> tuple[str, ...]: ...

    def initialize(self, runtime_ctx: dict) -> None: ...

    def warm(self, historical: object) -> None: ...

    def on_market_snapshot(self, snapshot: object) -> None: ...

    def produce_events(self) -> tuple[StrategyEvent, ...]: ...

    def serialize_state(self) -> str: ...

    def restore_state(self, state: str) -> None: ...

    def health(self) -> dict: ...


class CapitalPolicyAdapter(Protocol):
    """Capital admission/reservation authority. Stops at admission.

    It does NOT know broker lots, contract sizes, MT5/TradeLocker, or a fixed
    f -> notional formula. There is deliberately NO translate_heat_to_notional.
    """

    policy_id: str

    def admit(self, request: CapitalRequest) -> CapitalDecision: ...

    def release(self, reservation_id: str) -> None: ...

    def reconstruct_reservations(self) -> tuple[ReservationRecord, ...]: ...

    def shared_heat_state(self) -> dict: ...


class CapitalTranslationAdapter(Protocol):
    """Bridges an admitted capital decision into an ECONOMIC target.

    Inputs arrive only AFTER account binding. The output is economic exposure,
    not broker order syntax.
    """

    translation_id: str

    def translate(
        self,
        event: StrategyEvent,
        decision: CapitalDecision,
        account_snapshot: BoundAccountSnapshot,
        strategy_context: StrategyExposureContext,
        market_reference: MarketReference | None = None,
    ) -> EconomicTarget: ...


class BrokerSession(Protocol):
    """Minimal cross-provider broker semantic interface. No MT5 import."""

    def connect(self) -> bool: ...

    def disconnect(self) -> None: ...

    def health(self) -> dict: ...

    def identity(self) -> BrokerIdentity: ...

    def account_state(self) -> AccountState: ...

    def symbol_info(self, symbol: str) -> SymbolInfo | None: ...

    def tick(self, symbol: str) -> Tick | None: ...

    def bars(self, symbol: str, timeframe: str, count: int) -> list[Bar] | None: ...

    def positions(self) -> list[Position]: ...

    def orders(self) -> list[Order]: ...

    def deals(self, start: float, end: float) -> list[Deal]: ...

    def order_check(self, intent: OrderIntent) -> CheckResult: ...

    def submit_order(self, intent: OrderIntent) -> SubmitResult: ...

    def cancel_order(self, order_id: str) -> CancelResult: ...

    def close_position(self, position_id: str, reason: str) -> CloseResult: ...

    def reconcile_snapshot(self) -> BrokerSnapshot: ...
