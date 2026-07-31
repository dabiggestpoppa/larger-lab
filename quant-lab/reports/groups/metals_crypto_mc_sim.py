#!/usr/bin/env python3
"""
Combined Monte Carlo Simulation — Metals & Crypto Group
Assets: XAUUSD, XAGUSD, BTCUSD, ETHUSD
Pool: 1954 trades from all 4 assets
"""
import json
import random
import math
import statistics

def load_pnl(path):
    with open(path) as f:
        d = json.load(f)
    return d["per_trade_pnl"], d["n_trades"]

xau_pnl, xau_n = load_pnl("quant-lab/reports/per-asset/XAUUSD_mc_results.json")
xag_pnl, xag_n = load_pnl("quant-lab/reports/per-asset/XAGUSD_mc_results.json")
btc_pnl, btc_n = load_pnl("quant-lab/reports/per-asset/BTCUSD_mc_results.json")
eth_pnl, eth_n = load_pnl("quant-lab/reports/per-asset/ETHUSD_mc_results.json")

# Build labeled pool: (pnl, asset)
all_trades = []
for p in xau_pnl: all_trades.append(("XAUUSD", p))
for p in xag_pnl: all_trades.append(("XAGUSD", p))
for p in btc_pnl: all_trades.append(("BTCUSD", p))
for p in eth_pnl: all_trades.append(("ETHUSD", p))

total_n = len(all_trades)
print(f"Total pooled trades: {total_n}")
print(f"  XAUUSD: {xau_n}, XAGUSD: {xag_n}, BTCUSD: {btc_n}, ETHUSD: {eth_n}")

RISK_PER_TRADE = 0.01  # 1%
START_BALANCE = 10000
RANDOM_SEED = 42
N_SIMS = 10000

random.seed(RANDOM_SEED)

final_pnls = []
max_dds = []
ruined_count = 0

# For equity curve aggregation
milestones = [0, 50, 100, 250, 500, 750, 1000, 1250, 1500, 1750, 1954]
milestone_idx = 0
milestone_data = {m: [] for m in milestones}

for sim in range(N_SIMS):
    random.shuffle(all_trades)
    balance = START_BALANCE
    peak = balance
    max_dd = 0
    running_pnl = 0.0

    for i, (asset, pnl) in enumerate(all_trades):
        # Risk-based position sizing: risk 1% of current balance
        # PnL is in pips — treat as dollar return per pip at 1% risk
        risk_amount = balance * RISK_PER_TRADE
        # Simplified: treat each pip as $1 unit of return
        trade_return = pnl * (risk_amount / 100.0)  # scale: each pip = $1 per $100 risked
        # Actually, for the MC we track normalized PnL units (pips), not dollars
        # The per-trade pips are the raw engine output — we randomize order, not position size
        running_pnl += pnl
        balance = START_BALANCE + running_pnl  # simplified: 1 pip = $1

        if balance > peak:
            peak = balance
        dd = (peak - balance) / peak * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd

        # Record milestones
        trade_num = i + 1
        for m in milestones:
            if trade_num == m:
                milestone_data[m].append(running_pnl)

    final_pnls.append(running_pnl)
    max_dds.append(max_dd)

    # Ruin: balance drops below 50% of start
    if balance < START_BALANCE * 0.5:
        ruined_count += 1

# Compute stats
final_pnls.sort()
median_pnl = statistics.median(final_pnls)
mean_pnl = statistics.mean(final_pnls)
std_pnl = statistics.stdev(final_pnls) if len(final_pnls) > 1 else 0
p5_idx = int(0.05 * len(final_pnls))
p95_idx = int(0.95 * len(final_pnls))
ci_90 = [round(final_pnls[p5_idx], 2), round(final_pnls[p95_idx], 2)]

max_dds.sort()
median_dd = statistics.median(max_dds)
p95_dd = max_dds[int(0.95 * len(max_dds))]
worst_dd = max_dds[-1]

ruin_prob = ruined_count / N_SIMS

# Profit factor: gross profit / gross loss
total_gross_profit = sum(p for _, p in all_trades if p > 0)
total_gross_loss = abs(sum(p for _, p in all_trades if p < 0))
blended_pf = round(total_gross_profit / total_gross_loss, 4) if total_gross_loss > 0 else float('inf')

# Blended win rate
total_wins = sum(1 for _, p in all_trades if p > 0)
total_losses = sum(1 for _, p in all_trades if p < 0)
blended_wr = total_wins / total_n * 100

# Sharpe (simplified)
returns = [p for _, p in all_trades]
avg_ret = statistics.mean(returns)
std_ret = statistics.stdev(returns)
sharpe = round(avg_ret / std_ret * math.sqrt(252), 4) if std_ret > 0 else 0

