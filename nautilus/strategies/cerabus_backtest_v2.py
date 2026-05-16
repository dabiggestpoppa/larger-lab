"""
CEREBUS FX v4 — Comprehensive Strategy Backtest Engine v2
=========================================================
Implements ALL strategies from the CEREBUS FX v4 Complete Manual
with corrected logic based on detailed manual analysis.

KEY CORRECTIONS from v1:
  1. P90 direction = trade direction (constraint resolution direction)
  2. TP targets: Asian -25% and Asian -50% (expansion, not mean reversion)
  3. SL: 80% of P90 body for initial, 168% of body for cascades
  4. Cascade: same direction P90s only, 30-90 min window, max 3
  5. 45-min add: +8 pip extension required
  6. Deep Mean Reversion: counter-trade at 200% level
  7. Stall-Harvest: enter at 168% in P90 direction
  8. Constraint Anchor: trade Asian band breakout in breakout direction

Author: OWL — CEREBUS Strategy Reconstruction Agent
Date: 2026-05-16
"""
import sys
import json
import time
import math
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict

import pandas as pd
import numpy as np

#  Data Loading 

def load_eurusd_m5():
    """Load EUR/USD M5 data from Downloads."""
    data_path = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")
    
    if not data_path.exists():
        print(f" Data file not found: {data_path}")
        return None
    
    print(f" Loading {data_path.name} ({data_path.stat().st_size // 1024 // 1024}MB)...")
    
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
            vol = int(parts[6])
            records.append({'open': o, 'high': h, 'low': l, 'close': c, 'volume': vol, 'ts': ts})
        except (ValueError, IndexError):
            continue
    
    df = pd.DataFrame(records)
    df.set_index('ts', inplace=True)
    df.sort_index(inplace=True)
    
    print(f"   Loaded {len(df):,} bars ({df.index[0]} → {df.index[-1]})")
    return df


#  Utility Functions 

def to_pips(price_diff, pair="EUR/USD"):
    """Convert price difference to pips."""
    if "JPY" in pair: return price_diff * 100.0
    if "XAU" in pair: return price_diff * 10.0
    return price_diff * 10000.0

def to_price(pips, pair="EUR/USD"):
    """Convert pips to price."""
    if "JPY" in pair: return pips / 100.0
    if "XAU" in pair: return pips / 10.0
    return pips / 10000.0

def day_results(trades, name, pair="EUR/USD"):
    """Compute performance metrics from trade list."""
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
        "expectancy": round(total / len(pnls), 3),
        "by_exit": by_exit,
    }


#  Data Preparation 

def prepare_data(df):
    """Add computed columns to the dataframe."""
    df = df.copy()
    df['utc_h'] = df.index.hour
    df['est_h'] = (df['utc_h'] - 5 + 24) % 24
    df['date'] = df.index.date
    df['body_pips'] = to_pips((df['close'] - df['open']).abs())
    df['body_dir'] = np.where(df['close'] > df['open'], 1, -1)  # 1=bull, -1=bear
    df['range_pips'] = to_pips(df['high'] - df['low'])
    return df

def get_day_data(df, date):
    """Get data for a specific date."""
    return df[df['date'] == date].copy()

def calc_asian_range(day_df):
    """Calculate Asian Range from 7PM-3AM EST bars (19:00-03:00 EST = 00:00-08:00 UTC)."""
    asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
    if len(asian) < 2:
        return None, None, None
    ah = asian['high'].max()
    al = asian['low'].min()
    ar = to_pips(ah - al)
    return ah, al, ar

def classify_tier(ar_pips):
    """Classify Asian Range into tier."""
    if ar_pips is None: return 'NA'
    if ar_pips < 20: return 'T1'
    if ar_pips < 30: return 'T2'
    if ar_pips < 45: return 'T3'
    return 'NO_GO'

def p90_threshold(est_h):
    """Get P90 candle body threshold for given EST hour."""
    if est_h < 2 or est_h >= 11: return 99.0
    if est_h < 4: return 4.1
    if est_h < 6: return 4.6
    if est_h < 8: return 4.6
    if est_h < 10: return 5.9
    if est_h < 11: return 6.2
    return 99.0

def find_p90_signals(entry_df):
    """Find ALL P90 signals in entry window data. Returns list of (direction, row) tuples."""
    signals = []
    for idx, row in entry_df.iterrows():
        thresh = p90_threshold(row['est_h'])
        if row['body_pips'] >= thresh:
            direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
            signals.append((direction, row, idx))
    return signals

def find_first_p90_signal(entry_df):
    """Find the first P90 signal in entry window data. Returns (direction, row, idx) or (None, None, None)."""
    signals = find_p90_signals(entry_df)
    if signals:
        return signals[0]
    return None, None, None

