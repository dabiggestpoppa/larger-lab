#!/usr/bin/env python3
"""
Run all CEREBUS strategy backtests on prepared data.
This is the main entry point for Hermes/OpenClaw to trigger backtests.

Usage:
    python -m nautilus.run_all_backtests
    python -m nautilus.run_all_backtests --symbol EURUSD --timeframe M5
    python -m nautilus.run_all_backtests --strategy symmetry_trap
"""
import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

DATA_DIR = Path(__file__).parent / "data"
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

RESULTS_FILE = REPORTS_DIR / "backtest_results.json"


def load_data(symbol="EURUSD", timeframe="M5"):
    """Load prepared parquet data for a symbol/timeframe."""
    # Try different naming patterns
    patterns = [
        DATA_DIR / f"{symbol}_{timeframe}.parquet",
        DATA_DIR / f"{symbol}!_{timeframe}.parquet",
        DATA_DIR / f"EUR_USD_{timeframe}.parquet",
    ]
    for path in patterns:
        if path.exists():
            return pd.read_parquet(path)
    
    # Try CSV fallback
    csv_patterns = [
        DATA_DIR / f"{symbol}_{timeframe}.csv",
        DATA_DIR / f"{symbol}!_{timeframe}.csv",
    ]
    for path in csv_patterns:
        if path.exists():
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            return df
    
    # Try to find any matching file
    for f in DATA_DIR.glob(f"*{symbol}*{timeframe}*"):
        if f.suffix == '.parquet':
            return pd.read_parquet(f)
        elif f.suffix == '.csv':
            return pd.read_csv(f, index_col=0, parse_dates=True)
    
    return None


