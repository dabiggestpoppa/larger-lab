"""
P90 Cascade Activation Strategy v2 — CEREBUS FX v4.0 (Part 2)
==============================================================

FIXED: Proper continuation logic (not mean reversion).
P90 candle direction = resolution direction.
Targets extend BEYOND the Asian Range in the candle's direction.

CASCADE STATISTICS (from manual):
  1st P90:  83.3% WR
  2nd P90:  87.8% WR (BEST)
  3rd P90:  84.2% WR
  4th+ P90: 76.4% WR (AVOID)

Author: Quant Lab — CEREBUS FX v4.0 Strategy Reconstruction v2
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from enum import Enum

import pandas as pd
import numpy as np


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


class CascadeConfig:
    def __init__(self):
        # Session timing (EST). UTC = EST + 5
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

        # Tier config
        self.tier_config = {
            "T1": {"max_pips": 20, "size_pct": 1.0, "expansion": 3.12},
            "T2": {"min_pips": 20, "max_pips": 30, "size_pct": 0.75, "expansion": 2.68},
            "T3": {"min_pips": 30, "max_pips": 45, "size_pct": 0.50, "expansion": 2.18},
            "NO_GO": {"min_pips": 45, "size_pct": 0.0, "expansion": 1.52},
        }

        # Cascade parameters
        self.max_cascades = 3
        self.cascade_window_minutes = 120
        self.optimal_cascade_start = 30
        self.optimal_cascade_end = 90
        self.cascade_size_1 = 0.20
        self.cascade_size_2 = 0.10
        self.cascade_sl_mult = 1.68

        # 45-min add parameters
        self.add_time_minutes = 45
        self.add_extension_pips = 8.0
        self.add_size = 0.30

        # Initial P90 sizing
        self.initial_size = 0.40
        self.initial_sl_mult = 0.80

        # Risk
        self.max_drawdown_pct = 0.5
        self.daily_loss_limit_pct = 0.40
        self.position_size_lots = 0.1


class CascadeTrade:
    def __init__(self, entry_time, direction, entry_price, sl_price, tp_price,
                 size_lots, activation_type, cascade_num=0):
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


class P90CascadeStrategyV2:
    """
    P90 Cascade Activation Strategy v2.

    KEY FIX: This is a CONTINUATION strategy, not mean reversion.
    - Bullish P90 = LONG, TP above entry, SL below entry
    - Bearish P90 = SHORT, TP below entry, SL above entry
    - Targets: -25% and -50% of Asian Range BEYOND the Asian Range boundary
    """

    def __init__(self, config: CascadeConfig = None):
        self.cfg = config or CascadeConfig()
        self.trades: List[CascadeTrade] = []

    @staticmethod
    def _utc_to_est(utc_hour: int) -> int:
        return (utc_hour - 5 + 24) % 24

    def _get_est_hour(self, ts) -> int:
        return self._utc_to_est(ts.hour)

    def _in_asian(self, est_h: int) -> bool:
        return est_h >= self.cfg.asian_start_est or est_h < self.cfg.asian_end_est

    def _in_entry_window(self, est_h: int) -> bool:
        return self.cfg.entry_start_est <= est_h < self.cfg.entry_end_est

    def _is_hard_exit(self, est_h: int) -> bool:
        return est_h >= self.cfg.hard_exit_est

    def _get_threshold(self, est_h: int) -> float:
        for (start, end), threshold in self.cfg.p90_thresholds.items():
            if start <= est_h < end:
                return threshold
        return 6.2

    def _get_tier(self, ar_pips: float) -> TierStatus:
        if ar_pips < 20:
            return TierStatus.T1
        elif ar_pips < 30:
            return TierStatus.T2
        elif ar_pips < 45:
            return TierStatus.T3
        else:
            return TierStatus.NO_GO

    @staticmethod
    def _to_pips(price_diff: float, pair: str = "EUR/USD") -> float:
        if "JPY" in pair:
            return price_diff * 100
        return price_diff * 10000

    @staticmethod
    def _to_price(pips: float, pair: str = "EUR/USD") -> float:
        if "JPY" in pair:
            return pips / 100
        return pips / 10000

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

        # ── State Variables ────────────────────────────────────────────
        asian_high = None
        asian_low = None
        asian_range_pips = None
        tier = TierStatus.NA
        asian_range_complete = False

        # Session state
        session_direction = CascadeDirection.NONE
        initial_p90_time = None
        initial_p90_price = None
        initial_p90_body_pips = None
        cascade_count = 0
        add_45min_done = False
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
            est_h = int(row["est_hour"])
            date = row["date"]
            o = float(row["open"])
            h = float(row["high"])
            l = float(row["low"])
            c = float(row["close"])

            # ── New Day Reset ───────────────────────────────────────────
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

            # ── Asian Range Calculation (7PM-3AM EST) ───────────────────
            if self._in_asian(est_h):
                if asian_high is None:
                    asian_high = h
                    asian_low = l
                else:
                    asian_high = max(asian_high, h)
                    asian_low = min(asian_low, l)
                # At 3AM EST, finalize Asian Range
                if est_h == self.cfg.asian_end_est:
                    if asian_high is not None and asian_low is not None:
                        asian_range_pips = self._to_pips(asian_high - asian_low, pair)
                        tier = self._get_tier(asian_range_pips)
                        asian_range_complete = True
                continue

            # Skip if Asian range not yet complete
            if not asian_range_complete:
                continue

            # Skip NO-GO days
            if tier == TierStatus.NO_GO:
                continue

            # Skip if daily loss limit hit
            if daily_loss_limit_hit:
                continue

            # ── Hard Exit (12PM EST) ────────────────────────────────────
            if self._is_hard_exit(est_h):
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

            # ── Manage Active Trades ────────────────────────────────────
            trades_to_remove = []
            for t in active_trades:
                if t.exit_time is not None:
                    continue

                is_long = t.direction == CascadeDirection.LONG

                # Check SL
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

                # Check TP (-50% of Asian Range from Asian boundary)
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

                # Check 132% Kill Switch
                if asian_high is not None and asian_range_pips:
                    kill_offset = self._to_price(asian_range_pips * 1.32, pair)
                    if is_long:
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

            # Skip if outside entry window
            if not self._in_entry_window(est_h):
                continue

            # Skip if no Asian range
            if asian_range_pips is None or asian_range_pips <= 0:
                continue

            # ── P90 Signal Detection ────────────────────────────────────
            candle_body_pips = self._to_pips(abs(c - o), pair)
            threshold = self._get_threshold(est_h)

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
                initial_p90_body_pips = candle_body_pips
                cascade_count = 1
                add_45min_done = False

                # Calculate SL and TP
                # SL: 80% of P90 body below entry (for LONG) or above entry (for SHORT)
                sl_pips = candle_body_pips * self.cfg.initial_sl_mult
                sl_offset = self._to_price(sl_pips, pair)

                # TP: -50% of Asian Range BEYOND the Asian boundary
                # For LONG: TP = asian_high + (asian_range * 0.50) — continuation above range
                # For SHORT: TP = asian_low - (asian_range * 0.50) — continuation below range
                tp_offset = self._to_price(asian_range_pips * 0.50, pair)

                if signal_direction == CascadeDirection.LONG:
                    sl_price = c - sl_offset
                    tp_price = asian_high + tp_offset
                else:
                    sl_price = c + sl_offset
                    tp_price = asian_low - tp_offset

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

            # ── Cascade P90 Check (same direction) ──────────────────────
            elif session_direction == signal_direction:
                if cascade_count >= self.cfg.max_cascades:
                    continue

                if initial_p90_time is not None:
                    minutes_since = (ts - initial_p90_time).total_seconds() / 60.0
                    if minutes_since > self.cfg.cascade_window_minutes:
                        continue
                    if minutes_since < self.cfg.optimal_cascade_start:
                        continue

                cascade_count += 1

                # SL: 168% of THIS P90 body
                sl_pips = candle_body_pips * self.cfg.cascade_sl_mult
                sl_offset = self._to_price(sl_pips, pair)
                tp_offset = self._to_price(asian_range_pips * 0.50, pair)

                if signal_direction == CascadeDirection.LONG:
                    sl_price = c - sl_offset
                    tp_price = asian_high + tp_offset
                else:
                    sl_price = c + sl_offset
                    tp_price = asian_low - tp_offset

                if cascade_count == 2:
                    size = position_size * self.cfg.cascade_size_1 / 0.4
                    act_type = "cascade_1"
                elif cascade_count == 3:
                    size = position_size * self.cfg.cascade_size_2 / 0.4
                    act_type = "cascade_2"
                else:
                    continue

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

            # ── 45-Min Add Check ────────────────────────────────────────
            if (initial_p90_time is not None and
                    not add_45min_done and
                    cascade_count >= 1 and
                    len(active_trades) > 0):

                minutes_since = (ts - initial_p90_time).total_seconds() / 60.0
                if (self.cfg.add_time_minutes <= minutes_since < self.cfg.add_time_minutes + 5):
                    # Check extension achieved
                    if session_direction == CascadeDirection.LONG:
                        extension_pips = self._to_pips(c - initial_p90_price, pair)
                    else:
                        extension_pips = self._to_pips(initial_p90_price - c, pair)

                    if extension_pips >= self.cfg.add_extension_pips and not kill_switch_triggered:
                        add_45min_done = True
                        tp_offset = self._to_price(asian_range_pips * 0.50, pair)

                        if session_direction == CascadeDirection.LONG:
                            tp_price = asian_high + tp_offset
                            sl_price = initial_p90_price  # Breakeven
                        else:
                            tp_price = asian_low - tp_offset
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
        if not trades:
            return {"strategy": "P90_Cascade_v2", "pair": pair, "total_trades": 0, "error": "No trades generated"}

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
            "strategy": "P90_Cascade_v2",
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


# ── Standalone Runner ────────────────────────────────────────────────────────

if __name__ == "__main__":
    data_path = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")

    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        sys.exit(1)

    print(f"Loading {data_path.name}...")
    sys.path.insert(0, str(Path(__file__).parent))
    from data_loader import _parse_csv
    df = _parse_csv(data_path)
    print(f"  Loaded {len(df):,} bars ({df.index[0]} -> {df.index[-1]})")

    strategy = P90CascadeStrategyV2()
    results = strategy.run_backtest(df, pair="EUR/USD")

    print(f"\n{'='*60}")
    print(f"P90 CASCADE v2 BACKTEST RESULTS")
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

    # Save results
    results_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results")
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"p90_cascade_v2_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {results_file}")
