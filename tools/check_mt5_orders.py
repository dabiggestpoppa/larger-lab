import MetaTrader5 as mt5
from pathlib import Path
import json

CONFIG_FILE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_config.json")
with open(CONFIG_FILE) as f:
    cfg = json.load(f)

mt5.initialize()
auth = mt5.login(login=cfg['login'], password=cfg['password'], server=cfg['server'])
print(f"Connected: {mt5.account_info().login}")
print(f"Balance: {mt5.account_info().balance}")
print(f"AutoTrading: {mt5.terminal_info().trade_allowed}")

# Check pending orders
orders = mt5.orders_get()
if orders:
    print(f"\nPending orders: {len(orders)}")
    for o in orders:
        print(f"  Ticket:{o.ticket} {o.symbol} {o.type} {o.volume} @ {o.price_open} SL:{o.sl} TP:{o.tp} magic:{o.magic}")
else:
    print("\nNo pending orders")

# Check positions
positions = mt5.positions_get()
if positions:
    print(f"\nOpen positions: {len(positions)}")
    for p in positions:
        print(f"  Ticket:{p.ticket} {p.symbol} {'BUY' if p.type==0 else 'SELL'} {p.volume} @ {p.price_open} PnL:{p.profit} magic:{p.magic}")
else:
    print("\nNo open positions")

# Check orders history (today)
from datetime import datetime, timezone
today = datetime.now(timezone.utc).date()
history = mt5.history_orders_get(today, datetime.now(timezone.utc))
if history:
    print(f"\nOrder history today: {len(history)}")
    for h in history:
        print(f"  Ticket:{h.ticket} {h.symbol} {h.type} {h.volume} @ {h.price_open} state:{h.state} magic:{h.magic}")
else:
    print("\nNo order history today")

mt5.shutdown()
