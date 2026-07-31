"""
BLIND CHAIN DIAGNOSTIC
======================
Why are there zero cascade trades even with 20-60% Goldilocks?
The v1 had 49 trades. The v2 has 0. Let me find out why.

v1 used gold_low <= row['close'] <= gold_high (standard)
My v2 uses the same but maybe the zone calc is wrong for SHORT.
"""
import sys, io
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range
from datetime import date
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TIERS = {
    'T1': {'ar_max': 20, 'trigger': 12, 'next_trig': 15, 'au': 10},
    'T2': {'ar_max': 30, 'trigger': 15, 'next_trig': 19, 'au': 12},
    'T3': {'ar_max': 45, 'trigger': 19, 'next_trig': 25, 'au': 15},
}
AU1 = {2: 4.1, 3: 4.1, 4: 4.6, 5: 4.6, 6: 4.6, 7: 5.9, 8: 5.9, 9: 6.2, 10: 6.2, 11: 6.2}


def classify_tier(ar_pips):
    if ar_pips < 20:  return 'T1'
    if ar_pips < 30:  return 'T2'
    if ar_pips <= 45: return 'T3'
    return 'NO_GO'


def get_p90_threshold(est_hour):
    h = int(est_hour)
    if h < 2: return 4.1
    if h > 11: return 6.2
    return AU1.get(h, 4.6)


def run_diagnostic(df, start_date, end_date):
    """Trace cascade analysis for diagnostic"""
    df = df[(df['est_date'] >= start_date) & (df['est_date'] <= end_date)]
    
    days_with_anchor = 0
    days_with_impulse = 0
    days_with_gold_price = 0  # Price visits Goldilocks
    days_with_gold_close = 0  # Candle CLOSES in Goldilocks
    days_with_micro_p90 = 0
    
    sample_days = []
    
    for dk in sorted(df['est_date'].unique()):
        day_bars = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
        if len(day_bars) < 10: continue
        ar = compute_asian_range(df, dk)
        if ar is None: continue
        tier = classify_tier(ar['ar_pips'])
        if tier == 'NO_GO' or ar['ar_pips'] < 3: continue
        
        params = TIERS[tier]
        window = day_bars[(day_bars['est_hour'] >= 2) & (day_bars['est_hour'] < 12)].reset_index(drop=True)
        if len(window) < 10: continue
        
        ah = ar['ah']; al = ar['al']
        
        # Find anchor
        anchor = None
        for i in range(len(window)):
            row = window.iloc[i]
            eh = row['est_hour']
            if eh < 2 or eh >= 11: continue
            body = abs(row['close'] - row['open']) * 10000
            p90_thresh = get_p90_threshold(eh)
            if body >= p90_thresh:
                if row['close'] > ah or row['close'] < al:
                    anchor = {'idx': i, 'row': row, 'body': body,
                              'dir': 1 if row['close'] > row['open'] else -1}
                    break
        if anchor is None: continue
        days_with_anchor += 1
        
        # Impulse leg
        anchor_dir = anchor['dir']
        anchor_close = anchor['row']['close']
        impulse_extreme = anchor_close
        impulse_idx = anchor['idx']
        for i in range(anchor['idx'] + 1, len(window)):
            row = window.iloc[i]
            if anchor_dir == 1:
                if row['high'] > impulse_extreme:
                    impulse_extreme = row['high']; impulse_idx = i
            else:
                if row['low'] < impulse_extreme:
                    impulse_extreme = row['low']; impulse_idx = i
        
        impulse_distance = abs(impulse_extreme - anchor_close) * 10000
        if impulse_distance < params['trigger']: continue
        days_with_impulse += 1
        
        # Goldilocks zone 32-50%
        g_low = 0.32; g_high = 0.50
        if anchor_dir == 1:
            gold_high = impulse_extreme - (impulse_distance * g_low / 10000)
            gold_low = impulse_extreme - (impulse_distance * g_high / 10000)
        else:
            gold_low = impulse_extreme + (impulse_distance * g_low / 10000)
            gold_high = impulse_extreme + (impulse_distance * g_high / 10000)
        
        # Check: does price visit this zone at all (wick)?
        price_visits_gold = False
        any_close_in_gold = False
        micro_p90_in_gold = False
        
        for i in range(impulse_idx + 1, len(window)):
            row = window.iloc[i]
            if row['est_hour'] >= 11: break
            
            # Wick visit
            if anchor_dir == 1:
                wick_in = (row['low'] <= gold_high and row['high'] >= gold_low)
            else:
                wick_in = (row['low'] <= gold_high and row['high'] >= gold_low)
            
            if wick_in:
                price_visits_gold = True
                
                # Close in zone
                if gold_low <= row['close'] <= gold_high:
                    any_close_in_gold = True
                    
                    # Micro-P90 check
                    body = abs(row['close'] - row['open']) * 10000
                    is_bull = row['close'] > row['open']
                    is_bear = row['close'] < row['open']
                    if body >= 4.5:
                        if (anchor_dir == 1 and is_bull) or (anchor_dir == -1 and is_bear):
                            micro_p90_in_gold = True
        
        if price_visits_gold: days_with_gold_price += 1
        if any_close_in_gold: days_with_gold_close += 1
        if micro_p90_in_gold: days_with_micro_p90 += 1
        
        if len(sample_days) < 20 and price_visits_gold and not micro_p90_in_gold:
            sample_days.append({
                'date': dk,
                'dir': anchor_dir,
                'impulse': impulse_distance,
                'gold_low': gold_low,
                'gold_high': gold_high,
                'price_visits': price_visits_gold,
                'close_in_zone': any_close_in_gold,
            })
    
    total_days = len(df[df['est_date'] >= start_date]['est_date'].unique())
    print(f"Total EST days in range: ~{total_days}")
    print(f"Days with P90 anchor: {days_with_anchor} ({days_with_anchor/max(total_days,1)*100:.1f}%)")
    print(f"  With impulse past trigger: {days_with_impulse} ({days_with_impulse/max(days_with_anchor,1)*100:.1f}% of anchors)")
    print(f"    Price wicks into Goldilocks 32-50%: {days_with_gold_price} ({days_with_gold_price/max(days_with_impulse,1)*100:.1f}% of impulses)")
    print(f"    Candle CLOSES in Goldilocks: {days_with_gold_close} ({days_with_gold_close/max(days_with_impulse,1)*100:.1f}%)")
    print(f"    Micro-P90 inside Goldilocks: {days_with_micro_p90} ({days_with_micro_p90/max(days_with_impulse,1)*100:.1f}%)")
    print(f"\nSample failures (price visits but no close):")
    for s in sample_days[:10]:
        print(f"  {s['date']} dir={s['dir']} impulse={s['impulse']:.1f}p "
              f"gold=[{s['gold_low']:.5f}, {s['gold_high']:.5f}] "
              f"visit={'Y'} close={s['close_in_zone']}")


