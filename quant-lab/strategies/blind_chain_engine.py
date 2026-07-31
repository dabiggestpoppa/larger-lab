"""
BLIND STRUCTURAL CHAIN — Recursive Loop Engine
================================================
From CEREBUS FX v4 Manual, pages 95-104.

"The cascade fires exactly when the field is resetting its constraint energy
for the next resolution leg — maximum R-multiple, minimum boundary exposure."

CONCEPT:
- P90 candle = Anchor (sets direction + entry)
- Wait for impulse to extend
- Wait for 32-50% partial rebalancing (Goldilocks Zone)
- Micro-P90 candle close from Goldilocks = CASCADE_ENTRY
- SL = 168% of micro-P90 body (stall zone)

KEY DIFFERENCE FROM OLD MODEL:
- Old: "Add at +45 minutes" (blind time guess)
- New: "Add when Loop Partial Rebalancing completes" (structural certainty)

MANUAL STATS:
- 742 chains detected, 658 valid (88.7%)
- 93.7% continuation probability after Goldilocks entry
- 168% SL best for cascades (vs 80% for initial)
- Optimal timing: 45-60 min after anchor (resolution momentum peak)

EXECUTION:
1. P90 anchor fires → Enter 40% size, SL at 80% P90 body
2. Price extends (impulse leg)
3. Price pulls back to 32-50% of impulse (Goldilocks Zone)
4. Micro-P90 (body >= 4.5p) in anchor direction from Goldilocks → Enter 30-40%
5. SL for cascade = 168% of micro-P90 body
6. Target = Tier threshold or 1.44x shift
"""
import sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range
from datetime import date
import pandas as pd

SPREAD_COST = 0.5

# Tier trigger thresholds for cascade (from manual)
TIERS = {
    'T1': {'ar_max': 20, 'trigger': 12, 'next_trig': 15, 'au': 10},
    'T2': {'ar_max': 30, 'trigger': 15, 'next_trig': 19, 'au': 12},
    'T3': {'ar_max': 45, 'trigger': 19, 'next_trig': 25, 'au': 15},
}

# P90 body thresholds by EST hour (AU1)
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


