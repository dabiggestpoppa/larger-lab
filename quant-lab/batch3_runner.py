"""
CEREBUS Batch 3 Backtest + Monte Carlo Runner
Assets: GBPAUD, GBPNZD, GBPCHF, XAUUSD, XAGBTC, BTCUSD, ETHUSD

Run from: quant-lab/engines/  (where symmetry_trap.py lives)
"""
import sys, os, json, random, math, statistics
from datetime import datetime
from pathlib import Path

# Ensure engine directory is first in path so "import symmetry_trap" works
ENGINE_DIR = Path(__file__).parent / "engines"
sys.path.insert(0, str(ENGINE_DIR))
# Also add parent (quant-lab/) to path
sys.path.insert(0, str(Path(__file__).parent))

# Add workspace and configs to path
WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(WORKSPACE / "quant-lab" / "configs"))

# Import configs
import importlib
ac = importlib.import_module("quant_lab.configs.asset_configs")
ASSET_CONFIGS = ac.ASSET_CONFIGS

# Import backtest engine (this will trigger "from symmetry_trap import ..." inside)
from symmetry_trap_backtest import (
    SymmetryTrapBacktest,
    format_report,
)

DATA_DIR = WORKSPACE / "quant-lab" / "data"
REPORT_DIR = WORKSPACE / "quant-lab" / "reports" / "per-asset"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

ASSETS = ["GBPAUD", "GBPNZD", "GBPCHF", "XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD"]
MC_SIMULATIONS = 10000
STARTING_BALANCE = 10000.0


def run_backtest(asset_key):
    config = ASSET_CONFIGS[asset_key]
    csv_path = DATA_DIR / f"{asset_key}_M5.csv"
    print(f"\n{'='*60}")
    print(f"Running backtest: {asset_key} ({config['name']})")
    print(f"  pip_value={config['pip_value']}, tiers={list(config['tiers'].keys())}")

    bt = SymmetryTrapBacktest(config=config)
    result = bt.run_from_csv(str(csv_path))
    print(f"  Trades: {result.total_trades}, WR: {result.win_rate:.1f}%, PnL: {result.total_pnl_pips:+.1f}p")
    return result


def run_monte_carlo(trades, n_sims=MC_SIMULATIONS):
    pnl_list = [t.pnl_pips for t in trades]
    if not pnl_list:
        return None

    n_trades = len(pnl_list)
    all_equity_curves = []
    max_dd_list = []
    total_pnl_list = []
    pf_list = []

    for _ in range(n_sims):
        random.shuffle(pnl_list)
        equity = [0.0]
        peak = 0.0
        max_dd = 0.0
        wins_list = []
        losses_list_g = []

        for pnl in pnl_list:
            new_eq = equity[-1] + pnl
            equity.append(new_eq)
            if new_eq > peak:
                peak = new_eq
            dd = peak - new_eq
            if dd > max_dd:
                max_dd = dd
            if pnl > 0:
                wins_list.append(pnl)
            else:
                losses_list_g.append(abs(pnl))

        all_equity_curves.append(equity)
        max_dd_list.append(max_dd)
        total_pnl_list.append(sum(pnl_list))

        gross_profit = sum(wins_list) if wins_list else 0
        gross_loss = sum(losses_list_g) if losses_list_g else 0.001
        pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")
        pf_list.append(min(pf, 10.0))

    trade_count = len(all_equity_curves[0])
    median_curve = []
    p5_curve = []
    p95_curve = []
    for i in range(trade_count):
        vals = [curve[i] for curve in all_equity_curves]
        vals.sort()
        median_curve.append(statistics.median(vals))
        p5_idx = max(0, int(len(vals) * 0.05))
        p95_idx = min(len(vals) - 1, int(len(vals) * 0.95))
        p5_curve.append(vals[p5_idx])
        p95_curve.append(vals[p95_idx])

    max_dd_list.sort()
    ruin_count = sum(1 for dd in max_dd_list if dd >= STARTING_BALANCE * 0.5)

    pf_list.sort()

    total_pnl_list.sort()
    ci_low = total_pnl_list[int(len(total_pnl_list) * 0.05)]
    ci_high = total_pnl_list[int(len(total_pnl_list) * 0.95)]

    return {
        "n_simulations": n_sims,
        "median_final_pnl": statistics.median(total_pnl_list),
        "mean_final_pnl": statistics.mean(total_pnl_list),
        "std_final_pnl": statistics.stdev(total_pnl_list) if len(total_pnl_list) > 1 else 0,
        "total_pnl_ci_90": [round(ci_low, 1), round(ci_high, 1)],
        "median_max_dd": statistics.median(max_dd_list),
        "p95_max_dd": max_dd_list[int(len(max_dd_list) * 0.95)],
        "max_dd_worst": max(max_dd_list),
        "ruin_probability": round(ruin_count / n_sims * 100, 2),
        "median_pf": statistics.median(pf_list),
        "p5_pf": pf_list[int(len(pf_list) * 0.05)],
        "p95_pf": pf_list[int(len(pf_list) * 0.95)],
        "median_equity_curve": [round(v, 1) for v in median_curve],
        "p5_equity_curve": [round(v, 1) for v in p5_curve],
        "p95_equity_curve": [round(v, 1) for v in p95_curve],
        "per_trade_pnl": pnl_list,
        "n_trades": n_trades,
    }


