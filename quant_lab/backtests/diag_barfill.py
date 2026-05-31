"""Test: Can Nautilus backtest fill market orders with LAST bars?"""
import sys, os
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
import pandas as pd

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType, Bar
from nautilus_trader.model.enums import AccountType, OmsType, OrderSide, TimeInForce as TIF
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.objects import Money, Quantity
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.backtest.models import FillModel

# Create instrument
instrument = TestInstrumentProvider.default_fx_ccy('USD/CHF', venue=Venue('OANDA'))

# Load bars with default LAST-EXTERNAL bar type
bar_type_last = BarType.from_str(str(instrument.id) + '-5-MINUTE-LAST-EXTERNAL')
print('Bar type (LAST):', bar_type_last)

# Also create a BID bar type
bar_type_bid_str = str(instrument.id) + '-5-MINUTE-BID-EXTERNAL'
bar_type_bid = BarType.from_str(bar_type_bid_str)
print('Bar type (BID):', bar_type_bid)

# Also ASK
bar_type_ask_str = str(instrument.id) + '-5-MINUTE-ASK-EXTERNAL'

# Load 500 bars
csv_path = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\USDCHFPRO_M5_MAD.csv')
df = pd.read_csv(csv_path, nrows=500)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
keep = [c for c in ['open','high','low','close','volume'] if c in df.columns]
df = df[keep]

# Create LAST bars
w_last = BarDataWrangler(bar_type=bar_type_last, instrument=instrument)
bars_last = w_last.process(df)
print('LAST bars:', len(bars_last))

# Create BID bars (use close as bid)
df_bid = df.copy()
df_bid['close'] = df_bid['open']  # bid ~ open for simplicity
w_bid = BarDataWrangler(bar_type=bar_type_bid, instrument=instrument)
bars_bid = w_bid.process(df_bid)
print('BID bars:', len(bars_bid))

# Create a dummy LAST bar set for single-bar test
print('\n=== TEST 1: Market order directly against engine (no strategy) ===')

config = BacktestEngineConfig(
    trader_id=TraderId('BARTEST-001'),
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
engine.add_data(bars_last)

# Manually submit a market order using the cache's order factory
# Actually, let's use the engine's submit_order via a minimal approach
# Since we don't have a strategy, let's test with a strategy but log qty
from nautilus_trader.trading.strategy import Strategy, StrategyConfig
from nautilus_trader.model.data import Bar as BarType_Bar

class QuickTestStrategy(Strategy):
    def __init__(self, config):
        super().__init__(config)
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.bar_type = BarType.from_str(config.bar_type)
        self.submitted = False
        self.order_result = None

    def on_bar(self, bar):
        if not self.submitted:
            self.submitted = True
            qty = Quantity.from_str('1000')
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.BUY,
                quantity=qty,
                time_in_force=TIF.IOC,
            )
            self.log.info('SUBMITTING order qty=' + str(qty))
            self.submit_order(order)
            self.order_result = order

strat_config = StrategyConfig(instrument_id=str(instrument.id), bar_type=str(bar_type_last))
strategy = QuickTestStrategy(config=strat_config)
engine.add_strategy(strategy=strategy)

engine.run()

orders = engine.cache.orders()
print('Orders:', len(orders))
for o in orders:
    st = o.status.name if hasattr(o.status, 'name') else str(o.status)
    print('  status=', st, ' side=', o.side, ' qty=', o.quantity, sep='')
    if hasattr(o, 'events') and o.events:
        for evt in o.events:
            print('    event:', type(evt).__name__, '-', str(evt)[:150])

positions = engine.cache.positions()
print('Positions:', len(positions))

accounts = engine.cache.accounts()
for acc in accounts:
    print('Account:', acc.id if hasattr(acc, 'id') else acc)
    for bal in acc.balances.values() if hasattr(acc, 'balances') else []:
        print('  balance:', bal)

engine.dispose()

# === TEST 2: Try with BID+ASK bars
print('\n=== TEST 2: BID+ASK bars ===')

config2 = BacktestEngineConfig(
    trader_id=TraderId('BARTEST-002'),
    logging=LoggingConfig(log_level='ERROR'),
)
engine2 = BacktestEngine(config=config2)
engine2.add_venue(
    venue=Venue('OANDA'),
    oms_type=OmsType.NETTING,
    account_type=AccountType.MARGIN,
    base_currency=USD,
    starting_balances=[Money(10000, USD)],
    fill_model=FillModel(prob_fill_on_limit=0.95, prob_slippage=0.05),
)
engine2.add_instrument(instrument)

# Create ASK bars
df_ask = df.copy()
bar_type_ask = BarType.from_str(bar_type_ask_str)
w_ask = BarDataWrangler(bar_type=bar_type_ask, instrument=instrument)
bars_ask = w_ask.process(df_ask)
print('ASK bars:', len(bars_ask))

engine2.add_data(bars_bid)
engine2.add_data(bars_ask)

strat_config2 = StrategyConfig(instrument_id=str(instrument.id), bar_type=bar_type_bid_str)
strategy2 = QuickTestStrategy(config=strat_config2)
engine2.add_strategy(strategy2)

engine2.run()

orders2 = engine2.cache.orders()
print('Orders:', len(orders2))
for o in orders2:
    st = o.status.name if hasattr(o.status, 'name') else str(o.status)
    print('  status=', st, ' side=', o.side, ' qty=', o.quantity, sep='')
    if hasattr(o, 'events') and o.events:
        for evt in o.events:
            print('    event:', type(evt).__name__, '-', str(evt)[:150])

positions2 = engine2.cache.positions()
print('Positions:', len(positions2))

engine2.dispose()
