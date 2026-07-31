"""
P90 Binary Test — PER-ASSET CALIBRATED THRESHOLDS
==================================================
Calibrates P90 thresholds from each asset's own historical data,
then runs the binary expiry sweep.

This is the CORRECT methodology from the manual:
1. For each asset, compute 90th percentile of M5 body sizes per 2h bucket
2. Use those asset-specific thresholds for signal generation
3. Run binary expiry sweep (1-120min) with per-asset thresholds
"""
import sys, csv, json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab")))

UTC = timezone.utc
ACT_START_UTC = 8   # 3AM EST
ACT_END_UTC = 17    # 12PM EST
EXPIRY_WINDOWS = [1, 2, 3, 5, 10, 15, 20, 30, 45, 60, 90, 120]

# Pip sizes per asset
PIP_SIZES = {
    'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDJPY': 0.01, 'USDCHF': 0.0001,
    'AUDUSD': 0.0001, 'NZDUSD': 0.0001, 'USDCAD': 0.0001, 'EURGBP': 0.0001,
    'GBPJPY': 0.01, 'GBPAUD': 0.0001, 'GBPNZD': 0.0001, 'GBPCHF': 0.0001,
    'GBPCAD': 0.0001, 'EURJPY': 0.01, 'EURAUD': 0.0001, 'EURNZD': 0.0001,
    'EURCHF': 0.0001, 'EURCAD': 0.0001, 'AUDJPY': 0.01, 'AUDNZD': 0.0001,
    'AUDCHF': 0.0001, 'AUDCAD': 0.0001, 'NZDJPY': 0.01, 'NZDCHF': 0.0001,
    'NZDCAD': 0.0001, 'CADJPY': 0.01, 'CADCHF': 0.0001,
    'XAUUSD': 0.1, 'XAGUSD': 0.01,
    'BTCUSD': 1.0, 'ETHUSD': 1.0, 'SOLUSD': 1.0, 'XRPUSD': 0.0001,
    'US500': 1.0,
}

# CSV file patterns to search for each pair
def find_csv(pair_name):
    patterns = [
        f"quant-lab/data/{pair_name}_M5.csv",
        f"quant-lab/data/{pair_name}PRO_M5_2023_2026.csv",
        f"quant-lab/data/{pair_name}PRO_M5_2023_2025.csv",
        f"quant-lab/data/{pair_name}PRO_M5.csv",
        f"quant-lab/data/{pair_name}_M5_fetched.csv",
    ]
    for p in patterns:
        if Path(p).exists():
            return p
    return None


def load_bars(csv_path):
    bars = []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts_raw = row.get('timestamp') or row.get('time') or row.get('date')
                if not ts_raw: continue
                ts_raw = ts_raw.strip()
                ts = None
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S%z']:
                    try:
                        ts = datetime.strptime(ts_raw, fmt)
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=UTC)
                        break
                    except ValueError:
                        continue
                if ts is None:
                    try:
                        ts = datetime.fromtimestamp(int(ts_raw), tz=UTC)
                    except:
                        continue
                o = float(row.get('open') or row.get('Open'))
                h = float(row.get('high') or row.get('High'))
                lo = float(row.get('low') or row.get('Low'))
                cl = float(row.get('close') or row.get('Close'))
                bars.append((ts, o, h, lo, cl))
            except:
                continue
    bars.sort(key=lambda b: b[0])
    return bars


