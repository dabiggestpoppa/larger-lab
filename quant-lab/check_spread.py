import sys
sys.path.insert(0, 'configs')
from trading_costs import get_costs, TRADING_COSTS

for sym in sorted(TRADING_COSTS.keys()):
    c = TRADING_COSTS[sym]
    print('%s: spread=%sp comm=%sp total=%sp' % (sym, c['spread_pips'], c['commission_pips'], c['spread_pips']+c['commission_pips']))
