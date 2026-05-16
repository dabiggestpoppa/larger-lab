"""Check when ar_pips gets set."""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
from nautilus.data_loader import _parse_csv
from pathlib import Path
import pandas as pd

df = _parse_csv(Path(r'C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv'))
df = df.tail(50000).copy()
df['est_hour'] = (df.index.hour - 5 + 24) % 24
df['date'] = df.index.date

# Check: for day 2 (which has Asian range), what happens at 3AM EST?
date = df['date'].unique()[1]
day = df[df['date'] == date]

# Show bars around 3AM EST (est_h == 3)
print("Bars around 3AM EST on 2025-09-03:")
window = day[(day['est_hour'] >= 2) & (day['est_hour'] <= 4)]
for idx, row in window.head(10).iterrows():
    print(f"  {idx} | est_h={row['est_hour']} | O={row['open']:.5f} H={row['high']:.5f} L={row['low']:.5f} C={row['close']:.5f}")

# The issue: est_h == 3 means the bar STARTS at 3AM EST
# But the Asian range should be classified at the FIRST bar of 3AM
# Let's check if the condition `est_h == 3` is ever True
print(f"\nBars with est_h == 3: {(day['est_hour'] == 3).sum()}")
print(f"Bars with est_h == 2: {(day['est_hour'] == 2).sum()}")

# Check the actual UTC hours
print(f"\nUTC hours in day: {sorted(day.index.hour.unique())}")
print(f"EST hours in day: {sorted(day['est_hour'].unique())}")

# The real issue: the Asian session ends at 3AM EST = 8:00 UTC
# But the bar at 8:00 UTC has est_h = 3, and the condition is `est_h == 3`
# However, the bar at 8:00 UTC is the FIRST bar of the 3AM hour
# The Asian range high/low should already be set from the previous bars
# Let's verify
asian = day[(day['est_hour'] >= 19) | (day['est_hour'] < 3)]
print(f"\nAsian bars: {len(asian)}")
print(f"Asian high: {asian['high'].max():.5f}")
print(f"Asian low: {asian['low'].min():.5f}")
print(f"Asian range: {(asian['high'].max() - asian['low'].min()) * 10000:.1f}p")

# Now check: does the bar at est_h == 3 have the Asian data?
bar_at_3am = day[day['est_hour'] == 3]
if len(bar_at_3am) > 0:
    print(f"\nFirst bar at est_h==3: {bar_at_3am.index[0]}")
    print(f"  This bar's high: {bar_at_3am.iloc[0]['high']:.5f}")
    print(f"  This bar's low: {bar_at_3am.iloc[0]['low']:.5f}")
