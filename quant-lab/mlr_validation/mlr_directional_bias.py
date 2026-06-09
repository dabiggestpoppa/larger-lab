"""
MLR Directional Bias Validation — INTRADAY ONLY
================================================
Validates MLR extension hit rates with DIRECTIONAL BIAS from Asian session close vs open.

RULES (from Holy Grail Excel — EURUSD_Asian_Fibonacci & session_data_full_week):
  1. Asian Range = Asian High - Asian Low (19:00 EST prev day to 03:00 EST current day)
  2. T+0 = Asian Close (last bar of Asian session)
  3. DIRECTIONAL BIAS:
     - Bullish if Asian_Close > Asian_Open
     - Bearish if Asian_Close < Asian_Open
  4. Extensions measured from T+0 IN THE BIAS DIRECTION:
     +25% = T+0 + (AR x 0.25)  |  +50% = T+0 + (AR x 0.50)  |  +100% = T+0 + (AR x 1.00)
  5. REKEY (132%) measured in OPPOSITE direction:
     -132% = T+0 - (AR x 1.32) for Bullish bias
     +132% = T+0 + (AR x 1.32) for Bearish bias
  6. Hit = daily high/low reaches level during Activation Window (03:00-12:00 EST)

Excel Claims (from Delivery Stats sheet):
  -25% extension: 90% hit rate
  -50% extension: 82% hit rate

Excel Actual Results (from EURUSD_Asian_Hit_Rates):
  Overall -25%: 65.19% (exact), 100% (with tolerance)
  Overall -50%: 54.94% (exact), 100% (with tolerance)
  Bullish -25%: 65.02% | Bearish -25%: 65.39%

Usage:
    python mlr_directional_bias.py --pair EURUSD
    python mlr_directional_bias.py --all-pairs
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "quant-lab" / "data"
RESULTS_DIR = REPO_ROOT / "quant-lab" / "mlr_validation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

EXTENSIONS = {"ext_25": 0.25, "ext_50": 0.50, "ext_100": 1.00}
REKEY_PCT = 1.32


def load_m5_csv(filepath):
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
                bars.append({"ts": ts, "date": ts.date(), "open": o, "high": h, "low": l, "close": c})
            except (KeyError, ValueError, TypeError):
                continue
    bars.sort(key=lambda b: b["ts"])
    return bars


def build_daily_index(bars):
    by_date = defaultdict(list)
    for b in bars:
        by_date[b["date"]].append(b)
    for d in by_date:
        by_date[d].sort(key=lambda b: b["ts"])
    return dict(by_date)


def get_asian_session(bars_by_date, d):
    """Asian = 19:00 EST prev day to 03:00 EST current day. Returns (open, high, low, close, range) or None."""
    prev = d - timedelta(days=1)
    asian_bars = []
    if prev in bars_by_date:
        asian_bars.extend(b for b in bars_by_date[prev] if b["ts"].hour >= 19)
    if d in bars_by_date:
        asian_bars.extend(b for b in bars_by_date[d] if b["ts"].hour < 3)
    if len(asian_bars) < 2:
        return None
    asian_bars.sort(key=lambda b: b["ts"])
    s_open = asian_bars[0]["open"]
    s_high = max(b["high"] for b in asian_bars)
    s_low = min(b["low"] for b in asian_bars)
    s_close = asian_bars[-1]["close"]
    s_range = s_high - s_low
    if s_range <= 0:
        return None
    return (s_open, s_high, s_low, s_close, s_range)


def get_activation_bars(bars_by_date, d):
    """Activation window = 03:00-12:00 EST."""
    if d not in bars_by_date:
        return []
    return [b for b in bars_by_date[d] if 3 <= b["ts"].hour < 12]


def calc_levels(t0, ar, bias):
    """Directional extension levels from T+0."""
    levels = {"t0": t0, "range": ar, "bias": bias}
    if bias == "Bullish":
        for name, pct in EXTENSIONS.items():
            levels[name] = t0 + (ar * pct)
        levels["rekey"] = t0 - (ar * REKEY_PCT)
    else:
        for name, pct in EXTENSIONS.items():
            levels[name] = t0 - (ar * pct)
        levels["rekey"] = t0 + (ar * REKEY_PCT)
    return levels


def check_hits(act_bars, levels, bias):
    """Check if price hits directional extension levels during activation window."""
    hits = {name: False for name in list(EXTENSIONS.keys()) + ["rekey"]}
    for b in act_bars:
        if bias == "Bullish":
            for name in EXTENSIONS:
                if b["high"] >= levels[name]:
                    hits[name] = True
            if b["low"] <= levels["rekey"]:
                hits["rekey"] = True
        else:
            for name in EXTENSIONS:
                if b["low"] <= levels[name]:
                    hits[name] = True
            if b["high"] >= levels["rekey"]:
                hits["rekey"] = True
    return hits


def run_intraday_directional(bars, bars_by_date, pair):
    """
    Intraday Directional MLR:
    Asian Session -> Bias from Close vs Open -> Extensions in bias direction -> Hit in Activation Window
    """
    print(f"\n{'='*60}")
    print(f"INTRADAY DIRECTIONAL MLR — {pair}")
    print(f"{'='*60}")

    trading_dates = sorted(d for d in bars_by_date if d.weekday() < 5)
    counts = {name: {"hits": 0, "total": 0} for name in list(EXTENSIONS.keys()) + ["rekey"]}
    bias_counts = {"Bullish": 0, "Bearish": 0}
    total = 0

    for d in trading_dates:
        sr = get_asian_session(bars_by_date, d)
        if sr is None:
            continue
        s_open, s_high, s_low, s_close, s_range = sr
        t0 = s_close

        if s_close > s_open:
            bias = "Bullish"
        elif s_close < s_open:
            bias = "Bearish"
        else:
            continue

        bias_counts[bias] += 1
        total += 1

        act_bars = get_activation_bars(bars_by_date, d)
        if not act_bars:
            continue

        levels = calc_levels(t0, s_range, bias)
        hits = check_hits(act_bars, levels, bias)

        for name in counts:
            counts[name]["total"] += 1
            if hits[name]:
                counts[name]["hits"] += 1

    print(f"Total sessions with directional bias: {total}")
    print(f"  Bullish: {bias_counts['Bullish']} ({bias_counts['Bullish']/max(total,1)*100:.1f}%)")
    print(f"  Bearish: {bias_counts['Bearish']} ({bias_counts['Bearish']/max(total,1)*100:.1f}%)")
    print()
    print(f"{'Level':<14} {'Hits':>6} {'Total':>6} {'Rate':>8}")
    print("-" * 38)

    results = {"pair": pair, "level": "intraday_directional", "total": total, "bias": bias_counts}
    for name in list(EXTENSIONS.keys()) + ["rekey"]:
        c = counts[name]
        rate = c["hits"] / max(c["total"], 1) * 100
        label = f"{name} ext" if name != "rekey" else "132% rekey"
        print(f"{label:<14} {c['hits']:>6} {c['total']:>6} {rate:>7.1f}%")
        results[name] = {"hits": c["hits"], "total": c["total"], "rate": round(rate, 1)}

    return results


def find_csv(pair):
    for pattern in [f"{pair}PRO_M5*.csv", f"{pair}_M5*.csv", f"{pair}m_M5*.csv"]:
        matches = list(DATA_DIR.glob(pattern))
        if matches:
            return str(max(matches, key=lambda p: p.stat().st_size))
    return None


def main():
    parser = argparse.ArgumentParser(description="MLR Directional Bias Validation — Intraday")
    parser.add_argument("--pair", type=str, help="Single pair to test")
    parser.add_argument("--all-pairs", action="store_true", help="Test all available pairs")
    parser.add_argument("--csv", type=str, help="Explicit CSV path")
    args = parser.parse_args()

    if args.pair:
        pairs = [args.pair.upper()]
    elif args.all_pairs:
        pairs = set()
        for f in DATA_DIR.glob("*_M5*.csv"):
            name = f.stem.split("_")[0].replace("PRO", "").replace("m", "")
            pairs.add(name)
        pairs = sorted(pairs)
        print(f"Found {len(pairs)} pairs: {', '.join(pairs)}")
    else:
        parser.print_help()
        sys.exit(1)

    all_results = {}

    for pair in pairs:
        csv_path = args.csv if args.csv else find_csv(pair)
        if not csv_path or not Path(csv_path).exists():
            print(f"No CSV found for {pair}, skipping")
            continue

        print(f"\n{'#'*60}")
        print(f"# {pair} — {csv_path}")
        print(f"{'#'*60}")

        bars = load_m5_csv(csv_path)
        bars_by_date = build_daily_index(bars)
        print(f"Loaded {len(bars)} M5 bars across {len(bars_by_date)} trading days")

        r = run_intraday_directional(bars, bars_by_date, pair)
        all_results[pair] = r

    out_path = RESULTS_DIR / "mlr_directional_bias_intraday.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to: {out_path}")

    # Summary
    print(f"\n{'='*80}")
    print("INTRADAY DIRECTIONAL MLR — SUMMARY")
    print(f"{'='*80}")
    print(f"{'Pair':<10} {'N':>5} {'Bias B/S':>12} {'-25%':>8} {'-50%':>8} {'-100%':>8} {'132%':>8}")
    print("-" * 70)
    for pair, r in all_results.items():
        bias_str = f"{r['bias']['Bullish']}/{r['bias']['Bearish']}"
        print(f"{pair:<10} {r['total']:>5} {bias_str:>12} "
              f"{r['ext_25']['rate']:>7.1f}% {r['ext_50']['rate']:>7.1f}% "
              f"{r['ext_100']['rate']:>7.1f}% {r['rekey']['rate']:>7.1f}%")


if __name__ == "__main__":
    main()
