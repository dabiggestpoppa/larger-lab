#!/usr/bin/env python3
"""Monte Carlo Simulation — DMR MT5 Results. 10K iterations."""
import json, random, numpy as np
from pathlib import Path
from datetime import datetime
import pandas as pd

RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5")

data = json.load(open(RESULTS_DIR / "dmr_mt5_working_20260519_144233.json"))
trades_df = pd.read_csv(RESULTS_DIR / "dmr_mt5_working_trades_20260519_144233.csv")

print(f"Loaded {len(trades_df)} trades | WR: {data['win_rate']}% | PF: {data['profit_factor']}")

pnls = trades_df['pnl'].values
wins = pnls[pnls > 0]
losses = pnls[pnls <= 0]
avg_loss_abs = abs(losses.mean()) if len(losses) > 0 else 1.0

print(f"Wins: {len(wins)} avg={wins.mean():.2f}p | Losses: {len(losses)} avg={losses.mean():.2f}p")

NUM_ITERATIONS = 10000
INITIAL_EQUITY = 10000.0
RISK_PER_TRADE = 0.0025

print(f"\nRunning {NUM_ITERATIONS:,} MC iterations...")

results = []
ruin_count = 0

for i in range(NUM_ITERATIONS):
    equity = INITIAL_EQUITY
    peak = equity
    max_dd = 0
    seq = list(pnls)
    random.shuffle(seq)

    for pnl_pips in seq:
        risk_amount = equity * RISK_PER_TRADE
        pnl_dollars = risk_amount * (pnl_pips / avg_loss_abs)
        equity += pnl_dollars
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)
        if equity < INITIAL_EQUITY * 0.5:
            ruin_count += 1
            break

    results.append({
        'final_equity': equity,
        'max_dd_pct': max_dd,
        'total_return_pct': (equity - INITIAL_EQUITY) / INITIAL_EQUITY * 100,
        'ruined': equity < INITIAL_EQUITY * 0.5
    })

    if (i + 1) % 2000 == 0:
        print(f"  {i+1:,} / {NUM_ITERATIONS:,}...")

final_equities = [r['final_equity'] for r in results]
max_dds = [r['max_dd_pct'] for r in results]
returns = [r['total_return_pct'] for r in results]

print(f"\n{'='*60}")
print("MONTE CARLO RESULTS — 10,000 iterations")
print(f"{'='*60}")
print(f"\nFinal Equity:  Mean=${np.mean(final_equities):,.0f} | Median=${np.median(final_equities):,.0f} | Best=${np.max(final_equities):,.0f} | Worst=${np.min(final_equities):,.0f}")
print(f"Returns:       Mean={np.mean(returns):.1f}% | Median={np.median(returns):.1f}% | Best={np.max(returns):.1f}% | Worst={np.min(returns):.1f}%")
print(f"Max DD:        Mean={np.mean(max_dds):.1f}% | Median={np.median(max_dds):.1f}% | Worst={np.max(max_dds):.1f}% | P95={np.percentile(max_dds, 95):.1f}% | P99={np.percentile(max_dds, 99):.1f}%")
print(f"Ruin:          {ruin_count:,} / {NUM_ITERATIONS:,} ({ruin_count/NUM_ITERATIONS*100:.2f}%)")
print(f"Survival:      {(1-ruin_count/NUM_ITERATIONS)*100:.2f}%")

profitable = sum(1 for r in returns if r > 0)
print(f"Prob profit:   {profitable/NUM_ITERATIONS*100:.1f}%")
print(f"Prob >10%:     {sum(1 for r in returns if r > 10)/NUM_ITERATIONS*100:.1f}%")
print(f"Prob >20%:     {sum(1 for r in returns if r > 20)/NUM_ITERATIONS*100:.1f}%")

for p in [5, 10, 25, 50, 75, 90, 95]:
    val = np.percentile(final_equities, p)
    print(f"  Equity P{p:>2}: ${val:,.0f} ({(val/INITIAL_EQUITY-1)*100:+.1f}%)")

output = {
    "strategy": "Deep_Mean_Reversion", "source": "MT5_Monte_Carlo",
    "iterations": NUM_ITERATIONS, "initial_equity": INITIAL_EQUITY,
    "risk_per_trade": RISK_PER_TRADE, "ruin_count": ruin_count,
    "ruin_pct": round(ruin_count/NUM_ITERATIONS*100, 2),
    "survival_rate": round((1-ruin_count/NUM_ITERATIONS)*100, 2),
    "final_equity": {"mean": round(float(np.mean(final_equities)), 0), "median": round(float(np.median(final_equities)), 0), "best": round(float(np.max(final_equities)), 0), "worst": round(float(np.min(final_equities)), 0)},
    "returns": {"mean": round(float(np.mean(returns)), 1), "median": round(float(np.median(returns)), 1), "best": round(float(np.max(returns)), 1), "worst": round(float(np.min(returns)), 1)},
    "max_dd": {"mean": round(float(np.mean(max_dds)), 1), "median": round(float(np.median(max_dds)), 1), "worst": round(float(np.max(max_dds)), 1), "p95": round(float(np.percentile(max_dds, 95)), 1), "p99": round(float(np.percentile(max_dds, 99)), 1)},
    "prob_profitable": round(profitable/NUM_ITERATIONS*100, 1),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
out_path = RESULTS_DIR / f"mc_dmr_mt5_{ts}.json"
with open(out_path, 'w') as f:
    json.dump(output, f, indent=2)
print(f"\nSaved: {out_path}")
