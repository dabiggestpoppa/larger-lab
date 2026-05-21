"""Check MT5 EA status and the 'Out of activations' issue."""
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

print(f"Account: {acct.login} | Balance: {acct.balance}")
print(f"AutoTrading: {info.trade_allowed}")
print(f"Community connection: {info.community_connection}")
print(f"DLLs allowed: {info.dlls_allowed}")

# Check all open positions and their magic numbers
positions = mt5.positions_get()
if positions:
    print(f"\nOpen positions: {len(positions)}")
    for p in positions:
        print(f"  {p.symbol} {'BUY' if p.type==0 else 'SELL'} {p.volume} @ {p.price_open} PnL:{p.profit} magic:{p.magic}")
else:
    print("\nNo open positions")

# Check pending orders
orders = mt5.orders_get()
if orders:
    print(f"\nPending orders: {len(orders)}")
    for o in orders:
        print(f"  {o.symbol} type={o.type} vol={o.volume} price={o.price_open} magic={o.magic}")
else:
    print("No pending orders")

# Check history for today
from datetime import datetime, timezone
today = datetime.now(timezone.utc).date()
history = mt5.history_orders_get(today, datetime.now(timezone.utc))
if history:
    print(f"\nOrder history today: {len(history)}")
    for h in history[-5:]:
        print(f"  {h.symbol} type={h.type} vol={h.volume} state={h.state} magic={h.magic} comment={h.comment}")
else:
    print("\nNo order history today")

# Check history deals
deals = mt5.history_deals_get(today, datetime.now(timezone.utc))
if deals:
    print(f"\nDeals today: {len(deals)}")
    for d in deals[-5:]:
        print(f"  {d.symbol} {'BUY' if d.type==0 else 'SELL'} {d.volume} @ {d.price} profit={d.profit} magic={d.magic}")
else:
    print("\nNo deals today")

mt5.shutdown()
