"""
Main backtest runner for Quant Lab.
Fetches Oanda data → runs Nautilus backtest → generates report.

Usage:
    python -m nautilus.run_backtest --instrument EUR_USD --granularity D --count 1000
    python -m nautilus.run_backtest --instrument GBP_USD --granularity H1 --count 5000 --strategy ema_cross
"""
import argparse
import sys
from datetime import datetime
from decimal import Decimal

from nautilus_trader.backtest.config import BacktestEngineConfig
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.objects import Money

from .config import INITIAL_CAPITAL, PAPER_TRADING
from .oanda_adapter import fetch_candles, save_to_csv, SYMBOL_MAP


def run_ema_cross_backtest(
    instrument: str = "EUR_USD",
    granularity: str = "D",
    count: int = 1000,
    fast_ema: int = 10,
    slow_ema: int = 20,
    save_data: bool = True,
):
    """
    Run EMA Cross backtest with Oanda data.

    This mirrors the Pine Script EMA Cross strategy for cross-validation.
    """
    print(f"\n{'='*60}")
    print(f"🧪 QUANT LAB BACKTEST")
    print(f"{'='*60}")
    print(f"  Instrument:  {instrument}")
    print(f"  Granularity: {granularity}")
    print(f"  Bars:        {count}")
    print(f"  Strategy:    EMA Cross ({fast_ema}/{slow_ema})")
    print(f"  Capital:     ${INITIAL_CAPITAL:,.2f}")
    print(f"  Mode:        {'PAPER' if PAPER_TRADING else 'LIVE'}")
    print(f"{'='*60}\n")

    # Step 1: Fetch data from Oanda
    print("📡 Fetching data from Oanda...")
    oanda_instrument = SYMBOL_MAP.get(instrument, instrument.replace("/", "_"))

    try:
        df = fetch_candles(oanda_instrument, granularity, count)
        if df.empty:
            print("❌ No data fetched. Check Oanda API key in .env")
            return None
        print(f"  ✅ Fetched {len(df)} candles")
        print(f"  Date range: {df.index[0]} to {df.index[-1]}")
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None

    # Step 2: Save data
    if save_data:
        filepath = save_to_csv(df, instrument, granularity)
        print(f"  💾 Data saved to {filepath}")

    # Step 3: Set up Nautilus backtest engine
    print("\n⚙️  Setting up Nautilus Trader engine...")

    config = BacktestEngineConfig(
        trader_id=TraderId("QUANT-LAB-001"),
    )

    engine = BacktestEngine(config=config)

    # Add venue
    SIM = Venue("SIM")
    fill_model = FillModel(
        prob_fill_on_limit=0.2,
        prob_slippage=0.5,
        random_seed=42,
    )

    engine.add_venue(
        venue=SIM,
        oms_type=OmsType.HEDGING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money(str(INITIAL_CAPITAL), USD)],
        fill_model=fill_model,
    )

    # Add instrument
    from nautilus_trader.test_kit.providers import TestInstrumentProvider
    instrument_obj = TestInstrumentProvider.default_fx_ccy(instrument, SIM)
    engine.add_instrument(instrument_obj)
    print(f"  ✅ Added instrument: {instrument_obj.id}")

    # Step 4: Add data
    print("\n📊 Loading data into engine...")

    from nautilus_trader.model.data import Bar, BarSpecification, BarType
    from nautilus_trader.model.enums import AggregationSource, BarAggregation
    from nautilus_trader.model.objects import Price, Quantity

    # Map granularity to bar spec
    bar_spec_map = {
        "M1": (1, BarAggregation.MINUTE),
        "M5": (5, BarAggregation.MINUTE),
        "M15": (15, BarAggregation.MINUTE),
        "M30": (30, BarAggregation.MINUTE),
        "H1": (1, BarAggregation.HOUR),
        "H4": (4, BarAggregation.HOUR),
        "D": (1, BarAggregation.DAY),
    }

    if granularity in bar_spec_map:
        step, agg = bar_spec_map[granularity]
    else:
        step, agg = 1, BarAggregation.DAY

    bar_spec = BarSpecification(step, agg, AggregationSource.EXTERNAL)
    bar_type = BarType(instrument_obj.id, bar_spec, AggregationSource.EXTERNAL)

    bars_added = 0
    for timestamp, row in df.iterrows():
        try:
            bar = Bar(
                bar_type=bar_type,
                open=Price(str(round(row.get("open", row.get("mid_open", 0)), 5)),
                high=Price(str(round(row.get("high", row.get("mid_high", 0)), 5)),
                low=Price(str(round(row.get("low", row.get("mid_low", 0)), 5)),
                close=Price(str(round(row.get("close", row.get("mid_close", 0)), 5)),
                volume=Quantity(str(int(row.get("volume", 1000))), 0),
                ts_event=int(timestamp.timestamp() * 1e9),
                ts_init=int(timestamp.timestamp() * 1e9),
            )
            engine.add_data(bar)
            bars_added += 1
        except Exception as e:
            pass  # Skip problematic bars

    print(f"  ✅ Loaded {bars_added} bars")

    # Step 5: Add strategy
    print(f"\n🎯 Adding EMA Cross strategy (fast={fast_ema}, slow={slow_ema})...")

    from .strategies.ema_cross import EMACrossStrategy, EMACrossConfig

    strategy_config = EMACrossConfig(
        instrument_id=instrument_obj.id,
        bar_type=str(bar_type),
        fast_ema_period=fast_ema,
        slow_ema_period=slow_ema,
        trade_size=Decimal("100000"),
        close_positions_on_stop=True,
    )

    strategy = EMACrossStrategy(config=strategy_config)
    engine.add_strategy(strategy)

    # Step 6: Run backtest
    print(f"\n🚀 Running backtest...")
    start_time = datetime.now()

    engine.run()

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"  ✅ Backtest completed in {elapsed:.2f}s")

    # Step 7: Generate report
    print(f"\n📈 RESULTS:")
    print(f"{'='*60}")

    try:
        # Account report
        account_report = engine.trader.generate_account_report(SIM)
        if account_report is not None:
            print(f"\n  Account Report:")
            print(f"  {account_report.to_string()}")

        # Order fills report
        fills_report = engine.trader.generate_order_fills_report()
        if fills_report is not None:
            print(f"\n  Order Fills:")
            print(f"  Total fills: {len(fills_report)}")

        # Positions report
        positions_report = engine.trader.generate_positions_report()
        if positions_report is not None:
            print(f"\n  Positions:")
            print(f"  {positions_report.to_string()}")

    except Exception as e:
        print(f"  ⚠️  Could not generate full report: {e}")

    # Cleanup
    engine.reset()
    engine.dispose()

    print(f"\n{'='*60}")
    print(f"✅ Backtest complete!")
    print(f"{'='*60}\n")

    return {
        "instrument": instrument,
        "granularity": granularity,
        "bars": bars_added,
        "strategy": f"EMA Cross ({fast_ema}/{slow_ema})",
        "elapsed_seconds": elapsed,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quant Lab Backtest Runner")
    parser.add_argument("--instrument", type=str, default="EUR/USD", help="Instrument (e.g., EUR/USD)")
    parser.add_argument("--granularity", type=str, default="D", help="Candle granularity")
    parser.add_argument("--count", type=int, default=1000, help="Number of candles")
    parser.add_argument("--fast-ema", type=int, default=10, help="Fast EMA period")
    parser.add_argument("--slow-ema", type=int, default=20, help="Slow EMA period")
    parser.add_argument("--no-save", action="store_true", help="Don't save data to CSV")

    args = parser.parse_args()

    result = run_ema_cross_backtest(
        instrument=args.instrument,
        granularity=args.granularity,
        count=args.count,
        fast_ema=args.fast_ema,
        slow_ema=args.slow_ema,
        save_data=not args.no_save,
    )

    if result is None:
        sys.exit(1)
