import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\optimizer_v3_20260517_193905.json') as f:
    data = json.load(f)

for name, r in data.items():
    if r.get('total_trades', 0) > 0:
        print(f"{name}:")
        print(f"  Trades: {r['total_trades']} | WR: {r['win_rate']}% | PF: {r['profit_factor']} | MaxDD: {r['max_dd']}p")
        print(f"  Exits: {r.get('by_exit', {})}")
        print()
