import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
import pandas as pd

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType, OmsType, OrderSide, TimeInForce
from nautilus_trader.model.identifiers import TraderId, Venue, InstrumentId
from nautilus_trader.model.objects import Money, Quantity
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.trading.strategy import Strategy, StrategyConfig

inst = TestInstrumentProvider.default_fx_ccy('USD/CHF', venue=Venue('OANDA'))
bt_str = str(inst.id) + '-5-MINUTE-LAST-EXTERNAL'
bt = BarType.from_str(bt_str)

csv = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\USDCHFPRO_M5_MAD.csv')
df = pd.read_csv(csv, nrows=100)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
keep = [c for c in ['open','high','low','close','volume'] if c in df.columns]
w = BarDataWrangler(bar_type=bt, instrument=inst)
bars = w.process(df[keep])
print('Bars:', len(bars))

class SingleOrderConfig(StrategyConfig, frozen=True):
    instrument_id: str = str(inst.id)
    bar_type: str = bt_str

class SingleOrderStrategy(Strategy):
    def __init__(self, config: SingleOrderConfig):
        super().__init__(config)
        self._done = False
        self.instrument_id = InstrumentId.from_str(config.instrument_id)

    def on_bar(self, bar):
        if not self._done:
            self._done = True
            qty = Quantity.from_str('1000')
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.BUY,
                quantity=qty,
                time_in_force=TimeInForce.GTC,
            )
            print('Submitting GTC market order, qty=', qty, sep='')
            self.submit_order(order)

config = BacktestEngineConfig(
    trader_id=TraderId('SIMPLE-001'),
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
engine.add_instrument(inst)

sc = SingleOrderConfig()
engine.add_strategy(strategy=SingleOrderStrategy(config=sc))
engine.add_data(bars)
engine.run()

orders = engine.cache.orders()
print('Orders:', len(orders))
for o in orders:
    st = o.status.name if hasattr(o.status, 'name') else str(o.status)
    print('  status=', st, ' qty=', o.quantity, ' side=', o.side, sep='')
    if hasattr(o, 'events') and o.events:
        for e in o.events:
            print('   ', type(e).__name__, ':', str(e)[:200])

positions = engine.cache.positions()
print('Positions:', len(positions))
for p in positions:
    print('  side=', p.side, ' qty=', p.quantity, ' avg_px=', p.avg_px_open, sep='')

engine.dispose()
