import sys, os
sys.path.insert(0, 'engines')
from symmetry_trap_backtest import SymmetryTrapBacktest

# Exact same config as original sweep script
cfg = {
    'csv': 'EURUSD_M5.csv', 'pip_value': 0.0001,
    'tiers': {'T1': {'ar_max': 20.0, 'au': 10.0, 'trigger': 12.0},
              'T2': {'ar_max': 30.0, 'au': 12.0, 'trigger': 15.0},
              'T3': {'ar_max': 45.0, 'au': 15.0, 'trigger': 19.0}},
}
bt = SymmetryTrapBacktest(
    pip_size=0.0001, tier_config=cfg['tiers'], symbol='EURUSD',
    config={'pip_value': 0.0001, 'tiers': cfg['tiers'], 'name': 'EURUSD'}
)
r = bt.run_from_csv(os.path.join('data', 'EURUSD_M5.csv'))
print('EURUSD: tr=%d wr=%.1f%% pf=%.2f tr/d=%.2f' % (r.total_trades, r.win_rate, r.profit_factor, r.total_trades/r.data_days))
