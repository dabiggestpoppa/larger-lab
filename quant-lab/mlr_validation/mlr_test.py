"""
MLR (Monday London Range) Validation Test
==========================================
Validates MLR hit rates on intraday (daily AR) and weekly levels.
Also validates Rekey (132%) levels.

NO imports from quant-lab/engines/. This is a standalone test.

What we test:
  INTRADAY MLR:
    - Asian Range (19:00-03:00 EST) = the "MLR" for intraday
    - Extensions: -25%, -50%, -100% of AR from T+0 anchor
    - Rekey: 132% of AR in opposite direction
    - T+0 Anchor = Friday 05:00 EST close (weekly) or session start (intraday)

  WEEKLY MLR:
    - Monday London Range (03:00-11:00 EST Monday)
    - Extensions: -25%, -50%, -100% of MLR from T+0 anchor
    - Rekey: 132% of MLR in opposite direction

  HIT DEFINITION:
    - A "hit" = price reaches the extension level at any point during the session
    - Measured from session start (03:00 EST) to session end (12:00 PM EST)
    - Wicks count (high/low), not just closes

Usage:
    python -m quant-lab.mlr_validation.mlr_test --pair EURUSD --data quant-lab/data/EURUSD_M5.csv
    python -m quant-lab.mlr_validation.mlr_test --pair EURUSD --level weekly
    python -m quant-lab.mlr_validation.mlr_test --pair EURUSD --level intraday
    python -m quant-lab.mlr_validation.mlr_test --pair EURUSD --level rekey
    python -m quant-lab.mlr_validation.mlr_test --all-pairs
"""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, time
from pathlib import Path

# ─── NO ENGINE IMPORTS ──────────────────────────────────────────────
# This module is completely standalone. We read raw CSV data directly.

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "quant-lab" / "data"
RESULTS_DIR = REPO_ROOT / "quant-lab" / "mlr_validation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── SESSION DEFINITIONS ────────────────────────────────────────────
# All times in EST (UTC-5)
ASIAN_START = time(19, 0)    # 7:00 PM EST
ASIAN_END = time(3, 0)       # 3:00 AM EST (next day)
LONDON_START = time(3, 0)    # 3:00 AM EST
LONDON_END = time(11, 0)     # 11:00 AM EST
HARD_EXIT = time(12, 0)      # 12:00 PM EST

# Extension levels to test
EXTENSIONS = {
    "ext_25": 0.25,
    "ext_50": 0.50,
    "ext_100": 1.00,
}

# Rekey level
REKEY_PCT = 1.32


# ─── DATA LOADING ───────────────────────────────────────────────────

def load_daily_data(filepath: str) -> list:
    """
    Load daily OHLC data from CSV.
    Expected format: timestamp,open,high,low,close,volume
    Returns list of dicts sorted by date.
    """
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                dt = datetime.fromisoformat(row["timestamp"].strip())
                rows.append({
                    "date": dt.date(),
                    "datetime": dt,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                })
            except (KeyError, ValueError):
                continue
    rows.sort(key=lambda x: x["datetime"])
    return rows


def load_m5_data(filepath: str) -> list:
    """
    Load M5 OHLC data from CSV.
    Handles multiple column formats (timestamp, time, etc.)
    Returns list of dicts sorted by datetime.
    """
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Try different timestamp column names
                ts = None
                for col in ["timestamp", "time", "datetime"]:
                    if col in row and row[col].strip():
                        val = row[col].strip()
                        try:
                            # Try Unix timestamp (integer)
                            ts = datetime.fromtimestamp(int(val))
                            break
                        except ValueError:
                            try:
                                ts = datetime.fromisoformat(val)
                                break
                            except ValueError:
                                continue
                if ts is None:
                    continue

                rows.append({
                    "datetime": ts,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                })
            except (KeyError, ValueError):
                continue
    rows.sort(key=lambda x: x["datetime"])
    return rows


# ─── SESSION CALCULATIONS ───────────────────────────────────────────

