"""Debug: trace through cascade combo step by step."""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
from nautilus.data_loader import _parse_csv
from pathlib import Path
import pandas as pd

df = _parse_csv(Path(r'C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv'))
df = df.tail(50000).copy()
df['est_hour'] = (df.index.hour - 5 + 24) % 24
df['date'] = df.index.date

# Simulate the strategy logic with debug output
asian_high = None
asian_low = None
ar_pips = None
session_active = False
session_direction = None
initial_p90_time = None
initial_p90_price = None
cascade_count = 0
add_done = False
kill_switch = False
active_trades = 0
total_trades = 0
last_date = None

p90_thresholds = {(2, 4): 4.1, (4, 6): 4.6, (6, 8): 4.6, (8, 10): 5.9, (10, 11): 6.2}

def get_threshold(est_h):
    for (start, end), thresh in p90_thresholds.items():
        if start <= est_h < end:
            return thresh
    return 6.2

for i in range(50, len(df) - 1):
    row = df.iloc[i]
    ts = df.index[i]
    est_h = row['est_hour']
    date = row['date']
    o, h, l, c = row['open'], row['high'], row['low'], row['close']

    # New Day Reset
    if date != last_date:
        asian_high = None; asian_low = None; ar_pips = None
        session_active = False; session_direction = None
        initial_p90_time = None; initial_p90_price = None
        cascade_count = 0; add_done = False; kill_switch = False
        active_trades = 0; last_date = date

    # Asian Range
    if est_h >= 19 or est_h < 3:
        if asian_high is None: asian_high = h; asian_low = l
        else: asian_high = max(asian_high, h); asian_low = min(asian_low, l)
        if est_h == 3 and asian_high is not None and asian_low is not None:
            ar_pips = (asian_high - asian_low) * 10000
        continue

    if ar_pips is None or ar_pips <= 0: continue
    if ar_pips >= 45: continue  # NO-GO

    if est_h >= 12: continue
    if not (2 <= est_h < 11): continue

    # P90 Signal Detection
    body_pips = abs(c - o) * 10000
    threshold = get_threshold(est_h)
    bull_signal = (c > o) and (body_pips >= threshold)
    bear_signal = (c < o) and (body_pips >= threshold)

    if not bull_signal and not bear_signal: continue

    signal_dir = "LONG" if bull_signal else "SHORT"

    # Initial P90
    if not session_active:
        session_active = True; session_direction = signal_dir
        initial_p90_time = ts; initial_p90_price = c
        cascade_count = 1; add_done = False
        active_trades += 1; total_trades += 1
        print(f'  [INITIAL P90] {ts} | {signal_dir} | body={body_pips:.1f}p | AR={ar_pips:.1f}p | threshold={threshold}p')

    # Cascade P90
    elif session_active and session_direction == signal_dir:
        if cascade_count >= 3: continue
        if initial_p90_time is not None:
            ms = (ts - initial_p90_time).total_seconds() / 60.0
            if ms < 30 or ms > 90: continue
        cascade_count += 1
        active_trades += 1; total_trades += 1
        print(f'  [CASCADE {cascade_count-1}] {ts} | {signal_dir} | body={body_pips:.1f}p | AR={ar_pips:.1f}p')

    # 45-Min Add
    if session_active and not add_done and cascade_count >= 1 and initial_p90_time is not None:
        ms = (ts - initial_p90_time).total_seconds() / 60.0
        if 45 <= ms < 50:
            if session_direction == "LONG":
                ext_pips = (c - initial_p90_price) * 10000
            else:
                ext_pips = (initial_p90_price - c) * 10000
            if ext_pips >= 8.0:
                add_done = True
                active_trades += 1; total_trades += 1
                print(f'  [45MIN ADD] {ts} | ext={ext_pips:.1f}p')

print(f'\nTotal trades: {total_trades}')
