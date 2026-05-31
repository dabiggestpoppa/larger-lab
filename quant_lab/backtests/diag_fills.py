"""Debug: Check order fill status and position tracking in detail"""
import sys
from pathlib import Path
from decimal import Decimal
from collections import Counter

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

# Use 5000 bars for speed
df = pd.read_csv(csv_path, nrows=5000)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
w = BarDataWrangler(bar_type=bar_type, instrument=instrument)
bars = w.process(df)
print(f'Loaded {len(bars)} bars')

config = BacktestEngineConfig(
    trader_id=TraderId('FILL-TEST-001'),
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

filled_orders = [o for o in orders if hasattr(o.status, 'name') and o.status.name == 'FILLED']
filled_count = len(filled_orders)
print(f'\nFILLED orders: {filled_count}')
for o in filled_orders[:5]:
    print(f'  side={o.side} qty={o.quantity} type={o.order_type}')
    if hasattr(o, 'last_event') and o.last_event:
        evt = o.last_event
        print(f'    last_event type: {type(evt).__name__}')
        for attr in ['last_px', 'last_qty', 'price']:
            if hasattr(evt, attr):
                val = getattr(evt, attr)
                if val:
                    print(f'    fill {attr}: {val}')

denied_orders = [o for o in orders if hasattr(o.status, 'name') and o.status.name == 'DENIED']
if denied_orders:
    print(f'\nDENIED orders: {len(denied_orders)}')
    for o in denied_orders[:3]:
        if hasattr(o, 'last_event') and o.last_event:
            reason = getattr(o.last_event, 'reason', None)
            print(f'  reason: {reason}')

# Position analysis
positions = engine.cache.positions()
print(f'\nPOSITIONS in cache: {len(positions)}')
for p in positions[:10]:
    print(f'  side={p.side} qty={p.quantity} opening={p.opening_avg_px} unrealized={p.unrealized_pnl}')

# Strategy internal stats
print(f'\nSTRATEGY INTERNAL STATS')
print(f'  total_trades: {strategy.total_trades}')
print(f'  wins: {strategy.wins}')
print(f'  losses: {strategy.losses}')
print(f'  total_pnl_pips: {strategy.total_pnl_pips}')
if strategy.total_trades > 0:
    print(f'  win_rate: {strategy.wins / strategy.total_trades * 100:.1f}%')

engine.dispose()