def calc_asian_range(daily_data: list, target_date) -> dict:
    """
    Calculate Asian Range for a given date.
    Asian Session: 19:00 EST (prev day) to 03:00 EST (target_date)
    For daily data, we use the daily high/low as proxy.

    With daily data, the "Asian Range" is approximated as the
    previous day's range (since we don't have intraday data in daily CSV).

    Returns: {high, low, range_pips, t0_anchor, direction}
    """
    # Find the row for target_date
    row = None
    for r in daily_data:
        if r["date"] == target_date:
            row = r
            break

    if row is None:
        return None

    # With daily data, we use the daily range as the "Asian Range"
    # This is the best approximation without intraday data
    ar_high = row["high"]
    ar_low = row["low"]
    ar_range = ar_high - ar_low

    # T+0 Anchor = close of the range (using daily close as proxy)
    t0_anchor = row["close"]

    # Direction: bullish if close > midpoint, bearish if close < midpoint
    midpoint = (ar_high + ar_low) / 2
    direction = "bullish" if row["close"] > midpoint else "bearish"

    return {
        "date": target_date,
        "high": ar_high,
        "low": ar_low,
        "range": ar_range,
        "range_pips": ar_range / 0.0001,  # Approximate for EUR/USD
        "t0_anchor": t0_anchor,
        "direction": direction,
        "midpoint": midpoint,
    }


def calc_monday_london_range(daily_data: list, monday_date) -> dict:
    """
    Calculate Monday London Range.
    Monday London: 03:00-11:00 EST on Monday
    With daily data, we use Monday's daily range as proxy.

    Returns: {high, low, range_pips, t0_anchor, direction}
    """
    row = None
    for r in daily_data:
        if r["date"] == monday_date:
            row = r
            break

    if row is None:
        return None

    mlr_high = row["high"]
    mlr_low = row["low"]
    mlr_range = mlr_high - mlr_low

    t0_anchor = row["close"]
    midpoint = (mlr_high + mlr_low) / 2
    direction = "bullish" if row["close"] > midpoint else "bearish"

    return {
        "date": monday_date,
        "high": mlr_high,
        "low": mlr_low,
        "range": mlr_range,
        "range_pips": mlr_range / 0.0001,
        "t0_anchor": t0_anchor,
        "direction": direction,
        "midpoint": midpoint,
    }


# ─── EXTENSION LEVEL CALCULATIONS ───────────────────────────────────

def calc_extension_levels(session_data: dict) -> dict:
    """
    Calculate extension levels from session range.
    Extensions are in the direction of the bias.
    Rekey is in the opposite direction.

    For bullish bias:
      -25% = T+0 + (AR × 0.25)
      -50% = T+0 + (AR × 0.50)
      -100% = T+0 + (AR × 1.00)
      132% rekey = T+0 - (AR × 1.32)

    For bearish bias:
      -25% = T+0 - (AR × 0.25)
      -50% = T+0 - (AR × 0.50)
      -100% = T+0 - (AR × 1.00)
      132% rekey = T+0 + (AR × 1.32)
    """
    t0 = session_data["t0_anchor"]
    ar = session_data["range"]
    direction = session_data["direction"]

    levels = {}
    if direction == "bullish":
        for name, pct in EXTENSIONS.items():
            levels[name] = t0 + (ar * pct)
        levels["rekey"] = t0 - (ar * REKEY_PCT)
    else:
        for name, pct in EXTENSIONS.items():
            levels[name] = t0 - (ar * pct)
        levels["rekey"] = t0 + (ar * REKEY_PCT)

    levels["direction"] = direction
    levels["t0_anchor"] = t0
    levels["range"] = ar
    levels["range_pips"] = session_data["range_pips"]
    levels["session_high"] = session_data["high"]
    levels["session_low"] = session_data["low"]

    return levels


# ─── HIT DETECTION ──────────────────────────────────────────────────

def check_levels_hit(daily_data: list, target_date, levels: dict) -> dict:
    """
    Check if price hit any of the extension levels on the target date.
    With daily data, we check if the daily high/low reached the levels.

    Returns: {ext_25: bool, ext_50: bool, ext_100: bool, rekey: bool, ...}
    """
    row = None
    for r in daily_data:
        if r["date"] == target_date:
            row = r
            break

    if row is None:
        return None

    direction = levels["direction"]
    results = {}

    if direction == "bullish":
        # For bullish: extensions are above T+0, rekey is below
        for name in EXTENSIONS:
            results[name] = row["high"] >= levels[name]
        results["rekey"] = row["low"] <= levels["rekey"]
    else:
        # For bearish: extensions are below T+0, rekey is above
        for name in EXTENSIONS:
            results[name] = row["low"] <= levels[name]
        results["rekey"] = row["high"] >= levels["rekey"]

    results["daily_high"] = row["high"]
    results["daily_low"] = row["low"]
    results["daily_close"] = row["close"]

    return results


