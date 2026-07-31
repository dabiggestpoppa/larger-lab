import json

# Check original floor tr/day
orig = json.load(open('reports/trigger_sweep_max_accuracy.json'))
# Check cost sweep results
cost = json.load(open('reports/fx_eur_cost_sweep.json'))

print('=== ORIGINAL FLOOR (no costs) vs COST FLOOR ===')
for pair in sorted(cost.keys()):
    orig_floor = orig.get(pair, {}).get('floor', {})
    cost_floor = cost[pair].get('floor', {})
    orig_td = orig_floor.get('tr_per_day', 0)
    cost_td = cost_floor.get('net_tr_per_day', 0)
    orig_wr = orig_floor.get('wr', 0)
    cost_wr = cost_floor.get('net_wr', 0)
    print('%s: orig %.1f tr/d %.1f%% WR | cost %.2f tr/d %.1f%% WR' % (pair, orig_td, orig_wr, cost_td, cost_wr))
