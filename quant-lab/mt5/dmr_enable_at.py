#!/usr/bin/env python3
"""Try to enable MT5 AutoTrading and verify."""
import MetaTrader5 as mt5

LOGIN = 650898
PASSWORD = "Teflondon1718!"
SERVER = "OxSecurities-Live"

if not mt5.initialize():
    print(f"Init failed: {mt5.last_error()}")
    exit(1)

auth = mt5.login(login=LOGIN, password=PASSWORD, server=SERVER)
if not auth:
    print(f"Login failed: {mt5.last_error()}")
    mt5.shutdown()
    exit(1)

term = mt5.terminal_info()
print(f"Terminal trade_allowed: {term.trade_allowed}")
print(f"Terminal tradeapi_disabled: {term.tradeapi_disabled}")

acct = mt5.account_info()
print(f"Account trade allowed: {acct.trade_allowed}")
print(f"Account trade expert: {acct.trade_expert}")

# The issue: terminal_info().trade_allowed = False means AutoTrading is OFF in MT5
# This is a UI setting that must be toggled in the MT5 terminal
# The Python API cannot toggle it programmatically — it's a safety feature

if not term.trade_allowed:
    print("\n⚠️  AUTOTRADING IS DISABLED IN MT5!")
    print("You need to click the 'AutoTrading' button in the MT5 toolbar.")
    print("It's the green/blue play button in the top toolbar.")
    print("When enabled, it should turn green.")
else:
    print("\n✅ AutoTrading is enabled!")

mt5.shutdown()