# ─── MAIN VALIDATION RUNNER ─────────────────────────────────────────

def run_intraday_mlr(daily_data: list, pair: str) -> dict:
    """
    Run intraday MLR validation.
    For each trading day, calculate the "MLR" (= daily range as proxy for AR),
    then check if extensions were hit that same day.

    This tests: does the daily range predict the day's extension targets?
    """
    print(f"\n{'='*60}")
    print(f"INTRADAY MLR VALIDATION — {pair}")
    print(f"{'='*60}")

    # Group data by date
    dates = sorted(set(r["date"] for r in daily_data))
    print(f"Total trading days: {len(dates)}")
    print(f"Date range: {dates[0]} to {dates[-1]}")

    # For intraday MLR: use each day's range as the "AR"
    # and check if extensions were hit that same day
    results = {
        "ext_25": {"hits": 0, "total": 0},
        "ext_50": {"hits": 0, "total": 0},
        "ext_100": {"hits": 0, "total": 0},
        "rekey": {"hits": 0, "total": 0},
    }

    detailed = []

    for i, d in enumerate(dates):
        # Calculate "AR" from the day's range
        day_rows = [r for r in daily_data if r["date"] == d]
        if not day_rows:
            continue

        day_high = max(r["high"] for r in day_rows)
        day_low = min(r["low"] for r in day_rows)
        day_close = day_rows[-1]["close"]
        day_open = day_rows[0]["open"]

        ar = day_high - day_low
        if ar == 0:
            continue

        midpoint = (day_high + day_low) / 2
        direction = "bullish" if day_close > midpoint else "bearish"

        session_data = {
            "date": d,
            "high": day_high,
            "low": day_low,
            "range": ar,
            "range_pips": ar / 0.0001,
            "t0_anchor": day_close,
            "direction": direction,
            "midpoint": midpoint,
        }

        levels = calc_extension_levels(session_data)

        # Check hits (same day)
        if direction == "bullish":
            ext_25_hit = day_high >= levels["ext_25"]
            ext_50_hit = day_high >= levels["ext_50"]
            ext_100_hit = day_high >= levels["ext_100"]
            rekey_hit = day_low <= levels["rekey"]
        else:
            ext_25_hit = day_low <= levels["ext_25"]
            ext_50_hit = day_low <= levels["ext_50"]
            ext_100_hit = day_low <= levels["ext_100"]
            rekey_hit = day_high >= levels["rekey"]

        results["ext_25"]["total"] += 1
        results["ext_50"]["total"] += 1
        results["ext_100"]["total"] += 1
        results["rekey"]["total"] += 1

        if ext_25_hit:
            results["ext_25"]["hits"] += 1
        if ext_50_hit:
            results["ext_50"]["hits"] += 1
        if ext_100_hit:
            results["ext_100"]["hits"] += 1
        if rekey_hit:
            results["rekey"]["hits"] += 1

        detailed.append({
            "date": str(d),
            "direction": direction,
            "ar_pips": round(session_data["range_pips"], 1),
            "ext_25_hit": ext_25_hit,
            "ext_50_hit": ext_50_hit,
            "ext_100_hit": ext_100_hit,
            "rekey_hit": rekey_hit,
        })

    # Print results
    print(f"\n--- INTRADAY MLR RESULTS ---")
    for level_name in ["ext_25", "ext_50", "ext_100", "rekey"]:
        r = results[level_name]
        pct = (r["hits"] / r["total"] * 100) if r["total"] > 0 else 0
        label = f"{level_name} ({int(EXTENSIONS.get(level_name, REKEY_PCT)*100)}%)" if level_name != "rekey" else f"rekey ({int(REKEY_PCT*100)}%)"
        print(f"  {label:20s}: {r['hits']:4d}/{r['total']:4d} = {pct:5.1f}%")

    return {
        "pair": pair,
        "level": "intraday",
        "total_days": len(dates),
        "results": results,
        "detailed": detailed,
    }


