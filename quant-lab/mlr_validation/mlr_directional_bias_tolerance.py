"""
MLR Directional Bias Validation — INTRADAY WITH 2-PIP TOLERANCE
================================================================
Same as mlr_directional_bias.py but with ±2 pip tolerance on hit detection.

Tolerance: level ± (2 * pip_size) — price within 2 pips of the level counts as a hit.
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
TOLERANCE_PIPS = 2  # 2-pip tolerance


def get_pip_size(pair):
    """Return pip size for a pair."""
    if "JPY" in pair:
        return 0.01
    if pair in ("BTCUSD", "ETHUSD", "BNBUSD", "SOLUSD", "LTCUSD", "BCHUSD"):
        return 1.0
    if pair == "XAUUSD":
        return 0.1
    if pair == "XAGUSD":
        return 0.01
    if pair in ("US500", "NAS100", "DE30", "FR40", "HK50"):
        return 1.0
    return 0.0001


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
    if d not in bars_by_date:
        return []
    return [b for b in bars_by_date[d] if 3 <= b["ts"].hour < 12]


def calc_levels(t0, ar, bias):
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


def check_hits_with_tolerance(act_bars, levels, bias, tolerance):
    """
    Check if price hits directional extension levels with ±tolerance tolerance.
    For Bullish: high >= level - tolerance (extensions), low <= level + tolerance (rekey)
    For Bearish: low <= level + tolerance (extensions), high >= level - tolerance (rekey)
    """
    hits = {name: False for name in list(EXTENSIONS.keys()) + ["rekey"]}
    for b in act_bars:
        if bias == "Bullish":
            for name in EXTENSIONS:
                if b["high"] >= (levels[name] - tolerance):
                    hits[name] = True
            if b["low"] <= (levels["rekey"] + tolerance):
                hits["rekey"] = True
        else:
            for name in EXTENSIONS:
                if b["low"] <= (levels[name] + tolerance):
                    hits[name] = True
            if b["high"] >= (levels["rekey"] - tolerance):
                hits["rekey"] = True
    return hits


def run_intraday_directional(bars, bars_by_date, pair, tolerance_pips=TOLERANCE_PIPS):
    pip_size = get_pip_size(pair)
    tolerance = tolerance_pips * pip_size

    print(f"\n{'='*60}")
    print(f"INTRADAY DIRECTIONAL MLR — {pair} (±{tolerance_pips} pip tolerance)")
    print(f"  pip_size={pip_size}, tolerance={tolerance}")
    print(f"{'='*60}")

    trading_dates = sorted(d for d in bars_by_date if d.weekday() < 5)
    counts_exact = {name: {"hits": 0, "total": 0} for name in list(EXTENSIONS.keys()) + ["rekey"]}
    counts_tol = {name: {"hits": 0, "total": 0} for name in list(EXTENSIONS.keys()) + ["rekey"]}
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
        hits_exact = check_hits_exact(act_bars, levels, bias)
        hits_tol = check_hits_with_tolerance(act_bars, levels, bias, tolerance)

        for name in counts_exact:
            counts_exact[name]["total"] += 1
            if hits_exact[name]:
                counts_exact[name]["hits"] += 1
        for name in counts_tol:
            counts_tol[name]["total"] += 1
            if hits_tol[name]:
                counts_tol[name]["hits"] += 1

    print(f"Total sessions: {total} (Bullish={bias_counts['Bullish']}, Bearish={bias_counts['Bearish']})")
    print()
    print(f"{'Level':<14} {'Exact':>10} {'±2p Tol':>10} {'Diff':>8}")
    print("-" * 46)

    results = {"pair": pair, "level": "intraday_directional", "total": total,
               "bias": bias_counts, "tolerance_pips": tolerance_pips, "pip_size": pip_size}

    for name in list(EXTENSIONS.keys()) + ["rekey"]:
        ce = counts_exact[name]
        ct = counts_tol[name]
        rate_exact = ce["hits"] / max(ce["total"], 1) * 100
        rate_tol = ct["hits"] / max(ct["total"], 1) * 100
        diff = rate_tol - rate_exact
        label = f"{name} ext" if name != "rekey" else "132% rekey"
        print(f"{label:<14} {rate_exact:>8.1f}% {rate_tol:>8.1f}% {diff:>+7.1f}%")
        results[name] = {
            "exact": {"hits": ce["hits"], "total": ce["total"], "rate": round(rate_exact, 1)},
            "tolerance": {"hits": ct["hits"], "total": ct["total"], "rate": round(rate_tol, 1)},
            "diff": round(diff, 1)
        }

    return results


def check_hits_exact(act_bars, levels, bias):
    """Original exact hit detection (no tolerance)."""
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


def find_csv(pair):
    for pattern in [f"{pair}PRO_M5*.csv", f"{pair}_M5*.csv", f"{pair}m_M5*.csv"]:
        matches = list(DATA_DIR.glob(pattern))
        if matches:
            return str(max(matches, key=lambda p: p.stat().st_size))
    return None


def main():
    parser = argparse.ArgumentParser(description="MLR Directional Bias with Tolerance")
    parser.add_argument("--pair", type=str, help="Single pair")
    parser.add_argument("--all-pairs", action="store_true", help="All pairs")
    parser.add_argument("--tolerance", type=int, default=TOLERANCE_PIPS, help="Tolerance in pips (default: 2)")
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
        print(f"Found {len(pairs)} pairs")
    else:
        parser.print_help()
        sys.exit(1)

    all_results = {}
    for pair in pairs:
        csv_path = args.csv if args.csv else find_csv(pair)
        if not csv_path or not Path(csv_path).exists():
            print(f"No CSV for {pair}, skipping")
            continue

        print(f"\n{'#'*60}")
        print(f"# {pair} — {csv_path}")
        print(f"{'#'*60}")

        bars = load_m5_csv(csv_path)
        bars_by_date = build_daily_index(bars)
        print(f"Loaded {len(bars)} M5 bars across {len(bars_by_date)} days")

        r = run_intraday_directional(bars, bars_by_date, pair, args.tolerance)
        all_results[pair] = r

    out_path = RESULTS_DIR / f"mlr_directional_bias_tol{args.tolerance}p.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()
