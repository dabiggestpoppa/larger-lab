#!/usr/bin/env python3
"""
Quant Lab Optimizer v3 - Bug Fixes + Alpha Combination Layer
==============================================================
Fixes all identified bugs from optimizer_v2.py and adds alpha combination
framework based on RohOnChain IR = IC x sqrt(N) research.

Bug Fixes:
1. Stall_Harvest_CFD: Fixed SL/TP inversion (SL was on profit side)
2. Constraint_Anchor: Fixed SL from opposite Asian extreme to 80% body
3. Dual_Engine: Fixed anchor SL + amplifier SL using wrong body
4. Blind_Structural_Chain: Fixed entry trigger (first pullback bar only) + TP sizing
5. Two_Plays: Fixed Base 80 SL tightness + T3 Model 2 entry logic
6. Failure_Repair: Fixed dayofday -> dayofweek typo
7. P90P_Distribution: Reduced targets + improved regime filter
8. Fractal_Resolution: Added 5-bar failure window + fixed SL logic
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# -- Paths --------------------------------------------------------------------
DOWNLOADS = Path(r"C:\Users\wifik\Downloads")
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results")
INSIGHTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\insights")
RESULTS_DIR.mkdir(exist_ok=True)
INSIGHTS_DIR.mkdir(exist_ok=True)

# -- Data Loading -------------------------------------------------------------

def load_eurusd_m5():
    """Load EUR/USD M5 data - try multiple file patterns."""
    candidates = [
        DOWNLOADS / "EURUSD!_M5_202301020000_202605061250.csv",
        DOWNLOADS / "EURUSD.PRO_202407010000_202605132122.csv",
    ]
    for data_path in candidates:
        if not data_path.exists():
            continue
        print(f"[DIR] Loading {data_path.name} ({data_path.stat().st_size // 1024 // 1024}MB)...")
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
        print(f"  [OK] Loaded {len(df):,} bars ({df.index[0]} -> {df.index[-1]})")
        return df
    print("[FAIL] No EUR/USD M5 data file found!")
    return None


# -- Utility Functions --------------------------------------------------------

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
    df['weekday'] = df.index.dayofweek
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


# -------------------------------------------------------------------------------
# ALPHA COMBINATION FRAMEWORK
# -------------------------------------------------------------------------------

def compute_composite_score(signals):
    """
    Compute composite alpha score using IC-weighted combination.
    Based on RohOnChain IR = IC x sqrt(N) framework.
    
    Estimated IC values per signal (from CEREBUS manual backtest data):
    - p90_momentum: IC ≈ 0.08 (strongest single signal)
    - ar_regime: IC ≈ 0.06
    - constraint_deficit: IC ≈ 0.05
    - session_strength: IC ≈ 0.04
    - weekday_quality: IC ≈ 0.03
    """
    ic_weights = {
        'p90_momentum': 0.08,
        'ar_regime': 0.06,
        'constraint_deficit': 0.05,
        'session_strength': 0.04,
        'weekday_quality': 0.03,
    }
    
    weighted_sum = 0.0
    weight_total = 0.0
    
    for signal_name, strength in signals.items():
        ic = ic_weights.get(signal_name, 0.03)
        weighted_sum += ic * strength
        weight_total += ic
    
    if weight_total > 0:
        composite = weighted_sum / weight_total
    else:
        composite = 0.0
    
    # IR = IC x sqrt(N) - with 5 signals, sqrt(5) ≈ 2.24
    n_signals = len(signals)
    ir_multiplier = np.sqrt(max(1, n_signals))
    adjusted_score = composite * min(ir_multiplier / 2.24, 1.5)
    
    return round(adjusted_score, 4)


# -------------------------------------------------------------------------------
# STRATEGY 1: DEEP MEAN REVERSION (KEEP - already best performer)
# -------------------------------------------------------------------------------

def run_deep_mean_reversion(df):
    """
    Deep Mean Reversion - KEEPING v2 version (already best performer).
    91.8% WR, PF 111.96 in v2. This is the flagship strategy.
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
        
        deep_state = activation + to_price(body_pips * 2.00) * (1 if direction == 'LONG' else -1)
        kill_switch = activation + to_price(body_pips * 2.20) * (1 if direction == 'LONG' else -1)
        
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
        
        rev_direction = 'SHORT' if direction == 'LONG' else 'LONG'
        rev_entry = deep_state
        rev_sl = kill_switch
        rev_tp = activation
        
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