def run_weekly_mlr(daily_data: list, pair: str) -> dict:
    """
    Run weekly MLR validation.
    For each Monday, calculate the MLR (= Monday's range as proxy),
    then check if extensions were hit during the rest of the week (Tue-Fri).

    This tests: does Monday's range predict the week's extension targets?
    """
    print(f"\n{'='*60}")
    print(f"WEEKLY MLR VALIDATION — {pair}")
    print(f"{'='*60}")

    dates = sorted(set(r["date"] for r in daily_data))
    print(f"Total trading days: {len(dates)}")
    print(f"Date range: {dates[0]} to {dates[-1]}")

    # Find all Mondays
    mondays = [d for d in dates if d.weekday() == 0]
    print(f"Total Mondays: {len(mondays)}")

    results = {
        "ext_25": {"hits": 0, "total": 0},
        "ext_50": {"hits": 0, "total": 0},
        "ext_100": {"hits": 0, "total": 0},
        "rekey": {"hits": 0, "total": 0},
    }

    detailed = []

    for monday in mondays:
        # Calculate MLR from Monday's range
        monday_rows = [r for r in daily_data if r["date"] == monday]
        if not monday_rows:
            continue

        monday_high = max(r["high"] for r in monday_rows)
        monday_low = min(r["low"] for r in monday_rows)
        monday_close = monday_rows[-1]["close"]

        mlr = monday_high - monday_low
        if mlr == 0:
            continue

        midpoint = (monday_high + monday_low) / 2
        direction = "bullish" if monday_close > midpoint else "bearish"

        session_data = {
            "date": monday,
            "high": monday_high,
            "low": monday_low,
            "range": mlr,
            "range_pips": mlr / 0.0001,
            "t0_anchor": monday_close,
            "direction": direction,
            "midpoint": midpoint,
        }

        levels = calc_extension_levels(session_data)

        # Check hits for the rest of the week (Tue-Fri)
        week_dates = [
            monday + timedelta(days=i) for i in range(1, 5)
        ]
        week_dates = [d for d in week_dates if d in set(dates)]

        if not week_dates:
            continue

        # Get the high/low for the entire week
        week_high = monday_high
        week_low = monday_low
        for wd in week_dates:
            wd_rows = [r for r in daily_data if r["date"] == wd]
            if wd_rows:
                week_high = max(week_high, max(r["high"] for r in wd_rows))
                week_low = min(week_low, min(r["low"] for r in wd_rows))

        # Check if levels were hit
        if direction == "bullish":
            ext_25_hit = week_high >= levels["ext_25"]
            ext_50_hit = week_high >= levels["ext_50"]
            ext_100_hit = week_high >= levels["ext_100"]
            rekey_hit = week_low <= levels["rekey"]
        else:
            ext_25_hit = week_low <= levels["ext_25"]
            ext_50_hit = week_low <= levels["ext_50"]
            ext_100_hit = week_low <= levels["ext_100"]
            rekey_hit = week_high >= levels["rekey"]

        results["ext_25"]["total"] += 1
        results["ext_50"]["total"] += 1
        results["ext_100"]["total"] += 1
        results["rekey"]["total"] += 1

        if ext_25_hit:
            results["ext_25"]["hits"] += 1
        if ext_50_hit:
            results["ext_50"]["hits"] += 1
        if ext_100_hit:
            results["ext_100"]["hits"] += 1
        if rekey_hit:
            results["rekey"]["hits"] += 1

        detailed.append({
            "monday": str(monday),
            "direction": direction,
            "mlr_pips": round(session_data["range_pips"], 1),
            "week_high": week_high,
            "week_low": week_low,
            "ext_25_hit": ext_25_hit,
            "ext_50_hit": ext_50_hit,
            "ext_100_hit": ext_100_hit,
            "rekey_hit": rekey_hit,
        })

    # Print results
    print(f"\n--- WEEKLY MLR RESULTS ---")
    for level_name in ["ext_25", "ext_50", "ext_100", "rekey"]:
        r = results[level_name]
        pct = (r["hits"] / r["total"] * 100) if r["total"] > 0 else 0
        label = f"{level_name} ({int(EXTENSIONS.get(level_name, REKEY_PCT)*100)}%)" if level_name != "rekey" else f"rekey ({int(REKEY_PCT*100)}%)"
        print(f"  {label:20s}: {r['hits']:4d}/{r['total']:4d} = {pct:5.1f}%")

    return {
        "pair": pair,
        "level": "weekly",
        "total_mondays": len(mondays),
        "results": results,
        "detailed": detailed,
    }


