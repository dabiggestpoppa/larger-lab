#!/usr/bin/env python3
"""
Multi-Asset Forex M5 Backtest Engine
=====================================
Runs all 10 CEREBUS strategies on 8 forex M5 pairs with cost model.
Cost: 2.9 pips/trade (spread 0.2 + slippage 2.0 + commission 0.7)
"""
import sys
import json
import time
import warnings
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

# ── Configuration ────────────────────────────────────────────────────────────

DOWNLOADS = Path(r"C:\Users\wifik\Downloads")
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results")
REPORTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

COST_PER_TRADE_PIPS = 2.9  # spread 0.2 + slippage 2.0 + commission 0.7

FOREX_FILES = [
    ("EURUSD", "EURUSD!_M5_202301020000_202605061250.csv"),
    ("GBPUSD", "GBPUSD!_M5_202301020000_202605061250.csv"),
    ("USDJPY", "USDJPY!_M5_202301020000_202605061250.csv"),
    ("USDCHF", "USDCHF!_M5_202301020000_202605061250.csv"),
    ("AUDUSD", "AUDUSD!_M5_202301020000_202605061250.csv"),
    ("NZDUSD", "NZDUSD!_M5_202301020000_202605061250.csv"),
    ("USDCAD", "USDCAD!_M5_202301020000_202605061250.csv"),
    ("CHFJPY", "CHFJPY!_M5_202201030000_202605061250.csv"),
]

# ── Data Loading ─────────────────────────────────────────────────────────────

def load_csv_m5(filename, pair_name):
    """Load a forex M5 CSV file."""
    data_path = DOWNLOADS / filename
    if not data_path.exists():
        print(f"  [X] File not found: {data_path}")
        return None
    size_mb = data_path.stat().st_size // 1024 // 1024
    print(f"  [>] Loading {data_path.name} ({size_mb}MB)...")
    records = []
    with open(data_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for line in lines[1:]:
        parts = line.strip().split()
        if len(parts) < 7:
            continue
        try:
            ts = pd.Timestamp(f"{parts[0]} {parts[1]}", tz='UTC')
            o, h, l, c = float(parts[2]), float(parts[3]), float(parts[4]), float(parts[5])
            vol = int(parts[6]) if len(parts[6]) < 20 else 0
            records.append({'open': o, 'high': h, 'low': l, 'close': c, 'volume': vol, 'ts': ts})
        except (ValueError, IndexError):
            continue
    df = pd.DataFrame(records)
    df.set_index('ts', inplace=True)
    df.sort_index(inplace=True)
    df = df[~df.index.duplicated(keep='first')]
    print(f"    [OK] Loaded {len(df):,} bars ({df.index[0].date()} -> {df.index[-1].date()})")
    return df


# ── Utility Functions ────────────────────────────────────────────────────────

def to_pips(price_diff, pair):
    if "JPY" in pair: return price_diff * 100.0
    return price_diff * 10000.0

def to_price(pips, pair):
    if "JPY" in pair: return pips / 100.0
    return pips / 10000.0

def prepare_data(df, pair):
    df = df.copy()
    df['utc_h'] = df.index.hour
    df['est_h'] = (df['utc_h'] - 5 + 24) % 24
    df['date'] = df.index.date
    df['body_pips'] = to_pips((df['close'] - df['open']).abs(), pair)
    df['weekday'] = df.index.dayofweek
    return df

def get_day_data(df, date):
    return df[df['date'] == date].copy()

def calc_asian_range(day_df, pair):
    asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
    if len(asian) < 2:
        return None, None, None
    ah = asian['high'].max()
    al = asian['low'].min()
    ar = to_pips(ah - al, pair)
    return ah, al, ar

def classify_tier(ar_pips):
    if ar_pips is None: return 'NA'
    if ar_pips < 20: return 'T1'
    if ar_pips < 30: return 'T2'
    if ar_pips < 45: return 'T3'
    return 'NO_GO'

def p90_threshold(est_h):
    if est_h < 2 or est_h >= 11: return 99.0
    if est_h < 4: return 4.1
    if est_h < 6: return 4.6
    if est_h < 8: return 4.6
    if est_h < 10: return 5.9
    if est_h < 11: return 6.2
    return 99.0

def manage_trade(post_df, entry_price, direction, sl, tp, pair, hard_exit_est=17):
    if post_df.empty:
        return None
    for idx, row in post_df.iterrows():
        h, l, c = row['high'], row['low'], row['close']
        if row['est_h'] >= hard_exit_est:
            pnl = to_pips(c - entry_price, pair) * (1 if direction == 'LONG' else -1)
            return {'pnl': pnl, 'result': 'W' if pnl > 0 else 'L',
                    'reason': 'hard_exit', 'exit_price': c, 'exit_time': idx}
        if direction == 'LONG':
            if l <= sl:
                pnl = to_pips(sl - entry_price, pair)
                return {'pnl': pnl, 'result': 'L', 'reason': 'sl', 'exit_price': sl, 'exit_time': idx}
            if h >= tp:
                pnl = to_pips(tp - entry_price, pair)
                return {'pnl': pnl, 'result': 'W', 'reason': 'tp', 'exit_price': tp, 'exit_time': idx}
        else:
            if h >= sl:
                pnl = to_pips(entry_price - sl, pair)
                return {'pnl': pnl, 'result': 'L', 'reason': 'sl', 'exit_price': sl, 'exit_time': idx}
            if l <= tp:
                pnl = to_pips(entry_price - tp, pair)
                return {'pnl': pnl, 'result': 'W', 'reason': 'tp', 'exit_price': tp, 'exit_time': idx}
    last = post_df.iloc[-1]
    c = last['close']
    pnl = to_pips(c - entry_price, pair) * (1 if direction == 'LONG' else -1)
    return {'pnl': pnl, 'result': 'W' if pnl > 0 else 'L',
            'reason': 'end_data', 'exit_price': c, 'exit_time': post_df.index[-1]}


def calc_results(trades, name, pair):
    if not trades:
        return {"strategy": name, "pair": pair, "total_trades": 0, "error": "No trades"}
    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    total = sum(pnls)
    wr = len(wins) / len(pnls) * 100 if pnls else 0
    avg_w = sum(wins) / len(wins) if wins else 0
    avg_l = sum(losses) / len(losses) if losses else 0
    cum, peak, max_dd = [0], 0, 0
    for p in pnls:
        cum.append(cum[-1] + p)
    for v in cum:
        if v > peak: peak = v
        max_dd = min(max_dd, v - peak)
    gp = sum(wins) if wins else 0
    gl = abs(sum(losses)) if losses else 1
    pf = gp / gl if gl > 0 else 0
    expectancy = total / len(pnls) if pnls else 0
    by_exit = {}
    for t in trades:
        k = t.get('reason', 'unknown')
        by_exit[k] = by_exit.get(k, 0) + 1
    return {
        "strategy": name, "pair": pair,
        "total_trades": len(trades), "wins": len(wins), "losses": len(losses),
        "win_rate": round(wr, 1), "total_pnl": round(total, 2),
        "avg_win": round(avg_w, 2), "avg_loss": round(avg_l, 2),
        "max_dd": round(max_dd, 2), "profit_factor": round(pf, 2),
        "expectancy": round(expectancy, 3),
        "by_exit": by_exit,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 1: DEEP MEAN REVERSION
# ═══════════════════════════════════════════════════════════════════════════════

def run_deep_mean_reversion(df, pair):
    df = prepare_data(df, pair)
    trades = []
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day, pair)
        if ar is None or ar > 45 or ar < 3: continue
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        direction, p90, p90_time = None, None, None
        for idx, row in entry.iterrows():
            if row['body_pips'] >= p90_threshold(row['est_h']):
                direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
                p90 = row; p90_time = idx; break
        if direction is None: continue
        activation = p90['close']
        body_pips = to_pips(abs(p90['close'] - p90['open']), pair)
        deep_state = activation + to_price(body_pips * 2.00, pair) * (1 if direction == 'LONG' else -1)
        kill_switch = activation + to_price(body_pips * 2.20, pair) * (1 if direction == 'LONG' else -1)
        post_p90 = day[(day.index > p90_time) & (day['est_h'] < 12)]
        if post_p90.empty: continue
        touch_idx = None
        for idx, row in post_p90.iterrows():
            if direction == 'LONG' and row['low'] <= deep_state: touch_idx = idx; break
            elif direction == 'SHORT' and row['high'] >= deep_state: touch_idx = idx; break
        if touch_idx is None: continue
        rev_direction = 'SHORT' if direction == 'LONG' else 'LONG'
        post_entry = day[(day.index > touch_idx) & (day['est_h'] < 17)]
        if post_entry.empty: continue
        trade = manage_trade(post_entry, deep_state, rev_direction, kill_switch, activation, pair)
        if trade: trades.append(trade)
    return calc_results(trades, "Deep_Mean_Reversion", pair)


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 2: STALL-HARVEST CFD
# ═══════════════════════════════════════════════════════════════════════════════

def run_stall_harvest_cfd(df, pair):
    df = prepare_data(df, pair)
    trades = []
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day, pair)
        if ar is None or ar > 45 or ar < 3: continue
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        direction, p90, p90_time = None, None, None
        for idx, row in entry.iterrows():
            if row['body_pips'] >= p90_threshold(row['est_h']):
                direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
                p90 = row; p90_time = idx; break
        if direction is None: continue
        activation = p90['close']
        body_pips = to_pips(abs(p90['close'] - p90['open']), pair)
        stall_zone = activation + to_price(body_pips * 1.68, pair) * (1 if direction == 'LONG' else -1)
        deep_state = activation + to_price(body_pips * 2.00, pair) * (1 if direction == 'LONG' else -1)
        post_p90 = day[(day.index > p90_time) & (day['est_h'] < 12)]
        if post_p90.empty: continue
        entered, entry_idx = False, None
        for idx, row in post_p90.iterrows():
            if direction == 'LONG' and row['close'] > deep_state: break
            if direction == 'SHORT' and row['close'] < deep_state: break
            if (idx - p90_time).total_seconds() > 1800: break
            if direction == 'LONG' and row['high'] >= stall_zone: entered = True; entry_idx = idx; break
            elif direction == 'SHORT' and row['low'] <= stall_zone: entered = True; entry_idx = idx; break
        if not entered: continue
        rev_direction = 'SHORT' if direction == 'LONG' else 'LONG'
        buffer = to_price(body_pips * 0.5, pair)
        if rev_direction == 'SHORT':
            rev_sl = deep_state + buffer
            rev_tp = activation - to_price(ar * 0.30, pair)
        else:
            rev_sl = deep_state - buffer
            rev_tp = activation + to_price(ar * 0.30, pair)
        post_entry = day[(day.index > entry_idx) & (day['est_h'] < 17)]
        if post_entry.empty: continue
        trade = manage_trade(post_entry, stall_zone, rev_direction, rev_sl, rev_tp, pair)
        if trade: trades.append(trade)
    return calc_results(trades, "Stall_Harvest_CFD", pair)


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 3: CONSTRAINT ANCHOR
# ═══════════════════════════════════════════════════════════════════════════════

