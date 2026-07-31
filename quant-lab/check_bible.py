import json
# Check the original sweep floor configs
orig = json.load(open('reports/trigger_sweep_max_accuracy.json'))
eur = orig['EURUSD']
print('EURUSD sweep points:')
for p in eur:
    print('  T1=%.1f: tr=%d wr=%.1f%% pf=%.2f tr/d=%.2f' % (p['t1_trigger'], p['trades'], p['wr'], p['pf'], p['tr_per_day']))

# The floor is the first point (lowest trigger = native)
# The original floor at T1=12 had 5593 trades
# But current asset_configs T1=12 ar_max=20 gives 3186 trades
# This means the original sweep used DIFFERENT tier configs
print()
print('Current asset_configs EURUSD T1: trigger=12, ar_max=20, au=10')
print('Original floor at T1=12 had 5593 trades')
print('Current engine at T1=12 has 3186 trades')
print('Difference: original had wider AR or different AU values')
