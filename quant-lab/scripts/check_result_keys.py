"""Check all keys in result JSON."""
import json

fp = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports/baskets/eur_basket_results.json'
with open(fp) as f:
    data = json.load(f)

results = data.get('results', {})
for sym in sorted(results.keys()):
    res = results[sym]
    if isinstance(res, dict):
        print("{}: {}".format(sym, sorted(res.keys())))
