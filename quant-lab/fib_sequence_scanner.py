"""
FIBONACCI SEQUENCE SCANNER
==========================
Reconstructed from the Holy Grail Excel (cerebus 3 market hoily grail (3).xlsx)

Scans price data for Fibonacci sequence patterns:
  - Session range (Asian/London/NY) → directional bias → extension levels
  - Fibonacci retracement → extension sequences
  - ILM zone interactions
  - 132% invalidation detection
  - Pattern completion tracking

Based on sheets:
  - Fibonacci Sequences Catalog (sequence definitions + success rates)
  - Pattern Formations (pattern types + success rates)
  - Hit Rate Analysis Framework (calculation rules)
  - ILM Zone Behaviors (zone hit rates)
  - EURUSD_132_PATTERNS (132% violation tracking)
  - session_data_full_week (session-level data)
"""

import csv
import json
import sys
import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, date
from pathlib import Path

REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
QUANT_LAB = REPO_ROOT / "quant-lab"
DATA_DIR = QUANT_LAB / "data"
RESULTS_DIR = QUANT_LAB / "mlr_validation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# FIBONACCI LEVELS (from Hit Rate Analysis Framework)
# ═══════════════════════════════════════════════════════════════════════════════

FIB_EXTENSIONS = {
    "ext_25": 0.25,
    "ext_50": 0.50,
    "ext_100": 1.00,
    "ext_168": 1.68,
}

FIB_REKEY = 1.32  # 132% invalidation level

# From Fibonacci Sequences Catalog — sequence success rates
SEQUENCE_DEFINITIONS = {
    "50_-25": {"structure": "50% retracement → -25% extension", "success": 84.0, "freq": 28.6},
    "61.8_-50": {"structure": "61.8% retracement → -50% extension", "success": 82.0, "freq": 23.8},
    "72_-25": {"structure": "72% retracement → -25% extension", "success": 83.5, "freq": 31.6},
    "78.6_-100": {"structure": "78.6% deep retracement → -100% extension", "success": 76.0, "freq": 15.2},
    "50_72_-25": {"structure": "3-leg composite: 50%→72%→-25%", "success": 78.7, "freq": 78.7},
    "50_50_retest": {"structure": "50% → retest at 50%", "success": 83.2, "freq": 35.0},
    "72_72_retest": {"structure": "72% → retest at 72%", "success": 68.0, "freq": 25.0},
    "50_100": {"structure": "50% → 100% continuation", "success": 100.0, "freq": 100.0},
}

# From Pattern Formations — pattern types
PATTERN_TYPES = {
    "Alpha": {"structure": "A-B(72%)→B-C(-25%)→C-D(61.8%)", "success": 78.3},
    "Beta": {"structure": "A-B(50%)→B-C(72%)→C-D(-25%)", "success": 74.6},
    "Gamma": {"structure": "A-B(61.8%)→B-C(-50%)→C-D(50%)", "success": 76.8},
    "Delta": {"structure": "A-B(50%)→B-C(-25%)→C-D(50%)", "success": 72.9},
    "15M_AB_CD_Bullish": {"structure": "50%→-25%", "success": 84.0},
    "15M_AB_CD_Bearish": {"structure": "61.8%→-50%", "success": 66.0},
}

# From ILM Zone Behaviors
ILM_ZONES = {
    "ILM_Daily": {"hit_rate": 64.3, "continuation": 69, "velocity": "1.2x-1.6x"},
    "IELM_2Day": {"hit_rate": 48.3, "continuation": 48.3, "velocity": "1.5x-2.1x"},
    "WILM_Weekly": {"hit_rate": 34.2, "continuation": 34.2, "velocity": "1.8x-2.8x"},
    "Quarter_Levels": {"hit_rate": 80.5, "continuation": 72, "velocity": "1.3x-1.8x"},
    "Full_Alignment": {"hit_rate": 87.3, "continuation": 87.3, "velocity": "2.5x+"},
}


def get_pip_size(pair):
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


def get_session_range(bars_by_date, d, start_hour, end_hour, prev_day=False):
    """Get session OHLC for a given date and hour range."""
    session_bars = []
    if prev_day:
        prev = d - timedelta(days=1)
        if prev in bars_by_date:
            session_bars.extend(b for b in bars_by_date[prev] if b["ts"].hour >= start_hour)
        if d in bars_by_date:
            session_bars.extend(b for b in bars_by_date[d] if b["ts"].hour < end_hour)
    else:
        if d in bars_by_date:
            session_bars.extend(b for b in bars_by_date[d] if start_hour <= b["ts"].hour < end_hour)
    if len(session_bars) < 2:
        return None
    session_bars.sort(key=lambda b: b["ts"])
    s_open = session_bars[0]["open"]
    s_high = max(b["high"] for b in session_bars)
    s_low = min(b["low"] for b in session_bars)
    s_close = session_bars[-1]["close"]
    s_range = s_high - s_low
    if s_range <= 0:
        return None
    return (s_open, s_high, s_low, s_close, s_range)


