"""
P90 Kinetic Strategy — Nautilus Trader Implementation
CEREBUS FX v4.0 P90 Kinetic Engine (Model A: All Variants)

Matches p90_engine.py P90Engine EXACTLY.

Reference: engines/p90_engine.py — P90Engine class, process_bar(), _calc_trade_params()

P90 Logic (Engine A — Kinetic, NOT Symmetry Trap, NOT DMR):
1.  Asian Session (7PM-3AM EST): Track Asian Range high/low
2.  P90 Detection Window (2AM-11AM EST):
    First M5 bar where body >= threshold AND close outside Asian Range = P90 signal
3.  Entry: IMMEDIATE on close of P90 candle (NO pullback, NO OCC)
4.  Direction: WITH P90 (momentum)
    - Bullish P90 (close > open) → BUY (LONG)
    - Bearish P90 (close < open) → SELL (SHORT)
5.  SL: 80% of P90 candle body from close (INITIAL), 168% (CASCADE)
6.  TP: +25% and +50% of Asian Range from entry (momentum, NOT mean reversion)
7.  CASCADE: 2nd/3rd P90 same direction within 120min. SL = 168% of NEW P90 body.
8.  EWS: Opposite P90 at target + boundary breach = EXIT only (NOT reversal entry)
9.  12PM EST: Hard state reset (session_active = False)
10. 5PM EST: Hard exit all positions
11. Max 1 trade per variant type per session

P90 vs DMR Key Differences:
| Aspect | DMR                  | P90                    |
|--------|----------------------|------------------------|
| Entry  | After DS pullback    | Immediate on P90 close |
| Dir    | AGAINST P90          | WITH P90 (momentum)    |
| SL     | 2.2x body (KS)       | 80%/168% body          |
| TP     | Activation level     | +25%/+50% of AR        |
"""
from decimal import Decimal
from typing import Optional

from nautilus_trader.common.enums import LogColor
from nautilus_trader.core.data import Data
from nautilus_trader.core.message import Event
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce, PositionSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.model.orders import MarketOrder, StopMarketOrder
from nautilus_trader.trading.strategy import Strategy, StrategyConfig


# ─── ALL configs imported from configs/asset_configs.py (single source of truth) ──
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'configs'))
from asset_configs import ASSET_CONFIGS, get_config

# Default P90 thresholds by EST hour (EUR/USD reference)
P90_THRESHOLDS = {
    2: 4.1, 3: 4.1, 4: 4.6, 5: 4.6, 6: 4.6,
    7: 5.9, 8: 5.9, 9: 6.2, 10: 6.2,
}

# Per-symbol P90 thresholds — derived from asset_configs p90_threshold
# Scale by hour relative to base threshold (EUR/USD ratio)
SYMBOL_P90 = {}
PIP_DIVISORS = {}

for _key, _cfg in ASSET_CONFIGS.items():
    _pip_val = _cfg["pip_value"]
    _divisor = 1.0 / _pip_val
    PIP_DIVISORS[_key] = _divisor
    # Add .PRO variant for FX majors
    if _cfg.get("pip_value") == 0.0001 and len(_key) == 6:
        PIP_DIVISORS[_key + ".PRO"] = _divisor
    # Build per-symbol P90 thresholds from p90_threshold
    _base = _cfg.get("p90_threshold", 4.6)
    _ratio = _base / 4.6  # scale relative to EUR/USD base
    SYMBOL_P90[_key] = {h: round(t * _ratio, 1) for h, t in P90_THRESHOLDS.items()}
    if _cfg.get("pip_value") == 0.0001 and len(_key) == 6:
        SYMBOL_P90[_key + ".PRO"] = SYMBOL_P90[_key]

# Ensure XAU/USD variants exist
for _alias in ["XAU/USD", "XAUUSD"]:
    if _alias not in PIP_DIVISORS:
        PIP_DIVISORS[_alias] = PIP_DIVISORS.get("XAUUSD", 10.0)
