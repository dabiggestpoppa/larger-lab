import json, os

all_configs = {}
sweep_files = [
    'reports/trigger_sweep_max_accuracy.json',
    'reports/trigger_sweep_forex_full.json',
    'reports/trigger_sweep_usd.json',
    'reports/trigger_sweep_gbp.json',
    'reports/trigger_sweep_chf.json',
    'reports/trigger_sweep_cad.json',
    'reports/trigger_sweep_nzd.json',
    'reports/trigger_sweep_remaining_eur.json',
]

for f in sweep_files:
    if not os.path.exists(f):
        print('MISSING: ' + f)
        continue
    try:
        data = json.load(open(f))
        for pair, points in data.items():
            if isinstance(points, list) and len(points) > 0:
                if pair not in all_configs:
                    all_configs[pair] = []
                all_configs[pair].extend(points)
    except Exception as e:
        print('Error: ' + f + ': ' + str(e))

# Load metals/indices
try:
    mi = json.load(open('reports/trigger_sweep_metals_indices.json'))
    for pair in ['XAUUSD','XAGUSD','US500','DE30','FR40','HK50']:
        if pair in mi:
            v = mi[pair]
            key = pair + '_FLOOR'
            if isinstance(v, dict) and 'floor' in v:
                all_configs[key] = v['floor'] if isinstance(v['floor'], list) else [v['floor']]
except Exception as e:
    print('Metals error: ' + str(e))

# Load crypto
try:
    cr = json.load(open('reports/trigger_sweep_crypto.json'))
    for level in ['floor', 'ceiling']:
        if level in cr:
            for pair, data in cr[level].items():
                key = pair + '_' + level.upper()
                all_configs[key] = data if isinstance(data, list) else [data]
except Exception as e:
    print('Crypto error: ' + str(e))

# Extract floor/ceiling/knee
result = {}
for pair, points in sorted(all_configs.items()):
    if not isinstance(points, list) or len(points) == 0:
        continue
    points_sorted = sorted([p for p in points if isinstance(p, dict)], key=lambda x: x.get('t1_trigger', 0))
    if len(points_sorted) == 0:
        continue
    
    floor = points_sorted[0]
    ceiling = None
    knee = None
    max_pf = 0
    
    for p in points_sorted:
        if p.get('tr_per_day', 0) >= 0.5 and ceiling is None:
            ceiling = p
        if p.get('pf', 0) > max_pf:
            max_pf = p.get('pf', 0)
            knee = p
    
    if ceiling is None:
        ceiling = points_sorted[-1]
    
    def safe(d, k, default=0):
        if not isinstance(d, dict):
            return default
        return d.get(k, default)
    
    result[pair] = {
        'floor': {'trigger': safe(floor,'t1_trigger'), 'wr': safe(floor,'wr'), 'trades': safe(floor,'trades'), 'tr_per_day': safe(floor,'tr_per_day'), 'pf': safe(floor,'pf')},
        'ceiling': {'trigger': safe(ceiling,'t1_trigger'), 'wr': safe(ceiling,'wr'), 'trades': safe(ceiling,'trades'), 'tr_per_day': safe(ceiling,'tr_per_day'), 'pf': safe(ceiling,'pf')},
        'knee': {'trigger': safe(knee,'t1_trigger'), 'wr': safe(knee,'wr'), 'trades': safe(knee,'trades'), 'tr_per_day': safe(knee,'tr_per_day'), 'pf': safe(knee,'pf')},
        'n_sweep_points': len(points_sorted)
    }

print('Total pairs: ' + str(len(result)))
for pair, cfg in result.items():
    f = cfg['floor']
    c = cfg['ceiling']
    k = cfg['knee']
    line = pair + ' n=' + str(cfg['n_sweep_points'])
    line += '  Floor: trig=' + str(f['trigger']) + ' wr=' + str(f['wr']) + '% tr/d=' + str(f['tr_per_day']) + ' pf=' + str(f['pf'])
    line += '  Ceiling: trig=' + str(c['trigger']) + ' wr=' + str(c['wr']) + '%'
    line += '  Knee: trig=' + str(k['trigger']) + ' wr=' + str(k['wr']) + '% pf=' + str(k['pf'])
    print(line)

os.makedirs('data/holy_grail_extracted', exist_ok=True)
with open('data/holy_grail_extracted/sweep_configs_all.json', 'w') as f:
    json.dump(result, f, indent=2)
print('Saved sweep_configs_all.json')
