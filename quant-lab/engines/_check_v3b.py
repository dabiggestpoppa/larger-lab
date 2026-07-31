import json
from pathlib import Path

reports_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports")
targets = ['EURGBP','EURCHF','EURCAD','EURNZD','EURAUD','EURJPY','EURUSD']

fpath = reports_dir / "full_backtest_campaign_v3.json"
with open(fpath) as f:
    data = json.load(f)

print(f"timestamp: {data.get('timestamp','?')}")
print(f"total_assets: {data.get('total_assets','?')}")
results = data.get('results', {})
print(f"results type: {type(results)}, count: {len(results) if isinstance(results, (dict,list)) else '?'}")

if isinstance(results, dict):
    for k, v in list(results.items())[:3]:
        print(f"\nKey: {k}")
        if isinstance(v, dict):
            for kk, vv in list(v.items())[:15]:
                print(f"  {kk}: {vv}")
elif isinstance(results, list):
    for r in results[:3]:
        if isinstance(r, dict):
            print(f"\nKeys: {list(r.keys())[:15]}")
            for k in ['asset_key','symbol','total_trades','data_days','win_rate','profit_factor']:
                if k in r:
                    print(f"  {k}: {r[k]}")
