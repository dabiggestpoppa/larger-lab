"""
CEREBUS FX v4.0 — Trigger/AU Sweep for Metals & Indices
========================================================
MAD Directive 2026-06-06: Run trigger/AU sweeps for XAU, XAG, US500, DE30, FR40, HK50.
"""

from __future__ import annotations

import json
import sys
import io
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)

REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
QUANT_LAB = REPO_ROOT / "quant-lab"
DATA_DIR = QUANT_LAB / "data"
REPORTS_DIR = QUANT_LAB / "reports"
CONFIGS_DIR = QUANT_LAB / "configs"
ENGINES_DIR = QUANT_LAB / "engines"

sys.path.insert(0, str(CONFIGS_DIR))
sys.path.insert(0, str(ENGINES_DIR))

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv

SWEEP_ASSETS = ["XAUUSD", "XAGUSD", "US500", "DE30", "FR40", "HK50"]

TRIGGER_MULTIPLIERS = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.7, 2.0, 2.5, 3.0]


def build_scaled_config(asset_key, mult):
    base = ASSET_CONFIGS[asset_key]
    tiers = {}
    for tn in ["T1", "T2", "T3"]:
        t = base["tiers"][tn]
        tiers[tn] = {
            "ar_max": round(t["ar_max"] * mult, 1),
            "au": round(t["au"] * mult, 1),
            "trigger": round(t["trigger"] * mult, 1),
        }
    return tiers


def run_sweep_asset(asset_key):
    csv_path = DATA_DIR / f"{asset_key}_M5.csv"
    if not csv_path.exists():
        candidates = sorted(DATA_DIR.glob(f"{asset_key}*.csv"))
        if candidates:
            csv_path = candidates[0]
        else:
            print(f"  ERROR: No CSV for {asset_key}", flush=True)
            return []

    base_config = ASSET_CONFIGS[asset_key]
    pip_value = base_config["pip_value"]
    base_t1 = base_config["tiers"]["T1"]["trigger"]

    print(f"  Loading {asset_key} data...", flush=True)
    bars, _ = load_m5_csv(str(csv_path), pip_size=pip_value)
    if not bars:
        print(f"  ERROR: No bars loaded", flush=True)
        return []

    n_days = (bars[-1].timestamp.date() - bars[0].timestamp.date()).days
    print(f"  {len(bars)} bars, {n_days} days, pip={pip_value}, base_t1={base_t1}", flush=True)

    results = []
    for i, mult in enumerate(TRIGGER_MULTIPLIERS):
        tier_config = build_scaled_config(asset_key, mult)
        t1_trigger = round(base_t1 * mult, 1)

        t0 = time.time()
        bt = SymmetryTrapBacktest(
            pip_size=pip_value,
            tier_config=tier_config,
            symbol=asset_key,
            config=None,
        )
        result = bt.run(bars)
        elapsed = time.time() - t0

        if result.total_trades == 0:
            print(f"  [{i+1:2d}/{len(TRIGGER_MULTIPLIERS)}] mult={mult:.1f} t1={t1_trigger:8.1f} | 0 trades ({elapsed:.1f}s)", flush=True)
            continue

        tr_per_day = result.total_trades / n_days if n_days > 0 else 0
        pf = result.profit_factor if result.profit_factor != float("inf") else 999.99

        entry = {
            "trades": result.total_trades,
            "days": n_days,
            "wr": round(result.win_rate, 2),
            "pnl": round(result.total_pnl_pips, 1),
            "pf": round(pf, 2),
            "avg_w": round(result.avg_win_pips, 2),
            "avg_l": round(result.avg_loss_pips, 2),
            "exp": round(result.expectancy_pips, 2),
            "max_dd": round(result.max_drawdown_pips, 1),
            "max_cw": result.max_consec_wins,
            "max_cl": result.max_consec_losses,
            "t1_trigger": t1_trigger,
            "tr_per_day": round(tr_per_day, 4),
            "multiplier": mult,
        }
        results.append(entry)

        print(f"  [{i+1:2d}/{len(TRIGGER_MULTIPLIERS)}] mult={mult:.1f} t1={t1_trigger:8.1f} | "
              f"trades={result.total_trades:5d} | WR={result.win_rate:5.1f}% | PF={pf:6.2f} | "
              f"pnl={result.total_pnl_pips:10.1f} | tr/d={tr_per_day:.3f} | {elapsed:.1f}s", flush=True)

    return results


def main():
    print("=" * 70, flush=True)
    print("CEREBUS Trigger/AU Sweep — Metals & Indices", flush=True)
    print(f"Assets: {', '.join(SWEEP_ASSETS)}", flush=True)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 70, flush=True)

    all_results = {}
    for asset_key in SWEEP_ASSETS:
        print(f"\n{'='*70}", flush=True)
        print(f"SWEEPING: {asset_key}", flush=True)
        print(f"{'='*70}", flush=True)
        results = run_sweep_asset(asset_key)
        if results:
            all_results[asset_key] = {"floor": results}

    output_path = REPORTS_DIR / "trigger_sweep_metals_indices.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to: {output_path}", flush=True)

    # Summary
    print("\n" + "=" * 70, flush=True)
    print("SWEEP SUMMARY", flush=True)
    print("=" * 70, flush=True)
    for asset_key, data in all_results.items():
        floor = data.get("floor", [])
        if not floor:
            print(f"\n{asset_key}: NO RESULTS", flush=True)
            continue

        best_trades = max(floor, key=lambda e: e["trades"])
        best_wr = max(floor, key=lambda e: e["wr"])
        best_pf = max(floor, key=lambda e: e["pf"] if e["pf"] < 999 else 0)
        best_pnl = max(floor, key=lambda e: e["pnl"])

        print(f"\n{asset_key}:", flush=True)
        print(f"  Max Trades: mult={best_trades['multiplier']:.1f} t1={best_trades['t1_trigger']:.1f} | "
              f"trades={best_trades['trades']} | WR={best_trades['wr']:.1f}% | "
              f"PF={best_trades['pf']:.2f} | tr/d={best_trades['tr_per_day']:.3f}", flush=True)
        print(f"  Max WR:     mult={best_wr['multiplier']:.1f} t1={best_wr['t1_trigger']:.1f} | "
              f"trades={best_wr['trades']} | WR={best_wr['wr']:.1f}% | "
              f"PF={best_wr['pf']:.2f} | tr/d={best_wr['tr_per_day']:.3f}", flush=True)
        print(f"  Max PF:     mult={best_pf['multiplier']:.1f} t1={best_pf['t1_trigger']:.1f} | "
              f"trades={best_pf['trades']} | WR={best_pf['wr']:.1f}% | "
              f"PF={best_pf['pf']:.2f} | tr/d={best_pf['tr_per_day']:.3f}", flush=True)
        print(f"  Max PnL:    mult={best_pnl['multiplier']:.1f} t1={best_pnl['t1_trigger']:.1f} | "
              f"trades={best_pnl['trades']} | WR={best_pnl['wr']:.1f}% | "
              f"PF={best_pnl['pf']:.2f} | tr/d={best_pnl['tr_per_day']:.3f}", flush=True)

    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)


if __name__ == "__main__":
    main()
