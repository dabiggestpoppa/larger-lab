"""
CEREBUS FX v4.0 — Symmetry Trap ONLY Multi-Asset Backtest Runner
==================================================================
ST ONLY. No P90. No hybrid. Pure Symmetry Trap engine.

Runs Symmetry Trap backtest across ALL available assets in ASSET_CONFIGS registry.
Uses per-asset config injection (tier config, pip_size, etc.).

Outputs:
  - quant-lab/reports/st_only_multi_asset_results.json
  - quant-lab/reports/st_only_multi_asset_report.md
"""

from __future__ import annotations

import csv
import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Path Setup ────────────────────────────────────────────────────────────
REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
QUANT_LAB = REPO_ROOT / "quant-lab"
DATA_DIR = QUANT_LAB / "data"
REPORTS_DIR = QUANT_LAB / "reports"
CONFIGS_DIR = QUANT_LAB / "configs"
ENGINES_DIR = QUANT_LAB / "engines"

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(CONFIGS_DIR))
sys.path.insert(0, str(ENGINES_DIR))

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [ST-ONLY] %(levelname)s: %(message)s",
)
logger = logging.getLogger("st_only_multi_asset")
logging.getLogger("cerebus.symmetry_trap").setLevel(logging.WARNING)
logging.getLogger("cerebus.symmetry_trap_backtest").setLevel(logging.WARNING)

# ── Imports ───────────────────────────────────────────────────────────────
from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, format_report, BacktestResult, load_m5_csv


# ── STEP 1: Check existing CSV data ───────────────────────────────────────

def get_existing_data() -> Dict[str, Path]:
    """Scan DATA_DIR for M5 CSV files and map to asset keys."""
    data_map: Dict[str, Path] = {}
    all_csvs = sorted(DATA_DIR.glob("*.csv"))

    for asset_key in ASSET_CONFIGS:
        # Pattern 1: {ASSET_KEY}_M5.csv  (e.g., EURUSD_M5.csv)
        p1 = DATA_DIR / f"{asset_key}_M5.csv"
        if p1.exists():
            data_map[asset_key] = p1
            continue

        # Pattern 2: {asset_key}PRO_M5*.csv
        candidates = sorted(DATA_DIR.glob(f"{asset_key}PRO_M5*.csv"))
        if candidates:
            best = max(candidates, key=lambda p: p.stat().st_size)
            data_map[asset_key] = best
            continue

        # Pattern 3: {asset_key}m_M5*.csv
        candidates = sorted(DATA_DIR.glob(f"{asset_key}m_M5*.csv"))
        if candidates:
            best = max(candidates, key=lambda p: p.stat().st_size)
            data_map[asset_key] = best
            continue

        # Pattern 4: Generic
        candidates = sorted(DATA_DIR.glob(f"{asset_key}*M5*.csv"))
        if candidates:
            best = max(candidates, key=lambda p: p.stat().st_size)
            data_map[asset_key] = best
            continue

    return data_map


# ── STEP 2: Run backtest per asset ────────────────────────────────────────

def run_asset_backtest(asset_key: str, csv_path: Path) -> Optional[dict]:
    """Run ST ONLY backtest for a single asset with config injection."""
    config = ASSET_CONFIGS[asset_key]
    pip_size = config["pip_value"]
    tier_config = config["tiers"]

    log_asset = f"{asset_key} ({config.get('name', asset_key)})"
    csv_size_mb = csv_path.stat().st_size / 1024 / 1024
    print(f"  Running {log_asset} | pip_size={pip_size} | csv={csv_path.name} ({csv_size_mb:.1f}MB)")

    try:
        bt = SymmetryTrapBacktest(
            pip_size=pip_size,
            tier_config=tier_config,
            symbol=asset_key,
            config=config,
        )
        result: BacktestResult = bt.run_from_csv(str(csv_path))
    except Exception as e:
        print(f"  ERROR {log_asset}: {e}")
        import traceback
        traceback.print_exc()
        return None

    report_text = format_report(result)
    print(f"  {log_asset}: {result.total_trades} trades | WR={result.win_rate:.1f}% | PnL={result.total_pnl_pips:+.1f}p | PF={result.profit_factor:.2f}")

    flags = []
    if result.total_trades == 0:
        flags.append("ZERO_TRADES")
    if result.win_rate < 50.0 and result.total_trades > 0:
        flags.append("LOW_WR")
    if result.win_rate > 99.0 and result.total_trades > 5:
        flags.append("SUSPICIOUS_HIGH_WR")

    # Compute avg TP and avg SL distances
    avg_tp_dist = 0.0
    avg_sl_dist = 0.0
    if result.trades:
        tp_dists = []
        sl_dists = []
        for t in result.trades:
            if t.tp_price and t.entry_price:
                tp_dists.append(abs(t.tp_price - t.entry_price) / pip_size)
            if t.sl_price and t.entry_price:
                sl_dists.append(abs(t.entry_price - t.sl_price) / pip_size)
        avg_tp_dist = sum(tp_dists) / len(tp_dists) if tp_dists else 0.0
        avg_sl_dist = sum(sl_dists) / len(sl_dists) if sl_dists else 0.0

    entry = {
        "asset_key": asset_key,
        "name": config.get("name", asset_key),
        "config_used": {
            "pip_value": config["pip_value"],
            "k_factor": config["k_factor"],
            "sl_method": config.get("sl_method", "N/A"),
            "csv_file": csv_path.name,
        },
        "total_trades": result.total_trades,
        "wins": result.wins,
        "losses": result.losses,
        "win_rate": round(result.win_rate, 2),
        "pnl_pips": round(result.total_pnl_pips, 2),
        "profit_factor": round(result.profit_factor, 4) if result.profit_factor != float("inf") else 999.99,
        "sharpe": round(result.sharpe_ratio, 4),
        "max_drawdown_pips": round(result.max_drawdown_pips, 2),
        "max_drawdown_pct": round(result.max_drawdown_pct, 4),
        "expectancy_pips": round(result.expectancy_pips, 2),
        "avg_win_pips": round(result.avg_win_pips, 2),
        "avg_loss_pips": round(result.avg_loss_pips, 2),
        "avg_tp_distance_pips": round(avg_tp_dist, 2),
        "avg_sl_distance_pips": round(avg_sl_dist, 2),
        "long_trades": result.long_trades,
        "long_wr": round(result.long_wr, 2),
        "long_pnl_pips": round(result.long_pnl, 2),
        "short_trades": result.short_trades,
        "short_wr": round(result.short_wr, 2),
        "short_pnl_pips": round(result.short_pnl, 2),
        "tier_stats": result.tier_stats,
        "hourly_stats": result.hourly_stats,
        "loop_stats": result.loop_stats,
        "data_bars": result.data_bars,
        "data_days": result.data_days,
        "kelly": round(result.kelly_criterion, 4),
        "max_consec_wins": result.max_consec_wins,
        "max_consec_losses": result.max_consec_losses,
        "flags": flags,
        "report_text": report_text,
    }
    return entry


