"""
Symmetry Trap v4 — Tick-Level SL Management
============================================
The manual's SL is OCC (Opposite Close Candle) extreme — CLOSE only.
But the KEY difference from Strategy Tester:
- Strategy Tester uses real tick data — SL triggers on wick through level
- M5 close-based backtest: SL only triggers on close < level
- This means our backtest SURVIVES more trades (no wick SL hits)

But we're still losing. Why?
1. The entry "opposite close" is in the WRONG direction — it's a pullback INTO the losing zone
2. The distribution targets assume continuation, but on M5 the bias break is often noise

Let me test: what if the "opposite close" is actually a CONFIRMATION that the move is stalling?
The MANUAL says to enter anyway. So maybe the issue is spread/slippage.

Test: Zero spread + instant fill at close + strict OCC SL.
"""
import sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
from shared import load_data, compute_asian_range
from datetime import date
import pandas as pd

SPREAD = 0.0

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
all_trades = []

for dk in sorted(df['est_date'].unique()):
    db = df[df['est_date'] == dk].sort_values('timestamp').reset_index(drop=True)
    if len(db) < 10: continue
    ar = compute_asian_range(df, dk)
    if ar is None: continue
    tier = classify_tier(ar['ar_pips'])
    if tier == 'NO_GO' or ar['ar_pips'] < 3: continue
    params = TIERS[tier]
    au = params['au']
    ah = ar['ah']; al = ar['al']
    ar_pips = ar['ar_pips']
    ar_val = ar_pips / 10000.0

    day = db[(db['est_hour']>=3) & (db['est_hour']<12)]
    bars = list(day.iterrows())
    if len(bars) < 5: continue

    # Bias lock
    bias = 0; bias_idx = None
    for i,(_, b) in enumerate(bars):
        if b['close'] > ah: bias = 1; bias_idx = i; break
        if b['close'] < al: bias = -1; bias_idx = i; break
    if bias == 0: continue

    # Entry: impulse + opposite close
    entry = None; eidx = None
    for j in range(bias_idx+1, len(bars)):
        _, b = bars[j]
        body = abs(b['close']-b['open'])*10000
        if bias==1 and b['close']>b['open'] and body>=au*0.5:
            if j+1<len(bars):
                _, nb = bars[j+1]
                if nb['close']<nb['open']:
                    entry=nb['close']; eidx=j+1; break
        elif bias==1 and b['close']<b['open'] and body>=au*0.5:
            pass  # wrong direction impulse
        elif bias==-1 and b['close']<b['open'] and body>=au*0.5:
            if j+1<len(bars):
                _, nb = bars[j+1]
                if nb['close']>nb['open']:
                    entry=nb['close']; eidx=j+1; break

    if entry is None: continue

    # Targets + management (tick-level: use high/low for target hits)
    if bias == 1:
        sl = al
        t25 = ah+ar_val*0.25; t50 = ah+ar_val*0.50; t100 = ah+ar_val*1.00
    else:
        sl = ah
        t25 = al-ar_val*0.25; t50 = al-ar_val*0.50; t100 = al-ar_val*1.00

    pos = 1.0; pnl = 0.0; t25h = False; t50h = False
    for j in range(eidx+1, len(bars)):
        _, b = bars[j]
        h = b['high']; l = b['low']; c = b['close']
        if b['est_hour'] >= 12:
            if pos > 0: pnl += (c-entry)*bias*10000*pos; pos = 0
            break
        # SL on CLOSE only (OCC)
        if bias==1 and c < sl:
            if pos > 0: pnl += (c-entry)*10000*pos; pos = 0
            break
        if bias==-1 and c > sl:
            if pos > 0: pnl += (entry-c)*10000*pos; pos = 0
            break
        # Target hits (use high/low for zero spread)
        if bias==1:
            if h >= t25 and not t25h: pnl += (t25-entry)*10000*0.5; pos-=0.5; t25h=True
            if h >= t50 and not t50h: pnl += (t50-entry)*10000*0.4; pos-=0.4; t50h=True
            if t50h and pos>0 and h >= t100: pnl += (t100-entry)*10000*pos; pos=0; break
        else:
            if l <= t25 and not t25h: pnl += (entry-t25)*10000*0.5; pos-=0.5; t25h=True
            if l <= t50 and not t50h: pnl += (entry-t50)*10000*0.4; pos-=0.4; t50h=True
            if t50h and pos>0 and l <= t100: pnl += (entry-t100)*10000*pos; pos=0; break

    if pnl != 0 or pos < 1.0:
        all_trades.append({'date': str(dk), 'pnl_pips': pnl, 'tier': tier, 'ar': ar_pips})

# Results
tdf = pd.DataFrame(all_trades)
n = len(tdf)
wr = (tdf['pnl_pips'] > 0).mean() * 100
total = tdf['pnl_pips'].sum()
wins = tdf[tdf['pnl_pips']>0]['pnl_pips'].sum()
losses = abs(tdf[tdf['pnl_pips']<0]['pnl_pips'].sum())
pf = wins/losses if losses > 0 else 99

print(f"ZERO SPREAD | Tick-level targets | Close-only SL")
print(f"Trades: {n} (full dataset 2023H2-2026H1)")
print(f"WR: {wr:.1f}% (manual: 83-86%)")
print(f"PF: {pf:.2f} (manual: 3.82)")
print(f"Total: {total:.1f}p | Avg: {total/n:.1f}p")

print("\nBy tier:")
for t in ['T1','T2','T3']:
    tf = tdf[tdf['tier']==t]
    if len(tf)==0: continue
    print(f"  {t}: {len(tf)} tr, WR {(tf['pnl_pips']>0).mean()*100:.1f}%, "
          f"avg {tf['pnl_pips'].mean():.1f}p, total {tf['pnl_pips'].sum():.1f}p")

print("\nBy AR size:")
tdf['ar_bin'] = pd.cut(tdf['ar'], bins=[0,15,20,25,30,35,40,45,100],
    labels=['<15','15-20','20-25','25-30','30-35','35-40','40-45','>45'])
for ab in ['<15','15-20','20-25','25-30','30-35','35-40','40-45']:
    tf = tdf[tdf['ar_bin']==ab]
    if len(tf)==0: continue
    print(f"  AR {ab}: {len(tf)} tr, WR {(tf['pnl_pips']>0).mean()*100:.1f}%, "
          f"avg {tf['pnl_pips'].mean():.1f}p")

# What % hit T25? T50? T100? SL?
print(f"\nTarget analysis:")
t25_count = sum(1 for t in all_trades if t['pnl_pips'] > 0)  # winners
sl_count = sum(1 for t in all_trades if t['pnl_pips'] < 0)   # losers
print(f"  Winners: {t25_count} ({t25_count/n*100:.1f}%)")
print(f"  Losers (SL): {sl_count} ({sl_count/n*100:.1f}%)")
print(f"  Avg win: {tdf[tdf['pnl_pips']>0]['pnl_pips'].mean():.1f}p")
print(f"  Avg loss: {tdf[tdf['pnl_pips']<0]['pnl_pips'].mean():.1f}p")