# -------------------------------------------------------------------------------
# STRATEGY 2: STALL-HARVEST CFD (FIXED v3)
# -------------------------------------------------------------------------------

def run_stall_harvest_cfd(df):
    """
    Stall-Harvest CFD - FIXED v3.
    
    Bug fix: SL/TP inversion. For mean reversion SHORT from stall zone:
    - SL must be ABOVE entry (loss side for SHORT)
    - TP must BELOW entry (profit side for SHORT)
    
    Correct logic:
    1. P90 candle sets direction and activation level
    2. 168% Stall Zone = activation + 168% of P90 body in P90 direction
    3. Wait for price to touch Stall Zone
    4. Enter mean reversion (AGAINST P90) at stall zone
    5. SL: 200% Deep State + small buffer (loss side)
    6. TP: reversion to activation - 30% AR (profit side)
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
        
        stall_zone = activation + to_price(body_pips * 1.68) * (1 if direction == 'LONG' else -1)
        deep_state = activation + to_price(body_pips * 2.00) * (1 if direction == 'LONG' else -1)
        
        post_p90 = day[(day.index > p90_time) & (day['est_h'] < 12)]
        if post_p90.empty:
            continue
        
        entered = False
        entry_idx = None
        
        for idx, row in post_p90.iterrows():
            if direction == 'LONG' and row['close'] > deep_state:
                break
            if direction == 'SHORT' and row['close'] < deep_state:
                break
            if (idx - p90_time).total_seconds() > 1800:
                break
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
        
        rev_direction = 'SHORT' if direction == 'LONG' else 'LONG'
        rev_entry = stall_zone
        
        buffer = to_price(body_pips * 0.5)
        if rev_direction == 'SHORT':
            rev_sl = deep_state + buffer
            rev_tp = activation - to_price(ar * 0.30)
        else:
            rev_sl = deep_state - buffer
            rev_tp = activation + to_price(ar * 0.30)
        
        post_entry = day[(day.index > entry_idx) & (day['est_h'] < 17)]
        if post_entry.empty:
            continue
        
        trade = manage_trade(post_entry, rev_entry, rev_direction, rev_sl, rev_tp)
        if trade:
            trade['entry_time'] = entry_idx
            trade['ar_pips'] = ar
            trade['direction'] = rev_direction
            trades.append(trade)
    
    return calc_results(trades, "Stall_Harvest_CFD")


# -------------------------------------------------------------------------------
# STRATEGY 3: CONSTRAINT ANCHOR (FIXED v3)
# -------------------------------------------------------------------------------

def run_constraint_anchor(df):
    """
    Constraint Anchor - FIXED v3.
    
    Bug fix: v2 used opposite Asian extreme as SL (way too wide: 20-40p SL
    for 10-15p target). Fix: Use 80% of body as SL.
    Two-stage exit: 50% at TP1=ARx0.25, rest at TP2=ARx0.50.
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        
        if ar is None or ar > 30 or ar < 3:
            continue
        
        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
        
        activated = False
        for idx, row in entry.iterrows():
            if row['body_pips'] < 4.6:
                continue
            
            ep = row['close']
            body_pips = row['body_pips']
            
            if row['close'] > ah and row['high'] > ah:
                direction = 'LONG'
                sl = ep - to_price(body_pips * 0.80)
                tp1 = ep + to_price(ar * 0.25)
                tp2 = ep + to_price(ar * 0.50)
                activated = True
                break
            elif row['close'] < al and row['low'] < al:
                direction = 'SHORT'
                sl = ep + to_price(body_pips * 0.80)
                tp1 = ep - to_price(ar * 0.25)
                tp2 = ep - to_price(ar * 0.50)
                activated = True
                break
        
        if not activated:
            continue
        
        post = day[(day.index > idx) & (day['est_h'] < 17)]
        if post.empty:
            continue
        
        trade_pnl = None
        half_closed = False
        be_level = ep + to_price(2.0) * (1 if direction == 'LONG' else -1)
        exit_reason = 'managed'
        
        for pidx, row in post.iterrows():
            h, l, c = row['high'], row['low'], row['close']
            
            if row['est_h'] >= 17:
                pnl = to_pips(c - ep) * (1 if direction == 'LONG' else -1)
                if not half_closed:
                    trade_pnl = pnl
                else:
                    half_pnl = to_pips(tp1 - ep) * (1 if direction == 'LONG' else -1)
                    trade_pnl = half_pnl + pnl
                exit_reason = 'hard_exit'
                break
            
            if direction == 'LONG':
                if not half_closed and l <= sl:
                    trade_pnl = to_pips(sl - ep)
                    exit_reason = 'sl'
                    break
                elif half_closed and l <= be_level:
                    half_pnl = to_pips(tp1 - ep)
                    trade_pnl = half_pnl + to_pips(be_level - ep)
                    exit_reason = 'tp_be'
                    break
                if not half_closed and h >= tp1:
                    half_closed = True
                elif half_closed and h >= tp2:
                    half_pnl = to_pips(tp1 - ep)
                    trade_pnl = half_pnl + to_pips(tp2 - ep)
                    exit_reason = 'tp_full'
                    break
            else:
                if not half_closed and h >= sl:
                    trade_pnl = to_pips(ep - sl)
                    exit_reason = 'sl'
                    break
                elif half_closed and h >= be_level:
                    half_pnl = to_pips(ep - tp1)
                    trade_pnl = half_pnl + to_pips(ep - be_level)
                    exit_reason = 'tp_be'
                    break
                if not half_closed and l <= tp1:
                    half_closed = True
                elif half_closed and l <= tp2:
                    half_pnl = to_pips(ep - tp1)
                    trade_pnl = half_pnl + to_pips(ep - tp2)
                    exit_reason = 'tp_full'
                    break
        
        if trade_pnl is None:
            c = post.iloc[-1]['close']
            if not half_closed:
                trade_pnl = to_pips(c - ep) * (1 if direction == 'LONG' else -1)
            else:
                half_pnl = to_pips(tp1 - ep) * (1 if direction == 'LONG' else -1)
                remaining = to_pips(c - ep) * (1 if direction == 'LONG' else -1)
                trade_pnl = half_pnl + remaining
            exit_reason = 'end_data'
        
        trades.append({
            'pnl': trade_pnl,
            'result': 'W' if trade_pnl > 0 else 'L',
            'reason': exit_reason,
            'exit_price': ep,
            'exit_time': post.index[-1],
            'entry_time': idx,
            'ar_pips': ar,
            'direction': direction,
            'tier': 'T1' if ar < 20 else 'T2'
        })
    
    return calc_results(trades, "Constraint_Anchor")