# ── STEP 3: Generate summary report ───────────────────────────────────────

def generate_summary(all_results: List[dict], no_data: List[str]) -> str:
    lines = []
    lines.append("# Symmetry Trap ONLY Multi-Asset Backtest Report")
    lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"\n**Engine:** Symmetry Trap (ST) ONLY — No P90 involved**\n")

    # Per-pair breakdown table
    lines.append("## Per-Pair Summary\n")
    lines.append("| Asset | Trades | WR% | Avg TP (p) | Avg SL (p) | Total Pips | PF | MaxDD (p) |")
    lines.append("|-------|--------|-----|------------|------------|------------|----|-----------|")

    total_pnl = 0.0
    total_trades = 0
    wrs = []
    for r in sorted(all_results, key=lambda x: x["pnl_pips"], reverse=True):
        lines.append(
            f"| {r['asset_key']} | {r['total_trades']} | {r['win_rate']:.1f}% | "
            f"{r['avg_tp_distance_pips']:.1f} | {r['avg_sl_distance_pips']:.1f} | "
            f"{r['pnl_pips']:+.1f} | {r['profit_factor']:.2f} | {r['max_drawdown_pips']:.1f} |"
        )
        total_pnl += r["pnl_pips"]
        total_trades += r["total_trades"]
        wrs.append(r['win_rate'])

    avg_wr = sum(wrs) / len(wrs) if wrs else 0

    lines.append(f"\n## Final Summary\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| **Total Trades** | {total_trades} |")
    lines.append(f"| **Average WR** | {avg_wr:.1f}% |")
    lines.append(f"| **Combined Pips** | {total_pnl:+.1f} |")
    lines.append(f"| **Assets Tested** | {len(all_results)} |")
    lines.append(f"| **Assets Missing Data** | {len(no_data)} |")

    if no_data:
        lines.append(f"\n## Assets Missing Data\n")
        for n in no_data:
            lines.append(f"- {n}")

    # Full summary table (extended)
    lines.append("\n## Extended Summary Table\n")
    lines.append("| Asset | Trades | WR% | PnL (pips) | PF | Sharpe | MaxDD (pips) | T1 | T2 | T3 | Flags |")
    lines.append("|-------|--------|-----|------------|----|--------|--------------|----|----|----|-------|")

    for r in sorted(all_results, key=lambda x: x["pnl_pips"], reverse=True):
        ts = r.get("tier_stats", {})
        t1 = ts.get("T1", {}).get("wr", "-")
        t2 = ts.get("T2", {}).get("wr", "-")
        t3 = ts.get("T3", {}).get("wr", "-")
        t1s = f"{t1}%" if isinstance(t1, (int, float)) else t1
        t2s = f"{t2}%" if isinstance(t2, (int, float)) else t2
        t3s = f"{t3}%" if isinstance(t3, (int, float)) else t3
        flags_str = ", ".join(r.get("flags", [])) or "OK"
        lines.append(
            f"| {r['asset_key']} | {r['total_trades']} | {r['win_rate']:.1f}% | "
            f"{r['pnl_pips']:+.1f} | {r['profit_factor']:.2f} | {r['sharpe']:.2f} | "
            f"{r['max_drawdown_pips']:.1f} | {t1s} | {t2s} | {t3s} | {flags_str} |"
        )

    # Aggregate tier stats
    lines.append("\n## Aggregate Tier Summary\n")
    lines.append("| Tier | Total Trades | Avg WR% | Total PnL |")
    lines.append("|------|-------------|---------|-----------|")
    for tier in ["T1", "T2", "T3"]:
        t_trades = sum(r["tier_stats"].get(tier, {}).get("trades", 0) for r in all_results if r.get("tier_stats"))
        t_pnl = sum(r["tier_stats"].get(tier, {}).get("pnl", 0) for r in all_results if r.get("tier_stats"))
        tier_wrs = [r["tier_stats"][tier]["wr"] for r in all_results if r.get("tier_stats") and tier in r["tier_stats"]]
        avg_twr = sum(tier_wrs) / len(tier_wrs) if tier_wrs else 0
        lines.append(f"| {tier} | {t_trades} | {avg_twr:.1f}% | {t_pnl:+.1f}p |")

    # Per-pair detailed reports
    lines.append("\n## Detailed Per-Asset Reports\n")
    for r in sorted(all_results, key=lambda x: x["pnl_pips"], reverse=True):
        lines.append(f"### {r['asset_key']} — {r['name']}\n")
        lines.append(f"```\n{r['report_text']}\n```\n")

    lines.append(f"\n---\n*ST-ONLY backtest run @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | No P90 signals involved*")
    return "\n".join(lines)