def run_constraint_anchor(df, pair):
    df = prepare_data(df, pair)
    trades = []
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day, pair)
        if ar is None or ar > 30 or ar < 3: continue
        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
        activated = False
        for idx, row in entry.iterrows():
            if row['body_pips'] < 4.6: continue
            ep = row['close']
            body_pips = row['body_pips']
            if row['close'] > ah and row['high'] > ah:
                direction = 'LONG'
                sl = ep - to_price(body_pips * 0.80, pair)
                tp1 = ep + to_price(ar * 0.25, pair)
                tp2 = ep + to_price(ar * 0.50, pair)
                activated = True; break
            elif row['close'] < al and row['low'] < al:
                direction = 'SHORT'
                sl = ep + to_price(body_pips * 0.80, pair)
                tp1 = ep - to_price(ar * 0.25, pair)
                tp2 = ep - to_price(ar * 0.50, pair)
                activated = True; break
        if not activated: continue
        post = day[(day.index > idx) & (day['est_h'] < 17)]
        if post.empty: continue
        trade_pnl = None
        half_closed = False
        be_level = ep + to_price(2.0, pair) * (1 if direction == 'LONG' else -1)
        exit_reason = 'managed'
        for pidx, row in post.iterrows():
            h, l, c = row['high'], row['low'], row['close']
            if row['est_h'] >= 17:
                pnl = to_pips(c - ep, pair) * (1 if direction == 'LONG' else -1)
                if not half_closed: trade_pnl = pnl
                else:
                    half_pnl = to_pips(tp1 - ep, pair) * (1 if direction == 'LONG' else -1)
                    trade_pnl = half_pnl + pnl
                exit_reason = 'hard_exit'; break
            if direction == 'LONG':
                if not half_closed and l <= sl: trade_pnl = to_pips(sl - ep, pair); exit_reason = 'sl'; break
                elif half_closed and l <= be_level:
                    half_pnl = to_pips(tp1 - ep, pair); trade_pnl = half_pnl + to_pips(be_level - ep, pair)
                    exit_reason = 'tp_be'; break
                if not half_closed and h >= tp1: half_closed = True
                elif half_closed and h >= tp2:
                    half_pnl = to_pips(tp1 - ep, pair); trade_pnl = half_pnl + to_pips(tp2 - ep, pair)
                    exit_reason = 'tp_full'; break
            else:
                if not half_closed and h >= sl: trade_pnl = to_pips(ep - sl, pair); exit_reason = 'sl'; break
                elif half_closed and h >= be_level:
                    half_pnl = to_pips(ep - tp1, pair); trade_pnl = half_pnl + to_pips(ep - be_level, pair)
                    exit_reason = 'tp_be'; break
                if not half_closed and l <= tp1: half_closed = True
                elif half_closed and l <= tp2:
                    half_pnl = to_pips(ep - tp1, pair); trade_pnl = half_pnl + to_pips(ep - tp2, pair)
                    exit_reason = 'tp_full'; break
        if trade_pnl is None:
            c = post.iloc[-1]['close']
            if not half_closed: trade_pnl = to_pips(c - ep, pair) * (1 if direction == 'LONG' else -1)
            else:
                half_pnl = to_pips(tp1 - ep, pair) * (1 if direction == 'LONG' else -1)
                remaining = to_pips(c - ep, pair) * (1 if direction == 'LONG' else -1)
                trade_pnl = half_pnl + remaining
            exit_reason = 'end_data'
        trades.append({'pnl': trade_pnl, 'result': 'W' if trade_pnl > 0 else 'L',
                       'reason': exit_reason, 'exit_price': ep, 'exit_time': post.index[-1],
                       'entry_time': idx, 'ar_pips': ar, 'direction': direction})
    return calc_results(trades, "Constraint_Anchor", pair)


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 4: BLIND STRUCTURAL CHAIN
# ═══════════════════════════════════════════════════════════════════════════════

