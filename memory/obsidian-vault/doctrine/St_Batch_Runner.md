# St Batch Runner

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine #python #engines

```python
"""
CEREBUS FX v4.0 — Symmetry Trap Batch Runner + Monte Carlo
============================================================
Runs Symmetry Trap backtest + full Monte Carlo for multiple assets.
Writes per-asset markdown reports + JSON MC results.

Usage: python engines/st_batch_runner.py
"""

from __future__ import annotations
import json
import math
import os
import sys
import random
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev

import numpy as np

# ─── Path setup ────────────────────────────────────────────────────────────
ENGINES_DIR = os.path.dirname(os.path.abspath(__file__))
QUANT_LAB = os.path.dirname(ENGINES_DIR)
sys.path.insert(0, ENGINES_DIR)
sys.path.insert(0, os.path.join(QUANT_LAB, "configs"))

from symmetry_trap_backtest import (
    SymmetryTrapBacktest,
    BacktestResult,
    TradeRecord,
    compute_stats,
    load_m5_csv,
)
from asset_configs import ASSET_CONFIGS

# ─── MC CONFIG ──────────────────────────────────────────────────────────────
MC_ITERATIONS = 10_000
MC_MAX_TRADES = 500
MC_SEED = 42
INITIAL_BALANCE = 10000.0
RISK_PER_TRADE_PCT = 0.01  # 1%

ASSETS = [
    {"key": "EURUSD", "csv": os.path.join(QUANT_LAB, "data", "EURUSD_M5.csv")},
    {"key": "GBPUSD", "csv": os.path.join(QUANT_LAB, "data", "GBPUSD_M5.csv")},
    {"key": "USDCHF", "csv": os.path.join(QUANT_LAB, "data", "USDCHF_M5.csv")},
]

REPORTS_DIR = os.path.join(QUANT_LAB, "reports", "per-asset")


# ─── MONTE CARLO ────────────────────────────────────────────────────────────

def run_monte_carlo(trade_pnls: list, config: dict,
                    initial_balance: float = INITIAL_BALANCE,
                    risk_pct: float = RISK_PER_TRADE_PCT,
                    n_iterations: int = MC_ITERATIONS,
                    max_trades: int = MC_MAX_TRADES,
                    seed: int = MC_SEED) -> dict:
    """
    Run Monte Carlo simulation using ACTUAL per-trade PnL distribution.
    Risk: 1% of starting $10,000 = $100 per trade.
    Position sizing: risk_amount / (sl_pips * pip_value_per_lot)
    Since SL varies per trade, we simplify: fixed fractional at 1% of current equity.
    """
    if not trade_pnls:
        return {"error": "no trades to simulate"}

    pip_size = config["pip_value"]
    pip_value_per_001 = 0.10  # approx $0.10 per pip for 0.01 lot on standard forex

    rng = np.random.default_rng(seed)
    n_trades = len(trade_pnls)
    trade_arr = np.array(trade_pnls)  # in pips

    # Pre-generate all random samples: (n_iterations, max_trades)
    indices = rng.integers(0, n_trades, size=(n_iterations, max_trades))
    sampled_pips = trade_arr[indices]  # (n_iterations, max_trades) in pips

    # For position sizing, we use a simplified approach:
    # risk 1% of equity per trade, with position size based on avg loss in pips
    avg_loss_pips = abs(float(np.mean(trade_arr[trade_arr < 0]))) if np.any(trade_arr < 0) else 1.0
    # $ value of avg loss per 0.01 lot
    avg_loss_dollar_per_001 = avg_loss_pips * pip_value_per_001

    # Simulate equity curves in USD
    equity_curves = np.zeros((n_iterations, max_trades + 1))
    equity_curves[:, 0] = initial_balance

    for j in range(max_trades):
        # Current equity
        current_eq = equity_curves[:, j]
        # Risk 1% of current equity
        risk_usd = current_eq * risk_pct
        # Convert to lot size based on avg loss
        lot_sizes = np.clip(risk_usd / (avg_loss_pips * pip_value_per_001 * 100), 0.01, 10.0)
        # If avg loss = 5 pips, pip_value = $0.10 per 0.01 lot, then
        # avg loss per 0.01 lot = 5 * 0.10 = $0.50
        # risk $100 / $0.50 = 200 units of 0.01 = 2.00 lots
        # More generally: USD PnL = pips * lot_size * pip_value_per_001 * 100
        usd_pnl = sampled_pips[:, j] * lot_sizes * pip_size / pip_size
        # Actually for standard forex (pip_size=0.0001):
        # pip_value per lot = 0.0001 * 100000 = $10 (for 1.0 lot) or $1 (for 0.1 lot) or $0.10 (for 0.01 lot)
        # But pip_value_per_001 above is already $0.10
        # So: USD = pips * lot_size_in_lots * pip_value_per_lot
        # pip_value_per_lot = pip_size * 100000 = 0.0001 * 100000 = $10 for 1 lot
        # pip_value per 0.01 lot = $0.10 (matches our assumption)
        lot_in_lots = lot_sizes * 0.01  # convert "units of 0.01" to lots
        pip_val_per_lot = pip_size * 100000  # $ per pip per 1.0 lot
        usd_pnl = sampled_pips[:, j] * lot_in_lots * pip_val_per_lot
        next_eq = current_eq + usd_pnl
        # Clamp: can't go below 0
        equity_curves[:, j + 1] = np.maximum(next_eq, 0.0)

    # Final equity
    final_equity = equity_curves[:, -1]
    final_pnl = final_equity - initial_balance

    # Max drawdown per iteration
    running_max = np.maximum.accumulate(equity_curves, axis=1)
    drawdowns = running_max - equity_curves
    max_drawdowns = np.max(drawdowns, axis=1)
    max_dd_pct = max_drawdowns / initial_balance * 100

    # Ruin: equity drops below initial_balance * 0.5 (50% drawdown = ruin)
    ruin_threshold = initial_balance * 0.5
    min_equity = np.min(equity_curves, axis=1)
    pct_ruin = float(np.mean(min_equity <= ruin_threshold)) * 100

    # Profit factor per iteration
    pnl_per_iter = sampled_pips * 0.01 * pip_size * 100000  # rough USD
    # Simplified: use pips directly for PF
    sampled_usd_simple = sampled_pips * np.mean(np.clip(
        (INITIAL_BALANCE * risk_pct) / (avg_loss_pips * pip_size * 100000 / 100), 0.01, 10.0
    )) * 0.01 * pip_size * 100000

    # Compute equity curve percentiles (5th, 25th, 50th, 75th, 95th) across all iterations
    eq_p5 = np.percentile(equity_curves, 5, axis=0)
    eq_p25 = np.percentile(equity_curves, 25, axis=0)
    eq_p50 = np.percentile(equity_curves, 50, axis=0)
    eq_p75 = np.percentile(equity_curves, 75, axis=0)
    eq_p95 = np.percentile(equity_curves, 95, axis=0)

    # Profit factor per iteration
    profit_factors = []
    for i in range(n_iterations):
        trade_usd = sampled_pips[i] * 0.01 * pip_size * 100000  # same lot size for simplicity
        gp = float(np.sum(trade_usd[trade_usd > 0]))
        gl = float(abs(np.sum(trade_usd[trade_usd <= 0])))
        if gl > 0:
            profit_factors.append(gp / gl)
        else:
            profit_factors.append(float('inf'))
    profit_factors = np.array(profit_factors)
    # Cap inf for reporting
    pf_capped = np.clip(profit_factors, 0, 100)

    return {
        "n_iterations": n_iterations,
        "initial_balance": initial_balance,
        "risk_per_trade_pct": risk_pct * 100,
        "avg_loss_pips": round(avg_loss_pips, 2),

        # Final PnL distribution (USD)
        "median_final_pnl_usd": round(float(np.median(final_pnl)), 2),
        "mean_final_pnl_usd": round(float(np.mean(final_pnl)), 2),
        "std_final_pnl_usd": round(float(np.std(final_pnl)), 2),
        "pct_profitable": round(float(np.mean(final_pnl > 0)) * 100, 1),
        "pnl_5th_pctile": round(float(np.percentile(final_pnl, 5)), 2),
        "pnl_25th_pctile": round(float(np.percentile(final_pnl, 25)), 2),
        "pnl_50th_pctile": round(float(np.percentile(final_pnl, 50)), 2),
        "pnl_75th_pctile": round(float(np.percentile(final_pnl, 75)), 2),
        "pnl_90th_pctile": round(float(np.percentile(final_pnl, 90)), 2),
        "pnl_95th_pctile": round(float(np.percentile(final_pnl, 95)), 2),

        # 90% CI for total PnL
        "pnl_90ci_low": round(float(np.percentile(final_pnl, 5)), 2),
        "pnl_90ci_high": round(float(np.percentile(final_pnl, 95)), 2),

        # Max drawdown distribution (USD)
        "median_max_dd_usd": round(float(np.median(max_drawdowns)), 2),
        "mean_max_dd_usd": round(float(np.mean(max_drawdowns)), 2),
        "max_dd_90th_pctile": round(float(np.percentile(max_drawdowns, 90)), 2),
        "max_dd_95th_pctile": round(float(np.percentile(max_drawdowns, 95)), 2),
        "max_dd_99th_pctile": round(float(np.percentile(max_drawdowns, 99)), 2),
        "worst_dd_usd": round(float(np.max(max_drawdowns)), 2),

        # Max drawdown distribution (%)
        "median_max_dd_pct": round(float(np.median(max_dd_pct)), 2),
        "max_dd_pct_95th": round(float(np.percentile(max_dd_pct, 95)), 2),

        # Ruin probability
        "ruin_probability_pct": round(pct_ruin, 2),

        # Profit factor distribution
        "pf_median": round(float(np.median(pf_capped)), 2),
        "pf_5th": round(float(np.percentile(pf_capped, 5)), 2),
        "pf_95th": round(float(np.percentile(pf_capped, 95)), 2),
        "pf_mean": round(float(np.mean(pf_capped)), 2),

        # Equity curve percentiles (sampled at intervals for JSON)
        "eq_curve_trades": list(range(0, max_trades + 1, 10)),
        "eq_p5": [round(float(v), 2) for v in eq_p5[::10]],
        "eq_p25": [round(float(v), 2) for v in eq_p25[::10]],
        "eq_p50": [round(float(v), 2) for v in eq_p50[::10]],
        "eq_p75": [round(float(v), 2) for v in eq_p75[::10]],
        "eq_p95": [round(float(v), 2) for v in eq_p95[::10]],
    }


# ─── REPORT GENERATOR ──────────────────────────────────────────────────────

def generate_report(asset_key: str, result: BacktestResult, mc: dict, config: dict) -> str:
    """Generate comprehensive markdown report."""
    lines = []
    lines.append(f"# Symmetry Trap — Full Backtest Report: {asset_key}")
    lines.append(f"**CEREBUS FX v4.0** | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EDT')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Summary ──
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Asset | {config['name']} |")
    lines.append(f"| Pip Size | {config['pip_value']} |")
    lines.append(f"| K-Factor | {config['k_factor']} |")
    lines.append(f"| SL Method | {config['sl_method']} |")
    lines.append(f"| Data Bars | {result.data_bars:,} |")
    lines.append(f"| Data Days | {result.data_days} |")
    lines.append(f"| Total Trades | {result.total_trades} |")
    lines.append(f"| Win Rate | {result.win_rate:.1f}% |")
    lines.append(f"| Total PnL | {result.total_pnl_pips:+.1f} pips |")
    lines.append(f"| Profit Factor | {result.profit_factor:.2f} |")
    lines.append(f"| Sharpe Ratio | {result.sharpe_ratio:.2f} |")
    lines.append(f"| Max Drawdown | {result.max_drawdown_pips:.1f} pips ({result.max_drawdown_pct:.2f}%) |")
    lines.append(f"| Expectancy | {result.expectancy_pips:+.2f} pips/trade |")
    lines.append(f"| Avg Win | {result.avg_win_pips:+.2f} pips |")
    lines.append(f"| Avg Loss | {result.avg_loss_pips:+.2f} pips |")
    lines.append(f"| Kelly Criterion | {result.kelly_criterion * 100:.1f}% |")
    lines.append(f"| Max Consec Wins | {result.max_consec_wins} |")
    lines.append(f"| Max Consec Losses | {result.max_consec_losses} |")
    lines.append("")

    # ── Direction Breakdown ──
    lines.append("## Direction Breakdown")
    lines.append("")
    lines.append(f"| Direction | Trades | Win Rate | PnL |")
    lines.append(f"|-----------|--------|----------|-----|")
    lines.append(f"| Long | {result.long_trades} | {result.long_wr:.1f}% | {result.long_pnl:+.1f} pips |")
    lines.append(f"| Short | {result.short_trades} | {result.short_wr:.1f}% | {result.short_pnl:+.1f} pips |")
    lines.append("")

    # ── Tier Breakdown ──
    lines.append("## Tier Breakdown")
    lines.append("")
    lines.append("| Tier | AR Max | AU | Trigger | Trades | Win Rate | PnL |")
    lines.append("|------|--------|----|---------|--------|----------|-----|")
    for tier_name in ["T1", "T2", "T3"]:
        tc = config["tiers"].get(tier_name, {})
        ts = result.tier_stats.get(tier_name, {})
        lines.append(
            f"| {tier_name} | {tc.get('ar_max', 'N/A')} | {tc.get('au', 'N/A')}p | {tc.get('trigger', 'N/A')}p "
            f"| {ts.get('trades', 0)} | {ts.get('wr', 0):.1f}% | {ts.get('pnl', 0):+.1f}p |"
        )
    lines.append("")

    # ── Loop Distribution ──
    lines.append("## Loop Distribution (Option B: Continuous Loop)")
    lines.append("")
    lines.append("| Loop | Trades | Win Rate | PnL |")
    lines.append("|------|--------|----------|-----|")
    for lk in sorted(result.loop_stats.keys(), key=lambda x: int(x) if x.isdigit() else 99):
        ls = result.loop_stats[lk]
        lines.append(f"| {lk} | {ls['trades']} | {ls['wr']:.1f}% | {ls['pnl']:+.1f}p |")
    lines.append("")

    # ── Hourly Distribution ──
    lines.append("## Hourly Distribution (EST)")
    lines.append("")
    lines.append("| Hour (EST) | Trades | Win Rate | PnL |")
    lines.append("|-----------|--------|----------|-----|")
    for h in sorted(result.hourly_stats.keys(), key=int):
        hs = result.hourly_stats[h]
        lines.append(f"| {int(h):02d}:00 | {hs['trades']} | {hs['wr']:.1f}% | {hs['pnl']:+.1f}p |")
    lines.append("")

    # ── Per-Trade PnL (first 50 + summary) ──
    lines.append("## Per-Trade PnL Distribution")
    lines.append("")
    pnls = [t.pnl_pips for t in result.trades] if result.trades else []
    if pnls:
        lines.append(f"- Total trades: {len(pnls)}")
        lines.append(f"- Median PnL: {float(np.median(pnls)):.1f} pips")
        lines.append(f"- Std Dev: {float(np.std(pnls)):.1f} pips")
        lines.append(f"- Best trade: {max(pnls):+.1f} pips")
        lines.append(f"- Worst trade: {min(pnls):+.1f} pips")
        lines.append(f"- Skewness: {float(np.mean(((pnls - np.mean(pnls)) / max(np.std(pnls), 0.001)) ** 3)):.3f}")
        lines.append("")

        # Histogram
        lines.append("### PnL Histogram")
        lines.append("")
        bins = [(-999, -20), (-20, -10), (-10, -5), (-5, 0), (0, 5), (5, 10), (10, 15), (15, 25), (25, 999)]
        labels = ["<-20p", "-20 to -10", "-10 to -5", "-5 to 0", "0 to 5", "5 to 10", "10 to 15", "15 to 25", ">25p"]
        hist = [0] * len(bins)
        for p in pnls:
            for i, (lo, hi) in enumerate(bins):
                if lo <= p < hi:
                    hist[i] += 1
                    break
        max_count = max(hist) if hist else 1
        lines.append("| Range | Count | Bar |")
        lines.append("|-------|-------|-----|")
        for label, count in zip(labels, hist):
            bar = "█" * max(1, int(count / max_count * 30))
            lines.append(f"| {label} | {count} | {bar} |")
        lines.append("")

    # ── Trade Result Breakdown ──
    lines.append("## Trade Result Breakdown")
    lines.append("")
    result_counts = {}
    for t in result.trades:
        r = t.result
        result_counts[r] = result_counts.get(r, 0) + 1
    for res, count in sorted(result_counts.items(), key=lambda x: -x[1]):
        pct = count / result.total_trades * 100
        lines.append(f"- {res}: {count} ({pct:.1f}%)")
    lines.append("")

    # ── Monte Carlo ──
    lines.append("## Monte Carlo Simulation (10,000 iterations)")
    lines.append("")
    if "error" in mc:
        lines.append(f"**ERROR: {mc['error']}**")
    else:
        lines.append(f"**Configuration:**")
        lines.append(f"- Starting balance: ${mc['initial_balance']:,.0f}")
        lines.append(f"- Risk per trade: {mc['risk_per_trade_pct']}% of equity")
        lines.append(f"- Iterations: {mc['n_iterations']:,}")
        lines.append(f"- Avg loss per trade: {mc['avg_loss_pips']:.1f} pips")
        lines.append("")

        lines.append("### Final PnL Distribution (USD)")
        lines.append("")
        lines.append("| Percentile | Final Equity | PnL |")
        lines.append("|-----------|-------------|-----|")
        lines.append(f"| 5th | ${mc['initial_balance'] + mc['pnl_5th_pctile']:,.2f} | ${mc['pnl_5th_pctile']:+,.2f} |")
        lines.append(f"| 10th | ${mc['initial_balance'] + mc['pnl_90ci_low']:,.2f} | ${mc['pnl_90ci_low']:+,.2f} |")
        lines.append(f"| 25th | ${mc['initial_balance'] + mc['pnl_25th_pctile']:,.2f} | ${mc['pnl_25th_pctile']:+,.2f} |")
        lines.append(f"| 50th (median) | ${mc['initial_balance'] + mc['median_final_pnl_usd']:,.2f} | ${mc['median_final_pnl_usd']:+,.2f} |")
        lines.append(f"| 75th | ${mc['initial_balance'] + mc['pnl_75th_pctile']:,.2f} | ${mc['pnl_75th_pctile']:+,.2f} |")
        lines.append(f"| 90th | ${mc['initial_balance'] + mc['pnl_90ci_high']:,.2f} | ${mc['pnl_90ci_high']:+,.2f} |")
        lines.append(f"| 95th | ${mc['initial_balance'] + mc['pnl_95th_pctile']:,.2f} | ${mc['pnl_95th_pctile']:+,.2f} |")
        lines.append(f"| Mean | ${mc['initial_balance'] + mc['mean_final_pnl_usd']:,.2f} | ${mc['mean_final_pnl_usd']:+,.2f} |")
        lines.append(f"| Std Dev | — | ${mc['std_final_pnl_usd']:,.2f} |")
        lines.append(f"| Profitable simulations | {mc['pct_profitable']:.1f}% |")
        lines.append("")
        lines.append(f"**90% Confidence Interval for Total PnL: [${mc['pnl_90ci_low']:+,.2f}, ${mc['pnl_90ci_high']:+,.2f}]**")
        lines.append("")

        lines.append("### Max Drawdown Distribution (USD)")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Median Max DD | ${mc['median_max_dd_usd']:,.2f} |")
        lines.append(f"| Mean Max DD | ${mc['mean_max_dd_usd']:,.2f} |")
        lines.append(f"| 90th Percentile DD | ${mc['max_dd_90th_pctile']:,.2f} |")
        lines.append(f"| 95th Percentile DD | ${mc['max_dd_95th_pctile']:,.2f} |")
        lines.append(f"| 99th Percentile DD | ${mc['max_dd_99th_pctile']:,.2f} |")
        lines.append(f"| Worst DD | ${mc['worst_dd_usd']:,.2f} |")
        lines.append(f"| Median Max DD % | {mc['median_max_dd_pct']:.1f}% |")
        lines.append(f"| 95th DD % | {mc['max_dd_pct_95th']:.1f}% |")
        lines.append("")

        lines.append("### Risk of Ruin")
        lines.append("")
        lines.append(f"- Ruin threshold (50% drawdown = $5,000): **{mc['ruin_probability_pct']:.2f}%** of simulations hit this level")
        lines.append("")

        lines.append("### Profit Factor Distribution (Monte Carlo)")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Mean PF | {mc['pf_mean']:.2f} |")
        lines.append(f"| Median PF | {mc['pf_median']:.2f} |")
        lines.append(f"| 5th Percentile PF | {mc['pf_5th']:.2f} |")
        lines.append(f"| 95th Percentile PF | {mc['pf_95th']:.2f} |")
        lines.append("")

        lines.append("### Equity Curve Percentiles (Median Path)")
        lines.append("")
        # Show at trade 0, 50, 100, 200, 300, 400, 500
        show_indices = [0, 1, 5, 10, 20, 30, 40, 50]  # map to 0, 10, 50, 100, 200, 300, 400, 500
        header = "| Trade # | " + " | ".join(str(i) for i in show_indices) + " |"
        sep = "|---------|" + "------|" * len(show_indices)
        lines.append(header)
        lines.append(sep)
        for label, eq_data in [("5th %", mc["eq_p5"]), ("25th %", mc["eq_p25"]),
                                ("50th %", mc["eq_p50"]), ("75th %", mc["eq_p75"]),
                                ("95th %", mc["eq_p95"])]:
            vals = [eq_data[i] if i < len(eq_data) else "N/A" for i in show_indices]
            lines.append(f"| {label} | " + " | ".join(f"${v:,.0f}" if isinstance(v, (int, float)) else str(v) for v in vals) + " |")
        lines.append("")

    lines.append("---")
    lines.append(f"*Report generated by CEREBUS Symmetry Trap Batch Runner | {datetime.now().strftime('%Y-%m-%d %H:%M:%S EDT')}*")
    return "\n".join(lines)


# ─── MAIN ──────────────────────────────────────────────────────────────────

def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    batch_summary = {
        "batch": "Batch 1 — Majors A",
        "assets": [],
        "errors": [],
        "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S EDT'),
    }

    for asset_info in ASSETS:
        key = asset_info["key"]
        csv_path = asset_info["csv"]
        print(f"\n{'='*60}")
        print(f"  Processing {key}")
        print(f"{'='*60}")

        config = ASSET_CONFIGS.get(key)
        if config is None:
            msg = f"No config found for {key}"
            print(f"  ERROR: {msg}")
            batch_summary["errors"].append(msg)
            continue

        print(f"  Loading CSV: {csv_path}")
        if not os.path.exists(csv_path):
            msg = f"CSV not found: {csv_path}"
            print(f"  ERROR: {msg}")
            batch_summary["errors"].append(msg)
            continue

        # Run backtest
        bt = SymmetryTrapBacktest(config=config)
        result = bt.run_from_csv(csv_path)
        print(f"  Backtest: {result.total_trades} trades, {result.win_rate:.1f}% WR, PF {result.profit_factor:.2f}")

        # Extract per-trade PnL for MC
        trade_pnls = [t.pnl_pips for t in result.trades] if result.trades else []

        # Run Monte Carlo
        mc = {}
        if trade_pnls:
            print(f"  Running Monte Carlo ({MC_ITERATIONS:,} iterations)...")
            mc = run_monte_carlo(trade_pnls, config)
            print(f"  MC: median PnL ${mc.get('median_final_pnl_usd', 0):+,.2f}, "
                  f"ruin prob {mc.get('ruin_probability_pct', 0):.2f}%")
        else:
            mc = {"error": "no trades to simulate"}
            print(f"  WARNING: No trades, skipping Monte Carlo")

        # Generate report
        report_md = generate_report(key, result, mc, config)
        report_path = os.path.join(REPORTS_DIR, f"{key}_full_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"  Report: {report_path}")

        # Write MC results JSON
        mc_json_path = os.path.join(REPORTS_DIR, f"{key}_mc_results.json")
        with open(mc_json_path, "w", encoding="utf-8") as f:
            json.dump(mc, f, indent=2, default=str)
        print(f"  MC JSON: {mc_json_path}")

        # Collect summary
        batch_summary["assets"].append({
            "key": key,
            "config_name": config["name"],
            "trades": result.total_trades,
            "wins": result.wins,
            "losses": result.losses,
            "win_rate": round(result.win_rate, 1),
            "total_pnl_pips": round(result.total_pnl_pips, 1),
            "profit_factor": round(result.profit_factor, 2),
            "sharpe_ratio": round(result.sharpe_ratio, 2),
            "max_dd_pips": round(result.max_drawdown_pips, 1),
            "max_dd_pct": round(result.max_drawdown_pct, 2),
            "expectancy_pips": round(result.expectancy_pips, 2),
            "median_mc_pnl_usd": mc.get("median_final_pnl_usd", "N/A"),
            "mc_ruin_prob_pct": mc.get("ruin_probability_pct", "N/A"),
            "report_path": report_path,
            "mc_json_path": mc_json_path,
        })

    # Write batch summary
    summary_path = os.path.join(os.path.dirname(QUANT_LAB), "progress", "st-batch1-progress.md")
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)

    summary_lines = []
    summary_lines.append(f"# Symmetry Trap Batch 1 — Majors A: Progress Report")
    summary_lines.append(f"**Generated:** {batch_summary['generated_at']}")
    summary_lines.append(f"**Assets:** EURUSD, GBPUSD, USDCHF")
    summary_lines.append(f"**Engine:** Symmetry Trap (Model B, 4-state FSM)")
    summary_lines.append(f"**Monte Carlo:** {MC_ITERATIONS:,} iterations per asset")
    summary_lines.append("")
    summary_lines.append("---")
    summary_lines.append("")

    # Summary table
    summary_lines.append("## Batch Summary")
    summary_lines.append("")
    summary_lines.append("| Asset | Trades | WR | PF | Sharpe | MaxDD (pips) | MaxDD (%) | Median MC PnL | Ruin Prob |")
    summary_lines.append("|-------|--------|----|----|--------|-------------|-----------|---------------|-----------|")
    for a in batch_summary["assets"]:
        summary_lines.append(
            f"| {a['key']} | {a['trades']} | {a['win_rate']:.1f}% | {a['profit_factor']:.2f} | "
            f"{a['sharpe_ratio']:.2f} | {a['max_dd_pips']:.1f} | {a['max_dd_pct']:.2f}% | "
            f"${a['median_mc_pnl_usd']:+,.2f} | {a['mc_ruin_prob_pct']:.2f}% |"
        )
    summary_lines.append("")

    # Per-asset details
    for a in batch_summary["assets"]:
        summary_lines.append(f"## {a['key']} ({a['config_name']})")
        summary_lines.append("")
        summary_lines.append(f"- **Trades:** {a['trades']} (W:{a['wins']} L:{a['losses']})")
        summary_lines.append(f"- **Win Rate:** {a['win_rate']:.1f}%")
        summary_lines.append(f"- **Total PnL:** {a['total_pnl_pips']:+.1f} pips")
        summary_lines.append(f"- **Profit Factor:** {a['profit_factor']:.2f}")
        summary_lines.append(f"- **Sharpe Ratio:** {a['sharpe_ratio']:.2f}")
        summary_lines.append(f"- **Max Drawdown:** {a['max_dd_pips']:.1f} pips ({a['max_dd_pct']:.2f}%)")
        summary_lines.append(f"- **Expectancy:** {a['expectancy_pips']:+.2f} pips/trade")
        summary_lines.append(f"- **MC Median PnL:** ${a['median_mc_pnl_usd']:+,.2f}")
        summary_lines.append(f"- **MC Ruin Probability:** {a['mc_ruin_prob_pct']:.2f}%")
        summary_lines.append(f"- **Report:** `{a['report_path']}`")
        summary_lines.append(f"- **MC Data:** `{a['mc_json_path']}`")
        summary_lines.append("")

    if batch_summary["errors"]:
        summary_lines.append("## Errors & Flags")
        summary_lines.append("")
        for err in batch_summary["errors"]:
            summary_lines.append(f"- ⚠️ {err}")
        summary_lines.append("")

    summary_lines.append("---")
    summary_lines.append(f"*Batch completed: {batch_summary['generated_at']}*")

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))
    print(f"\n\nBatch summary: {summary_path}")

    print(f"\n{'='*60}")
    print(f"  BATCH 1 COMPLETE")
    print(f"  Reports: {REPORTS_DIR}")
    print(f"  Summary: {summary_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

```

