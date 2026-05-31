import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
import pandas as pd

from nautilus_trader.model.data import BarType
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.persistence.wranglers import BarDataWrangler

inst = TestInstrumentProvider.default_fx_ccy('USD/CHF', venue=Venue('OANDA'))
bt_str = str(inst.id) + '-5-MINUTE-LAST-EXTERNAL'
bt = BarType.from_str(bt_str)

csv = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\USDCHFPRO_M5_MAD.csv')
df = pd.read_csv(csv, nrows=5)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
keep = [c for c in ['open','high','low','close','volume'] if c in df.columns]
w = BarDataWrangler(bar_type=bt, instrument=inst)
bars = w.process(df[keep])
print('Created', len(bars), 'bars')

b = bars[0]
print('Type:', type(b))
print('Methods:', [m for m in dir(b) if not m.startswith('_') and 'bar' in m.lower()])
print()
print('bar_type:', b.bar_type if hasattr(b, 'bar_type') else 'NO bar_type attr')
print('bar_spec:', b.bar_spec if hasattr(b, 'bar_spec') else 'NO bar_spec')
# check type
from nautilus_trader.model.data import Bar as NautilusBar
print('Is Bar:', isinstance(b, NautilusBar))
# Check bar_type property
try:
    result = b.bar_type()
    print('bar_type():', result)
except Exception as e:
    print('bar_type() error:', e)
    # maybe it's a property not method
    try:
        result = b.bar_type
        print('bar_type (prop):', result)
    except Exception as e2:
        print('bar_type (prop) error:', e2)
