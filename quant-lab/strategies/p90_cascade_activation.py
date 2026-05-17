"""
P90 Cascade Activation Strategy — CEREBUS FX v4.0 (Part 2, Pages 10-15)
=========================================================================

Nautilus Trader native strategy implementing the full P90 Cascade Activation
system from the CEREBUS FX manual Part 2.

CASCADE ACTIVATION LOGIC:
  1. Initial P90 (Bias Setter): First P90 candle in 2-11 AM EST window
     -> Establishes direction of constraint resolution for session
     -> Size: 40% | Boundary: 80% of P90 body | Target: -50% Asian Range

  2. Cascade P90 (Momentum Confirmation): Subsequent P90 in SAME direction
     -> Must occur within 120 min of Initial P90 (optimal: 30-90 min)
     -> Size: 20% | Boundary: 168% of THIS P90 body (Stall Zone)
     -> Target: -50% Asian Range

  3. Cascade 2 P90 (Sustained Momentum): Third P90 in same direction
     -> Size: 10% | Boundary: 168% of THIS P90 body
     -> Max 3 cascades per session (4th+ = AVOID, 76.4% WR)

  4. 45-Min Add: Time-based add after 45min + 8p extension
     -> Size: 30% | Boundary: Breakeven | Target: -50% Asian Range

CASCADE + 45-MIN ADD COMBO (Highest Conviction):
  When BOTH trigger: Signal 1 (40%) + 45-Min Add (30%) + Cascade P90 (30%)
  Combined Win Rate: 93.4%

CASCADE STATISTICS (from manual):
  1st P90:  83.3% WR | Baseline
  2nd P90:  87.8% WR | BEST (+5.4% edge)
  3rd P90:  84.2% WR | GOOD
  4th+ P90: 76.4% WR | AVOID

OPTIMAL CASCADE TIMING:
  45-60 min after initial P90 = 88.2% WR (sweet spot)
  Skip cascades after 90 min from initial activation

Author: Quant Lab — CEREBUS FX v4.0 Strategy Reconstruction
File: quant-lab/strategies/p90_cascade_activation.py
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from enum import Enum

import pandas as pd
import numpy as np


# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════════

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


class ActivationType(str, Enum):
    INITIAL = "initial"
    CASCADE_1 = "cascade_1"
    CASCADE_2 = "cascade_2"
    ADD_45MIN = "add_45min"


# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

class P90CascadeConfig:
    """
    Full configuration for P90 Cascade Activation Strategy.
    All parameters sourced from CEREBUS FX v4.0 manual Part 2 (pages 10-15).
    """

    def __init__(self):
        # Session Timing (EST). UTC = EST + 5
        self.asian_start_est = 19
        self.asian_end_est = 3
        self.entry_start_est = 2
        self.entry_end_est = 11
        self.hard_exit_est = 12

        # P90 candle body thresholds by EST time window (pips)
        self.p90_thresholds = {
            (2, 4): 4.1,
            (4, 6): 4.6,
            (6, 8): 4.6,
            (8, 10): 5.9,
            (10, 11): 6.2,
        }

        # P90 candle quality: body must be > 60% of total range
        self.p90_body_pct = 0.60

        # Tier system (Asian Range -> Position Sizing)
        self.tier_config = {
            "T1": {"max_pips": 20, "size_pct": 1.0, "expansion": 3.12},
            "T2": {"min_pips": 20, "max_pips": 30, "size_pct": 0.75, "expansion": 2.68},
            "T3": {"min_pips": 30, "max_pips": 45, "size_pct": 0.50, "expansion": 2.18},
            "NO_GO": {"min_pips": 45, "size_pct": 0.0, "expansion": 1.52},
        }

        # Cascade parameters
        self.max_cascades = 3
        self.cascade_window_min = 30
        self.cascade_window_max = 90
        self.cascade_sl_mult = 1.68
        self.cascade_size_1 = 0.20
        self.cascade_size_2 = 0.10

        # 45-min add parameters
        self.add_time_minutes = 45
        self.add_time_window = 5
        self.add_extension_pips = 8.0
        self.add_size = 0.30

        # Initial P90 sizing
        self.initial_size = 0.40
        self.initial_sl_mult = 0.80

        # Risk management
        self.max_drawdown_pct = 0.50
        self.daily_loss_limit_pct = 0.40
        self.hold_time_minutes = 120
        self.kill_switch_pct = 1.32

        # Target levels
        self.tp1_pct = 0.25
        self.tp2_pct = 0.50

        # Position sizing
        self.position_size_lots = 0.1
        self.initial_risk_pct = 0.12


# ═══════════════════════════════════════════════════════════════════════════════
# Trade Record
# ═══════════════════════════════════════════════════════════════════════════════

class CascadeTrade:
    """Represents a single cascade trade activation."""

    def __init__(self, entry_time, direction: CascadeDirection, entry_price: float,
                 sl_price: float, tp_price: float, size_lots: float,
                 activation_type: ActivationType, cascade_num: int = 0):
        self.entry_time = entry_time
        self.direction = direction
        self.entry_price = entry_price
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.size_lots = size_lots
        self.activation_type = activation_type
        self.cascade_num = cascade_num
        self.exit_time = None
        self.exit_price = None
        self.pnl_pips = 0.0
        self.result = ""
        self.exit_reason = ""


# ═══════════════════════════════════════════════════════════════════════════════
# P90 Cascade Activation Strategy
# ═══════════════════════════════════════════════════════════════════════════════

class P90CascadeActivationStrategy:
    """
    P90 Cascade Activation Strategy — CEREBUS FX v4.0 (Part 2)

    Implements the full cascade system:
    - Initial P90 sets direction of constraint resolution
    - Subsequent P90s in same direction = cascade activations
    - 45-min time-based add
    - Combined cascade + add for 93.4% win rate (highest conviction)

    This is a CONTINUATION strategy:
    - Bullish P90 = LONG, TP above Asian High
    - Bearish P90 = SHORT, TP below Asian Low
    """

    def __init__(self, config: P90CascadeConfig = None):
        self.cfg = config or P90CascadeConfig()
        self.trades: List[CascadeTrade] = []

    # -- Time Helpers ----------------------------------------------------------

    @staticmethod
    def _utc_to_est(utc_hour: int) -> int:
        return (utc_hour - 5 + 24) % 24

    def _get_est_hour(self, ts) -> int:
        return self._utc_to_est(ts.hour)

    def _in_asian_session(self, est_h: int) -> bool:
        return est_h >= self.cfg.asian_start_est or est_h <= self.cfg.asian_end_est

    def _in_entry_window(self, est_h: int) -> bool:
        return self.cfg.entry_start_est <= est_h < self.cfg.entry_end_est

    def _is_hard_exit_time(self, est_h: int) -> bool:
        return est_h >= self.cfg.hard_exit_est

    # -- P90 Signal Detection --------------------------------------------------

    def _get_p90_threshold(self, est_h: int) -> float:
        for (start, end), threshold in self.cfg.p90_thresholds.items():
            if start <= est_h < end:
                return threshold
        return 6.2

    def _is_p90_candle(self, o: float, h: float, l: float, c: float) -> bool:
        total_range = h - l
        if total_range <= 0:
            return False
        body_size = abs(c - o)
        return (body_size / total_range) > self.cfg.p90_body_pct

    def _check_p90_signal(self, o: float, h: float, l: float, c: float,
                          est_h: int) -> Tuple[bool, CascadeDirection]:
        if not self._is_p90_candle(o, h, l, c):
            return False, CascadeDirection.NONE
        body_pips = self._to_pips(abs(c - o))
        threshold = self._get_p90_threshold(est_h)
        if body_pips < threshold:
            return False, CascadeDirection.NONE
        if c > o:
            return True, CascadeDirection.LONG
        elif c < o:
            return True, CascadeDirection.SHORT
        return False, CascadeDirection.NONE

    # -- Tier Classification ---------------------------------------------------

    def _get_tier(self, ar_pips: float) -> TierStatus:
        if ar_pips < 20:
            return TierStatus.T1
        elif ar_pips < 30:
            return TierStatus.T2
        elif ar_pips < 45:
            return TierStatus.T3
        else:
            return TierStatus.NO_GO

    # -- Pip/Price Conversion --------------------------------------------------

    @staticmethod
    def _to_pips(price_diff: float, pair: str = "EUR/USD") -> float:
        if "JPY" in pair:
            return price_diff * 100
        elif "XAU" in pair:
            return price_diff * 10
        return price_diff * 10000

    @staticmethod
    def _to_price(pips: float, pair: str = "EUR/USD") -> float:
        if "JPY" in pair:
            return pips / 100
        elif "XAU" in pair:
            return pips / 10
        return pips / 10000

    # -- Backtest Engine -------------------------------------------------------

    def run_backtest(self, df: pd.DataFrame, pair: str = "EUR/USD",
                     max_bars: int = None) -> Dict:
        if df is None or len(df) < 500:
            return {"error": "Insufficient data", "total_trades": 0}

        df = df.copy()
        if max_bars and len(df) > max_bars:
            df = df.tail(max_bars).copy()

        if df.index.tz is not None:
            df.index = df.index.tz_convert(None)

        df["est_hour"] = df.index.hour.map(self._utc_to_est)
        df["date"] = df.index.date

        # State
        asian_high = None
        asian_low = None
        asian_range_pips = None
        tier = TierStatus.NA
        asian_range_complete = False

        session_direction = CascadeDirection.NONE
        initial_p90_time = None
        initial_p90_price = None
        initial_p90_body_pips = None
        cascade_count = 0
        add_45min_done = False
        kill_switch_triggered = False

        active_trades: List[CascadeTrade] = []
        all_trades: List[CascadeTrade] = []

        daily_pnl = 0.0
        last_date = None
        daily_loss_limit_hit = False

        position_size = self.cfg.position_size_lots

        for i in range(50, len(df) - 1):
            row = df.iloc[i]
            ts = df.index[i]
            est_h = int(row["est_hour"])
            date = row["date"]
            o = float(row["open"])
            h = float(row["high"])
            l = float(row["low"])
            c = float(row["close"])

            # New Day Reset
            if date != last_date:
                for t in active_trades:
                    if t.exit_time is None:
                        direction_mult = 1 if t.direction == CascadeDirection.LONG else -1
                        pip_diff = self._to_pips((c - t.entry_price) * direction_mult, pair)
                        t.pnl_pips = pip_diff
                        t.exit_time = ts
                        t.exit_price = c
                        t.result = "win" if t.pnl_pips > 0 else "loss"
                        t.exit_reason = "new_day"
                        all_trades.append(t)
                        daily_pnl += t.pnl_pips
                active_trades = [t for t in active_trades if t.exit_time is None]

                asian_high = None
                asian_low = None
                asian_range_pips = None
                tier = TierStatus.NA
                asian_range_complete = False
                session_direction = CascadeDirection.NONE
                initial_p90_time = None
                initial_p90_price = None
                initial_p90_body_pips = None
                cascade_count = 0
                add_45min_done = False
                kill_switch_triggered = False
                daily_pnl = 0.0
                daily_loss_limit_hit = False
                last_date = date

            # Asian Range Calculation (7PM-3AM EST)
            if self._in_asian_session(est_h):
                if asian_high is None:
                    asian_high = h
                    asian_low = l
                else:
                    asian_high = max(asian_high, h)
                    asian_low = min(asian_low, l)
                if est_h == self.cfg.asian_end_est and asian_high is not None:
                    asian_range_pips = self._to_pips(asian_high - asian_low, pair)
                    tier = self._get_tier(asian_range_pips)
                    asian_range_complete = True
                continue

            if not asian_range_complete:
                continue
            if tier == TierStatus.NO_GO:
                continue
            if daily_loss_limit_hit:
                continue

            # Hard Exit (12PM EST)
            if self._is_hard_exit_time(est_h):
                for t in active_trades:
                    if t.exit_time is None:
                        direction_mult = 1 if t.direction == CascadeDirection.LONG else -1
                        pip_diff = self._to_pips((c - t.entry_price) * direction_mult, pair)
                        t.pnl_pips = pip_diff
                        t.exit_time = ts
                        t.exit_price = c
                        t.result = "win" if t.pnl_pips > 0 else "loss"
                        t.exit_reason = "hard_exit_12pm"
                        all_trades.append(t)
                        daily_pnl += t.pnl_pips
                active_trades = [t for t in active_trades if t.exit_time is None]
                session_direction = CascadeDirection.NONE
                continue

            # Manage Active Trades
            trades_to_remove = []
            for t in active_trades:
                if t.exit_time is not None:
                    continue

                is_long = t.direction == CascadeDirection.LONG

                # SL check
                if is_long and l <= t.sl_price:
                    t.pnl_pips = self._to_pips(t.sl_price - t.entry_price, pair)
                    t.exit_time = ts
                    t.exit_price = t.sl_price
                    t.result = "loss"
                    t.exit_reason = "sl"
                    all_trades.append(t)
                    daily_pnl += t.pnl_pips
                    trades_to_remove.append(t)
                    continue
                elif not is_long and h >= t.sl_price:
                    t.pnl_pips = self._to_pips(t.entry_price - t.sl_price, pair)
                    t.exit_time = ts
                    t.exit_price = t.sl_price
                    t.result = "loss"
                    t.exit_reason = "sl"
                    all_trades.append(t)
                    daily_pnl += t.pnl_pips
                    trades_to_remove.append(t)
                    continue

                # TP check
                if is_long and h >= t.tp_price:
                    t.pnl_pips = self._to_pips(t.tp_price - t.entry_price, pair)
                    t.exit_time = ts
                    t.exit_price = t.tp_price
                    t.result = "win"
                    t.exit_reason = "tp_50"
                    all_trades.append(t)
                    daily_pnl += t.pnl_pips
                    trades_to_remove.append(t)
                    continue
                elif not is_long and l <= t.tp_price:
                    t.pnl_pips = self._to_pips(t.entry_price - t.tp_price, pair)
                    t.exit_time = ts
                    t.exit_price = t.tp_price
                    t.result = "win"
                    t.exit_reason = "tp_50"
                    all_trades.append(t)
                    daily_pnl += t.pnl_pips
                    trades_to_remove.append(t)
                    continue

                # 132% Kill Switch
                if asian_high is not None and asian_range_pips:
                    kill_offset = self._to_price(asian_range_pips * self.cfg.kill_switch_pct, pair)
                    if is_long:
                        kill_level = asian_high + kill_offset
                        if h >= kill_level:
                            kill_switch_triggered = True
                    else:
                        kill_level = asian_low - kill_offset
                        if l <= kill_level:
                            kill_switch_triggered = True

                # Hold time (120 min)
                if initial_p90_time is not None:
                    minutes_held = (ts - initial_p90_time).total_seconds() / 60.0
                    if minutes_held >= self.cfg.hold_time_minutes:
                        direction_mult = 1 if is_long else -1
                        pip_diff = self._to_pips((c - t.entry_price) * direction_mult, pair)
                        t.pnl_pips = pip_diff
                        t.exit_time = ts
                        t.exit_price = c
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
                        pip_diff = self._to_pips((c - t.entry_price) * direction_mult, pair)
                        t.pnl_pips = pip_diff
                        t.exit_time = ts
                        t.exit_price = c
                        t.result = "win" if t.pnl_pips > 0 else "loss"
                        t.exit_reason = "kill_switch_132"
                        all_trades.append(t)
                        daily_pnl += t.pnl_pips
                active_trades = [t for t in active_trades if t.exit_time is None]
                continue

            if not self._in_entry_window(est_h):
                continue
            if asian_range_pips is None or asian_range_pips <= 0:
                continue

            # P90 Signal Detection
            is_signal, signal_direction = self._check_p90_signal(o, h, l, c, est_h)
            if not is_signal:
                continue

            candle_body_pips = self._to_pips(abs(c - o), pair)

            # STEP 1: Initial P90
            if session_direction == CascadeDirection.NONE:
                session_direction = signal_direction
                initial_p90_time = ts
                initial_p90_price = c
                initial_p90_body_pips = candle_body_pips
                cascade_count = 1
                add_45min_done = False

                sl_pips = candle_body_pips * self.cfg.initial_sl_mult
                sl_offset = self._to_price(sl_pips, pair)
                tp_offset = self._to_price(asian_range_pips * self.cfg.tp2_pct, pair)

                if signal_direction == CascadeDirection.LONG:
                    sl_price = c - sl_offset
                    tp_price = asian_high + tp_offset
                else:
                    sl_price = c + sl_offset
                    tp_price = asian_low - tp_offset

                trade = CascadeTrade(
                    entry_time=ts, direction=signal_direction, entry_price=c,
                    sl_price=sl_price, tp_price=tp_price, size_lots=position_size,
                    activation_type=ActivationType.INITIAL, cascade_num=0,
                )
                active_trades.append(trade)

            # STEP 3: Cascade P90 (same direction)
            elif session_direction == signal_direction:
                if cascade_count >= self.cfg.max_cascades:
                    continue
                if initial_p90_time is not None:
                    minutes_since = (ts - initial_p90_time).total_seconds() / 60.0
                    if minutes_since < self.cfg.cascade_window_min:
                        continue
                    if minutes_since > self.cfg.cascade_window_max:
                        continue

                cascade_count += 1

                sl_pips = candle_body_pips * self.cfg.cascade_sl_mult
                sl_offset = self._to_price(sl_pips, pair)
                tp_offset = self._to_price(asian_range_pips * self.cfg.tp2_pct, pair)

                if signal_direction == CascadeDirection.LONG:
                    sl_price = c - sl_offset
                    tp_price = asian_high + tp_offset
                else:
                    sl_price = c + sl_offset
                    tp_price = asian_low - tp_offset

                if cascade_count == 2:
                    size = position_size * self.cfg.cascade_size_1 / self.cfg.initial_size
                    act_type = ActivationType.CASCADE_1
                elif cascade_count == 3:
                    size = position_size * self.cfg.cascade_size_2 / self.cfg.initial_size
                    act_type = ActivationType.CASCADE_2
                else:
                    continue

                trade = CascadeTrade(
                    entry_time=ts, direction=signal_direction, entry_price=c,
                    sl_price=sl_price, tp_price=tp_price, size_lots=size,
                    activation_type=act_type, cascade_num=cascade_count - 1,
                )
                active_trades.append(trade)

            # Opposite direction = IGNORE

            # STEP 2: 45-Min Add Check
            if (initial_p90_time is not None and not add_45min_done and
                    cascade_count >= 1 and len(active_trades) > 0):

                minutes_since = (ts - initial_p90_time).total_seconds() / 60.0
                add_start = self.cfg.add_time_minutes
                add_end = add_start + self.cfg.add_time_window

                if add_start <= minutes_since < add_end:
                    if session_direction == CascadeDirection.LONG:
                        extension_pips = self._to_pips(c - initial_p90_price, pair)
                    else:
                        extension_pips = self._to_pips(initial_p90_price - c, pair)

                    if extension_pips >= self.cfg.add_extension_pips and not kill_switch_triggered:
                        add_45min_done = True
                        tp_offset = self._to_price(asian_range_pips * self.cfg.tp2_pct, pair)

                        if session_direction == CascadeDirection.LONG:
                            tp_price = asian_high + tp_offset
                            sl_price = initial_p90_price
                        else:
                            tp_price = asian_low - tp_offset
                            sl_price = initial_p90_price

                        trade = CascadeTrade(
                            entry_time=ts, direction=session_direction, entry_price=c,
                            sl_price=sl_price, tp_price=tp_price,
                            size_lots=position_size * self.cfg.add_size / self.cfg.initial_size,
                            activation_type=ActivationType.ADD_45MIN, cascade_num=0,
                        )
                        active_trades.append(trade)

        return self._calculate_results(all_trades, pair)

    # -- Results Calculation ---------------------------------------------------

    def _calculate_results(self, trades: List[CascadeTrade], pair: str) -> Dict:
        if not trades:
            return {"strategy": "P90_Cascade_Activation", "pair": pair,
                    "total_trades": 0, "error": "No trades generated"}

        pnls = [t.pnl_pips for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        total_pnl = sum(pnls)
        win_rate = len(wins) / len(pnls) * 100 if pnls else 0
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0

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

        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        by_type = {}
        for t in trades:
            at = t.activation_type.value
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

        by_exit = {}
        for t in trades:
            er = t.exit_reason
            if er not in by_exit:
                by_exit[er] = 0
            by_exit[er] += 1

        session_dates = set()
        for t in trades:
            session_dates.add(t.entry_time.date())

        return {
            "strategy": "P90_Cascade_Activation",
            "pair": pair,
            "total_trades": len(trades),
            "total_sessions": len(session_dates),
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
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Standalone Runner
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json

    data_path = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")

    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        sys.exit(1)

    print(f"Loading {data_path.name}...")

    # Simple CSV parser (no nautilus_trader dependency)
    def _parse_simple(fp):
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            raw = f.readlines()
        records = []
        for line in raw[1:]:
            parts = line.strip().split()
            if len(parts) < 7:
                continue
            try:
                ts = datetime.strptime(f"{parts[0]} {parts[1]}", "%Y.%m.%d %H:%M:%S")
                records.append({"timestamp": ts, "open": float(parts[2]),
                                "high": float(parts[3]), "low": float(parts[4]),
                                "close": float(parts[5])})
            except (ValueError, IndexError):
                continue
        d = pd.DataFrame(records)
        d.set_index("timestamp", inplace=True)
        d.sort_index(inplace=True)
        return d

    df = _parse_simple(data_path)

    if df.empty:
        print("No data parsed")
        sys.exit(1)

    print(f"  Loaded {len(df):,} bars ({df.index[0]} -> {df.index[-1]})")

    strategy = P90CascadeActivationStrategy()
    results = strategy.run_backtest(df, pair="EUR/USD")

    print(f"\n{'='*60}")
    print(f"P90 CASCADE ACTIVATION BACKTEST RESULTS")
    print(f"{'='*60}")
    print(f"  Total Trades:   {results.get('total_trades', 0)}")
    print(f"  Total Sessions: {results.get('total_sessions', 0)}")
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
            print(f"    {reason:25s}: {count}")

    print(f"{'='*60}")

    results_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtests")
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"p90_cascade_activation_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {results_file}")
