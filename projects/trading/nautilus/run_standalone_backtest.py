#!/usr/bin/env python3
"""
Standalone backtest runner — no Nautilus Trader dependency.
Uses pandas DataFrames loaded directly from CSV.
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# ── CSV Parser (copied from data_loader to avoid nautilus import) ──────────

def _parse_csv(filepath):
    """Parse forex.com or OX Securities CSV into DataFrame."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        raw_lines = f.readlines()

    data_lines = [l for l in raw_lines[1:] if l.strip()]

    # Fix OX line wrapping
    fixed = []
    i = 0
    while i < len(data_lines):
        line = data_lines[i]
        if i + 1 < len(data_lines) and re.match(r'^\d{4}\.\d{2}\.\d{2}', data_lines[i + 1]):
            parts = line.strip().split()
            if len(parts) >= 8:
                fixed.append(line)
            else:
                merged = line.strip() + " " + data_lines[i + 1].strip()
                fixed.append(merged)
                i += 1
        else:
            fixed.append(line)
        i += 1

    records = []
    for line in fixed:
        parts = line.strip().split()
        if len(parts) < 7:
            continue
        try:
            date_str, time_str = parts[0], parts[1]
            open_val, high_val = float(parts[2]), float(parts[3])
            low_val, close_val = float(parts[4]), float(parts[5])
            tick_vol = int(parts[6]) if len(parts) > 6 else 0
            ts = datetime.strptime(f"{date_str} {time_str}", "%Y.%m.%d %H:%M:%S")
            records.append({
                "timestamp": ts, "open": open_val, "high": high_val,
                "low": low_val, "close": close_val,
                "tick_volume": tick_vol,
            })
        except (ValueError, IndexError):
            continue

    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)
    return df


# ── Strategy Implementations ──────────────────────────────────────────

class P90CascadeConfig:
    def __init__(self):
        self.asian_start_hour_est = 19
        self.asian_end_hour_est = 3
        self.entry_start_hour_est = 2
        self.entry_end_hour_est = 11
        self.hard_exit_hour_est = 12
        self.p90_thresholds = {
            (2, 4): 4.1, (4, 6): 4.6, (6, 8): 4.6,
            (8, 10): 5.9, (10, 11): 6.2,
        }
        self.max_cascades = 3
        self.cascade_window_minutes = 120
        self.optimal_cascade_start = 30
        self.optimal_cascade_end = 90
        self.cascade_sl_mult = 1.68
        self.add_time_minutes = 45
        self.add_extension_pips = 8.0
        self.initial_sl_mult = 0.80
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


