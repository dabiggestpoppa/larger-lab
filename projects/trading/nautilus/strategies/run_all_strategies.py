"""
Unified CEREBUS Strategy Backtest Runner
=========================================
Runs all extracted CEREBUS strategies against EUR/USD M5 data.
Standalone backtest engine using pandas for speed and clarity.
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# Will be set after loading data
DATA = None

# ── Data Loading ─────────────────────────────────────────────────────────────

def load_eurusd_m5():
    """Load EUR/USD M5 data from Downloads."""
    data_path = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")
    
    if not data_path.exists():
        print(f"❌ Data file not found: {data_path}")
        return None
    
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
            vol = int(parts[6])
            records.append({'open': o, 'high': h, 'low': l, 'close': c, 'volume': vol, 'ts': ts})
        except (ValueError, IndexError):
            continue
    
    df = pd.DataFrame(records)
    df.set_index('ts', inplace=True)
    df.sort_index(inplace=True)
    
    print(f"  ✅ Loaded {len(df):,} bars ({df.index[0]} → {df.index[-1]})")
    return df


# ── Utility Functions ────────────────────────────────────────────────────────

def to_pips(price_diff, pair="EUR/USD"):
    if "JPY" in pair: return price_diff * 100.0
    if "XAU" in pair: return price_diff * 10.0
    return price_diff * 10000.0

def to_price(pips, pair="EUR/USD"):
    if "JPY" in pair: return pips / 100.0
    if "XAU" in pair: return pips / 10.0
    return pips / 10000.0

def day_results(trades, name, pair="EUR/USD"):
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
    
    return {
        "strategy": name, "pair": pair,
        "total_trades": len(trades), "wins": len(wins), "losses": len(losses),
        "win_rate": round(wr, 1), "total_pnl": round(total, 2),
        "avg_win": round(avg_w, 2), "avg_loss": round(avg_l, 2),
        "max_dd": round(max_dd, 2), "profit_factor": round(pf, 2),
        "expectancy": round(total / len(pnls), 3),
        "by_exit": count_by_key(trades, 'reason'),
    }

def count_by_key(items, key):
    d = {}
    for item in items:
        k = item.get(key, 'unknown')
        d[k] = d.get(k, 0) + 1
    return d


# ═══════════════════════════════════════════════════════════════════════════════
# CORE BACKTEST ENGINE — processes one day at a time
# ═══════════════════════════════════════════════════════════════════════════════

def prepare_data(df):
    """Add computed columns to the dataframe."""
    df = df.copy()
    df['utc_h'] = df.index.hour
    df['est_h'] = (df['utc_h'] - 5 + 24) % 24
    df['date'] = df.index.date
    df['body_pips'] = to_pips((df['close'] - df['open']).abs())
    return df

def get_day_data(df, date):
    """Get data for a specific date."""
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

def find_p90_signal(entry_df):
    """Find the first P90 signal in entry window data. Returns (direction, row) or (None, None)."""
    for idx, row in entry_df.iterrows():
        thresh = p90_threshold(row['est_h'])
        if row['body_pips'] >= thresh:
            direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
            return direction, row
    return None, None

def manage_trade(post_df, entry_price, direction, sl, tp, hard_exit_est=17):
    """Manage a single trade through subsequent bars. Returns trade dict or None."""
    for idx, row in post_df.iterrows():
        h, l, c = row['high'], row['low'], row['close']
        
        # Hard exit
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
    
    # End of data — exit at last close
    last = post_df.iloc[-1]
    c = last['close']
    pnl = to_pips(c - entry_price) * (1 if direction == 'LONG' else -1)
    return {'pnl': pnl, 'result': 'W' if pnl > 0 else 'L',
            'reason': 'end_data', 'exit_price': c, 'exit_time': post_df.index[-1]}


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 1: CFD EXPANSION ENGINE  (Manual target: 85-90% WR)
# ═══════════════════════════════════════════════════════════════════════════════

def run_cfd_expansion(df):
    """
    CFD Expansion Engine — Part 1.
    
    P90 candle triggers mean reversion trade:
    - Direction: LONG if bullish P90, SHORT if bearish P90
    - SL: weighted avg of 80% body (40%) and 1.5x body (40%)
    - TP: +25% AR and +50% AR (expansion, NOT mean reversion — the P90 candle
      indicates the direction of constraint resolution, and the trade rides
      the expansion of the constraint deficit)
    - Kill switch: 132% of Asian Range from Asian extreme
    - Hard exit: 12PM EST
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
        direction, p90 = find_p90_signal(entry)
        
        if direction is None:
            continue
        
        entry_price = p90['close']
        entry_time = p90.name
        body_pips = to_pips(abs(p90['close'] - p90['open']))
        
        # SL: weighted average of Signal 1 (80% body) and Signal 2 (150% body)
        sl1_pips = body_pips * 0.80
        sl2_pips = body_pips * 1.50
        avg_sl = (sl1_pips * 0.4 + sl2_pips * 0.4) / 0.8  # 80% total size
        
        # TP1 = +25% AR, TP2 = +50% AR (expansion direction, same as P90)
        tp1 = entry_price + to_price(ar * 0.25) * (1 if direction == 'LONG' else -1)
        tp2 = entry_price + to_price(ar * 0.50) * (1 if direction == 'LONG' else -1)
        sl = entry_price - to_price(avg_sl) * (1 if direction == 'LONG' else -1)
        
        # Kill switch: 132% AR from Asian extreme
        kill = (ah + to_price(ar * 1.32)) if direction == 'LONG' else (al - to_price(ar * 1.32))
        
        # Manage trade
        post = day[(day.index > entry_time) & (day['est_h'] < 17)]
        
        trade = manage_trade(post, entry_price, direction, sl, tp2)
        if trade:
            trade['entry_time'] = entry_time
            trade['ar_pips'] = ar
            trade['direction'] = direction
            trades.append(trade)
    
    return day_results(trades, "CFD_Expansion")


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 2: DEEP MEAN REBALANCING  (Manual target: 74-84% WR)
# ═══════════════════════════════════════════════════════════════════════════════

