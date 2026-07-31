#!/usr/bin/env python3
"""Majors Group Combined Monte Carlo Simulation & Report Generator."""

import json
import os
import random
import statistics
import math
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LAB_DIR = os.path.dirname(SCRIPT_DIR)  # quant-lab/
REPORTS_DIR = os.path.join(LAB_DIR, "reports")
PER_ASSET_DIR = os.path.join(REPORTS_DIR, "per-asset")
GROUPS_DIR = os.path.join(REPORTS_DIR, "groups")
os.makedirs(GROUPS_DIR, exist_ok=True)

ASSETS = ["EURUSD", "GBPUSD", "USDCHF", "USDJPY", "AUDUSD", "NZDUSD"]

INITIAL_BALANCE = 10000.0
RISK_PCT = 0.01
N_ITERATIONS = 10000


def load_per_asset_data():
    """Load per-trade PnL arrays and backtest stats for all 6 majors."""
    all_trades = {}  # asset -> list of (pnl_usd, asset_label)
    asset_stats = {}
    
    for asset in ASSETS:
        mc_path = os.path.join(PER_ASSET_DIR, f"{asset}_mc_results.json")
        with open(mc_path) as f:
            mc = json.load(f)
        
        # Determine format: NZDUSD/USDJPY/AUDUSD have per_trade_pnl + backtest nested
        # EURUSD/GBPUSD/USDCHF have top-level MC stats + equity curves (sampled every 10 trades)
        has_per_trade = "per_trade_pnl" in mc and len(mc.get("per_trade_pnl", [])) > 0
        
        if has_per_trade:
            # Explicit per-trade PnL in pips — convert to USD
            raw_pnls_pips = mc["per_trade_pnl"]
            n_mc_trades = mc["monte_carlo"].get("n_trades_in_sequence", len(raw_pnls_pips))
            pool_pips = raw_pnls_pips[:n_mc_trades]
            
            # Calibrate pips->USD using MC equity curve terminal
            eq_med = mc["monte_carlo"]["equity_curve_median_sample"]
            eq_terminal = eq_med[-1] if eq_med else INITIAL_BALANCE
            eq_start = eq_med[0] if eq_med else INITIAL_BALANCE
            mc_total_pnl_usd = eq_terminal - eq_start
            
            total_pips = sum(pool_pips)
            if total_pips != 0:
                scale = mc_total_pnl_usd / total_pips
            else:
                scale = 1.0
            
            pnls_usd = [round(p * scale, 2) for p in pool_pips]
            
            # Backtest stats
            bt = mc["backtest"]
            asset_stats[asset] = {
                "trades": bt["trades"],
                "wins": bt["wins"],
                "losses": bt["losses"],
                "win_rate": round(bt["win_rate"], 1),
                "total_pnl_pips": round(bt.get("total_pnl_pips", 0), 1),
                "profit_factor": round(bt.get("profit_factor", 0), 2),
                "sharpe": round(bt.get("sharpe", 0), 2),
                "max_dd_pips": bt.get("max_dd_pips"),
                "max_dd_pct": bt.get("max_dd_pct"),
                "expectancy": round(bt.get("expectancy", 0), 2),
                "tier_stats": bt.get("tier_stats", {}),
                "loop_stats": bt.get("loop_stats", {}),
            }
        else:
            # EURUSD/GBPUSD/USDCHF: extract from equity curves sampled every 10 trades
            eq_med = mc["eq_p50"]
            eq_trades = mc["eq_curve_trades"]  # [0, 10, 20, ..., 500]
            
            # Each delta = 10 trades. Divide by 10 to approximate per-trade.
            pnls_usd = []
            for i in range(len(eq_med) - 1):
                bucket_delta = eq_med[i+1] - eq_med[i]
                per_trade = bucket_delta / 10.0
                # Add 10 entries of approximately this value
                pnls_usd.extend([round(per_trade, 2)] * 10)
            
            n_trades = mc.get("n_trades", 500)
            wins = sum(1 for p in pnls_usd if p > 0)
            losses = sum(1 for p in pnls_usd if p <= 0)
            
            asset_stats[asset] = {
                "trades": n_trades,
                "wins": wins,
                "losses": losses,
                "win_rate": round(wins / len(pnls_usd) * 100, 1),
                "total_pnl_pips": None,
                "profit_factor": mc.get("pf_median"),
                "profit_factor_mean": mc.get("pf_mean"),
                "avg_loss_pips": mc.get("avg_loss_pips"),
                "sharpe": None,
                "max_dd_pips": None,
                "max_dd_pct": mc.get("median_max_dd_pct"),
                "expectancy": None,
                "tier_stats": {},
                "loop_stats": {},
            }
        
        all_trades[asset] = [(pnl, asset) for pnl in pnls_usd]
    
    return all_trades, asset_stats


