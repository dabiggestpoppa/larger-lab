"""
BLIND STRUCTURAL CHAIN v2 — SL + Goldilocks Calibrated for M5
===================================================================
Built from blind_chain_engine.py (v1).

ROOT CAUSE (from tracker + diagnostic):
- Goldilocks zone 32-50% for typical impulse (15-22p) = 2.7-4.0p wide
- micro-P90 requires 4.5p body — candle can't fit in zone
- Only ~12% of impulse days produce a valid micro-P90 inside Goldilocks
- v1 SL = 168% of cascade body (~8-10p). Tight SL + rare setup = all hit SL.

CALIBRATION:
1. Widen Goldilocks zone: 20-60% instead of 32-50%
   -> zone width for 18p impulse: 7.2p vs 3.2p — 4.5p body fits easily
2. SL variants:
   a. 168% of cascade body (original)
   b. 120% of cascade body
   c. 100% of cascade body (= body size)
   d. Goldilocks zone boundary as structural SL
   e. 80% of anchor body
3. Reduce micro-P90 threshold to 3.0p (instead of 4.5p) for M5
"""
import sys, io
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range
from datetime import date
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SPREAD_COST = 0.5
TIERS = {
    'T1': {'ar_max': 20, 'trigger': 12, 'au': 10},
    'T2': {'ar_max': 30, 'trigger': 15, 'au': 12},
    'T3': {'ar_max': 45, 'trigger': 19, 'au': 15},
}
AU1 = {2: 4.1, 3: 4.1, 4: 4.6, 5: 4.6, 6: 4.6, 7: 5.9, 8: 5.9, 9: 6.2, 10: 6.2, 11: 6.2}


def classify_tier(ar_pips):
    if ar_pips < 20:  return 'T1'
    if ar_pips < 30:  return 'T2'
    if ar_pips <= 45: return 'T3'
    return 'NO_GO'


def get_p90_thresh(est_hour):
    h = int(est_hour)
    if h < 2: return 4.1
    if h > 11: return 6.2
    return AU1.get(h, 4.6)


