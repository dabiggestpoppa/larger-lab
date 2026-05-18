#!/usr/bin/env python3
"""
Stall-Harvest Multi-Pair Runner
Runs the standalone Stall_Harvest strategy on multiple pairs/TFs.
Does NOT require nautilus_trader — uses internal CSV parsing.
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# Add parent dir for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Internal CSV Parser (same as data_loader._parse_csv, no nautilus dep) ──

def _parse_csv_internal(filepath):
    """Parse forex.com CSV into DataFrame — no nautilus dependency."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        raw_lines = f.readlines()

    data_lines = [l for l in raw_lines[1:] if l.strip()]

    # Fix OX line wrapping
    fixed = []
    i = 0
    while i < len(data_lines):
        line = data_lines[i]
        if i + 1 < len(data_lines) and re.match(r'^\d{4}\.\d{2}\.\d{2}', data_lines[i + 1]):
            parts = line.strip().split()
            if len(parts) >= 8:
                fixed.append(line)
            else:
                merged = line.strip() + " " + data_lines[i + 1].strip()
                fixed.append(merged)
                i += 1
        else:
            fixed.append(line)
        i += 1

    records = []
    for line in fixed:
        parts = line.strip().split()
        if len(parts) < 7:
            continue
        try:
            date_str, time_str = parts[0], parts[1]
            open_val, high_val = float(parts[2]), float(parts[3])
            low_val, close_val = float(parts[4]), float(parts[5])
            ts = datetime.strptime(f"{date_str} {time_str}", "%Y.%m.%d %H:%M:%S")
            records.append({
                "timestamp": ts, "open": open_val, "high": high_val,
                "low": low_val, "close": close_val,
            })
        except (ValueError, IndexError):
            continue

    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)
    return df


# ── Import the strategy ─────────────────────────────────────────────────────

from stall_harvest import StallHarvestStrategy, StallHarvestConfig


# ── Runner ──────────────────────────────────────────────────────────────────

DOWNLOADS = Path(r"C:\Users\wifik\Downloads")
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

RUN_CONFIGS = [
    {"file": "EURUSD!_M5_202301020000_202605061250.csv", "pair": "EUR/USD", "tf": "M5"},
    # {"file": "EURUSD!_M1_202301020000_202605061253.csv", "pair": "EUR/USD", "tf": "M1"},
    {"file": "USDCHF!_M5_202301020000_202605061250.csv", "pair": "USD/CHF", "tf": "M5"},
    {"file": "GBPUSD!_M5_202301020000_202605061250.csv", "pair": "GBP/USD", "tf": "M5"},
    {"file": "USDJPY!_M5_202301020000_202605061250.csv", "pair": "USD/JPY", "tf": "M5"},
]


def run_single(config):
    """Run Stall_Harvest on a single pair/TF."""
    data_path = DOWNLOADS / config["file"]
    pair = config["pair"]
    tf = config["tf"]

    if not data_path.exists():
        print(f"  [FAIL] File not found: {data_path}", flush=True)
        return None

    print(f"\n{'='*60}", flush=True)
    print(f"[RUN] {pair} {tf} — {data_path.name}", flush=True)
    print(f"  Loading...", flush=True)

    df = _parse_csv_internal(data_path)
    if df.empty:
        print(f"  [FAIL] No data parsed!", flush=True)
        return None

    print(f"  Loaded {len(df):,} bars ({df.index[0]} → {df.index[-1]})", flush=True)

    strategy = StallHarvestStrategy()
    results = strategy.run_backtest(df, pair=pair)
    results["timeframe"] = tf
    results["data_file"] = config["file"]

    # Print summary
    print(f"\n  RESULTS:")
    print(f"  Total Trades:   {results.get('total_trades', 0)}")
    print(f"  Wins:           {results.get('wins', 0)} ({results.get('win_rate', 0)}%)")
    print(f"  Losses:         {results.get('losses', 0)}")
    print(f"  Total P&L:      {results.get('total_pnl_pips', 0)} pips")
    print(f"  Avg Win:        {results.get('avg_win_pips', 0)} pips")
    print(f"  Avg Loss:       {results.get('avg_loss_pips', 0)} pips")
    print(f"  Max Drawdown:   {results.get('max_drawdown_pips', 0)} pips")
    print(f"  Profit Factor:  {results.get('profit_factor', 0)}")

    if "by_session" in results:
        print(f"  By Session:")
        for s, data in results["by_session"].items():
            print(f"    {s:10s}: {data['trades']} trades | {data['win_rate']}% WR | {data['pnl_pips']} pips")

    if "by_exit_reason" in results:
        print(f"  By Exit Reason:")
        for reason, count in sorted(results["by_exit_reason"].items(), key=lambda x: -x[1]):
            print(f"    {reason:25s}: {count}")

    return results


def main():
    print("=" * 60, flush=True)
    print("STALL-HARVEST MULTI-PAIR VALIDATION", flush=True)
    print("=" * 60, flush=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_results = {}

    for config in RUN_CONFIGS:
        pair_tf = f"{config['pair'].replace('/', '')}_{config['tf']}"
        results = run_single(config)

        if results:
            # Save individual results
            fname = f"stall_harvest_{pair_tf}_{timestamp}.json"
            fpath = RESULTS_DIR / fname
            with open(fpath, "w") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"  [SAVE] Saved to {fpath}")
            all_results[pair_tf] = results

    # Save combined results
    combined_path = RESULTS_DIR / f"stall_harvest_all_{timestamp}.json"
    with open(combined_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    # Summary table
    print(f"\n{'='*60}")
    print(f"COMBINED SUMMARY")
    print(f"{'='*60}")
    print(f"{'Pair/TF':<15} {'Trades':>6} {'WR%':>6} {'P&L(p)':>8} {'PF':>5} {'MaxDD':>7}")
    print(f"{'─'*55}")
    for key, r in all_results.items():
        if r.get("total_trades", 0) > 0:
            print(f"{key:<15} {r['total_trades']:>6} {r['win_rate']:>6.1f} "
                  f"{r['total_pnl_pips']:>8.1f} {r['profit_factor']:>5.2f} "
                  f"{r['max_drawdown_pips']:>7.1f}")
        else:
            print(f"{key:<15} {'N/A':>6} {'N/A':>6} {'N/A':>8} {'N/A':>5} {'N/A':>7}")

    print(f"\n[SAVE] Combined results saved to {combined_path}")
    return all_results


if __name__ == "__main__":
    main()
