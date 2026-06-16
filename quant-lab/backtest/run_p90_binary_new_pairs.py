"""Binary test for new pairs: BTCUSD, ETHUSD, SOLUSD, XRPUSD"""
import sys, csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
ACT_START_UTC = 8
ACT_END_UTC = 17
EXPIRY_WINDOWS = [1, 2, 3, 5, 10, 15, 20, 30, 45, 60, 90, 120]

THRESHOLDS = {
    'BTCUSD': {8: 106.6, 10: 106.6, 12: 106.6, 14: 106.6, 16: 106.6},
    'ETHUSD': {8: 18.2, 10: 18.2, 12: 18.2, 14: 18.2, 16: 18.2},
    'SOLUSD': {8: 0.78, 10: 0.78, 12: 0.78, 14: 0.78, 16: 0.78},
    'XRPUSD': {8: 0.00078, 10: 0.00078, 12: 0.00078, 14: 0.00078, 16: 0.00078},
}
PIP_SIZES = {'BTCUSD': 1.0, 'ETHUSD': 1.0, 'SOLUSD': 1.0, 'XRPUSD': 0.0001}

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

def run_binary(bars, pip_size, thresholds):
    results = {exp: {'wins': 0, 'losses': 0, 'total': 0} for exp in EXPIRY_WINDOWS}
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
    return results

pairs = [
    ('BTCUSD', 'quant-lab/data/BTCUSD_M5.csv'),
    ('ETHUSD', 'quant-lab/data/ETHUSD_M5.csv'),
    ('SOLUSD', 'quant-lab/data/SOLUSD_M5.csv'),
    ('XRPUSD', 'quant-lab/data/XRPUSD_M5.csv'),
]

for name, path in pairs:
    print(f'\n{name} ({path})...')
    if not Path(path).exists():
        print('  File not found!')
        continue
    bars = load_bars(path)
    print(f'  {len(bars)} bars, {bars[0][0].date()} -> {bars[-1][0].date()}')
    pip_size = PIP_SIZES[name]
    thresholds = THRESHOLDS[name]
    results = run_binary(bars, pip_size, thresholds)
    print(f'  {"Expiry":>8} {"Signals":>8} {"Wins":>6} {"Loss":>6} {"WR%":>7}')
    best_wr = 0
    best_exp = 0
    above_75 = []
    for exp in EXPIRY_WINDOWS:
        r = results[exp]
        if r['total'] > 0:
            wr = r['wins'] / r['total'] * 100
            print(f'  {exp:>5}min {r["total"]:>8} {r["wins"]:>6} {r["losses"]:>6} {wr:>6.1f}%')
            if wr > best_wr:
                best_wr = wr
                best_exp = exp
            if wr >= 75:
                above_75.append(exp)
    print(f'  Best: {best_exp}min @ {best_wr:.1f}% WR')
    print(f'  Expiry windows >= 75% WR: {above_75}')