def run_deep_mean_reversion(df):
    """
    Deep Mean Rebalancing — Part 1, Section 4.
    
    When price reaches 168% (Stall Zone) or 200% (Deep State) of P90 body:
    - Enter mean reversion at 200% level
    - Direction: AGAINST the move (reversion to P90 level)
    - SL: 8 pips beyond 200% (~220%)
    - TP1: Return to P90 activation level (0%)
    - TP2: -50% Daily Range from activation
    """
    df = prepare_data(df)
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        
        if ar is None or ar > 45 or ar < 3:
            continue
        
        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        direction, p90 = find_p90_signal(entry)
        
        if direction is None:
            continue
        
        activation = p90['close']
        body_pips = to_pips(abs(p90['close'] - p90['open']))
        
        # Calculate 168% and 200% extension levels
        stall_zone = activation + to_price(body_pips * 1.68) * (1 if direction == 'LONG' else -1)
        deep_state = activation + to_price(body_pips * 2.00) * (1 if direction == 'LONG' else -1)
        kill_sw = activation + to_price(body_pips * 2.20) * (1 if direction == 'LONG' else -1)
        
        # Look for price reaching deep state after P90
        p90_time = p90.name
        post_p90 = day[(day.index > p90_time) & (day['est_h'] < 17)]
        
        touched = False
        for idx, row in post_p90.iterrows():
            if direction == 'LONG' and row['high'] >= deep_state:
                touched = True
                break
            elif direction == 'SHORT' and row['low'] <= deep_state:
                touched = True
                break
        
        if not touched:
            continue
        
        # Mean reversion: trade AGAINST the move
        rev_direction = 'SHORT' if direction == 'LONG' else 'LONG'
        rev_entry = deep_state
        rev_sl = kill_sw
        rev_tp = activation  # Return to 0%
        
        # Manage the reversion trade
        post_entry = post_p90[(post_p90.index > idx)]
        
        trade = manage_trade(post_entry, rev_entry, rev_direction, rev_sl, rev_tp)
        if trade:
            trade['entry_time'] = idx
            trade['ar_pips'] = ar
            trade['direction'] = rev_direction
            trades.append(trade)
    
    return day_results(trades, "Deep_Mean_Reversion")


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 3: CONSTRAINT ANCHOR  (Manual target: 91.7% WR, +1.42R)
# ═══════════════════════════════════════════════════════════════════════════════

