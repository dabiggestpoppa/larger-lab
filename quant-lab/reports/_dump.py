import json
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\cost_analysis_native_nogate.json') as f:
    data = json.load(f)

targets = ['XAUUSD','XAGUSD','US500','BTCUSD','ETHUSD','DE30','FR40','HK50']
for k in data:
    s = data[k]['symbol']
    if s in targets:
        c = data[k]['costs']
        a = data[k]['adjusted']
        r = data[k]['raw']
        print(f"{s}: spread={c['spread_pips_per_trade']}p | comm={c['commission_pips_per_trade']}p | total={c['total_cost_pips_per_trade']}p | pipval={c['pip_value_per_lot']}")
        print(f"  Raw: {r['wr']}% WR {r['pf']} PF | Adj: {a['wr']}% WR {a['pf']} PF")
        print()
