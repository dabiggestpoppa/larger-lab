#!/usr/bin/env python3
"""
CEREBUS Symmetry Trap — Top 5 Majors: Full Backtest + Monte Carlo
===================================================================
Runs detailed backtest + 10K Monte Carlo sims for ETHUSD, HK50, NZDUSD, BTCUSD, US500.
Writes per-asset reports to quant-lab/reports/top5_majors/.
"""

import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

# Add engine path for sibling imports
sys.path.insert(0, os.path.dirname(__file__))

from symmetry_trap_backtest import (
    SymmetryTrapBacktest,
    compute_stats,
    load_m5_csv,
)

# ─── Configuration ───────────────────────────────────────────────────────

REPORTS_DIR = Path(__file__).parent.parent / "reports" / "top5_majors"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

ASSETS = [
    ("ETHUSD", "ETHUSD"),
    ("HK50", "HK50"),
    ("NZDUSD", "NZDUSD"),
    ("BTCUSD", "BTCUSD"),
    ("US500", "US500"),
]

DATA_DIR = Path(__file__).parent.parent / "data"


# ─── Monte Carlo (linear $/pip, matching existing report convention) ────

def _mc_percentile(data, pct):
    idx = int(len(data) * pct / 100.0)
    return data[min(idx, len(data) - 1)]


