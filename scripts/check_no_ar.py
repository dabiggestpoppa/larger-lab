"""Check: does ar_max=999 + t1=12 match the 5593 baseline?"""
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

# ar_max=999 + t1=12
cfg = deepcopy(ASSET_CONFIGS[pair])
cfg['tiers'] = {
    'T1': {'ar_max': 999.0, 'au': 10.0, 'trigger': 12.0},
    'T2': {'ar_max': 999.0, 'au': 12.0, 'trigger': 15.0},
    'T3': {'ar_max': 999.0, 'au': 15.0, 'trigger': 19.0},
}
bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg)
r = bt.run(bars)

print('ar_max=999 (no AR gate), t1=12:')
print('  Trades: %d (baseline: 5593, delta: %+.1f%%)' % (r.total_trades, (r.total_trades - 5593)/5593.0*100))
print('  WR: %.1f%% (baseline: 82.9%%)' % r.win_rate)
print('  PF: %.2f (baseline: 12.5)' % r.profit_factor)

wins = [t for t in r.trades if t.pnl_pips > 0]
losses = [t for t in r.trades if t.pnl_pips <= 0]
avg_w = sum(t.pnl_pips for t in wins) / len(wins) if wins else 0
avg_l = sum(t.pnl_pips for t in losses) / len(losses) if losses else 0
total_pnl = sum(t.pnl_pips for t in r.trades)
print('  PnL: %.1f (baseline: 33421)' % total_pnl)
print('  avg_w: %.2f (baseline: 7.84)' % avg_w)
print('  avg_l: %.2f (baseline: -3.11)' % avg_l)

print()
print('CONCLUSION:')
if abs(r.total_trades - 5593) / 5593.0 < 0.05:
    print('  PASS: Within 5%% of baseline trade count')
    print('  The max accuracy sweep used ar_max=999 (no AR gate)')
elif abs(r.total_trades - 5593) / 5593.0 < 0.15:
    print('  WARN: Within 15%% of baseline')
else:
    print('  FAIL: >15%% deviation')
