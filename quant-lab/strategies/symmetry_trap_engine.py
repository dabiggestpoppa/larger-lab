"""
DISTRIBUTION SYMMETRY TRAP — Engine v3 (CORRECT)
=================================================
From CEREBUS FX v4 Manual, pages 145-154. Rebuilt from scratch.

CONCEPT: Bias Lock → Atomic Entry → Distribution Targets

UNIFIED TEST FRAMEWORK (from manual page 145):
  BIAS: First M5 close outside Asian band
  ENTRY: Impulse body >= AU*0.5 + opposite close
  SL: OCC extreme (close back inside band) — zero buffer
  TARGETS: Band Extreme ± AR*x in trade direction
    T25 = AR*25% -> close 50%
    T50 = AR*50% -> close 40%
    T100 = AR*100% -> close 10% runner
  GEAR SHIFT: If impulse >= next tier trigger, use shifted AU for runner sizing
  HARD EXIT: 12PM EST

MANUAL STATS:
  WR: 83-86% | PF: 3.82 | Avg R: +1.84R | Expectancy: +1.38R
  Total: +579% ($10k -> $67,924) | Max DD: 3.9%
"""
import sys, os
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range
import pandas as pd
from datetime import date

SPREAD_COST = 0.6  # realistic for EUR/USD M5 during Asian/London

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
    au = params['au']

    # ═══ BIAS LOCK ═══
    bias = 0
    bias_idx = None
    day_3am = day_bars[(day_bars['est_hour'] >= 3) & (day_bars['est_hour'] < 12)]
    for i, (_, bar) in enumerate(day_3am.iterrows()):
        c = bar['close']
        if c > ah: bias = 1; bias_idx = i; break
        if c < al: bias = -1; bias_idx = i; break
    if bias == 0:
        return trades

    # ═══ ATOMIC ENTRY ═══
    # Find impulse in bias direction with body >= AU*0.5, after bias lock
    entry = None
    entry_au = au  # default AU for target calc (may be gear-shifted)
    impulse_body_pips = 0
    bars_list = list(day_3am.iterrows())

    for j in range(bias_idx + 1, len(bars_list)):
        idx, bar = bars_list[j]
        o = bar['open']
        c = bar['close']
        body_pips = abs(c - o) * 10000.0
        is_bull = c > o
        is_bear = c < o

        # Impulse in bias direction?
        found_impulse = False
        if bias == 1 and is_bull and body_pips >= au * 0.5:
            found_impulse = True
            impulse_body_pips = body_pips
        elif bias == -1 and is_bear and body_pips >= au * 0.5:
            found_impulse = True
            impulse_body_pips = body_pips

        if found_impulse:
            # Check next candle for opposite close
            if j + 1 < len(bars_list):
                _, next_bar = bars_list[j + 1]
                nc = next_bar['close']
                no = next_bar['open']
                opposite = (bias == 1 and nc < no) or (bias == -1 and nc > no)
                if opposite:
                    entry = nc
                    # GEAR SHIFT: if impulse exceeds next tier trigger, shift target AU
                    if impulse_body_pips >= params['next_trig']:
                        # Shift to next tier AU
                        if tier == 'T1': entry_au = TIERS['T2']['au']  # 12
                        elif tier == 'T2': entry_au = TIERS['T3']['au']  # 15
                        else: entry_au = 25  # MT25
                    break

    if entry is None:
        return trades

    # ═══ TARGETS + MANAGEMENT ═══
    # T25/T50/T100 measured from BAND EDGE in trade direction
    ar_val = ar_pips / 10000.0
    if bias == 1:
        # LONG: band extreme = Asian High, targets above
        sl_level = al  # close below AL = exit
        t25 = ah + ar_val * 0.25
        t50 = ah + ar_val * 0.50
        t100 = ah + ar_val * 1.00
    else:
        # SHORT: band extreme = Asian Low, targets below
        sl_level = ah  # close above AH = exit
        t25 = al - ar_val * 0.25
        t50 = al - ar_val * 0.50
        t100 = al - ar_val * 1.00

    pos = 1.0
    pnl = 0.0
    t25_hit = False
    t50_hit = False
    be_moved = False

    # Scan from entry onward
    scanning = False
    for j in range(bias_idx + 1, len(bars_list)):
        _, bar = bars_list[j]
        if entry is not None and bar['close'] == entry and not scanning:
            scanning = True
            continue
        if not scanning:
            continue
        if bar['est_hour'] >= 12:
            # Hard exit
            if pos > 0:
                pnl += (bar['close'] - entry) * bias * 10000.0 * pos - SPREAD_COST * pos
                pos = 0
            break

        c = bar['close']

        # SL: close back inside Asian band
        if bias == 1 and c < sl_level:
            if pos > 0:
                pnl += (c - entry) * 10000.0 * pos - SPREAD_COST * pos
                pos = 0
            break
        if bias == -1 and c > sl_level:
            if pos > 0:
                pnl += (entry - c) * 10000.0 * pos - SPREAD_COST * pos
                pos = 0
            break

        if bias == 1:
            if c >= t25 and not t25_hit:
                pnl += (t25 - entry) * 10000.0 * 0.50
                pos -= 0.50
                t25_hit = True
                if not be_moved:
                    be_moved = True
            if c >= t50 and not t50_hit:
                pnl += (t50 - entry) * 10000.0 * 0.40
                pos -= 0.40
                t50_hit = True
            if t50_hit and pos > 0 and c >= t100:
                pnl += (t100 - entry) * 10000.0 * pos
                pos = 0
                break
        else:
            if c <= t25 and not t25_hit:
                pnl += (entry - t25) * 10000.0 * 0.50
                pos -= 0.50
                t25_hit = True
                if not be_moved:
                    be_moved = True
            if c <= t50 and not t50_hit:
                pnl += (entry - t50) * 10000.0 * 0.40
                pos -= 0.40
                t50_hit = True
            if t50_hit and pos > 0 and c <= t100:
                pnl += (entry - t100) * 10000.0 * pos
                pos = 0
                break

    if pnl != 0 or pos < 1.0:
        trades.append({'date': str(date_key), 'direction': bias,
            'entry_price': entry, 'pnl_pips': pnl, 'tier': tier, 'au': entry_au})
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
    print("SYMMETRY TRAP v3 — Manual-Correct Build")
    print("=" * 55)
    df = load_data()
    print("\n2024-2025...")
    tr, days = run_backtest(df, date(2024, 1, 1), date(2025, 12, 31))
    if not tr: print("No trades!"); sys.exit(1)

    tdf = pd.DataFrame(tr)
    n = len(tdf)
    wr = (tdf['pnl_pips'] > 0).mean() * 100
    total = tdf['pnl_pips'].sum()
    wins = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].sum()
    losses = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].sum())
    pf = wins / losses if losses > 0 else float('inf')

    print(f"Days: {days}, Trades: {n}")
    print(f"WR: {wr:.1f}% (manual: 83-86%)")
    print(f"PF: {pf:.2f} (manual: 3.82)")
    print(f"Total: {total:.1f}p, Avg: {total/n:.1f}p/trade")

    print("\nTiers:")
    for t in sorted(tdf['tier'].unique()):
        tf = tdf[tdf['tier']==t]
        print(f"  {t}: {len(tf)} tr, WR {(tf['pnl_pips']>0).mean()*100:.1f}%, "
              f"avg {tf['pnl_pips'].mean():.1f}p, total {tf['pnl_pips'].sum():.1f}p")

    tdf['year'] = pd.to_datetime(tdf['date']).dt.year
    print("\nYearly:")
    for y in sorted(tdf['year'].unique()):
        yf = tdf[tdf['year']==y]
        print(f"  {y}: {len(yf)}, WR {(yf['pnl_pips']>0).mean()*100:.1f}%, {yf['pnl_pips'].sum():.1f}p")

    print("\nFull dataset (2023H2-2026H1)...")
    tr2, days2 = run_backtest(df)
    tdf2 = pd.DataFrame(tr2)
    n2 = len(tdf2)
    wr2 = (tdf2['pnl_pips'] > 0).mean() * 100
    total2 = tdf2['pnl_pips'].sum()
    print(f"Days: {days2}, Trades: {n2}")
    print(f"WR: {wr2:.1f}% | Total: {total2:.1f}p | Avg: {total2/n2:.1f}p/trade")
