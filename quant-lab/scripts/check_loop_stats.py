"""Check if loop_stats exist in the JSON results."""
import json, os

baskets_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports/baskets'

for f in sorted(os.listdir(baskets_dir)):
    if not f.endswith('_results.json'):
        continue
    fp = os.path.join(baskets_dir, f)
    with open(fp) as fh:
        data = json.load(fh)
    results = data.get('results', {})
    if isinstance(results, dict):
        for sym, res in sorted(results.items()):
            if isinstance(res, dict):
                ls = res.get('loop_stats', None)
                if ls:
                    print("{}: {}".format(sym, ls))
                # Also check top-level keys for anything loop-related
                for k in res.keys():
                    if 'loop' in k.lower():
                        print("  {} -> {}".format(k, res[k]))
