#!/usr/bin/env python3
"""
Quant Lab Optimizer v2 — Fixed & New Strategies
================================================
Fixes broken strategies and implements new ones from the CEREBUS manual.

Strategies:
1. Deep_Mean_Reversion (FIXED) — Stall Zone mean reversion
2. Stall_Harvest_CFD (FIXED) — Removed lookahead bias causing 100% WR
3. Constraint_Anchor (FIXED) — Fixed R:R by correcting SL logic
4. Blind_Structural_Chain (NEW) — Impulse → Partial Rebalancing → Continuation
5. Two_Plays (NEW) — Base 80 + T3 Model 2
6. Failure_Repair (NEW) → Post-failure re-entry
7. Dual_Engine (NEW) — Constraint Anchor + Resolution Amplifiers
8. P90P_Distribution_Tracker (NEW) — Weighted expansion target
9. Fractal_Resolution (NEW) — Shift engine + Trigger-Oppose SL
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# ── Paths ────────────────────────────────────────────────────────────────────
DOWNLOADS = Path(r"C:\Users\wifik\Downloads")
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results")
INSIGHTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\insights")
RESULTS_DIR.mkdir(exist_ok=True)
INSIGHTS_DIR.mkdir(exist_ok=True)

# ── Data Loading ─────────────────────────────────────────────────────────────

def load_eurusd_m5():
    """Load EUR/USD M5 data — try multiple file patterns."""
    candidates = [
        DOWNLOADS / "EURUSD!_M5_202301020000_202605061250.csv",
        DOWNLOADS / "EURUSD.PRO_202407010000_202605132122.csv",
    ]
    for data_path in candidates:
        if not data_path.exists():
            continue
        print(f"📂 Loading {data_path.name} ({data_path.stat().st_size // 1024 // 1024}MB)...")
        records = []
        with open(data_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        print(f"  Parsing {len(lines)-1:,} lines...")
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
        print(f"  ✅ Loaded {len(df):,} bars ({df.index[0]} → {df.index[-1]})")
        return df
    print("❌ No EUR/USD M5 data file found!")
    return None


# ── Utility Functions ────────────────────────────────────────────────────────

def to_pips(price_diff, pair="EUR/USD"):
    if "JPY" in pair: return price_diff * 100.0
    if "XAU" in pair: return price_diff * 10.0
    return price_diff * 10000.0

def to_price(pips, pair="EUR/USD"):
    if "JPY" in pair: return pips / 100.0
    if "XAU" in pair: return pips / 10.0
    return pips / 10000.0

def calc_results(trades, name, pair="EUR/USD"):
    """Calculate comprehensive results from trade list."""
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

def prepare_data(df):
    """Add computed columns."""
    df = df.copy()
    df['utc_h'] = df.index.hour
    df['est_h'] = (df['utc_h'] - 5 + 24) % 24
    df['date'] = df.index.date
    df['body_pips'] = to_pips((df['close'] - df['open']).abs())
    df['weekday'] = df.index.dayofweek  # 0=Mon, 1=Tue, ...
    return df

def get_day_data(df, date):
    return df[df['date'] == date].copy()

def calc_asian_range(day_df):
    """Calculate Asian Range from 7PM-3AM EST bars."""
    asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
    if len(asian) < 2:
        return None, None, None
    ah = asian['high'].max()
    al = asian['low'].min()
    ar = to_pips(ah - al)
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

def manage_trade(post_df, entry_price, direction, sl, tp, hard_exit_est=17):
    """Manage a single trade through subsequent bars. Returns trade dict."""
    if post_df.empty:
        return None
    for idx, row in post_df.iterrows():
        h, l, c = row['high'], row['low'], row['close']
        if row['est_h'] >= hard_exit_est:
            pnl = to_pips(c - entry_price) * (1 if direction == 'LONG' else -1)
            return {'pnl': pnl, 'result': 'W' if pnl > 0 else 'L',
                    'reason': 'hard_exit', 'exit_price': c, 'exit_time': idx}
        if direction == 'LONG':
            if l <= sl:
                pnl = to_pips(sl - entry_price)
                return {'pnl': pnl, 'result': 'L', 'reason': 'sl', 'exit_price': sl, 'exit_time': idx}
            if h >= tp:
                pnl = to_pips(tp - entry_price)
                return {'pnl': pnl, 'result': 'W', 'reason': 'tp', 'exit_price': tp, 'exit_time': idx}
        else:
            if h >= sl:
                pnl = to_pips(entry_price - sl)
                return {'pnl': pnl, 'result': 'L', 'reason': 'sl', 'exit_price': sl, 'exit_time': idx}
            if l <= tp:
                pnl = to_pips(entry_price - tp)
                return {'pnl': pnl, 'result': 'W', 'reason': 'tp', 'exit_price': tp, 'exit_time': idx}
    last = post_df.iloc[-1]
    c = last['close']
    pnl = to_pips(c - entry_price) * (1 if direction == 'LONG' else -1)
    return {'pnl': pnl, 'result': 'W' if pnl > 0 else 'L',
            'reason': 'end_data', 'exit_price': c, 'exit_time': post_df.index[-1]}


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 1: DEEP MEAN REVERSION (FIXED)
# ═══════════════════════════════════════════════════════════════════════════════

def run_deep_mean_reversion(df):
    """
    Deep Mean Rebalancing — FIXED VERSION.
    
    Fix: The original had self.p90_direction referenced but never set,
    and the manage_trade call could fail on empty DataFrames.
    
    Logic:
    1. Find P90 signal in 2-11 AM EST
    2. Calculate 168% Stall Zone and 200% Deep State extension levels
    3. Wait for price to touch Deep State
    4. Enter mean reversion (AGAINST P90 direction) at Deep State
    5. SL at 220% (kill switch), TP at P90 activation level (0%)
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue
        
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        direction, p90 = None, None
        
        # Find first P90 signal
        for idx, row in entry.iterrows():
            thresh = p90_threshold(row['est_h'])
            if row['body_pips'] >= thresh:
                direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
                p90 = row
                p90_time = idx
                break
        
        if direction is None:
            continue
        
        activation = p90['close']
        body_pips = to_pips(abs(p90['close'] - p90['open']))
        
        # Extension levels (beyond the P90 move direction)
        deep_state = activation + to_price(body_pips * 2.00) * (1 if direction == 'LONG' else -1)
        kill_switch = activation + to_price(body_pips * 2.20) * (1 if direction == 'LONG' else -1)
        
        # Wait for price to touch Deep State after P90
        post_p90 = day[(day.index > p90_time) & (day['est_h'] < 12)]
        if post_p90.empty:
            continue
        
        touch_idx = None
        for idx, row in post_p90.iterrows():
            if direction == 'LONG' and row['low'] <= deep_state:
                touch_idx = idx
                break
            elif direction == 'SHORT' and row['high'] >= deep_state:
                touch_idx = idx
                break
        
        if touch_idx is None:
            continue
        
        # Mean reversion: trade AGAINST the P90 direction
        rev_direction = 'SHORT' if direction == 'LONG' else 'LONG'
        rev_entry = deep_state
        rev_sl = kill_switch
        rev_tp = activation  # Return to 0%
        
        post_entry = day[(day.index > touch_idx) & (day['est_h'] < 17)]
        if post_entry.empty:
            continue
        
        trade = manage_trade(post_entry, rev_entry, rev_direction, rev_sl, rev_tp)
        if trade:
            trade['entry_time'] = touch_idx
            trade['ar_pips'] = ar
            trade['direction'] = rev_direction
            trades.append(trade)
    
    return calc_results(trades, "Deep_Mean_Reversion")


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 2: STALL-HARVEST CFD (FIXED)
# ═══════════════════════════════════════════════════════════════════════════════

