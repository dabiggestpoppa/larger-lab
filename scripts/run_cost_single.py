"""Quick test: which pair hangs?"""
import sys, os, time

def flush_print(*args, **kwargs):
    print(*args, **kwargs, flush=True)

sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

import symmetry_trap_backtest as stb
from asset_configs import ASSET_CONFIGS

data_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data'

def find_csv(pair):
    for suffix in ['_M5.csv', '_PRO_M5.csv']:
        path = os.path.join(data_dir, pair + suffix)
        if os.path.exists(path):
            return path
    return None

from copy import deepcopy
import symmetry_trap as st
import importlib
importlib.reload(st)
importlib.reload(stb)

forex_pairs = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'USDCAD',
    'EURGBP', 'EURJPY', 'EURCHF', 'EURCAD', 'EURNZD', 'EURAUD',
    'GBPJPY', 'GBPCHF', 'GBPCAD', 'GBPAUD', 'GBPNZD',
    'AUDJPY', 'AUDCHF', 'AUDCAD', 'AUDNZD',
    'NZDJPY', 'NZDCHF', 'NZDCAD',
    'CADJPY', 'CADCHF', 'CHFJPY',
]

for pair in forex_pairs:
    csv_path = find_csv(pair)
    if not csv_path:
        continue
    
    pip_value = ASSET_CONFIGS.get(pair, {}).get('pip_value', 0.0001)
    
    # Test load only
    t0 = time.time()
    bars, _ = stb.load_m5_csv(csv_path, pip_size=pip_value)
    load_t = time.time() - t0
    
    # Test backtest
    cfg = deepcopy(ASSET_CONFIGS.get(pair, {'pip_value': 0.0001}))
    cfg['tiers'] = {
        'T1': {'ar_max': 999.0, 'au': 10.0, 'trigger': 12.0},
        'T2': {'ar_max': 999.0, 'au': 12.0, 'trigger': 15.0},
        'T3': {'ar_max': 999.0, 'au': 15.0, 'trigger': 19.0},
    }
    
    t1 = time.time()
    bt = stb.SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg)
    result = bt.run(bars)
    run_t = time.time() - t1
    
    flush_print('%-10s | load=%.1fs | run=%.1fs | %d bars -> %d trades' % (pair, load_t, run_t, len(bars), result.total_trades))