def manage_trade(post_df, entry_price, direction, sl, tp, hard_exit_est=17):
    """Manage a single trade through subsequent bars. Returns trade dict or None."""
    for idx, row in post_df.iterrows():
        h, l, c = row['high'], row['low'], row['close']
        
        # Hard exit at 12PM EST
        if row['est_h'] >= hard_exit_est:
            pnl = to_pips(c - entry_price) * (1 if direction == 'LONG' else -1)
            return {'pnl': pnl, 'result': 'W' if pnl > 0 else 'L',
                    'reason': 'hard_exit_12pm', 'exit_price': c, 'exit_time': idx}
        
        if direction == 'LONG':
            # Check SL first (adverse move)
            if l <= sl:
                pnl = to_pips(sl - entry_price)
                return {'pnl': pnl, 'result': 'L', 'reason': 'sl', 'exit_price': sl, 'exit_time': idx}
            # Check TP (favorable move)
            if h >= tp:
                pnl = to_pips(tp - entry_price)
                return {'pnl': pnl, 'result': 'W', 'reason': 'tp', 'exit_price': tp, 'exit_time': idx}
        else:  # SHORT
            if h >= sl:
                pnl = to_pips(entry_price - sl)
                return {'pnl': pnl, 'result': 'L', 'reason': 'sl', 'exit_price': sl, 'exit_time': idx}
            if l <= tp:
                pnl = to_pips(entry_price - tp)
                return {'pnl': pnl, 'result': 'W', 'reason': 'tp', 'exit_price': tp, 'exit_time': idx}
    
    # End of data — exit at last close
    last = post_df.iloc[-1]
    c = last['close']
    pnl = to_pips(c - entry_price) * (1 if direction == 'LONG' else -1)
    return {'pnl': pnl, 'result': 'W' if pnl > 0 else 'L',
            'reason': 'end_data', 'exit_price': c, 'exit_time': post_df.index[-1]}


# 
# STRATEGY 1: CFD EXPANSION ENGINE  (Manual target: 85-90% WR)
# 

