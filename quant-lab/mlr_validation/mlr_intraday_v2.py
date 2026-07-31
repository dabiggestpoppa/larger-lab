"""
MLR Intraday Validation v2 — Optimized
=======================================
Pre-indexes M5 bars by (date, hour) for O(1) session lookup.
Calculates Asian Range (19:00-03:00 EST) and Activation Window (03:00-12:00 EST).
"""

import csv, json, sys
from pathlib import Path
from datetime import datetime, timedelta, time
from collections import defaultdict

DATA_DIR = Path("quant-lab/data")
RESULTS_DIR = Path("quant-lab/mlr_validation/results")

EXTENSIONS = {"ext_25": 0.25, "ext_50": 0.50, "ext_100": 1.00}
REKEY_PCT = 1.32


def load_and_index_m5(filepath):
    """
    Load M5 bars and index by (date, hour) for fast session lookup.
    Returns: bars_by_date_hour dict, all_dates sorted list
    """
    # Index: date -> hour -> list of bars
    by_date_hour = defaultdict(lambda: defaultdict(list))
    by_date = defaultdict(list)

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
                h = ts.hour
                bar = {"high": float(row["high"]), "low": float(row["low"]),
                       "close": float(row["close"]), "open": float(row["open"])}
                if bar["high"] <= 0 or bar["low"] <= 0:
                    continue
                by_date_hour[d][h].append(bar)
                by_date[d].append(bar)
            except:
                continue

    dates = sorted(by_date.keys())
    return by_date_hour, by_date, dates


def calc_asian_range(by_date_hour, target_date):
    """Asian Range: 19:00 EST prev day → 03:00 EST target_date."""
    prev_date = target_date - timedelta(days=1)

    highs, lows, closes = [], [], []

    # Previous day 19:00-23:00
    for h in range(19, 24):
        for bar in by_date_hour[prev_date].get(h, []):
            highs.append(bar["high"])
            lows.append(bar["low"])
            closes.append(bar["close"])

    # Target day 00:00-02:00
    for h in range(0, 3):
        for bar in by_date_hour[target_date].get(h, []):
            highs.append(bar["high"])
            lows.append(bar["low"])
            closes.append(bar["close"])

    if len(highs) < 2:
        return None

    ar_high = max(highs)
    ar_low = min(lows)
    ar_range = ar_high - ar_low
    if ar_range <= 0:
        return None

    # T+0 Anchor = last bar close (03:00 EST = last bar before activation)
    t0 = closes[-1] if closes else ar_high

    return {"high": ar_high, "low": ar_low, "range": ar_range, "t0_anchor": t0}


def calc_activation_window(by_date_hour, target_date):
    """Activation Window: 03:00-12:00 EST."""
    highs, lows = [], []
    for h in range(3, 12):
        for bar in by_date_hour[target_date].get(h, []):
            highs.append(bar["high"])
            lows.append(bar["low"])

    if len(highs) < 1:
        return None

    return {"high": max(highs), "low": min(lows)}


def calc_levels(t0, ar):
    levels = {"t0": t0, "range": ar}
    for name, pct in EXTENSIONS.items():
        levels["+" + name] = t0 + (ar * pct)
        levels["-" + name] = t0 - (ar * pct)
    levels["+rekey"] = t0 + (ar * REKEY_PCT)
    levels["-rekey"] = t0 - (ar * REKEY_PCT)
    return levels


