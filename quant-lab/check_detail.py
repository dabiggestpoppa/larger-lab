import json
orig = json.load(open('reports/trigger_sweep_max_accuracy.json'))
eur = orig['EURUSD']
print('Keys in first data point:', list(eur[0].keys()))
print()
# Check if there's trade-level data
for k in eur[0]:
    v = eur[0][k]
    if isinstance(v, list):
        print('List field: %s (len=%d)' % (k, len(v)))
