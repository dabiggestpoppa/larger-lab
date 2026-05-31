import sys
from pathlib import Path
from decimal import Decimal
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))

import pandas as pd

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USD, CHF
from nautilus_trader.model.data import BarType, Bar, BarSpecification, BarAggregation
from nautilus_trader.model.enums import AccountType, OmsType, AggregationSource, PriceType
from nautilus_trader.model.identifiers import TraderId, Venue, InstrumentId
from nautilus_trader.model.objects import Money, Quantity, Price
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.model.functions import instrument_id_from_str

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

# Create CHF/USD instrument and bars for conversion
chfusd = TestInstrumentProvider.default_fx_ccy('CHF/USD', venue=Venue('OANDA'))
chfusd_bar_type_str = f'{chfusd.id}-5-MINUTE-LAST-EXTERNAL'
chfusd_bar_type = BarType.from_str(chfusd_bar_type_str)
print(f'CHF/USD instrument: {chfusd.id}, bar_type: {chfusd_bar_type}')

# Create inverse bars (CHF/USD = 1/USDCHF)
chf_usd_bars = []
for bar in bars:
    ts = bar.ts_event
    # Invert prices
    inv_open = 1.0 / float(bar.open)
    inv_high = 1.0 / float(bar.low)  # high of USDCHF = low of CHFUSD
    inv_low = 1.0 / float(bar.high)
    inv_close = 1.0 / float(bar.close)
    
    # Create a bar data dict and process through wrangler
    bar_data = {
        'open': round(inv_open, 5),
        'high': round(inv_high, 5),
        'low': round(inv_low, 5),
        'close': round(inv_close, 5),
        'volume': 100,
    }
    chf_usd_bars.append(bar_data)

# Use wrangler for CHF/USD too
chf_df = pd.DataFrame(chf_usd_bars)
# We need timestamps - use the same indices
chf_df.index = df.index[:len(chf_df)]
chf_w = BarDataWrangler(bar_type=chfusd_bar_type, instrument=chfusd)
chf_bars_processed = chf_w.process(chf_df)
print(f'Created {len(chf_bars_processed)} CHF/USD bars')

config = BacktestEngineConfig(
    trader_id=TraderId('FULL-001'),
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
engine.add_instrument(chfusd)

lot_size = Decimal('1000')
print(f'Using lot_size: {lot_size}')

strat_config = SymmetryTrapConfig(
    instrument_id=str(instrument.id),
    bar_type=str(bar_type),
    lot_size=lot_size,
)
strategy = SymmetryTrapStrategy(config=strat_config)
engine.add_strategy(strategy=strategy)
engine.add_data(bars)
engine.add_data(chf_bars_processed)

print('Running full backtest...')
engine.run()

orders = engine.cache.orders()
print(f'\n=== RESULTS ===')
print(f'Total orders: {len(orders)}')

status_counts = Counter()
for o in orders:
    s = o.status.name if hasattr(o.status, 'name') else str(o.status)
    status_counts[s] += 1
print('Status distribution:')
for status, count in sorted(status_counts.items()):
    print(f'  {status}: {count}')

positions = engine.cache.positions()
print(f'Positions in cache: {len(positions)}')

result = engine.get_result()
print(f'\nEngine results:')
print(f'  Orders: {result.total_orders}')
print(f'  Positions: {result.total_positions}')

pnl_stats = result.stats_pnls.get('USD', {})
print(f'  PnL stats: {pnl_stats}')

# Check account
accounts = engine.cache.accounts()
for acc in accounts:
    print(f'\nAccount: {acc}')
    print(f'  Balances: {acc.balances}')

engine.dispose()
