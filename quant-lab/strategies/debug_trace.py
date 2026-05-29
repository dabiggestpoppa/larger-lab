"""
Diagnostic: What is the Symmetry Trap engine actually doing?
Trace individual trades to understand the failure mode.
"""
import sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range
from datetime import date
import pandas as pd

SPREAD_COST = 0.0  # zero spread to isolate the edge

TIERS = {
    'T1':  {'ar_max': 20, 'au': 10, 'trigger': 12, 'next_trig': 15},
    'T2':  {'ar_max': 30, 'au': 12, 'trigger': 15, 'next_trig': 19},
    'T3':  {'ar_max': 45, 'au': 15, 'trigger': 19, 'next_trig': 25},
}

def classify_tier(ar_pips):
    if ar_pips < 20:  return 'T1'
    if ar_pips < 30:  return 'T2'
    if ar_pips <= 45: return 'T3'
    return 'NO_GO'

df = load_data()

# Trace a few specific days
test_dates = [date(2024,1,15), date(2024,1,16), date(2024,1,17), date(2024,1,18), date(2024,2,1)]

for dk in test_dates:
    db = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
    ar = compute_asian_range(df, dk)
    if ar is None: continue
    tier = classify_tier(ar['ar_pips'])
    if tier == 'NO_GO': continue
    params = TIERS[tier]
    au = params['au']
    ah = ar['ah']; al = ar['al']
    ar_pips = ar['ar_pips']

    day = db[(db['est_hour']>=3) & (db['est_hour']<12)]
    bars_list = list(day.iterrows())

    # Find bias
    bias = 0; bias_idx = None
    for i, (_, bar) in enumerate(bars_list):
        if bar['close'] > ah: bias = 1; bias_idx = i; break
        if bar['close'] < al: bias = -1; bias_idx = i; break
    if bias == 0: continue

    # Find entry
    entry = None; entry_idx = None
    for j in range(bias_idx+1, len(bars_list)):
        _, bar = bars_list[j]
        body_pips = abs(bar['close']-bar['open'])*10000
        is_bull = bar['close']>bar['open']
        is_bear = bar['close']<bar['open']
        if bias==1 and is_bull and body_pips >= au*0.5:
            if j+1 < len(bars_list):
                _, nb = bars_list[j+1]
                if nb['close'] < nb['open']:
                    entry = nb['close']; entry_idx = j+1; break
        elif bias==-1 and is_bear and body_pips >= au*0.5:
            if j+1 < len(bars_list):
                _, nb = bars_list[j+1]
                if nb['close'] > nb['open']:
                    entry = nb['close']; entry_idx = j+1; break
    if entry is None: continue

    # Calculate targets
    ar_val = ar_pips/10000.0
    if bias == 1:
        t25 = ah + ar_val*0.25; t50 = ah + ar_val*0.50; t100 = ah + ar_val*1.00
        sl = al
    else:
        t25 = al - ar_val*0.25; t50 = al - ar_val*0.50; t100 = al - ar_val*1.00
        sl = ah

    # Trace outcome
    pos = 1.0; pnl = 0.0; t25h = False; t50h = False; exit_reason = "unknown"
    for j in range(entry_idx+1, len(bars_list)):
        _, bar = bars_list[j]
        c = bar['close']
        if bar['est_hour'] >= 12:
            pnl += (c - entry)*bias*10000.0*pos; pos = 0; exit_reason = "12PM"; break
        if bias==1 and c < sl:
            pnl += (c-entry)*10000.0*pos; pos = 0; exit_reason = "SL"; break
        if bias==-1 and c > sl:
            pnl += (entry-c)*10000.0*pos; pos = 0; exit_reason = "SL"; break
        if bias==1:
            if c >= t25 and not t25h: pnl += (t25-entry)*10000*0.5; pos-=0.5; t25h=True
            if c >= t50 and not t50h: pnl += (t50-entry)*10000*0.4; pos-=0.4; t50h=True
            if t50h and pos>0 and c>=t100: pnl += (t100-entry)*10000*pos; pos=0; exit_reason="T100"; break
        else:
            if c <= t25 and not t25h: pnl += (entry-t25)*10000*0.5; pos-=0.5; t25h=True
            if c <= t50 and not t50h: pnl += (entry-t50)*10000*0.4; pos-=0.4; t50h=True
            if t50h and pos>0 and c<=t100: pnl += (entry-t100)*10000*pos; pos=0; exit_reason="T100"; break
    if pos > 0:
        _, last_bar = bars_list[-1]
        pnl += (last_bar['close']-entry)*bias*10000.0*pos
        exit_reason = "end_of_data"

    dir_str = "LONG" if bias==1 else "SHORT"
    print(f"{dk} {dir_str} {tier} AR={ar_pips:.1f}p entry={entry:.5f}")
    print(f"  SL={sl:.5f} T25={t25:.5f} T50={t50:.5f} T100={t100:.5f}")
    print(f"  Result: {pnl:.1f}p ({exit_reason})")
    print()
