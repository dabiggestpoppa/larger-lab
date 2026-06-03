import sys, json; sys.path.insert(0, 'configs')
from asset_configs import ASSET_CONFIGS
for sym in ['EURUSD', 'USDCHF', 'NZDUSD']:
    cfg = ASSET_CONFIGS[sym]
    print(f"=== {sym} ===")
    for k, v in cfg.items():
        if k != 'tiers':
            print(f"  {k}: {v}")
    print()