def run_day(day_bars, ar_info):
    trades = []
    ah = ar_info['ah']
    al = ar_info['al']
    ar_pips = ar_info['ar_pips']
    date_key = ar_info['date_key']
    tier = classify_tier(ar_pips)
    if tier == 'NO_GO' or ar_pips < 3:
        return trades
    params = TIERS[tier]
    window = day_bars[(day_bars['est_hour'] >= 2) & (day_bars['est_hour'] < 12)].reset_index(drop=True)
    if len(window) < 10: return trades

    # ═══ ANCHOR: P90 candle ═══
    anchor = None
    for i in range(len(window)):
        row = window.iloc[i]
        eh = row['est_hour']
        if eh < 2 or eh >= 11: continue
        body = abs(row['close'] - row['open']) * 10000
        p90_thresh = get_p90_threshold(eh)
        if body >= p90_thresh:
            # Check if it closes outside Asian band
            if row['close'] > ah or row['close'] < al:
                anchor = {'idx': i, 'row': row, 'body': body,
                          'dir': 1 if row['close'] > row['open'] else -1}
                break
    if anchor is None: return trades

    # ═══ IMPULSE LEG: extend from anchor ═══
    # Track how far price moves in anchor direction
    anchor_dir = anchor['dir']
    anchor_close = anchor['row']['close']
    impulse_extreme = anchor_close
    impulse_idx = anchor['idx']

    for i in range(anchor['idx'] + 1, len(window)):
        row = window.iloc[i]
        if anchor_dir == 1:
            if row['high'] > impulse_extreme:
                impulse_extreme = row['high']
                impulse_idx = i
        else:
            if row['low'] < impulse_extreme:
                impulse_extreme = row['low']
                impulse_idx = i

    impulse_distance = abs(impulse_extreme - anchor_close) * 10000  # pips
    if impulse_distance < params['trigger']:  # Must exceed tier threshold
        return trades

    # ═══ GOLDILOCKS ZONE: 32-50% rebalancing ═══
    # The zone where partial rebalancing should end
    if anchor_dir == 1:
        gold_high = impulse_extreme - (impulse_distance * 0.32 / 10000)
        gold_low = impulse_extreme - (impulse_distance * 0.50 / 10000)
    else:
        gold_low = impulse_extreme + (impulse_distance * 0.32 / 10000)
        gold_high = impulse_extreme + (impulse_distance * 0.50 / 10000)

    # ═══ CASCADE TRIGGER: Micro-P90 in anchor direction from Goldilocks ═══
    cascade_entry = None
    cascade_idx = None
    cascade_body = None

    for i in range(impulse_idx + 1, len(window)):
        row = window.iloc[i]
        if row['est_hour'] >= 11: break

        # Check if price is in Goldilocks zone
        in_gold = gold_low <= row['close'] <= gold_high
        if not in_gold:
            # Also check with low/high
            in_gold = (gold_low <= row['high'] and row['low'] <= gold_high)
        if not in_gold: continue

        # Check for micro-P90 in anchor direction
        body = abs(row['close'] - row['open']) * 10000
        is_bullish = row['close'] > row['open']
        is_bearish = row['close'] < row['open']

        if body >= 4.5:  # Micro-P90 threshold (from Part 14)
            if anchor_dir == 1 and is_bullish:
                cascade_entry = row['close']
                cascade_idx = i
                cascade_body = body
                break
            elif anchor_dir == -1 and is_bearish:
                cascade_entry = row['close']
                cascade_idx = i
                cascade_body = body
                break

    if cascade_entry is None: return trades

    # ═══ CASCADE MANAGEMENT ═══
    # SL = 168% of micro-P90 body from entry (opposite direction)
    sl_dist = cascade_body * 1.68 / 10000
    if anchor_dir == 1:
        sl = cascade_entry - sl_dist
        target = cascade_entry + (impulse_distance / 10000)  # Full impulse retest
    else:
        sl = cascade_entry + sl_dist
        target = cascade_entry - (impulse_distance / 10000)

    pos = 1.0
    pnl = 0.0

    for i in range(cascade_idx + 1, len(window)):
        row = window.iloc[i]
        c = row['close']
        h = row['high']
        l = row['low']

        if row['est_hour'] >= 12:
            if pos > 0:
                pnl += (c - cascade_entry) * anchor_dir * 10000 * pos - SPREAD_COST * pos
                pos = 0
            break

        if anchor_dir == 1:
            if c < sl:
                if pos > 0:
                    pnl += (c - cascade_entry) * 10000 * pos - SPREAD_COST * pos
                    pos = 0
                break
            if h >= target and pos > 0:
                pnl += (target - cascade_entry) * 10000 * pos - SPREAD_COST * pos
                pos = 0
                break
        else:
            if c > sl:
                if pos > 0:
                    pnl += (cascade_entry - c) * 10000 * pos - SPREAD_COST * pos
                    pos = 0
                break
            if l <= target and pos > 0:
                pnl += (cascade_entry - target) * 10000 * pos - SPREAD_COST * pos
                pos = 0
                break

    if pnl != 0 or pos < 1.0:
        trades.append({'date': str(date_key), 'pnl_pips': pnl,
                       'tier': tier, 'ar': ar_pips,
                       'impulse_dist': impulse_distance})
    return trades


def run_backtest(df, start_date=None, end_date=None):
    if start_date: df = df[df['est_date'] >= start_date]
    if end_date:   df = df[df['est_date'] <= end_date]
    all_trades = []
    days = 0
    for dk in sorted(df['est_date'].unique()):
        db = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
        if len(db) < 10: continue
        ar = compute_asian_range(df, dk)
        if ar is None: continue
        ar['date_key'] = dk
        tr = run_day(db, ar)
        if tr: all_trades.extend(tr)
        days += 1
    return all_trades, days


if __name__ == "__main__":
    print("=" * 55)
    print("BLIND STRUCTURAL CHAIN — Recursive Loop Engine")
    print("=" * 55)
    df = load_data()

    for period_name, sd, ed in [
        ("2024-2025", date(2024, 1, 1), date(2025, 12, 31)),
        ("Full 2023H2-2026H1", date(2023, 7, 1), date(2026, 6, 30)),
    ]:
        tr, days = run_backtest(df, sd, ed)
        if not tr: print(f"\n{period_name}: No trades"); continue
        tdf = pd.DataFrame(tr)
        n = len(tdf)
        wr = (tdf['pnl_pips'] > 0).mean() * 100
        total = tdf['pnl_pips'].sum()
        wins = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].sum()
        losses = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].sum())
        pf = wins / losses if losses > 0 else 99

        print(f"\n{period_name}: Days={days}, Trades={n}")
        print(f"  WR: {wr:.1f}% | PF: {pf:.2f} | Total: {total:.1f}p | Avg: {total/n:.1f}p")

        for t in ['T1', 'T2', 'T3']:
            tf = tdf[tdf['tier'] == t]
            if len(tf) == 0: continue
            print(f"  {t}: {len(tf)} tr, WR {(tf['pnl_pips']>0).mean()*100:.1f}%, "
                  f"avg {tf['pnl_pips'].mean():.1f}p")