def run_day(day_bars, ar_info, gold_pct_low, gold_pct_high, sl_mode, min_micro_body=4.5):
    """
    gold_pct_low/high: Goldilocks zone as percentages (e.g., 32, 50 means 32-50%)
    sl_mode: 'pct_168', 'pct_120', 'pct_100', 'gold_struct', 'anchor_80'
    min_micro_body: minimum body size for micro-P90 candle (default 4.5, try 3.0 for relaxed)
    """
    trades = []
    ah = ar_info['ah']; al = ar_info['al']
    ar_pips = ar_info['ar_pips']
    date_key = ar_info['date_key']
    tier = classify_tier(ar_pips)
    if tier == 'NO_GO' or ar_pips < 3: return trades
    params = TIERS[tier]
    window = day_bars[(day_bars['est_hour'] >= 2) & (day_bars['est_hour'] < 12)].reset_index(drop=True)
    if len(window) < 10: return trades

    # ANCHOR: P90
    anchor = None
    for i in range(len(window)):
        row = window.iloc[i]; eh = row['est_hour']
        if eh < 2 or eh >= 11: continue
        body = abs(row['close'] - row['open']) * 10000
        if body >= get_p90_thresh(eh):
            if row['close'] > ah or row['close'] < al:
                anchor = {'idx': i, 'row': row, 'body': body,
                          'dir': 1 if row['close'] > row['open'] else -1}
                break
    if anchor is None: return trades

    # IMPULSE LEG
    anchor_dir = anchor['dir']
    anchor_close = anchor['row']['close']
    impulse_extreme = anchor_close; impulse_idx = anchor['idx']
    for i in range(anchor['idx'] + 1, len(window)):
        row = window.iloc[i]
        if anchor_dir == 1:
            if row['high'] > impulse_extreme: impulse_extreme = row['high']; impulse_idx = i
        else:
            if row['low'] < impulse_extreme: impulse_extreme = row['low']; impulse_idx = i
    impulse_dist = abs(impulse_extreme - anchor_close) * 10000  # pips
    if impulse_dist < params['trigger']: return trades

    # GOLDILOCKS ZONE (gold_pct_low/high are percentages 32/50/20/60 etc.)
    if anchor_dir == 1:
        gold_high_p = impulse_extreme - impulse_dist * (gold_pct_low / 100) / 10000
        gold_low_p  = impulse_extreme - impulse_dist * (gold_pct_high / 100) / 10000
    else:
        gold_low_p  = impulse_extreme + impulse_dist * (gold_pct_low / 100) / 10000
        gold_high_p = impulse_extreme + impulse_dist * (gold_pct_high / 100) / 10000

    # CASCADE: micro-P90 in Goldilocks
    cascade_entry = None; cascade_idx = None; cascade_body = None
    for i in range(impulse_idx + 1, len(window)):
        row = window.iloc[i]
        if row['est_hour'] >= 11: break
        in_gold = gold_low_p <= row['close'] <= gold_high_p
        if not in_gold:
            in_gold = (gold_low_p <= row['high'] and row['low'] <= gold_high_p)
        if not in_gold: continue
        body = abs(row['close'] - row['open']) * 10000
        is_bull = row['close'] > row['open']
        is_bear = row['close'] < row['open']
        if body >= min_micro_body:
            if (anchor_dir == 1 and is_bull) or (anchor_dir == -1 and is_bear):
                cascade_entry = row['close']; cascade_idx = i; cascade_body = body
                break
    if cascade_entry is None: return trades

    # SL
    if sl_mode == 'pct_168':
        sl_dist = cascade_body * 1.68 / 10000
    elif sl_mode == 'pct_120':
        sl_dist = cascade_body * 1.20 / 10000
    elif sl_mode == 'pct_100':
        sl_dist = cascade_body * 1.00 / 10000
    elif sl_mode == 'gold_struct':
        zone_width = abs(gold_high_p - gold_low_p)
        if anchor_dir == 1:
            sl = gold_low_p - zone_width * 0.1
        else:
            sl = gold_high_p + zone_width * 0.1
        sl_dist = None
    elif sl_mode == 'anchor_80':
        anchor_body_price = anchor['body'] / 10000
        sl_dist = anchor_body_price * 0.80
    else:
        sl_dist = cascade_body * 1.68 / 10000

    if sl_dist is not None:
        sl = cascade_entry - sl_dist if anchor_dir == 1 else cascade_entry + sl_dist

    # TARGET
    target = cascade_entry + (impulse_dist / 10000) if anchor_dir == 1 else cascade_entry - (impulse_dist / 10000)

    pos = 1.0; pnl = 0.0
    for i in range(cascade_idx + 1, len(window)):
        row = window.iloc[i]; c = row['close']; h = row['high']; l = row['low']
        if row['est_hour'] >= 12:
            if pos > 0: pnl += (c - cascade_entry) * anchor_dir * 10000 * pos - SPREAD_COST * pos; pos = 0
            break
        if anchor_dir == 1:
            if c < sl:
                if pos > 0: pnl += (c - cascade_entry) * 10000 * pos - SPREAD_COST * pos; pos = 0
                break
            if h >= target and pos > 0: pnl += (target - cascade_entry) * 10000 * pos - SPREAD_COST * pos; pos = 0; break
        else:
            if c > sl:
                if pos > 0: pnl += (cascade_entry - c) * 10000 * pos - SPREAD_COST * pos; pos = 0
                break
            if l <= target and pos > 0: pnl += (cascade_entry - target) * 10000 * pos - SPREAD_COST * pos; pos = 0; break

    if pnl != 0 or pos < 1.0:
        trades.append({'date': str(date_key), 'pnl_pips': pnl, 'tier': tier, 'ar': ar_pips,
                       'impulse_dist': impulse_dist, 'cascade_body': cascade_body,
                       'gold_low': gold_low_p, 'gold_high': gold_high_p,
                       'zone_width_pips': abs(gold_high_p - gold_low_p) * 10000,
                       'sl_mode': sl_mode})
    return trades


def run_backtest(df, gold_pct_low, gold_pct_high, sl_mode, min_micro_body=4.5,
                 start_date=None, end_date=None):
    if start_date: df = df[df['est_date'] >= start_date]
    if end_date:   df = df[df['est_date'] <= end_date]
    all_trades = []; days = 0
    for dk in sorted(df['est_date'].unique()):
        db = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
        if len(db) < 10: continue
        ar = compute_asian_range(df, dk)
        if ar is None: continue
        ar['date_key'] = dk
        tr = run_day(db, ar, gold_pct_low, gold_pct_high, sl_mode, min_micro_body)
        if tr: all_trades.extend(tr)
        days += 1
    return all_trades, days


