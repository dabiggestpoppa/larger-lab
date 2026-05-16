"""
P90 Cascade Activation Strategy — CEREBUS FX v4.0 (Part 2, Pages 10-15)
=========================================================================

Subsequent P90 Activations | Rolling Constraint Boundaries | Directional Bias Validation
Data Period: January 2022 – March 2026 | EUR/USD M5 | 315,000+ Candles

CASCADE ACTIVATION LOGIC:
  1. Initial P90 (Bias Setter): First P90 candle in 2-11 AM EST window
     → Establishes direction of constraint resolution for session
     → Size: 40% | Boundary: 80% of P90 body | Target: -50% Asian Range

  2. Cascade P90 (Momentum Confirmation): Subsequent P90 in SAME direction
     → Must occur within 120 min of Initial P90
     → Size: 20% | Boundary: 168% of THIS P90 body (wider)
     → Target: -50% Asian Range

  3. Cascade 2 P90 (Sustained Momentum): Third P90 in same direction
     → Size: 10% | Boundary: 168% of THIS P90 body
     → Max 3 cascades per session (4th+ = AVOID, 76.4% WR)

  4. 45-Min Add: Time-based add after 45min + 8p extension
     → Size: 30% | Boundary: Breakeven | Target: -50% Asian Range

CASCADE + 45-MIN ADD COMBO (Highest Conviction):
  When BOTH trigger: Signal 1 (40%) + 45-Min Add (30%) + Cascade P90 (30%)
  Combined Win Rate: 93.4%

CASCADE STATISTICS:
  1st P90:  83.3% WR | Baseline
  2nd P90:  87.8% WR | BEST (+5.4% edge)
  3rd P90:  84.2% WR | GOOD
  4th+ P90: 76.4% WR | AVOID

OPTIMAL CASCADE TIMING:
  45-60 min after initial P90 = 88.2% WR (sweet spot)
  Skip cascades after 90 min from initial activation

Author: Quant Lab — based on CEREBUS FX v4.0 manual Part 2
"""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Tuple
from enum import Enum

import pandas as pd
import numpy as np


# ── Enums ────────────────────────────────────────────────────────────────────

class CascadeDirection(str, Enum):
    NONE = ""
    LONG = "LONG"
    SHORT = "SHORT"


class TierStatus(str, Enum):
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    NO_GO = "NO_GO"
    NA = "NA"


# ── Configuration ────────────────────────────────────────────────────────────

class P90CascadeConfig:
    """Configuration for P90 Cascade Activation Strategy."""

    def __init__(self):
        # Session timing (EST → UTC: EST = UTC - 5)
        self.asian_start_hour_est = 19     # 7 PM EST
        self.asian_end_hour_est = 3        # 3 AM EST
        self.entry_start_hour_est = 2      # 2 AM EST
        self.entry_end_hour_est = 11       # 11 AM EST
        self.hard_exit_hour_est = 12       # 12 PM EST

        # P90 candle body thresholds by time window (pips)
        self.p90_thresholds = {
            (2, 4): 4.1,    # 2-4 AM EST
            (4, 6): 4.6,    # 4-6 AM EST
            (6, 8): 4.6,    # 6-8 AM EST
            (8, 10): 5.9,   # 8-10 AM EST
            (10, 11): 6.2,  # 10-11 AM EST
        }

        # Tier config (Asian Range → Position Sizing)
        self.tier_config = {
            "T1": {"max_pips": 20, "size_pct": 1.0, "expansion": 3.12},
            "T2": {"min_pips": 20, "max_pips": 30, "size_pct": 0.75, "expansion": 2.68},
            "T3": {"min_pips": 30, "max_pips": 45, "size_pct": 0.50, "expansion": 2.18},
            "NO_GO": {"min_pips": 45, "size_pct": 0.0, "expansion": 1.52},
        }

        # Cascade parameters
        self.max_cascades = 3
        self.cascade_window_minutes = 120     # Max time from initial P90
        self.optimal_cascade_start = 30       # Min minutes after initial
        self.optimal_cascade_end = 90         # Max minutes for optimal
        self.cascade_size_1 = 0.20            # 20% for 2nd P90
        self.cascade_size_2 = 0.10            # 10% for 3rd P90
        self.cascade_sl_mult = 1.68           # 168% of P90 body

        # 45-min add parameters
        self.add_time_minutes = 45
        self.add_extension_pips = 8.0
        self.add_size = 0.30                  # 30%

        # Initial P90 sizing
        self.initial_size = 0.40              # 40%
        self.initial_sl_mult = 0.80           # 80% of P90 body

        # Risk
        self.max_drawdown_pct = 0.5
        self.daily_loss_limit_pct = 0.40

        # Position sizing
        self.position_size_lots = 0.1         # 10 micro lots


