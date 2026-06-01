# -*- coding: utf-8 -*-
"""
Phase 0: Ground Truth Calibration — 19-Asset Nautilus Sweep
============================================================
Runs Symmetry Trap + P90 across all assets with available data.
Outputs: nautilus_ground_truth_matrix.json + markdown report.

Strategy logic: LOCKED. No changes. Pure execution wrapper.
"""
import sys, os, json, time
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab')
from datetime import datetime
from pathlib import Path
from decimal import Decimal

import pytz
import pandas as pd

from run_cerebus_backtest_fixed import run_backtest, find_csv, ASSET_CONFIGS

EST = pytz.timezone('US/Eastern')
REPORTS_DIR = Path('quant-lab/reports')

# Asset list (skip NAS100 — no CSV data available)
ALL_ASSETS = [
    # FX Majors
    "EURUSD", "GBPUSD", "USDCHF", "USDJPY", "AUDUSD", "NZDUSD",
    # FX Crosses
    "GBPJPY", "GBPCHF", "GBPAUD", "GBPNZD", "CHFJPY",
    # Metals
    "XAUUSD", "XAGUSD",
    # Crypto
    "BTCUSD", "ETHUSD",
    # Indices
    "US500", "DE30", "FR40", "HK50",
]

STRATEGIES = ["symmetry_trap", "p90"]


def check_data_availability():
    available = []
    missing = []
    for symbol in ALL_ASSETS:
        csv_path = find_csv(symbol)
        if csv_path:
            size_mb = csv_path.stat().st_size / (1024 * 1024)
            available.append((symbol, csv_path, size_mb))
            print(f"  [OK] {symbol}: {csv_path.name} ({size_mb:.1f} MB)")
        else:
            missing.append(symbol)
            print(f"  [MISSING] {symbol}: NO CSV FOUND")
    return available, missing


