import MetaTrader5 as mt5
SYMBOL = "EURUSD.PRO"
MAGIC = 20260528

if not mt5.initialize():
    print("MT5 init failed")
    exit(1)

# Cancel ALL our pending orders
orders = mt5.orders_get(symbol=SYMBOL)
pending = [o for o in orders if o.magic == MAGIC] if orders else []
print(f"Cancelling {len(pending)} pending orders...")
for o in pending:
    req = {"action": mt5.TRADE_ACTION_REMOVE, "order": o.ticket}
    result = mt5.order_send(req)
    print(f"  ticket={o.ticket}: retcode={result.retcode if result else 'None'}")

# Check 
orders2 = mt5.orders_get(symbol=SYMBOL)
remaining = [o for o in orders2 if o.magic == MAGIC] if orders2 else []
print(f"Remaining: {len(remaining)}")
mt5.shutdown()
