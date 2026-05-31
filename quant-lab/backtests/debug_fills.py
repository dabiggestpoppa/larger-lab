"""Debug: dump ALL order statuses and check order details."""
import sys
from pathlib import Path
from decimal import Decimal
from collections import Counter
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

print('Instrument ID: %s' % instrument.id)
print('Bar type: %s' % bar_type)
print('size_precision: %d' % instrument.size_precision)
print('size_increment: %s' % instrument.size_increment)
print('min_quantity: %s' % instrument.min_quantity)

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

config = BacktestEngineConfig(
    trader_id=TraderId('CEREBUS-FILL-001'),
    logging=LoggingConfig(log_level='ERROR'),
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

print('\nRunning backtest...')
engine.run()
print('Done.\n')

# --- Dump all order statuses ---
all_orders = strategy.cache.orders()
print('=== ORDER STATUSES (total: %d) ===' % len(all_orders))

status_counts = Counter()
for o in all_orders:
    status_counts[o.status] += 1

for status, count in status_counts.most_common():
    print('  %s: %d' % (status, count))

# Show first 3 orders in detail
print('\n=== FIRST 5 ORDERS DETAIL ===')
for o in all_orders[:5]:
    print('---')
    print('  client_order_id: %s' % o.client_order_id)
    print('  status: %s' % o.status)
    print('  side: %s' % o.side)
    print('  type: %s' % o.order_type)
    print('  quantity: %s' % o.quantity)
    print('  filled_qty: ' + str(o.filled_qty))
    print('  avg_px: ' + str(getattr(o, 'avg_px', 'N/A')))
    if hasattr(o, 'last_trade_id') and o.last_trade_id:
        print('  last_trade_id: %s' % o.last_trade_id)

# --- Check fills ---
print('\n=== FILLS ===')
fills = strategy.cache.orders(instrument_id=instrument.id)
fill_count = 0
for o in fills:
    if o.filled_qty and int(o.filled_qty) > 0:
        fill_count += 1
        if fill_count <= 5:
            print('  FILLED: %s side=%s qty=%s filled=%s avg_px=%s' % (
                o.client_order_id, o.side, o.quantity, o.filled_qty, getattr(o, 'avg_px', 'N/A')))
print('Total orders with fills: %d' % fill_count)

# --- Check positions ---
all_positions = strategy.cache.positions()
print('\n=== POSITIONS (total: %d) ===' % len(all_positions))
for p in all_positions[:5]:
    print('  %s' % p)

# --- Result object ---
result = engine.get_result()
print('\n=== RESULT ===')
print('total_orders: %d' % result.total_orders)
print('total_positions: %d' % result.total_positions)

# Try order fills report if available
if hasattr(result, 'fills'):
    print('fills: %d' % len(result.fills))

# Check realized Pnl from positions
realized_pnl_total = 0.0
for p in all_positions:
    if p.realized_pnl is not None:
        realized_pnl_total += float(p.realized_pnl)
print('Total realized PnL from positions: %.2f' % realized_pnl_total)

# Strategy stats
total_trades = strategy.total_trades
wins = strategy.wins
losses = strategy.losses
pnl_pips = strategy.total_pnl_pips
win_rate = (wins / total_trades * 100.0) if total_trades > 0 else 0.0
print('\n=== STRATEGY INTERNAL STATS ===')
print('trades=%d wins=%d losses=%d WR=%.1f%% pnl_pips=%.1f' % (
    total_trades, wins, losses, win_rate, pnl_pips))

engine.dispose()
