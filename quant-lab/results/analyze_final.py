import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\optimizer_v3_20260517_202833.json') as f:
    data = json.load(f)

profitable = 0
for name, r in data.items():
    if r.get('total_trades', 0) > 0:
        pf = r['profit_factor']
        status = 'PROFITABLE' if pf > 1.0 else 'LOSING'
        if pf > 1.0:
            profitable += 1
        print(f"{name}: Trades={r['total_trades']} | WR={r['win_rate']}% | PF={pf} | PnL={r['total_pnl']}p | MaxDD={r['max_dd']}p | {status}")

print(f"\nProfitable: {profitable}/10 = {profitable*10}%")