LINKS:
[[Codemap]]
[[01 System Overview]]
[[02 Agent Workflow]]
[[03 Srra Topology]]
[[04 Data And Storage]]
[[Agents]]
[[Api Reference]]
[[Cg 1 Mermaid Specs]]
[[Cg 1 Revised]]
[[Cg 2 Mermaid Specs]]
[[Cg 2 World Model Activation]]
[[Cg 3 Openclaw Anchor]]
[[Cg 3 Relational Topology]]
[[Cg 4 Execution Intelligence]]
[[Cg 4 Mermaid Specs]]
[[Cg 5 Continuity Intelligence]]
[[Cg 6 Meta Cognition]]
[[Cg 7 Multi Scale Orchestration]]
[[Cg 8 Operator Coevolution]]
[[Cg 9 Autonomous Strategic Field]]
[[Chaos Scenarios]]
[[Chat Response Bug Diagram]]
[[Cleanup Report]]
[[Code Quality]]
[[Contributing]]
[[Debugging]]
[[Domain Micro Doctrines]]
[[Harness Engineering]]
[[Heartbeat]]
[[Identity]]
[[Master Plan 2026 05 18]]
[[Master Plan Observer Core]]
[[Master Prompt]]
[[Module Guide]]
[[Observer Core Workspace State]]
[[Oce Unified Frontend Plan]]
[[O 6 Implementation Plan]]
[[O 7 Persistent Field Doc]]
[[Phase10]]
[[Phase Breakdown]]
[[Principles]]
[[Project Progress Clean]]
[[Quality Review]]
[[Quality Review Feedback]]
[[Readme]]
[[Soul]]
[[Sub Agent Rules]]
[[Team Tasks]]
[[Telegram Bot Setup]]
[[Testing]]
[[Test Manual]]
[[Tools]]
[[Topological Cognition Architecture]]
[[User]]
[[Workspace State]]
[[Progress]]
[[Action]]
[[Citation Workflow]]
[[Configuration]]
[[Standard]]
[[Usage]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Memory]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
