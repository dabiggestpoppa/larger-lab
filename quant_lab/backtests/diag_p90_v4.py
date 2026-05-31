"""
Diagnostic v4: Deep dive into why Nautilus orders don't fill.
Key insight: orders exist but 0 are FILLED. Check order status enum values.
"""
import sys, json
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtests")
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")

from nautilus_trader.model.enums import OrderStatus, OrderType, TimeInForce, OmsType
from nautilus_trader.model.objects import Money, Quantity, Price
from nautilus_trader.model.identifiers import Venue, TraderId, InstrumentId
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.objects import Currency, Amount
from nautilus_trader.core import nautilus_common
import pandas as pd
from pathlib import Path
from decimal import Decimal

csv_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSDPRO_M5_2023_2025.csv")

# Setup
inst, venue_name = get_instrument_and_venue("EURUSD.PRO")
bar_type_base = make_bar_type("EURUSD.PRO", inst)
bars = load_bars(csv_path, inst, bar_type_base)

print(f"Instrument: {inst}")
print(f"  size_increment={inst.size_increment}, lot_size={inst.lot_size}, size_precision={inst.size_precision}")
print(f"  price_precision={inst.price_precision}, price_increment={inst.price_increment}")

bars_small = bars[:200]

# Run backtest
config = BacktestEngineConfig(
    trader_id=TraderId("CEREBUS-DEBUG"),
    logging=LoggingConfig(log_level="ERROR"),
)

engine = BacktestEngine(config=config)
engine.add_venue(
    venue=Venue("OANDA"),
    oms_type=OmsType.NETTING,
    account_type=AccountType.MARGIN,
    base_currency=USD,
    starting_balances=[Money(10000, USD)],
    fill_model=FillModel(
        prob_fill_on_limit=1.0,
        prob_slippage=0.0,
    ),
)
engine.add_instrument(inst)

strat_config = P90Config(
    instrument_id=str(inst.id),
    bar_type=str(bar_type_base),
    lot_size=Decimal("1000"),
)
strategy = P90Strategy(config=strat_config)
engine.add_strategy(strategy=strategy)
engine.add_data(bars_small)

engine.run()

# List ALL order statuses
all_orders = engine.cache.orders()
print(f"\nTotal orders: {len(all_orders)}")
for o in all_orders[:10]:
    print(f"  Order: id={o.client_order_id} side={o.side} qty={o.quantity} "
          f"type={o.order_type} tif={o.time_in_force} status={o.status} "
          f"avg_px={o.avg_px} filled_qty={o.filled_qty}")
    print(f"    instrument_id={o.instrument_id}")
    # Check for reject reason
    if hasattr(o, 'reject_reason') and o.reject_reason:
        print(f"    reject_reason={o.reject_reason}")

# Check order events
print("\nAll statuses:")
for s in OrderStatus:
    matching = [o for o in all_orders if o.status == s]
    if matching:
        print(f"  {s.name}: {len(matching)}")

# Check the strategy internal stats
print(f"\nStrategy: trades={strategy.total_trades} pnl={strategy.total_pnl:.1f}p")

# Check positions
positions_all = engine.cache.positions()
positions_open = engine.cache.positions_open()
positions_closed = engine.cache.positions_closed()
print(f"\nPositions: all={len(positions_all)} open={len(positions_open)} closed={len(positions_closed)}")

# Check account
for acc in engine.cache.accounts():
    for bal in acc.balances().values():
        print(f"  Balance: {bal}")

engine.dispose()
print("\nDone.")
