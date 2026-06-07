import sys; sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
from asset_configs import ASSET_CONFIGS

for pair in ['EURUSD', 'CHFJPY', 'EURJPY', 'GBPJPY', 'USDJPY']:
    c = ASSET_CONFIGS[pair]
    print(f'{pair}:')
    for t in ['T1','T2','T3']:
        tier = c['tiers'][t]
        print(f'  {t}: ar_max={tier["ar_max"]}, au={tier["au"]}, trigger={tier["trigger"]}')
    print()
