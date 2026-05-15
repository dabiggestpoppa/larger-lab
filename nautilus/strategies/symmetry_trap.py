"""
Symmetry Trap Strategy — CEREBUS FX Distribution Symmetry Trap
==============================================================
Implements the Distribution Symmetry Trap from the CEREBUS FX v4.0 manual
(Part 15, Pages 141-143) for Nautilus Trader backtesting.

THREE-LAYER EXECUTION MODEL (per manual):
  Layer 1 — BIAS LOCK: First M5 close outside Asian Range band sets direction
  Layer 2 — ATOMIC ENTRY: Impulse candle in bias direction + opposite close pullback
  Layer 3 — DISTRIBUTION TARGETS: -25% / -50% / -100% of Asian Range

SESSION TIMING (per manual):
  Asian Range: 7PM - 3AM EST (19:00-03:00 UTC) — constraint deficit measurement
  Bias Window: 3AM - 12PM EST (08:00-17:00 UTC) — bias lock + entry window
  Hard Exit: 12:00 PM EST (17:00 UTC) — close ALL

TIER CLASSIFICATION (per manual, page 140):
  T1: Asian Range < 20 pips  | Atomic Unit = 10p
  T2: Asian Range 20-30 pips | Atomic Unit = 12p
  T3: Asian Range 30-45 pips | Atomic Unit = 15p
  NO-GO: Asian Range > 45 pips

POSITION MANAGEMENT (per manual):
  T25 (-25% AR): Close 50% of position, move SL to breakeven
  T50 (-50% AR): Close 40% of position
  T100 (-100% AR): Close remaining 10% runner
  SL: M5 close back inside Asian band (81.2% rule — NOT wicks, CLOSES only)

RISK MANAGEMENT (per manual):
  Risk per trade: 0.25% equity
  Max daily loss: 1.0% (4 trades x 0.25%)
  SL distance: Atomic Unit (tier-specific)

Author: Quant Lab — based on CEREBUS FX v4.0 manual
"""
from decimal import Decimal
from datetime import datetime, timezone

from nautilus_trader.core.message import Event
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.events import OrderFilled
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.trading.strategy import Strategy, StrategyConfig

from ..config import (
    ASIAN_SESSION_END_UTC,
    ASIAN_SESSION_START_UTC,
    DAILY_LOSS_LIMIT_PCT,
    HARD_EXIT_HOUR_UTC,
    TIER_CONFIG,
)


class SymmetryTrapConfig(StrategyConfig, frozen=True):
    """Configuration for Symmetry Trap strategy."""

    instrument_id: InstrumentId = None
    bar_type: BarType = None
    # Risk management (per manual: 0.25% per trade, 1.0% max daily)
    initial_capital: Decimal = Decimal("100000")
    risk_per_trade_pct: Decimal = Decimal("0.0025")  # 0.25%
    max_daily_loss_pct: Decimal = Decimal("0.01")  # 1.0%
    # Strategy params
    tier: str = "T2"
    # Session timing (per manual: 7PM-3AM EST = 19:00-03:00 UTC)
    asian_session_start_utc: int = ASIAN_SESSION_START_UTC  # 19 (7PM EST)
    asian_session_end_utc: int = ASIAN_SESSION_END_UTC      # 3 (3AM EST)
    bias_window_start_utc: int = 8   # 3AM EST
    bias_window_end_utc: int = 17    # 12PM EST (hard exit)


