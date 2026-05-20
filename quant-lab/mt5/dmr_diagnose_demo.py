#!/usr/bin/env python3
"""Diagnostic: Check what the DEMO account sees."""
import MetaTrader5 as mt5
from datetime import datetime, timezone

LOGIN = 1114712
PASSWORD = "***"
SERVER = "OxSecurities-Demo"
SYMBOL = "EURUSD.PRO"

def p90_threshold(est_h):
    if est_h < 2 or est_h >= 11: return 99.0
    if est_h < 4: return 4.1
    if est_h < 6: return 4.6
    if est_h < 8: return 4.6
    if est_h < 10: return 5.9
    if est_h < 11: return 6.2
    return 99.0

def to_pips(price_diff):
    return price_diff * 10000.0

if not mt5.initialize():
    print("MT5 init failed:", mt5.last_error())
    exit(1)

auth = mt5.login(login=LOGIN, password=PASSWORD, server=SERVER)
if not auth:
    print("Login failed:", mt5.last_error())
    mt5.shutdown()
    exit(1)

acct = mt5.account_info()
print(f"Connected: {acct.login} | {acct.server} | Balance: {acct.balance}")

# Check symbol
sym = mt5.symbol_info(SYMBOL)
if sym:
    print(f"Symbol {SYMBOL}: FOUND | Digits: {sym.digits} | Visible: {sym.visible}")
else:
    print(f"Symbol {SYMBOL}: NOT FOUND")
    # Try to find what symbols are available
    all_syms = mt5.symbols_get()
    if all_syms:
        eur_syms = [s.name for s in all_syms if 'EUR' in s.name]
        print(f"Available EUR symbols: {eur_syms[:10]}")

# Get bars
rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M5, 0, 500)
if rates is None or len(rates) == 0:
    print("No data!")
    mt5.shutdown()
    exit(1)

print(f"Got {len(rates)} bars")
print(f"First: {datetime.fromtimestamp(rates[0]['time'], tz=timezone.utc)}")
print(f"Last: {datetime.fromtimestamp(rates[-1]['time'], tz=timezone.utc)}")

# Check today's P90s
today = datetime.now(timezone.utc).date()
p90_count = 0
for r in rates:
    ts = datetime.fromtimestamp(r['time'], tz=timezone.utc)
    if ts.date() != today:
        continue
    est_h = (ts.hour - 5 + 24) % 24
    if est_h < 2 or est_h >= 11:
        continue
    body = to_pips(abs(r['close'] - r['open']))
    thresh = p90_threshold(est_h)
    if body >= thresh:
        p90_count += 1
        direction = 'LONG' if r['close'] > r['open'] else 'SHORT'
        print(f"  P90: {ts.strftime('%H:%M')} UTC ({est_h} EST) | Body: {body:.1p} | {direction}")

print(f"\nP90s on demo: {p90_count}")
mt5.shutdown()