def _compute_equity_bands(pnl_list, n_sims=2000, trades_per_sim=None, starting_balance=10000.0):
    if not pnl_list:
        return {}
    if trades_per_sim is None:
        trades_per_sim = len(pnl_list)

    dollar_per_pip = 1.0
    ruin_threshold = starting_balance * 0.5
    equity_curves = []

    for _ in range(n_sims):
        balance = starting_balance
        curve = [balance]
        ruined = False
        for _ in range(trades_per_sim):
            pnl_pips = random.choice(pnl_list)
            balance += pnl_pips * dollar_per_pip
            curve.append(balance)
            if balance <= ruin_threshold:
                ruined = True
                break
        if ruined:
            while len(curve) <= trades_per_sim:
                curve.append(balance)
        equity_curves.append(curve)

    n_points = trades_per_sim + 1
    bands = {}
    for pt_idx in range(0, n_points, max(1, n_points // 20)):
        values = sorted(c[min(pt_idx, len(c) - 1)] for c in equity_curves)
        bands[str(pt_idx)] = {
            "p5": round(_mc_percentile(values, 5), 2),
            "p50": round(_mc_percentile(values, 50), 2),
            "p95": round(_mc_percentile(values, 95), 2),
        }
    return bands


def monte_carlo_simulation(
    pnl_list: list,
    n_sims: int = 10000,
    trades_per_sim: int = None,
    starting_balance: float = 10000.0,
    risk_per_trade: float = 0.01,
) -> dict:
    """
    Monte Carlo with actual per-trade PnL resampling (with replacement).
    Linear model: $1 per pip, no compounding. Matches existing report convention.
    Ruin = balance drops to 50% of starting.
    """
    if not pnl_list:
        return {}
    if trades_per_sim is None:
        trades_per_sim = len(pnl_list)

    dollar_per_pip = 1.0
    ruin_threshold = starting_balance * 0.5

    final_balances = []
    max_drawdowns = []
    total_pnls_list = []
    profit_factors = []
    ruin_count = 0

    for _ in range(n_sims):
        balance = starting_balance
        peak = balance
        max_dd_pct = 0.0
        gross_profit = 0.0
        gross_loss = 0.0

        for _ in range(trades_per_sim):
            pnl_pips = random.choice(pnl_list)
            dollar_pnl = pnl_pips * dollar_per_pip
            balance += dollar_pnl
            if dollar_pnl > 0:
                gross_profit += dollar_pnl
            else:
                gross_loss += abs(dollar_pnl)

            if balance > peak:
                peak = balance
            dd = (peak - balance) / peak * 100.0 if peak > 0 else 0.0
            if dd > max_dd_pct:
                max_dd_pct = dd
            if balance <= ruin_threshold:
                break

        final_balances.append(balance)
        max_drawdowns.append(max_dd_pct)
        total_pnls_list.append(balance - starting_balance)
        pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        profit_factors.append(pf)
        if balance <= ruin_threshold:
            ruin_count += 1

    final_balances.sort()
    max_drawdowns.sort()
    total_pnls_list.sort()
    profitable_sims = sum(1 for b in final_balances if b > starting_balance)

    return {
        "n_sims": n_sims,
        "trades_per_sim": trades_per_sim,
        "starting_balance": starting_balance,
        "risk_per_trade": risk_per_trade,
        "ruin_threshold": ruin_threshold,
        "ruin_probability": round(ruin_count / n_sims * 100.0, 2),
        "profitable_simulations": round(profitable_sims / n_sims * 100.0, 1),
        "mean_final_balance": round(sum(final_balances) / len(final_balances), 2),
        "median_final_balance": round(_mc_percentile(final_balances, 50), 2),
        "final_balance_ci_90": [
            round(_mc_percentile(final_balances, 5), 2),
            round(_mc_percentile(final_balances, 95), 2),
        ],
        "total_pnl_distribution": {
            "min": round(_mc_percentile(total_pnls_list, 0), 2),
            "p5": round(_mc_percentile(total_pnls_list, 5), 2),
            "p10": round(_mc_percentile(total_pnls_list, 10), 2),
            "p25": round(_mc_percentile(total_pnls_list, 25), 2),
            "p50": round(_mc_percentile(total_pnls_list, 50), 2),
            "p75": round(_mc_percentile(total_pnls_list, 75), 2),
            "p90": round(_mc_percentile(total_pnls_list, 90), 2),
            "p95": round(_mc_percentile(total_pnls_list, 95), 2),
            "p100": round(_mc_percentile(total_pnls_list, 100), 2),
            "ci_90": [
                round(_mc_percentile(total_pnls_list, 5), 2),
                round(_mc_percentile(total_pnls_list, 95), 2),
            ],
        },
        "max_drawdown_distribution_pct": {
            "p5": round(_mc_percentile(max_drawdowns, 5), 2),
            "p25": round(_mc_percentile(max_drawdowns, 25), 2),
            "median": round(_mc_percentile(max_drawdowns, 50), 2),
            "mean": round(sum(max_drawdowns) / len(max_drawdowns), 2),
            "p75": round(_mc_percentile(max_drawdowns, 75), 2),
            "p95": round(_mc_percentile(max_drawdowns, 95), 2),
            "max": round(_mc_percentile(max_drawdowns, 100), 2),
        },
        "equity_curve_bands": _compute_equity_bands(
            pnl_list, n_sims=2000,
            trades_per_sim=trades_per_sim,
            starting_balance=starting_balance,
        ),
    }


# ─── Report Generation ──────────────────────────────────────────────────

def generate_report(symbol, result, mc_results, config):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pip_size = config.get("pip_value", 0.0001)
    lines = []
    lines.append(f"# CEREBUS Symmetry Trap — Full Backtest Report: {symbol}\n")
    lines.append(f"> Generated: {now}")
    lines.append(f"> Engine: CEREBUS Symmetry Trap v4.0 (Model B, 4-state FSM)")
    lines.append(f"> Pip Value: {pip_size}\n")

    t = result
    # Summary
    lines.append("## Executive Summary\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Trades | {t.total_trades} |")
    lines.append(f"| Wins / Losses | {t.wins} / {t.losses} |")
    lines.append(f"| Win Rate | {t.win_rate:.1f}% |")
    lines.append(f"| Total PnL | {t.total_pnl_pips:+.1f} pips |")
    lines.append(f"| Profit Factor | {t.profit_factor:.2f} |")
    lines.append(f"| Sharpe Ratio | {t.sharpe_ratio:.2f} |")
    lines.append(f"| Expectancy | {t.expectancy_pips:+.2f} pips |")
    lines.append(f"| Avg Win | {t.avg_win_pips:+.1f} pips |")
    lines.append(f"| Avg Loss | {t.avg_loss_pips:+.1f} pips |")
    lines.append(f"| Max Drawdown | {t.max_drawdown_pips:.1f} pips ({t.max_drawdown_pct:.2f}%) |")
    lines.append(f"| Kelly Criterion | {t.kelly_criterion:.4f} |")
    lines.append(f"| Max Consec Wins | {t.max_consec_wins} |")
    lines.append(f"| Max Consec Losses | {t.max_consec_losses} |")
    lines.append(f"| Data Bars | {t.data_bars:,} |")
    lines.append(f"| Data Days | {t.data_days} |")
    lines.append("")

    # Direction Breakdown
    lines.append("## Long / Short Breakdown\n")
    lines.append("| Direction | Trades | Win Rate | PnL |")
    lines.append("|-----------|--------|----------|-----|")
    lines.append(f"| LONG | {t.long_trades} | {t.long_wr:.1f}% | {t.long_pnl:+.1f}p |")
    lines.append(f"| SHORT | {t.short_trades} | {t.short_wr:.1f}% | {t.short_pnl:+.1f}p |")
    dir_spread = abs(t.long_wr - t.short_wr) if t.long_trades > 0 and t.short_trades > 0 else 0
    lines.append(f"\n**Directional spread: {dir_spread:.1f}%** -- {'negligible' if dir_spread < 5 else 'moderate'} variance.\n")

    # Tier Breakdown (detailed)
    lines.append("## Tier Breakdown\n")
    tier_config = config.get("tiers", {})
    lines.append("| Tier | AR Max | AU | Trigger | Trades | WR | PnL | % Trades |")
    lines.append("|------|--------|-----|---------|--------|-----|------|----------|")
    if t.total_trades > 0:
        for tier in ["T1", "T2", "T3"]:
            ts = t.tier_stats.get(tier, {})
            if ts:
                tc = tier_config.get(tier, {})
                ar_max = tc.get("ar_max", "-")
                au = tc.get("au", "-")
                trigger = tc.get("trigger", "-")
                pct = ts['trades'] / t.total_trades * 100
                lines.append(f"| {tier} | {ar_max}p | {au}p | {trigger}p | {ts['trades']} | {ts['wr']:.1f}% | {ts['pnl']:+.1f}p | {pct:.1f}% |")
    lines.append("")
    if t.tier_stats:
        best_tier = max(t.tier_stats.keys(), key=lambda k: t.tier_stats[k].get('wr', 0))
        worst_tier = min(t.tier_stats.keys(), key=lambda k: t.tier_stats[k].get('wr', 0))
        lines.append(f"**{best_tier} has the best WR**; {worst_tier} is the weakest.\n")

    # Loop Distribution
    lines.append("## Loop Distribution (Option B)\n")
    lines.append("| Loop | Trades | WR | PnL |")
    lines.append("|------|--------|-----|------|")
    for loop_key in sorted(t.loop_stats.keys(), key=lambda x: int(x) if x.isdigit() else 99):
        ls = t.loop_stats[loop_key]
        lines.append(f"| Loop {loop_key} | {ls['trades']} | {ls['wr']:.1f}% | {ls['pnl']:+.1f}p |")
    if t.loop_stats:
        total_l12 = sum(t.loop_stats[k]['trades'] for k in t.loop_stats if k in ('1', '2'))
        if t.total_trades > 0:
            lines.append(f"\n**{total_l12 / t.total_trades * 100:.0f}% of trades from Loops 1-2.**\n")
    lines.append("")

    # Hourly Distribution
    lines.append("## Hourly Distribution (EST)\n")
    lines.append("| Hour | Trades | WR | PnL |")
    lines.append("|------|--------|-----|------|")
    for h in sorted(t.hourly_stats.keys(), key=int):
        hs = t.hourly_stats[h]
        lines.append(f"| {int(h):02d}:00 | {hs['trades']} | {hs['wr']:.1f}% | {hs['pnl']:+.1f}p |")
    lines.append("")

    # Per-Trade PnL Distribution stats
    lines.append("## Per-Trade PnL Distribution\n")
    pnls = [tr.pnl_pips for tr in t.trades] if t.trades else []
    if pnls:
        wins_p = [p for p in pnls if p > 0]
        losses_p = [p for p in pnls if p < 0]
        sorted_pnls = sorted(pnls)
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Win Count | {len(wins_p)} |")
        lines.append(f"| Loss Count | {len(losses_p)} |")
        lines.append(f"| Best Trade | {max(pnls):+.1f} pips |")
        lines.append(f"| Worst Trade | {min(pnls):+.1f} pips |")
        lines.append(f"| Median Trade | {sorted_pnls[len(sorted_pnls)//2]:+.1f} pips |")
        lines.append("")

        # Histogram
        bins = [(-999, -20), (-20, -10), (-10, -5), (-5, -1), (-1, 0),
                (0, 1), (1, 5), (5, 10), (10, 20), (20, 50), (50, 100), (100, 999)]
        lines.append("| PnL Range (pips) | Count | Bar |")
        lines.append("|------------------|-------|-----|")
        max_count = 1
        bin_counts = []
        for lo, hi in bins:
            c = sum(1 for p in pnls if lo <= p < hi)
            bin_counts.append(((lo, hi), c))
            max_count = max(max_count, c)
        for (lo, hi), c in bin_counts:
            bar = '#' * int(c / max_count * 30) if max_count > 0 else ''
            label = f"{lo:+.0f} to {hi:+.0f}" if lo > -999 else f"< {hi:+.0f}"
            if hi < 999:
                label = f"{lo:+.0f} to {hi:+.0f}"
            else:
                label = f"> {lo:+.0f}"
            lines.append(f"| {label} | {c} | {bar} |")
        lines.append("")

    # Per-Trade PnL List
    lines.append("## Per-Trade PnL List\n")
    lines.append("| # | Entry | Exit | Dir | Tier | Loop | Result | PnL (pips) |")
    lines.append("|---|-------|------|-----|------|------|--------|------------|")
    for i, tr in enumerate(t.trades, 1):
        es = tr.entry_time.strftime("%Y-%m-%d %H:%M") if tr.entry_time else "-"
        exs = tr.exit_time.strftime("%Y-%m-%d %H:%M") if tr.exit_time else "-"
        lines.append(f"| {i} | {es} | {exs} | {tr.direction[:4]} | {tr.tier} | {tr.loop_count} | {tr.result} | {tr.pnl_pips:+.1f} |")
    lines.append("")

    # Monte Carlo Section
    lines.append("## Monte Carlo Simulation\n")
    if mc_results:
        lines.append("**Parameters:**")
        lines.append(f"- Simulations: {mc_results['n_sims']:,}")
        lines.append(f"- Trades per simulation: {mc_results['trades_per_sim']}")
        lines.append(f"- Starting balance: ${mc_results['starting_balance']:,.0f}")
        lines.append(f"- Risk per trade: {mc_results['risk_per_trade']*100:.0f}%")
        lines.append("- Method: Resampled actual per-trade PnL (with replacement)")
        lines.append("")

        lines.append("### Ruin & Profitability\n")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Ruin Probability | {mc_results['ruin_probability']:.2f}% |")
        lines.append(f"| Profitable Simulations | {mc_results['profitable_simulations']:.1f}% |")
        lines.append(f"| Mean Final Balance | ${mc_results['mean_final_balance']:,.2f} |")
        lines.append(f"| Median Final Balance | ${mc_results['median_final_balance']:,.2f} |")
        lines.append("")

        lines.append("### Total PnL Distribution\n")
        pnl_dist = mc_results['total_pnl_distribution']
        lines.append("| Percentile | PnL ($) |")
        lines.append("|------------|---------|")
        lines.append(f"| Min | ${pnl_dist['min']:,.2f} |")
        lines.append(f"| 5th | ${pnl_dist['p5']:,.2f} |")
        lines.append(f"| 10th | ${pnl_dist['p10']:,.2f} |")
        lines.append(f"| 25th | ${pnl_dist['p25']:,.2f} |")
        lines.append(f"| 50th (Median) | ${pnl_dist['p50']:,.2f} |")
        lines.append(f"| 75th | ${pnl_dist['p75']:,.2f} |")
        lines.append(f"| 90th | ${pnl_dist['p90']:,.2f} |")
        lines.append(f"| 95th | ${pnl_dist['p95']:,.2f} |")
        lines.append(f"| Max | ${pnl_dist['p100']:,.2f} |")
        ci = pnl_dist['ci_90']
        lines.append(f"| **90% CI** | **[${ci[0]:,.2f}, ${ci[1]:,.2f}]** |")
        lines.append("")

        lines.append("### Max Drawdown Distribution (% of peak equity)\n")
        dd = mc_results['max_drawdown_distribution_pct']
        lines.append("| Percentile | Max DD (%) |")
        lines.append("|------------|------------|")
        lines.append(f"| 5th | {dd['p5']:.2f}% |")
        lines.append(f"| 25th | {dd['p25']:.2f}% |")
        lines.append(f"| Median | {dd['median']:.2f}% |")
        lines.append(f"| Mean | {dd['mean']:.2f}% |")
        lines.append(f"| 75th | {dd['p75']:.2f}% |")
        lines.append(f"| 95th | {dd['p95']:.2f}% |")
        lines.append(f"| Max | {dd['max']:.2f}% |")
        lines.append("")

        lines.append("### Equity Curve Bands\n")
        ec = mc_results.get('equity_curve_bands', {})
        if ec:
            lines.append("| Trade # | 5th %ile | Median | 95th %ile |")
            lines.append("|---------|----------|--------|----------|")
            for pt in sorted(ec.keys(), key=lambda x: int(x)):
                e = ec[pt]
                lines.append(f"| {pt} | ${e['p5']:,.0f} | ${e['p50']:,.0f} | ${e['p95']:,.0f} |")
        lines.append("")

    # Key Observations
    lines.append("## Key Observations\n")
    if t.win_rate >= 90:
        lines.append(f"- **Elite WR ({t.win_rate:.1f}%)** -- Approaching regime detection threshold.")
    elif t.win_rate >= 80:
        lines.append(f"- **Strong WR ({t.win_rate:.1f}%)** -- Well above threshold.")
    else:
        lines.append(f"- WR {t.win_rate:.1f}% -- below expected range.")

    if t.profit_factor > 10:
        lines.append(f"- **PF {t.profit_factor:.1f}** -- Exceptional risk/reward.")
    elif t.profit_factor > 3:
        lines.append(f"- PF {t.profit_factor:.1f} -- strong edge.")

    if t.max_drawdown_pct < 0.5:
        lines.append(f"- **Max DD {t.max_drawdown_pct:.2f}%** -- minimal capital erosion.")
    elif t.max_drawdown_pct < 2:
        lines.append(f"- Max DD {t.max_drawdown_pct:.2f}% -- manageable.")

    if abs(t.long_wr - t.short_wr) < 5:
        lines.append("- Directionally balanced -- no directional bias.")
    else:
        bias = "LONG" if t.long_wr > t.short_wr else "SHORT"
        lines.append(f"- Directional bias towards {bias} ({abs(t.long_wr - t.short_wr):.1f}% spread).")

    l1 = t.loop_stats.get('1', {})
    if l1.get('wr', 0) > 90:
        lines.append(f"- **Loop 1 WR {l1['wr']:.1f}%** -- strongest edge on first impulses.")

    if mc_results:
        if mc_results['ruin_probability'] < 1:
            lines.append(f"- **Ruin prob {mc_results['ruin_probability']:.2f}%** -- essentially zero.")
        prof = mc_results['profitable_simulations']
        if prof > 99:
            lines.append(f"- **{prof:.1f}% MC sims profitable** -- robust across all sequences.")
    lines.append("")

    # Flags
    lines.append("## Flags & Recommendations\n")
    flags = []
    if t.win_rate < 70:
        flags.append("- WR below 70% -- investigate parameter fit.")
    if t.total_trades < 50:
        flags.append("- Fewer than 50 trades -- statistically weak sample.")
    if t.profit_factor < 1.5:
        flags.append("- PF below 1.5 -- edge may be insufficient after costs.")
    if t.max_drawdown_pct > 5:
        flags.append("- Max DD > 5% -- consider tighter risk management.")

    for k, v in t.loop_stats.items():
        if int(k) >= 3 and v.get('wr', 0) < 60:
            flags.append("- Loops 3+ show WR < 60% -- consider reducing max loops.")

    kill_count = sum(1 for tr in t.trades if tr.result == "KILL_SWITCH")
    if kill_count > t.total_trades * 0.2:
        flags.append(f"- {kill_count} kill-switches ({kill_count/t.total_trades*100:.0f}% of trades).")

    if not flags:
        flags.append("- No critical flags. Configuration looks clean.")
    for f in flags:
        lines.append(f)
    lines.append("")

    lines.append(f"\n---\n\n*MC raw results: `{symbol}_mc_results.json`*")
    return "\n".join(lines)


# ─── Main ────────────────────────────────────────────────────────────────

def main():
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from configs.asset_configs import ASSET_CONFIGS

    summary = {}
    random.seed(42)

    for symbol_key, csv_name in ASSETS:
        print(f"\n{'='*60}")
        print(f"Running: {symbol_key}")
        print(f"{'='*60}")

        config = ASSET_CONFIGS[symbol_key]
        csv_path = str(DATA_DIR / f"{csv_name}_M5.csv")

        bt = SymmetryTrapBacktest(config=config, symbol=symbol_key)
        bars, _ = load_m5_csv(csv_path, config.get("pip_value", 0.0001))
        result = bt.run(bars)
        result.symbol = symbol_key

        t = result
        print(f"  Trades: {t.total_trades} | WR: {t.win_rate:.1f}% | PnL: {t.total_pnl_pips:+.1f}p | PF: {t.profit_factor:.2f} | Sharpe: {t.sharpe_ratio:.2f}")

        pnl_list = [tr.pnl_pips for tr in t.trades] if t.trades else []
        mc_results = None
        if pnl_list:
            print(f"  MC: 10K sims...")
            mc_results = monte_carlo_simulation(pnl_list, n_sims=10000, trades_per_sim=len(pnl_list))
            print(f"  MC: Ruin={mc_results['ruin_probability']:.2f}% | Profitable={mc_results['profitable_simulations']:.1f}% | MedPnL=${mc_results['total_pnl_distribution']['p50']:,.0f}")

        report_text = generate_report(symbol_key, result, mc_results, config)
        report_path = REPORTS_DIR / f"{symbol_key}_full_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)
        print(f"  Report: {report_path}")

        if mc_results:
            mc_path = REPORTS_DIR / f"{symbol_key}_mc_results.json"
            with open(mc_path, "w", encoding="utf-8") as f:
                json.dump(mc_results, f, indent=2, default=str)
            print(f"  MC JSON: {mc_path}")

        summary[symbol_key] = {
            "trades": t.total_trades,
            "wr": round(t.win_rate, 1),
            "pnl_pips": round(t.total_pnl_pips, 1),
            "pf": round(t.profit_factor, 2),
            "sharpe": round(t.sharpe_ratio, 2),
            "max_dd_pct": round(t.max_drawdown_pct, 2),
            "ruin_prob": mc_results['ruin_probability'] if mc_results else None,
            "mc_profitable_pct": mc_results['profitable_simulations'] if mc_results else None,
            "mc_median_pnl": mc_results['total_pnl_distribution']['p50'] if mc_results else None,
        }

    # Batch summary
    summary_path = Path(__file__).parent.parent / "progress" / "st-phase5-top5-progress.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# Phase 5 Top 5 Majors -- Batch Summary\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("| Asset | Trades | WR | PnL (pips) | PF | Sharpe | MaxDD% | Ruin% | MC Profitable% | MC Med PnL |\n")
        f.write("|-------|--------|-----|------------|-----|--------|--------|-------|----------------|------------|\n")
        for sym, s in summary.items():
            mc_pnl = f"${s['mc_median_pnl']:,.0f}" if s['mc_median_pnl'] is not None else "-"
            f.write(f"| {sym} | {s['trades']} | {s['wr']}% | {s['pnl_pips']:+.1f} | {s['pf']:.2f} | {s['sharpe']:.2f} | {s['max_dd_pct']:.2f}% | {s['ruin_prob']}% | {s['mc_profitable_pct']}% | {mc_pnl} |\n")
        f.write(f"\nReports: `{REPORTS_DIR}`\n")
    print(f"\nBatch summary: {summary_path}")
    print("ALL DONE")


if __name__ == "__main__":
    os.chdir(Path(__file__).parent.parent)
    main()
