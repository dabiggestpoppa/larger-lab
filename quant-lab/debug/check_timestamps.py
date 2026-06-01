import sys
sys.path.insert(0, '.')
from symmetry_trap_backtest import load_m5_csv
from datetime import timedelta

bars, sym = load_m5_csv('../data/XAUUSD_M5.csv')

# Check first 20 bars timestamps
print('First 20 bars (UTC):')
for bar in bars[:20]:
    est_dt = bar.timestamp + timedelta(hours=-5)
    print(f'  UTC: {bar.timestamp} -> EST: {est_dt.strftime("%Y-%m-%d %H:%M")}')

print()
print('Last 20 bars (UTC):')
for bar in bars[-20:]:
    est_dt = bar.timestamp + timedelta(hours=-5)
    print(f'  UTC: {bar.timestamp} -> EST: {est_dt.strftime("%Y-%m-%d %H:%M")}')