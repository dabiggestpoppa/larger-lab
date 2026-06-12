import pandas as pd
import numpy as np
from pathlib import Path

RAW_DATA_DIR = Path("quant-lab/data")

def load_m5(symbol):
    p = RAW_DATA_DIR / f'{symbol}_M5.csv'
    df = pd.read_csv(p)
    cm = {}
    for c in df.columns:
        cl = c.lower().strip()
        if cl in ('date','datetime','time','timestamp'): cm[c] = 'dt'
        elif cl in ('open','high','low','close'): cm[c] = cl
        elif cl in ('volume','vol','tickvol'): cm[c] = 'volume'
    df = df.rename(columns=cm)
    df['dt'] = pd.to_datetime(df['dt'], utc=True, errors='coerce')
    df = df.dropna(subset=['dt']).set_index('dt').sort_index()
    if 'volume' not in df.columns: df['volume'] = 0
    return df

def tier(ar_pips, symbol=""):
    if "BTC" in symbol:
        if ar_pips < 500: return "T1", ar_pips * 0.5, 52
        if ar_pips < 1000: return "T2", ar_pips * 0.5, 68
        if ar_pips < 2000: return "T3", ar_pips * 0.5, 94
        return "T4", 0.0, 999
    else:
        if ar_pips < 20: return "T1", ar_pips * 0.5, 52
        if ar_pips < 30: return "T2", ar_pips * 0.5, 68
        if ar_pips < 45: return "T3", ar_pips * 0.5, 94
        return "T4", 0.0, 999

df = load_m5('BTCUSD')
df['est_hour'] = (df.index.hour - 5) % 24
df['is_asian'] = (df['est_hour'] >= 19) | (df['est_hour'] < 3)
df['trade_date'] = df.index.date

# Check tier distribution
tiers = {'T1': 0, 'T2': 0, 'T3': 0, 'T4': 0}
for date, day_bars in df.groupby('trade_date'):
    if len(day_bars) < 20: continue
    ab = day_bars[day_bars['is_asian']]
    if len(ab) < 2: continue
    ah = ab['high'].max(); al = ab['low'].min()
    ar_p = (ah - al) * 10000
    t, _, _ = tier(ar_p, 'BTCUSD')
    tiers[t] += 1

print(f'BTC tier distribution: {tiers}')
print(f'Total days: {sum(tiers.values())}')

# Also check what ar_p values look like
arps = []
for date, day_bars in df.groupby('trade_date'):
    if len(day_bars) < 20: continue
    ab = day_bars[day_bars['is_asian']]
    if len(ab) < 2: continue
    ah = ab['high'].max(); al = ab['low'].min()
    arps.append((ah - al) * 10000)

arps = sorted(arps)
print(f'\nBTC AR percentiles:')
print(f'  Min:    {arps[0]:.0f} pips')
print(f'  10th:   {arps[len(arps)//10]:.0f} pips')
print(f'  25th:   {arps[len(arps)//4]:.0f} pips')
print(f'  50th:   {arps[len(arps)//2]:.0f} pips')
print(f'  75th:   {arps[3*len(arps)//4]:.0f} pips')
print(f'  90th:   {arps[9*len(arps)//10]:.0f} pips')
print(f'  Max:    {arps[-1]:.0f} pips')