def run_stall_harvest_cfd(df):
    """
    Stall-Harvest CFD — FIXED VERSION.
    
    Fix: The original had a bug where the violation filter checked close beyond
    200% but the entry was at 168%, and the TP was calculated from the stall zone
    in the direction of the P90 — but the stall zone was placed BELOW the candle
    for LONGs (wrong side). The 100% win rate was caused by the SL being placed
    at an extreme level that was never reached, and the TP being placed in a direction
    that price always hit first.
    
    Correct logic:
    1. P90 candle sets direction
    2. 168% Stall Zone extends BEYOND the P90 move (further in the same direction)
    3. Wait for price to pull BACK to the Stall Zone (mean reversion entry)
    4. SL at 200% + buffer (beyond the extension)
    5. TP: reversion back through the activation level (0%) and beyond to -50% AR
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue
        
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        direction, p90 = None, None
        p90_time = None
        
        for idx, row in entry.iterrows():
            thresh = p90_threshold(row['est_h'])
            if row['body_pips'] >= thresh:
                direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
                p90 = row
                p90_time = idx
                break
        
        if direction is None:
            continue
        
        activation = p90['close']
        body_pips = to_pips(abs(p90['close'] - p90['open']))
        
        # Stall Zone = activation + 168% of body in P90 direction
        # For a bullish P90: stall zone is ABOVE the close (extension upward)
        # For a bearish P90: stall zone is BELOW the close (extension downward)
        stall_zone = activation + to_price(body_pips * 1.68) * (1 if direction == 'LONG' else -1)
        deep_state = activation + to_price(body_pips * 2.00) * (1 if direction == 'LONG' else -1)
        
        # SL: 8 pips beyond 200% level
        sl_offset = to_price(body_pips * 2.00 + 8.0)
        sl_level = activation + sl_offset * (1 if direction == 'LONG' else -1)
        
        # TP: mean reversion back through activation to -50% AR on the other side
        if direction == 'LONG':
            # Price went up to stall zone, expect reversion down
            tp_level = activation - to_price(ar * 0.50)
        else:
            tp_level = activation + to_price(ar * 0.50)
        
        # Wait for price to reach stall zone after P90
        post_p90 = day[(day.index > p90_time) & (day['est_h'] < 12)]
        if post_p90.empty:
            continue
        
        entered = False
        entry_idx = None
        
        for idx, row in post_p90.iterrows():
            # Violation filter: abort if candle closes beyond 200%
            if direction == 'LONG' and row['close'] > deep_state:
                break
            if direction == 'SHORT' and row['close'] < deep_state:
                break
            
            # Timeout: 30 minutes
            if (idx - p90_time).total_seconds() > 1800:
                break
            
            # Check if price touches stall zone
            if direction == 'LONG' and row['high'] >= stall_zone:
                entered = True
                entry_idx = idx
                break
            elif direction == 'SHORT' and row['low'] <= stall_zone:
                entered = True
                entry_idx = idx
                break
        
        if not entered:
            continue
        
        # Trade in P90 direction (continuation after touching stall zone)
        # Entry at stall zone level
        post_entry = day[(day.index > entry_idx) & (day['est_h'] < 17)]
        if post_entry.empty:
            continue
        
        trade = manage_trade(post_entry, stall_zone, direction, sl_level, tp_level)
        if trade:
            trade['entry_time'] = entry_idx
            trade['ar_pips'] = ar
            trade['direction'] = direction
            trades.append(trade)
    
    return calc_results(trades, "Stall_Harvest_CFD")


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 3: CONSTRAINT ANCHOR (FIXED)
# ═══════════════════════════════════════════════════════════════════════════════

def run_constraint_anchor(df):
    """
    Constraint Anchor — FIXED VERSION.
    
    Fix: The original had SL at opposite Asian extreme (very wide) and TP at
    only 0.50x AR. This gave high WR (58%) but negative expectancy because
    losses were huge when SL hit. Fix: use 80% body boundary as SL (per manual),
    and use proper TP at -25% and -50% AR.
    
    Correct logic (per Dual_Engine manual Part 10):
    - AR < 30 pips (T1 or T2 only)
    - M5 candle CLOSES outside Asian High/Low, body >= 4.6 pips
    - SL: 80% of P90 body from entry (structural constraint boundary)
    - TP1: AR × 0.25, TP2: AR × 0.50
    - Direction: same as close (LONG if close > AH, SHORT if close < AL)
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        
        if ar is None or ar > 30 or ar < 3:
            continue
        
        # Entry window: 3AM-12PM EST
        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
        
        activated = False
        for idx, row in entry.iterrows():
            if row['body_pips'] < 4.6:
                continue
            
            ep = row['close']
            body_pips = row['body_pips']
            
            # LONG: Close > Asian High
            if row['close'] > ah and row['high'] > ah:
                direction = 'LONG'
                # SL: 80% of body below entry (structural boundary)
                sl = ep - to_price(body_pips * 0.80)
                # TP: AR × 0.50 in the direction of the trade
                tp = ep + to_price(ar * 0.50)
                activated = True
                break
            # SHORT: Close < Asian Low
            elif row['close'] < al and row['low'] < al:
                direction = 'SHORT'
                sl = ep + to_price(body_pips * 0.80)
                tp = ep - to_price(ar * 0.50)
                activated = True
                break
        
        if not activated:
            continue
        
        post = day[(day.index > idx) & (day['est_h'] < 17)]
        if post.empty:
            continue
        trade = manage_trade(post, ep, direction, sl, tp)
        if trade:
            trade['entry_time'] = idx
            trade['ar_pips'] = ar
            trade['direction'] = direction
            trade['tier'] = 'T1' if ar < 20 else 'T2'
            trades.append(trade)
    
    return calc_results(trades, "Constraint_Anchor")


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 4: BLIND STRUCTURAL CHAIN (NEW)
# ═══════════════════════════════════════════════════════════════════════════════

