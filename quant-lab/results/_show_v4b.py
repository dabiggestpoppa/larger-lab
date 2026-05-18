import json

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\results\optimizer_v4b_20260517_193302.json') as f:
    data = json.load(f)

for name, r in data.items():
    if r.get('total_trades', 0) > 0:
        trades = r['total_trades']
        wr = r['win_rate']
        pf = r['profit_factor']
        mdd = r['max_dd']
        pnl = r['total_pnl']
        print(f'{name}:')
        print(f'  Trades: {trades} | WR: {wr}% | PF: {pf} | MaxDD: {mdd}p | PnL: {pnl}p')
        exits = r.get('by_exit', {})
        print(f'  Exits: {exits}')
        print()
