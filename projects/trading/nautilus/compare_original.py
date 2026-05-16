"""Compare original p90_cascade.py with unified engine."""
import sys, json
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
from nautilus.strategies.p90_cascade import P90CascadeStrategy, P90CascadeConfig
from nautilus.data_loader import _parse_csv
from pathlib import Path

df = _parse_csv(Path(r'C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv'))
df = df.tail(50000)
print(f'Data: {len(df)} bars')

strategy = P90CascadeStrategy()
results = strategy.run_backtest(df, pair='EUR/USD')
print(f"Trades: {results.get('total_trades',0)}")
print(f"WR: {results.get('win_rate',0)}%")
print(f"PnL: {results.get('total_pnl_pips',0)}p")
print(f"By type: {json.dumps(results.get('by_activation_type',{}), indent=2)}")
print(f"By exit: {json.dumps(results.get('by_exit_reason',{}), indent=2)}")