def run_cfd_expansion(df):
    """
    CFD Expansion Engine — Part 1, Section 3.
    
    CORE LOGIC:
    - P90 candle = Activation Signal for constraint resolution direction
    - Trade IN THE DIRECTION of the P90 candle (not mean reversion)
    - Signal 1 (40%): SL at 80% of P90 body, TP at Asian -25%
    - Signal 2 (40%): SL at 150% of P90 body, TP at Asian -25%
    - Signal 3 (20%): After 45min + 8p extension, SL at breakeven, TP at Asian -50%
    
    The "-25%" and "-50%" in the manual refer to the constraint deficit
    expanding BEYOND the Asian Range in the P90 direction.
    For a LONG P90: TP = Asian_High + (AR * 0.25) and TP = Asian_High + (AR * 0.50)
    For a SHORT P90: TP = Asian_Low - (AR * 0.25) and TP = Asian_Low - (AR * 0.50)
    
    Kill switch: 132% of Asian Range from Asian extreme in trade direction.
    Hard exit: 12PM EST.
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        
        if ar is None or ar > 45 or ar < 3:
            continue
        
        # Entry window: 2-11 AM EST
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        direction, p90, p90_idx = find_first_p90_signal(entry)
        
        if direction is None:
            continue
        
        entry_price = p90['close']
        body_pips = to_pips(abs(p90['close'] - p90['open']))
        
        # TP targets: expansion beyond Asian Range in P90 direction
        # TP1 = Asian boundary + 25% of AR (in trade direction)
        # TP2 = Asian boundary + 50% of AR (in trade direction)
        if direction == 'LONG':
            tp1 = ah + to_price(ar * 0.25)
            tp2 = ah + to_price(ar * 0.50)
            # Kill switch: 132% above Asian high
            kill = ah + to_price(ar * 1.32)
        else:
            tp1 = al - to_price(ar * 0.25)
            tp2 = al - to_price(ar * 0.50)
            kill = al - to_price(ar * 1.32)
        
        # Signal 1: SL at 80% of P90 body
        sl1 = entry_price - to_price(body_pips * 0.80) * (1 if direction == 'LONG' else -1)
        
        # Signal 2: SL at 150% of P90 body
        sl2 = entry_price - to_price(body_pips * 1.50) * (1 if direction == 'LONG' else -1)
        
        # Use the wider SL (Signal 2) for more realistic backtest
        # Actually, per manual: Signal 1 uses 80%, Signal 2 uses 150%
        # We'll use the average weighted by size
        sl_avg = (sl1 * 0.4 + sl2 * 0.4) / 0.8
        
        # Manage trade with TP2 as target
        post = day[(day.index > p90_idx) & (day['est_h'] < 17)]
        
        # Check for kill switch
        trade = manage_trade_with_kill(post, entry_price, direction, sl_avg, tp1, tp2, kill)
        if trade:
            trade['entry_time'] = p90_idx
            trade['ar_pips'] = ar
            trade['direction'] = direction
            trade['body_pips'] = body_pips
            trade['tier'] = classify_tier(ar)
            trades.append(trade)
    
    return day_results(trades, "CFD_Expansion")


def manage_trade_with_kill(post_df, entry_price, direction, sl, tp1, tp2, kill):
    """Manage trade with TP1 partial close, TP2, SL, kill switch, and hard exit."""
    if len(post_df) == 0:
        return None
    
    position_open = True
    hit_tp1 = False
    
    for idx, row in post_df.iterrows():
        h, l, c = row['high'], row['low'], row['close']
        
        # Hard exit at 12PM EST
        if row['est_h'] >= 17:
            pnl = to_pips(c - entry_price) * (1 if direction == 'LONG' else -1)
            return {'pnl': pnl, 'result': 'W' if pnl > 0 else 'L',
                    'reason': 'hard_exit_12pm', 'exit_price': c, 'exit_time': idx}
        
        # Kill switch check
        if direction == 'LONG' and h >= kill:
            pnl = to_pips(kill - entry_price) * (1 if direction == 'LONG' else -1)
            return {'pnl': pnl, 'result': 'L', 'reason': 'kill_switch_132',
                    'exit_price': kill, 'exit_time': idx}
        elif direction == 'SHORT' and l <= kill:
            pnl = to_pips(entry_price - kill) * (1 if direction == 'LONG' else -1)
            return {'pnl': pnl, 'result': 'L', 'reason': 'kill_switch_132',
                    'exit_price': kill, 'exit_time': idx}
        
        if direction == 'LONG':
            # Check SL
            if l <= sl:
                pnl = to_pips(sl - entry_price)
                return {'pnl': pnl, 'result': 'L', 'reason': 'sl',
                        'exit_price': sl, 'exit_time': idx}
            # Check TP1 — close 50%, move SL to breakeven
            if not hit_tp1 and h >= tp1:
                hit_tp1 = True
                sl = entry_price  # Move to breakeven
            # Check TP2 — close remaining
            if h >= tp2:
                pnl = to_pips(tp2 - entry_price)
                return {'pnl': pnl, 'result': 'W', 'reason': 'tp',
                        'exit_price': tp2, 'exit_time': idx}
        else:  # SHORT
            if h >= sl:
                pnl = to_pips(entry_price - sl)
                return {'pnl': pnl, 'result': 'L', 'reason': 'sl',
                        'exit_price': sl, 'exit_time': idx}
            if not hit_tp1 and l <= tp1:
                hit_tp1 = True
                sl = entry_price
            if l <= tp2:
                pnl = to_pips(entry_price - tp2)
                return {'pnl': pnl, 'result': 'W', 'reason': 'tp',
                        'exit_price': tp2, 'exit_time': idx}
    
    # End of data
    last = post_df.iloc[-1]
    c = last['close']
    pnl = to_pips(c - entry_price) * (1 if direction == 'LONG' else -1)
    return {'pnl': pnl, 'result': 'W' if pnl > 0 else 'L',
            'reason': 'end_data', 'exit_price': c, 'exit_time': post_df.index[-1]}


# 
# STRATEGY 2: P90 CASCADE ACTIVATION  (Manual target: 87.8% WR for 2nd cascade)
# 

def run_p90_cascade(df):
    """
    P90 Cascade Activation — Part 2.
    
    CASCADE LOGIC:
    1. Initial P90 sets direction of constraint resolution
    2. Subsequent P90s in SAME direction = valid cascade activations
    3. Max 3 cascades per session (4th+ = AVOID)
    4. Cascade window: 30-90 min from initial P90 (optimal: 45-60 min)
    5. Initial P90: SL at 80% of body
    6. Cascade P90s: SL at 168% of THIS P90 body (wider)
    7. All positions target: Asian -50% expansion
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        
        if ar is None or ar > 45 or ar < 3:
            continue
        
        # Find all P90 signals in 2-11 AM EST
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        all_signals = find_p90_signals(entry)
        
        if len(all_signals) == 0:
            continue
        
        # Initial P90 sets direction
        init_dir, init_p90, init_idx = all_signals[0]
        resolution_direction = init_dir
        
        # Process each activation
        activations = []
        
        # Signal 1: Initial P90
        body_pips = to_pips(abs(init_p90['close'] - init_p90['open']))
        ep = init_p90['close']
        sl = ep - to_price(body_pips * 0.80) * (1 if init_dir == 'LONG' else -1)
        
        if init_dir == 'LONG':
            tp = ah + to_price(ar * 0.50)
        else:
            tp = al - to_price(ar * 0.50)
        
        activations.append({
            'direction': init_dir, 'entry_price': ep, 'sl': sl, 'tp': tp,
            'entry_time': init_idx, 'type': 'initial', 'size': 0.4
        })
        
        # Cascade P90s: subsequent same-direction P90s within 30-90 min
        cascade_count = 0
        init_ts = init_idx
        
        for sig_dir, sig_row, sig_idx in all_signals[1:]:
            if cascade_count >= 3:
                break
            
            # Must be same direction
            if sig_dir != resolution_direction:
                continue
            
            # Time check: 30-90 min from initial
            time_diff = (sig_idx - init_ts).total_seconds() / 60.0
            if time_diff < 30 or time_diff > 90:
                continue
            
            cascade_count += 1
            sig_body = to_pips(abs(sig_row['close'] - sig_row['open']))
            sig_ep = sig_row['close']
            # Cascade SL: 168% of THIS P90 body
            sig_sl = sig_ep - to_price(sig_body * 1.68) * (1 if sig_dir == 'LONG' else -1)
            
            if sig_dir == 'LONG':
                sig_tp = ah + to_price(ar * 0.50)
            else:
                sig_tp = al - to_price(ar * 0.50)
            
            size = 0.2 if cascade_count == 1 else 0.1  # 20% for 2nd, 10% for 3rd
            
            activations.append({
                'direction': sig_dir, 'entry_price': sig_ep, 'sl': sig_sl, 'tp': sig_tp,
                'entry_time': sig_idx, 'type': f'cascade_{cascade_count}', 'size': size
            })
        
        # Manage each activation independently
        for act in activations:
            post = day[(day.index > act['entry_time']) & (day['est_h'] < 17)]
            trade = manage_trade(post, act['entry_price'], act['direction'], act['sl'], act['tp'])
            if trade:
                trade['entry_time'] = act['entry_time']
                trade['ar_pips'] = ar
                trade['direction'] = act['direction']
                trade['activation_type'] = act['type']
                trade['size'] = act['size']
                trade['tier'] = classify_tier(ar)
                trades.append(trade)
    
    return day_results(trades, "P90_Cascade")


