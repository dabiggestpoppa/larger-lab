"""
DISTRIBUTION SYMMETRY TRAP ENGINE — Exact Manual Specification (Pages 145-154)
================================================================================
Three-layer system:
  LAYER 1 — BIAS LOCK: First M5 close outside Asian Range → direction for session
  LAYER 2 — ATOMIC ENTRY: Impulse candle in bias direction (body >= AU x 0.5)
               + NEXT candle closes opposite → ENTER on pullback close
  LAYER 3 — DISTRIBUTION TARGETS: -25%/-50%/-100% of Asian Range from band edge

SL: M5 CLOSE back inside Asian band (81.2% rule — NOT wicks, CLOSES only)
HARD EXIT: 12:00 PM EST

PREVIOUS ENGINES WERE WRONG — they used SL calibration, band re-entry, Goldilocks
concepts that do NOT exist in the Symmetry Trap specification.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np

sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range

TIER_PARAMS = {
    'T1': {'ar_max': 20, 'au': 10, 'trigger': 12},
    'T2': {'ar_max': 30, 'au': 12, 'trigger': 15},
    'T3': {'ar_max': 45, 'au': 15, 'trigger': 19},
}

def classify_tier(ar_pips):
    if ar_pips < 20: return 'T1'
    elif ar_pips < 30: return 'T2'
    elif ar_pips <= 45: return 'T3'
    return 'NO_GO'

def run_symmetry_trap_day(day_bars, ar_info):
    trades = []
    ah = ar_info['ah']
    al = ar_info['al']
    ar_pips = ar_info['ar_pips']
    date_key = ar_info['date_key']
    tier = classify_tier(ar_pips)
    if tier == 'NO_GO' or ar_pips < 3:
        return trades
    au = TIER_PARAMS[tier]['au']

    # Session window: 2AM-12PM EST (use est_hour column directly)
    window = day_bars[(day_bars['est_hour'] >= 2) & (day_bars['est_hour'] < 12)].copy()
    if len(window) < 10:
        return trades

    # === LAYER 1: BIAS LOCK ===
    # First M5 close outside Asian band → sets direction for entire session
    bias = None
    bias_edge = None
    for i in range(len(window)):
        row = window.iloc[i]
        if row['est_hour'] < 2:
            continue
        if row['close'] > ah:
            bias = 1; bias_edge = ah; break
        elif row['close'] < al:
            bias = -1; bias_edge = al; break
    if bias is None:
        return trades

    # === LAYER 2: ATOMIC ENTRY ===
    # Impulse in bias direction (body >= AU x 0.5) then NEXT candle closes opposite
    entry = None
    for i in range(len(window)):
        row = window.iloc[i]
        if row['est_hour'] < 2 or row['est_hour'] >= 12:
            continue
        body = abs(row['close'] - row['open']) * 10000
        is_bull = row['close'] > row['open']
        is_bear = row['close'] < row['open']

        impulse_ok = (bias == 1 and is_bull and body >= au * 0.5) or \
                     (bias == -1 and is_bear and body >= au * 0.5)

        if impulse_ok and i + 1 < len(window):
            nxt = window.iloc[i + 1]
            if nxt['est_hour'] >= 12:
                break
            nxt_bull = nxt['close'] > nxt['open']
            nxt_bear = nxt['close'] < nxt['open']
            # Pullback: next candle closes opposite direction
            if bias == 1 and nxt_bear:
                entry = {'price': nxt['close'], 'idx': i + 1}
                break
            elif bias == -1 and nxt_bull:
                entry = {'price': nxt['close'], 'idx': i + 1}
                break
    if entry is None:
        return trades

    # === LAYER 3: TARGETS + MANAGEMENT ===
    entry_price = entry['price']
    if bias == 1:
        t25 = bias_edge + (ar_pips * 0.25 / 10000)
        t50 = bias_edge + (ar_pips * 0.50 / 10000)
        t100 = bias_edge + (ar_pips * 1.00 / 10000)
        sl_level = al  # close below Asian Low = invalidated
    else:
        t25 = bias_edge - (ar_pips * 0.25 / 10000)
        t50 = bias_edge - (ar_pips * 0.50 / 10000)
        t100 = bias_edge - (ar_pips * 1.00 / 10000)
        sl_level = ah  # close above Asian High = invalidated

    t25_hit = t50_hit = t100_hit = False
    final_pnl = 0.0

    for i in range(entry['idx'] + 1, len(window)):
        row = window.iloc[i]
        if row['est_hour'] >= 12:
            break  # 12PM hard exit

        # SL: close back inside Asian band
        if bias == 1 and row['close'] <= sl_level:
            final_pnl = (row['close'] - entry_price) * 10000
            break
        if bias == -1 and row['close'] >= sl_level:
            final_pnl = (entry_price - row['close']) * 10000
            break

        if bias == 1:
            if not t25_hit and row['close'] >= t25:
                t25_hit = True
            if not t50_hit and row['close'] >= t50:
                t50_hit = True
            if not t100_hit and row['close'] >= t100:
                t100_hit = True
                final_pnl = (t100 - entry_price) * 10000
                break
        else:
            if not t25_hit and row['close'] <= t25:
                t25_hit = True
            if not t50_hit and row['close'] <= t50:
                t50_hit = True
            if not t100_hit and row['close'] <= t100:
                t100_hit = True
                final_pnl = (entry_price - t100) * 10000
                break
    else:
        # Loop completed without break = hard exit at window end
        last = window.iloc[-1]
        final_pnl = (last['close'] - entry_price) * 10000 * bias

    if final_pnl == 0 and t25_hit:
        # Didn't break on SL or TP, check where we ended
        last = window.iloc[-1]
        final_pnl = (last['close'] - entry_price) * 10000 * bias

    trades.append({
        'date': date_key, 'tier': tier, 'bias': bias,
        'ar_pips': ar_pips, 'au': au,
        't25_hit': t25_hit, 't50_hit': t50_hit, 't100_hit': t100_hit,
        'pnl_pips': final_pnl,
        'sl_hit': (bias == 1 and final_pnl < 0 and not t25_hit) or \
                   (bias == -1 and final_pnl < 0 and not t25_hit),
    })
    return trades


def run_backtest():
    df = load_data()
    if df is None or len(df) == 0:
        print("No data loaded"); return

    all_dates = sorted(df['est_date'].unique())
    print(f"{'='*60}")
    print(f"DISTRIBUTION SYMMETRY TRAP — Exact Manual Spec")
    print(f"{'='*60}")
    print(f"Data: {len(df)} bars | {len(all_dates)} sessions")
    print(f"Layers: Bias Lock → Atomic Entry → Distribution Targets")
    print(f"{'='*60}")

    all_trades = []
    for dk in all_dates:
        day_bars = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
        if len(day_bars) < 10: continue
        ar_info = compute_asian_range(day_bars, dk)
        if ar_info is None: continue
        ar_info['date_key'] = dk
        trades = run_symmetry_trap_day(day_bars, ar_info)
        all_trades.extend(trades)

    if not all_trades:
        print("No trades generated"); return

    wins = [t for t in all_trades if t['pnl_pips'] > 0]
    losses = [t for t in all_trades if t['pnl_pips'] <= 0]
    wr = len(wins) / len(all_trades) * 100
    total_pnl = sum(t['pnl_pips'] for t in all_trades)
    avg_pnl = total_pnl / len(all_trades)
    avg_win = np.mean([t['pnl_pips'] for t in wins]) if wins else 0
    avg_loss = np.mean([abs(t['pnl_pips']) for t in losses]) if losses else 0
    pf = (avg_win * len(wins)) / (avg_loss * len(losses)) if losses and avg_loss > 0 else float('inf')
    t25h = len([t for t in all_trades if t['t25_hit']])
    t50h = len([t for t in all_trades if t['t50_hit']])
    t100h = len([t for t in all_trades if t['t100_hit']])
    slh = len([t for t in all_trades if t['sl_hit']])

    print(f"\nTotal trades: {len(all_trades)}")
    print(f"Win Rate: {wr:.1f}% ({len(wins)}/{len(all_trades)})")
    print(f"Total PnL: {total_pnl:.1f} pips | Avg: {avg_pnl:.2f} pips")
    print(f"Avg Win: {avg_win:.1f}p | Avg Loss: {avg_loss:.1f}p | PF: {pf:.2f}")
    print(f"\nTarget Hits: T25={t25h} ({t25h/len(all_trades)*100:.0f}%) | T50={t50h} ({t50h/len(all_trades)*100:.0f}%) | T100={t100h} ({t100h/len(all_trades)*100:.0f}%)")
    print(f"SL hits: {slh} ({slh/len(all_trades)*100:.1f}%)")

    for tn in ['T1','T2','T3']:
        tt = [t for t in all_trades if t['tier']==tn]
        if not tt: continue
        tw = len([t for t in tt if t['pnl_pips']>0])
        print(f"  {tn}: {len(tt)} tr | WR:{tw/len(tt)*100:.1f}% | PnL:{sum(t['pnl_pips'] for t in tt):.1f}p | T25:{len([t for t in tt if t['t25_hit']])} T50:{len([t for t in tt if t['t50_hit']])}")

    print(f"\nMANUAL: WR=83-86% T25=42%/91%WR T50=31%/88%WR SL=~3% PF=3.82")
    return all_trades

if __name__ == '__main__':
    run_backtest()
