#!/usr/bin/env python3
"""
DMR MT5 Strategy Tester — Full History Backtest
=================================================
Runs the DMR strategy using MT5's historical data via the MetaTrader5 Python API.
This replicates what MT5's Strategy Tester does, but outputs full results.

Usage: python dmr_mt5_strategy_tester.py
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pandas as pd
import numpy as np

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import MetaTrader5 as mt5

# ── Configuration ──────────────────────────────────────────────────────────
SYMBOL = "EURUSD.PRO"
TIMEFRAME = mt5.TIMEFRAME_M5
LOT_SIZE = 0.01
MAGIC_NUMBER = 20260519
FROM_DATE = datetime(2022, 1, 1, tzinfo=timezone.utc)
TO_DATE = datetime(2026, 5, 19, tzinfo=timezone.utc)
SPREAD_PIPS = 3.6  # Typical spread for EURUSD.PRO

# ── P90 Thresholds by EST hour ─────────────────────────────────────────────
def p90_threshold(est_hour):
    if est_hour < 2 or est_hour >= 11:
        return 999.0
    if est_hour < 4:  return 4.1
    if est_hour < 6:  return 4.6
    if est_hour < 8:  return 4.6
    if est_hour < 10: return 5.9
    if est_hour < 11: return 6.2
    return 999.0

# ── Utility Functions ──────────────────────────────────────────────────────
def to_pips(price_diff):
    return price_diff * 10000.0

def to_price(pips):
    return pips / 10000.0

def get_est_hour(utc_dt):
    """Convert UTC datetime to EST hour (UTC-5)"""
    est_offset = timedelta(hours=-5)
    est_dt = utc_dt + est_offset
    return est_dt.hour

def calc_asian_range(df_day):
    """Calculate Asian Range (2 AM - 8 AM EST)"""
    asian = df_day[(df_day['est_h'] >= 2) & (df_day['est_h'] < 8)]
    if asian.empty:
        return None, None, None
    ah = asian['high'].max()
    al = asian['low'].min()
    ar = to_pips(ah - al)
    return ah, al, ar

def manage_trade(post_data, entry, direction, sl, tp):
    """Simulate trade management — check each bar for SL/TP hit"""
    for idx, row in post_data.iterrows():
        if direction == 'LONG':
            # Check SL first (low <= sl)
            if row['low'] <= sl:
                pnl = to_pips(sl - entry)
                return {'exit_price': sl, 'pnl_pips': pnl, 'exit_reason': 'sl', 'exit_time': idx}
            # Check TP (high >= tp)
            if row['high'] >= tp:
                pnl = to_pips(tp - entry)
                return {'exit_price': tp, 'pnl_pips': pnl, 'exit_reason': 'tp', 'exit_time': idx}
        else:  # SHORT
            # Check SL first (high >= sl)
            if row['high'] >= sl:
                pnl = to_pips(entry - sl)
                return {'exit_price': sl, 'pnl_pips': pnl, 'exit_reason': 'sl', 'exit_time': idx}
            # Check TP (low <= tp)
            if row['low'] <= tp:
                pnl = to_pips(entry - tp)
                return {'exit_price': tp, 'pnl_pips': pnl, 'exit_reason': 'tp', 'exit_time': idx}
    
    # Hard exit at end of data
    last = post_data.iloc[-1]
    last_price = last['close']
    if direction == 'LONG':
        pnl = to_pips(last_price - entry)
    else:
        pnl = to_pips(entry - last_price)
    return {'exit_price': last_price, 'pnl_pips': pnl, 'exit_reason': 'end_data', 'exit_time': post_data.index[-1]}

def calc_results(trades, strategy_name):
    """Calculate comprehensive results"""
    if not trades:
        return {'strategy': strategy_name, 'total_trades': 0}
    
    wins = [t for t in trades if t['pnl_pips'] > 0]
    losses = [t for t in trades if t['pnl_pips'] <= 0]
    total_pnl = sum(t['pnl_pips'] for t in trades)
    
    # Max drawdown
    cumulative = np.cumsum([t['pnl_pips'] for t in trades])
    peak = np.maximum.accumulate(cumulative)
    drawdown = peak - cumulative
    max_dd = float(np.max(drawdown)) if len(drawdown) > 0 else 0
    
    # Exit reasons
    by_exit = {}
    for t in trades:
        reason = t['exit_reason']
        by_exit[reason] = by_exit.get(reason, 0) + 1
    
    # By year
    by_year = {}
    for t in trades:
        year = t['entry_time'][:4] if isinstance(t['entry_time'], str) else str(t['entry_time'])[:4]
        if year not in by_year:
            by_year[year] = {'trades': 0, 'wins': 0, 'pnl': 0}
        by_year[year]['trades'] += 1
        by_year[year]['pnl'] += t['pnl_pips']
        if t['pnl_pips'] > 0:
            by_year[year]['wins'] += 1
    
    # By month
    by_month = {}
    for t in trades:
        month = t['entry_time'][:7] if isinstance(t['entry_time'], str) else str(t['entry_time'])[:7]
        if month not in by_month:
            by_month[month] = {'trades': 0, 'wins': 0, 'pnl': 0}
        by_month[month]['trades'] += 1
        by_month[month]['pnl'] += t['pnl_pips']
        if t['pnl_pips'] > 0:
            by_month[month]['wins'] += 1
    
    # Consecutive wins/losses
    max_consec_wins = 0
    max_consec_losses = 0
    curr_wins = 0
    curr_losses = 0
    for t in trades:
        if t['pnl_pips'] > 0:
            curr_wins += 1
            curr_losses = 0
            max_consec_wins = max(max_consec_wins, curr_wins)
        else:
            curr_losses += 1
            curr_wins = 0
            max_consec_losses = max(max_consec_losses, curr_losses)
    
    # Profit factor
    gross_profit = sum(t['pnl_pips'] for t in wins) if wins else 0
    gross_loss = abs(sum(t['pnl_pips'] for t in losses)) if losses else 1
    pf = gross_profit / gross_loss if gross_loss > 0 else 999
    
    return {
        'strategy': strategy_name,
        'total_trades': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(len(wins) / len(trades) * 100, 1) if trades else 0,
        'total_pnl_pips': round(total_pnl, 2),
        'avg_win': round(np.mean([t['pnl_pips'] for t in wins]), 2) if wins else 0,
        'avg_loss': round(np.mean([t['pnl_pips'] for t in losses]), 2) if losses else 0,
        'max_drawdown_pips': round(max_dd, 2),
        'profit_factor': round(pf, 2),
        'expectancy': round(total_pnl / len(trades), 2) if trades else 0,
        'gross_profit': round(gross_profit, 2),
        'gross_loss': round(gross_loss, 2),
        'max_consec_wins': max_consec_wins,
        'max_consec_losses': max_consec_losses,
        'by_exit': by_exit,
        'by_year': {k: {'trades': v['trades'], 'wins': v['wins'], 'wr': round(v['wins']/v['trades']*100, 1) if v['trades'] > 0 else 0, 'pnl': round(v['pnl'], 2)} for k, v in by_year.items()},
    }

# ── Main Backtest ──────────────────────────────────────────────────────────
def run_backtest():
    print("=" * 60)
    print("DMR MT5 Strategy Tester — Full History Backtest")
    print("=" * 60)
    
    # Connect to MT5
    if not mt5.initialize():
        print(f"❌ MT5 initialize failed: {mt5.last_error()}")
        return None
    
    # Get terminal info
    terminal = mt5.terminal_info()
    print(f"✅ Connected: {terminal.company} {terminal.name} Build {terminal.build}")
    
    # Check symbol
    symbol_info = mt5.symbol_info(SYMBOL)
    if symbol_info is None:
        print(f"❌ Symbol {SYMBOL} not found. Available symbols:")
        symbols = mt5.symbols_get()
        for s in symbols:
            if "EURUSD" in s.name:
                print(f"  {s.name}")
        mt5.shutdown()
        return None
    
    print(f"✅ Symbol: {SYMBOL} | Spread: {symbol_info.spread} | Digits: {symbol_info.digits}")
    
    # Load historical data
    print(f"\n📊 Loading {SYMBOL} M5 data from {FROM_DATE} to {TO_DATE}...")
    rates = mt5.copy_rates_range(SYMBOL, TIMEFRAME, FROM_DATE, TO_DATE)
    
    if rates is None or len(rates) == 0:
        print(f"❌ No data loaded: {mt5.last_error()}")
        mt5.shutdown()
        return None
    
    print(f"✅ Loaded {len(rates):,} M5 bars")
    
    # Convert to DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)
    
    # Add EST hour
    df['est_h'] = df.index.map(lambda x: (x.hour - 5) % 24)
    df['date'] = df.index.map(lambda x: (x - pd.Timedelta(hours=5)).date())
    df['body_pips'] = (df['close'] - df['close'].shift(1)).abs() * 10000
    df['body_pips'] = df['body_pips'].fillna(0)
    
    print(f"  Date range: {df.index[0]} → {df.index[-1]}")
    print(f"  Trading days: {df['date'].nunique()}")
    
    # ── Run DMR Strategy ────────────────────────────────────────────────
    trades = []
    skip_stats = {'no_asian': 0, 'ar_too_big': 0, 'ar_too_small': 0, 'no_p90': 0, 'no_ds_touch': 0}
    
    print(f"\n🔄 Running DMR strategy...")
    
    for date in sorted(df['date'].unique()):
        day = df[df['date'] == date]
        
        # Asian Range filter
        ah, al, ar = calc_asian_range(day)
        if ar is None:
            skip_stats['no_asian'] += 1
            continue
        if ar > 45:
            skip_stats['ar_too_big'] += 1
            continue
        if ar < 3:
            skip_stats['ar_too_small'] += 1
            continue
        
        # Find P90 signal (2-11 AM EST)
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
            skip_stats['no_p90'] += 1
            continue
        
        activation = p90['close']
        body_pips = to_pips(abs(p90['close'] - p90['open']))
        
        # Extension levels
        deep_state = activation + to_price(body_pips * 2.00) * (1 if direction == 'LONG' else -1)
        kill_switch = activation + to_price(body_pips * 2.20) * (1 if direction == 'LONG' else -1)
        
        # Wait for Deep State touch after P90
        post_p90 = day[(day.index > p90_time) & (day['est_h'] < 12)]
        if post_p90.empty:
            skip_stats['no_ds_touch'] += 1
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
            skip_stats['no_ds_touch'] += 1
            continue
        
        # Mean reversion: trade AGAINST P90 direction
        rev_direction = 'SHORT' if direction == 'LONG' else 'LONG'
        rev_entry = deep_state
        rev_sl = kill_switch
        rev_tp = activation
        
        # Manage trade from touch point
        post_entry = day[(day.index > touch_idx) & (day['est_h'] < 17)]
        if post_entry.empty:
            continue
        
        trade = manage_trade(post_entry, rev_entry, rev_direction, rev_sl, rev_tp)
        if trade:
            trade['entry_time'] = str(touch_idx)
            trade['p90_direction'] = direction
            trade['rev_direction'] = rev_direction
            trade['ar_pips'] = ar
            trade['body_pips'] = body_pips
            trade['activation'] = activation
            trade['deep_state'] = deep_state
            trade['kill_switch'] = kill_switch
            trades.append(trade)
    
    # Calculate results
    results = calc_results(trades, "Deep_Mean_Reversion")
    results['symbol'] = SYMBOL
    results['timeframe'] = 'M5'
    results['period'] = f"{FROM_DATE.strftime('%Y-%m-%d')} to {TO_DATE.strftime('%Y-%m-%d')}"
    results['total_bars'] = len(rates)
    results['trading_days'] = df['date'].nunique()
    results['skip_stats'] = skip_stats
    results['spread_pips'] = SPREAD_PIPS
    
    # Add spread-adjusted PnL
    total_spread_cost = results['total_trades'] * SPREAD_PIPS
    results['spread_cost_pips'] = total_spread_cost
    results['net_pnl_pips'] = round(results['total_pnl_pips'] - total_spread_cost, 2)
    results['net_win_rate'] = results['win_rate']  # Same win rate, but net PnL is lower
    
    # Estimate dollar PnL (0.01 lots on EUR/USD ≈ $0.10 per pip)
    results['estimated_gross_pnl_usd'] = round(results['total_pnl_pips'] * 0.10, 2)
    results['estimated_spread_cost_usd'] = round(total_spread_cost * 0.10, 2)
    results['estimated_net_pnl_usd'] = round(results['net_pnl_pips'] * 0.10, 2)
    
    mt5.shutdown()
    
    return results, trades

# ── Output ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    start_time = time.time()
    result = run_backtest()
    elapsed = time.time() - start_time
    
    if result is None:
        print("❌ Backtest failed")
        sys.exit(1)
    
    results, trades = result
    
    # Save JSON results
    output_dir = Path(__file__).parent
    json_path = output_dir / "dmr_mt5_strategy_tester_results.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 DMR MT5 STRATEGY TESTER RESULTS")
    print("=" * 60)
    print(f"Symbol:        {results['symbol']} {results['timeframe']}")
    print(f"Period:        {results['period']}")
    print(f"Total Bars:    {results['total_bars']:,}")
    print(f"Trading Days:  {results['trading_days']}")
    print(f"Spread:        {results['spread_pips']} pips")
    print("-" * 60)
    print(f"Total Trades:  {results['total_trades']}")
    print(f"Wins:          {results['wins']}")
    print(f"Losses:        {results['losses']}")
    print(f"Win Rate:      {results['win_rate']}%")
    print(f"Gross PnL:     {results['total_pnl_pips']:+.2f} pips")
    print(f"Spread Cost:   -{results['spread_cost_pips']:.2f} pips ({results['total_trades']} × {results['spread_pips']}p)")
    print(f"Net PnL:       {results['net_pnl_pips']:+.2f} pips")
    print(f"Avg Win:       {results['avg_win']:+.2f} pips")
    print(f"Avg Loss:      {results['avg_loss']:+.2f} pips")
    print(f"Max DD:        {results['max_drawdown_pips']:.2f} pips")
    print(f"Profit Factor: {results['profit_factor']}")
    print(f"Expectancy:    {results['expectancy']:+.2f} pips/trade")
    print(f"Max Cons Wins: {results['max_consec_wins']}")
    print(f"Max Cons Loss: {results['max_consec_losses']}")
    print("-" * 60)
    print(f"Gross PnL:     ${results['estimated_gross_pnl_usd']:+.2f} (0.01 lots)")
    print(f"Spread Cost:   -${results['estimated_spread_cost_usd']:.2f}")
    print(f"Net PnL:       ${results['estimated_net_pnl_usd']:+.2f} (0.01 lots)")
    print("-" * 60)
    print(f"Exit Reasons:  {results['by_exit']}")
    print(f"\nBy Year:")
    for year, data in sorted(results['by_year'].items()):
        print(f"  {year}: {data['trades']} trades | {data['wr']}% WR | {data['pnl']:+.2f}p")
    print("-" * 60)
    print(f"Skip Stats:    {results['skip_stats']}")
    print(f"\n⏱️  Completed in {elapsed:.1f}s")
    print(f"📄 Results saved: {json_path}")
    print("=" * 60)