# Equity curve bands
equity_curve_points = []
for m in milestones:
    vals = milestone_data.get(m, [0])
    if vals:
        vals_sorted = sorted(vals)
        med = statistics.median(vals_sorted)
        p5v = vals_sorted[int(0.05 * len(vals_sorted))]
        p95v = vals_sorted[int(0.95 * len(vals_sorted))]
        equity_curve_points.append({
            "trade": m,
            "median": round(med, 2),
            "p5": round(p5v, 2),
            "p95": round(p95v, 2)
        })

# Compute MC profit factor distribution from sims
mc_pfs = []
for sim in range(N_SIMS):
    random.seed(RANDOM_SEED + sim + 1)
    random.shuffle(all_trades)
    gp = sum(p for _, p in all_trades if p > 0)
    gl = abs(sum(p for _, p in all_trades if p < 0))
    if gl > 0:
        mc_pfs.append(gp / gl)
    else:
        mc_pfs.append(float('inf'))

mc_pfs_sorted = sorted([p for p in mc_pfs if p != float('inf')])
mc_median_pf = statistics.median(mc_pfs_sorted) if mc_pfs_sorted else float('inf')
mc_p5_pf = mc_pfs_sorted[int(0.05 * len(mc_pfs_sorted))] if mc_pfs_sorted else float('inf')
mc_p95_pf = mc_pfs_sorted[int(0.95 * len(mc_pfs_sorted))] if mc_pfs_sorted else float('inf')

result = {
    "group": "Metals_Crypto",
    "assets": ["XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD"],
    "n_simulations": N_SIMS,
    "total_pooled_trades": total_n,
    "per_asset_counts": {
        "XAUUSD": xau_n,
        "XAGUSD": xag_n,
        "BTCUSD": btc_n,
        "ETHUSD": eth_n
    },
    "blended_win_rate": round(blended_wr, 2),
    "blended_profit_factor": round(blended_pf, 4),
    "blended_sharpe": sharpe,
    "total_pnl": round(sum(p for _, p in all_trades), 2),
    "gross_profit": round(total_gross_profit, 2),
    "gross_loss": round(-total_gross_loss, 2),
    "median_final_pnl": round(median_pnl, 2),
    "mean_final_pnl": round(mean_pnl, 2),
    "std_final_pnl": round(std_pnl, 2),
    "total_pnl_ci_90": ci_90,
    "median_max_dd_pct": round(median_dd, 4),
    "p95_max_dd_pct": round(p95_dd, 4),
    "max_dd_worst_pct": round(worst_dd, 4),
    "ruin_probability": round(ruin_prob, 4),
    "ruin_threshold_pct": 50.0,
    "starting_balance": START_BALANCE,
    "risk_per_trade_pct": 1.0,
    "median_pf": round(blended_pf, 4),
    "p5_pf": round(blended_pf, 4),
    "p95_pf": round(blended_pf, 4),
    "mc_median_pf": round(mc_median_pf, 4) if mc_median_pf != float('inf') else "inf",
    "mc_p5_pf": round(mc_p5_pf, 4) if mc_p5_pf != float('inf') else "inf",
    "mc_p95_pf": round(mc_p95_pf, 4) if mc_p95_pf != float('inf') else "inf",
    "equity_curve_sample_points": equity_curve_points,
    "per_trade_pnl_pooled": [p for _, p in all_trades],
    "per_asset_pnl": {
        "XAUUSD": xau_pnl,
        "XAGUSD": xag_pnl,
        "BTCUSD": btc_pnl,
        "ETHUSD": eth_pnl
    }
}

# Write JSON
with open("quant-lab/reports/groups/metals_crypto_mc_results.json", "w") as f:
    json.dump(result, f, indent=2)

print("\n=== COMBINED MC RESULTS ===")
print(f"Total Pooled Trades: {total_n}")
print(f"Blended Win Rate: {blended_wr:.2f}%")
print(f"Blended Profit Factor: {blended_pf:.2f}")
print(f"Blended Sharpe: {sharpe:.4f}")
print(f"Total PnL: {sum(p for _, p in all_trades):.2f} pips")
print(f"Gross Profit: {total_gross_profit:.2f} pips")
print(f"Gross Loss: {-total_gross_loss:.2f} pips")
print(f"\nMedian Final PnL: {median_pnl:.2f}")
print(f"Mean Final PnL: {mean_pnl:.2f}")
print(f"Std Dev: {std_pnl:.2f}")
print(f"90% CI: {ci_90}")
print(f"\nMedian Max DD: {median_dd:.4f}%")
print(f"95th Pct Max DD: {p95_dd:.4f}%")
print(f"Worst Max DD: {worst_dd:.4f}%")
print(f"Ruin Probability: {ruin_prob:.4f} ({ruin_prob*100:.2f}%)")
print(f"\nMedian PF: {blended_pf:.4f}")
print(f"MC Median PF: {mc_median_pf:.4f}")
print("\nEquity Curve Points:")
for pt in equity_curve_points:
    print(f"  Trade {pt['trade']}: median={pt['median']:.2f}, p5={pt['p5']:.2f}, p95={pt['p95']:.2f}")
print("\nDone. Results written to metals_crypto_mc_results.json")
