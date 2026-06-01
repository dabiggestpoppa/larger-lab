"""
CEREBUS Nautilus Backtest Runner — FIXED VERSION
==================================================
Loads per-asset configs from asset_configs.py for correct pip divisors,
tier configs, and P90 thresholds.

Usage:
  python naut_crypto_fixed2.py --strategy symmetry_trap --symbol BTCUSD
  python naut_crypto_fixed2.py --strategy p90 --symbol ETHUSD
"""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab')
sys.path.insert(0, 'quant-lab/configs')
sys.path.insert(0, 'quant-lab/strategies')
sys.path.insert(0, 'quant-lab/backtests')

import argparse
import json
from datetime import datetime
from pathlib import Path
from decimal import Decimal

import pandas as pd
import pytz

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.config import BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType, OmsType, AggregationSource
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.persistence.wranglers import BarDataWrangler

from strategies.symmetry_trap_strategy import SymmetryTrapStrategy, SymmetryTrapConfig
from strategies.p90_strategy import P90Strategy, P90Config
from quant_lab.configs.asset_configs import ASSET_CONFIGS

EST = pytz.timezone('US/Eastern')
DATA_DIR = Path('quant-lab/data')
REPORTS_DIR = Path('quant-lab/reports')
REPORTS_DIR.mkdir(exist_ok=True)


def get_instrument_and_venue(symbol: str):
    """Create Nautilus instrument — supports both FX and crypto."""
    symbol_map = {
        # FX pairs
        'EURUSD.PRO': ('EUR/USD', 'OANDA'),
        'EURUSD': ('EUR/USD', 'OANDA'),
        'USDCHF.PRO': ('USD/CHF', 'OANDA'),
        'USDCHF': ('USD/CHF', 'OANDA'),
        'GBPUSD.PRO': ('GBP/USD', 'OANDA'),
        'GBPUSD': ('GBP/USD', 'OANDA'),
        'USDJPY.PRO': ('USD/JPY', 'OANDA'),
        'USDJPY': ('USD/JPY', 'OANDA'),
        'AUDUSD': ('AUD/USD', 'OANDA'),
        'NZDUSD': ('NZD/USD', 'OANDA'),
        'GBPJPY': ('GBP/JPY', 'OANDA'),
        'GBPCHF': ('GBP/CHF', 'OANDA'),
        'GBPAUD': ('GBP/AUD', 'OANDA'),
        'GBPNZD': ('GBP/NZD', 'OANDA'),
        'CHFJPY': ('CHF/JPY', 'OANDA'),
        # Metals
        'XAUUSD': ('XAU/USD', 'OANDA'),
        'XAGUSD': ('XAG/USD', 'OANDA'),
        # Crypto
        'BTCUSD': ('BTC/USD', 'OANDA'),
        'ETHUSD': ('ETH/USD', 'OANDA'),
    }
    if symbol in symbol_map:
        pair, venue_name = symbol_map[symbol]
    elif len(symbol) == 6:
        pair = f"{symbol[:3]}/{symbol[3:]}"
        venue_name = 'OANDA'
    else:
        pair = symbol
        venue_name = 'OANDA'

    # Create instrument — use appropriate provider for each asset type
    try:
        instrument = TestInstrumentProvider.default_fx_ccy(pair, venue=Venue(venue_name))
    except (ValueError, Exception):
        # Fallback for indices and other non-standard symbols (US500, DE30, etc.)
        instrument = TestInstrumentProvider.equity(symbol=pair, venue=venue_name)
    return instrument, venue_name


def make_bar_type(symbol: str, instrument) -> BarType:
    bar_type_str = f"{instrument.id}-5-MINUTE-LAST-EXTERNAL"
    return BarType.from_str(bar_type_str)


def load_bars(csv_path: Path, instrument, bar_type) -> list:
    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found!")
        return []
    df = pd.read_csv(csv_path)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    elif 'date' in df.columns:
        if 'time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))
        else:
            df['timestamp'] = pd.to_datetime(df['date'])
    
    if 'timestamp' in df.columns:
        df = df.set_index('timestamp')
    df.index = pd.to_datetime(df.index, utc=True)
    keep_cols = [c for c in ['open', 'high', 'low', 'close', 'volume'] if c in df.columns]
    df = df[keep_cols]
    for c in keep_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce').astype('float64')
    wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)
    bars = wrangler.process(df)
    print(f"  Loaded {len(bars)} bars from {csv_path.name}")
    return bars


def find_csv(symbol: str) -> Path:
    """Find CSV file for a symbol."""
    candidates = [
        DATA_DIR / f"{symbol}_M5.csv",
        DATA_DIR / f"{symbol.replace('.PRO', '')}_M5.csv",
        DATA_DIR / f"{symbol}_MAD.csv",
        DATA_DIR / f"{symbol}_dt.csv",
    ]
    for c in candidates:
        if c.exists() and c.stat().st_size > 1000:
            return c
    # Try PRO versions
    for c in [
        DATA_DIR / f"{symbol}.PRO_M5.csv",
        DATA_DIR / f"{symbol}PRO_M5.csv",
    ]:
        if c.exists() and c.stat().st_size > 1000:
            return c
    return None


