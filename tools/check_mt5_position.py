import MetaTrader5 as mt5
import json

cfg_file = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_config.json"
with open(cfg_file) as f:
    cfg = json.load(f)

mt5.initialize()
auth = mt5.login(login=cfg['login'], password=cfg['password'], server=cfg['server'])
print(f"Auth: {auth}")

acct = mt5.account_info()
print(f"Balance: {acct.balance} | Equity: {acct.equity}")

positions = mt5.positions_get()
if positions:
    for p in positions:
        if p.magic == cfg['magic_number']:
            print(f"DMR Position: {p.symbol} {p.type} @ {p.price_open} SL:{p.sl} TP:{p.tp} PnL:{p.profit} Ticket:{p.ticket}")
else:
    print("No open positions")

# Also check the specific ticket
positions2 = mt5.positions_get(ticket=91311591)
if positions2:
    p = positions2[0]
    print(f"\nTicket 91311591: {p.symbol} {'BUY' if p.type==0 else 'SELL'} @ {p.price_open} SL:{p.sl} TP:{p.tp} PnL:{p.profit}")
else:
    print("\nTicket 91311591: CLOSED or not found")

mt5.shutdown()
