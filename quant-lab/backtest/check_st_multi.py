import json
d = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\st_multi_asset_results.json'))
for r in d['results']:
    print(f"{r['asset_key']:10s}: trades={r['total_trades']:4d}, wr={r['win_rate']:5.1f}%, pnl={r['pnl_pips']:+8.1f}p, pf={r['profit_factor']:.2f}")
    print(f"           config: k={r['config_used'].get('k_factor','?')}, tiers={list(r['config_used'].get('tiers',{}).keys())}")