# 
# STRATEGY 3: CASCADE + 45-MIN ADD COMBO  (Manual target: 93.4% WR)
# 

def run_cascade_combo(df):
    """
    Cascade + 45-Min Add Combo — Part 2, Section 5.
    
    HIGHEST CONVICTION strategy: Combined Win Rate = 93.4%
    
    When BOTH cascade and 45-min add trigger:
      Signal 1: Initial P90 (40%) | SL: 80% body | TP: Asian -50%
      Signal 2: 45-Min Add (30%) | SL: Breakeven | TP: Asian -50%
      Signal 3: Cascade P90 (20%) | SL: 168% body | TP: Asian -50%
      Signal 4: Cascade 2 (10%) | SL: 168% body | TP: Asian -50%
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        
        if ar is None or ar > 45 or ar < 3:
            continue
        
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        all_signals = find_p90_signals(entry)
        
        if len(all_signals) == 0:
            continue
        
        init_dir, init_p90, init_idx = all_signals[0]
        init_ts = init_idx
        init_ep = init_p90['close']
        init_body = to_pips(abs(init_p90['close'] - init_p90['open']))
        
        if init_dir == 'LONG':
            tp = ah + to_price(ar * 0.50)
        else:
            tp = al - to_price(ar * 0.50)
        
        activations = []
        
        # Signal 1: Initial P90 (40%)
        sl1 = init_ep - to_price(init_body * 0.80) * (1 if init_dir == 'LONG' else -1)
        activations.append({
            'direction': init_dir, 'entry_price': init_ep, 'sl': sl1, 'tp': tp,
            'entry_time': init_idx, 'type': 'initial_p90', 'size': 0.4
        })
        
        # Signal 2: 45-Min Add Check
        add_45_triggered = False
        add_45_time = init_idx + timedelta(minutes=45)
        add_45_bar = day[(day.index >= add_45_time) & (day['est_h'] < 11)]
        
        if len(add_45_bar) > 0:
            # Check if resolution output extended +8 pips from entry
            if init_dir == 'LONG':
                max_since_entry = add_45_bar['high'].max()
                if to_pips(max_since_entry - init_ep) >= 8.0:
                    add_45_triggered = True
            else:
                min_since_entry = add_45_bar['low'].min()
                if to_pips(init_ep - min_since_entry) >= 8.0:
                    add_45_triggered = True
        
        if add_45_triggered:
            # 45-Min Add (30%): SL at breakeven
            activations.append({
                'direction': init_dir, 'entry_price': init_ep, 'sl': init_ep, 'tp': tp,
                'entry_time': add_45_time, 'type': 'add_45min', 'size': 0.3
            })
        
        # Signal 3+: Cascade P90s
        cascade_count = 0
        for sig_dir, sig_row, sig_idx in all_signals[1:]:
            if cascade_count >= 2:
                break
            if sig_dir != init_dir:
                continue
            time_diff = (sig_idx - init_ts).total_seconds() / 60.0
            if time_diff < 30 or time_diff > 90:
                continue
            
            cascade_count += 1
            sig_body = to_pips(abs(sig_row['close'] - sig_row['open']))
            sig_ep = sig_row['close']
            sig_sl = sig_ep - to_price(sig_body * 1.68) * (1 if sig_dir == 'LONG' else -1)
            
            activations.append({
                'direction': sig_dir, 'entry_price': sig_ep, 'sl': sig_sl, 'tp': tp,
                'entry_time': sig_idx, 'type': f'cascade_{cascade_count}', 'size': 0.2 if cascade_count == 1 else 0.1
            })
        
        # Manage each activation
        for act in activations:
            post = day[(day.index > act['entry_time']) & (day['est_h'] < 17)]
            trade = manage_trade(post, act['entry_price'], act['direction'], act['sl'], act['tp'])
            if trade:
                trade['entry_time'] = act['entry_time']
                trade['ar_pips'] = ar
                trade['direction'] = act['direction']
                trade['activation_type'] = act['type']
                trade['size'] = act['size']
                trade['tier'] = classify_tier(ar)
                trades.append(trade)
    
    return day_results(trades, "Cascade_Combo_45min")


# 
# STRATEGY 4: DEEP MEAN REBALANCING  (Manual target: 74-84% WR)
# 

def run_deep_mean_reversion(df):
    """
    Deep Mean Rebalancing — Part 1, Section 4.
    
    COUNTER-TRADE at deep extension levels:
    - Trigger: Price reaches 168% (Stall Zone) or 200% (Deep State) of P90 body
    - Direction: AGAINST the P90 move (mean reversion)
    - Entry: At 200% level
    - SL: 8 pips beyond 200% (~220%)
    - TP1: Return to P90 activation level (0% reversion)
    - TP2: Asian -50% in the reversion direction
    - Must occur before 12PM EST
    - Filter: Asian -50% target NOT yet hit
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        
        if ar is None or ar > 45 or ar < 3:
            continue
        
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        direction, p90, p90_idx = find_first_p90_signal(entry)
        
        if direction is None:
            continue
        
        activation = p90['close']
        body_pips = to_pips(abs(p90['close'] - p90['open']))
        
        # Calculate extension levels from activation in P90 direction
        if direction == 'LONG':
            stall_zone = activation + to_price(body_pips * 1.68)
            deep_state = activation + to_price(body_pips * 2.00)
            kill_sw = activation + to_price(body_pips * 2.20)
        else:
            stall_zone = activation - to_price(body_pips * 1.68)
            deep_state = activation - to_price(body_pips * 2.00)
            kill_sw = activation - to_price(body_pips * 2.20)
        
        # Look for price reaching deep state after P90
        p90_time = p90_idx
        post_p90 = day[(day.index > p90_time) & (day['est_h'] < 17)]
        
        touched = False
        touch_idx = None
        for idx, row in post_p90.iterrows():
            if direction == 'LONG' and row['high'] >= deep_state:
                touched = True
                touch_idx = idx
                break
            elif direction == 'SHORT' and row['low'] <= deep_state:
                touched = True
                touch_idx = idx
                break
        
        if not touched:
            continue
        
        # Mean reversion: trade AGAINST the move
        rev_direction = 'SHORT' if direction == 'LONG' else 'LONG'
        rev_entry = deep_state
        rev_sl = kill_sw
        rev_tp = activation  # Return to 0% (P90 activation level)
        
        # Manage the reversion trade
        post_entry = post_p90[(post_p90.index > touch_idx)]
        
        trade = manage_trade(post_entry, rev_entry, rev_direction, rev_sl, rev_tp)
        if trade:
            trade['entry_time'] = touch_idx
            trade['ar_pips'] = ar
            trade['direction'] = rev_direction
            trade['tier'] = classify_tier(ar)
            trades.append(trade)
    
    return day_results(trades, "Deep_Mean_Reversion")


