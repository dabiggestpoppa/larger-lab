"""
SYMMETRY TRAP v5 — Built exactly from manual pseudocode (page 145)
==================================================================
Manual says:
  t25  = asian_edge + ar * 0.25 * bias
  t50  = asian_edge + ar * 0.50 * bias
  t100 = asian_edge + ar * 1.00 * bias

Where asian_edge = asian_high for LONG, asian_low for SHORT.
Bias: +1 for LONG, -1 for SHORT.

So t25 = asian_high + ar*0.25 for LONG (above band)
    t25 = asian_low - ar*0.25 for SHORT (below band)

SL = asian_low for LONG (opposite band edge) — close back inside = exit
    = asian_high for SHORT

Entry = opposite candle close (pullback from impulse)

KEY FIX: SL triggers on close BACK INSIDE the asian band, not just
touching the opposite edge. For LONG: close < asian_low. For SHORT: close > asian_high.
Wait, that's what I had. Let me re-read.

Actually, from the 81.2% rule: M5 close back inside Asian band = exit.
For SL on a LONG trade: close < asian_low (the opposite edge)
For SL on a SHORT trade: close > asian_high (the opposite edge)

That IS what I had before. Let me try a completely different approach:
build it EXACTLY as the manual's pseudocode and run it with ZERO spread.

Let me also carefully check: does the impulse need to close outside the band?
The manual says "Impulse >= trigger in bias direction". The impulse just needs
body >= atomic*0.5 in the bias direction. It does NOT need to close outside the band.
"""
import sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range
from datetime import date
import pandas as pd

SPREAD = 0.0

TIERS = {
    'T1': {'ar_max': 20, 'atomic': 10},
    'T2': {'ar_max': 30, 'atomic': 12},
    'T3': {'ar_max': 45, 'atomic': 15},
}

def classify_tier(ar_pips):
    if ar_pips < 20:  return 'T1'
    if ar_pips < 30:  return 'T2'
    if ar_pips <= 45: return 'T3'
    return 'NO_GO'

df = load_data()
all_trades = []

for dk in sorted(df['est_date'].unique()):
    day_bars = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
    if len(day_bars) < 10: continue
    ar_info = compute_asian_range(df, dk)
    if ar_info is None: continue
    ar_pips = ar_info['ar_pips']
    tier = classify_tier(ar_pips)
    if tier == 'NO_GO' or ar_pips < 3: continue

    params = TIERS[tier]
    atomic = params['atomic']
    ah = ar_info['ah']
    al = ar_info['al']
    ar_val = ar_pips / 10000.0

    # Filter to trading window 3AM-12PM
    window = day_bars[(day_bars['est_hour'] >= 3) & (day_bars['est_hour'] < 12)].reset_index(drop=True)
    if len(window) < 5: continue

    # ═══ LAYER 1: BIAS LOCK ═══
    bias = 0
    bias_idx = None
    for i in range(len(window)):
        row = window.iloc[i]
        if row['close'] > ah:
            bias = 1; bias_idx = i; break
        if row['close'] < al:
            bias = -1; bias_idx = i; break
    if bias == 0: continue

    # ═══ LAYER 2: ATOMIC ENTRY (exact manual pseudocode) ═══
    # for idx, row in post_bias.iterrows():
    #   if bias==1 and row['close']>row['open'] and body>=atomic*0.5:
    #     if next_candle['close'] < next_candle['open']:
    #       entry = next_candle['close']; break
    entry = None
    entry_idx = None

    for j in range(bias_idx + 1, len(window)):
        row = window.iloc[j]
        body = abs(row['close'] - row['open']) * 10000  # pips

        if bias == 1 and row['close'] > row['open'] and body >= atomic * 0.5:
            # Check next candle
            if j + 1 < len(window):
                next_row = window.iloc[j + 1]
                if next_row['close'] < next_row['open']:  # opposite (red) close
                    entry = next_row['close']
                    entry_idx = j + 1
                    break
        elif bias == -1 and row['close'] < row['open'] and body >= atomic * 0.5:
            if j + 1 < len(window):
                next_row = window.iloc[j + 1]
                if next_row['close'] > next_row['open']:  # opposite (green) close
                    entry = next_row['close']
                    entry_idx = j + 1
                    break

    if entry is None: continue

    # ═══ LAYER 3: DISTRIBUTION TARGETS ═══
    # t25 = asian_edge + ar * 0.25 * bias
    if bias == 1:
        asian_edge = ah  # the edge that was broken for bias
        sl = al          # opposite edge (close back inside = exit)
    else:
        asian_edge = al
        sl = ah

    t25  = asian_edge + ar_val * 0.25 * bias
    t50  = asian_edge + ar_val * 0.50 * bias
    t100 = asian_edge + ar_val * 1.00 * bias

    # ═══ MANAGEMENT (zero spread, check high/low for targets, close for SL) ═══
    pos = 1.0  # full position
    pnl = 0.0
    t25_hit = False
    t50_hit = False

    for k in range(entry_idx + 1, len(window)):
        row = window.iloc[k]
        h = row['high']
        l = row['low']
        c = row['close']
        eh = row['est_hour']

        # Hard exit 12PM
        if eh >= 12:
            if pos > 0:
                pnl += (c - entry) * bias * 10000 * pos
                pos = 0
            break

        # SL: close back inside Asian band
        if bias == 1 and c < sl:
            if pos > 0:
                pnl += (c - entry) * 10000 * pos
                pos = 0
            break
        if bias == -1 and c > sl:
            if pos > 0:
                pnl += (entry - c) * 10000 * pos
                pos = 0
            break

        # Target management (check wicks for target hits)
        if bias == 1:
            if h >= t25 and not t25_hit:
                pnl += (t25 - entry) * 10000 * 0.50
                pos -= 0.50
                t25_hit = True
            if h >= t50 and not t50_hit:
                pnl += (t50 - entry) * 10000 * 0.40
                pos -= 0.40
                t50_hit = True
            if t50_hit and pos > 0 and h >= t100:
                pnl += (t100 - entry) * 10000 * pos
                pos = 0
                break
        else:
            if l <= t25 and not t25_hit:
                pnl += (entry - t25) * 10000 * 0.50
                pos -= 0.50
                t25_hit = True
            if l <= t50 and not t50_hit:
                pnl += (entry - t50) * 10000 * 0.40
                pos -= 0.40
                t50_hit = True
            if t50_hit and pos > 0 and l <= t100:
                pnl += (entry - t100) * 10000 * pos
                pos = 0
                break

    if pnl != 0 or pos < 1.0:
        all_trades.append({
            'date': str(dk), 'pnl_pips': pnl, 'tier': tier, 'ar': ar_pips
        })

