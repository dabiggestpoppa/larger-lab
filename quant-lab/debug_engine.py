import sys, os
sys.path.insert(0, 'engines')
sys.path.insert(0, 'configs')
from symmetry_trap_backtest import SymmetryTrapBacktest
from trading_costs import get_costs
from asset_configs import get_config

# Run EURUSD with costs=0 and compare to original
pair = 'EURUSD'
cfg = get_config(pair)
costs = get_costs(pair)

# Run with ZERO costs
bt0 = SymmetryTrapBacktest(
    pip_size=costs['pip_size'], tier_config=cfg['tiers'], symbol=pair,
    config={'pip_value': costs['pip_size'], 'tiers': cfg['tiers'], 'name': pair},
    spread_pips=0, commission_pips=0
)
r0 = bt0.run_from_csv(os.path.join('data', pair + '_M5.csv'))
print('ZERO COSTS: tr=%d wr=%.1f%% pf=%.2f tr/d=%.2f' % (r0.total_trades, r0.win_rate, r0.profit_factor, r0.total_trades/1341))

# Run with corrected costs (spread=0.1p, comm=0.07p)
bt1 = SymmetryTrapBacktest(
    pip_size=costs['pip_size'], tier_config=cfg['tiers'], symbol=pair,
    config={'pip_value': costs['pip_size'], 'tiers': cfg['tiers'], 'name': pair},
    spread_pips=0.1, commission_pips=0.07
)
r1 = bt1.run_from_csv(os.path.join('data', pair + '_M5.csv'))
print('WITH COSTS: tr=%d wr=%.1f%% pf=%.2f tr/d=%.2f' % (r1.total_trades, r1.win_rate, r1.profit_factor, r1.total_trades/1341))
print('NET: tr=%d net_wr=%.1f%% net_pf=%.2f' % (r1.total_trades, r1.net_win_rate, r1.net_profit_factor))