# 
# STRATEGY 5: STALL-HARVEST CFD LEG  (Manual target: 86% WR)
# 

def run_stall_harvest_cfd(df):
    """
    Stall-Harvest CFD Leg — Part 4.
    
    1. Find P90 signal in 2-11 AM EST
    2. Wait for price to reach 168% Stall Zone (in P90 direction)
    3. Enter IN P90 DIRECTION at 168% level
    4. SL at 200% + 1.5x body buffer
    5. TP: Asian -50% expansion from entry
    6. Abort if candle closes beyond 200%
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        
        if ar is None or ar > 45 or ar < 3:
            continue
        
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        direction, p90, p90_idx = find_first_p90_signal(entry)
        
        if direction is None:
            continue
        
        activation = p90['close']
        body_pips = to_pips(abs(p90['close'] - p90['open']))
        
        # 168% Stall Zone in P90 direction
        stall = activation + to_price(body_pips * 1.68) * (1 if direction == 'LONG' else -1)
        # 200% Deep State
        deep = activation + to_price(body_pips * 2.00) * (1 if direction == 'LONG' else -1)
        # SL: 200% + 1.5x body buffer beyond 168%
        sl_level = activation + to_price(body_pips * (2.00 + 1.5)) * (1 if direction == 'LONG' else -1)
        
        p90_time = p90_idx
        post_p90 = day[(day.index > p90_time) & (day['est_h'] < 17)]
        
        entered = False
        entry_idx = None
        for idx, row in post_p90.iterrows():
            # Violation filter: abort if candle closes beyond 200%
            if direction == 'LONG' and row['close'] > deep:
                break
            if direction == 'SHORT' and row['close'] < deep:
                break
            
            if direction == 'LONG' and row['high'] >= stall:
                entered = True
                entry_idx = idx
                break
            elif direction == 'SHORT' and row['low'] <= stall:
                entered = True
                entry_idx = idx
                break
        
        if not entered:
            continue
        
        # TP: Asian -50% expansion from entry level
        if direction == 'LONG':
            tp_level = ah + to_price(ar * 0.50)
        else:
            tp_level = al - to_price(ar * 0.50)
        
        post_entry = post_p90[(post_p90.index > entry_idx)]
        trade = manage_trade(post_entry, stall, direction, sl_level, tp_level)
        if trade:
            trade['entry_time'] = entry_idx
            trade['ar_pips'] = ar
            trade['direction'] = direction
            trade['tier'] = classify_tier(ar)
            trades.append(trade)
    
    return day_results(trades, "Stall_Harvest_CFD")


# 
# STRATEGY 6: CONSTRAINT ANCHOR  (Manual target: 91.7% WR, +1.42R)
# 

def run_constraint_anchor(df):
    """
    Constraint Anchor — Part 10, Section 1.
    
    Structural activation at Asian constraint band violation.
    - AR < 30 pips (T1 or T2 only)
    - Time: 3AM-12PM EST
    - M5 candle CLOSES outside Asian High/Low, body >= 4.6 pips
    - Direction: IN THE DIRECTION OF THE BREAKOUT (not mean reversion)
    - SL: Opposite Asian extreme
    - TP: Asian boundary + 50% AR expansion
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
            
            # LONG: Close > Asian High (breakout above)
            if row['close'] > ah:
                direction = 'LONG'
                ep = row['close']
                sl = al  # Opposite Asian extreme
                tp = ah + to_price(ar * 0.50)  # Expansion target
                activated = True
                break
            # SHORT: Close < Asian Low (breakout below)
            elif row['close'] < al:
                direction = 'SHORT'
                ep = row['close']
                sl = ah
                tp = al - to_price(ar * 0.50)
                activated = True
                break
        
        if not activated:
            continue
        
        post = day[(day.index > idx) & (day['est_h'] < 17)]
        trade = manage_trade(post, ep, direction, sl, tp)
        if trade:
            trade['entry_time'] = idx
            trade['ar_pips'] = ar
            trade['direction'] = direction
            trade['tier'] = classify_tier(ar)
            trades.append(trade)
    
    return day_results(trades, "Constraint_Anchor")


