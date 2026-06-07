"""Test: keep trigger at T1 value for all loops (don't update on tier reclass)."""
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

# Test with trigger locked to T1 value
cfg = deepcopy(ASSET_CONFIGS[pair])
cfg['tiers'] = {
    'T1': {'ar_max': 60.0, 'au': 10.0, 'trigger': 12.0},
    'T2': {'ar_max': 60.0, 'au': 12.0, 'trigger': 12.0},  # Same trigger as T1
    'T3': {'ar_max': 60.0, 'au': 15.0, 'trigger': 12.0},  # Same trigger as T1
}
pip_value = 0.0001

bars, _ = load_m5_csv(csv_path, pip_size=pip_value)
bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg)

t0 = time.time()
result = bt.run(bars)
elapsed = time.time() - t0

print('Fixed trigger (all tiers use T1 trigger=12):')
print('  Trades: %d (baseline: 5,593)' % result.total_trades)
print('  WR: %.1f%% (baseline: 82.9%%)' % result.win_rate)
print('  PF: %.2f (baseline: 12.5)' % result.profit_factor)
print('  Time: %.1fs' % elapsed)

delta = result.total_trades - 5593
pct = (delta / 5593.0) * 100
print('  Delta: %+d trades (%+.1f%%)' % (delta, pct))

# Also test with t1=10 flat
cfg2 = deepcopy(ASSET_CONFIGS[pair])
cfg2['tiers'] = {
    'T1': {'ar_max': 60.0, 'au': 10.0, 'trigger': 10.0},
    'T2': {'ar_max': 60.0, 'au': 12.0, 'trigger': 10.0},
    'T3': {'ar_max': 60.0, 'au': 15.0, 'trigger': 10.0},
}
bt2 = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg2)
result2 = bt2.run(bars)

print()
print('BIBLE config (t1=10 flat, all tiers same):')
print('  Trades: %d (floor baseline: 7,134)' % result2.total_trades)
print('  WR: %.1f%% (baseline: 81.1%%)' % result2.win_rate)
print('  PF: %.2f (baseline: 11.3)' % result2.profit_factor)
