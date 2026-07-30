"""
Nautilus Backtest Runner for Symmetry Trap
===========================================
Runs Symmetry Trap strategy through Nautilus Trader backtest engine
for cross-validation against Python/CSV engine.
"""

from __future__ import annotations

import sys
from pathlib import Path
from decimal import Decimal

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.config import BacktestEngineConfig
from nautilus_trader.config import LoggingConfig, RiskEngineConfig, CacheConfig, DataEngineConfig, ExecEngineConfig, PortfolioConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.objects import Price, Quantity, Money, Currency
from nautilus_trader.model.enums import OmsType, AccountType
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.backtest.models.fee import FixedFeeModel

from strategies.symmetry_trap_nautilus import (
    SymmetryTrapStrategy,
    SymmetryTrapConfig,
)


def load_csv_to_nautilus_bars(csv_path: str, instrument_id: str, bar_type: BarType) -> list[Bar]:
    """Load M5 CSV data into Nautilus Bar objects."""
    import pandas as pd
    
    df = pd.read_csv(csv_path)
    
    # Ensure timestamp column
    if 'timestamp' in df.columns:
        df['ts_event'] = pd.to_datetime(df['timestamp'])
    elif 'time' in df.columns:
        df['ts_event'] = pd.to_datetime(df['time'], unit='s')
    else:
        raise ValueError("No timestamp column found")
    
    df = df.sort_values('ts_event')
    
    bars = []
    for _, row in df.iterrows():
        bar = Bar(
            bar_type=bar_type,
            open=Price.from_str(str(row['open'])),
            high=Price.from_str(str(row['high'])),
            low=Price.from_str(str(row['low'])),
            close=Price.from_str(str(row['close'])),
            volume=Quantity.from_str(str(row.get('tick_volume', 1))),
            ts_event=int(row['ts_event'].timestamp() * 1e9),
            ts_init=int(row['ts_event'].timestamp() * 1e9),
        )
        bars.append(bar)
    
    return bars


def run_nautilus_backtest(
    csv_path: str,
    symbol: str,
    pip_size: float,
    tier_config: dict,
) -> dict:
    """Run Symmetry Trap backtest in Nautilus."""
    
    # Instrument setup
    instrument_id = InstrumentId.from_str(f"{symbol}.SIM")
    bar_type = BarType.from_str(f"{instrument_id}-5-MINUTE-LAST-EXTERNAL")
    
    # Load data
    print(f"Loading data from {csv_path}...")
    bars = load_csv_to_nautilus_bars(csv_path, instrument_id, bar_type)
    print(f"Loaded {len(bars)} bars")
    
    # Strategy config
    strategy_config = SymmetryTrapConfig(
        instrument_id=str(instrument_id),
        bar_type=bar_type,
        tier_config=tier_config,
        lot_size=Decimal("0.01"),
    )
    
    # Backtest engine config - Nautilus 1.221 API
    engine_config = BacktestEngineConfig(
        trader_id="BACKTEST-001",
        logging=LoggingConfig(log_level="INFO"),
        risk_engine=RiskEngineConfig(),
        cache=CacheConfig(),
        data_engine=DataEngineConfig(),
        exec_engine=ExecEngineConfig(),
        portfolio=PortfolioConfig(),
    )
    
    # Create engine
    engine = BacktestEngine(config=engine_config)
    
    # Add venue with realistic costs
    # Commission: $7 per lot round-trip = $3.5 per side
    # For 0.01 lot = $0.035 per side
    # Spread: ~1 pip = 0.0001 for EURUSD
    usd_currency = Currency.from_str("USD")
    venue = Venue("SIM")
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        starting_balances=[Money.from_str("10000 USD")],
        base_currency=usd_currency,
        fee_model=FixedFeeModel(commission=Money.from_str("0.035 USD")),  # $0.035 per side for 0.01 lot
        fill_model=FillModel(
            prob_fill_on_limit=1.0,
            prob_fill_on_stop=1.0,
            prob_slippage=0.0,
        ),
    )
    
    # Add instrument (CurrencyPair for FX)
    from nautilus_trader.model.instruments import CurrencyPair
    from nautilus_trader.model.objects import Price, Quantity
    from nautilus_trader.model.enums import CurrencyType
    
    # Create EURUSD instrument
    eur_currency = Currency.from_str("EUR")
    instrument = CurrencyPair(
        instrument_id=instrument_id,
        raw_symbol=Symbol("EURUSD"),
        base_currency=eur_currency,
        quote_currency=usd_currency,
        price_precision=5,
        size_precision=2,
        price_increment=Price.from_str("0.00001"),
        size_increment=Quantity.from_str("0.01"),
        ts_event=0,
        ts_init=0,
        lot_size=Quantity.from_str("0.01"),
        min_quantity=Quantity.from_str("0.01"),
        max_quantity=Quantity.from_str("100.00"),
        margin_init=Decimal("0.0333"),  # 30:1 leverage
        margin_maint=Decimal("0.025"),  # 40:1 leverage
    )
    engine.add_instrument(instrument)
    
    # Add data
    engine.add_data(bars)
    
    # Add strategy
    strategy = SymmetryTrapStrategy(config=strategy_config)
    engine.add_strategy(strategy)
    
    # Run
    print("Running backtest...")
    engine.run()
    
    # Get results
    result = engine.get_result()
    
    # Extract metrics
    metrics = {
        "total_trades": result.total_trades,
        "win_rate": result.win_rate * 100 if result.win_rate else 0,
        "net_pnl": float(result.net_pnl) if result.net_pnl else 0,
        "profit_factor": float(result.profit_factor) if result.profit_factor else 0,
        "max_drawdown": float(result.max_drawdown) if result.max_drawdown else 0,
        "avg_trade": float(result.avg_trade) if result.avg_trade else 0,
    }
    
    print(f"\n=== NAUTILUS BACKTEST RESULTS ===")
    print(f"Symbol: {symbol}")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Win Rate: {metrics['win_rate']:.1f}%")
    print(f"Net PnL: {metrics['net_pnl']:.2f}")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2f}")
    print(f"Avg Trade: {metrics['avg_trade']:.2f}")
    
    return metrics


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Nautilus backtest for Symmetry Trap")
    parser.add_argument("--csv", required=True, help="Path to CSV data file")
    parser.add_argument("--symbol", required=True, help="Symbol (e.g., EURUSD)")
    parser.add_argument("--pip-size", type=float, default=0.0001, help="Pip size")
    args = parser.parse_args()
    
    tier_config = {
        "T1": {"au_pips": 10, "trigger_pips": 12},
        "T2": {"au_pips": 12, "trigger_pips": 15},
        "T3": {"au_pips": 15, "trigger_pips": 19},
    }
    
    run_nautilus_backtest(
        csv_path=args.csv,
        symbol=args.symbol,
        pip_size=args.pip_size,
        tier_config=tier_config,
    )