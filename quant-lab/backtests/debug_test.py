"""Quick debug test for P90 Cascade Activation strategy."""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

STRATEGY_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
sys.path.insert(0, str(STRATEGY_DIR))

from p90_cascade_activation import P90CascadeActivationStrategy, P90CascadeConfig

# Parse CSV
data_path = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")
with open(data_path, 'r', encoding='utf-8', errors='ignore') as f:
    raw = f.readlines()
records = []
for line in raw[1:]:
    parts = line.strip().split()
    if len(parts) < 7:
        continue
    try:
        ts = datetime.strptime(f"{parts[0]} {parts[1]}", "%Y.%m.%d %H:%M:%S")
        records.append({"timestamp": ts, "open": float(parts[2]),
                        "high": float(parts[3]), "low": float(parts[4]),
                        "close": float(parts[5])})
    except (ValueError, IndexError):
        continue
df = pd.DataFrame(records)
df.set_index("timestamp", inplace=True)
df.sort_index(inplace=True)

# Test on first 5 days
df5 = df[df.index < datetime(2023, 1, 7)].copy()
print(f"Testing on {len(df5)} bars: {df5.index[0]} -> {df5.index[-1]}")

# Check Asian range for day 1 (Jan 2)
jan2 = df5[df5.index.date == datetime(2023, 1, 2).date()]
jan2_asian = jan2[((jan2.index.hour - 5 + 24) % 24 >= 19) | ((jan2.index.hour - 5 + 24) % 24 < 3)]
print(f"\nJan 2 bars: {len(jan2)}, Asian bars: {len(jan2_asian)}")
if len(jan2_asian) > 0:
    ah = jan2_asian['high'].max()
    al = jan2_asian['low'].min()
    print(f"  Asian High: {ah:.5f}, Low: {al:.5f}, Range: {(ah-al)*10000:.1f} pips")

# Jan 3
jan3 = df5[df5.index.date == datetime(2023, 1, 3).date()]
jan3_asian = jan3[((jan3.index.hour - 5 + 24) % 24 >= 19) | ((jan3.index.hour - 5 + 24) % 24 < 3)]
jan3_entry = jan3[((jan3.index.hour - 5 + 24) % 24 >= 2) & ((jan3.index.hour - 5 + 24) % 24 < 11)]
print(f"\nJan 3 bars: {len(jan3)}, Asian: {len(jan3_asian)}, Entry: {len(jan3_entry)}")
if len(jan3_asian) > 0:
    ah = jan3_asian['high'].max()
    al = jan3_asian['low'].min()
    print(f"  Asian High: {ah:.5f}, Low: {al:.5f}, Range: {(ah-al)*10000:.1f} pips")

# Run strategy
strategy = P90CascadeActivationStrategy()
results = strategy.run_backtest(df5, pair="EUR/USD")
print(f"\nResults: trades={results.get('total_trades', 0)}, error={results.get('error', 'none')}")

# Now test on more data
df_more = df[df.index < datetime(2023, 2, 1)].copy()
print(f"\nTesting on {len(df_more)} bars (Jan 2023)...")
results2 = strategy.run_backtest(df_more, pair="EUR/USD")
print(f"Results: trades={results2.get('total_trades', 0)}, WR={results2.get('win_rate', 0)}%")
if results2.get('total_trades', 0) > 0:
    print(f"PnL: {results2.get('total_pnl_pips', 0)} pips")
    for at, data in results2.get('by_activation_type', {}).items():
        print(f"  {at}: {data['trades']} trades, {data['win_rate']}% WR, {data['pnl_pips']} pips")
