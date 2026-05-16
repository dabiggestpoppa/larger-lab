"""Quick backtest runner for P90 Cascade Combo strategy."""
import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# Direct import of just the CSV parser to avoid nautilus dependency
sys.path.insert(0, str(Path(__file__).parent))

# Inline the _parse_csv function to avoid importing nautilus_trader
import re

def _parse_csv(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        raw_lines = f.readlines()
    data_lines = [l for l in raw_lines[1:] if l.strip()]
    # Fix OX line wrapping
    fixed = []
    i = 0
    while i < len(data_lines):
        line = data_lines[i]
        if i + 1 < len(data_lines) and re.match(r'^\d{4}\.\d{2}\.\d{2}', data_lines[i + 1]):
            parts = line.strip().split()
            if len(parts) >= 8:
                fixed.append(line)
            else:
                merged = line.strip() + " " + data_lines[i + 1].strip()
                fixed.append(merged)
                i += 1
        else:
            fixed.append(line)
        i += 1
    data_lines = fixed

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
                "low": low_val, "close": close_val, "tick_volume": tick_vol,
            })
        except (ValueError, IndexError):
            continue
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)
    return df


from strategies.p90_cascade_combo import P90CascadeComboStrategy

df = _parse_csv(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")
print(f"Data: {len(df)} bars, {df.index[0]} to {df.index[-1]}")

strategy = P90CascadeComboStrategy()
results = strategy.run_backtest(df, pair="EUR/USD")

print(f"\n=== P90 CASCADE + 45-MIN ADD COMBO ===")
print(f"Total Trades: {results.get('total_trades', 0)}")
print(f"Total Sessions: {results.get('total_sessions', 0)}")
print(f"Win Rate: {results.get('win_rate', 0)}%")
print(f"Total PnL: {results.get('total_pnl_pips', 0)} pips")
print(f"Profit Factor: {results.get('profit_factor', 0)}")
print(f"Max DD: {results.get('max_drawdown_pips', 0)} pips")

if "by_activation_type" in results:
    print(f"\nBy Type:")
    for at, d in results["by_activation_type"].items():
        print(f"  {at}: {d['trades']} trades, {d['win_rate']}% WR, {d['pnl_pips']} pips")

if "by_exit_reason" in results:
    print(f"\nBy Exit:")
    for r, c in sorted(results["by_exit_reason"].items(), key=lambda x: -x[1]):
        print(f"  {r}: {c}")

# Save
results_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results")
results_dir.mkdir(exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
rf = results_dir / f"p90_cascade_combo_{ts}.json"
with open(rf, "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nSaved to {rf}")
