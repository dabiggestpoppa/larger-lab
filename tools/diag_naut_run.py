"""
Run Nautilus ST backtest on XAUUSD with session-level debug output.
Compare active day count and trade count with Python engine.
"""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab/backtests')

from pathlib import Path
from run_cerebus_backtest_fixed import run_backtest

# Modify the runner to log session init details
# We'll run it and parse the output

result = run_backtest(
    strategy_name='symmetry_trap',
    symbol='XAUUSD',
    csv_path=Path('quant-lab/data/XAUUSD_M5.csv'),
)

if result:
    print(f"\n=== NAUTILUS XAUUSD RESULTS ===")
    print(f"Trades: {result.get('strategy_trades', 0)}")
    print(f"Win Rate: {result.get('strategy_win_rate', 0):.1f}%")
    print(f"PnL: {result.get('strategy_pnl_pips', 0):.1f} pips")
    print(f"Bars: {result.get('bars', 0)}")
