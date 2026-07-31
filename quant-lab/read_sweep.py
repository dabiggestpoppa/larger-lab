import json, os

for f in ['reports/trigger_sweep_metals_indices.json', 'reports/trigger_sweep_crypto.json']:
    if not os.path.exists(f):
        print(f'MISSING: {f}')
        continue
    data = json.load(open(f))
    print(f'\n=== {f} ===')
    for pair, points in data.items():
        if isinstance(points, list) and len(points) > 0:
            floor = points[0]
            print(f'  {pair}: n={len(points)} Floor trig={floor.get("t1_trigger",0):.1f} wr={floor.get("wr",0):.1f}%')
        elif isinstance(points, dict):
            print(f'  {pair}: keys={list(points.keys())[:5]}')
