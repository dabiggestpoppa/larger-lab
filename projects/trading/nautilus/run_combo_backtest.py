"""Run P90 Cascade + 45-Min Add Combo backtest."""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from strategies.p90_cascade_combo import P90CascadeComboStrategy
from data_loader import _parse_csv

# Load EURUSD M5 data
data_path = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")
print(f"Loading {data_path.name}...")
df = _parse_csv(data_path)
print(f"Loaded {len(df):,} bars ({df.index[0]} -> {df.index[-1]})")

# Run combo backtest
strategy = P90CascadeComboStrategy()
results = strategy.run_backtest(df, pair="EUR/USD")

print(f"\n{'='*60}")
print(f"P90 CASCADE + 45-MIN ADD COMBO RESULTS")
print(f"{'='*60}")
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
    print(f"\n  By Activation Type:")
    for at, data in results["by_activation_type"].items():
        print(f"    {at:15s}: {data['trades']} trades | {data['win_rate']}% WR | {data['pnl_pips']} pips")

if "by_exit_reason" in results:
    print(f"\n  By Exit Reason:")
    for reason, count in sorted(results["by_exit_reason"].items(), key=lambda x: -x[1]):
        print(f"    {reason:20s}: {count}")

print(f"{'='*60}")

# Save results
results_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results")
results_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
results_file = results_dir / f"p90_cascade_combo_{timestamp}.json"
save_results = {k: v for k, v in results.items() if k != "trades"}
with open(results_file, "w") as f:
    json.dump(save_results, f, indent=2, default=str)
print(f"\nResults saved to {results_file}")
