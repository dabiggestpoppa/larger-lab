"""Diagnostic v2: Track order events and position changes in P90 backtest"""
import sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtests")
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")

from run_cerebus_backtest import *
from nautilus_trader.model.enums import OrderStatus
from pathlib import Path
from decimal import Decimal

csv_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSDPRO_M5_2023_2025.csv")
instrument, venue = get_instrument_and_venue("EURUSD.PRO")
bar_type = make_bar_type("EURUSD.PRO", instrument)

bars = load_bars(csv_path, instrument, bar_type)
print(f"Loaded {len(bars)} bars")

# Use first 5000 bars for quick test
bars_small = bars[:5000]
print(f"Using {len(bars_small)} bars for diagnostic")

# Test with lot_size=1 (minimum valid)
for lot_size_str in ["1", "0.01"]:
    lot_size = Decimal(lot_size_str)
    print(f"\n{'='*60}")
    print(f"Testing with lot_size={lot_size}")
    print(f"{'='*60}")

    config = BacktestEngineConfig(
        trader_id=TraderId(f"CEREBUS-P90-DIAG-{lot_size_str}"),
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
        lot_size=lot_size,
    )
    strategy = P90Strategy(config=strat_config)
    engine.add_strategy(strategy=strategy)
    engine.add_data(bars_small)

    engine.run()

    # Strategy internal stats
    print(f"Strategy internal: trades={strategy.total_trades} W={strategy.wins} L={strategy.losses} PnL={strategy.total_pnl:.1f}p")

    result = engine.get_result()
    print(f"Engine: orders={result.total_orders} positions={result.total_positions}")

    # Check all orders
    all_orders = engine.cache.orders()
    print(f"Orders in cache: {len(all_orders)}")
    filled = [o for o in all_orders if o.status == OrderStatus.FILLED]
    rejected = [o for o in all_orders if o.status == OrderStatus.REJECTED]
    canceled = [o for o in all_orders if o.status == OrderStatus.CANCELED]
    print(f"  Filled: {len(filled)}, Rejected: {len(rejected)}, Canceled: {len(canceled)}")

    if filled:
        print(f"  First filled: {filled[0].side} qty={filled[0].quantity} filled_px={filled[0].avg_px}")
    if rejected:
        print(f"  First rejected: {rejected[0].side} qty={rejected[0].quantity} reason={rejected[0].reject_reason}")
    if canceled:
        print(f"  First canceled: {canceled[0].side} qty={canceled[0].quantity}")

    # Check positions
    positions = engine.cache.positions()
    print(f"Positions in cache: {len(positions)}")
    for pos in positions[:5]:
        print(f"  {pos}")

    # Check account balance
    accounts = engine.cache.accounts()
    for acc in accounts:
        bal = acc.balance(USD)
        if bal:
            print(f"  Account balance: {bal}")

    engine.dispose()

print("\nDiagnostic v2 complete.")