def calc_fib_levels(s_open, s_high, s_low, s_close, s_range, bias):
    """
    Calculate Fibonacci extension levels based on directional bias.
    
    From Hit Rate Analysis Framework:
    Bullish (Close > Open):
      - 0% = Session LOW
      - 100% = Session HIGH
      - Extensions ABOVE: -25%, -50%, -100%, -168% (above high)
      - Invalidation BELOW: 132% (below low)
    
    Bearish (Close < Open):
      - 0% = Session HIGH
      - 100% = Session LOW
      - Extensions BELOW: -25%, -50%, -100%, -168% (below low)
      - Invalidation ABOVE: 132% (above high)
    """
    t0 = s_close
    levels = {"t0": t0, "range": s_range, "bias": bias,
              "s_open": s_open, "s_high": s_high, "s_low": s_low}

    if bias == "Bullish":
        fib_0 = s_low
        fib_100 = s_high
        for name, pct in FIB_EXTENSIONS.items():
            levels[name] = fib_100 + (s_range * pct)
        levels["rekey_132"] = fib_0 - (s_range * FIB_REKEY)
    else:
        fib_0 = s_high
        fib_100 = s_low
        for name, pct in FIB_EXTENSIONS.items():
            levels[name] = fib_100 - (s_range * pct)
        levels["rekey_132"] = fib_0 + (s_range * FIB_REKEY)

    return levels


def scan_sequence(bars_by_date, pair, session_type="Asian", tolerance_pips=0):
    """
    Scan for Fibonacci sequence patterns.
    
    Session types:
      Asian: 19:00 prev day → 03:00 current day, activation 03:00-12:00
      London: 03:00-11:00, activation 11:00-16:00
      NY: 08:00-12:00, activation 12:00-16:00
      Weekly: Monday London 03:00-11:00, activation Mon 11:00 → Fri close
    """
    pip_size = get_pip_size(pair)
    tolerance = tolerance_pips * pip_size

    if session_type == "Asian":
        get_session = lambda d: get_session_range(bars_by_date, d, 19, 3, prev_day=True)
        get_activation = lambda d: [b for b in bars_by_date.get(d, []) if 3 <= b["ts"].hour < 12]
    elif session_type == "London":
        get_session = lambda d: get_session_range(bars_by_date, d, 3, 11)
        get_activation = lambda d: [b for b in bars_by_date.get(d, []) if 11 <= b["ts"].hour < 16]
    elif session_type == "NY":
        get_session = lambda d: get_session_range(bars_by_date, d, 8, 12)
        get_activation = lambda d: [b for b in bars_by_date.get(d, []) if 12 <= b["ts"].hour < 16]
    elif session_type == "Weekly":
        get_session = lambda d: get_session_range(bars_by_date, d, 3, 11)  # Monday London
        get_activation = lambda d: _get_week_bars(bars_by_date, d)  # Mon 11:00 → Fri
    else:
        raise ValueError(f"Unknown session type: {session_type}")

    trading_dates = sorted(d for d in bars_by_date if d.weekday() < 5)

    counts_exact = {name: {"hits": 0, "total": 0} for name in list(FIB_EXTENSIONS.keys()) + ["rekey_132"]}
    counts_tol = {name: {"hits": 0, "total": 0} for name in list(FIB_EXTENSIONS.keys()) + ["rekey_132"]}
    bias_counts = {"Bullish": 0, "Bearish": 0}
    total = 0

    for d in trading_dates:
        sr = get_session(d)
        if sr is None:
            continue
        s_open, s_high, s_low, s_close, s_range = sr

        if s_close > s_open:
            bias = "Bullish"
        elif s_close < s_open:
            bias = "Bearish"
        else:
            continue

        bias_counts[bias] += 1
        total += 1

        act_bars = get_activation(d)
        if not act_bars:
            continue

        levels = calc_fib_levels(s_open, s_high, s_low, s_close, s_range, bias)

        # Exact hits
        hits_exact = _check_hits(act_bars, levels, bias)
        # Tolerance hits
        hits_tol = _check_hits_tolerance(act_bars, levels, bias, tolerance)

        for name in counts_exact:
            counts_exact[name]["total"] += 1
            if hits_exact[name]:
                counts_exact[name]["hits"] += 1
        for name in counts_tol:
            counts_tol[name]["total"] += 1
            if hits_tol[name]:
                counts_tol[name]["hits"] += 1

    levels_result = {}
    for name in list(FIB_EXTENSIONS.keys()) + ["rekey_132"]:
        ce = counts_exact[name]
        ct = counts_tol[name]
        re_rate = ce["hits"] / max(ce["total"], 1) * 100
        rt_rate = ct["hits"] / max(ct["total"], 1) * 100
        levels_result[name] = {
            "exact": {"hits": ce["hits"], "total": ce["total"], "rate": round(re_rate, 1)},
            "tolerance": {"hits": ct["hits"], "total": ct["total"], "rate": round(rt_rate, 1)},
            "diff": round(rt_rate - re_rate, 1)
        }

    return {
        "pair": pair,
        "session_type": session_type,
        "total": total,
        "bias": bias_counts,
        "tolerance_pips": tolerance_pips,
        "pip_size": pip_size,
        "levels": levels_result
    }


