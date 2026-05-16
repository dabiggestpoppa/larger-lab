"""
P90 Cascade + 45-Min Add Combo Strategy — CEREBUS FX v4.0 (Part 2-3, Pages 10-16)
===================================================================================

HIGHEST CONVICTION strategy from the manual: Combined Win Rate = 93.4%

FULL CASCADE + 45-MIN ADD COMBO PROTOCOL:
  Step 1: Initial P90 Activation (2-11 AM EST)
    -> Wait for P90 candle close >= time-dependent threshold
    -> Activate 40% size | Boundary: 80% of P90 body | Target: -50% Asian Range
    -> Set direction of constraint resolution (LONG or SHORT)
    -> Start 120-min cascade window timer

  Step 2: 45-Min Add Check (+45 min from Signal 1)
    -> Check if resolution output extended +8 pips from entry
    -> If YES: Activate 30% size | Boundary: Breakeven | Target: -50% Asian Range
    -> If NO: Skip, wait for cascade signal

  Step 3: Cascade P90 Check (30-90 min from Signal 1)
    -> Watch for new P90 candle in SAME direction
    -> If SAME: Activate 20% size | Boundary: 168% of THIS P90 body
    -> If OPPOSITE: IGNORE (noise, not reversal)

  Step 4: Cascade 2 P90 Check (60-90 min from Signal 1)
    -> If SAME direction: Activate 10% size | Boundary: 168% of THIS P90 body
    -> STOP here (max 3 cascades)

  Step 5: Exit Management
    -> TP1 (-25% Asian Range): Close 50% of total position, move SL to breakeven
    -> TP2 (-50% Asian Range): Close remaining
    -> Hard Exit (12 PM EST): Close ALL
    -> Kill Switch (132% Asian Range): Close ALL immediately
    -> Hold Time (120 min): Close ALL

COMBINED SIZING WHEN BOTH CASCADE + 45-MIN ADD TRIGGER:
  Signal 1: Initial P90 (40%) | Signal 2: 45-Min Add (30%) | Signal 3: Cascade P90 (20%) | Cascade 2: (10%)
  Total: 100% size across up to 4 activations

MANUAL TARGETS:
  Win Rate: 93.4% (cascade + add combo)
  Daily Goal: 1.0-1.5%
  Max Daily Drawdown: < 0.50%

Author: Quant Lab — CEREBUS FX v4.0 Strategy Reconstruction
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from enum import Enum

import pandas as pd
import numpy as np


class Direction(str, Enum):
    NONE = ""
    LONG = "LONG"
    SHORT = "SHORT"


class Tier(str, Enum):
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    NO_GO = "NO_GO"
    NA = "NA"


class ComboConfig:
    """Configuration for P90 Cascade + 45-Min Add Combo."""

    def __init__(self):
        # Session timing (EST). UTC = EST + 5
        self.asian_start_est = 19    # 7 PM EST
        self.asian_end_est = 3       # 3 AM EST
        self.entry_start_est = 2     # 2 AM EST
        self.entry_end_est = 11     # 11 AM EST
        self.hard_exit_est = 12      # 12 PM EST

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
            "T1": {"max_pips": 20, "size_pct": 1.0},
            "T2": {"min_pips": 20, "max_pips": 30, "size_pct": 0.75},
            "T3": {"min_pips": 30, "max_pips": 45, "size_pct": 0.50},
            "NO_GO": {"min_pips": 45, "size_pct": 0.0},
        }

        # Cascade parameters
        self.max_cascades = 3
        self.cascade_window_min = 30     # Min minutes after initial for cascade
        self.cascade_window_max = 90     # Max minutes after initial for cascade
        self.cascade_sl_mult = 1.68      # 168% of P90 body

        # 45-min add parameters
        self.add_time_min = 45           # Minutes after initial
        self.add_time_window = 5         # Window to check (45-50 min)
        self.add_extension_pips = 8.0    # Required extension for add

        # Sizing (percent of total allocation)
        self.initial_size = 0.40         # 40%
        self.add_size = 0.30             # 30%
        self.cascade1_size = 0.20        # 20%
        self.cascade2_size = 0.10        # 10%

        # Initial P90 SL
        self.initial_sl_mult = 0.80      # 80% of P90 body

        # Risk
        self.max_daily_loss_pct = 0.40   # Kill switch
        self.hold_time_min = 1220         # 120 min max hold

        # Position sizing (micro lots)
        self.position_size_lots = 0.1     # 10 micro lots base


class ComboTrade:
    """Represents a single activation within a combo session."""

    def __init__(self, entry_time, direction, entry_price, sl_price, tp_price,
                 size_lots, activation_type):
        self.entry_time = entry_time
        self.direction = direction
        self.entry_price = entry_price
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.size_lots = size_lots
        self.activation_type = activation_type
        self.exit_time = None
        self.exit_price = None
        self.pnl_pips = 0.0
        self.result = ""
        self.exit_reason = ""


class P90CascadeComboStrategy:
    """
    P90 Cascade + 45-Min Add Combo — CEREBUS FX v4.0

    Full implementation of the 5-step protocol from pages 10-16.
    """

    def __init__(self, config: ComboConfig = None):
        self.cfg = config or ComboConfig()

    @staticmethod
    def _utc_to_est(utc_hour: int) -> int:
        """Convert UTC hour to EST hour."""
        return (utc_hour - 5 + 24) % 24

    def _get_est_hour(self, ts) -> int:
        """Get EST hour from pandas Timestamp."""
        return self._utc_to_est(ts.hour)

    def _in_asian(self, est_h: int) -> bool:
        return est_h >= 19 or est_h < 3

    def _in_entry_window(self, est_h: int) -> bool:
        return 2 <= est_h < 11

    def _is_hard_exit(self, est_h: int) -> bool:
        return est_h >= 12

    def _get_threshold(self, est_h: int) -> float:
        for (start, end), thresh in self.cfg.p90_thresholds.items():
            if start <= est_h < end:
                return thresh
        return 6.2

    def _get_tier(self, ar_pips: float) -> Tier:
        if ar_pips < 20:
            return Tier.T1
        elif ar_pips < 30:
            return Tier.T2
        elif ar_pips < 45:
            return Tier.T3
        return Tier.NO_GO

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

    def run_backtest(self, df: pd.DataFrame, pair: str = "EUR/USD") -> Dict:
        """
        Run the full P90 Cascade + 45-Min Add Combo backtest.

        Args:
            df: DataFrame with [open, high, low, close] and DatetimeIndex (UTC)
            pair: Pair name for pip calculation

        Returns:
            Dict with backtest results
        """
        if df is None or len(df) < 500:
            return {"error": "Insufficient data", "total_trades": 0}

        df = df.copy()
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None) if df.index.tz is None else df.index.tz_convert(None)

        df["est_hour"] = df.index.hour.map(self._utc_to_est)
        df["date"] = df.index.date

        # ── State ──────────────────────────────────────────────────────
        asian_high = None
        asian_low = None
        ar_pips = None
        tier = Tier.NA

        session_active = False
        session_direction = Direction.NONE
        initial_p90_time = None
        initial_p90_price = None
        initial_p90_body_pips = None
        cascade_count = 0
        add_done = False
        tp1_hit = False
        tp2_hit = False
        kill_switch = False

        active_trades: List[ComboTrade] = []
        all_trades: List[ComboTrade] = []
        daily_pnl = 0.0
        last_date = None

        for i in range(50, len(df) - 1):
            row = df.iloc[i]
            ts = df.index[i]
            est_h = row["est_hour"]
            date = row["date"]
            o, h, l, c = row["open"], row["high"], row["low"], row["close"]

            # ── New Day Reset ───────────────────────────────────────────
            if date != last_date:
                for t in active_trades:
                    if t.exit_time is None:
                        direction_mult = 1 if t.direction == Direction.LONG else -1
                        t.pnl_pips = self._to_pips((c - t.entry_price) * direction_mult, pair)
                        t.exit_time = ts
                        t.exit_price = c
                        t.result = "win" if t.pnl_pips > 0 else "loss"
                        t.exit_reason = "new_day"
                        all_trades.append(t)
                        daily_pnl += t.pnl_pips
                active_trades.clear()

                asian_high = None
                asian_low = None
                ar_pips = None
                tier = Tier.NA
                session_active = False
                session_direction = Direction.NONE
                initial_p90_time = None
                initial_p90_price = None
                initial_p90_body_pips = None
                cascade_count = 0
                add_done = False
                tp1_hit = False
                tp2_hit = False
                kill_switch = False
                daily_pnl = 0.0
                last_date = date

            # ── Asian Range Calculation (7PM-3AM EST) ───────────────────
            if self._in_asian(est_h):
                if asian_high is None:
                    asian_high = h
                    asian_low = l
                else:
                    asian_high = max(asian_high, h)
                    asian_low = min(asian_low, l)
                # Classify tier at 3AM
                if est_h == 3 and asian_high is not None:
                    ar_pips = self._to_pips(asian_high - asian_low, pair)
                    tier = self._get_tier(ar_pips)
                continue

            # Skip NO-GO days
            if tier == Tier.NO_GO:
                continue

            # Skip if no Asian range yet
            if ar_pips is None or ar_pips <= 0:
                continue

            # ── Manage Active Trades ────────────────────────────────────
            trades_to_remove = []
            for t in active_trades:
                if t.exit_time is not None:
                    continue

                direction_mult = 1 if t.direction == Direction.LONG else -1

                # Check SL
                if t.direction == Direction.LONG and l <= t.sl_price:
                    t.pnl_pips = self._to_pips(t.sl_price - t.entry_price, pair)
                    t.exit_time = ts
                    t.exit_price = t.sl_price
                    t.result = "loss"
                    t.exit_reason = "sl"
                    all_trades.append(t)
                    daily_pnl += t.pnl_pips
                    trades_to_remove.append(t)
                    continue
                elif t.direction == Direction.SHORT and h >= t.sl_price:
                    t.pnl_pips = self._to_pips(t.entry_price - t.sl_price, pair)
                    t.exit_time = ts
                    t.exit_price = t.sl_price
                    t.result = "loss"
                    t.exit_reason = "sl"
                    all_trades.append(t)
                    daily_pnl += t.pnl_pips
                    trades_to_remove.append(t)
                    continue

                # Check TP2 (-50% Asian Range) — full close
                if t.direction == Direction.LONG and l <= t.tp_price:
                    t.pnl_pips = self._to_pips(t.tp_price - t.entry_price, pair)
                    t.exit_time = ts
                    t.exit_price = t.tp_price
                    t.result = "win"
                    t.exit_reason = "tp2_50"
                    all_trades.append(t)
                    daily_pnl += t.pnl_pips
                    trades_to_remove.append(t)
                    tp2_hit = True
                    continue
                elif t.direction == Direction.SHORT and h >= t.tp_price:
                    t.pnl_pips = self._to_pips(t.entry_price - t.tp_price, pair)
                    t.exit_time = ts
                    t.exit_price = t.tp_price
                    t.result = "win"
                    t.exit_reason = "tp2_50"
                    all_trades.append(t)
                    daily_pnl += t.pnl_pips
                    trades_to_remove.append(t)
                    tp2_hit = True
                    continue

                # Check 132% Kill Switch
                if asian_high is not None:
                    kill_offset = self._to_price(ar_pips * 1.32, pair)
                    if t.direction == Direction.LONG:
                        kill_level = asian_high + kill_offset
                        if h >= kill_level:
                            kill_switch = True
                    else:
                        kill_level = asian_low - kill_offset
                        if l <= kill_level:
                            kill_switch = True

                # Check hold time (120 min from initial P90)
                if initial_p90_time is not None:
                    minutes_held = (ts - initial_p90_time).total_seconds() / 60.0
                    if minutes_held >= self.cfg.hold_time_min:
                        t.pnl_pips = self._to_pips((c - t.entry_price) * direction_mult, pair)
                        t.exit_time = ts
                        t.exit_price = c
                        t.result = "win" if t.pnl_pips > 0 else "loss"
                        t.exit_reason = "hold_time"
                        all_trades.append(t)
                        daily_pnl += t.pnl_pips
                        trades_to_remove.append(t)

            for t in trades_to_remove:
                if t in active_trades:
                    active_trades.remove(t)

            # Kill switch: close all immediately
            if kill_switch:
                for t in active_trades:
                    if t.exit_time is None:
                        direction_mult = 1 if t.direction == Direction.LONG else -1
                        t.pnl_pips = self._to_pips((c - t.entry_price) * direction_mult, pair)
                        t.exit_time = ts
                        t.exit_price = c
                        t.result = "win" if t.pnl_pips > 0 else "loss"
                        t.exit_reason = "kill_switch_132"
                        all_trades.append(t)
                        daily_pnl += t.pnl_pips
                active_trades.clear()
                session_active = False
                continue

            # ── Hard Exit (12PM EST) ────────────────────────────────────
            if self._is_hard_exit(est_h):
                for t in active_trades:
                    if t.exit_time is None:
                        direction_mult = 1 if t.direction == Direction.LONG else -1
                        t.pnl_pips = self._to_pips((c - t.entry_price) * direction_mult, pair)
                        t.exit_time = ts
                        t.exit_price = c
                        t.result = "win" if t.pnl_pips > 0 else "loss"
                        t.exit_reason = "hard_exit_12pm"
                        all_trades.append(t)
                        daily_pnl += t.pnl_pips
                active_trades.clear()
                session_active = False
                continue

            # Skip if outside entry window
            if not self._in_entry_window(est_h):
                continue

            # ── P90 Signal Detection ────────────────────────────────────
            body_pips = self._to_pips(abs(c - o), pair)
            threshold = self._get_threshold(est_h)
            bull_signal = (c > o) and (body_pips >= threshold)
            bear_signal = (c < o) and (body_pips >= threshold)

            if not bull_signal and not bear_signal:
                continue

            signal_dir = Direction.LONG if bull_signal else Direction.SHORT

            # ── STEP 1: Initial P90 ─────────────────────────────────────
            if not session_active:
                session_active = True
                session_direction = signal_dir
                initial_p90_time = ts
                initial_p90_price = c
                initial_p90_body_pips = body_pips
                cascade_count = 1
                add_done = False
                tp1_hit = False
                tp2_hit = False

                # SL at 80% of P90 body
                sl_pips = body_pips * self.cfg.initial_sl_mult
                sl_offset = self._to_price(sl_pips, pair)
                tp_offset = self._to_price(ar_pips * 0.50, pair)

                if signal_dir == Direction.LONG:
                    sl_price = c - sl_offset
                    tp_price = c - tp_offset  # Mean reversion: pullback
                else:
                    sl_price = c + sl_offset
                    tp_price = c + tp_offset

                trade = ComboTrade(
                    entry_time=ts, direction=signal_dir, entry_price=c,
                    sl_price=sl_price, tp_price=tp_price,
                    size_lots=self.cfg.position_size_lots,
                    activation_type="initial_p90",
                )
                active_trades.append(trade)

            # ── STEP 3: Cascade P90 Check ───────────────────────────────
            elif session_active and session_direction == signal_dir:
                if cascade_count >= self.cfg.max_cascades:
                    continue

                if initial_p90_time is not None:
                    minutes_since = (ts - initial_p90_time).total_seconds() / 60.0
                    if minutes_since < self.cfg.cascade_window_min:
                        continue
                    if minutes_since > self.cfg.cascade_window_max:
                        continue

                if tp2_hit:
                    continue

                cascade_count += 1

                # SL at 168% of THIS P90 body
                sl_pips = body_pips * self.cfg.cascade_sl_mult
                sl_offset = self._to_price(sl_pips, pair)
                tp_offset = self._to_price(ar_pips * 0.50, pair)

                if signal_dir == Direction.LONG:
                    sl_price = c - sl_offset
                    tp_price = c - tp_offset
                else:
                    sl_price = c + sl_offset
                    tp_price = c + tp_offset

                if cascade_count == 2:
                    size = self.cfg.position_size_lots * self.cfg.cascade1_size / self.cfg.initial_size
                    act_type = "cascade_1"
                elif cascade_count == 3:
                    size = self.cfg.position_size_lots * self.cfg.cascade2_size / self.cfg.initial_size
                    act_type = "cascade_2"
                else:
                    continue

                trade = ComboTrade(
                    entry_time=ts, direction=signal_dir, entry_price=c,
                    sl_price=sl_price, tp_price=tp_price,
                    size_lots=size, activation_type=act_type,
                )
                active_trades.append(trade)

            # Opposite direction = IGNORE

            # ── STEP 2: 45-Min Add Check ────────────────────────────────
            if (session_active and not add_done and cascade_count >= 1
                    and initial_p90_time is not None and len(active_trades) > 0):

                minutes_since = (ts - initial_p90_time).total_seconds() / 60.0
                add_start = self.cfg.add_time_min
                add_end = add_start + self.cfg.add_time_window

                if add_start <= minutes_since < add_end:
                    # Check extension achieved
                    if session_direction == Direction.LONG:
                        ext_pips = self._to_pips(c - initial_p90_price, pair)
                    else:
                        ext_pips = self._to_pips(initial_p90_price - c, pair)

                    if ext_pips >= self.cfg.add_extension_pips and not kill_switch:
                        add_done = True
                        tp_offset = self._to_price(ar_pips * 0.50, pair)

                        if session_direction == Direction.LONG:
                            tp_price = initial_p90_price - tp_offset
                            sl_price = initial_p90_price  # Breakeven
                        else:
                            tp_price = initial_p90_price + tp_offset
                            sl_price = initial_p90_price

                        size = self.cfg.position_size_lots * self.cfg.add_size / self.cfg.initial_size

                        trade = ComboTrade(
                            entry_time=ts, direction=session_direction, entry_price=c,
                            sl_price=sl_price, tp_price=tp_price,
                            size_lots=size, activation_type="add_45min",
                        )
                        active_trades.append(trade)

        # ── Calculate Results ───────────────────────────────────────────
        return self._calc_results(all_trades, pair)

    def _calc_results(self, trades: List[ComboTrade], pair: str) -> Dict:
        if not trades:
            return {"strategy": "P90_Cascade_Combo", "pair": pair, "total_trades": 0, "error": "No trades"}

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

        # Count sessions (unique entry dates)
        session_dates = set()
        for t in trades:
            session_dates.add(t.entry_time.date())

        return {
            "strategy": "P90_Cascade_Combo",
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
    import json
    from pathlib import Path

    data_path = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")

    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        sys.exit(1)

    print(f"Loading {data_path.name}...")
    sys.path.insert(0, str(Path(__file__).parent))
    from data_loader import _parse_csv
    df = _parse_csv(data_path)
    print(f"  Loaded {len(df):,} bars ({df.index[0]} -> {df.index[-1]})")

    strategy = P90CascadeComboStrategy()
    results = strategy.run_backtest(df, pair="EUR/USD")

    print(f"\n{'='*60}")
    print(f"P90 CASCADE + 45-MIN ADD COMBO RESULTS")
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
            print(f"    {reason:20s}: {count}")

    print(f"{'='*60}")

    # Save results
    results_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results")
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"p90_cascade_combo_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {results_file}")