def run_blind_structural_chain(df, pair):
    df = prepare_data(df, pair)
    trades = []
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day, pair)
        if ar is None or ar > 45 or ar < 3: continue
        tier = classify_tier(ar)
        if tier == 'T1': impulse_min = 12.0
        elif tier == 'T2': impulse_min = 16.0
        elif tier == 'T3': impulse_min = 20.0
        else: continue
        baseline_data = day[day['est_h'] == 3]
        if baseline_data.empty: continue
        baseline_price = baseline_data.iloc[0]['close']
        baseline_time = baseline_data.index[0]
        entry_data = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
        cycle_count = 0
        max_cycles = 3
        last_extreme = baseline_price
        impulse_direction = None
        impulse_size_pips = 0
        looking_for_impulse = True
        looking_for_pullback = False
        pullback_low = None
        pullback_high = None
        pullback_start_time = None
        invalidated = False
        entry_this_cycle = False
        i = 0
        while i < len(entry_data):
            row = entry_data.iloc[i]
            idx = entry_data.index[i]
            c = row['close']
            if looking_for_impulse:
                move_pips = to_pips(c - baseline_price, pair)
                if abs(move_pips) >= impulse_min:
                    impulse_direction = 'LONG' if move_pips > 0 else 'SHORT'
                    impulse_size_pips = abs(move_pips)
                    last_extreme = c
                    looking_for_impulse = False
                    looking_for_pullback = True
                    pullback_start_time = idx
                    pullback_low = row['low']
                    pullback_high = row['high']
                    invalidated = False
                    entry_this_cycle = False
            elif looking_for_pullback and not entry_this_cycle:
                if impulse_direction == 'LONG':
                    pullback_low = min(pullback_low, row['low'])
                    impulse_range = to_pips(last_extreme - baseline_price, pair)
                    if impulse_range > 0:
                        if to_pips(last_extreme - pullback_low, pair) / impulse_range > 0.80:
                            invalidated = True
                    if impulse_size_pips > 0:
                        retrace_pct = to_pips(last_extreme - pullback_low, pair) / impulse_size_pips
                        if 0.32 <= retrace_pct <= 0.50 and not invalidated:
                            entry_price = c
                            sl = pullback_low - to_price(5.0, pair)
                            tp = entry_price + to_price(impulse_size_pips * 0.80, pair)
                            post = day[(day.index > idx) & (day['est_h'] < 17)]
                            if not post.empty:
                                trade = manage_trade(post, entry_price, 'LONG', sl, tp, pair)
                                if trade: trades.append(trade)
                            entry_this_cycle = True
                            cycle_count += 1
                            if cycle_count >= max_cycles: break
                            looking_for_impulse = True
                            looking_for_pullback = False
                            baseline_price = c
                            i += 1; continue
                elif impulse_direction == 'SHORT':
                    pullback_high = max(pullback_high, row['high'])
                    impulse_range = to_pips(baseline_price - last_extreme, pair)
                    if impulse_range > 0:
                        if to_pips(pullback_high - last_extreme, pair) / impulse_range > 0.80:
                            invalidated = True
                    if impulse_size_pips > 0:
                        retrace_pct = to_pips(pullback_high - last_extreme, pair) / impulse_size_pips
                        if 0.32 <= retrace_pct <= 0.50 and not invalidated:
                            entry_price = c
                            sl = pullback_high + to_price(5.0, pair)
                            tp = entry_price - to_price(impulse_size_pips * 0.80, pair)
                            post = day[(day.index > idx) & (day['est_h'] < 17)]
                            if not post.empty:
                                trade = manage_trade(post, entry_price, 'SHORT', sl, tp, pair)
                                if trade: trades.append(trade)
                            entry_this_cycle = True
                            cycle_count += 1
                            if cycle_count >= max_cycles: break
                            looking_for_impulse = True
                            looking_for_pullback = False
                            baseline_price = c
                            i += 1; continue
                if (idx - pullback_start_time).total_seconds() > 5400:
                    looking_for_impulse = True
                    looking_for_pullback = False
                    invalidated = False
                if impulse_direction == 'LONG' and c > last_extreme:
                    last_extreme = c
                    impulse_size_pips = to_pips(c - baseline_price, pair)
                    pullback_low = row['low']
                elif impulse_direction == 'SHORT' and c < last_extreme:
                    last_extreme = c
                    impulse_size_pips = to_pips(baseline_price - c, pair)
                    pullback_high = row['high']
            i += 1
    return calc_results(trades, "Blind_Structural_Chain", pair)


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 5: TWO PLAYS
# ═══════════════════════════════════════════════════════════════════════════════

