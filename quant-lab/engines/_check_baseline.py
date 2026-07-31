import json
from pathlib import Path

results_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\st_multi_asset_results.json")
with open(results_path) as f:
    data = json.load(f)

targets = ['EURGBP','EURCHF','EURCAD','EURNZD','EURAUD','EURJPY','EURUSD']
print(f"{'Asset':10s} | {'Trades':>6s} | {'Days':>5s} | {'Tr/Day':>6s} | {'WR%':>6s} | {'PF':>6s}")
print("-" * 60)
for r in data['results']:
    if r['asset_key'] in targets:
        days = r.get('data_days', 0)
        tr = r['total_trades']
        tpd = tr/days if days > 0 else 0
        print(f"{r['asset_key']:10s} | {tr:6d} | {days:5d} | {tpd:6.2f} | {r['win_rate']:5.1f}% | {r['profit_factor']:6.2f}")
