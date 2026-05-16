"""Minimal trace to find the bug."""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
from nautilus.data_loader import _parse_csv
from pathlib import Path
import pandas as pd

df = _parse_csv(Path(r'C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv'))
df = df.tail(50000).copy()
df['est_hour'] = (df.index.hour - 5 + 24) % 24
df['date'] = df.index.date

# Check: for a specific GO day, do we see P90 signals?
date = df['date'].unique()[1]  # Skip first day (no asian)
day = df[df['date'] == date]
print(f"Date: {date}, bars: {len(day)}")

# Asian
asian = day[(day['est_hour'] >= 19) | (day['est_hour'] < 3)]
ah = asian['high'].max()
al = asian['low'].min()
ar = (ah - al) * 10000
print(f"Asian: high={ah:.5f} low={al:.5f} AR={ar:.1f}p")

# Entry window
entry = day[(day['est_hour'] >= 2) & (day['est_hour'] < 11)]
entry = entry.copy()
entry['body_pips'] = abs(entry['close'] - entry['open']) * 10000
entry['est_h'] = entry['est_hour']

# Check thresholds
p90_thresholds = {(2, 4): 4.1, (4, 6): 4.6, (6, 8): 4.6, (8, 10): 5.9, (10, 11): 6.2}
def get_thresh(eh):
    for (s, e), t in p90_thresholds.items():
        if s <= eh < e: return t
    return 6.2

entry['threshold'] = entry['est_h'].apply(get_thresh)
entry['passes'] = entry['body_pips'] >= entry['threshold']
entry['bull'] = (entry['close'] > entry['open']) & entry['passes']
entry['bear'] = (entry['close'] < entry['open']) & entry['passes']

print(f"Entry bars: {len(entry)}")
print(f"Bull signals: {entry['bull'].sum()}")
print(f"Bear signals: {entry['bear'].sum()}")

# Show first few signals
signals = entry[entry['bull'] | entry['bear']]
if len(signals) > 0:
    print("\nFirst 5 signals:")
    for idx, row in signals.head(5).iterrows():
        dir = "BULL" if row['bull'] else "BEAR"
        print(f"  {idx} | {dir} | body={row['body_pips']:.1f}p | thresh={row['threshold']:.1f}p | est_h={row['est_h']}")
else:
    print("\nNo signals found!")
    print("Body pips distribution:")
    print(entry['body_pips'].describe())
    print(f"\nMax body: {entry['body_pips'].max():.1f}p")
    print(f"Bars with body >= 4.1: {(entry['body_pips'] >= 4.1).sum()}")
