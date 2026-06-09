"""
MLR (Monday London Range) Validation Test v2
=============================================
Bidirectional extension hit rate validation.

Based on Excel Delivery Stats + Validation Checklist claims:
  - -25% extension hit rate: claimed 90%
  - -50% extension hit rate: claimed 82%
  - 132% rekey: claimed 94-95%

INTRADAY MLR:
  Range = Asian Session Range (19:00-03:00 EST, H1 candles)
  T+0 Anchor = 03:00 EST close (start of activation)
  Extensions measured from T+0 in BOTH directions:
    +25% = T+0 + (AR × 0.25)  |  -25% = T+0 - (AR × 0.25)
    +50% = T+0 + (AR × 0.50)  |  -50% = T+0 - (AR × 0.50)
    +100% = T+0 + (AR × 1.00) |  -100% = T+0 - (AR × 1.00)
  Rekey (132%) = opposite direction from extension extreme
  Session = 03:00-12:00 EST (activation window)
  Hit = wick (high/low) reaches level during session

WEEKLY MLR:
  Range = Monday London Range (03:00-11:00 EST Monday, H1 candles)
  T+0 Anchor = Monday 11:00 EST close
  Extensions measured from T+0 in BOTH directions (same as above)
  Rekey (132%) = opposite direction
  Session = Monday 11:00 EST through Friday close
  Hit = wick reaches level during the week

DATA SOURCE:
  Uses 5-min CSV files from quant-lab/data/
  Aggregates to H1 for session range calculation.

NO imports from quant-lab/engines/. Standalone test.
"""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, time, date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "quant-lab" / "data"
RESULTS_DIR = REPO_ROOT / "quant-lab" / "mlr_validation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── SESSION TIMES (EST / UTC-5) ────────────────────────────────────
# Asian Session: 19:00 EST (00:00 UTC) to 03:00 EST (08:00 UTC)
# London Session: 03:00 EST (08:00 UTC) to 11:00 EST (16:00 UTC)
# Activation Window: 03:00 EST to 12:00 EST (17:00 UTC)
# Hard Exit: 12:00 EST (17:00 UTC)

ASIAN_START_HOUR = 19    # 19:00 EST
ASIAN_END_HOUR = 3       # 03:00 EST (next day)
LONDON_END_HOUR = 11     # 11:00 EST
HARD_EXIT_HOUR = 12      # 12:00 EST

# Extension levels (bidirectional)
EXTENSIONS = {
    "ext_25": 0.25,
    "ext_50": 0.50,
    "ext_100": 1.00,
}
REKEY_PCT = 1.32


# ─── DATA LOADING ───────────────────────────────────────────────────

def load_m5_csv(filepath: str) -> list:
    """
    Load M5 OHLC data from CSV. Handles multiple column formats.
    Returns list of dicts with datetime, open, high, low, close.
    Sorted by datetime.
    """
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts = None
                for col in ["timestamp", "time", "datetime"]:
                    if col in row and row[col].strip():
                        val = row[col].strip()
                        try:
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

                o = float(row["open"])
                h = float(row["high"])
                l = float(row["low"])
                c = float(row["close"])

                # Skip zero/negative prices
                if o <= 0 or h <= 0 or l <= 0:
                    continue

                rows.append({
                    "datetime": ts,
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": c,
                    "date": ts.date(),
                    "hour": ts.hour,
                })
            except (KeyError, ValueError, TypeError):
                continue

    rows.sort(key=lambda x: x["datetime"])
    return rows


def find_data_file(pair: str) -> str:
    """Find the best M5 data file for a pair."""
    # Try different naming patterns
    patterns = [
        f"{pair}_M5.csv",
        f"{pair}PRO_M5.csv",
        f"{pair}PRO_M5_2023_2026.csv",
        f"{pair}PRO_M5_2023_2025.csv",
        f"{pair}M5.csv",
    ]
    for p in patterns:
        fp = DATA_DIR / p
        if fp.exists():
            return str(fp)

    # Try partial match
    for f in DATA_DIR.glob(f"*{pair}*M5*.csv"):
        return str(f)

    return None


# ─── SESSION RANGE CALCULATION ───────────────────────────────────────

