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

df = pd.read_csv(csv_path)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
w = BarDataWrangler(bar_type=bar_type, instrument=instrument)
bars = w.process(df)
print(f'Loaded {len(bars)} bars')

config = BacktestEngineConfig(
    trader_id=TraderId('FULL-TEST-001'),
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

# Use lot_size=1 (Nautilus v1.226 FX requires integer lots)
lot_size = Decimal(str(max(Decimal('0.01'), instrument.size_increment)))
print(f'Using lot_size: {lot_size}')

strat_config = SymmetryTrapConfig(
    instrument_id=str(instrument.id),
    bar_type=str(bar_type),
    lot_size=lot_size,
)
strategy = SymmetryTrapStrategy(config=strat_config)
engine.add_strategy(strategy=strategy)
engine.add_data(bars)

print('Running full backtest...')
engine.run()

orders = engine.cache.orders()
print(f'\nTotal orders: {len(orders)}')

status_counts = Counter()
for o in orders:
    s = o.status.name if hasattr(o.status, 'name') else str(o.status)
    status_counts[s] += 1
print('Status distribution:')
for status, count in sorted(status_counts.items()):
    print(f'  {status}: {count}')

# Show first few denied/filled
for o in orders[:5]:
    s = o.status.name if hasattr(o.status, 'name') else str(o.status)
    print(f'  Order: status={s} side={o.side} qty={o.quantity} type={o.order_type} tif={o.time_in_force}')
    if hasattr(o, 'last_event') and o.last_event:
        evt = o.last_event
        reason = getattr(evt, 'reason', None)
        if reason:
            print(f'    reason: {reason}')

positions = engine.cache.positions()
print(f'\nPositions: {len(positions)}')
for p in positions[:5]:
    print(f'  Position: qty={p.quantity} entry={p.opening_avg_px} side={p.side}')

result = engine.get_result()
print(f'\nResult orders: {result.total_orders}')
print(f'Result positions: {result.total_positions}')

pnl_stats = result.stats_pnls.get('USD', {})
print(f'PnL stats: {pnl_stats}')

engine.dispose()