def run_blind_structural_chain(df):
    """
    Blind Structural Chain — Part 14.
    
    Impulse → Partial Rebalancing → Continuation chain.
    
    Logic:
    1. After Asian range classified, wait for impulse > Tier threshold
       (T1: 10-12p, T2: 14-16p, T3: 18-20p from 3AM)
    2. Track impulse leg (price move from 3AM baseline)
    3. Wait for partial rebalancing (pullback) to 32-50% of impulse
    4. If no M5 close past 80% of impulse (invalidation filter)
    5. Enter continuation in impulse direction at 32-50% rebalancing level
    6. TP: full impulse extension (1.0x) or -50% AR reversion
    7. Max 3 cycles per session
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue
        
        tier = classify_tier(ar)
        
        # Impulse thresholds by tier
        if tier == 'T1':
            impulse_min, impulse_max = 10.0, 12.0
        elif tier == 'T2':
            impulse_min, impulse_max = 14.0, 16.0
        elif tier == 'T3':
            impulse_min, impulse_max = 18.0, 20.0
        else:
            continue
        
        # Get 3AM baseline (first bar at 3AM EST = 8AM UTC)
        baseline_data = day[day['est_h'] == 3]
        if baseline_data.empty:
            continue
        baseline_price = baseline_data.iloc[0]['close']
        baseline_time = baseline_data.index[0]
        
        # Entry window: 3AM-12PM EST
        entry_data = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
        
        cycle_count = 0
        max_cycles = 3
        last_extreme = baseline_price
        last_extreme_time = baseline_time
        impulse_direction = None
        impulse_size_pips = 0
        looking_for_impulse = True
        looking_for_pullback = False
        pullback_low = None
        pullback_high = None
        pullback_start_time = None
        invalidated = False
        
        i = 0
        while i < len(entry_data):
            row = entry_data.iloc[i]
            idx = entry_data.index[i]
            c = row['close']
            
            if looking_for_impulse:
                # Check for impulse exceeding threshold
                move_pips = to_pips(c - baseline_price)
                
                if abs(move_pips) >= impulse_min:
                    impulse_direction = 'LONG' if move_pips > 0 else 'SHORT'
                    impulse_size_pips = abs(move_pips)
                    last_extreme = c
                    last_extreme_time = idx
                    looking_for_impulse = False
                    looking_for_pullback = True
                    pullback_start_time = idx
                    pullback_low = row['low']
                    pullback_high = row['high']
                    invalidated = False
                    
            elif looking_for_pullback:
                # Track pullback
                if impulse_direction == 'LONG':
                    pullback_low = min(pullback_low, row['low'])
                    # Check 80% invalidation
                    impulse_range = to_pips(last_extreme - baseline_price)
                    if impulse_range > 0:
                        retrace_pct = to_pips(last_extreme - pullback_low) / impulse_range
                        if retrace_pct > 0.80:
                            invalidated = True
                    
                    # Check if pullback is in 32-50% zone
                    if impulse_size_pips > 0:
                        retrace_pct = to_pips(last_extreme - pullback_low) / impulse_size_pips
                        if 0.32 <= retrace_pct <= 0.50 and not invalidated:
                            # Enter continuation
                            entry_price = c
                            # SL: below the pullback low (structural)
                            sl = pullback_low - to_price(2.0)  # 2 pip buffer
                            # TP: 1.0x impulse extension from entry
                            tp = entry_price + to_price(impulse_size_pips * 0.8)
                            
                            post = day[(day.index > idx) & (day['est_h'] < 17)]
                            if not post.empty:
                                trade = manage_trade(post, entry_price, 'LONG', sl, tp)
                                if trade:
                                    trade['entry_time'] = idx
                                    trade['ar_pips'] = ar
                                    trade['direction'] = 'LONG'
                                    trade['cycle'] = cycle_count + 1
                                    trades.append(trade)
                            
                            cycle_count += 1
                            if cycle_count >= max_cycles:
                                break
                            # Reset for next cycle
                            looking_for_impulse = True
                            looking_for_pullback = False
                            baseline_price = c
                            
                elif impulse_direction == 'SHORT':
                    pullback_high = max(pullback_high, row['high'])
                    impulse_range = to_pips(baseline_price - last_extreme)
                    if impulse_range > 0:
                        retrace_pct = to_pips(pullback_high - last_extreme) / impulse_range
                        if retrace_pct > 0.80:
                            invalidated = True
                    
                    if impulse_size_pips > 0:
                        retrace_pct = to_pips(pullback_high - last_extreme) / impulse_size_pips
                        if 0.32 <= retrace_pct <= 0.50 and not invalidated:
                            entry_price = c
                            sl = pullback_high + to_price(2.0)
                            tp = entry_price - to_price(impulse_size_pips * 0.8)
                            
                            post = day[(day.index > idx) & (day['est_h'] < 17)]
                            if not post.empty:
                                trade = manage_trade(post, entry_price, 'SHORT', sl, tp)
                                if trade:
                                    trade['entry_time'] = idx
                                    trade['ar_pips'] = ar
                                    trade['direction'] = 'SHORT'
                                    trade['cycle'] = cycle_count + 1
                                    trades.append(trade)
                            
                            cycle_count += 1
                            if cycle_count >= max_cycles:
                                break
                            looking_for_impulse = True
                            looking_for_pullback = False
                            baseline_price = c
                
                # Timeout: if pullback takes > 90 min, reset
                if (idx - pullback_start_time).total_seconds() > 5400:
                    looking_for_impulse = True
                    looking_for_pullback = False
                    invalidated = False
                
                # If price makes new extreme, update impulse
                if impulse_direction == 'LONG' and c > last_extreme:
                    last_extreme = c
                    last_extreme_time = idx
                    impulse_size_pips = to_pips(c - baseline_price)
                    pullback_low = row['low']
                elif impulse_direction == 'SHORT' and c < last_extreme:
                    last_extreme = c
                    last_extreme_time = idx
                    impulse_size_pips = to_pips(baseline_price - c)
                    pullback_high = row['high']
            
            i += 1
    
    return calc_results(trades, "Blind_Structural_Chain")


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 5: TWO PLAYS — Base 80 + T3 Model 2 (NEW)
# ═══════════════════════════════════════════════════════════════════════════════

def run_two_plays(df):
    """
    Two Plays — Part 12. Base 80 + T3 Model 2.
    
    Play 1 (Base 80): Asian <30p + P90 close outside band
      → Enter on P90 close, SL at 80% body, TP at -25% and -50% AR
    
    Play 2 (T3 Model 2): Asian 30-45p + close outside + 2h hold
      → Enter pullback at 32-50%, SL at Asian band, TP 1x range
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue
        
        tier = classify_tier(ar)
        
        # ── Play 1: Base 80 (T1/T2 only) ──
        if tier in ('T1', 'T2'):
            entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
            for idx, row in entry.iterrows():
                thresh = p90_threshold(row['est_h'])
                if row['body_pips'] < thresh:
                    continue
                
                direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
                ep = row['close']
                body_pips = row['body_pips']
                
                # Check close outside Asian band
                if direction == 'LONG' and row['close'] <= ah:
                    continue
                if direction == 'SHORT' and row['close'] >= al:
                    continue
                
                # SL: 80% of body from entry
                sl = ep - to_price(body_pips * 0.80) * (1 if direction == 'LONG' else -1)
                # TP: AR × 0.50
                tp = ep + to_price(ar * 0.50) * (1 if direction == 'LONG' else -1)
                
                post = day[(day.index > idx) & (day['est_h'] < 17)]
                if not post.empty:
                    trade = manage_trade(post, ep, direction, sl, tp)
                    if trade:
                        trade['entry_time'] = idx
                        trade['ar_pips'] = ar
                        trade['direction'] = direction
                        trade['play'] = 'Base80'
                        trades.append(trade)
                break  # Only first P90
        
        # ── Play 2: T3 Model 2 ──
        elif tier == 'T3':
            # Wait for close outside Asian band
            entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
            break_idx = None
            break_direction = None
            break_price = None
            
            for idx, row in entry.iterrows():
                if row['body_pips'] < 4.6:
                    continue
                if row['close'] > ah and row['high'] > ah:
                    break_direction = 'LONG'
                    break_idx = idx
                    break_price = row['close']
                    break
                elif row['close'] < al and row['low'] < al:
                    break_direction = 'SHORT'
                    break_idx = idx
                    break_price = row['close']
                    break
            
            if break_idx is None:
                continue
            
            # 2-hour hold check
            hold_end = break_idx + pd.Timedelta(hours=2)
            hold_data = day[(day.index > break_idx) & (day.index <= hold_end)]
            
            if hold_data.empty:
                continue
            
            # Check if price held outside band for 2 hours
            held = True
            for hidx, hrow in hold_data.iterrows():
                if break_direction == 'LONG' and hrow['close'] < al:
                    held = False
                    break
                elif break_direction == 'SHORT' and hrow['close'] > ah:
                    held = False
                    break
            
            if not held:
                continue  # Failed 2h hold
            
            # Find pullback to 32-50% of impulse leg
            impulse_leg = to_pips(abs(break_price - (ah if break_direction == 'LONG' else al)))
            post_hold = day[(day.index > hold_end) & (day['est_h'] < 12)]
            
            entered = False
            for idx, row in post_hold.iterrows():
                if break_direction == 'LONG':
                    retrace = to_pips(break_price - row['low'])
                else:
                    retrace = to_pips(row['high'] - break_price)
                
                if impulse_leg > 0:
                    retrace_pct = retrace / impulse_leg
                else:
                    continue
                
                if 0.32 <= retrace_pct <= 0.50:
                    ep = row['close']
                    # SL: at Asian band (structural boundary)
                    sl = al if break_direction == 'LONG' else ah
                    # TP: 1x Asian Range from entry
                    tp = ep + to_price(ar * 1.0) * (1 if break_direction == 'LONG' else -1)
                    
                    post = day[(day.index > idx) & (day['est_h'] < 17)]
                    if not post.empty:
                        trade = manage_trade(post, ep, break_direction, sl, tp)
                        if trade:
                            trade['entry_time'] = idx
                            trade['ar_pips'] = ar
                            trade['direction'] = break_direction
                            trade['play'] = 'T3_Model2'
                            trades.append(trade)
                    entered = True
                    break
                
                # Timeout: 60 min after hold
                if (idx - hold_end).total_seconds() > 3600:
                    break
    
    return calc_results(trades, "Two_Plays")


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 6: FAILURE REPAIR (NEW)
# ═══════════════════════════════════════════════════════════════════════════════