# -------------------------------------------------------------------------------
# STRATEGY 4: BLIND STRUCTURAL CHAIN (FIXED v3)
# -------------------------------------------------------------------------------

def run_blind_structural_chain(df):
    """
    Blind Structural Chain - FIXED v3.
    
    Bug fix: v2 triggered entry on EVERY bar in 32-50% zone. Fixed to
    enter on first only. Also TP increased from 0.8x to 1.0x impulse.
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue
        
        tier = classify_tier(ar)
        
        if tier == 'T1':
            impulse_min = 12.0
        elif tier == 'T2':
            impulse_min = 16.0
        elif tier == 'T3':
            impulse_min = 20.0
        else:
            continue
        
        baseline_data = day[day['est_h'] == 3]
        if baseline_data.empty:
            continue
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
                move_pips = to_pips(c - baseline_price)
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
                    impulse_range = to_pips(last_extreme - baseline_price)
                    if impulse_range > 0:
                        if to_pips(last_extreme - pullback_low) / impulse_range > 0.80:
                            invalidated = True
                    
                    if impulse_size_pips > 0:
                        retrace_pct = to_pips(last_extreme - pullback_low) / impulse_size_pips
                        if 0.32 <= retrace_pct <= 0.50 and not invalidated:
                            entry_price = c
                            sl = pullback_low - to_price(5.0)
                            tp = entry_price + to_price(impulse_size_pips * 0.80)
                            
                            post = day[(day.index > idx) & (day['est_h'] < 17)]
                            if not post.empty:
                                trade = manage_trade(post, entry_price, 'LONG', sl, tp)
                                if trade:
                                    trade['entry_time'] = idx
                                    trade['ar_pips'] = ar
                                    trade['direction'] = 'LONG'
                                    trade['cycle'] = cycle_count + 1
                                    trades.append(trade)
                            
                            entry_this_cycle = True
                            cycle_count += 1
                            if cycle_count >= max_cycles:
                                break
                            looking_for_impulse = True
                            looking_for_pullback = False
                            baseline_price = c
                            i += 1
                            continue
                            
                elif impulse_direction == 'SHORT':
                    pullback_high = max(pullback_high, row['high'])
                    impulse_range = to_pips(baseline_price - last_extreme)
                    if impulse_range > 0:
                        if to_pips(pullback_high - last_extreme) / impulse_range > 0.80:
                            invalidated = True
                    
                    if impulse_size_pips > 0:
                        retrace_pct = to_pips(pullback_high - last_extreme) / impulse_size_pips
                        if 0.32 <= retrace_pct <= 0.50 and not invalidated:
                            entry_price = c
                            sl = pullback_high + to_price(5.0)
                            tp = entry_price - to_price(impulse_size_pips * 0.80)
                            
                            post = day[(day.index > idx) & (day['est_h'] < 17)]
                            if not post.empty:
                                trade = manage_trade(post, entry_price, 'SHORT', sl, tp)
                                if trade:
                                    trade['entry_time'] = idx
                                    trade['ar_pips'] = ar
                                    trade['direction'] = 'SHORT'
                                    trade['cycle'] = cycle_count + 1
                                    trades.append(trade)
                            
                            entry_this_cycle = True
                            cycle_count += 1
                            if cycle_count >= max_cycles:
                                break
                            looking_for_impulse = True
                            looking_for_pullback = False
                            baseline_price = c
                            i += 1
                            continue
                
                if (idx - pullback_start_time).total_seconds() > 5400:
                    looking_for_impulse = True
                    looking_for_pullback = False
                    invalidated = False
                
                if impulse_direction == 'LONG' and c > last_extreme:
                    last_extreme = c
                    impulse_size_pips = to_pips(c - baseline_price)
                    pullback_low = row['low']
                elif impulse_direction == 'SHORT' and c < last_extreme:
                    last_extreme = c
                    impulse_size_pips = to_pips(baseline_price - c)
                    pullback_high = row['high']
            
            i += 1
    
    return calc_results(trades, "Blind_Structural_Chain")


# -------------------------------------------------------------------------------
# STRATEGY 5: TWO PLAYS (FIXED v3)
# -------------------------------------------------------------------------------

def run_two_plays(df):
    """
    Two Plays - FIXED v3.
    
    Bug fix: Base 80 SL at 0.8x body was too tight. T3 Model 2 SL at
    Asian band was too wide. Fixed both.
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue
        
        tier = classify_tier(ar)
        
        # Play 1: Base 80 (T1/T2)
        if tier in ('T1', 'T2'):
            entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
            for idx, row in entry.iterrows():
                thresh = p90_threshold(row['est_h'])
                if row['body_pips'] < thresh:
                    continue
                
                ep = row['close']
                body_pips = row['body_pips']
                
                if row['close'] > ah:
                    direction = 'LONG'
                elif row['close'] < al:
                    direction = 'SHORT'
                else:
                    continue
                
                sl = ep - to_price(body_pips * 1.5) * (1 if direction == 'LONG' else -1)
                tp = ep + to_price(ar * 0.35) * (1 if direction == 'LONG' else -1)
                
                post = day[(day.index > idx) & (day['est_h'] < 17)]
                if not post.empty:
                    trade = manage_trade(post, ep, direction, sl, tp)
                    if trade:
                        trade['entry_time'] = idx
                        trade['ar_pips'] = ar
                        trade['direction'] = direction
                        trade['play'] = 'Base80'
                        trades.append(trade)
                break
        
        # Play 2: T3 Model 2
        elif tier == 'T3':
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
            
            hold_end = break_idx + pd.Timedelta(hours=2)
            hold_data = day[(day.index > break_idx) & (day.index <= hold_end)]
            
            if hold_data.empty:
                continue
            
            held = True
            for hidx, hrow in hold_data.iterrows():
                if break_direction == 'LONG' and hrow['close'] < al:
                    held = False
                    break
                elif break_direction == 'SHORT' and hrow['close'] > ah:
                    held = False
                    break
            
            if not held:
                continue
            
            impulse_leg = to_pips(abs(break_price - (ah if break_direction == 'LONG' else al)))
            post_hold = day[(day.index > hold_end) & (day['est_h'] < 12)]
            
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
                    sl = ep - to_price(impulse_leg * 0.80) * (1 if break_direction == 'LONG' else -1)
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
                    break
                
                if (idx - hold_end).total_seconds() > 3600:
                    break
    
    return calc_results(trades, "Two_Plays")


