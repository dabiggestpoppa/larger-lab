"""Diagnostic v3: Test with different bar types + check why orders don't fill"""
import sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtests")
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")

from run_cerebus_backtest import *
from pathlib import Path
from decimal import Decimal
from nautilus_trader.model.enums import OrderStatus, OmsType
from nautilus_trader.model.objects import Money, Quantity, Price
from nautilus_trader.model.identifiers import Venue, TraderId
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.backtest.models import FillModel

csv_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSDPRO_M5_2023_2025.csv")
instrument, venue_name = get_instrument_and_venue("EURUSD.PRO")

print(f"Instrument: size_increment={instrument.size_increment} lot_size={instrument.lot_size}")
print(f"Price precision: {instrument.price_precision}")

bars = load_bars(csv_path, instrument, BarType.from_str("EUR/USD.OANDA-5-MINUTE-LAST-EXTERNAL"))
bars_small = bars[:200]

# Test different bar type specs
bar_type_strategies = [
    "EUR/USD.OANDA-5-MINUTE-LAST-EXTERNAL",  # current
    "EUR/USD.OANDA-5-MINUTE-LAST-INTERNAL",  # internal agg
]

for bts in bar_type_strategies:
    print(f"\n{'='*60}")
    print(f"BarType: {bts}")

    try:
        bar_type = BarType.from_str(bts)
    except Exception as e:
        print(f"  Invalid: {e}")
        continue

    config = BacktestEngineConfig(
        trader_id=TraderId(f"CEREBUS-TEST"),
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
    engine.add_instrument(instrument)

    strat_config = P90Config(
        instrument_id=str(instrument.id),
        bar_type=str(bar_type),
        lot_size=Decimal("1000"),
    )
    strategy = P90Strategy(config=strat_config)
    engine.add_strategy(strategy=strategy)
    engine.add_data(bars_small)

    engine.run()

    all_orders = engine.cache.orders()
    statuses = {}
    for o in all_orders:
        s = str(o.status)
        statuses[s] = statuses.get(s, 0) + 1
    print(f"  Orders: {len(all_orders)} | Status breakdown: {statuses}")
    print(f"  Strategy: trades={strategy.total_trades} pnl={strategy.total_pnl:.1f}p")
    print(f"  Engine: positions={engine.cache.positions()}")

    engine.dispose()

# Also test: manually place an order to see if fills work at all
print(f"\n{'='*60}")
print("Manual order test (no strategy)")

engine2 = BacktestEngine(config=BacktestEngineConfig(
    trader_id=TraderId("MANUAL-TEST"),
))
engine2.add_venue(
    venue=Venue("OANDA"),
    oms_type=OmsType.NETTING,
    account_type=AccountType.MARGIN,
    base_currency=USD,
    starting_balances=[Money(10000, USD)],
    fill_model=FillModel(prob_fill_on_limit=1.0, prob_slippage=0.0),
)
engine2.add_instrument(instrument)

# Can't manually place without a strategy, but let's check the bar data
print(f"  Data loaded: {len(bars_small)} bars")
if bars_small:
    b = bars_small[0]
    print(f"  Bar: O={b.open} H={b.high} L={b.low} C={b.close} ts={b.ts_event}")

engine2.dispose()
print("\nComplete.")