def run_two_plays(df, pair):
    df = prepare_data(df, pair)
    trades = []
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day, pair)
        if ar is None or ar > 45 or ar < 3: continue
        tier = classify_tier(ar)
        if tier in ('T1', 'T2'):
            entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
            for idx, row in entry.iterrows():
                if row['body_pips'] < p90_threshold(row['est_h']): continue
                ep = row['close']
                body_pips = row['body_pips']
                if row['close'] > ah:
                    direction = 'LONG'; close_dist = to_pips(row['close'] - ah, pair)
                elif row['close'] < al:
                    direction = 'SHORT'; close_dist = to_pips(al - row['close'], pair)
                else: continue
                if close_dist < 2.0 or ar > 20: continue
                sl = ep - to_price(body_pips * 1.5, pair) * (1 if direction == 'LONG' else -1)
                tp = ep + to_price(ar * 0.35, pair) * (1 if direction == 'LONG' else -1)
                post = day[(day.index > idx) & (day['est_h'] < 17)]
                if not post.empty:
                    trade = manage_trade(post, ep, direction, sl, tp, pair)
                    if trade: trades.append(trade)
                break
        elif tier == 'T3':
            entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
            break_idx = None
            break_direction = None
            break_price = None
            for idx, row in entry.iterrows():
                if row['body_pips'] < 4.6: continue
                if row['close'] > ah and row['high'] > ah:
                    break_direction = 'LONG'; break_idx = idx; break_price = row['close']; break
                elif row['close'] < al and row['low'] < al:
                    break_direction = 'SHORT'; break_idx = idx; break_price = row['close']; break
            if break_idx is None: continue
            hold_end = break_idx + pd.Timedelta(hours=2)
            hold_data = day[(day.index > break_idx) & (day.index <= hold_end)]
            if hold_data.empty: continue
            held = True
            for hidx, hrow in hold_data.iterrows():
                if break_direction == 'LONG' and hrow['close'] < al: held = False; break
                elif break_direction == 'SHORT' and hrow['close'] > ah: held = False; break
            if not held: continue
            impulse_leg = to_pips(abs(break_price - (ah if break_direction == 'LONG' else al)), pair)
            post_hold = day[(day.index > hold_end) & (day['est_h'] < 12)]
            for idx, row in post_hold.iterrows():
                if break_direction == 'LONG': retrace = to_pips(break_price - row['low'], pair)
                else: retrace = to_pips(row['high'] - break_price, pair)
                if impulse_leg > 0: retrace_pct = retrace / impulse_leg
                else: continue
                if 0.32 <= retrace_pct <= 0.50:
                    ep = row['close']
                    sl = ep - to_price(impulse_leg * 0.80, pair) * (1 if break_direction == 'LONG' else -1)
                    tp = ep + to_price(ar * 1.0, pair) * (1 if break_direction == 'LONG' else -1)
                    post = day[(day.index > idx) & (day['est_h'] < 17)]
                    if not post.empty:
                        trade = manage_trade(post, ep, break_direction, sl, tp, pair)
                        if trade: trades.append(trade)
                    break
                if (idx - hold_end).total_seconds() > 3600: break
    return calc_results(trades, "Two_Plays", pair)


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 6: FAILURE REPAIR
# ═══════════════════════════════════════════════════════════════════════════════