def generate_report(asset_key, result, mc_results):
    config = ASSET_CONFIGS[asset_key]
    L = []
    L.append(f"# Symmetry Trap Full Report: {asset_key} ({config['name']})")
    L.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    L.append(f"**Engine:** Symmetry Trap (Engine B) - 4-state FSM")
    L.append(f"**Symbol Registered:** {result.symbol}")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## Summary Statistics")
    L.append("")
    L.append("| Metric | Value |")
    L.append("|--------|-------|")
    L.append(f"| Total Trades | {result.total_trades} |")
    L.append(f"| Wins / Losses | {result.wins} / {result.losses} |")
    L.append(f"| Win Rate | {result.win_rate:.1f}% |")
    L.append(f"| Total PnL | {result.total_pnl_pips:+.1f} pips |")
    L.append(f"| Gross Profit | {result.gross_profit:.1f} pips |")
    L.append(f"| Gross Loss | -{result.gross_loss:.1f} pips |")
    L.append(f"| Profit Factor | {result.profit_factor:.2f} |")
    L.append(f"| Expectancy | {result.expectancy_pips:+.2f} pips/trade |")
    L.append(f"| Avg Win | {result.avg_win_pips:+.1f} pips |")
    L.append(f"| Avg Loss | {result.avg_loss_pips:+.1f} pips |")
    L.append(f"| Sharpe Ratio | {result.sharpe_ratio:.2f} |")
    L.append(f"| Max Drawdown | {result.max_drawdown_pips:.1f} pips ({result.max_drawdown_pct:.2f}%) |")
    L.append(f"| Kelly Criterion | {result.kelly_criterion:.4f} |")
    L.append(f"| Max Consec Wins | {result.max_consec_wins} |")
    L.append(f"| Max Consec Losses | {result.max_consec_losses} |")
    L.append(f"| Data Bars | {result.data_bars:,} |")
    L.append(f"| Data Days | {result.data_days} |")
    L.append("")

    L.append("## Directional Breakdown")
    L.append("")
    L.append("| Direction | Trades | WR | PnL |")
    L.append("|-----------|--------|-----|------|")
    L.append(f"| Long | {result.long_trades} | {result.long_wr:.1f}% | {result.long_pnl:+.1f}p |")
    L.append(f"| Short | {result.short_trades} | {result.short_wr:.1f}% | {result.short_pnl:+.1f}p |")
    L.append("")

    L.append("## Tier Breakdown")
    L.append("")
    L.append("| Tier | Trades | WR | PnL |")
    L.append("|------|--------|-----|------|")
    for tier in ["T1", "T2", "T3"]:
        if tier in result.tier_stats:
            ts = result.tier_stats[tier]
            tier_cfg = config["tiers"].get(tier, {})
            au = tier_cfg.get("au", "?")
            ar_max = tier_cfg.get("ar_max", "?")
            L.append(f"| {tier} (AU={au}p, AR<={ar_max}p) | {ts['trades']} | {ts['wr']:.1f}% | {ts['pnl']:+.1f}p |")
        else:
            L.append(f"| {tier} | 0 | -- | -- |")
    L.append("")

    L.append("## Hourly Distribution (EST)")
    L.append("")
    L.append("| Hour EST | Trades | WR | PnL |")
    L.append("|----------|--------|-----|------|")
    for h_str in sorted(result.hourly_stats.keys(), key=int):
        hs = result.hourly_stats[h_str]
        h = int(h_str)
        L.append(f"| {h:02d}:00-{h+1:02d}:00 | {hs['trades']} | {hs['wr']:.1f}% | {hs['pnl']:+.1f}p |")
    L.append("")

    if result.loop_stats:
        L.append("## Loop Distribution (Option B: Continuous Loop)")
        L.append("")
        L.append("| Loop | Trades | WR | PnL |")
        L.append("|------|--------|-----|------|")
        for lk in sorted(result.loop_stats.keys(), key=lambda x: int(x) if x.isdigit() else 99):
            ls = result.loop_stats[lk]
            L.append(f"| {lk} | {ls['trades']} | {ls['wr']:.1f}% | {ls['pnl']:+.1f}p |")
        L.append("")

    pnls = [t.pnl_pips for t in result.trades]
    if pnls:
        wins_p = [p for p in pnls if p > 0]
        losses_p = [p for p in pnls if p <= 0]
        L.append("## Per-Trade PnL Distribution")
        L.append("")
        L.append(f"- **Best Trade:** +{max(pnls):.1f} pips")
        L.append(f"- **Worst Trade:** {min(pnls):.1f} pips")
        L.append(f"- **Median Trade:** {statistics.median(pnls):.1f} pips")
        if wins_p:
            L.append(f"- **Wins:** {len(wins_p)} (avg +{statistics.mean(wins_p):.1f}p)")
        if losses_p:
            L.append(f"- **Losses:** {len(losses_p)} (avg {statistics.mean(losses_p):.1f}p)")
        L.append("")

    mc_curves = None
    if mc_results:
        L.append("---")
        L.append("")
        L.append("## Monte Carlo Simulation")
        L.append(f"**Simulations:** {mc_results['n_simulations']:,} | **Starting Balance:** ${STARTING_BALANCE:,.0f} | **Risk/Trade:** 1%")
        L.append("")
        L.append("### Total PnL Distribution")
        L.append("")
        L.append("| Metric | Value |")
        L.append("|--------|-------|")
        L.append(f"| Median Final PnL | {mc_results['median_final_pnl']:+.1f} pips |")
        L.append(f"| Mean Final PnL | {mc_results['mean_final_pnl']:+.1f} pips |")
        L.append(f"| Std Dev | {mc_results['std_final_pnl']:.1f} pips |")
        L.append(f"| 90% CI | [{mc_results['total_pnl_ci_90'][0]:+.1f}, {mc_results['total_pnl_ci_90'][1]:+.1f}] |")
        L.append("")

        L.append("### Drawdown Distribution")
        L.append("")
        L.append("| Metric | Value |")
        L.append("|--------|-------|")
        L.append(f"| Median Max DD | {mc_results['median_max_dd']:.1f} pips |")
        L.append(f"| 95th Pct Max DD | {mc_results['p95_max_dd']:.1f} pips |")
        L.append(f"| Worst Max DD | {mc_results['max_dd_worst']:.1f} pips |")
        L.append(f"| Ruin Probability (>50% DD) | {mc_results['ruin_probability']:.2f}% |")
        L.append("")

        L.append("### Profit Factor Distribution (MC)")
        L.append("")
        L.append("| Metric | Value |")
        L.append("|--------|-------|")
        L.append(f"| Median PF | {mc_results['median_pf']:.2f} |")
        L.append(f"| 5th Pct PF | {mc_results['p5_pf']:.2f} |")
        L.append(f"| 95th Pct PF | {mc_results['p95_pf']:.2f} |")
        L.append("")

        eq = mc_results["median_equity_curve"]
        p5 = mc_results["p5_equity_curve"]
        p95 = mc_results["p95_equity_curve"]
        L.append("### Equity Curve Summary (Selected Points)")
        L.append("")
        L.append("| Trade # | Median | 5th Pct | 95th Pct |")
        L.append("|---------|--------|---------|----------|")
        points = sorted(set([0, 25, 50, 100, 250, len(eq) - 1]))
        mc_curves = []
        for i in points:
            if i < len(eq):
                L.append(f"| {i} | {eq[i]:+.1f}p | {p5[i]:+.1f}p | {p95[i]:+.1f}p |")
                mc_curves.append({"trade": i, "median": eq[i], "p5": p5[i], "p95": p95[i]})
        L.append("")

        kelly = result.kelly_criterion
        half_kelly = max(kelly / 2, 0.01)
        L.append("### Risk Analysis")
        L.append("")
        L.append(f"- **Kelly Criterion:** {kelly:.4f}")
        L.append(f"- **Recommended Risk (1/2 Kelly):** {half_kelly * 100:.2f}% per trade")
        L.append(f"- **Expected Return per Trade (1R):** {result.expectancy_pips:.2f} pips")
        if result.expectancy_pips > 0:
            L.append("- **Verdict:** Positive expectancy - statistically profitable")
        else:
            L.append("- **Verdict:** Negative expectancy - needs optimization")
        L.append("")

    L.append("---")
    L.append("")
    L.append("*Report generated by CEREBUS Batch 3 Backtest Runner*")
    L.append("")
    return "\n".join(L), mc_curves


