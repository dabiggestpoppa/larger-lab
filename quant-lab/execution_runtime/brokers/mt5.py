"""QL-EXEC-R2 — MT5BrokerSession.

A concrete, broker-neutral-in-contract implementation of the generic
BrokerSession interface over MetaTrader5. Dependency-injected: the real
MetaTrader5 module is passed in (lazily), so tests inject FakeMT5 and never
touch a terminal.

This module is the TRANSPORT layer only. It performs NO strategy sizing, NO
Capital Routing math, and does NOT import tb_live / tb_forward / triangular
strategy code.
"""  # noqa: E501
from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Optional

from ..enums import (
    BrokerErrorCategory,
    ClockStatus,
    Environment,
    FillPolicy,
    HedgingNetting,
    OrderSide,
    SlippageUnit,
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

# ─── STANDARD MT5 ENUM VALUES (adapter-internal; never leak to generic) ───
# These are the MetaTrader5 C enum values. The generic contract must never
# carry these; they exist only inside this adapter to build MT5 requests.
_ACTION_DEAL = 1
_ACTION_REMOVE = 8
_ORDER_TYPE_BUY = 0
_ORDER_TYPE_SELL = 1
_POSITION_TYPE_BUY = 0
_POSITION_TYPE_SELL = 1

_TIMEFRAME = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 16385}

# TB-R6 validated observation: THIS broker build accepts ``type_filling``
# values permuted from the standard MT5 enum. Standard MT5 constants are
# FOK=0 / IOC=1 / RETURN=2; the validated TB path observed FOK=1 / IOC=2 /
# RETURN=0 via order_check probing. This is a BROKER-SPECIFIC observation, kept
# injectable rather than universal. The generic FillPolicy enum is untouched.
_DEFAULT_FILL_POLICY_CODES = {
    FillPolicy.FILL_OR_KILL: 1,
    FillPolicy.IMMEDIATE_OR_CANCEL: 2,
    FillPolicy.RETURN_OR_PARTIAL: 0,
}
# filling_mode bitfield (broker-observed): bit value -> generic FillPolicy.
_DEFAULT_FILL_POLICY_BITS = {
    1: FillPolicy.FILL_OR_KILL,
    2: FillPolicy.IMMEDIATE_OR_CANCEL,
    4: FillPolicy.RETURN_OR_PARTIAL,
}

# Server-clock plausibility gate (from TB's validated calibration): only
# |offset| < 12h is accepted as a real server timezone. Stale ticks retain the
# previous calibration.
_MAX_CLOCK_OFFSET_SECONDS = 12 * 3600

# TB-R6 discovery: this broker's Python API returns None from order_check for
# request comments >= 30 chars. Comments are therefore bounded to 29 chars.
_MAX_COMMENT_LENGTH = 29

_TRADE_MODE_ENV = {0: Environment.DEMO, 1: Environment.CONTEST, 2: Environment.REAL}


def is_success_retcode(retcode: Any) -> bool:
    """TB-R6 validated success retcodes: 0 and TRADE_RETCODE_DONE (10009)."""
    if retcode is None:
        return False
    try:
        return int(retcode) == 0 or int(retcode) == 10009
    except (TypeError, ValueError):
        return False


def normalize_trade_mode(trade_mode: Any) -> Environment:
    """MT5 trade_mode int (0/1/2) -> generic Environment. Unknown -> UNKNOWN."""
    try:
        return _TRADE_MODE_ENV.get(int(trade_mode), Environment.UNKNOWN)
    except (TypeError, ValueError):
        return Environment.UNKNOWN


def normalize_fill_policy_bits(
    filling_mode: Any, bit_map: Optional[dict] = None
) -> tuple[FillPolicy, ...]:
    """Normalize symbol filling_mode bits into generic FillPolicy values.

    The declared bits are a DECLARED capability, not a guarantee of accepted
    behavior (TB R6 showed declared and accepted modes can differ).
    """
    mapping = bit_map or _DEFAULT_FILL_POLICY_BITS
    try:
        bits = int(filling_mode)
    except (TypeError, ValueError):
        return ()
    policies = []
    for bit, policy in sorted(mapping.items()):
        if bits & bit:
            policies.append(policy)
    return tuple(policies)


