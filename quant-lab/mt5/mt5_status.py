import MetaTrader5 as mt5
from datetime import datetime

mt5.initialize()

print("=== MT5 Account ===")
info = mt5.account_info()
print(f"Balance: ${info.balance:.2f} | Equity: ${info.equity:.2f}")

print("\n=== Open Positions ===")
positions = mt5.positions_get()
if positions:
    for p in positions:
        dir_name = "BUY" if p.type == 0 else "SELL"
        print(f"Ticket:{p.ticket} {p.symbol} {dir_name} {p.volume:.2f}@{p.price_open:.5f} SL:{p.sl:.5f} TP:{p.tp:.5f} P&L:${p.profit:.2f}")
else:
    print("No open positions")

print(f"\nChecked: {datetime.now().strftime('%H:%M:%S')}")
mt5.shutdown()