def run_constraint_anchor(df):
    """
    Constraint Anchor — Part 10, Section 1.
    
    Structural activation at Asian constraint band violation.
    - AR < 30 pips (T1 or T2 only)
    - Time: 3AM-12PM EST (8-17 UTC)
    - M5 candle CLOSES outside Asian High/Low, body >= 4.6 pips
    - SL: Opposite Asian extreme
    - TP1: AR × 0.25, TP2: AR × 0.50
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
            
            # LONG: Close > Asian High
            if row['close'] > ah and row['high'] > ah:
                direction = 'LONG'
                ep = row['close']
                sl = al  # Opposite extreme
                tp = ep + to_price(ar * 0.50)
                activated = True
                break
            # SHORT: Close < Asian Low
            elif row['close'] < al and row['low'] < al:
                direction = 'SHORT'
                ep = row['close']
                sl = ah
                tp = ep - to_price(ar * 0.50)
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
            trade['tier'] = 'T1' if ar < 20 else 'T2'
            trades.append(trade)
    
    return day_results(trades, "Constraint_Anchor")


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 4: STALL-HARVEST CFD LEG  (Manual target: 86% WR)
# ═══════════════════════════════════════════════════════════════════════════════

def run_stall_harvest_cfd(df):
    """
    Stall-Harvest CFD Leg — Part 4.
    
    1. Find P90 signal in 2-11 AM EST
    2. Wait for price to reach 168% Stall Zone
    3. Enter in P90 direction at 168% level
    4. SL at 200% + 1.5x body buffer
    5. TP: +50% Daily Range from entry
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
        direction, p90 = find_p90_signal(entry)
        
        if direction is None:
            continue
        
        activation = p90['close']
        body_pips = to_pips(abs(p90['close'] - p90['open']))
        
        # 168% Stall Zone
        stall = activation + to_price(body_pips * 1.68) * (1 if direction == 'LONG' else -1)
        # 200% Deep State
        deep = activation + to_price(body_pips * 2.00) * (1 if direction == 'LONG' else -1)
        # SL: 200% + 1.5x body buffer beyond 168%
        sl_level = activation + to_price(body_pips * (1.68 + 1.5)) * (1 if direction == 'LONG' else -1)
        
        p90_time = p90.name
        post_p90 = day[(day.index > p90_time) & (day['est_h'] < 17)]
        
        entered = False
        for idx, row in post_p90.iterrows():
            # Violation filter: abort if candle closes beyond 200%
            if direction == 'LONG' and row['close'] > deep:
                break
            if direction == 'SHORT' and row['close'] < deep:
                break
            
            if direction == 'LONG' and row['high'] >= stall:
                entered = True
                break
            elif direction == 'SHORT' and row['low'] <= stall:
                entered = True
                break
        
        if not entered:
            continue
        
        # TP: +50% AR from entry
        tp_level = stall + to_price(ar * 0.50) * (1 if direction == 'LONG' else -1)
        
        post_entry = post_p90[(post_p90.index > idx)]
        trade = manage_trade(post_entry, stall, direction, sl_level, tp_level)
        if trade:
            trade['entry_time'] = idx
            trade['ar_pips'] = ar
            trade['direction'] = direction
            trades.append(trade)
    
    return day_results(trades, "Stall_Harvest_CFD")


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 5: MONDAY ASIAN FLOAT  (Manual target: 29.5% 24h float rate)
# ═══════════════════════════════════════════════════════════════════════════════

