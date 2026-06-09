"""
MLR Intraday Validation — Proper Session-Based
===============================================
Uses actual M5 data to calculate:
  1. Asian Range (19:00 EST prev day → 03:00 EST target day)
  2. Extensions from T+0 anchor (03:00 EST close)
  3. Hit check during Activation Window (03:00-12:00 EST)

This is the CORRECT intraday test — uses actual session ranges from M5 data.
"""

import csv, json, sys
from pathlib import Path
from datetime import datetime, timedelta, time
from collections import defaultdict

DATA_DIR = Path("quant-lab/data")
RESULTS_DIR = Path("quant-lab/mlr_validation/results")

EXTENSIONS = {"ext_25": 0.25, "ext_50": 0.50, "ext_100": 1.00}
REKEY_PCT = 1.32

ASIAN_START = 19   # 19:00 EST
ASIAN_END = 3      # 03:00 EST (next day)
ACTIVATION_END = 12  # 12:00 EST


def load_m5(filepath):
    """Load M5 bars with datetime, OHLC."""
    bars = []
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
                o, h, l, c = float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])
                if h <= 0 or l <= 0:
                    continue
                bars.append({"dt": ts, "date": ts.date(), "hour": ts.hour,
                             "open": o, "high": h, "low": l, "close": c})
            except:
                continue
    bars.sort(key=lambda x: x["dt"])
    return bars


def calc_asian_range(bars, target_date):
    """Calculate Asian Range: 19:00 EST prev day → 03:00 EST target_date."""
    prev_date = target_date - timedelta(days=1)
    session_bars = []
    for b in bars:
        if b["date"] == prev_date and b["hour"] >= ASIAN_START:
            session_bars.append(b)
        elif b["date"] == target_date and b["hour"] < ASIAN_END:
            session_bars.append(b)

    if len(session_bars) < 2:
        return None

    high = max(b["high"] for b in session_bars)
    low = min(b["low"] for b in session_bars)
    range_val = high - low
    if range_val <= 0:
        return None

    # T+0 Anchor = close of last bar in Asian session (03:00 EST)
    t0 = session_bars[-1]["close"]

    return {
        "date": target_date,
        "high": high,
        "low": low,
        "range": range_val,
        "t0_anchor": t0,
        "bar_count": len(session_bars),
    }


def calc_activation_window(bars, target_date):
    """Get high/low during activation window: 03:00-12:00 EST."""
    act_bars = [b for b in bars if b["date"] == target_date and ASIAN_END <= b["hour"] < ACTIVATION_END]
    if len(act_bars) < 1:
        return None
    return {
        "high": max(b["high"] for b in act_bars),
        "low": min(b["low"] for b in act_bars),
        "bar_count": len(act_bars),
    }


def calc_levels(t0, ar):
    """Bidirectional extension levels."""
    levels = {"t0": t0, "range": ar}
    for name, pct in EXTENSIONS.items():
        levels["+" + name] = t0 + (ar * pct)
        levels["-" + name] = t0 - (ar * pct)
    levels["+rekey"] = t0 + (ar * REKEY_PCT)
    levels["-rekey"] = t0 - (ar * REKEY_PCT)
    return levels