def main():
    batch_results = {}
    batch_errors = {}

    for asset in ASSETS:
        try:
            result = run_backtest(asset)
            mc_results = run_monte_carlo(result.trades) if result.trades else None
            report_text, mc_curves = generate_report(asset, result, mc_results)

            report_path = REPORT_DIR / f"{asset}_full_report.md"
            report_path.write_text(report_text, encoding="utf-8")
            print(f"  Report written: {report_path}")

            if mc_results:
                mc_json = {k: v for k, v in mc_results.items()
                           if k not in ("median_equity_curve", "p5_equity_curve", "p95_equity_curve")}
                mc_json["equity_curve_sample_points"] = mc_curves
                mc_path = REPORT_DIR / f"{asset}_mc_results.json"
                mc_path.write_text(json.dumps(mc_json, indent=2), encoding="utf-8")
                print(f"  MC results written: {mc_path}")

            batch_results[asset] = {
                "trades": result.total_trades,
                "wr": round(result.win_rate, 1),
                "pf": round(result.profit_factor, 2),
                "sharpe": round(result.sharpe_ratio, 2),
                "maxdd_pips": round(result.max_drawdown_pips, 1),
                "maxdd_pct": round(result.max_drawdown_pct, 2),
                "pnl": round(result.total_pnl_pips, 1),
                "status": "OK",
            }

            if result.total_trades < 5:
                if asset == "XAGUSD":
                    batch_errors[asset] = f"XAGUSD generated only {result.total_trades} trades -- config likely issues (tier thresholds too tight, pip_value=0.01 with small AR)"
                else:
                    batch_errors[asset] = f"{asset} generated only {result.total_trades} trades -- check config"
                batch_results[asset]["status"] = "FLAGGED"

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            batch_errors[asset] = str(e)
            batch_results[asset] = {"status": "ERROR", "error": str(e)}

    print(f"\n{'=' * 60}")
    print("Batch Summary:")
    for asset, info in batch_results.items():
        st = info.get("status", "?")
        if st == "OK":
            print(f"  {asset}: {info['trades']} tr, {info['wr']}% WR, PF={info['pf']}, Sharpe={info['sharpe']}, MaxDD={info['maxdd_pips']}p ({info['maxdd_pct']}%), PnL={info['pnl']:+}")
        elif st == "FLAGGED":
            print(f"  {asset}: {info.get('trades','?')} tr (FLAGGED: {batch_errors.get(asset, 'low trade count')})")
        else:
            print(f"  {asset}: ERROR -- {info.get('error', 'unknown')}")

    # Build progress file
    PL = []
    PL.append("# Batch 3 -- Crosses B + Metals + Crypto Backtest Summary")
    PL.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    PL.append("")
    PL.append("| Asset | Trades | WR | PF | Sharpe | MaxDD (pips) | MaxDD (%) | PnL (pips) | Status |")
    PL.append("|-------|--------|-----|-----|--------|-------------|-----------|------------|--------|")
    for asset in ASSETS:
        info = batch_results[asset]
        st = info.get("status", "?")
        if st == "OK":
            PL.append(f"| {asset} | {info['trades']} | {info['wr']}% | {info['pf']} | {info['sharpe']} | {info['maxdd_pips']} | {info['maxdd_pct']}% | {info['pnl']:+} | OK |")
        elif st == "FLAGGED":
            w = info.get('wr', '?')
            p = info.get('pf', '?')
            s = info.get('sharpe', '?')
            md = info.get('maxdd_pips', '?')
            mdp = info.get('maxdd_pct', '?')
            pn = info.get('pnl', '?')
            PL.append(f"| {asset} | {info.get('trades','?')} | {w}% | {p} | {s} | {md} | {mdp}% | {pn} | FLAGGED |")
        else:
            PL.append(f"| {asset} | -- | -- | -- | -- | -- | -- | -- | ERROR |")
    PL.append("")

    if batch_errors:
        PL.append("## Issues / Flags")
        PL.append("")
        for a, e2 in batch_errors.items():
            PL.append(f"- **{a}:** {e2}")
        PL.append("")

    PL.append("## Reports Generated")
    PL.append("")
    for asset in ASSETS:
        PL.append(f"- `{REPORT_DIR}/{asset}_full_report.md`")
        PL.append(f"- `{REPORT_DIR}/{asset}_mc_results.json`")
    PL.append("")

    PL.append("## Monte Carlo Comparison")
    PL.append("")
    PL.append("| Asset | Median PnL | 90% CI | Median MaxDD | Ruin Prob | Median PF |")
    PL.append("|-------|-----------|--------|-------------|-----------|-----------|")
    for asset in ASSETS:
        mc_path = REPORT_DIR / f"{asset}_mc_results.json"
        if mc_path.exists():
            mc = json.loads(mc_path.read_text(encoding="utf-8"))
            ci = mc.get("total_pnl_ci_90", ["?", "?"])
            PL.append(f"| {asset} | {mc.get('median_final_pnl','?'):+}p | [{ci[0]:+}, {ci[1]:+}] | {mc.get('median_max_dd','?')}p | {mc.get('ruin_probability','?')}% | {mc.get('median_pf','?')} |")
    PL.append("")

    PL.append("## Asset Configuration Reference")
    PL.append("")
    for asset in ASSETS:
        cfg = ASSET_CONFIGS[asset]
        PL.append(f"### {asset}")
        PL.append(f"- pip_value: {cfg['pip_value']}")
        PL.append(f"- k_factor: {cfg['k_factor']}")
        PL.append(f"- sl_method: {cfg['sl_method']}")
        for tname, tcfg in cfg['tiers'].items():
            PL.append(f"- {tname}: AR<={tcfg['ar_max']}p, AU={tcfg['au']}p, trigger={tcfg['trigger']}p")
        PL.append("")

    PROGRESS_DIR = WORKSPACE / "progress"
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    progress_path = PROGRESS_DIR / "st-batch3-progress.md"
    progress_path.write_text("\n".join(PL), encoding="utf-8")
    print(f"\nProgress file: {progress_path}")


if __name__ == "__main__":
    main()
