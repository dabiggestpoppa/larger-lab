import sys, os
sys.path.insert(0, 'engines')
sys.path.insert(0, 'configs')
from symmetry_trap_backtest import SymmetryTrapBacktest
from trading_costs import get_costs
from asset_configs import get_config

pair = 'EURUSD'
cfg = get_config(pair)
costs = get_costs(pair)
total_cost = costs['spread_pips'] + costs['commission_pips']
print('Costs: spread=%sp commission=%sp total=%sp' % (costs['spread_pips'], costs['commission_pips'], total_cost))

bt = SymmetryTrapBacktest(
    pip_size=costs['pip_size'], tier_config=cfg['tiers'], symbol=pair,
    config={'pip_value': costs['pip_size'], 'tiers': cfg['tiers'], 'name': pair},
    spread_pips=costs['spread_pips'], commission_pips=costs['commission_pips']
)
r = bt.run_from_csv(os.path.join('data', pair + '_M5.csv'))

gross_wins = sum(1 for t in r.trades if t.pnl_pips > 0)
gross_losses = sum(1 for t in r.trades if t.pnl_pips < 0)
net_wins = sum(1 for t in r.trades if t.net_pnl_pips > 0)
net_losses = sum(1 for t in r.trades if t.net_pnl_pips < 0)
flipped_to_loss = sum(1 for t in r.trades if t.pnl_pips > 0 and t.net_pnl_pips <= 0)
stayed_win = sum(1 for t in r.trades if t.pnl_pips > 0 and t.net_pnl_pips > 0)
breakeven_zone = sum(1 for t in r.trades if 0 < t.pnl_pips <= total_cost)

print('Total trades: %d' % r.total_trades)
print('Gross: %dW / %dL = %.1f%% WR' % (gross_wins, gross_losses, gross_wins/r.total_trades*100))
print('Net:   %dW / %dL = %.1f%% WR' % (net_wins, net_losses, net_wins/r.total_trades*100))
print('WR drop: %.1f%%' % (gross_wins/r.total_trades*100 - net_wins/r.total_trades*100))
print()
print('Trades flipped WIN->LOSS by cost: %d' % flipped_to_loss)
print('Trades staying wins after cost: %d' % stayed_win)
print('Trades in breakeven zone: %d' % breakeven_zone)
print()
print('Avg gross win: %.2fp' % r.avg_win_pips)
print('Avg gross loss: %.2fp' % r.avg_loss_pips)
print('Avg net win: %.2fp' % r.net_avg_win_pips)
print('Avg net loss: %.2fp' % r.net_avg_loss_pips)
print('Gross PnL: %.1fp' % r.total_pnl_pips)
print('Net PnL: %.1fp' % r.net_pnl_pips)
print('Total cost: %.1fp' % (r.total_spread_cost + r.total_commission_cost))
