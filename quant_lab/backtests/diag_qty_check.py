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

inst = TestInstrumentProvider.default_fx_ccy('USD/CHF', venue=Venue('OANDA'))
bt_str = str(inst.id) + '-5-MINUTE-LAST-EXTERNAL'
bt = BarType.from_str(bt_str)

csv = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\USDCHFPRO_M5_MAD.csv')
df = pd.read_csv(csv, nrows=5000)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
keep = [c for c in ['open','high','low','close','volume'] if c in df.columns]
w = BarDataWrangler(bar_type=bt, instrument=inst)
bars = w.process(df[keep])
print('Loaded', len(bars), 'bars')

# Monkey-patch to log order submission
_submit_count = [0]
_orig_submit = SymmetryTrapStrategy._submit_entry_order

def _patched_submit(self):
    _submit_count[0] += 1
    n = _submit_count[0]
    print('SUBMIT #' + str(n) + ': lot_size=' + str(self.lot_size) + ' impulse_dir=' + str(self.impulse_direction) + ' state=' + self._strategy_state)
    qty = self.order_factory.market(
        instrument_id=self.instrument_id,
        order_side=__import__('nautilus_trader.model.enums', fromlist=['OrderSide']).OrderSide.BUY if self.impulse_direction == 1 else __import__('nautilus_trader.model.enums', fromlist=['OrderSide']).OrderSide.SELL,
        quantity=__import__('nautilus_trader.model.objects', fromlist=['Quantity']).Quantity.from_str(str(self.lot_size)),
        time_in_force=__import__('nautilus_trader.model.enums', fromlist=['TimeInForce']).TimeInForce.IOC,
        reduce_only=False,
    )
    print('  Created order qty=' + str(qty) + ' type=' + type(qty).__name__)
    _orig_submit(self)

SymmetryTrapStrategy._submit_entry_order = _patched_submit

config = BacktestEngineConfig(
    trader_id=TraderId('QTY-001'),
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

sc = SymmetryTrapConfig(
    instrument_id=str(id),
    bar_type=bt_str,
    lot_size=Decimal('1000'),
)
engine.add_strategy(strategy=SymmetryTrapStrategy(config=sc))
engine.add_data(bars)
engine.run()

orders = engine.cache.orders()
print('\nTotal orders:', len(orders))
status_c = Counter()
qty_c = Counter()
for o in orders:
    st = o.status.name if hasattr(o.status, 'name') else str(o.status)
    status_c[st] += 1
    qty_c[str(o.quantity)] += 1
print('Status dist:', dict(status_c))
print('Qty dist:', dict(qty_c))

engine.dispose()
