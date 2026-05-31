import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
import pandas as pd

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import TraderId, Venue, InstrumentId
from nautilus_trader.model.objects import Money
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.trading.strategy import Strategy, StrategyConfig

inst = TestInstrumentProvider.default_fx_ccy('USD/CHF', venue=Venue('OANDA'))
bt_str = str(inst.id) + '-5-MINUTE-LAST-EXTERNAL'
bt = BarType.from_str(bt_str)
print('Expected bar_type:', bt)

csv = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\USDCHFPRO_M5_MAD.csv')
df = pd.read_csv(csv, nrows=10)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
keep = [c for c in ['open','high','low','close','volume'] if c in df.columns]
w = BarDataWrangler(bar_type=bt, instrument=inst)
bars = w.process(df[keep])

print('First 3 bars bar_type:')
for b in bars[:3]:
    abt = b.bar_type()
    print('  bar_type:', abt, '| spec:', abt.spec(), '| inst:', abt.inst_id, '| match:', abt == bt)

class DebugConfig(StrategyConfig, frozen=True):
    instrument_id: str = str(inst.id)
    bar_type: str = bt_str

class DebugStrategy(Strategy):
    def __init__(self, config: DebugConfig):
        super().__init__(config)
        self._count = 0
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self._bt = BarType.from_str(config.bar_type)
        print('Strategy bar_type:', self._bt)
        print('  spec:', self._bt.spec())

    def on_bar(self, bar):
        self._count += 1
        if self._count <= 3:
            print('on_bar #', self._count, ': bar_type=', bar.bar_type(), ' ts=', bar.ts_event, sep='')

    def on_stop(self):
        print('on_stop: total bars received =', self._count)

config = BacktestEngineConfig(
    trader_id=TraderId('DEBUG-001'),
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
engine.add_strategy(strategy=DebugStrategy(config=DebugConfig()))
engine.add_data(bars)
engine.run()
engine.dispose()
