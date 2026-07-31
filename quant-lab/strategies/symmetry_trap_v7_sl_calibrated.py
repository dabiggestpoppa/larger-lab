"""
Symmetry Trap v7 — SL Calibrated for M5 Close-Bar Backtesting
==============================================================
Built from v6_exact manual translation, with SL calibration to fix
the M5 close-bar backtesting gap.

KEY INSIGHT (from tracker):
- v6 SL = opposite Asian band (full AR distance). On M5, losses avg 12.7p while wins avg 6.2p.
- T25 still hits 76% and T50 hits 67% — the entry logic is sound.
- Problem: SL is FULL AR distance away. Price must cross the entire Asian band + more to stop out.

CALIBRATION APPROACH:
Test multiple SL distances from entry:
  - v6: SL = opposite Asian band (100% AR from entry) — baseline, ~37% WR
  - v7a: SL at 50% of AR distance from entry (midpoint)
  - v7b: SL at Asian mid-point (midpoint of AH/AL)
  - v7c: SL at entry-side Asian band edge (not opposite edge)
  - v7d: SL at 25% of AR distance from entry (tight)
  - v7e: SL at 75% of AR distance from entry
  - v7f: SL at 33% of AR distance from entry

The logic above T25/T50 hits stays the same because those are still very strong (~76%/67%).
What changes is the loss side — tighter SL should reduce avg loss from 12.7p to 3-6p
while keeping most wins intact.

Then we pick the best variant and do a full parametric sweep within it.
"""
import sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range
from datetime import date, datetime
import pandas as pd
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# === CONFIG (same as v6) ===
TIERS = {
    'T1': {'ar_max': 20, 'atomic': 10, 'trigger': 12},
    'T2': {'ar_max': 30, 'atomic': 12, 'trigger': 15},
    'T3': {'ar_max': 45, 'atomic': 15, 'trigger': 19},
}

AU1 = {2: 4.1, 3: 4.1, 4: 4.6, 5: 4.6, 6: 4.6, 7: 5.9, 8: 5.9, 9: 6.2, 10: 6.2, 11: 6.2}


def classify_tier(ar_pips):
    if ar_pips < 20:  return 'T1'
    if ar_pips < 30:  return 'T2'
    if ar_pips <= 45: return 'T3'
    return 'NO_GO'


