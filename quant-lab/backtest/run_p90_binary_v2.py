"""
P90 BINARY EXCURSION TEST V2
=============================
Exact replication of the manual's binary test that yielded 83.3% WR.

METHODOLOGY (from CEREBUS FX v4 Manual):
1. P90 Activation: M5 candle body >= threshold for that time window
2. Direction: LONG if close above Asian High, SHORT if close below Asian Low
3. Entry: Close of P90 candle
4. Win: Price hits -25% Asian Range target (from Asian boundary)
5. Loss: Price closes beyond 80% of P90 body against the trade
6. Time limit: 90 minutes (18 M5 candles)

This is NOT "any close above entry" — it's target vs boundary.
"""
import sys, json, csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab")))

from configs.asset_configs import ASSET_CONFIGS

EST = timezone(timedelta(hours=-5))
EST_OFFSET = -5

# Manual's P90 thresholds for EUR/USD (reference)
MANUAL_THRESHOLDS = {
    2: 4.1, 4: 4.6, 6: 4.6, 8: 5.9, 10: 6.2
}

SCAN_CANDLES = 18  # 90 minutes


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
    """Dynamic P90 threshold discovery per 2-hour bucket."""
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
            sorted_bodies = sorted(bodies)
            idx = int(len(sorted_bodies) * 0.9)
            thresholds[bucket] = sorted_bodies[min(idx, len(sorted_bodies) - 1)]
        else:
            thresholds[bucket] = MANUAL_THRESHOLDS.get(bucket, 4.6)
    return thresholds


def compute_asian_range(bars, current_idx):
    """Compute Asian Range: high/low between 7PM prev day and 3AM EST."""
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


