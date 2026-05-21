import MetaTrader5 as mt5
from pathlib import Path
import json

CONFIG_FILE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_config.json")
with open(CONFIG_FILE) as f:
    cfg = json.load(f)

mt5.initialize()
mt5.login(login=cfg['login'], password=cfg['password'], server=cfg['server'])
info = mt5.terminal_info()
acct = mt5.account_info()

print(f"Login: {acct.login}")
print(f"Balance: {acct.balance}")
print(f"AutoTrading (trade_allowed): {info.trade_allowed}")
print(f"Expert advisors: {info.expert}")
print(f"Trade allowed: {info.trade_allowed}")
print(f"Terminal build: {info.build}")

# Check for any existing orders
orders = mt5.orders_get()
print(f"\nPending orders: {len(orders) if orders else 0}")
if orders:
    for o in orders:
        print(f"  Ticket:{o.ticket} {o.symbol} type={o.type} vol={o.volume} price={o.price_open} magic={o.magic}")

positions = mt5.positions_get()
print(f"Open positions: {len(positions) if positions else 0}")
if positions:
    for p in positions:
        print(f"  Ticket:{p.ticket} {p.symbol} {'BUY' if p.type==0 else 'SELL'} vol={p.volume} PnL={p.profit}")

mt5.shutdown()
