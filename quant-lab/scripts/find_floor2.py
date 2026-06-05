import json, os

reports = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

# Read all sweep files and find FLOOR entries for our pairs
pairs_map = {
    'EURJPY': ['trigger_sweep_max_accuracy.json', 'trigger_sweep_remaining_eur.json'],
    'EURNZD': ['trigger_sweep_nzd.json', 'trigger_sweep_max_accuracy.json'],
    'GBPNZD': ['trigger_sweep_gbp.json', 'trigger_sweep_max_accuracy.json'],
    'EURAUD': ['trigger_sweep_aud.json', 'trigger_sweep_max_accuracy.json'],
    'GBPAUD': ['trigger_sweep_gbp.json', 'trigger_sweep_max_accuracy.json'],
    'GBPCAD': ['trigger_sweep_cad.json', 'trigger_sweep_max_accuracy.json'],
}

target_pairs = ['EURJPY', 'EURNZD', 'GBPNZD', 'EURAUD', 'GBPAUD', 'GBPCAD']

found = {}
for pair, files in pairs_map.items():
    for fname in files:
        fpath = os.path.join(reports, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath) as f:
            data = json.load(f)
        if isinstance(data, dict):
            val = data.get(pair, data.get(pair + '.PRO', None))
            if val is None:
                # Try nested
                for k, v in data.items():
                    if isinstance(v, dict) and pair in v:
                        val = v[pair]
                        break
            if val and isinstance(val, list):
                # Find entry with most trades (FLOOR)
                best = max(val, key=lambda x: x.get('trades', 0) if isinstance(x, dict) else 0)
                if isinstance(best, dict):
                    found[pair] = {
                        'file': fname,
                        'trades': best.get('trades', 0),
                        'wr': best.get('wr', 0),
                        'pf': best.get('pf', 0),
                        'trigger': best.get('t1_trigger', 0),
                        'tr_per_day': best.get('tr_per_day', 0),
                        'pnl': best.get('pnl', 0),
                        'max_dd': best.get('max_dd', 0),
                    }
                    break

for p in target_pairs:
    if p in found:
        d = found[p]
        print(f'{p}: trades={d["trades"]}, wr={d["wr"]:.1f}%, pf={d["pf"]:.1f}, trigger={d["trigger"]}, tr/day={d["tr_per_day"]:.3f}, pnl={d["pnl"]:.0f}, max_dd={d["max_dd"]:.0f} ({d["file"]})')
    else:
        print(f'{p}: NOT FOUND')
