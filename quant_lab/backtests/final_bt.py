"""Final backtest with proper stats extraction."""
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
sys.path.insert(0, str(Path(__file__).parent.parent / 'strategies'))
from symmetry_trap_strategy import SymmetryTrapStrategy, SymmetryTrapConfig

EST = pytz.timezone('US/Eastern')

instrument = TestInstrumentProvider.default_fx_ccy('EUR/USD', venue=Venue('OANDA'))
bar_type_str = str(instrument.id) + '-5-MINUTE-LAST-EXTERNAL'
bar_type = BarType.from_str(bar_type_str)

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
print('Loaded %d bars' % len(bars))

config = BacktestEngineConfig(
    trader_id=TraderId('CEREBUS-FINAL-001'),
    logging=LoggingConfig(log_level='ERROR'),
)
engine = BacktestEngine(config=config)
engine.add_venue(
    venue=Venue('OANDA'),
    oms_type=OmsType.NETTING,
    account_type=AccountType.MARGIN,
    base_currency=USD,
    starting_balances=[Money(10000, USD)],
    fill_model=FillModel(prob_fill_on_limit=1.0, prob_slippage=0.0),
)
engine.add_instrument(instrument)

strat_config = SymmetryTrapConfig(
    instrument_id=str(instrument.id),
    bar_type=str(bar_type),
    lot_size=Decimal('1000'),
)
strategy = SymmetryTrapStrategy(config=strat_config)
engine.add_strategy(strategy=strategy)
engine.add_data(bars)

print('Running backtest...')
engine.run()
print('Done.')

result = engine.get_result()

# Strategy internal stats
total_trades = strategy.total_trades
wins = strategy.wins
losses = strategy.losses
pnl_pips = strategy.total_pnl_pips
win_rate = (wins / total_trades * 100.0) if total_trades > 0 else 0.0

# Nautilus result stats
print('\n=== NAUTILUS RESULT ===')
print('total_orders=%d' % result.total_orders)
print('total_positions=%d' % result.total_positions)
print('total_events=%d' % result.total_events)

# Try to get PnL from result
pnl_stats = result.stats_pnls.get('USD', {})
print('stats_pnls USD: %s' % pnl_stats)

# Try account
account = engine.trader.portfolio.account(Venue('OANDA'))
if account:
    print('\n=== ACCOUNT ===')
    print('balance: %s' % account.balance_total(USD))
    print('balance_free: %s' % account.balance_free(USD))
    print('balance_locked: %s' % account.balance_locked(USD))
    print('unrealized_pnl: %s' % engine.trader.portfolio.unrealized_pnl(Venue('OANDA')))

# Print all positions
all_positions = engine.trader.portfolio.positions()
print('\nAll positions in portfolio: %d' % len(all_positions))
for p in all_positions[:5]:
    print('  %s' % p)

# Print realized PnL from positions
realized_pnl = 0.0
for p in all_positions:
    if hasattr(p, 'realized_pnl'):
        realized_pnl += float(p.realized_pnl)
print('Sum of realized_pnl from positions: %.2f' % realized_pnl)

# Final report
print('\n=== FINAL RESULTS ===')
print('Strategy: Symmetry Trap / EURUSD.PRO')
print('Bars: %d' % len(bars))
print('Total trades: %d' % total_trades)
print('Wins: %d' % wins)
print('Losses: %d' % losses)
print('Win rate: %.1f%%' % win_rate)
print('PnL (pips): %.1f' % pnl_pips)

# Save report
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
    "trades": total_trades,
    "wins": wins,
    "losses": losses,
    "win_rate_pct": round(win_rate, 1),
    "pnl_pips": round(pnl_pips, 1),
    "pnl_stats_nautilus": {k: str(v) for k, v in pnl_stats.items()},
    "benchmark": {
        "expected_trades": "~574+",
        "expected_wr": "~91%",
        "expected_pf": "~23",
        "expected_maxdd": "~15p",
    }
}

report_path = REPORTS_DIR / ('NAUTILUS_SYMMETRY_TRAP_FINAL_%s.json' % timestamp)
with open(report_path, 'w') as f:
    json.dump(report, f, indent=2, default=str)
print('\nReport saved: %s' % report_path)

engine.dispose()