class P90CascadeStrategy:
    def __init__(self, config=None):
        self.cfg = config or P90CascadeConfig()

    def _utc_to_est(self, utc_hour):
        return (utc_hour - 5 + 24) % 24

    def _in_asian(self, est_h):
        return est_h >= 19 or est_h < 3

    def _in_entry(self, est_h):
        return 2 <= est_h < 11

    def _is_hard_exit(self, est_h):
        return est_h >= 12

    def _get_threshold(self, est_h):
        for (start, end), thresh in self.cfg.p90_thresholds.items():
            if start <= est_h < end:
                return thresh
        return 6.2

    def _to_pips(self, price_diff, pair="EUR/USD"):
        if "JPY" in pair:
            return price_diff * 100
        return price_diff * 10000

    def _to_price(self, pips, pair="EUR/USD"):
        if "JPY" in pair:
            return pips / 100
        return pips / 10000

    def run_backtest(self, df, pair="EUR/USD"):
        if df is None or len(df) < 500:
            return {"error": "Insufficient data", "total_trades": 0}

        df = df.copy()
        df["est_hour"] = df.index.hour.map(self._utc_to_est)
        df["date"] = df.index.date

        asian_high = None
        asian_low = None
        ar_pips = None

        session_direction = None
        initial_p90_time = None
        initial_p90_price = None
        cascade_count = 0
        add_done = False
        tp2_hit = False
        kill_switch = False

        active_trades = []
        all_trades = []
        daily_pnl = 0.0
        last_date = None

        for i in range(50, len(df) - 1):
            row = df.iloc[i]
            ts = df.index[i]
            est_h = row["est_hour"]
            date = row["date"]
            o, h, l, c = row["open"], row["high"], row["low"], row["close"]

            # New day reset
            if date != last_date:
                for t in active_trades:
                    if t.exit_time is None:
                        dm = 1 if t.direction == "LONG" else -1
                        t.pnl_pips = self._to_pips((c - t.entry_price) * dm, pair)
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
                session_direction = None
                initial_p90_time = None
                initial_p90_price = None
                cascade_count = 0
                add_done = False
                tp2_hit = False
                kill_switch = False
                daily_pnl = 0.0
                last_date = date

            # Asian range calc
            if self._in_asian(est_h):
                if asian_high is None:
                    asian_high = h
                    asian_low = l
                else:
                    asian_high = max(asian_high, h)
                    asian_low = min(asian_low, l)
                if est_h == 2 and asian_high is not None:
                    ar_pips = self._to_pips(asian_high - asian_low, pair)
                continue

            if ar_pips is None or ar_pips <= 0:
                continue

            # Manage active trades
            trades_to_remove = []
            for t in active_trades:
                if t.exit_time is not None:
                    continue
                dm = 1 if t.direction == "LONG" else -1

                # SL check
                if t.direction == "LONG" and l <= t.sl_price:
                    t.pnl_pips = self._to_pips(t.sl_price - t.entry_price, pair)
                    t.exit_time = ts; t.exit_price = t.sl_price
                    t.result = "loss"; t.exit_reason = "sl"
                    all_trades.append(t); daily_pnl += t.pnl_pips
                    trades_to_remove.append(t); continue
                elif t.direction == "SHORT" and h >= t.sl_price:
                    t.pnl_pips = self._to_pips(t.entry_price - t.sl_price, pair)
                    t.exit_time = ts; t.exit_price = t.sl_price
                    t.result = "loss"; t.exit_reason = "sl"
                    all_trades.append(t); daily_pnl += t.pnl_pips
                    trades_to_remove.append(t); continue

                # TP2 check (-50% AR)
                if t.direction == "LONG" and l <= t.tp_price:
                    t.pnl_pips = self._to_pips(t.tp_price - t.entry_price, pair)
                    t.exit_time = ts; t.exit_price = t.tp_price
                    t.result = "win"; t.exit_reason = "tp2_50"
                    all_trades.append(t); daily_pnl += t.pnl_pips
                    trades_to_remove.append(t); tp2_hit = True; continue
                elif t.direction == "SHORT" and h >= t.tp_price:
                    t.pnl_pips = self._to_pips(t.entry_price - t.tp_price, pair)
                    t.exit_time = ts; t.exit_price = t.tp_price
                    t.result = "win"; t.exit_reason = "tp2_50"
                    all_trades.append(t); daily_pnl += t.pnl_pips
                    trades_to_remove.append(t); tp2_hit = True; continue

                # Kill switch 132%
                if asian_high is not None:
                    kill_off = self._to_price(ar_pips * 1.32, pair)
                    if t.direction == "LONG" and h >= asian_high + kill_off:
                        kill_switch = True
                    elif t.direction == "SHORT" and l <= asian_low - kill_off:
                        kill_switch = True

                # Hold time 120min
                if initial_p90_time is not None:
                    mins = (ts - initial_p90_time).total_seconds() / 60.0
                    if mins >= 120:
                        t.pnl_pips = self._to_pips((c - t.entry_price) * dm, pair)
                        t.exit_time = ts; t.exit_price = c
                        t.result = "win" if t.pnl_pips > 0 else "loss"
                        t.exit_reason = "hold_time"
                        all_trades.append(t); daily_pnl += t.pnl_pips
                        trades_to_remove.append(t)

            for t in trades_to_remove:
                if t in active_trades:
                    active_trades.remove(t)

            if kill_switch:
                for t in active_trades:
                    if t.exit_time is None:
                        dm = 1 if t.direction == "LONG" else -1
                        t.pnl_pips = self._to_pips((c - t.entry_price) * dm, pair)
                        t.exit_time = ts; t.exit_price = c
                        t.result = "win" if t.pnl_pips > 0 else "loss"
                        t.exit_reason = "kill_switch_132"
                        all_trades.append(t); daily_pnl += t.pnl_pips
                active_trades.clear()
                session_direction = None
                continue

            # Hard exit 12PM
            if self._is_hard_exit(est_h):
                for t in active_trades:
                    if t.exit_time is None:
                        dm = 1 if t.direction == "LONG" else -1
                        t.pnl_pips = self._to_pips((c - t.entry_price) * dm, pair)
                        t.exit_time = ts; t.exit_price = c
                        t.result = "win" if t.pnl_pips > 0 else "loss"
                        t.exit_reason = "hard_exit_12pm"
                        all_trades.append(t); daily_pnl += t.pnl_pips
                active_trades.clear()
                session_direction = None
                continue

            if not self._in_entry(est_h):
                continue

            # P90 signal detection
            body_pips = self._to_pips(abs(c - o), pair)
            threshold = self._get_threshold(est_h)
            bull = (c > o) and (body_pips >= threshold)
            bear = (c < o) and (body_pips >= threshold)
            if not bull and not bear:
                continue

            signal_dir = "LONG" if bull else "SHORT"

            # Initial P90
            if session_direction is None:
                session_direction = signal_dir
                initial_p90_time = ts
                initial_p90_price = c
                cascade_count = 1
                add_done = False
                tp2_hit = False

                sl_pips = body_pips * self.cfg.initial_sl_mult
                sl_off = self._to_price(sl_pips, pair)
                tp_off = self._to_price(ar_pips * 0.50, pair)

                if signal_dir == "LONG":
                    sl_price = c - sl_off
                    tp_price = c - tp_off
                else:
                    sl_price = c + sl_off
                    tp_price = c + tp_off

                trade = CascadeTrade(ts, signal_dir, c, sl_price, tp_price,
                                     self.cfg.position_size_lots, "initial", 0)
                active_trades.append(trade)

            # Cascade P90
            elif session_direction == signal_dir:
                if cascade_count >= self.cfg.max_cascades:
                    continue
                if initial_p90_time is not None:
                    mins_since = (ts - initial_p90_time).total_seconds() / 60.0
                    if mins_since > self.cfg.cascade_window_minutes:
                        continue
                    if mins_since < self.cfg.optimal_cascade_start:
                        continue
                if tp2_hit:
                    continue

                cascade_count += 1
                sl_pips = body_pips * self.cfg.cascade_sl_mult
                sl_off = self._to_price(sl_pips, pair)
                tp_off = self._to_price(ar_pips * 0.50, pair)

                if signal_dir == "LONG":
                    sl_price = c - sl_off
                    tp_price = c - tp_off
                else:
                    sl_price = c + sl_off
                    tp_price = c + tp_off

                if cascade_count == 2:
                    size = self.cfg.position_size_lots * 0.5
                    act = "cascade_1"
                elif cascade_count == 3:
                    size = self.cfg.position_size_lots * 0.25
                    act = "cascade_2"
                else:
                    continue

                trade = CascadeTrade(ts, signal_dir, c, sl_price, tp_price, size, act, cascade_count - 1)
                active_trades.append(trade)

            # 45-min add
            if (session_direction is not None and not add_done and
                    cascade_count >= 1 and initial_p90_time is not None and len(active_trades) > 0):
                mins_since = (ts - initial_p90_time).total_seconds() / 60.0
                if 45 <= mins_since < 50:
                    if session_direction == "LONG":
                        ext_pips = self._to_pips(c - initial_p90_price, pair)
                    else:
                        ext_pips = self._to_pips(initial_p90_price - c, pair)

                    if ext_pips >= self.cfg.add_extension_pips and not kill_switch:
                        add_done = True
                        tp_off = self._to_price(ar_pips * 0.50, pair)
                        if session_direction == "LONG":
                            tp_price = initial_p90_price - tp_off
                            sl_price = initial_p90_price
                        else:
                            tp_price = initial_p90_price + tp_off
                            sl_price = initial_p90_price

                        size = self.cfg.position_size_lots * 0.75
                        trade = CascadeTrade(ts, session_direction, c, sl_price, tp_price, size, "add_45min", 0)
                        active_trades.append(trade)

        return self._calc_results(all_trades, pair)

    def _calc_results(self, trades, pair):
        if not trades:
            return {"strategy": "P90_Cascade", "pair": pair, "total_trades": 0, "error": "No trades"}

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
        pf = gross_profit / gross_loss if gross_loss > 0 else 0

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

        session_dates = set(t.entry_time.date() for t in trades)

        return {
            "strategy": "P90_Cascade",
            "pair": pair,
            "total_trades": len(trades),
            "total_sessions": len(session_dates),
            "wins": len(wins), "losses": len(losses),
            "win_rate": round(win_rate, 1),
            "total_pnl_pips": round(total_pnl, 2),
            "avg_win_pips": round(avg_win, 2),
            "avg_loss_pips": round(avg_loss, 2),
            "max_drawdown_pips": round(max_dd, 2),
            "profit_factor": round(pf, 2),
            "by_activation_type": by_type_summary,
            "by_exit_reason": by_exit,
        }


