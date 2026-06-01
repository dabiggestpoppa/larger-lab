import sys
sys.path.insert(0, '.')
from symmetry_trap_backtest import load_m5_csv
from datetime import timedelta
from collections import defaultdict

bars, sym = load_m5_csv('../data/XAUUSD_M5.csv')

# The Asian session for EST date 2022-01-19 is:
# - 7PM-11PM EST 01-18 (UTC 00:00-05:00 on 01-19)
# - 12AM-3AM EST 01-19 (UTC 05:00-08:00 on 01-19)

# Let me check the bars more carefully
print("All bars with EST date 2022-01-18 or 2022-01-19:")
for bar in bars:
    est = bar.timestamp + timedelta(hours=-5)
    est_date = est.strftime('%Y-%m-%d')
    est_hour = est.hour
    
    if est_date in ['2022-01-18', '2022-01-19']:
        print(f"  UTC: {bar.timestamp} -> EST: {est_date} {est_hour:02d}:00 | H:{bar.high:.2f} L:{bar.low:.2f}")

# Now let me check the actual Asian session bars for EST 2022-01-19
print("\n\nAsian session bars for EST 2022-01-19:")
asian_bars = []
for bar in bars:
    est = bar.timestamp + timedelta(hours=-5)
    est_date = est.strftime('%Y-%m-%d')
    est_hour = est.hour
    
    # Asian session for EST date 2022-01-19:
    # - Bars with EST date 2022-01-18 and hour >= 19 (7PM-11PM)
    # - Bars with EST date 2022-01-19 and hour < 3 (12AM-3AM)
    if (est_date == '2022-01-18' and est_hour >= 19) or (est_date == '2022-01-19' and est_hour < 3):
        asian_bars.append(bar)
        print(f"  UTC: {bar.timestamp} -> EST: {est_date} {est_hour:02d}:00 | H:{bar.high:.2f} L:{bar.low:.2f}")

print(f"\nTotal Asian bars for EST 2022-01-19: {len(asian_bars)}")