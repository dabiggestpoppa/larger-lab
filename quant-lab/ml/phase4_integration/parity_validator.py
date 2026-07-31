"""
Phase 4.4: Parity Validation
==============================
Compares live simulation metrics against backtest baseline.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# Benchmark reference (from CEREBUS FX v4 Manual)
BENCHMARKS = {
    "EURUSD":   {"wr": 88.4, "r": 1.18, "pf": 4.18, "dd": 0.8,  "trades_yr": 3842},
    "GBPUSD":   {"wr": 86.2, "r": 1.35, "pf": 3.82, "dd": 0.9,  "trades_yr": 4120},
    "USDCHF":   {"wr": 87.9, "r": 1.21, "pf": 4.82, "dd": 0.6,  "trades_yr": 3710},
    "USDJPY":   {"wr": 85.8, "r": 1.42, "pf": 4.58, "dd": 0.7,  "trades_yr": 3950},
    "AUDUSD":   {"wr": 87.5, "r": 1.25, "pf": 4.42, "dd": 0.75, "trades_yr": 3620},
    "NZDUSD":   {"wr": 85.7, "r": 1.25, "pf": 4.18, "dd": 0.85, "trades_yr": 3620},
    "CHFJPY":   {"wr": 84.8, "r": 1.55, "pf": 4.82, "dd": 4.8,  "trades_yr": 4210},
    "GBPJPY":   {"wr": 82.9, "r": 1.75, "pf": 4.82, "dd": 5.4,  "trades_yr": 4850},
    "GBPAUD":   {"wr": 83.5, "r": 1.62, "pf": 4.82, "dd": 5.6,  "trades_yr": 4450},
    "GBPNZD":   {"wr": 85.8, "r": 1.48, "pf": 4.82, "dd": 5.2,  "trades_yr": 4380},
    "GBPCHF":   {"wr": 88.1, "r": 1.38, "pf": 4.82, "dd": 4.6,  "trades_yr": 3890},
    "US500":    {"wr": 92.3, "r": 0.92, "pf": 4.82, "dd": 3.8,  "trades_yr": 2650},
    "DE30":     {"wr": 91.4, "r": 0.98, "pf": 4.82, "dd": 4.1,  "trades_yr": 2890},
    "FR40":     {"wr": 91.1, "r": 1.01, "pf": 4.82, "dd": 4.2,  "trades_yr": 2910},
    "USTEC100": {"wr": 90.2, "r": 1.08, "pf": 4.82, "dd": 4.8,  "trades_yr": 3120},
    "HK50":     {"wr": 89.2, "r": 1.12, "pf": 4.82, "dd": 5.1,  "trades_yr": 3450},
    "XAUUSD":   {"wr": 87.6, "r": 1.38, "pf": 4.82, "dd": 5.0,  "trades_yr": 3800},
    "XAGUSD":   {"wr": 85.4, "r": 1.52, "pf": 4.82, "dd": 5.8,  "trades_yr": 3400},
    "BTCUSD":   {"wr": 94.9, "r": 1.82, "pf": 4.82, "dd": 3.4,  "trades_yr": 2847},
    "ETHUSD":   {"wr": 79.2, "r": 2.05, "pf": 4.82, "dd": 7.8,  "trades_yr": 3150},
}

TOLERANCES = {"wr": 2.0, "r": 0.2, "pf_min": 2.5, "dd_buffer": 2.0, "trades_min_pct": 0.80}


def check_parity(asset: str, results: dict) -> dict:
    """
    Compare results against manual benchmarks.
    Returns pass/fail with diagnostic directives.
    """
    if asset not in BENCHMARKS:
        return {"status": "ERROR", "msg": f"No benchmark for {asset}"}

    bench = BENCHMARKS[asset]
    issues = []

    # Win Rate Check
    wr_delta = results.get("win_rate", 0) - bench["wr"]
    if abs(wr_delta) > TOLERANCES["wr"]:
        issues.append(f"WR {results['win_rate']:.1f}% vs target {bench['wr']}% (delta {wr_delta:+.1f}%)")

    # R-Multiple Check
    r_delta = results.get("avg_r", 0) - bench["r"]
    if abs(r_delta) > TOLERANCES["r"]:
        issues.append(f"Avg R {results['avg_r']:.2f} vs target {bench['r']} (delta {r_delta:+.2f})")

    # Profit Factor Floor
    if results.get("profit_factor", 0) < TOLERANCES["pf_min"]:
        issues.append(f"PF {results['profit_factor']:.2f} below floor {TOLERANCES['pf_min']}")

    # Max Drawdown Check
    max_dd_allowed = bench["dd"] + TOLERANCES["dd_buffer"]
    if results.get("max_dd", 0) > max_dd_allowed:
        issues.append(f"Max DD {results['max_dd']:.1f}% exceeds {max_dd_allowed:.1f}%")

    # Trade Count Check
    min_trades = int(bench["trades_yr"] * TOLERANCES["trades_min_pct"])
    if results.get("total_trades", 0) < min_trades:
        issues.append(f"Trades {results['total_trades']} below minimum {min_trades}")

    if not issues:
        return {"status": "PASS", "asset": asset, "msg": "All metrics within tolerance"}
    else:
        return {"status": "FAIL", "asset": asset, "issues": issues}


def validate_parity(backtest_metrics: dict, live_sim_metrics: dict, tolerance: float = 0.05) -> dict:
    """
    Compare live simulation vs backtest baseline.
    """
    wr_drift = abs(live_sim_metrics.get("win_rate", 0) - backtest_metrics.get("win_rate", 0)) / max(backtest_metrics.get("win_rate", 1), 1e-6)
    r_drift = abs(live_sim_metrics.get("avg_r", 0) - backtest_metrics.get("avg_r", 0)) / max(backtest_metrics.get("avg_r", 1), 1e-6)

    issues = []
    if wr_drift > tolerance:
        issues.append(f"Win Rate Drift: {wr_drift:.1%} exceeds {tolerance:.1%} tolerance.")
    if r_drift > tolerance:
        issues.append(f"R-Multiple Drift: {r_drift:.1%} exceeds {tolerance:.1%} tolerance.")

    if issues:
        return {"status": "DRIFT_DETECTED", "issues": issues}
    else:
        return {"status": "PARITY_CONFIRMED", "message": "Live simulation matches backtest expectations."}


def check_all_assets(results: dict[str, dict]) -> dict:
    """Run parity check on all assets."""
    summary = {"pass": [], "fail": [], "errors": []}
    for asset, metrics in results.items():
        result = check_parity(asset, metrics)
        if result["status"] == "PASS":
            summary["pass"].append(asset)
        elif result["status"] == "FAIL":
            summary["fail"].append(result)
        else:
            summary["errors"].append(result)

    print(f"\n📊 Parity Check: {len(summary['pass'])} PASS, {len(summary['fail'])} FAIL, {len(summary['errors'])} ERRORS")
    for f in summary["fail"]:
        print(f"  ❌ {f['asset']}: {f['issues']}")
    return summary