def build_mt5_order_request(
    intent: OrderIntent,
    symbol_info: Optional[SymbolInfo] = None,
    tick: Optional[Tick] = None,
    fill_code: Optional[int] = None,
    *,
    action: int = _ACTION_DEAL,
    max_comment_length: int = _MAX_COMMENT_LENGTH,
    position_ticket: Optional[int] = None,
) -> Optional[dict]:
    """Pure MT5 order-request construction. No scattered dict creation.

    Market side mapping follows the validated TB semantics: BUY at ASK,
    SELL at BID (unless an explicit reference price is supplied). The request
    never invents a strategy notional or a universal slippage default.
    """
    if intent.volume <= 0:
        return None
    is_buy = intent.side is OrderSide.BUY
    order_type = _ORDER_TYPE_BUY if is_buy else _ORDER_TYPE_SELL

    if intent.reference_price is not None:
        price = float(intent.reference_price)
    elif tick is not None:
        price = tick.ask if is_buy else tick.bid
    else:
        price = 0.0

    deviation = _slippage_deviation(intent, symbol_info)
    comment = (intent.ownership_tag or "")[:max_comment_length]

    request: dict[str, Any] = {
        "action": action,
        "symbol": intent.symbol,
        "volume": float(intent.volume),
        "type": order_type,
        "price": price,
        "deviation": deviation,
        "magic": int(intent.broker_magic),
        "comment": comment,
    }
    if fill_code is not None:
        request["type_filling"] = int(fill_code)
    if position_ticket is not None:
        request["position"] = int(position_ticket)
    return request


def _slippage_deviation(intent: OrderIntent, symbol_info: Optional[SymbolInfo]) -> int:
    """Map a unit-explicit generic slippage constraint to MT5 deviation points.

    POINTS map directly. PRICE is converted via symbol point. No naked number
    and no universal 20-point default (that is a TB execution choice).
    """
    if intent.slippage_constraint is None:
        return 0
    if intent.slippage_unit is SlippageUnit.POINTS:
        return int(intent.slippage_constraint)
    if (
        intent.slippage_unit is SlippageUnit.PRICE
        and symbol_info is not None
        and symbol_info.point > 0
    ):
        return int(round(intent.slippage_constraint / symbol_info.point))
    return 0


