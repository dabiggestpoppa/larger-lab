import hashlib
import json
from datetime import datetime

files = [
    'quant-lab/engines/mt5_data_feed.py',
    'quant-lab/engines/symmetry_trap_live.py',
    'quant-lab/mt5/execution_layer.py',
    'quant-lab/mt5/symmetry_trap_executor_multi.py',
    'quant-lab/engines/symmetry_trap_backtest.py',
]

baseline = {
    'timestamp': datetime.utcnow().isoformat() + 'Z',
    'commit': '88c8f4af4',
    'files': {}
}

for f in files:
    with open(f, 'rb') as fp:
        content = fp.read()
        baseline['files'][f] = {
            'sha256': hashlib.sha256(content).hexdigest(),
            'size': len(content)
        }

with open('artifacts/symmetry_trap/parity_baseline.json', 'w') as fp:
    json.dump(baseline, fp, indent=2)

print('parity_baseline.json created')
for f, info in baseline['files'].items():
    print(f'  {f}: {info["sha256"][:16]}... ({info["size"]} bytes)')