# ── MAIN ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("SYMMETRY TRAP ONLY — MULTI-ASSET BACKTEST")
    print("=" * 60)
    print(f"Total assets in registry: {len(ASSET_CONFIGS)}")
    print(f"Assets: {', '.join(ASSET_CONFIGS.keys())}")

    # Check existing data
    print("\n--- Checking existing CSV data ---")
    data_map = get_existing_data()
    print(f"Found CSV data for {len(data_map)} assets: {', '.join(data_map.keys())}")

    missing = [k for k in ASSET_CONFIGS if k not in data_map]
    print(f"Missing data for {len(missing)} assets: {', '.join(missing)}")

    # Run backtests
    print("\n--- Running Symmetry Trap ONLY backtests ---")
    all_results: List[dict] = []
    run_errors: List[str] = []

    for asset_key in sorted(ASSET_CONFIGS.keys()):
        if asset_key not in data_map:
            continue

        csv_path = data_map[asset_key]
        print(f"\n>>> {asset_key}: {csv_path.name}")

        entry = run_asset_backtest(asset_key, csv_path)
        if entry is not None:
            all_results.append(entry)
        else:
            run_errors.append(asset_key)

    # Generate reports
    print("\n--- Generating reports ---")

    # JSON results
    json_data = {
        "generated": datetime.now().isoformat(),
        "engine": "Symmetry Trap (ST) ONLY — No P90",
        "total_assets_in_registry": len(ASSET_CONFIGS),
        "assets_tested": len(all_results),
        "assets_missing_data": missing,
        "assets_with_errors": run_errors,
        "summary": {
            "total_trades": sum(r["total_trades"] for r in all_results),
            "avg_wr": round(sum(r["win_rate"] for r in all_results) / len(all_results), 1) if all_results else 0,
            "combined_pips": round(sum(r["pnl_pips"] for r in all_results), 1),
        },
        "results": all_results,
    }
    json_path = REPORTS_DIR / "st_only_multi_asset_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, default=str)
    print(f"Saved JSON results to {json_path}")

    # Markdown summary
    md_report = generate_summary(all_results, missing)
    md_path = REPORTS_DIR / "st_only_multi_asset_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"Saved markdown report to {md_path}")

    # Final verification
    print("\n--- Verification ---")
    for r in all_results:
        flags = r.get("flags", [])
        if flags:
            print(f"  FLAG {r['asset_key']}: {', '.join(flags)}")
        else:
            print(f"  OK   {r['asset_key']}: WR={r['win_rate']:.1f}% | Trades={r['total_trades']}")

    print(f"\n=== COMPLETE: {len(all_results)}/{len(ASSET_CONFIGS)} assets backtested ===")

    # Print summary table to console
    print("\n\n" + "=" * 70)
    print("ST-ONLY MULTI-ASSET BACKTEST SUMMARY")
    print("=" * 70)
    for r in sorted(all_results, key=lambda x: x["pnl_pips"], reverse=True):
        print(f"  {r['asset_key']:10s} | {r['total_trades']:5d} tr | WR {r['win_rate']:5.1f}% | "
              f"PnL {r['pnl_pips']:+8.1f}p | PF {r['profit_factor']:.2f} | "
              f"TP_avg {r['avg_tp_distance_pips']:.1f}p | SL_avg {r['avg_sl_distance_pips']:.1f}p")
    print(f"\n{'':10s}   {sum(r['total_trades'] for r in all_results):5d} tr | "
          f"Total PnL {sum(r['pnl_pips'] for r in all_results):+.1f} pips | "
          f"Avg WR {sum(r['win_rate'] for r in all_results)/len(all_results) if all_results else 0:.1f}%")


if __name__ == "__main__":
    main()