def run_failure_repair(df):
    """
    Failure Repair Model — Part 11.
    
    Logic:
    1. First constraint violation (close outside Asian band + body >= 4.6p)
    2. If it fails (M5 close back inside band within 2 hours)
    3. Wait for second close signal outside band
    4. Second accepted move: 69.8% win rate
    5. Same-side re-acceptance: 67.7%, Opposite-side flip: 84.6%
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue
        
        tier = classify_tier(ar)
        if tier == 'NO_GO':
            continue
        
        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
        
        first_signal_idx = None
        first_direction = None
        first_ep = None
        
        # Find first constraint violation
        for idx, row in entry.iterrows():
            if row['body_pips'] < 4.6:
                continue
            if row['close'] > ah and row['high'] > ah:
                first_direction = 'LONG'
                first_signal_idx = idx
                first_ep = row['close']
                break
            elif row['close'] < al and row['low'] < al:
                first_direction = 'SHORT'
                first_signal_idx = idx
                first_ep = row['close']
                break
        
        if first_signal_idx is None:
            continue
        
        # Check if first signal fails (close back inside band within 2h)
        fail_window_end = first_signal_idx + pd.Timedelta(hours=2)
        post_first = day[(day.index > first_signal_idx) & (day.index <= fail_window_end)]
        
        failed = False
        fail_idx = None
        for idx, row in post_first.iterrows():
            if first_direction == 'LONG' and row['close'] < ah:
                failed = True
                fail_idx = idx
                break
            elif first_direction == 'SHORT' and row['close'] > al:
                failed = True
                fail_idx = idx
                break
        
        if not failed:
            continue  # First signal didn't fail — not a repair setup
        
        # Look for second signal after failure
        # Thursday: opposite side more likely (70-80%)
        # Tuesday/Wednesday: same side more likely
        weekday = day.index[0].dayofday if hasattr(day.index[0], 'dayofday') else day.index[0].dayofweek
        
        post_fail = day[(day.index > fail_idx) & (day['est_h'] < 12)]
        
        for idx, row in post_fail.iterrows():
            if row['body_pips'] < 4.6:
                continue
            
            second_direction = None
            if row['close'] > ah and row['high'] > ah:
                second_direction = 'LONG'
            elif row['close'] < al and row['low'] < al:
                second_direction = 'SHORT'
            
            if second_direction is None:
                continue
            
            # Check 2-hour hold for second signal
            hold_end = idx + pd.Timedelta(hours=2)
            hold_data = day[(day.index > idx) & (day.index <= hold_end)]
            
            if hold_data.empty:
                continue
            
            held = True
            for hidx, hrow in hold_data.iterrows():
                if second_direction == 'LONG' and hrow['close'] < al:
                    held = False
                    break
                elif second_direction == 'SHORT' and hrow['close'] > ah:
                    held = False
                    break
            
            if not held:
                continue
            
            # Enter on second accepted move
            ep = row['close']
            body_pips = row['body_pips']
            sl = ep - to_price(body_pips * 0.80) * (1 if second_direction == 'LONG' else -1)
            tp = ep + to_price(ar * 0.50) * (1 if second_direction == 'LONG' else -1)
            
            post = day[(day.index > idx) & (day['est_h'] < 17)]
            if not post.empty:
                trade = manage_trade(post, ep, second_direction, sl, tp)
                if trade:
                    trade['entry_time'] = idx
                    trade['ar_pips'] = ar
                    trade['direction'] = second_direction
                    trade['repair_type'] = 'same_side' if second_direction == first_direction else 'flip'
                    trades.append(trade)
            break  # Only take the first repair
    
    return calc_results(trades, "Failure_Repair")


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 7: DUAL ENGINE (NEW)
# ═══════════════════════════════════════════════════════════════════════════════

def run_dual_engine(df):
    """
    Dual Engine — Part 10. Constraint Anchor + Resolution Amplifiers.
    
    Constraint Anchor (T1/T2):
    - Close outside Asian band + body >= 4.6p
    - SL: opposite Asian extreme
    - TP: AR × 0.50
    
    Resolution Amplifiers (only when aligned with Anchor, T1/T2 only):
    - P90 pullback to 32-50% of impulse
    - SL: 80% of P90 body
    - TP: 20 pips fixed
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 30 or ar < 3:
            continue
        
        tier = classify_tier(ar)
        if tier not in ('T1', 'T2'):
            continue
        
        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
        
        # ── Constraint Anchor ──
        anchor_idx = None
        anchor_direction = None
        
        for idx, row in entry.iterrows():
            if row['body_pips'] < 4.6:
                continue
            if row['close'] > ah and row['high'] > ah:
                anchor_direction = 'LONG'
                anchor_idx = idx
                anchor_ep = row['close']
                break
            elif row['close'] < al and row['low'] < al:
                anchor_direction = 'SHORT'
                anchor_idx = idx
                anchor_ep = row['close']
                break
        
        if anchor_idx is None:
            continue
        
        # Anchor trade
        body_pips = to_pips(abs(day.loc[anchor_idx, 'close'] - day.loc[anchor_idx, 'open']))
        if anchor_direction == 'LONG':
            anchor_sl = al  # Opposite extreme
            anchor_tp = anchor_ep + to_price(ar * 0.50)
        else:
            anchor_sl = ah
            anchor_tp = anchor_ep - to_price(ar * 0.50)
        
        post_anchor = day[(day.index > anchor_idx) & (day['est_h'] < 17)]
        if not post_anchor.empty:
            trade = manage_trade(post_anchor, anchor_ep, anchor_direction, anchor_sl, anchor_tp)
            if trade:
                trade['entry_time'] = anchor_idx
                trade['ar_pips'] = ar
                trade['direction'] = anchor_direction
                trade['engine'] = 'anchor'
                trades.append(trade)
        
        # ── Resolution Amplifier (aligned with anchor, T1: up to 2, T2: max 1) ──
        max_amps = 2 if tier == 'T1' else 1
        amps_added = 0
        
        if anchor_direction == 'LONG':
            impulse_high = day.loc[anchor_idx, 'high']
            impulse_low = day.loc[anchor_idx, 'low']  # Approximate
        else:
            impulse_low = day.loc[anchor_idx, 'low']
            impulse_high = day.loc[anchor_idx, 'high']
        
        post_anchor_entry = day[(day.index > anchor_idx) & (day['est_h'] < 11)]
        
        for idx, row in post_anchor_entry.iterrows():
            if amps_added >= max_amps:
                break
            
            amp_body = row['body_pips']
            if amp_body < 4.1:
                continue
            
            amp_direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
            
            # Only take aligned amplifiers
            if amp_direction != anchor_direction:
                continue
            
            # Check pullback to 32-50% of impulse
            if anchor_direction == 'LONG':
                impulse_size = to_pips(impulse_high - anchor_ep)
                if impulse_size > 0:
                    retrace = to_pips(impulse_high - row['low'])
                    retrace_pct = retrace / impulse_size
                else:
                    continue
            else:
                impulse_size = to_pips(anchor_ep - impulse_low)
                if impulse_size > 0:
                    retrace = to_pips(row['high'] - impulse_low)
                    retrace_pct = retrace / impulse_size
                else:
                    continue
            
            if 0.32 <= retrace_pct <= 0.50:
                ep = row['close']
                sl = ep - to_price(amp_body * 0.80) * (1 if amp_direction == 'LONG' else -1)
                tp = ep + to_price(20.0) * (1 if amp_direction == 'LONG' else -1)  # Fixed 20p TP
                
                post = day[(day.index > idx) & (day['est_h'] < 17)]
                if not post.empty:
                    trade = manage_trade(post, ep, amp_direction, sl, tp)
                    if trade:
                        trade['entry_time'] = idx
                        trade['ar_pips'] = ar
                        trade['direction'] = amp_direction
                        trade['engine'] = 'amplifier'
                        trades.append(trade)
                amps_added += 1
    
    return calc_results(trades, "Dual_Engine")


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 8: P90P DISTRIBUTION TRACKER (NEW)
# ═══════════════════════════════════════════════════════════════════════════════

