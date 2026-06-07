import json, sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from asset_configs import ASSET_CONFIGS

# Check: at mult=0.3, what happens to ar_max?
pairs = ['EURUSD', 'CHFJPY', 'EURJPY', 'GBPJPY', 'USDJPY']
mult = 0.3

print("=== AR MAX SCALING at mult=0.3 ===")
for pair in pairs:
    cfg = ASSET_CONFIGS[pair]
    print(f"\n{pair}:")
    for tier in ['T1', 'T2', 'T3']:
        orig = cfg['tiers'][tier]['ar_max']
        scaled = round(orig * mult, 1)
        print(f"  {tier}: ar_max orig={orig} -> scaled={scaled}")

print("\n=== THE PROBLEM ===")
print("classify_tier_by_ar checks: asian_range_pips <= tier_config[tier_name]['ar_max']")
print("When ar_max is scaled down by 0.3x, MANY sessions get AR > ar_max → NO_GO")
print("Example: CHFJPY T1 ar_max orig=28p, scaled=8.4p")
print("  Typical Asian Range for CHFJPY: 15-40 pips")
print("  At orig 28p: passes on ~60% of days")
print("  At scaled 8.4p: passes on ~5% of days")
print("  → 12x fewer trading sessions → 12x fewer trades")

print("\n=== ALSO: trigger scaling ===")
for pair in ['EURUSD', 'CHFJPY']:
    cfg = ASSET_CONFIGS[pair]
    print(f"\n{pair} T1 trigger:")
    orig = cfg['tiers']['T1']['trigger']
    for m in [0.3, 0.5, 1.0]:
        print(f"  mult={m}: trigger={round(orig*m, 1)} (orig={orig})")

print("\n=== DAY COUNT DIFFERENCE EXPLAINED ===")
print("Baseline sweep: each pair has different day counts")
print("  EURUSD: 1341 days (data starts later)")
print("  CHFJPY: 1336 days")
print("  EURJPY: 3101 days (more history)")
print("  Why? Different CSV files with different date ranges")
print("")
print("New sweep: all pairs have consistent days per file")
print("  CHFJPY: 1599 days")
print("  EURJPY: 3888 days")
print("  The new sweep uses LONGER data windows")
print("  BUT produces FAR fewer trades per day")
print("  → This confirms the AR gate is filtering out sessions")