if __name__ == "__main__":
    print("=" * 70)
    print("BLIND STRUCTURAL CHAIN v2 — SL + Goldilocks Calibration")
    print("=" * 70)
    df = load_data()
    sd = date(2024, 1, 1); ed = date(2025, 12, 31)

    # ===== Quick sanity check: reproduce v1 baseline =====
    print("\n--- v1 Reproduction (Goldilocks 32-50, SL 168%, micro>=4.5) ---")
    tr, days = run_backtest(df, 32, 50, 'pct_168', min_micro_body=4.5, start_date=sd, end_date=ed)
    if tr:
        tdf = pd.DataFrame(tr); n = len(tdf)
        wr = (tdf['pnl_pips'] > 0).mean() * 100
        total = tdf['pnl_pips'].sum()
        wins = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].sum()
        losses = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].sum())
        pf = wins / losses if losses > 0 else 99
        print(f"  Trades={n} Days={days} WR={wr:.1f}% PF={pf:.2f} Total={total:.1f}p Avg={total/n:.1f}p")
    else:
        print("  NO TRADES — something is wrong")

    # ===== Phase 1: Standard Goldilocks + SL variants =====
    print("\n--- Phase 1: SL Variants (Goldilocks 32-50%, micro>=4.5) ---")
    sl_modes = [
        ('pct_168',   '168% of cascade body'),
        ('pct_120',   '120% of cascade body'),
        ('pct_100',   '100% of cascade body'),
        ('gold_struct','Goldilocks boundary'),
        ('anchor_80',  '80% of anchor body'),
    ]
    p1 = []
    for mode, desc in sl_modes:
        tr, days = run_backtest(df, 32, 50, mode, 4.5, sd, ed)
        if not tr: print(f"  {mode}: NO TRADES"); p1.append({'mode': mode, 'desc': desc, 'gold': '32-50', 'trades': 0}); continue
        tdf = pd.DataFrame(tr); n = len(tdf)
        wr = (tdf['pnl_pips'] > 0).mean() * 100
        total = tdf['pnl_pips'].sum()
        wins_g = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].sum()
        losses_g = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].sum())
        pf = wins_g / losses_g if losses_g > 0 else 99
        print(f"  {mode:<12} Tr={n:>3} WR={wr:>5.1f}% PF={pf:>5.2f} Total={total:>7.1f}p "
              f"Avg={total/n:>6.1f}p | {desc}")
        p1.append({'mode': mode, 'desc': desc, 'gold': '32-50', 'trades': n, 'days': days,
                    'wr': wr, 'pf': pf, 'total': total, 'avg': total/n})

    # ===== Phase 2: Wider Goldilocks + relaxed micro =====
    print("\n--- Phase 2: Goldilocks Widening (best SL above) ---")
    valid_p1 = [r for r in p1 if r['trades'] > 0]
    best_sl = max(valid_p1, key=lambda x: x['pf'])['mode'] if valid_p1 else 'pct_100'
    
    gold_variants = [
        (32, 50, 4.5, 'Standard manual'),
        (25, 55, 4.5, 'Relaxed 25-55'),
        (20, 60, 4.5, 'Wide 20-60'),
        (25, 50, 4.5, 'Low-relaxed 25-50'),
        (20, 60, 3.0, 'Wide + relaxed micro 3.0'),
        (25, 55, 3.0, 'Relaxed zone + micro 3.0'),
        (20, 60, 3.5, 'Wide + micro 3.5'),
    ]
    p2 = []
    for g_low, g_high, min_body, desc in gold_variants:
        tr, days = run_backtest(df, g_low, g_high, best_sl, min_body, sd, ed)
        if not tr: print(f"  Gold {g_low}-{g_high}% micro>={min_body}: NO TRADES"); p2.append({'desc': desc, 'trades': 0}); continue
        tdf = pd.DataFrame(tr); n = len(tdf)
        wr = (tdf['pnl_pips'] > 0).mean() * 100
        total = tdf['pnl_pips'].sum()
        wins_g = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].sum()
        losses_g = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].sum())
        pf = wins_g / losses_g if losses_g > 0 else 99
        zw = tdf['zone_width_pips'].mean()
        print(f"  Gold {g_low:>2}-{g_high:>2}% micro>={min_body}: Tr={n:>3} WR={wr:>5.1f}% "
              f"PF={pf:>5.2f} Total={total:>7.1f}p Zone={zw:.1f}p | {desc}")
        p2.append({'g_low': g_low, 'g_high': g_high, 'min_body': min_body, 'desc': desc,
                    'trades': n, 'days': days, 'wr': wr, 'pf': pf, 'total': total, 'avg': total/n})

    # ===== Phase 3: Best Goldilocks + SL sweep =====
    print("\n--- Phase 3: Best Goldilocks x SL sweep ---")
    valid_p2 = [r for r in p2 if r['trades'] > 0]
    top2_gold = sorted(valid_p2, key=lambda x: x['pf'], reverse=True)[:2]
    top2_sl = sorted(valid_p1, key=lambda x: x['pf'], reverse=True)[:2]
    
    p3 = []
    for g_r in top2_gold:
        for s_r in top2_sl:
            tr, days = run_backtest(df, g_r['g_low'], g_r['g_high'], s_r['mode'], g_r['min_body'], sd, ed)
            if not tr: continue
            tdf = pd.DataFrame(tr); n = len(tdf)
            wr = (tdf['pnl_pips'] > 0).mean() * 100
            total = tdf['pnl_pips'].sum()
            wins_g = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].sum()
            losses_g = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].sum())
            pf = wins_g / losses_g if losses_g > 0 else 99
            print(f"  Gold {g_r['g_low']}-{g_r['g_high']}% micro{g_r['min_body']} + SL {s_r['mode']}: "
                  f"Tr={n:>3} WR={wr:>5.1f}% PF={pf:>5.2f} Total={total:>7.1f}p")
            p3.append({'g_low': g_r['g_low'], 'g_high': g_r['g_high'], 'min_body': g_r['min_body'],
                        'mode': s_r['mode'], 'trades': n, 'wr': wr, 'pf': pf, 'total': total})

    # ===== Winner =====
    all_results = valid_p1 + valid_p2 + p3
    print(f"\n{'='*70}")
    print("CALIBRATION SUMMARY (all variants)")
    print(f"{'='*70}")
    for r in sorted(all_results, key=lambda x: x.get('pf', 0), reverse=True):
        desc = r.get('desc', r.get('mode', 'combined'))
        print(f"  Tr={r['trades']:>3} WR={r['wr']:>5.1f}% PF={r['pf']:>5.2f} "
              f"Total={r['total']:>7.1f}p Avg={r.get('avg',0):>6.1f}p | {desc}")

    if all_results:
        best = max(all_results, key=lambda x: x['pf'])
        print(f"\nBest: {best.get('desc', best.get('mode', 'combined'))}")
        print(f"  Tr={best['trades']} WR={best['wr']:.1f}% PF={best['pf']:.2f} Total={best['total']:.1f}p")

        # Full run
        g_low = best.get('g_low', 32); g_high = best.get('g_high', 50)
        mode = best.get('mode', 'pct_168'); min_body = best.get('min_body', 4.5)
        
        print(f"\n{'='*70}")
        print("WINNER — FULL DATASET RUN")
        print(f"Config: Goldilocks {g_low}-{g_low}%, SL={mode}, micro-P90 >= {min_body}p")
        for pname, s, e in [("2024-2025", date(2024,1,1), date(2025,12,31)),
                              ("Full 2023H2-2026H1", date(2023,7,1), date(2026,6,30))]:
            tr, days = run_backtest(df, g_low, g_high, mode, min_body, s, e)
            if not tr: print(f"{pname}: No trades"); continue
            tdf = pd.DataFrame(tr); n = len(tdf)
            wr = (tdf['pnl_pips'] > 0).mean() * 100
            total = tdf['pnl_pips'].sum()
            wins_g = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].sum()
            losses_g = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].sum())
            pf = wins_g / losses_g if losses_g > 0 else 99
            print(f"\n{pname}: Days={days}, Trades={n}")
            print(f"  WR: {wr:.1f}% (v1=0%, manual=93.7%) | PF: {pf:.2f}")
            print(f"  Total: {total:.1f}p | Avg: {total/n:.1f}p")
            for t in ['T1', 'T2', 'T3']:
                tf = tdf[tdf['tier'] == t]
                if len(tf) == 0: continue
                print(f"  {t}: {len(tf)} tr, WR {(tf['pnl_pips']>0).mean()*100:.1f}% avg {tf['pnl_pips'].mean():.1f}p")
