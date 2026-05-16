"""
P90 Base Strategy — CEREBUS FX V5 LIVE PERFECT FORM
====================================================
Converted from Pine Script v6 to Nautilus Trader Python.

This is the P90 BASE STRATEGY — all key functions are here.
Variations can be made by editing logic per the CEREBUS manual.

P90 SYSTEM OVERVIEW:
  1. ASIAN RANGE CALCULATION: 7PM-3AM EST (19:00-03:00 UTC)
     - Measures constraint deficit (high-low range during Asian session)
     - Tier classification: T1 (<20p), T2 (20-30p), T3 (30-45p), NO-GO (>45p)

  2. P90 ENTRY WINDOW: 2AM-11AM EST (02:00-11:00 UTC)
     - Bull signal: Bullish candle with body >= time-dependent threshold
     - Bear signal: Bearish candle with body >= time-dependent threshold
     - Thresholds vary by time window (2-4AM: 4.1p, 4-6AM: 4.6p, etc.)

  3. POSITION MANAGEMENT:
     - Position 1 (40%): SL at 0.8x candle body, TP at -50% extension
     - Position 2 (40%): SL at 1.5x candle body, TP at -50% extension
     - Position 3 (20%): Added after 45min if 8p extension achieved

  4. EXIT CONDITIONS:
     - Hard exit: 12PM EST (17:00 UTC) — close ALL
     - 132% violation: Close ALL
     - Hold time: 120 minutes max
     - Extension filter: Block entry if -25% AND -50% already hit

  5. P90P DISTRIBUTION TRACKER:
     - 2AM checkpoint: Base target = AR * tier_factor
     - 6AM checkpoint: Adjusted target with P90 confirmation boost
     - 9AM checkpoint: Regime-based final target with accuracy estimate

Author: Quant Lab — converted from CEREBUS FX v4/v5 Pine Script
"""
from decimal import Decimal
from datetime import datetime, time, timezone, timedelta
from typing import Optional, Dict, List, Tuple
from enum import Enum

from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce, OrderStatus
from nautilus_trader.model.events import OrderFilled
from nautilus_trader.model.identifiers import InstrumentId, PositionId
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.trading.strategy import Strategy, StrategyConfig

from ..config import (
    ASIAN_SESSION_START_UTC,
    ASIAN_SESSION_END_UTC,
    HARD_EXIT_HOUR_UTC,
    TIER_CONFIG,
    DAILY_LOSS_LIMIT_PCT,
    PIP_VALUES,
)


# ── Enums ────────────────────────────────────────────────────────────────────

class P90Direction(str, Enum):
    NONE = ""
    LONG = "LONG"
    SHORT = "SHORT"


class ARStatus(str, Enum):
    GO = "GO"
    CAUTION = "CAUTION"
    NO_GO = "NO-GO"


class RegimeStatus(str, Enum):
    NONE = ""
    CONFIRMED = "CONFIRMED"
    CAUTION = "CAUTION"
    FAILED = "FAILED"


class TierStatus(str, Enum):
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    NO_GO = "NO-GO"
    NA = "N/A"


# ── Configuration ────────────────────────────────────────────────────────────

