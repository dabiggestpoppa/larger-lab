"""
CEREBUS Symmetry Trap — Majors 6 Full Backtest + Monte Carlo
=============================================================
Runs backtest + MC for EURUSD, GBPUSD, USDCHF, USDJPY, AUDUSD, NZDUSD
Writes individual reports + group report.
"""

import os
import sys
import json
import math
import random
from datetime import datetime
from pathlib import Path

# ─── Path setup ────────────────────────────────────────────────────────────
ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
QUANTLAB_DIR = os.path.dirname(ENGINES_DIR)
sys.path.insert(0, ENGINES_DIR)
sys.path.insert(0, QUANTLAB_DIR)

import numpy as np

from symmetry_trap_backtest import (
    SymmetryTrapBacktest,
    load_m5_csv,
    compute_stats,
    BacktestResult,
    TradeRecord,
)
from configs.asset_configs import get_config

# ─── CONFIG ────────────────────────────────────────────────────────────────
SEED = 42
MC_ITERATIONS = 10_000
MAX_TRADES_PER_SIM = 500
INITIAL_BALANCE = 10000.0
RISK_PCT = 0.01  # 1% risk per trade

ASSETS = [
    ("EURUSD", "quant-lab/data/EURUSD_M5.csv"),
    ("GBPUSD", "quant-lab/data/GBPUSD_M5.csv"),
    ("USDCHF", "quant-lab/data/USDCHF_M5.csv"),
    ("USDJPY", "quant-lab/data/USDJPY_M5.csv"),
    ("AUDUSD", "quant-lab/data/AUDUSD_M5.csv"),
    ("NZDUSD", "quant-lab/data/NZDUSD_M5.csv"),
]

REPORT_DIR = "quant-lab/reports/top5_majors"


# ─── MONTE CARLO ───────────────────────────────────────────────────────────

