import json, os
from datetime import datetime

base_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

files = [
    'trigger_sweep_aud.json', 'trigger_sweep_cad.json', 'trigger_sweep_chf.json',
    'trigger_sweep_gbp.json', 'trigger_sweep_nzd.json', 'trigger_sweep_usd.json',
    'trigger_sweep_remaining_eur.json', 'trigger_sweep_crypto.json',
    'trigger_sweep_metals_indices.json', 'trigger_sweep_max_accuracy.json',
    'trigger_sweep_forex_full.json'
]

for f in files:
    path = os.path.join(base_dir, f)
    if os.path.exists(path):
        data = json.load(open(path))
        mtime = os.path.getmtime(path)
        mod = datetime.fromtimestamp(mtime)
        pairs = list(data.keys())
        total_entries = sum(len(v) if isinstance(v, list) else 1 for v in data.values())
        print(f'{f:40s} | pairs={len(pairs):2d} | entries={total_entries:4d} | modified={mod}')
    else:
        print(f'{f:40s} | NOT FOUND')
