# If CSV has 1599 days from 2022-01-03 to 2026-05-21
# And baseline used 1336 days
# Then baseline data ended at: 2022-01-03 + 1336 days

from datetime import datetime, timedelta

start = datetime(2022, 1, 3)
baseline_end = start + timedelta(days=1336)
new_end = start + timedelta(days=1599)

print(f"CSV start: {start.date()}")
print(f"Baseline end (1336 days): {baseline_end.date()}")
print(f"New sweep end (1599 days): {new_end.date()}")
print(f"Extra data in new CSV: {(new_end - baseline_end).days} days")

# The baseline was generated on June 4th
# If the CSV at that time only had data up to ~mid 2025
# And now it has data up to May 2026
# That's the 263 day difference

# But the trade rate difference is 44x, not just "fewer days"
# Baseline: 5599 trades / 1336 days = 4.19 tr/d
# New: 153 trades / 1599 days = 0.096 tr/d

# Even if we only compare the same 1336 days:
# New sweep would have: 0.096 * 1336 = 128 trades
# Baseline: 5599 trades
# Still 44x difference!

print(f"\nEven comparing same 1336 day period:")
print(f"  Baseline: 5599 trades")
print(f"  New (extrapolated): {0.096 * 1336:.0f} trades")
print(f"  Ratio: {5599/(0.096*1336):.1f}x")

# The engine code changed. Let me check the OLD engine more carefully.
# The key difference: OLD engine had classify_tier() at session init
# NEW engine has classify_tier_by_ar() (gate only) + classify_tier_by_impulse() at detection

# OLD classify_tier():
#   for tier_name in ("T1", "T2", "T3"):
#     if tier_name in tier_config and asian_range_pips <= tier_config[tier_name]["ar_max"]:
#       cfg = tier_config[tier_name]
#       return tier_name, cfg["au"], cfg["trigger"]
#   return "NO_GO", 0.0, 0.0

# For CHFJPY:
#   T1: ar_max=28, au=14, trigger=17
#   T2: ar_max=48, au=24, trigger=29
#   T3: ar_max=85, au=42, trigger=50

# OLD: Session init sets tier based on AR
#   AR <= 28p -> T1 (trigger=17, au=14)
#   AR <= 48p -> T2 (trigger=29, au=24)  
#   AR <= 85p -> T3 (trigger=50, au=42)
#   AR > 85p -> NO_GO

# NEW: Session init only checks AR gate (ar_max=60 for all tiers in DEFAULT_TIER_CONFIG)
#   But wait - the asset config has ar_max values 28, 48, 85
#   And classify_tier_by_ar uses self.tier_config which comes from ASSET_CONFIGS
#   So the AR gate checks: AR <= 28 (T1 ar_max) -> passes
#   If AR > 28: AR <= 48 (T2 ar_max) -> passes
#   If AR > 48: AR <= 85 (T3 ar_max) -> passes
#   If AR > 85: NO_GO

# So the AR gate behavior is THE SAME between old and new!
# The difference is in what happens AFTER the gate

# OLD: After gate, tier is set, trigger is locked
#   T1 sessions use trigger=17 for impulse detection
#   T2 sessions use trigger=29
#   T3 sessions use trigger=50

# NEW: After gate, tier=PENDING, uses T1 trigger for detection
#   ALL sessions use trigger=17 (T1) for impulse detection
#   Then classifies by impulse size

# This means NEW engine should detect MORE impulses (lower trigger for T2/T3 sessions)
# But we see FAR FEWER trades

# UNLESS: the issue is in how the backtest processes the signals
# Let me check if the backtest's run() method changed

print("\n=== CHECKING BACKTEST RUN METHOD ===")
print("The backtest creates SymmetryTrapEngine with tier_config=self.tier_config")
print("In the new sweep, tier_config comes from build_scaled_config()")
print("At mult=1.0, this is IDENTICAL to raw ASSET_CONFIGS")
print("")
print("BUT: the engine's __init__ also reads config.get('pip_value')")
print("And the backtest passes config=scaled_config")
print("Let me check if pip_value differs...")

import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
from asset_configs import ASSET_CONFIGS

chf = ASSET_CONFIGS['CHFJPY']
print(f"\nCHFJPY config:")
for k, v in chf.items():
    if k != 'tiers':
        print(f"  {k}: {v}")
    else:
        for t, tv in v.items():
            print(f"  tiers.{t}: {tv}")

# Check: does the engine use pip_value correctly?
# CHFJPY pip_value = 0.01
# But JPY pairs need pip_size = 0.07 (not 0.01!)
# 0.01 is the price increment, but 1 pip for JPY = 0.01 in price = 0.01/0.01 = 1 pip
# Actually for JPY pairs, 1 pip = 0.01 in price terms
# And the sweep uses pip_size = 0.07 for JPY pairs

print("\n=== PIP SIZE ANALYSIS ===")
print("CHFJPY pip_value from config: 0.01")
print("Sweep uses pip_size: 0.07 (for JPY pairs)")
print("Engine __init__: self.pip_size = config.get('pip_value', pip_size)")
print("  -> self.pip_size = 0.01 (from config, overriding 0.07!)")
print("")
print("*** THIS IS THE BUG! ***")
print("The engine reads pip_value=0.01 from config")
print("But the sweep intended to use pip_size=0.07")
print("0.01 vs 0.07 = 7x difference in pip calculation")
print("")
print("With pip_size=0.01:")
print("  A 17 pip trigger = 17 * 0.01 = 0.17 price units")
print("  A 170 pip move = 170 * 0.01 = 1.7 price units")
print("")
print("With pip_size=0.07:")
print("  A 17 pip trigger = 17 * 0.07 = 1.19 price units")
print("  A 170 pip move = 170 * 0.07 = 11.9 price units")
print("")
print("Wait - that's backwards. Let me recalculate.")
print("For CHFJPY, price is around 150-200")
print("1 pip = 0.01 (for JPY pairs)")
print("So pip_size should be 0.01, not 0.07")
print("")
print("But the sweep uses 0.07 for JPY pairs...")
print("That's 7x too large!")
print("With pip_size=0.07, a 17 pip trigger = 17 * 0.07 = 1.19 price units")
print("But the actual price moves in CHFJPY are measured in 0.01 increments")
print("So the trigger is 7x LARGER than intended")
print("-> 7x fewer impulses detected -> 7x fewer trades")
print("")
print("But 7x doesn't explain 44x...")
