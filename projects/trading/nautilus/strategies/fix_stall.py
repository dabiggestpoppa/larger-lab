#!/usr/bin/env python3
"""Fix Stall_Harvest_CFD function in optimizer_v4.py"""
import re

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\projects\trading\nautilus\strategies\optimizer_v4.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = '# STRATEGY 2: STALL-HARVEST CFD (FIXED'
end_marker = '# STRATEGY 3: CONSTRAINT ANCHOR'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print(f'Could not find markers: start={start_idx}, end={end_idx}')
    exit(1)

new_func = '''# STRATEGY 2: STALL-HARVEST CFD (FIXED -- proper mean reversion)
# ======================================================================

def run_stall_harvest_cfd(df):
    """
    Stall-Harvest CFD -- FIXED v4b.

    Using 120% extension entry (more realistic than 168%):
    - P90 candle sets direction and activation level
    - Entry at 120% extension of P90 body beyond activation
    - Mean reversion: trade AGAINST P90 direction
    - SL: 80% of body from entry (tight structural stop)
    - TP: activation level (full reversion)
    - Timeout: 45 minutes to reach entry zone
    """
    df = prepare_data(df)
    trades = []

    for date in sorted(df['date'].unique()):
        day = get_day_data(df, date)
        ah, al, ar = calc_asian_range(day)
        if ar is None or ar > 45 or ar < 3:
            continue

        entry = day[(day['est_h'] >= 2) & (day['est_h'] < 11)]
        direction, p90 = None, None
        p90_time = None

        for idx, row in entry.iterrows():
            thresh = p90_threshold(row['est_h'])
            if row['body_pips'] >= thresh:
                direction = 'LONG' if row['close'] > row['open'] else 'SHORT'
                p90 = row
                p90_time = idx
                break

        if direction is None:
            continue

        activation = p90['close']
        body_pips = to_pips(abs(p90['close'] - p90['open']))

        # Entry zone: 120% extension beyond activation in P90 direction
        entry_zone = activation + to_price(body_pips * 1.20) * (1 if direction == 'LONG' else -1)

        # Mean reversion: trade AGAINST P90 direction
        rev_direction = 'SHORT' if direction == 'LONG' else 'LONG'

        if rev_direction == 'SHORT':
            rev_entry = entry_zone
            rev_sl = entry_zone + to_price(body_pips * 0.80)
            rev_tp = activation
        else:
            rev_entry = entry_zone
            rev_sl = entry_zone - to_price(body_pips * 0.80)
            rev_tp = activation

        post_p90 = day[(day.index > p90_time) & (day['est_h'] < 12)]
        if post_p90.empty:
            continue

        entered = False
        entry_idx = None

        for idx, row in post_p90.iterrows():
            if (idx - p90_time).total_seconds() > 2700:
                break

            if direction == 'LONG' and row['high'] >= entry_zone:
                entered = True
                entry_idx = idx
                break
            elif direction == 'SHORT' and row['low'] <= entry_zone:
                entered = True
                entry_idx = idx
                break

        if not entered:
            continue

        post_entry = day[(day.index > entry_idx) & (day['est_h'] < 17)]
        if post_entry.empty:
            continue

        trade = manage_trade(post_entry, rev_entry, rev_direction, rev_sl, rev_tp)
        if trade:
            trade['entry_time'] = entry_idx
            trade['ar_pips'] = ar
            trade['direction'] = rev_direction
            trades.append(trade)

    return calc_results(trades, "Stall_Harvest_CFD")


'''

new_content = content[:start_idx] + new_func + content[end_idx:]
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\projects\trading\nautilus\strategies\optimizer_v4.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print('Stall_Harvest_CFD rewritten successfully')