def run_failure_repair(df, pair):
    df = prepare_data(df, pair)
    trades = []
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day, pair)
        if ar is None or ar > 45 or ar < 3: continue
        tier = classify_tier(ar)
        if tier == 'NO_GO': continue
        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
        first_signal_idx = None
        first_direction = None
        for idx, row in entry.iterrows():
            if row['body_pips'] < 4.6: continue
            if row['close'] > ah and row['high'] > ah: first_direction = 'LONG'; first_signal_idx = idx; break
            elif row['close'] < al and row['low'] < al: first_direction = 'SHORT'; first_signal_idx = idx; break
        if first_signal_idx is None: continue
        fail_window_end = first_signal_idx + pd.Timedelta(hours=2)
        post_first = day[(day.index > first_signal_idx) & (day.index <= fail_window_end)]
        failed = False
        fail_idx = None
        for idx, row in post_first.iterrows():
            if first_direction == 'LONG' and row['close'] < ah: failed = True; fail_idx = idx; break
            elif first_direction == 'SHORT' and row['close'] > al: failed = True; fail_idx = idx; break
        if not failed: continue
        weekday = day.index[0].dayofweek
        post_fail = day[(day.index > fail_idx) & (day['est_h'] < 12)]
        for idx, row in post_fail.iterrows():
            if row['body_pips'] < 4.6: continue
            second_direction = None
            if row['close'] > ah and row['high'] > ah: second_direction = 'LONG'
            elif row['close'] < al and row['low'] < al: second_direction = 'SHORT'
            if second_direction is None: continue
            hold_end = idx + pd.Timedelta(hours=2)
            hold_data = day[(day.index > idx) & (day.index <= hold_end)]
            if hold_data.empty: continue
            held = True
            for hidx, hrow in hold_data.iterrows():
                if second_direction == 'LONG' and hrow['close'] < al: held = False; break
                elif second_direction == 'SHORT' and hrow['close'] > ah: held = False; break
            if not held: continue
            ep = row['close']
            body_pips = row['body_pips']
            sl = ep - to_price(body_pips * 1.0, pair) * (1 if second_direction == 'LONG' else -1)
            tp = ep + to_price(ar * 0.50, pair) * (1 if second_direction == 'LONG' else -1)
            post = day[(day.index > idx) & (day['est_h'] < 17)]
            if not post.empty:
                trade = manage_trade(post, ep, second_direction, sl, tp, pair)
                if trade: trades.append(trade)
            break
    return calc_results(trades, "Failure_Repair", pair)


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 7: DUAL ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def run_dual_engine(df, pair):
    df = prepare_data(df, pair)
    trades = []
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day, pair)
        if ar is None or ar > 30 or ar < 3: continue
        tier = classify_tier(ar)
        if tier not in ('T1', 'T2'): continue
        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
        anchor_idx = None
        anchor_direction = None
        anchor_ep = None
        for idx, row in entry.iterrows():
            if row['body_pips'] < 4.6: continue
            if row['close'] > ah and row['high'] > ah: anchor_direction = 'LONG'; anchor_idx = idx; anchor_ep = row['close']; break
            elif row['close'] < al and row['low'] < al: anchor_direction = 'SHORT'; anchor_idx = idx; anchor_ep = row['close']; break
        if anchor_idx is None: continue
        anchor_body_pips = to_pips(abs(day.loc[anchor_idx, 'close'] - day.loc[anchor_idx, 'open']), pair)
        if anchor_direction == 'LONG':
            close_dist = to_pips(anchor_ep - ah, pair)
            if close_dist < 2.0 or ar > 20: continue
            anchor_sl = anchor_ep - to_price(anchor_body_pips * 1.5, pair)
            anchor_tp = anchor_ep + to_price(ar * 0.35, pair)
        else:
            close_dist = to_pips(al - anchor_ep, pair)
            if close_dist < 2.0 or ar > 20: continue
            anchor_sl = anchor_ep + to_price(anchor_body_pips * 1.5, pair)
            anchor_tp = anchor_ep - to_price(ar * 0.35, pair)
        post_anchor = day[(day.index > anchor_idx) & (day['est_h'] < 17)]
        if not post_anchor.empty:
            trade = manage_trade(post_anchor, anchor_ep, anchor_direction, anchor_sl, anchor_tp, pair)
            if trade: trades.append(trade)
        max_amps = 2 if tier == 'T1' else 1
        amps_added = 0
        if anchor_direction == 'LONG':
            impulse_high = day.loc[anchor_idx, 'high']
        else:
            impulse_low = day.loc[anchor_idx, 'low']
        post_anchor_entry = day[(day.index > anchor_idx) & (day['est_h'] < 11)]
        for idx, row in post_anchor_entry.iterrows():
            if amps_added >= max_amps: break
            amp_body = row['body_pips']
            if amp_body < 4.1: continue
            amp_direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
            if amp_direction != anchor_direction: continue
            if anchor_direction == 'LONG':
                impulse_size = to_pips(impulse_high - anchor_ep, pair)
                if impulse_size > 0: retrace = to_pips(impulse_high - row['low'], pair); retrace_pct = retrace / impulse_size
                else: continue
            else:
                impulse_size = to_pips(anchor_ep - impulse_low, pair)
                if impulse_size > 0: retrace = to_pips(row['high'] - impulse_low, pair); retrace_pct = retrace / impulse_size
                else: continue
            if 0.32 <= retrace_pct <= 0.50:
                ep = row['close']
                sl = ep - to_price(amp_body * 1.5, pair) * (1 if amp_direction == 'LONG' else -1)
                tp = ep + to_price(ar * 0.35, pair) * (1 if amp_direction == 'LONG' else -1)
                post = day[(day.index > idx) & (day['est_h'] < 17)]
                if not post.empty:
                    trade = manage_trade(post, ep, amp_direction, sl, tp, pair)
                    if trade: trades.append(trade)
                amps_added += 1
    return calc_results(trades, "Dual_Engine", pair)


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 8: P90P DISTRIBUTION
# ═══════════════════════════════════════════════════════════════════════════════

def run_p90p_distribution(df, pair):
    df = prepare_data(df, pair)
    trades = []
    tier_factors = {'T1': 1.80, 'T2': 1.50, 'T3': 1.20}
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day, pair)
        if ar is None or ar > 45 or ar < 3: continue
        tier = classify_tier(ar)
        if tier in ('NO_GO', 'NA'): continue
        base_factor = tier_factors.get(tier, 1.20)
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        p90_idx = None
        p90_row = None
        for idx, row in entry.iterrows():
            if row['body_pips'] >= p90_threshold(row['est_h']):
                p90_idx = idx; p90_row = row; break
        if p90_idx is None: continue
        direction = 'LONG' if p90_row['close'] > p90_row['open'] else 'SHORT'
        ep = p90_row['close']
        body_pips = p90_row['body_pips']
        if direction == 'LONG' and ep <= ah: continue
        if direction == 'SHORT' and ep >= al: continue
        regime = 'NEUTRAL'
        nine_am_data = day[(day['est_h'] >= 3) & (day['est_h'] <= 9)]
        if not nine_am_data.empty and ar > 0:
            daily_range_so_far = to_pips(nine_am_data['high'].max() - nine_am_data['low'].min(), pair)
            regime_ratio = daily_range_so_far / ar
            if regime_ratio >= 1.50: regime = 'CONFIRMED'
            elif regime_ratio < 1.45: regime = 'FAILED'
        if regime == 'FAILED': continue
        target_fraction = 0.70 if regime == 'CONFIRMED' else 0.55
        target_pips = ar * base_factor * target_fraction
        sl = ep - to_price(body_pips * 0.80, pair) * (1 if direction == 'LONG' else -1)
        tp = ep + to_price(target_pips, pair) * (1 if direction == 'LONG' else -1)
        post = day[(day.index > p90_idx) & (day['est_h'] < 17)]
        if not post.empty:
            trade = manage_trade(post, ep, direction, sl, tp, pair)
            if trade: trades.append(trade)
    return calc_results(trades, "P90P_Distribution", pair)


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 9: FRACTAL RESOLUTION
# ═══════════════════════════════════════════════════════════════════════════════

