"""Trace the exact flow for the first few P90 signals."""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
from nautilus.data_loader import _parse_csv
from pathlib import Path
import pandas as pd

df = _parse_csv(Path(r'C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv'))
df = df.tail(50000).copy()
df['est_hour'] = (df.index.hour - 5 + 24) % 24
df['date'] = df.index.date

p90_thresholds = {(2, 4): 4.1, (4, 6): 4.6, (6, 8): 4.6, (8, 10): 5.9, (10, 11): 6.2}

def get_thresh(eh):
    for (s, e), t in p90_thresholds.items():
        if s <= eh < e: return t
    return 6.2

asian_high = None; asian_low = None; ar_pips = None
tier_val = "NA"
session_active = False
session_direction = None
initial_p90_time = None; initial_p90_price = None
cascade_count = 0; add_done = False; kill_switch = False
active_trades = []; all_trades = []
daily_pnl = 0.0; last_date = None
skip_count = 0; signal_count = 0

for i in range(50, len(df) - 1):
    row = df.iloc[i]; ts = df.index[i]; est_h = row['est_hour']
    date = row['date']; o = row['open']; h = row['high']; l = row['low']; c = row['close']

    if date != last_date:
        for t in active_trades:
            if t.exit_time is None:
                dm = 1 if t.direction == "LONG" else -1
                t.pnl_pips = (c - t.entry_price) * dm * 10000
                t.exit_time = ts; t.exit_price = c
                t.result = "win" if t.pnl_pips > 0 else "loss"; t.exit_reason = "new_day"
                all_trades.append(t); daily_pnl += t.pnl_pips
        active_trades.clear()
        asian_high = None; asian_low = None; ar_pips = None; tier_val = "NA"
        session_active = False; session_direction = None
        initial_p90_time = None; initial_p90_price = None
        cascade_count = 0; add_done = False; kill_switch = False
        daily_pnl = 0.0; last_date = date

    # Asian Range
    if est_h >= 19 or est_h < 3:
        if asian_high is None: asian_high = h; asian_low = l
        else: asian_high = max(asian_high, h); asian_low = min(asian_low, l)
        if est_h == 3 and asian_high is not None and asian_low is not None:
            ar_pips = (asian_high - asian_low) * 10000
            if ar_pips < 20: tier_val = "T1"
            elif ar_pips < 30: tier_val = "T2"
            elif ar_pips < 45: tier_val = "T3"
            else: tier_val = "NO_GO"
        continue

    # THESE ARE THE KEY CHECKS
    if tier_val == "NO_GO": skip_count += 1; continue
    if ar_pips is None: skip_count += 1; continue
    if ar_pips <= 0: skip_count += 1; continue

    # Manage trades (simplified)
    if kill_switch:
        for t in active_trades:
            if t.exit_time is None:
                dm = 1 if t.direction == "LONG" else -1
                t.pnl_pips = (c - t.entry_price) * dm * 10000
                t.exit_time = ts; t.exit_price = c
                t.result = "win" if t.pnl_pips > 0 else "loss"; t.exit_reason = "kill_switch"
                all_trades.append(t)
        active_trades.clear(); session_active = False; kill_switch = False; continue

    if est_h >= 12:
        for t in active_trades:
            if t.exit_time is None:
                dm = 1 if t.direction == "LONG" else -1
                t.pnl_pips = (c - t.entry_price) * dm * 10000
                t.exit_time = ts; t.exit_price = c
                t.result = "win" if t.pnl_pips > 0 else "loss"; t.exit_reason = "hard_exit"
                all_trades.append(t)
        active_trades.clear(); session_active = False; continue

    if not (2 <= est_h < 11): continue

    # P90 Signal Detection
    body_pips = abs(c - o) * 10000
    threshold = get_thresh(est_h)
    bull_signal = (c > o) and (body_pips >= threshold)
    bear_signal = (c < o) and (body_pips >= threshold)
    if not bull_signal and not bear_signal: continue

    signal_count += 1
    signal_dir = "LONG" if bull_signal else "SHORT"

    if not session_active:
        session_active = True; session_direction = signal_dir
        initial_p90_time = ts; initial_p90_price = c
        cascade_count = 1; add_done = False
        active_trades.append({'entry': c, 'dir': signal_dir, 'sl': c - body_pips * 0.8 * 0.0001})
        all_trades.append({'entry': c, 'dir': signal_dir, 'exit': None, 'pnl': 0})
        print(f'  [P90] {ts} {signal_dir} body={body_pips:.1f}p AR={ar_pips:.1f}p thresh={threshold}p')
        if signal_count >= 20:
            break

print(f'\nTotal signals found: {signal_count}')
print(f'Skipped (NO-GO/None): {skip_count}')
print(f'Active trades: {len(active_trades)}')
print(f'All trades: {len(all_trades)}')