for _alias in ["BTC/USD", "BTCUSD"]:
    if _alias not in PIP_DIVISORS:
        PIP_DIVISORS[_alias] = PIP_DIVISORS.get("BTCUSD", 1.0)
for _alias in ["ETH/USD", "ETHUSD"]:
    if _alias not in PIP_DIVISORS:
        PIP_DIVISORS[_alias] = PIP_DIVISORS.get("ETHUSD", 1.0)

# Cascade P90 max time window (120 minutes)
CASCADE_WINDOW_MINUTES = 120


class P90Config(StrategyConfig, frozen=True):
    """Configuration for P90 Kinetic Strategy."""
    instrument_id: str = "EURUSD.PRO"
    bar_type: str = "EURUSD.PRO-5-MINUTE-LAST-EXTERNAL"
    lot_size: Decimal = Decimal("1000")
    magic_number: int = 20260530
    initial_sl_mult: float = 0.80     # SL = 80% of INITIAL P90 body
    cascade_sl_mult: float = 1.68     # SL = 168% of CASCADE P90 body
    tp1_ar_frac: float = 0.25         # TP1 = +25% of Asian Range
    tp2_ar_frac: float = 0.50         # TP2 = +50% of Asian Range
    cascade_window_min: int = 120     # Cascade window in minutes
    hard_exit_hour: int = 17          # 5PM EST — hard exit all positions
    state_reset_hour: int = 12        # 12PM EST — hard state reset
    est_offset: int = -5              # EST = UTC - 5
    max_initial_per_day: int = 1      # Max INITIAL trades per session
    max_cascade_per_day: int = 1      # Max CASCADE trades per session