def run_fractal_resolution(df, pair):
    df = prepare_data(df, pair)
    trades = []
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day, pair)
        if ar is None or ar > 45 or ar < 3: continue
        tier = classify_tier(ar)
        if tier == 'T1': impulse_threshold = 10.0
        elif tier == 'T2': impulse_threshold = 14.0
        elif tier == 'T3': impulse_threshold = 18.0
        else: continue
        baseline_data = day[day['est_h'] == 3]
        if baseline_data.empty: continue
        baseline_price = baseline_data.iloc[0]['close']
        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
        impulse_high = baseline_price
        impulse_low = baseline_price
        impulse_direction = None
        impulse_size = 0
        looking_for_impulse = True
        trigger_candle_high = None
        trigger_candle_low = None
        bars_since_extreme = 0
        prev_row = None
        for idx, row in entry.iterrows():
            c = row['close']
            h = row['high']
            l = row['low']
            if looking_for_impulse:
                move = to_pips(c - baseline_price, pair)
                if abs(move) >= impulse_threshold:
                    impulse_direction = 'LONG' if move > 0 else 'SHORT'
                    impulse_size = abs(move)
                    impulse_high = h; impulse_low = l
                    looking_for_impulse = False
                    trigger_candle_high = h; trigger_candle_low = l
                    bars_since_extreme = 0
                else:
                    impulse_high = max(impulse_high, h)
                    impulse_low = min(impulse_low, l)
            else:
                if impulse_direction == 'LONG':
                    if c > impulse_high:
                        impulse_high = h; impulse_low = min(impulse_low, l)
                        impulse_size = to_pips(c - baseline_price, pair)
                        trigger_candle_high = h; trigger_candle_low = l
                        bars_since_extreme = 0
                    else: bars_since_extreme += 1
                    if impulse_size > 0 and bars_since_extreme <= 5:
                        retrace = to_pips(impulse_high - c, pair)
                        if retrace / impulse_size > 0.75:
                            shift_direction = 'SHORT'
                            sl = max(trigger_candle_high, prev_row['high']) if prev_row is not None else trigger_candle_high
                            tp = c - to_price(impulse_size * 1.0, pair)
                            post = day[(day.index > idx) & (day['est_h'] < 17)]
                            if not post.empty:
                                trade = manage_trade(post, c, shift_direction, sl, tp, pair)
                                if trade: trades.append(trade)
                            looking_for_impulse = True; impulse_direction = None; impulse_size = 0
                            impulse_high = baseline_price; impulse_low = baseline_price
                            prev_row = row; continue
                    if bars_since_extreme > 5:
                        looking_for_impulse = True; impulse_direction = None; impulse_size = 0
                        impulse_high = baseline_price; impulse_low = baseline_price
                elif impulse_direction == 'SHORT':
                    if c < impulse_low:
                        impulse_low = l; impulse_high = max(impulse_high, h)
                        impulse_size = to_pips(baseline_price - c, pair)
                        trigger_candle_high = h; trigger_candle_low = l
                        bars_since_extreme = 0
                    else: bars_since_extreme += 1
                    if impulse_size > 0 and bars_since_extreme <= 5:
                        retrace = to_pips(c - impulse_low, pair)
                        if retrace / impulse_size > 0.75:
                            shift_direction = 'LONG'
                            sl = min(trigger_candle_low, prev_row['low']) if prev_row is not None else trigger_candle_low
                            tp = c + to_price(impulse_size * 1.0, pair)
                            post = day[(day.index > idx) & (day['est_h'] < 17)]
                            if not post.empty:
                                trade = manage_trade(post, c, shift_direction, sl, tp, pair)
                                if trade: trades.append(trade)
                            looking_for_impulse = True; impulse_direction = None; impulse_size = 0
                            impulse_high = baseline_price; impulse_low = baseline_price
                            prev_row = row; continue
                    if bars_since_extreme > 5:
                        looking_for_impulse = True; impulse_direction = None; impulse_size = 0
                        impulse_high = baseline_price; impulse_low = baseline_price
            prev_row = row
    return calc_results(trades, "Fractal_Resolution", pair)


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 10: COMPOSITE ALPHA
# ═══════════════════════════════════════════════════════════════════════════════

def compute_composite_score(signals):
    ic_weights = {
        'p90_momentum': 0.08, 'ar_regime': 0.06,
        'constraint_deficit': 0.05, 'session_strength': 0.04, 'weekday_quality': 0.03,
    }
    weighted_sum = 0.0
    weight_total = 0.0
    for signal_name, strength in signals.items():
        ic = ic_weights.get(signal_name, 0.03)
        weighted_sum += ic * strength
        weight_total += ic
    if weight_total > 0: composite = weighted_sum / weight_total
    else: composite = 0.0
    n_signals = len(signals)
    ir_multiplier = np.sqrt(max(1, n_signals))
    adjusted_score = composite * min(ir_multiplier / 2.24, 1.5)
    return round(adjusted_score, 4)

def run_composite_alpha(df, pair):
    df = prepare_data(df, pair)
    trades = []
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day, pair)
        if ar is None or ar > 45 or ar < 3: continue
        tier = classify_tier(ar)
        if tier == 'NO_GO': continue
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        p90_direction = None; p90_body = 0; p90_idx = None; p90_est_h = 5
        for idx, row in entry.iterrows():
            if row['body_pips'] >= p90_threshold(row['est_h']):
                p90_direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
                p90_body = row['body_pips']; p90_idx = idx; p90_est_h = row['est_h']; break
        if p90_idx is None: continue
        ep = day.loc[p90_idx, 'close']
        if p90_direction == 'LONG' and ep <= ah: continue
        if p90_direction == 'SHORT' and ep >= al: continue
        day_signals = {}
        day_signals['ar_regime'] = {'T1': 1.0, 'T2': 0.6, 'T3': 0.3}.get(tier, 0.0)
        day_signals['constraint_deficit'] = max(0, 1.0 - (ar / 45.0))
        if p90_body > 0:
            thresh = p90_threshold(5)
            day_signals['p90_momentum'] = min(1.0, (p90_body - thresh) / thresh)
        if 3 <= p90_est_h <= 5: day_signals['session_strength'] = 1.0
        elif 6 <= p90_est_h <= 8: day_signals['session_strength'] = 0.8
        else: day_signals['session_strength'] = 0.5
        weekday = day.index[0].dayofweek
        if weekday in (1, 2, 3): day_signals['weekday_quality'] = 1.0
        elif weekday == 0: day_signals['weekday_quality'] = 0.7
        else: day_signals['weekday_quality'] = 0.5
        composite = compute_composite_score(day_signals)
        if composite < 0.20: continue
        direction = p90_direction
        if direction == 'LONG': close_dist = to_pips(ep - ah, pair)
        else: close_dist = to_pips(al - ep, pair)
        if close_dist < 2.0 or ar > 20: continue
        sl = ep - to_price(p90_body * 1.5, pair) * (1 if direction == 'LONG' else -1)
        base_tp = ar * (0.25 + 0.15 * min(composite, 1.0))
        tp = ep + to_price(base_tp, pair) * (1 if direction == 'LONG' else -1)
        post = day[(day.index > p90_idx) & (day['est_h'] < 17)]
        if not post.empty:
            trade = manage_trade(post, ep, direction, sl, tp, pair)
            if trade: trades.append(trade)
    return calc_results(trades, "Composite_Alpha", pair)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

