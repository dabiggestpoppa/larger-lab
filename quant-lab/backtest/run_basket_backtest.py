"""
CEREBUS ST BASKET BACKTEST RUNNER
==================================
Runs Symmetry Trap backtest for a basket of FX pairs.
Uses Nautilus Phase 0 ground truth engine (symmetry_trap_backtest.py).
Outputs per-pair reports + basket portfolio report + spread data.

Usage:
    python run_basket_backtest.py --basket EUR
    python run_basket_backtest.py --basket USD
    etc.
"""

from __future__ import annotations

import csv
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ── Path Setup ────────────────────────────────────────────────────────────
REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
QUANT_LAB = REPO_ROOT / "quant-lab"
DATA_DIR = QUANT_LAB / "data"
REPORTS_DIR = QUANT_LAB / "reports" / "baskets"
CONFIGS_DIR = QUANT_LAB / "configs"
ENGINES_DIR = QUANT_LAB / "engines"

sys.path.insert(0, str(CONFIGS_DIR))
sys.path.insert(0, str(ENGINES_DIR))

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, BacktestResult

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── BASKET DEFINITIONS ────────────────────────────────────────────────────
BASKETS = {
    "EUR": {
        "pairs": ["EURUSD", "EURGBP", "EURJPY", "EURAUD", "EURNZD", "EURCHF", "EURCAD"],
        "description": "EUR Basket — all EUR minor/cross pairs",
    },
    "GBP": {
        "pairs": ["GBPUSD", "EURGBP", "GBPJPY", "GBPAUD", "GBPNZD", "GBPCHF", "GBPCAD"],
        "description": "GBP Basket — all GBP minor/cross pairs (ALREADY DONE)",
    },
    "USD": {
        "pairs": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD"],
        "description": "USD Basket — all USD minor/cross pairs",
    },
    "JPY": {
        "pairs": ["EURJPY", "GBPJPY", "USDJPY", "AUDJPY", "NZDJPY", "CADJPY", "CHFJPY"],
        "description": "JPY Basket — all JPY cross pairs",
    },
    "AUD": {
        "pairs": ["EURAUD", "GBPAUD", "AUDUSD", "AUDNZD", "AUDJPY", "AUDCHF", "AUDCAD"],
        "description": "AUD Basket — all AUD minor/cross pairs",
    },
    "NZD": {
        "pairs": ["EURNZD", "GBPNZD", "NZDUSD", "AUDNZD", "NZDJPY", "NZDCHF", "NZDCAD"],
        "description": "NZD Basket — all NZD minor/cross pairs",
    },
    "CHF": {
        "pairs": ["EURCHF", "GBPCHF", "USDCHF", "AUDCHF", "NZDCHF", "CADCHF", "CHFJPY"],
        "description": "CHF Basket — all CHF minor/cross pairs",
    },
    "CAD": {
        "pairs": ["EURCAD", "GBPCAD", "USDCAD", "AUDCAD", "NZDCAD", "CADJPY", "CADCHF"],
        "description": "CAD Basket — all CAD minor/cross pairs",
    },
}


def find_csv(asset_key: str) -> Optional[Path]:
    """Find CSV file for an asset key."""
    # Pattern 1: {KEY}_M5.csv
    p1 = DATA_DIR / f"{asset_key}_M5.csv"
    if p1.exists():
        return p1
    # Pattern 2: {KEY}_PRO_M5*.csv
    candidates = sorted(DATA_DIR.glob(f"{asset_key}_PRO_M5*.csv"))
    if candidates:
        return max(candidates, key=lambda p: p.stat().st_size)
    # Pattern 3: {KEY}PRO_M5*.csv
    candidates = sorted(DATA_DIR.glob(f"{asset_key}PRO_M5*.csv"))
    if candidates:
        return max(candidates, key=lambda p: p.stat().st_size)
    # Pattern 4: Generic
    candidates = sorted(DATA_DIR.glob(f"{asset_key}*M5*.csv"))
    if candidates:
        return max(candidates, key=lambda p: p.stat().st_size)
    return None


