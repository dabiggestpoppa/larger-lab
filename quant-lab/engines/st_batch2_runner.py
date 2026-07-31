"""
Batch 2 Symmetry Trap Backtest + Monte Carlo Runner
Assets: USDJPY, AUDUSD, NZDUSD, CHFJPY, GBPJPY
"""
from __future__ import annotations
import json, os, random, statistics, sys, importlib.util
from datetime import datetime
from pathlib import Path

ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
ENGINE_DIR = ROOT / "quant-lab" / "engines"
DATA_DIR = ROOT / "quant-lab" / "data"
REPORTS_DIR = ROOT / "quant-lab" / "reports" / "per-asset"
PROGRESS_DIR = ROOT / "progress"

# ---- load modules ----
sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(ROOT / "quant-lab" / "configs"))

from asset_configs import ASSET_CONFIGS
# Need to inject into sys.modules for the backtest engine
import symmetry_trap as st_mod
sys.modules["symmetry_trap"] = st_mod
from symmetry_trap_backtest import load_m5_csv, SymmetryTrapBacktest, BacktestResult, TradeRecord

ASSETS = ["USDJPY", "AUDUSD", "NZDUSD", "CHFJPY", "GBPJPY"]
MC_SIMULATIONS = 10_000
INITIAL_BALANCE = 10000.0
RISK_PCT = 0.01
random.seed(42)


def compute_equity_curve_percentiles(pnls, n_trades, n_sims, method):
    curves = []
    for _ in range(min(n_sims, 500)):
        shuffled = random.sample(pnls, n_trades)
        curve, equity = [], 0.0
        for p in shuffled:
            equity += p
            curve.append(round(equity, 1))
        curves.append(curve)
    if not curves:
        return []
    result = []
    for i in range(n_trades):
        vals = sorted(c[i] for c in curves)
        n = len(vals)
        if method == "median":
            result.append(round(statistics.median(vals), 1))
        elif method == "p5":
            result.append(round(vals[int(n * 0.05)], 1))
        elif method == "p95":
            result.append(round(vals[int(n * 0.95)], 1))
    return result


def run_monte_carlo(trade_dicts, initial_balance, risk_pct, n_sims):
    if not trade_dicts:
        return {}
    pnls = [t["pnl_pips"] for t in trade_dicts]
    n_trades = len(pnls)
    terminal_pnls, max_dds, profit_factors = [], [], []
    for _ in range(n_sims):
        shuffled = random.sample(pnls, n_trades)
        equity, peak, max_dd, gp, gl = 0.0, 0.0, 0.0, 0.0, 0.0
        for p in shuffled:
            equity += p
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd
            if p > 0:
                gp += p
            else:
                gl += abs(p)
        terminal_pnls.append(equity)
        max_dds.append(max_dd)
        if gl > 0:
            profit_factors.append(gp / gl)
        elif gp > 0:
            profit_factors.append(float("inf"))

    terminal_sorted = sorted(terminal_pnls)
    dd_sorted = sorted(max_dds)
    pf_sorted = sorted(p for p in profit_factors if p != float("inf"))
    n = len(terminal_sorted)
    ruin_count = sum(1 for d in max_dds if d >= 200)

    return {
        "n_simulations": n_sims,
        "initial_balance": initial_balance,
        "risk_per_trade_pct": risk_pct,
        "n_trades_in_sequence": n_trades,
        "terminal_pnl_median": round(statistics.median(terminal_sorted), 1),
        "terminal_pnl_mean": round(statistics.mean(terminal_sorted), 1),
        "terminal_pnl_std": round(statistics.stdev(terminal_sorted) if n > 1 else 0, 1),
        "terminal_pnl_5th": round(terminal_sorted[int(n * 0.05)], 1),
        "terminal_pnl_25th": round(terminal_sorted[int(n * 0.25)], 1),
        "terminal_pnl_75th": round(terminal_sorted[int(n * 0.75)], 1),
        "terminal_pnl_95th": round(terminal_sorted[int(n * 0.95)], 1),
        "terminal_pnl_min": round(terminal_sorted[0], 1),
        "terminal_pnl_max": round(terminal_sorted[-1], 1),
        "max_dd_median": round(statistics.median(dd_sorted), 1),
        "max_dd_mean": round(statistics.mean(dd_sorted), 1),
        "max_dd_95th": round(dd_sorted[int(len(dd_sorted) * 0.95)], 1),
        "max_dd_99th": round(dd_sorted[int(len(dd_sorted) * 0.99)], 1),
        "max_dd_worst": round(dd_sorted[-1], 1),
        "ruin_probability": round(ruin_count / n_sims * 100, 2),
        "profit_factor_median": round(statistics.median(pf_sorted), 3) if pf_sorted else None,
        "profit_factor_5th": round(pf_sorted[int(len(pf_sorted) * 0.05)], 3) if pf_sorted else None,
        "profit_factor_95th": round(pf_sorted[int(len(pf_sorted) * 0.95)], 3) if pf_sorted else None,
        "confidence_90_lo": round(terminal_sorted[int(n * 0.05)], 1),
        "confidence_90_hi": round(terminal_sorted[int(n * 0.95)], 1),
        "equity_curve_median_sample": compute_equity_curve_percentiles(pnls, n_trades, n_sims, "median")[:50],
        "equity_curve_5th_sample": compute_equity_curve_percentiles(pnls, n_trades, n_sims, "p5")[:50],
        "equity_curve_95th_sample": compute_equity_curve_percentiles(pnls, n_trades, n_sims, "p95")[:50],
    }