def calc_session_range(m5_data: list, target_date: date, start_hour: int, end_hour: int) -> dict:
    """
    Calculate the high/low range for a specific session window.

    For Asian session (19:00-03:00):
      Uses bars from 19:00 previous day to 03:00 target_date

    For London session (03:00-11:00):
      Uses bars from 03:00 to 11:00 on target_date

    Returns: {high, low, range, t0_anchor, start_dt, end_dt} or None
    """
    bars = []

    if start_hour > end_hour:
        # Overnight session (Asian): 19:00 prev day → 03:00 target
        prev_date = target_date - timedelta(days=1)
        for bar in m5_data:
            d = bar["date"]
            h = bar["hour"]
            if d == prev_date and h >= start_hour:
                bars.append(bar)
            elif d == target_date and h < end_hour:
                bars.append(bar)
    else:
        # Same-day session (London): 03:00-11:00 target
        for bar in m5_data:
            if bar["date"] == target_date and start_hour <= bar["hour"] < end_hour:
                bars.append(bar)

    if len(bars) < 2:
        return None

    high = max(b["high"] for b in bars)
    low = min(b["low"] for b in bars)
    range_val = high - low

    if range_val <= 0:
        return None

    # T+0 Anchor = close of the last bar in the session
    t0_anchor = bars[-1]["close"]

    return {
        "date": target_date,
        "high": high,
        "low": low,
        "range": range_val,
        "t0_anchor": t0_anchor,
        "bar_count": len(bars),
        "start_hour": start_hour,
        "end_hour": end_hour,
    }


def calc_asian_range(m5_data: list, target_date: date) -> dict:
    """Calculate Asian Session Range (19:00 EST prev day → 03:00 EST target)."""
    return calc_session_range(m5_data, target_date, ASIAN_START_HOUR, ASIAN_END_HOUR)


def calc_london_range(m5_data: list, target_date: date) -> dict:
    """Calculate London Session Range (03:00-11:00 EST)."""
    return calc_session_range(m5_data, target_date, ASIAN_END_HOUR, LONDON_END_HOUR)


# ─── EXTENSION LEVELS (BIDIRECTIONAL) ───────────────────────────────

def calc_bidirectional_levels(session_data: dict) -> dict:
    """
    Calculate extension levels in BOTH directions from T+0 anchor.

    From the Excel:
      Range A = Asian Range (high - low)
      T+0 = anchor (session close)

      +25% = T+0 + (Range A × 0.25)
      +50% = T+0 + (Range A × 0.50)
      +100% = T+0 + (Range A × 1.00)

      -25% = T+0 - (Range A × 0.25)
      -50% = T+0 - (Range A × 0.50)
      -100% = T+0 - (Range A × 1.00)

      Rekey 132% = opposite direction from extension
        If +extension hit first: rekey = T+0 - (Range A × 1.32)
        If -extension hit first: rekey = T+0 + (Range A × 1.32)

    A level is "hit" if price reaches it at any point during the session window.
    """
    t0 = session_data["t0_anchor"]
    ar = session_data["range"]

    levels = {
        "t0_anchor": t0,
        "range": ar,
        "session_high": session_data["high"],
        "session_low": session_data["low"],
    }

    # Positive extensions (above T+0)
    for name, pct in EXTENSIONS.items():
        levels[f"+{name}"] = t0 + (ar * pct)

    # Negative extensions (below T+0)
    for name, pct in EXTENSIONS.items():
        levels[f"-{name}"] = t0 - (ar * pct)

    # Rekey levels (132% in opposite direction)
    levels["+rekey"] = t0 + (ar * REKEY_PCT)  # above T+0
    levels["-rekey"] = t0 - (ar * REKEY_PCT)  # below T+0

    return levels


# ─── HIT DETECTION ──────────────────────────────────────────────────

def check_intraday_hits(m5_data: list, target_date: date, levels: dict) -> dict:
    """
    Check if price hit extension levels during the activation window.
    Activation window: 03:00-12:00 EST on target_date.

    A "hit" = wick (high/low) reaches the level.
    """
    # Get bars for activation window (03:00-12:00 EST)
    act_bars = [
        b for b in m5_data
        if b["date"] == target_date and ASIAN_END_HOUR <= b["hour"] < HARD_EXIT_HOUR
    ]

    if len(act_bars) < 1:
        return None

    act_high = max(b["high"] for b in act_bars)
    act_low = min(b["low"] for b in act_bars)

    results = {}

    # Check positive extensions (need high >= level)
    for name in EXTENSIONS:
        level_key = f"+{name}"
        results[level_key] = act_high >= levels[level_key]

    # Check negative extensions (need low <= level)
    for name in EXTENSIONS:
        level_key = f"-{name}"
        results[level_key] = act_low <= levels[level_key]

    # Check rekey levels
    results["+rekey"] = act_high >= levels["+rekey"]
    results["-rekey"] = act_low <= levels["-rekey"]

    results["activation_high"] = act_high
    results["activation_low"] = act_low
    results["bar_count"] = len(act_bars)

    return results


