"""Check: after ar_pips is set, do subsequent bars see it?"""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
from nautilus.data_loader import _parse_csv
from pathlib import Path
import pandas as pd

df = _parse_csv(Path(r'C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv'))
df = df.tail(50000).copy()
df['est_hour'] = (df.index.hour - 5 + 24) % 24
df['date'] = df.index.date

asian_high = None; asian_low = None; ar_pips = None
tier_val = "NA"
last_date = None
ar_set_count = 0
entry_check_count = 0

for i in range(50, len(df) - 1):
    row = df.iloc[i]; ts = df.index[i]; est_h = row['est_hour']
    date = row['date']; o = row['open']; h = row['high']; l = row['low']; c = row['close']

    if date != last_date:
        asian_high = None; asian_low = None; ar_pips = None; tier_val = "NA"
        last_date = date

    # Asian Range
    if est_h >= 19 or est_h < 3:
        if asian_high is None: asian_high = h; asian_low = l
        else: asian_high = max(asian_high, h); asian_low = min(asian_low, l)
        if est_h == 3 and asian_high is not None and asian_low is not None:
            ar_pips = (asian_high - asian_low) * 10000
            if ar_pips < 45:
                tier_val = "GO"
            else:
                tier_val = "NO_GO"
            ar_set_count += 1
            if ar_set_count <= 3:
                print(f"  [AR SET] {ts} | est_h={est_h} | AR={ar_pips:.1f}p | tier={tier_val}")
        continue

    # Check if ar_pips is set for entry window bars
    if ar_pips is not None and 2 <= est_h < 11:
        entry_check_count += 1
        if entry_check_count <= 5:
            body = abs(c - o) * 10000
            print(f"  [ENTRY CHECK] {ts} | est_h={est_h} | AR={ar_pips:.1f}p | body={body:.1f}p | tier={tier_val}")

print(f"\nar_set_count: {ar_set_count}")
print(f"entry_check_count: {entry_check_count}")