def run_monday_asian_float(df):
    """
    Monday Asian Float — Part 7.
    
    Pattern: Monday Asian Range acts as weekly constraint boundary.
    - After Monday Asian closes (3AM EST), price breaks out
    - 24h float rate: 29.5% (Tue full day stays outside Mon range)
    - 48h float rate: 21.8% (Tue + Wed full day float)
    
    Strategy: When Monday AR is T1/T2, enter breakout after 3AM EST
    with target of weekly expansion (mean 6.62x AR).
    """
    df = prepare_data(df)
    trades = []
    
    # Group by week
    df['week'] = df.index.isocalendar().week.astype(int)
    df['weekday'] = df.index.dayofweek  # 0=Monday
    
    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        
        # Only trade on Tuesday (weekday=1) after Monday float
        if day.index[0].dayofday != 1:
            continue
        
        # Get Monday's Asian Range
        monday_date = date - pd.Timedelta(days=1)
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
                tp = ep + to_price(ar * 3.0)  # Conservative weekly target
                break
            elif row['close'] < al:
                direction = 'SHORT'
                ep = row['close']
                sl = ah
                tp = ep - to_price(ar * 3.0)
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


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY 6: DAILY ASIAN FLOAT (Run-and-Retest)  (Manual target: 18.8% float)
# ═══════════════════════════════════════════════════════════════════════════════

def run_daily_asian_float(df):
    """
    Daily Asian Float — Part 8.
    
    Pattern: London open breaks Asian constraint band, shallow partial
    rebalancing holds, constraint deficit resolved.
    
    - 18.8% of days: price never re-enters Asian band (broad float)
    - 2.9%: shallow float (<=38% reentry, no reentry)
    - After run-and-retest: 56.4p mean continuation
    
    Strategy: Enter when price breaks Asian band with shallow pullback (<=38% AR).
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
                # Pullback = retrace back toward Asian range
                retrace = to_pips(breakout_price - row['low'])
                if retrace > ar * 0.38:
                    pullback_ok = False
                    break
                # If it re-enters Asian band, not a float day
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
        tp = ep + to_price(ar * 0.56) * (1 if breakout_dir == 'LONG' else -1)  # 56.4p mean continuation
        
        post = day[(day.index > breakout_idx) & (day['est_h'] < 17)]
        trade = manage_trade(post, ep, breakout_dir, sl, tp)
        if trade:
            trade['entry_time'] = breakout_idx
            trade['ar_pips'] = ar
            trade['direction'] = breakout_dir
            trades.append(trade)
    
    return day_results(trades, "Daily_Asian_Float")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("🧪 CEREBUS FX v4 — Strategy Reconstruction Backtest Engine")
    print("=" * 70)
    
    df = load_eurusd_m5()
    if df is None:
        return
    
    print(f"\n📊 Data: {len(df):,} bars | {df.index[0].date()} → {df.index[-1].date()}")
    
    strategies = [
        ("CFD_Expansion", run_cfd_expansion),
        ("Deep_Mean_Reversion", run_deep_mean_reversion),
        ("Constraint_Anchor", run_constraint_anchor),
        ("Stall_Harvest_CFD", run_stall_harvest_cfd),
        ("Monday_Asian_Float", run_monday_asian_float),
        ("Daily_Asian_Float", run_daily_asian_float),
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
                      f"MaxDD: {r['max_dd']}p | Exp: {r['expectancy']}p")
            else:
                print(f"  ⚠️ No trades ({elapsed:.1f}s)")
        except Exception as e:
            elapsed = time.time() - t0
            print(f"  ❌ {e} ({elapsed:.1f}s)")
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
    
    # Targets comparison
    print(f"\n📋 TARGETS:")
    targets = {
        "CFD_Expansion": "85-90% WR",
        "Deep_Mean_Reversion": "74-84% WR",
        "Constraint_Anchor": "91.7% WR",
        "Stall_Harvest_CFD": "86% WR",
        "Monday_Asian_Float": "29.5% 24h float",
        "Daily_Asian_Float": "18.8% broad float",
    }
    for name, target in targets.items():
        r = all_results.get(name, {})
        wr = r.get('win_rate', 0)
        n = r.get('total_trades', 0)
        print(f"  {name}: WR={wr}% (target: {target}) | n={n}")
    
    # Save
    results_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results")
    results_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rf = results_dir / f"cerabus_all_{ts}.json"
    with open(rf, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n💾 Saved to {rf}")
    
    return all_results


if __name__ == "__main__":
    main()