if __name__ == "__main__":
    df = load_data()
    print("=" * 65)
    print("BLIND CHAIN CASCADE DETECTION DIAGNOSTIC (Goldilocks 32-50%)")
    print("=" * 65)
    run_diagnostic(df, date(2024, 1, 1), date(2025, 12, 31))
    
    print("\n\nNow with WIDER Goldilocks 20-60%:")
    print("(re-running with adjusted percentages)")
    
    # Quick re-run with wider
    df2 = df.copy()
    days_with_gold_price = 0
    days_with_gold_close = 0
    days_with_micro_p90 = 0
    days_with_impulse2 = 0
    
    for dk in sorted(df2[(df2['est_date'] >= date(2024,1,1)) & (df2['est_date'] <= date(2025,12,31))]['est_date'].unique()):
        day_bars = df2[df2['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
        if len(day_bars) < 10: continue
        ar = compute_asian_range(df2, dk)
        if ar is None: continue
        tier = classify_tier(ar['ar_pips'])
        if tier == 'NO_GO' or ar['ar_pips'] < 3: continue
        params = TIERS[tier]
        window = day_bars[(day_bars['est_hour'] >= 2) & (day_bars['est_hour'] < 12)].reset_index(drop=True)
        if len(window) < 10: continue
        ah = ar['ah']; al = ar['al']
        
        anchor = None
        for i in range(len(window)):
            row = window.iloc[i]
            eh = row['est_hour']
            if eh < 2 or eh >= 11: continue
            body = abs(row['close'] - row['open']) * 10000
            if body >= get_p90_threshold(eh):
                if row['close'] > ah or row['close'] < al:
                    anchor = {'idx': i, 'row': row, 'dir': 1 if row['close'] > row['open'] else -1}
                    break
        if anchor is None: continue
        
        anchor_dir = anchor['dir']
        anchor_close = anchor['row']['close']
        impulse_extreme = anchor_close
        impulse_idx = anchor['idx']
        for i in range(anchor['idx'] + 1, len(window)):
            row = window.iloc[i]
            if anchor_dir == 1:
                if row['high'] > impulse_extreme: impulse_extreme = row['high']; impulse_idx = i
            else:
                if row['low'] < impulse_extreme: impulse_extreme = row['low']; impulse_idx = i
        impulse_distance = abs(impulse_extreme - anchor_close) * 10000
        if impulse_distance < params['trigger']: continue
        days_with_impulse2 += 1
        
        g_low = 0.20; g_high = 0.60
        if anchor_dir == 1:
            gh = impulse_extreme - impulse_distance * g_low / 10000
            gl = impulse_extreme - impulse_distance * g_high / 10000
        else:
            gl = impulse_extreme + impulse_distance * g_low / 10000
            gh = impulse_extreme + impulse_distance * g_high / 10000
        
        for i in range(impulse_idx + 1, len(window)):
            row = window.iloc[i]
            if row['est_hour'] >= 11: break
            wick_in = (row['low'] <= gh and row['high'] >= gl)
            if wick_in:
                days_with_gold_price += 1
                if gl <= row['close'] <= gh:
                    days_with_gold_close += 1
                    body = abs(row['close'] - row['open']) * 10000
                    if body >= 4.5:
                        is_bull = row['close'] > row['open']
                        is_bear = row['close'] < row['open']
                        if (anchor_dir == 1 and is_bull) or (anchor_dir == -1 and is_bear):
                            days_with_micro_p90 += 1
                break  # only count first visit
    
    print(f"\nWith Goldilocks 20-60%:")
    print(f"  Impulses: {days_with_impulse2}")
    print(f"  Price visits Goldilocks: {days_with_gold_price} ({days_with_gold_price/max(days_with_impulse2,1)*100:.1f}%)")
    print(f"  Close in Goldilocks: {days_with_gold_close} ({days_with_gold_close/max(days_with_impulse2,1)*100:.1f}%)")
    print(f"  Micro-P90 cascade: {days_with_micro_p90} ({days_with_micro_p90/max(days_with_impulse2,1)*100:.1f}%)")