# 
# STRATEGY 7: MONDAY ASIAN FLOAT  (Manual target: 29.5% 24h float rate)
# 

def run_monday_asian_float(df):
    """
    Monday Asian Float — Part 7.
    
    Pattern: Monday Asian Range acts as weekly constraint boundary.
    - After Monday Asian closes (3AM EST Tue), price breaks out
    - 24h float rate: 29.5% (Tue full day stays outside Mon range)
    - Strategy: When Monday AR is T1/T2, enter breakout after 3AM EST on Tuesday
    - Direction: IN THE DIRECTION OF THE BREAKOUT
    - SL: Opposite Monday Asian extreme
    - TP: Monday AR * 3.0 (conservative weekly target)
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        
        # Only trade on Tuesday (weekday=1)
        if len(day) == 0:
            continue
        if day.index[0].dayofweek != 1:
            continue
        
        # Get Monday's Asian Range
        monday_date = date - timedelta(days=1)
        monday = df[df['date'] == monday_date]
        
        if len(monday) < 10:
            continue
        
        ah, al, ar = calc_asian_range(monday)
        
        if ar is None or ar > 45 or ar < 3:
            continue
        
        # Enter breakout: if price moves outside Monday's Asian range
        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 17)]
        
        for idx, row in entry.iterrows():
            if row['close'] > ah:
                direction = 'LONG'
                ep = row['close']
                sl = al
                tp = ah + to_price(ar * 3.0)
                break
            elif row['close'] < al:
                direction = 'SHORT'
                ep = row['close']
                sl = ah
                tp = al - to_price(ar * 3.0)
                break
        else:
            continue
        
        post = day[(day.index > idx) & (day['est_h'] < 17)]
        trade = manage_trade(post, ep, direction, sl, tp)
        if trade:
            trade['entry_time'] = idx
            trade['ar_pips'] = ar
            trade['direction'] = direction
            trades.append(trade)
    
    return day_results(trades, "Monday_Asian_Float")


# 
# STRATEGY 8: DAILY ASIAN FLOAT (Run-and-Retest)  (Manual target: 18.8% float)
# 

def run_daily_asian_float(df):
    """
    Daily Asian Float — Part 8.
    
    Pattern: London open breaks Asian constraint band, shallow partial
    rebalancing holds, constraint deficit resolved.
    
    - 18.8% of days: price never re-enters Asian band (broad float)
    - After run-and-retest: 56.4p mean continuation
    
    Strategy: Enter when price breaks Asian band with shallow pullback (<=38% AR).
    Direction: CONTINUATION in breakout direction.
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        
        if ar is None or ar > 45 or ar < 3:
            continue
        
        # Look for breakout after Asian session (3AM EST)
        entry = day[(day['est_h'] >= 3) & (day['est_h'] < 12)]
        
        breakout_dir = None
        breakout_idx = None
        breakout_price = None
        
        for idx, row in entry.iterrows():
            if row['close'] > ah:
                breakout_dir = 'LONG'
                breakout_idx = idx
                breakout_price = row['close']
                break
            elif row['close'] < al:
                breakout_dir = 'SHORT'
                breakout_idx = idx
                breakout_price = row['close']
                break
        
        if breakout_dir is None:
            continue
        
        # Check for shallow pullback (<=38% of AR)
        post_breakout = day[(day.index > breakout_idx) & (day['est_h'] < 12)]
        
        pullback_ok = True
        for idx, row in post_breakout.iterrows():
            if breakout_dir == 'LONG':
                retrace = to_pips(breakout_price - row['low'])
                if retrace > ar * 0.38:
                    pullback_ok = False
                    break
                if row['low'] <= ah:
                    pullback_ok = False
                    break
            else:
                retrace = to_pips(row['high'] - breakout_price)
                if retrace > ar * 0.38:
                    pullback_ok = False
                    break
                if row['high'] >= al:
                    pullback_ok = False
                    break
        
        if not pullback_ok:
            continue
        
        # Enter continuation after shallow pullback
        ep = breakout_price
        sl = al if breakout_dir == 'LONG' else ah
        tp = ep + to_price(ar * 0.56) * (1 if breakout_dir == 'LONG' else -1)
        
        post = day[(day.index > breakout_idx) & (day['est_h'] < 17)]
        trade = manage_trade(post, ep, breakout_dir, sl, tp)
        if trade:
            trade['entry_time'] = breakout_idx
            trade['ar_pips'] = ar
            trade['direction'] = breakout_dir
            trades.append(trade)
    
    return day_results(trades, "Daily_Asian_Float")


