"""Test without reload."""
import sys, os, time

sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from symmetry_trap_backtest import load_m5_csv
from asset_configs import ASSET_CONFIGS

test_pairs = ['EURUSD', 'GBPUSD', 'USDCHF', 'AUDUSD', 'EURGBP', 'GBPJPY']
for pair in test_pairs:
    csv_path = os.path.join(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data', pair + '_M5.csv')
    if not os.path.exists(csv_path):
        continue
    pip = ASSET_CONFIGS.get(pair, {}).get('pip_value', 0.0001)
    t0 = time.time()
    bars, sym = load_m5_csv(csv_path, pip_size=pip)
    print('%s: %d bars in %.2fs' % (pair, len(bars), time.time() - t0))