def run_symmetry_trade_backtest(df, symbol="EURUSD", tier="T2"):
    """
    Simplified Symmetry Trap backtest using pandas.
    Implements the 3-layer CEREBUS model directly on DataFrame data.
    """
    if df is None or len(df) < 100:
        return {"error": "Insufficient data"}
    
    # Tier config (from CEREBUS manual page 140)
    tier_config = {
        "T1": {"atom_tp": 10, "trig": 12, "sl_pips": 4},
        "T2": {"atom_tp": 12, "trig": 15, "sl_pips": 6},
        "T3": {"atom_tp": 15, "trig": 19, "sl_pips": 8},
    }
    tc = tier_config.get(tier, tier_config["T2"])
    
    # Ensure UTC index
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    
    df['hour_utc'] = df.index.hour
    df['date'] = df.index.date
    
    trades = []
    position = None  # {'side': 'buy'/'sell', 'entry': price, 'sl': price, 'tp': price, 'size': lots}
    
    asian_high = None
    asian_low = None
    asian_range = None
    bias_locked = False
    daily_direction = 0
    loop_count = 0
    daily_pnl = 0
    last_date = None
    
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]
        hour = row['hour_utc']
        date = row['date']
        
        # New day reset
        if date != last_date:
            asian_high = None
            asian_low = None
            asian_range = None
            bias_locked = False
            daily_direction = 0
            loop_count = 0
            daily_pnl = 0
            last_date = date
        
        o, h, l, c = row['open'], row['high'], row['low'], row['close']
        po, pc = prev['open'], prev['close']
        
        # Asian session: measure range (19:00-03:00 UTC)
        if (hour >= 19 or hour < 3):
            if asian_high is None:
                asian_high = h
                asian_low = l
            else:
                asian_high = max(asian_high, h)
                asian_low = min(asian_low, l)
            continue
        
        # End of Asian: classify tier
        if asian_high is not None and asian_range is None:
            asian_range = (asian_high - asian_low) / (df['close'].iloc[:i].mean() * 0.0001)  # approx pips
            if asian_range < 20:
                tc = tier_config["T1"]
            elif asian_range <= 30:
                tc = tier_config["T2"]
            elif asian_range <= 45:
                tc = tier_config["T3"]
            else:
                tc = None  # NO-GO
            bias_locked = True
        
        if tc is None:
            continue
        
        # Hard exit at 17:00 UTC (12PM EST)
        if hour >= 17 and position is not None:
            if position['side'] == 'buy':
                pnl = (c - position['entry']) * position['size'] * 100000
            else:
                pnl = (position['entry'] - c) * position['size'] * 100000
            daily_pnl += pnl
            trades.append({
                'exit_time': str(df.index[i]), 'side': position['side'],
                'entry': position['entry'], 'exit': c, 'pnl': round(pnl, 2),
                'reason': 'hard_exit'
            })
            position = None
            loop_count = 0
            continue
        
        # Bias window: 08:00-17:00 UTC
        if hour < 8 or hour >= 17:
            continue
        
        if loop_count >= 8:
            continue
        
        if position is not None:
            # Check SL (close back inside Asian band)
            if position['side'] == 'buy' and c < asian_low:
                pnl = (c - position['entry']) * position['size'] * 100000
                daily_pnl += pnl
                trades.append({
                    'exit_time': str(df.index[i]), 'side': position['side'],
                    'entry': position['entry'], 'exit': c, 'pnl': round(pnl, 2),
                    'reason': 'sl_asian_band'
                })
                position = None
                continue
            elif position['side'] == 'sell' and c > asian_high:
                pnl = (position['entry'] - c) * position['size'] * 100000
                daily_pnl += pnl
                trades.append({
                    'exit_time': str(df.index[i]), 'side': position['side'],
                    'entry': position['entry'], 'exit': c, 'pnl': round(pnl, 2),
                    'reason': 'sl_asian_band'
                })
                position = None
                continue
            
            # Check TP
            if position['side'] == 'buy' and c >= position['tp']:
                pnl = (c - position['entry']) * position['size'] * 100000
                daily_pnl += pnl
                trades.append({
                    'exit_time': str(df.index[i]), 'side': position['side'],
                    'entry': position['entry'], 'exit': c, 'pnl': round(pnl, 2),
                    'reason': 'tp'
                })
                position = None
                continue
            elif position['side'] == 'sell' and c <= position['tp']:
                pnl = (position['entry'] - c) * position['size'] * 100000
                daily_pnl += pnl
                trades.append({
                    'exit_time': str(df.index[i]), 'side': position['side'],
                    'entry': position['entry'], 'exit': c, 'pnl': round(pnl, 2),
                    'reason': 'tp'
                })
                position = None
                continue
            continue
        
        # Entry logic: Impulse + pullback
        if bias_locked and asian_high is not None:
            # Bullish impulse: price drops below Asian low by trig threshold
            trig_points = tc['trig'] * 10 * 0.0001  # convert pips to price
            if l <= asian_low - trig_points:
                # Wait for pullback (opposite close)
                if pc < po:  # red candle = pullback
                    entry = c
                    sl = entry - tc['sl_pips'] * 10 * 0.0001
                    tp = entry + tc['atom_tp'] * 10 * 0.0001
                    position = {'side': 'buy', 'entry': entry, 'sl': sl, 'tp': tp, 'size': 0.1}
                    loop_count += 1
                    continue
            
            # Bearish impulse: price rises above Asian high by trig threshold
            if h >= asian_high + trig_points:
                if pc > po:  # green candle = pullback
                    entry = c
                    sl = entry + tc['sl_pips'] * 10 * 0.0001
                    tp = entry - tc['atom_tp'] * 10 * 0.0001
                    position = {'side': 'sell', 'entry': entry, 'sl': sl, 'tp': tp, 'size': 0.1}
                    loop_count += 1
                    continue
    
    # Calculate metrics
    if not trades:
        return {"error": "No trades generated", "total_trades": 0}
    
    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    
    total_pnl = sum(pnls)
    win_rate = len(wins) / len(pnls) * 100 if pnls else 0
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    
    # Max drawdown
    cumulative = [0]
    for p in pnls:
        cumulative.append(cumulative[-1] + p)
    peak = cumulative[0]
    max_dd = 0
    for v in cumulative:
        if v > peak:
            peak = v
        dd = v - peak
        if dd < max_dd:
            max_dd = dd
    
    # Profit factor
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    return {
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "total_pnl": round(total_pnl, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "max_drawdown": round(max_dd, 2),
        "profit_factor": round(profit_factor, 2),
        "trades": trades[:50],  # First 50 trades for inspection
    }


def main():
    parser = argparse.ArgumentParser(description="Run CEREBUS strategy backtests")
    parser.add_argument("--symbol", default="EURUSD", help="Symbol to test")
    parser.add_argument("--timeframe", default="M5", help="Timeframe (M1/M5/H1)")
    parser.add_argument("--strategy", default="symmetry_trap", help="Strategy to run")
    parser.add_argument("--tier", default="T2", help="Tier (T1/T2/T3)")
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"🧪 CEREBUS BACKTEST — {args.strategy}")
    print(f"{'='*60}")
    print(f"  Symbol:    {args.symbol}")
    print(f"  Timeframe: {args.timeframe}")
    print(f"  Tier:      {args.tier}")
    print(f"{'='*60}\n")
    
    # Load data
    print(f"📂 Loading data for {args.symbol} {args.timeframe}...")
    df = load_data(args.symbol, args.timeframe)
    
    if df is None:
        print(f"❌ No data found for {args.symbol} {args.timeframe}")
        print(f"   Run prep_data.py first to convert CSV files")
        return
    
    print(f"  ✅ Loaded {len(df):,} bars ({df.index[0]} → {df.index[-1]})")
    
    # Run backtest
    print(f"\n🔄 Running {args.strategy} backtest...")
    
    if args.strategy == "symmetry_trap":
        result = run_symmetry_trade_backtest(df, args.symbol, args.tier)
    else:
        print(f"❌ Unknown strategy: {args.strategy}")
        return
    
    # Display results
    if "error" in result:
        print(f"\n❌ {result['error']}")
        return
    
    print(f"\n{'='*60}")
    print(f"📊 BACKTEST RESULTS")
    print(f"{'='*60}")
    print(f"  Total Trades:   {result['total_trades']}")
    print(f"  Wins:           {result['wins']} ({result['win_rate']}%)")
    print(f"  Losses:         {result['losses']}")
    print(f"  Total P&L:      ${result['total_pnl']:,.2f}")
    print(f"  Avg Win:        ${result['avg_win']:,.2f}")
    print(f"  Avg Loss:       ${result['avg_loss']:,.2f}")
    print(f"  Max Drawdown:   ${result['max_drawdown']:,.2f}")
    print(f"  Profit Factor:  {result['profit_factor']}")
    print(f"{'='*60}")
    
    # Save results
    result['symbol'] = args.symbol
    result['timeframe'] = args.timeframe
    result['strategy'] = args.strategy
    result['tier'] = args.tier
    result['timestamp'] = datetime.now().isoformat()
    result['data_bars'] = len(df)
    result['data_start'] = str(df.index[0])
    result['data_end'] = str(df.index[-1])
    
    report_path = REPORTS_DIR / f"{args.strategy}_{args.symbol}_{args.timeframe}_{args.tier}.json"
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n📄 Report saved: {report_path}")
    
    # Update master results
    all_results = {}
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE) as f:
            all_results = json.load(f)
    all_results[f"{args.symbol}_{args.timeframe}_{args.tier}"] = result
    with open(RESULTS_FILE, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    return result


if __name__ == "__main__":
    main()
