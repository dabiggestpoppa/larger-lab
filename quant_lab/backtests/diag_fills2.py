import sys, os
from pathlib import Path
from decimal import Decimal
from collections import Counter

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
bar_type_str = str(instrument.id) + '-5-MINUTE-LAST-EXTERNAL'
bar_type = BarType.from_str(bar_type_str)

df = pd.read_csv(csv_path, nrows=5000)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
w = BarDataWrangler(bar_type=bar_type, instrument=instrument)
bars = w.process(df)
print('Loaded', len(bars), 'bars')

config = BacktestEngineConfig(
    trader_id=TraderId('FILL2-001'),
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
    bar_type=bar_type_str,
    lot_size=Decimal('1000'),
)
strategy = SymmetryTrapStrategy(config=strat_config)
engine.add_strategy(strategy=strategy)
engine.add_data(bars)
engine.run()

orders = engine.cache.orders()
print('\nORDERS:', len(orders), 'total')

status_counts = Counter()
for o in orders:
    s = o.status.name if hasattr(o.status, 'name') else str(o.status)
    status_counts[s] += 1
print('Status distribution:')
for status, count in sorted(status_counts.items()):
    print('  ', status, ':', count)

filled = [o for o in orders if hasattr(o.status, 'name') and o.status.name == 'FILLED']
print('\nFILLED:', len(filled))
for o in filled[:3]:
    evts = o.events if hasattr(o, 'events') else []
    fp = None
    for e in evts:
        if type(e).__name__ == 'OrderFilled':
            fp = getattr(e, 'last_px', None)
    print('  side=', o.side, ' qty=', o.quantity, ' fill_price=', fp, sep='')

denied = [o for o in orders if hasattr(o.status, 'name') and o.status.name == 'DENIED']
if denied:
    print('\nDENIED:', len(denied))
    for o in denied[:3]:
        r = '?'
        if hasattr(o, 'last_event') and o.last_event:
            r = getattr(o.last_event, 'reason', '?')
        print('  reason=', r, sep='')

positions = engine.cache.positions()
print('\nPOSITIONS:', len(positions))
pos_attrs = [a for a in dir(positions[0]) if not a.startswith('_')] if positions else []
print('Position attributes:', pos_attrs[:20])

for p in positions[:5]:
    d = {}
    for a in ['side', 'quantity', 'avg_px_open', 'opening_price', 'realized_pnl', 'unrealized_pnl']:
        if hasattr(p, a):
            d[a] = getattr(p, a)
    print(' ', d)

print('\nSTRATEGY INTERNAL')
print('  total_trades:', strategy.total_trades)
print('  wins:', strategy.wins)
print('  losses:', strategy.losses)
print('  total_pnl_pips:', strategy.total_pnl_pips)
if strategy.total_trades > 0:
    print('  win_rate:', round(strategy.wins / strategy.total_trades * 100, 1), '%')

engine.dispose()
