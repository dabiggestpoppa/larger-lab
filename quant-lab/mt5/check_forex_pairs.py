#!/usr/bin/env python3
"""Check which forex pairs have sufficient M5 history"""
import MetaTrader5 as mt5
from datetime import datetime, timezone

if not mt5.initialize():
    print("MT5 init failed")
    exit(1)

FROM = datetime(2022, 1, 1, tzinfo=timezone.utc)
pairs = ['EURUSD.PRO', 'USDCHF.PRO', 'CHFJPY.PRO', 'XAUUSD.PRO', 'XAUAUD.PRO']

for sym in pairs:
    rates = mt5.copy_rates_from(sym, mt5.TIMEFRAME_M5, FROM, 100)
    if rates is not None and len(rates) > 0:
        first_date = datetime.fromtimestamp(rates[0][0], tz=timezone.utc)
        last_date = datetime.fromtimestamp(rates[-1][0], tz=timezone.utc)
        days = (last_date - first_date).days
        est_bars = days * 288  # ~288 M5 bars per day
        print(f"{sym}: {len(rates)} bars sampled | {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')} | ~{days} days | est {est_bars:,} total bars")
    else:
        print(f"{sym}: NO DATA")

mt5.shutdown()
