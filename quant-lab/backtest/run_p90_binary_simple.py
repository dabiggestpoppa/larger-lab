"""
P90 BINARY TEST — SIMPLE
========================
3AM-12PM EST: If P90 candle prints, enter in direction.
Expiry: 1-120 min. Win if price closes in direction by expiry.

NO Asian Range. NO targets. NO tiers. NO SL.
Just: P90 prints -> enter -> does close go your way before expiry?
"""
import sys, json, csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab")))
from configs.asset_configs import ASSET_CONFIGS

UTC = timezone.utc
EST = timezone(timedelta(hours=-5))

# Activation window: 3AM-12PM EST = 8AM-17PM UTC
ACT_START_UTC = 8
ACT_END_UTC = 17

# Expiry windows to test (minutes)
EXPIRY_WINDOWS = [1, 2, 3, 5, 10, 15, 20, 30, 45, 60, 90, 120]

# P90 thresholds by 2-hour UTC buckets (matching manual's EST buckets)
# 3-5AM EST = 8-10AM UTC, 5-7AM EST = 10-12PM UTC, etc.
# Using manual's EUR/USD reference thresholds
P90_THRESHOLDS = {
    8: 4.1,   # 3-5AM EST
    10: 4.6,  # 5-7AM EST
    12: 4.6,  # 7-9AM EST
    14: 5.9,  # 9-11AM EST
    16: 6.2,  # 11AM-12PM EST
}


def find_csv(symbol):
    for p in [
        f"quant-lab/data/{symbol}_M5.csv",
        f"quant-lab/data/{symbol}_M5_fetched.csv",
        f"quant-lab/data/{symbol}PRO_M5_2023_2026.csv",
        f"quant-lab/data/{symbol}PRO_M5_2023_2025.csv",
        f"quant-lab/data/{symbol}PRO_M5.csv",
    ]:
        if Path(p).exists():
            return p
    return None


def load_bars(csv_path):
    bars = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts_raw = row.get("timestamp") or row.get("time") or row.get("date")
                if not ts_raw:
                    continue
                ts_raw = ts_raw.strip()
                # Try parsing as datetime string
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                    try:
                        ts = datetime.strptime(ts_raw, fmt).replace(tzinfo=UTC)
                        break
                    except ValueError:
                        continue
                else:
                    # Try unix timestamp
                    try:
                        ts = datetime.fromtimestamp(int(ts_raw), tz=UTC)
                    except (ValueError, OSError):
                        continue
                o = float(row.get("open") or row.get("Open"))
                h = float(row.get("high") or row.get("High"))
                lo = float(row.get("low") or row.get("Low"))
                cl = float(row.get("close") or row.get("Close"))
                bars.append((ts, o, h, lo, cl))
            except (ValueError, KeyError, TypeError):
                continue
    bars.sort(key=lambda b: b[0])
    return bars


