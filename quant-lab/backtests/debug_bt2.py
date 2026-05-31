"""Debug: check order fills in detail."""
import sys
from pathlib import Path
from decimal import Decimal
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

sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
from symmetry_trap_strategy import SymmetryTrapStrategy, SymmetryTrapConfig

instrument = TestInstrumentProvider.default_fx_ccy('EUR/USD', venue=Venue('OANDA'))
bar_type_str = str(instrument.id) + '-5-MINUTE-LAST-EXTERNAL'
bar_type = BarType.from_str(bar_type_str)

csv_path = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSDPRO_M5_2023_2025.csv')
df = pd.read_csv(csv_path)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
keep_cols = ['open','high','low','close','volume']
df = df[keep_cols]
for c in keep_cols:
    df[c] = pd.to_numeric(df[c], errors='coerce').astype('float64')

wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)
bars = wrangler.process(df)
print('Loaded %d bars' % len(bars))

config = BacktestEngineConfig(
    trader_id=TraderId('CEREBUS-DBG3-001'),
    logging=LoggingConfig(log_level='WARNING'),
)
engine = BacktestEngine(config=config)
engine.add_venue(
    venue=Venue('OANDA'),
    oms_type=OmsType.NETTING,
    account_type=AccountType.MARGIN,
    base_currency=USD,
    starting_balances=[Money(10000, USD)],
    fill_model=FillModel(prob_fill_on_limit=1.0, prob_slippage=0.0),
)
engine.add_instrument(instrument)

strat_config = SymmetryTrapConfig(
    instrument_id=str(instrument.id),
    bar_type=str(bar_type),
    lot_size=Decimal('1000'),
)
strategy = SymmetryTrapStrategy(config=strat_config)
engine.add_strategy(strategy=strategy)
engine.add_data(bars)

print('Running...')
engine.run()
print('Done.')

result = engine.get_result()
print('total_orders=%d total_positions=%d total_events=%d' % (
    result.total_orders, result.total_positions, result.total_events))
print('strat.total_trades=%d wins=%d losses=%d pnl_pips=%.1f' % (
    strategy.total_trades, strategy.wins, strategy.losses, strategy.total_pnl_pips))

# Inspect orders
all_orders = strategy.cache.orders()
print('orders in cache: %d' % len(all_orders))
denied = 0
filled = 0
rejected = 0
for o in all_orders:
    s = str(o.status)
    if 'DENIED' in s:
        denied += 1
    elif 'FILLED' in s:
        filled += 1
    elif 'REJECTED' in s:
        rejected += 1
print('DENIED=%d FILLED=%d REJECTED=%d' % (denied, filled, rejected))

# Show first denied order reason
for o in all_orders[:3]:
    if hasattr(o, 'reason') and o.reason:
        print('  reason for %s: %s' % (o.client_order_id, o.reason))

# Check positions
all_pos = strategy.cache.positions()
print('positions: %d' % len(all_pos))

engine.dispose()