def run_monte_carlo(trade_pnls, pip_value, iterations=MC_ITERATIONS,
                    initial_balance=INITIAL_BALANCE, risk_pct=RISK_PCT,
                    seed=SEED):
    """
    Run Monte Carlo simulation using actual per-trade PnL distribution.
    Returns dict with full MC results.
    """
    rng = np.random.default_rng(seed)
    n_trades = len(trade_pnls)
    trade_arr = np.array(trade_pnls)

    # Risk-based position sizing: 1% of account / (SL in pips * pip_value)
    # For MC we use fixed-fractional: risk_pct of current equity per trade
    # Simplified: fixed lot based on avg loss
    avg_loss = abs(np.mean(trade_arr[trade_arr < 0])) if np.any(trade_arr < 0) else 1.0
    lot_size = (initial_balance * risk_pct) / (avg_loss * pip_value) if avg_loss > 0 else 0.01
    pip_value_per_lot = pip_value * lot_size

    # Pre-generate random samples: (iterations, max_trades)
    max_trades = min(MAX_TRADES_PER_SIM, n_trades * 10)
    indices = rng.integers(0, n_trades, size=(iterations, max_trades))
    sampled_pips = trade_arr[indices]  # (iterations, max_trades)
    sampled_usd = sampled_pips * pip_value_per_lot

    # Cumulative equity curves
    equity_curves = np.cumsum(sampled_usd, axis=1)

    # Final PnL
    final_pnls = equity_curves[:, -1]

    # Max drawdown per iteration
    running_max = np.maximum.accumulate(equity_curves, axis=1)
    drawdowns = running_max - equity_curves
    max_drawdowns = np.max(drawdowns, axis=1)

    # Min equity (for ruin check)
    min_equity = np.min(equity_curves, axis=1)

    # Max consecutive losses
    is_loss = sampled_usd < 0
    max_consec_losses = np.zeros(iterations, dtype=int)
    for i in range(iterations):
        streak = 0
        ms = 0
        for j in range(max_trades):
            if is_loss[i, j]:
                streak += 1
                ms = max(ms, streak)
            else:
                streak = 0
        max_consec_losses[i] = ms

    # Median equity curve
    median_curve = np.median(equity_curves, axis=0)
    p5_curve = np.percentile(equity_curves, 5, axis=0)
    p95_curve = np.percentile(equity_curves, 95, axis=0)

    # Ruin: equity drops below -initial_balance (lose everything)
    ruin_threshold = -initial_balance
    pct_ruin = np.mean(min_equity <= ruin_threshold) * 100

    # 50% drawdown probability
    dd50_threshold = initial_balance * 0.5
    pct_50_dd = np.mean(max_drawdowns >= dd50_threshold) * 100

    # 90% CI for total PnL
    ci_90_low = np.percentile(final_pnls, 5)
    ci_90_high = np.percentile(final_pnls, 95)

    return {
        "iterations": iterations,
        "initial_balance": initial_balance,
        "risk_pct": risk_pct,
        "lot_size": round(lot_size, 4),
        "pip_value_per_lot": round(pip_value_per_lot, 4),
        "max_trades_per_sim": max_trades,
        "median_final_pnl": round(float(np.median(final_pnls)), 2),
        "mean_final_pnl": round(float(np.mean(final_pnls)), 2),
        "std_final_pnl": round(float(np.std(final_pnls)), 2),
        "pct_profitable": round(float(np.mean(final_pnls > 0)) * 100, 1),
        "final_pnl_5th": round(float(np.percentile(final_pnls, 5)), 2),
        "final_pnl_25th": round(float(np.percentile(final_pnls, 25)), 2),
        "final_pnl_50th": round(float(np.percentile(final_pnls, 50)), 2),
        "final_pnl_75th": round(float(np.percentile(final_pnls, 75)), 2),
        "final_pnl_95th": round(float(np.percentile(final_pnls, 95)), 2),
        "ci_90_low": round(float(ci_90_low), 2),
        "ci_90_high": round(float(ci_90_high), 2),
        "median_max_dd": round(float(np.median(max_drawdowns)), 2),
        "mean_max_dd": round(float(np.mean(max_drawdowns)), 2),
        "max_dd_95th": round(float(np.percentile(max_drawdowns, 95)), 2),
        "worst_dd": round(float(np.max(max_drawdowns)), 2),
        "median_max_consec_losses": round(float(np.median(max_consec_losses)), 1),
        "worst_consec_losses": int(np.max(max_consec_losses)),
        "pct_ruin": round(float(pct_ruin), 2),
        "pct_50pct_drawdown": round(float(pct_50_dd), 2),
        "median_equity_curve": [round(float(x), 2) for x in median_curve[::max(1, len(median_curve)//50)]],
        "p5_equity_curve": [round(float(x), 2) for x in p5_curve[::max(1, len(p5_curve)//50)]],
        "p95_equity_curve": [round(float(x), 2) for x in p95_curve[::max(1, len(p95_curve)//50)]],
    }


# ─── REPORT GENERATOR ──────────────────────────────────────────────────────

def generate_full_report(asset_key, result, mc_results, trade_pnls, config):
    """Generate comprehensive markdown report for one asset."""
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append(f"# CEREBUS Symmetry Trap — Full Backtest Report: {asset_key}")
    lines.append(f"")
    lines.append(f"> **Generated:** {now}  ")
    lines.append(f"> **Engine:** Symmetry Trap (Model B, 4-state FSM)  ")
    lines.append(f"> **Data:** {result.data_bars:,} M5 bars | {result.data_days} trading days  ")
    lines.append(f"> **Config:** AU={config['tiers']['T1']['au']}p / Trigger={config['tiers']['T1']['trigger']}p (T1)  ")
    lines.append(f"")

    # ── Executive Summary ──
    lines.append(f"## Executive Summary")
    lines.append(f"")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Trades | {result.total_trades} |")
    lines.append(f"| Wins / Losses | {result.wins} / {result.losses} |")
    lines.append(f"| Win Rate | {result.win_rate:.1f}% |")
    lines.append(f"| Total PnL | {result.total_pnl_pips:+.1f} pips |")
    lines.append(f"| Gross Profit | {result.gross_profit:+.1f} pips |")
    lines.append(f"| Gross Loss | {result.gross_loss:+.1f} pips |")
    lines.append(f"| Profit Factor | {result.profit_factor:.2f} |")
    lines.append(f"| Expectancy | {result.expectancy_pips:+.2f} pips/trade |")
    lines.append(f"| Avg Win | {result.avg_win_pips:+.2f} pips |")
    lines.append(f"| Avg Loss | {result.avg_loss_pips:+.2f} pips |")
    lines.append(f"| Sharpe Ratio | {result.sharpe_ratio:.2f} |")
    lines.append(f"| Max Drawdown | {result.max_drawdown_pips:.1f} pips ({result.max_drawdown_pct:.2f}%) |")
    lines.append(f"| Kelly Criterion | {result.kelly_criterion*100:.1f}% |")
    lines.append(f"| Max Consec Wins | {result.max_consec_wins} |")
    lines.append(f"| Max Consec Losses | {result.max_consec_losses} |")
    lines.append(f"| Data Period | {result.data_days} trading days |")
    lines.append(f"")

    # ── Direction Breakdown ──
    lines.append(f"## Direction Breakdown")
    lines.append(f"")
    lines.append(f"| Direction | Trades | Win Rate | PnL |")
    lines.append(f"|-----------|--------|----------|------|")
    lines.append(f"| LONG | {result.long_trades} | {result.long_wr:.1f}% | {result.long_pnl:+.1f} pips |")
    lines.append(f"| SHORT | {result.short_trades} | {result.short_wr:.1f}% | {result.short_pnl:+.1f} pips |")
    lines.append(f"")

    # ── Tier Breakdown ──
    lines.append(f"## Tier Breakdown (T1 / T2 / T3)")
    lines.append(f"")
    lines.append(f"| Tier | Trades | Win Rate | PnL | Avg PnL |")
    lines.append(f"|------|--------|----------|------|---------|")
    for tier in ["T1", "T2", "T3"]:
        if tier in result.tier_stats:
            ts = result.tier_stats[tier]
            avg = ts['pnl'] / ts['trades'] if ts['trades'] > 0 else 0
            lines.append(f"| {tier} | {ts['trades']} | {ts['wr']:.1f}% | {ts['pnl']:+.1f}p | {avg:+.2f}p |")
        else:
            lines.append(f"| {tier} | — | — | — | — |")
    lines.append(f"")
    lines.append(f"*T1 AR ≤ {config['tiers']['T1']['ar_max']}p | T2 AR ≤ {config['tiers']['T2']['ar_max']}p | T3 AR ≤ {config['tiers']['T3']['ar_max']}p*")
    lines.append(f"")

    # ── Loop Distribution ──
    lines.append(f"## Loop Distribution")
    lines.append(f"")
    if result.loop_stats:
        lines.append(f"| Loop | Trades | Win Rate | PnL |")
        lines.append(f"|------|--------|----------|------|")
        for lk in sorted(result.loop_stats.keys(), key=lambda x: int(x) if x.isdigit() else 99):
            ls = result.loop_stats[lk]
            lines.append(f"| {lk} | {ls['trades']} | {ls['wr']:.1f}% | {ls['pnl']:+.1f}p |")
    else:
        lines.append(f"*No loop data available.*")
    lines.append(f"")

    # ── Hourly Distribution ──
    lines.append(f"## Hourly Distribution (EST)")
    lines.append(f"")
    lines.append(f"| Hour (EST) | Trades | Win Rate | PnL |")
    lines.append(f"|------------|--------|----------|------|")
    for h in range(2, 13):
        hs = result.hourly_stats.get(str(h))
        if hs:
            lines.append(f"| {h:02d}:00 | {hs['trades']} | {hs['wr']:.1f}% | {hs['pnl']:+.1f}p |")
        else:
            lines.append(f"| {h:02d}:00 | — | — | — |")
    lines.append(f"")
    lines.append(f"*12PM cutoff by design. Hours 13+ have no entries.*")
    lines.append(f"")

    # ── Per-Trade PnL Distribution ──
    lines.append(f"## Per-Trade PnL Distribution")
    lines.append(f"")
    if trade_pnls:
        arr = np.array(trade_pnls)
        winners = arr[arr > 0]
        losers = arr[arr < 0]
        evens = arr[arr == 0]

        lines.append(f"| Bucket | Count | Pct |")
        lines.append(f"|--------|-------|-----|")
        lines.append(f"| +15p+ | {np.sum(arr >= 15)} | {np.sum(arr >= 15)/len(arr)*100:.1f}% |")
        lines.append(f"| +10p to +15p | {np.sum((arr >= 10) & (arr < 15))} | {np.sum((arr >= 10) & (arr < 15))/len(arr)*100:.1f}% |")
        lines.append(f"| +5p to +10p | {np.sum((arr >= 5) & (arr < 10))} | {np.sum((arr >= 5) & (arr < 10))/len(arr)*100:.1f}% |")
        lines.append(f"| +1p to +5p | {np.sum((arr >= 1) & (arr < 5))} | {np.sum((arr >= 1) & (arr < 5))/len(arr)*100:.1f}% |")
        lines.append(f"| 0p to +1p | {np.sum((arr >= 0) & (arr < 1))} | {np.sum((arr >= 0) & (arr < 1))/len(arr)*100:.1f}% |")
        lines.append(f"| 0p (scratch) | {len(evens)} | {len(evens)/len(arr)*100:.1f}% |")
        lines.append(f"| -1p to 0p | {np.sum((arr < 0) & (arr >= -1))} | {np.sum((arr < 0) & (arr >= -1))/len(arr)*100:.1f}% |")
        lines.append(f"| -5p to -1p | {np.sum((arr < -1) & (arr >= -5))} | {np.sum((arr < -1) & (arr >= -5))/len(arr)*100:.1f}% |")
        lines.append(f"| -10p to -5p | {np.sum((arr < -5) & (arr >= -10))} | {np.sum((arr < -5) & (arr >= -10))/len(arr)*100:.1f}% |")
        lines.append(f"| -10p or worse | {np.sum(arr < -10)} | {np.sum(arr < -10)/len(arr)*100:.1f}% |")
        lines.append(f"")
        lines.append(f"**Median PnL:** {float(np.median(arr)):.1f}p | **Mean PnL:** {float(np.mean(arr)):.2f}p | **StdDev:** {float(np.std(arr)):.2f}p")
    lines.append(f"")

    # ── Monte Carlo Section ──
    lines.append(f"## Monte Carlo Simulation ({mc_results['iterations']:,} iterations)")
    lines.append(f"")
    lines.append(f"**Parameters:**")
    lines.append(f"- Initial Balance: ${mc_results['initial_balance']:,.0f}")
    lines.append(f"- Risk per Trade: {mc_results['risk_pct']*100:.0f}% of account")
    lines.append(f"- Lot Size (computed): {mc_results['lot_size']:.4f}")
    lines.append(f"- Max Trades/Sim: {mc_results['max_trades_per_sim']}")
    lines.append(f"- Seed: {SEED}")
    lines.append(f"")

    lines.append(f"### MC — Final PnL Distribution")
    lines.append(f"")
    lines.append(f"| Percentile | Final PnL ($) |")
    lines.append(f"|------------|---------------|")
    lines.append(f"| 5th | ${mc_results['final_pnl_5th']:+,.2f} |")
    lines.append(f"| 25th | ${mc_results['final_pnl_25th']:+,.2f} |")
    lines.append(f"| 50th (Median) | ${mc_results['final_pnl_50th']:+,.2f} |")
    lines.append(f"| 75th | ${mc_results['final_pnl_75th']:+,.2f} |")
    lines.append(f"| 95th | ${mc_results['final_pnl_95th']:+,.2f} |")
    lines.append(f"| Mean | ${mc_results['mean_final_pnl']:+,.2f} |")
    lines.append(f"| Std Dev | ${mc_results['std_final_pnl']:,.2f} |")
    lines.append(f"| Profitable Simulations | {mc_results['pct_profitable']:.1f}% |")
    lines.append(f"")

    lines.append(f"### MC — 90% Confidence Interval for Total PnL")
    lines.append(f"")
    lines.append(f"**${mc_results['ci_90_low']:+,.2f} to ${mc_results['ci_90_high']:+,.2f}** (90% of simulations fall in this range)")
    lines.append(f"")

    lines.append(f"### MC — Drawdown Distribution")
    lines.append(f"")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Median Max DD | ${mc_results['median_max_dd']:,.2f} |")
    lines.append(f"| Mean Max DD | ${mc_results['mean_max_dd']:,.2f} |")
    lines.append(f"| 95th Percentile DD | ${mc_results['max_dd_95th']:,.2f} |")
    lines.append(f"| Worst DD | ${mc_results['worst_dd']:,.2f} |")
    lines.append(f"| P(50% Drawdown) | {mc_results['pct_50pct_drawdown']:.2f}% |")
    lines.append(f"| P(Ruin: lose all) | {mc_results['pct_ruin']:.2f}% |")
    lines.append(f"")

    lines.append(f"### MC — Consecutive Losses")
    lines.append(f"")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Median Max Consec Losses | {mc_results['median_max_consec_losses']:.0f} |")
    lines.append(f"| Worst Consec Losses | {mc_results['worst_consec_losses']} |")
    lines.append(f"")

    # ── Key Observations ──
    lines.append(f"## Key Observations")
    lines.append(f"")
    obs = []
    if result.win_rate >= 85:
        obs.append(f"- **Exceptional win rate:** {result.win_rate:.1f}% — structural edge confirmed")
    elif result.win_rate >= 70:
        obs.append(f"- **Strong win rate:** {result.win_rate:.1f}%")
    else:
        obs.append(f"- **Moderate win rate:** {result.win_rate:.1f}%")

    if result.profit_factor >= 3:
        obs.append(f"- **Outstanding profit factor:** {result.profit_factor:.2f} — gross profit vastly exceeds gross loss")
    elif result.profit_factor >= 1.5:
        obs.append(f"- **Solid profit factor:** {result.profit_factor:.2f}")
    else:
        obs.append(f"- **Weak profit factor:** {result.profit_factor:.2f} — needs improvement")

    if result.sharpe_ratio >= 3:
        obs.append(f"- **Excellent Sharpe:** {result.sharpe_ratio:.2f} — risk-adjusted returns are exceptional")
    elif result.sharpe_ratio >= 1.5:
        obs.append(f"- **Good Sharpe:** {result.sharpe_ratio:.2f}")

    if result.max_drawdown_pct <= 5:
        obs.append(f"- **Low drawdown:** {result.max_drawdown_pct:.2f}% — well-controlled risk")
    elif result.max_drawdown_pct <= 10:
        obs.append(f"- **Moderate drawdown:** {result.max_drawdown_pct:.2f}%")
    else:
        obs.append(f"- **High drawdown:** {result.max_drawdown_pct:.2f}% — risk management concern")

    if abs(result.long_pnl - result.short_pnl) / max(abs(result.total_pnl_pips), 1) < 0.3:
        obs.append(f"- **Balanced directionality:** Long {result.long_pnl:+.1f}p / Short {result.short_pnl:+.1f}p — no directional bias")
    else:
        better = "Long" if result.long_pnl > result.short_pnl else "Short"
        obs.append(f"- **Directional bias:** {better} performs better (Long {result.long_pnl:+.1f}p vs Short {result.short_pnl:+.1f}p)")

    if mc_results['pct_ruin'] < 1:
        obs.append(f"- **Near-zero ruin probability:** {mc_results['pct_ruin']:.2f}% — very safe at 1% risk")
    elif mc_results['pct_ruin'] < 5:
        obs.append(f"- **Low ruin probability:** {mc_results['pct_ruin']:.2f}%")
    else:
        obs.append(f"- **Elevated ruin probability:** {mc_results['pct_ruin']:.2f}% — consider reducing risk")

    best_tier = max(result.tier_stats.items(), key=lambda x: x[1]['pnl']) if result.tier_stats else None
    if best_tier:
        obs.append(f"- **Best tier:** {best_tier[0]} with {best_tier[1]['pnl']:+.1f}p ({best_tier[1]['wr']:.1f}% WR)")

    for o in obs:
        lines.append(o)
    lines.append(f"")

    # ── Flags ──
    lines.append(f"## Flags")
    lines.append(f"")
    flags = []
    if result.win_rate < 60:
        flags.append(f"- ⚠️ **LOW WIN RATE:** Below 60% — edge may be weak")
    if result.profit_factor < 1.2:
        flags.append(f"- ⚠️ **LOW PROFIT FACTOR:** Below 1.2 — not enough margin of safety")
    if result.max_drawdown_pct > 15:
        flags.append(f"- 🔴 **HIGH DRAWDOWN:** Over 15% — significant risk")
    if result.max_consec_losses >= 10:
        flags.append(f"- ⚠️ **LONG LOSS STREAK:** {result.max_consec_losses} consecutive losses observed")
    if mc_results['pct_ruin'] > 5:
        flags.append(f"- 🔴 **RUIN RISK:** {mc_results['pct_ruin']:.1f}% probability of losing entire account")
    if result.total_trades < 50:
        flags.append(f"- ⚠️ **SMALL SAMPLE:** Only {result.total_trades} trades — results may not be statistically significant")

    if not flags:
        lines.append(f"*No critical flags. Strategy passes basic validation.*")
    else:
        for f in flags:
            lines.append(f)
    lines.append(f"")

    lines.append(f"---")
    lines.append(f"*Report generated by CEREBUS Symmetry Trap Backtest Engine v4.0*")
    lines.append(f"*Monte Carlo: {mc_results['iterations']:,} iterations | Seed: {SEED}*")

    return "\n".join(lines)


# ─── MAIN ──────────────────────────────────────────────────────────────────

def main():
    os.makedirs(REPORT_DIR, exist_ok=True)

    all_results = {}
    all_trade_pnls = {}
    all_configs = {}

    for asset_key, csv_path in ASSETS:
        print(f"\n{'='*60}")
        print(f"  Running: {asset_key}")
        print(f"{'='*60}")

        config = get_config(asset_key)
        pip_value = config["pip_value"]
        symbol = asset_key  # Use key as symbol name

        print(f"  Config: pip_value={pip_value}, T1 AU={config['tiers']['T1']['au']}p")
        print(f"  Loading CSV: {csv_path}")

        bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=symbol, config=config)
        result = bt.run_from_csv(csv_path)
        result.symbol = asset_key  # Normalize symbol to key

        print(f"  Trades: {result.total_trades} | WR: {result.win_rate:.1f}% | PnL: {result.total_pnl_pips:+.1f}p | PF: {result.profit_factor:.2f}")

        # Extract per-trade PnL list
        trade_pnls = [t.pnl_pips for t in result.trades] if result.trades else []
        all_trade_pnls[asset_key] = trade_pnls
        all_results[asset_key] = result
        all_configs[asset_key] = config

        # Monte Carlo
        if trade_pnls:
            print(f"  Running Monte Carlo ({MC_ITERATIONS:,} iterations)...")
            mc = run_monte_carlo(trade_pnls, pip_value)
            print(f"  MC Median PnL: ${mc['median_final_pnl']:+,.2f} | Ruin: {mc['pct_ruin']:.2f}%")
        else:
            mc = {"error": "No trades to simulate", "iterations": 0}

        # Write individual report
        report_md = generate_full_report(asset_key, result, mc, trade_pnls, config)
        report_path = os.path.join(REPORT_DIR, f"{asset_key}_full_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"  Report: {report_path}")

        # Write MC results JSON
        mc_path = os.path.join(REPORT_DIR, f"{asset_key}_mc_results.json")
        with open(mc_path, "w", encoding="utf-8") as f:
            json.dump(mc, f, indent=2, default=str)
        print(f"  MC JSON: {mc_path}")

    # ── Group Report ──
    print(f"\n{'='*60}")
    print(f"  Generating Group Report")
    print(f"{'='*60}")

    group_md = generate_group_report(all_results, all_trade_pnls, all_configs)
    group_path = os.path.join(REPORT_DIR, "majors6_group_report.md")
    with open(group_path, "w", encoding="utf-8") as f:
        f.write(group_md)
    print(f"  Group report: {group_path}")

    # ── Progress file ──
    progress_md = generate_progress_file(all_results)
    progress_path = "progress/st-phase5-majors-progress.md"
    os.makedirs("progress", exist_ok=True)
    with open(progress_path, "w", encoding="utf-8") as f:
        f.write(progress_md)
    print(f"  Progress: {progress_path}")

    print(f"\n✅ All {len(ASSETS)} assets complete.")


def generate_group_report(all_results, all_trade_pnls, all_configs):
    """Generate combined Majors 6 group report."""
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append(f"# CEREBUS Symmetry Trap — Majors 6 Group Report")
    lines.append(f"")
    lines.append(f"> **Generated:** {now}  ")
    lines.append(f"> **Assets:** EURUSD, GBPUSD, USDCHF, USDJPY, AUDUSD, NZDUSD  ")
    lines.append(f"> **Engine:** Symmetry Trap (Model B, 4-state FSM)  ")
    lines.append(f"")

    # ── Per-Asset Comparison Table ──
    lines.append(f"## Per-Asset Comparison")
    lines.append(f"")
    lines.append(f"| Asset | Trades | WR | PnL (pips) | PF | Sharpe | MaxDD (pips) | Long PnL | Short PnL |")
    lines.append(f"|-------|--------|-----|------------|-----|--------|-------------|----------|-----------|")

    total_trades = 0
    total_wins = 0
    total_losses_count = 0
    total_pnl = 0.0
    total_gross_profit = 0.0
    total_gross_loss = 0.0
    all_pnls_combined = []

    for asset_key, _ in ASSETS:
        r = all_results[asset_key]
        total_trades += r.total_trades
        total_wins += r.wins
        total_losses_count += r.losses
        total_pnl += r.total_pnl_pips
        total_gross_profit += r.gross_profit
        total_gross_loss += r.gross_loss
        all_pnls_combined.extend(all_trade_pnls[asset_key])

        lines.append(
            f"| {asset_key} | {r.total_trades} | {r.win_rate:.1f}% | "
            f"{r.total_pnl_pips:+.1f} | {r.profit_factor:.2f} | "
            f"{r.sharpe_ratio:.2f} | {r.max_drawdown_pips:.1f} | "
            f"{r.long_pnl:+.1f} | {r.short_pnl:+.1f} |"
        )

    # Aggregate stats
    agg_wr = total_wins / total_trades * 100 if total_trades > 0 else 0
    agg_pf = total_gross_profit / total_gross_loss if total_gross_loss > 0 else float("inf")

    lines.append(f"|")
    lines.append(
        f"| **TOTAL** | **{total_trades}** | **{agg_wr:.1f}%** | "
        f"**{total_pnl:+.1f}** | **{agg_pf:.2f}** | — | — | — | — |"
    )
    lines.append(f"")

    # ── Tier Summary Across All Majors ──
    lines.append(f"## Tier Summary (All Majors Combined)")
    lines.append(f"")
    lines.append(f"| Tier | Trades | Win Rate | Total PnL |")
    lines.append(f"|------|--------|----------|-----------|")
    for tier in ["T1", "T2", "T3"]:
        tier_trades = sum(r.tier_stats[tier]['trades'] for r in all_results.values() if tier in r.tier_stats)
        tier_pnl = sum(r.tier_stats[tier]['pnl'] for r in all_results.values() if tier in r.tier_stats)
        tier_wins = sum(r.tier_stats[tier]['trades'] * r.tier_stats[tier]['wr'] / 100 for r in all_results.values() if tier in r.tier_stats)
        tier_wr = tier_wins / tier_trades * 100 if tier_trades > 0 else 0
        lines.append(f"| {tier} | {tier_trades} | {tier_wr:.1f}% | {tier_pnl:+.1f}p |")
    lines.append(f"")

    # ── Combined Monte Carlo ──
    lines.append(f"## Combined Monte Carlo Simulation")
    lines.append(f"")
    lines.append(f"**Method:** Pool all {len(all_pnls_combined)} trades from all 6 majors, run {MC_ITERATIONS:,} iterations.")
    lines.append(f"")

    if all_pnls_combined:
        # Use average pip_value weighted by trade count
        # For combined MC, we normalize to pips then convert
        # Use EURUSD pip_value as reference (0.0001 for most, 0.01 for JPY)
        # Better: run MC on normalized pips, then report in pips
        combined_mc = run_monte_carlo(all_pnls_combined, pip_value=0.0001)

        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Iterations | {combined_mc['iterations']:,} |")
        lines.append(f"| Total Trades Pooled | {len(all_pnls_combined)} |")
        lines.append(f"| Median Final PnL | ${combined_mc['median_final_pnl']:+,.2f} |")
        lines.append(f"| Mean Final PnL | ${combined_mc['mean_final_pnl']:+,.2f} |")
        lines.append(f"| 90% CI Low | ${combined_mc['ci_90_low']:+,.2f} |")
        lines.append(f"| 90% CI High | ${combined_mc['ci_90_high']:+,.2f} |")
        lines.append(f"| Profitable Simulations | {combined_mc['pct_profitable']:.1f}% |")
        lines.append(f"| Median Max DD | ${combined_mc['median_max_dd']:,.2f} |")
        lines.append(f"| Worst DD | ${combined_mc['worst_dd']:,.2f} |")
        lines.append(f"| P(Ruin) | {combined_mc['pct_ruin']:.2f}% |")
        lines.append(f"| P(50% DD) | {combined_mc['pct_50pct_drawdown']:.2f}% |")
        lines.append(f"| Worst Consec Losses | {combined_mc['worst_consec_losses']} |")
        lines.append(f"")
    else:
        lines.append(f"*No trades available for combined MC.*")
        lines.append(f"")

    # ── Hourly Heatmap (Combined) ──
    lines.append(f"## Combined Hourly Distribution (All Majors)")
    lines.append(f"")
    lines.append(f"| Hour (EST) | Total Trades | Avg WR | Total PnL |")
    lines.append(f"|------------|-------------|--------|-----------|")
    for h in range(2, 13):
        h_trades = sum(r.hourly_stats.get(str(h), {}).get('trades', 0) for r in all_results.values())
        h_pnl = sum(r.hourly_stats.get(str(h), {}).get('pnl', 0) for r in all_results.values())
        h_wins = sum(
            r.hourly_stats.get(str(h), {}).get('trades', 0) * r.hourly_stats.get(str(h), {}).get('wr', 0) / 100
            for r in all_results.values() if str(h) in r.hourly_stats
        )
        h_wr = h_wins / h_trades * 100 if h_trades > 0 else 0
        if h_trades > 0:
            lines.append(f"| {h:02d}:00 | {h_trades} | {h_wr:.1f}% | {h_pnl:+.1f}p |")
    lines.append(f"")

    # ── Key Takeaways ──
    lines.append(f"## Key Takeaways")
    lines.append(f"")

    best_asset = max(all_results.items(), key=lambda x: x[1].total_pnl_pips)
    worst_asset = min(all_results.items(), key=lambda x: x[1].total_pnl_pips)
    best_wr_asset = max(all_results.items(), key=lambda x: x[1].win_rate)

    lines.append(f"- **Best PnL:** {best_asset[0]} with {best_asset[1].total_pnl_pips:+.1f} pips")
    lines.append(f"- **Highest WR:** {best_wr_asset[0]} with {best_wr_asset[1].win_rate:.1f}%")
    lines.append(f"- **Lowest PnL:** {worst_asset[0]} with {worst_asset[1].total_pnl_pips:+.1f} pips")
    lines.append(f"- **Total trades across all majors:** {total_trades}")
    lines.append(f"- **Aggregate WR:** {agg_wr:.1f}%")
    lines.append(f"- **Aggregate PF:** {agg_pf:.2f}")
    lines.append(f"- **Total PnL:** {total_pnl:+.1f} pips")
    lines.append(f"")

    lines.append(f"---")
    lines.append(f"*Majors 6 Group Report — CEREBUS Symmetry Trap v4.0*")

    return "\n".join(lines)


def generate_progress_file(all_results):
    """Generate progress file for subagent tracking."""
    lines = []
    lines.append(f"# ST Phase 5 — Majors 6 Backtest Progress")
    lines.append(f"")
    lines.append(f"> **Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"> **Status:** COMPLETE  ")
    lines.append(f"")

    lines.append(f"## Results Summary")
    lines.append(f"")
    lines.append(f"| Asset | Trades | WR | PnL | PF | Sharpe | Reports |")
    lines.append(f"|-------|--------|-----|------|-----|--------|---------|")

    for asset_key, _ in ASSETS:
        r = all_results[asset_key]
        report_path = f"quant-lab/reports/top5_majors/{asset_key}_full_report.md"
        mc_path = f"quant-lab/reports/top5_majors/{asset_key}_mc_results.json"
        exists = "✅" if os.path.exists(report_path) else "❌"
        lines.append(
            f"| {asset_key} | {r.total_trades} | {r.win_rate:.1f}% | "
            f"{r.total_pnl_pips:+.1f}p | {r.profit_factor:.2f} | "
            f"{r.sharpe_ratio:.2f} | {exists} |"
        )

    lines.append(f"")
    lines.append(f"## Output Files")
    lines.append(f"")
    for asset_key, _ in ASSETS:
        lines.append(f"- `{asset_key}_full_report.md` — Full backtest + MC report")
        lines.append(f"- `{asset_key}_mc_results.json` — Raw MC simulation data")
    lines.append(f"- `majors6_group_report.md` — Combined group analysis")
    lines.append(f"")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