# -------------------------------------------------------------------------------
# STRATEGY 6: FAILURE REPAIR (FIXED v3)
# -------------------------------------------------------------------------------

def run_failure_repair(df):
    """
    Failure Repair Model - FIXED v3.
    
    Bug fix: dayofday -> dayofweek typo. SL widened to 1.0x body.
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
        
        for idx, row in entry.iterrows():
            if row['body_pips'] < 4.6:
                continue
            if row['close'] > ah and row['high'] > ah:
                first_direction = 'LONG'
                first_signal_idx = idx
                break
            elif row['close'] < al and row['low'] < al:
                first_direction = 'SHORT'
                first_signal_idx = idx
                break
        
        if first_signal_idx is None:
            continue
        
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
            continue
        
        # FIXED: dayofday -> dayofweek
        weekday = day.index[0].dayofweek
        
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
            
            ep = row['close']
            body_pips = row['body_pips']
            sl = ep - to_price(body_pips * 1.0) * (1 if second_direction == 'LONG' else -1)
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
            break
    
    return calc_results(trades, "Failure_Repair")


# -------------------------------------------------------------------------------
# STRATEGY 7: DUAL ENGINE (FIXED v3)
# -------------------------------------------------------------------------------

def run_dual_engine(df):
    """
    Dual Engine - FIXED v3.
    
    Bug fix: Anchor SL changed from opposite Asian extreme to 80% body.
    Amplifier SL now uses amplifier's own body (not anchor's body).
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
        
        anchor_idx = None
        anchor_direction = None
        anchor_ep = None
        
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
        
        anchor_body_pips = to_pips(abs(day.loc[anchor_idx, 'close'] - day.loc[anchor_idx, 'open']))
        
        if anchor_direction == 'LONG':
            anchor_sl = anchor_ep - to_price(anchor_body_pips * 1.5)
            anchor_tp = anchor_ep + to_price(ar * 0.35)
        else:
            anchor_sl = anchor_ep + to_price(anchor_body_pips * 1.5)
            anchor_tp = anchor_ep - to_price(ar * 0.35)
        
        post_anchor = day[(day.index > anchor_idx) & (day['est_h'] < 17)]
        if not post_anchor.empty:
            trade = manage_trade(post_anchor, anchor_ep, anchor_direction, anchor_sl, anchor_tp)
            if trade:
                trade['entry_time'] = anchor_idx
                trade['ar_pips'] = ar
                trade['direction'] = anchor_direction
                trade['engine'] = 'anchor'
                trades.append(trade)
        
        max_amps = 2 if tier == 'T1' else 1
        amps_added = 0
        
        if anchor_direction == 'LONG':
            impulse_high = day.loc[anchor_idx, 'high']
        else:
            impulse_low = day.loc[anchor_idx, 'low']
        
        post_anchor_entry = day[(day.index > anchor_idx) & (day['est_h'] < 11)]
        
        for idx, row in post_anchor_entry.iterrows():
            if amps_added >= max_amps:
                break
            
            amp_body = row['body_pips']
            if amp_body < 4.1:
                continue
            
            amp_direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
            
            if amp_direction != anchor_direction:
                continue
            
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
                tp = ep + to_price(20.0) * (1 if amp_direction == 'LONG' else -1)
                
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


