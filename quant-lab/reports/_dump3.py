import json
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\cost_analysis_native_nogate.json') as f:
    d = json.load(f)
for v in d.values():
    s = v['symbol']
    c = v['costs']
    if 'JPY' in s or s in ['XAUUSD','BTCUSD','ETHUSD','US500','DE30','FR40','HK50']:
        print(f"{s}: spread={c['spread_pips_per_trade']}p comm={c['commission_pips_per_trade']}p pipval={c['pip_value_per_lot']}")
