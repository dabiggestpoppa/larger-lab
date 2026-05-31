"""
CEREBUS FX v4.0 — Unified Nautilus Backtest Runner
===================================================
Runs Nautilus Trader backtests for Symmetry Trap and P90 strategies.
Compatible with Nautilus Trader v1.221+

Usage:
  python run_cerebus_backtest.py --strategy symmetry_trap --symbol EURUSD.PRO --csv data/EURUSDPRO_M5.csv
  python run_cerebus_backtest.py --strategy p90 --symbol USDCHF.PRO --csv data/USDCHFPRO_M5.csv
  python run_cerebus_backtest.py --strategy p90 --symbol EURUSD.PRO --bars 5000

Target benchmarks:
  Symmetry Trap (EURUSD 4Y): ~91% WR, PF 23, MaxDD ~15p
  P90 CASCADE (USDCHF 3.5Y): ~83% WR, PF 2.8
"""
import sys, os, argparse, json
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from decimal import Decimal

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.config import BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType, BarAggregation as BA
from nautilus_trader.model.enums import AccountType, OmsType, AggregationSource
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.backtest.models import FillModel

import pandas as pd
import pytz

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.symmetry_trap_strategy import SymmetryTrapStrategy, SymmetryTrapConfig
from strategies.p90_strategy import P90Strategy, P90Config

DATA_DIR = Path(__file__).parent.parent / 'data'
REPORTS_DIR = Path(__file__).parent.parent / 'reports'
REPORTS_DIR.mkdir(exist_ok=True)

EST = pytz.timezone('US/Eastern')


def get_instrument_and_venue(symbol: str):
    """Create Nautilus instrument and venue from broker symbol."""
    symbol_map = {
        'EURUSD.PRO': ('EUR/USD', 'OANDA'),
        'USDCHF.PRO': ('USD/CHF', 'OANDA'),
        'GBPUSD.PRO': ('GBP/USD', 'OANDA'),
        'USDJPY.PRO': ('USD/JPY', 'OANDA'),
    }
    pair, venue_name = symbol_map.get(symbol, (symbol[:3] + '/' + symbol[3:6], 'OANDA'))
    instrument = TestInstrumentProvider.default_fx_ccy(pair, venue=Venue(venue_name))
    return instrument, venue_name


def make_bar_type(symbol: str, instrument) -> BarType:
    """Create bar type from string (Nautilus v1.221 API)."""
    bar_type_str = f"{instrument.id}-5-MINUTE-LAST-EXTERNAL"
    bar_type = BarType.from_str(bar_type_str)
    return bar_type


def load_bars(csv_path: Path, instrument, bar_type) -> list:
    """Load M5 bars from CSV into Nautilus Bar objects."""
    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found!")
        return []

    df = pd.read_csv(csv_path)

    # Handle various CSV formats
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    elif 'date' in df.columns:
        if 'time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))
        else:
            df['timestamp'] = pd.to_datetime(df['date'])
    elif '<DATE>' in df.columns:
        # MT5 tab-delimited format
        if '<TIME>' in df.columns:
            df['timestamp'] = pd.to_datetime(df['<DATE>'] + ' ' + df['<TIME>'])
        else:
            df['timestamp'] = pd.to_datetime(df['<DATE>'])
        df.rename(columns={
            '<OPEN>': 'open', '<HIGH>': 'high', '<LOW>': 'low',
            '<CLOSE>': 'close', '<TICKVOL>': 'volume',
            '<VOL>': 'volume', '<SPREAD>': 'spread',
        }, inplace=True)
    elif 'Open' in df.columns:
        df.rename(columns={
            'Open': 'open', 'High': 'high', 'Low': 'low',
            'Close': 'close', 'Volume': 'volume',
        }, inplace=True)
        if 'Date' in df.columns:
            if 'Time' in df.columns:
                df['timestamp'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
            else:
                df['timestamp'] = pd.to_datetime(df['Date'])

    # Set timestamp as index for Nautilus
    if 'timestamp' in df.columns:
        df = df.set_index('timestamp')
    df.index = pd.to_datetime(df.index, utc=True)
    # Keep only the columns Nautilus wrangler expects
    keep_cols = [c for c in ['open', 'high', 'low', 'close', 'volume'] if c in df.columns]
    df = df[keep_cols]
    # Convert all to float64 for Cython buffer compatibility
    for c in keep_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce').astype('float64')
    wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)
    bars = wrangler.process(df)
    print(f"  Loaded {len(bars)} bars from {csv_path.name}")
    return bars