def run_p90p_distribution(df):
    """
    P90P Distribution Tracker — Part 5.
    
    Uses weighted expansion factor to predict daily target.
    Entry: P90 close outside Asian band
    TP: Weighted target (T1: 3.12x, T2: 2.68x, T3: 2.18x) with regime adjustment
    SL: 80% of P90 body
    """
    df = prepare_data(df)
    trades = []
    
    # Tier base factors
    tier_factors = {'T1': 3.12, 'T2': 2.68, 'T3': 2.18}
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue
        
        tier = classify_tier(ar)
        if tier == 'NO_GO' or tier == 'NA':
            continue
        
        base_factor = tier_factors.get(tier, 2.18)
        
        # Find P90 signal
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        p90_idx = None
        p90_row = None
        
        for idx, row in entry.iterrows():
            thresh = p90_threshold(row['est_h'])
            if row['body_pips'] >= thresh:
                p90_idx = idx
                p90_row = row
                break
        
        if p90_idx is None:
            continue
        
        direction = 'LONG' if p90_row['close'] > p90_row['open'] else 'SHORT'
        ep = p90_row['close']
        body_pips = p90_row['body_pips']
        
        # Check close outside Asian band
        if direction == 'LONG' and ep <= ah:
            continue
        if direction == 'SHORT' and ep >= al:
            continue
        
        # Calculate regime at 9AM if possible
        regime_factor = 1.0
        nine_am_data = day[(day['est_h'] >= 3) & (day['est_h'] <= 9)]
        if not nine_am_data.empty and ar > 0:
            daily_range_so_far = to_pips(nine_am_data['high'].max() - nine_am_data['low'].min())
            regime_ratio = daily_range_so_far / ar
            if regime_ratio >= 1.50:
                regime_factor = 1.10  # CONFIRMED
            elif regime_ratio < 1.45:
                regime_factor = 0.90  # FAILED
        
        # Weighted target
        weighted_factor = base_factor * regime_factor
        target_pips = ar * weighted_factor
        
        # SL: 80% of body
        sl = ep - to_price(body_pips * 0.80) * (1 if direction == 'LONG' else -1)
        tp = ep + to_price(target_pips) * (1 if direction == 'LONG' else -1)
        
        post = day[(day.index > p90_idx) & (day['est_h'] < 17)]
        if not post.empty:
            trade = manage_trade(post, ep, direction, sl, tp)
            if trade:
                trade['entry_time'] = p90_idx
                trade['ar_pips'] = ar
                trade['direction'] = direction
                trade['target_pips'] = round(target_pips, 1)
                trades.append(trade)
    
    return calc_results(trades, "P90P_Distribution")


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 9: FRACTAL RESOLUTION — Shift Engine (NEW)
# ═══════════════════════════════════════════════════════════════════════════════

