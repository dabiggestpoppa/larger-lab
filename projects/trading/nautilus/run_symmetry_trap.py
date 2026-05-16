"""
Symmetry Trap Backtest Runner — CEREBUS FX Atomic Market Structure
===================================================================
Loads CSV data (forex.com / OX Securities format) and runs the
Symmetry Trap strategy through the Nautilus Trader backtest engine.

Usage:
    python -m nautilus.run_symmetry_trap --instrument EURUSD --timeframe M5 --count 5000
    python -m nautilus.run_symmetry_trap --instrument EURUSD --timeframe M5 --count 5000 --tier T1
"""
import argparse
import os
import sys
from datetime import datetime
from decimal import Decimal

from nautilus_trader.backtest.config import BacktestEngineConfig
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import Bar, BarSpecification, BarType
from nautilus_trader.model.enums import AccountType, AggregationSource, BarAggregation, OmsType
from nautilus_trader.model.identifiers import InstrumentId, TraderId, Venue
from nautilus_trader.model.objects import Money, Price, Quantity

from .config import DATA_DIR, DOWNLOADS_DIR, INITIAL_CAPITAL, PIP_VALUES, ASIAN_SESSION_START_UTC, ASIAN_SESSION_END_UTC
from .data_loader import discover_files, load_csv_as_nautilus_bars, _parse_csv
from .strategies.symmetry_trap import SymmetryTrapConfig, SymmetryTrapStrategy


