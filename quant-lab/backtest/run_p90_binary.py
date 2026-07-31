"""
P90 BINARY EXCURSION TEST
=========================
Exact replication of the manual's binary test methodology.

METHODOLOGY (from CEREBUS FX v4 Manual):
1. P90 Activation: M5 candle body >= 90th percentile threshold for that 2h time bucket
2. Direction: LONG if close above Asian High, SHORT if close below Asian Low
3. Entry: Close of P90 candle
4. Win: Any future M5 candle CLOSES in trade direction within 90 min (18 candles)
5. Loss: Any future M5 candle CLOSES against trade direction within 90 min
6. Timeout: Neither happens within 90 min (excluded from WR)

No TP/SL levels. No kill switch. No EWS. Pure directional close vs time.
"""
import sys, json, csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab")))

from configs.asset_configs import ASSET_CONFIGS

EST = timezone(timedelta(hours=-5))
EST_OFFSET = -5

# 2-hour time buckets for dynamic P90 thresholds (from manual)
TIME_BUCKETS = [(2, 4), (4, 6), (6, 8), (8, 10), (10, 12)]

# Scan window: 90 minutes = 18 M5 candles (from manual)
SCAN_CANDLES = 18


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
    """
    Phase 1: Dynamic P90 Threshold Discovery.
    Group M5 candles by 2-hour time buckets, compute 90th percentile of absolute body size.
    Only use bars within activation window (2AM-11AM EST).
    """
    bucket_bodies = defaultdict(list)

    for ts, o, h, lo, cl in bars:
        est_hour = (ts.hour + EST_OFFSET) % 24
        if est_hour < 2 or est_hour >= 11:
            continue
        # Find 2-hour bucket
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
            thresholds[bucket] = 4.6  # default fallback

    return thresholds


