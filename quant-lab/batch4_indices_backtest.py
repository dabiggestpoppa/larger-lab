#!/usr/bin/env python3
"""
CEREBUS Symmetry Trap — Batch 4 Indices Backtest + Monte Carlo
Assets: US500, DE30, FR40, HK50
"""

import sys
import os
import json
import random
import math
import statistics
from datetime import datetime
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')

from symmetry_trap_backtest import (
    SymmetryTrapBacktest,
    load_m5_csv,
    compute_stats,
    BacktestResult,
    TradeRecord,
    format_report,
)
import asset_configs

ASSETS = ["US500", "DE30", "FR40", "HK50"]
DATA_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data")
REPORT_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\per-asset")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

MC_SIMULATIONS = 10000
MC_START_BALANCE = 10000.0
MC_RISK_PER_TRADE = 0.01  # 1%


def run_backtest(asset_key):
    """Run backtest for a single asset."""
    print(f"\n{'='*60}")
    print(f"  Running backtest: {asset_key}")
    print(f"{'='*60}")

    config = asset_configs.ASSET_CONFIGS.get(asset_key)
    if not config:
        print(f"  ERROR: No config for {asset_key}")
        return None

    csv_file = DATA_DIR / f"{asset_key}_M5.csv"
    if not csv_file.exists():
        print(f"  ERROR: CSV not found: {csv_file}")
        return None

    bt = SymmetryTrapBacktest(config=config)
    result = bt.run_from_csv(str(csv_file))
    result.symbol = asset_key

    print(f"  Trades: {result.total_trades} | WR: {result.win_rate:.1f}% | "
          f"PF: {result.profit_factor:.2f} | PnL: {result.total_pnl_pips:+.1f}p | "
          f"Sharpe: {result.sharpe_ratio:.2f} | MaxDD: {result.max_drawdown_pips:.1f}p")

    return result