# 
# STRATEGY 9: RESOLUTION AMPLIFIER  (Manual target: 82.4% WR, +2.64R)
# 

def run_resolution_amplifier(df):
    """
    Resolution Amplifier — Part 10, Section 2.
    
    Path Exploitation after constraint resolution confirmed.
    - Trigger: After Asian -25% target hit, price continues in resolution direction
    - Entry: On shallow pullback to Asian boundary
    - Direction: Same as resolution direction
    - SL: Beyond the -25% level (invalidation of continuation)
    - TP: Daily -50% expansion
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        
        if ar is None or ar > 45 or ar < 3:
            continue
        
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        direction, p90, p90_idx = find_first_p90_signal(entry)
        
        if direction is None:
            continue
        
        # Calculate -25% level
        if direction == 'LONG':
            level_25 = ah + to_price(ar * 0.25)
            level_50 = ah + to_price(ar * 0.50)
        else:
            level_25 = al - to_price(ar * 0.25)
            level_50 = al - to_price(ar * 0.50)
        
        # Check if -25% was hit
        post_p90 = day[(day.index > p90_idx) & (day['est_h'] < 12)]
        
        hit_25 = False
        for idx, row in post_p90.iterrows():
            if direction == 'LONG' and row['high'] >= level_25:
                hit_25 = True
                break
            elif direction == 'SHORT' and row['low'] <= level_25:
                hit_25 = True
                break
        
        if not hit_25:
            continue
        
        # Look for pullback to Asian boundary (entry point)
        post_25 = day[(day.index > idx) & (day['est_h'] < 12)]
        
        entered = False
        for idx2, row2 in post_25.iterrows():
            if direction == 'LONG' and row2['low'] <= ah:
                # Pullback to Asian high — enter continuation
                ep = ah
                sl = ah - to_price(ar * 0.10)  # SL just below Asian high
                tp = level_50
                entered = True
                break
            elif direction == 'SHORT' and row2['high'] >= al:
                ep = al
                sl = al + to_price(ar * 0.10)
                tp = level_50
                entered = True
                break
        
        if not entered:
            continue
        
        post_entry = day[(day.index > idx2) & (day['est_h'] < 17)]
        trade = manage_trade(post_entry, ep, direction, sl, tp)
        if trade:
            trade['entry_time'] = idx2
            trade['ar_pips'] = ar
            trade['direction'] = direction
            trades.append(trade)
    
    return day_results(trades, "Resolution_Amplifier")


# 
# STRATEGY 10: FULL-DAY RANGE REGIME TRACKER  (Manual target: 79.8% overall)
# 

def run_full_day_regime(df):
    """
    Full-Day Range Regime Tracker — Part 9.
    
    Tracks daily range expansion relative to Asian Range.
    - Regime ratio = Current Daily Range / Asian Range
    - If ratio >= 1.5 by 8:45 AM: Expansion confirmed (hold runners)
    - If ratio < 1.5: Compression (take profits early)
    - T2 accuracy: 86%
    
    Strategy: Enter on P90, use regime to determine target trimming.
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        
        if ar is None or ar > 45 or ar < 3:
            continue
        
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        direction, p90, p90_idx = find_first_p90_signal(entry)
        
        if direction is None:
            continue
        
        ep = p90['close']
        body_pips = to_pips(abs(p90['close'] - p90['open']))
        
        # Check regime at 8:45 AM EST
        regime_time = day[day['est_h'] == 8]
        if len(regime_time) > 0:
            # Find bar closest to 8:45
            current_range = to_pips(day[day['est_h'] <= 8]['high'].max() - day[day['est_h'] <= 8]['low'].min())
            regime_ratio = current_range / ar if ar > 0 else 0
        else:
            regime_ratio = 1.0  # Default
        
        # SL: 80% of body
        sl = ep - to_price(body_pips * 0.80) * (1 if direction == 'LONG' else -1)
        
        # TP based on regime
        if regime_ratio >= 1.5:
            # Expansion confirmed — target Daily -50%
            if direction == 'LONG':
                tp = ah + to_price(ar * 0.50)
            else:
                tp = al - to_price(ar * 0.50)
        else:
            # Compression — target Asian -25%
            if direction == 'LONG':
                tp = ah + to_price(ar * 0.25)
            else:
                tp = al - to_price(ar * 0.25)
        
        post = day[(day.index > p90_idx) & (day['est_h'] < 17)]
        trade = manage_trade(post, ep, direction, sl, tp)
        if trade:
            trade['entry_time'] = p90_idx
            trade['ar_pips'] = ar
            trade['direction'] = direction
            trade['regime_ratio'] = round(regime_ratio, 2)
            trades.append(trade)
    
    return day_results(trades, "Full_Day_Regime")


