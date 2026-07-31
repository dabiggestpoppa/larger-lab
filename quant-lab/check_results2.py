import json
orig = json.load(open('reports/trigger_sweep_max_accuracy.json'))
print(type(orig))
if isinstance(orig, dict):
    print(list(orig.keys())[:5])
    k = list(orig.keys())[0]
    print(k, type(orig[k]), orig[k] if not isinstance(orig[k], dict) else list(orig[k].keys()))
elif isinstance(orig, list):
    print('list len:', len(orig))
    print(orig[0] if orig else 'empty')
