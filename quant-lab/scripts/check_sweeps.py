import json, os

reports = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

# Check trigger_sweep files for each low-cost pair
pairs = ['EURJPY', 'EURNZD', 'GBPNZD', 'EURAUD', 'GBPAUD', 'GBPCAD']

# Map pair to sweep file
sweep_files = {
    'EURJPY': 'trigger_sweep_max_accuracy.json',
    'EURNZD': 'trigger_sweep_nzd.json',
    'GBPNZD': 'trigger_sweep_gbp.json',
    'EURAUD': 'trigger_sweep_aud.json',
    'GBPAUD': 'trigger_sweep_gbp.json',
    'GBPCAD': 'trigger_sweep_cad.json',
}

for pair in pairs:
    fname = sweep_files.get(pair)
    if not fname:
        print(f'{pair}: NO SWEEP FILE MAPPED')
        continue
    fpath = os.path.join(reports, fname)
    if not os.path.exists(fpath):
        print(f'{pair}: FILE NOT FOUND ({fname})')
        continue
    with open(fpath) as f:
        data = json.load(f)
    # Find this pair's data
    if isinstance(data, dict):
        pdata = data.get(pair, data.get(pair + '.PRO', {}))
        if not pdata:
            # Try to find in list
            print(f'{pair}: keys={list(data.keys())[:5]}')
            continue
        print(f'{pair}: {json.dumps(pdata, indent=2)[:500]}')
    else:
        print(f'{pair}: unexpected format')
