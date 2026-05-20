#!/usr/bin/env python3
"""
DMR Multi-Asset Strategy Tester
Runs the DMR strategy on all available forex pairs.
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import MetaTrader5 as mt5

TIMEFRAME = mt5.TIMEFRAME_M5
LOT_SIZE = 0.01
MAGIC_NUMBER = 20260520
FROM_DATE = datetime(2022, 1, 1, tzinfo=timezone.utc)
TO_DATE = datetime(2026, 5, 19, tzinfo=timezone.utc)
SYMBOLS = ['EURUSD.PRO', 'USDCHF.PRO', 'CHFJPY.PRO', 'XAUUSD.PRO']

def to_pips(price_diff): return price_diff * 10000.0
def to_price(pips): return pips / 10000.0

def get_est_hour(utc_dt):
    return (utc_dt.hour - 5) % 24

def p90_threshold(est_hour):
    if est_hour < 2 or est_hour >= 11: return 999.0
    if est_hour < 4: return 4.1
    if est_hour < 6: return 4.6
    if est_hour < 8: return 4.6
    if est_hour < 10: return 5.9
    if est_hour < 11: return 6.2
    return 999.0

def calc_asian_range(df_day):
    asian = df_day[(df_day['est_h'] >= 2) & (df_day['est_h'] < 8)]
    if asian.empty: return None, None, None
    return asian['high'].max(), asian['low'].min(), to_pips(asian['high'].max() - asian['low'].min())

def manage_trade(post_data, entry, direction, sl, tp):
    for idx, row in post_data.iterrows():
        if direction == 'LONG':
            if row['low'] <= sl:
                return {'exit_price': sl, 'pnl_pips': to_pips(sl - entry), 'exit_reason': 'sl'}
            if row['high'] >= tp:
                return {'exit_price': tp, 'pnl_pips': to_pips(tp - entry), 'exit_reason': 'tp'}
        else:
            if row['high'] >= sl:
                return {'exit_price': sl, 'pnl_pips': to_pips(entry - sl), 'exit_reason': 'sl'}
            if row['low'] <= tp:
                return {'exit_price': tp, 'pnl_pips': to_pips(entry - tp), 'exit_reason': 'tp'}
    last = post_data.iloc[-1]
    pnl = to_pips(last['close'] - entry) if direction == 'LONG' else to_pips(entry - last['close'])
    return {'exit_price': last['close'], 'pnl_pips': pnl, 'exit_reason': 'end_data'}

def run_symbol_backtest(df, symbol):
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = df[df['date'] == date]
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue
        
        entry_window = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        direction, p90 = None, None
        p90_time = None
        
        for idx, row in entry_window.iterrows():
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
        post_entry = day[(day.index > touch_idx) & (day['est_h'] < 17)]
        if post_entry.empty:
            continue
        
        trade = manage_trade(post_entry, deep_state, rev_direction, kill_switch, activation)
        trade['entry_time'] = str(touch_idx)
        trade['pnl_pips'] = round(trade['pnl_pips'], 2)
        trades.append(trade)
    
    if not trades:
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'total_pnl': 0, 'max_dd': 0, 'profit_factor': 0}
    
    wins = [t for t in trades if t['pnl_pips'] > 0]
    losses = [t for t in trades if t['pnl_pips'] <= 0]
    total = sum(t['pnl_pips'] for t in trades)
    cum = np.cumsum([t['pnl_pips'] for t in trades])
    peak = np.maximum.accumulate(cum)
    max_dd = float(np.max(peak - cum)) if len(cum) > 0 else 0
    
    gross_profit = sum(t['pnl_pips'] for t in wins) if wins else 0
    gross_loss = abs(sum(t['pnl_pips'] for t in losses)) if losses else 1
    
    by_year = {}
    for t in trades:
        y = t['entry_time'][:4]
        if y not in by_year:
            by_year[y] = {'trades': 0, 'wins': 0, 'pnl': 0}
        by_year[y]['trades'] += 1
        by_year[y]['pnl'] += t['pnl_pips']
        if t['pnl_pips'] > 0:
            by_year[y]['wins'] += 1
    
    return {
        'symbol': symbol,
        'total_trades': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(len(wins)/len(trades)*100, 1),
        'total_pnl': round(total, 2),
        'avg_win': round(np.mean([t['pnl_pips'] for t in wins]), 2) if wins else 0,
        'avg_loss': round(np.mean([t['pnl_pips'] for t in losses]), 2) if losses else 0,
        'max_dd': round(max_dd, 2),
        'profit_factor': round(gross_profit/gross_loss, 2),
        'expectancy': round(total/len(trades), 2),
        'by_year': {k: {'trades': v['trades'], 'wr': round(v['wins']/v['trades']*100,1) if v['trades'] > 0 else 0, 'pnl': round(v['pnl'],2)} for k,v in by_year.items()},
    }

def main():
    if not mt5.initialize():
        print("MT5 init failed")
        return
    
    print(f"Connected to MT5 | Backtesting DMR on {len(SYMBOLS)} symbols")
    print(f"Period: {FROM_DATE.strftime('%Y-%m-%d')} to {TO_DATE.strftime('%Y-%m-%d')}")
    print("=" * 70)
    
    all_results = {}
    
    for symbol in SYMBOLS:
        print(f"\nLoading {symbol}...")
        rates = mt5.copy_rates_range(symbol, TIMEFRAME, FROM_DATE, TO_DATE)
        
        if rates is None or len(rates) == 0:
            print(f"  NO DATA for {symbol}")
            continue
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
        df.set_index('time', inplace=True)
        df.sort_index(inplace=True)
        df['est_h'] = df.index.map(lambda x: (x.hour - 5) % 24)
        df['date'] = df.index.map(lambda x: (x - pd.Timedelta(hours=5)).date())
        df['body_pips'] = (df['close'] - df['close'].shift(1)).abs() * 10000
        df['body_pips'] = df['body_pips'].fillna(0)
        
        print(f"  {len(rates):,} bars | {df['date'].nunique()} trading days")
        
        start = time.time()
        result = run_symbol_backtest(df, symbol)
        elapsed = time.time() - start
        
        all_results[symbol] = result
        
        if result['total_trades'] > 0:
            print(f"  Trades: {result['total_trades']} | WR: {result['win_rate']}% | PnL: {result['total_pnl']:+.2f}p | PF: {result['profit_factor']} | MaxDD: {result['max_dd']:.2f}p | {elapsed:.1f}s")
        else:
            print(f"  NO TRADES | {elapsed:.1f}s")
    
    mt5.shutdown()
    
    # Save results
    output_dir = Path(__file__).parent
    json_path = output_dir / "dmr_multi_asset_results.json"
    with open(json_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    # Print summary table
    print("\n" + "=" * 70)
    print("📊 MULTI-ASSET DMR BACKTEST SUMMARY")
    print("=" * 70)
    print(f"{'Symbol':<15} {'Trades':>7} {'WR':>7} {'PnL':>12} {'PF':>8} {'MaxDD':>8}")
    print("-" * 70)
    
    total_trades = 0
    total_pnl = 0
    
    for sym, r in all_results.items():
        if r['total_trades'] > 0:
            print(f"{sym:<15} {r['total_trades']:>7} {r['win_rate']:>6.1f}% {r['total_pnl']:>+11.2f}p {r['profit_factor']:>7.1f} {r['max_dd']:>7.2f}p")
            total_trades += r['total_trades']
            total_pnl += r['total_pnl']
    
    print("-" * 70)
    print(f"{'TOTAL':<15} {total_trades:>7} {'':>7} {total_pnl:>+11.2f}p")
    print(f"\nResults saved: {json_path}")
    
    return all_results

if __name__ == "__main__":
    main()