class P90Config(StrategyConfig, frozen=True):
    """Configuration for P90 Base Strategy."""
    instrument_id: InstrumentId = None
    bar_type: BarType = None

    # Session timing (EST → UTC conversion)
    asian_start_hour_est: int = 19       # 7 PM EST
    asian_end_hour_est: int = 3          # 3 AM EST
    entry_start_hour_est: int = 2        # 2 AM EST
    entry_end_hour_est: int = 11         # 11 AM EST
    hard_exit_hour_est: int = 12         # 12 PM EST

    # Asian Range thresholds (pips)
    ar_go_threshold: int = 30
    ar_caution_threshold: int = 45
    ar_nogo_threshold: int = 55

    # P90 candle body thresholds by time window (pips)
    p90_bull_2_4am: float = 4.1
    p90_bull_4_6am: float = 4.6
    p90_bull_6_8am: float = 4.6
    p90_bull_8_10am: float = 5.9
    p90_bull_10_11am: float = 6.2
    p90_bear_2_4am: float = 4.1
    p90_bear_4_6am: float = 4.6
    p90_bear_6_8am: float = 4.6
    p90_bear_8_10am: float = 5.9
    p90_bear_10_11am: float = 6.2

    # Extension levels
    ext_25_pct: float = 0.25
    ext_50_pct: float = 0.50

    # SL multipliers
    sl_pos1_mult: float = 0.80    # 80% of candle body
    sl_pos2_mult: float = 1.50    # 1.5x candle body

    # Position sizing (percentage of equity)
    pos1_size_pct: float = 40.0
    pos2_size_pct: float = 40.0
    pos3_size_pct: float = 20.0

    # Timing
    hold_time_minutes: int = 120
    add_time_minutes: int = 45
    add_extension_pips: float = 8.0

    # Violation
    violation_mult: float = 1.32

    # Risk
    max_drawdown_pct: float = 3.0


# ── Helper Functions ─────────────────────────────────────────────────────────

def est_from_utc_hour(utc_hour: int) -> int:
    """Convert UTC hour to EST hour (UTC-5)."""
    return (utc_hour - 5 + 24) % 24


def pips_to_price(pips: float, instrument_id: str = "EUR/USD") -> float:
    """Convert pips to price for a given instrument."""
    pip_value = PIP_VALUES.get(instrument_id, 10.0)
    return pips * pip_value / 10000.0  # Standard pip = 0.0001 for most pairs


def price_to_pips(price_diff: float, instrument_id: str = "EUR/USD") -> float:
    """Convert price difference to pips."""
    pip_value = PIP_VALUES.get(instrument_id, 10.0)
    return price_diff * 10000.0 / pip_value


def calc_qty(size_percent: float, equity: float, entry_price: float) -> float:
    """Calculate position quantity from equity percentage."""
    return (equity * size_percent / 100.0) / entry_price


# ── P90 Strategy ─────────────────────────────────────────────────────────────

