#!/usr/bin/env python3
"""Monte Carlo Simulation — DMR MT5 Results. Fixed lot sizing. 10K iterations."""
import json, random, numpy as np
from pathlib import Path
from datetime import datetime
import pandas as pd

RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5")

data = json.load(open(RESULTS_DIR / "dmr_mt5_working_20260519_144233.json"))
trades_df = pd.read_csv(RESULTS_DIR / "dmr_mt5_working_trades_20260519_144233.csv")

pnls = trades_df['pnl'].values  # in pips
wins = pnls[pnls > 0]
losses = pnls[pnls <= 0]

print(f"Trades: {len(pnls)} | WR: {data['win_rate']}% | PF: {data['profit_factor']}")
print(f"Wins: {len(wins)} avg={wins.mean():.2f}p | Losses: {len(losses)} avg={losses.mean():.2f}p")

NUM_ITERATIONS = 10000
INITIAL_EQUITY = 10000.0
LOT_SIZE = 0.01  # Micro lots (0.01 = $0.10/pip for EUR/USD)
PIP_VALUE = 0.10  # $0.10 per pip for 0.01 lot

print(f"\nMC Parameters: {NUM_ITERATIONS:,} iterations | ${INITIAL_EQUITY:,.0f} equity | {LOT_SIZE} lots | ${PIP_VALUE}/pip")

results = []
ruin_count = 0
RUIN_THRESHOLD = INITIAL_EQUITY * 0.5  # 50% drawdown = ruin

for i in range(NUM_ITERATIONS):
    equity = INITIAL_EQUITY
    peak = equity
    max_dd_pct = 0
    seq = list(pnls)
    random.shuffle(seq)

    for pnl_pips in seq:
        pnl_dollars = pnl_pips * PIP_VALUE * (LOT_SIZE / 0.01)
        equity += pnl_dollars

        if equity > peak:
            peak = equity
        dd_pct = (peak - equity) / peak * 100 if peak > 0 else 0
        max_dd_pct = max(max_dd_pct, dd_pct)

        if equity <= RUIN_THRESHOLD:
            ruin_count += 1
            break

    results.append({
        'final_equity': equity,
        'max_dd_pct': max_dd_pct,
        'total_return_pct': (equity - INITIAL_EQUITY) / INITIAL_EQUITY * 100,
        'ruined': equity <= RUIN_THRESHOLD
    })

    if (i + 1) % 2000 == 0:
        print(f"  {i+1:,} / {NUM_ITERATIONS:,}...")

final_equities = np.array([r['final_equity'] for r in results])
max_dds = np.array([r['max_dd_pct'] for r in results])
returns = np.array([r['total_return_pct'] for r in results])

print(f"\n{'='*60}")
print("MONTE CARLO RESULTS — 10,000 iterations (Fixed 0.01 lots)")
print(f"{'='*60}")
print(f"\n📊 Final Equity:")
print(f"  Mean:   ${np.mean(final_equities):,.0f}")
print(f"  Median: ${np.median(final_equities):,.0f}")
print(f"  Best:   ${np.max(final_equities):,.0f}")
print(f"  Worst:  ${np.min(final_equities):,.0f}")
print(f"  Std:    ${np.std(final_equities):,.0f}")

print(f"\n📈 Returns:")
print(f"  Mean:   {np.mean(returns):.1f}%")
print(f"  Median: {np.median(returns):.1f}%")
print(f"  Best:   {np.max(returns):.1f}%")
print(f"  Worst:  {np.min(returns):.1f}%")

print(f"\n🔻 Max Drawdown:")
print(f"  Mean:   {np.mean(max_dds):.1f}%")
print(f"  Median: {np.median(max_dds):.1f}%")
print(f"  Worst:  {np.max(max_dds):.1f}%")
print(f"  P95:    {np.percentile(max_dds, 95):.1f}%")
print(f"  P99:    {np.percentile(max_dds, 99):.1f}%")

