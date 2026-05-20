#!/usr/bin/env python3
"""Check full date range for each forex pair"""
import MetaTrader5 as mt5
from datetime import datetime, timezone

if not mt5.initialize():
    print("MT5 init failed")
    exit(1)

pairs = ['EURUSD.PRO', 'USDCHF.PRO', 'CHFJPY.PRO', 'XAUUSD.PRO']
FROM = datetime(2021, 1, 1, tzinfo=timezone.utc)
TO = datetime(2026, 5, 19, tzinfo=timezone.utc)

for sym in pairs:
    rates = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M5, FROM, TO)
    if rates is not None and len(rates) > 0:
        first_date = datetime.fromtimestamp(rates[0][0], tz=timezone.utc)
        last_date = datetime.fromtimestamp(rates[-1][0], tz=timezone.utc)
        days = (last_date - first_date).days
        print(f"{sym}: {len(rates):,} bars | {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')} | {days} days")
    else:
        print(f"{sym}: NO DATA")

mt5.shutdown()