# ── Deep Mean Reversion Strategy ─────────────────────────────────────

class DeepMeanReversionStrategy:
    """
    Deep Mean Rebalancing — CEREBUS FX v4.0 (Pages 20-29)
    
    Trigger: Price touches 168% (Stall Zone) or 200% (Deep State) extension
    Entry: Limit order at 200% level
    SL: 8 pips beyond 200% (~220%)
    TP1: Return to 0% (activation level)
    TP2: -50% daily range
    """

    def __init__(self):
        self.position_size_lots = 0.1

    def _utc_to_est(self, utc_hour):
        return (utc_hour - 5 + 24) % 24

    def _to_pips(self, price_diff, pair="EUR/USD"):
        if "JPY" in pair:
            return price_diff * 100
        return price_diff * 10000

    def _to_price(self, pips, pair="EUR/USD"):
        if "JPY" in pair:
            return pips / 100
        return pips / 10000

    def run_backtest(self, df, pair="EUR/USD"):
        if df is None or len(df) < 500:
            return {"error": "Insufficient data", "total_trades": 0}

        df = df.copy()
        df["est_hour"] = df.index.hour.map(self._utc_to_est)
        df["date"] = df.index.date

        asian_high = None
        asian_low = None
        ar_pips = None

        activation_level = None  # P90 entry price (0%)
        stall_zone_price = None  # 168%
        deep_state_price = None  # 200%
        kill_switch_price = None  # 220%
        daily_target_50 = None   # -50% daily range

        active_trade = None
        all_trades = []
        last_date = None
        p90_direction = None

        for i in range(50, len(df) - 1):
            row = df.iloc[i]
            ts = df.index[i]
            est_h = row["est_hour"]
            date = row["date"]
            o, h, l, c = row["open"], row["high"], row["low"], row["close"]

            # New day reset
            if date != last_date:
                if active_trade is not None:
                    dm = 1 if active_trade["direction"] == "LONG" else -1
                    pnl = self._to_pips((c - active_trade["entry"]) * dm, pair)
                    active_trade["pnl_pips"] = pnl
                    active_trade["exit_time"] = ts
                    active_trade["exit_price"] = c
                    active_trade["result"] = "win" if pnl > 0 else "loss"
                    active_trade["exit_reason"] = "new_day"
                    all_trades.append(active_trade)
                    active_trade = None

                asian_high = None
                asian_low = None
                ar_pips = None
                activation_level = None
                stall_zone_price = None
                deep_state_price = None
                kill_switch_price = None
                daily_target_50 = None
                p90_direction = None
                last_date = date

            # Asian range calc (7PM-3AM EST)
            est = self._utc_to_est(row["est_hour"])
            if est >= 19 or est < 3:
                if asian_high is None:
                    asian_high = h
                    asian_low = l
                else:
                    asian_high = max(asian_high, h)
                    asian_low = min(asian_low, l)
                if est == 2 and asian_high is not None:
                    ar_pips = self._to_pips(asian_high - asian_low, pair)
                continue

            if ar_pips is None or ar_pips <= 0:
                continue

            # Hard exit 12PM EST
            if est_h >= 12:
                if active_trade is not None:
                    dm = 1 if active_trade["direction"] == "LONG" else -1
                    pnl = self._to_pips((c - active_trade["entry"]) * dm, pair)
                    active_trade["pnl_pips"] = pnl
                    active_trade["exit_time"] = ts
                    active_trade["exit_price"] = c
                    active_trade["result"] = "win" if pnl > 0 else "loss"
                    active_trade["exit_reason"] = "hard_exit_12pm"
                    all_trades.append(active_trade)
                    active_trade = None
                continue

            # Entry window: 2AM-12PM EST
            if not (2 <= est_h < 12):
                continue

            # Detect P90 activation (first big candle sets direction)
            body_pips = self._to_pips(abs(c - o), pair)
            thresholds = {(2, 4): 4.1, (4, 6): 4.6, (6, 8): 4.6, (8, 10): 5.9, (10, 12): 6.2}
            thresh = 6.2
            for (s, e), t in thresholds.items():
                if s <= est_h < e:
                    thresh = t
                    break

            if body_pips >= thresh and activation_level is None:
                activation_level = c
                p90_direction = "SHORT" if c > o else "LONG"  # Mean reversion: go opposite to P90 direction
                # Actually per manual: P90 direction = resolution direction, reversion = opposite
                # If bullish P90 (c > o), resolution is UP, reversion = SHORT at deep state
                p90_direction = "SHORT" if c > o else "LONG"

                # Calculate extension levels from Asian range
                ar_price = self._to_price(ar_pips, pair)
                if c > o:  # Bullish P90 → price went up → SHORT reversion
                    stall_zone_price = activation_level + ar_price * 1.68
                    deep_state_price = activation_level + ar_price * 2.00
                    kill_switch_price = activation_level + ar_price * 2.20
                    daily_target_50 = activation_level - self._to_price(ar_pips * 0.50, pair)
                else:  # Bearish P90 → price went down → LONG reversion
                    stall_zone_price = activation_level - ar_price * 1.68
                    deep_state_price = activation_level - ar_price * 2.00
                    kill_switch_price = activation_level - ar_price * 2.20
                    daily_target_50 = activation_level + self._to_price(ar_pips * 0.50, pair)

            # Check for deep state touch → enter reversion
            if active_trade is None and deep_state_price is not None and activation_level is not None:
                # Price must touch or exceed deep state
                if p90_direction == "SHORT" and h >= deep_state_price:
                    # Enter SHORT at deep state (limit order)
                    entry = deep_state_price
                    sl = kill_switch_price  # 220%
                    tp1 = activation_level  # Return to 0%
                    tp2 = daily_target_50    # -50% daily range
                    active_trade = {
                        "entry": entry, "direction": "SHORT",
                        "sl": sl, "tp1": tp1, "tp2": tp2,
                        "entry_time": ts, "size": self.position_size_lots,
                    }
                elif p90_direction == "LONG" and l <= deep_state_price:
                    entry = deep_state_price
                    sl = kill_switch_price
                    tp1 = activation_level
                    tp2 = daily_target_50
                    active_trade = {
                        "entry": entry, "direction": "LONG",
                        "sl": sl, "tp1": tp1, "tp2": tp2,
                        "entry_time": ts, "size": self.position_size_lots,
                    }

            # Manage active trade
            if active_trade is not None:
                dm = 1 if active_trade["direction"] == "LONG" else -1

                # SL check
                if active_trade["direction"] == "SHORT" and h >= active_trade["sl"]:
                    pnl = self._to_pips(active_trade["entry"] - active_trade["sl"], pair)
                    active_trade["pnl_pips"] = pnl
                    active_trade["exit_time"] = ts
                    active_trade["exit_price"] = active_trade["sl"]
                    active_trade["result"] = "loss"
                    active_trade["exit_reason"] = "sl_220"
                    all_trades.append(active_trade)
                    active_trade = None
                    continue
                elif active_trade["direction"] == "LONG" and l <= active_trade["sl"]:
                    pnl = self._to_pips(active_trade["sl"] - active_trade["entry"], pair)
                    active_trade["pnl_pips"] = pnl
                    active_trade["exit_time"] = ts
                    active_trade["exit_price"] = active_trade["sl"]
                    active_trade["result"] = "loss"
                    active_trade["exit_reason"] = "sl_220"
                    all_trades.append(active_trade)
                    active_trade = None
                    continue

                # TP1 check (return to activation level)
                if active_trade["direction"] == "SHORT" and l <= active_trade["tp1"]:
                    pnl = self._to_pips(active_trade["entry"] - active_trade["tp1"], pair)
                    active_trade["pnl_pips"] = pnl
                    active_trade["exit_time"] = ts
                    active_trade["exit_price"] = active_trade["tp1"]
                    active_trade["result"] = "win"
                    active_trade["exit_reason"] = "tp1_0pct"
                    all_trades.append(active_trade)
                    active_trade = None
                    continue
                elif active_trade["direction"] == "LONG" and h >= active_trade["tp1"]:
                    pnl = self._to_pips(active_trade["tp1"] - active_trade["entry"], pair)
                    active_trade["pnl_pips"] = pnl
                    active_trade["exit_time"] = ts
                    active_trade["exit_price"] = active_trade["tp1"]
                    active_trade["result"] = "win"
                    active_trade["exit_reason"] = "tp1_0pct"
                    all_trades.append(active_trade)
                    active_trade = None
                    continue

        return self._calc_results(all_trades, pair)

    def _calc_results(self, trades, pair):
        if not trades:
            return {"strategy": "Deep_Mean_Reversion", "pair": pair, "total_trades": 0, "error": "No trades"}

        pnls = [t["pnl_pips"] for t in trades]
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
        pf = gross_profit / gross_loss if gross_loss > 0 else 0

        by_exit = {}
        for t in trades:
            er = t["exit_reason"]
            if er not in by_exit:
                by_exit[er] = 0
            by_exit[er] += 1

        return {
            "strategy": "Deep_Mean_Reversion",
            "pair": pair,
            "total_trades": len(trades),
            "wins": len(wins), "losses": len(losses),
            "win_rate": round(win_rate, 1),
            "total_pnl_pips": round(total_pnl, 2),
            "avg_win_pips": round(avg_win, 2),
            "avg_loss_pips": round(avg_loss, 2),
            "max_drawdown_pips": round(max_dd, 2),
            "profit_factor": round(pf, 2),
            "by_exit_reason": by_exit,
        }