STRATEGIES = [
    ("Deep_Mean_Reversion", run_deep_mean_reversion),
    ("Stall_Harvest_CFD", run_stall_harvest_cfd),
    ("Constraint_Anchor", run_constraint_anchor),
    ("Blind_Structural_Chain", run_blind_structural_chain),
    ("Two_Plays", run_two_plays),
    ("Failure_Repair", run_failure_repair),
    ("Dual_Engine", run_dual_engine),
    ("P90P_Distribution", run_p90p_distribution),
    ("Fractal_Resolution", run_fractal_resolution),
    ("Composite_Alpha", run_composite_alpha),
]


def apply_costs(result, cost_pips):
    """Apply per-trade cost to results."""
    if result.get('total_trades', 0) == 0:
        return result
    n = result['total_trades']
    total_cost = cost_pips * n
    result['total_pnl'] = round(result['total_pnl'] - total_cost, 2)
    result['expectancy'] = round(result['expectancy'] - cost_pips, 3)
    result['avg_win'] = round(result['avg_win'] - cost_pips, 2) if result['wins'] > 0 else result['avg_win']
    result['avg_loss'] = round(result['avg_loss'] - cost_pips, 2) if result['losses'] > 0 else result['avg_loss']
    # Recalculate profit factor
    wins = result.get('wins', 0)
    losses = result.get('losses', 0)
    if wins > 0 and losses > 0:
        adj_avg_win = result['avg_win']
        adj_avg_loss = abs(result['avg_loss'])
        gp = adj_avg_win * wins
        gl = adj_avg_loss * losses
        result['profit_factor'] = round(gp / gl, 2) if gl > 0 else 0
    result['cost_pips'] = cost_pips
    result['total_cost'] = round(total_cost, 2)
    return result


