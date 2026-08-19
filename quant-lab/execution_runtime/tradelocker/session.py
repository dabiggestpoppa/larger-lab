"""QL-EXEC-R5 — TradeLockerBrokerSession (generic BrokerSession implementation).

Provider-neutral IN CONTRACT, provider-native IN TRUTH:

- ``accountId`` and ``accNum`` stay distinct; identity uses ``accNum``.
- INFO route for market data, TRADE route for execution (routes cached with
  account/instrument binding, refreshed when stale).
- ``orderId != positionId``: submit returns the order id; a position is only
  assumed when provider position truth says so.
- Accepted order != filled position: ``submit_order`` returns OK on acceptance;
  fill truth comes from positions / executions reconciliation.
- Close request != closed truth: ``close_position`` places a closing order
  (IOC then GTC per the official client); the position is confirmed flat only
  via ``positions()``.
- Market orders are IOC, limit/stop orders are GTC — mapping owned here.
- ``order_check`` is a LOCAL structural preflight (TradeLocker has no
  broker-side preflight endpoint); capability ``supports_order_check`` is
  UNSUPPORTED and documented.

No live orders. Offline / mock / demo-read foundation only.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from ..capabilities import BrokerCapabilities
from ..enums import (
    BrokerErrorCategory,
    CapabilityState,
    ClockStatus,
    Environment,
    FillPolicy,
    HedgingNetting,
    OrderSide,
    OrderType,
    QuantityUnit,
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
from .client import (
    R_CLOSE_POSITION,
    R_DELETE_ORDER,
    R_PLACE_ORDER,
    TradeLockerApiError,
    TradeLockerClient,
    TradeLockerRateLimitExceeded,
)
from .transport import AmbiguousSendError, TimeoutBeforeSendError
from .types import TradeLockerInstrument, TradeLockerQuote

# Market orders are IOC and limit/stop are GTC per the official TradeLocker
# client contract — the adapter owns this mapping, strategy never sees it.
VALIDITY_MARKET = "IOC"
VALIDITY_RESTING = "GTC"

_RESOLUTION_MAP = {
    "M1": "1m",
    "M5": "5m",
    "M15": "15m",
    "M30": "30m",
    "H1": "1h",
    "H4": "4h",
    "D1": "1d",
}
_INTERVAL_SECONDS = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}


@dataclass(frozen=True)
class TradeLockerProfile:
    """Immutable instance-scoped TradeLocker profile (provider-quirk overrides).

    Defaults come from official provider truth; explicit broker-observed
    deviations belong HERE, never as module globals.
    """

    broker_company: str = "TradeLocker"
    currency: str = "USD"
    environment: Environment = Environment.DEMO
    max_strategy_id_length: int = 32
    min_qty: float = 0.01
    quantity_precision: int = 6
    version: str = "r5"


def _as_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class TradeLockerBrokerSession(BrokerSession):
    """TradeLocker behind the generic BrokerSession contract."""

    provider_name = "TRADELOCKER"

    def __init__(
        self,
        *,
        client: TradeLockerClient,
        account_id: int,
        acc_num: int,
        server: str = "",
        profile: Optional[TradeLockerProfile] = None,
    ) -> None:
        self._client = client
        self._account_id = account_id
        self._acc_num = acc_num
        self._server = server
        self._profile = profile or TradeLockerProfile()

        self._connected = False
        self._instruments_by_name: dict[str, TradeLockerInstrument] = {}
        self._instruments_by_id: dict[int, TradeLockerInstrument] = {}
        self._last_quote: dict[str, TradeLockerQuote] = {}
        self._clock_calibrated_at = 0.0
        self._last_account_state: dict = {}

    # ── lifecycle ─────────────────────────────────────────────────────────

    def connect(self) -> bool:
        try:
            if not self._client.authenticated():
                self._client.authenticate()
            self._client.get_config(force=True)
            instruments = self._client.get_instruments(self._account_id)
            self._instruments_by_name = {}
            self._instruments_by_id = {}
            for inst in instruments:
                self._instruments_by_name[inst.name] = inst
                self._instruments_by_id[inst.tradable_instrument_id] = inst
            self._connected = True
            return True
        except Exception:
            self._connected = False
            return False

    def disconnect(self) -> None:
        self._connected = False

    def health(self) -> dict:
        return {
            "connected": self._connected,
            "provider": self.provider_name,
            "account_id": self._account_id,
            "acc_num": self._acc_num,
            "config_hash": self._client.config_snapshot.version_hash
            if self._client.config_snapshot
            else None,
            "instrument_count": len(self._instruments_by_name),
            "access_token_expiry_seconds": self._client.token_expiry_seconds(),
            "auth_refresh_count": self._client.refresh_count(),
        }

    # ── identity / account / clock ────────────────────────────────────────

    def identity(self) -> BrokerIdentity:
        return BrokerIdentity(
            broker_company=self._profile.broker_company,
            server=self._server,
            account_identifier=str(self._acc_num),
            environment=self._profile.environment,
            currency=self._profile.currency,
            account_mode=self._profile.environment.value,
            hedging_netting=HedgingNetting.UNKNOWN,
            trade_allowed=True,
            terminal_trade_allowed=True,
            tradeapi_disabled=False,
        )

    def account_state(self) -> AccountState:
        try:
            raw = self._client.get_account_state(self._account_id)
        except TradeLockerApiError:
            raw = self._last_account_state
        self._last_account_state = raw
        return AccountState(
            currency=str(raw.get("currency", self._profile.currency) or self._profile.currency),
            equity=_nullable_float(raw.get("equity")),
            balance=_nullable_float(raw.get("balance")),
            margin=_nullable_float(raw.get("margin")),
            free_margin=_nullable_float(raw.get("freeMargin")),
            buying_power=_nullable_float(raw.get("buyingPower")),
            account_mode=str(raw.get("mode", raw.get("type", self._profile.environment.value))),
        )

    def clock_state(self) -> BrokerClockState:
        quote = next(iter(self._last_quote.values()), None)
        if quote is None or quote.server_time_ms <= 0:
            return BrokerClockState(
                source_clock_name="TRADELOCKER_SERVER_TIME",
                source_offset_seconds=0.0,
                calibrated=False,
                status=ClockStatus.UNCALIBRATED,
                observed_at_utc=utcnow_iso(),
                failure_reason="no quote server time observed",
            )
        local_ms = time.time() * 1000.0
        offset = (quote.server_time_ms - local_ms) / 1000.0
        fresh = abs(local_ms - quote.server_time_ms) < 60000
        return BrokerClockState(
            source_clock_name="TRADELOCKER_SERVER_TIME",
            source_offset_seconds=offset,
            calibrated=fresh,
            calibration_age_seconds=abs(local_ms - quote.server_time_ms) / 1000.0,
            status=ClockStatus.CALIBRATED if fresh else ClockStatus.STALE,
            observed_at_utc=utcnow_iso(),
        )

    # ── instruments / market data ─────────────────────────────────────────

    def _instrument(self, symbol: str) -> Optional[TradeLockerInstrument]:
        return self._instruments_by_name.get(symbol)

    def ensure_symbol(self, symbol: str) -> bool:
        return self._instrument(symbol) is not None

    def symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        inst = self._instrument(symbol)
        if inst is None:
            return None
        digits = _as_int(inst.raw.get("pricePrecision"), 5)
        return SymbolInfo(
            symbol=symbol,
            digits=digits,
            point=10.0 ** (-digits),
            contract_size=_as_float(inst.raw.get("contractSize"), 0.0),
            volume_min=_as_float(inst.raw.get("volumeMin"), self._profile.min_qty),
            volume_max=_as_float(inst.raw.get("volumeMax"), 0.0),
            volume_step=_as_float(inst.raw.get("volumeStep"), self._profile.min_qty),
            visible=True,
            trade_mode="TRADELOCKER",
            trade_tick_size=10.0 ** (-digits),
            trade_tick_value=_as_float(inst.raw.get("tickValue"), 0.0),
            declared_fill_policies=(FillPolicy.IMMEDIATE_OR_CANCEL,),
        )

    def tick(self, symbol: str) -> Optional[Tick]:
        inst = self._instrument(symbol)
        if inst is None:
            return None
        route = inst.route("INFO")
        if route is None:
            return None
        try:
            quote = self._client.get_quotes(inst.tradable_instrument_id, route)
        except TradeLockerApiError:
            return None
        self._last_quote[symbol] = quote
        local_ms = time.time() * 1000.0
        offset = (quote.server_time_ms - local_ms) / 1000.0 if quote.server_time_ms else 0.0
        valid = quote.bid > 0.0 and quote.ask >= quote.bid
        return Tick(
            symbol=symbol,
            bid=quote.bid,
            ask=quote.ask,
            time=quote.server_time_ms / 1000.0 if quote.server_time_ms else 0.0,
            observed_at_utc=local_ms / 1000.0,
            source_clock_name="TRADELOCKER_SERVER_TIME",
            offset_seconds=offset,
            valid=valid,
        )

    def bars(self, symbol: str, timeframe: str = "M5", count: int = 500) -> Optional[list]:
        inst = self._instrument(symbol)
        if inst is None:
            return None
        route = inst.route("INFO")
        if route is None:
            return None
        resolution = _RESOLUTION_MAP.get(timeframe, "5m")
        interval = _INTERVAL_SECONDS.get(resolution, 300)
        to_ms = int(time.time() * 1000.0)
        from_ms = to_ms - max(count, 1) * interval * 1000
        try:
            rows = self._client.get_price_history(
                inst.tradable_instrument_id, route, resolution, from_ms, to_ms
            )
        except TradeLockerApiError:
            return None
        offset = 0.0
        q = self._last_quote.get(symbol)
        if q is not None and q.server_time_ms:
            offset = (q.server_time_ms - time.time() * 1000.0) / 1000.0
        out = []
        for row in rows:
            t = _as_int(row.get("t"), 0)
            out.append(
                Bar(
                    symbol=symbol,
                    time=t / 1000.0 if t else 0.0,
                    open=_as_float(row.get("o")),
                    high=_as_float(row.get("h")),
                    low=_as_float(row.get("l")),
                    close=_as_float(row.get("c")),
                    volume=_as_float(row.get("v")),
                    observed_at_utc=time.time(),
                    source_clock_name="TRADELOCKER_SERVER_TIME",
                    offset_seconds=offset,
                )
            )
        return out

    # ── positions / orders / deals ────────────────────────────────────────

    def positions(self) -> list:
        try:
            rows = self._client.get_positions(self._account_id)
        except TradeLockerApiError:
            return []
        out = []
        for row in rows:
            pid = row.get("id")
            if pid is None:
                continue
            inst = self._instruments_by_id.get(_as_int(row.get("tradableInstrumentId")))
            symbol = inst.name if inst else str(row.get("tradableInstrumentId", ""))
            side_raw = str(row.get("side", ""))
            qty = _as_float(row.get("qty"))
            out.append(
                Position(
                    position_id=str(pid),
                    symbol=symbol,
                    volume=abs(qty),
                    side="LONG" if side_raw == "buy" else "SHORT",
                    price_open=_as_float(row.get("price")),
                    current_price=_nullable_float(row.get("currentPrice")),
                    magic=0,
                    ownership_tag=str(row.get("strategyId", "") or ""),
                    time=_as_int(row.get("serverTime", row.get("time", 0))) / 1000.0,
                    profit=_nullable_float(row.get("pnl", row.get("profit"))),
                )
            )
        return out

    def orders(self) -> list:
        try:
            rows = self._client.get_orders(self._account_id, history=False)
        except TradeLockerApiError:
            return []
        out = []
        for row in rows:
            oid = row.get("id")
            if oid is None:
                continue
            inst = self._instruments_by_id.get(_as_int(row.get("tradableInstrumentId")))
            symbol = inst.name if inst else str(row.get("tradableInstrumentId", ""))
            out.append(
                Order(
                    order_id=str(oid),
                    symbol=symbol,
                    volume=abs(_as_float(row.get("qty"))),
                    order_type=str(row.get("type", "")),
                    magic=0,
                    ownership_tag=str(row.get("strategyId", "") or ""),
                    time=_as_int(row.get("serverTime", row.get("time", 0))) / 1000.0,
                )
            )
        return out

    def deals(self, start: float = 0.0, end: float = 0.0) -> list:
        try:
            rows = self._client.get_executions(self._account_id)
        except TradeLockerApiError:
            return []
        open_positions = {p.position_id: p for p in self.positions()}
        out = []
        for row in rows:
            oid = row.get("orderId", row.get("id"))
            if oid is None:
                continue
            inst = self._instruments_by_id.get(_as_int(row.get("tradableInstrumentId")))
            symbol = inst.name if inst else str(row.get("tradableInstrumentId", ""))
            side_raw = str(row.get("side", ""))
            qty = _as_float(row.get("qty"))
            side = "LONG" if side_raw == "buy" else "SHORT"
            pid = str(row.get("positionId", 0) or 0)
            # Entry vs exit normalization: a fill whose position currently
            # exists with a matching side is an entry; otherwise a close.
            entry = True
            pos = open_positions.get(pid)
            if pos is not None and pos.side != side:
                entry = False
            elif pos is None and pid != "0":
                entry = False
            out.append(
                Deal(
                    deal_id=str(row.get("id", oid)),
                    symbol=symbol,
                    volume=abs(qty),
                    price=_as_float(row.get("price")),
                    entry=entry,
                    order_id=str(oid),
                    position_id=pid,
                    side=side,
                    magic=0,
                    ownership_tag=str(row.get("strategyId", "") or ""),
                    time=_as_int(row.get("serverTime", row.get("time", 0))) / 1000.0,
                    profit=_nullable_float(row.get("pnl", row.get("profit"))),
                )
            )
        return out

    # ── execution ─────────────────────────────────────────────────────────

    def order_check(self, intent: OrderIntent) -> CheckResult:
        """LOCAL structural preflight only — TradeLocker has no broker-side
        order_check endpoint. No network, no provider state mutation."""
        if not self._connected:
            return CheckResult(
                ok=False, reason="not connected", error_category=BrokerErrorCategory.NOT_CONNECTED
            )
        inst = self._instrument(intent.symbol)
        if inst is None:
            return CheckResult(
                ok=False,
                reason=f"unknown instrument: {intent.symbol}",
                error_category=BrokerErrorCategory.SYMBOL_UNAVAILABLE,
            )
        if inst.route("TRADE") is None:
            return CheckResult(
                ok=False,
                reason=f"no TRADE route for {intent.symbol}",
                error_category=BrokerErrorCategory.SYMBOL_UNAVAILABLE,
            )
        if intent.volume <= 0:
            return CheckResult(
                ok=False, reason="zero quantity", error_category=BrokerErrorCategory.INVALID_REQUEST
            )
        if intent.quantity_unit is not QuantityUnit.LOT:
            return CheckResult(
                ok=False,
                reason=f"unsupported quantity unit {intent.quantity_unit}",
                error_category=BrokerErrorCategory.INVALID_REQUEST,
            )
        validity_reason = self._validity_check(intent)
        if validity_reason:
            return CheckResult(
                ok=False, reason=validity_reason, error_category=BrokerErrorCategory.INVALID_REQUEST
            )
        if intent.ownership_tag and len(intent.ownership_tag) > self._profile.max_strategy_id_length:
            return CheckResult(
                ok=False,
                reason=(
                    f"ownership tag exceeds max strategyId length "
                    f"({self._profile.max_strategy_id_length})"
                ),
                error_category=BrokerErrorCategory.INVALID_REQUEST,
            )
        return CheckResult(ok=True, retcode=0, error_category=BrokerErrorCategory.NONE)

    def _validity_check(self, intent: OrderIntent) -> str:
        # TradeLocker truth: market orders are IOC; limit/stop orders are GTC.
        # The generic FillPolicy has no GTC member (it models fill policy, not
        # validity), so the adapter owns the mapping: any explicit non-default
        # fill policy that contradicts provider validity fails closed.
        if intent.order_type is OrderType.MARKET:
            if intent.fill_policy not in (FillPolicy.BROKER_DEFAULT, FillPolicy.IMMEDIATE_OR_CANCEL):
                return f"market orders must be IOC, got {intent.fill_policy}"
        else:
            if intent.fill_policy is not FillPolicy.BROKER_DEFAULT:
                return f"{intent.order_type.value} orders are GTC-only, got {intent.fill_policy}"
        return ""

    def submit_order(self, intent: OrderIntent) -> OrderResult:
        if not self._connected:
            return OrderResult(
                ok=False, reason="not connected", error_category=BrokerErrorCategory.NOT_CONNECTED
            )
        check = self.order_check(intent)
        if not check.ok:
            return OrderResult(
                ok=False,
                reason=check.reason,
                error_category=check.error_category,
            )
        inst = self._instrument(intent.symbol)
        route_id = inst.route("TRADE")
        order_type = {
            OrderType.MARKET: "market",
            OrderType.LIMIT: "limit",
            OrderType.STOP: "stop",
        }[intent.order_type]
        validity = VALIDITY_MARKET if intent.order_type is OrderType.MARKET else VALIDITY_RESTING
        side = "buy" if intent.side is OrderSide.BUY else "sell"
        try:
            order_id = self._client.place_order(
                account_id=self._account_id,
                instrument_id=inst.tradable_instrument_id,
                qty=round(intent.volume, self._profile.quantity_precision),
                side=side,
                order_type=order_type,
                validity=validity,
                route_id=route_id,
                price=intent.reference_price,
                stop_price=intent.price_constraint if intent.order_type is OrderType.STOP else None,
                strategy_id=intent.ownership_tag or None,
            )
        except AmbiguousSendError as err:
            return OrderResult(
                ok=False,
                reason=f"ambiguous send — reconcile broker truth before retry: {err}",
                error_category=BrokerErrorCategory.TRANSPORT_ERROR,
            )
        except TimeoutBeforeSendError as err:
            return OrderResult(
                ok=False,
                reason=f"timeout before send: {err}",
                error_category=BrokerErrorCategory.TRANSPORT_ERROR,
            )
        except TradeLockerRateLimitExceeded as err:
            return OrderResult(
                ok=False,
                reason=f"rate limited: {err}",
                error_category=BrokerErrorCategory.TRANSPORT_ERROR,
            )
        except TradeLockerApiError as err:
            if err.status == 400:
                return OrderResult(
                    ok=False,
                    reason=f"order rejected by provider: {err}",
                    error_category=BrokerErrorCategory.ORDER_REJECTED,
                )
            return OrderResult(
                ok=False,
                reason=f"provider error: {err}",
                error_category=BrokerErrorCategory.TRANSPORT_ERROR,
            )
        # Acceptance only — fill truth comes from positions/executions.
        return OrderResult(
            ok=True,
            broker_order_id=str(order_id),
            broker_message="accepted; fill unconfirmed — reconcile positions truth",
            error_category=BrokerErrorCategory.NONE,
        )

    def cancel_order(self, order_id: str) -> CancelResult:
        if not self._connected:
            return CancelResult(
                ok=False, reason="not connected", error_category=BrokerErrorCategory.NOT_CONNECTED
            )
        try:
            self._client.cancel_order(self._account_id, int(order_id))
        except (AmbiguousSendError, TimeoutBeforeSendError) as err:
            return CancelResult(
                ok=False, reason=str(err), error_category=BrokerErrorCategory.TRANSPORT_ERROR
            )
        except TradeLockerApiError as err:
            if err.status == 404:
                return CancelResult(
                    ok=False, reason="order not found", error_category=BrokerErrorCategory.INVALID_REQUEST
                )
            return CancelResult(
                ok=False, reason=str(err), error_category=BrokerErrorCategory.TRANSPORT_ERROR
            )
        return CancelResult(ok=True, error_category=BrokerErrorCategory.NONE)

    def close_position(self, position_id: str, reason: str = "") -> CloseResult:
        if not self._connected:
            return CloseResult(
                ok=False, reason="not connected", error_category=BrokerErrorCategory.NOT_CONNECTED
            )
        try:
            self._client.close_position(int(position_id), qty=0.0)
        except (AmbiguousSendError, TimeoutBeforeSendError) as err:
            return CloseResult(
                ok=False, reason=str(err), error_category=BrokerErrorCategory.TRANSPORT_ERROR
            )
        except TradeLockerApiError as err:
            if err.status == 404:
                return CloseResult(
                    ok=False,
                    reason="position not found",
                    error_category=BrokerErrorCategory.INVALID_REQUEST,
                )
            return CloseResult(
                ok=False, reason=str(err), error_category=BrokerErrorCategory.TRANSPORT_ERROR
            )
        # Closing ORDER placed — not proof the position is gone.
        return CloseResult(
            ok=True,
            reason="close order placed; position flatness must be confirmed via positions truth",
            error_category=BrokerErrorCategory.NONE,
        )

    def reconcile_snapshot(self) -> BrokerSnapshot:
        return BrokerSnapshot(
            account_state=self.account_state(),
            positions=tuple(self.positions()),
            orders=tuple(self.orders()),
            deals=tuple(self.deals()),
        )

    # ── R5 provider truth helpers ─────────────────────────────────────────

    def capabilities(self) -> BrokerCapabilities:
        """Truthful tri-state capability surface (UNKNOWN fails closed)."""
        return BrokerCapabilities(
            supports_market_order=CapabilityState.SUPPORTED,
            supports_limit_order=CapabilityState.SUPPORTED,
            supports_stop_order=CapabilityState.SUPPORTED,
            supports_cancel=CapabilityState.SUPPORTED,
            supports_partial_fill_reporting=CapabilityState.UNKNOWN,
            supports_partial_close=CapabilityState.SUPPORTED,  # qty-based close
            supports_modify_order=CapabilityState.UNKNOWN,  # cancel+replace until verified
            supports_native_sl_tp=CapabilityState.SUPPORTED,
            supports_trailing_stop=CapabilityState.UNKNOWN,
            supports_client_order_id=CapabilityState.UNSUPPORTED,  # strategyId is a tag, not id
            supports_hedging=CapabilityState.UNKNOWN,  # per-account, unverified
            supports_netting=CapabilityState.UNKNOWN,
            supports_order_check=CapabilityState.UNSUPPORTED,  # local preflight only
            supports_client_tag=CapabilityState.SUPPORTED,
            supports_deal_history=CapabilityState.SUPPORTED,  # executions + ordersHistory
            supports_margin_estimate=CapabilityState.UNKNOWN,
            supports_symbol_activation=CapabilityState.UNKNOWN,
            supports_multi_account_session=CapabilityState.SUPPORTED,
            supports_history=CapabilityState.SUPPORTED,
            supports_streaming_quotes=CapabilityState.UNSUPPORTED,  # REST polling only
            supports_rest_quotes=CapabilityState.SUPPORTED,
        )

    # ── multi-account ─────────────────────────────────────────────────────

    @property
    def account_id(self) -> int:
        return self._account_id

    @property
    def acc_num(self) -> int:
        return self._acc_num

    def discover_accounts(self) -> list:
        """Read-only account discovery (one session, many authorized accounts)."""
        return self._client.get_all_accounts()


def _nullable_float(value) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