# 
# MAIN RUNNER
# 

def main():
    print("=" * 70)
    print(" CEREBUS FX v4 — Strategy Backtest Engine v2")
    print("=" * 70)
    
    df = load_eurusd_m5()
    if df is None:
        return
    
    print(f"\n Data: {len(df):,} bars | {df.index[0].date()} → {df.index[-1].date()}")
    
    strategies = [
        ("CFD_Expansion",        run_cfd_expansion,        "85-90% WR"),
        ("P90_Cascade",          run_p90_cascade,          "87.8% WR (2nd)"),
        ("Cascade_Combo_45min",  run_cascade_combo,        "93.4% WR"),
        ("Deep_Mean_Reversion",  run_deep_mean_reversion,  "74-84% WR"),
        ("Stall_Harvest_CFD",    run_stall_harvest_cfd,    "86% WR"),
        ("Constraint_Anchor",    run_constraint_anchor,    "91.7% WR"),
        ("Monday_Asian_Float",   run_monday_asian_float,   "29.5% 24h float"),
        ("Daily_Asian_Float",    run_daily_asian_float,    "18.8% broad float"),
        ("Resolution_Amplifier", run_resolution_amplifier, "82.4% WR"),
        ("Full_Day_Regime",      run_full_day_regime,      "79.8% overall"),
    ]
    
    all_results = {}
    
    for name, fn, target in strategies:
        print(f"\n{''*60}")
        print(f" {name} (target: {target})")
        t0 = time.time()
        try:
            r = fn(df)
            elapsed = time.time() - t0
            all_results[name] = r
            if r.get('total_trades', 0) > 0:
                print(f"   {r['total_trades']} trades | WR: {r['win_rate']}% | "
                      f"P&L: {r['total_pnl']}p | PF: {r['profit_factor']} | "
                      f"MaxDD: {r['max_dd']}p | Exp: {r['expectancy']}p")
                if r.get('by_exit'):
                    print(f"     Exits: {r['by_exit']}")
            else:
                print(f"   No trades ({elapsed:.1f}s)")
        except Exception as e:
            elapsed = time.time() - t0
            print(f"   {e} ({elapsed:.1f}s)")
            import traceback
            traceback.print_exc()
            all_results[name] = {"strategy": name, "error": str(e), "total_trades": 0}
    
    # Summary
    print(f"\n{'='*70}")
    print(f" COMPARATIVE RESULTS")
    print(f"{'='*70}")
    print(f"{'Strategy':<25} {'Trades':>6} {'WR%':>6} {'P&L(p)':>8} {'PF':>5} {'MaxDD':>7} {'Target':<18}")
    print(f"{''*70}")
    
    for name, fn, target in strategies:
        r = all_results.get(name, {})
        if r.get('total_trades', 0) > 0:
            print(f"{name:<25} {r['total_trades']:>6} {r['win_rate']:>6.1f} "
                  f"{r['total_pnl']:>8.1f} {r['profit_factor']:>5.2f} "
                  f"{r['max_dd']:>7.1f} {target:<18}")
        else:
            print(f"{name:<25} {'N/A':>6} {'N/A':>6} {'N/A':>8} {'N/A':>5} {'N/A':>7} {target:<18}")
    
    # Save results
    results_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results")
    results_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rf = results_dir / f"cerabus_v2_{ts}.json"
    with open(rf, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n Saved to {rf}")
    
    return all_results


if __name__ == "__main__":
    main()