class P90Strategy(Strategy):
    """
    P90 Kinetic Strategy — Nautilus Trader (Model A: All Variants)

    State machine per day:
    RESET → TRACK_ASIAN → LOCK_AR → SEARCH → IN_TRADE → (EXIT) → SEARCH

    Three variants: INITIAL, CASCADE, EWS (exit only)
    """

    def __init__(self, config: P90Config):
        super().__init__(config)
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.bar_type = BarType.from_str(config.bar_type)
        self.lot_size = config.lot_size
        self.magic_number = config.magic_number
        self.initial_sl_mult = config.initial_sl_mult
        self.cascade_sl_mult = config.cascade_sl_mult
        self.tp1_ar_frac = config.tp1_ar_frac
        self.tp2_ar_frac = config.tp2_ar_frac
        self.cascade_window_min = config.cascade_window_min
        self.hard_exit_hour = config.hard_exit_hour
        self.state_reset_hour = config.state_reset_hour
        self.est_offset = config.est_offset
        self.max_initial_per_day = config.max_initial_per_day
        self.max_cascade_per_day = config.max_cascade_per_day

        # Get pip divisor and thresholds for this symbol
        sym_str = str(self.instrument_id.symbol)
        sym_key = sym_str.replace("/", "").replace(".", "")
        self.pip_divisor = PIP_DIVISORS.get(sym_str, PIP_DIVISORS.get(sym_key, 10000.0))

        # Get P90 thresholds (try with and without / separator)
        self.p90_thresholds = SYMBOL_P90.get(sym_str, SYMBOL_P90.get(sym_key, P90_THRESHOLDS))

        # Daily session state
        self.reset_daily_state()

        # Asian range tracking
        self.asian_high = 0.0
        self.asian_low = 99999.0
        self.asian_locked = False
        self.current_date = None

        # Trade state (matches engine P90Engine state fields)
        self._strategy_state = "SEARCH"            # SEARCH or IN_TRADE
        self.active_variant = "INITIAL"  # INITIAL, CASCADE, EWS
        self.direction = 0               # 1=LONG, -1=SHORT, 0=FLAT
        self.entry_price = 0.0
        self.sl_price = 0.0
        self.tp1_price = 0.0             # +25% AR
        self.tp2_price = 0.0             # +50% AR
        self.p90_body_pips = 0.0
        self.p90_body_price = 0.0

        # Cascade state
        self.p90_count = 0               # P90s fired same direction this session
        self.last_p90_exit_time = None   # For cascade window calculation
        self.initial_today = 0
        self.cascade_today = 0

        # Asian range
        self.ar_price = 0.0              # Asian range in price units
        self.asian_range_pips = 0.0

        # Session active flag (set by AR bounds check)
        self.session_active = False

        # AR bounds (shared with engine tier classification)
        self.min_ar = 3                  # minimum AR pips
        self.max_ar = 45                 # maximum AR pips

        # Statistics
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.total_pnl = 0.0

        self.log.info(
            f"P90 Strategy initialized: {self.instrument_id} pip_div={self.pip_divisor}",
            color=LogColor.GREEN,
        )

    def reset_daily_state(self):
        """Reset all per-day state variables (matches engine initialize_session)."""
        self._strategy_state = "SEARCH"
        self.active_variant = "INITIAL"
        self.direction = 0
        self.entry_price = 0.0
        self.sl_price = 0.0
        self.tp1_price = 0.0
        self.tp2_price = 0.0
        self.p90_body_pips = 0.0
        self.p90_body_price = 0.0
        self.p90_count = 0
        self.last_p90_exit_time = None
        self.initial_today = 0
        self.cascade_today = 0

    def on_start(self):
        """Called when strategy starts."""
        self.subscribe_bars(self.bar_type)
        self.log.info(f"Subscribed to {self.bar_type}", color=LogColor.BLUE)

    def on_bar(self, bar: Bar):
        """Main strategy logic — called on each new M5 bar."""
        # bar.ts_event is UTC nanoseconds
        bar_ts = bar.ts_event
        utc_hour = (bar_ts // 3600_000_000_000) % 24
        est_hour = (utc_hour + self.est_offset) % 24

        # Check for new day (simplified: detect new session)
        bar_date = bar_ts  # Use timestamp as proxy
        if self.current_date is None or self._is_new_day(bar, self.current_date):
            self.current_date = bar.ts_event
            self.reset_daily_state()
            self.asian_high = 0.0
            self.asian_low = 99999.0
            self.asian_locked = False

        # ─── Asian Session: 7PM-3AM EST → Track range ───
        if est_hour >= 19 or est_hour < 3:
            if float(bar.high) > self.asian_high:
                self.asian_high = float(bar.high)
            if float(bar.low) < self.asian_low:
                self.asian_low = float(bar.low)

        # ─── Lock Asian Range at 3AM EST ───
        if est_hour == 3 and not self.asian_locked:
            self.asian_locked = True
            self.ar_price = self.asian_high - self.asian_low
            self.asian_range_pips = self._price_to_pips(self.ar_price)

            # AR bounds check (NO_GO tier = skip day)
            if self.asian_range_pips < self.min_ar or self.asian_range_pips > self.max_ar:
                self.log.info(
                    f"AR {self.asian_range_pips:.1f}p outside bounds "
                    f"[{self.min_ar}-{self.max_ar}], session inactive"
                )
                self.session_active = False
            else:
                self.session_active = True
                self.log.info(
                    f"AR LOCKED: {self.asian_range_pips:.1f}p "
                    f"H={self.asian_high:.5f} L={self.asian_low:.5f}",
                    color=LogColor.YELLOW,
                )

        # ─── Hard exit at 5PM EST ───
        if est_hour >= self.hard_exit_hour:
            if not self.portfolio.is_flat(self.instrument_id):
                self._close_all_positions("hard_exit_5pm")
            return

        # ─── Hard state reset at 12PM EST ───
        if est_hour == self.state_reset_hour:
            if self._strategy_state == "IN_TRADE":
                self._close_all_positions("12pm_state_reset")
            self.session_active = False
            self._strategy_state = "SEARCH"
            self.log.info("12PM: Hard state reset, session terminated")
            return

        # ─── Only process during trading window 2AM-11AM ───
        if est_hour < 2 or est_hour >= 11:
            return

        # Skip if session not active
        if not self.session_active:
            return

        f_close = float(bar.close)
        f_open = float(bar.open)
        f_high = float(bar.high)
        f_low = float(bar.low)
        body = abs(f_close - f_open)
        body_pips = self._price_to_pips(body)

        # ─── TP/SL Management (IN_TRADE) ───
        if self._strategy_state == "IN_TRADE":
            sig = self._manage_trade(f_high, f_low, f_close, bar)
            return

        # ─── EWS Detection (in SEARCH — only if we had a prior position that exited) ───
        # EWS fires during IN_TRADE only (opposite P90 + boundary breach)
        # This is handled in _manage_trade via EWS check before TP/SL

        # ─── P90 Detection (SEARCH state) ───
        if self._strategy_state == "SEARCH":
            self._scan_for_p90(bar, est_hour, body, body_pips, f_close, f_open)

    def _scan_for_p90(self, bar: Bar, est_hour: int, body: float,
                      body_pips: float, close: float, open_price: float):
        """
        Check if this bar is a P90 signal.

        Engine requires BOTH:
        1. body >= threshold for current EST hour (_is_p90)
        2. close outside Asian Range (_is_boundary_breach)
        """
        if est_hour < 2 or est_hour >= 11:
            return

        threshold = self.p90_thresholds.get(est_hour, 999.0)

        if body_pips < threshold:
            return

        # Boundary breach: close must be outside Asian Range
        if close <= self.asian_high and close >= self.asian_low:
            return  # No boundary breach — not a P90 signal

        # Direction: WITH P90 (momentum)
        if close > open_price:
            direction = 1  # LONG
        elif close < open_price:
            direction = -1  # SHORT
        else:
            return  # Doji, no direction

        # Detect variant
        variant = self._detect_variant(bar, direction)

        # Enforce max trades per variant per session
        if variant == "INITIAL" and self.initial_today >= self.max_initial_per_day:
            return
        if variant == "CASCADE" and self.cascade_today >= self.max_cascade_per_day:
            return

        # Calculate trade params
        sl, tp1, tp2 = self._calc_trade_params(variant, direction, close, body)

        # Set state
        self._strategy_state = "IN_TRADE"
        self.active_variant = variant
        self.direction = direction
        self.entry_price = close
        self.sl_price = sl
        self.tp1_price = tp1
        self.tp2_price = tp2
        self.p90_body_pips = body_pips
        self.p90_body_price = body
        self.p90_count += 1

        if variant == "INITIAL":
            self.initial_today += 1
        elif variant == "CASCADE":
            self.cascade_today += 1

        dir_str = "LONG" if direction == 1 else "SHORT"
        self.log.info(
            f"P90 ENTRY [{variant}]: {dir_str} @ {close:.5f}, "
            f"SL={sl:.5f}, TP1={tp1:.5f}, TP2={tp2:.5f} "
            f"body={body_pips:.1f}p",
            color=LogColor.YELLOW,
        )

        # Submit order
        self._submit_entry_order(direction, bar)

    def _detect_variant(self, bar: Bar, direction: int) -> str:
        """
        Detect which P90 variant applies.

        CASCADE: Same-dir P90 within 120 min of last exit time
        INITIAL: First P90 of session (default)
        """
        if (self.last_p90_exit_time is not None and
                self.p90_count > 0):
            # Both in nanoseconds since epoch
            delta_ns = bar.ts_event - self.last_p90_exit_time
            delta_min = delta_ns / 60_000_000_000.0
            if delta_min <= self.cascade_window_min:
                self.log.info(
                    f"Cascade P90 detected: #{self.p90_count + 1}, "
                    f"delta={delta_min:.0f}min"
                )
                return "CASCADE"

        return "INITIAL"

    def _calc_trade_params(self, variant: str, direction: int,
                           entry: float, body: float):
        """
        Calculate SL, TP1, TP2 based on variant.

        Reference: engines/p90_engine.py _calc_trade_params()

        INITIAL: SL = 80% of body from close, TP = +25%/+50% AR
        CASCADE: SL = 168% of body from close, TP = +25%/+50% AR
        """
        if variant == "INITIAL":
            sl_offset = body * self.initial_sl_mult
        elif variant == "CASCADE":
            sl_offset = body * self.cascade_sl_mult
        else:
            sl_offset = body * self.initial_sl_mult

        ar_target_1 = self.ar_price * self.tp1_ar_frac  # +25% AR
        ar_target_2 = self.ar_price * self.tp2_ar_frac  # +50% AR

        if direction == 1:  # LONG
            sl = entry - sl_offset
            tp1 = entry + ar_target_1
            tp2 = entry + ar_target_2
        else:  # SHORT
            sl = entry + sl_offset
            tp1 = entry - ar_target_1
            tp2 = entry - ar_target_2

        return sl, tp1, tp2

    def _submit_entry_order(self, direction: int, bar: Bar):
        """Submit market entry order."""
        if direction == 1:
            order_side = OrderSide.BUY
        else:
            order_side = OrderSide.SELL

        qty = Quantity.from_str(str(self.lot_size))

        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=order_side,
            quantity=qty,
            time_in_force=TimeInForce.IOC,
            reduce_only=False,
        )
        self.submit_order(order)

    def _manage_trade(self, high: float, low: float, close: float, bar: Bar):
        """
        Manage active TP/SL/EWS checks per bar.

        Reference: engines/p90_engine.py process_bar() IN_TRADE section.

        Checks ORDER (engine exact):
        1. TP2 (further target)
        2. TP1
        3. SL (close-only)
        """
        # ─── EWS Detection ───
        # Opposite P90 at target + boundary breach = EXIT (not reversal)
        # We check this first, same as engine's EWS detection in IN_TRADE state
        if self._check_ews(bar):
            return

        if self.direction == 1:  # LONG
            # TP2 check first (further out)
            if self.tp2_price > 0 and high >= self.tp2_price:
                self._exit_trade("TP2_HIT", self.tp2_price, bar)
                return

            # TP1 check
            if self.tp1_price > 0 and high >= self.tp1_price:
                self._exit_trade("TP1_HIT", self.tp1_price, bar)
                return

            # SL check (CLOSE ONLY, matches engine: bar.close <= self.sl_price)
            if close <= self.sl_price:
                self._exit_trade("SL_HIT", self.sl_price, bar)
                return

        else:  # SHORT
            # TP2 check first
            if self.tp2_price > 0 and low <= self.tp2_price:
                self._exit_trade("TP2_HIT", self.tp2_price, bar)
                return

            # TP1 check
            if self.tp1_price > 0 and low <= self.tp1_price:
                self._exit_trade("TP1_HIT", self.tp1_price, bar)
                return

            # SL check (CLOSE ONLY, matches engine: bar.close >= self.sl_price)
            if close >= self.sl_price:
                self._exit_trade("SL_HIT", self.sl_price, bar)
                return

    def _check_ews(self, bar: Bar) -> bool:
        """
        EWS: Opposite P90 at target + boundary breach = force exit, NOT reversal.

        Reference: engines/p90_engine.py process_bar() EWS Detection section.

        Conditions:
        1. Current bar is a P90 (body >= threshold for current EST hour)
        2. Current bar direction is OPPOSITE to active position
        3. Current bar breaches Asian Range boundary
        """
        if self._strategy_state != "IN_TRADE":
            return False

        est_hour = self._get_est_hour(bar)
        # Only check during P90 window
        if est_hour < 2 or est_hour >= 11:
            return False

        f_close = float(bar.close)
        f_open = float(bar.open)
        body = abs(f_close - f_open)
        body_pips = self._price_to_pips(body)
        threshold = self.p90_thresholds.get(est_hour, 999.0)

        # Must be a P90 candle
        if body_pips < threshold:
            return False

        # Direction must be opposite to current position
        if f_close > f_open:  # Bullish bar
            bar_dir = 1
        elif f_close < f_open:  # Bearish bar
            bar_dir = -1
        else:
            return False

        if bar_dir == self.direction:
            return False  # Same direction, not EWS

        # Must breach Asian Range boundary
        if f_close <= self.asian_high and f_close >= self.asian_low:
            return False

        # EWS triggered — close position, do NOT reverse
        self.log.info(
            f"EWS: Opposite P90 at target — force close position, NOT reversal",
            color=LogColor.RED,
        )
        self._exit_trade("EWS_EXIT", f_close, bar)
        return True

    def _exit_trade(self, reason: str, exit_price: float, bar: Bar):
        """Exit trade and reset state to SEARCH."""
        pnl_pips = self._calc_pnl_pips(exit_price)
        self.total_trades += 1
        self.total_pnl += pnl_pips

        dir_str = "LONG" if self.direction == 1 else "SHORT"
        if pnl_pips > 0:
            self.wins += 1
            log_color = LogColor.GREEN
        else:
            self.losses += 1
            log_color = LogColor.RED

        self.log.info(
            f"EXIT [{self.active_variant}] {dir_str}: {reason} @ {exit_price:.5f} "
            f"PnL={pnl_pips:+.1f}p (total={self.total_pnl:.1f}p)",
            color=log_color,
        )

        # Close position
        if not self.portfolio.is_flat(self.instrument_id):
            self.close_all_positions(self.instrument_id)

        # Save exit time for cascade tracking (in nanoseconds, same as bar.ts_event)
        self.last_p90_exit_time = bar.ts_event

        # Reset to SEARCH state (matches engine _reset_state)
        self._strategy_state = "SEARCH"
        self.direction = 0
        self.entry_price = 0.0
        self.sl_price = 0.0
        self.tp1_price = 0.0
        self.tp2_price = 0.0
        self.p90_body_pips = 0.0
        self.p90_body_price = 0.0

    def _close_all_positions(self, reason: str):
        """Close all open positions."""
        if not self.portfolio.is_flat(self.instrument_id):
            self.close_all_positions(self.instrument_id)
            self.log.info(f"CLOSED ALL: reason={reason}")

    def _calc_pnl_pips(self, exit_price: float) -> float:
        """Calculate PnL in pips for the trade."""
        if self.direction == 1:  # LONG
            return self._price_to_pips(exit_price - self.entry_price)
        else:  # SHORT
            return self._price_to_pips(self.entry_price - exit_price)

    def _price_to_pips(self, price: float) -> float:
        return price * self.pip_divisor

    def _pips_to_price(self, pips: float) -> float:
        return pips / self.pip_divisor

    def _get_est_hour(self, bar: Bar) -> int:
        """Extract EST hour from bar UTC timestamp."""
        bar_ts = bar.ts_event
        utc_hour = (bar_ts // 3600_000_000_000) % 24
        return (utc_hour + self.est_offset) % 24

    def _bar_to_ns(self, bar: Bar) -> int:
        """Return bar timestamp as nanoseconds since epoch (int)."""
        return int(bar.ts_event)

    def _is_new_day(self, bar: Bar, current_date) -> bool:
        """Detect new trading day (~20h gap = new session)."""
        return bar.ts_event > current_date + 20 * 3600_000_000_000

    def on_stop(self):
        """Called when strategy stops — print final stats."""
        self.log.info(
            f"P90 FINAL STATS: Trades={self.total_trades} W={self.wins} L={self.losses} "
            f"PnL={self.total_pnl:.1f}p WinRate={self.wins / self.total_trades * 100:.1f}%"
            if self.total_trades > 0
            else f"P90 FINAL STATS: No trades",
            color=LogColor.MAGENTA,
        )

    def on_event(self, event: Event):
        """Handle events (order fills, position changes)."""
        super().on_event(event)
