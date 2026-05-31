"""Quick diagnostic for P90 strategy - run with small bar count"""
import sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtests")
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")

from run_cerebus_backtest import *
from pathlib import Path
from decimal import Decimal

csv_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSDPRO_M5_2023_2025.csv")
instrument, venue = get_instrument_and_venue("EURUSD.PRO")
bar_type = make_bar_type("EURUSD.PRO", instrument)

bars = load_bars(csv_path, instrument, bar_type)
print(f"Loaded {len(bars)} bars")

# Use only first 5000 bars for quick test
bars_small = bars[:5000]
print(f"Using {len(bars_small)} bars for diagnostic")

config = BacktestEngineConfig(
    trader_id=TraderId("CEREBUS-P90-DIAG"),
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
        prob_fill_on_limit=1.0,   # Always fill for diagnostic
        prob_slippage=0.0,
    ),
)
engine.add_instrument(instrument)

strat_config = P90Config(
    instrument_id=str(instrument.id),
    bar_type=str(bar_type),
    lot_size=Decimal("0.01"),
)
strategy = P90Strategy(config=strat_config)
engine.add_strategy(strategy=strategy)
engine.add_data(bars_small)

print("\nRunning backtest...")
engine.run()

# Access strategy internal stats
print(f"\n=== Strategy Internal Stats ===")
try:
    print(f"  total_trades={strategy.total_trades}")
    print(f"  wins={strategy.wins}")
    print(f"  losses={strategy.losses}")
    print(f"  total_pnl={strategy.total_pnl:.1f}")
    if strategy.total_trades > 0:
        print(f"  win_rate={strategy.wins/strategy.total_trades*100:.1f}%")
except Exception as e:
    print(f"  Error accessing stats: {e}")

result = engine.get_result()
print(f"\n=== Nautilus Engine Stats ===")
print(f"  Orders: {result.total_orders}")
print(f"  Positions: {result.total_positions}")
pnl_stats = result.stats_pnls.get('USD', {})
print(f"  PnL Stats: {pnl_stats}")

# Check account state
accounts = engine.cache.accounts()
print(f"\n=== Accounts ===")
for acc in accounts:
    print(f"  {acc}")

# Check positions
positions = engine.cache.positions()
print(f"\n=== Positions: {len(positions)} ===")
for pos in positions[:5]:
    print(f"  {pos}")

engine.dispose()
print("\nDiagnostic complete.")
