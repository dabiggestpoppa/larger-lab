#!/usr/bin/env python3
"""Test a single strategy for speed."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from optimizer_v4 import load_eurusd_m5, prepare_data, run_deep_mean_reversion

print("Loading data...")
t0 = time.time()
df = load_eurusd_m5()
df = prepare_data(df)
t1 = time.time()
print(f"Data ready: {len(df):,} bars in {t1-t0:.1f}s")

print("Running Deep_Mean_Reversion...")
t2 = time.time()
result = run_deep_mean_reversion(df)
t3 = time.time()
print(f"Done in {t3-t2:.1f}s")
print(f"Result: {result.get('total_trades', 0)} trades, WR={result.get('win_rate', 0)}%, PnL={result.get('total_pnl', 0)}p")