class SymmetryTrapStrategy(Strategy):
    """
    Distribution Symmetry Trap — CEREBUS FX v4.0 (Part 15, Pages 141-143)

    Three-Layer Model:
    1. BIAS LOCK: First M5 close outside Asian Range sets session direction
    2. ATOMIC ENTRY: Impulse (body >= Atomic Unit x 0.5) + opposite close pullback
    3. DISTRIBUTION TARGETS: -25% / -50% / -100% of Asian Range from band edge

    Exit Rules:
    - T25: Close 50%, move SL to breakeven
    - T50: Close 40%
    - T100: Close remaining 10%
    - SL: M5 close back inside Asian band (81.2% rule)
    - Hard Exit: 12:00 PM EST (17:00 UTC)
    """

    def __init__(self, config: SymmetryTrapConfig):
        super().__init__(config)
        self.instrument_id = config.instrument_id
        if isinstance(config.bar_type, str):
            self.bar_type = BarType.from_str(config.bar_type)
        else:
            self.bar_type = config.bar_type
        self.tier_name = config.tier
        self.tier_config = TIER_CONFIG[config.tier]

        # Session timing
        self.asian_start = config.asian_session_start_utc
        self.asian_end = config.asian_session_end_utc
        self.bias_start = config.bias_window_start_utc
        self.bias_end = config.bias_window_end_utc

        # Risk management (per manual)
        self.initial_capital = config.initial_capital
        self.risk_per_trade = float(config.risk_per_trade_pct)
        self.max_daily_loss = float(config.max_daily_loss_pct)

        # Session state — Asian Range measurement
        self.asian_high: float = 0.0
        self.asian_low: float = 0.0
        self.asian_range: float = 0.0
        self.asian_range_measured: bool = False

        # Layer 1: Bias Lock state
        self.bias_locked: bool = False
        self.daily_direction: int = 0  # +1 = LONG, -1 = SHORT
        self.bias_bar_edge: float = 0.0

        # Layer 2: Atomic Entry state
        self.entry_taken: bool = False
        self.entry_price: float = 0.0
        self.impulse_seen: bool = False
        self.impulse_high: float = 0.0
        self.impulse_low: float = 0.0

        # Layer 3: Position management
        self.position_open: bool = False
        self.position_side: int = 0
        self.t25_hit: bool = False
        self.t50_hit: bool = False
        self.sl_moved_to_breakeven: bool = False

        # Daily tracking
        self.daily_pnl: float = 0.0
        self.trades_today: int = 0
        self.daily_loss: float = 0.0
        self.hard_exit_triggered: bool = False

        # Previous bar tracking (for pullback detection)
        self.prev_bar_open: float = 0.0
        self.prev_bar_close: float = 0.0
        self.prev_bar_high: float = 0.0
        self.prev_bar_low: float = 0.0
        self.prev_bar_is_green: bool = False
        self.has_prev_bar: bool = False

    def on_start(self):
        """Called when strategy starts."""
        self.subscribe_bars(self.bar_type)
        self.log.info(
            f"Symmetry Trap (Distribution) started | Tier: {self.tier_name} | "
            f"Instrument: {self.instrument_id} | "
            f"Risk/trade: {self.risk_per_trade:.2%} | "
            f"Max daily loss: {self.max_daily_loss:.2%}"
        )

    def on_bar(self, bar: Bar):
        """Main strategy logic on each bar — three-layer execution."""
        bar_time = bar.ts_event
        dt_utc = datetime.fromtimestamp(bar_time / 1e9, tz=timezone.utc)
        hour_utc = dt_utc.hour

        bar_open = float(bar.open)
        bar_close = float(bar.close)
        bar_high = float(bar.high)
        bar_low = float(bar.low)
        is_green = bar_close > bar_open

        # ── New day reset (after 18:00 UTC = 1PM EST) ───────────
        if hour_utc >= 18 and not self.asian_range_measured:
            self._reset_daily_state()

        # ── Step 1: Measure Asian Range (19:00-03:00 UTC) ───────
        if self._is_asian_session(hour_utc):
            self._measure_asian_range(bar)
            self._store_prev_bar(bar_open, bar_close, bar_high, bar_low, is_green)
            return

        # ── Step 2: Hard exit at 12:00 PM EST (17:00 UTC) ──────
        if hour_utc >= 17 and not self.hard_exit_triggered:
            self._hard_exit_all("12:00 PM EST Hard Exit")
            self._store_prev_bar(bar_open, bar_close, bar_high, bar_low, is_green)
            return

        # ── Step 3: Check SL (M5 close back inside Asian band) ──
        if self.position_open and not self.hard_exit_triggered:
            if self._check_sl_violation(bar):
                self._close_position("SL: M5 close back inside Asian band (81.2% rule)")
                self._store_prev_bar(bar_open, bar_close, bar_high, bar_low, is_green)
                return

        # ── Step 4: Check targets ────────────────────────────────
        if self.position_open and not self.hard_exit_triggered:
            self._check_targets(bar)

        # ── Step 5: Bias Window (08:00-17:00 UTC) ──────────────
        if self.bias_start <= hour_utc < self.bias_end:
            if not self.asian_range_measured or self.asian_range == 0:
                self._store_prev_bar(bar_open, bar_close, bar_high, bar_low, is_green)
                return

            # Layer 1: BIAS LOCK — first M5 close outside Asian band
            if not self.bias_locked:
                self._check_bias_lock(bar)

            # Layer 2: ATOMIC ENTRY — impulse + opposite close pullback
            elif not self.entry_taken and self.daily_direction != 0:
                self._check_atomic_entry(bar)

        # Store previous bar for pullback detection
        self._store_prev_bar(bar_open, bar_close, bar_high, bar_low, is_green)

    def _is_asian_session(self, hour_utc: int) -> bool:
        """Check if current hour is within Asian session (19:00-03:00 UTC)."""
        return hour_utc >= self.asian_start or hour_utc < self.asian_end

    def _measure_asian_range(self, bar: Bar):
        """Track Asian session high/low for constraint deficit."""
        if not self.asian_range_measured:
            self.asian_high = float(bar.high)
            self.asian_low = float(bar.low)
            self.asian_range_measured = True
        else:
            self.asian_high = max(self.asian_high, float(bar.high))
            self.asian_low = min(self.asian_low, float(bar.low))

        if self.asian_high > self.asian_low:
            self.asian_range = self.asian_high - self.asian_low

    def _reset_daily_state(self):
        """Reset all state for a new trading day."""
        self.asian_high = 0.0
        self.asian_low = 0.0
        self.asian_range = 0.0
        self.asian_range_measured = False
        self.bias_locked = False
        self.daily_direction = 0
        self.bias_bar_edge = 0.0
        self.entry_taken = False
        self.entry_price = 0.0
        self.impulse_seen = False
        self.impulse_high = 0.0
        self.impulse_low = 0.0
        self.position_open = False
        self.position_side = 0
        self.t25_hit = False
        self.t50_hit = False
        self.sl_moved_to_breakeven = False
        self.daily_pnl = 0.0
        self.trades_today = 0
        self.daily_loss = 0.0
        self.hard_exit_triggered = False
        self.has_prev_bar = False

    def _store_prev_bar(self, o, c, h, l, is_green):
        """Store previous bar data for pullback detection."""
        self.prev_bar_open = o
        self.prev_bar_close = c
        self.prev_bar_high = h
        self.prev_bar_low = l
        self.prev_bar_is_green = is_green
        self.has_prev_bar = True

    def _get_atomic_unit(self) -> float:
        """Get Atomic Unit in price terms based on tier (per manual, page 140)."""
        tier = self._classify_tier()
        atomic_pips = TIER_CONFIG.get(tier, TIER_CONFIG["T2"])["atomic"]
        return atomic_pips * 0.0001

    def _classify_tier(self) -> str:
        """Classify current Asian range into tier (per manual, page 140)."""
        ar_pips = self.asian_range / 0.0001
        if ar_pips < 20:
            return "T1"
        elif ar_pips < 30:
            return "T2"
        elif ar_pips < 45:
            return "T3"
        return "NO_GO"

    def _check_bias_lock(self, bar: Bar):
        """
        Layer 1: BIAS LOCK
        First M5 close outside Asian band sets direction for entire session.
        Per manual: LONG bias if close > Asian High, SHORT if close < Asian Low.
        """
        close = float(bar.close)

        if close > self.asian_high:
            self.bias_locked = True
            self.daily_direction = 1
            self.bias_bar_edge = self.asian_high
            self.log.info(
                f"🔒 BIAS LOCK: LONG | Close {close:.5f} > Asian High {self.asian_high:.5f} | "
                f"AR: {self.asian_range / 0.0001:.1f}p"
            )
        elif close < self.asian_low:
            self.bias_locked = True
            self.daily_direction = -1
            self.bias_bar_edge = self.asian_low
            self.log.info(
                f"🔒 BIAS LOCK: SHORT | Close {close:.5f} < Asian Low {self.asian_low:.5f} | "
                f"AR: {self.asian_range / 0.0001:.1f}p"
            )

    def _check_atomic_entry(self, bar: Bar):
        """
        Layer 2: ATOMIC ENTRY
        Per manual (page 143):
        1. Wait for impulse candle in bias direction (body >= Atomic Unit x 0.5)
        2. Wait for NEXT candle to close OPPOSITE direction (pullback)
        3. Enter MARKET on pullback candle close
        """
        if not self.has_prev_bar:
            return

        atomic_unit = self._get_atomic_unit()
        impulse_threshold = atomic_unit * 0.5
        close = float(bar.close)
        is_green = close > float(bar.open)

        # Check for impulse candle in bias direction
        if not self.impulse_seen:
            if self.daily_direction > 0:  # LONG bias
                if self.prev_bar_is_green and abs(self.prev_bar_close - self.prev_bar_open) >= impulse_threshold:
                    self.impulse_seen = True
                    self.impulse_high = self.prev_bar_high
                    self.impulse_low = self.prev_bar_low
                    self.log.info(
                        f"⚡ IMPULSE (LONG): body={abs(self.prev_bar_close - self.prev_bar_open) / 0.0001:.1f}p >= "
                        f"threshold={impulse_threshold / 0.0001:.1f}p"
                    )
            else:  # SHORT bias
                if not self.prev_bar_is_green and abs(self.prev_bar_close - self.prev_bar_open) >= impulse_threshold:
                    self.impulse_seen = True
                    self.impulse_high = self.prev_bar_high
                    self.impulse_low = self.prev_bar_low
                    self.log.info(
                        f"⚡ IMPULSE (SHORT): body={abs(self.prev_bar_close - self.prev_bar_open) / 0.0001:.1f}p >= "
                        f"threshold={impulse_threshold / 0.0001:.1f}p"
                    )
            return

        # After impulse, wait for opposite close pullback
        if self.daily_direction > 0:  # LONG bias
            if not is_green:  # Pullback = red candle
                self._enter_position(close, "ATOMIC_ENTRY_LONG")
        else:  # SHORT bias
            if is_green:  # Pullback = green candle
                self._enter_position(close, "ATOMIC_ENTRY_SHORT")

    def _enter_position(self, price: float, signal_type: str):
        """Enter a market position."""
        if self.daily_loss >= self.max_daily_loss:
            self.log.warning(f"Daily loss limit reached ({self.daily_loss:.2%}) — skipping entry")
            return

        # Get equity from portfolio
        try:
            equity = float(self.cache.equity())
        except AttributeError:
            # Fallback: use account balance from portfolio
            try:
                account = self.cache.account_for_venue(self.instrument_id.venue)
                equity = float(account.balance().total) if account else float(self.initial_capital)
            except Exception:
                equity = float(self.initial_capital)
        if equity <= 0:
            return

        atomic_unit = self._get_atomic_unit()
        risk_amount = equity * self.risk_per_trade
        pip_value = 10.0

        atomic_pips = atomic_unit / 0.0001
        size = risk_amount / (atomic_pips * pip_value)
        size = max(size, 1000)
        size = Decimal(str(int(size / 1000) * 1000))

        order_side = OrderSide.BUY if self.daily_direction > 0 else OrderSide.SELL

        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=order_side,
            quantity=Quantity(size, 0),
            time_in_force=TimeInForce.IOC,
        )
        self.submit_order(order)

        self.entry_taken = True
        self.entry_price = price
        self.position_open = True
        self.position_side = self.daily_direction
        self.trades_today += 1

        t25 = self._calc_target(0.25)
        t50 = self._calc_target(0.50)
        t100 = self._calc_target(1.00)

        self.log.info(
            f"📊 {signal_type} | {'BUY' if order_side == OrderSide.BUY else 'SELL'} "
            f"| Price: {price:.5f} | Size: {size} | "
            f"T25: {t25:.5f} | T50: {t50:.5f} | T100: {t100:.5f} | "
            f"Risk: {self.risk_per_trade:.2%}"
        )

    def _calc_target(self, pct: float) -> float:
        """Calculate distribution target as % of Asian Range from band edge."""
        if self.daily_direction > 0:  # LONG
            return self.bias_bar_edge - (self.asian_range * pct)
        else:  # SHORT
            return self.bias_bar_edge + (self.asian_range * pct)

    def _check_targets(self, bar: Bar):
        """Check and manage distribution targets (Layer 3)."""
        if not self.position_open:
            return

        close = float(bar.close)

        if self.daily_direction > 0:  # LONG
            if not self.t25_hit and close <= self._calc_target(0.25):
                self.t25_hit = True
                self.sl_moved_to_breakeven = True
                self._partial_close(0.50, "T25 (-25% AR)")
            elif not self.t50_hit and close <= self._calc_target(0.50):
                self.t50_hit = True
                self._partial_close(0.40, "T50 (-50% AR)")
            elif close <= self._calc_target(1.00):
                self._close_position("T100 (-100% AR)")
        else:  # SHORT
            if not self.t25_hit and close >= self._calc_target(0.25):
                self.t25_hit = True
                self.sl_moved_to_breakeven = True
                self._partial_close(0.50, "T25 (-25% AR)")
            elif not self.t50_hit and close >= self._calc_target(0.50):
                self.t50_hit = True
                self._partial_close(0.40, "T50 (-50% AR)")
            elif close >= self._calc_target(1.00):
                self._close_position("T100 (-100% AR)")

    def _check_sl_violation(self, bar: Bar) -> bool:
        """
        Check stop loss: M5 close back inside Asian band (81.2% rule).
        Per manual: NOT wicks, CLOSES only.
        """
        close = float(bar.close)

        if self.sl_moved_to_breakeven:
            if self.daily_direction > 0:
                return close < self.entry_price
            else:
                return close > self.entry_price
        else:
            if self.daily_direction > 0:
                return close < self.asian_high
            else:
                return close > self.asian_low

    def _partial_close(self, pct: float, reason: str):
        """Partial close of position."""
        positions = self.cache.positions_open(instrument_id=self.instrument_id)
        for position in positions:
            if position.quantity <= 0:
                continue
            close_qty = Decimal(str(int(float(position.quantity) * pct / 1000) * 1000))
            if close_qty <= 0:
                continue
            close_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=close_side,
                quantity=Quantity(close_qty, 0),
                time_in_force=TimeInForce.IOC,
            )
            self.submit_order(order)
            self.log.info(f"📈 {reason}: Closed {close_qty} ({pct:.0%})")

    def _close_position(self, reason: str):
        """Close entire position."""
        positions = self.cache.positions_open(instrument_id=self.instrument_id)
        for position in positions:
            if position.quantity <= 0:
                continue
            close_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=close_side,
                quantity=Quantity.from_str(str(abs(position.quantity))),
                time_in_force=TimeInForce.IOC,
            )
            self.submit_order(order)
            self.log.info(f"🔴 CLOSE: {reason} | Position: {position.id}")
        self.position_open = False

    def _hard_exit_all(self, reason: str):
        """Close all positions — hard exit rule."""
        self.hard_exit_triggered = True
        positions = self.cache.positions_open(instrument_id=self.instrument_id)
        for position in positions:
            if position.quantity <= 0:
                continue
            close_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=close_side,
                quantity=Quantity.from_str(str(abs(position.quantity))),
                time_in_force=TimeInForce.IOC,
            )
            self.submit_order(order)
            self.log.warning(f"🔴 HARD EXIT: {reason} | Position: {position.id}")
        self.position_open = False

    def on_event(self, event: Event):
        """Handle events."""
        if isinstance(event, OrderFilled):
            self.log.debug(f"Fill: {event}")

    def on_stop(self):
        """Called when strategy stops."""
        self._hard_exit_all("Strategy stopped")
        self.log.info(
            f"Symmetry Trap stopped | Trades: {self.trades_today} | "
            f"Daily PnL: {self.daily_pnl:.2f}"
        )