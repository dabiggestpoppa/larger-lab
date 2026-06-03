"""Quick test: does the Nautilus strategy SL trigger immediately on entry bar?"""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab')
sys.path.insert(0, 'quant-lab/configs')
sys.path.insert(0, 'quant-lab/strategies')
sys.path.insert(0, 'quant-lab/backtests')

from run_cerebus_backtest_fixed import run_backtest

result = run_backtest('symmetry_trap', 'EURUSD', bars_limit=10000)
if result:
    print(f"\n=== RESULT ===")
    print(f"Trades: {result.get('strategy_trades', 0)}")
    print(f"WR: {result.get('strategy_win_rate', 0):.1f}%")
    print(f"PnL: {result.get('strategy_pnl_pips', 0):.1f}p")
    print(f"Wins: {result.get('strategy_wins', 0)}")
    print(f"Losses: {result.get('strategy_losses', 0)}")
else:
    print("No result")