def check_weekly_hits(m5_data: list, monday_date: date, levels: dict) -> dict:
    """
    Check if price hit extension levels during the week (Mon 11:00 EST - Fri close).
    """
    # Get bars for the week (Monday after 11:00 EST through Friday)
    week_dates = [monday_date + timedelta(days=i) for i in range(5)]

    week_bars = []
    for d in week_dates:
        for b in m5_data:
            if b["date"] == d:
                # Monday: only after 11:00 EST
                if d == monday_date and b["hour"] < LONDON_END_HOUR:
                    continue
                week_bars.append(b)

    if len(week_bars) < 1:
        return None

    week_high = max(b["high"] for b in week_bars)
    week_low = min(b["low"] for b in week_bars)

    results = {}

    for name in EXTENSIONS:
        level_key = f"+{name}"
        results[level_key] = week_high >= levels[level_key]

    for name in EXTENSIONS:
        level_key = f"-{name}"
        results[level_key] = week_low <= levels[level_key]

    results["+rekey"] = week_high >= levels["+rekey"]
    results["-rekey"] = week_low <= levels["-rekey"]

    results["week_high"] = week_high
    results["week_low"] = week_low
    results["bar_count"] = len(week_bars)

    return results


# ─── VALIDATION RUNNERS ──────────────────────────────────────────────

def run_intraday_mlr(m5_data: list, pair: str) -> dict:
    """
    Intraday MLR validation.
    For each trading day:
      1. Calculate Asian Range (19:00-03:00 EST)
      2. Calculate bidirectional extension levels from T+0
      3. Check if levels were hit during activation (03:00-12:00 EST)
    """
    print(f"\n{'='*60}")
    print(f"INTRADAY MLR — {pair}")
    print(f"{'='*60}")

    # Get all unique dates
    all_dates = sorted(set(b["date"] for b in m5_data))
    print(f"Data range: {all_dates[0]} to {all_dates[-1]}")
    print(f"Total bars: {len(m5_data)}")

    # Counters for each level (bidirectional)
    counts = {}
    for name in EXTENSIONS:
        counts[f"+{name}"] = {"hits": 0, "total": 0}
        counts[f"-{name}"] = {"hits": 0, "total": 0}
    counts["+rekey"] = {"hits": 0, "total": 0}
    counts["-rekey"] = {"hits": 0, "total": 0}

    # Also track combined (either direction hits)
    combined = {}
    for name in EXTENSIONS:
        combined[name] = {"hits": 0, "total": 0}
    combined["rekey"] = {"hits": 0, "total": 0}

    detailed = []
    skipped = 0

    for d in all_dates:
        # Step 1: Calculate Asian Range
        ar = calc_asian_range(m5_data, d)
        if ar is None:
            skipped += 1
            continue

        # Step 2: Calculate levels
        levels = calc_bidirectional_levels(ar)

        # Step 3: Check hits during activation window
        hits = check_intraday_hits(m5_data, d, levels)
        if hits is None:
            skipped += 1
            continue

        # Count results
        day_result = {"date": str(d), "ar": ar["range"], "t0": ar["t0_anchor"]}

        for name in EXTENSIONS:
            pos_key = f"+{name}"
            neg_key = f"-{name}"

            counts[pos_key]["total"] += 1
            counts[neg_key]["total"] += 1

            pos_hit = hits[pos_key]
            neg_hit = hits[neg_key]

            if pos_hit:
                counts[pos_key]["hits"] += 1
            if neg_hit:
                counts[neg_key]["hits"] += 1

            # Combined: either direction
            combined[name]["total"] += 1
            if pos_hit or neg_hit:
                combined[name]["hits"] += 1

            day_result[pos_key] = pos_hit
            day_result[neg_key] = neg_hit

        # Rekey
        counts["+rekey"]["total"] += 1
        counts["-rekey"]["total"] += 1
        if hits["+rekey"]:
            counts["+rekey"]["hits"] += 1
        if hits["-rekey"]:
            counts["-rekey"]["hits"] += 1
        combined["rekey"]["total"] += 1
        if hits["+rekey"] or hits["-rekey"]:
            combined["rekey"]["hits"] += 1

        day_result["+rekey"] = hits["+rekey"]
        day_result["-rekey"] = hits["-rekey"]
        detailed.append(day_result)

    total_tested = counts["+ext_25"]["total"]

    print(f"\nDays tested: {total_tested} (skipped: {skipped})")
    print(f"\n--- BIDIRECTIONAL RESULTS ---")
    print(f"{'Level':<15} {'Direction':<12} {'Hits':>6} {'Total':>6} {'Rate':>8}")
    print("-" * 55)

    for name in EXTENSIONS:
        pct = int(EXTENSIONS[name] * 100)
        for direction in ["+", "-"]:
            key = f"{direction}{name}"
            c = counts[key]
            rate = (c["hits"] / c["total"] * 100) if c["total"] > 0 else 0
            print(f"{pct}% ext       {direction:>6}       {c['hits']:>6} {c['total']:>6} {rate:>7.1f}%")

    print(f"\n--- COMBINED (EITHER DIRECTION) ---")
    for name in EXTENSIONS:
        pct = int(EXTENSIONS[name] * 100)
        c = combined[name]
        rate = (c["hits"] / c["total"] * 100) if c["total"] > 0 else 0
        print(f"  {pct}% ext:  {c['hits']:>6}/{c['total']:>6} = {rate:>7.1f}%")

    print(f"\n--- REKEY (132%) ---")
    for direction in ["+", "-"]:
        key = f"{direction}rekey"
        c = counts[key]
        rate = (c["hits"] / c["total"] * 100) if c["total"] > 0 else 0
        print(f"  {direction}132%:  {c['hits']:>6}/{c['total']:>6} = {rate:>7.1f}%")
    c = combined["rekey"]
    rate = (c["hits"] / c["total"] * 100) if c["total"] > 0 else 0
    print(f"  combined: {c['hits']:>6}/{c['total']:>6} = {rate:>7.1f}%")

    return {
        "pair": pair,
        "level": "intraday",
        "total_tested": total_tested,
        "skipped": skipped,
        "counts": counts,
        "combined": combined,
        "detailed": detailed,
    }


