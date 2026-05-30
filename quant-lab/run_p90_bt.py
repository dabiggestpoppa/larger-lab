"""P90 backtest runner - runs from engines/ directory."""
import sys, os, time

ENGINES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engines")
sys.path.insert(0, ENGINES_DIR)
os.chdir(ENGINES_DIR)

from p90_backtest import run_backtest

csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "EURUSDPRO_M5_2023_2026.csv")
print(f"CSV: {csv_path}")
print(f"Exists: {os.path.exists(csv_path)}")
print(f"Size: {os.path.getsize(csv_path) / 1024 / 1024:.1f} MB")
print("=" * 60)

t0 = time.time()
report = run_backtest(csv_path, symbol="EURUSD")
t1 = time.time()

print(f"\nRuntime: {t1 - t0:.1f}s")
print("=" * 60)
if isinstance(report, str):
    print(report)
else:
    for k, v in report.items():
        print(f"  {k}: {v}")