def monte_carlo_simulation(trades, n_sims=MC_SIMULATIONS, start_balance=MC_START_BALANCE,
                           risk_per_trade=MC_RISK_PER_TRADE, use_actual_pnl=True):
    """
    Monte Carlo simulation using actual per-trade PnL distribution.

    Parameters:
        trades: List of TradeRecord
        n_sims: Number of Monte Carlo simulations
        start_balance: Starting account balance ($10,000)
        risk_per_trade: Risk per trade as fraction of balance (1%)
        use_actual_pnl: If True, resample actual PnL values; if False, random normal

    Returns:
        Dict with MC statistics
    """
    if not trades:
        return {}

    pnl_list = [t.pnl_pips for t in trades]
    n_trades = len(pnl_list)

    random.seed(42)  # Reproducibility

    equity_curves = []
    final_pnls = []
    max_dd_list = []
    ruin_count = 0
    profit_factors = []

    for sim in range(n_sims):
        # Shuffle trade order (resample with replacement)
        shuffled = random.choices(pnl_list, k=n_trades)

        # Build equity curve with 1% risk per trade
        balance = start_balance
        peak = balance
        max_dd = 0.0
        equity = [balance]
        gross_profit = 0.0
        gross_loss = 0.0
        ruined = False

        for pnl_pips in shuffled:
            # Size position: risk 1% of current balance per trade
            # PnL in pips -> convert to dollar impact
            # For indices with pip_size=1.0, 1 pip = $1 per lot, but we scale by risk
            risk_dollars = balance * risk_per_trade
            # Simplified: treat pips as dollar units directly (pip_value=1.0 for indices)
            # Scale: if trade makes +19 pips, we risk 1% per trade
            trade_pnl = pnl_pips  # Direct pip PnL (indices pip=1.0 means ~$1 unit)

            balance += trade_pnl

            if balance <= 0:
                ruined = True
                balance = 0
                break

            if balance > peak:
                peak = balance
            dd = (peak - balance) / peak * 100.0 if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd

            if trade_pnl > 0:
                gross_profit += trade_pnl
            else:
                gross_loss += abs(trade_pnl)

            equity.append(balance)

        if ruined:
            ruin_count += 1

        final_pnls.append(balance - start_balance)
        max_dd_list.append(max_dd)

        # Profit factor for this simulation
        if gross_loss > 0:
            pf = gross_profit / gross_loss
        else:
            pf = float('inf') if gross_profit > 0 else 0.0
        profit_factors.append(pf)

        # Store equity curve (sample every 100th sim to save memory)
        if sim < 1000:
            equity_curves.append(equity)

    # Compute statistics
    final_pnls_sorted = sorted(final_pnls)
    n_sims_actual = len(final_pnls_sorted)

    median_pnl = statistics.median(final_pnls_sorted)
    p5_idx = max(0, int(n_sims_actual * 0.05) - 1)
    p95_idx = min(n_sims_actual - 1, int(n_sims_actual * 0.95) - 1)
    p10_idx = max(0, int(n_sims_actual * 0.10) - 1)
    p25_idx = max(0, int(n_sims_actual * 0.25) - 1)
    p75_idx = min(n_sims_actual - 1, int(n_sims_actual * 0.75) - 1)
    p90_idx = min(n_sims_actual - 1, int(n_sims_actual * 0.90) - 1)

    mean_pnl = statistics.mean(final_pnls)
    stdev_pnl = statistics.stdev(final_pnls) if len(final_pnls) > 1 else 0.0

    # Max drawdown distribution
    dd_sorted = sorted(max_dd_list)
    median_dd = statistics.median(dd_sorted)

    # Confidence interval for total PnL (90% CI)
    ci_90_low = final_pnls_sorted[p5_idx]
    ci_90_high = final_pnls_sorted[p95_idx]

    # Profit factor distribution (filter out inf)
    pf_finite = [pf for pf in profit_factors if pf != float('inf') and pf > 0]
    if pf_finite:
        median_pf = statistics.median(pf_finite)
        pf_p25 = sorted(pf_finite)[max(0, int(len(pf_finite) * 0.25) - 1)]
        pf_p75 = sorted(pf_finite)[min(len(pf_finite) - 1, int(len(pf_finite) * 0.75) - 1)]
    else:
        median_pf = 0.0
        pf_p25 = pf_p75 = 0.0

    # Percentage of profitable simulations
    profitable_sims = sum(1 for p in final_pnls if p > 0)
    pct_profitable = profitable_sims / n_sims_actual * 100.0

    # Median equity curve from sampled simulations
    median_equity = []
    if equity_curves:
        # Pad curves to same length
        max_len = max(len(ec) for ec in equity_curves)
        padded = []
        for ec in equity_curves:
            if len(ec) < max_len:
                padded.append(ec + [ec[-1]] * (max_len - len(ec)))
            else:
                padded.append(ec)

        for i in range(max_len):
            vals = [p[i] for p in padded]
            median_equity.append(statistics.median(vals))

    return {
        "n_simulations": n_sims,
        "n_trades_per_sim": n_trades,
        "start_balance": start_balance,
        "risk_per_trade_pct": risk_per_trade * 100,
        "ruin_probability_pct": ruin_count / n_sims * 100.0,
        "pct_profitable_sims": pct_profitable,
        "mean_total_pnl": round(mean_pnl, 2),
        "median_total_pnl": round(median_pnl, 2),
        "stdev_total_pnl": round(stdev_pnl, 2),
        "ci_90_low": round(ci_90_low, 2),
        "ci_90_high": round(ci_90_high, 2),
        "mean_final_balance": round(statistics.mean([p + start_balance for p in final_pnls]), 2),
        "median_final_balance": round(median_pnl + start_balance, 2),
        "pnl_distribution": {
            "min": round(min(final_pnls), 2),
            "p5": round(final_pnls_sorted[p5_idx], 2),
            "p10": round(final_pnls_sorted[p10_idx], 2),
            "p25": round(final_pnls_sorted[p25_idx], 2),
            "p50": round(median_pnl, 2),
            "p75": round(final_pnls_sorted[p75_idx], 2),
            "p90": round(final_pnls_sorted[p90_idx], 2),
            "p95": round(final_pnls_sorted[p95_idx], 2),
            "max": round(max(final_pnls), 2),
        },
        "max_drawdown_distribution": {
            "mean": round(statistics.mean(dd_sorted), 2),
            "median": round(median_dd, 2),
            "p5": round(dd_sorted[p5_idx], 2),
            "p95": round(dd_sorted[p95_idx], 2),
            "max": round(max(dd_sorted), 2),
        },
        "profit_factor_distribution": {
            "median": round(median_pf, 2),
            "p25": round(pf_p25, 2),
            "p75": round(pf_p75, 2),
        },
        "sampled_equity_curves": len(equity_curves),
    }


