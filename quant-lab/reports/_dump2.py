import json
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\cost_analysis_all.json') as f:
    d = json.load(f)
for v in d.values():
    s = v['symbol']
    r = v['raw']
    a = v['adjusted']
    c = v['costs']
    print(f"{s}: raw={r['wr']}% pf={r['pf']} | adj={a['wr']}% pf={a['pf']} | spread={c['spread_pips_per_trade']}p comm={c['commission_pips_per_trade']}p pipval={c['pip_value_per_lot']}")
