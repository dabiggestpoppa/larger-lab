"""Sweep ar_max to find the value that gives ~5593 trades."""
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
pip_value = 0.0001
bars, _ = load_m5_csv(csv_path, pip_size=pip_value)

print('Sweeping ar_max with t1=12 (target: 5593 trades):')
print('%-15s %-10s %-10s %-10s %-10s' % ('ar_max', 'Trades', 'WR%', 'PF', 'Delta%'))
print('-' * 55)

for ar_max in [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 999]:
    cfg = deepcopy(ASSET_CONFIGS[pair])
    cfg['tiers'] = {
        'T1': {'ar_max': float(ar_max), 'au': 10.0, 'trigger': 12.0},
        'T2': {'ar_max': float(ar_max), 'au': 12.0, 'trigger': 15.0},
        'T3': {'ar_max': float(ar_max), 'au': 15.0, 'trigger': 19.0},
    }
    bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg)
    r = bt.run(bars)
    delta_pct = (r.total_trades - 5593) / 5593.0 * 100
    print('%-15s %-10d %-10.1f %-10.2f %+.1f%%' % (ar_max, r.total_trades, r.win_rate, r.profit_factor, delta_pct))
