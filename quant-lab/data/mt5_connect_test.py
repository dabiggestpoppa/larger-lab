"""Quick test: connect to running MT5 and validate data availability"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5
from datetime import datetime

if not mt5.initialize():
    print(f"INIT FAILED: {mt5.last_error()}")
    sys.exit(1)

print("MT5 initialized!")

account = mt5.account_info()
print(f"Account: {account.login} | {account.server} | Balance: {account.balance} {account.currency}")

# Test data pull for each symbol
symbols = {
    'EURUSD.PRO': 'EURUSD',
    'USDCHF.PRO': 'USDCHF',
    'CHFJPY.PRO': 'CHFJPY',
    'XAUUSD.PRO': 'XAUUSD',
}

print("\n=== DATA AVAILABILITY ===")
for sym, name in symbols.items():
    rates = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M5, datetime(2022, 1, 1), datetime.now())
    if rates is not None and len(rates) > 0:
        first = datetime.fromtimestamp(rates[0][0])
        last = datetime.fromtimestamp(rates[-1][0])
        print(f"  {name:12}: {len(rates):>8,} M5 bars | {first} → {last}")
    else:
        print(f"  {name:12}: NO DATA")

mt5.shutdown()
print("\nDone.")