# ═══ RESULTS ═══
tdf = pd.DataFrame(all_trades)
n = len(tdf)
wr = (tdf['pnl_pips'] > 0).mean() * 100
total = tdf['pnl_pips'].sum()
wins = tdf[tdf['pnl_pips'] > 0]['pnl_pips'].sum()
losses = abs(tdf[tdf['pnl_pips'] < 0]['pnl_pips'].sum())
pf = wins / losses if losses > 0 else 99

print(f"=== SYMMETRY TRAP v5 (Exact Manual Pseudocode, Zero Spread) ===")
print(f"Period: 2023H2-2026H1 | Trades: {n}")
print(f"WR: {wr:.1f}%  (manual: 83-86%)")
print(f"PF: {pf:.2f}  (manual: 3.82)")
print(f"Total: {total:.1f}p | Avg: {total/n:.1f}p/trade")
print(f"Wins: {wins:.1f}p | Losses: {losses:.1f}p")

print(f"\nBy tier:")
for t in ['T1', 'T2', 'T3']:
    tf = tdf[tdf['tier'] == t]
    if len(tf) == 0: continue
    w = (tf['pnl_pips'] > 0).mean() * 100
    print(f"  {t}: {len(tf)} tr, WR {w:.1f}%, avg {tf['pnl_pips'].mean():.1f}p, total {tf['pnl_pips'].sum():.1f}p")

print(f"\nWin/Loss breakdown:")
print(f"  Avg win:  {tdf[tdf['pnl_pips']>0]['pnl_pips'].mean():.1f}p")
print(f"  Avg loss: {tdf[tdf['pnl_pips']<0]['pnl_pips'].mean():.1f}p")
print(f"  Win avg / Loss avg ratio: {tdf[tdf['pnl_pips']>0]['pnl_pips'].mean() / abs(tdf[tdf['pnl_pips']<0]['pnl_pips'].mean()):.2f}")

# What % of winners hit T25? T50? T100?
print(f"\nTarget hit analysis (winners only):")
winners = tdf[tdf['pnl_pips'] > 0]
if len(winners) > 0:
    # Estimate: if avg winner is > AR*0.25 in pips, T25 was hit
    print(f"  Avg winner: {winners['pnl_pips'].mean():.1f}p")
    print(f"  Median winner: {winners['pnl_pips'].median():.1f}p")