def run_pair(pair, filepath):
    """Run intraday MLR for a single pair."""
    print(f"\nLoading {pair} from {filepath.name}...")
    bars = load_m5(str(filepath))
    print(f"  {len(bars)} M5 bars loaded")

    dates = sorted(set(b["date"] for b in bars))
    print(f"  Date range: {dates[0]} to {dates[-1]}, {len(dates)} trading days")

    counts = {}
    for name in EXTENSIONS:
        counts["+" + name] = {"hits": 0, "total": 0}
        counts["-" + name] = {"hits": 0, "total": 0}
    counts["+rekey"] = {"hits": 0, "total": 0}
    counts["-rekey"] = {"hits": 0, "total": 0}
    combined = {name: {"hits": 0, "total": 0} for name in list(EXTENSIONS.keys()) + ["rekey"]}

    skipped = 0
    for d in dates:
        # Step 1: Calculate Asian Range
        ar = calc_asian_range(bars, d)
        if ar is None:
            skipped += 1
            continue

        # Step 2: Calculate extension levels
        levels = calc_levels(ar["t0_anchor"], ar["range"])

        # Step 3: Check hits during activation window
        act = calc_activation_window(bars, d)
        if act is None:
            skipped += 1
            continue

        # Check extensions
        for name in EXTENSIONS:
            pos_hit = act["high"] >= levels["+" + name]
            neg_hit = act["low"] <= levels["-" + name]
            counts["+" + name]["total"] += 1
            counts["-" + name]["total"] += 1
            if pos_hit: counts["+" + name]["hits"] += 1
            if neg_hit: counts["-" + name]["hits"] += 1
            combined[name]["total"] += 1
            if pos_hit or neg_hit: combined[name]["hits"] += 1

        # Check rekey
        rekey_pos = act["high"] >= levels["+rekey"]
        rekey_neg = act["low"] <= levels["-rekey"]
        counts["+rekey"]["total"] += 1
        counts["-rekey"]["total"] += 1
        if rekey_pos: counts["+rekey"]["hits"] += 1
        if rekey_neg: counts["-rekey"]["hits"] += 1
        combined["rekey"]["total"] += 1
        if rekey_pos or rekey_neg: combined["rekey"]["hits"] += 1

    total = counts["+ext_25"]["total"]
    print(f"  Days tested: {total} (skipped: {skipped})")

    print(f"\n  --- INTRADAY MLR (Asian Range → Activation Window) ---")
    print(f"  {'Level':<12} {'Direction':<10} {'Hits':>5} {'Total':>5} {'Rate':>7}")
    print(f"  {'-'*45}")

    for name in EXTENSIONS:
        pct = int(EXTENSIONS[name] * 100)
        for direction in ["+", "-"]:
            key = direction + name
            c = counts[key]
            rate = (c["hits"] / c["total"] * 100) if c["total"] > 0 else 0
            print(f"  {pct}% ext     {direction:>5}     {c['hits']:>5} {c['total']:>5} {rate:>6.1f}%")

    print(f"\n  --- COMBINED (EITHER DIRECTION) ---")
    for name in list(EXTENSIONS.keys()) + ["rekey"]:
        c = combined[name]
        rate = (c["hits"] / c["total"] * 100) if c["total"] > 0 else 0
        label = f"{int(EXTENSIONS.get(name, REKEY_PCT)*100)}%"
        print(f"    {label:>5} ext: {c['hits']:>5}/{c['total']:>5} = {rate:>6.1f}%")

    return {
        "pair": pair,
        "total": total,
        "skipped": skipped,
        "combined": combined,
        "counts": counts,
    }


def main():
    # Find all M5 data files (both original and fetched)
    files = []

    # Original M5 files
    for f in sorted(DATA_DIR.glob("*M5*.csv")):
        name = f.name
        skip = ["BCHUSD", "BNBUSD", "BTCUSD", "ETHUSD", "LTCUSD", "SOLUSD",
                "XLMUSD", "DE30", "FR40", "HK50", "US500", "test_sample"]
        if any(s in name for s in skip):
            continue
        # Check if it's actually M5 (not daily)
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
                            pair = name.replace(".csv", "").replace("_M5", "").replace("PRO", "").replace("_fetched", "").replace("_2023_2026", "").replace("_2023_2025", "").replace("_MAD", "").replace("_dt", "")
                            files.append((pair, f))
        except:
            pass

    # Also add fetched files
    for f in sorted(DATA_DIR.glob("*_M5_fetched.csv")):
        pair = f.stem.replace("_M5_fetched", "")
        # Skip if already added
        if any(p == pair for p, _ in files):
            continue
        files.append((pair, f))

    # Deduplicate: prefer fetched files (more data)
    seen = {}
    for pair, f in files:
        if pair not in seen:
            seen[pair] = f
        else:
            # Prefer the one with more data (fetched)
            if "_fetched" in f.name:
                seen[pair] = f

    files = [(pair, f) for pair, f in seen.items()]
    files.sort()

    print(f"Found {len(files)} pairs with M5 data")
    all_results = {}

    for pair, f in files:
        result = run_pair(pair, f)
        all_results[pair] = result

    # Print combined summary
    print(f"\n\n{'='*80}")
    print(f"INTRADAY MLR SUMMARY — ALL PAIRS")
    print(f"{'='*80}")
    print(f"{'Pair':<10} | {'N':>5} | {'-25%':>7} {'-50%':>7} {'-100%':>7} {'Rekey':>7}")
    print(f"{'-'*60}")

    for pair in sorted(all_results.keys()):
        r = all_results[pair]
        c = r["combined"]

        def fmt(d, k):
            v = d.get(k, {})
            if isinstance(v, dict) and v.get("total", 0) > 0:
                return f"{v['hits']/v['total']*100:.1f}%"
            return "N/A"

        print(f"{pair:<10} | {r['total']:>5} | {fmt(c,'ext_25'):>7} {fmt(c,'ext_50'):>7} {fmt(c,'ext_100'):>7} {fmt(c,'rekey'):>7}")

    # Save
    out = RESULTS_DIR / "mlr_intraday_all_pairs.json"
    with open(out, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
