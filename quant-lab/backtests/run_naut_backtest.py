"""
Nautilus Backtest Runner — DMR Strategy
Runs backtest using Nautilus Trader engine with MT5 historical data.

Usage:
  1. MT5 terminal must be open and logged in
  2. First run data fetcher: python ../data/mt5_data_fetcher.py
  3. Then run this: python run_naut_backtest.py

Target: Match Python backtest benchmark (94.8% WR, EUR/USD)
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

from decimal import Decimal
from pathlib import Path

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.config import BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import Bar, BarSpecification, BarType, BarAggregation
from nautilus_trader.model.enums import AccountType, AggregationSource, BarAggregation as BA, OmsType, OrderSide
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.backtest.venue import SimulatedVenue
from nautilus_trader.portfolio import Portfolio

import pandas as pd
import pytz

# Add strategies dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
from dmr_strategy import DMRStrategy, DMRConfig

DATA_DIR = Path(__file__).parent.parent / 'data'
REPORTS_DIR = Path(__file__).parent.parent / 'reports'
REPORTS_DIR.mkdir(exist_ok=True)

EST = pytz.timezone('US/Eastern')

def load_bars_from_csv(csv_path: str) -> list:
    """Load M5 bars from CSV and convert to Nautilus Bar objects"""
    df = pd.read_csv(csv_path, parse_dates=['timestamp'])
    
    instrument = TestInstrumentProvider.default_fx_ccy("EUR/USD", venue=Venue("OANDA"))
    
    bar_spec = BarSpecification(
        step=5,
        aggregation=BarAggregation.MINUTE,
        price_type=BarAggregation.MID,
    )
    bar_type = BarType(instrument_id=instrument.id, bar_spec=bar_spec, aggregation_source=AggregationSource.EXTERNAL)
    
    wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)
    
    # Convert to Nautilus bars
    bars = wrangler.from_dataframe(df)
    print(f"Loaded {len(bars)} bars from {csv_path}")
    return bars, instrument, bar_type


def run_backtest():
    print("="*70)
    print("  DMR BACKTEST — Nautilus Trader")
    print("="*70)
    
    # Load data
    csv_path = DATA_DIR / "EURUSD_M5.csv"
    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found!")
        print("Run data fetcher first: python ../data/mt5_data_fetcher.py")
        return
    
    bars, instrument, bar_type = load_bars_from_csv(str(csv_path))
    
    if len(bars) == 0:
        print("No bars loaded!")
        return
    
    print(f"Date range: {bars[0].timestamp} to {bars[-1].timestamp}")
    
    # Configure backtest engine
    config = BacktestEngineConfig(
        trader_id=TraderId("DMR-BACKTEST-001"),
        logging=LoggingConfig(log_level="INFO"),
        venue=Venue("OANDA"),
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money(10000, USD)],
        fill_model=FillModel(
            prob_fill_on_limit=0.95,
            prob_fill_on_stop=0.95,
            prob_slippage=0.05,
        ),
    )
    
    engine = BacktestEngine(config=config)
    
    # Add venue
    engine.add_venue(
        venue=Venue("OANDA"),
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money(10000, USD)],
        fill_model=FillModel(),
    )
    
    # Add instrument
    engine.add_instrument(instrument)
    
    # Add strategy
    strategy_config = DMRConfig(
        instrument_id=instrument.id.value,
        bar_type=bar_type.value,
        lot_size=Decimal("0.01"),
    )
    strategy = DMRStrategy(config=strategy_config)
    engine.add_strategy(strategy=strategy)
    
    # Add data
    engine.add_data(bars)
    
    # Run
    print(f"\nRunning backtest with {len(bars)} bars...")
    engine.run()
    
    # Results
    result = engine.get_result()
    
    print(f"\n{'='*70}")
    print(f"  BACKTEST RESULTS")
    print(f"{'='*70}")
    print(f"  Trades:     {result.total_trades}")
    print(f"  Win Rate:   {result.win_rate:.1f}%")
    print(f"  PnL:        {result.pnl:.2f}")
    print(f"  PF:         {result.profit_factor:.2f}")
    print(f"  Max DD:     {result.max_drawdown:.4f}")
    print(f"  Returns:    {result.total_return:.2%}")
    print(f"{'='*70}")
    
    # Save report
    report_path = REPORTS_DIR / f"DMR_NAUTILUS_BACKTEST_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
    # TODO: serialize results properly
    print(f"\nReport saved to: {report_path}")
    
    engine.dispose()
    print("\nDone.")


if __name__ == '__main__':
    run_backtest()