def get_spread_data(csv_path: Path, sample_size: int = 5000) -> dict:
    """Extract spread statistics from CSV data."""
    spreads = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= sample_size:
                break
            try:
                spreads.append(float(row.get("spread", 0)))
            except (ValueError, TypeError):
                continue
    if not spreads:
        return {"avg_spread": 0, "max_spread": 0, "min_spread": 0, "median_spread": 0}
    spreads.sort()
    return {
        "avg_spread": round(sum(spreads) / len(spreads), 1),
        "max_spread": round(spreads[-1], 1),
        "min_spread": round(spreads[0], 1),
        "median_spread": round(spreads[len(spreads) // 2], 1),
    }


def run_pair_backtest(asset_key: str, csv_path: Path) -> Optional[dict]:
    """Run ST backtest for a single pair."""
    if asset_key not in ASSET_CONFIGS:
        print(f"  SKIP {asset_key}: no config in ASSET_CONFIGS")
        return None

    config = ASSET_CONFIGS[asset_key]
    pip_size = config["pip_value"]
    tier_config = config["tiers"]

    print(f"  Running {asset_key} | pip={pip_size} | {csv_path.name}")

    try:
        bt = SymmetryTrapBacktest(
            pip_size=pip_size,
            tier_config=tier_config,
            symbol=asset_key,
            config=config,
        )
        result: BacktestResult = bt.run_from_csv(str(csv_path))

        # Extract spread data
        spread_data = get_spread_data(csv_path)

        return {
            "asset": asset_key,
            "name": config.get("name", asset_key),
            "csv": csv_path.name,
            "trades": result.total_trades,
            "wr": round(result.win_rate, 1),
            "pnl_pips": round(result.total_pnl_pips, 1),
            "pf": round(result.profit_factor, 2) if result.profit_factor else 0,
            "sharpe": round(result.sharpe_ratio, 2) if result.sharpe_ratio else 0,
            "max_dd_pct": round(result.max_drawdown_pct, 1) if result.max_drawdown_pct else 0,
            "max_dd_pips": round(result.max_drawdown_pips, 1) if result.max_drawdown_pips else 0,
            "expectancy": round(result.expectancy_pips, 2) if result.expectancy_pips else 0,
            "wins": result.wins,
            "losses": result.losses,
            "kills": result.kills,
            "gross_profit": round(result.gross_profit, 1),
            "gross_loss": round(result.gross_loss, 1),
            "avg_win": round(result.avg_win_pips, 1),
            "avg_loss": round(result.avg_loss_pips, 1),
            "max_consec_wins": result.max_consec_wins,
            "max_consec_losses": result.max_consec_losses,
            "long_trades": result.long_trades,
            "long_wr": round(result.long_wr, 1) if result.long_trades > 0 else 0,
            "short_trades": result.short_trades,
            "short_wr": round(result.short_wr, 1) if result.short_trades > 0 else 0,
            "spread": spread_data,
            "data_bars": result.data_bars,
            "data_days": result.data_days,
        }
    except Exception as e:
        print(f"  ERROR {asset_key}: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_basket(basket_name: str) -> dict:
    """Run backtest for all pairs in a basket."""
    if basket_name not in BASKETS:
        print(f"Unknown basket: {basket_name}. Available: {list(BASKETS.keys())}")
        return {}

    basket = BASKETS[basket_name]
    pairs = basket["pairs"]

    print(f"\n{'='*60}")
    print(f"  CEREBUS ST BASKET BACKTEST — {basket_name}")
    print(f"  {basket['description']}")
    print(f"  Pairs: {pairs}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    results = {}
    missing = []

    for pair in pairs:
        csv_path = find_csv(pair)
        if csv_path is None:
            print(f"  MISSING DATA: {pair}")
            missing.append(pair)
            continue

        result = run_pair_backtest(pair, csv_path)
        if result:
            results[pair] = result

    # ── Generate Report ─────────────────────────────────────────────────
    report_path = REPORTS_DIR / f"{basket_name.lower()}_basket_report.md"
    json_path = REPORTS_DIR / f"{basket_name.lower()}_basket_results.json"

    # Save JSON
    with open(json_path, "w") as f:
        json.dump({
            "basket": basket_name,
            "description": basket["description"],
            "pairs": pairs,
            "missing_data": missing,
            "results": results,
            "generated": datetime.now().isoformat(),
        }, f, indent=2)

    # Generate Markdown Report
    total_trades = sum(r["trades"] for r in results.values())
    total_pnl = sum(r["pnl_pips"] for r in results.values())
    total_wins = sum(r["wins"] for r in results.values())
    total_losses = sum(r["losses"] for r in results.values())
    avg_wr = (total_wins / total_trades * 100) if total_trades > 0 else 0

    with open(report_path, "w") as f:
        f.write(f"# CEREBUS ST — {basket_name} Basket Report\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Basket:** {basket_name} ({basket['description']})\n")
        f.write(f"**Engine:** Symmetry Trap (Nautilus Phase 0 Ground Truth)\n\n")

        f.write("---\n\n")
        f.write("## Summary Table\n\n")
        f.write("| Asset | Trades | WR | PnL (pips) | PF | Sharpe | Max DD% | Avg Spread |\n")
        f.write("|-------|--------|-----|------------|-----|--------|---------|------------|\n")

        for pair in pairs:
            if pair in results:
                r = results[pair]
                spread_str = f"{r['spread']['avg_spread']}p" if r['spread']['avg_spread'] > 0 else "N/A"
                f.write(f"| {r['name']} | {r['trades']} | {r['wr']}% | {r['pnl_pips']} | {r['pf']} | {r['sharpe']} | {r['max_dd_pct']}% | {spread_str} |\n")
            else:
                f.write(f"| {pair} | — | — | — | — | — | — | — |\n")

        f.write(f"\n| **TOTAL** | **{total_trades}** | **{avg_wr:.1f}%** | **{total_pnl:.1f}** | — | — | — | — |\n")

        f.write("\n---\n\n")
        f.write("## Detailed Breakdown\n\n")
        f.write("| Asset | W | L | Kills | Gross Profit | Gross Loss | Avg Win | Avg Loss | Long WR | Short WR |\n")
        f.write("|-------|---|---|-------|--------------|------------|---------|----------|---------|----------|\n")
        for pair in pairs:
            if pair in results:
                r = results[pair]
                f.write(f"| {r['name']} | {r['wins']} | {r['losses']} | {r['kills']} | {r['gross_profit']} | {r['gross_loss']} | {r['avg_win']} | {r['avg_loss']} | {r['long_wr']}% | {r['short_wr']}% |\n")

        f.write("\n---\n\n")
        f.write("## Spread Data\n\n")
        f.write("| Asset | Avg | Median | Min | Max |\n")
        f.write("|-------|-----|--------|-----|-----|\n")
        for pair in pairs:
            if pair in results and results[pair]["spread"]["avg_spread"] > 0:
                s = results[pair]["spread"]
                f.write(f"| {pair} | {s['avg_spread']}p | {s['median_spread']}p | {s['min_spread']}p | {s['max_spread']}p |\n")

        if missing:
            f.write(f"\n---\n\n")
            f.write("## Missing Data\n\n")
            for m in missing:
                f.write(f"- {m}: no CSV data found\n")

        f.write(f"\n---\n\n")
        f.write(f"*Report generated by CEREBUS Basket Backtest Runner*\n")

    print(f"\n{'='*60}")
    print(f"  {basket_name} BASKET COMPLETE")
    print(f"  Pairs run: {len(results)}/{len(pairs)}")
    print(f"  Total trades: {total_trades}")
    print(f"  Avg WR: {avg_wr:.1f}%")
    print(f"  Total PnL: {total_pnl:.1f} pips")
    print(f"  Report: {report_path}")
    print(f"  JSON: {json_path}")
    print(f"{'='*60}\n")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CEREBUS ST Basket Backtest")
    parser.add_argument("--basket", required=True, help="Basket name (EUR/GBP/USD/JPY/AUD/NZD/CHF/CAD)")
    args = parser.parse_args()
    run_basket(args.basket.upper())