class MT5BrokerSession(BrokerSession):
    """Dependency-injected MetaTrader5 broker session.

    ``mt5_module`` may be the real MetaTrader5 module (future runtime) or a
    FakeMT5 (tests). It is never imported hard-wired here.
    """

    def __init__(
        self,
        mt5_module: Any = None,
        *,
        fill_policy_codes: Optional[dict] = None,
        fill_policy_bits: Optional[dict] = None,
        max_comment_length: int = _MAX_COMMENT_LENGTH,
        clock_probe_symbol: str = "",
    ) -> None:
        self._mt5 = mt5_module
        self._connected = False
        self._fill_policy_codes = dict(fill_policy_codes or _DEFAULT_FILL_POLICY_CODES)
        self._fill_policy_bits = dict(fill_policy_bits or _DEFAULT_FILL_POLICY_BITS)
        self._max_comment_length = max_comment_length
        self._clock_probe_symbol = clock_probe_symbol
        self._server_offset_s: Optional[float] = None
        self._last_error_category: Optional[BrokerErrorCategory] = None

    # ── transport lifecycle ───────────────────────────────────────────────

    def connect(self) -> bool:
        """Attach to an externally authenticated terminal session (no creds)."""
        if self._mt5 is None:
            self._connected = False
            self._last_error_category = BrokerErrorCategory.NOT_CONNECTED
            return False
        try:
            if not bool(self._mt5.initialize()):
                self._connected = False
                self._last_error_category = BrokerErrorCategory.TRANSPORT_ERROR
                return False
            self._connected = self._mt5.terminal_info() is not None
            if not self._connected:
                self._last_error_category = BrokerErrorCategory.NOT_CONNECTED
            return self._connected
        except Exception:  # noqa: BLE001 - normalize any raw transport error
            self._connected = False
            self._last_error_category = BrokerErrorCategory.TRANSPORT_ERROR
            return False

    def disconnect(self) -> None:
        """Idempotent shutdown. Never closes positions."""
        if self._mt5 is not None:
            try:
                self._mt5.shutdown()
            except Exception:  # noqa: BLE001
                pass
        self._connected = False

    def health(self) -> dict:
        return {
            "connected": self._connected,
            "clock_calibrated": self._server_offset_s is not None,
            "last_error_category": (
                self._last_error_category.value if self._last_error_category else None
            ),
        }

    # ── identity / account / clock ────────────────────────────────────────

    def _terminal_info(self) -> Any:
        if self._mt5 is None or not self._connected:
            return None
        try:
            return self._mt5.terminal_info()
        except Exception:  # noqa: BLE001
            return None

    def _account_info(self) -> Any:
        if self._mt5 is None or not self._connected:
            return None
        try:
            return self._mt5.account_info()
        except Exception:  # noqa: BLE001
            return None

    def identity(self) -> BrokerIdentity:
        ai = self._account_info()
        ti = self._terminal_info()
        env = normalize_trade_mode(getattr(ai, "trade_mode", None))
        return BrokerIdentity(
            broker_company=str(getattr(ti, "company", "") or ""),
            server=str(getattr(ai, "server", "") or ""),
            account_identifier=str(getattr(ai, "login", "") or ""),
            environment=env,
            currency=str(getattr(ai, "currency", "") or ""),
            account_mode=env.value,
            hedging_netting=HedgingNetting.UNKNOWN,
            trade_allowed=bool(getattr(ai, "trade_allowed", True)),
            terminal_trade_allowed=bool(getattr(ti, "trade_allowed", True)),
            tradeapi_disabled=bool(getattr(ti, "tradeapi_disabled", False)),
        )

    def account_state(self) -> AccountState:
        ai = self._account_info()
        if ai is None:
            return AccountState()
        return AccountState(
            currency=str(getattr(ai, "currency", "") or ""),
            balance=_opt_float(ai, "balance"),
            equity=_opt_float(ai, "equity"),
            margin=_opt_float(ai, "margin"),
            free_margin=_opt_float(ai, "free_margin"),
            buying_power=None,  # MT5 free margin is NOT generic buying power
            account_mode=normalize_trade_mode(getattr(ai, "trade_mode", None)).value,
        )

    def clock_state(self, symbol: Optional[str] = None) -> BrokerClockState:
        probe = symbol or self._clock_probe_symbol
        offset = self._calibrate_clock(probe) if probe else self._server_offset_s
        if offset is None:
            return BrokerClockState(
                source_clock_name="MT5_SERVER",
                source_offset_seconds=0.0,
                calibrated=False,
                status=ClockStatus.UNCALIBRATED,
                observed_at_utc=utcnow_iso(),
                failure_reason="no fresh tick available",
            )
        return BrokerClockState(
            source_clock_name="MT5_SERVER",
            source_offset_seconds=offset,
            calibrated=True,
            status=ClockStatus.CALIBRATED,
            observed_at_utc=utcnow_iso(),
        )

    def _calibrate_clock(self, symbol: str) -> Optional[float]:
        """Measure source-minus-UTC offset from a live tick (12h plausibility).

        A stale/missing tick retains the previous valid calibration; it never
        silently mixes source and local clocks.
        """
        if self._mt5 is None or not self._connected:
            return self._server_offset_s
        try:
            tk = self._mt5.symbol_info_tick(symbol)
        except Exception:  # noqa: BLE001
            return self._server_offset_s
        if tk is None:
            return self._server_offset_s
        off = float(tk.time) - time.time()
        if abs(off) < _MAX_CLOCK_OFFSET_SECONDS:
            self._server_offset_s = off
        return self._server_offset_s

    # ── symbol ────────────────────────────────────────────────────────────

    def symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        if self._mt5 is None or not self._connected:
            return None
        try:
            si = self._mt5.symbol_info(symbol)
        except Exception:  # noqa: BLE001
            return None
        if si is None:
            return None
        return SymbolInfo(
            symbol=symbol,
            digits=int(getattr(si, "digits", 0) or 0),
            point=float(getattr(si, "point", 0.0) or 0.0),
            contract_size=float(getattr(si, "trade_contract_size", 0.0) or 0.0),
            volume_min=float(getattr(si, "volume_min", 0.0) or 0.0),
            volume_max=float(getattr(si, "volume_max", 0.0) or 0.0),
            volume_step=float(getattr(si, "volume_step", 0.0) or 0.0),
            visible=bool(getattr(si, "visible", False)),
            trade_mode=normalize_trade_mode(getattr(si, "trade_mode", None)).value,
            trade_tick_size=float(getattr(si, "trade_tick_size", 0.0) or 0.0),
            trade_tick_value=float(getattr(si, "trade_tick_value", 0.0) or 0.0),
            declared_fill_policies=normalize_fill_policy_bits(
                getattr(si, "filling_mode", 0), self._fill_policy_bits
            ),
        )

    def ensure_symbol(self, symbol: str) -> bool:
        if self._mt5 is None or not self._connected:
            return False
        try:
            return bool(self._mt5.symbol_select(symbol, True))
        except Exception:  # noqa: BLE001
            return False

    def probe_fill_policies(self, symbol: str) -> Optional[FillPolicy]:
        """Discover the ACTUAL accepted fill policy via order_check.

        Mirrors TB's validated probe: try FOK -> IOC -> RETURN and return the
        first mode that order_check accepts. Declared filling_mode bits are NOT
        trusted blindly.
        """
        info = self.symbol_info(symbol)
        tick = self.tick(symbol)
        if info is None or tick is None or not tick.valid:
            return None
        order = (FillPolicy.FILL_OR_KILL, FillPolicy.IMMEDIATE_OR_CANCEL, FillPolicy.RETURN_OR_PARTIAL)
        for policy in order:
            code = self._fill_policy_codes.get(policy)
            if code is None:
                continue
            req = build_mt5_order_request(
                OrderIntent(
                    intent_id=f"probe:{symbol}",
                    account_id="probe",
                    symbol=symbol,
                    side=OrderSide.BUY,
                    volume=info.volume_min if info.volume_min > 0 else 0.01,
                    reference_price=tick.ask,
                    fill_policy=policy,
                    slippage_constraint=None,
                ),
                info,
                tick,
                code,
                max_comment_length=self._max_comment_length,
            )
            if req is None:
                continue
            raw = self._safe_order_check(req)
            ret = None if raw is None else getattr(raw, "retcode", None)
            if is_success_retcode(ret):
                return policy
        return None

    # ── market data ───────────────────────────────────────────────────────

    def tick(self, symbol: str) -> Optional[Tick]:
        if self._mt5 is None or not self._connected:
            return None
        try:
            raw = self._mt5.symbol_info_tick(symbol)
        except Exception:  # noqa: BLE001
            return None
        if raw is None:
            return None
        bid = float(getattr(raw, "bid", 0.0) or 0.0)
        ask = float(getattr(raw, "ask", 0.0) or 0.0)
        valid = bid > 0 and ask > 0 and ask >= bid
        return Tick(
            symbol=symbol,
            bid=bid,
            ask=ask,
            time=float(getattr(raw, "time", 0.0) or 0.0),
            observed_at_utc=time.time(),
            source_clock_name="MT5_SERVER",
            offset_seconds=self._server_offset_s if self._server_offset_s is not None else 0.0,
            valid=valid,
        )

    def bars(self, symbol: str, timeframe: str = "M5", count: int = 500) -> Optional[list[Bar]]:
        if self._mt5 is None or not self._connected:
            return None
        tf = _TIMEFRAME.get(timeframe)
        if tf is None:
            return None
        try:
            raw = self._mt5.copy_rates_from_pos(symbol, tf, 0, count)
        except Exception:  # noqa: BLE001
            return None
        if raw is None or len(raw) == 0:
            return None
        bars = [self._normalize_bar(symbol, r) for r in raw]
        bars.sort(key=lambda b: b.time)
        return bars

    def _normalize_bar(self, symbol: str, raw: Any) -> Bar:
        def field(name: str, default: Any = 0.0) -> Any:
            if hasattr(raw, "get"):
                return raw.get(name, default)
            try:
                return raw[name]
            except (KeyError, IndexError, TypeError):
                return getattr(raw, name, default)

        real_volume = field("real_volume", 0.0)
        tick_volume = field("tick_volume", 0.0)
        volume = float(real_volume if real_volume else tick_volume)
        return Bar(
            symbol=symbol,
            time=float(field("time", 0.0)),  # RAW source bar-open time, preserved
            open=float(field("open", 0.0)),
            high=float(field("high", 0.0)),
            low=float(field("low", 0.0)),
            close=float(field("close", 0.0)),
            volume=volume,
            observed_at_utc=time.time(),
            source_clock_name="MT5_SERVER",
            offset_seconds=self._server_offset_s if self._server_offset_s is not None else 0.0,
        )

    # ── broker state ──────────────────────────────────────────────────────

    def positions(self) -> list[Position]:
        raw = self._safe_positions()
        if not raw:
            return []
        out = []
        for p in raw:
            ptype = int(getattr(p, "type", -1))
            side = "LONG" if ptype == _POSITION_TYPE_BUY else ("SHORT" if ptype == _POSITION_TYPE_SELL else "")
            out.append(
                Position(
                    position_id=str(getattr(p, "ticket", "") or ""),
                    symbol=str(getattr(p, "symbol", "") or ""),
                    volume=float(getattr(p, "volume", 0.0) or 0.0),
                    side=side,
                    price_open=float(getattr(p, "price_open", 0.0) or 0.0),
                    current_price=_opt_float(p, "price_current"),
                    magic=int(getattr(p, "magic", 0) or 0),
                    ownership_tag=str(getattr(p, "comment", "") or ""),
                    time=float(getattr(p, "time", 0.0) or 0.0),
                    profit=_opt_float(p, "profit"),
                )
            )
        return out

    def orders(self) -> list[Order]:
        raw = self._safe_orders()
        if not raw:
            return []
        return [
            Order(
                order_id=str(getattr(o, "ticket", "") or ""),
                symbol=str(getattr(o, "symbol", "") or ""),
                volume=float(getattr(o, "volume_current", 0.0) or 0.0),
                order_type=str(getattr(o, "type", "") or ""),
                magic=int(getattr(o, "magic", 0) or 0),
                ownership_tag=str(getattr(o, "comment", "") or ""),
                time=float(getattr(o, "time_setup", 0.0) or 0.0),
            )
            for o in raw
        ]

    def deals(self, start: float = 0.0, end: float = 0.0) -> list[Deal]:
        if self._mt5 is None or not self._connected:
            return []
        if end <= 0:
            end = time.time() + 3600.0
        if start <= 0:
            start = end - 6 * 3600.0
        try:
            raw = self._mt5.history_deals_get(
                datetime.utcfromtimestamp(start), datetime.utcfromtimestamp(end)
            )
        except Exception:  # noqa: BLE001
            return []
        if not raw:
            return []
        return [self._normalize_deal(d) for d in raw]

    def _normalize_deal(self, d: Any) -> Deal:
        return Deal(
            deal_id=str(getattr(d, "ticket", "") or ""),
            symbol=str(getattr(d, "symbol", "") or ""),
            volume=float(getattr(d, "volume", 0.0) or 0.0),
            price=float(getattr(d, "price", 0.0) or 0.0),
            entry=bool(getattr(d, "entry", True)),
            order_id=str(getattr(d, "order", "") or ""),
            position_id=str(getattr(d, "position_id", "") or ""),
            side="",
            magic=int(getattr(d, "magic", 0) or 0),
            ownership_tag=str(getattr(d, "comment", "") or ""),
            time=float(getattr(d, "time", 0.0) or 0.0),
            profit=_opt_float(d, "profit"),
            commission=_opt_float(d, "commission"),
            swap=_opt_float(d, "swap"),
            fee=_opt_float(d, "fee"),
        )

    # ── order lifecycle ───────────────────────────────────────────────────

    def order_check(self, intent: OrderIntent) -> CheckResult:
        req, fill_code, err = self._prepare_order(intent)
        if req is None:
            return CheckResult(ok=False, reason=err or "cannot build order request")
        raw = self._safe_order_check(req)
        retcode = None if raw is None else getattr(raw, "retcode", None)
        ok = is_success_retcode(retcode)
        return CheckResult(
            ok=ok,
            retcode=None if retcode is None else int(retcode),
            broker_message=str(getattr(raw, "comment", "") or "") if raw is not None else "",
            reason="" if ok else f"order_check failed (retcode={retcode})",
        )

    def submit_order(self, intent: OrderIntent) -> OrderResult:
        req, fill_code, err = self._prepare_order(intent)
        if req is None:
            return OrderResult(
                ok=False,
                reason=err or "cannot build order request",
                error_category=BrokerErrorCategory.INVALID_REQUEST,
            )
        raw = self._safe_order_send(req)
        retcode = None if raw is None else getattr(raw, "retcode", None)
        ok = is_success_retcode(retcode)
        order_id = ""
        if ok and raw is not None and getattr(raw, "order", None) is not None:
            order_id = str(getattr(raw, "order"))
        return OrderResult(
            ok=ok,
            broker_order_id=order_id,
            retcode=None if retcode is None else int(retcode),
            broker_message=str(getattr(raw, "comment", "") or "") if raw is not None else "",
            reason="" if ok else f"order rejected (retcode={retcode})",
            error_category=(
                BrokerErrorCategory.UNKNOWN_BROKER_ERROR
                if ok
                else BrokerErrorCategory.ORDER_REJECTED
            ),
        )

    def cancel_order(self, order_id: str) -> CancelResult:
        if self._mt5 is None or not self._connected:
            return CancelResult(ok=False, reason="not connected")
        req = {"action": _ACTION_REMOVE, "order": int(order_id)}
        raw = self._safe_order_send(req)
        retcode = None if raw is None else getattr(raw, "retcode", None)
        ok = is_success_retcode(retcode)
        return CancelResult(
            ok=ok,
            reason="" if ok else f"cancel rejected (retcode={retcode})",
        )

    def close_position(self, position_id: str, reason: str = "") -> CloseResult:
        pos = next((p for p in self.positions() if p.position_id == position_id), None)
        if pos is None:
            return CloseResult(ok=False, reason="position not found")
        tick = self.tick(pos.symbol)
        if tick is None or not tick.valid:
            return CloseResult(ok=False, reason="no valid tick for position symbol")
        side = OrderSide.SELL if pos.side == "LONG" else OrderSide.BUY
        price = tick.bid if side is OrderSide.SELL else tick.ask
        intent = OrderIntent(
            intent_id=f"close:{position_id}",
            account_id="",
            symbol=pos.symbol,
            side=side,
            volume=pos.volume,
            reference_price=price,
            broker_magic=pos.magic,
            ownership_tag=pos.ownership_tag,
        )
        req, fill_code, err = self._prepare_order(intent)
        if req is None:
            return CloseResult(ok=False, reason=err or "cannot build close request")
        req["position"] = int(position_id)
        raw = self._safe_order_send(req)
        retcode = None if raw is None else getattr(raw, "retcode", None)
        ok = is_success_retcode(retcode)
        return CloseResult(ok=ok, reason="" if ok else f"close rejected (retcode={retcode})")

    def reconcile_snapshot(self) -> BrokerSnapshot:
        return BrokerSnapshot(
            account_state=self.account_state(),
            positions=tuple(self.positions()),
            orders=tuple(self.orders()),
            deals=tuple(self.deals()),
        )

    # ── internal helpers ──────────────────────────────────────────────────

    def _prepare_order(
        self, intent: OrderIntent
    ) -> tuple[Optional[dict], Optional[int], str]:
        """Shared validation + request construction for order_check/send.

        Returns (request, fill_code, error). error is "" on success.
        """
        if self._mt5 is None or not self._connected:
            return None, None, "not connected"
        if intent.volume <= 0:
            return None, None, "zero quantity"
        info = self.symbol_info(intent.symbol)
        tick = self.tick(intent.symbol)
        fill_code = self._resolve_fill_code(intent, info)
        if fill_code is None:
            return None, None, f"unsupported fill policy: {intent.fill_policy.value}"
        req = build_mt5_order_request(
            intent,
            info,
            tick,
            fill_code,
            max_comment_length=self._max_comment_length,
        )
        if req is None:
            return None, None, "cannot build order request"
        return req, fill_code, ""

    def _resolve_fill_code(
        self, intent: OrderIntent, info: Optional[SymbolInfo]
    ) -> Optional[int]:
        policy = intent.fill_policy
        if policy in (FillPolicy.BROKER_DEFAULT, FillPolicy.UNKNOWN):
            resolved = self.probe_fill_policies(intent.symbol)
            if resolved is not None:
                return self._fill_policy_codes.get(resolved)
            if info is not None and info.declared_fill_policies:
                return self._fill_policy_codes.get(info.declared_fill_policies[0])
            return self._fill_policy_codes.get(FillPolicy.RETURN_OR_PARTIAL, 0)
        return self._fill_policy_codes.get(policy)

    def _safe_order_check(self, req: dict) -> Any:
        try:
            return self._mt5.order_check(req)
        except Exception:  # noqa: BLE001
            return None

    def _safe_order_send(self, req: dict) -> Any:
        try:
            return self._mt5.order_send(req)
        except Exception:  # noqa: BLE001
            return None

    def _safe_positions(self) -> list:
        if self._mt5 is None or not self._connected:
            return []
        try:
            raw = self._mt5.positions_get()
        except Exception:  # noqa: BLE001
            return []
        return list(raw) if raw else []

    def _safe_orders(self) -> list:
        if self._mt5 is None or not self._connected:
            return []
        try:
            raw = self._mt5.orders_get()
        except Exception:  # noqa: BLE001
            return []
        return list(raw) if raw else []


def _opt_float(obj: Any, name: str) -> Optional[float]:
    v = getattr(obj, name, None)
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