def calibrate_p90_thresholds(bars, pip_size):
    """
    Phase 1: Dynamic P90 threshold discovery.
    Group M5 candles by 2-hour UTC bucket within activation window.
    Compute 90th percentile of absolute body size for each bucket.
    """
    bucket_bodies = defaultdict(list)
    for ts, o, h, lo, cl in bars:
        utc_hour = ts.hour
        if utc_hour < ACT_START_UTC or utc_hour >= ACT_END_UTC:
            continue
        bucket = (utc_hour // 2) * 2
        body_pips = abs(cl - o) / pip_size
        bucket_bodies[bucket].append(body_pips)

    thresholds = {}
    for bucket in [(ACT_START_UTC // 2) * 2 + i * 2 for i in range((ACT_END_UTC - ACT_START_UTC) // 2)]:
        bodies = bucket_bodies.get(bucket, [])
        if len(bodies) >= 10:
            sorted_bodies = sorted(bodies)
            idx = int(len(sorted_bodies) * 0.9)
            thresholds[bucket] = sorted_bodies[min(idx, len(sorted_bodies) - 1)]
        else:
            thresholds[bucket] = 4.6  # fallback
    return thresholds


def run_binary(bars, pip_size, thresholds):
    """Phase 2: Binary outcome excursion test."""
    results = {exp: {'wins': 0, 'losses': 0, 'total': 0} for exp in EXPIRY_WINDOWS}
    signal_count = 0

    for i, (ts, o, h, lo, cl) in enumerate(bars):
        utc_hour = ts.hour
        if utc_hour < ACT_START_UTC or utc_hour >= ACT_END_UTC:
            continue

        body = abs(cl - o)
        bucket = (utc_hour // 2) * 2
        threshold = thresholds.get(bucket, 4.6) * pip_size
        if body < threshold:
            continue

        direction = 1 if cl > o else -1
        entry = cl
        signal_count += 1

        for expiry_min in EXPIRY_WINDOWS:
            expiry_ts = ts + timedelta(minutes=expiry_min)
            max_j = min(i + expiry_min + 1, len(bars))
            outcome = 'LOSS'
            for j in range(i + 1, max_j):
                f_ts, f_o, f_h, f_lo, f_cl = bars[j]
                if f_ts > expiry_ts:
                    break
                if direction == 1 and f_cl > entry:
                    outcome = 'WIN'
                    break
                if direction == -1 and f_cl < entry:
                    outcome = 'WIN'
                    break
            if outcome == 'WIN':
                results[expiry_min]['wins'] += 1
            else:
                results[expiry_min]['losses'] += 1
            results[expiry_min]['total'] += 1

    return results, signal_count


def main():
    report_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\hyperliquid_full")
    report_dir.mkdir(parents=True, exist_ok=True)

    # All pairs to test
    all_pairs = sorted(PIP_SIZES.keys())
    all_results = {}
    calibration_data = {}

    for pair_name in all_pairs:
        csv_path = find_csv(pair_name)
        if csv_path is None:
            print(f"\n{pair_name}: No CSV file found. Skipping.")
            continue

        pip_size = PIP_SIZES[pair_name]
        print(f"\n{pair_name} ({csv_path})...")

        bars = load_bars(csv_path)
        if not bars:
            print("  No bars loaded")
            continue
        print(f"  {len(bars)} bars, {bars[0][0].date()} -> {bars[-1][0].date()}")

        # Phase 1: Calibrate thresholds from this asset's own data
        thresholds = calibrate_p90_thresholds(bars, pip_size)
        calibration_data[pair_name] = {str(k): round(v, 4) for k, v in sorted(thresholds.items())}
        print(f"  Calibrated thresholds: {{{', '.join(f'{k}: {v:.2f}p' for k, v in sorted(thresholds.items()))}}}")

        # Phase 2: Run binary test with calibrated thresholds
        results, signal_count = run_binary(bars, pip_size, thresholds)
        print(f"  Signals: {signal_count}")

        # Print expiry sweep
        print(f"  {'Expiry':>8} {'Signals':>8} {'Wins':>6} {'Loss':>6} {'WR%':>7}")
        best_wr = 0
        best_exp = 0
        above_75 = []
        for exp in EXPIRY_WINDOWS:
            r = results[exp]
            if r['total'] > 0:
                wr = r['wins'] / r['total'] * 100
                print(f"  {exp:>5}min {r['total']:>8} {r['wins']:>6} {r['losses']:>6} {wr:>6.1f}%")
                if wr > best_wr:
                    best_wr = wr
                    best_exp = exp
                if wr >= 75:
                    above_75.append(exp)

        print(f"  Best: {best_exp}min @ {best_wr:.1f}% WR")
        print(f"  Expiry windows >= 75% WR: {above_75}")

        all_results[pair_name] = {
            'thresholds': calibration_data[pair_name],
            'signals': signal_count,
            'expiries': {
                str(exp): {
                    'total': results[exp]['total'],
                    'wins': results[exp]['wins'],
                    'losses': results[exp]['losses'],
                    'wr': round(results[exp]['wins'] / results[exp]['total'] * 100, 1) if results[exp]['total'] > 0 else 0
                }
                for exp in EXPIRY_WINDOWS
            },
            'best_expiry': best_exp,
            'best_wr': round(best_wr, 1),
            'above_75': above_75,
        }

    # Save full results
    output = {
        'methodology': 'Per-asset calibrated P90 thresholds from historical M5 data',
        'window': '3AM-12PM EST',
        'expiry_windows': EXPIRY_WINDOWS,
        'pairs': all_results,
    }
    with open(report_dir / 'p90_binary_calibrated_all_pairs.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n\nResults saved to {report_dir / 'p90_binary_calibrated_all_pairs.json'}")

    # Print summary table
    print("\n\n" + "=" * 100)
    print("  P90 BINARY TEST — PER-ASSET CALIBRATED THRESHOLDS")
    print("=" * 100)
    header = f"{'Pair':<10}"
    for exp in EXPIRY_WINDOWS:
        header += f" {exp:>5}m"
    header += f" {'Best':>6} {'WR%':>6}"
    print(header)
    print("-" * 90)

    for pair_name in all_pairs:
        if pair_name not in all_results:
            continue
        r = all_results[pair_name]
        row = f"{pair_name:<10}"
        for exp in EXPIRY_WINDOWS:
            wr_data = r['expiries'].get(str(exp), {})
            wr = wr_data.get('wr', 0)
            row += f" {wr:>5.1f}"
        row += f" {r['best_expiry']:>5}m {r['best_wr']:>5.1f}%"
        print(row)

    # Print calibrated thresholds summary
    print("\n\nCALIBRATED P90 THRESHOLDS (pips by 2h UTC bucket):")
    print(f"{'Pair':<10} {'8-10':>8} {'10-12':>8} {'12-14':>8} {'14-16':>8} {'16-17':>8}")
    print("-" * 60)
    for pair_name in all_pairs:
        if pair_name not in calibration_data:
            continue
        t = calibration_data[pair_name]
        print(f"{pair_name:<10} {t.get('8', 0):>8.2f} {t.get('10', 0):>8.2f} {t.get('12', 0):>8.2f} {t.get('14', 0):>8.2f} {t.get('16', 0):>8.2f}")


if __name__ == "__main__":
    main()
