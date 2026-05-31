import sys
from pathlib import Path
from decimal import Decimal

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
print(f'Bar type: {bar_type}')

df = pd.read_csv(csv_path, nrows=20000)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
w = BarDataWrangler(bar_type=bar_type, instrument=instrument)
bars = w.process(df)
print(f'Loaded {len(bars)} bars')
print(f'First bar: {bars[0]}')
print(f'Last bar: {bars[-1]}')

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

print('Running backtest...')
engine.run()
result = engine.get_result()

print(f'\n=== RESULTS ===')
print(f'Orders: {result.total_orders}')
print(f'Positions: {result.total_positions}')

orders = engine.cache.orders()
print(f'Cached orders: {len(orders)}')
filled = [o for o in orders if 'FILLED' in str(o.status)]
rejected = [o for o in orders if 'REJECTED' in str(o.status)]
expired = [o for o in orders if 'EXPIRED' in str(o.status)]
submitted = [o for o in orders if 'SUBMITTED' in str(o.status)]
cancelled = [o for o in orders if 'CANCELED' in str(o.status) or 'CANCELLED' in str(o.status)]
print(f'FILLED: {len(filled)}, REJECTED: {len(rejected)}, EXPIRED: {len(expired)}, SUBMITTED: {len(submitted)}, CANCELLED: {len(cancelled)}')

if filled:
    o = filled[0]
    print(f'First filled: status={o.status} side={o.side} qty={o.quantity} price={o.avg_price if hasattr(o, "avg_price") else "N/A"}')
if rejected:
    o = rejected[0]
    print(f'First rejected: status={o.status}')
    for attr in ['reject_reason', 'reason', 'last_event']:
        if hasattr(o, attr):
            print(f'  {attr}: {getattr(o, attr)}')
    print(f'  repr: {o}')

# Check trades 
try:
    trades = engine.cache.trades()
    print(f'Trades: {len(trades)}')
    for t in trades[:3]:
        print(f'  Trade: {t}')
except Exception as e:
    print(f'Trades error: {e}')

engine.dispose()
