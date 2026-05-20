#!/usr/bin/env python3
"""
Diagnostic: Check what P90s the forward test should have seen today.
Uses same logic as the forward test but on historical data.
"""
import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json

# Use LIVE account to match what we want
LOGIN = 650898
PASSWORD = "Teflondon1718!"
SERVER = "OxSecurities-Live"
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

def to_price(pips):
    return pips / 10000.0

def est_from_utc(utc_h):
    return (utc_h - 5 + 24) % 24

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

# Get today's bars (last 500 from now, same as forward test)
rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M5, 0, 500)
if rates is None or len(rates) == 0:
    print("No data!")
    mt5.shutdown()
    exit(1)

print(f"Got {len(rates)} bars from copy_rates_from_pos")
print(f"First bar: {datetime.fromtimestamp(rates[0]['time'], tz=timezone.utc)}")
print(f"Last bar: {datetime.fromtimestamp(rates[-1]['time'], tz=timezone.utc)}")

# Convert to bars with EST
bars = []
for r in rates:
    ts = datetime.fromtimestamp(r['time'], tz=timezone.utc)
    est_h = est_from_utc(ts.hour)
    bars.append({
        'time': ts, 'est_h': est_h, 'date': ts.date(),
        'open': r['open'], 'high': r['high'], 'low': r['low'], 'close': r['close']
    })

# Filter to today
today = datetime.now(timezone.utc).date()
today_bars = [b for b in bars if b['date'] == today]
print(f"\nToday's bars: {len(today_bars)}")
if today_bars:
    print(f"First today: {today_bars[0]['time'].strftime('%H:%M')} EST {today_bars[0]['est_h']}")
    print(f"Last today: {today_bars[-1]['time'].strftime('%H:%M')} EST {today_bars[-1]['est_h']}")

# Scan for P90s in 2-11 AM EST window
print(f"\n--- P90 Scan (2-11 AM EST) ---")
p90_count = 0
for bar in today_bars:
    eh = bar['est_h']
    if eh < 2 or eh >= 11:
        continue
    body = to_pips(abs(bar['close'] - bar['open']))
    thresh = p90_threshold(eh)
    is_p90 = body >= thresh
    marker = " <<< P90!" if is_p90 else ""
    if is_p90 or body > 3.0:  # Show all large candles
        print(f"  {bar['time'].strftime('%H:%M')} EST | Body: {body:.1f}p | Thresh: {thresh:.1f}p | {'P90!' if is_p90 else 'no'}{marker}")
    if is_p90:
        p90_count += 1
        direction = 'LONG' if bar['close'] > bar['open'] else 'SHORT'
        activation = bar['close']
        ds = activation + to_price(body * 2.00) * (1 if direction == 'LONG' else -1)
        ks = activation + to_price(body * 2.20) * (1 if direction == 'LONG' else -1)
        rev = 'SHORT' if direction == 'LONG' else 'LONG'
        print(f"    Direction: {direction} | Activation: {activation} | DS: {ds} | KS: {ks} | Trade: {rev}")

print(f"\nTotal P90s found: {p90_count}")

# Also check: what did the forward test's get_today_bars actually return?
# The forward test filters by date match. Let's check if there's a timezone issue.
print(f"\n--- Date Check ---")
print(f"Today (UTC): {today}")
for bar in today_bars[:5]:
    print(f"  Bar: {bar['time'].strftime('%Y-%m-%d %H:%M')} UTC | Date: {bar['date']} | EST_h: {bar['est_h']}")
print("  ...")
for bar in today_bars[-3:]:
    print(f"  Bar: {bar['time'].strftime('%Y-%m-%d %H:%M')} UTC | Date: {bar['date']} | EST_h: {bar['est_h']}")

mt5.shutdown()