def run_pair(pair, filepath):
    """Run intraday MLR for a single pair."""
    print(f"\n{pair}: loading {filepath.name}...")
    by_date_hour, by_date, dates = load_and_index_m5(str(filepath))
    print(f"  {len(dates)} trading days, {sum(len(b) for b in by_date.values())} total bars")

    counts = {}
    for name in EXTENSIONS:
        counts["+" + name] = {"hits": 0, "total": 0}
        counts["-" + name] = {"hits": 0, "total": 0}
    counts["+rekey"] = {"hits": 0, "total": 0}
    counts["-rekey"] = {"hits": 0, "total": 0}
    combined = {name: {"hits": 0, "total": 0} for name in list(EXTENSIONS.keys()) + ["rekey"]}

    skipped = 0
    for d in dates:
        ar = calc_asian_range(by_date_hour, d)
        if ar is None:
            skipped += 1
            continue

        levels = calc_levels(ar["t0_anchor"], ar["range"])
        act = calc_activation_window(by_date_hour, d)
        if act is None:
            skipped += 1
            continue

        for name in EXTENSIONS:
            pos_hit = act["high"] >= levels["+" + name]
            neg_hit = act["low"] <= levels["-" + name]
            counts["+" + name]["total"] += 1
            counts["-" + name]["total"] += 1
            if pos_hit: counts["+" + name]["hits"] += 1
            if neg_hit: counts["-" + name]["hits"] += 1
            combined[name]["total"] += 1
            if pos_hit or neg_hit: combined[name]["hits"] += 1

        rekey_pos = act["high"] >= levels["+rekey"]
        rekey_neg = act["low"] <= levels["-rekey"]
        counts["+rekey"]["total"] += 1
        counts["-rekey"]["total"] += 1
        if rekey_pos: counts["+rekey"]["hits"] += 1
        if rekey_neg: counts["-rekey"]["hits"] += 1
        combined["rekey"]["total"] += 1
        if rekey_pos or rekey_neg: combined["rekey"]["hits"] += 1

    total = counts["+ext_25"]["total"]
    print(f"  Tested: {total} days (skipped: {skipped})")

    def fmt(d, k):
        v = d.get(k, {})
        return f"{v['hits']/v['total']*100:.1f}%" if isinstance(v, dict) and v.get("total", 0) > 0 else "N/A"

    print(f"  Combined: -25%={fmt(combined,'ext_25')} -50%={fmt(combined,'ext_50')} -100%={fmt(combined,'ext_100')} Rekey={fmt(combined,'rekey')}")

    return {"pair": pair, "total": total, "skipped": skipped, "combined": combined}


def main():
    # Collect all M5 files
    files = {}
    for f in sorted(DATA_DIR.glob("*M5*.csv")):
        name = f.name
        skip = ["BCHUSD", "BNBUSD", "BTCUSD", "ETHUSD", "LTCUSD", "SOLUSD",
                "XLMUSD", "DE30", "FR40", "HK50", "US500", "test_sample"]
        if any(s in name for s in skip):
            continue
        # Check if M5
        try:
            with open(f) as fh:
                reader = csv.DictReader(fh)
                r1, r2 = next(reader, None), next(reader, None)
                if r1 and r2:
                    ts_col = next((c for c in ["timestamp", "time"] if c in r1), None)
                    if ts_col:
                        t1, t2 = r1[ts_col].strip(), r2[ts_col].strip()
                        try:
                            dt1, dt2 = datetime.fromtimestamp(int(t1)), datetime.fromtimestamp(int(t2))
                        except:
                            dt1, dt2 = datetime.fromisoformat(t1), datetime.fromisoformat(t2)
                        if (dt2 - dt1).total_seconds() <= 600:
                            pair = name.replace(".csv","").replace("_M5","").replace("PRO","").replace("_fetched","").replace("_2023_2026","").replace("_2023_2025","").replace("_MAD","").replace("_dt","")
                            # Prefer fetched files
                            if pair not in files or "_fetched" in name:
                                files[pair] = f
        except:
            pass

    print(f"Found {len(files)} pairs")
    all_results = {}

    for pair in sorted(files.keys()):
        result = run_pair(pair, files[pair])
        all_results[pair] = result

    # Summary table
    print(f"\n\n{'='*75}")
    print(f"{'Pair':<10} | {'N':>5} | {'-25%':>7} {'-50%':>7} {'-100%':>7} {'Rekey':>7}")
    print(f"{'-'*55}")

    for pair in sorted(all_results.keys()):
        r = all_results[pair]
        c = r["combined"]
        def fmt(d, k):
            v = d.get(k, {})
            return f"{v['hits']/v['total']*100:.1f}%" if isinstance(v, dict) and v.get("total", 0) > 0 else "N/A"
        print(f"{pair:<10} | {r['total']:>5} | {fmt(c,'ext_25'):>7} {fmt(c,'ext_50'):>7} {fmt(c,'ext_100'):>7} {fmt(c,'rekey'):>7}")

    out = RESULTS_DIR / "mlr_intraday_v2_all_pairs.json"
    with open(out, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
