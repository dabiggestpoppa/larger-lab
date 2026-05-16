"""Check est_h values during Asian session."""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
from nautilus.data_loader import _parse_csv
from pathlib import Path
import pandas as pd

df = _parse_csv(Path(r'C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv'))
df = df.tail(50000).copy()
df['est_hour'] = (df.index.hour - 5 + 24) % 24
df['date'] = df.index.date

# Check est_h values for Asian session bars on day 2
date = df['date'].unique()[1]
day = df[df['date'] == date]
asian = day[(day['est_hour'] >= 19) | (day['est_hour'] < 3)]

print(f"Asian bars est_h values: {sorted(asian['est_hour'].unique())}")
print(f"Count per est_h:")
for eh in sorted(asian['est_hour'].unique()):
    count = (asian['est_hour'] == eh).sum()
    print(f"  est_h={eh}: {count} bars")

# The issue: est_h < 3 means est_h can be 0, 1, 2
# But the condition is `est_h == 3` which is the END of Asian
# The bar at est_h=3 is NOT in the Asian session (it's the first bar AFTER Asian)
# So the condition `if est_h == 3` is checked AFTER the `if est_h >= 19 or est_h < 3` block
# But wait - the code structure is:
#   if est_h >= 19 or est_h < 3:  <-- this is the Asian block
#       ...track high/low...
#       if est_h == 3:  <-- this is INSIDE the Asian block
#           ar_pips = ...
#       continue
#
# The problem: est_h == 3 does NOT satisfy `est_h >= 19 or est_h < 3`
# So the Asian block is NEVER entered when est_h == 3!
# The `if est_h == 3` check is inside the Asian block but est_h==3 doesn't trigger it!

print("\n=== BUG FOUND ===")
print("est_h == 3 does NOT satisfy 'est_h >= 19 or est_h < 3'")
print("So the 'if est_h == 3' condition inside the Asian block is DEAD CODE")
print("ar_pips is NEVER set!")

# The fix: classify the Asian range when est_h == 3 (first bar OUTSIDE Asian)
# This should be done OUTSIDE the Asian block
