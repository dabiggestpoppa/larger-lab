import json, os

reports = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

# Get full entry data for each pair from max_accuracy sweep
with open(os.path.join(reports, 'trigger_sweep_max_accuracy.json')) as f:
    data = json.load(f)

target_pairs = ['EURJPY', 'EURNZD', 'GBPNZD', 'EURAUD', 'GBPAUD', 'GBPCAD']

for pair in target_pairs:
    val = data.get(pair, [])
    if not val:
        print(f'{pair}: NOT FOUND')
        continue
    # val is a list of entries with different triggers
    # Find the FLOOR entry (lowest trigger with good trades)
    # Sort by trigger ascending
    entries = sorted([e for e in val if isinstance(e, dict)], key=lambda x: x.get('t1_trigger', 999))
    print(f'{pair}: {len(entries)} entries')
    for e in entries[:3]:  # Show first 3 (lowest triggers = FLOOR)
        print(f'  trigger={e.get("t1_trigger",0)}, trades={e.get("trades",0)}, wr={e.get("wr",0):.1f}%, pf={e.get("pf",0):.1f}')