def get_p90_threshold(utc_hour, pip_size):
    """Get P90 threshold for this UTC hour."""
    bucket = (utc_hour // 2) * 2
    threshold_pips = P90_THRESHOLDS.get(bucket, 4.6)
    return threshold_pips * pip_size


def run_binary(bars, pip_size):
    """
    For each P90 signal in 3PM-12PM EST window, test all expiry windows.
    Win = close in direction by expiry. Loss = close against by expiry.
    """
    results_by_expiry = {exp: {"wins": 0, "losses": 0, "total": 0} for exp in EXPIRY_WINDOWS}

    for i, (ts, o, h, lo, cl) in enumerate(bars):
        utc_hour = ts.hour

        # Activation window: 8AM-5PM UTC = 3AM-12PM EST
        if utc_hour < ACT_START_UTC or utc_hour >= ACT_END_UTC:
            continue

        # P90 check: body >= threshold
        body = abs(cl - o)
        threshold = get_p90_threshold(utc_hour, pip_size)
        if body < threshold:
            continue

        # Direction: bullish = LONG, bearish = SHORT
        direction = 1 if cl > o else -1
        entry = cl

        # Test each expiry window
        for expiry_min in EXPIRY_WINDOWS:
            expiry_ts = ts + timedelta(minutes=expiry_min)
            max_j = min(i + expiry_min + 1, len(bars))

            outcome = "LOSS"  # default if no close in direction found
            for j in range(i + 1, max_j):
                f_ts, f_o, f_h, f_lo, f_cl = bars[j]
                if f_ts > expiry_ts:
                    break

                if direction == 1:  # LONG: win if any close > entry
                    if f_cl > entry:
                        outcome = "WIN"
                        break
                else:  # SHORT: win if any close < entry
                    if f_cl < entry:
                        outcome = "WIN"
                        break

            if outcome == "WIN":
                results_by_expiry[expiry_min]["wins"] += 1
            else:
                results_by_expiry[expiry_min]["losses"] += 1
            results_by_expiry[expiry_min]["total"] += 1

    return results_by_expiry


def main():
    report_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\hyperliquid_full")
    report_dir.mkdir(parents=True, exist_ok=True)

    skip_prefixes = ("NAS", "FR40", "HK50", "DE30", "LCO", "OIL")
    all_pairs = [k for k in ASSET_CONFIGS.keys() if not k.startswith(skip_prefixes)]
    all_results = {}

    for symbol in all_pairs:
        csv_path = find_csv(symbol)
        if not csv_path:
            continue
        config = ASSET_CONFIGS.get(symbol)
        if not config:
            continue

        pip_size = config.get("pip_value", 0.0001)
        print(f"\n{symbol} ({csv_path})...")
        bars = load_bars(csv_path)
        if not bars:
            print("  No bars loaded")
            continue

        print(f"  {len(bars)} bars, {bars[0][0].date()} -> {bars[-1][0].date()}")
        results = run_binary(bars, pip_size)

        # Print results for each expiry
        print(f"  {'Expiry':>8} {'Signals':>8} {'Wins':>6} {'Loss':>6} {'WR%':>7}")
        best_wr = 0
        best_exp = 0
        above_75 = []
        for exp in EXPIRY_WINDOWS:
            r = results[exp]
            if r["total"] > 0:
                wr = r["wins"] / r["total"] * 100
                print(f"  {exp:>5}min {r['total']:>8} {r['wins']:>6} {r['losses']:>6} {wr:>6.1f}%")
                if wr > best_wr:
                    best_wr = wr
                    best_exp = exp
                if wr >= 75:
                    above_75.append(exp)

        print(f"  Best: {best_exp}min @ {best_wr:.1f}% WR")
        print(f"  Expiry windows >= 75% WR: {above_75}")

        all_results[symbol] = {
            str(exp): {
                "total": results[exp]["total"],
                "wins": results[exp]["wins"],
                "losses": results[exp]["losses"],
                "wr": round(results[exp]["wins"] / results[exp]["total"] * 100, 1) if results[exp]["total"] > 0 else 0
            }
            for exp in EXPIRY_WINDOWS
        }
        all_results[symbol]["best_expiry"] = best_exp
        all_results[symbol]["best_wr"] = round(best_wr, 1)
        all_results[symbol]["above_75"] = above_75

    # Summary table
    print("\n\n" + "=" * 120)
    print("  P90 BINARY TEST — EXPIRY SWEEP (3AM-12PM EST, Win = close in direction by expiry)")
    print("=" * 120)

    header = f"{'Pair':<10}"
    for exp in EXPIRY_WINDOWS:
        header += f" {exp:>5}m"
    header += f" {'Best':>6} {'WR%':>6}"
    print(header)
    print("-" * 120)

    for sym in all_pairs:
        if sym not in all_results or "best_expiry" not in all_results[sym]:
            continue
        row = f"{sym:<10}"
        for exp in EXPIRY_WINDOWS:
            wr_data = all_results[sym].get(str(exp), {})
            wr = wr_data.get("wr", 0)
            row += f" {wr:>5.1f}"
        row += f" {all_results[sym]['best_expiry']:>5}m {all_results[sym]['best_wr']:>5.1f}%"
        print(row)

    with open(report_dir / "p90_binary_simple_all_pairs.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {report_dir / 'p90_binary_simple_all_pairs.json'}")


if __name__ == "__main__":
    main()
