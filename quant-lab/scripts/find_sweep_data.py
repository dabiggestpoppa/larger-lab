import json, os

reports = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

# Search all sweep files for our 6 pairs
target_pairs = ['EURJPY', 'EURNZD', 'GBPNZD', 'EURAUD', 'GBPAUD', 'GBPCAD']

sweep_files = [
    'trigger_sweep_max_accuracy.json',
    'trigger_sweep_aud.json',
    'trigger_sweep_cad.json',
    'trigger_sweep_chf.json',
    'trigger_sweep_gbp.json',
    'trigger_sweep_nzd.json',
    'trigger_sweep_usd.json',
    'trigger_sweep_remaining_eur.json',
    'fx_eur_cost_sweep.json',
    'fx_gbp_cost_sweep.json',
    'fx_chfjpy_cost_sweep.json',
]

found = {}
for fname in sweep_files:
    fpath = os.path.join(reports, fname)
    if not os.path.exists(fpath):
        continue
    with open(fpath) as f:
        try:
            data = json.load(f)
        except:
            continue
    if isinstance(data, dict):
        for key in data:
            base = key.replace('.PRO', '').replace('_PRO', '')
            if base in target_pairs and base not in found:
                val = data[key]
                if isinstance(val, list) and len(val) > 0:
                    # Find the FLOOR entry (usually first or has specific trigger)
                    for entry in val:
                        if isinstance(entry, dict) and entry.get('trades', 0) > 0:
                            found[base] = {
                                'file': fname,
                                'trades': entry.get('trades', 0),
                                'wr': entry.get('wr', 0),
                                'pf': entry.get('pf', 0),
                                'trigger': entry.get('t1_trigger', 0),
                                'tr_per_day': entry.get('tr_per_day', 0),
                                'pnl': entry.get('pnl', 0),
                            }
                            break
    elif isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict):
                sym = entry.get('symbol', entry.get('pair', ''))
                base = sym.replace('.PRO', '').replace('_PRO', '')
                if base in target_pairs and base not in found:
                    found[base] = {
                        'file': fname,
                        'trades': entry.get('trades', 0),
                        'wr': entry.get('wr', 0),
                        'pf': entry.get('pf', 0),
                        'trigger': entry.get('t1_trigger', 0),
                        'tr_per_day': entry.get('tr_per_day', 0),
                        'pnl': entry.get('pnl', 0),
                    }

for p in target_pairs:
    if p in found:
        d = found[p]
        print(f'{p}: trades={d["trades"]}, wr={d["wr"]:.1f}%, pf={d["pf"]:.1f}, trigger={d["trigger"]}, tr/day={d["tr_per_day"]:.3f}, pnl={d["pnl"]:.0f} ({d["file"]})')
    else:
        print(f'{p}: NOT FOUND')
