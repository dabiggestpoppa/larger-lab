import sys
sys.path.insert(0, '.')
from symmetry_trap_backtest import load_m5_csv
from datetime import timedelta
from collections import defaultdict

bars, sym = load_m5_csv('../data/XAUUSD_M5.csv')

# Check the first 5 days of EST grouping
est_days = defaultdict(list)
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    est_days[dk].append(bar)

print("=== EST Day Grouping (Python runner) ===")
for dk in sorted(est_days.keys())[:5]:
    day_bars = sorted(est_days[dk], key=lambda b: b.timestamp)
    print(f"\nEST date {dk}: {len(day_bars)} bars")
    
    # Find Asian range
    ah, al = 0.0, 99999.0
    for b in day_bars:
        h = (b.timestamp.hour - 5) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    
    ar_pips = (ah - al) / 0.1 if ah > 0 and al < 99999 else 0
    print(f"  Asian range: {ar_pips:.1f} pips")
    
    # Check if this day has bars at 7PM EST (midnight UTC)
    has_7pm = any((b.timestamp.hour - 5) % 24 == 19 for b in day_bars)
    has_3am = any((b.timestamp.hour - 5) % 24 == 3 for b in day_bars)
    print(f"  Has 7PM EST bar: {has_7pm}, Has 3AM EST bar: {has_3am}")
    
    # Check bar timestamps
    for b in day_bars[:3]:
        est_h = (b.timestamp.hour - 5) % 24
        print(f"    UTC: {b.timestamp} -> EST hour: {est_h}")

# Now check UTC grouping
utc_days = defaultdict(list)
for bar in bars:
    dk = bar.timestamp.strftime('%Y-%m-%d')
    utc_days[dk].append(bar)

print("\n\n=== UTC Day Grouping (Nautilus-style) ===")
for dk in sorted(utc_days.keys())[:5]:
    day_bars = sorted(utc_days[dk], key=lambda b: b.timestamp)
    print(f"\nUTC date {dk}: {len(day_bars)} bars")
    
    # Find Asian range
    ah, al = 0.0, 99999.0
    for b in day_bars:
        h = (b.timestamp.hour - 5) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    
    ar_pips = (ah - al) / 0.1 if ah > 0 and al < 99999 else 0
    print(f"  Asian range: {ar_pips:.1f} pips")
    
    # Check bar timestamps
    for b in day_bars[:3]:
        est_h = (b.timestamp.hour - 5) % 24
        print(f"    UTC: {b.timestamp} -> EST hour: {est_h}")