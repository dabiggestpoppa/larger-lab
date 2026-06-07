"""Test: what if we remove the 5-loop limit?"""
import sys, time
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

import importlib
import symmetry_trap
import symmetry_trap_backtest
importlib.reload(symmetry_trap)
importlib.reload(symmetry_trap_backtest)

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv
from copy import deepcopy

pair = 'EURUSD'
csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'

# Test various configurations
configs_to_test = [
    ('BIBLE (t1=10, ar_max=60, 4PM, no extras)', {
        'T1': {'ar_max': 60.0, 'au': 10.0, 'trigger': 10.0},
        'T2': {'ar_max': 60.0, 'au': 12.0, 'trigger': 10.0},
        'T3': {'ar_max': 60.0, 'au': 15.0, 'trigger': 10.0},
    }),
    ('MaxAcc (t1=12, ar_max=60, 4PM, no extras)', {
        'T1': {'ar_max': 60.0, 'au': 10.0, 'trigger': 12.0},
        'T2': {'ar_max': 60.0, 'au': 12.0, 'trigger': 15.0},
        'T3': {'ar_max': 60.0, 'au': 15.0, 'trigger': 19.0},
    }),
    ('Original (t1=12, ar_max=20/30/45, 12PM, with extras)', {
        'T1': {'ar_max': 20.0, 'au': 10.0, 'trigger': 12.0},
        'T2': {'ar_max': 30.0, 'au': 12.0, 'trigger': 15.0},
        'T3': {'ar_max': 45.0, 'au': 15.0, 'trigger': 19.0},
    }),
]

pip_value = 0.0001
bars, _ = load_m5_csv(csv_path, pip_size=pip_value)

for name, tiers in configs_to_test:
    cfg = deepcopy(ASSET_CONFIGS[pair])
    cfg['tiers'] = tiers
    bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg)
    result = bt.run(bars)
    print(f'{name}:')
    print(f'  Trades: {result.total_trades}, WR: {result.win_rate:.1f}%, PF: {result.profit_factor:.2f}')
    print()
