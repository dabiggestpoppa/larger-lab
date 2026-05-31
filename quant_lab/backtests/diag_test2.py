import sys
from pathlib import Path
from decimal import Decimal
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))

import pandas as pd

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.config import BacktestEngineConfig
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

df = pd.read_csv(csv_path, nrows=20000)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
w = BarDataWrangler(bar_type=bar_type, instrument=instrument)
bars = w.process(df)
print(f'Loaded {len(bars)} bars')

config = BacktestEngineConfig(
    trader_id=TraderId('CEREBUS-TEST-001'),
    logging=LoggingConfig(log_level='ERROR'),
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

strat_config = SymmetryTrapConfig(
    instrument_id=str(instrument.id),
    bar_type=str(bar_type),
    lot_size=Decimal('0.01'),
)
strategy = SymmetryTrapStrategy(config=strat_config)
engine.add_strategy(strategy=strategy)
engine.add_data(bars)

print('Running...')
engine.run()

orders = engine.cache.orders()
print(f'\nTotal cached orders: {len(orders)}')

# Count all statuses
status_counts = Counter()
for o in orders:
    status_counts[str(o.status)] += 1
print('Status distribution:')
for status, count in sorted(status_counts.items()):
    print(f'  {status}: {count}')

# Show details of first few
print(f'\nFirst 5 orders:')
for o in orders[:5]:
    print(f'  id={o.id} status={o.status} side={o.side} qty={o.quantity} instrument={o.instrument_id}')
    print(f'    type={o.order_type} tif={o.time_in_force}')
    if hasattr(o, 'last_event') and o.last_event:
        print(f'    last_event={o.last_event}')
    if hasattr(o, 'reject_reason'):
        print(f'    reject_reason={o.reject_reason}')

# Also check positions  
positions = engine.cache.positions()
print(f'\nPositions: {len(positions)}')
for p in positions[:5]:
    print(f'  {p}')

engine.dispose()
