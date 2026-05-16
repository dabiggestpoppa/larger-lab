"""Quick debug: check Asian Range and P90 signal detection."""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
from nautilus.data_loader import _parse_csv
from pathlib import Path
import pandas as pd

df = _parse_csv(Path(r'C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv'))
df = df.tail(50000).copy()
df['est_hour'] = (df.index.hour - 5 + 24) % 24
df['date'] = df.index.date

print("=== ASIAN RANGE CHECK (first 5 days) ===")
for date in list(df['date'].unique())[:5]:
    day = df[df['date'] == date]
    asian = day[(day['est_hour'] >= 19) | (day['est_hour'] < 3)]
    if len(asian) > 0:
        ah = asian['high'].max()
        al = asian['low'].min()
        ar_pips = (ah - al) * 10000
        print(f'  {date}: AR={ar_pips:.1f}p | high={ah:.5f} | low={al:.5f} | bars={len(asian)}')
    else:
        print(f'  {date}: NO asian bars')

print("\n=== P90 SIGNAL CHECK ===")
entry = df[(df['est_hour'] >= 2) & (df['est_hour'] < 11)]
entry['body_pips'] = abs(entry['close'] - entry['open']) * 10000
print(f'  Entry window bars: {len(entry)}')
print(f'  Body pips: mean={entry["body_pips"].mean():.2f}, max={entry["body_pips"].max():.2f}')
print(f'  Bars >= 4.1p: {(entry["body_pips"] >= 4.1).sum()}')
print(f'  Bars >= 6.2p: {(entry["body_pips"] >= 6.2).sum()}')

# Check how many days have AR < 45 (GO days)
print("\n=== TIER DISTRIBUTION ===")
go_days = 0
nogo_days = 0
for date in df['date'].unique():
    day = df[df['date'] == date]
    asian = day[(day['est_hour'] >= 19) | (day['est_hour'] < 3)]
    if len(asian) > 0:
        ar = (asian['high'].max() - asian['low'].min()) * 10000
        if ar < 45:
            go_days += 1
        else:
            nogo_days += 1
print(f'  GO days (AR<45): {go_days}')
print(f'  NO-GO days (AR>=45): {nogo_days}')
print(f'  Total days: {go_days + nogo_days}')