class P90BaseStrategy(Strategy):
    """
    CEREBUS P90 Base Strategy for Nautilus Trader.

    Implements the full P90 system:
    - Asian Range calculation and tier classification
    - Time-dependent candle body threshold entries
    - 3-position scaling with extension-based adds
    - P90P Distribution Tracker checkpoints
    - Hard exit, violation exit, and hold time exit
    """

    def __init__(self, config: P90Config):
        super().__init__(config)
        self.cfg = config

        # ── State: Asian Range ──────────────────────────────────────────
        self.asian_high: Optional[float] = None
        self.asian_low: Optional[float] = None
        self.asian_range_complete: bool = False
        self.asian_range_pips: Optional[float] = None
        self.asian_open_bar_index: Optional[int] = None
        self.asian_close_bar_index: Optional[int] = None

        # ── State: P90 Signal ───────────────────────────────────────────
        self.last_signal_time: Optional[datetime] = None
        self.last_entry_time: Optional[datetime] = None
        self.p90_entry_price: Optional[float] = None
        self.p90_candle_body_pips: Optional[float] = None
        self.p90_direction: P90Direction = P90Direction.NONE
        self.in_hold_period: bool = False
        self.signals_today: int = 0
        self.pos3_entered: bool = False

        # ── State: Extension Tracking ───────────────────────────────────
        self.entry_ext_25_long: Optional[float] = None
        self.entry_ext_50_long: Optional[float] = None
        self.entry_ext_25_short: Optional[float] = None
        self.entry_ext_50_short: Optional[float] = None
        self.entry_ext_25_hit: bool = False
        self.entry_ext_50_hit: bool = False
        self.entry_violation_triggered: bool = False

        # ── State: P90P Distribution Tracker ────────────────────────────
        self.tier_status: TierStatus = TierStatus.NA
        self.base_factor: float = 1.52
        self.base_precision: float = 5.0
        self.base_target_pips: Optional[float] = None

        # 6AM checkpoint
        self.checkpoint_6am_done: bool = False
        self.range_7pm_6am: Optional[float] = None
        self.expected_6am_pips: Optional[float] = None
        self.adjusted_target_6am: Optional[float] = None
        self.precision_6am: Optional[float] = None
        self.p90_confirmed_2_6am: bool = False

        # 9AM checkpoint
        self.checkpoint_9am_done: bool = False
        self.range_3am_9am: Optional[float] = None
        self.regime_ratio: Optional[float] = None
        self.regime_status: RegimeStatus = RegimeStatus.NONE
        self.completion_pct_9am: Optional[float] = None
        self.regime_boost: Optional[float] = None
        self.final_target_9am: Optional[float] = None
        self.precision_9am: Optional[float] = None
        self.high_3am_9am: Optional[float] = None
        self.low_3am_9am: Optional[float] = None

        # ── State: Daily Tracking ───────────────────────────────────────
        self.day_equity_start: Optional[float] = None
        self.current_day: Optional[int] = None
        self.drawdown_triggered: bool = False

        # ── Instrument ──────────────────────────────────────────────────
        self.instrument_id_str = str(config.instrument_id) if config.instrument_id else "EUR/USD"

    # ── Session Helpers ─────────────────────────────────────────────────

    def _get_est_hour(self, bar: Bar) -> int:
        """Get EST hour from bar timestamp."""
        utc_hour = bar.ts_event.hour  # nanosecond timestamp → hour
        return est_from_utc_hour(utc_hour)

    def _get_est_minute(self, bar: Bar) -> int:
        """Get EST minute from bar timestamp."""
        return bar.ts_event.minute

    def _in_asian_session(self, bar: Bar) -> bool:
        """Check if bar is within Asian session (7PM-3AM EST)."""
        h = self._get_est_hour(bar)
        return h >= self.cfg.asian_start_hour_est or h < self.cfg.asian_end_hour_est

    def _in_p90_entry_window(self, bar: Bar) -> bool:
        """Check if bar is within P90 entry window (2AM-11AM EST)."""
        h = self._get_est_hour(bar)
        return h >= self.cfg.entry_start_hour_est and h < self.cfg.entry_end_hour_est

    def _is_hard_exit_time(self, bar: Bar) -> bool:
        """Check if it's hard exit time (12PM EST)."""
        h = self._get_est_hour(bar)
        return h >= self.cfg.hard_exit_hour_est

    def _is_new_day(self, bar: Bar) -> bool:
        """Check if this bar starts a new trading day."""
        bar_day = bar.ts_event.day
        if self.current_day is None or bar_day != self.current_day:
            self.current_day = bar_day
            return True
        return False

    # ── P90 Threshold Helpers ───────────────────────────────────────────

    def _get_p90_bull_threshold(self, bar: Bar) -> float:
        """Get bull candle body threshold for current time window."""
        h = self._get_est_hour(bar)
        if h >= 2 and h < 4:
            return self.cfg.p90_bull_2_4am
        elif h >= 4 and h < 6:
            return self.cfg.p90_bull_4_6am
        elif h >= 6 and h < 8:
            return self.cfg.p90_bull_6_8am
        elif h >= 8 and h < 10:
            return self.cfg.p90_bull_8_10am
        elif h >= 10 and h < 11:
            return self.cfg.p90_bull_10_11am
        return 0.0

    def _get_p90_bear_threshold(self, bar: Bar) -> float:
        """Get bear candle body threshold for current time window."""
        h = self._get_est_hour(bar)
        if h >= 2 and h < 4:
            return self.cfg.p90_bear_2_4am
        elif h >= 4 and h < 6:
            return self.cfg.p90_bear_4_6am
        elif h >= 6 and h < 8:
            return self.cfg.p90_bear_6_8am
        elif h >= 8 and h < 10:
            return self.cfg.p90_bear_8_10am
        elif h >= 10 and h < 11:
            return self.cfg.p90_bear_10_11am
        return 0.0

    # ── Asian Range Calculation ─────────────────────────────────────────

    def _update_asian_range(self, bar: Bar):
        """Calculate Asian Range from 7PM-3AM EST."""
        est_hour = self._get_est_hour(bar)
        est_minute = self._get_est_minute(bar)

        # Start of Asian session: 7PM EST
        if est_hour == self.cfg.asian_start_hour_est and est_minute == 0:
            self.asian_high = bar.high.as_double()
            self.asian_low = bar.low.as_double()
            self.asian_open_bar_index = self.cache.bar_count(self.cfg.bar_type)
            self.asian_range_complete = False

        # During Asian session: track high/low
        if self._in_asian_session(bar) and not self.asian_range_complete:
            if self.asian_high is not None:
                self.asian_high = max(self.asian_high, bar.high.as_double())
            if self.asian_low is not None:
                self.asian_low = min(self.asian_low, bar.low.as_double())

        # End of Asian session: 3AM EST
        if est_hour == self.cfg.asian_end_hour_est and est_minute == 0:
            self.asian_close_bar_index = self.cache.bar_count(self.cfg.bar_type) - 1
            self.asian_range_complete = True
            if self.asian_high is not None and self.asian_low is not None:
                self.asian_range_pips = price_to_pips(
                    self.asian_high - self.asian_low, self.instrument_id_str
                )

    def _get_ar_status(self) -> ARStatus:
        """Get Asian Range status."""
        if self.asian_range_pips is None:
            return ARStatus.GO
        if self.asian_range_pips < self.cfg.ar_go_threshold:
            return ARStatus.GO
        elif self.asian_range_pips < self.cfg.ar_caution_threshold:
            return ARStatus.GO
        elif self.asian_range_pips < self.cfg.ar_nogo_threshold:
            return ARStatus.CAUTION
        else:
            return ARStatus.NO_GO

    def _get_tier(self) -> TierStatus:
        """Get tier classification from Asian Range."""
        if self.asian_range_pips is None:
            return TierStatus.NA
        if self.asian_range_pips < 20:
            return TierStatus.T1
        elif self.asian_range_pips < 30:
            return TierStatus.T2
        elif self.asian_range_pips < 45:
            return TierStatus.T3
        else:
            return TierStatus.NO_GO

    # ── P90 Signal Detection ────────────────────────────────────────────

    def _check_p90_signals(self, bar: Bar) -> Tuple[bool, bool]:
        """
        Check for P90 bull/bear signals.
        Returns (bull_signal, bear_signal).
        """
        if not self.asian_range_complete:
            return False, False
        if not self._in_p90_entry_window(bar):
            return False, False
        if self.in_hold_period:
            return False, False
        if self.drawdown_triggered:
            return False, False

        candle_body_pips = price_to_pips(
            abs(bar.close.as_double() - bar.open.as_double()),
            self.instrument_id_str
        )

        # Bull signal: bullish candle with body >= threshold
        bull_threshold = self._get_p90_bull_threshold(bar)
        bull_candle = (bar.close.as_double() > bar.open.as_double() and
                       candle_body_pips >= bull_threshold)

        # Bear signal: bearish candle with body >= threshold
        bear_threshold = self._get_p90_bear_threshold(bar)
        bear_candle = (bar.close.as_double() < bar.open.as_double() and
                       candle_body_pips >= bear_threshold)

        return bull_candle, bear_candle

    # ── Extension Tracking ──────────────────────────────────────────────

    def _update_extension_tracking(self, bar: Bar):
        """Track extension level hits after P90 entry."""
        if self.p90_direction == P90Direction.LONG and self.asian_range_complete:
            if not self.entry_ext_25_hit and bar.high.as_double() >= self.entry_ext_25_long:
                self.entry_ext_25_hit = True
            if not self.entry_ext_50_hit and bar.high.as_double() >= self.entry_ext_50_long:
                self.entry_ext_50_hit = True
            if not self.entry_violation_triggered:
                violation = self.asian_high + (self.asian_range_pips * self.cfg.violation_mult * 0.0001)
                if bar.high.as_double() >= violation:
                    self.entry_violation_triggered = True

        elif self.p90_direction == P90Direction.SHORT and self.asian_range_complete:
            if not self.entry_ext_25_hit and bar.low.as_double() <= self.entry_ext_25_short:
                self.entry_ext_25_hit = True
            if not self.entry_ext_50_hit and bar.low.as_double() <= self.entry_ext_50_short:
                self.entry_ext_50_hit = True
            if not self.entry_violation_triggered:
                violation = self.asian_low - (self.asian_range_pips * self.cfg.violation_mult * 0.0001)
                if bar.low.as_double() <= violation:
                    self.entry_violation_triggered = True

    # ── P90P Distribution Tracker ───────────────────────────────────────

    def _update_p90p_tracker(self, bar: Bar):
        """Update P90P Distribution Tracker checkpoints."""
        est_hour = self._get_est_hour(bar)
        est_minute = self._get_est_minute(bar)

        # Tier and base factor (available once AR complete)
        if self.asian_range_complete:
            self.tier_status = self._get_tier()
            tier_cfg = TIER_CONFIG.get(self.tier_status.value, TIER_CONFIG["NO_GO"])
            self.base_factor = tier_cfg.get("expansion", 1.52)
            self.base_precision = 2.5 if self.tier_status == TierStatus.T1 else \
                                  3.0 if self.tier_status == TierStatus.T2 else \
                                  3.5 if self.tier_status == TierStatus.T3 else 5.0
            if self.asian_range_pips:
                self.base_target_pips = self.asian_range_pips * self.base_factor

        # Track P90 confirmation between 2-6AM
        if est_hour >= 2 and est_hour < 6:
            bull_sig, bear_sig = self._check_p90_signals(bar)
            if bull_sig or bear_sig:
                self.p90_confirmed_2_6am = True

        # 6AM checkpoint
        if est_hour == 6 and est_minute == 0 and self.asian_range_complete and not self.checkpoint_6am_done:
            if self.asian_high and self.asian_low:
                self.range_7pm_6am = price_to_pips(
                    bar.high.as_double() - self.asian_low, self.instrument_id_str
                )
                if self.base_target_pips:
                    self.expected_6am_pips = self.base_target_pips * 0.65
                p90_adj = 1.05 if self.p90_confirmed_2_6am else 1.00
                if self.range_7pm_6am:
                    self.adjusted_target_6am = (self.range_7pm_6am / 0.65) * p90_adj
                self.precision_6am = 2.5 if self.p90_confirmed_2_6am else 3.5
                self.checkpoint_6am_done = True

        # Track 3AM-9AM range
        if est_hour == 3 and est_minute == 0:
            self.high_3am_9am = bar.high.as_double()
            self.low_3am_9am = bar.low.as_double()

        if est_hour > 3 and est_hour < 9:
            if self.high_3am_9am is not None:
                self.high_3am_9am = max(self.high_3am_9am, bar.high.as_double())
            if self.low_3am_9am is not None:
                self.low_3am_9am = min(self.low_3am_9am, bar.low.as_double())

        # 9AM checkpoint
        if est_hour == 9 and est_minute == 0 and self.asian_range_complete and not self.checkpoint_9am_done:
            if self.high_3am_9am and self.low_3am_9am:
                self.range_3am_9am = price_to_pips(
                    self.high_3am_9am - self.low_3am_9am, self.instrument_id_str
                )
                if self.asian_range_pips and self.asian_range_pips > 0:
                    self.regime_ratio = self.range_3am_9am / self.asian_range_pips
                else:
                    self.regime_ratio = 0

                # Regime classification
                if self.regime_ratio and self.regime_ratio >= 1.50:
                    self.regime_status = RegimeStatus.CONFIRMED
                    self.completion_pct_9am = 0.902
                    self.regime_boost = 1.10
                elif self.regime_ratio and self.regime_ratio >= 1.45:
                    self.regime_status = RegimeStatus.CAUTION
                    self.completion_pct_9am = 0.861
                    self.regime_boost = 1.05
                else:
                    self.regime_status = RegimeStatus.FAILED
                    self.completion_pct_9am = 0.738
                    self.regime_boost = 0.90

                # Final target
                if self.asian_high and self.asian_low:
                    range_7pm_9am = price_to_pips(
                        bar.high.as_double() - self.asian_low, self.instrument_id_str
                    )
                    if self.completion_pct_9am and self.regime_boost:
                        self.final_target_9am = (range_7pm_9am / self.completion_pct_9am) * self.regime_boost

                self.precision_9am = 2.0 if self.regime_status == RegimeStatus.CONFIRMED else \
                                     2.5 if self.regime_status == RegimeStatus.CAUTION else 3.5
                self.checkpoint_9am_done = True

    # ── Daily Reset ─────────────────────────────────────────────────────

    def _daily_reset(self, bar: Bar):
        """Reset daily tracking variables."""
        self.signals_today = 0
        self.last_signal_time = None
        self.last_entry_time = None
        self.pos3_entered = False
        self.p90_confirmed_2_6am = False
        self.checkpoint_6am_done = False
        self.checkpoint_9am_done = False
        self.range_7pm_6am = None
        self.expected_6am_pips = None
        self.adjusted_target_6am = None
        self.precision_6am = None
        self.range_3am_9am = None
        self.regime_ratio = None
        self.regime_status = RegimeStatus.NONE
        self.completion_pct_9am = None
        self.regime_boost = None
        self.final_target_9am = None
        self.precision_9am = None
        self.high_3am_9am = None
        self.low_3am_9am = None

        # Track daily equity for drawdown
        if self.day_equity_start is None:
            self.day_equity_start = self.portfolio.equity().as_double()

    # ── Risk Management ─────────────────────────────────────────────────

    def _check_drawdown(self) -> bool:
        """Check if daily drawdown limit is triggered."""
        if self.day_equity_start is None or self.day_equity_start <= 0:
            return False
        current_equity = self.portfolio.equity().as_double()
        drawdown_pct = 100.0 * (current_equity - self.day_equity_start) / self.day_equity_start
        return drawdown_pct < -self.cfg.max_drawdown_pct

    def _can_trade(self, bar: Bar) -> bool:
        """Check if trading is allowed."""
        # Session filter: only trade prime hours (2AM-12PM EST)
        est_hour = self._get_est_hour(bar)
        can_trade_session = est_hour >= 2 and est_hour < 12
        return can_trade_session and not self.drawdown_triggered

    # ── Position Entry ──────────────────────────────────────────────────

    def _enter_p90_positions(self, bar: Bar, direction: P90Direction):
        """Enter P90 positions (Pos1 and Pos2)."""
        if self.p90_entry_price is None or self.p90_candle_body_pips is None:
            return

        equity = self.portfolio.equity().as_double()
        entry = self.p90_entry_price

        # Position 1 (40%)
        sl1_pips = self.p90_candle_body_pips * self.cfg.sl_pos1_mult
        sl1_price = (entry - pips_to_price(sl1_pips, self.instrument_id_str)
                     if direction == P90Direction.LONG
                     else entry + pips_to_price(sl1_pips, self.instrument_id_str))
        tp1_price = self.entry_ext_50_long if direction == P90Direction.LONG else self.entry_ext_50_short

        qty1 = calc_qty(self.cfg.pos1_size_pct, equity, entry)

        if direction == P90Direction.LONG:
            self.buy(
                instrument_id=self.cfg.instrument_id,
                quantity=Quantity.from_str(str(qty1)),
                price=Price.from_str(str(tp1_price)),
                stop_loss=Price.from_str(str(sl1_price)),
                comment="P90_Pos1_Long",
            )
        else:
            self.sell(
                instrument_id=self.cfg.instrument_id,
                quantity=Quantity.from_str(str(qty1)),
                price=Price.from_str(str(tp1_price)),
                stop_loss=Price.from_str(str(sl1_price)),
                comment="P90_Pos1_Short",
            )

        # Position 2 (40%)
        sl2_pips = self.p90_candle_body_pips * self.cfg.sl_pos2_mult
        sl2_price = (entry - pips_to_price(sl2_pips, self.instrument_id_str)
                     if direction == P90Direction.LONG
                     else entry + pips_to_price(sl2_pips, self.instrument_id_str))

        qty2 = calc_qty(self.cfg.pos2_size_pct, equity, entry)

        if direction == P90Direction.LONG:
            self.buy(
                instrument_id=self.cfg.instrument_id,
                quantity=Quantity.from_str(str(qty2)),
                price=Price.from_str(str(tp1_price)),
                stop_loss=Price.from_str(str(sl2_price)),
                comment="P90_Pos2_Long",
            )
        else:
            self.sell(
                instrument_id=self.cfg.instrument_id,
                quantity=Quantity.from_str(str(qty2)),
                price=Price.from_str(str(tp1_price)),
                stop_loss=Price.from_str(str(sl2_price)),
                comment="P90_Pos2_Short",
            )

    def _check_position3_add(self, bar: Bar):
        """Check if Position 3 should be added (45min after entry + 8p extension)."""
        if self.last_entry_time is None or self.pos3_entered:
            return
        if self.p90_entry_price is None:
            return

        now = bar.ts_event
        minutes_elapsed = (now - self.last_entry_time).total_seconds() / 60.0

        if minutes_elapsed >= self.cfg.add_time_minutes and minutes_elapsed < (self.cfg.add_time_minutes + 5):
            # Check extension achieved
            if self.p90_direction == P90Direction.LONG:
                extension_pips = price_to_pips(
                    bar.high.as_double() - self.p90_entry_price, self.instrument_id_str
                )
            else:
                extension_pips = price_to_pips(
                    self.p90_entry_price - bar.low.as_double(), self.instrument_id_str
                )

            if extension_pips >= self.cfg.add_extension_pips and not self.entry_violation_triggered:
                equity = self.portfolio.equity().as_double()
                entry = self.p90_entry_price

                sl3_pips = self.p90_candle_body_pips * self.cfg.sl_pos2_mult if self.p90_candle_body_pips else 10
                sl3_price = (entry - pips_to_price(sl3_pips, self.instrument_id_str)
                             if self.p90_direction == P90Direction.LONG
                             else entry + pips_to_price(sl3_pips, self.instrument_id_str))
                tp_price = self.entry_ext_50_long if self.p90_direction == P90Direction.LONG else self.entry_ext_50_short

                qty3 = calc_qty(self.cfg.pos3_size_pct, equity, entry)

                if self.p90_direction == P90Direction.LONG:
                    self.buy(
                        instrument_id=self.cfg.instrument_id,
                        quantity=Quantity.from_str(str(qty3)),
                        price=Price.from_str(str(tp_price)),
                        stop_loss=Price.from_str(str(sl3_price)),
                        comment="P90_Pos3_Long",
                    )
                else:
                    self.sell(
                        instrument_id=self.cfg.instrument_id,
                        quantity=Quantity.from_str(str(qty3)),
                        price=Price.from_str(str(tp_price)),
                        stop_loss=Price.from_str(str(sl3_price)),
                        comment="P90_Pos3_Short",
                    )

                self.pos3_entered = True

    # ── Exit Conditions ─────────────────────────────────────────────────

    def _check_exits(self, bar: Bar):
        """Check and execute exit conditions."""
        # Hard exit: 12PM EST
        if self._is_hard_exit_time(bar):
            self.close_all_positions()
            self.log.info("P90 Hard Exit (12 PM EST)")
            return

        # 132% violation
        if self.entry_violation_triggered:
            self.close_all_positions()
            self.log.info("P90 132% Violation Exit")
            return

        # Hold time exit (120 minutes)
        if self.last_entry_time is not None:
            now = bar.ts_event
            minutes_held = (now - self.last_entry_time).total_seconds() / 60.0
            if minutes_held >= self.cfg.hold_time_minutes:
                self.close_all_positions()
                self.log.info(f"P90 Hold Time Exit ({self.cfg.hold_time_minutes} min)")
                self.last_entry_time = None
                self.in_hold_period = False
                return

    # ── Nautilus Event Handlers ─────────────────────────────────────────

    def on_start(self):
        """Strategy started."""
        self.log.info("P90 Base Strategy started")

    def on_bar(self, bar: Bar):
        """Process each bar."""
        # Daily reset
        if self._is_new_day(bar):
            self._daily_reset(bar)

        # Update drawdown tracking
        self.drawdown_triggered = self._check_drawdown()

        # Update Asian Range
        self._update_asian_range(bar)

        # Update P90P Distribution Tracker
        self._update_p90p_tracker(bar)

        # Update extension tracking
        if self.p90_direction != P90Direction.NONE:
            self._update_extension_tracking(bar)

        # Check exits first
        self._check_exits(bar)

        # Check hold period expiration
        if self.last_entry_time is not None and self.in_hold_period:
            now = bar.ts_event
            minutes_since = (now - self.last_entry_time).total_seconds() / 60.0
            if minutes_since >= self.cfg.hold_time_minutes:
                self.in_hold_period = False

        # Check for new P90 signals
        bull_signal, bear_signal = self._check_p90_signals(bar)

        if bull_signal or bear_signal:
            ar_status = self._get_ar_status()
            filter_blocked = self.entry_ext_25_hit and self.entry_ext_50_hit

            valid_entry = (ar_status != ARStatus.NO_GO and
                           not filter_blocked and
                           not self.entry_violation_triggered)

            if valid_entry:
                direction = P90Direction.LONG if bull_signal else P90Direction.SHORT

                # Record signal
                self.signals_today += 1
                self.last_signal_time = bar.ts_event
                self.p90_entry_price = bar.close.as_double()
                self.p90_candle_body_pips = price_to_pips(
                    abs(bar.close.as_double() - bar.open.as_double()),
                    self.instrument_id_str
                )
                self.p90_direction = direction
                self.last_entry_time = bar.ts_event
                self.in_hold_period = True

                # Calculate extension levels
                if self.asian_range_pips and self.asian_high and self.asian_low:
                    self.entry_ext_25_long = self.asian_high + (self.asian_range_pips * self.cfg.ext_25_pct * 0.0001)
                    self.entry_ext_50_long = self.asian_high + (self.asian_range_pips * self.cfg.ext_50_pct * 0.0001)
                    self.entry_ext_25_short = self.asian_low - (self.asian_range_pips * self.cfg.ext_25_pct * 0.0001)
                    self.entry_ext_50_short = self.asian_low - (self.asian_range_pips * self.cfg.ext_50_pct * 0.0001)

                self.entry_ext_25_hit = False
                self.entry_ext_50_hit = False
                self.entry_violation_triggered = False

                # Enter positions
                self._enter_p90_positions(bar, direction)

                self.log.info(
                    f"P90 {direction.value} signal | "
                    f"Body: {self.p90_candle_body_pips:.1f}p | "
                    f"AR: {self.asian_range_pips:.1f}p | "
                    f"Tier: {self.tier_status.value} | "
                    f"Entry: {self.p90_entry_price}"
                )

        # Check Position 3 add
        if self.p90_direction != P90Direction.NONE:
            self._check_position3_add(bar)

    def on_stop(self):
        """Strategy stopped."""
        self.log.info("P90 Base Strategy stopped")
        self.close_all_positions()