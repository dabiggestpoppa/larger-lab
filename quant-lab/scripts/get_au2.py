import json, os

reports = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

# Read the full trigger_sweep_max_accuracy.json to get AU values for our pairs
with open(os.path.join(reports, 'trigger_sweep_max_accuracy.json')) as f:
    data = json.load(f)

target_pairs = ['EURJPY', 'EURNZD', 'GBPNZD', 'EURAUD', 'GBPAUD', 'GBPCAD']

for pair in target_pairs:
    val = data.get(pair, [])
    if not val:
        print(f'{pair}: NOT FOUND in max_accuracy')
        continue
    # Find entry with max trades (FLOOR)
    best = max(val, key=lambda x: x.get('trades', 0) if isinstance(x, dict) else 0)
    if isinstance(best, dict):
        print(f'{pair}: trigger={best.get("t1_trigger",0)}, trades={best.get("trades",0)}, wr={best.get("wr",0):.1f}%, pf={best.get("pf",0):.1f}')
        # Print all keys
        print(f'  all keys: {list(best.keys())}')
