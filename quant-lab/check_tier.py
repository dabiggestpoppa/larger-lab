import sys
sys.path.insert(0, 'engines')
from symmetry_trap import classify_tier_by_ar, classify_tier_by_impulse, DEFAULT_TIER_CONFIG

# Test with EURUSD tiers
tiers = {'T1': {'ar_max': 20.0, 'au': 10.0, 'trigger': 12.0},
         'T2': {'ar_max': 30.0, 'au': 12.0, 'trigger': 15.0},
         'T3': {'ar_max': 45.0, 'au': 15.0, 'trigger': 19.0}}

print('DEFAULT_TIER_CONFIG:', DEFAULT_TIER_CONFIG)
print()

# Test AR classification with old tiers
for ar in [10, 15, 20, 25, 30, 35, 40, 45, 50, 60]:
    t = classify_tier_by_ar(ar, tiers)
    print('AR=%.1f pip: %s' % (ar, t[0]))

print()

# Test impulse classification
for imp in [10, 12, 15, 18, 20, 25, 30, 35]:
    t = classify_tier_by_impulse(imp, tiers)
    print('Impulse=%.1f pip: tier=%s au=%.1f trigger=%.1f' % (imp, t[0], t[1], t[2]))
