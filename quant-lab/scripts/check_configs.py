import sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")
from asset_configs import ASSET_CONFIGS

new_pairs = ['EURGBP', 'EURJPY', 'EURAUD', 'EURNZD', 'EURCHF', 'EURCAD', 'USDCAD',
             'AUDJPY', 'AUDNZD', 'AUDCHF', 'AUDCAD', 'NZDJPY', 'NZDCHF', 'NZDCAD',
             'CADJPY', 'CADCHF', 'GBPCAD']

print(f"Total configs: {len(ASSET_CONFIGS)}")
print(f"Available: {sorted(ASSET_CONFIGS.keys())}")
print()
for p in new_pairs:
    if p in ASSET_CONFIGS:
        tiers = ASSET_CONFIGS[p]['tiers']
        t1 = tiers.get('T1', {})
        print(f"{p}: FOUND - T1 ar_max={t1.get('ar_max')}, au={t1.get('au')}, trig={t1.get('trigger')}")
    else:
        print(f"{p}: MISSING")
