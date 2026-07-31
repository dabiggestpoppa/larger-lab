"""
Compare bar alignment between Python and Nautilus for first active session.
Focus on: first few bars, their EST hours, and Asian range calculation.
"""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab/engines')
sys.path.insert(0, 'quant-lab/strategies')

from datetime import timedelta, timezone
from collections import defaultdict
from symmetry_trap_backtest import load_m5_csv
from symmetry_trap import SymmetryTrapEngine, Bar, EngineState
import pandas as pd
import pytz

# Python bars
py_bars, _ = load_m5_csv('quant-lab/data/XAUUSD_M5.csv')
print(f"Python bars: {len(py_bars)}")
print(f"First Python bar: ts={py_bars[0].timestamp} h={py_bars[0].timestamp.hour}")

# Nautilus bars via BarDataWrangler
from pathlib import Path
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.model.data import BarType

instrument = TestInstrumentProvider.default_fx_ccy("XAU/USD", venue=Venue("OANDA"))
bar_type_str = f"{instrument.id}-5-MINUTE-LAST-EXTERNAL"
bar_type = BarType.from_str(bar_type_str)

df = pd.read_csv('quant-lab/data/XAUUSD_M5.csv')
if 'timestamp' in df.columns:
    df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)

keep_cols = [c for c in ['open', 'high', 'low', 'close', 'volume'] if c in df.columns]
df = df[keep_cols]
for c in keep_cols:
    df[c] = pd.to_numeric(df[c], errors='coerce').astype('float64')

wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)
naut_bars = wrangler.process(df)
print(f"Nautilus bars: {len(naut_bars)}")

# Compare first 20 bars
print("\n=== First 20 bars comparison ===")
print(f"{'#':>3} | {'Python ts':>25} | {'Python EST h':>12} | {'Nautilus ts_event':>20} | {'Ns EST h':>8} | {'Match':>5}")
for i in range(min(20, len(py_bars), len(naut_bars))):
    py_b = py_bars[i]
    naut_b = naut_bars[i]

    py_ts = py_b.timestamp
    if py_ts.tzinfo is None:
        py_ts_utc = py_ts.replace(tzinfo=timezone.utc)
    else:
        py_ts_utc = py_ts.astimezone(timezone.utc)
    py_est_h = (py_ts_utc.hour - 5) % 24

    # Nautilus ts_event is UTC nanoseconds
    naut_ts_ns = naut_b.ts_event
    naut_ts_utc_s = naut_ts_ns / 1e9
    from datetime import datetime as dt
    naut_ts_utc = dt.fromtimestamp(naut_ts_utc_s, tz=timezone.utc)
    naut_est_h = (naut_ts_utc.hour - 5) % 24

    match = py_ts_utc == naut_ts_utc
    print(f"{i:>3} | {str(py_ts):>25} | {py_est_h:>12} | {str(naut_ts_utc):>20} | {naut_est_h:>8} | {'Y' if match else 'N':>5}")

# Check if bar counts match
print(f"\nPython bar count: {len(py_bars)}")
print(f"Nautilus bar count: {len(naut_bars)}")
print(f"Bar count match: {len(py_bars) == len(naut_bars)}")

# Check: do ALL timestamps match?
mismatches = 0
for i in range(min(len(py_bars), len(naut_bars))):
    py_b = py_bars[i]
    naut_b = naut_bars[i]
    py_ts = py_b.timestamp
    if py_ts.tzinfo is None:
        py_ts_utc = py_ts.replace(tzinfo=timezone.utc)
    else:
        py_ts_utc = py_ts.astimezone(timezone.utc)
    naut_ts_ns = naut_b.ts_event
    naut_ts_utc_s = naut_ts_ns / 1e9
    naut_ts_utc = dt.fromtimestamp(naut_ts_utc_s, tz=timezone.utc)
    if py_ts_utc != naut_ts_utc:
        mismatches += 1

print(f"Timestamp mismatches: {mismatches}")
if mismatches > 0:
    print("First 5 mismatches:")
    count = 0
    for i in range(min(len(py_bars), len(naut_bars))):
        py_b = py_bars[i]
        naut_b = naut_bars[i]
        py_ts = py_b.timestamp
        if py_ts.tzinfo is None:
            py_ts_utc = py_ts.replace(tzinfo=timezone.utc)
        else:
            py_ts_utc = py_ts.astimezone(timezone.utc)
        naut_ts_ns = naut_b.ts_event
        naut_ts_utc_s = naut_ts_ns / 1e9
        naut_ts_utc = dt.fromtimestamp(naut_ts_utc_s, tz=timezone.utc)
        if py_ts_utc != naut_ts_utc and count < 5:
            print(f"  Bar {i}: Python={py_ts_utc}, Nautilus={naut_ts_utc}")
            count += 1
