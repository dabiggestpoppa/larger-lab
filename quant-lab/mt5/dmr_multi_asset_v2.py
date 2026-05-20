#!/usr/bin/env python3
"""
DMR Multi-Asset Strategy Tester v2
Handles JPY pairs (2-digit pips) and XAU (different price scale).
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import MetaTrader5 as mt5

TIMEFRAME = mt5.TIMEFRAME_M5
LOT_SIZE = 0.01
FROM_DATE = datetime(2022, 1, 1, tzinfo=timezone.utc)
TO_DATE = datetime(2026, 5, 19, tzinfo=timezone.utc)

# Symbol-specific configs: (pip_multiplier, price_digits)
# Standard forex: 10000 (4 digits), JPY: 100 (2 digits), XAU: 1 (1 digit)
SYMBOL_CONFIGS = {
    'EURUSD.PRO': {'pip_mult': 10000, 'digits': 5, 'name': 'EUR/USD'},
    'USDCHF.PRO': {'pip_mult': 10000, 'digits': 5, 'name': 'USD/CHF'},
    'CHFJPY.PRO': {'pip_mult': 100, 'digits': 3, 'name': 'CHF/JPY'},
    'XAUUSD.PRO': {'pip_mult': 1, 'digits': 2, 'name': 'XAU/USD'},
}

def to_pips(price_diff, pip_mult):
    return price_diff * pip_mult

def to_price(pips, pip_mult):
    return pips / pip_mult

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

def calc_asian_range(df_day, pip_mult):
    asian = df_day[(df_day['est_h'] >= 2) & (df_day['est_h'] < 8)]
    if asian.empty: return None, None, None
    return asian['high'].max(), asian['low'].min(), to_pips(asian['high'].max() - asian['low'].min(), pip_mult)

def manage_trade(post_data, entry, direction, sl, tp, pip_mult):
    for idx, row in post_data.iterrows():
        if direction == 'LONG':
            if row['low'] <= sl:
                return {'pnl_pips': to_pips(sl - entry, pip_mult), 'exit_reason': 'sl'}
            if row['high'] >= tp:
                return {'pnl_pips': to_pips(tp - entry, pip_mult), 'exit_reason': 'tp'}
        else:
            if row['high'] >= sl:
                return {'pnl_pips': to_pips(entry - sl, pip_mult), 'exit_reason': 'sl'}
            if row['low'] <= tp:
                return {'pnl_pips': to_pips(entry - tp, pip_mult), 'exit_reason': 'tp'}
    last = post_data.iloc[-1]
    pnl = to_pips(last['close'] - entry, pip_mult) if direction == 'LONG' else to_pips(entry - last['close'], pip_mult)
    return {'pnl_pips': pnl, 'exit_reason': 'end_data'}

def run_symbol_backtest(df, symbol, config):
    pip_mult = config['pip_mult']
    trades = []
    
    for date in sorted(df['date'].unique()):
        day = df[df['date'] == date]
        ah, al, ar = calc_asian_range(day, pip_mult)
        if ar is None or ar > 45 or ar < 3:
            continue
        
        entry_window = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        direction = None
        p90_time = None
        
        for idx, row in entry_window.iterrows():
            thresh = p90_threshold(row['est_h'])
            if row['body_pips'] >= thresh:
                direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
                p90_time = idx
                break
        
        if direction is None:
            continue
        
        p90_bar = entry_window.loc[p90_time]
        activation = p90_bar['close']
        body_pips = to_pips(abs(p90_bar['close'] - p90_bar['open']), pip_mult)
        deep_state = activation + to_price(body_pips * 2.00, pip_mult) * (1 if direction == 'LONG' else -1)
        kill_switch = activation + to_price(body_pips * 2.20, pip_mult) * (1 if direction == 'LONG' else -1)
        
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
        
        trade = manage_trade(post_entry, deep_state, rev_direction, kill_switch, activation, pip_mult)
        trade['entry_time'] = str(touch_idx)
        trade['pnl_pips'] = round(trade['pnl_pips'], 2)
        trades.append(trade)
    
    if not trades:
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'total_pnl': 0, 'max_dd': 0, 'profit_factor': 0, 'by_year': {}}
    
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
        'name': config['name'],
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
    
    print(f"DMR Multi-Asset Backtest v2 | {len(SYMBOL_CONFIGS)} symbols")
    print(f"Period: {FROM_DATE.strftime('%Y-%m-%d')} to {TO_DATE.strftime('%Y-%m-%d')}")
    print("=" * 75)
    
    all_results = {}
    
    for symbol, config in SYMBOL_CONFIGS.items():
        print(f"\nLoading {symbol} ({config['name']})...")
        rates = mt5.copy_rates_range(symbol, TIMEFRAME, FROM_DATE, TO_DATE)
        
        if rates is None or len(rates) == 0:
            print(f"  NO DATA")
            continue
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
        df.set_index('time', inplace=True)
        df.sort_index(inplace=True)
        df['est_h'] = df.index.map(lambda x: (x.hour - 5) % 24)
        df['date'] = df.index.map(lambda x: (x - pd.Timedelta(hours=5)).date())
        df['body_pips'] = (df['close'] - df['close'].shift(1)).abs() * config['pip_mult']
        df['body_pips'] = df['body_pips'].fillna(0)
        
        print(f"  {len(rates):,} bars | {df['date'].nunique()} days | pip_mult={config['pip_mult']}")
        
        start = time.time()
        result = run_symbol_backtest(df, symbol, config)
        elapsed = time.time() - start
        all_results[symbol] = result
        
        if result['total_trades'] > 0:
            print(f"  Trades: {result['total_trades']} | WR: {result['win_rate']}% | PnL: {result['total_pnl']:+.2f} | PF: {result['profit_factor']} | MaxDD: {result['max_dd']:.2f} | {elapsed:.1f}s")
        else:
            print(f"  NO TRADES | {elapsed:.1f}s")
    
    mt5.shutdown()
    
    # Save
    output_dir = Path(__file__).parent
    json_path = output_dir / "dmr_multi_asset_v2.json"
    with open(json_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    # Summary
    print("\n" + "=" * 75)
    print("📊 MULTI-ASSET DMR BACKTEST SUMMARY")
    print("=" * 75)
    print(f"{'Symbol':<15} {'Name':<10} {'Trades':>7} {'WR':>7} {'PnL':>12} {'PF':>8} {'MaxDD':>8}")
    print("-" * 75)
    
    total_trades = 0
    total_pnl = 0
    
    for sym, r in all_results.items():
        if r['total_trades'] > 0:
            name = SYMBOL_CONFIGS[sym]['name']
            print(f"{sym:<15} {name:<10} {r['total_trades']:>7} {r['win_rate']:>6.1f}% {r['total_pnl']:>+11.2f} {r['profit_factor']:>7.1f} {r['max_dd']:>7.2f}")
            total_trades += r['total_trades']
            total_pnl += r['total_pnl']
        else:
            name = SYMBOL_CONFIGS[sym]['name']
            print(f"{sym:<15} {name:<10} {'NO TRADES':>30}")
    
    print("-" * 75)
    print(f"{'TOTAL':<15} {'':<10} {total_trades:>7} {'':>7} {total_pnl:>+11.2f}")
    print(f"\nResults: {json_path}")
    
    return all_results

if __name__ == "__main__":
    main()
