import MetaTrader5 as mt5
import json

cfg_file = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_config.json"
with open(cfg_file) as f:
    cfg = json.load(f)

mt5.initialize()
auth = mt5.login(login=cfg['login'], password=cfg['password'], server=cfg['server'])

# Check today's history
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

history = mt5.history_deals_get(start, now)
if history:
    for d in history:
        if d.magic == cfg['magic_number']:
            print(f"Deal: {d.symbol} {d.type} @ {d.price} Vol:{d.volume} PnL:{d.profit} Ticket:{d.order}")
else:
    print("No deals today")

# Also check account history for context
acct = mt5.account_info()
print(f"\nBalance: {acct.balance} | Equity: {acct.equity}")

# Check all positions
positions = mt5.positions_get()
if positions:
    for p in positions:
        print(f"Open: {p.symbol} {'BUY' if p.type==0 else 'SELL'} @ {p.price_open} PnL:{p.profit} Ticket:{p.ticket}")
else:
    print("No open positions")

mt5.shutdown()