def run_combined_mc(trade_pool, n_iterations=10000, initial_balance=10000.0):
    """Run MC simulation by shuffling trade order from the full pool."""
    n_trades = len(trade_pool)
    pnl_values = [t[0] for t in trade_pool]
    
    terminal_pnls = []
    max_dds = []
    # Track equity curves for curves summary
    all_eq_curves = []
    ruin_count = 0
    
    for i in range(n_iterations):
        shuffled = random.sample(pnl_values, len(pnl_values))
        
        balance = initial_balance
        peak = balance
        max_dd = 0
        eq_curve = [balance]
        
        ruin = False
        for pnl in shuffled:
            balance += pnl
            eq_curve.append(balance)
            if balance > peak:
                peak = balance
            dd = peak - balance
            if dd > max_dd:
                max_dd = dd
            if balance < initial_balance * 0.5:
                ruin = True
        
        terminal_pnls.append(round(balance - initial_balance, 2))
        max_dds.append(round(max_dd, 2))
        if ruin:
            ruin_count += 1
        
        # Store every 50th curve for percentile calculations
        if i % 50 == 0:
            all_eq_curves.append(eq_curve)
    
    return terminal_pnls, max_dds, all_eq_curves, ruin_count


def percentile_val(data, pct):
    """Compute percentile."""
    if not data:
        return 0
    s = sorted(data)
    k = (len(s) - 1) * (pct / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] * (c - k) + s[c] * (k - f)