def compute_asian_range(bars, current_idx):
    """
    Compute Asian Range: high/low of all bars between 7PM previous day and 3AM EST.
    """
    current_ts = bars[current_idx][0]
    current_date = current_ts.astimezone(EST).date()

    # Asian session: 7PM previous day to 3AM current day
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
    Phase 2: Binary Outcome Excursion Test.
    For each P90 activation, scan forward 18 candles (90 min) for directional close.
    """
    pip_size = config.get("pip_value", 0.0001)

    # Phase 1: Compute dynamic P90 thresholds
    p90_thresholds = compute_p90_thresholds(bars, pip_size)

    results = []
    session_date = None
    daily_signals = 0
    max_daily_signals = 3  # from manual: max 3 cascades + initial = ~4, but binary test uses 1st only

    for i, (ts, o, h, lo, cl) in enumerate(bars):
        est_hour = (ts.hour + EST_OFFSET) % 24

        # Activation window: 2AM-11AM EST
        if est_hour < 2 or est_hour >= 11:
            continue

        # New session tracking
        bar_date = ts.astimezone(EST).date()
        if bar_date != session_date:
            session_date = bar_date
            daily_signals = 0

        # Get P90 threshold for this 2-hour bucket
        bucket = (est_hour // 2) * 2
        threshold = p90_thresholds.get(bucket, 4.6)

        # Check if body >= P90 threshold
        body_pips = abs(cl - o) / pip_size
        if body_pips < threshold:
            continue

        # Compute Asian Range for direction
        asian_high, asian_low = compute_asian_range(bars, i)
        if asian_high == 0.0 or asian_low == float('inf'):
            continue

        # Direction: LONG if close above Asian High, SHORT if close below Asian Low
        if cl > asian_high:
            direction = 1  # LONG
        elif cl < asian_low:
            direction = -1  # SHORT
        else:
            continue  # Close inside Asian Range = no signal

        entry_price = cl

        # Scan forward up to 18 candles (90 minutes)
        outcome = "TIMEOUT"
        time_to_result = 90
        max_j = min(i + SCAN_CANDLES + 1, len(bars))

        for j in range(i + 1, max_j):
            f_ts, f_o, f_h, f_lo, f_cl = bars[j]
            minutes_elapsed = (f_ts - ts).total_seconds() / 60.0

            if direction == 1:  # LONG
                # Win: any M5 candle closes above entry
                if f_cl > entry_price:
                    outcome = "WIN"
                    time_to_result = minutes_elapsed
                    break
                # Loss: any M5 candle closes below entry
                if f_cl < entry_price:
                    outcome = "LOSS"
                    time_to_result = minutes_elapsed
                    break
            else:  # SHORT
                # Win: any M5 candle closes below entry
                if f_cl < entry_price:
                    outcome = "WIN"
                    time_to_result = minutes_elapsed
                    break
                # Loss: any M5 candle closes above entry
                if f_cl > entry_price:
                    outcome = "LOSS"
                    time_to_result = minutes_elapsed
                    break

        results.append({
            'entry_time': ts,
            'direction': 'LONG' if direction == 1 else 'SHORT',
            'entry_price': entry_price,
            'body_pips': round(body_pips, 1),
            'threshold': round(threshold, 1),
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

        # Compute stats (exclude timeouts from WR)
        wins = [r for r in results if r['outcome'] == 'WIN']
        losses = [r for r in results if r['outcome'] == 'LOSS']
        timeouts = [r for r in results if r['outcome'] == 'TIMEOUT']
        decisive = wins + losses

        wr = len(wins) / len(decisive) * 100 if decisive else 0
        avg_win_time = sum(r['minutes'] for r in wins) / len(wins) if wins else 0
        avg_loss_time = sum(r['minutes'] for r in losses) / len(losses) if losses else 0

        # Timing analysis: wins by time bucket
        timing_buckets = defaultdict(lambda: {'wins': 0, 'losses': 0})
        for r in results:
            if r['outcome'] == 'TIMEOUT':
                continue
            bucket = (r['est_hour'] // 2) * 2
            if r['outcome'] == 'WIN':
                timing_buckets[bucket]['wins'] += 1
            else:
                timing_buckets[bucket]['losses'] += 1

        # Cascade timing: wins by minutes to resolution
        win_times = sorted([r['minutes'] for r in wins])
        t30_45 = len([t for t in win_times if 30 <= t < 45])
        t45_60 = len([t for t in win_times if 45 <= t <= 60])
        t60_90 = len([t for t in win_times if 60 < t <= 90])

        days = (bars[-1][0] - bars[0][0]).days if len(bars) > 1 else 0

        print(f"  Signals: {len(results)} | Wins: {len(wins)} | Losses: {len(losses)} | Timeouts: {len(timeouts)}")
        print(f"  WR (excl. timeout): {wr:.1f}% | Avg win time: {avg_win_time:.0f}min | Avg loss time: {avg_loss_time:.0f}min")
        if days > 0:
            print(f"  Trades/day: {len(results)/days:.1f}")
        print(f"  Timing sweet spot (45-60min): {t45_60} wins")
        print(f"  P90 thresholds: {{{', '.join(f'{k}: {v:.1f}p' for k, v in sorted(thresholds.items()))}}}")

        all_results[symbol] = {
            'signals': len(results),
            'wins': len(wins),
            'losses': len(losses),
            'timeouts': len(timeouts),
            'win_rate': round(wr, 1),
            'avg_win_time': round(avg_win_time, 1),
            'avg_loss_time': round(avg_loss_time, 1),
            'tr_per_day': round(len(results) / days, 1) if days > 0 else 0,
            'days': days,
            'timing_sweet_spot_45_60': t45_60,
            'thresholds': {k: round(v, 2) for k, v in sorted(thresholds.items())},
        }

    # Summary
    print("\n\n" + "=" * 100)
    print("  P90 BINARY EXCURSION TEST — MULTI-PAIR RESULTS")
    print("=" * 100)
    h = f"{'Pair':<10} {'Signals':>8} {'WR%':>7} {'Wins':>6} {'Loss':>6} {'Tout':>6} {'Tr/D':>6} {'AvgWin':>7} {'45-60m':>7}"
    print(h)
    print("-" * 75)

    for sym, r in sorted(all_results.items(), key=lambda x: x[1].get('win_rate', 0), reverse=True):
        if r['signals'] > 0:
            print(f"{sym:<10} {r['signals']:>8} {r['win_rate']:>6.1f}% {r['wins']:>6} {r['losses']:>6} {r['timeouts']:>6} {r['tr_per_day']:>6} {r['avg_win_time']:>6.0f}m {r['timing_sweet_spot_45_60']:>6}")

    # Save results
    with open(report_dir / "p90_binary_all_pairs.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {report_dir / 'p90_binary_all_pairs.json'}")


if __name__ == "__main__":
    main()
