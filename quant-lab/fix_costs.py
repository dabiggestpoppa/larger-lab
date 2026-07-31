import sys
sys.path.insert(0, 'configs')
from trading_costs import TRADING_COSTS

# MT5 spread is in points. For 5-digit FX: 1 point = 0.1 pip. For 3-digit JPY: 1 point = 0.1 pip.
# So divide all spread_pips by 10 to convert from points to pips.
# Exception: crypto where pip_size=1.0, spread is already in dollar terms.

for sym, costs in TRADING_COSTS.items():
    if costs['pip_size'] == 1.0:
        # Crypto: spread is in dollars = pips (pip_size=1.0)
        continue
    # FX: convert points to pips (divide by 10)
    old = costs['spread_pips']
    costs['spread_pips'] = round(old / 10.0, 2)

# Print corrected table
for sym in sorted(TRADING_COSTS.keys()):
    c = TRADING_COSTS[sym]
    print('%s: spread=%.2fp comm=%.2fp total=%.2fp pip_size=%s' % (sym, c['spread_pips'], c['commission_pips'], c['spread_pips']+c['commission_pips'], c['pip_size']))

# Write corrected file
import json
with open('configs/trading_costs_corrected.json', 'w') as f:
    json.dump(TRADING_COSTS, f, indent=2)
print()
print('Corrected costs saved.')
