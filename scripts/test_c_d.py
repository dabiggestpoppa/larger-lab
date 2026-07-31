"""Reproduce Test C, D, and C+D from the transcript exactly."""
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

# ── BASELINE (original engine, original config) ──
cfg_base = deepcopy(ASSET_CONFIGS[pair])
cfg_base['tiers'] = {
    'T1': {'ar_max': 20.0, 'au': 10.0, 'trigger': 12.0},
    'T2': {'ar_max': 30.0, 'au': 12.0, 'trigger': 15.0},
    'T3': {'ar_max': 45.0, 'au': 15.0, 'trigger': 19.0},
}
bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg_base)
r = bt.run(bars)
print('BASELINE (ar_max=20/30/45, t1=12): trades=%d, wr=%.1f%%, pf=%.2f' % (r.total_trades, r.win_rate, r.profit_factor))

# ── TEST C: No AR gate (ar_max=999) ──
cfg_c = deepcopy(ASSET_CONFIGS[pair])
cfg_c['tiers'] = {
    'T1': {'ar_max': 999.0, 'au': 10.0, 'trigger': 12.0},
    'T2': {'ar_max': 999.0, 'au': 12.0, 'trigger': 15.0},
    'T3': {'ar_max': 999.0, 'au': 15.0, 'trigger': 19.0},
}
bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg_c)
r = bt.run(bars)
print('TEST C (no AR gate, t1=12):      trades=%d, wr=%.1f%%, pf=%.2f  (target: 4209)' % (r.total_trades, r.win_rate, r.profit_factor))

# ── TEST D: Low trigger + 4PM (keep AR gate) ──
cfg_d = deepcopy(ASSET_CONFIGS[pair])
cfg_d['tiers'] = {
    'T1': {'ar_max': 20.0, 'au': 10.0, 'trigger': 8.0},
    'T2': {'ar_max': 30.0, 'au': 12.0, 'trigger': 8.0},
    'T3': {'ar_max': 45.0, 'au': 15.0, 'trigger': 8.0},
}
bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg_d)
r = bt.run(bars)
print('TEST D (low trig=8, AR gate on): trades=%d, wr=%.1f%%, pf=%.2f  (target: 4064)' % (r.total_trades, r.win_rate, r.profit_factor))

# ── C+D: No AR gate + Low trigger ──
cfg_cd = deepcopy(ASSET_CONFIGS[pair])
cfg_cd['tiers'] = {
    'T1': {'ar_max': 999.0, 'au': 10.0, 'trigger': 8.0},
    'T2': {'ar_max': 999.0, 'au': 12.0, 'trigger': 8.0},
    'T3': {'ar_max': 999.0, 'au': 15.0, 'trigger': 8.0},
}
bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg_cd)
r = bt.run(bars)
print('C+D (no AR gate, trig=8):        trades=%d, wr=%.1f%%, pf=%.2f  (target: 9228)' % (r.total_trades, r.win_rate, r.profit_factor))

# ── BIBLE: ar_max=60, trigger=10 flat ──
cfg_bible = deepcopy(ASSET_CONFIGS[pair])
cfg_bible['tiers'] = {
    'T1': {'ar_max': 60.0, 'au': 10.0, 'trigger': 10.0},
    'T2': {'ar_max': 60.0, 'au': 12.0, 'trigger': 10.0},
    'T3': {'ar_max': 60.0, 'au': 15.0, 'trigger': 10.0},
}
bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg_bible)
r = bt.run(bars)
print('BIBLE (ar_max=60, trig=10):      trades=%d, wr=%.1f%%, pf=%.2f' % (r.total_trades, r.win_rate, r.profit_factor))

# ── MAX ACCURACY BASELINE: ar_max=60, t1=12 ──
cfg_ma = deepcopy(ASSET_CONFIGS[pair])
cfg_ma['tiers'] = {
    'T1': {'ar_max': 60.0, 'au': 10.0, 'trigger': 12.0},
    'T2': {'ar_max': 60.0, 'au': 12.0, 'trigger': 15.0},
    'T3': {'ar_max': 60.0, 'au': 15.0, 'trigger': 19.0},
}
bt = SymmetryTrapBacktest(pip_size=pip_value, symbol=pair, config=cfg_ma)
r = bt.run(bars)
print('MAXACC (ar_max=60, t1=12):       trades=%d, wr=%.1f%%, pf=%.2f  (target: 5593)' % (r.total_trades, r.win_rate, r.profit_factor))
