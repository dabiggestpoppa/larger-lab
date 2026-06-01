# -*- coding: utf-8 -*-
"""
Precise diff: Run Python backtest instrumented to log every session's 
trade count, then compare with Nautilus session-by-session.

Key insight: The backtest campaign Python result (1163 trades for ST EURUSD)
comes from the symmetry_trap_backtest.py SymmetryTrapBacktest.run() method.
We need to match that exactly, then compare per-session with Nautilus.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from datetime import datetime, timedelta, timezone as tz
from collections import defaultdict

LAB = Path("C:/Users/wifik/Desktop/projects/larger-lab")
sys.path.insert(0, str(LAB / "quant-lab/engines"))

import pandas as pd

from symmetry_trap_backtest import load_m5_csv, SymmetryTrapBacktest, SymmetryTrapEngine, TradeRecord
from symmetry_trap import Bar, EngineState, TradeDirection

# === 1. Load data ===
bars, sym = load_m5_csv(str(LAB / "quant-lab/data/EURUSD_M5.csv"))
print(f"Loaded {len(bars)} bars | {bars[0].timestamp} -> {bars[-1].timestamp}")

# === 2. Run Python with per-session logging ===
py_bt = SymmetryTrapBacktest(pip_size=0.0001)

# Replicate the run() method but with logging
est_offset = -5

days = {}
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=est_offset)
    dk = est_dt.strftime("%Y-%m-%d")
    if dk not in days:
        days[dk] = []
    days[dk].append(bar)

py_session_trades = {}  # date -> trade count
py_total = 0

for dk in sorted(days.keys()):
    day_bars = sorted(days[dk], key=lambda b: b.timestamp)
    
    # Find Asian range
    ah, al = 0.0, 99999.0
    for b in day_bars:
        h = (b.timestamp.hour + est_offset) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    if ah <= 0 or al >= 99999:
        continue
    
    engine = SymmetryTrapEngine(pip_size=0.0001)
    engine.initialize_session(ah, al)
    if not engine.session_active:
        continue
    
    day_trades = 0
    for bar in day_bars:
        bar_est_h = (bar.timestamp.hour + est_offset) % 24
        if bar_est_h >= 12 and engine.state == EngineState.SEARCH:
            break
        
        signal = engine.process_bar(bar)
        if signal and signal.event in ("TP_HIT", "SL_HIT", "KILL_SWITCH"):
            day_trades += 1
    
    py_session_trades[dk] = day_trades
    py_total += day_trades

print(f"\n=== PYTHON GT ===")
print(f"Total trades: {py_total}")
print(f"Active sessions: {len(py_session_trades)}")
print(f"Avg trades/session: {py_total/max(len(py_session_trades),1):.1f}")

# Show top sessions
top_sessions = sorted(py_session_trades.items(), key=lambda x: -x[1])[:10]
print(f"\nTop 10 sessions by trade count:")
for dk, cnt in top_sessions:
    print(f"  {dk}: {cnt} trades")

# Show distribution
dist = defaultdict(int)
for dk, cnt in py_session_trades.items():
    dist[cnt] += 1
print(f"\nTrade count distribution:")
for k in sorted(dist.keys()):
    print(f"  {k} trades: {dist[k]} sessions")

# === 3. Run Nautilus with per-session logging ===
# We need to instrument the Nautilus strategy to log trades per session
# We'll create a wrapper that captures strategy events

from decimal import Decimal
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.backtest.models import FillModel

sys.path.insert(0, str(LAB / "quant-lab/strategies"))

# Monkey-patch the Nautilus strategy to log per-session trades
from symmetry_trap_strategy import SymmetryTrapStrategy, SymmetryTrapConfig, EST_OFFSET

original_on_bar = SymmetryTrapStrategy.on_bar
original_on_stop = SymmetryTrapStrategy.on_stop

naut_session_log = {}  # date -> trade count
naut_total_trades = [0]

def patched_on_bar(self, bar):
    # Track which EST day this bar belongs to
    est_hour = (bar.ts_event // 3_600_000_000_000 + EST_OFFSET) % 24
    utc_date = datetime.fromtimestamp(bar.ts_event / 1e9, tz=tz.utc).date()
    est_date = (utc_date if est_hour >= (24 + EST_OFFSET) % 24 
                else utc_date)  # simplified
    
    # Count before
    trades_before = self.total_trades
    original_on_bar(self, bar)
    # Count after
    if self.total_trades > trades_before:
        dk = str(utc_date)  # Nautilus uses UTC date as session key
        naut_session_log[dk] = naut_session_log.get(dk, 0) + (self.total_trades - trades_before)
        naut_total_trades[0] = self.total_trades

SymmetryTrapStrategy.on_bar = patched_on_bar

# Run Nautilus
# from nautilus_trader.model.functions import instrument_id_from_str  # not needed

instrument = TestInstrumentProvider.default_fx_ccy('EUR/USD', venue=Venue('OANDA'))
bar_type_str = f'{instrument.id}-5-MINUTE-LAST-EXTERNAL'
bar_type = BarType.from_str(bar_type_str)

# Load Nautilus bars
csv_path = LAB / "quant-lab/data/EURUSD_M5.csv"
df = pd.read_csv(csv_path)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
keep = [c for c in ['open','high','low','close','volume'] if c in df.columns]
df = df[keep]
for c in keep:
    df[c] = pd.to_numeric(df[c], errors='coerce').astype('float64')

wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)
naut_bars = wrangler.process(df)
print(f"\nNautilus bars: {len(naut_bars)}")

config = BacktestEngineConfig(
    trader_id=TraderId('PRECISE-DIFF'),
    logging=LoggingConfig(log_level='ERROR'),
)
engine = BacktestEngine(config=config)
engine.add_venue(
    venue=Venue('OANDA'), oms_type=OmsType.NETTING,
    account_type=AccountType.MARGIN, base_currency=USD,
    starting_balances=[Money(10000, USD)],
    fill_model=FillModel(prob_fill_on_limit=1.0, prob_slippage=0.0),
)
engine.add_instrument(instrument)

tier_ovr = {
    'T1': {'ar_max': 20.0, 'au': 10.0, 'trigger': 12.0},
    'T2': {'ar_max': 30.0, 'au': 12.0, 'trigger': 15.0},
    'T3': {'ar_max': 45.0, 'au': 15.0, 'trigger': 19.0},
}
strat_config = SymmetryTrapConfig(
    instrument_id=str(instrument.id), bar_type=str(bar_type),
    lot_size=Decimal('1000'), tier_config_override=tier_ovr,
)
strategy = SymmetryTrapStrategy(config=strat_config)
engine.add_strategy(strategy=strategy)
engine.add_data(naut_bars)

print("Running Nautilus...")
engine.run()

# Restore
SymmetryTrapStrategy.on_bar = original_on_bar

print(f"\n=== NAUTILUS ===")
print(f"Total trades: {naut_total_trades[0]}")
print(f"Active sessions: {len(naut_session_log)}")
if naut_session_log:
    print(f"Avg trades/session: {naut_total_trades[0]/len(naut_session_log):.1f}")

naut_top = sorted(naut_session_log.items(), key=lambda x: -x[1])[:10]
print(f"\nTop 10 Nautilus sessions:")
for dk, cnt in naut_top:
    print(f"  {dk}: {cnt} trades")

naut_dist = defaultdict(int)
for dk, cnt in naut_session_log.items():
    naut_dist[cnt] += 1
print(f"\nNautilus distribution:")
for k in sorted(naut_dist.keys()):
    print(f"  {k} trades: {naut_dist[k]} sessions")

# === 4. Direct session comparison ===
print(f"\n=== SESSION-BY-SESSION COMPARISON ===")
# Map dates: Python EST date D ~= Nautilus UTC date D+1 (roughly) 
# Better approach: compare the same UTC dates
# Python EST date D covers UTC [D 05:00 to D+1 04:59]
# Nautilus UTC date D covers UTC [D 00:00 to D 23:59]
# They overlap but aren't aligned

# Let's compare on Nautilus dates and see what Python says for overlapping sessions
common_dates = set(py_session_trades.keys()) & set(
    (datetime.strptime(d, "%Y-%m-%d").date() - timedelta(hours=5)).strftime("%Y-%m-%d")
    for d in naut_session_log.keys()
)

# Easier: just compare totals and average
print(f"Python total: {py_total} trades in {len(py_session_trades)} sessions")
print(f"Nautilus total: {naut_total_trades[0]} trades in {len(naut_session_log)} sessions")
print(f"Ratio: Nautilus/Python = {naut_total_trades[0]/max(py_total,1):.2f}x")

# === 5. The real smoking gun: feed Nautilus ONLY the first N sessions ===
# and compare session-by-session with Python
print(f"\n=== MATCHING SESSIONS ===")
# Align by creating Nautilus-equivalent date keys
# Nautilus UTC date = Python EST date + 1 day (approximately)
# Better: convert Nautilus sessions to Python keys
naut_as_python = {}
for dk_str, cnt in naut_session_log.items():
    # Nautilus date D (UTC) overlaps mostly with Python date D-1 (EST)
    # Python EST date D-1 covers UTC [D-1 05:00 to D 04:59]
    # Nautilus UTC date D covers UTC [D 00:00 to D 23:59]
    # Overlap: D 00:00-04:59 (Asian continuation) + D 05:00-23:59 (rest of day)
    # So Nautilus date D contains MORE bars than Python date D-1
    # Specifically, Nautilus has extra bars from D-1's UTC range that Python puts in D-1
    
    # The cleanest mapping: Nautilus UTC date D -> Python EST date D (NOT D-1)
    # Because Python EST date D = UTC [D 05:00 to D+1 04:59]
    # Nautilus UTC date D = UTC [D 00:00 to D 23:59]
    # These overlap by UTC [D 05:00 to D 23:59]
    # The difference: Nautilus also has D 00:00-04:59 = Asian continuation from previous session
    
    # Let's just match what we can
    naut_as_python[dk_str] = cnt

matched = 0
unmatched_naut = 0
for dk, naut_cnt in sorted(naut_session_log.items()):
    if dk in py_session_trades:
        py_cnt = py_session_trades[dk]
        diff = naut_cnt - py_cnt
        if matched < 20:
            print(f"  {dk}: Py={py_cnt} | Naut={naut_cnt} | Diff={diff:+d}")
        matched += 1
    else:
        unmatched_naut += 1

print(f"\nMatched sessions: {matched}")
print(f"Unmatched Nautilus sessions: {unmatched_naut}")

# Check: what about Python dates that Nautilus doesn't have?
unmatched_py = sum(1 for dk in py_session_trades if dk not in naut_session_log)
print(f"Unmatched Python sessions: {unmatched_py}")

engine.dispose()
print("\nDone.")
