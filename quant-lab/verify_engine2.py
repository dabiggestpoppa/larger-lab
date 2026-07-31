import sys, os
sys.path.insert(0, 'engines')
sys.path.insert(0, 'configs')
from symmetry_trap_backtest import SymmetryTrapBacktest
from asset_configs import get_config

pair = 'EURUSD'
cfg = get_config(pair)
bt = SymmetryTrapBacktest(
    pip_size=0.0001, tier_config=cfg['tiers'], symbol=pair,
    config={'pip_value': 0.0001, 'tiers': cfg['tiers'], 'name': pair}
)
r = bt.run_from_csv(os.path.join('data', pair + '_M5.csv'))
print('EURUSD: tr=%d wr=%.1f%% pf=%.2f tr/d=%.2f dd=%.1fp' % (r.total_trades, r.win_rate, r.profit_factor, r.total_trades/r.data_days, r.max_drawdown_pips))
print('Expected: tr=5593 wr=82.9%% pf=12.48 tr/d=4.17')
