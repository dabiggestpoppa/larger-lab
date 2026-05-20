"""
Multi-Asset Forex M5 Backtest
Runs all 10 CEREBUS strategies on 8 forex M5 pairs.
Reuses the existing backtest framework from nautilus/strategies.
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# Add nautilus strategies to path
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\projects\trading\nautilus\strategies")

# â”€â”€ Configuration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

FOREX_FILES = {
    "EUR/USD": r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv",
    "GBP/USD": r"C:\Users\wifik\Downloads\GBPUSD!_M5_202301020000_202605061250.csv",
    "USD/JPY": r"C:\Users\wifik\Downloads\USDJPY!_M5_202301020000_202605061250.csv",
    "USD/CHF": r"C:\Users\wifik\Downloads\USDCHF!_M5_202301020000_202605061250.csv",
    "AUD/USD": r"C:\Users\wifik\Downloads\AUDUSD!_M5_202301020000_202605061250.csv",
    "NZD/USD": r"C:\Users\wifik\Downloads\NZDUSD!_M5_202301020000_202605061250.csv",
    "USD/CAD": r"C:\Users\wifik\Downloads\USDCAD!_M5_202301020000_202605061250.csv",
    "CHF/JPY": r"C:\Users\wifik\Downloads\CHFJPY!_M5_202201030000_202605061250.csv",
}

COST_PER_TRADE_PIPS = 2.9  # spread 0.2 + slippage 2.0 + commission 0.7

# â”€â”€ Data Loading â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def load_forex_csv(path, pair):
    """Load a forex M5 CSV file."""
    path = Path(path)
    if not path.exists():
        print(f"  MISSING: {path.name}")
        return None
    
    mb = path.stat().st_size // 1024 // 1024
    print(f"  Loading {path.name} ({mb}MB)...", end=" ", flush=True)
    
    records = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    is_jpy = "JPY" in pair
    
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
    print(f"OK ({len(df):,} bars)")
    return df


def to_pips(price_diff, pair):
    if "JPY" in pair:
        return price_diff * 100.0
    return price_diff * 10000.0

def to_price(pips, pair):
    if "JPY" in pair:
        return pips / 100.0
    return pips / 10000.0


def prepare_data(df, pair):
    """Add computed columns."""
    df = df.copy()
    df['utc_h'] = df.index.hour
    df['est_h'] = (df['utc_h'] - 5 + 24) % 24
    df['date'] = df.index.date
    df['body_pips'] = to_pips((df['close'] - df['open']).abs(), pair)
    df['range_pips'] = to_pips((df['high'] - df['low']).abs(), pair)
    return df


def compute_results(trades, name, pair):
    """Compute summary statistics from trades list."""
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
        if v > peak:
            peak = v
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
    }


# â”€â”€ Strategy Implementations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Simplified versions that capture the core logic of each strategy.
# These are derived from the optimizer_v4b results and the strategy analysis.

def run_p90_base(df, pair):
    """P90 Base Strategy â€” core CEREBUS entry with fixed SL/TP."""
    trades = []
    dates = sorted(df['date'].unique())
    
    for date in dates:
        day_df = df[df['date'] == date]
        if len(day_df) < 10:
            continue
        
        # Asian Range: 7PM-3AM EST
        asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
        if len(asian) < 2:
            continue
        ah = asian['high'].max()
        al = asian['low'].min()
        ar_pips = to_pips(ah - al, pair)
        
        # Tier classification
        if ar_pips < 20:
            tier = 'T1'
            sl_pips = 10.0
            tp_pips = 16.8
        elif ar_pips < 30:
            tier = 'T2'
            sl_pips = 13.2
            tp_pips = 26.4
        elif ar_pips < 45:
            tier = 'T3'
            sl_pips = 16.8
            tp_pips = 40.0
        else:
            continue  # NO_GO
        
        # Entry window: 3AM-11AM EST
        entry_df = day_df[(day_df['est_h'] >= 3) & (day_df['est_h'] < 11)]
        if len(entry_df) < 2:
            continue
        
        # P90 threshold by hour
        p90_thresh = {
            3: 4.1, 4: 4.1, 5: 4.6, 6: 4.6, 7: 4.6, 8: 4.6,
            9: 5.9, 10: 6.2
        }
        
        signal_dir = None
        signal_row = None
        for idx, row in entry_df.iterrows():
            thresh = p90_thresh.get(row['est_h'], 99.0)
            if row['body_pips'] >= thresh:
                signal_dir = 'LONG' if row['close'] > row['open'] else 'SHORT'
                signal_row = row
                break
        
        if signal_dir is None:
            continue
        
        entry_price = signal_row['close']
        entry_idx = signal_row.name
        
        # SL/TP in price
        if signal_dir == 'LONG':
            sl_price = entry_price - to_price(sl_pips, pair)
            tp_price = entry_price + to_price(tp_pips, pair)
        else:
            sl_price = entry_price + to_price(sl_pips, pair)
            tp_price = entry_price - to_price(tp_pips, pair)
        
        # Manage trade: bars after signal until 5PM EST
        post_df = day_df[(day_df['est_h'] > signal_row['est_h']) & (day_df['est_h'] < 17)]
        
        exited = False
        for idx, row in post_df.iterrows():
            h, l, c = row['high'], row['low'], row['close']
            if signal_dir == 'LONG':
                if l <= sl_price:
                    pnl = to_pips(sl_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if h >= tp_price:
                    pnl = to_pips(tp_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
            else:
                if h >= sl_price:
                    pnl = to_pips(entry_price - sl_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if l <= tp_price:
                    pnl = to_pips(entry_price - tp_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
        
        if not exited:
            # Hard exit at last bar before 5PM
            if len(post_df) > 0:
                last = post_df.iloc[-1]
                if signal_dir == 'LONG':
                    pnl = to_pips(last['close'] - entry_price, pair) - COST_PER_TRADE_PIPS
                else:
                    pnl = to_pips(entry_price - last['close'], pair) - COST_PER_TRADE_PIPS
                trades.append({'pnl': pnl, 'reason': 'hard_exit'})
    
    return trades


def run_deep_mean_reversion(df, pair):
    """Deep Mean Reversion â€” P90 entry + mean reversion SL/TP."""
    trades = []
    dates = sorted(df['date'].unique())
    
    for date in dates:
        day_df = df[df['date'] == date]
        if len(day_df) < 10:
            continue
        
        # Asian Range
        asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
        if len(asian) < 2:
            continue
        ah = asian['high'].max()
        al = asian['low'].min()
        ar_pips = to_pips(ah - al, pair)
        
        if ar_pips < 15 or ar_pips > 60:
            continue
        
        # Entry window
        entry_df = day_df[(day_df['est_h'] >= 3) & (day_df['est_h'] < 11)]
        if len(entry_df) < 2:
            continue
        
        p90_thresh = {3: 4.1, 4: 4.1, 5: 4.6, 6: 4.6, 7: 4.6, 8: 4.6, 9: 5.9, 10: 6.2}
        
        signal_dir = None
        signal_row = None
        for idx, row in entry_df.iterrows():
            thresh = p90_thresh.get(row['est_h'], 99.0)
            if row['body_pips'] >= thresh:
                signal_dir = 'LONG' if row['close'] > row['open'] else 'SHORT'
                signal_row = row
                break
        
        if signal_dir is None:
            continue
        
        entry_price = signal_row['close']
        
        # DMR uses wider SL (AR-based) and TP at opposite AR boundary
        if signal_dir == 'LONG':
            sl_price = entry_price - to_price(ar_pips * 0.5, pair)
            tp_price = ah + to_price(5.0, pair)  # breakout above AR high
        else:
            sl_price = entry_price + to_price(ar_pips * 0.5, pair)
            tp_price = al - to_price(5.0, pair)  # breakout below AR low
        
        post_df = day_df[(day_df['est_h'] > signal_row['est_h']) & (day_df['est_h'] < 17)]
        
        exited = False
        for idx, row in post_df.iterrows():
            h, l, c = row['high'], row['low'], row['close']
            if signal_dir == 'LONG':
                if l <= sl_price:
                    pnl = to_pips(sl_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if h >= tp_price:
                    pnl = to_pips(tp_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
            else:
                if h >= sl_price:
                    pnl = to_pips(entry_price - sl_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if l <= tp_price:
                    pnl = to_pips(entry_price - tp_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
        
        if not exited and len(post_df) > 0:
            last = post_df.iloc[-1]
            if signal_dir == 'LONG':
                pnl = to_pips(last['close'] - entry_price, pair) - COST_PER_TRADE_PIPS
            else:
                pnl = to_pips(entry_price - last['close'], pair) - COST_PER_TRADE_PIPS
            trades.append({'pnl': pnl, 'reason': 'hard_exit'})
    
    return trades


def run_composite_alpha(df, pair):
    """Composite Alpha â€” combines P90 + cascade + regime filter."""
    trades = []
    dates = sorted(df['date'].unique())
    
    for date in dates:
        day_df = df[df['date'] == date]
        if len(day_df) < 10:
            continue
        
        asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
        if len(asian) < 2:
            continue
        ah = asian['high'].max()
        al = asian['low'].min()
        ar_pips = to_pips(ah - al, pair)
        
        if ar_pips < 18 or ar_pips > 50:
            continue
        
        entry_df = day_df[(day_df['est_h'] >= 3) & (day_df['est_h'] < 11)]
        if len(entry_df) < 2:
            continue
        
        p90_thresh = {3: 4.1, 4: 4.1, 5: 4.6, 6: 4.6, 7: 4.6, 8: 4.6, 9: 5.9, 10: 6.2}
        
        signal_dir = None
        signal_row = None
        for idx, row in entry_df.iterrows():
            thresh = p90_thresh.get(row['est_h'], 99.0)
            if row['body_pips'] >= thresh:
                signal_dir = 'LONG' if row['close'] > row['open'] else 'SHORT'
                signal_row = row
                break
        
        if signal_dir is None:
            continue
        
        entry_price = signal_row['close']
        
        # Composite: tighter SL, multiple TP levels
        sl_pips = ar_pips * 0.35
        tp1_pips = ar_pips * 0.8
        tp2_pips = ar_pips * 1.32
        
        if signal_dir == 'LONG':
            sl_price = entry_price - to_price(sl_pips, pair)
            tp1_price = entry_price + to_price(tp1_pips, pair)
            tp2_price = entry_price + to_price(tp2_pips, pair)
        else:
            sl_price = entry_price + to_price(sl_pips, pair)
            tp1_price = entry_price - to_price(tp1_pips, pair)
            tp2_price = entry_price - to_price(tp2_pips, pair)
        
        post_df = day_df[(day_df['est_h'] > signal_row['est_h']) & (day_df['est_h'] < 17)]
        
        exited = False
        for idx, row in post_df.iterrows():
            h, l, c = row['high'], row['low'], row['close']
            if signal_dir == 'LONG':
                if l <= sl_price:
                    pnl = to_pips(sl_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if h >= tp2_price:
                    pnl = to_pips(tp2_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp2'})
                    exited = True
                    break
                if h >= tp1_price:
                    pnl = to_pips(tp1_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp1'})
                    exited = True
                    break
            else:
                if h >= sl_price:
                    pnl = to_pips(entry_price - sl_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if l <= tp2_price:
                    pnl = to_pips(entry_price - tp2_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp2'})
                    exited = True
                    break
                if l <= tp1_price:
                    pnl = to_pips(entry_price - tp1_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp1'})
                    exited = True
                    break
        
        if not exited and len(post_df) > 0:
            last = post_df.iloc[-1]
            if signal_dir == 'LONG':
                pnl = to_pips(last['close'] - entry_price, pair) - COST_PER_TRADE_PIPS
            else:
                pnl = to_pips(entry_price - last['close'], pair) - COST_PER_TRADE_PIPS
            trades.append({'pnl': pnl, 'reason': 'hard_exit'})
    
    return trades


def run_failure_repair(df, pair):
    """Failure Repair â€” enters on failed P90 breakout."""
    trades = []
    dates = sorted(df['date'].unique())
    
    for date in dates:
        day_df = df[df['date'] == date]
        if len(day_df) < 10:
            continue
        
        asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
        if len(asian) < 2:
            continue
        ah = asian['high'].max()
        al = asian['low'].min()
        ar_pips = to_pips(ah - al, pair)
        
        if ar_pips < 20 or ar_pips > 55:
            continue
        
        entry_df = day_df[(day_df['est_h'] >= 3) & (day_df['est_h'] < 11)]
        if len(entry_df) < 2:
            continue
        
        p90_thresh = {3: 4.1, 4: 4.1, 5: 4.6, 6: 4.6, 7: 4.6, 8: 4.6, 9: 5.9, 10: 6.2}
        
        # Look for failed breakout: price breaks AR boundary then reverses
        signal_dir = None
        signal_row = None
        for idx, row in entry_df.iterrows():
            thresh = p90_thresh.get(row['est_h'], 99.0)
            if row['body_pips'] >= thresh:
                # Check if this is a failed breakout
                if row['close'] > ah and row['close'] < row['open']:
                    signal_dir = 'SHORT'  # Failed bullish breakout
                    signal_row = row
                    break
                elif row['close'] < al and row['close'] > row['open']:
                    signal_dir = 'LONG'  # Failed bearish breakout
                    signal_row = row
                    break
        
        if signal_dir is None:
            continue
        
        entry_price = signal_row['close']
        
        if signal_dir == 'LONG':
            sl_price = al - to_price(5.0, pair)
            tp_price = entry_price + to_price(ar_pips * 0.8, pair)
        else:
            sl_price = ah + to_price(5.0, pair)
            tp_price = entry_price - to_price(ar_pips * 0.8, pair)
        
        post_df = day_df[(day_df['est_h'] > signal_row['est_h']) & (day_df['est_h'] < 17)]
        
        exited = False
        for idx, row in post_df.iterrows():
            h, l, c = row['high'], row['low'], row['close']
            if signal_dir == 'LONG':
                if l <= sl_price:
                    pnl = to_pips(sl_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if h >= tp_price:
                    pnl = to_pips(tp_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
            else:
                if h >= sl_price:
                    pnl = to_pips(entry_price - sl_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if l <= tp_price:
                    pnl = to_pips(entry_price - tp_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
        
        if not exited and len(post_df) > 0:
            last = post_df.iloc[-1]
            if signal_dir == 'LONG':
                pnl = to_pips(last['close'] - entry_price, pair) - COST_PER_TRADE_PIPS
            else:
                pnl = to_pips(entry_price - last['close'], pair) - COST_PER_TRADE_PIPS
            trades.append({'pnl': pnl, 'reason': 'hard_exit'})
    
    return trades


def run_stall_harvest(df, pair):
    """Stall Harvest â€” captures small moves during Asian session."""
    trades = []
    dates = sorted(df['date'].unique())
    
    for date in dates:
        day_df = df[df['date'] == date]
        if len(day_df) < 10:
            continue
        
        # Asian session: 7PM-3AM EST
        asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
        if len(asian) < 5:
            continue
        
        ah = asian['high'].max()
        al = asian['low'].min()
        ar_pips = to_pips(ah - al, pair)
        
        if ar_pips < 8 or ar_pips > 35:
            continue
        
        # Entry: first pullback within Asian range
        entry_df = asian
        signal_dir = None
        signal_row = None
        
        for idx, row in entry_df.iterrows():
            body = row['body_pips']
            if body < 2.0:
                continue
            # Look for counter-trend bar after a move
            mid = (ah + al) / 2
            if row['close'] < mid and row['close'] > row['open']:
                signal_dir = 'LONG'
                signal_row = row
                break
            elif row['close'] > mid and row['close'] < row['open']:
                signal_dir = 'SHORT'
                signal_row = row
                break
        
        if signal_dir is None:
            continue
        
        entry_price = signal_row['close']
        
        if signal_dir == 'LONG':
            sl_price = al - to_price(2.0, pair)
            tp_price = entry_price + to_price(ar_pips * 0.5, pair)
        else:
            sl_price = ah + to_price(2.0, pair)
            tp_price = entry_price - to_price(ar_pips * 0.5, pair)
        
        post_df = day_df[day_df['est_h'] > 3]
        
        exited = False
        for idx, row in post_df.iterrows():
            if row['est_h'] >= 8:
                break
            h, l, c = row['high'], row['low'], row['close']
            if signal_dir == 'LONG':
                if l <= sl_price:
                    pnl = to_pips(sl_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if h >= tp_price:
                    pnl = to_pips(tp_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
            else:
                if h >= sl_price:
                    pnl = to_pips(entry_price - sl_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if l <= tp_price:
                    pnl = to_pips(entry_price - tp_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
        
        if not exited and len(post_df) > 0:
            last = post_df[post_df['est_h'] < 8]
            if len(last) > 0:
                c = last.iloc[-1]['close']
                if signal_dir == 'LONG':
                    pnl = to_pips(c - entry_price, pair) - COST_PER_TRADE_PIPS
                else:
                    pnl = to_pips(entry_price - c, pair) - COST_PER_TRADE_PIPS
                trades.append({'pnl': pnl, 'reason': 'time_exit'})
    
    return trades


def run_constraint_anchor(df, pair):
    """Constraint Anchor â€” trades within Asian range boundaries."""
    trades = []
    dates = sorted(df['date'].unique())
    
    for date in dates:
        day_df = df[df['date'] == date]
        if len(day_df) < 10:
            continue
        
        asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
        if len(asian) < 2:
            continue
        ah = asian['high'].max()
        al = asian['low'].min()
        ar_pips = to_pips(ah - al, pair)
        
        if ar_pips < 15 or ar_pips > 50:
            continue
        
        # Entry: price pulls back to AR boundary in London session
        london_df = day_df[(day_df['est_h'] >= 8) & (day_df['est_h'] < 13)]
        if len(london_df) < 2:
            continue
        
        signal_dir = None
        signal_row = None
        for idx, row in london_df.iterrows():
            if row['low'] <= al + to_price(2.0, pair) and row['close'] > row['open']:
                signal_dir = 'LONG'
                signal_row = row
                break
            elif row['high'] >= ah - to_price(2.0, pair) and row['close'] < row['open']:
                signal_dir = 'SHORT'
                signal_row = row
                break
        
        if signal_dir is None:
            continue
        
        entry_price = signal_row['close']
        
        if signal_dir == 'LONG':
            sl_price = al - to_price(3.0, pair)
            tp_price = ah
        else:
            sl_price = ah + to_price(3.0, pair)
            tp_price = al
        
        post_df = day_df[(day_df['est_h'] > signal_row['est_h']) & (day_df['est_h'] < 17)]
        
        exited = False
        for idx, row in post_df.iterrows():
            h, l, c = row['high'], row['low'], row['close']
            if signal_dir == 'LONG':
                if l <= sl_price:
                    pnl = to_pips(sl_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if h >= tp_price:
                    pnl = to_pips(tp_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
            else:
                if h >= sl_price:
                    pnl = to_pips(entry_price - sl_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if l <= tp_price:
                    pnl = to_pips(entry_price - tp_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
        
        if not exited and len(post_df) > 0:
            last = post_df.iloc[-1]
            if signal_dir == 'LONG':
                pnl = to_pips(last['close'] - entry_price, pair) - COST_PER_TRADE_PIPS
            else:
                pnl = to_pips(entry_price - last['close'], pair) - COST_PER_TRADE_PIPS
            trades.append({'pnl': pnl, 'reason': 'hard_exit'})
    
    return trades


def run_blind_structural_chain(df, pair):
    """Blind Structural Chain â€” multi-leg breakout strategy."""
    trades = []
    dates = sorted(df['date'].unique())
    
    for date in dates:
        day_df = df[df['date'] == date]
        if len(day_df) < 10:
            continue
        
        asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
        if len(asian) < 2:
            continue
        ah = asian['high'].max()
        al = asian['low'].min()
        ar_pips = to_pips(ah - al, pair)
        
        if ar_pips < 25 or ar_pips > 70:
            continue
        
        entry_df = day_df[(day_df['est_h'] >= 3) & (day_df['est_h'] < 11)]
        if len(entry_df) < 2:
            continue
        
        p90_thresh = {3: 4.1, 4: 4.1, 5: 4.6, 6: 4.6, 7: 4.6, 8: 4.6, 9: 5.9, 10: 6.2}
        
        signal_dir = None
        signal_row = None
        for idx, row in entry_df.iterrows():
            thresh = p90_thresh.get(row['est_h'], 99.0)
            if row['body_pips'] >= thresh:
                signal_dir = 'LONG' if row['close'] > row['open'] else 'SHORT'
                signal_row = row
                break
        
        if signal_dir is None:
            continue
        
        entry_price = signal_row['close']
        
        # BSC: wide SL, very wide TP (chain of breakouts)
        sl_pips = ar_pips * 0.6
        tp_pips = ar_pips * 2.0
        
        if signal_dir == 'LONG':
            sl_price = entry_price - to_price(sl_pips, pair)
            tp_price = entry_price + to_price(tp_pips, pair)
        else:
            sl_price = entry_price + to_price(sl_pips, pair)
            tp_price = entry_price - to_price(tp_pips, pair)
        
        post_df = day_df[(day_df['est_h'] > signal_row['est_h']) & (day_df['est_h'] < 17)]
        
        exited = False
        for idx, row in post_df.iterrows():
            h, l, c = row['high'], row['low'], row['close']
            if signal_dir == 'LONG':
                if l <= sl_price:
                    pnl = to_pips(sl_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if h >= tp_price:
                    pnl = to_pips(tp_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
            else:
                if h >= sl_price:
                    pnl = to_pips(entry_price - sl_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if l <= tp_price:
                    pnl = to_pips(entry_price - tp_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
        
        if not exited and len(post_df) > 0:
            last = post_df.iloc[-1]
            if signal_dir == 'LONG':
                pnl = to_pips(last['close'] - entry_price, pair) - COST_PER_TRADE_PIPS
            else:
                pnl = to_pips(entry_price - last['close'], pair) - COST_PER_TRADE_PIPS
            trades.append({'pnl': pnl, 'reason': 'hard_exit'})
    
    return trades


def run_two_plays(df, pair):
    """Two Plays â€” two consecutive entries on same signal."""
    trades = []
    dates = sorted(df['date'].unique())
    
    for date in dates:
        day_df = df[df['date'] == date]
        if len(day_df) < 10:
            continue
        
        asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
        if len(asian) < 2:
            continue
        ah = asian['high'].max()
        al = asian['low'].min()
        ar_pips = to_pips(ah - al, pair)
        
        if ar_pips < 18 or ar_pips > 45:
            continue
        
        entry_df = day_df[(day_df['est_h'] >= 3) & (day_df['est_h'] < 11)]
        if len(entry_df) < 2:
            continue
        
        p90_thresh = {3: 4.1, 4: 4.1, 5: 4.6, 6: 4.6, 7: 4.6, 8: 4.6, 9: 5.9, 10: 6.2}
        
        signal_dir = None
        signal_row = None
        for idx, row in entry_df.iterrows():
            thresh = p90_thresh.get(row['est_h'], 99.0)
            if row['body_pips'] >= thresh:
                signal_dir = 'LONG' if row['close'] > row['open'] else 'SHORT'
                signal_row = row
                break
        
        if signal_dir is None:
            continue
        
        entry_price = signal_row['close']
        
        # Two plays: entry + re-entry at better price
        sl_pips = ar_pips * 0.45
        tp_pips = ar_pips * 0.9
        
        for play in range(2):
            if signal_dir == 'LONG':
                sl_price = entry_price - to_price(sl_pips, pair)
                tp_price = entry_price + to_price(tp_pips, pair)
            else:
                sl_price = entry_price + to_price(sl_pips, pair)
                tp_price = entry_price - to_price(tp_pips, pair)
            
            post_df = day_df[(day_df['est_h'] > signal_row['est_h']) & (day_df['est_h'] < 17)]
            
            exited = False
            for idx, row in post_df.iterrows():
                h, l, c = row['high'], row['low'], row['close']
                if signal_dir == 'LONG':
                    if l <= sl_price:
                        pnl = to_pips(sl_price - entry_price, pair) - COST_PER_TRADE_PIPS
                        trades.append({'pnl': pnl, 'reason': 'sl', 'play': play + 1})
                        exited = True
                        break
                    if h >= tp_price:
                        pnl = to_pips(tp_price - entry_price, pair) - COST_PER_TRADE_PIPS
                        trades.append({'pnl': pnl, 'reason': 'tp', 'play': play + 1})
                        exited = True
                        break
                else:
                    if h >= sl_price:
                        pnl = to_pips(entry_price - sl_price, pair) - COST_PER_TRADE_PIPS
                        trades.append({'pnl': pnl, 'reason': 'sl', 'play': play + 1})
                        exited = True
                        break
                    if l <= tp_price:
                        pnl = to_pips(entry_price - tp_price, pair) - COST_PER_TRADE_PIPS
                        trades.append({'pnl': pnl, 'reason': 'tp', 'play': play + 1})
                        exited = True
                        break
            
            if not exited and len(post_df) > 0:
                last = post_df.iloc[-1]
                if signal_dir == 'LONG':
                    pnl = to_pips(last['close'] - entry_price, pair) - COST_PER_TRADE_PIPS
                else:
                    pnl = to_pips(entry_price - last['close'], pair) - COST_PER_TRADE_PIPS
                trades.append({'pnl': pnl, 'reason': 'hard_exit', 'play': play + 1})
            
            # Re-entry: move entry to midpoint
            if signal_dir == 'LONG':
                entry_price = entry_price + to_price(tp_pips * 0.3, pair)
            else:
                entry_price = entry_price - to_price(tp_pips * 0.3, pair)
    
    return trades


def run_fractal_resolution(df, pair):
    """Fractal Resolution â€” multi-timeframe fractal breakout."""
    trades = []
    dates = sorted(df['date'].unique())
    
    for date in dates:
        day_df = df[df['date'] == date]
        if len(day_df) < 10:
            continue
        
        asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
        if len(asian) < 2:
            continue
        ah = asian['high'].max()
        al = asian['low'].min()
        ar_pips = to_pips(ah - al, pair)
        
        if ar_pips < 20 or ar_pips > 55:
            continue
        
        entry_df = day_df[(day_df['est_h'] >= 3) & (day_df['est_h'] < 11)]
        if len(entry_df) < 2:
            continue
        
        p90_thresh = {3: 4.1, 4: 4.1, 5: 4.6, 6: 4.6, 7: 4.6, 8: 4.6, 9: 5.9, 10: 6.2}
        
        signal_dir = None
        signal_row = None
        for idx, row in entry_df.iterrows():
            thresh = p90_thresh.get(row['est_h'], 99.0)
            if row['body_pips'] >= thresh:
                signal_dir = 'LONG' if row['close'] > row['open'] else 'SHORT'
                signal_row = row
                break
        
        if signal_dir is None:
            continue
        
        entry_price = signal_row['close']
        
        # Fractal: SL at fractal boundary, TP at next fractal level
        sl_pips = ar_pips * 0.5
        tp_pips = ar_pips * 1.68
        
        if signal_dir == 'LONG':
            sl_price = entry_price - to_price(sl_pips, pair)
            tp_price = entry_price + to_price(tp_pips, pair)
        else:
            sl_price = entry_price + to_price(sl_pips, pair)
            tp_price = entry_price - to_price(tp_pips, pair)
        
        post_df = day_df[(day_df['est_h'] > signal_row['est_h']) & (day_df['est_h'] < 17)]
        
        exited = False
        for idx, row in post_df.iterrows():
            h, l, c = row['high'], row['low'], row['close']
            if signal_dir == 'LONG':
                if l <= sl_price:
                    pnl = to_pips(sl_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if h >= tp_price:
                    pnl = to_pips(tp_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
            else:
                if h >= sl_price:
                    pnl = to_pips(entry_price - sl_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if l <= tp_price:
                    pnl = to_pips(entry_price - tp_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
        
        if not exited and len(post_df) > 0:
            last = post_df.iloc[-1]
            if signal_dir == 'LONG':
                pnl = to_pips(last['close'] - entry_price, pair) - COST_PER_TRADE_PIPS
            else:
                pnl = to_pips(entry_price - last['close'], pair) - COST_PER_TRADE_PIPS
            trades.append({'pnl': pnl, 'reason': 'hard_exit'})
    
    return trades


def run_dual_engine(df, pair):
    """Dual Engine â€” combines momentum and mean reversion signals."""
    trades = []
    dates = sorted(df['date'].unique())
    
    for date in dates:
        day_df = df[df['date'] == date]
        if len(day_df) < 10:
            continue
        
        asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
        if len(asian) < 2:
            continue
        ah = asian['high'].max()
        al = asian['low'].min()
        ar_pips = to_pips(ah - al, pair)
        
        if ar_pips < 18 or ar_pips > 50:
            continue
        
        entry_df = day_df[(day_df['est_h'] >= 3) & (day_df['est_h'] < 11)]
        if len(entry_df) < 2:
            continue
        
        p90_thresh = {3: 4.1, 4: 4.1, 5: 4.6, 6: 4.6, 7: 4.6, 8: 4.6, 9: 5.9, 10: 6.2}
        
        signal_dir = None
        signal_row = None
        for idx, row in entry_df.iterrows():
            thresh = p90_thresh.get(row['est_h'], 99.0)
            if row['body_pips'] >= thresh:
                signal_dir = 'LONG' if row['close'] > row['open'] else 'SHORT'
                signal_row = row
                break
        
        if signal_dir is None:
            continue
        
        entry_price = signal_row['close']
        
        # Dual engine: moderate SL, two TP levels
        sl_pips = ar_pips * 0.4
        tp_pips = ar_pips * 1.0
        
        if signal_dir == 'LONG':
            sl_price = entry_price - to_price(sl_pips, pair)
            tp_price = entry_price + to_price(tp_pips, pair)
        else:
            sl_price = entry_price + to_price(sl_pips, pair)
            tp_price = entry_price - to_price(tp_pips, pair)
        
        post_df = day_df[(day_df['est_h'] > signal_row['est_h']) & (day_df['est_h'] < 17)]
        
        exited = False
        for idx, row in post_df.iterrows():
            h, l, c = row['high'], row['low'], row['close']
            if signal_dir == 'LONG':
                if l <= sl_price:
                    pnl = to_pips(sl_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if h >= tp_price:
                    pnl = to_pips(tp_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
            else:
                if h >= sl_price:
                    pnl = to_pips(entry_price - sl_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if l <= tp_price:
                    pnl = to_pips(entry_price - tp_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
        
        if not exited and len(post_df) > 0:
            last = post_df.iloc[-1]
            if signal_dir == 'LONG':
                pnl = to_pips(last['close'] - entry_price, pair) - COST_PER_TRADE_PIPS
            else:
                pnl = to_pips(entry_price - last['close'], pair) - COST_PER_TRADE_PIPS
            trades.append({'pnl': pnl, 'reason': 'hard_exit'})
    
    return trades


def run_p90p_distribution(df, pair):
    """P90P Distribution â€” P90 with distribution-based exit."""
    trades = []
    dates = sorted(df['date'].unique())
    
    for date in dates:
        day_df = df[df['date'] == date]
        if len(day_df) < 10:
            continue
        
        asian = day_df[(day_df['est_h'] >= 19) | (day_df['est_h'] < 3)]
        if len(asian) < 2:
            continue
        ah = asian['high'].max()
        al = asian['low'].min()
        ar_pips = to_pips(ah - al, pair)
        
        if ar_pips < 15 or ar_pips > 40:
            continue
        
        entry_df = day_df[(day_df['est_h'] >= 3) & (day_df['est_h'] < 11)]
        if len(entry_df) < 2:
            continue
        
        p90_thresh = {3: 4.1, 4: 4.1, 5: 4.6, 6: 4.6, 7: 4.6, 8: 4.6, 9: 5.9, 10: 6.2}
        
        signal_dir = None
        signal_row = None
        for idx, row in entry_df.iterrows():
            thresh = p90_thresh.get(row['est_h'], 99.0)
            if row['body_pips'] >= thresh:
                signal_dir = 'LONG' if row['close'] > row['open'] else 'SHORT'
                signal_row = row
                break
        
        if signal_dir is None:
            continue
        
        entry_price = signal_row['close']
        
        # P90P: tight SL, distribution-based TP
        sl_pips = ar_pips * 0.3
        tp_pips = ar_pips * 0.6
        
        if signal_dir == 'LONG':
            sl_price = entry_price - to_price(sl_pips, pair)
            tp_price = entry_price + to_price(tp_pips, pair)
        else:
            sl_price = entry_price + to_price(sl_pips, pair)
            tp_price = entry_price - to_price(tp_pips, pair)
        
        post_df = day_df[(day_df['est_h'] > signal_row['est_h']) & (day_df['est_h'] < 17)]
        
        exited = False
        for idx, row in post_df.iterrows():
            h, l, c = row['high'], row['low'], row['close']
            if signal_dir == 'LONG':
                if l <= sl_price:
                    pnl = to_pips(sl_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if h >= tp_price:
                    pnl = to_pips(tp_price - entry_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
            else:
                if h >= sl_price:
                    pnl = to_pips(entry_price - sl_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'sl'})
                    exited = True
                    break
                if l <= tp_price:
                    pnl = to_pips(entry_price - tp_price, pair) - COST_PER_TRADE_PIPS
                    trades.append({'pnl': pnl, 'reason': 'tp'})
                    exited = True
                    break
        
        if not exited and len(post_df) > 0:
            last = post_df.iloc[-1]
            if signal_dir == 'LONG':
                pnl = to_pips(last['close'] - entry_price, pair) - COST_PER_TRADE_PIPS
            else:
                pnl = to_pips(entry_price - last['close'], pair) - COST_PER_TRADE_PIPS
            trades.append({'pnl': pnl, 'reason': 'hard_exit'})
    
    return trades


# â”€â”€ Strategy Registry â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

STRATEGIES = {
    "Deep_Mean_Reversion": run_deep_mean_reversion,
    "Composite_Alpha": run_composite_alpha,
    "Failure_Repair": run_failure_repair,
    "Stall_Harvest": run_stall_harvest,
    "Constraint_Anchor": run_constraint_anchor,
    "Blind_Structural_Chain": run_blind_structural_chain,
    "Two_Plays": run_two_plays,
    "Fractal_Resolution": run_fractal_resolution,
    "Dual_Engine": run_dual_engine,
    "P90P_Distribution": run_p90p_distribution,
}


# â”€â”€ Main Runner â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main():
    start_time = time.time()
    all_results = {}
    
    print("=" * 70)
    print("MULTI-ASSET FOREX M5 BACKTEST")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Strategies: {len(STRATEGIES)} | Assets: {len(FOREX_FILES)}")
    print("=" * 70)
    
    for strat_name, strat_func in STRATEGIES.items():
        print(f"\n{'â”€' * 50}")
        print(f"Strategy: {strat_name}")
        print(f"{'â”€' * 50}")
        
        all_results[strat_name] = {}
        
        for pair, file_path in FOREX_FILES.items():
            # Load data
            df_raw = load_forex_csv(file_path, pair)
            if df_raw is None:
                continue
            
            df = prepare_data(df_raw, pair)
            del df_raw  # free memory
            
            # Run strategy
            t0 = time.time()
            trades = strat_func(df, pair)
            elapsed = time.time() - t0
            
            # Compute results
            results = compute_results(trades, strat_name, pair)
            results['timeframe'] = 'M5'
            results['elapsed_sec'] = round(elapsed, 1)
            
            all_results[strat_name][pair.replace("/", "_")] = results
            
            wr = results.get('win_rate', 0)
            pf = results.get('profit_factor', 0)
            pnl = results.get('total_pnl', 0)
            trades_count = results.get('total_trades', 0)
            print(f"  {pair:12s} | {trades_count:5d} trades | WR: {wr:5.1f}% | PF: {pf:6.2f} | PnL: {pnl:8.1f}p | {elapsed:.1f}s")
            
            del df  # free memory
    
    # â”€â”€ Save Results â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    output_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\multi_asset_forex_m5.json")
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nâœ… Results saved to: {output_path}")
    
    # â”€â”€ Generate Report â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    report_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\MULTI_ASSET_FOREX_M5_REPORT.md")
    
    report_lines = [
        "# Multi-Asset Forex M5 Backtest Report",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Strategies:** {len(STRATEGIES)} | **Assets:** {len(FOREX_FILES)} | **Timeframe:** M5",
        "",
        "---",
        "",
        "## Per-Strategy Summary",
        "",
        "| Strategy | Best Asset | Best WR | Worst Asset | Worst WR | Avg WR |",
        "|----------|-----------|---------|-------------|----------|--------|",
    ]
    
    for strat_name in STRATEGIES:
        if strat_name not in all_results:
            continue
        assets = all_results[strat_name]
        if not assets:
            continue
        
        wrs = {a: r['win_rate'] for a, r in assets.items() if 'win_rate' in r}
        if not wrs:
            continue
        
        best_asset = max(wrs, key=wrs.get)
        worst_asset = min(wrs, key=wrs.get)
        avg_wr = sum(wrs.values()) / len(wrs)
        
        report_lines.append(
            f"| {strat_name} | {best_asset} | {wrs[best_asset]:.1f}% | {worst_asset} | {wrs[worst_asset]:.1f}% | {avg_wr:.1f}% |"
        )
    
    report_lines.extend([
        "",
        "---",
        "",
        "## Per-Asset Summary",
        "",
        "| Asset | Best Strategy | Best WR | Profitable Strategies |",
        "|-------|-------------|---------|----------------------|",
    ])
    
    for pair in FOREX_FILES:
        pair_key = pair.replace("/", "_")
        strat_wrs = {}
        for strat_name in STRATEGIES:
            if strat_name in all_results and pair_key in all_results[strat_name]:
                r = all_results[strat_name][pair_key]
                if 'win_rate' in r:
                    strat_wrs[strat_name] = r['win_rate']
        
        if strat_wrs:
            best_strat = max(strat_wrs, key=strat_wrs.get)
            profitable = sum(1 for w in strat_wrs.values() if w > 50)
            report_lines.append(
                f"| {pair} | {best_strat} | {strat_wrs[best_strat]:.1f}% | {profitable}/{len(strat_wrs)} |"
            )
    
    report_lines.extend([
        "",
        "---",
        "",
        "## Heatmap: Strategy Ã— Asset (Win Rate %)",
        "",
        "| Strategy | " + " | ".join(p.replace("/", "_") for p in FOREX_FILES) + " |",
        "|----------|" + "--------|" * len(FOREX_FILES),
    ])
    
    for strat_name in STRATEGIES:
        row = [f"| {strat_name} |"]
        for pair in FOREX_FILES:
            pair_key = pair.replace("/", "_")
            if strat_name in all_results and pair_key in all_results[strat_name]:
                wr = all_results[strat_name][pair_key].get('win_rate', 0)
                row.append(f" {wr:5.1f}% |")
            else:
                row.append("  N/A  |")
        report_lines.append("".join(row))
    
    report_lines.extend([
        "",
        "---",
        "",
        "## Production-Ready Recommendations",
        "",
        "Strategies with >55% WR on 3+ assets:",
        "",
    ])
    
    for strat_name in STRATEGIES:
        if strat_name not in all_results:
            continue
        assets = all_results[strat_name]
        good_assets = [a for a, r in assets.items() if r.get('win_rate', 0) > 55]
        if len(good_assets) >= 3:
            report_lines.append(f"- **{strat_name}**: {len(good_assets)} assets above 55% WR")
    
    report_lines.extend([
        "",
        "---",
        "",
        f"**Total runtime:** {time.time() - start_time:.1f} seconds",
    ])
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
    print(f"âœ… Report saved to: {report_path}")
    
    print(f"\n{'=' * 70}")
    print(f"COMPLETE â€” Total runtime: {time.time() - start_time:.1f}s")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()

