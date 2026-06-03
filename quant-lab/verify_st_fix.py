"""Verify ST engine fix produces results matching Nautilus ground truth."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 'quant-lab/configs')

import json
from pathlib import Path
from engines.symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection
from datetime import datetime, timezone, timedelta
import pandas as pd

DATA_DIR = Path('quant-lab/data')

def load_bars_csv(csv_path: Path, max_bars: int = 50000):
    df = pd.read_csv(csv_path, nrows=max_bars)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    elif 'date' in df.columns:
        if 'time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str), utc=True)
        else:
            df['timestamp'] = pd.to_datetime(df['date'], utc=True)
    bars = []
    for _, row in df.iterrows():
        ts = row['timestamp'] if isinstance(row['timestamp'], datetime) else pd.Timestamp(row['timestamp']).to_pydatetime()
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        bars.append(Bar(
            timestamp=ts,
            open=float(row['open']),
            high=float(row['high']),
            low=float(row['low']),
            close=float(row['close']),
        ))
    return bars

def run_engine_backtest(symbol: str, csv_path: Path, pip_size: float = 0.0001, max_bars: int = 50000):
    bars = load_bars_csv(csv_path, max_bars)
    if not bars:
        return None

    e = SymmetryTrapEngine(pip_size=pip_size, symbol=symbol)
    
    trades = []
    for bar in bars:
        sig = e.process_bar(bar)
        if sig and sig.event in ('TP_HIT', 'SL_HIT', 'KILL_SWITCH', 'EWS_EXIT'):
            trades.append({
                'event': sig.event,
                'direction': 'LONG' if sig.direction == TradeDirection.LONG else 'SHORT',
                'entry': sig.entry_price,
                'exit': sig.sl_price if 'SL' in sig.event else sig.tp_price,
                'pnl_pips': round((sig.tp_price - sig.entry_price) / pip_size if sig.event == 'TP_HIT'
                                  else (sig.sl_price - sig.entry_price) / pip_size if sig.event == 'SL_HIT'
                                  else 0, 1),
            })
    
    wins = sum(1 for t in trades if t['pnl_pips'] > 0)
    losses = sum(1 for t in trades if t['pnl_pips'] <= 0)
    total_pnl = sum(t['pnl_pips'] for t in trades)
    
    return {
        'symbol': symbol,
        'trades': len(trades),
        'wins': wins,
        'losses': losses,
        'wr': round(wins / len(trades) * 100, 1) if trades else 0,
        'pnl_pips': round(total_pnl, 1),
    }

# Test on EURUSD
csv = DATA_DIR / 'EURUSD_M5.csv'
if not csv.exists():
    csv = DATA_DIR / 'EURUSDPRO_M5_2023_2026.csv'
if not csv.exists():
    csv = DATA_DIR / 'EURUSDPRO_M5_2023_2025.csv'

print(f"Testing ST engine fix on EURUSD...")
print(f"Data: {csv.name}")

result = run_engine_backtest('EURUSD', csv, pip_size=0.0001, max_bars=50000)
if result:
    print(f"\n=== MT5 ENGINE RESULTS (FIXED) ===")
    print(f"Trades: {result['trades']}")
    print(f"WR: {result['wr']}%")
    print(f"PnL: {result['pnl_pips']}p")
    print(f"Wins: {result['wins']} | Losses: {result['losses']}")
    print(f"\nGround truth (Nautilus Phase 0):")
    print(f"  EURUSD: 2,186 trades | 82.1% WR | +8,585p")
else:
    print("No result")
