#!/usr/bin/env python3
"""Quick test of v4 strategies - focused on fixed ones."""
import sys
import time
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from optimizer_v4 import (
    load_eurusd_m5, prepare_data,
    run_deep_mean_reversion, run_stall_harvest_cfd, run_constraint_anchor,
    run_blind_structural_chain, run_two_plays, run_failure_repair,
    run_dual_engine, run_p90p_distribution, run_fractal_resolution,
    run_composite_alpha,
)

print("Loading data...", flush=True)
df = load_eurusd_m5()
df = prepare_data(df)
print(f"Data ready: {len(df):,} bars", flush=True)

strategies = [
    ("Deep_Mean_Reversion", run_deep_mean_reversion),
    ("Stall_Harvest_CFD", run_stall_harvest_cfd),
    ("Constraint_Anchor", run_constraint_anchor),
    ("Blind_Structural_Chain", run_blind_structural_chain),
    ("Two_Plays", run_two_plays),
    ("Failure_Repair", run_failure_repair),
    ("Dual_Engine", run_dual_engine),
    ("P90P_Distribution", run_p90p_distribution),
    ("Fractal_Resolution", run_fractal_resolution),
    ("Composite_Alpha", run_composite_alpha),
]

all_results = {}
for name, fn in strategies:
    print(f"Running {name}...", flush=True)
    t0 = time.time()
    try:
        r = fn(df)
        elapsed = time.time() - t0
        all_results[name] = r
        if r.get("total_trades", 0) > 0:
            print(f"  {r['total_trades']} trades | WR: {r['win_rate']}% | "
                  f"PnL: {r['total_pnl']}p | PF: {r['profit_factor']} | "
                  f"MaxDD: {r['max_dd']}p | Exp: {r['expectancy']}p | "
                  f"AnnRet: {r.get('annual_return_pct', 0)}% | "
                  f"({elapsed:.1f}s)", flush=True)
        else:
            print(f"  No trades ({elapsed:.1f}s)", flush=True)
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  ERROR: {e} ({elapsed:.1f}s)", flush=True)
        import traceback
        traceback.print_exc()
        all_results[name] = {"strategy": name, "error": str(e), "total_trades": 0}

# Summary
print(f"\n{'='*70}", flush=True)
print("COMPARATIVE RESULTS v4b", flush=True)
print(f"{'='*70}", flush=True)
print(f"{'Strategy':<25} {'Trades':>6} {'WR%':>6} {'PnL(p)':>8} {'PF':>5} {'MaxDD':>7} {'Exp':>6} {'AnnRet':>7}", flush=True)
print(f"{'─'*70}", flush=True)

profitable = 0
total = 0
for name, r in all_results.items():
    if r.get("total_trades", 0) > 0:
        total += 1
        if r.get("profit_factor", 0) > 1.0:
            profitable += 1
        print(f"{name:<25} {r['total_trades']:>6} {r['win_rate']:>6.1f} "
              f"{r['total_pnl']:>8.1f} {r['profit_factor']:>5.2f} "
              f"{r['max_dd']:>7.1f} {r['expectancy']:>6.3f} "
              f"{r.get('annual_return_pct', 0):>7.1f}", flush=True)
    else:
        print(f"{name:<25} {'N/A':>6} {'N/A':>6} {'N/A':>8} {'N/A':>5} {'N/A':>7} {'N/A':>6} {'N/A':>7}", flush=True)

if total > 0:
    print(f"\nProfitable: {profitable}/{total} = {profitable/total*100:.0f}% (target: 80%)", flush=True)

# Save
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results")
RESULTS_DIR.mkdir(exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
rf = RESULTS_DIR / f"optimizer_v4b_{ts}.json"
with open(rf, "w") as f:
    json.dump(all_results, f, indent=2, default=str)
print(f"\nResults saved to {rf}", flush=True)
