#!/usr/bin/env python3
"""Quick backtest runner for P90 Cascade and Combo strategies."""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from data_loader import _parse_csv

# Load data
data_path = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")
print(f"Loading data from {data_path.name}...")
df = _parse_csv(data_path)
print(f"  Loaded {len(df):,} bars ({df.index[0]} -> {df.index[-1]})")

# ── Run P90 Cascade ─────────────────────────────────────────────────
from strategies.p90_cascade import P90CascadeStrategy

print("\n" + "="*60)
print("RUNNING P90 CASCADE ACTIVATION")
print("="*60)

strategy = P90CascadeStrategy()
results_cascade = strategy.run_backtest(df, pair="EUR/USD")

print(f"\n  Total Trades:   {results_cascade.get('total_trades', 0)}")
print(f"  Wins:           {results_cascade.get('wins', 0)} ({results_cascade.get('win_rate', 0)}%)")
print(f"  Losses:         {results_cascade.get('losses', 0)}")
print(f"  Total P&L:      {results_cascade.get('total_pnl_pips', 0)} pips")
print(f"  Avg Win:        {results_cascade.get('avg_win_pips', 0)} pips")
print(f"  Avg Loss:       {results_cascade.get('avg_loss_pips', 0)} pips")
print(f"  Max Drawdown:   {results_cascade.get('max_drawdown_pips', 0)} pips")
print(f"  Profit Factor:  {results_cascade.get('profit_factor', 0)}")

if "by_activation_type" in results_cascade:
    print(f"\n  By Activation Type:")
    for at, data in results_cascade["by_activation_type"].items():
        print(f"    {at:15s}: {data['trades']} trades | {data['win_rate']}% WR | {data['pnl_pips']} pips")

if "by_exit_reason" in results_cascade:
    print(f"\n  By Exit Reason:")
    for reason, count in sorted(results_cascade["by_exit_reason"].items(), key=lambda x: -x[1]):
        print(f"    {reason:20s}: {count}")

# ── Run P90 Cascade + 45-Min Combo ─────────────────────────────────
from strategies.p90_cascade_combo import P90CascadeComboStrategy

print("\n" + "="*60)
print("RUNNING P90 CASCADE + 45-MIN ADD COMBO")
print("="*60)

combo = P90CascadeComboStrategy()
results_combo = combo.run_backtest(df, pair="EUR/USD")

print(f"\n  Total Trades:   {results_combo.get('total_trades', 0)}")
print(f"  Total Sessions: {results_combo.get('total_sessions', 0)}")
print(f"  Wins:           {results_combo.get('wins', 0)} ({results_combo.get('win_rate', 0)}%)")
print(f"  Losses:         {results_combo.get('losses', 0)}")
print(f"  Total P&L:      {results_combo.get('total_pnl_pips', 0)} pips")
print(f"  Avg Win:        {results_combo.get('avg_win_pips', 0)} pips")
print(f"  Avg Loss:       {results_combo.get('avg_loss_pips', 0)} pips")
print(f"  Max Drawdown:   {results_combo.get('max_drawdown_pips', 0)} pips")
print(f"  Profit Factor:  {results_combo.get('profit_factor', 0)}")

if "by_activation_type" in results_combo:
    print(f"\n  By Activation Type:")
    for at, data in results_combo["by_activation_type"].items():
        print(f"    {at:15s}: {data['trades']} trades | {data['win_rate']}% WR | {data['pnl_pips']} pips")

if "by_exit_reason" in results_combo:
    print(f"\n  By Exit Reason:")
    for reason, count in sorted(results_combo["by_exit_reason"].items(), key=lambda x: -x[1]):
        print(f"    {reason:20s}: {count}")

# ── Save Results ────────────────────────────────────────────────────
results_dir = Path("results")
results_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

cascade_file = results_dir / f"p90_cascade_{timestamp}.json"
with open(cascade_file, "w") as f:
    json.dump(results_cascade, f, indent=2, default=str)

combo_file = results_dir / f"p90_cascade_combo_{timestamp}.json"
with open(combo_file, "w") as f:
    json.dump(results_combo, f, indent=2, default=str)

print(f"\nResults saved to {cascade_file} and {combo_file}")
print("="*60)
