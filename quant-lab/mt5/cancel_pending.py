import MetaTrader5 as mt5

SYMBOL = "EURUSD.PRO"
MAGIC = 20260528

if not mt5.initialize():
    print("MT5 init failed")
    exit(1)

# Check pending orders
orders = mt5.orders_get(symbol=SYMBOL)
pending = [o for o in orders if o.magic == MAGIC] if orders else []
print(f"Pending orders: {len(pending)}")
for o in pending:
    print(f"  ticket={o.ticket} type={o.type} price={o.price_open} vol={o.volume_current}")

# Cancel all our pending orders
for o in pending:
    req = {
        "action": mt5.TRADE_ACTION_REMOVE,
        "order": o.ticket,
    }
    result = mt5.order_send(req)
    print(f"  Cancel ticket={o.ticket}: retcode={result.retcode if result else 'None'}")

# Check positions
positions = mt5.positions_get(symbol=SYMBOL)
pos = [p for p in positions if p.magic == MAGIC] if positions else []
print(f"\nOpen positions: {len(pos)}")
for p in pos:
    print(f"  ticket={p.ticket} type={p.type} open_price={p.price_open} SL={p.sl} TP={p.tp}")

mt5.shutdown()
print("Done")