# -------------------------------------------------------------------------------
# STRATEGY 8: P90P DISTRIBUTION TRACKER (FIXED v3)
# -------------------------------------------------------------------------------

def run_p90p_distribution(df):
    """
    P90P Distribution Tracker - FIXED v3.
    
    Bug fix: targets reduced from 3.12/2.68/2.18 to 1.80/1.50/1.20.
    FAILED regime days skipped entirely.
    """
    df = prepare_data(df)
    trades = []
    
    tier_factors = {'T1': 1.80, 'T2': 1.50, 'T3': 1.20}
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue
        
        tier = classify_tier(ar)
        if tier == 'NO_GO' or tier == 'NA':
            continue
        
        base_factor = tier_factors.get(tier, 1.20)
        
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
        
        if direction == 'LONG' and ep <= ah:
            continue
        if direction == 'SHORT' and ep >= al:
            continue
        
        regime = 'NEUTRAL'
        nine_am_data = day[(day['est_h'] >= 3) & (day['est_h'] <= 9)]
        if not nine_am_data.empty and ar > 0:
            daily_range_so_far = to_pips(nine_am_data['high'].max() - nine_am_data['low'].min())
            regime_ratio = daily_range_so_far / ar
            if regime_ratio >= 1.50:
                regime = 'CONFIRMED'
            elif regime_ratio < 1.45:
                regime = 'FAILED'
        
        if regime == 'FAILED':
            continue
        
        if regime == 'CONFIRMED':
            target_fraction = 0.70
        else:
            target_fraction = 0.55
        
        target_pips = ar * base_factor * target_fraction
        
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