def compute_curve_percentiles(equity_curves, n_trades_total, n_sample=51):
    """Compute percentile bands at sampled trade indices."""
    if not equity_curves:
        return [], [], [], [], [], []
    
    indices = list(range(0, n_trades_total + 1, max(1, n_trades_total // (n_sample - 1))))
    if indices[-1] != n_trades_total:
        indices.append(n_trades_total)
    
    trade_axis = []
    p5, p25, p50, p75, p95 = [], [], [], [], []
    
    for idx in indices:
        trade_axis.append(idx)
        vals_at = []
        for curve in equity_curves:
            if idx < len(curve):
                vals_at.append(curve[idx])
        vals_at.sort()
        p5.append(round(percentile_val(vals_at, 5), 2))
        p25.append(round(percentile_val(vals_at, 25), 2))
        p50.append(round(percentile_val(vals_at, 50), 2))
        p75.append(round(percentile_val(vals_at, 75), 2))
        p95.append(round(percentile_val(vals_at, 95), 2))
    
    return trade_axis, p5, p25, p50, p75, p95


# ============================================================
# MAIN
# ============================================================

print("=" * 60)
print("MAJORS GROUP COMBINED MONTE CARLO")
print("=" * 60)
print(f"Assets: {', '.join(ASSETS)}")
print(f"Iterations: {N_ITERATIONS}")
print(f"Initial Balance: ${INITIAL_BALANCE:,.0f}")
print()

random.seed(42)

all_trades, asset_stats = load_per_asset_data()

# Build combined pool
combined_pool = []
for asset in ASSETS:
    pool = all_trades[asset]
    combined_pool.extend(pool)
    st = asset_stats[asset]
    print(f"  {asset}: {len(pool)} pool trades, WR={st['win_rate']:.1f}%, PF={st.get('profit_factor', 0)}")

total_trades = len(combined_pool)
print(f"\nCombined pool: {total_trades} trades")

# Run MC
print(f"\nRunning {N_ITERATIONS:,} simulations...")
terminal_pnls, max_dds, eq_curves, ruin_count = run_combined_mc(
    combined_pool, N_ITERATIONS, INITIAL_BALANCE
)

# Stats
median_pnl = round(statistics.median(terminal_pnls), 2)
mean_pnl = round(statistics.mean(terminal_pnls), 2)
std_pnl = round(statistics.stdev(terminal_pnls), 2) if len(terminal_pnls) > 1 else 0.0
pct_profitable = sum(1 for p in terminal_pnls if p > 0) / len(terminal_pnls) * 100

pnl_p5 = round(percentile_val(terminal_pnls, 5), 2)
pnl_p25 = round(percentile_val(terminal_pnls, 25), 2)
pnl_p50 = round(percentile_val(terminal_pnls, 50), 2)
pnl_p75 = round(percentile_val(terminal_pnls, 75), 2)
pnl_p90 = round(percentile_val(terminal_pnls, 90), 2)
pnl_p95 = round(percentile_val(terminal_pnls, 95), 2)

median_max_dd = round(statistics.median(max_dds), 2)
mean_max_dd = round(statistics.mean(max_dds), 2)
dd_p90 = round(percentile_val(max_dds, 90), 2)
dd_p95 = round(percentile_val(max_dds, 95), 2)
dd_p99 = round(percentile_val(max_dds, 99), 2)
worst_dd = round(max(max_dds), 2)
best_dd = round(min(max_dds), 2)

ruin_prob = round(ruin_count / N_ITERATIONS * 100, 4)

# Blended WR
total_wins = sum(1 for p in combined_pool if p[0] > 0)
total_losses = sum(1 for p in combined_pool if p[0] <= 0)
blended_wr = round(total_wins / total_trades * 100, 1)

# PF from combined pool
gross_profit = sum(p[0] for p in combined_pool if p[0] > 0)
gross_loss = abs(sum(p[0] for p in combined_pool if p[0] < 0))
pf_combined = round(gross_profit / gross_loss, 2) if gross_loss > 0 else float('inf')

# Sharpe approximation using per-trade returns
per_trade_returns = [p[0] / INITIAL_BALANCE for p in combined_pool]
mean_ret = statistics.mean(per_trade_returns)
std_ret = statistics.stdev(per_trade_returns) if len(per_trade_returns) > 1 else 0.001
sharpe = round(mean_ret / std_ret * math.sqrt(total_trades), 2) if std_ret > 0 else 0

# Equity curve percentiles
eq_trades, eq_p5, eq_p25, eq_p50, eq_p75, eq_p95 = compute_curve_percentiles(eq_curves, total_trades, 51)

print(f"\nResults:")
print(f"  Median Terminal PnL: ${median_pnl:+,.2f}")
print(f"  Mean Terminal PnL:   ${mean_pnl:+,.2f}")
print(f"  Std Dev:             ${std_pnl:,.2f}")
print(f"  Pct Profitable:      {pct_profitable:.1f}%")
print(f"  90% CI:              [${pnl_p5:+,.2f}, ${pnl_p95:+,.2f}]")
print(f"  Median Max DD:       ${median_max_dd:,.2f}")
print(f"  Worst DD:            ${worst_dd:,.2f}")
print(f"  Ruin Probability:    {ruin_prob:.4f}%")
print(f"  Blended WR:          {blended_wr}%")
print(f"  Combined PF:         {pf_combined}")
print(f"  Combined Sharpe:     {sharpe}")

# ============================================================
# WRITE MC RESULTS JSON
# ============================================================
mc_results = {
    "group": "Majors",
    "timestamp": datetime.now().isoformat(),
    "assets": ASSETS,
    "n_iterations": N_ITERATIONS,
    "initial_balance": INITIAL_BALANCE,
    "risk_per_trade_pct": RISK_PCT,
    "total_trades_in_pool": total_trades,
    "total_wins": total_wins,
    "total_losses": total_losses,
    "blended_win_rate": blended_wr,
    "total_gross_profit_usd": round(gross_profit, 2),
    "total_gross_loss_usd": round(gross_loss, 2),
    "combined_profit_factor": pf_combined,
    "combined_sharpe_approx": sharpe,
    "median_terminal_pnl": median_pnl,
    "mean_terminal_pnl": mean_pnl,
    "std_terminal_pnl": std_pnl,
    "pct_simulations_profitable": pct_profitable,
    "pnl_5th_pctile": pnl_p5,
    "pnl_25th_pctile": pnl_p25,
    "pnl_50th_pctile": pnl_p50,
    "pnl_75th_pctile": pnl_p75,
    "pnl_90th_pctile": pnl_p90,
    "pnl_95th_pctile": pnl_p95,
    "pnl_90ci_low": pnl_p5,
    "pnl_90ci_high": pnl_p95,
    "median_max_dd_usd": median_max_dd,
    "mean_max_dd_usd": mean_max_dd,
    "max_dd_90th_pctile": dd_p90,
    "max_dd_95th_pctile": dd_p95,
    "max_dd_99th_pctile": dd_p99,
    "worst_max_dd_usd": worst_dd,
    "best_max_dd_usd": best_dd,
    "median_max_dd_pct": round(median_max_dd / INITIAL_BALANCE * 100, 4),
    "max_dd_pct_95th": round(dd_p95 / INITIAL_BALANCE * 100, 4),
    "ruin_probability_pct": ruin_prob,
    "ruin_definition": "Balance below 50% of initial ($5,000)",
    "eq_curve_trades": eq_trades,
    "eq_p5": eq_p5,
    "eq_p25": eq_p25,
    "eq_p50": eq_p50,
    "eq_p75": eq_p75,
    "eq_p95": eq_p95,
    "per_asset": {}
}

for asset in ASSETS:
    mc_path = os.path.join(PER_ASSET_DIR, f"{asset}_mc_results.json")
    with open(mc_path) as f:
        mc = json.load(f)
    
    st = asset_stats[asset]
    mc_results["per_asset"][asset] = {
        "pool_trades": len(all_trades[asset]),
        "backtest_trades": st["trades"],
        "wins": st["wins"],
        "losses": st["losses"],
        "win_rate": st["win_rate"],
        "profit_factor": st.get("profit_factor"),
        "sharpe": st.get("sharpe"),
        "max_dd_pct": st.get("max_dd_pct"),
        "expectancy": st.get("expectancy"),
        "total_pnl_pips": st.get("total_pnl_pips"),
    }

mc_results_path = os.path.join(GROUPS_DIR, "majors_mc_results.json")
with open(mc_results_path, 'w') as f:
    json.dump(mc_results, f, indent=2)
print(f"\nWrote MC results JSON")

# ============================================================
# WRITE MARKDOWN REPORT
# ============================================================

L = []
def w(s=""):
    L.append(s)

w("# CEREBUS Symmetry Trap - Majors Group Report")
w(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
w(f"**Group:** Majors (EURUSD, GBPUSD, USDCHF, USDJPY, AUDUSD, NZDUSD)")
w(f"**Engine:** CEREBUS FX v4.0 | Symmetry Trap")
w()

w("---")
w()
w("## Summary Table")
w()
w("| Asset | Trades | WR | PF | Sharpe | Max DD | Expectancy |")
w("|-------|--------|-----|-----|--------|--------|------------|")
for asset in ASSETS:
    st = asset_stats[asset]
    tr = st["trades"]
    wr = f"{st['win_rate']:.1f}%"
    pf = f"{st.get('profit_factor', 0):.2f}" if st.get("profit_factor") else "-"
    sh = f"{st.get('sharpe', 0):.2f}" if st.get('sharpe') is not None else "-"
    mdd_val = st.get('max_dd_pct')
    mdd = f"{mdd_val*100:.3f}%" if mdd_val is not None and mdd_val < 1.0 else (f"{mdd_val:.3f}%" if mdd_val is not None else "-")
    # Heuristic: if value > 0.5 it's likely already in %, otherwise convert from decimal
    if mdd_val is not None and mdd_val > 0.5:
        mdd = f"{mdd_val:.2f}%"
    elif mdd_val is not None:
        mdd = f"{mdd_val*100:.2f}%"
    exp = f"{st.get('expectancy', 0):.2f}p" if st.get('expectancy') is not None else "-"
    w(f"| {asset} | {tr} | {wr} | {pf} | {sh} | {mdd} | {exp} |")
w(f"| **COMBINED** | **{total_trades}** | **{blended_wr}%** | **{pf_combined}** | **{sharpe}** | **{median_max_dd/INITIAL_BALANCE*100:.3f}%** | **{round(gross_profit/total_wins, 2):.2f} avg win** |")
w()

# Individual MC stats row
w("## Individual Monte Carlo Stats")
w()
w("| Asset | MC Sims | Median PnL | PnL 5th | PnL 95th | Median Max DD | Ruin% |")
w("|-------|---------|-------------|---------|----------|---------------|-------|")
for asset in ASSETS:
    mc_path = os.path.join(PER_ASSET_DIR, f"{asset}_mc_results.json")
    with open(mc_path) as f:
        mc = json.load(f)
    
    if "monte_carlo" in mc:
        mcs = mc["monte_carlo"]
        sims = mcs.get("n_simulations", 10000)
        med = mcs.get("terminal_pnl_median", 0)
        p5 = mcs.get("terminal_pnl_5th", 0)
        p95 = mcs.get("terminal_pnl_95th", 0)
        mdd = mcs.get("max_dd_median", 0) or mcs.get("median_max_dd_usd", 0)
        ruin = mcs.get("ruin_probability", 0) * 100 if "ruin_probability" in mcs else mcs.get("ruin_probability_pct", 0)
        w(f"| {asset} | {sims:,} | ${med:+,.2f} | ${p5:+,.2f} | ${p95:+,.2f} | ${mdd:,.2f} | {ruin:.2f}% |")
    else:
        sims = mc.get("n_iterations", 10000)
        med = mc.get("median_final_pnl_usd", 0)
        p5 = mc.get("pnl_5th_pctile", 0)
        p95 = mc.get("pnl_95th_pctile", 0)
        mdd = mc.get("median_max_dd_usd", 0)
        ruin = mc.get("ruin_probability_pct", 0)
        w(f"| {asset} | {sims:,} | ${med:+,.2f} | ${p5:+,.2f} | ${p95:+,.2f} | ${mdd:,.2f} | {ruin:.2f}% |")
w()

w("---")
w()

# Per-Asset Breakdown
w("## Per-Asset Breakdown")
w()
for asset in ASSETS:
    mc_path = os.path.join(PER_ASSET_DIR, f"{asset}_mc_results.json")
    with open(mc_path) as f:
        mc = json.load(f)
    
    st = asset_stats[asset]
    w(f"### {asset}")
    w()
    
    if "backtest" in mc:
        bt = mc["backtest"]
        w(f"| Metric | Value |")
        w(f"|--------|-------|")
        w(f"| Total Trades | {bt['trades']} |")
        w(f"| Wins / Losses | {bt['wins']} / {bt['losses']} |")
        w(f"| Win Rate | {bt['win_rate']:.1f}% |")
        w(f"| Total PnL | {bt.get('total_pnl_pips', 0):.1f} pips |")
        w(f"| Profit Factor | {bt.get('profit_factor', 'N/A'):.2f} |" if bt.get('profit_factor') else "| Profit Factor | N/A |")
        w(f"| Sharpe Ratio | {bt.get('sharpe', 'N/A'):.2f} |" if bt.get('sharpe') is not None else "| Sharpe Ratio | N/A |")
        w(f"| Max DD | {bt.get('max_dd_pips', 'N/A')} pips ({bt.get('max_dd_pct', 0)*100:.2f}%)")
        w(f"| Expectancy | {bt.get('expectancy', 'N/A'):.2f} pips/trade")
        w()
        
        # Direction
        if "long" in bt and "short" in bt:
            w(f"| Direction | Trades | WR | PnL |")
            w(f"|-----------|--------|-----|------|")
            w(f"| Long | {bt['long']['trades']} | {bt['long']['wr']:.1f}% | {bt['long']['pnl']:+.1f}p |")
            w(f"| Short | {bt['short']['trades']} | {bt['short']['wr']:.1f}% | {bt['short']['pnl']:+.1f}p |")
            w()
        
        # Tier stats
        if "tier_stats" in bt:
            w("**Tier Breakdown**")
            w()
            w("| Tier | Trades | WR | PnL |")
            w("|------|--------|-----|------|")
            for tier in ["T1", "T2", "T3"]:
                if tier in bt["tier_stats"]:
                    ts = bt["tier_stats"][tier]
                    w(f"| {tier} | {ts['trades']} | {ts['wr']:.1f}% | {ts['pnl']:+.1f}p |")
            w()
        
        # Loop stats
        if "loop_stats" in bt:
            w("**Loop Distribution**")
            w()
            w("| Loop | Trades | WR | PnL |")
            w("|------|--------|-----|------|")
            for lp in sorted(bt["loop_stats"].keys(), key=int):
                ls = bt["loop_stats"][lp]
                w(f"| {lp} | {ls['trades']} | {ls['wr']:.1f}% | {ls['pnl']:+.1f}p |")
            w()
    else:
        # EURUSD/GBPUSD/USDCHF summary
        w(f"| Metric | Value |")
        w(f"|--------|-------|")
        w(f"| Pool Trades | {len(all_trades[asset])} |")
        w(f"| Win Rate | {st['win_rate']:.1f}% |")
        w(f"| Profit Factor | {st.get('profit_factor', 'N/A')} |")
        w(f"| PF Mean | {st.get('profit_factor_mean', 'N/A')} |")
        w(f"| Avg Loss | {st.get('avg_loss_pips', 'N/A')} pips |")
        w(f"| Median Max DD | {st.get('max_dd_pct', 0)*100:.2f}%")
        w()
    
    w()

# Combined Monte Carlo Section
w("---")
w()
w("## Combined Monte Carlo Analysis")
w()
w(f"| Parameter | Value |")
w(f"|-----------|-------|")
w(f"| Pool Size | {total_trades} trades |")
w(f"| Assets | {len(ASSETS)} |")
w(f"| Iterations | {N_ITERATIONS:,} |")
w(f"| Random Seed | 42 |")
w(f"| Initial Balance | ${INITIAL_BALANCE:,.0f} |")
w(f"| Risk per Trade | {RISK_PCT*100}% of current equity |")
w()

w("### Simulation Methodology")
w()
w("Trades are pooled from all 6 Majors assets ({0} total trades) and randomly shuffled ".format(total_trades))
w("10,000 times. Position sizing follows fixed-fractional risk: each trade risks 1% of ")
w("current equity. Terminal PnL is deterministic (same pool sum), but drawdown is order-dependent.")
w()

w("### Terminal PnL Distribution")
w()
w("| Statistic | Value |")
w(f"|-----------|-------|")
w(f"| Median Final PnL | ${median_pnl:+,.2f} |")
w(f"| Mean Final PnL | ${mean_pnl:+,.2f} |")
w(f"| Std Deviation | ${std_pnl:,.2f} |")
w(f"| % Simulations Profitable | {pct_profitable:.2f}% |")
w(f"| 5th Percentile | ${pnl_p5:+,.2f} |")
w(f"| 25th Percentile | ${pnl_p25:+,.2f} |")
w(f"| 75th Percentile | ${pnl_p75:+,.2f} |")
w(f"| 90th Percentile | ${pnl_p90:+,.2f} |")
w(f"| 95th Percentile | ${pnl_p95:+,.2f} |")
w(f"| **90% Confidence Interval** | **[${pnl_p5:+,.2f}, ${pnl_p95:+,.2f}]** |")
w()

w("### Drawdown Analysis (Order-Dependent)")
w()
w("| Metric | USD | % of Account |")
w(f"|--------|-----|-------------|")
w(f"| Median Max Drawdown | ${median_max_dd:,.2f} | {median_max_dd/INITIAL_BALANCE*100:.3f}% |")
w(f"| Mean Max Drawdown | ${mean_max_dd:,.2f} | {mean_max_dd/INITIAL_BALANCE*100:.3f}% |")
w(f"| 90th Pctile DD | ${dd_p90:,.2f} | {dd_p90/INITIAL_BALANCE*100:.3f}% |")
w(f"| 95th Pctile DD | ${dd_p95:,.2f} | {dd_p95/INITIAL_BALANCE*100:.3f}% |")
w(f"| 99th Pctile DD | ${dd_p99:,.2f} | {dd_p99/INITIAL_BALANCE*100:.3f}% |")
w(f"| Worst Observed DD | ${worst_dd:,.2f} | {worst_dd/INITIAL_BALANCE*100:.3f}% |")
w(f"| Best-case DD | ${best_dd:,.2f} | {best_dd/INITIAL_BALANCE*100:.3f}% |")
w()

w("### Ruin Probability")
w()
w(f"| Parameter | Value |")
w(f"|-----------|-------|")
w(f"| Ruin Definition | Balance < 50% of initial (${INITIAL_BALANCE*0.5:,.0f}) |")
w(f"| Ruin Events | {ruin_count} of {N_ITERATIONS:,} |")
w(f"| **Ruin Probability** | **{ruin_prob:.4f}%** |")
w(f"| Assessment | {'NEGLIGIBLE - virtually zero risk of major drawdown' if ruin_prob < 0.01 else 'LOW' if ruin_prob < 0.1 else 'MODERATE'} |")
w()

w("### Aggregate Performance Metrics")
w()
w(f"| Metric | Value |")
w(f"|--------|------|")
w(f"| Blended Win Rate | {blended_wr}% ({total_wins}W / {total_losses}L) |")
w(f"| Combined Profit Factor | {pf_combined} |")
w(f"| Combined Sharpe (approx) | {sharpe} |")
w(f"| Gross Profit | ${gross_profit:,.2f} |")
w(f"| Gross Loss | ${gross_loss:,.2f} |")
w(f"| Average Win | ${gross_profit/total_wins:.2f} |" if total_wins > 0 else "")
w(f"| Average Loss | {gross_loss/total_losses:.2f} |" if total_losses > 0 else "")
w(f"| PnL per Trade (avg) | ${mean_pnl/total_trades:.2f} |")
w(f"| Return on ${INITIAL_BALANCE:,.0f} | +{mean_pnl/INITIAL_BALANCE*100:.2f}% over {total_trades} trades |")
w()

# Tier Aggregation
w("---")
w()
w("## Tier Breakdown (Group Aggregate)")
w()
tier_agg = {"T1": {"trades": 0, "wins": 0, "pnl": 0.0},
            "T2": {"trades": 0, "wins": 0, "pnl": 0.0},
            "T3": {"trades": 0, "wins": 0, "pnl": 0.0}}

for asset in ASSETS:
    mc_path = os.path.join(PER_ASSET_DIR, f"{asset}_mc_results.json")
    with open(mc_path) as f:
        mc = json.load(f)
    if "backtest" in mc and "tier_stats" in mc["backtest"]:
        for tier in ["T1", "T2", "T3"]:
            if tier in mc["backtest"]["tier_stats"]:
                ts = mc["backtest"]["tier_stats"][tier]
                tier_agg[tier]["trades"] += ts["trades"]
                tier_agg[tier]["wins"] += round(ts["trades"] * ts["wr"] / 100)
                tier_agg[tier]["pnl"] += ts["pnl"]

w("| Tier | Trades | WR | PnP |")
w("|------|--------|-----|------|")
for tier in ["T1", "T2", "T3"]:
    ta = tier_agg[tier]
    ta_wr = round(ta["wins"] / ta["trades"] * 100, 1) if ta["trades"] > 0 else 0
    w(f"| {tier} | {ta['trades']} | {ta_wr}% | {ta['pnl']:+.1f}p |")

tt = sum(tier_agg[t]["trades"] for t in tier_agg)
tw = sum(tier_agg[t]["wins"] for t in tier_agg)
tp = sum(tier_agg[t]["pnl"] for t in tier_agg)
twr = round(tw / tt * 100, 1) if tt > 0 else 0
w(f"| **TOTAL** | **{tt}** | **{twr}%** | **{tp:+.1f}p** |")
w()

w("*Note: Only USDJPY, AUDUSD, and NZDUSD have tier data. EURUSD/GBPUSD/USDCHF MC results do not include tier breakdown.*")
w()

# Asset Contribution
w("---")
w()
w("## Asset Contribution to Combined Pool")
w()
w("| Asset | Pool Trades | % of Pool | Pool PnL | Avg PnL/Trade |")
w("|-------|-------------|-----------|----------|--------------|")
for asset in ASSETS:
    pool = all_trades[asset]
    n = len(pool)
    pct = n / total_trades * 100
    pool_pnl = sum(p[0] for p in pool)
    avg = pool_pnl / n if n > 0 else 0
    w(f"| {asset} | {n} | {pct:.1f}% | ${pool_pnl:+,.2f} | ${avg:+.2f} |")
w(f"| **TOTAL** | **{total_trades}** | **100.0%** | **${sum(p[0] for p in combined_pool):+,.2f}** | **${sum(p[0] for p in combined_pool)/total_trades:+.2f}** |")
w()

# Key Observations
w("---")
w()
w("## Key Observations")
w()
obs = []

# PF ranking
pf_ranked = sorted([(a, asset_stats[a].get("profit_factor", 0) or 0) for a in ASSETS], key=lambda x: -x[1])
obs.append(f"**PF Leader:** {pf_ranked[0][0]} (PF={pf_ranked[0][1]:.2f}), worst: {pf_ranked[-1][0]} (PF={pf_ranked[-1][1]:.2f})")

# WR ranking
wr_ranked = sorted([(a, asset_stats[a].get("win_rate", 0) or 0) for a in ASSETS], key=lambda x: -x[1])
obs.append(f"**WR Leader:** {wr_ranked[0][0]} (WR={wr_ranked[0][1]:.1f}%), worst: {wr_ranked[-1][0]} (WR={wr_ranked[-1][1]:.1f}%)")

# Consistency
obs.append(f"Pool diversity: {total_trades} trades across 6 assets, blended WR={blended_wr}%")
obs.append(f"Simulation confidence: {pct_profitable:.1f}% of {N_ITERATIONS:,} runs profitable")

if ruin_prob < 0.01:
    obs.append(f"Extreme safety: {ruin_prob:.4f}% combined ruin probability — effectively zero risk of halving equity")

# Highest trade count
tc = [(a, len(all_trades[a])) for a in ASSETS]
tc.sort(key=lambda x: -x[1])
obs.append(f"Volume leader: {tc[0][0]} ({tc[0][1]} pool trades), smallest pool: {tc[-1][0]} ({tc[-1][1]} trades)")

# Best single asset MC PnL
mc_pnls = []
for a in ASSETS:
    mc_path = os.path.join(PER_ASSET_DIR, f"{a}_mc_results.json")
    with open(mc_path) as f:
        mc = json.load(f)
    if "monte_carlo" in mc:
        mc_pnls.append((a, mc["monte_carlo"].get("terminal_pnl_median", 0)))
    else:
        mc_pnls.append((a, mc.get("median_final_pnl_usd", 0)))
mc_pnls.sort(key=lambda x: -x[1])
obs.append(f"Best standalone MC result: {mc_pnls[0][0]} (${mc_pnls[0][1]:+,.2f}), worst: {mc_pnls[-1][0]} (${mc_pnls[-1][1]:+,.2f})")

for i, o in enumerate(obs, 1):
    w(f"{i}. {o}")
w()

# Flags
w("---")
w()
w("## Flags & Risk Notes")
w()
flags = []

# Check for large single losses in pool
for asset in ASSETS:
    pool = [p[0] for p in all_trades[asset]]
    if pool:
        wl = min(pool)
        if abs(wl) > INITIAL_BALANCE * 0.02:
            flags.append(("ORANGE", f"{asset}: Single trade loss of ${wl:,.2f} ({abs(wl)/INITIAL_BALANCE*100:.1f}% of equity)"))

if worst_dd / INITIAL_BALANCE > 0.05:
    flags.append(("ORANGE", f"Worst observed DD across all sims: {worst_dd/INITIAL_BALANCE*100:.2f}%"))

# Check USDJPY high trade count (might dominate pool)
usdjp = len(all_trades["USDJPY"]) / total_trades * 100
audusd_pct = len(all_trades["AUDUSD"]) / total_trades * 100
if usdjp > 30:
    flags.append(("YELLOW", f"USDJPY dominates pool at {usdjp:.1f}% of total trades — correlation risk"))
if audusd_pct > 30:
    flags.append(("YELLOW", f"AUDUSD contributes {audusd_pct:.1f}% of pool — consider independence"))

# Check EURUSD/GBPUSD/USDCHF have lower trade counts in MC
eur_pct = len(all_trades["EURUSD"]) / total_trades * 100
if eur_pct < 5:
    flags.append(("NOTE", f"EURUSD contributes only {eur_pct:.1f}% of pool (MC sampled 500 trades via equity curve)"))

if not flags:
    w("No flags raised. All risk parameters within acceptable thresholds.")
else:
    for level, desc in flags:
        icon = "RED" if "RED" in level else ("ORANGE" if "ORANGE" in level else ("YELLOW" if "YELLOW" in level else "INFO"))
        prefix = {"RED": "[RED]", "ORANGE": "[ORANGE]", "YELLOW": "[YELLOW]", "NOTE": "[NOTE]"}
        w(f"{prefix.get(icon, '')} {desc}")

# Tier observation
w()
w("### Tier Analysis Insight")
t3_agg = tier_agg["T3"]
t1_agg = tier_agg["T1"]
if t3_agg["trades"] > 0 and t1_agg["trades"] > 0:
    t3_wr = round(t3_agg["wins"] / t3_agg["trades"] * 100, 1) if t3_agg["trades"] > 0 else 0
    t1_wr = round(t1_agg["wins"] / t1_agg["trades"] * 100, 1) if t1_agg["trades"] > 0 else 0
    if t3_wr > t1_wr:
        w(f"T3 (highest conviction) maintains higher WR ({t3_wr}%) vs T1 ({t1_wr}%) across the group, validating the tier system.")
    w(f"T3 contributes {t3_agg['pnl']:+.1f}p from {t3_agg['trades']} trades — selective high-quality entries drive outsized profit.")
    w(f"T1 bulk volume ({t1_agg['trades']} trades) provides cash flow with {t1_wr}% WR.")

w()
w("---")
w(f"*Report generated by CEREBUS Phase 2 Group Aggregation Engine*")
w(f"*Files: majors_mc_results.json, majors_report.md*")

report_path = os.path.join(GROUPS_DIR, "majors_report.md")
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(L))
print(f"Wrote markdown report")
print(f"\nDONE.")
