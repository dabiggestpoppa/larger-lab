#!/usr/bin/env python3
"""
P90 Cascade Activation — Backtest Runner
=========================================

Runs the P90 Cascade Activation strategy on EUR/USD M5 data
and outputs comprehensive performance reports.

Usage:
    python run_cascade_backtest.py                  # Full backtest
    python run_cascade_backtest.py --quick          # Quick test (10K bars)
    python run_cascade_backtest.py --data <path>    # Custom data file

Output:
    - Console: formatted performance summary
    - File: JSON results in quant-lab/backtests/
"""
import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd

# ── Path Setup ──────────────────────────────────────────────────────────────
STRATEGY_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
sys.path.insert(0, str(STRATEGY_DIR))

from p90_cascade_activation import (
    P90CascadeActivationStrategy,
    P90CascadeConfig,
)


# ── CSV Parser (standalone — no nautilus_trader dependency) ─────────────────

def _fix_ox_line_wrapping(lines):
    """Fix OX Securities CSV where CLOSE value wraps to next line."""
    fixed = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if i + 1 < len(lines) and re.match(r'^\d{4}\.\d{2}\.\d{2}', lines[i + 1]):
            parts = line.strip().split()
            if len(parts) >= 8:
                fixed.append(line)
            else:
                merged = line.strip() + " " + lines[i + 1].strip()
                fixed.append(merged)
                i += 1
        else:
            fixed.append(line)
        i += 1
    return fixed


def parse_csv(filepath: Path) -> pd.DataFrame:
    """
    Parse forex.com or OX Securities CSV into DataFrame.
    Compatible with the data_loader._parse_csv format.
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        raw_lines = f.readlines()

    data_lines = [l for l in raw_lines[1:] if l.strip()]
    data_lines = _fix_ox_line_wrapping(data_lines)

    records = []
    for line in data_lines:
        parts = line.strip().split()
        if len(parts) < 7:
            continue
        try:
            date_str, time_str = parts[0], parts[1]
            open_val, high_val = float(parts[2]), float(parts[3])
            low_val, close_val = float(parts[4]), float(parts[5])
            tick_vol = int(parts[6]) if len(parts) > 6 else 0
            ts = datetime.strptime(f"{date_str} {time_str}", "%Y.%m.%d %H:%M:%S")
            records.append({
                "timestamp": ts, "open": open_val, "high": high_val,
                "low": low_val, "close": close_val,
                "tick_volume": tick_vol,
            })
        except (ValueError, IndexError):
            continue

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)
    return df


# ── Backtest Runner ─────────────────────────────────────────────────────────

def run_backtest(data_path: Path, pair: str = "EUR/USD",
                 max_bars: int = None, config: P90CascadeConfig = None) -> dict:
    """
    Run P90 Cascade Activation backtest.

    Args:
        data_path: Path to CSV data file
        pair: Trading pair
        max_bars: Limit bars for quick testing
        config: Custom config (uses default if None)

    Returns:
        Dict with backtest results
    """
    print(f"📂 Loading data from {data_path.name}...")
    df = parse_csv(data_path)

    if df.empty:
        print("❌ No data parsed from file")
        return {"error": "No data parsed"}

    print(f"  ✅ Loaded {len(df):,} bars ({df.index[0]} → {df.index[-1]})")

    if max_bars and len(df) > max_bars:
        df = df.tail(max_bars).copy()
        print(f"  ⚡ Quick mode: using last {max_bars:,} bars")

    strategy = P90CascadeActivationStrategy(config=config or P90CascadeConfig())
    results = strategy.run_backtest(df, pair=pair)

    return results


def print_results(results: dict):
    """Print formatted backtest results."""
    print(f"\n{'='*60}")
    print(f"📊 P90 CASCADE ACTIVATION BACKTEST RESULTS")
    print(f"{'='*60}")
    print(f"  Strategy:       {results.get('strategy', 'N/A')}")
    print(f"  Pair:           {results.get('pair', 'N/A')}")
    print(f"  Total Trades:   {results.get('total_trades', 0)}")
    print(f"  Total Sessions: {results.get('total_sessions', 0)}")
    print(f"  Wins:           {results.get('wins', 0)} ({results.get('win_rate', 0)}%)")
    print(f"  Losses:         {results.get('losses', 0)}")
    print(f"  Total P&L:      {results.get('total_pnl_pips', 0)} pips")
    print(f"  Avg Win:        {results.get('avg_win_pips', 0)} pips")
    print(f"  Avg Loss:       {results.get('avg_loss_pips', 0)} pips")
    print(f"  Max Drawdown:   {results.get('max_drawdown_pips', 0)} pips")
    print(f"  Profit Factor:  {results.get('profit_factor', 0)}")

    if "by_activation_type" in results:
        print(f"\n  ── By Activation Type ──")
        for at, data in results["by_activation_type"].items():
            print(f"    {at:15s}: {data['trades']:3d} trades | "
                  f"{data['win_rate']:5.1f}% WR | "
                  f"{data['pnl_pips']:+7.2f} pips")

    if "by_exit_reason" in results:
        print(f"\n  ── By Exit Reason ──")
        for reason, count in sorted(results["by_exit_reason"].items(), key=lambda x: -x[1]):
            print(f"    {reason:25s}: {count}")

    print(f"{'='*60}")


def save_results(results: dict, output_dir: Path) -> Path:
    """Save results to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"p90_cascade_activation_{timestamp}.json"

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    return results_file


def main():
    parser = argparse.ArgumentParser(description="P90 Cascade Activation Backtest Runner")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to CSV data file (default: Downloads/EURUSD M5)")
    parser.add_argument("--quick", action="store_true",
                        help="Quick test with 10K bars")
    parser.add_argument("--max-bars", type=int, default=None,
                        help="Max bars to use")
    parser.add_argument("--pair", type=str, default="EUR/USD",
                        help="Trading pair (default: EUR/USD)")
    args = parser.parse_args()

    # Default data path
    if args.data:
        data_path = Path(args.data)
    else:
        data_path = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")

    if not data_path.exists():
        print(f"❌ Data file not found: {data_path}")
        print("   Use --data <path> to specify a custom data file")
        sys.exit(1)

    # Determine max bars
    max_bars = args.max_bars
    if args.quick:
        max_bars = 10000

    # Run backtest
    results = run_backtest(data_path, pair=args.pair, max_bars=max_bars)

    # Print results
    print_results(results)

    # Save results
    output_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtests")
    results_file = save_results(results, output_dir)
    print(f"\n💾 Results saved to {results_file}")

    # Return exit code based on results
    if results.get("total_trades", 0) == 0:
        print("\n⚠️  No trades generated — check data and parameters")
        sys.exit(1)

    print(f"\n✅ Backtest complete: {results.get('total_trades', 0)} trades, "
          f"{results.get('win_rate', 0)}% WR, "
          f"{results.get('total_pnl_pips', 0)} pips")


if __name__ == "__main__":
    main()
