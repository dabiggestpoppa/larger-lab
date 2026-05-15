"""
Nautilus Trader backtesting engine setup.
Supports Oanda data for FX, indices, and commodities.
"""
import os
from pathlib import Path

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.config import LoggingConfig, RiskEngineConfig
from nautilus_trader.core.nautilus_pyo3 import InstrumentProviderConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import TraderId, StrategyId, InstrumentId
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.test_kit.providers import TestInstrumentProvider

from .config import DATA_DIR, INITIAL_CAPITAL, PAPER_TRADING


def create_backtest_engine(
    data_dir: str = DATA_DIR,
    initial_capital: float = INITIAL_CAPITAL,
) -> BacktestEngine:
    """Create and configure a Nautilus Trader backtest engine."""

    engine_config = BacktestEngineConfig(
        trader_id=TraderId("QUANT-LAB-001"),
        logging=LoggingConfig(
            log_level="INFO",
            log_colors=True,
        ),
        risk_engine=RiskEngineConfig(
            bypass=True,  # Bypass risk checks for backtesting
        ),
        data_engine=None,  # Uses default
        run_engine=None,  # Uses default
    )

    engine = BacktestEngine(config=engine_config)

    # Add venue (simulated for backtesting)
    # For FX backtesting, we use a simulated FX venue
    from nautilus_trader.adapters.sandbox.config import SandboxExecutionConfig
    from nautilus_trader.model.identifiers import Venue

    # Set initial capital
    engine.add_account(
        account_type=AccountType.CASH,
        base_currency=USD,
        balance=Money(initial_capital, USD),
    )

    return engine


def load_fx_instruments():
    """Load common FX instruments for backtesting."""
    instruments = [
        TestInstrumentProvider.default_fx_ccy("AUD/USD"),
        TestInstrumentProvider.default_fx_ccy("EUR/USD"),
        TestInstrumentProvider.default_fx_ccy("GBP/USD"),
        TestInstrumentProvider.default_fx_ccy("USD/JPY"),
        TestInstrumentProvider.default_fx_ccy("USD/CHF"),
        TestInstrumentProvider.default_fx_ccy("USD/CAD"),
        TestInstrumentProvider.default_fx_ccy("NZD/USD"),
        TestInstrumentProvider.default_fx_ccy("EUR/GBP"),
        TestInstrumentProvider.default_fx_ccy("EUR/JPY"),
        TestInstrumentProvider.default_fx_ccy("GBP/JPY"),
    ]
    return instruments


def load_commodity_instruments():
    """Load commodity instruments (XAU/USD, XAG/USD, etc.)."""
    instruments = [
        TestInstrumentProvider.default_fx_ccy("XAU/USD"),  # Gold
        TestInstrumentProvider.default_fx_ccy("XAG/USD"),  # Silver
    ]
    return instruments


def run_backtest(
    strategy,
    instruments: list,
    bar_type: str = "1-MINUTE",
    start_date: str = None,
    end_date: str = None,
    data_dir: str = DATA_DIR,
):
    """
    Run a backtest with the given strategy and instruments.

    Args:
        strategy: Nautilus Trader strategy instance
        instruments: List of instruments to trade
        bar_type: Bar granularity (e.g., "1-MINUTE", "5-MINUTE", "1-HOUR", "1-DAY")
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        data_dir: Directory containing bar data
    """
    engine = create_backtest_engine(data_dir=data_dir)

    # Add instruments
    for instrument in instruments:
        engine.add_instrument(instrument)

    # Add strategy
    engine.add_strategy(strategy)

    # Load data from catalog if available
    catalog_path = Path(data_dir) / "nautilus_catalog"
    if catalog_path.exists():
        catalog = ParquetDataCatalog(catalog_path)
        for instrument in instruments:
            instrument_id = instrument.id
            bar_type_obj = BarType.from_str(f"{instrument_id}-{bar_type}-LAST-EXTERNAL")
            try:
                bars = catalog.bars(bar_types=[bar_type_obj])
                for bar in bars:
                    engine.add_data(bar)
            except Exception as e:
                print(f"  ⚠️  No data for {instrument_id}: {e}")

    # Run the backtest
    print(f"🚀 Running backtest...")
    print(f"   Instruments: {[str(i.id) for i in instruments]}")
    print(f"   Bar type: {bar_type}")
    print(f"   Period: {start_date} to {end_date}")

    engine.run()

    # Print results
    print(f"\n📊 Backtest Results:")
    print(f"   Portfolio: {engine.portfolio}")
    result = engine.get_result()
    print(f"   P&L: {result}")

    engine.dispose()
    return result