def generate_report(asset_key, result, mc):
    ts_str = datetime.now().strftime("%Y-%m-%d %H:%M EST")
    cfg = ASSET_CONFIGS[asset_key]
    L = []
    L.append(f"# Symmetry Trap Backtest Report - {cfg['name']}")
    L.append("")
    L.append(f"> **Generated:** {ts_str} | **Engine:** CEREBUS FX v4.0 - Model B")
    L.append(f"> **Data:** {result.data_bars:,} M5 bars | {result.data_days} trading days")
    L.append(f"> **Symbol:** {asset_key} | Pip Size: {cfg['pip_value']} | SL: {cfg['sl_method']}")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 1. Configuration")
    L.append("")
    L.append("| Parameter | Value |")
    L.append("|-----------|-------|")
    L.append(f"| k-Factor | {cfg['k_factor']} |")
    L.append(f"| SL Method | {cfg['sl_method']} |")
    L.append(f"| P90 Threshold | {cfg['p90_threshold']} pips |")
    for tn in ["T1", "T2", "T3"]:
        if tn in cfg["tiers"]:
            t = cfg["tiers"][tn]
            L.append(f"| {tn} | AR <= {t['ar_max']}p | AU = {t['au']}p | Trigger = {t['trigger']}p |")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 2. Summary Statistics")
    L.append("")
    L.append("| Metric | Value |")
    L.append("|--------|-------|")
    L.append(f"| Total Trades | {result.total_trades} |")
    L.append(f"| Wins / Losses | {result.wins} / {result.losses} |")
    L.append(f"| Win Rate | {result.win_rate:.1f}% |")
    L.append(f"| Total PnL | {result.total_pnl_pips:+.1f} pips |")
    L.append(f"| Profit Factor | {result.profit_factor:.2f} |")
    L.append(f"| Sharpe Ratio | {result.sharpe_ratio:.2f} |")
    L.append(f"| Max Drawdown | {result.max_drawdown_pips:.1f} pips ({result.max_drawdown_pct:.2f}%) |")
    L.append(f"| Expectancy | {result.expectancy_pips:+.2f} pips/trade |")
    L.append(f"| Avg Win | {result.avg_win_pips:+.1f} pips |")
    L.append(f"| Avg Loss | {result.avg_loss_pips:+.1f} pips |")
    L.append(f"| Kelly Criterion | {result.kelly_criterion:.3f} |")
    L.append(f"| Max Consec Wins | {result.max_consec_wins} |")
    L.append(f"| Max Consec Losses | {result.max_consec_losses} |")
    L.append("")
    L.append("### Direction Breakdown")
    L.append("")
    L.append("| Direction | Trades | Win Rate | PnL |")
    L.append("|-----------|--------|----------|------|")
    L.append(f"| LONG | {result.long_trades} | {result.long_wr:.1f}% | {result.long_pnl:+.1f}p |")
    L.append(f"| SHORT | {result.short_trades} | {result.short_wr:.1f}% | {result.short_pnl:+.1f}p |")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 3. Tier Breakdown")
    L.append("")
    if result.tier_stats:
        L.append("| Tier | Trades | Win Rate | PnL (pips) |")
        L.append("|------|--------|----------|------------|")
        for tn in ["T1", "T2", "T3", "NO_GO"]:
            if tn in result.tier_stats:
                ts_ = result.tier_stats[tn]
                L.append(f"| {tn} | {ts_['trades']} | {ts_['wr']:.1f}% | {ts_['pnl']:+.1f} |")
    else:
        L.append("_No tier data available._")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 4. Hourly Distribution (EST)")
    L.append("")
    L.append("Activation window: 02:00-12:00 EST (12PM cutoff enforced)")
    L.append("")
    if result.hourly_stats:
        L.append("| Hour (EST) | Trades | Win Rate | PnL (pips) |")
        L.append("|------------|--------|----------|------------|")
        for h in sorted(result.hourly_stats.keys(), key=int):
            hs = result.hourly_stats[h]
            L.append(f"| {int(h):02d}:00 | {hs['trades']} | {hs['wr']:.1f}% | {hs['pnl']:+.1f} |")
    else:
        L.append("_No hourly data available._")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 5. Loop Distribution (Option B)")
    L.append("")
    L.append("Sequential loops per session (max 5). Kill switches increment loop count.")
    L.append("")
    if result.loop_stats:
        L.append("| Loop | Trades | Win Rate | PnL (pips) |")
        L.append("|------|--------|----------|------------|")
        for lk in sorted(result.loop_stats.keys(), key=lambda x: int(x) if x.isdigit() else 99):
            ls = result.loop_stats[lk]
            L.append(f"| {lk} | {ls['trades']} | {ls['wr']:.1f}% | {ls['pnl']:+.1f} |")
    else:
        L.append("_No loop data._")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 6. Per-Trade PnL List")
    L.append("")
    L.append("| # | Date | Dir | Entry | Exit | Result | PnL (pips) | Tier | Loop |")
    L.append("|---|------|-----|-------|------|--------|-------------|------|------|")
    for idx, t in enumerate(result.trades, 1):
        dt_s = t.entry_time.strftime("%Y-%m-%d") if t.entry_time else "N/A"
        L.append(f"| {idx} | {dt_s} | {t.direction} | {t.entry_price:.5f} | {t.exit_price:.5f} | {t.result} | {t.pnl_pips:+.1f} | {t.tier} | {t.loop_count} |")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 7. Monte Carlo Simulation")
    L.append("")
    L.append(f"**Method:** Randomized trade sequence simulation using actual per-trade PnL")
    L.append(f"**Simulations:** {mc.get('n_simulations', 'N/A'):,}")
    L.append(f"**Risk per trade:** 1% of ${mc.get('initial_balance', 0):,.0f}")
    L.append(f"**Trade sequence length:** {mc.get('n_trades_in_sequence', 'N/A')} trades")
    L.append("")
    L.append("### Terminal PnL Distribution")
    L.append("")
    L.append("| Percentile | Terminal PnL (pips) |")
    L.append("|------------|---------------------|")
    L.append(f"| Min | {mc.get('terminal_pnl_min', 'N/A')} |")
    L.append(f"| 5th | {mc.get('terminal_pnl_5th', 'N/A')} |")
    L.append(f"| 25th | {mc.get('terminal_pnl_25th', 'N/A')} |")
    L.append(f"| Median | {mc.get('terminal_pnl_median', 'N/A')} |")
    L.append(f"| Mean | {mc.get('terminal_pnl_mean', 'N/A')} |")
    L.append(f"| 75th | {mc.get('terminal_pnl_75th', 'N/A')} |")
    L.append(f"| 95th | {mc.get('terminal_pnl_95th', 'N/A')} |")
    L.append(f"| Max | {mc.get('terminal_pnl_max', 'N/A')} |")
    L.append(f"| Std Dev | {mc.get('terminal_pnl_std', 'N/A')} |")
    L.append("")
    L.append(f"**90% CI for Total PnL:** [{mc.get('confidence_90_lo', 'N/A')}, {mc.get('confidence_90_hi', 'N/A')}] pips")
    L.append("")
    L.append("### Max Drawdown Distribution")
    L.append("")
    L.append("| Metric | Value (pips) |")
    L.append("|--------|--------------|")
    L.append(f"| Median | {mc.get('max_dd_median', 'N/A')} |")
    L.append(f"| Mean | {mc.get('max_dd_mean', 'N/A')} |")
    L.append(f"| 95th pctl | {mc.get('max_dd_95th', 'N/A')} |")
    L.append(f"| 99th pctl | {mc.get('max_dd_99th', 'N/A')} |")
    L.append(f"| Worst | {mc.get('max_dd_worst', 'N/A')} |")
    L.append("")
    L.append(f"**Ruin Probability** (max DD >= 200 pips): **{mc.get('ruin_probability', 'N/A')}%**")
    L.append("")
    L.append("### Monte Carlo Profit Factor Distribution")
    L.append("")
    L.append("| Percentile | Profit Factor |")
    L.append("|------------|---------------|")
    pf5 = mc.get('profit_factor_5th', 'N/A')
    pf50 = mc.get('profit_factor_median', 'N/A')
    pf95 = mc.get('profit_factor_95th', 'N/A')
    L.append(f"| 5th | {pf5} |")
    L.append(f"| Median | {pf50} |")
    L.append(f"| 95th | {pf95} |")
    L.append("")
    eq_med = mc.get('equity_curve_median_sample', [])
    eq_p5 = mc.get('equity_curve_5th_sample', [])
    eq_p95 = mc.get('equity_curve_95th_sample', [])
    if eq_med:
        L.append("### Sample Equity Curve (First 50 Trades)")
        L.append("")
        L.append("| Trade # | Median | 5th Pctl | 95th Pctl |")
        L.append("|---------|--------|----------|-----------|")
        for i in range(min(50, len(eq_med))):
            v5 = f"{eq_p5[i]:+.1f}" if i < len(eq_p5) else "N/A"
            v95 = f"{eq_p95[i]:+.1f}" if i < len(eq_p95) else "N/A"
            L.append(f"| {i+1} | {eq_med[i]:+.1f} | {v5} | {v95} |")
    L.append("")
    L.append("---")
    L.append("")
    L.append(f"*Report generated by CEREBUS Symmetry Trap Backtest Engine v4.0 - {ts_str}*")
    return "\n".join(L)


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    batch_results = {}

    for asset_key in ASSETS:
        print(f"\n{'='*60}\n  ASSET: {asset_key}\n{'='*60}")
        csv_path = DATA_DIR / f"{asset_key}_M5.csv"
        if not csv_path.exists():
            alt = DATA_DIR / f"{asset_key}PRO_M5.csv"
            if alt.exists():
                csv_path = alt
            else:
                print(f"  SKIP: No data file for {asset_key}")
                batch_results[asset_key] = {"error": "No data file"}
                continue

        config = ASSET_CONFIGS.get(asset_key)
        if not config:
            print(f"  SKIP: No config for {asset_key}")
            batch_results[asset_key] = {"error": "No config"}
            continue

        print(f"  Config: {config['name']} | pip={config['pip_value']} | k={config['k_factor']}")
        print(f"  Loading {csv_path.name}...")

        try:
            bt = SymmetryTrapBacktest(config=config)
            result = bt.run_from_csv(str(csv_path))
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback; traceback.print_exc()
            batch_results[asset_key] = {"error": str(e)}
            continue

        trade_dicts = [{"pnl_pips": t.pnl_pips, "direction": t.direction, "result": t.result, "tier": t.tier} for t in result.trades]
        print(f"  Trades: {result.total_trades} | WR: {result.win_rate:.1f}% | PnL: {result.total_pnl_pips:+.1f}p | PF: {result.profit_factor:.2f} | Sharpe: {result.sharpe_ratio:.2f} | MaxDD: {result.max_drawdown_pips:.1f}p")

        if result.total_trades == 0:
            batch_results[asset_key] = {"trades": 0, "wr": 0, "pf": 0, "sharpe": 0, "maxdd": 0, "report_path": None, "error": "No trades"}
            warn = f"# Symmetry Trap - {asset_key}\n\nNo trades generated.\nData: {result.data_bars:,} bars, {result.data_days} days\n"
            (REPORTS_DIR / f"{asset_key}_full_report.md").write_text(warn)
            continue

        print(f"  Monte Carlo ({MC_SIMULATIONS:,} sims)...")
        mc = run_monte_carlo(trade_dicts, INITIAL_BALANCE, RISK_PCT, MC_SIMULATIONS)
        print(f"  MC: Median={mc.get('terminal_pnl_median')}p | Ruin={mc.get('ruin_probability')}% | PF_med={mc.get('profit_factor_median')}")

        report_md = generate_report(asset_key, result, mc)
        rpath = REPORTS_DIR / f"{asset_key}_full_report.md"
        rpath.write_text(report_md, encoding="utf-8")
        print(f"  Report: {rpath}")

        mc_json = {
            "asset": asset_key,
            "timestamp": datetime.now().isoformat(),
            "backtest": {
                "trades": result.total_trades, "wins": result.wins, "losses": result.losses,
                "win_rate": result.win_rate, "total_pnl_pips": result.total_pnl_pips,
                "profit_factor": result.profit_factor, "sharpe": result.sharpe_ratio,
                "max_dd_pips": result.max_drawdown_pips, "max_dd_pct": result.max_drawdown_pct,
                "expectancy": result.expectancy_pips, "tier_stats": result.tier_stats,
                "hourly_stats": result.hourly_stats, "loop_stats": result.loop_stats,
                "long": {"trades": result.long_trades, "wr": result.long_wr, "pnl": result.long_pnl},
                "short": {"trades": result.short_trades, "wr": result.short_wr, "pnl": result.short_pnl},
            },
            "monte_carlo": mc,
            "per_trade_pnl": [t.pnl_pips for t in result.trades],
        }
        mpath = REPORTS_DIR / f"{asset_key}_mc_results.json"
        mpath.write_text(json.dumps(mc_json, indent=2), encoding="utf-8")

        batch_results[asset_key] = {
            "trades": result.total_trades, "wins": result.wins, "losses": result.losses,
            "wr": round(result.win_rate, 1), "pnl": round(result.total_pnl_pips, 1),
            "pf": round(result.profit_factor, 2), "sharpe": round(result.sharpe_ratio, 2),
            "maxdd": round(result.max_drawdown_pips, 1), "maxdd_pct": round(result.max_drawdown_pct, 2),
            "report_path": str(rpath), "mc_path": str(mpath),
            "mc_median_pnl": mc.get("terminal_pnl_median"), "mc_ruin_prob": mc.get("ruin_probability"),
        }

    # ---- batch summary ----
    print("\n" + "=" * 60 + "\n  BATCH SUMMARY\n" + "=" * 60)
    now = datetime.now().strftime('%Y-%m-%d %H:%M EST')
    SL = []
    SL.append(f"# Batch 2 Progress - Majors B + Crosses A")
    SL.append(f"")
    SL.append(f"> **Date:** {now} | **Assets:** USDJPY, AUDUSD, NZDUSD, CHFJPY, GBPJPY")
    SL.append(f"> **Engine:** Symmetry Trap (Model B, 4-state FSM)")
    SL.append(f"")
    SL.append(f"## Results Summary")
    SL.append(f"")
    SL.append(f"| Asset | Trades | W | L | WR | PnL (pips) | PF | Sharpe | MaxDD (pips) | MaxDD % | MC Median | Ruin % |")
    SL.append(f"|-------|--------|---|---|----|------------|----|--------|---------------|---------|-----------|--------|")

    errors, flags = [], []
    for ak in ASSETS:
        r = batch_results.get(ak, {})
        if "error" in r:
            errors.append(f"- **{ak}**: {r['error']}")
            SL.append(f"| {ak} | ERROR | - | - | - | - | - | - | - | - | - | - |")
            continue
        if r.get("trades", 0) == 0:
            flags.append(f"- **{ak}**: Zero trades")
        SL.append(f"| {ak} | {r.get('trades','-')} | {r.get('wins','-')} | {r.get('losses','-')} | {r.get('wr','-')}% | {r.get('pnl','-'):+}p | {r.get('pf','-')} | {r.get('sharpe','-')} | {r.get('maxdd','-')} | {r.get('maxdd_pct','-')}% | {r.get('mc_median_pnl','-')} | {r.get('mc_ruin_prob','-')}% |")

    SL.append("")
    SL.append("## Reports Generated")
    SL.append("")
    for ak in ASSETS:
        r = batch_results.get(ak, {})
        if r.get("report_path"):
            SL.append(f"- **{ak}**: `{r['report_path']}`")
        else:
            SL.append(f"- **{ak}**: No report generated")

    if errors:
        SL.append("") ; SL.append("## Errors") ; SL.extend(errors)
    if flags:
        SL.append("") ; SL.append("## Flags") ; SL.extend(flags)

    SL.append("")
    SL.append("---")
    done = len([a for a in ASSETS if batch_results.get(a, {}).get("report_path")])
    SL.append(f"*Batch 2 complete - {done}/{len(ASSETS)} reports generated*")

    ppath = PROGRESS_DIR / "st-batch2-progress.md"
    ppath.write_text("\n".join(SL), encoding="utf-8")
    print(f"\n  Progress: {ppath}")
    print(f"\n  BATCH 2 COMPLETE")


if __name__ == "__main__":
    main()
