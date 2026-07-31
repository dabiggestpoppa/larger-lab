import json

# Original sweep results (no costs) - list oftrigger sweep points per pair
orig = json.load(open('reports/trigger_sweep_max_accuracy.json'))
# The floor is the FIRST entry (lowest trigger = native trigger)
# The ceiling is the LAST entry with >=0.5 tr/day

# Cost sweep results
cost_eur = json.load(open('reports/fx_eur_cost_sweep.json'))
cost_gbp = json.load(open('reports/fx_gbp_cost_sweep.json'))

print('=== EURUSD comparison ===')
eur_usd = orig.get('EURUSD', [])
for pt in eur_usd:
    print('T1=%.1f: tr=%d tr/d=%.2f wr=%.1f%% pf=%.2f' % (pt['t1_trigger'], pt['trades'], pt['tr_per_day'], pt['wr'], pt['pf']))

print()
print('=== EURUSD cost sweep ===')
e = cost_eur.get('EURUSD', {})
f = e.get('floor', {})
c = e.get('ceiling', {})
print('Floor: tr=%d tr/d=%.2f net_wr=%.1f%% net_pf=%.2f' % (f.get('trades',0), f.get('net_tr_per_day',0), f.get('net_wr',0), f.get('net_pf',0)))
if c:
    print('Ceiling: tr=%d tr/d=%.2f net_wr=%.1f%% net_pf=%.2f' % (c.get('trades',0), c.get('net_tr_per_day',0), c.get('net_wr',0), c.get('net_pf',0)))
else:
    print('Ceiling: None')
