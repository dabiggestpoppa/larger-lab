"""Test Nautilus v1.226 Quantity API compatibility"""
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.enums import TimeInForce as TIF
from decimal import Decimal

# Test Quantity creation with different lot sizes
for lot_str in ['1000', '0.01', '1', '10000']:
    try:
        q = Quantity.from_str(lot_str)
        print(f'Quantity.from_str("{lot_str}") = {q}, precision={q.precision}')
    except Exception as e:
        print(f'Quantity.from_str("{lot_str}") ERROR: {e}')

print()

# Check TimeInForce enum values
print(f'TIF.IOC = {TIF.IOC}, value={TIF.IOC.value}')
print(f'TIF.FOK = {TIF.FOK}, value={TIF.FOK.value}')
print(f'TIF.GTC = {TIF.GTC}, value={TIF.GTC.value}')
print(f'TIF.GTD = {TIF.GTD}, value={TIF.GTD.value}')

print()

# Check how the test instrument works
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.model.identifiers import Venue
inst = TestInstrumentProvider.default_fx_ccy('USD/CHF', venue=Venue('OANDA'))
print(f'Instrument: {inst.id}')
print(f'  size_precision: {inst.size_precision}')
print(f'  size_increment: {inst.size_increment}')
print(f'  min_quantity: {inst.min_quantity}')
print(f'  max_quantity: {inst.max_quantity}')
print(f'  lot_size: {inst.lot_size}')

print()

# Check if Strategy has order_factory and submit_order
from nautilus_trader.trading.strategy import Strategy
methods = [m for m in dir(Strategy) if 'order' in m.lower() or 'submit' in m.lower()]
print(f'Strategy order-related methods: {methods}')