def main():
    print("=" * 70)
    print("🧪 MULTI-ASSET FOREX M5 BACKTEST — 10 CEREBUS Strategies × 8 Pairs")
    print(f"💰 Cost model: {COST_PER_TRADE_PIPS} pips/trade")
    print("=" * 70)

    all_results = {}  # {strategy: {asset: result}}

    for pair_name, filename in FOREX_FILES:
        print(f"\n{'#'*70}")
        print(f"### {pair_name} ###")
        print(f"{'#'*70}")

        df = load_csv_m5(filename, pair_name)
        if df is None:
            print(f"  [SKIP] Could not load {pair_name}")
            continue

        for strat_name, strat_fn in STRATEGIES:
            if strat_name not in all_results:
                all_results[strat_name] = {}

            print(f"\n  ▶ {strat_name}")
            t0 = time.time()
            try:
                r = strat_fn(df, pair_name)
                elapsed = time.time() - t0
                r = apply_costs(r, COST_PER_TRADE_PIPS)
                all_results[strat_name][pair_name] = r
                if r.get('total_trades', 0) > 0:
                    print(f"    [OK] {r['total_trades']} trades | WR: {r['win_rate']}% | "
                          f"P&L: {r['total_pnl']}p (cost: -{r.get('total_cost',0)}p) | "
                          f"PF: {r['profit_factor']} | MaxDD: {r['max_dd']}p | "
                          f"Exp: {r['expectancy']}p ({elapsed:.1f}s)")
                else:
                    print(f"    [WARN] No trades ({elapsed:.1f}s)")
            except Exception as e:
                elapsed = time.time() - t0
                print(f"    [FAIL] {type(e).__name__}: {e} ({elapsed:.1f}s)")
                import traceback
                traceback.print_exc()
                all_results[strat_name][pair_name] = {
                    "strategy": strat_name, "pair": pair_name,
                    "total_trades": 0, "error": str(e)
                }

        # Free memory
        del df

    # ── Save JSON ─────────────────────────────────────────────────────────
    output = {}
    for strat_name, assets in all_results.items():
        output[strat_name] = {}
        for pair_name, r in assets.items():
            output[strat_name][pair_name] = {
                "timeframe": "M5",
                "total_trades": r.get('total_trades', 0),
                "win_rate": r.get('win_rate', 0),
                "profit_factor": r.get('profit_factor', 0),
                "total_pnl": r.get('total_pnl', 0),
                "max_dd_pips": r.get('max_dd', 0),
                "avg_win": r.get('avg_win', 0),
                "avg_loss": r.get('avg_loss', 0),
                "expectancy": r.get('expectancy', 0),
            }

    json_path = RESULTS_DIR / "multi_asset_forex_m5.json"
    with open(json_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n💾 JSON saved to {json_path}")

    # ── Generate Report ───────────────────────────────────────────────────
    generate_report(all_results, output)

    return all_results


def generate_report(all_results, output):
    """Generate comprehensive markdown report."""
    report_lines = []
    report_lines.append("# 🧪 Multi-Asset Forex M5 Backtest Report")
    report_lines.append(f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**Cost Model:** {COST_PER_TRADE_PIPS} pips/trade (spread 0.2 + slippage 2.0 + commission 0.7)")
    report_lines.append(f"**Timeframe:** M5")
    report_lines.append(f"**Strategies:** 10 CEREBUS")
    report_lines.append(f"**Assets:** EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, NZDUSD, USDCAD, CHFJPY")
    report_lines.append("")

    # ── Per-Strategy Summary ──────────────────────────────────────────────
    report_lines.append("## 📊 Per-Strategy Summary\n")
    report_lines.append("| Strategy | Best Asset | Best WR% | Best P&L | Worst Asset | Worst WR% | Worst P&L | Avg WR% |")
    report_lines.append("|----------|------------|----------|----------|-------------|-----------|-----------|---------|")

    for strat_name, _ in STRATEGIES:
        assets = all_results.get(strat_name, {})
        valid = {k: v for k, v in assets.items() if v.get('total_trades', 0) > 0}
        if not valid:
            report_lines.append(f"| {strat_name} | N/A | - | - | N/A | - | - | - |")
            continue
        best = max(valid.items(), key=lambda x: x[1].get('win_rate', 0))
        worst = min(valid.items(), key=lambda x: x[1].get('win_rate', 0))
        avg_wr = sum(v.get('win_rate', 0) for v in valid.values()) / len(valid)
        report_lines.append(
            f"| {strat_name} | {best[0]} | {best[1].get('win_rate',0)}% | {best[1].get('total_pnl',0)}p | "
            f"{worst[0]} | {worst[1].get('win_rate',0)}% | {worst[1].get('total_pnl',0)}p | {avg_wr:.1f}% |"
        )

    # ── Per-Asset: Best Strategies ────────────────────────────────────────
    report_lines.append("\n## 📈 Per-Asset: Top Strategies\n")
    all_assets = [p[0] for p in FOREX_FILES]
    for asset in all_assets:
        report_lines.append(f"### {asset}\n")
        asset_strats = []
        for strat_name, _ in STRATEGIES:
            r = all_results.get(strat_name, {}).get(asset, {})
            if r.get('total_trades', 0) > 0:
                asset_strats.append((strat_name, r))
        asset_strats.sort(key=lambda x: x[1].get('total_pnl', 0), reverse=True)
        report_lines.append("| Rank | Strategy | Trades | WR% | P&L(p) | PF | MaxDD | Exp |")
        report_lines.append("|------|----------|--------|-----|--------|----|-------|-----|")
        for i, (sn, r) in enumerate(asset_strats, 1):
            report_lines.append(
                f"| {i} | {sn} | {r['total_trades']} | {r.get('win_rate',0)}% | "
                f"{r.get('total_pnl',0)}p | {r.get('profit_factor',0)} | "
                f"{r.get('max_dd',0)}p | {r.get('expectancy',0)}p |"
            )
        report_lines.append("")

    # ── Heatmap: WR% Matrix ──────────────────────────────────────────────
    report_lines.append("## 🔥 Win Rate Heatmap (Strategy × Asset)\n")
    header = "| Strategy |" + "".join(f" {a} |" for a in all_assets) + " Avg |"
    sep = "|----------|" + "--------|" * (len(all_assets) + 1)
    report_lines.append(header)
    report_lines.append(sep)
    for strat_name, _ in STRATEGIES:
        row = f"| {strat_name} |"
        wrs = []
        for asset in all_assets:
            r = all_results.get(strat_name, {}).get(asset, {})
            wr = r.get('win_rate', 0)
            n = r.get('total_trades', 0)
            if n > 0:
                wrs.append(wr)
                row += f" {wr:.1f}% |"
            else:
                row += " N/A |"
        avg_wr = sum(wrs) / len(wrs) if wrs else 0
        row += f" {avg_wr:.1f}% |"
        report_lines.append(row)

    # ── Heatmap: P&L Matrix ──────────────────────────────────────────────
    report_lines.append("\n## 💰 P&L Heatmap (Strategy × Asset)\n")
    header = "| Strategy |" + "".join(f" {a} |" for a in all_assets) + " Total |"
    sep = "|----------|" + "--------|" * (len(all_assets) + 1)
    report_lines.append(header)
    report_lines.append(sep)
    for strat_name, _ in STRATEGIES:
        row = f"| {strat_name} |"
        pnls = []
        for asset in all_assets:
            r = all_results.get(strat_name, {}).get(asset, {})
            pnl = r.get('total_pnl', 0)
            n = r.get('total_trades', 0)
            if n > 0:
                pnls.append(pnl)
                row += f" {pnl:.1f} |"
            else:
                row += " N/A |"
        total_pnl = sum(pnls) if pnls else 0
        row += f" {total_pnl:.1f} |"
        report_lines.append(row)

    # ── Comparison to EUR/USD-only ────────────────────────────────────────
    report_lines.append("\n## 📊 EUR/USD Comparison (Multi-Asset vs Single-Asset)\n")
    report_lines.append("| Strategy | EUR/USD WR% | Avg WR All | Diff | EUR/USD P&L | Total P&L |")
    report_lines.append("|----------|-------------|-----------|------|-------------|-----------|")
    for strat_name, _ in STRATEGIES:
        eur_r = all_results.get(strat_name, {}).get('EURUSD', {})
        valid = {k: v for k, v in all_results.get(strat_name, {}).items() if v.get('total_trades', 0) > 0}
        if not valid or 'EURUSD' not in valid:
            report_lines.append(f"| {strat_name} | N/A | N/A | N/A | N/A | N/A |")
            continue
        avg_wr = sum(v.get('win_rate', 0) for v in valid.values()) / len(valid)
        total_pnl = sum(v.get('total_pnl', 0) for v in valid.values())
        report_lines.append(
            f"| {strat_name} | {eur_r.get('win_rate',0)}% | {avg_wr:.1f}% | "
            f"{avg_wr - eur_r.get('win_rate',0):+.1f}% | "
            f"{eur_r.get('total_pnl',0)}p | {total_pnl:.1f}p |"
        )

    # ── Key Findings ──────────────────────────────────────────────────────
    report_lines.append("\n## 🎯 Key Findings\n")

    # Best overall strategy by total P&L
    strat_totals = []
    for strat_name, _ in STRATEGIES:
        valid = {k: v for k, v in all_results.get(strat_name, {}).items() if v.get('total_trades', 0) > 0}
        total = sum(v.get('total_pnl', 0) for v in valid.values())
        avg_wr = sum(v.get('win_rate', 0) for v in valid.values()) / len(valid) if valid else 0
        strat_totals.append((strat_name, total, avg_wr, len(valid)))
    strat_totals.sort(key=lambda x: x[1], reverse=True)

    report_lines.append("### Best Strategies by Total P&L (all assets combined)\n")
    for i, (sn, pnl, wr, n_assets) in enumerate(strat_totals, 1):
        report_lines.append(f"{i}. **{sn}**: {pnl:.1f}p total | {wr:.1f}% avg WR | traded on {n_assets} assets")

    # Best asset by total P&L
    asset_totals = {asset: 0 for asset in all_assets}
    for strat_name, _ in STRATEGIES:
        for asset in all_assets:
            r = all_results.get(strat_name, {}).get(asset, {})
            if r.get('total_trades', 0) > 0:
                asset_totals[asset] = asset_totals.get(asset, 0) + r.get('total_pnl', 0)
    sorted_assets = sorted(asset_totals.items(), key=lambda x: x[1], reverse=True)

    report_lines.append("\n### Best Assets by Total P&L (all strategies combined)\n")
    for i, (asset, pnl) in enumerate(sorted_assets, 1):
        report_lines.append(f"{i}. **{asset}**: {pnl:.1f}p total")

    report_lines.append("\n---")
    report_lines.append(f"\n*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    report_path = REPORTS_DIR / "MULTI_ASSET_FOREX_M5_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    print(f"📝 Report saved to {report_path}")


if __name__ == "__main__":
    main()