# ── Cascade Trade ────────────────────────────────────────────────────────────

class CascadeTrade:
    """Represents a single cascade trade."""

    def __init__(self, entry_time, direction, entry_price, sl_price, tp_price,
                 size_lots, activation_type, cascade_num=0):
        self.entry_time = entry_time
        self.direction = direction
        self.entry_price = entry_price
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.size_lots = size_lots
        self.activation_type = activation_type  # "initial", "cascade_1", "cascade_2", "add_45min"
        self.cascade_num = cascade_num
        self.exit_time = None
        self.exit_price = None
        self.pnl_pips = 0.0
        self.result = ""  # "win", "loss", "hard_exit"
        self.exit_reason = ""


# ── P90 Cascade Strategy ─────────────────────────────────────────────────────

class P90CascadeStrategy:
    """
    P90 Cascade Activation Strategy — CEREBUS FX v4.0 (Part 2)

    Implements the full cascade system:
    - Initial P90 sets direction
    - Subsequent P90s in same direction = cascade activations
    - 45-min time-based add
    - Combined cascade + add for 93.4% win rate
    """

    def __init__(self, config: P90CascadeConfig = None):
        self.cfg = config or P90CascadeConfig()
        self.trades: List[CascadeTrade] = []

    def _get_est_hour(self, timestamp) -> int:
        """Convert UTC timestamp to EST hour (UTC-5)."""
        if isinstance(timestamp, pd.Timestamp):
            utc_hour = timestamp.hour
        else:
            utc_hour = timestamp
        return (utc_hour - 5 + 24) % 24

    def _get_est_minute(self, timestamp) -> int:
        """Get EST minute from timestamp."""
        if isinstance(timestamp, pd.Timestamp):
            return timestamp.minute
        return 0

    def _in_asian_session(self, est_hour: int) -> bool:
        """Check if hour is within Asian session (7PM-3AM EST)."""
        return est_hour >= self.cfg.asian_start_hour_est or est_hour < self.cfg.asian_end_hour_est

    def _in_entry_window(self, est_hour: int) -> bool:
        """Check if hour is within P90 entry window (2AM-11AM EST)."""
        return self.cfg.entry_start_hour_est <= est_hour < self.cfg.entry_end_hour_est

    def _is_hard_exit_time(self, est_hour: int) -> bool:
        """Check if it's hard exit time (12PM EST)."""
        return est_hour >= self.cfg.hard_exit_hour_est

    def _get_p90_threshold(self, est_hour: int) -> float:
        """Get P90 candle body threshold for current time window."""
        for (start, end), threshold in self.cfg.p90_thresholds.items():
            if start <= est_hour < end:
                return threshold
        return 6.2  # Default for edge cases

    def _get_tier(self, ar_pips: float) -> TierStatus:
        """Classify Asian Range into tier."""
        if ar_pips < 20:
            return TierStatus.T1
        elif ar_pips < 30:
            return TierStatus.T2
        elif ar_pips < 45:
            return TierStatus.T3
        else:
            return TierStatus.NO_GO

    def _price_to_pips(self, price_diff: float, pair: str = "EUR/USD") -> float:
        """Convert price difference to pips."""
        if "JPY" in pair:
            return price_diff * 100
        elif "XAU" in pair:
            return price_diff * 10
        return price_diff * 10000

    def _pips_to_price(self, pips: float, pair: str = "EUR/USD") -> float:
        """Convert pips to price."""
        if "JPY" in pair:
            return pips / 100
        elif "XAU" in pair:
            return pips / 10
        return pips / 10000

    def run_backtest(self, df: pd.DataFrame, pair: str = "EUR/USD",
                     max_bars: int = None) -> Dict:
        """
        Run P90 Cascade backtest on DataFrame data.

        Args:
            df: DataFrame with columns [open, high, low, close] and DatetimeIndex (UTC)
            pair: Pair name for pip calculation
            max_bars: Limit bars for faster testing

        Returns:
            Dict with backtest results
        """
        if df is None or len(df) < 500:
            return {"error": "Insufficient data", "total_trades": 0}

        df = df.copy()
        if max_bars and len(df) > max_bars:
            df = df.tail(max_bars).copy()

        # Ensure UTC index
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')

        df['hour_utc'] = df.index.hour
        df['minute'] = df.index.minute
        df['est_hour'] = (df['hour_utc'] - 5 + 24) % 24
        df['date'] = df.index.date

        # ── State Variables ────────────────────────────────────────────
        asian_high = None
        asian_low = None
        asian_range_pips = None
        tier = TierStatus.NA

        # Session state
        session_direction = CascadeDirection.NONE
        initial_p90_time = None
        initial_p90_price = None
        cascade_count = 0
        add_45min_done = False
        targets_hit = {"tp1_25": False, "tp2_50": False}
        kill_switch_triggered = False

        # Active trades
        active_trades: List[CascadeTrade] = []
        all_trades: List[CascadeTrade] = []

        # Daily tracking
        daily_pnl = 0.0
        last_date = None
        daily_loss_limit_hit = False

        position_size = self.cfg.position_size_lots

        for i in range(50, len(df) - 1):
            row = df.iloc[i]
            ts = df.index[i]
            est_h = row['est_hour']
            date = row['date']
            o, h, l, c = row['open'], row['high'], row['low'], row['close']

            # ── New Day Reset ───────────────────────────────────────────
            if date != last_date:
                # Close any open trades at end of previous day
                for t in active_trades:
                    if t.exit_time is None:
                        pip_diff = (c - t.entry_price) * (1 if t.direction == CascadeDirection.LONG else -1)
                        t.pnl_pips = self._price_to_pips(pip_diff, pair)
                        t.exit_time = ts
                        t.exit_price = c
                        t.result = "win" if t.pnl_pips > 0 else "loss"
                        t.exit_reason = "new_day"
                        all_trades.append(t)
                        daily_pnl += t.pnl_pips
                active_trades.clear()

                # Reset session state
                asian_high = None
                asian_low = None
                asian_range_pips = None
                tier = TierStatus.NA
                session_direction = CascadeDirection.NONE
                initial_p90_time = None
                initial_p90_price = None
                cascade_count = 0
                add_45min_done = False
                targets_hit = {"tp1_25": False, "tp2_50": False}
                kill_switch_triggered = False
                daily_pnl = 0.0
                daily_loss_limit_hit = False
                last_date = date

            # ── Asian Range Calculation (7PM-3AM EST) ───────────────────
            if self._in_asian_session(est_h):
                if asian_high is None:
                    asian_high = h
                    asian_low = l
                else:
                    asian_high = max(asian_high, h)
                    asian_low = min(asian_low, l)
                # Close Asian: classify tier at 3AM
                if est_h == self.cfg.asian_end_hour_est:
                    if asian_high is not None and asian_low is not None:
                        asian_range_pips = self._price_to_pips(asian_high - asian_low, pair)
                        tier = self._get_tier(asian_range_pips)
                continue

            # Skip if NO-GO tier
            if tier == TierStatus.NO_GO:
                continue

            # Skip if daily loss limit hit
            if daily_loss_limit_hit:
                continue

            # ── Hard Exit (12PM EST) ────────────────────────────────────
            if self._is_hard_exit_time(est_h):
                for t in active_trades:
                    if t.exit_time is None:
                        pip_diff = (c - t.entry_price) * (1 if t.direction == CascadeDirection.LONG else -1)
                        t.pnl_pips = self._price_to_pips(pip_diff, pair)
                        t.exit_time = ts
                        t.exit_price = c
                        t.result = "win" if t.pnl_pips > 0 else "loss"
                        t.exit_reason = "hard_exit_12pm"
                        all_trades.append(t)
                        daily_pnl += t.pnl_pips
                active_trades.clear()
                session_direction = CascadeDirection.NONE
                continue

            # ── Manage Active Trades ────────────────────────────────────
            trades_to_remove = []
            for t in active_trades:
                if t.exit_time is not None:
                    continue

                direction_mult = 1 if t.direction == CascadeDirection.LONG else -1

                # Check SL
                if t.direction == CascadeDirection.LONG and l <= t.sl_price:
                    t.pnl_pips = self._price_to_pips(t.sl_price - t.entry_price, pair)
                    t.exit_time = ts
                    t.exit_price = t.sl_price
                    t.result = "loss"
                    t.exit_reason = "sl"
                    all_trades.append(t)
                    daily_pnl += t.pnl_pips
                    trades_to_remove.append(t)
                    continue
                elif t.direction == CascadeDirection.SHORT and h >= t.sl_price:
                    t.pnl_pips = self._price_to_pips(t.entry_price - t.sl_price, pair)
                    t.exit_time = ts
                    t.exit_price = t.sl_price
                    t.result = "loss"
                    t.exit_reason = "sl"
                    all_trades.append(t)
                    daily_pnl += t.pnl_pips
                    trades_to_remove.append(t)
                    continue

                # Check TP1 (-25% Asian Range)
                if not targets_hit["tp1_25"] and asian_range_pips:
                    tp1_offset = self._pips_to_price(asian_range_pips * 0.25, pair)
                    if t.direction == CascadeDirection.LONG:
                        tp1 = t.entry_price - tp1_offset  # Mean reversion: pullback
                        if l <= tp1:
                            targets_hit["tp1_25"] = True
                    else:
                        tp1 = t.entry_price + tp1_offset
                        if h >= tp1:
                            targets_hit["tp1_25"] = True

                # Check TP2 (-50% Asian Range)
                if asian_range_pips:
                    tp2_offset = self._pips_to_price(asian_range_pips * 0.50, pair)
                    if t.direction == CascadeDirection.LONG:
                        tp2 = t.entry_price - tp2_offset
                        if l <= t.tp_price:
                            pip_diff = (t.tp_price - t.entry_price) * direction_mult
                            t.pnl_pips = self._price_to_pips(pip_diff, pair)
                            t.exit_time = ts
                            t.exit_price = t.tp_price
                            t.result = "win"
                            t.exit_reason = "tp2_50"
                            all_trades.append(t)
                            daily_pnl += t.pnl_pips
                            trades_to_remove.append(t)
                            targets_hit["tp2_50"] = True
                    else:
                        tp2 = t.entry_price + tp2_offset
                        if h >= t.tp_price:
                            pip_diff = (t.entry_price - t.tp_price) * direction_mult
                            t.pnl_pips = self._price_to_pips(pip_diff, pair)
                            t.exit_time = ts
                            t.exit_price = t.tp_price
                            t.result = "win"
                            t.exit_reason = "tp2_50"
                            all_trades.append(t)
                            daily_pnl += t.pnl_pips
                            trades_to_remove.append(t)
                            targets_hit["tp2_50"] = True

                # Check 132% Kill Switch
                if asian_high is not None and asian_range_pips:
                    kill_offset = self._pips_to_price(asian_range_pips * 1.32, pair)
                    if t.direction == CascadeDirection.LONG:
                        kill_level = asian_high + kill_offset
                        if h >= kill_level:
                            kill_switch_triggered = True
                    else:
                        kill_level = asian_low - kill_offset
                        if l <= kill_level:
                            kill_switch_triggered = True

                # Check hold time (120 min)
                if initial_p90_time is not None:
                    minutes_held = (ts - initial_p90_time).total_seconds() / 60.0
                    if minutes_held >= 120:
                        exit_p = c
                        pip_diff = (exit_p - t.entry_price) * direction_mult
                        t.pnl_pips = self._price_to_pips(pip_diff, pair)
                        t.exit_time = ts
                        t.exit_price = exit_p
                        t.result = "win" if t.pnl_pips > 0 else "loss"
                        t.exit_reason = "hold_time_120min"
                        all_trades.append(t)
                        daily_pnl += t.pnl_pips
                        trades_to_remove.append(t)

            for t in trades_to_remove:
                if t in active_trades:
                    active_trades.remove(t)

            # Kill switch: close all
            if kill_switch_triggered:
                for t in active_trades:
                    if t.exit_time is None:
                        direction_mult = 1 if t.direction == CascadeDirection.LONG else -1
                        pip_diff = (c - t.entry_price) * direction_mult
                        t.pnl_pips = self._price_to_pips(pip_diff, pair)
                        t.exit_time = ts
                        t.exit_price = c
                        t.result = "win" if t.pnl_pips > 0 else "loss"
                        t.exit_reason = "kill_switch_132"
                        all_trades.append(t)
                        daily_pnl += t.pnl_pips
                active_trades.clear()
                continue

            # Skip if outside entry window
            if not self._in_entry_window(est_h):
                continue

            # Skip if no Asian range
            if asian_range_pips is None or asian_range_pips <= 0:
                continue

            # ── P90 Signal Detection ────────────────────────────────────
            candle_body_pips = self._price_to_pips(abs(c - o), pair)
            threshold = self._get_p90_threshold(est_h)

            bull_signal = (c > o) and (candle_body_pips >= threshold)
            bear_signal = (c < o) and (candle_body_pips >= threshold)

            if not bull_signal and not bear_signal:
                continue

            signal_direction = CascadeDirection.LONG if bull_signal else CascadeDirection.SHORT

            # ── Initial P90 (first signal of session) ───────────────────
            if session_direction == CascadeDirection.NONE:
                session_direction = signal_direction
                initial_p90_time = ts
                initial_p90_price = c
                cascade_count = 1
                add_45min_done = False
                targets_hit = {"tp1_25": False, "tp2_50": False}

                # Calculate SL and TP
                sl_pips = candle_body_pips * self.cfg.initial_sl_mult
                sl_offset = self._pips_to_price(sl_pips, pair)
                tp_offset = self._pips_to_price(asian_range_pips * 0.50, pair)

                if signal_direction == CascadeDirection.LONG:
                    sl_price = c - sl_offset
                    tp_price = c - tp_offset  # Mean reversion target
                else:
                    sl_price = c + sl_offset
                    tp_price = c + tp_offset

                trade = CascadeTrade(
                    entry_time=ts,
                    direction=signal_direction,
                    entry_price=c,
                    sl_price=sl_price,
                    tp_price=tp_price,
                    size_lots=position_size,
                    activation_type="initial",
                    cascade_num=0,
                )
                active_trades.append(trade)

            # ── Cascade P90 Check ───────────────────────────────────────
            elif session_direction == signal_direction:
                # Same direction = potential cascade
                if cascade_count >= self.cfg.max_cascades:
                    continue

                # Check timing: within 120 min of initial
                if initial_p90_time is not None:
                    minutes_since = (ts - initial_p90_time).total_seconds() / 60.0
                    if minutes_since > self.cfg.cascade_window_minutes:
                        continue
                    if minutes_since < self.cfg.optimal_cascade_start:
                        continue  # Too soon

                # Check targets not already hit
                if targets_hit["tp2_50"]:
                    continue

                cascade_count += 1

                # Calculate SL using 168% of THIS P90 body
                sl_pips = candle_body_pips * self.cfg.cascade_sl_mult
                sl_offset = self._pips_to_price(sl_pips, pair)
                tp_offset = self._pips_to_price(asian_range_pips * 0.50, pair)

                if signal_direction == CascadeDirection.LONG:
                    sl_price = c - sl_offset
                    tp_price = c - tp_offset
                else:
                    sl_price = c + sl_offset
                    tp_price = c + tp_price

                # Size based on cascade number
                if cascade_count == 2:
                    size = position_size * self.cfg.cascade_size_1 / 0.4  # Scale relative to initial
                    act_type = "cascade_1"
                elif cascade_count == 3:
                    size = position_size * self.cfg.cascade_size_2 / 0.4
                    act_type = "cascade_2"
                else:
                    continue  # 4th+ cascade = AVOID

                trade = CascadeTrade(
                    entry_time=ts,
                    direction=signal_direction,
                    entry_price=c,
                    sl_price=sl_price,
                    tp_price=tp_price,
                    size_lots=size,
                    activation_type=act_type,
                    cascade_num=cascade_count - 1,
                )
                active_trades.append(trade)

            # Opposite direction P90 = IGNORE (noise, not reversal)

            # ── 45-Min Add Check ────────────────────────────────────────
            if (initial_p90_time is not None and
                    not add_45min_done and
                    cascade_count >= 1 and
                    len(active_trades) > 0):

                minutes_since = (ts - initial_p90_time).total_seconds() / 60.0
                if (self.cfg.add_time_minutes <= minutes_since < self.cfg.add_time_minutes + 5):
                    # Check extension achieved
                    if session_direction == CascadeDirection.LONG:
                        extension_pips = self._price_to_pips(c - initial_p90_price, pair)
                    else:
                        extension_pips = self._price_to_pips(initial_p90_price - c, pair)

                    if extension_pips >= self.cfg.add_extension_pips and not kill_switch_triggered:
                        add_45min_done = True
                        tp_offset = self._pips_to_price(asian_range_pips * 0.50, pair)

                        if session_direction == CascadeDirection.LONG:
                            tp_price = initial_p90_price - tp_offset
                            sl_price = initial_p90_price  # Breakeven
                        else:
                            tp_price = initial_p90_price + tp_offset
                            sl_price = initial_p90_price

                        trade = CascadeTrade(
                            entry_time=ts,
                            direction=session_direction,
                            entry_price=c,
                            sl_price=sl_price,
                            tp_price=tp_price,
                            size_lots=position_size * self.cfg.add_size / 0.4,
                            activation_type="add_45min",
                            cascade_num=0,
                        )
                        active_trades.append(trade)

        # ── Calculate Results ───────────────────────────────────────────
        return self._calculate_results(all_trades, pair)

    def _calculate_results(self, trades: List[CascadeTrade], pair: str) -> Dict:
        """Calculate backtest results from completed trades."""
        if not trades:
            return {
                "strategy": "P90_Cascade",
                "pair": pair,
                "total_trades": 0,
                "error": "No trades generated",
            }

        pnls = [t.pnl_pips for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        total_pnl = sum(pnls)
        win_rate = len(wins) / len(pnls) * 100 if pnls else 0
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0

        # Max drawdown
        cumulative = [0]
        for p in pnls:
            cumulative.append(cumulative[-1] + p)
        peak = cumulative[0]
        max_dd = 0
        for v in cumulative:
            if v > peak:
                peak = v
            dd = v - peak
            if dd < max_dd:
                max_dd = dd

        # Profit factor
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # By activation type
        by_type = {}
        for t in trades:
            at = t.activation_type
            if at not in by_type:
                by_type[at] = {"trades": 0, "wins": 0, "pnl": 0}
            by_type[at]["trades"] += 1
            by_type[at]["pnl"] += t.pnl_pips
            if t.pnl_pips > 0:
                by_type[at]["wins"] += 1

        by_type_summary = {}
        for at, data in by_type.items():
            by_type_summary[at] = {
                "trades": data["trades"],
                "wins": data["wins"],
                "win_rate": round(data["wins"] / data["trades"] * 100, 1) if data["trades"] > 0 else 0,
                "pnl_pips": round(data["pnl"], 2),
            }

        # By exit reason
        by_exit = {}
        for t in trades:
            er = t.exit_reason
            if er not in by_exit:
                by_exit[er] = 0
            by_exit[er] += 1

        return {
            "strategy": "P90_Cascade",
            "pair": pair,
            "total_trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 1),
            "total_pnl_pips": round(total_pnl, 2),
            "avg_win_pips": round(avg_win, 2),
            "avg_loss_pips": round(avg_loss, 2),
            "max_drawdown_pips": round(max_dd, 2),
            "profit_factor": round(profit_factor, 2),
            "by_activation_type": by_type_summary,
            "by_exit_reason": by_exit,
            "trades": [
                {
                    "entry_time": str(t.entry_time),
                    "direction": t.direction.value,
                    "entry": t.entry_price,
                    "exit": t.exit_price,
                    "pnl_pips": round(t.pnl_pips, 2),
                    "result": t.result,
                    "reason": t.exit_reason,
                    "type": t.activation_type,
                }
                for t in trades[:100]  # First 100 for inspection
            ],
        }


# ── Standalone Runner ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    from pathlib import Path

    # Load data
    data_path = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")

    if not data_path.exists():
        print(f"❌ Data file not found: {data_path}")
        sys.exit(1)

    print(f"📂 Loading data from {data_path.name}...")

    # Parse CSV
    sys.path.insert(0, str(Path(__file__).parent))
    from data_loader import _parse_csv
    df = _parse_csv(data_path)

    if df.empty:
        print("❌ No data parsed")
        sys.exit(1)

    print(f"  ✅ Loaded {len(df):,} bars ({df.index[0]} → {df.index[-1]})")

    # Run backtest
    strategy = P90CascadeStrategy()
    results = strategy.run_backtest(df, pair="EUR/USD")

    # Display results
    print(f"\n{'='*60}")
    print(f"📊 P90 CASCADE BACKTEST RESULTS")
    print(f"{'='*60}")
    print(f"  Total Trades:   {results.get('total_trades', 0)}")
    print(f"  Wins:           {results.get('wins', 0)} ({results.get('win_rate', 0)}%)")
    print(f"  Losses:         {results.get('losses', 0)}")
    print(f"  Total P&L:      {results.get('total_pnl_pips', 0)} pips")
    print(f"  Avg Win:        {results.get('avg_win_pips', 0)} pips")
    print(f"  Avg Loss:       {results.get('avg_loss_pips', 0)} pips")
    print(f"  Max Drawdown:   {results.get('max_drawdown_pips', 0)} pips")
    print(f"  Profit Factor:  {results.get('profit_factor', 0)}")

    if "by_activation_type" in results:
        print(f"\n  By Activation Type:")
        for at, data in results["by_activation_type"].items():
            print(f"    {at:15s}: {data['trades']} trades | {data['win_rate']}% WR | {data['pnl_pips']} pips")

    if "by_exit_reason" in results:
        print(f"\n  By Exit Reason:")
        for reason, count in sorted(results["by_exit_reason"].items(), key=lambda x: -x[1]):
            print(f"    {reason:20s}: {count}")

    print(f"{'='*60}")

    # Save results
    results_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results")
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"p90_cascade_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Results saved to {results_file}")