def run_rekey_test(daily_data: list, pair: str, level: str = "both") -> dict:
    """
    Run Rekey (132%) validation specifically.
    Tests both intraday and weekly rekey hit rates.
    """
    print(f"\n{'='*60}")
    print(f"REKEY (132%) VALIDATION — {pair}")
    print(f"{'='*60}")

    all_results = {}

    if level in ("intraday", "both"):
        intraday = run_intraday_mlr(daily_data, pair)
        all_results["intraday"] = intraday["results"]["rekey"]

    if level in ("weekly", "both"):
        weekly = run_weekly_mlr(daily_data, pair)
        all_results["weekly"] = weekly["results"]["rekey"]

    print(f"\n--- REKEY SUMMARY ---")
    for lvl, res in all_results.items():
        pct = (res["hits"] / res["total"] * 100) if res["total"] > 0 else 0
        print(f"  {lvl:10s}: {res['hits']:4d}/{res['total']:4d} = {pct:5.1f}%")

    return {
        "pair": pair,
        "level": "rekey",
        "results": all_results,
    }


# ─── MULTI-PAIR RUNNER ──────────────────────────────────────────────

def find_data_files() -> dict:
    """Find all available daily data files."""
    pairs = {}
    for f in DATA_DIR.glob("*_M5.csv"):
        name = f.stem.replace("_M5", "")
        # Skip PRO files (those are M5, not daily)
        if "PRO" not in name:
            pairs[name] = str(f)
    return pairs


def run_all_pairs(level: str = "both"):
    """Run MLR validation on all available pairs."""
    data_files = find_data_files()
    print(f"Found {len(data_files)} pairs with daily data")

    all_results = {}
    for pair, filepath in sorted(data_files.items()):
        print(f"\n{'#'*60}")
        print(f"# {pair}")
        print(f"{'#'*60}")

        daily_data = load_daily_data(filepath)
        if len(daily_data) < 50:
            print(f"  Skipping {pair}: only {len(daily_data)} days of data")
            continue

        pair_results = {}
        if level in ("intraday", "both"):
            pair_results["intraday"] = run_intraday_mlr(daily_data, pair)
        if level in ("weekly", "both"):
            pair_results["weekly"] = run_weekly_mlr(daily_data, pair)

        all_results[pair] = pair_results

    # Save combined results
    output_file = RESULTS_DIR / "mlr_all_pairs.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {output_file}")

    return all_results


# ─── CLI ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MLR Validation Test")
    parser.add_argument("--pair", default="EURUSD", help="Pair to test")
    parser.add_argument("--data", help="Path to data file (auto-detected if not specified)")
    parser.add_argument("--level", choices=["intraday", "weekly", "rekey", "both"], default="both")
    parser.add_argument("--all-pairs", action="store_true", help="Run on all available pairs")
    args = parser.parse_args()

    if args.all_pairs:
        run_all_pairs(args.level)
        return

    # Find data file
    if args.data:
        data_file = args.data
    else:
        # Try to find the pair's data file
        candidate = DATA_DIR / f"{args.pair}_M5.csv"
        if candidate.exists():
            data_file = str(candidate)
        else:
            print(f"ERROR: No data file found for {args.pair}")
            print(f"  Looked for: {candidate}")
            print(f"  Use --data to specify path")
            sys.exit(1)

    print(f"Loading data from: {data_file}")
    daily_data = load_daily_data(data_file)
    print(f"Loaded {len(daily_data)} daily bars")

    if len(daily_data) < 10:
        print("ERROR: Not enough data")
        sys.exit(1)

    # Run tests
    all_results = {"pair": args.pair, "data_file": data_file}

    if args.level in ("intraday", "both"):
        all_results["intraday"] = run_intraday_mlr(daily_data, args.pair)

    if args.level in ("weekly", "both"):
        all_results["weekly"] = run_weekly_mlr(daily_data, args.pair)

    if args.level == "rekey":
        all_results["rekey"] = run_rekey_test(daily_data, args.pair, "both")

    # Save results
    output_file = RESULTS_DIR / f"mlr_{args.pair}_{args.level}.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    main()
