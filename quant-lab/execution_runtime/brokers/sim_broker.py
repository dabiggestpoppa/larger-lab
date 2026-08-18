"""QL-EXEC-R3 — transport-neutral SimBrokerSession.

Implements ``BrokerSession`` with NO network and NO MetaTrader5 so the
GenericRuntime can be proven broker-agnostic (the MT5 adapter is already proven
separately in R2/R2.1). A submitted accepted market order deterministically
creates a broker order record, a deal record, and a position record.

Injected deterministic failure modes:

    FULL_FILL        -> accepted, full position (default)
    PARTIAL_FILL     -> accepted, position at ``partial_ratio`` of requested
    ZERO_FILL        -> accepted order, NO position
    ORDER_REJECT     -> rejected (ORDER_REJECTED)
    TRANSPORT_ERROR  -> order_send transport error (TRANSPORT_ERROR)

The broker's in-memory truth survives runtime object recreation when the same
instance is reused across restarts (it is the injected persistent fixture).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..enums import (
    BrokerErrorCategory,
    ClockStatus,
    Environment,
    FillPolicy,
    HedgingNetting,
    OrderSide,
)
from ..interfaces import BrokerSession
from ..types import (
    AccountState,
    Bar,
    BrokerClockState,
    BrokerIdentity,
    BrokerSnapshot,
    CancelResult,
    CheckResult,
    CloseResult,
    Deal,
    Order,
    OrderIntent,
    OrderResult,
    Position,
    SymbolInfo,
    Tick,
    utcnow_iso,
)

SUCCESS_RETCODE = 10009
REJECT_RETCODE = 10030


@dataclass
class _SimPosition:
    position_id: str
    symbol: str
    volume: float
    side: str
    price_open: float
    magic: int
    ownership_tag: str
    time: float


@dataclass
class _SimOrder:
    order_id: str
    symbol: str
    volume: float
    side: str
    magic: int
    ownership_tag: str
    time: float


@dataclass
class _SimDeal:
    deal_id: str
    symbol: str
    volume: float
    price: float
    entry: bool
    order_id: str
    position_id: str
    side: str
    magic: int
    ownership_tag: str
    time: float


class SimBrokerSession(BrokerSession):
    """Deterministic in-memory broker behind the generic BrokerSession contract."""

    def __init__(
        self,
        *,
        broker_company: str = "SIM-BROKER",
        server: str = "SIM-Demo",
        account_identifier: str = "sim-100001",
        environment: Environment = Environment.SIM,
        currency: str = "USD",
        hedging_netting: HedgingNetting = HedgingNetting.HEDGING,
        account_id: str = "sim-account",
        partial_ratio: float = 0.6,
        default_ask: float = 1.10005,
        default_bid: float = 1.10000,
    ) -> None:
        self._connected = False
        self._broker_company = broker_company
        self._server = server
        self._account_identifier = account_identifier
        self._environment = environment
        self._currency = currency
        self._hedging_netting = hedging_netting
        self._account_id = account_id
        self._partial_ratio = partial_ratio
        self._default_ask = default_ask
        self._default_bid = default_bid

        self._positions: dict[str, _SimPosition] = {}
        self._orders: dict[str, _SimOrder] = {}
        self._deals: list[_SimDeal] = []
        self._symbols: dict[str, SymbolInfo] = {}
        self._next_id = 100000

        self._fail_mode = "FULL_FILL"
        self._order_check_ok = True
        self._connect_ok = True
        self._symbol_fail: dict[str, str] = {}  # broker_symbol -> mode override

    # ── test configuration helpers ────────────────────────────────────────

    def set_fail_mode(self, mode: str) -> None:
        self._fail_mode = mode

    def set_symbol_fail_mode(self, symbol: str, mode: str) -> None:
        """Per-symbol failure override (e.g. leg2 partial, leg3 reject)."""
        self._symbol_fail[symbol] = mode

    def clear_symbol_fail_modes(self) -> None:
        self._symbol_fail.clear()

    def _mode_for(self, symbol: str) -> str:
        return self._symbol_fail.get(symbol, self._fail_mode)

    def set_order_check_ok(self, ok: bool) -> None:
        self._order_check_ok = ok

    def set_connect_ok(self, ok: bool) -> None:
        self._connect_ok = ok

    def set_connected(self, connected: bool) -> None:
        self._connected = connected

    def seed_foreign_position(
        self,
        position_id: str,
        symbol: str = "GBPUSD",
        volume: float = 1.0,
        side: str = "LONG",
        magic: int = 999999,
        ownership_tag: str = "FOREIGN",
    ) -> None:
        self._positions[position_id] = _SimPosition(
            position_id=position_id,
            symbol=symbol,
            volume=volume,
            side=side,
            price_open=1.0,
            magic=magic,
            ownership_tag=ownership_tag,
            time=0.0,
        )

    def add_symbol(self, symbol: str, **kwargs) -> None:
        self._symbols[symbol] = SymbolInfo(symbol=symbol, **kwargs)

    def position_count(self) -> int:
        return len(self._positions)

    def order_count(self) -> int:
        return len(self._orders)

    def deal_count(self) -> int:
        return len(self._deals)

    def broker_position(self, position_id: str) -> Optional[_SimPosition]:
        return self._positions.get(position_id)

    # ── BrokerSession ─────────────────────────────────────────────────────

    def connect(self) -> bool:
        self._connected = self._connect_ok
        return self._connect_ok

    def disconnect(self) -> None:
        self._connected = False

    def health(self) -> dict:
        return {"connected": self._connected}

    def identity(self) -> BrokerIdentity:
        return BrokerIdentity(
            broker_company=self._broker_company,
            server=self._server,
            account_identifier=self._account_identifier,
            environment=self._environment,
            currency=self._currency,
            account_mode=self._environment.value,
            hedging_netting=self._hedging_netting,
            trade_allowed=True,
            terminal_trade_allowed=True,
            tradeapi_disabled=False,
        )

    def account_state(self) -> AccountState:
        return AccountState(
            currency=self._currency,
            equity=10000.0,
            balance=10000.0,
            margin=0.0,
            free_margin=10000.0,
            buying_power=None,
            account_mode=self._environment.value,
        )

    def clock_state(self) -> BrokerClockState:
        return BrokerClockState(
            source_clock_name="SIM_CLOCK",
            source_offset_seconds=0.0,
            calibrated=True,
            status=ClockStatus.CALIBRATED,
            observed_at_utc=utcnow_iso(),
        )

    def symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        return self._symbols.get(
            symbol,
            SymbolInfo(
                symbol=symbol,
                digits=5,
                point=0.00001,
                contract_size=100000.0,
                volume_min=0.01,
                volume_max=100.0,
                volume_step=0.01,
                visible=True,
                trade_mode="SIM",
                declared_fill_policies=(FillPolicy.FILL_OR_KILL,),
            ),
        )

    def ensure_symbol(self, symbol: str) -> bool:
        return True

    def tick(self, symbol: str) -> Optional[Tick]:
        return Tick(
            symbol=symbol,
            bid=self._default_bid,
            ask=self._default_ask,
            time=0.0,
            observed_at_utc=0.0,
            source_clock_name="SIM_CLOCK",
            offset_seconds=0.0,
            valid=True,
        )

    def bars(self, symbol: str, timeframe: str = "M5", count: int = 500) -> Optional[list[Bar]]:
        return []

    def positions(self) -> list[Position]:
        return [
            Position(
                position_id=p.position_id,
                symbol=p.symbol,
                volume=p.volume,
                side=p.side,
                price_open=p.price_open,
                current_price=None,
                magic=p.magic,
                ownership_tag=p.ownership_tag,
                time=p.time,
                profit=None,
            )
            for p in self._positions.values()
        ]

    def orders(self) -> list[Order]:
        return [
            Order(
                order_id=o.order_id,
                symbol=o.symbol,
                volume=o.volume,
                order_type="MARKET",
                magic=o.magic,
                ownership_tag=o.ownership_tag,
                time=o.time,
            )
            for o in self._orders.values()
        ]

    def deals(self, start: float = 0.0, end: float = 0.0) -> list[Deal]:
        return [
            Deal(
                deal_id=d.deal_id,
                symbol=d.symbol,
                volume=d.volume,
                price=d.price,
                entry=d.entry,
                order_id=d.order_id,
                position_id=d.position_id,
                side=d.side,
                magic=d.magic,
                ownership_tag=d.ownership_tag,
                time=d.time,
            )
            for d in self._deals
        ]

    def order_check(self, intent: OrderIntent) -> CheckResult:
        if not self._connected:
            return CheckResult(
                ok=False, reason="not connected", error_category=BrokerErrorCategory.NOT_CONNECTED
            )
        if not self._order_check_ok:
            return CheckResult(
                ok=False,
                retcode=REJECT_RETCODE,
                reason="order_check rejected",
                error_category=BrokerErrorCategory.ORDER_CHECK_FAILED,
            )
        return CheckResult(ok=True, retcode=0, error_category=BrokerErrorCategory.NONE)

    def submit_order(self, intent: OrderIntent) -> OrderResult:
        if not self._connected:
            return OrderResult(
                ok=False, reason="not connected", error_category=BrokerErrorCategory.NOT_CONNECTED
            )
        if intent.volume <= 0:
            return OrderResult(
                ok=False, reason="zero quantity", error_category=BrokerErrorCategory.INVALID_REQUEST
            )
        mode = self._mode_for(intent.symbol)
        if mode == "ORDER_REJECT":
            return OrderResult(
                ok=False,
                retcode=REJECT_RETCODE,
                reason="order rejected",
                error_category=BrokerErrorCategory.ORDER_REJECTED,
            )
        if mode == "TRANSPORT_ERROR":
            return OrderResult(
                ok=False,
                reason="order_send transport error",
                error_category=BrokerErrorCategory.TRANSPORT_ERROR,
            )

        order_id = str(self._next_id)
        self._next_id += 1
        side = "LONG" if intent.side is OrderSide.BUY else "SHORT"
        self._orders[order_id] = _SimOrder(
            order_id=order_id,
            symbol=intent.symbol,
            volume=intent.volume,
            side=side,
            magic=intent.broker_magic,
            ownership_tag=intent.ownership_tag,
            time=0.0,
        )

        if mode == "ZERO_FILL":
            # Accepted order, but no position/deal materializes.
            return OrderResult(
                ok=True, broker_order_id=order_id, retcode=SUCCESS_RETCODE,
                error_category=BrokerErrorCategory.NONE,
            )

        filled = intent.volume
        if mode == "PARTIAL_FILL":
            filled = round(intent.volume * self._partial_ratio, 6)

        position_id = str(self._next_id)
        self._next_id += 1
        self._positions[position_id] = _SimPosition(
            position_id=position_id,
            symbol=intent.symbol,
            volume=filled,
            side=side,
            price_open=intent.reference_price or self._default_ask,
            magic=intent.broker_magic,
            ownership_tag=intent.ownership_tag,
            time=0.0,
        )
        deal_id = str(self._next_id)
        self._next_id += 1
        self._deals.append(
            _SimDeal(
                deal_id=deal_id,
                symbol=intent.symbol,
                volume=filled,
                price=intent.reference_price or self._default_ask,
                entry=True,
                order_id=order_id,
                position_id=position_id,
                side=side,
                magic=intent.broker_magic,
                ownership_tag=intent.ownership_tag,
                time=0.0,
            )
        )
        return OrderResult(
            ok=True,
            broker_order_id=order_id,
            retcode=SUCCESS_RETCODE,
            error_category=BrokerErrorCategory.NONE,
        )

    def cancel_order(self, order_id: str) -> CancelResult:
        if not self._connected:
            return CancelResult(
                ok=False, reason="not connected", error_category=BrokerErrorCategory.NOT_CONNECTED
            )
        return CancelResult(ok=True, error_category=BrokerErrorCategory.NONE)

    def close_position(self, position_id: str, reason: str = "") -> CloseResult:
        if not self._connected:
            return CloseResult(
                ok=False, reason="not connected", error_category=BrokerErrorCategory.NOT_CONNECTED
            )
        pos = self._positions.get(position_id)
        if pos is None:
            return CloseResult(
                ok=False, reason="position not found", error_category=BrokerErrorCategory.INVALID_REQUEST
            )
        del self._positions[position_id]
        deal_id = str(self._next_id)
        self._next_id += 1
        self._deals.append(
            _SimDeal(
                deal_id=deal_id,
                symbol=pos.symbol,
                volume=pos.volume,
                price=pos.price_open,
                entry=False,
                order_id="",
                position_id=position_id,
                side=pos.side,
                magic=pos.magic,
                ownership_tag=pos.ownership_tag,
                time=0.0,
            )
        )
        return CloseResult(ok=True, error_category=BrokerErrorCategory.NONE)

    def reconcile_snapshot(self) -> BrokerSnapshot:
        return BrokerSnapshot(
            account_state=self.account_state(),
            positions=tuple(self.positions()),
            orders=tuple(self.orders()),
            deals=tuple(self.deals()),
        )
