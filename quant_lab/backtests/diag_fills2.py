"""Debug: Check order fill status - suppress Nautilus log noise"""
import sys, os
from pathlib import Path
from decimal import Decimal
from collections import Counter

# Suppress Nautilus logging noise
os.environ['NAUTILUS_LOG_LEVEL'] = 'ERROR'

sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))

import pandas as pd

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

csv_path = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\USDCHFPRO_M5_MAD.csv')

instrument = TestInstrumentProvider.default_fx_ccy('USD/CHF', venue=Venue('OANDA'))
bar_type_str = f'{instrument.id}-5-MINUTE-LAST-EXTERNAL'
bar_type = BarType.from_str(bar_type_str)

df = pd.read_csv(csv_path, nrows=5000)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
w = BarDataWrangler(bar_type=bar_type, instrument=instrument)
bars = w.process(df)
print(f'Loaded {len(bars)} bars')

config = BacktestEngineConfig(
    trader_id=TraderId('FILL2-001'),
    logging=LoggingConfig(log_level='CRITICAL'),  # Suppress almost all Nautilus logs
)
engine = BacktestEngine(config=config)
engine.add_venue(
    venue=Venue('OANDA'),
    oms_type=OmsType.NETTING,
    account_type=AccountType.MARGIN,
    base_currency=USD,
    starting_balances=[Money(10000, USD)],
    fill_model=FillModel(prob_fill_on_limit=0.95, prob_slippage=0.05),
)
engine.add_instrument(instrument)

lot_size = Decimal('1000')
strat_config = SymmetryTrapConfig(
    instrument_id=str(instrument.id),
    bar_type=str(bar_type),
    lot_size=lot_size,
)
strategy = SymmetryTrapStrategy(config=strat_config)
engine.add_strategy(strategy=strategy)
engine.add_data(bars)

engine.run()

# Order analysis
orders = engine.cache.orders()
print(f'\nORDERS: {len(orders)} total')

status_counts = Counter()
for o in orders:
    s = o.status.name if hasattr(o.status, 'name') else str(o.status)
    status_counts[s] += 1
print('Status distribution:')
for status, count in sorted(status_counts.items()):
    print(f'  {status}: {count}')

# Filled order details
filled = [o for o in orders if hasattr(o.status, 'name') and o.status.name == 'FILLED']
print(f'\nFILLED: {len(filled)}')
for o in filled[:5]:
    evts = o.events if hasattr(o, 'events') else []
    fill_evts = [e for e in evts if type(e).__name__ == 'OrderFilled'] if evts else []
    fill_price = None
    if fill_evts:
        fill_price = getattr(fill_evts[0], 'last_px', None)
    print(f'  side={o.side} qty={o.quantity} fill_price={fill_price}')

# Denied order details
denied = [o for o in orders if hasattr(o.status, 'name') and o.status.name == 'DENIED']
if denied:
    print(f'\nDENIED: {len(denied)}')
    for o in denied[:3]:
        print(f'  reason={getattr(o.last_event, \"reason\", None) if hasattr(o, \"last_event\") and o.last_event else \"?\"}')

# Position analysis
positions = engine.cache.positions()
print(f'\nPOSITIONS: {len(positions)}')
for p in positions[:10]:
    # Check available attributes on Position object
    attrs = {}
    for attr in ['side', 'quantity', 'opening_avg_px', 'avg_px_open', 'entry_price', 'realized_pnl', 'unrealized_pnl']:
        if hasattr(p, attr):
            attrs[attr] = getattr(p, attr)
    print(f'  {attrs}')

# Strategy internal stats
print(f'\nSTRATEGY INTERNAL')
print(f'  total_trades: {strategy.total_trades}')
print(f'  wins: {strategy.wins}')
print(f'  losses: {strategy.losses}')
print(f'  total_pnl_pips: {strategy.total_pnl_pips}')
if strategy.total_trades > 0:
    print(f'  win_rate: {strategy.wins/strategy.total_trades*100:.1f}%')

engine.dispose()
