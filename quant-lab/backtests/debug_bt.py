"""Quick debug script to check symmetry trap Nautilus backtest results."""
import sys, json
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import pandas as pd
import pytz

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.config import BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.backtest.models import FillModel

REPORTS_DIR = Path(__file__).parent.parent / 'reports'

# Add strategies dir
sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
from symmetry_trap_strategy import SymmetryTrapStrategy, SymmetryTrapConfig

EST = pytz.timezone('US/Eastern')

# Setup
instrument = TestInstrumentProvider.default_fx_ccy('EUR/USD', venue=Venue('OANDA'))
bar_type_str = f'{instrument.id}-5-MINUTE-LAST-EXTERNAL'
bar_type = BarType.from_str(bar_type_str)

# Load data
csv_path = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSDPRO_M5_2023_2025.csv')
df = pd.read_csv(csv_path)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')
df.index = pd.to_datetime(df.index, utc=True)
keep_cols = ['open','high','low','close','volume']
df = df[keep_cols]
for c in keep_cols:
    df[c] = pd.to_numeric(df[c], errors='coerce').astype('float64')

wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)
bars = wrangler.process(df)
print(f'Loaded {len(bars)} bars')

# Engine
config = BacktestEngineConfig(
    trader_id=TraderId('CEREBUS-DEBUG-001'),
    logging=LoggingConfig(log_level='WARNING'),
)
engine = BacktestEngine(config=config)
engine.add_venue(
    venue=Venue('OANDA'),
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

strat_config = SymmetryTrapConfig(
    instrument_id=str(instrument.id),
    bar_type=str(bar_type),
    lot_size=Decimal('0.01'),
)
strategy = SymmetryTrapStrategy(config=strat_config)
engine.add_strategy(strategy=strategy)
engine.add_data(bars)

print('Running backtest...')
engine.run()

# Get result
result = engine.get_result()

# Print ALL available stats
print(f'\n=== RESULT OBJECT ===')
print(f'total_orders: {result.total_orders}')
print(f'total_positions: {result.total_positions}')
print(f'total_events: {result.total_events}')
print(f'elapsed_time: {result.elapsed_time}')

print(f'\n=== STATS_PNLS ===')
for k, v in result.stats_pnls.items():
    print(f'  {k}: {v}')

print(f'\n=== STATS_RETURNS ===')
for k, v in result.stats_returns.items():
    print(f'  {k}: {v}')

print(f'\n=== STATS_PERF ===')
for k, v in result.stats_perf.items():
    print(f'  {k}: {v}')

# Check strategy internal stats
print(f'\n=== STRATEGY INTERNAL STATS ===')
print(f'total_trades: {strategy.total_trades}')
print(f'wins: {strategy.wins}')
print(f'losses: {strategy.losses}')
print(f'total_pnl_pips: {strategy.total_pnl_pips}')
if strategy.total_trades > 0:
    wr = strategy.wins / strategy.total_trades * 100
    print(f'win_rate: {wr:.1f}%')

# Try to get from portfolio
print(f'\n=== PORTFOLIO ===')
portfolio = engine.trader.portfolio
instruments = portfolio.instruments(Venue('OANDA'))
print(f'Instruments: {instruments}')

# Save comprehensive report
timestamp = datetime.now(EST).strftime('%Y%m%d_%H%M%S')
report = {
    "strategy": "symmetry_trap",
    "symbol": "EURUSD.PRO",
    "bars": len(bars),
    "timestamp": timestamp,
    "total_orders": result.total_orders,
    "total_positions": result.total_positions,
    "total_events": result.total_events,
    "elapsed_s": result.elapsed_time,
    "stats_pnls": result.stats_pnls,
    "stats_returns": result.stats_returns,
    "stats_perf": {k: str(v) for k, v in result.stats_perf.items()},
    "strategy_internal": {
        "total_trades": strategy.total_trades,
        "wins": strategy.wins,
        "losses": strategy.losses,
        "total_pnl_pips": strategy.total_pnl_pips,
        "win_rate": (strategy.wins / strategy.total_trades * 100) if strategy.total_trades > 0 else 0,
    }
}

report_path = REPORTS_DIR / f"NAUTILUS_SYMMETRY_TRAP_DEBUG_{timestamp}.json"
with open(report_path, 'w') as f:
    json.dump(report, f, indent=2, default=str)
print(f'\nReport saved: {report_path}')

engine.dispose()
