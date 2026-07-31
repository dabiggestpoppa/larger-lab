"""
P90 BINARY EXCURSION TEST — CORRECT IMPLEMENTATION
===================================================
From the manual (Slide 5 — Binary Leg: Dynamic Expiry By Time-of-Day):

1. Entry: P90 candle close (body >= 90th percentile for 2h bucket)
2. Direction: LONG if close above Asian High, SHORT if close below Asian Low
3. Expiry: Fixed time window (sweep 1-120 min)
4. Win: Price CLOSES in direction by expiry (above entry for LONG, below for SHORT)
5. Loss: Price CLOSES against by expiry

NO target levels. NO stop loss. Just directional close within time window.

Phase 1: Sweep expiry 1-120 min, find all windows >75% WR per pair
Phase 2: For windows >75%, find optimal cascade add timing (2nd entry)
"""
import sys, json, csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab")))

from configs.asset_configs import ASSET_CONFIGS

EST = timezone(timedelta(hours=-5))
EST_OFFSET = -5


def find_csv(symbol: str):
    patterns = [
        f"quant-lab/data/{symbol}_M5.csv",
        f"quant-lab/data/{symbol}_M5_fetched.csv",
        f"quant-lab/data/{symbol}PRO_M5_2023_2026.csv",
        f"quant-lab/data/{symbol}PRO_M5_2023_2025.csv",
        f"quant-lab/data/{symbol}PRO_M5.csv",
    ]
    for p in patterns:
        if Path(p).exists():
            return p
    return None


def load_bars(csv_path: str):
    bars = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts_raw = (row.get("timestamp") or row.get("time") or row.get("date") or row.get("datetime"))
                if not ts_raw:
                    continue
                ts = None
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"]:
                    try:
                        ts = datetime.strptime(ts_raw.strip(), fmt).replace(tzinfo=EST)
                        break
                    except ValueError:
                        continue
                if ts is None:
                    continue
                o = float(row.get("open") or row.get("Open"))
                h = float(row.get("high") or row.get("High"))
                lo = float(row.get("low") or row.get("Low"))
                cl = float(row.get("close") or row.get("Close"))
                bars.append((ts, o, h, lo, cl))
            except (ValueError, KeyError):
                continue
    bars.sort(key=lambda b: b[0])
    return bars


