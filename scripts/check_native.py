"""Check what per-pair configs are available in asset_configs.py."""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
from asset_configs import ASSET_CONFIGS

print('Per-pair native configs from asset_configs.py:')
print('%-10s | %-30s | %-30s' % ('Pair', 'T1 (ar_max, au, trigger)', 'T2 (ar_max, au, trigger)'))
print('-' * 80)
for pair in sorted(ASSET_CONFIGS.keys()):
    cfg = ASSET_CONFIGS[pair]
    tiers = cfg.get('tiers', {})
    t1 = tiers.get('T1', {})
    t2 = tiers.get('T2', {})
    t3 = tiers.get('T3', {})
    print('%-10s | au=%-5s trig=%-5s ar=%-5s | au=%-5s trig=%-5s ar=%-5s' % (
        pair,
        t1.get('au', '?'), t1.get('trigger', '?'), t1.get('ar_max', '?'),
        t2.get('au', '?'), t2.get('trigger', '?'), t2.get('ar_max', '?')))