def run_weekly_mlr(m5_data: list, pair: str) -> dict:
    """
    Weekly MLR validation.
    For each Monday:
      1. Calculate Monday London Range (03:00-11:00 EST)
      2. Calculate bidirectional extension levels from T+0
      3. Check if levels were hit during the week (Mon 11:00 - Fri close)
    """
    print(f"\n{'='*60}")
    print(f"WEEKLY MLR — {pair}")
    print(f"{'='*60}")

    all_dates = sorted(set(b["date"] for b in m5_data))

    # Find all Mondays
    mondays = [d for d in all_dates if d.weekday() == 0]
    print(f"Total Mondays: {len(mondays)}")
    print(f"Data range: {all_dates[0]} to {all_dates[-1]}")

    counts = {}
    for name in EXTENSIONS:
        counts[f"+{name}"] = {"hits": 0, "total": 0}
        counts[f"-{name}"] = {"hits": 0, "total": 0}
    counts["+rekey"] = {"hits": 0, "total": 0}
    counts["-rekey"] = {"hits": 0, "total": 0}

    combined = {}
    for name in EXTENSIONS:
        combined[name] = {"hits": 0, "total": 0}
    combined["rekey"] = {"hits": 0, "total": 0}

    detailed = []
    skipped = 0

    for monday in mondays:
        # Step 1: Calculate Monday London Range
        mlr = calc_london_range(m5_data, monday)
        if mlr is None:
            skipped += 1
            continue

        # Step 2: Calculate levels
        levels = calc_bidirectional_levels(mlr)

        # Step 3: Check hits during the week
        hits = check_weekly_hits(m5_data, monday, levels)
        if hits is None:
            skipped += 1
            continue

        # Count results
        for name in EXTENSIONS:
            pos_key = f"+{name}"
            neg_key = f"-{name}"
            counts[pos_key]["total"] += 1
            counts[neg_key]["total"] += 1
            if hits[pos_key]:
                counts[pos_key]["hits"] += 1
            if hits[neg_key]:
                counts[neg_key]["hits"] += 1
            combined[name]["total"] += 1
            if hits[pos_key] or hits[neg_key]:
                combined[name]["hits"] += 1

        counts["+rekey"]["total"] += 1
        counts["-rekey"]["total"] += 1
        if hits["+rekey"]:
            counts["+rekey"]["hits"] += 1
        if hits["-rekey"]:
            counts["-rekey"]["hits"] += 1
        combined["rekey"]["total"] += 1
        if hits["+rekey"] or hits["-rekey"]:
            combined["rekey"]["hits"] += 1

        detailed.append({
            "monday": str(monday),
            "mlr": mlr["range"],
            "t0": mlr["t0_anchor"],
        })

    total_tested = counts["+ext_25"]["total"]

    print(f"\nWeeks tested: {total_tested} (skipped: {skipped})")
    print(f"\n--- BIDIRECTIONAL RESULTS ---")
    print(f"{'Level':<15} {'Direction':<12} {'Hits':>6} {'Total':>6} {'Rate':>8}")
    print("-" * 55)

    for name in EXTENSIONS:
        pct = int(EXTENSIONS[name] * 100)
        for direction in ["+", "-"]:
            key = f"{direction}{name}"
            c = counts[key]
            rate = (c["hits"] / c["total"] * 100) if c["total"] > 0 else 0
            print(f"{pct}% ext       {direction:>6}       {c['hits']:>6} {c['total']:>6} {rate:>7.1f}%")

    print(f"\n--- COMBINED (EITHER DIRECTION) ---")
    for name in EXTENSIONS:
        pct = int(EXTENSIONS[name] * 100)
        c = combined[name]
        rate = (c["hits"] / c["total"] * 100) if c["total"] > 0 else 0
        print(f"  {pct}% ext:  {c['hits']:>6}/{c['total']:>6} = {rate:>7.1f}%")

    print(f"\n--- REKEY (132%) ---")
    for direction in ["+", "-"]:
        key = f"{direction}rekey"
        c = counts[key]
        rate = (c["hits"] / c["total"] * 100) if c["total"] > 0 else 0
        print(f"  {direction}132%:  {c['hits']:>6}/{c['total']:>6} = {rate:>7.1f}%")
    c = combined["rekey"]
    rate = (c["hits"] / c["total"] * 100) if c["total"] > 0 else 0
    print(f"  combined: {c['hits']:>6}/{c['total']:>6} = {rate:>7.1f}%")

    return {
        "pair": pair,
        "level": "weekly",
        "total_tested": total_tested,
        "skipped": skipped,
        "counts": counts,
        "combined": combined,
        "detailed": detailed,
    }