def run_session_with_sl_mode(day_bars, ah, al, ar_pips, date_key, sl_mode):
    """
    Same logic as v6 but with configurable SL.
    
    sl_mode options:
      'opposite_band'  — v6 SL: opposite Asian band (full AR distance)
      'pct_50'         — SL at 50% of AR distance from entry (toward opposite band)
      'asian_mid'      — SL at the midpoint of Asian range (AH+AL)/2
      'entry_band'     — SL at entry-side Asian band edge (closer to entry)
      'pct_25'         — SL at 25% of AR distance from entry
      'pct_75'         — SL at 75% of AR distance from entry
      'pct_33'         — SL at 33% of AR distance from entry
    """
    trades = []
    tier = classify_tier(ar_pips)
    if tier == 'NO_GO' or ar_pips < 3:
        return trades

    params = TIERS[tier]
    atomic = params['atomic']
    ar_val = ar_pips / 10000.0

    session = day_bars[(day_bars['est_hour'] >= 3) & (day_bars['est_hour'] < 12)].reset_index(drop=True)
    if len(session) < 5:
        return trades

    # === LAYER 1: LOCK BIAS (same as v6) ===
    bias = 0
    bias_idx = -1
    for i in range(len(session)):
        row = session.iloc[i]
        if row['close'] > ah:
            bias = 1; bias_idx = i; break
        if row['close'] < al:
            bias = -1; bias_idx = i; break

    if bias == 0:
        return trades

    asian_high = ah
    asian_low = al

    # === LAYER 2: ATOMIC ENTRY (same as v6) ===
    entry = None
    entry_idx = None

    for j in range(bias_idx + 1, len(session)):
        row = session.iloc[j]
        body = abs(row['close'] - row['open']) * 10000.0

        if bias == 1 and row['close'] > row['open'] and body >= atomic * 0.5:
            if j + 1 < len(session):
                next_candle = session.iloc[j + 1]
                if next_candle['close'] < next_candle['open']:
                    entry = next_candle['close']
                    entry_idx = j + 1
                    break

        if bias == -1 and row['close'] < row['open'] and body >= atomic * 0.5:
            if j + 1 < len(session):
                next_candle = session.iloc[j + 1]
                if next_candle['close'] > next_candle['open']:
                    entry = next_candle['close']
                    entry_idx = j + 1
                    break

    if entry is None:
        return trades

    # === CALIBRATED SL CALCULATION ===
    if bias == 1:
        # LONG: SL is BELOW entry
        ar_from_entry = (ah - entry)  # negative (entry is above AH)
        ar_to_opposite = (entry - al)  # positive (AL is below entry)
        
        if sl_mode == 'opposite_band':
            sl = al  # v6: far edge
        elif sl_mode == 'asian_mid':
            sl = (ah + al) / 2.0  # midpoint of Asian range
        elif sl_mode == 'entry_band':
            sl = ah  # entry-side band edge (closer)
        elif sl_mode == 'pct_25':
            sl = entry - ar_to_opposite * 0.25
        elif sl_mode == 'pct_33':
            sl = entry - ar_to_opposite * 0.33
        elif sl_mode == 'pct_50':
            sl = entry - ar_to_opposite * 0.50
        elif sl_mode == 'pct_75':
            sl = entry - ar_to_opposite * 0.75
        else:
            sl = al  # fallback
    else:
        # SHORT: SL is ABOVE entry
        ar_to_opposite = (ah - entry)  # positive (AH is above entry)
        
        if sl_mode == 'opposite_band':
            sl = ah  # v6: far edge
        elif sl_mode == 'asian_mid':
            sl = (ah + al) / 2.0
        elif sl_mode == 'entry_band':
            sl = al  # entry-side band edge (closer)
        elif sl_mode == 'pct_25':
            sl = entry + ar_to_opposite * 0.25
        elif sl_mode == 'pct_33':
            sl = entry + ar_to_opposite * 0.33
        elif sl_mode == 'pct_50':
            sl = entry + ar_to_opposite * 0.50
        elif sl_mode == 'pct_75':
            sl = entry + ar_to_opposite * 0.75
        else:
            sl = ah  # fallback

    # === LAYER 3: DISTRIBUTION TARGETS (same as v6) ===
    if bias == 1:
        asian_edge = asian_high
    else:
        asian_edge = asian_low

    t25  = asian_edge + ar_val * 0.25 * bias
    t50  = asian_edge + ar_val * 0.50 * bias
    t100 = asian_edge + ar_val * 1.00 * bias

    # === MANAGEMENT (same as v6, but with calibrated SL) ===
    pos = 1.0
    pnl_pips = 0.0
    t25_hit = False
    t50_hit = False

    for k in range(entry_idx + 1, len(session)):
        row = session.iloc[k]
        c = row['close']
        h = row['high']
        l = row['low']

        # Hard exit 12PM
        if row['est_hour'] >= 12:
            if pos > 0:
                pnl_pips += (c - entry) * bias * 10000.0 * pos
                pos = 0
            break

        # SL: close below/above calibrated level
        if bias == 1 and c < sl:
            if pos > 0:
                pnl_pips += (c - entry) * 10000.0 * pos
                pos = 0
            break
        if bias == -1 and c > sl:
            if pos > 0:
                pnl_pips += (entry - c) * 10000.0 * pos
                pos = 0
            break

        # Target management (same as v6)
        if bias == 1:
            if h >= t25 and not t25_hit:
                pnl_pips += (t25 - entry) * 10000.0 * 0.50
                pos -= 0.50
                t25_hit = True
            if h >= t50 and not t50_hit:
                pnl_pips += (t50 - entry) * 10000.0 * 0.40
                pos -= 0.40
                t50_hit = True
            if t50_hit and pos > 0 and h >= t100:
                pnl_pips += (t100 - entry) * 10000.0 * pos
                pos = 0
                break
        else:
            if l <= t25 and not t25_hit:
                pnl_pips += (entry - t25) * 10000.0 * 0.50
                pos -= 0.50
                t25_hit = True
            if l <= t50 and not t50_hit:
                pnl_pips += (entry - t50) * 10000.0 * 0.40
                pos -= 0.40
                t50_hit = True
            if t50_hit and pos > 0 and l <= t100:
                pnl_pips += (entry - t100) * 10000.0 * pos
                pos = 0
                break

    if pnl_pips != 0 or pos < 1.0:
        trades.append({
            'date': str(date_key), 'pnl_pips': pnl_pips,
            'tier': tier, 'ar': ar_pips, 'bias': bias,
            'asian_edge': asian_edge, 'entry': entry,
            't25': t25, 't50': t50, 't100': t100, 'sl': sl,
            't25_hit': t25_hit, 't50_hit': t50_hit,
            'sl_mode': sl_mode,
        })

    return trades


