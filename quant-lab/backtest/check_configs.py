import sys; sys.path.insert(0, 'configs')
from asset_configs import ASSET_CONFIGS
for sym in ['EURUSD', 'USDCHF', 'NZDUSD']:
    cfg = ASSET_CONFIGS[sym]
    print(f"{sym}: engine={cfg.get('engine')}, k={cfg.get('k_factor')}, sl={cfg.get('sl_method')}")
    for tn in ['T1','T2','T3']:
        if tn in cfg.get('tiers',{}):
            t = cfg['tiers'][tn]
            print(f"  {tn}: ar_max={t.get('ar_max')}, au={t.get('au')}, trigger={t.get('trigger')}")
    print()
