"""Symmetry Trap backtest runner."""
import sys, os, time
from datetime import datetime

ENGINES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engines")
sys.path.insert(0, ENGINES_DIR)
os.chdir(ENGINES_DIR)

from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv, format_report

csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "EURUSDPRO_M5_2023_2026.csv")
print(f"CSV: {csv_path}")
print(f"Size: {os.path.getsize(csv_path) / 1024 / 1024:.1f} MB")
print("=" * 60)

t0 = time.time()
print("Loading bars...")
bars, symbol = load_m5_csv(csv_path)
print(f"Loaded {len(bars)} bars for {symbol}")

# Filter to 2024-2025 for clean 2-year backtest
filtered = [b for b in bars if b.timestamp >= datetime(2024, 1, 1) and b.timestamp < datetime(2026, 1, 1)]
print(f"Filtered to {len(filtered)} bars (2024-2025)")

bt = SymmetryTrapBacktest(symbol="EURUSD", pip_size=0.0001)
result = bt.run(filtered)
report = format_report(result)
t1 = time.time()

print(f"\nRuntime: {t1 - t0:.1f}s")
print("=" * 60)
print(report)
