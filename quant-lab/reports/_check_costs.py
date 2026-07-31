import json
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\cost_analysis_native_nogate.json') as f:
    data = json.load(f)

targets = ['XAUUSD','XAGUSD','US500','DE30','FR40','HK50','BTCUSD','ETHUSD']
for sym in targets:
    for k in data:
        s = data[k]['symbol'].replace('.PRO','').replace('.','')
        if s == sym.replace('.',''):
            c = data[k]['costs']
            a = data[k]['adjusted']
            r = data[k]['raw']
            d = data[k]['delta']
            print(f"{sym}: spread={c['spread_pips_per_trade']}p comm={c['commission_pips_per_trade']}p total={c['total_cost_pips_per_trade']}p | pip_value={c['pip_value_per_lot']} lot={c['lot_size']}")
            print(f"  Raw: {r['wr']}% WR, {r['pf']} PF | Adj: {a['wr']}% WR, {a['pf']} PF | Delta: {d['wr_change']}% WR, {d['pf_change']} PF")
            print()
            break
