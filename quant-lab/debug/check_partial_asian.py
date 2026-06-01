import sys
sys.path.insert(0, '.')
from symmetry_trap_backtest import load_m5_csv
from datetime import timedelta
from collections import defaultdict

bars, sym = load_m5_csv('../data/XAUUSD_M5.csv')

xau_tiers = {
    'T1': {'ar_max': 32.0, 'au': 16.0, 'trigger': 19.0},
    'T2': {'ar_max': 58.0, 'au': 29.0, 'trigger': 35.0},
    'T3': {'ar_max': 95.0, 'au': 48.0, 'trigger': 58.0},
}

# The key difference:
# Method A (Python runner): Groups by EST date, skips days with incomplete Asian range
# Method B (Nautilus-style): Processes sequentially, creates session at 3AM even with partial Asian range

# Let's trace what happens with days that only have 7PM-11PM EST bars

# Find EST days that have bars at 7PM but NOT at 3AM
est_days = defaultdict(list)
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    est_days[dk].append(bar)

partial_asian_days = []
for dk, day_bars in est_days.items():
    has_7pm = any((b.timestamp.hour - 5) % 24 == 19 for b in day_bars)
    has_3am = any((b.timestamp.hour - 5) % 24 == 3 for b in day_bars)
    
    if has_7pm and not has_3am:
        partial_asian_days.append(dk)

print(f"EST days with 7PM but no 3AM: {len(partial_asian_days)}")
print(f"First 10: {partial_asian_days[:10]}")

# For these days, what's the Asian range?
print("\nAsian range for partial days:")
for dk in partial_asian_days[:5]:
    day_bars = est_days[dk]
    ah, al = 0.0, 99999.0
    for b in day_bars:
        h = (b.timestamp.hour - 5) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    
    ar_pips = (ah - al) / 0.1
    tier = "NO_GO"
    for t in ['T1', 'T2', 'T3']:
        if ar_pips <= xau_tiers[t]['ar_max']:
            tier = t
            break
    
    print(f"  {dk}: AR={ar_pips:.1f}p, Tier={tier}")

# Now let's check what the Nautilus-style method does
# It processes bars sequentially, so when a new EST day arrives at 3AM,
# it has already accumulated the 7PM-11PM EST bars from the previous UTC day

# Let's trace the first few days
print("\n=== Tracing sequential processing ===")
current_date = None
asian_high = 0.0
asian_low = 99999.0

for bar in bars[:50]:
    est = bar.timestamp + timedelta(hours=-5)
    est_hour = est.hour
    est_date = est.strftime('%Y-%m-%d')
    
    # New day detection
    if est_date != current_date:
        if current_date is not None:
            ar_pips = (asian_high - asian_low) / 0.1 if asian_high > 0 and asian_low < 99999 else 0
            print(f"Day changed: {current_date} -> {est_date}")
            print(f"  Asian range: {ar_pips:.1f}p (H:{asian_high} L:{asian_low})")
        
        current_date = est_date
        asian_high = 0.0
        asian_low = 99999.0
    
    # Asian tracking
    if est_hour >= 19 or est_hour < 3:
        asian_high = max(asian_high, bar.high)
        asian_low = min(asian_low, bar.low)
        print(f"  Asian bar: UTC {bar.timestamp} -> EST {est_hour:02d}:00 | H:{bar.high:.2f} L:{bar.low:.2f}")