def run_symmetry_trap_backtest(
    instrument="EURUSD",
    timeframe="M5",
    count=5000,
    tier="T2",
    initial_capital=100000.0,
    prob_fill_on_limit=0.2,
    prob_slippage=0.5,
):
    """
    Run the Symmetry Trap (Deep Mean Rebalancing) backtest.
    """
    print(f"\n{'='*65}")
    print(f"CERBERUS SYMMETRY TRAP - BACKTEST")
    print(f"{'='*65}")
    print(f"  Instrument:  {instrument}")
    print(f"  Timeframe:   {timeframe}")
    print(f"  Bars:        {count}")
    print(f"  Tier:        {tier}")
    print(f"  Capital:     ${initial_capital:,.2f}")
    print(f"{'='*65}\n")

    # Step 1: Discover and load CSV data
    files = discover_files(DOWNLOADS_DIR)

    csv_filepath = None
    for sym, path in files.items():
        base = sym.replace("/", "").replace(".", "")
        if base.upper() == instrument.upper():
            csv_filepath = path
            break

    if csv_filepath is None:
        for sym, path in files.items():
            if instrument.upper() in sym.upper():
                csv_filepath = path
                break

    if csv_filepath is None:
        print(f"ERROR: No data file found for {instrument}")
        print("Available files:")
        for sym, path in files.items():
            print(f"  - {sym}: {os.path.basename(path)}")
        return None

    print(f"Data file: {csv_filepath}")

    # Parse CSV and limit to requested count
    df = _parse_csv(csv_filepath)
    if df.empty:
        print("ERROR: No data parsed from file")
        return None

    if len(df) > count:
        df = df.tail(count)

    print(f"Data: {len(df)} bars | {df.index[0]} -> {df.index[-1]}")

    # Step 2: Determine bar specification
    timeframe_map = {
        "M1": (1, BarAggregation.MINUTE),
        "M5": (5, BarAggregation.MINUTE),
        "M15": (15, BarAggregation.MINUTE),
        "M30": (30, BarAggregation.MINUTE),
        "H1": (1, BarAggregation.HOUR),
        "H4": (4, BarAggregation.HOUR),
        "D": (1, BarAggregation.DAY),
    }

    step, agg = timeframe_map.get(timeframe, (5, BarAggregation.MINUTE))
    bar_spec = BarSpecification(step, agg, AggregationSource.EXTERNAL)

    SIM = Venue("SIM")
    instrument_id_str = f"{instrument.replace('/', '_')}.SIM"
    try:
        instrument_id = InstrumentId.from_str(instrument_id_str)
    except Exception:
        instrument_id = InstrumentId.from_str(f"{instrument}.SIM")

    bar_type = BarType(instrument_id, bar_spec, AggregationSource.EXTERNAL)

    # Step 3: Convert CSV rows to Nautilus Bar objects
    bars = []
    for timestamp, row in df.iterrows():
        try:
            prec = 2 if row["close"] > 1000 else 5
            bar = Bar(
                bar_type=bar_type,
                open=Price(float(row["open"]), prec),
                high=Price(float(row["high"]), prec),
                low=Price(float(row["low"]), prec),
                close=Price(float(row["close"]), prec),
                volume=Quantity(int(row.get("tick_volume", 1000)), 0),
                ts_event=int(timestamp.timestamp() * 1e9),
                ts_init=int(timestamp.timestamp() * 1e9),
            )
            bars.append(bar)
        except Exception:
            pass

    print(f"Converted {len(bars)} Nautilus bars")

    if not bars:
        print("ERROR: No valid bars to backtest")
        return None

    # Step 4: Set up backtest engine
    print("\nSetting up Nautilus Trader engine...")

    config = BacktestEngineConfig(
        trader_id=TraderId("CERBERUS-001"),
    )

    engine = BacktestEngine(config=config)

    fill_model = FillModel(
        prob_fill_on_limit=prob_fill_on_limit,
        prob_slippage=prob_slippage,
        random_seed=42,
    )

    engine.add_venue(
        venue=SIM,
        oms_type=OmsType.HEDGING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money(str(initial_capital), USD)],
        fill_model=fill_model,
    )

    # Add instrument
    from nautilus_trader.test_kit.providers import TestInstrumentProvider
    try:
        instrument_obj = TestInstrumentProvider.default_fx_ccy(
            instrument.replace("_", "/"), SIM
        )
    except Exception:
        from nautilus_trader.model.instruments import Instrument
        from nautilus_trader.model.objects import Price as P, Quantity as Q
        from decimal import Decimal as D
        instrument_obj = Instrument(
            instrument_id=InstrumentId.from_str(f"{instrument}.SIM"),
            asset_class=Instrument.AssetClass.INDEX,
            quote_currency=USD,
            is_inverse=False,
            price_precision=2,
            size_precision=0,
            min_price_increment=P("0.01", 2),
            min_quantity_increment=Q("1", 0),
            max_quantity=Q("1000000", 0),
            min_quantity=Q("1", 0),
            margin_init=D("0.01"),
            margin_maint=D("0.005"),
            maker_fee=D("0.0002"),
            taker_fee=D("0.0005"),
            ts_event=0,
            ts_init=0,
        )

    engine.add_instrument(instrument_obj)
    print(f"Added instrument: {instrument_obj.id}")

    # Step 5: Load data into engine
    print("\nLoading data into engine...")
    engine.add_data(bars)
    print(f"Loaded {len(bars)} bars")

    # Step 6: Add Symmetry Trap strategy
    print(f"\nAdding Symmetry Trap strategy (tier={tier})...")

    strategy_config = SymmetryTrapConfig(
        instrument_id=instrument_obj.id,
        bar_type=bar_type,
        initial_capital=Decimal(str(initial_capital)),
        tier=tier,
    )

    strategy = SymmetryTrapStrategy(config=strategy_config)
    engine.add_strategy(strategy)

    # Step 7: Run backtest
    print(f"\nRunning backtest...")
    start_time = datetime.now()

    engine.run()

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"  Backtest completed in {elapsed:.2f}s")

    # Step 8: Generate report
    print(f"\nRESULTS:")
    print(f"{'='*65}")

    try:
        account_report = engine.trader.generate_account_report(SIM)
        if account_report is not None:
            print(f"\nAccount Report:")
            print(f"  {account_report.to_string()}")

        fills_report = engine.trader.generate_order_fills_report()
        if fills_report is not None:
            print(f"\nOrder Fills:")
            print(f"  Total fills: {len(fills_report)}")

        positions_report = engine.trader.generate_positions_report()
        if positions_report is not None:
            print(f"\nPositions:")
            print(f"  {positions_report.to_string()}")

    except Exception as e:
        print(f"  Warning: Could not generate full report: {e}")
        import traceback
        traceback.print_exc()

    engine.reset()
    engine.dispose()

    print(f"\n{'='*65}")
    print(f"Backtest complete!")
    print(f"{'='*65}\n")

    return {
        "instrument": instrument,
        "timeframe": timeframe,
        "bars": len(bars),
        "strategy": f"Symmetry Trap ({tier})",
        "elapsed_seconds": elapsed,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cerberus Symmetry Trap Backtest")
    parser.add_argument("--instrument", type=str, default="EURUSD",
                        help="Instrument (e.g., EURUSD, GBPUSD, XAUUSD, US500)")
    parser.add_argument("--timeframe", type=str, default="M5",
                        help="Timeframe (M1, M5, M15, M30, H1, H4, D)")
    parser.add_argument("--count", type=int, default=5000,
                        help="Number of bars to use")
    parser.add_argument("--tier", type=str, default="T2",
                        choices=["T1", "T2", "T3"],
                        help="Asian Range tier")
    parser.add_argument("--capital", type=float, default=100000,
                        help="Initial capital in USD")

    args = parser.parse_args()

    result = run_symmetry_trap_backtest(
        instrument=args.instrument,
        timeframe=args.timeframe,
        count=args.count,
        tier=args.tier,
        initial_capital=args.capital,
    )

    if result is None:
        sys.exit(1)