def _check_hits(act_bars, levels, bias):
    hits = {name: False for name in list(FIB_EXTENSIONS.keys()) + ["rekey_132"]}
    for b in act_bars:
        if bias == "Bullish":
            for name in FIB_EXTENSIONS:
                if b["high"] >= levels[name]:
                    hits[name] = True
            if b["low"] <= levels["rekey_132"]:
                hits["rekey_132"] = True
        else:
            for name in FIB_EXTENSIONS:
                if b["low"] <= levels[name]:
                    hits[name] = True
            if b["high"] >= levels["rekey_132"]:
                hits["rekey_132"] = True
    return hits


def _check_hits_tolerance(act_bars, levels, bias, tolerance):
    hits = {name: False for name in list(FIB_EXTENSIONS.keys()) + ["rekey_132"]}
    for b in act_bars:
        if bias == "Bullish":
            for name in FIB_EXTENSIONS:
                if b["high"] >= (levels[name] - tolerance):
                    hits[name] = True
            if b["low"] <= (levels["rekey_132"] + tolerance):
                hits["rekey_132"] = True
        else:
            for name in FIB_EXTENSIONS:
                if b["low"] <= (levels[name] + tolerance):
                    hits[name] = True
            if b["high"] >= (levels["rekey_132"] - tolerance):
                hits["rekey_132"] = True
    return hits


def _get_week_bars(bars_by_date, monday):
    week_bars = []
    for offset in range(5):
        d = monday + timedelta(days=offset)
        if d in bars_by_date:
            if offset == 0:
                week_bars.extend(b for b in bars_by_date[d] if b["ts"].hour >= 11)
            else:
                week_bars.extend(bars_by_date[d])
    return week_bars


def find_csv(pair):
    for pattern in [f"{pair}PRO_M5*.csv", f"{pair}_M5*.csv", f"{pair}m_M5*.csv"]:
        matches = list(DATA_DIR.glob(pattern))
        if matches:
            return str(max(matches, key=lambda p: p.stat().st_size))
    return None


def main():
    parser = argparse.ArgumentParser(description="Fibonacci Sequence Scanner")
    parser.add_argument("--pair", type=str, required=True, help="Pair to scan")
    parser.add_argument("--session", type=str, default="Asian",
                        choices=["Asian", "London", "NY", "Weekly"], help="Session type")
    parser.add_argument("--tolerance", type=int, default=0, help="Tolerance in pips")
    parser.add_argument("--csv", type=str, help="Explicit CSV path")
    args = parser.parse_args()

    pair = args.pair.upper()
    csv_path = args.csv if args.csv else find_csv(pair)
    if not csv_path or not Path(csv_path).exists():
        print(f"No CSV found for {pair}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"FIBONACCI SEQUENCE SCANNER — {pair} ({args.session})")
    print(f"{'='*60}")
    print(f"CSV: {csv_path}")

    bars = load_m5_csv(csv_path)
    bars_by_date = build_daily_index(bars)
    print(f"Loaded {len(bars)} M5 bars across {len(bars_by_date)} days")

    result = scan_sequence(bars_by_date, pair, args.session, args.tolerance)

    print(f"\nTotal sessions: {result['total']}")
    print(f"  Bullish: {result['bias']['Bullish']} ({result['bias']['Bullish']/max(result['total'],1)*100:.1f}%)")
    print(f"  Bearish: {result['bias']['Bearish']} ({result['bias']['Bearish']/max(result['total'],1)*100:.1f}%)")
    print()

    tol_label = f"±{args.tolerance}p" if args.tolerance > 0 else "Exact"
    print(f"{'Level':<14} {'Exact':>10} {tol_label:>10} {'Diff':>8}")
    print("-" * 46)

    for name in list(FIB_EXTENSIONS.keys()) + ["rekey_132"]:
        ce = result["levels"].get(name, {}).get("exact", {})
        ct = result["levels"].get(name, {}).get("tolerance", {})
        re_rate = ce.get("rate", 0)
        rt_rate = ct.get("rate", 0)
        diff = rt_rate - re_rate
        label = f"{name} ext" if name != "rekey_132" else "132% rekey"
        print(f"{label:<14} {re_rate:>8.1f}% {rt_rate:>8.1f}% {diff:>+7.1f}%")

    # Save results
    out_path = RESULTS_DIR / f"fib_scan_{pair}_{args.session.lower()}_tol{args.tolerance}p.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()
