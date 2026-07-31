"""
Run the EXACT Nautilus DMR backtest logic on the existing CSV data (NO MT5 needed).
This uses the run_dmr_backtest() function from naut_dmr_backtest.py directly.
"""
import sys, os, pandas as pd, pytz
from pathlib import Path

# Import the DMR engine from naut_dmr_backtest
sys.path.insert(0, str(Path(__file__).parent / "backtests"))

from naut_dmr_backtest import run_dmr_backtest, compute_stats

EST = pytz.timezone('US/Eastern')

DATA_DIR = Path(__file__).parent / "data"
REPORTS_DIR = Path(__file__).parent / "reports"

# Use the same config that produced 94.8% WR in the original backtest
SYMBOL_CONFIG = {
    'EURUSD.PRO': {
        'thresholds': {
            2: 4.1, 3: 4.1, 4: 4.6, 5: 4.6, 6: 4.6,
            7: 5.9, 8: 5.9, 9: 6.2, 10: 6.2,
        },
        'pip_divisor': 10000.0,
        'name': 'EURUSD',
    },
}

print("="*70)
print("DMR BACKTEST — Using Nautilus Logic on CSV Data (NO MT5)")
print("="*70)

# Load data from CSV
csv_path = DATA_DIR / "EURUSDPRO_M5_2023_2026.csv"
print(f"\nLoading: {csv_path}")
df = pd.read_csv(csv_path, parse_dates=['timestamp'])

# Make timestamp timezone-aware (assume UTC, convert to EST in the engine)
if df['timestamp'].dt.tz is None:
    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')

# Filter weekends
df = df[df['timestamp'].dt.dayofweek < 5].reset_index(drop=True)

print(f"Data: {len(df):,} M5 bars ({df['timestamp'].min()} → {df['timestamp'].max()})")

# Run backtest using Nautilus engine
config = SYMBOL_CONFIG['EURUSD.PRO']
trades, daily_pnl = run_dmr_backtest(df, config)
stats = compute_stats(trades)

print(f"\n{'='*70}")
print(f"RESULTS")
print(f"{'='*70}")
print(f"  Trades:        {stats['trades']}")
print(f"  Wins / Losses: {stats['wins']} / {stats['losses']}")
print(f"  Win Rate:      {stats['wr']}%")
print(f"  PnL:           {stats['pnl_pips']:+.1f} pips")
print(f"  Profit Factor: {stats['pf']}")
print(f"  Avg Win:       {stats['avg_win']}p")
print(f"  Avg Loss:      {stats['avg_loss']}p")
print(f"  Max Cons Wins: {stats['max_consec_wins']}")
print(f"  Max Cons Loss: {stats['max_consec_losses']}")
print(f"  Max DD:        {stats['max_drawdown_pips']}p")

# Save trades
REPORTS_DIR.mkdir(exist_ok=True)
if trades:
    trades_df = pd.DataFrame(trades)
    trades_path = REPORTS_DIR / "DMR_nautilus_csv_trades.csv"
    trades_df.to_csv(trades_path, index=False)
    print(f"\nTrades saved: {trades_path}")

# Also compute hourly breakdown
from collections import defaultdict
hourly = defaultdict(list)
for t in trades:
    try:
        h = t['entry_time'].hour if hasattr(t['entry_time'], 'hour') else t['entry_time']
        hourly[str(h)].append(t['pnl_pips'])
    except:
        pass

if hourly:
    print(f"\n--- Per-Hour Breakdown ---")
    for h in sorted(hourly.keys()):
        pnls = hourly[h]
        w = sum(1 for p in pnls if p > 0)
        print(f"  {h}: {len(pnls)}t | WR: {w/len(pnls)*100:.1f}% | PnL: {sum(pnls):+.1f}p")
