import sys
sys.path.insert(0, '.')
from symmetry_trap_backtest import load_m5_csv
from datetime import timedelta

bars, sym = load_m5_csv('../data/XAUUSD_M5.csv')

# Trace the bars around the EST day boundary for 2022-01-18 -> 2022-01-19
print("Bars around EST day boundary (2022-01-18 -> 2022-01-19):")
for bar in bars:
    est = bar.timestamp + timedelta(hours=-5)
    est_date = est.strftime('%Y-%m-%d')
    est_hour = est.hour
    
    if est_date in ['2022-01-18', '2022-01-19']:
        print(f"  UTC: {bar.timestamp} -> EST: {est_date} {est_hour:02d}:00 | H:{bar.high:.2f} L:{bar.low:.2f}")

# The key insight:
# - 2022-01-18 19:00 EST = 2022-01-19 00:00 UTC (start of Asian session)
# - 2022-01-19 03:00 EST = 2022-01-19 08:00 UTC (end of Asian session)
# - 2022-01-19 06:00 EST = 2022-01-19 11:00 UTC (first trading bar)

# So the Asian session for EST date 2022-01-19 is:
# - 2022-01-19 00:00 UTC (7PM EST 01-18) - ONLY 1 bar!
# - 2022-01-19 05:00-08:00 UTC (0AM-3AM EST 01-19) - MISSING!

# Wait, the data shows:
# - 2022-01-19 00:00 UTC -> EST 2022-01-18 19:00 (Asian session start)
# - 2022-01-19 11:10 UTC -> EST 2022-01-19 06:00 (trading session)

# There's a GAP from 00:00-11:00 UTC!
# This means the data doesn't have the 12AM-3AM EST bars for 2022-01-19

# Let me check if this is a data issue or a timezone issue
print("\n\nChecking for gaps in data:")
for i in range(len(bars) - 1):
    diff = (bars[i+1].timestamp - bars[i].timestamp).total_seconds()
    if diff > 3600:  # More than 1 hour gap
        print(f"  Gap: {bars[i].timestamp} -> {bars[i+1].timestamp} ({diff/3600:.1f} hours)")