# ─── CLI ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MLR Validation v2 (Bidirectional)")
    parser.add_argument("--pair", default="EURUSD", help="Pair to test")
    parser.add_argument("--data", help="Path to M5 CSV file (auto-detected)")
    parser.add_argument("--level", choices=["intraday", "weekly", "both"], default="both")
    parser.add_argument("--all-pairs", action="store_true")
    args = parser.parse_args()

    if args.all_pairs:
        # Find all pairs with M5 data
        for f in sorted(DATA_DIR.glob("*M5*.csv")):
            pair_name = f.stem.replace("_M5", "").replace("PRO", "").replace("_2023_2026", "").replace("_2023_2025", "")
            print(f"\n{'#'*60}")
            print(f"# {pair_name}")
            print(f"{'#'*60}")
            m5_data = load_m5_csv(str(f))
            if len(m5_data) < 1000:
                print(f"  Skipping: only {len(m5_data)} bars")
                continue
            run_intraday_mlr(m5_data, pair_name)
            run_weekly_mlr(m5_data, pair_name)
        return

    # Single pair
    if args.data:
        data_file = args.data
    else:
        data_file = find_data_file(args.pair)
        if data_file is None:
            print(f"ERROR: No data file found for {args.pair}")
            sys.exit(1)

    print(f"Loading: {data_file}")
    m5_data = load_m5_csv(data_file)
    print(f"Loaded {len(m5_data)} bars")

    if len(m5_data) < 100:
        print("ERROR: Not enough data")
        sys.exit(1)

    all_results = {"pair": args.pair, "data_file": data_file}

    if args.level in ("intraday", "both"):
        all_results["intraday"] = run_intraday_mlr(m5_data, args.pair)

    if args.level in ("weekly", "both"):
        all_results["weekly"] = run_weekly_mlr(m5_data, args.pair)

    # Save results
    output_file = RESULTS_DIR / f"mlr_v2_{args.pair}_{args.level}.json"
    # Convert date objects for JSON serialization
    serializable = json.loads(json.dumps(all_results, default=str))
    with open(output_file, "w") as f:
        json.dump(serializable, f, indent=2)
    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    main()