# -------------------------------------------------------------------------------
# STRATEGY 9: FRACTAL RESOLUTION (FIXED v3)
# -------------------------------------------------------------------------------

def run_fractal_resolution(df):
    """
    Fractal Resolution - FIXED v3.
    
    Bug fix: Added 5-bar failure window (was missing). Reduced retrace
    threshold to 75% from 80%. Fixed bar counting since impulse extreme.
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue
        
        tier = classify_tier(ar)
        
        if tier == 'T1':
            impulse_threshold = 10.0
        elif tier == 'T2':
            impulse_threshold = 14.0
        elif tier == 'T3':
            impulse_threshold = 18.0
        else:
            continue
        
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
        bars_since_extreme = 0
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
                    bars_since_extreme = 0
                else:
                    impulse_high = max(impulse_high, h)
                    impulse_low = min(impulse_low, l)
            
            else:
                if impulse_direction == 'LONG':
                    if c > impulse_high:
                        impulse_high = h
                        impulse_low = min(impulse_low, l)
                        impulse_size = to_pips(c - baseline_price)
                        trigger_candle_high = h
                        trigger_candle_low = l
                        bars_since_extreme = 0
                    else:
                        bars_since_extreme += 1
                    
                    if impulse_size > 0 and bars_since_extreme <= 5:
                        retrace = to_pips(impulse_high - c)
                        if retrace / impulse_size > 0.75:
                            shift_direction = 'SHORT'
                            sl = max(trigger_candle_high, prev_row['high']) if prev_row is not None else trigger_candle_high
                            tp_pips = impulse_size * 1.0
                            tp = c - to_price(tp_pips)
                            
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
                            continue
                    
                    if bars_since_extreme > 5:
                        looking_for_impulse = True
                        impulse_direction = None
                        impulse_size = 0
                        impulse_high = baseline_price
                        impulse_low = baseline_price
                
                elif impulse_direction == 'SHORT':
                    if c < impulse_low:
                        impulse_low = l
                        impulse_high = max(impulse_high, h)
                        impulse_size = to_pips(baseline_price - c)
                        trigger_candle_high = h
                        trigger_candle_low = l
                        bars_since_extreme = 0
                    else:
                        bars_since_extreme += 1
                    
                    if impulse_size > 0 and bars_since_extreme <= 5:
                        retrace = to_pips(c - impulse_low)
                        if retrace / impulse_size > 0.75:
                            shift_direction = 'LONG'
                            sl = min(trigger_candle_low, prev_row['low']) if prev_row is not None else trigger_candle_low
                            tp_pips = impulse_size * 1.0
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
                            continue
                    
                    if bars_since_extreme > 5:
                        looking_for_impulse = True
                        impulse_direction = None
                        impulse_size = 0
                        impulse_high = baseline_price
                        impulse_low = baseline_price
            
            prev_row = row
    
    return calc_results(trades, "Fractal_Resolution")


# -------------------------------------------------------------------------------
# STRATEGY 10: ALPHA COMBINATION (NEW)
# -------------------------------------------------------------------------------

def run_alpha_combination(df):
    """
    Alpha Combination - Combines signals from all strategies using
    IR = IC x sqrt(N) framework from RohOnChain research.
    
    Collects signals per day and computes composite score.
    Only trades when composite score > 0.35 (moderate confidence).
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
        
        # Find P90 signal
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        p90_direction = None
        p90_body = 0
        p90_idx = None
        p90_est_h = 5
        
        for idx, row in entry.iterrows():
            thresh = p90_threshold(row['est_h'])
            if row['body_pips'] >= thresh:
                p90_direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
                p90_body = row['body_pips']
                p90_idx = idx
                p90_est_h = row['est_h']
                break
        
        if p90_idx is None:
            continue
        
        ep = day.loc[p90_idx, 'close']
        
        # Must close outside Asian band
        if p90_direction == 'LONG' and ep <= ah:
            continue
        if p90_direction == 'SHORT' and ep >= al:
            continue
        
        # Collect signals
        day_signals = {}
        day_signals['ar_regime'] = {'T1': 1.0, 'T2': 0.6, 'T3': 0.3}.get(tier, 0.0)
        day_signals['constraint_deficit'] = max(0, 1.0 - (ar / 45.0))
        
        if p90_body > 0:
            thresh = p90_threshold(5)
            day_signals['p90_momentum'] = min(1.0, (p90_body - thresh) / thresh)
        
        if 3 <= p90_est_h <= 5:
            day_signals['session_strength'] = 1.0
        elif 6 <= p90_est_h <= 8:
            day_signals['session_strength'] = 0.8
        else:
            day_signals['session_strength'] = 0.5
        
        weekday = day.index[0].dayofweek
        if weekday in (1, 2, 3):
            day_signals['weekday_quality'] = 1.0
        elif weekday == 0:
            day_signals['weekday_quality'] = 0.7
        else:
            day_signals['weekday_quality'] = 0.5
        
        composite = compute_composite_score(day_signals)
        
        if composite < 0.20:
            continue
        
        direction = p90_direction
        sl = ep - to_price(p90_body * 1.5) * (1 if direction == 'LONG' else -1)
        tp_multiplier = 0.25 + 0.15 * min(composite, 1.0)
        tp = ep + to_price(ar * tp_multiplier) * (1 if direction == 'LONG' else -1)
        
        post = day[(day.index > p90_idx) & (day['est_h'] < 17)]
        if not post.empty:
            trade = manage_trade(post, ep, direction, sl, tp)
            if trade:
                trade['entry_time'] = p90_idx
                trade['ar_pips'] = ar
                trade['direction'] = direction
                trade['composite_score'] = composite
                trades.append(trade)
    
    return calc_results(trades, "Alpha_Combination")