# ── Main Runner ──────────────────────────────────────────────────────

def main():
    data_path = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")
    print(f"Loading data from {data_path.name}...")
    df = _parse_csv(data_path)
    print(f"  Loaded {len(df):,} bars ({df.index[0]} -> {df.index[-1]})")

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── 1. P90 Cascade ──────────────────────────────────────────────
    print("\n" + "="*60)
    print("1. P90 CASCADE ACTIVATION")
    print("="*60)
    strategy = P90CascadeStrategy()
    r1 = strategy.run_backtest(df, "EUR/USD")
    print_results(r1)
    with open(results_dir / f"p90_cascade_{timestamp}.json", "w") as f:
        json.dump(r1, f, indent=2, default=str)

    # ── 2. Deep Mean Reversion ───────────────────────────────────────
    print("\n" + "="*60)
    print("2. DEEP MEAN REVERSION")
    print("="*60)
    strategy2 = DeepMeanReversionStrategy()
    r2 = strategy2.run_backtest(df, "EUR/USD")
    print_results(r2)
    with open(results_dir / f"deep_mean_reversion_{timestamp}.json", "w") as f:
        json.dump(r2, f, indent=2, default=str)

    # ── Summary ──────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for r in [r1, r2]:
        name = r.get("strategy", "?")
        trades = r.get("total_trades", 0)
        wr = r.get("win_rate", 0)
        pnl = r.get("total_pnl_pips", 0)
        pf = r.get("profit_factor", 0)
        print(f"  {name:30s}: {trades:4d} trades | {wr:5.1f}% WR | {pnl:8.1f} pips | PF: {pf:.2f}")
    print("="*60)


