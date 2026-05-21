import MetaTrader5 as mt5
from pathlib import Path
import json

CONFIG_FILE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_config.json")
with open(CONFIG_FILE) as f:
    cfg = json.load(f)

mt5.initialize()
auth = mt5.login(login=cfg['login'], password=cfg['password'], server=cfg['server'])
info = mt5.terminal_info()
acct = mt5.account_info()

print(f"Connected: {acct.login}")
print(f"Balance: {acct.balance}")
print(f"AutoTrading (trade_allowed): {info.trade_allowed}")
print(f"Trade allowed: {info.trade_allowed}")
print(f"Expert advisors enabled: {info.expert}")

# Check for any pending orders
orders = mt5.orders_get()
print(f"Pending orders: {len(orders) if orders else 0}")

# Check positions
positions = mt5.positions_get()
print(f"Open positions: {len(positions) if positions else 0}")

mt5.shutdown()
