import MetaTrader5 as mt5
SYMBOL = "EURUSD.PRO"
MAGIC = 20260528

if not mt5.initialize():
    print("MT5 init failed")
    exit(1)

acct = mt5.account_info()
print(f"Account: {acct.login} | Balance: ${acct.balance:.2f}")

# Pending orders
orders = mt5.orders_get(symbol=SYMBOL)
pending = [o for o in orders if o.magic == MAGIC] if orders else []
print(f"\nPending orders (our magic): {len(pending)}")
for o in pending:
    print(f"  ticket={o.ticket} type={o.type} price={o.price_open} vol={o.volume_current} SL={o.sl} TP={o.tp}")

# Open positions
positions = mt5.positions_get(symbol=SYMBOL)
pos = [p for p in positions if p.magic == MAGIC] if positions else []
print(f"\nOpen positions (our magic): {len(pos)}")
for p in pos:
    print(f"  ticket={p.ticket} type={p.type} open={p.price_open} SL={p.sl} TP={p.tp} PnL={p.profit:+.2f}")

# Check specific ticket
print("\nChecking ticket 10627645:")
all_orders = mt5.orders_get()
if all_orders:
    for o in all_orders:
        if o.ticket == 10627645:
            print(f"  FOUND: type={o.type} price={o.price_open} SL={o.sl} TP={o.tp} state={o.state}")
            break
    else:
        print("  Not found in pending orders (may have been filled or cancelled)")

# Check all orders count
print(f"\nTotal pending orders (all): {len(orders) if orders else 0}")
print(f"Total open positions: {len(positions) if positions else 0}")

mt5.shutdown()
