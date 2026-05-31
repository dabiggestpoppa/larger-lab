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
from nautilus_trader.model.enums import AccountType, OmsType, OrderSide, TimeInForce as TIF
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.objects import Money, Quantity
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.backtest.models import FillModel

csv_path = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\USDCHFPRO_M5_MAD.csv')

instrument = TestInstrumentProvider.default_fx_ccy('USD/CHF', venue=Venue('OANDA'))
bar_type_str = f'{instrument.id}-5-MINUTE-LAST-EXTERNAL'
bar_type = BarType.from_str(bar_type_str)

df = pd.read_csv(csv_path, nrows=500)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
w = BarDataWrangler(bar_type=bar_type, instrument=instrument)
bars = w.process(df)
print(f'Loaded {len(bars)} bars')

config = BacktestEngineConfig(
    trader_id=TraderId('DIAG-001'),
    logging=LoggingConfig(log_level='INFO'),
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

from symmetry_trap_strategy import SymmetryTrapStrategy, SymmetryTrapConfig
strat_config = SymmetryTrapConfig(
    instrument_id=str(instrument.id),
    bar_type=str(bar_type),
    lot_size=Decimal('0.01'),
)
strategy = SymmetryTrapStrategy(config=strat_config)
engine.add_strategy(strategy=strategy)
engine.add_data(bars)

print(f'Engine instrument: {instrument.id}')
print(f'Strategy instrument: {strategy.instrument_id}')
print(f'Match: {strategy.instrument_id == instrument.id}')

engine.run()

orders = engine.cache.orders()
print(f'\nTotal orders: {len(orders)}')
for o in orders[:10]:
    status_name = o.status.name if hasattr(o.status, 'name') else str(o.status)
    print(f'  status={status_name} side={o.side} qty={o.quantity} type={o.order_type} tif={o.time_in_force}')
    if hasattr(o, 'last_event') and o.last_event:
        evt = o.last_event
        print(f'    last_event: {type(evt).__name__}: {evt}')
        for attr in vars(evt):
            if 'reason' in attr.lower() or 'reject' in attr.lower() or 'text' in attr.lower() or 'msg' in attr.lower():
                print(f'    {attr}: {getattr(evt, attr, None)}')

engine.dispose()