def run_binary_test(symbol, bars, config):
    """
    Binary Excursion Test:
    - Win: Price hits -25% Asian Range target
    - Loss: Price closes beyond 80% of P90 body against trade
    - Timeout: Neither within 90 min
    """
    pip_size = config.get("pip_value", 0.0001)
    p90_thresholds = compute_p90_thresholds(bars, pip_size)

    results = []

    for i, (ts, o, h, lo, cl) in enumerate(bars):
        est_hour = (ts.hour + EST_OFFSET) % 24
        if est_hour < 2 or est_hour >= 11:
            continue

        bucket = (est_hour // 2) * 2
        threshold = p90_thresholds.get(bucket, MANUAL_THRESHOLDS.get(bucket, 4.6))

        body_pips = abs(cl - o) / pip_size
        if body_pips < threshold:
            continue

        asian_high, asian_low = compute_asian_range(bars, i)
        if asian_high == 0.0 or asian_low == float('inf'):
            continue

        # Direction: LONG if close above Asian High, SHORT if close below Asian Low
        if cl > asian_high:
            direction = 1  # LONG
            ar_range = asian_high - asian_low  # AR in price units
            # Target: -25% AR from Asian boundary (extension)
            target_price = asian_high + ar_range * 0.25
            # Loss: close below entry by 80% of P90 body
            p90_body_price = abs(cl - o)
            loss_price = cl - p90_body_price * 0.80
        elif cl < asian_low:
            direction = -1  # SHORT
            ar_range = asian_high - asian_low
            # Target: -25% AR from Asian boundary (extension)
            target_price = asian_low - ar_range * 0.25
            # Loss: close above entry by 80% of P90 body
            p90_body_price = abs(cl - o)
            loss_price = cl + p90_body_price * 0.80
        else:
            continue

        entry_price = cl

        # Scan forward up to 18 candles (90 minutes)
        outcome = "TIMEOUT"
        time_to_result = 90
        max_j = min(i + SCAN_CANDLES + 1, len(bars))

        for j in range(i + 1, max_j):
            f_ts, f_o, f_h, f_lo, f_cl = bars[j]
            minutes_elapsed = (f_ts - ts).total_seconds() / 60.0

            if direction == 1:  # LONG
                # Win: High touches target
                if f_h >= target_price:
                    outcome = "WIN"
                    time_to_result = minutes_elapsed
                    break
                # Loss: Close below loss boundary
                if f_cl <= loss_price:
                    outcome = "LOSS"
                    time_to_result = minutes_elapsed
                    break
            else:  # SHORT
                # Win: Low touches target
                if f_lo <= target_price:
                    outcome = "WIN"
                    time_to_result = minutes_elapsed
                    break
                # Loss: Close above loss boundary
                if f_cl >= loss_price:
                    outcome = "LOSS"
                    time_to_result = minutes_elapsed
                    break

        results.append({
            'entry_time': ts,
            'direction': 'LONG' if direction == 1 else 'SHORT',
            'entry_price': entry_price,
            'body_pips': round(body_pips, 1),
            'threshold': round(threshold, 1),
            'ar_pips': round(ar_range / pip_size, 1) if ar_range > 0 else 0,
            'target_pips': round(abs(target_price - entry_price) / pip_size, 1),
            'sl_pips': round(abs(loss_price - entry_price) / pip_size, 1),
            'outcome': outcome,
            'minutes': round(time_to_result, 1),
            'est_hour': est_hour,
        })

    return results, p90_thresholds


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

        print(f"\n{symbol} ({csv_path})...")
        bars = load_bars(csv_path)
        if not bars:
            print("  No bars loaded")
            continue

        print(f"  {len(bars)} bars, {bars[0][0].date()} -> {bars[-1][0].date()}")

        results, thresholds = run_binary_test(symbol, bars, config)

        if not results:
            print("  No P90 signals found")
            all_results[symbol] = {"trades": 0, "thresholds": {}}
            continue

        wins = [r for r in results if r['outcome'] == 'WIN']
        losses = [r for r in results if r['outcome'] == 'LOSS']
        timeouts = [r for r in results if r['outcome'] == 'TIMEOUT']
        decisive = wins + losses

        wr = len(wins) / len(decisive) * 100 if decisive else 0
        avg_win_time = sum(r['minutes'] for r in wins) / len(wins) if wins else 0
        avg_loss_time = sum(r['minutes'] for r in losses) / len(losses) if losses else 0
        avg_target = sum(r['target_pips'] for r in results) / len(results) if results else 0
        avg_sl = sum(r['sl_pips'] for r in results) / len(results) if results else 0
        avg_ar = sum(r['ar_pips'] for r in results) / len(results) if results else 0

        # Timing analysis
        win_times = sorted([r['minutes'] for r in wins])
        t30_45 = len([t for t in win_times if 30 <= t < 45])
        t45_60 = len([t for t in win_times if 45 <= t <= 60])
        t60_90 = len([t for t in win_times if 60 < t <= 90])

        # By time bucket
        bucket_stats = defaultdict(lambda: {'w': 0, 'l': 0})
        for r in results:
            if r['outcome'] == 'TIMEOUT':
                continue
            b = (r['est_hour'] // 2) * 2
            if r['outcome'] == 'WIN':
                bucket_stats[b]['w'] += 1
            else:
                bucket_stats[b]['l'] += 1

        days = (bars[-1][0] - bars[0][0]).days if len(bars) > 1 else 0

        print(f"  Signals: {len(results)} | W: {len(wins)} | L: {len(losses)} | T: {len(timeouts)}")
        print(f"  WR: {wr:.1f}% | Avg win: {avg_win_time:.0f}min | Avg loss: {avg_loss_time:.0f}min")
        print(f"  Avg AR: {avg_ar:.1f}p | Avg target: {avg_target:.1f}p | Avg SL: {avg_sl:.1f}p")
        print(f"  Tr/D: {len(results)/days:.1f}" if days > 0 else "")
        print(f"  Timing: 30-45m={t30_45} 45-60m={t45_60} 60-90m={t60_90}")
        print(f"  Thresholds: {{{', '.join(f'{k}: {v:.1f}p' for k, v in sorted(thresholds.items()))}}}")
        bucket_strs = []
        for b, s in sorted(bucket_stats.items()):
            total = s['w'] + s['l']
            pct = s['w'] / total * 100 if total > 0 else 0
            bucket_strs.append(f"{b}: {s['w']}W/{s['l']}L ({pct:.0f}%)")
        print(f"  By bucket: {{{', '.join(bucket_strs)}}}")

        all_results[symbol] = {
            'signals': len(results), 'wins': len(wins), 'losses': len(losses),
            'timeouts': len(timeouts), 'win_rate': round(wr, 1),
            'avg_win_time': round(avg_win_time, 1), 'avg_loss_time': round(avg_loss_time, 1),
            'avg_ar_pips': round(avg_ar, 1), 'avg_target_pips': round(avg_target, 1),
            'avg_sl_pips': round(avg_sl, 1), 'tr_per_day': round(len(results) / days, 1) if days > 0 else 0,
            'days': days, 'timing_45_60': t45_60,
            'thresholds': {k: round(v, 2) for k, v in sorted(thresholds.items())},
        }

    # Summary
    print("\n\n" + "=" * 100)
    print("  P90 BINARY EXCURSION TEST V2 — MULTI-PAIR RESULTS")
    print("  Win = -25% AR target hit | Loss = 80% body close | Timeout = 90min")
    print("=" * 100)
    h = f"{'Pair':<10} {'Sig':>6} {'WR%':>6} {'W':>5} {'L':>5} {'T':>5} {'Tr/D':>5} {'AR':>5} {'Tgt':>5} {'SL':>5} {'45-60':>6}"
    print(h)
    print("-" * 80)

    for sym, r in sorted(all_results.items(), key=lambda x: x[1].get('win_rate', 0), reverse=True):
        if r['signals'] > 0:
            print(f"{sym:<10} {r['signals']:>6} {r['win_rate']:>5.1f}% {r['wins']:>5} {r['losses']:>5} {r['timeouts']:>5} {r['tr_per_day']:>5} {r['avg_ar_pips']:>5.1f} {r['avg_target_pips']:>5.1f} {r['avg_sl_pips']:>5.1f} {r['timing_45_60']:>6}")

    with open(report_dir / "p90_binary_v2_all_pairs.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {report_dir / 'p90_binary_v2_all_pairs.json'}")


if __name__ == "__main__":
    main()
