"""Parse Nautilus debug output to compare session inits with Python engine."""
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

DATA_DIR = 'tools'
OUTPUT_FILE = f'{DATA_DIR}/naut_debug_output.txt'

with open(OUTPUT_FILE, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

print(f"Read {len(lines)} lines from {OUTPUT_FILE}")

inits = []
nogos = []
for line in lines:
    line = line.strip()
    if 'NAUT Session INIT' in line:
        m = re.search(r'AR=([-\d.]+)p', line)
        ts_m = re.search(r'bar_ts=(\d+)', line)
        eh_m = re.search(r'est_h=(\d+)', line)
        tier_m = re.search(r'tier=(\w+)', line)
        if m and ts_m and eh_m:
            ar = float(m.group(1))
            ts = int(ts_m.group(1))
            est_h = int(eh_m.group(1))
            tier = tier_m.group(1) if tier_m else '?'
            inits.append((ts, est_h, ar, tier))
    elif 'NAUT NO-GO' in line:
        m = re.search(r'AR=([-\d.]+)p', line)
        ts_m = re.search(r'bar_ts=(\d+)', line)
        if m and ts_m:
            nogos.append((int(ts_m.group(1)), float(m.group(1))))

print(f'\n=== NAUTILUS SESSION STATS ===')
print(f'Total Session INITS: {len(inits)}')
print(f'Total NO-GO: {len(nogos)}')

tier_counts = Counter(e[3] for e in inits)
print(f'\nINITS by tier: {dict(tier_counts)}')

est_h_counts = Counter(e[1] for e in inits)
print(f'\nINITS by EST hour:')
for h in sorted(est_h_counts):
    print(f'  est_h={h}: {est_h_counts[h]}')

neg_ar = sum(1 for e in inits if e[2] < 0)
print(f'\nINITS with negative AR: {neg_ar}')

# Group by EST date
EST = timezone(timedelta(hours=-5))
date_inits = defaultdict(list)
for ts, est_h, ar, tier in inits:
    dt_utc = datetime.fromtimestamp(ts/1e9, tz=timezone.utc)
    dt_est = dt_utc.astimezone(EST)
    dk = dt_est.strftime('%Y-%m-%d')
    date_inits[dk].append((est_h, ar, tier))

print(f'\nUnique dates with session inits: {len(date_inits)}')
multi_inits = {dk: v for dk, v in date_inits.items() if len(v) > 1}
print(f'Dates with multiple INITS: {len(multi_inits)}')
if multi_inits:
    sorted_multi = sorted(multi_inits.items())
    for dk, v in sorted_multi[:20]:
        details = ', '.join(f'EST={e[0]} AR={e[1]:.1f}p {e[2]}' for e in v)
        print(f'  {dk}: {len(v)} inits [{details}]')

# Count: how many days have INIT at est_h != 3 (not 3AM)?
non_3am = sum(1 for _, est_h, _, _ in inits if est_h != 3)
print(f'\nINITS at est_h != 3 (NOT 3AM): {non_3am}')

# First and last
print(f'\nFirst 3:')
for ts, est_h, ar, tier in inits[:3]:
    dt = datetime.fromtimestamp(ts/1e9, tz=timezone.utc)
    print(f'  UTC={dt} EST={est_h} AR={ar:.1f}p {tier}')

print(f'\nWith negative AR (first 5):')
neg_count = 0
for ts, est_h, ar, tier in inits:
    if ar < 0 and neg_count < 5:
        dt = datetime.fromtimestamp(ts/1e9, tz=timezone.utc)
        print(f'  UTC={dt} EST={est_h} AR={ar:.1f}p {tier}')
        neg_count += 1