print(f"\n💀 Ruin (50% DD): {ruin_count:,} / {NUM_ITERATIONS:,} ({ruin_count/NUM_ITERATIONS*100:.2f}%)")
print(f"✅ Survival rate: {(1-ruin_count/NUM_ITERATIONS)*100:.2f}%")

profitable = sum(1 for r in returns if r > 0)
print(f"\n✅ Prob of profit:     {profitable/NUM_ITERATIONS*100:.1f}%")
print(f"✅ Prob >10% return:   {sum(1 for r in returns if r > 10)/NUM_ITERATIONS*100:.1f}%")
print(f"✅ Prob >20% return:   {sum(1 for r in returns if r > 20)/NUM_ITERATIONS*100:.1f}%")
print(f"✅ Prob >50% return:   {sum(1 for r in returns if r > 50)/NUM_ITERATIONS*100:.1f}%")

print(f"\n📈 Equity Percentiles:")
for p in [5, 10, 25, 50, 75, 90, 95]:
    val = np.percentile(final_equities, p)
    print(f"  P{p:>2}: ${val:>12,.0f} ({(val/INITIAL_EQUITY-1)*100:+.1f}%)")

print(f"\n📈 Drawdown Percentiles:")
for p in [5, 10, 25, 50, 75, 90, 95, 99]:
    val = np.percentile(max_dds, p)
    print(f"  P{p:>2}: {val:.1f}%")

# Also run with different lot sizes
print(f"\n{'='*60}")
print("SENSITIVITY: Different Lot Sizes")
print(f"{'='*60}")
for lot in [0.01, 0.05, 0.10, 0.25, 0.50, 1.00]:
    pip_val = 0.10 * (lot / 0.01)
    eq = INITIAL_EQUITY
    peak_eq = eq
    max_dd = 0
    for pnl_pips in pnls:  # Use actual sequence, not randomized
        eq += pnl_pips * pip_val
        if eq > peak_eq:
            peak_eq = eq
        dd = (peak_eq - eq) / peak_eq * 100 if peak_eq > 0 else 0
        max_dd = max(max_dd, dd)
    total_ret = (eq - INITIAL_EQUITY) / INITIAL_EQUITY * 100
    print(f"  {lot:>5.2f} lots: ${eq:>12,.0f} ({total_ret:+.1f}%) | MaxDD: {max_dd:.1f}%")

# Save
output = {
    "strategy": "Deep_Mean_Reversion", "source": "MT5_Monte_Carlo_v2",
    "iterations": NUM_ITERATIONS, "initial_equity": INITIAL_EQUITY,
    "lot_size": LOT_SIZE, "pip_value": PIP_VALUE,
    "ruin_count": ruin_count, "ruin_pct": round(ruin_count/NUM_ITERATIONS*100, 2),
    "survival_rate": round((1-ruin_count/NUM_ITERATIONS)*100, 2),
    "final_equity": {"mean": round(float(np.mean(final_equities)), 0), "median": round(float(np.median(final_equities)), 0), "best": round(float(np.max(final_equities)), 0), "worst": round(float(np.min(final_equities)), 0)},
    "returns": {"mean": round(float(np.mean(returns)), 1), "median": round(float(np.median(returns)), 1), "best": round(float(np.max(returns)), 1), "worst": round(float(np.min(returns)), 1)},
    "max_dd": {"mean": round(float(np.mean(max_dds)), 1), "median": round(float(np.median(max_dds)), 1), "worst": round(float(np.max(max_dds)), 1), "p95": round(float(np.percentile(max_dds, 95)), 1), "p99": round(float(np.percentile(max_dds, 99)), 1)},
    "prob_profitable": round(profitable/NUM_ITERATIONS*100, 1),
}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
out_path = RESULTS_DIR / f"mc_dmr_mt5_v2_{ts}.json"
with open(out_path, 'w') as f:
    json.dump(output, f, indent=2)
print(f"\nSaved: {out_path}")