def run_backtest(strategy_name: str, symbol: str, csv_path: Path,
                 lot_size: Decimal = Decimal("0.01"), bars_limit: int = 0):
    """Run a backtest for the given strategy + symbol."""

    print("=" * 70)
    print(f"  CEREBUS FX v4.0 — Nautilus Backtest")
    print(f"  Strategy: {strategy_name.upper()} | Symbol: {symbol}")
    print(f"  Time: {datetime.now(EST).strftime('%Y-%m-%d %H:%M:%S EST')}")
    print("=" * 70)

    # Setup instrument + bar type
    instrument, venue_name = get_instrument_and_venue(symbol)
    bar_type = make_bar_type(symbol, instrument)

    # Load data
    bars = load_bars(csv_path, instrument, bar_type)
    if not bars:
        print("No bars loaded. Aborting.")
        return None

    if bars_limit > 0:
        bars = bars[:bars_limit]
        print(f"  Limited to {bars_limit} bars")

    print(f"  Bars: {len(bars)}")

    # Configure engine
    config = BacktestEngineConfig(
        trader_id=TraderId(f"CEREBUS-{strategy_name.upper()}-001"),
        logging=LoggingConfig(log_level="INFO"),
    )

    engine = BacktestEngine(config=config)
    engine.add_venue(
        venue=Venue("OANDA"),
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money(10000, USD)],
        fill_model=FillModel(
            prob_fill_on_limit=0.95,
            prob_slippage=0.05,
        ),
    )
    engine.add_instrument(instrument)

    # Create strategy
    if strategy_name == 'symmetry_trap':
        strat_config = SymmetryTrapConfig(
            instrument_id=str(instrument.id),
            bar_type=str(bar_type),
            lot_size=lot_size,
        )
        strategy = SymmetryTrapStrategy(config=strat_config)
    elif strategy_name == 'p90':
        strat_config = P90Config(
            instrument_id=str(instrument.id),
            bar_type=str(bar_type),
            lot_size=lot_size,
        )
        strategy = P90Strategy(config=strat_config)
    else:
        print(f"Unknown strategy: {strategy_name}")
        return None

    engine.add_strategy(strategy=strategy)
    engine.add_data(bars)

    # Run
    print(f"\n  Running backtest...")
    engine.run()

    # Results
    result = engine.get_result()

    # Extract PnL stats
    pnl_stats = result.stats_pnls.get('USD', {})
    total_pnl = pnl_stats.get('total', 0.0)
    win_rate = pnl_stats.get('win_rate', 0.0) if pnl_stats else 0.0
    max_dd = pnl_stats.get('max_drawdown', 0.0) if pnl_stats else 0.0
    returns_pct = result.stats_returns.get('equity', 0.0)

    print(f"\n{'=' * 70}")
    print(f"  BACKTEST RESULTS — {strategy_name.upper()} / {symbol}")
    print(f"{'=' * 70}")
    print(f"  Orders:     {result.total_orders}")
    print(f"  Positions:  {result.total_positions}")
    print(f"  PnL (USD):  {total_pnl:.2f}")
    print(f"  Win Rate:   {win_rate:.1f}%")
    print(f"  Max DD:     {max_dd:.2%}")
    print(f"  Returns:    {returns_pct:.2%}")
    print(f"  Stats:      {pnl_stats}")
    print(f"{'=' * 70}")

    # Save report
    timestamp = datetime.now(EST).strftime('%Y%m%d_%H%M%S')
    report_name = f"NAUTILUS_{strategy_name.upper()}_{symbol}_{timestamp}.json"
    report_path = REPORTS_DIR / report_name

    report = {
        "strategy": strategy_name,
        "symbol": symbol,
        "bars": len(bars),
        "timestamp": timestamp,
        "total_orders": result.total_orders,
        "total_positions": result.total_positions,
        "pnl_usd": total_pnl,
        "win_rate": win_rate,
        "max_drawdown": max_dd,
        "returns": returns_pct,
        "elapsed_s": result.elapsed_time,
    }

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Report: {report_path}")

    engine.dispose()
    return report


def main():
    parser = argparse.ArgumentParser(description='CEREBUS FX Nautilus Backtest Runner')
    parser.add_argument('--strategy', choices=['symmetry_trap', 'p90'], required=True)
    parser.add_argument('--symbol', default='EURUSD.PRO')
    parser.add_argument('--csv', help='Path to CSV data file')
    parser.add_argument('--lot-size', type=float, default=0.01)
    parser.add_argument('--bars', type=int, default=0, help='Limit bars (0=all)')
    args = parser.parse_args()

    # Auto-find CSV if not specified
    csv_path = Path(args.csv) if args.csv else None
    if csv_path is None:
        search_dir = DATA_DIR
        base = args.symbol.replace('.', '').replace('.PRO', '')
        candidates = [
            search_dir / f"{base}_M5.csv",
            search_dir / f"{base}_M5_2023_2026.csv",
            search_dir / f"{base}_M5_MAD.csv",
            search_dir / f"{base}_2022_2026.csv",
            search_dir / f"{base}_dt.csv",
            search_dir / f"{args.symbol}_M5.csv",
            search_dir / f"{args.symbol}_M5_2023_2026.csv",
            search_dir / f"{args.symbol}_M5_MAD.csv",
        ]
        for c in candidates:
            if c.exists() and c.stat().st_size > 1000:
                csv_path = c
                break

    if csv_path is None or not csv_path.exists():
        print(f"ERROR: No data file found for {args.symbol}")
        print(f"Searched: {[str(c) for c in candidates]}")
        return

    result = run_backtest(
        strategy_name=args.strategy,
        symbol=args.symbol,
        csv_path=csv_path,
        lot_size=Decimal(str(args.lot_size)),
        bars_limit=args.bars,
    )

    if result:
        print("\n[+] Backtest complete.")
    else:
        print("\n[-] Backtest failed.")


if __name__ == '__main__':
    main()