def run_backtest_sl_mode(df, sl_mode, start_date=None, end_date=None):
    if start_date: df = df[df['est_date'] >= start_date]
    if end_date:   df = df[df['est_date'] <= end_date]

    all_trades = []
    days = 0

    for dk in sorted(df['est_date'].unique()):
        day_bars = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
        if len(day_bars) < 10: continue

        ar = compute_asian_range(df, dk)
        if ar is None: continue

        tr = run_session_with_sl_mode(day_bars, ar['ah'], ar['al'], ar['ar_pips'], dk, sl_mode)
        if tr: all_trades.extend(tr)
        days += 1

    return all_trades, days


if __name__ == "__main__":
    print("=" * 70)
    print("SYMMETRY TRAP v7 — SL Calibration for M5 Close Bars")
    print("=" * 70)

    df = load_data()
    start_date = date(2024, 1, 1)
    end_date = date(2025, 12, 31)

    sl_modes = [
        ('opposite_band',  'v6 baseline: opposite Asian band (100% AR)'),
        ('entry_band',     'Entry-side Asian band edge'),
        ('asian_mid',      'Asian range midpoint (AH+AL)/2'),
        ('pct_75',         '75% of AR distance from entry'),
        ('pct_50',         '50% of AR distance from entry (halfway to opposite band)'),
        ('pct_33',         '33% of AR distance from entry'),
        ('pct_25',         '25% of AR distance from entry (tightest)'),
    ]

    results = []

    for sl_mode, description in sl_modes:
        tr, days = run_backtest_sl_mode(df, sl_mode, start_date, end_date)
        if not tr:
            print(f"\n{sl_mode}: No trades")
            results.append({'sl_mode': sl_mode, 'description': description, 'trades': 0})
            continue
        
        tdf = pd.DataFrame(tr)
        n = len(tdf)
        wr = (tdf['pnl_pips'] > 0).mean() * 100
        total = tdf['pnl_pips'].sum()
        wins = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].sum()
        losses = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].sum())
        pf = wins / losses if losses > 0 else 99
        avg_win = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].mean() if (tdf['pnl_pips'] > 0).any() else 0
        avg_loss = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].mean()) if (tdf['pnl_pips'] < 0).any() else 0
        sl_dist = (abs(tdf['entry'] - tdf['sl']) * 10000).mean()
        
        # SL losses: % of trades that lost to SL vs to time (12PM hard exit)
        sl_losses = len(tdf[(tdf['pnl_pips'] < 0) & (tdf['t25_hit'] == False)])
        total_losses = len(tdf[tdf['pnl_pips'] < 0])
        sl_loss_pct = (sl_losses / total_losses * 100) if total_losses > 0 else 0

        t25_rate = tdf['t25_hit'].mean() * 100
        t50_rate = tdf['t50_hit'].mean() * 100

        print(f"\n{'-'*65}")
        print(f"SL Mode: {sl_mode} — {description}")
        print(f"  Trades={n} | Days={days} | Avg SL dist: {sl_dist:.1f}p")
        print(f"  WR: {wr:.1f}% | PF: {pf:.2f} | Total: {total:.1f}p | Avg: {total/n:.1f}p")
        print(f"  Avg Win: {avg_win:.1f}p | Avg Loss: {avg_loss:.1f}p | Win/Loss ratio: {avg_win/avg_loss:.2f}")
        print(f"  T25 hit: {t25_rate:.1f}% | T50 hit: {t50_rate:.1f}%")
        print(f"  SL losses: {sl_losses}/{total_losses} ({sl_loss_pct:.0f}%) of losing trades from SL")

        tier_stats = {}
        for t in ['T1', 'T2', 'T3']:
            tf = tdf[tdf['tier'] == t]
            if len(tf) == 0: continue
            tier_stats[t] = {
                'n': len(tf), 'wr': (tf['pnl_pips'] > 0).mean() * 100,
                'avg': tf['pnl_pips'].mean(), 'total': tf['pnl_pips'].sum()
            }
            print(f"    {t}: {len(tf)} tr, WR {(tf['pnl_pips'] > 0).mean()*100:.1f}%, "
                  f"avg {tf['pnl_pips'].mean():.1f}p, total {tf['pnl_pips'].sum():.1f}p")

        results.append({
            'sl_mode': sl_mode, 'description': description,
            'trades': n, 'days': days, 'wr': wr, 'pf': pf,
            'total': total, 'avg': total/n, 'avg_win': avg_win, 'avg_loss': avg_loss,
            'sl_dist': sl_dist, 't25_rate': t25_rate, 't50_rate': t50_rate,
            'wins_pips': wins, 'losses_pips': losses,
        })

    # === WINNER SELECTION ===
    print(f"\n{'='*70}")
    print("CALIBRATION SUMMARY")
    print(f"{'='*70}")
    print(f"{'SL Mode':<18} {'Trades':>6} {'WR%':>7} {'PF':>6} {'Total':>8} {'AvgW':>7} {'AvgL':>7} {'SLdist':>7}")
    print(f"{'-'*18} {'-'*6} {'-'*7} {'-'*6} {'-'*8} {'-'*7} {'-'*7} {'-'*7}")
    
    for r in results:
        if r['trades'] == 0:
            continue
        marker = ' ◄ WINNER' if r == max(
            [x for x in results if x['trades'] > 0],
            key=lambda x: x['pf'] * (1 if x['wr'] > 40 else 0.5)
        ) else ''
        print(f"{r['sl_mode']:<18} {r['trades']:>6} {r['wr']:>6.1f}% {r['pf']:>6.2f} "
              f"{r['total']:>7.1f}p {r['avg_win']:>6.1f}p {r['avg_loss']:>6.1f}p {r['sl_dist']:>6.1f}p{marker}")

    # Now run the winner on full dataset
    print(f"\n{'='*70}")
    print("WINNER — FULL DATASET RUN")
    print(f"{'='*70}")
    
    best = max(
        [x for x in results if x['trades'] > 0],
        key=lambda x: x['pf'] * (1 if x['wr'] > 40 else 0.5)
    )
    print(f"Best SL mode: {best['sl_mode']} — {best['description']}")
    
    for pname, sd, ed in [("2024-2025", date(2024,1,1), date(2025,12,31)),
                            ("Full 2023H2-2026H1", date(2023,7,1), date(2026,6,30))]:
        tr, days = run_backtest_sl_mode(df, best['sl_mode'], sd, ed)
        if not tr: print(f"{pname}: No trades"); continue
        tdf = pd.DataFrame(tr)
        n = len(tdf)
        wr = (tdf['pnl_pips'] > 0).mean() * 100
        total = tdf['pnl_pips'].sum()
        wins_g = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].sum()
        losses_g = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].sum())
        pf = wins_g / losses_g if losses_g > 0 else 99
        
        print(f"\n{pname}: Days={days} Trades={n}")
        print(f"WR: {wr:.1f}% (v6=37%, manual=83-86%) | PF: {pf:.2f} (v6=0.29, manual=3.82)")
        print(f"Total: {total:.1f}p | Avg: {total/n:.1f}p")
        
        for t in ['T1','T2','T3']:
            tf = tdf[tdf['tier']==t]
            if len(tf)==0: continue
            print(f"  {t}: {len(tf)} tr, WR {(tf['pnl_pips']>0).mean()*100:.1f}%, "
                  f"avg {tf['pnl_pips'].mean():.1f}p, total {tf['pnl_pips'].sum():.1f}p")

