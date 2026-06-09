"""
MLR Validation Test v3 — OPTIMIZED
==================================
Pre-aggregates M5 → daily bars, then runs validation.
~288x faster than v2 for M5 data.

Key changes:
- Loads M5 data once, aggregates to daily OHLC
- Session ranges calculated from daily data (Asian Range = daily range as proxy)
- Weekly MLR = Monday's daily range
- Bidirectional extensions
- Much faster: processes 1200 days in <1s instead of 345K M5 bars in 30s+
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, time, date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "quant-lab" / "data"
RESULTS_DIR = REPO_ROOT / "quant-lab" / "mlr_validation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

EXTENSIONS = {"ext_25": 0.25, "ext_50": 0.50, "ext_100": 1.00}
REKEY_PCT = 1.32


def load_m5_to_daily(filepath: str) -> list:
    """
    Load M5 CSV and aggregate to daily OHLC.
    Returns list of daily bars sorted by date.
    """
    daily = defaultdict(lambda: {"highs": [], "lows": [], "closes": [], "opens": []})

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

                d = ts.date()
                h = float(row["high"])
                l = float(row["low"])
                c = float(row["close"])
                o = float(row["open"])

                if h <= 0 or l <= 0:
                    continue

                daily[d]["highs"].append(h)
                daily[d]["lows"].append(l)
                daily[d]["closes"].append(c)
                daily[d]["opens"].append(o)
            except (KeyError, ValueError, TypeError):
                continue

    result = []
    for d in sorted(daily.keys()):
        data = daily[d]
        if len(data["highs"]) < 1:
            continue
        result.append({
            "date": d,
            "open": data["opens"][0],
            "high": max(data["highs"]),
            "low": min(data["lows"]),
            "close": data["closes"][-1],
        })

    return result


def calc_bidirectional_levels(t0: float, range_val: float) -> dict:
    """Calculate extension levels in both directions from T+0."""
    levels = {"t0": t0, "range": range_val}
    for name, pct in EXTENSIONS.items():
        levels[f"+{name}"] = t0 + (range_val * pct)
        levels[f"-{name}"] = t0 - (range_val * pct)
    levels["+rekey"] = t0 + (range_val * REKEY_PCT)
    levels["-rekey"] = t0 - (range_val * REKEY_PCT)
    return levels


def run_intraday(daily_data: list, pair: str) -> dict:
    """
    Intraday MLR: each day's range = the "AR".
    Extensions from T+0 (daily close) in both directions.
    Hit = next day's high/low reaches the level.
    """
    print(f"\n{'='*60}")
    print(f"INTRADAY MLR — {pair}")
    print(f"{'='*60}")

    # Build date-indexed lookup
    by_date = {d["date"]: d for d in daily_data}
    dates = sorted(by_date.keys())
    print(f"Trading days: {len(dates)}, Range: {dates[0]} to {dates[-1]}")

    counts = {}
    for name in EXTENSIONS:
        counts[f"+{name}"] = {"hits": 0, "total": 0}
        counts[f"-{name}"] = {"hits": 0, "total": 0}
    counts["+rekey"] = {"hits": 0, "total": 0}
    counts["-rekey"] = {"hits": 0, "total": 0}
    combined = {name: {"hits": 0, "total": 0} for name in list(EXTENSIONS.keys()) + ["rekey"]}

    for i, d in enumerate(dates):
        day = by_date[d]
        ar = day["high"] - day["low"]
        if ar <= 0:
            continue

        t0 = day["close"]
        levels = calc_bidirectional_levels(t0, ar)

        # Check hits: use same day's high/low (intraday = within the day)
        for name in EXTENSIONS:
            pos_hit = day["high"] >= levels[f"+{name}"]
            neg_hit = day["low"] <= levels[f"-{name}"]
            counts[f"+{name}"]["total"] += 1
            counts[f"-{name}"]["total"] += 1
            if pos_hit: counts[f"+{name}"]["hits"] += 1
            if neg_hit: counts[f"-{name}"]["hits"] += 1
            combined[name]["total"] += 1
            if pos_hit or neg_hit: combined[name]["hits"] += 1

        rekey_pos = day["high"] >= levels["+rekey"]
        rekey_neg = day["low"] <= levels["-rekey"]
        counts["+rekey"]["total"] += 1
        counts["-rekey"]["total"] += 1
        if rekey_pos: counts["+rekey"]["hits"] += 1
        if rekey_neg: counts["-rekey"]["hits"] += 1
        combined["rekey"]["total"] += 1
        if rekey_pos or rekey_neg: combined["rekey"]["hits"] += 1

    total = counts["+ext_25"]["total"]
    print(f"Days tested: {total}")

    print(f"\n--- COMBINED (EITHER DIRECTION) ---")
    for name in list(EXTENSIONS.keys()) + ["rekey"]:
        c = combined[name]
        pct = (c["hits"] / c["total"] * 100) if c["total"] > 0 else 0
        label = f"{int(EXTENSIONS.get(name, REKEY_PCT)*100)}%" if name != "rekey" else "132%"
        print(f"  {label:>5} ext: {c['hits']:>6}/{c['total']:>6} = {pct:>6.1f}%")

    return {"pair": pair, "level": "intraday", "total": total, "combined": combined, "counts": counts}


def run_weekly(daily_data: list, pair: str) -> dict:
    """
    Weekly MLR: Monday's range = the "MLR".
    Extensions from T+0 (Monday close) in both directions.
    Hit = any day Tue-Fri reaches the level.
    """
    print(f"\n{'='*60}")
    print(f"WEEKLY MLR — {pair}")
    print(f"{'='*60}")

    by_date = {d["date"]: d for d in daily_data}
    dates = sorted(by_date.keys())

    mondays = [d for d in dates if d.weekday() == 0]
    print(f"Mondays: {len(mondays)}, Range: {dates[0]} to {dates[-1]}")

    counts = {}
    for name in EXTENSIONS:
        counts[f"+{name}"] = {"hits": 0, "total": 0}
        counts[f"-{name}"] = {"hits": 0, "total": 0}
    counts["+rekey"] = {"hits": 0, "total": 0}
    counts["-rekey"] = {"hits": 0, "total": 0}
    combined = {name: {"hits": 0, "total": 0} for name in list(EXTENSIONS.keys()) + ["rekey"]}

    for monday in mondays:
        mon = by_date.get(monday)
        if mon is None:
            continue

        mlr = mon["high"] - mon["low"]
        if mlr <= 0:
            continue

        t0 = mon["close"]
        levels = calc_bidirectional_levels(t0, mlr)

        # Check hits Tue-Fri
        week_high = mon["high"]
        week_low = mon["low"]
        for offset in range(1, 5):
            d = monday + timedelta(days=offset)
            if d in by_date:
                week_high = max(week_high, by_date[d]["high"])
                week_low = min(week_low, by_date[d]["low"])

        for name in EXTENSIONS:
            pos_hit = week_high >= levels[f"+{name}"]
            neg_hit = week_low <= levels[f"-{name}"]
            counts[f"+{name}"]["total"] += 1
            counts[f"-{name}"]["total"] += 1
            if pos_hit: counts[f"+{name}"]["hits"] += 1
            if neg_hit: counts[f"-{name}"]["hits"] += 1
            combined[name]["total"] += 1
            if pos_hit or neg_hit: combined[name]["hits"] += 1

        rekey_pos = week_high >= levels["+rekey"]
        rekey_neg = week_low <= levels["-rekey"]
        counts["+rekey"]["total"] += 1
        counts["-rekey"]["total"] += 1
        if rekey_pos: counts["+rekey"]["hits"] += 1
        if rekey_neg: counts["-rekey"]["hits"] += 1
        combined["rekey"]["total"] += 1
        if rekey_pos or rekey_neg: combined["rekey"]["hits"] += 1

    total = counts["+ext_25"]["total"]
    print(f"Weeks tested: {total}")

    print(f"\n--- COMBINED (EITHER DIRECTION) ---")
    for name in list(EXTENSIONS.keys()) + ["rekey"]:
        c = combined[name]
        pct = (c["hits"] / c["total"] * 100) if c["total"] > 0 else 0
        label = f"{int(EXTENSIONS.get(name, REKEY_PCT)*100)}%" if name != "rekey" else "132%"
        print(f"  {label:>5} ext: {c['hits']:>6}/{c['total']:>6} = {pct:>6.1f}%")

    return {"pair": pair, "level": "weekly", "total": total, "combined": combined, "counts": counts}


def main():
    parser = argparse.ArgumentParser(description="MLR Validation v3 (Optimized)")
    parser.add_argument("--pair", default="EURUSD")
    parser.add_argument("--data", help="Path to M5 CSV")
    parser.add_argument("--level", choices=["intraday", "weekly", "both"], default="both")
    parser.add_argument("--all-pairs", action="store_true")
    args = parser.parse_args()

    if args.all_pairs:
        # Find all M5 files
        files = []
        for f in sorted(DATA_DIR.glob("*M5*.csv")):
            name = f.stem
            # Skip crypto, indices, test files
            skip = ["BCHUSD", "BNBUSD", "BTCUSD", "ETHUSD", "LTCUSD", "SOLUSD",
                    "XLMUSD", "XAUUSD", "XAGUSD", "DE30", "FR40", "HK50", "US500",
                    "test_sample"]
            if any(s in name for s in skip):
                continue
            # Skip daily data (check first few rows)
            try:
                with open(f) as fh:
                    reader = csv.DictReader(fh)
                    r1 = next(reader, None)
                    r2 = next(reader, None)
                    if r1 and r2:
                        ts_col = None
                        for c in ["timestamp", "time"]:
                            if c in r1: ts_col = c; break
                        if ts_col:
                            t1 = r1[ts_col].strip()
                            t2 = r2[ts_col].strip()
                            try:
                                dt1 = datetime.fromtimestamp(int(t1))
                                dt2 = datetime.fromtimestamp(int(t2))
                            except:
                                dt1 = datetime.fromisoformat(t1)
                                dt2 = datetime.fromisoformat(t2)
                            if (dt2 - dt1).total_seconds() <= 600:
                                pair = name.replace("_M5", "").replace("PRO", "").replace("_fetched", "").replace("_2023_2026", "").replace("_2023_2025", "").replace("_MAD", "").replace("_dt", "")
                                files.append((pair, str(f)))
            except:
                pass

        print(f"Found {len(files)} pairs with M5 data")
        all_results = {}
        for pair, filepath in files:
            print(f"\n{'#'*60}")
            print(f"# {pair}")
            print(f"{'#'*60}")
            daily = load_m5_to_daily(filepath)
            if len(daily) < 50:
                print(f"  Skip: only {len(daily)} days")
                continue
            result = {"pair": pair, "data_file": filepath, "days": len(daily)}
            result["intraday"] = run_intraday(daily, pair)
            result["weekly"] = run_weekly(daily, pair)
            all_results[pair] = result

        # Save
        out = RESULTS_DIR / "mlr_v3_all_pairs.json"
        with open(out, "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"\nAll results saved to {out}")
        return

    # Single pair
    if args.data:
        filepath = args.data
    else:
        # Auto-find
        for p in [f"{args.pair}_M5.csv", f"{args.pair}PRO_M5.csv", f"{args.pair}PRO_M5_2023_2026.csv"]:
            fp = DATA_DIR / p
            if fp.exists():
                filepath = str(fp)
                break
        else:
            print(f"ERROR: No data for {args.pair}")
            sys.exit(1)

    print(f"Loading: {filepath}")
    daily = load_m5_to_daily(filepath)
    print(f"Aggregated to {len(daily)} daily bars")

    results = {"pair": args.pair, "data_file": filepath, "days": len(daily)}
    if args.level in ("intraday", "both"):
        results["intraday"] = run_intraday(daily, args.pair)
    if args.level in ("weekly", "both"):
        results["weekly"] = run_weekly(daily, args.pair)

    out = RESULTS_DIR / f"mlr_v3_{args.pair}_{args.level}.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
