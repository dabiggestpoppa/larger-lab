"""
Run Nautilus XAUUSD backtest with debug monkey-patch to log:
- Session init events (date, tier, AR, active/trades)
- Trade count per session
- NO-GO count
"""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab')
sys.path.insert(0, 'quant-lab/strategies')
sys.path.insert(0, 'quant-lab/backtests')

import json
from pathlib import Path
from datetime import datetime
import pytz
import pandas as pd
from collections import defaultdict

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.identifiers import TraderId, Venue, InstrumentId
from nautilus_trader.model.enums import AccountType, OmsType, OrderSide
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Decimal
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import InstrumentCloseType
from strategies.symmetry_trap_strategy import SymmetryTrapStrategy, SymmetryTrapConfig
from quant_lab.configs.asset_configs import ASSET_CONFIGS

EST = pytz.timezone('US/Eastern')
DATA_DIR = Path('quant-lab/data')
REPORTS_DIR = Path('quant-lab/reports')

cfg = ASSET_CONFIGS['XAUUSD']

# Load instrument
instrument = TestInstrumentProvider.default_fx_ccy("XAU/USD", venue=Venue("OANDA"))
bar_type_str = f"{instrument.id}-5-MINUTE-LAST-EXTERNAL"
bar_type = BarType.from_str(bar_type_str)

# Load bars same as runner
df = pd.read_csv(DATA_DIR / "XAUUSD_M5.csv")
if 'timestamp' in df.columns:
    df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
keep_cols = [c for c in ['open', 'high', 'low', 'close', 'volume'] if c in df.columns]
df = df[keep_cols]
for c in keep_cols:
    df[c] = pd.to_numeric(df[c], errors='coerce').astype('float64')
wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)
bars = wrangler.process(df)
print(f"Loaded {len(bars)} bars")

# Monkey-patch the strategy to add debug logging
original_on_bar = SymmetryTrapStrategy.on_bar
session_log = []

def patched_on_bar(self, bar):
    # Capture session init events
    est_hour = self._est_hour_from_bar(bar, self.est_offset)
    ts = bar.ts_event

    # Track state before
    prev_active = self.session_active
    prev_state = self._strategy_state
    prev_tier = self.tier_name if hasattr(self, 'tier_name') else 'N/A'
    prev_loop = self.loop_count if hasattr(self, 'loop_count') else 0

    # Call original
    result = original_on_bar(self, bar)

    # Log session init events
    if not prev_active and self.session_active:
        session_log.append({
            'event': 'SESSION_INIT',
            'ts': str(ts),
            'est_hour': est_hour,
            'tier': self.tier_name,
            'ar_pips': round(self.asian_range_pips, 1),
            'trigger': self.trigger_pips,
            'active': self.session_active,
            'state': self._strategy_state,
        })

    # Log NO-GO events (session_active was checked but not set)
    # Hard to detect this way since on_bar returns early

    return result

SymmetryTrapStrategy.on_bar = patched_on_bar

# Build tier config override
tier_override = {}
for tier_name in ['T1', 'T2', 'T3']:
    t = cfg['tiers'][tier_name]
    tier_override[tier_name] = {'ar_max': t['ar_max'], 'au': t['au'], 'trigger': t['trigger']}

strat_config = SymmetryTrapConfig(
    instrument_id=str(instrument.id),
    bar_type=str(bar_type),
    lot_size=Decimal("1000"),
    tier_config_override=tier_override,
)

engine_config = BacktestEngineConfig(
    trader_id=TraderId("CEREBUS-ST-DEBUG-001"),
    logging=LoggingConfig(log_level="WARNING"),
)
engine = BacktestEngine(config=engine_config)
engine.add_venue(
    venue=Venue("OANDA"),
    oms_type=OmsType.NETTING,
    account_type=AccountType.MARGIN,
    base_currency=Money(10000, Money.currency),
    starting_balances=[Money(10000, Money.currency)],
)

Money.currency = None  # Will use default
from nautilus_trader.model.currency import Currency
USD = Currency.from_str("USD")

engine.add_venue(
    venue=Venue("OANDA"),
    oms_type=OmsType.NETTING,
    account_type=AccountType.MARGIN,
    base_currency=USD,
    starting_balances=[Money(10000, USD)],
)

engine.add_instrument(instrument)

strategy = SymmetryTrapStrategy(config=strat_config)
engine.add_strategy(strategy=strategy)
engine.add_data(bars)

print("Running backtest...")
engine.run()

print(f"\n=== NAUTILUS RESULTS ===")
print(f"Total trades: {strategy.total_trades}")
print(f"Wins: {strategy.wins}, Losses: {strategy.losses}")
print(f"WR: {strategy.wins/strategy.total_trades*100:.1f}%" if strategy.total_trades > 0 else "N/A")
print(f"PnL: {strategy.total_pnl_pips:.1f} pips")

print(f"\n=== SESSION LOG ===")
print(f"Session init events logged: {len(session_log)}")
for s in session_log[:20]:
    print(f"  {s}")

engine.dispose()