def run_sweep():
    print("=" * 70)
    print("  PHASE 0: GROUND TRUTH CALIBRATION — 19-ASSET NAUTILUS SWEEP")
    print(f"  Started: {datetime.now(EST).strftime('%Y-%m-%d %H:%M:%S EST')}")
    print("=" * 70)

    print("\n[1/3] Checking data availability...")
    available, missing = check_data_availability()
    print(f"\n  Available: {len(available)} | Missing: {len(missing)}")
    if missing:
        print(f"  Missing: {', '.join(missing)}")

    print(f"\n[2/3] Running Nautilus backtests ({len(available)} assets x {len(STRATEGIES)} strategies)...")
    matrix = {}
    errors = []
    total = len(available) * len(STRATEGIES)
    done = 0

    for symbol, csv_path, size_mb in available:
        matrix[symbol] = {}
        for strategy in STRATEGIES:
            done += 1
            print(f"\n{'─' * 70}")
            print(f"  [{done}/{total}] {strategy.upper()} / {symbol} (CSV: {size_mb:.1f}MB)")
            print(f"{'─' * 70}")
            try:
                t0 = time.time()
                result = run_backtest(strategy, symbol, csv_path)
                elapsed = time.time() - t0

                if result:
                    trades = result.get("strategy_trades", 0)
                    wr = result.get("strategy_win_rate", 0.0)
                    pnl = result.get("strategy_pnl_pips", 0.0)
                    bars = result.get("bars", 0)
                    wins = result.get("strategy_wins", 0)
                    losses = result.get("strategy_losses", 0)

                    matrix[symbol][strategy] = {
                        "trades": trades,
                        "wins": wins,
                        "losses": losses,
                        "win_rate_pct": round(wr, 1),
                        "pnl_pips": round(pnl, 1),
                        "bars": bars,
                        "elapsed_sec": round(elapsed, 1),
                        "status": "OK"
                    }
                    print(f"  DONE: {trades} trades | {wr:.1f}% WR | {pnl:+.1f}p | {elapsed:.0f}s")
                else:
                    matrix[symbol][strategy] = {"status": "FAILED"}
                    errors.append(f"{strategy}/{symbol}: No result")
                    print(f"  FAILED")
            except Exception as e:
                matrix[symbol][strategy] = {"status": "ERROR", "error": str(e)}
                errors.append(f"{strategy}/{symbol}: {str(e)}")
                print(f"  ERROR: {e}")

    print(f"\n[3/3] Compiling ground truth matrix...")
    ground_truth = {
        "metadata": {
            "phase": "Phase 0 — Ground Truth Calibration",
            "timestamp": datetime.now(EST).strftime('%Y-%m-%d %H:%M:%S EST'),
            "engine": "Nautilus (locked)",
            "strategies": STRATEGIES,
            "assets_attempted": len(ALL_ASSETS),
            "assets_available": len(available),
            "assets_missing": missing,
            "errors": errors,
        },
        "matrix": matrix,
    }

    json_path = REPORTS_DIR / "nautilus_ground_truth_matrix.json"
    with open(json_path, 'w') as f:
        json.dump(ground_truth, f, indent=2, default=str)
    print(f"  Matrix saved: {json_path}")

    # Generate markdown report
    report_path = REPORTS_DIR / "PHASE0_GROUND_TRUTH_REPORT.md"
    lines = []
    lines.append("# PHASE 0: GROUND TRUTH CALIBRATION REPORT\n")
    lines.append(f"**Generated:** {datetime.now(EST).strftime('%Y-%m-%d %H:%M:%S EST')}  ")
    lines.append(f"**Engine:** Nautilus (locked physics, no strategy changes)  ")
    lines.append(f"**Assets Available:** {len(available)}/{len(ALL_ASSETS)}  ")
    if missing:
        lines.append(f"**Missing Data:** {', '.join(missing)}\n")

    # ST table
    lines.append("## Symmetry Trap (ST) — All Assets\n")
    lines.append("| Asset | Trades | WR | PnL (pips) | Wins | Losses | Bars | Status |")
    lines.append("|-------|--------|-----|-------------|------|--------|------|--------|")
    st_total_trades = 0
    st_total_pnl = 0.0
    st_assets_ok = 0
    for symbol, _, _ in available:
        data = matrix.get(symbol, {}).get("symmetry_trap", {})
        if data.get("status") == "OK":
            lines.append(f"| {symbol} | {data['trades']} | {data['win_rate_pct']:.1f}% | {data['pnl_pips']:+.1f} | {data['wins']} | {data['losses']} | {data['bars']} | OK |")
            st_total_trades += data['trades']
            st_total_pnl += data['pnl_pips']
            st_assets_ok += 1
        else:
            err = data.get("error", data.get("status", "?"))
            lines.append(f"| {symbol} | — | — | — | — | — | — | ERR: {err} |")

    lines.append(f"\n**ST Aggregate ({st_assets_ok} assets):** {st_total_trades} trades | +{st_total_pnl:+.1f} pips\n")

    # P90 table
    lines.append("## P90 Kinetic Engine — All Assets\n")
    lines.append("| Asset | Trades | WR | PnL (pips) | Wins | Losses | Bars | Status |")
    lines.append("|-------|--------|-----|-------------|------|--------|------|--------|")
    p90_total_trades = 0
    p90_total_pnl = 0.0
    p90_assets_ok = 0
    for symbol, _, _ in available:
        data = matrix.get(symbol, {}).get("p90", {})
        if data.get("status") == "OK":
            lines.append(f"| {symbol} | {data['trades']} | {data['win_rate_pct']:.1f}% | {data['pnl_pips']:+.1f} | {data['wins']} | {data['losses']} | {data['bars']} | OK |")
            p90_total_trades += data['trades']
            p90_total_pnl += data['pnl_pips']
            p90_assets_ok += 1
        else:
            err = data.get("error", data.get("status", "?"))
            lines.append(f"| {symbol} | — | — | — | — | — | — | ERR: {err} |")

    lines.append(f"\n**P90 Aggregate ({p90_assets_ok} assets):** {p90_total_trades} trades | +{p90_total_pnl:+.1f} pips\n")

    if errors:
        lines.append("## Errors\n")
        for e in errors:
            lines.append(f"- {e}")
        lines.append("")

    lines.append("---")
    lines.append(f"*Phase 0 Complete | {len(available) * len(STRATEGIES) - len(errors)}/{len(available) * len(STRATEGIES)} runs successful*")

    with open(report_path, 'w') as f:
        f.write("\n".join(lines))
    print(f"  Report saved: {report_path}")

    print(f"\n{'=' * 70}")
    print(f"  PHASE 0 COMPLETE")
    print(f"  ST: {st_total_trades} trades across {st_assets_ok} assets | +{st_total_pnl:+.1f} pips")
    print(f"  P90: {p90_total_trades} trades across {p90_assets_ok} assets | +{p90_total_pnl:+.1f} pips")
    print(f"  Errors: {len(errors)}")
    print(f"  Reports: {json_path.name}, {report_path.name}")
    print(f"{'=' * 70}")

    return ground_truth


if __name__ == "__main__":
    run_sweep()
