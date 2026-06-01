# -*- coding: utf-8 -*-
"""
Trade Count Discrepancy Diagnostic
Runs BOTH Python engine and Nautilus engine on SAME EURUSD data.
Finds why Nautilus produces MORE trades.
"""
import sys, os
from pathlib import Path
from datetime import datetime, timezone as tz

LAB = Path("C:/Users/wifik/Desktop/projects/larger-lab")
sys.path.insert(0, str(LAB / "quant-lab"))
sys.path.insert(0, str(LAB / "quant-lab/engines"))
sys.path.insert(0, str(LAB / "quant-lab/strategies"))

import pandas as pd
import logging
logging.basicConfig(level=logging.WARNING)

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

# === 1. Load CSV ===
CSV_PATH = LAB / "quant-lab/data/EURUSD_M5.csv"
df = pd.read_csv(CSV_PATH)
print(f"CSV columns: {list(df.columns)} | shape: {df.shape}")
print(f"First ts: {df.iloc[0]['timestamp']} | Last ts: {df.iloc[-1]['timestamp']}")

# === 2. Run Python GT engine ===
from symmetry_trap import SymmetryTrapEngine, Bar

engine_py = SymmetryTrapEngine(pip_size=0.0001)

py_bars = []
for _, row in df.iterrows():
    try:
        ts = pd.Timestamp(str(row['timestamp'])).to_pydatetime()
        py_bars.append(Bar(
            timestamp=ts,
            open=float(row['open']),
            high=float(row['high']),
            low=float(row['low']),
            close=float(row['close'])
        ))
    except (KeyError, ValueError):
        continue

print(f"\nPython bars: {len(py_bars)}")

py_trades = []
py_entries = []
open_trade = None
for bar in py_bars:
    sig = engine_py.process_bar(bar)
    if sig is None:
        continue
    if sig.event == "ENTRY" and open_trade is None:
        open_trade = {
            "dir": sig.direction.value if sig.direction else 0,
            "entry": sig.entry_price, "sl": sig.sl_price,
            "tp": sig.tp_price, "ts": bar.timestamp,
            "loop": sig.loop_count
        }
        py_entries.append(open_trade)
    elif sig.event in ("TP_HIT", "SL_HIT", "KILL_SWITCH") and open_trade is not None:
        ep = open_trade["entry"]
        d = open_trade["dir"]
        xp = sig.entry_price if sig.entry_price else bar.close
        pnl = (xp - ep) / 0.0001 if d > 0 else (ep - xp) / 0.0001
        py_trades.append({
            "result": "WIN" if sig.event == "TP_HIT" else "LOSS",
            "pnl": pnl, "loop": open_trade["loop"]
        })
        open_trade = None

py_wins = sum(1 for t in py_trades if t["result"] == "WIN")
print(f"\n=== PYTHON GT ===")
print(f"Entries: {len(py_entries)} | Completed: {len(py_trades)}")
print(f"W: {py_wins} / L: {len(py_trades)-py_wins}")
if py_trades:
    print(f"WR: {py_wins/len(py_trades)*100:.1f}%")
    print(f"PnL: {sum(t['pnl'] for t in py_trades):.1f}p")

# === 3. Run Nautilus ===
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
from symmetry_trap_strategy import SymmetryTrapStrategy, SymmetryTrapConfig

instrument = TestInstrumentProvider.default_fx_ccy('EUR/USD', venue=Venue('OANDA'))
bar_type_str = f'{instrument.id}-5-MINUTE-LAST-EXTERNAL'
bar_type = BarType.from_str(bar_type_str)

df_n = df.copy()
df_n['timestamp'] = pd.to_datetime(df_n['timestamp'])
df_n = df_n.set_index('timestamp')
df_n.index = pd.to_datetime(df_n.index, utc=True)
keep = [c for c in ['open','high','low','close','volume'] if c in df_n.columns]
df_n = df_n[keep]
for c in keep:
    df_n[c] = pd.to_numeric(df_n[c], errors='coerce').astype('float64')

wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)
naut_bars = wrangler.process(df_n)
print(f"\nNautilus bars: {len(naut_bars)}")

config = BacktestEngineConfig(
    trader_id=TraderId('TRADE-DIFF-DIAG'),
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

naut_trades = strategy.total_trades
naut_wins = strategy.wins
naut_losses = strategy.losses
naut_wr = (naut_wins / naut_trades * 100.0) if naut_trades > 0 else 0.0

print(f"\n=== NAUTILUS ===")
print(f"Trades: {naut_trades} | W: {naut_wins} / L: {naut_losses} | WR: {naut_wr:.1f}%")

# === 4. Compare ===
print(f"\n=== DISCREPANCY ===")
print(f"Python:   {len(py_trades)} trades | {py_wins/len(py_trades)*100:.1f}% WR" if py_trades else "Python: 0 trades")
print(f"Nautilus: {naut_trades} trades | {naut_wr:.1f}% WR")
diff = naut_trades - len(py_trades)
print(f"Diff:     {diff:+d} trades (Nautilus {'more' if diff > 0 else 'fewer'})")
print(f"Bar diff: {len(naut_bars) - len(py_bars):+}")

# === 5. KEY HYPOTHESIS: Session/day boundary handling ===
# Nautilus uses bar.ts_event (UTC nanoseconds) for day detection
# Python uses Bar.timestamp (naive datetime from CSV)
# If CSV timestamps have no timezone, the EST conversion will be off by 5 hours
# This could cause: Asian session bars to shift to wrong day
# Result: Nautilus sees DIFFERENT Asian ranges -> different tier classifications -> different trade triggers

print(f"\n=== TIMEZONE CHECK ===")
print(f"Python bar[0] timestamp: {py_bars[0].timestamp} (tz={py_bars[0].timestamp.tzinfo})")
naut_first_dt = datetime.fromtimestamp(naut_bars[0].ts_event / 1e9, tz=tz.utc)
print(f"Nautilus bar[0] ts:      {naut_first_dt}")
est_offset = -5  # EST = UTC-5
first_est_hour = (naut_first_dt.hour + est_offset) % 24
print(f"Nautilus bar[0] EST hour: {first_est_hour}")

engine.dispose()
print("\nDone.")