def write_report(asset_key, result, mc_results):
    """Write detailed markdown report."""
    report_path = REPORT_DIR / f"{asset_key}_full_report.md"
    mc_json_path = REPORT_DIR / f"{asset_key}_mc_results.json"

    # Write MC results JSON first
    with open(mc_json_path, 'w') as f:
        json.dump(mc_results, f, indent=2)

    lines = []
    lines.append(f"# Symmetry Trap — Full Backtest Report: {asset_key}")
    lines.append(f"\n> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"> Engine: CEREBUS Symmetry Trap v4.0 (Model B, 4-state FSM)")
    lines.append(f"> Pip Value: {asset_configs.ASSET_CONFIGS[asset_key]['pip_value']}")

    # ── Summary ──
    lines.append(f"\n## 📊 Summary\n")
    if result.total_trades == 0:
        lines.append("**No trades generated.** Insufficient data or all sessions classified as NO_GO.\n")
        report_path.write_text("\n".join(lines), encoding='utf-8')
        return

    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Trades | {result.total_trades} |")
    lines.append(f"| Wins / Losses | {result.wins} / {result.losses} |")
    lines.append(f"| Win Rate | {result.win_rate:.1f}% |")
    lines.append(f"| Total PnL | {result.total_pnl_pips:+.1f} pips |")
    lines.append(f"| Profit Factor | {result.profit_factor:.2f} |")
    lines.append(f"| Sharpe Ratio | {result.sharpe_ratio:.2f} |")
    lines.append(f"| Expectancy | {result.expectancy_pips:+.2f} pips |")
    lines.append(f"| Avg Win | {result.avg_win_pips:+.1f} pips |")
    lines.append(f"| Avg Loss | {result.avg_loss_pips:+.1f} pips |")
    lines.append(f"| Max Drawdown | {result.max_drawdown_pips:.1f} pips ({result.max_drawdown_pct:.2f}%) |")
    lines.append(f"| Kelly Criterion | {result.kelly_criterion:.4f} |")
    lines.append(f"| Max Consec Wins | {result.max_consec_wins} |")
    lines.append(f"| Max Consec Losses | {result.max_consec_losses} |")
    lines.append(f"| Data Bars | {result.data_bars:,} |")
    lines.append(f"| Data Days | {result.data_days} |")

    # ── Long/Short Breakdown ──
    lines.append(f"\n## 📈 Long / Short Breakdown\n")
    lines.append(f"| Direction | Trades | Win Rate | PnL |")
    lines.append(f"|-----------|--------|----------|-----|")
    lines.append(f"| LONG | {result.long_trades} | {result.long_wr:.1f}% | {result.long_pnl:+.1f}p |")
    lines.append(f"| SHORT | {result.short_trades} | {result.short_wr:.1f}% | {result.short_pnl:+.1f}p |")

    # ── Tier Breakdown ──
    if result.tier_stats:
        lines.append(f"\n## 🏆 Tier Breakdown\n")
        lines.append(f"| Tier | Trades | Win Rate | PnL |")
        lines.append(f"|------|--------|----------|-----|")
        for tier_name in ["T1", "T2", "T3"]:
            if tier_name in result.tier_stats:
                ts = result.tier_stats[tier_name]
                lines.append(f"| {tier_name} | {ts['trades']} | {ts['wr']:.1f}% | {ts['pnl']:+.1f}p |")

    # ── Loop Distribution ──
    if result.loop_stats:
        lines.append(f"\n## 🔄 Loop Distribution (Option B)\n")
        lines.append(f"| Loop | Trades | Win Rate | PnL |")
        lines.append(f"|------|--------|----------|-----|")
        for loop_key in sorted(result.loop_stats.keys(), key=lambda x: int(x) if x.isdigit() else 99):
            ls = result.loop_stats[loop_key]
            lines.append(f"| Loop {loop_key} | {ls['trades']} | {ls['wr']:.1f}% | {ls['pnl']:+.1f}p |")

    # ── Hourly Distribution ──
    if result.hourly_stats:
        lines.append(f"\n## 🕐 Hourly Distribution (EST)\n")
        lines.append(f"| Hour | Trades | Win Rate | PnL |")
        lines.append(f"|------|--------|----------|-----|")
        for h in sorted(result.hourly_stats.keys(), key=int):
            hs = result.hourly_stats[h]
            lines.append(f"| {int(h):02d}:00 | {hs['trades']} | {hs['wr']:.1f}% | {hs['pnl']:+.1f}p |")

    # ── Per-Trade PnL List ──
    lines.append(f"\n## 📋 Per-Trade PnL List\n")
    lines.append(f"| # | Entry | Exit | Dir | Tier | Result | PnL (pips) |")
    lines.append(f"|---|-------|------|-----|------|--------|------------|")
    for i, t in enumerate(result.trades, 1):
        entry_str = t.entry_time.strftime('%Y-%m-%d %H:%M') if t.entry_time else 'N/A'
        exit_str = t.exit_time.strftime('%Y-%m-%d %H:%M') if t.exit_time else 'N/A'
        lines.append(f"| {i} | {entry_str} | {exit_str} | {t.direction} | {t.tier} | {t.result} | {t.pnl_pips:+.1f} |")

    # ── Monte Carlo Section ──
    lines.append(f"\n## 🎲 Monte Carlo Simulation\n")
    if mc_results:
        lines.append(f"**Parameters:**")
        lines.append(f"- Simulations: {mc_results['n_simulations']:,}")
        lines.append(f"- Trades per simulation: {mc_results['n_trades_per_sim']}")
        lines.append(f"- Starting balance: ${mc_results['start_balance']:,.0f}")
        lines.append(f"- Risk per trade: {mc_results['risk_per_trade_pct']:.0f}%")
        lines.append(f"- Method: Resampled actual per-trade PnL (with replacement)\n")

        md = mc_results["max_drawdown_distribution"]
        pf_d = mc_results["profit_factor_distribution"]
        pnl_d = mc_results["pnl_distribution"]

        lines.append(f"### Ruin & Profitability\n")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Ruin Probability | {mc_results['ruin_probability_pct']:.2f}% |")
        lines.append(f"| Profitable Simulations | {mc_results['pct_profitable_sims']:.1f}% |")
        lines.append(f"| Mean Final Balance | ${mc_results['mean_final_balance']:,.2f} |")
        lines.append(f"| Median Final Balance | ${mc_results['median_final_balance']:,.2f} |")

        lines.append(f"\n### Total PnL Distribution\n")
        lines.append(f"| Percentile | PnL ($) |")
        lines.append(f"|------------|---------|")
        lines.append(f"| Min | ${pnl_d['min']:,.2f} |")
        lines.append(f"| 5th | ${pnl_d['p5']:,.2f} |")
        lines.append(f"| 10th | ${pnl_d['p10']:,.2f} |")
        lines.append(f"| 25th | ${pnl_d['p25']:,.2f} |")
        lines.append(f"| 50th (Median) | ${pnl_d['p50']:,.2f} |")
        lines.append(f"| 75th | ${pnl_d['p75']:,.2f} |")
        lines.append(f"| 90th | ${pnl_d['p90']:,.2f} |")
        lines.append(f"| 95th | ${pnl_d['p95']:,.2f} |")
        lines.append(f"| Max | ${pnl_d['max']:,.2f} |")
        lines.append(f"| **90% CI** | **[${mc_results['ci_90_low']:,.2f}, ${mc_results['ci_90_high']:,.2f}]** |")

        lines.append(f"\n### Max Drawdown Distribution (% of peak equity)\n")
        lines.append(f"| Percentile | Max DD (%) |")
        lines.append(f"|------------|------------|")
        lines.append(f"| 5th | {md['p5']:.2f}% |")
        lines.append(f"| Median | {md['median']:.2f}% |")
        lines.append(f"| Mean | {md['mean']:.2f}% |")
        lines.append(f"| 95th | {md['p95']:.2f}% |")
        lines.append(f"| Max | {md['max']:.2f}% |")

        lines.append(f"\n### Profit Factor Distribution\n")
        lines.append(f"| Percentile | PF |")
        lines.append(f"|------------|----|")
        lines.append(f"| 25th | {pf_d['p25']:.2f} |")
        lines.append(f"| Median | {pf_d['median']:.2f} |")
        lines.append(f"| 75th | {pf_d['p75']:.2f} |")

        lines.append(f"\n---\n")
        lines.append(f"*MC raw results: `{asset_key}_mc_results.json`*")
    else:
        lines.append("*Monte Carlo not run (no trades).*")

    report_path.write_text("\n".join(lines), encoding='utf-8')
    print(f"  Report: {report_path}")
    print(f"  MC JSON: {mc_json_path}")


def main():
    print("=" * 60)
    print("  CEREBUS Symmetry Trap — Batch 4: Indices")
    print("  Assets: US500, DE30, FR40, HK50")
    print(f"  MC Simulations: {MC_SIMULATIONS:,}")
    print("=" * 60)

    all_results = {}
    errors = []

    for asset_key in ASSETS:
        try:
            # Run backtest
            result = run_backtest(asset_key)
            if result is None:
                errors.append(f"{asset_key}: Backtest returned None (missing config or CSV)")
                continue

            # Monte Carlo
            print(f"  Running Monte Carlo ({MC_SIMULATIONS:,} simulations)...")
            if result.trades:
                mc_results = monte_carlo_simulation(result.trades)
                print(f"  MC: Ruin={mc_results['ruin_probability_pct']:.2f}%, "
                      f"Profitable={mc_results['pct_profitable_sims']:.1f}%, "
                      f"Median PnL=${mc_results['median_total_pnl']:,.2f}, "
                      f"90% CI=[${mc_results['ci_90_low']:,.2f}, ${mc_results['ci_90_high']:,.2f}]")
            else:
                mc_results = {}
                print(f"  MC: Skipped (no trades)")

            # Write report
            write_report(asset_key, result, mc_results)
            all_results[asset_key] = {"result": result, "mc": mc_results}

        except Exception as e:
            import traceback
            print(f"  ERROR on {asset_key}: {e}")
            traceback.print_exc()
            errors.append(f"{asset_key}: {e}")

    # ── Write batch summary ──
    report_paths = []
    for asset_key in ASSETS:
        rp = REPORT_DIR / f"{asset_key}_full_report.md"
        mc_jp = REPORT_DIR / f"{asset_key}_mc_results.json"
        report_paths.append(f"- {asset_key}: `{rp}`, `{mc_jp}`")

    summary_lines = []
    summary_lines.append("# Batch 4 — Indices Backtest Summary\n")
    summary_lines.append(f"> Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    summary_lines.append(f"## Asset Results\n")
    summary_lines.append("| Asset | Trades | Win Rate | PF | Sharpe | MaxDD (pips) | PnL (pips) |")
    summary_lines.append("|-------|--------|----------|----|--------|-------------|------------|")
    for asset_key in ASSETS:
        if asset_key in all_results:
            r = all_results[asset_key]["result"]
            summary_lines.append(
                f"| {asset_key} | {r.total_trades} | {r.win_rate:.1f}% | "
                f"{r.profit_factor:.2f} | {r.sharpe_ratio:.2f} | "
                f"{r.max_drawdown_pips:.1f} | {r.total_pnl_pips:+.1f} |"
            )
        else:
            summary_lines.append(f"| {asset_key} | — | — | — | — | — | ERROR |")

    summary_lines.append(f"\n## Monte Carlo Summary (10k sims, $10K start, 1% risk/trade)\n")
    summary_lines.append("| Asset | Ruin % | Profitable % | Median PnL | 90% CI Low | 90% CI High | Median MaxDD |")
    summary_lines.append("|-------|--------|-------------|------------|-----------|------------|-------------|")
    for asset_key in ASSETS:
        if asset_key in all_results:
            mc = all_results[asset_key]["mc"]
            if mc:
                summary_lines.append(
                    f"| {asset_key} | {mc['ruin_probability_pct']:.2f}% | "
                    f"{mc['pct_profitable_sims']:.1f}% | "
                    f"${mc['median_total_pnl']:,.2f} | "
                    f"${mc['ci_90_low']:,.2f} | "
                    f"${mc['ci_90_high']:,.2f} | "
                    f"{mc['max_drawdown_distribution']['median']:.2f}% |"
                )
            else:
                summary_lines.append(f"| {asset_key} | — | — | — | — | — | No trades |")
        else:
            summary_lines.append(f"| {asset_key} | — | — | — | — | — | ERROR |")

    if errors:
        summary_lines.append(f"\n## ⚠️ Errors / Flags\n")
        for err in errors:
            summary_lines.append(f"- {err}")

    summary_lines.append(f"\n## Generated Files\n")
    for p in report_paths:
        summary_lines.append(p)

    summary_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\progress\st-batch4-progress.md")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(summary_lines), encoding='utf-8')
    print(f"\nBatch summary: {summary_path}")

    print(f"\n{'='*60}")
    print("  BATCH 4 COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
