"""Test load_m5_csv for each forex pair — find which one hangs."""
import sys, os, time
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from symmetry_trap_backtest import load_m5_csv
from asset_configs import ASSET_CONFIGS

data_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data'

forex_pairs = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'USDCAD',
    'EURGBP', 'EURJPY', 'EURCHF', 'EURCAD', 'EURNZD', 'EURAUD',
    'GBPJPY', 'GBPCHF', 'GBPCAD', 'GBPAUD', 'GBPNZD',
    'AUDJPY', 'AUDCHF', 'AUDCAD', 'AUDNZD',
    'NZDJPY', 'NZDCHF', 'NZDCAD',
    'CADJPY', 'CADCHF', 'CHFJPY',
]

def find_csv(pair):
    for suffix in ['_M5.csv', '_PRO_M5.csv']:
        path = os.path.join(data_dir, pair + suffix)
        if os.path.exists(path):
            return path
    return None

for pair in forex_pairs:
    csv_path = find_csv(pair)
    if not csv_path:
        print('%-10s | NO CSV' % pair)
        continue
    
    pip = ASSET_CONFIGS.get(pair, {}).get('pip_value', 0.0001)
    t0 = time.time()
    try:
        bars, sym = load_m5_csv(csv_path, pip_size=pip)
        elapsed = time.time() - t0
        print('%-10s | %6d bars | %.2fs' % (pair, len(bars), elapsed))
    except Exception as e:
        elapsed = time.time() - t0
        print('%-10s | ERROR: %s (%.1fs)' % (pair, str(e)[:50], elapsed))