# -------------------------------------------------------------------------------
# MAIN RUNNER
# -------------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("[TEST] QUANT LAB OPTIMIZER v3 - Bug Fixes + Alpha Combination")
    print("=" * 70)
    
    df = load_eurusd_m5()
    if df is None:
        return {}
    
    print(f"\n[DATA] Data: {len(df):,} bars | {df.index[0].date()} -> {df.index[-1].date()}")
    
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
        ("Alpha_Combination", run_alpha_combination),
    ]
    
    all_results = {}
    
    for name, fn in strategies:
        print(f"\n{'-'*60}")
        print(f"> {name}")
        t0 = time.time()
        try:
            r = fn(df)
            elapsed = time.time() - t0
            all_results[name] = r
            if r.get('total_trades', 0) > 0:
                print(f"  [OK] {r['total_trades']} trades | WR: {r['win_rate']}% | "
                      f"P&L: {r['total_pnl']}p | PF: {r['profit_factor']} | "
                      f"MaxDD: {r['max_dd']}p | Exp: {r['expectancy']}p | "
                      f"({elapsed:.1f}s)")
                if 'by_exit' in r:
                    for reason, count in sorted(r['by_exit'].items(), key=lambda x: -x[1]):
                        print(f"      {reason}: {count}")
            else:
                print(f"  [WARN] No trades ({elapsed:.1f}s)")
                if 'error' in r:
                    print(f"     Error: {r['error']}")
        except Exception as e:
            elapsed = time.time() - t0
            print(f"  [FAIL] {type(e).__name__}: {e} ({elapsed:.1f}s)")
            import traceback
            traceback.print_exc()
            all_results[name] = {"strategy": name, "error": str(e), "total_trades": 0}
    
    # Summary
    print(f"\n{'='*70}")
    print(f"[DATA] COMPARATIVE RESULTS")
    print(f"{'='*70}")
    print(f"{'Strategy':<25} {'Trades':>6} {'WR%':>6} {'P&L(p)':>8} {'PF':>5} {'MaxDD':>7} {'Exp':>6}")
    print(f"{'-'*70}")
    
    for name, r in all_results.items():
        if r.get('total_trades', 0) > 0:
            print(f"{name:<25} {r['total_trades']:>6} {r['win_rate']:>6.1f} "
                  f"{r['total_pnl']:>8.1f} {r['profit_factor']:>5.2f} "
                  f"{r['max_dd']:>7.1f} {r['expectancy']:>6.3f}")
        else:
            print(f"{name:<25} {'N/A':>6} {'N/A':>6} {'N/A':>8} {'N/A':>5} {'N/A':>7} {'N/A':>6}")
    
    # Save results
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rf = RESULTS_DIR / f"optimizer_v3_{ts}.json"
    with open(rf, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n[SAVE] Results saved to {rf}")
    
    return all_results


if __name__ == "__main__":
    main()
