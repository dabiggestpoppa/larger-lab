#!/usr/bin/env python3
"""
P90 Cascade Activation — Fixed Test Script
===========================================
Fixes from original:
1. P90 signal now requires close OUTSIDE Asian band (above AH for LONG, below AL for SHORT)
2. Asian range completion: range is "complete" after the Asian session ends (est_h == 3),
   but we don't `continue` past it — we let subsequent bars in the entry window use it.
3. Cascade window: 30-120 min (per manual: "within 120 min", optimal 45-60)
4. Debug logging: prints every P90 signal found + every trade entry/exit
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List, Tuple

import pandas as pd
import numpy as np


# ═══════════════════════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════════════════════

class P90CascadeConfig:
    def __init__(self):
        self.asian_start_est = 19   # 7 PM EST
        self.asian_end_est = 3      # 3 AM EST
        self.entry_start_est = 2    # 2 AM EST
        self.entry_end_est = 11     # 11 AM EST
        self.hard_exit_est = 12     # 12 PM EST

        # P90 body thresholds by EST time window (pips)
        self.p90_thresholds = {
            (2, 4): 4.1,
            (4, 6): 4.6,
            (6, 8): 4.6,
            (8, 10): 5.9,
            (10, 11): 6.2,
        }
        self.p90_body_pct = 0.60  # body must be > 60% of total range

        # Tier system
        self.tier_config = {
            "T1": {"max_pips": 20, "size_pct": 1.0},
            "T2": {"min_pips": 20, "max_pips": 30, "size_pct": 0.75},
            "T3": {"min_pips": 30, "max_pips": 45, "size_pct": 0.50},
            "NO_GO": {"min_pips": 45, "size_pct": 0.0},
        }

        # Cascade
        self.max_cascades = 3
        self.cascade_window_min = 30    # min minutes after initial P90
        self.cascade_window_max = 120   # max minutes (manual says within 120 min)
        self.cascade_sl_mult = 1.68
        self.cascade_size_1 = 0.20
        self.cascade_size_2 = 0.10

        # 45-min add
        self.add_time_minutes = 45
        self.add_time_window = 10      # widened window: 45-55 min
        self.add_extension_pips = 8.0
        self.add_size = 0.30

        # Initial P90
        self.initial_size = 0.40
        self.initial_sl_mult = 0.80

        # Risk
        self.hold_time_minutes = 120
        self.kill_switch_pct = 1.32
        self.tp1_pct = 0.25
        self.tp2_pct = 0.50
        self.position_size_lots = 0.1


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def to_pips(price_diff: float) -> float:
    return price_diff * 10000

def to_price(pips: float) -> float:
    return pips / 10000

def utc_to_est(utc_hour: int) -> int:
    return (utc_hour - 5 + 24) % 24


# ═══════════════════════════════════════════════════════════════════════════════
# CSV Parser
# ═══════════════════════════════════════════════════════════════════════════════

def parse_csv(filepath: str) -> pd.DataFrame:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        raw = f.readlines()
    records = []
    for line in raw[1:]:
        parts = line.strip().split()
        if len(parts) < 7:
            continue
        try:
            ts = datetime.strptime(f"{parts[0]} {parts[1]}", "%Y.%m.%d %H:%M:%S")
            records.append({
                "timestamp": ts,
                "open": float(parts[2]),
                "high": float(parts[3]),
                "low": float(parts[4]),
                "close": float(parts[5]),
            })
        except (ValueError, IndexError):
            continue
    df = pd.DataFrame(records)
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# Strategy
# ═══════════════════════════════════════════════════════════════════════════════

def run_backtest(df: pd.DataFrame, cfg: P90CascadeConfig, debug: bool = True):
    """
    Fixed P90 Cascade Activation backtest.
    """
    df = df.copy()
    df.index = df.index.tz_localize(None) if df.index.tz is not None else df.index
    df["est_hour"] = df.index.hour.map(utc_to_est)
    df["date"] = df.index.date

    # ── State variables ──
    asian_high = None
    asian_low = None
    asian_range_pips = None
    asian_range_complete = False
    tier = "NA"

    session_direction = None        # "LONG" | "SHORT" | None
    initial_p90_time = None
    initial_p90_price = None
    initial_p90_body_pips = None
    cascade_count = 0
    add_45min_done = False
    kill_switch_triggered = False

    active_trades = []
    all_trades = []
    daily_pnl = 0.0
    last_date = None
    daily_loss_limit_hit = False

    position_size = cfg.position_size_lots

    p90_signals_found = 0

    for i in range(50, len(df) - 1):
        row = df.iloc[i]
        ts = df.index[i]
        est_h = int(row["est_hour"])
        day = row["date"]
        o, h, l, c = float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])

        # ── New Day Reset ──
        if day != last_date:
            # Close any open trades at current close
            for t in active_trades:
                if t["exit_time"] is None:
                    direction_mult = 1 if t["direction"] == "LONG" else -1
                    pip_diff = to_pips((c - t["entry_price"]) * direction_mult)
                    t["pnl_pips"] = pip_diff
                    t["exit_time"] = ts
                    t["exit_price"] = c
                    t["result"] = "win" if pip_diff > 0 else "loss"
                    t["exit_reason"] = "new_day"
                    all_trades.append(t)
                    daily_pnl += pip_diff
            active_trades = [t for t in active_trades if t["exit_time"] is None]

            # Reset session state
            asian_high = None
            asian_low = None
            asian_range_pips = None
            asian_range_complete = False
            tier = "NA"
            session_direction = None
            initial_p90_time = None
            initial_p90_price = None
            initial_p90_body_pips = None
            cascade_count = 0
            add_45min_done = False
            kill_switch_triggered = False
            daily_pnl = 0.0
            daily_loss_limit_hit = False
            last_date = day

        # ── Asian Range Calculation (7PM-3AM EST) ──
        in_asian = (est_h >= cfg.asian_start_est or est_h <= cfg.asian_end_est)
        if in_asian:
            if asian_high is None:
                asian_high = h
                asian_low = l
            else:
                asian_high = max(asian_high, h)
                asian_low = min(asian_low, l)
            # Mark complete at the END of the Asian session (est_h == 3)
            if est_h == cfg.asian_end_est and asian_high is not None:
                asian_range_pips = to_pips(asian_high - asian_low)
                if asian_range_pips < 20:
                    tier = "T1"
                elif asian_range_pips < 30:
                    tier = "T2"
                elif asian_range_pips < 45:
                    tier = "T3"
                else:
                    tier = "NO_GO"
                asian_range_complete = True
            # Don't continue — let bars at est_h == 3 also be checked for signals
            # But Asian session bars themselves are not in the entry window, so
            # they won't trigger signals. The `continue` was actually fine for
            # est_h >= 19 (7PM-11PM). For est_h == 3, we need to NOT continue
            # so the range is set for subsequent bars.
            if est_h >= cfg.asian_start_est or est_h < cfg.asian_end_est:
                continue
            # est_h == 3: fall through to allow signal checks on these bars
            # (though 3 AM is before entry_start_est=2, so it won't match entry window)

        # ── Skip if no valid Asian range ──
        if not asian_range_complete or tier == "NO_GO" or daily_loss_limit_hit:
            # Still manage existing trades even if no new signals
            if active_trades:
                _manage_trades(active_trades, all_trades, h, l, c, ts, asian_high, asian_low,
                               asian_range_pips, cfg, initial_p90_time, kill_switch_triggered)
            continue

        # ── Hard Exit at 12PM EST ──
        if est_h >= cfg.hard_exit_est:
            for t in active_trades:
                if t["exit_time"] is None:
                    direction_mult = 1 if t["direction"] == "LONG" else -1
                    pip_diff = to_pips((c - t["entry_price"]) * direction_mult)
                    t["pnl_pips"] = pip_diff
                    t["exit_time"] = ts
                    t["exit_price"] = c
                    t["result"] = "win" if pip_diff > 0 else "loss"
                    t["exit_reason"] = "hard_exit_12pm"
                    all_trades.append(t)
                    daily_pnl += pip_diff
            active_trades = [t for t in active_trades if t["exit_time"] is None]
            session_direction = None
            continue

        # ── Manage Active Trades ──
        kill_switch_triggered = _manage_trades(
            active_trades, all_trades, h, l, c, ts, asian_high, asian_low,
            asian_range_pips, cfg, initial_p90_time, kill_switch_triggered
        )

        if kill_switch_triggered:
            for t in active_trades:
                if t["exit_time"] is None:
                    direction_mult = 1 if t["direction"] == "LONG" else -1
                    pip_diff = to_pips((c - t["entry_price"]) * direction_mult)
                    t["pnl_pips"] = pip_diff
                    t["exit_time"] = ts
                    t["exit_price"] = c
                    t["result"] = "win" if pip_diff > 0 else "loss"
                    t["exit_reason"] = "kill_switch_132"
                    all_trades.append(t)
                    daily_pnl += pip_diff
            active_trades = [t for t in active_trades if t["exit_time"] is None]
            continue

        # ── Only look for signals in entry window ──
        if not (cfg.entry_start_est <= est_h < cfg.entry_end_est):
            continue
        if asian_range_pips is None or asian_range_pips <= 0:
            continue

        # ── P90 Signal Detection ──
        # FIX #1: Must check close OUTSIDE Asian band
        total_range = h - l
        if total_range <= 0:
            continue
        body_size = abs(c - o)
        body_pct = body_size / total_range
        if body_pct <= cfg.p90_body_pct:
            continue

        # Check close outside Asian band
        is_bullish_p90 = c > asian_high
        is_bearish_p90 = c < asian_low
        if not is_bullish_p90 and not is_bearish_p90:
            continue

        # Check body threshold for time window
        body_pips = to_pips(body_size)
        threshold = None
        for (start, end), thr in cfg.p90_thresholds.items():
            if start <= est_h < end:
                threshold = thr
                break
        if threshold is None:
            continue
        if body_pips < threshold:
            continue

        # Valid P90 signal!
        signal_direction = "LONG" if is_bullish_p90 else "SHORT"
        p90_signals_found += 1

        if debug:
            print(f"  📡 P90 SIGNAL @ {ts} | {signal_direction} | body={body_pips:.1f}p | "
                  f"est_h={est_h} | O={o} H={h} L={l} C={c}")
            print(f"      Asian: H={asian_high} L={asian_low} Range={asian_range_pips:.1f}p Tier={tier}")

        candle_body_pips = body_pips

        # ── STEP 1: Initial P90 (Bias Setter) ──
        if session_direction is None:
            session_direction = signal_direction
            initial_p90_time = ts
            initial_p90_price = c
            initial_p90_body_pips = candle_body_pips
            cascade_count = 1
            add_45min_done = False

            sl_pips = candle_body_pips * cfg.initial_sl_mult
            sl_offset = to_price(sl_pips)
            tp_offset = to_price(asian_range_pips * cfg.tp2_pct)

            if signal_direction == "LONG":
                sl_price = c - sl_offset
                tp_price = c + tp_offset  # TP above entry
            else:
                sl_price = c + sl_offset
                tp_price = c - tp_offset  # TP below entry

            trade = {
                "entry_time": ts, "direction": signal_direction,
                "entry_price": c, "sl_price": sl_price, "tp_price": tp_price,
                "size_lots": position_size, "activation_type": "initial",
                "cascade_num": 0, "exit_time": None, "exit_price": None,
                "pnl_pips": 0.0, "result": "", "exit_reason": "",
            }
            active_trades.append(trade)
            if debug:
                print(f"  🟢 INITIAL P90 trade opened @ {c} | SL={sl_price} | TP={tp_price}")
            continue

        # ── STEP 2: Cascade P90 (same direction) ──
        if session_direction == signal_direction:
            if cascade_count >= cfg.max_cascades:
                if debug:
                    print(f"  ⛔ Cascade skipped: max cascades ({cfg.max_cascades}) reached")
                continue

            if initial_p90_time is not None:
                minutes_since = (ts - initial_p90_time).total_seconds() / 60.0
                if minutes_since < cfg.cascade_window_min:
                    if debug:
                        print(f"  ⛔ Cascade skipped: too soon ({minutes_since:.0f} < {cfg.cascade_window_min} min)")
                    continue
                if minutes_since > cfg.cascade_window_max:
                    if debug:
                        print(f"  ⛔ Cascade skipped: too late ({minutes_since:.0f} > {cfg.cascade_window_max} min)")
                    continue

            cascade_count += 1

            sl_pips = candle_body_pips * cfg.cascade_sl_mult
            sl_offset = to_price(sl_pips)
            tp_offset = to_price(asian_range_pips * cfg.tp2_pct)

            if signal_direction == "LONG":
                sl_price = c - sl_offset
                tp_price = c + tp_offset  # TP above entry
            else:
                sl_price = c + sl_offset
                tp_price = c - tp_offset  # TP below entry

            if cascade_count == 2:
                size = position_size * cfg.cascade_size_1 / cfg.initial_size
                act_type = "cascade_1"
            elif cascade_count == 3:
                size = position_size * cfg.cascade_size_2 / cfg.initial_size
                act_type = "cascade_2"
            else:
                continue

            trade = {
                "entry_time": ts, "direction": signal_direction,
                "entry_price": c, "sl_price": sl_price, "tp_price": tp_price,
                "size_lots": size, "activation_type": act_type,
                "cascade_num": cascade_count - 1, "exit_time": None,
                "exit_price": None, "pnl_pips": 0.0, "result": "",
                "exit_reason": "",
            }
            active_trades.append(trade)
            if debug:
                print(f"  🔵 CASCADE {cascade_count-1} trade opened @ {c} | SL={sl_price} | TP={tp_price}")

        # Opposite direction = IGNORE (no action needed)

        # ── STEP 3: 45-Min Add Check ──
        if (initial_p90_time is not None and not add_45min_done and
                cascade_count >= 1 and len(active_trades) > 0):

            minutes_since = (ts - initial_p90_time).total_seconds() / 60.0
            add_start = cfg.add_time_minutes
            add_end = add_start + cfg.add_time_window

            if add_start <= minutes_since < add_end:
                if session_direction == "LONG":
                    extension_pips = to_pips(c - initial_p90_price)
                else:
                    extension_pips = to_pips(initial_p90_price - c)

                if extension_pips >= cfg.add_extension_pips and not kill_switch_triggered:
                    add_45min_done = True
                    tp_offset = to_price(asian_range_pips * cfg.tp2_pct)

                    if session_direction == "LONG":
                        tp_price = c + tp_offset  # TP above entry
                        sl_price = initial_p90_price  # breakeven
                    else:
                        tp_price = c - tp_offset  # TP below entry
                        sl_price = initial_p90_price

                    trade = {
                        "entry_time": ts, "direction": session_direction,
                        "entry_price": c, "sl_price": sl_price, "tp_price": tp_price,
                        "size_lots": position_size * cfg.add_size / cfg.initial_size,
                        "activation_type": "add_45min", "cascade_num": 0,
                        "exit_time": None, "exit_price": None, "pnl_pips": 0.0,
                        "result": "", "exit_reason": "",
                    }
                    active_trades.append(trade)
                    if debug:
                        print(f"  🟡 45-MIN ADD trade opened @ {c} | ext={extension_pips:.1f}p | SL={sl_price} | TP={tp_price}")

    # ── Close any remaining open trades at last bar ──
    if active_trades:
        last_row = df.iloc[-1]
        last_ts = df.index[-1]
        last_c = float(last_row["close"])
        for t in active_trades:
            if t["exit_time"] is None:
                direction_mult = 1 if t["direction"] == "LONG" else -1
                pip_diff = to_pips((last_c - t["entry_price"]) * direction_mult)
                t["pnl_pips"] = pip_diff
                t["exit_time"] = last_ts
                t["exit_price"] = last_c
                t["result"] = "win" if pip_diff > 0 else "loss"
                t["exit_reason"] = "end_of_data"
                all_trades.append(t)

    return all_trades, p90_signals_found


def _manage_trades(active_trades, all_trades, h, l, c, ts,
                   asian_high, asian_low, asian_range_pips,
                   cfg, initial_p90_time, kill_switch):
    """Manage active trades: check SL, TP, kill switch, hold time."""
    trades_to_remove = []
    ks = kill_switch

    for t in active_trades:
        if t["exit_time"] is not None:
            continue

        is_long = t["direction"] == "LONG"

        # SL check
        if is_long and l <= t["sl_price"]:
            t["pnl_pips"] = to_pips(t["sl_price"] - t["entry_price"])
            t["exit_time"] = ts
            t["exit_price"] = t["sl_price"]
            t["result"] = "loss"
            t["exit_reason"] = "sl"
            all_trades.append(t)
            trades_to_remove.append(t)
            continue
        elif not is_long and h >= t["sl_price"]:
            t["pnl_pips"] = to_pips(t["entry_price"] - t["sl_price"])
            t["exit_time"] = ts
            t["exit_price"] = t["sl_price"]
            t["result"] = "loss"
            t["exit_reason"] = "sl"
            all_trades.append(t)
            trades_to_remove.append(t)
            continue

        # TP check
        if is_long and h >= t["tp_price"]:
            t["pnl_pips"] = to_pips(t["tp_price"] - t["entry_price"])
            t["exit_time"] = ts
            t["exit_price"] = t["tp_price"]
            t["result"] = "win"
            t["exit_reason"] = "tp_50"
            all_trades.append(t)
            trades_to_remove.append(t)
            continue
        elif not is_long and l <= t["tp_price"]:
            t["pnl_pips"] = to_pips(t["entry_price"] - t["tp_price"])
            t["exit_time"] = ts
            t["exit_price"] = t["tp_price"]
            t["result"] = "win"
            t["exit_reason"] = "tp_50"
            all_trades.append(t)
            trades_to_remove.append(t)
            continue

        # Kill switch check (132% of Asian Range from the opposite band)
        if asian_range_pips and asian_high is not None and asian_low is not None:
            ks_offset = to_price(asian_range_pips * cfg.kill_switch_pct)
            if is_long:
                # For LONG: kill if price drops 132% of AR below Asian Low
                kill_level = asian_low - ks_offset
                if l <= kill_level:
                    ks = True
            else:
                # For SHORT: kill if price rises 132% of AR above Asian High
                kill_level = asian_high + ks_offset
                if h >= kill_level:
                    ks = True

        # Hold time (120 min)
        if initial_p90_time is not None:
            minutes_held = (ts - initial_p90_time).total_seconds() / 60.0
            if minutes_held >= cfg.hold_time_minutes:
                direction_mult = 1 if is_long else -1
                pip_diff = to_pips((c - t["entry_price"]) * direction_mult)
                t["pnl_pips"] = pip_diff
                t["exit_time"] = ts
                t["exit_price"] = c
                t["result"] = "win" if pip_diff > 0 else "loss"
                t["exit_reason"] = "hold_time_120min"
                all_trades.append(t)
                trades_to_remove.append(t)

    for t in trades_to_remove:
        if t in active_trades:
            active_trades.remove(t)

    return ks


# ═══════════════════════════════════════════════════════════════════════════════
# Results
# ═══════════════════════════════════════════════════════════════════════════════

def calc_results(trades):
    if not trades:
        return {"total_trades": 0, "error": "No trades generated"}

    pnls = [t["pnl_pips"] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    total_pnl = sum(pnls)
    win_rate = len(wins) / len(pnls) * 100 if pnls else 0

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
        at = t["activation_type"]
        if at not in by_type:
            by_type[at] = {"trades": 0, "wins": 0, "pnl": 0}
        by_type[at]["trades"] += 1
        by_type[at]["pnl"] += t["pnl_pips"]
        if t["pnl_pips"] > 0:
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
        er = t["exit_reason"]
        by_exit[er] = by_exit.get(er, 0) + 1

    return {
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "total_pnl_pips": round(total_pnl, 2),
        "avg_win_pips": round(sum(wins) / len(wins), 2) if wins else 0,
        "avg_loss_pips": round(sum(losses) / len(losses), 2) if losses else 0,
        "max_drawdown_pips": round(max_dd, 2),
        "profit_factor": round(profit_factor, 2),
        "by_activation_type": by_type_summary,
        "by_exit_reason": by_exit,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    data_path = r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv"

    print(f"Loading data...")
    df = parse_csv(data_path)
    print(f"  Loaded {len(df):,} bars ({df.index[0]} -> {df.index[-1]})")

    # Use first 3 days of data for quick test
    start_date = df.index[0].date()
    end_date = start_date + timedelta(days=2)  # 3 days inclusive
    mask = (df.index.date >= start_date) & (df.index.date <= end_date)
    df_test = df.loc[mask].copy()
    print(f"  Testing on {start_date} -> {end_date} = {len(df_test):,} bars")

    cfg = P90CascadeConfig()
    print(f"\nRunning P90 Cascade Activation backtest...")
    print(f"  Entry window: {cfg.entry_start_est}:00 - {cfg.entry_end_est}:00 EST")
    print(f"  Cascade window: {cfg.cascade_window_min}-{cfg.cascade_window_max} min")
    print(f"  Max cascades: {cfg.max_cascades}")
    print()

    trades, p90_count = run_backtest(df_test, cfg, debug=True)

    print(f"\n{'='*60}")
    print(f"P90 CASCADE ACTIVATION — TEST RESULTS (3 days)")
    print(f"{'='*60}")
    print(f"  P90 signals found: {p90_count}")
    print(f"  Total trades:      {len(trades)}")

    if trades:
        results = calc_results(trades)
        print(f"  Wins:              {results['wins']} ({results['win_rate']}%)")
        print(f"  Losses:            {results['losses']}")
        print(f"  Total P&L:         {results['total_pnl_pips']} pips")
        print(f"  Avg Win:           {results['avg_win_pips']} pips")
        print(f"  Avg Loss:          {results['avg_loss_pips']} pips")
        print(f"  Max Drawdown:      {results['max_drawdown_pips']} pips")
        print(f"  Profit Factor:     {results['profit_factor']}")

        if results.get("by_activation_type"):
            print(f"\n  By Activation Type:")
            for at, data in results["by_activation_type"].items():
                print(f"    {at:15s}: {data['trades']} trades | "
                      f"{data['win_rate']}% WR | {data['pnl_pips']} pips")

        if results.get("by_exit_reason"):
            print(f"\n  By Exit Reason:")
            for reason, count in sorted(results["by_exit_reason"].items(), key=lambda x: -x[1]):
                print(f"    {reason:25s}: {count}")

        # Print individual trades
        print(f"\n  Individual Trades:")
        for i, t in enumerate(trades):
            print(f"    [{i+1}] {t['entry_time']} {t['direction']:5s} @ {t['entry_price']} | "
                  f"{t['activation_type']:10s} | P&L: {t['pnl_pips']:+.1f}p | "
                  f"Exit: {t['exit_reason']}")
    else:
        print("  ⚠️  No trades generated!")

    print(f"{'='*60}")

    # Save results
    output_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtests")
    output_dir.mkdir(parents=True, exist_ok=True)

    output = {
        "test_period": f"{start_date} to {end_date}",
        "bars": len(df_test),
        "p90_signals_found": p90_count,
        "results": calc_results(trades) if trades else {"total_trades": 0},
        "trades": [
            {
                "entry_time": str(t["entry_time"]),
                "exit_time": str(t["exit_time"]) if t["exit_time"] else None,
                "direction": t["direction"],
                "entry_price": t["entry_price"],
                "exit_price": t["exit_price"],
                "sl_price": t["sl_price"],
                "tp_price": t["tp_price"],
                "activation_type": t["activation_type"],
                "pnl_pips": round(t["pnl_pips"], 2),
                "result": t["result"],
                "exit_reason": t["exit_reason"],
            }
            for t in trades
        ],
    }

    results_file = output_dir / "p90_cascade_results.json"
    with open(results_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults saved to {results_file}")

    return len(trades)


if __name__ == "__main__":
    count = main()
    sys.exit(0 if count > 0 else 1)