def print_results(r):
    if "error" in r and r.get("total_trades", 0) == 0:
        print(f"  ERROR: {r['error']}")
        return
    print(f"  Total Trades:   {r.get('total_trades', 0)}")
    print(f"  Wins:           {r.get('wins', 0)} ({r.get('win_rate', 0)}%)")
    print(f"  Losses:         {r.get('losses', 0)}")
    print(f"  Total P&L:      {r.get('total_pnl_pips', 0)} pips")
    print(f"  Avg Win:        {r.get('avg_win_pips', 0)} pips")
    print(f"  Avg Loss:       {r.get('avg_loss_pips', 0)} pips")
    print(f"  Max Drawdown:   {r.get('max_drawdown_pips', 0)} pips")
    print(f"  Profit Factor:  {r.get('profit_factor', 0)}")
    if "by_activation_type" in r:
        print(f"  By Type:")
        for at, data in r["by_activation_type"].items():
            print(f"    {at:15s}: {data['trades']} trades | {data['win_rate']}% WR | {data['pnl_pips']} pips")
    if "by_exit_reason" in r:
        print(f"  By Exit:")
        for reason, count in sorted(r["by_exit_reason"].items(), key=lambda x: -x[1]):
            print(f"    {reason:20s}: {count}")


if __name__ == "__main__":
    main()
