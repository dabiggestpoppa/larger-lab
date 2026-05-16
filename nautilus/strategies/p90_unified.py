"""
P90 Unified Backtest Engine - CEREBUS FX v4.0
=================================================
Strategies:
  1. P90_Cascade_Combo - Cascade + 45min add (93.4% WR per manual)
  2. P90_Cascade - Initial + up to 3 cascades
  3. P90_Base - Single entry, 3-position scaling

Usage:
  python -m nautilus.strategies.p90_unified --pair EURUSD --strategy all
  python -m nautilus.strategies.p90_unified --all-pairs --strategy cascade_combo
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum

import pandas as pd

DOWNLOADS_DIR = Path(r"C:\Users\wifik\Downloads")
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results")
RESULTS_DIR.mkdir(exist_ok=True)

class Direction(str, Enum):
    NONE = ""
    LONG = "LONG"
    SHORT = "SHORT"

class Tier(str, Enum):
    T1 = "T1"; T2 = "T2"; T3 = "T3"; NO_GO = "NO_GO"; NA = "NA"

class P90Config:
    def __init__(self):
        self.p90_thresholds = {(2,4):4.1,(4,6):4.6,(6,8):4.6,(8,10):5.9,(10,11):6.2}
        self.max_cascades = 3
        self.cascade_window_min = 30
        self.cascade_window_max = 90
        self.cascade_sl_mult = 1.68
        self.add_time_min = 45
        self.add_time_window = 5
        self.add_extension_pips = 8.0
        self.initial_size = 0.40
        self.add_size = 0.30
        self.cascade1_size = 0.20
        self.cascade2_size = 0.10
        self.initial_sl_mult = 0.80
        self.hold_time_min = 120
        self.position_size_lots = 0.1
        self.tp2_pct = 0.50
        self.kill_switch_pct = 1.32

class P90Trade:
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

def utc_to_est(utc_hour): return (utc_hour - 5 + 24) % 24

def to_pips(price_diff, pair="EUR/USD"):
    if "JPY" in pair: return price_diff * 100
    if "XAU" in pair: return price_diff * 10
    return price_diff * 10000

def to_price(pips, pair="EUR/USD"):
    if "JPY" in pair: return pips / 100
    if "XAU" in pair: return pips / 10
    return pips / 10000

def get_threshold(est_h, cfg):
    for (start, end), thresh in cfg.p90_thresholds.items():
        if start <= est_h < end: return thresh
    return 6.2

def get_tier(ar_pips):
    if ar_pips < 20: return Tier.T1
    elif ar_pips < 30: return Tier.T2
    elif ar_pips < 45: return Tier.T3
    return Tier.NO_GO

def load_data(pair, max_bars=None):
    from nautilus.data_loader import _parse_csv
    pair_noslash = pair.replace("/", "")
    patterns = [f"{pair_noslash}!_M5_*.csv", f"{pair_noslash}_M5_*.csv",
                f"{pair_noslash}!_M1_*.csv", f"{pair_noslash}_M1_*.csv"]
    filepath = None
    for pattern in patterns:
        matches = list(DOWNLOADS_DIR.glob(pattern))
        if matches:
            matches.sort(key=lambda p: p.stat().st_size)
            filepath = matches[0]; break
    if filepath is None: return None
    df = _parse_csv(filepath)
    if df is not None and len(df) > 500:
        if max_bars and len(df) > max_bars: df = df.tail(max_bars).copy()
        return df
    return None

def discover_pairs():
    pairs = set()
    for f in DOWNLOADS_DIR.glob("*_M5_*.csv"):
        name = f.stem.split("_")[0].replace("!", "")
        pairs.add(name)
    return sorted(pairs)

def _calc_results(trades, pair, strategy_name):
    if not trades:
        return {"strategy": strategy_name, "pair": pair, "total_trades": 0, "error": "No trades"}
    pnls = [t.pnl_pips for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    total_pnl = sum(pnls)
    win_rate = len(wins) / len(pnls) * 100 if pnls else 0
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    cumulative = [0]
    for p in pnls: cumulative.append(cumulative[-1] + p)
    peak = cumulative[0]; max_dd = 0
    for v in cumulative:
        if v > peak: peak = v
        dd = v - peak
        if dd < max_dd: max_dd = dd
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    by_type = {}
    for t in trades:
        at = t.activation_type
        if at not in by_type: by_type[at] = {"trades": 0, "wins": 0, "pnl": 0}
        by_type[at]["trades"] += 1; by_type[at]["pnl"] += t.pnl_pips
        if t.pnl_pips > 0: by_type[at]["wins"] += 1
    by_type_summary = {at: {"trades": d["trades"], "wins": d["wins"],
        "win_rate": round(d["wins"]/d["trades"]*100,1) if d["trades"]>0 else 0,
        "pnl_pips": round(d["pnl"],2)} for at, d in by_type.items()}
    by_exit = {}
    for t in trades:
        er = t.exit_reason
        if er not in by_exit: by_exit[er] = 0
        by_exit[er] += 1
    session_dates = set(t.entry_time.date() for t in trades)
    return {"strategy": strategy_name, "pair": pair, "total_trades": len(trades),
        "total_sessions": len(session_dates), "wins": len(wins), "losses": len(losses),
        "win_rate": round(win_rate,1), "total_pnl_pips": round(total_pnl,2),
        "avg_win_pips": round(avg_win,2), "avg_loss_pips": round(avg_loss,2),
        "max_drawdown_pips": round(max_dd,2), "profit_factor": round(profit_factor,2),
        "by_activation_type": by_type_summary, "by_exit_reason": by_exit}

def _manage_trades(active_trades, all_trades, asian_high, asian_low, ar_pips,
                   initial_p90_time, ts, h, l, c, cfg, pair, Direction, Tier, P90Trade):
    """Shared trade management logic. Returns (kill_switch, tp2_hit)."""
    trades_to_remove = []
    kill_switch = False
    tp2_hit = False
    for t in active_trades:
        if t.exit_time is not None: continue
        dm = 1 if t.direction == Direction.LONG else -1
        # SL
        if t.direction == Direction.LONG and l <= t.sl_price:
            t.pnl_pips = to_pips(t.sl_price - t.entry_price, pair)
            t.exit_time = ts; t.exit_price = t.sl_price; t.result = "loss"; t.exit_reason = "sl"
            all_trades.append(t); trades_to_remove.append(t); continue
        elif t.direction == Direction.SHORT and h >= t.sl_price:
            t.pnl_pips = to_pips(t.entry_price - t.sl_price, pair)
            t.exit_time = ts; t.exit_price = t.sl_price; t.result = "loss"; t.exit_reason = "sl"
            all_trades.append(t); trades_to_remove.append(t); continue
        # TP2
        if t.direction == Direction.LONG and l <= t.tp_price:
            t.pnl_pips = to_pips(t.tp_price - t.entry_price, pair)
            t.exit_time = ts; t.exit_price = t.tp_price; t.result = "win"; t.exit_reason = "tp2_50"
            all_trades.append(t); trades_to_remove.append(t); tp2_hit = True; continue
        elif t.direction == Direction.SHORT and h >= t.tp_price:
            t.pnl_pips = to_pips(t.entry_price - t.tp_price, pair)
            t.exit_time = ts; t.exit_price = t.tp_price; t.result = "win"; t.exit_reason = "tp2_50"
            all_trades.append(t); trades_to_remove.append(t); tp2_hit = True; continue
        # Kill Switch
        if asian_high is not None:
            ko = to_price(ar_pips * cfg.kill_switch_pct, pair)
            if t.direction == Direction.LONG and h >= asian_high + ko: kill_switch = True
            elif t.direction == Direction.SHORT and l <= asian_low - ko: kill_switch = True
        # Hold Time
        if initial_p90_time is not None:
            mh = (ts - initial_p90_time).total_seconds() / 60.0
            if mh >= cfg.hold_time_min:
                t.pnl_pips = to_pips((c - t.entry_price) * dm, pair)
                t.exit_time = ts; t.exit_price = c
                t.result = "win" if t.pnl_pips > 0 else "loss"; t.exit_reason = "hold_time"
                all_trades.append(t); trades_to_remove.append(t)
    for t in trades_to_remove:
        if t in active_trades: active_trades.remove(t)
    return kill_switch, tp2_hit


# ============================================================================
# STRATEGY 1: P90 Cascade + 45-Min Add Combo
# ============================================================================

def run_cascade_combo(df, pair, cfg):
    if df is None or len(df) < 500:
        return {"strategy": "P90_Cascade_Combo", "pair": pair, "total_trades": 0, "error": "No data"}
    df = df.copy()
    df["est_hour"] = df.index.hour.map(utc_to_est)
    df["date"] = df.index.date

    asian_high = None; asian_low = None; ar_pips = None; tier = Tier.NA
    session_active = False; session_direction = Direction.NONE
    initial_p90_time = None; initial_p90_price = None
    cascade_count = 0; add_done = False
    active_trades = []; all_trades = []; last_date = None

    for i in range(50, len(df) - 1):
        row = df.iloc[i]; ts = df.index[i]; est_h = row["est_hour"]
        date = row["date"]; o, h, l, c = row["open"], row["high"], row["low"], row["close"]

        if date != last_date:
            for t in active_trades:
                if t.exit_time is None:
                    dm = 1 if t.direction == Direction.LONG else -1
                    t.pnl_pips = to_pips((c - t.entry_price) * dm, pair)
                    t.exit_time = ts; t.exit_price = c
                    t.result = "win" if t.pnl_pips > 0 else "loss"; t.exit_reason = "new_day"
                    all_trades.append(t)
            active_trades.clear()
            asian_high = None; asian_low = None; ar_pips = None; tier = Tier.NA
            session_active = False; session_direction = Direction.NONE
            initial_p90_time = None; initial_p90_price = None
            cascade_count = 0; add_done = False; last_date = date

        # Asian Range tracking
        if est_h >= 19 or est_h < 3:
            if asian_high is None: asian_high = h; asian_low = l
            else: asian_high = max(asian_high, h); asian_low = min(asian_low, l)
            continue

        # Classify Asian Range at first bar AFTER Asian session
        if est_h == 3 and asian_high is not None and asian_low is not None and ar_pips is None:
            ar_pips = to_pips(asian_high - asian_low, pair)
            tier = get_tier(ar_pips)

        if tier == Tier.NO_GO or ar_pips is None or ar_pips <= 0: continue

        # Manage trades
        ks, tp2 = _manage_trades(active_trades, all_trades, asian_high, asian_low, ar_pips,
                                  initial_p90_time, ts, h, l, c, cfg, pair, Direction, Tier, P90Trade)
        if ks:
            for t in active_trades:
                if t.exit_time is None:
                    dm = 1 if t.direction == Direction.LONG else -1
                    t.pnl_pips = to_pips((c - t.entry_price) * dm, pair)
                    t.exit_time = ts; t.exit_price = c
                    t.result = "win" if t.pnl_pips > 0 else "loss"; t.exit_reason = "kill_switch_132"
                    all_trades.append(t)
            active_trades.clear(); session_active = False; continue

        if est_h >= 12:
            for t in active_trades:
                if t.exit_time is None:
                    dm = 1 if t.direction == Direction.LONG else -1
                    t.pnl_pips = to_pips((c - t.entry_price) * dm, pair)
                    t.exit_time = ts; t.exit_price = c
                    t.result = "win" if t.pnl_pips > 0 else "loss"; t.exit_reason = "hard_exit_12pm"
                    all_trades.append(t)
            active_trades.clear(); session_active = False; continue

        if not (2 <= est_h < 11): continue

        body_pips = to_pips(abs(c - o), pair)
        threshold = get_threshold(est_h, cfg)
        bull = (c > o) and (body_pips >= threshold)
        bear = (c < o) and (body_pips >= threshold)
        if not bull and not bear: continue
        signal_dir = Direction.LONG if bull else Direction.SHORT

        # Initial P90
        if not session_active:
            session_active = True; session_direction = signal_dir
            initial_p90_time = ts; initial_p90_price = c
            cascade_count = 1; add_done = False
            sl_pips = body_pips * cfg.initial_sl_mult
            sl_off = to_price(sl_pips, pair); tp_off = to_price(ar_pips * cfg.tp2_pct, pair)
            sl = c - sl_off if signal_dir == Direction.LONG else c + sl_off
            tp = c - tp_off if signal_dir == Direction.LONG else c + tp_off
            active_trades.append(P90Trade(ts, signal_dir, c, sl, tp, cfg.position_size_lots, "initial_p90"))

        # Cascade P90
        elif session_direction == signal_dir:
            if cascade_count >= cfg.max_cascades: continue
            ms = (ts - initial_p90_time).total_seconds() / 60.0
            if ms < cfg.cascade_window_min or ms > cfg.cascade_window_max: continue
            if tp2: continue
            cascade_count += 1
            sl_pips = body_pips * cfg.cascade_sl_mult
            sl_off = to_price(sl_pips, pair); tp_off = to_price(ar_pips * cfg.tp2_pct, pair)
            sl = c - sl_off if signal_dir == Direction.LONG else c + sl_off
            tp = c - tp_off if signal_dir == Direction.LONG else c + tp_off
            sz = cfg.position_size_lots * cfg.cascade1_size / cfg.initial_size if cascade_count == 2 else cfg.position_size_lots * cfg.cascade2_size / cfg.initial_size
            at = "cascade_1" if cascade_count == 2 else "cascade_2"
            active_trades.append(P90Trade(ts, signal_dir, c, sl, tp, sz, at))

        # 45-Min Add
        if session_active and not add_done and cascade_count >= 1 and initial_p90_time:
            ms = (ts - initial_p90_time).total_seconds() / 60.0
            if cfg.add_time_min <= ms < cfg.add_time_min + cfg.add_time_window:
                ext = to_pips(c - initial_p90_price, pair) if session_direction == Direction.LONG else to_pips(initial_p90_price - c, pair)
                if ext >= cfg.add_extension_pips:
                    add_done = True
                    tp_off = to_price(ar_pips * cfg.tp2_pct, pair)
                    tp = initial_p90_price - tp_off if session_direction == Direction.LONG else initial_p90_price + tp_off
                    sl = initial_p90_price  # breakeven
                    sz = cfg.position_size_lots * cfg.add_size / cfg.initial_size
                    active_trades.append(P90Trade(ts, session_direction, c, sl, tp, sz, "add_45min"))

    return _calc_results(all_trades, pair, "P90_Cascade_Combo")


# ============================================================================
# STRATEGY 2: P90 Cascade Only
# ============================================================================

def run_cascade_only(df, pair, cfg):
    if df is None or len(df) < 500:
        return {"strategy": "P90_Cascade", "pair": pair, "total_trades": 0, "error": "No data"}
    df = df.copy()
    df["est_hour"] = df.index.hour.map(utc_to_est)
    df["date"] = df.index.date

    asian_high = None; asian_low = None; ar_pips = None; tier = Tier.NA
    session_direction = Direction.NONE; initial_p90_time = None
    cascade_count = 0
    active_trades = []; all_trades = []; last_date = None

    for i in range(50, len(df) - 1):
        row = df.iloc[i]; ts = df.index[i]; est_h = row["est_hour"]
        date = row["date"]; o, h, l, c = row["open"], row["high"], row["low"], row["close"]

        if date != last_date:
            for t in active_trades:
                if t.exit_time is None:
                    dm = 1 if t.direction == Direction.LONG else -1
                    t.pnl_pips = to_pips((c - t.entry_price) * dm, pair)
                    t.exit_time = ts; t.exit_price = c
                    t.result = "win" if t.pnl_pips > 0 else "loss"; t.exit_reason = "new_day"
                    all_trades.append(t)
            active_trades.clear()
            asian_high = None; asian_low = None; ar_pips = None; tier = Tier.NA
            session_direction = Direction.NONE; initial_p90_time = None
            cascade_count = 0; last_date = date

        if est_h >= 19 or est_h < 3:
            if asian_high is None: asian_high = h; asian_low = l
            else: asian_high = max(asian_high, h); asian_low = min(asian_low, l)
            continue

        if est_h == 3 and asian_high is not None and asian_low is not None and ar_pips is None:
            ar_pips = to_pips(asian_high - asian_low, pair); tier = get_tier(ar_pips)

        if tier == Tier.NO_GO or ar_pips is None or ar_pips <= 0: continue

        ks, tp2 = _manage_trades(active_trades, all_trades, asian_high, asian_low, ar_pips,
                                  initial_p90_time, ts, h, l, c, cfg, pair, Direction, Tier, P90Trade)
        if ks:
            for t in active_trades:
                if t.exit_time is None:
                    dm = 1 if t.direction == Direction.LONG else -1
                    t.pnl_pips = to_pips((c - t.entry_price) * dm, pair)
                    t.exit_time = ts; t.exit_price = c
                    t.result = "win" if t.pnl_pips > 0 else "loss"; t.exit_reason = "kill_switch_132"
                    all_trades.append(t)
            active_trades.clear(); session_direction = Direction.NONE; continue

        if est_h >= 12:
            for t in active_trades:
                if t.exit_time is None:
                    dm = 1 if t.direction == Direction.LONG else -1
                    t.pnl_pips = to_pips((c - t.entry_price) * dm, pair)
                    t.exit_time = ts; t.exit_price = c
                    t.result = "win" if t.pnl_pips > 0 else "loss"; t.exit_reason = "hard_exit_12pm"
                    all_trades.append(t)
            active_trades.clear(); session_direction = Direction.NONE; continue

        if not (2 <= est_h < 11): continue

        body_pips = to_pips(abs(c - o), pair)
        threshold = get_threshold(est_h, cfg)
        bull = (c > o) and (body_pips >= threshold)
        bear = (c < o) and (body_pips >= threshold)
        if not bull and not bear: continue
        signal_dir = Direction.LONG if bull else Direction.SHORT

        if session_direction == Direction.NONE:
            session_direction = signal_dir; initial_p90_time = ts; cascade_count = 1
            sl_pips = body_pips * cfg.initial_sl_mult
            sl_off = to_price(sl_pips, pair); tp_off = to_price(ar_pips * cfg.tp2_pct, pair)
            sl = c - sl_off if signal_dir == Direction.LONG else c + sl_off
            tp = c - tp_off if signal_dir == Direction.LONG else c + tp_off
            active_trades.append(P90Trade(ts, signal_dir, c, sl, tp, cfg.position_size_lots, "initial", 0))

        elif session_direction == signal_dir:
            if cascade_count >= cfg.max_cascades: continue
            ms = (ts - initial_p90_time).total_seconds() / 60.0
            if ms < cfg.cascade_window_min or ms > cfg.cascade_window_max: continue
            if tp2: continue
            cascade_count += 1
            sl_pips = body_pips * cfg.cascade_sl_mult
            sl_off = to_price(sl_pips, pair); tp_off = to_price(ar_pips * cfg.tp2_pct, pair)
            sl = c - sl_off if signal_dir == Direction.LONG else c + sl_off
            tp = c - tp_off if signal_dir == Direction.LONG else c + tp_off
            sz = cfg.position_size_lots * cfg.cascade1_size / cfg.initial_size if cascade_count == 2 else cfg.position_size_lots * cfg.cascade2_size / cfg.initial_size
            at = "cascade_1" if cascade_count == 2 else "cascade_2"
            active_trades.append(P90Trade(ts, signal_dir, c, sl, tp, sz, at, cascade_count - 1))

    return _calc_results(all_trades, pair, "P90_Cascade")


# ============================================================================
# STRATEGY 3: P90 Base
# ============================================================================

def run_p90_base(df, pair, cfg):
    if df is None or len(df) < 500:
        return {"strategy": "P90_Base", "pair": pair, "total_trades": 0, "error": "No data"}
    df = df.copy()
    df["est_hour"] = df.index.hour.map(utc_to_est)
    df["date"] = df.index.date

    asian_high = None; asian_low = None; ar_pips = None; tier = Tier.NA
    session_direction = Direction.NONE; initial_p90_time = None
    active_trades = []; all_trades = []; last_date = None

    for i in range(50, len(df) - 1):
        row = df.iloc[i]; ts = df.index[i]; est_h = row["est_hour"]
        date = row["date"]; o, h, l, c = row["open"], row["high"], row["low"], row["close"]

        if date != last_date:
            for t in active_trades:
                if t.exit_time is None:
                    dm = 1 if t.direction == Direction.LONG else -1
                    t.pnl_pips = to_pips((c - t.entry_price) * dm, pair)
                    t.exit_time = ts; t.exit_price = c
                    t.result = "win" if t.pnl_pips > 0 else "loss"; t.exit_reason = "new_day"
                    all_trades.append(t)
            active_trades.clear()
            asian_high = None; asian_low = None; ar_pips = None; tier = Tier.NA
            session_direction = Direction.NONE; initial_p90_time = None
            last_date = date

        if est_h >= 19 or est_h < 3:
            if asian_high is None: asian_high = h; asian_low = l
            else: asian_high = max(asian_high, h); asian_low = min(asian_low, l)
            continue

        if est_h == 3 and asian_high is not None and asian_low is not None and ar_pips is None:
            ar_pips = to_pips(asian_high - asian_low, pair); tier = get_tier(ar_pips)

        if tier == Tier.NO_GO or ar_pips is None or ar_pips <= 0: continue

        ks, tp2 = _manage_trades(active_trades, all_trades, asian_high, asian_low, ar_pips,
                                  initial_p90_time, ts, h, l, c, cfg, pair, Direction, Tier, P90Trade)
        if ks:
            for t in active_trades:
                if t.exit_time is None:
                    dm = 1 if t.direction == Direction.LONG else -1
                    t.pnl_pips = to_pips((c - t.entry_price) * dm, pair)
                    t.exit_time = ts; t.exit_price = c
                    t.result = "win" if t.pnl_pips > 0 else "loss"; t.exit_reason = "kill_switch_132"
                    all_trades.append(t)
            active_trades.clear(); session_direction = Direction.NONE; continue

        if est_h >= 12:
            for t in active_trades:
                if t.exit_time is None:
                    dm = 1 if t.direction == Direction.LONG else -1
                    t.pnl_pips = to_pips((c - t.entry_price) * dm, pair)
                    t.exit_time = ts; t.exit_price = c
                    t.result = "win" if t.pnl_pips > 0 else "loss"; t.exit_reason = "hard_exit_12pm"
                    all_trades.append(t)
            active_trades.clear(); session_direction = Direction.NONE; continue

        if not (2 <= est_h < 11): continue

        body_pips = to_pips(abs(c - o), pair)
        threshold = get_threshold(est_h, cfg)
        bull = (c > o) and (body_pips >= threshold)
        bear = (c < o) and (body_pips >= threshold)
        if not bull and not bear: continue
        signal_dir = Direction.LONG if bull else Direction.SHORT

        if session_direction == Direction.NONE:
            session_direction = signal_dir; initial_p90_time = ts
            sizes = [0.40, 0.40, 0.20]
            sl_mults = [cfg.initial_sl_mult, 1.50, 1.50]
            act_types = ["pos1_40", "pos2_40", "pos3_20"]
            for sz_pct, sl_mult, at in zip(sizes, sl_mults, act_types):
                sl_pips = body_pips * sl_mult
                sl_off = to_price(sl_pips, pair); tp_off = to_price(ar_pips * cfg.tp2_pct, pair)
                sl = c - sl_off if signal_dir == Direction.LONG else c + sl_off
                tp = c - tp_off if signal_dir == Direction.LONG else c + tp_off
                active_trades.append(P90Trade(ts, signal_dir, c, sl, tp,
                    cfg.position_size_lots * sz_pct / cfg.initial_size, at))

    return _calc_results(all_trades, pair, "P90_Base")


# ============================================================================
# Display & Main
# ============================================================================

def display_results(r):
    print(f"\n{'='*60}")
    print(f"  {r.get('strategy','?')} - {r.get('pair','?')}")
    print(f"{'='*60}")
    if r.get("error") and r.get("total_trades",0) == 0:
        print(f"  [FAIL] {r['error']}"); return
    print(f"  Trades: {r.get('total_trades',0)} | Sessions: {r.get('total_sessions',0)}")
    print(f"  Win Rate: {r.get('win_rate',0)}% ({r.get('wins',0)}W/{r.get('losses',0)}L)")
    print(f"  P&L: {r.get('total_pnl_pips',0)}p | Avg Win: {r.get('avg_win_pips',0)}p | Avg Loss: {r.get('avg_loss_pips',0)}p")
    print(f"  Max DD: {r.get('max_drawdown_pips',0)}p | PF: {r.get('profit_factor',0)}")
    if "by_activation_type" in r:
        print(f"  By Type:")
        for at, d in r["by_activation_type"].items():
            print(f"    {at:15s}: {d['trades']}t | {d['win_rate']}% WR | {d['pnl_pips']}p")
    if "by_exit_reason" in r:
        print(f"  By Exit:")
        for reason, count in sorted(r["by_exit_reason"].items(), key=lambda x: -x[1]):
            print(f"    {reason:20s}: {count}")
    print(f"{'='*60}")

def main():
    parser = argparse.ArgumentParser(description="P90 Unified Backtest Engine")
    parser.add_argument("--pair", type=str, default="EURUSD")
    parser.add_argument("--strategy", type=str, default="all",
                        choices=["all", "cascade_combo", "cascade", "base"])
    parser.add_argument("--all-pairs", action="store_true")
    parser.add_argument("--max-bars", type=int, default=None)
    args = parser.parse_args()

    cfg = P90Config()
    pairs = discover_pairs() if args.all_pairs else [args.pair]
    if not pairs: pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]

    if args.strategy == "all":
        strategies = [("cascade_combo", run_cascade_combo), ("cascade", run_cascade_only), ("base", run_p90_base)]
    elif args.strategy == "cascade_combo":
        strategies = [("cascade_combo", run_cascade_combo)]
    elif args.strategy == "cascade":
        strategies = [("cascade", run_cascade_only)]
    else:
        strategies = [("base", run_p90_base)]

    all_results = []
    for pair in pairs:
        print(f"\n[LOAD] {pair}...")
        df = load_data(pair, max_bars=args.max_bars)
        if df is None: continue
        for name, func in strategies:
            print(f"[RUN] {name}...")
            r = func(df, pair, cfg)
            display_results(r)
            all_results.append(r)

    if all_results:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        rf = RESULTS_DIR / f"p90_unified_{ts}.json"
        with open(rf, "w") as f: json.dump(all_results, f, indent=2, default=str)
        print(f"\n[SAVE] {rf}")

    if len(all_results) > 1:
        print(f"\n{'='*60}\n  SUMMARY\n{'='*60}")
        for r in all_results:
            s = "[OK]" if r.get("total_pnl_pips",0) > 0 else "[--]"
            print(f"  {s} {r['strategy']:20s} {r['pair']:10s} | WR:{r.get('win_rate',0):5.1f}% | P&L:{r.get('total_pnl_pips',0):8.1f}p | T:{r.get('total_trades',0)}")
        print(f"{'='*60}")

if __name__ == "__main__":
    main()