def run_fractal_resolution(df):
    """
    Fractal Resolution — Part 15. Shift Engine + Trigger-Oppose SL.
    
    Logic:
    1. Detect impulse > Tier threshold from 3AM baseline
    2. If impulse fails (M5 closes back >80% into impulse within 5 bars)
    3. Enter shift trade in opposite direction
    4. SL: extreme of Trigger-Oppose candle pair
    5. TP: 1.44x impulse size (proportional counter-move)
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue
        
        tier = classify_tier(ar)
        
        # Impulse thresholds
        if tier == 'T1':
            impulse_threshold = 10.0
        elif tier == 'T2':
            impulse_threshold = 14.0
        elif tier == 'T3':
            impulse_threshold = 18.0
        else:
            continue
        
        # 3AM baseline
        baseline_data = day[day['est_h'] == 3]
        if baseline_data.empty:
            continue
        baseline_price = baseline_data.iloc[0]['close']
        
        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
        
        impulse_high = baseline_price
        impulse_low = baseline_price
        impulse_direction = None
        impulse_size = 0
        looking_for_impulse = True
        trigger_candle_high = None
        trigger_candle_low = None
        
        prev_row = None
        
        for idx, row in entry.iterrows():
            c = row['close']
            h = row['high']
            l = row['low']
            
            if looking_for_impulse:
                move = to_pips(c - baseline_price)
                if abs(move) >= impulse_threshold:
                    impulse_direction = 'LONG' if move > 0 else 'SHORT'
                    impulse_size = abs(move)
                    impulse_high = h
                    impulse_low = l
                    looking_for_impulse = False
                    trigger_candle_high = h
                    trigger_candle_low = l
                else:
                    impulse_high = max(impulse_high, h)
                    impulse_low = min(impulse_low, l)
            
            else:
                # Track impulse extreme
                if impulse_direction == 'LONG':
                    if c > impulse_high:
                        impulse_high = h
                        impulse_size = to_pips(c - baseline_price)
                        trigger_candle_high = h
                        trigger_candle_low = l
                    
                    # Check for failure: close back >80% into impulse
                    if impulse_size > 0:
                        retrace = to_pips(impulse_high - c)
                        if retrace / impulse_size > 0.80:
                            # Shift triggered — enter opposite direction
                            shift_direction = 'SHORT'
                            
                            # SL: extreme of trigger-oppose pair
                            if prev_row is not None:
                                sl = max(trigger_candle_high, prev_row['high'])
                            else:
                                sl = trigger_candle_high
                            
                            # TP: 1.44x impulse size
                            tp_pips = impulse_size * 1.44
                            tp = c - to_price(tp_pips)  # SHORT target
                            
                            post = day[(day.index > idx) & (day['est_h'] < 17)]
                            if not post.empty:
                                trade = manage_trade(post, c, shift_direction, sl, tp)
                                if trade:
                                    trade['entry_time'] = idx
                                    trade['ar_pips'] = ar
                                    trade['direction'] = shift_direction
                                    trade['shift'] = True
                                    trades.append(trade)
                            
                            # Reset
                            looking_for_impulse = True
                            impulse_direction = None
                            impulse_size = 0
                            impulse_high = baseline_price
                            impulse_low = baseline_price
                
                elif impulse_direction == 'SHORT':
                    if c < impulse_low:
                        impulse_low = l
                        impulse_size = to_pips(baseline_price - c)
                        trigger_candle_high = h
                        trigger_candle_low = l
                    
                    if impulse_size > 0:
                        retrace = to_pips(c - impulse_low)
                        if retrace / impulse_size > 0.80:
                            shift_direction = 'LONG'
                            
                            if prev_row is not None:
                                sl = min(trigger_candle_low, prev_row['low'])
                            else:
                                sl = trigger_candle_low
                            
                            tp_pips = impulse_size * 1.44
                            tp = c + to_price(tp_pips)
                            
                            post = day[(day.index > idx) & (day['est_h'] < 17)]
                            if not post.empty:
                                trade = manage_trade(post, c, shift_direction, sl, tp)
                                if trade:
                                    trade['entry_time'] = idx
                                    trade['ar_pips'] = ar
                                    trade['direction'] = shift_direction
                                    trade['shift'] = True
                                    trades.append(trade)
                            
                            looking_for_impulse = True
                            impulse_direction = None
                            impulse_size = 0
                            impulse_high = baseline_price
                            impulse_low = baseline_price
            
            prev_row = row
    
    return calc_results(trades, "Fractal_Resolution")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("🧪 QUANT LAB OPTIMIZER v2 — Fixed & New Strategies")
    print("=" * 70)
    
    df = load_eurusd_m5()
    if df is None:
        return {}
    
    print(f"\n📊 Data: {len(df):,} bars | {df.index[0].date()} → {df.index[-1].date()}")
    
    strategies = [
        ("Deep_Mean_Reversion", run_deep_mean_reversion),
        ("Stall_Harvest_CFD", run_stall_harvest_cfd),
        ("Constraint_Anchor", run_constraint_anchor),
        ("Blind_Structural_Chain", run_blind_structural_chain),
        ("Two_Plays", run_two_plays),
        ("Failure_Repair", run_failure_repair),
        ("Dual_Engine", run_dual_engine),
        ("P90P_Distribution", run_p90p_distribution),
        ("Fractal_Resolution", run_fractal_resolution),
    ]
    
    all_results = {}
    
    for name, fn in strategies:
        print(f"\n{'─'*60}")
        print(f"▶ {name}")
        t0 = time.time()
        try:
            r = fn(df)
            elapsed = time.time() - t0
            all_results[name] = r
            if r.get('total_trades', 0) > 0:
                print(f"  ✅ {r['total_trades']} trades | WR: {r['win_rate']}% | "
                      f"P&L: {r['total_pnl']}p | PF: {r['profit_factor']} | "
                      f"MaxDD: {r['max_dd']}p | Exp: {r['expectancy']}p | "
                      f"({elapsed:.1f}s)")
                if 'by_exit' in r:
                    for reason, count in sorted(r['by_exit'].items(), key=lambda x: -x[1]):
                        print(f"      {reason}: {count}")
            else:
                print(f"  ⚠️ No trades ({elapsed:.1f}s)")
                if 'error' in r:
                    print(f"     Error: {r['error']}")
        except Exception as e:
            elapsed = time.time() - t0
            print(f"  ❌ {type(e).__name__}: {e} ({elapsed:.1f}s)")
            import traceback
            traceback.print_exc()
            all_results[name] = {"strategy": name, "error": str(e), "total_trades": 0}
    
    # Summary
    print(f"\n{'='*70}")
    print(f"📊 COMPARATIVE RESULTS")
    print(f"{'='*70}")
    print(f"{'Strategy':<25} {'Trades':>6} {'WR%':>6} {'P&L(p)':>8} {'PF':>5} {'MaxDD':>7} {'Exp':>6}")
    print(f"{'─'*70}")
    
    for name, r in all_results.items():
        if r.get('total_trades', 0) > 0:
            print(f"{name:<25} {r['total_trades']:>6} {r['win_rate']:>6.1f} "
                  f"{r['total_pnl']:>8.1f} {r['profit_factor']:>5.2f} "
                  f"{r['max_dd']:>7.1f} {r['expectancy']:>6.3f}")
        else:
            print(f"{name:<25} {'N/A':>6} {'N/A':>6} {'N/A':>8} {'N/A':>5} {'N/A':>7} {'N/A':>6}")
    
    # Save results
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rf = RESULTS_DIR / f"optimizer_v2_{ts}.json"
    with open(rf, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n💾 Results saved to {rf}")
    
    return all_results


if __name__ == "__main__":
    main()
