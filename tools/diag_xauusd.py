"""Diagnose XAUUSD Python ST trade count issue."""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab')
sys.path.insert(0, 'quant-lab/configs')

import pandas as pd
import numpy as np
from collections import Counter

data = pd.read_csv('quant-lab/data/XAUUSD_M5.csv', parse_dates=['timestamp'])
data['est_hour'] = (data['timestamp'].dt.hour + 19) % 24
data['date'] = data['timestamp'].dt.date

# Asian session: 7PM-3AM EST
asian = data[(data['est_hour'] >= 19) | (data['est_hour'] < 3)]
daily_asian = asian.groupby('date').agg(
    asian_high=('high', 'max'),
    asian_low=('low', 'min')
)
daily_asian['range_pips'] = (daily_asian['asian_high'] - daily_asian['asian_low']) / 0.1

print('Asian Range Distribution (pips):')
print(daily_asian['range_pips'].describe())
print()

for pct in [10, 25, 50, 75, 90, 95, 99]:
    val = daily_asian['range_pips'].quantile(pct/100)
    print(f'  P{pct}: {val:.1f} pips')

T1_MAX = 32.0
T2_MAX = 58.0
T3_MAX = 95.0

t1 = (daily_asian['range_pips'] <= T1_MAX).sum()
t2 = ((daily_asian['range_pips'] > T1_MAX) & (daily_asian['range_pips'] <= T2_MAX)).sum()
t3 = ((daily_asian['range_pips'] > T2_MAX) & (daily_asian['range_pips'] <= T3_MAX)).sum()
nogo = (daily_asian['range_pips'] > T3_MAX).sum()
total = len(daily_asian)

print(f'\nTier Classification (XAUUSD tiers: T1<={T1_MAX}, T2<={T2_MAX}, T3<={T3_MAX}):')
print(f'T1: {t1} ({t1/total*100:.1f}%)')
print(f'T2: {t2} ({t2/total*100:.1f}%)')
print(f'T3: {t3} ({t3/total*100:.1f}%)')
print(f'NO-GO: {nogo} ({nogo/total*100:.1f}%)')
print(f'Total sessions: {total}')

# Now run the engine and track WHY trades are low
from engines.symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection, EngineState

tier_config = {
    'T1': {'ar_max': 32.0, 'au': 16.0, 'trigger': 19.0},
    'T2': {'ar_max': 58.0, 'au': 29.0, 'trigger': 35.0},
    'T3': {'ar_max': 95.0, 'au': 48.0, 'trigger': 58.0},
}

engine = SymmetryTrapEngine(pip_size=0.1, tier_config=tier_config, symbol='XAUUSD')

current_date = None
asian_high = None
asian_low = None
session_init_count = 0
session_count = 0
no_go_count = 0
bars_processed = 0

timestamps = data['timestamp'].values
opens = data['open'].values
highs = data['high'].values
lows = data['low'].values
closes = data['close'].values

for i in range(len(data)):
    ts = pd.Timestamp(timestamps[i])
    est_hour = (ts.hour + 19) % 24
    bar_date = ts.date()
    
    if current_date != bar_date:
        current_date = bar_date
        asian_high = None
        asian_low = None
        engine.hard_exit()
    
    h = float(highs[i])
    lo = float(lows[i])
    
    in_asian = (est_hour >= 19 or est_hour < 3)
    if in_asian:
        if asian_high is None or h > asian_high:
            asian_high = h
        if asian_low is None or lo < asian_low:
            asian_low = lo
        continue
    
    if est_hour >= 12:
        if engine.session_active:
            engine.hard_exit()
        continue
    
    if est_hour == 3 and asian_high is not None and asian_low is not None:
        session_init_count += 1
        engine.initialize_session(asian_high, asian_low)
        if engine.session_active:
            session_count += 1
        else:
            no_go_count += 1
        continue
    
    if not engine.session_active:
        continue
    
    bars_processed += 1
    bar = Bar(timestamp=ts.to_pydatetime(), open=float(opens[i]), high=h, low=lo, close=float(closes[i]))
    engine.process_bar(bar)

entries = [s for s in engine.signal_log if s.event == 'ENTRY']
tp_hits = [s for s in engine.signal_log if s.event == 'TP_HIT']
sl_hits = [s for s in engine.signal_log if s.event == 'SL_HIT']
ks = [s for s in engine.signal_log if s.event == 'KILL_SWITCH']

print(f'\n--- Engine Results ---')
print(f'Sessions init: {session_init_count}, Active: {session_count}, NO-GO: {no_go_count}')
print(f'Bars processed (post-init, pre-noon): {bars_processed}')
print(f'Entries: {len(entries)}, TP: {len(tp_hits)}, SL: {len(sl_hits)}, KS: {len(ks)}')
print(f'Completed trades: {len(tp_hits)+len(sl_hits)}')

loop_dist = Counter(s.loop_count for s in entries)
print(f'Loop distribution: {dict(sorted(loop_dist.items()))}')

# COMPARE: The campaign found 604 trades. Nautilus found 1,718.
# Let's check: does Nautilus process differently?
# Key question: Does Nautilus process bars DURING the init bar itself?
# In our code, we `continue` after init, skipping the rest of the 3AM bar.
# Nautilus does NOT skip it — it sets swing_origin from the init bar close,
# then continues processing. Let's check if that matters.

print(f'\n--- Key Diagnostic ---')
print(f'NO-GO rate: {no_go_count/session_init_count*100:.1f}%')
print(f'Trades per active session: {(len(tp_hits)+len(sl_hits))/max(session_count,1):.2f}')
print(f'Expected ~1+ trades per active session minimum')
print(f'If most sessions have 0 trades, the impulse/retree thresholds may be too tight')