def compute_p90_thresholds(bars, pip_size):
    """Dynamic P90 thresholds per 2-hour bucket."""
    bucket_bodies = defaultdict(list)
    for ts, o, h, lo, cl in bars:
        est_hour = (ts.hour + EST_OFFSET) % 24
        if est_hour < 2 or est_hour >= 11:
            continue
        bucket = (est_hour // 2) * 2
        body_pips = abs(cl - o) / pip_size
        bucket_bodies[bucket].append(body_pips)

    thresholds = {}
    for bucket, bodies in sorted(bucket_bodies.items()):
        if len(bodies) >= 10:
            s = sorted(bodies)
            idx = int(len(s) * 0.9)
            thresholds[bucket] = s[min(idx, len(s) - 1)]
        else:
            thresholds[bucket] = {2: 4.1, 4: 4.6, 6: 4.6, 8: 5.9, 10: 6.2}.get(bucket, 4.6)
    return thresholds


def compute_asian_range(bars, current_idx):
    """Asian Range: high/low between 7PM prev day and 3AM EST."""
    current_ts = bars[current_idx][0]
    current_date = current_ts.astimezone(EST).date()
    asian_start = datetime.combine(current_date - timedelta(days=1), datetime.min.time().replace(hour=19), tzinfo=EST)
    asian_end = datetime.combine(current_date, datetime.min.time().replace(hour=3), tzinfo=EST)

    asian_high = 0.0
    asian_low = float('inf')
    found = False

    for j in range(current_idx, -1, -1):
        ts = bars[j][0]
        if ts >= asian_end:
            continue
        if ts < asian_start:
            break
        _, o, h, lo, cl = bars[j]
        asian_high = max(asian_high, h)
        asian_low = min(asian_low, lo)
        found = True

    return (asian_high, asian_low) if found else (0.0, float('inf'))


def run_binary_for_expiry(bars, expiry_minutes, p90_thresholds, pip_size):
    """
    Run binary test for a single expiry window.
    Win = price closes in direction by expiry.
    Loss = price closes against by expiry.
    """
    results = []

    for i, (ts, o, h, lo, cl) in enumerate(bars):
        est_hour = (ts.hour + EST_OFFSET) % 24
        if est_hour < 2 or est_hour >= 11:
            continue

        bucket = (est_hour // 2) * 2
        threshold = p90_thresholds.get(bucket, 4.6)
        body_pips = abs(cl - o) / pip_size
        if body_pips < threshold:
            continue

        asian_high, asian_low = compute_asian_range(bars, i)
        if asian_high == 0.0 or asian_low == float('inf'):
            continue

        if cl > asian_high:
            direction = 1  # LONG
        elif cl < asian_low:
            direction = -1  # SHORT
        else:
            continue

        entry_price = cl
        expiry_time = ts + timedelta(minutes=expiry_minutes)

        # Scan forward until expiry
        outcome = "TIMEOUT"
        max_j = min(i + expiry_minutes + 1, len(bars))

        for j in range(i + 1, max_j):
            f_ts, f_o, f_h, f_lo, f_cl = bars[j]
            if f_ts > expiry_time:
                break

            if direction == 1:  # LONG
                if f_cl > entry_price:
                    outcome = "WIN"
                    break
                if f_cl < entry_price:
                    outcome = "LOSS"
                    break
            else:  # SHORT
                if f_cl < entry_price:
                    outcome = "WIN"
                    break
                if f_cl > entry_price:
                    outcome = "LOSS"
                    break

        results.append(outcome)

    return results


def main():
    report_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\hyperliquid_full")
    report_dir.mkdir(parents=True, exist_ok=True)

    skip_prefixes = ("NAS", "FR40", "HK50", "DE30", "LCO", "OIL")
    all_pairs = [k for k in ASSET_CONFIGS.keys() if not k.startswith(skip_prefixes)]

    # Expiry windows to test: every 5 min from 5 to 120
    expiry_windows = list(range(5, 121, 5))

    all_results = {}

    for symbol in all_pairs:
        csv_path = find_csv(symbol)
        if not csv_path:
            continue
        config = ASSET_CONFIGS.get(symbol)
        if not config:
            continue

        print(f"\n{symbol}...")
        bars = load_bars(csv_path)
        if not bars:
            continue

        pip_size = config.get("pip_value", 0.0001)
        p90_thresholds = compute_p90_thresholds(bars, pip_size)

        # Phase 1: Sweep expiry windows
        expiry_results = {}
        best_wr = 0
        best_expiry = 0

        for expiry in expiry_windows:
            results = run_binary_for_expiry(bars, expiry, p90_thresholds, pip_size)
            if not results:
                continue
            wins = results.count("WIN")
            losses = results.count("LOSSES") if "LOSSES" in results else results.count("LOSS")
            timeouts = results.count("TIMEOUT")
            decisive = wins + losses
            if decisive < 10:
                continue
            wr = wins / decisive * 100
            expiry_results[expiry] = {
                'signals': len(results), 'wins': wins, 'losses': losses,
                'timeouts': timeouts, 'wr': round(wr, 1)
            }
            if wr > best_wr:
                best_wr = wr
                best_expiry = expiry

        # Find all windows >75% WR
        high_wr_windows = {e: r for e, r in expiry_results.items() if r['wr'] >= 75.0}

        print(f"  Best: {best_expiry}min @ {best_wr:.1f}% WR")
        print(f"  Windows >75% WR: {len(high_wr_windows)}")
        if high_wr_windows:
            sorted_windows = sorted(high_wr_windows.items(), key=lambda x: x[1]['wr'], reverse=True)
            for e, r in sorted_windows[:5]:
                print(f"    {e}min: {r['wr']:.1f}% ({r['wins']}W/{r['losses']}L/{r['timeouts']}T)")

        all_results[symbol] = {
            'best_expiry': best_expiry,
            'best_wr': best_wr,
            'high_wr_windows': {str(e): r for e, r in high_wr_windows.items()},
            'all_expiries': {str(e): r for e, r in expiry_results.items()},
            'thresholds': {k: round(v, 2) for k, v in sorted(p90_thresholds.items())},
        }

    # Summary
    print("\n\n" + "=" * 90)
    print("  P90 BINARY TEST — EXPIRY SWEEP RESULTS")
    print("  Win = close in direction by expiry | Loss = close against")
    print("=" * 90)
    h = f"{'Pair':<10} {'BestExp':>7} {'BestWR':>7} {'>75%':>5} {'Thresholds'}"
    print(h)
    print("-" * 80)

    for sym, r in sorted(all_results.items(), key=lambda x: x[1].get('best_wr', 0), reverse=True):
        if r['best_wr'] > 0:
            thresh_str = ', '.join(f'{k}:{v:.1f}p' for k, v in sorted(r['thresholds'].items()))
            print(f"{sym:<10} {r['best_expiry']:>5}min {r['best_wr']:>6.1f}% {len(r['high_wr_windows']):>5}  {thresh_str}")

    with open(report_dir / "p90_binary_expiry_sweep.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {report_dir / 'p90_binary_expiry_sweep.json'}")


if __name__ == "__main__":
    main()