def run_backtest(strategy_name: str, symbol: str, csv_path: Path = None, bars_limit: int = 0):
    """Run Nautilus backtest with correct per-asset config."""
    
    print("=" * 70)
    print(f"  CEREBUS Nautilus Backtest — {strategy_name.upper()} / {symbol}")
    print(f"  Time: {datetime.now(EST).strftime('%Y-%m-%d %H:%M:%S EST')}")
    print("=" * 70)

    # ── Load asset config ──
    asset_cfg = ASSET_CONFIGS.get(symbol, ASSET_CONFIGS.get('EURUSD'))
    print(f"  Asset config: pip_value={asset_cfg['pip_value']}, K={asset_cfg['k_factor']}")
    print(f"  Tiers: T1(ar_max={asset_cfg['tiers']['T1']['ar_max']}, au={asset_cfg['tiers']['T1']['au']})")
    print(f"          T2(ar_max={asset_cfg['tiers']['T2']['ar_max']}, au={asset_cfg['tiers']['T2']['au']})")
    print(f"          T3(ar_max={asset_cfg['tiers']['T3']['ar_max']}, au={asset_cfg['tiers']['T3']['au']})")

    # ── Setup instrument ──
    instrument, venue_name = get_instrument_and_venue(symbol)
    bar_type = make_bar_type(symbol, instrument)

    # ── Load data ──
    if csv_path is None:
        csv_path = find_csv(symbol)
    if csv_path is None:
        print(f"ERROR: No CSV found for {symbol}")
        return None
    
    bars = load_bars(csv_path, instrument, bar_type)
    if not bars:
        print("No bars loaded. Aborting.")
        return None
    if bars_limit > 0:
        bars = bars[:bars_limit]
        print(f"  Limited to {bars_limit} bars")

    # ── Configure engine ──
    config = BacktestEngineConfig(
        trader_id=TraderId(f"CEREBUS-{strategy_name.upper()}-001"),
        logging=LoggingConfig(log_level="ERROR"),
    )
    engine = BacktestEngine(config=config)
    engine.add_venue(
        venue=Venue("OANDA"),
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money(10000, USD)],
        fill_model=FillModel(prob_fill_on_limit=0.95, prob_slippage=0.05),
    )
    engine.add_instrument(instrument)

    # ── Create strategy with correct config ──
    lot_size = Decimal("1000")
    if strategy_name == 'symmetry_trap':
        # Build tier config override from asset_configs
        tier_override = {}
        for tier_name in ['T1', 'T2', 'T3']:
            t = asset_cfg['tiers'][tier_name]
            tier_override[tier_name] = {
                'ar_max': t['ar_max'],
                'au': t['au'],
                'trigger': t['trigger']
            }
        
        strat_config = SymmetryTrapConfig(
            instrument_id=str(instrument.id),
            bar_type=str(bar_type),
            lot_size=lot_size,
            tier_config_override=tier_override,
        )
        strategy = SymmetryTrapStrategy(config=strat_config)
    elif strategy_name == 'p90':
        strat_config = P90Config(
            instrument_id=str(instrument.id),
            bar_type=str(bar_type),
            lot_size=lot_size,
        )
        # P90 strategy reads SYMBOL_P90 dict which we already patched
        strategy = P90Strategy(config=strat_config)
    else:
        print(f"Unknown strategy: {strategy_name}")
        return None

    engine.add_strategy(strategy=strategy)
    engine.add_data(bars)

    # ── Run ──
    print(f"\n  Running backtest...")
    engine.run()

    # ── Results ──
    result = engine.get_result()
    try:
        strat_trades = strategy.total_trades
        strat_wins = strategy.wins
        strat_losses = strategy.losses
        strat_pnl = strategy.total_pnl if hasattr(strategy, 'total_pnl') else strategy.total_pnl_pips
        strat_wr = (strat_wins / strat_trades * 100.0) if strat_trades > 0 else 0.0
    except:
        strat_trades = strat_wins = strat_losses = 0
        strat_pnl = strat_wr = 0.0

    print(f"\n{'=' * 70}")
    print(f"  RESULTS: {strategy_name.upper()} / {symbol}")
    print(f"  Strategy Trades:  {strat_trades}")
    print(f"  Strategy W/L:     {strat_wins}/{strat_losses}")
    print(f"  Strategy WR:      {strat_wr:.1f}%")
    print(f"  Strategy PnL:     {strat_pnl:.1f} pips")
    print(f"  Engine Orders:    {result.total_orders}")
    print(f"{'=' * 70}")

    # ── Save report ──
    timestamp = datetime.now(EST).strftime('%Y%m%d_%H%M%S')
    report_name = f"NAUTILUS_{strategy_name.upper()}_{symbol}_{timestamp}.json"
    report_path = REPORTS_DIR / report_name
    report = {
        "strategy": strategy_name,
        "symbol": symbol,
        "bars": len(bars),
        "timestamp": timestamp,
        "engine_orders": result.total_orders,
        "engine_positions": result.total_positions,
        "strategy_trades": strat_trades,
        "strategy_wins": strat_wins,
        "strategy_losses": strat_losses,
        "strategy_win_rate": strat_wr,
        "strategy_pnl_pips": strat_pnl,
        "asset_cfg_pip": asset_cfg['pip_value'],
        "asset_cfg_k": asset_cfg['k_factor'],
    }
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"  Report: {report_path}")

    engine.dispose()
    return report


def main():
    parser = argparse.ArgumentParser(description='CEREBUS Nautilus Backtest (fixed configs)')
    parser.add_argument('--strategy', choices=['symmetry_trap', 'p90'], required=True)
    parser.add_argument('--symbol', required=True)
    parser.add_argument('--csv')
    parser.add_argument('--bars', type=int, default=0)
    args = parser.parse_args()

    csv_path = Path(args.csv) if args.csv else None
    result = run_backtest(args.strategy, args.symbol, csv_path, args.bars)
    
    if result:
        print("\n[+] Backtest complete.")
    else:
        print("\n[-] Backtest failed.")


if __name__ == '__main__':
    main()
