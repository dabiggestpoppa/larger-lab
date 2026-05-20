#!/usr/bin/env python3
"""
MT5 Strategy Tester Bridge
Uses MetaTrader5 Python API to run a Strategy Tester-equivalent backtest
and generates an HTML report matching MT5's native report format.
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

# Config
SYMBOL = "EURUSD.PRO"
TIMEFRAME = mt5.TIMEFRAME_M5
LOT_SIZE = 0.01
MAGIC_NUMBER = 20260520
FROM_DATE = datetime(2022, 1, 1, tzinfo=timezone.utc)
TO_DATE = datetime(2026, 5, 19, tzinfo=timezone.utc)

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

def run_backtest():
    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}")
        return None
    
    terminal = mt5.terminal_info()
    print(f"Connected: {terminal.company} {terminal.name} Build {terminal.build}")
    
    symbol_info = mt5.symbol_info(SYMBOL)
    if symbol_info is None:
        print(f"Symbol {SYMBOL} not found")
        mt5.shutdown()
        return None
    
    print(f"Loading {SYMBOL} M5 data...")
    rates = mt5.copy_rates_range(SYMBOL, TIMEFRAME, FROM_DATE, TO_DATE)
    mt5.shutdown()
    
    if rates is None or len(rates) == 0:
        print("No data loaded")
        return None
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)
    df['est_h'] = df.index.map(lambda x: (x.hour - 5) % 24)
    df['date'] = df.index.map(lambda x: (x - pd.Timedelta(hours=5)).date())
    df['body_pips'] = (df['close'] - df['close'].shift(1)).abs() * 10000
    df['body_pips'] = df['body_pips'].fillna(0)
    
    print(f"Loaded {len(rates):,} bars | {df['date'].nunique()} trading days")
    
    trades = []
    equity_curve = []
    
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
        trade['entry_time'] = touch_idx
        trade['exit_time'] = trade.get('exit_time', post_entry.index[-1])
        trade['pnl_pips'] = round(trade['pnl_pips'], 2)
        trades.append(trade)
        
        cum_pnl = sum(t['pnl_pips'] for t in trades)
        equity_curve.append({'time': str(touch_idx), 'pnl': round(cum_pnl, 2)})
    
    # Results
    if not trades:
        return {'total_trades': 0}
    
    wins = [t for t in trades if t['pnl_pips'] > 0]
    losses = [t for t in trades if t['pnl_pips'] <= 0]
    total = sum(t['pnl_pips'] for t in trades)
    cum = np.cumsum([t['pnl_pips'] for t in trades])
    peak = np.maximum.accumulate(cum)
    max_dd = float(np.max(peak - cum)) if len(cum) > 0 else 0
    
    by_exit = {}
    for t in trades:
        by_exit[t['exit_reason']] = by_exit.get(t['exit_reason'], 0) + 1
    
    by_year = {}
    for t in trades:
        y = str(t['entry_time'])[:4]
        if y not in by_year:
            by_year[y] = {'trades': 0, 'wins': 0, 'pnl': 0}
        by_year[y]['trades'] += 1
        by_year[y]['pnl'] += t['pnl_pips']
        if t['pnl_pips'] > 0:
            by_year[y]['wins'] += 1
    
    gross_profit = sum(t['pnl_pips'] for t in wins) if wins else 0
    gross_loss = abs(sum(t['pnl_pips'] for t in losses)) if losses else 1
    
    results = {
        'symbol': SYMBOL,
        'period': f"{FROM_DATE.strftime('%Y-%m-%d')} to {TO_DATE.strftime('%Y-%m-%d')}",
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
        'by_exit': by_exit,
        'by_year': {k: {'trades': v['trades'], 'wr': round(v['wins']/v['trades']*100,1), 'pnl': round(v['pnl'],2)} for k,v in by_year.items()},
        'equity_curve': equity_curve,
    }
    
    return results, trades

def generate_html_report(results, trades):
    """Generate HTML report matching MT5 Strategy Tester format"""
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>DMR Backtest Report — {results['symbol']}</title>
<style>
body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #1a1a2e; color: #e0e0e0; margin: 20px; }}
h1 {{ color: #6366f1; border-bottom: 2px solid #6366f1; padding-bottom: 10px; }}
h2 {{ color: #818cf8; margin-top: 30px; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
th, td {{ border: 1px solid #333; padding: 8px 12px; text-align: left; }}
th {{ background: #16213e; color: #818cf8; }}
tr:nth-child(even) {{ background: #1a1a2e; }}
tr:nth-child(odd) {{ background: #16213e; }}
.win {{ color: #4ade80; }}
.loss {{ color: #f87171; }}
.metric {{ display: inline-block; margin: 10px 20px 10px 0; padding: 10px 15px; background: #16213e; border-radius: 8px; }}
.metric-label {{ color: #818cf8; font-size: 12px; }}
.metric-value {{ font-size: 18px; font-weight: bold; }}
.positive {{ color: #4ade80; }}
.negative {{ color: #f87171; }}
</style></head><body>
<h1>📊 DMR Strategy Tester Report</h1>
<p><strong>Symbol:</strong> {results['symbol']} M5 | <strong>Period:</strong> {results['period']}</p>

<h2>Summary</h2>
<div class="metric"><div class="metric-label">Total Trades</div><div class="metric-value">{results['total_trades']}</div></div>
<div class="metric"><div class="metric-label">Win Rate</div><div class="metric-value {'positive' if results['win_rate'] >= 90 else ''}">{results['win_rate']}%</div></div>
<div class="metric"><div class="metric-label">Net PnL</div><div class="metric-value {'positive' if results['total_pnl'] > 0 else 'negative'}">{results['total_pnl']:+.2f} pips</div></div>
<div class="metric"><div class="metric-label">Profit Factor</div><div class="metric-value">{results['profit_factor']}</div></div>
<div class="metric"><div class="metric-label">Max Drawdown</div><div class="metric-value negative">{results['max_dd']:.2f} pips</div></div>
<div class="metric"><div class="metric-label">Expectancy</div><div class="metric-value">{results['expectancy']:+.2f} pips</div></div>

<h2>Yearly Breakdown</h2>
<table>
<tr><th>Year</th><th>Trades</th><th>Win Rate</th><th>PnL (pips)</th></tr>"""
    
    for year in sorted(results['by_year'].keys()):
        d = results['by_year'][year]
        color = 'win' if d['wr'] >= 90 else ('loss' if d['wr'] < 50 else '')
        html += f"\n<tr class='{color}'><td>{year}</td><td>{d['trades']}</td><td>{d['wr']}%</td><td>{d['pnl']:+.2f}</td></tr>"
    
    html += f"""
</table>

<h2>Exit Reasons</h2>
<table>
<tr><th>Reason</th><th>Count</th></tr>
"""
    for reason, count in results['by_exit'].items():
        html += f"\n<tr><td>{reason.upper()}</td><td>{count}</td></tr>"
    
    html += f"""
</table>

<h2>Trade List (Last 50)</h2>
<table>
<tr><th>#</th><th>Entry Time</th><th>PnL (pips)</th><th>Exit</th></tr>
"""
    for i, t in enumerate(trades[-50:], start=len(trades)-49):
        color = 'win' if t['pnl_pips'] > 0 else 'loss'
        entry_str = str(t['entry_time'])[:19] if t.get('entry_time') else 'N/A'
        html += f"\n<tr class='{color}'><td>{i}</td><td>{entry_str}</td><td>{t['pnl_pips']:+.2f}</td><td>{t['exit_reason']}</td></tr>"
    
    html += f"""
</table>

<p style="color: #666; margin-top: 30px;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT | DMR Backtest Bridge v2.0</p>
</body></html>"""
    
    return html

if __name__ == "__main__":
    start = time.time()
    result = run_backtest()
    
    if result is None:
        print("Backtest failed")
        sys.exit(1)
    
    results, trades = result
    elapsed = time.time() - start
    
    # Save JSON
    json_path = Path(__file__).parent / "dmr_strategy_tester_bridge.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Generate HTML report
    html = generate_html_report(results, trades)
    html_path = Path(__file__).parent / "DMR_STRATEGY_TESTER_REPORT.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n{'='*60}")
    print(f"DMR STRATEGY TESTER BRIDGE — RESULTS")
    print(f"{'='*60}")
    print(f"Trades: {results['total_trades']} | WR: {results['win_rate']}% | PnL: {results['total_pnl']:+.2f}p")
    print(f"PF: {results['profit_factor']} | MaxDD: {results['max_dd']:.2f}p | {elapsed:.1f}s")
    print(f"Report: {html_path}")
    print(f"JSON: {json_path}")
