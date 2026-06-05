"""Quick CSV vs Nautilus comparison for EURUSD."""
import sys, json
from pathlib import Path

engines_dir = Path(__file__).parent.parent / 'engines'
sys.path.insert(0, str(engines_dir))

from symmetry_trap_backtest import SymmetryTrapBacktest, BacktestResult

csv_path = str(Path(__file__).parent.parent / 'data' / 'EURUSD_M5.csv')
print(f"Running CSV engine backtest on {csv_path}")

bt = SymmetryTrapBacktest(pip_size=0.0001, symbol='EURUSD')
result = bt.run_from_csv(csv_path)

print(f"\n=== CSV ENGINE RESULTS ===")
print(f"Trades: {result.total_trades}")
print(f"WR: {result.win_rate:.1f}%")
print(f"PnL: {result.total_pnl_pips:.1f}p")
print(f"Bars: {result.data_bars}")
print(f"Days: {result.data_days}")

# Load Nautilus result
nautilus_report = Path(__file__).parent.parent / 'reports' / 'NAUTILUS_SYMMETRY_TRAP_EURUSD_20260604_203321.json'
if nautilus_report.exists():
    with open(nautilus_report) as f:
        n = json.load(f)
    print(f"\n=== NAUTILUS RESULTS ===")
    print(f"Trades: {n['strategy_trades']}")
    print(f"WR: {n['strategy_win_rate']:.1f}%")
    print(f"PnL: {n['strategy_pnl_pips']:.1f}p")
    print(f"Bars: {n['bars']}")
    
    print(f"\n=== DELTA (CSV - Nautilus) ===")
    print(f"Trade diff: {result.total_trades - n['strategy_trades']} more in CSV")
    print(f"WR diff: {result.win_rate - n['strategy_win_rate']:+.1f}pp")
    print(f"PnL diff: {result.total_pnl_pips - n['strategy_pnl_pips']:+.1f}p")
    print(f"CSV trades/day: {result.total_trades / max(result.data_days, 1):.2f}")
    print(f"Nautilus trades/day: {n['strategy_trades'] / max(result.data_days, 1):.2f}")
