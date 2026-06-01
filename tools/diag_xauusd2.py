"""Diagnose XAUUSD: compare campaign runner vs direct engine."""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab')
sys.path.insert(0, 'quant-lab/engines')
sys.path.insert(0, 'quant-lab/configs')

from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv
from quant_lab.configs.asset_configs import ASSET_CONFIGS

cfg = ASSET_CONFIGS['XAUUSD']
print('XAUUSD config:', cfg)

# Run using the SAME class the campaign uses
runner = SymmetryTrapBacktest(
    pip_size=cfg['pip_value'],
    symbol='XAUUSD',
    config=cfg,
)
result = runner.run_from_csv('quant-lab/data/XAUUSD_M5.csv')

print(f'\nCampaign class result:')
print(f'Total trades: {result.total_trades}')
print(f'Wins: {result.wins}, Losses: {result.losses}')
print(f'WR: {result.win_rate:.1f}%')
print(f'PnL: {result.total_pnl_pips:.1f} pips')
print(f'Tier stats: {result.tier_stats}')
print(f'Loop stats: {result.loop_stats}')
print(f'Data bars: {result.data_bars}, Days: {result.data_days}')

# Now check: how many sessions are active vs NO-GO?
# And how many sessions produce 0 trades?
# Add debug counting
from symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection, EngineState
import pandas as pd
from datetime import timedelta

data = pd.read_csv('quant-lab/data/XAUUSD_M5.csv', parse_dates=['timestamp'])
data['est_hour'] = (data['timestamp'].dt.hour + 19) % 24
data['date'] = data['timestamp'].date

asian = data[(data['est_hour'] >= 19) | (data['est_hour'] < 3)]
daily_asian = asian.groupby('date').agg(
    ah=('high', 'max'), al=('low', 'min')
)
daily_asian['range'] = (daily_asian['ah'] - daily_asian['al']) / 0.1

# Count using campaign class's own counting
active = 0
nogo = 0
total_init = 0
for date, row in daily_asian.iterrows():
    ah, al = row['ah'], row['al']
    if ah <= 0 or al >= 99999:
        continue
    total_init += 1
    ar = (ah - al) / cfg['pip_value']
    is_active = True
    for tier in ['T1', 'T2', 'T3']:
        if tier in cfg['tiers'] and ar <= cfg['tiers'][tier]['ar_max']:
            break
    else:
        is_active = False
    if is_active:
        active += 1
    else:
        nogo += 1

print(f'\nSession analysis (from config):')
print(f'Total days with data: {total_init}')
print(f'Active sessions: {active}')
print(f'NO-GO sessions: {nogo}')
print(f'Active rate: {active/total_init*100:.1f}%')

# Now: how many trades per active session?
print(f'Trades per active session: {result.total_trades/max(active,1):.2f}')

# The Nautilus result was 1,718 trades vs Python 604.
# Key question: does Nautilus handle something differently?
# Let me check the Nautilus code's session init behavior

print('\n--- Comparing Engine Implementations ---')
print('Python engine: k_factor=0.5, pip=0.1')
print(f'XAUUSD tiers: T1<={cfg["tiers"]["T1"]["ar_max"]}, T2<={cfg["tiers"]["T2"]["ar_max"]}, T3<={cfg["tiers"]["T3"]["ar_max"]}')
print(f'XAUUSD median AR: {daily_asian["range"].median():.1f} pips')
print(f'XAUUSD P25 AR: {daily_asian["range"].quantile(0.25):.1f} pips')

# Is the issue that gold price went from ~1800 to ~4500 (2.5x)?
# The same pips threshold captures more or less?
# At 1800, 32 pips = 1.8% move. At 4500, 32 pips = 0.7% move.
print('\n--- Gold price regime analysis ---')
print(f'Gold min price: {data["low"].min():.2f}')
print(f'Gold max price: {data["high"].max():.2f}')
print(f'Gold mean price: {data["close"].mean():.2f}')
print(f'Price ratio (max/min): {data["high"].max()/data["low"].min():.1f}x')
print('\nTier AR in percentage terms:')
for row_date in [data['timestamp'].min().date(), data['timestamp'].max().date()]:
    subset = data[data['date'] == row_date]
    if len(subset) > 0:
        price = subset['close'].mean()
        print(f'  {row_date}: price={price:.2f}')
        for tier_name in ['T1', 'T2', 'T3']:
            ar_pips = cfg['tiers'][tier_name]['ar_max']
            ar_price = ar_pips * cfg['pip_value']
            pct = ar_price / price * 100
            print(f'    {tier_name} max AR: {ar_pips}p = {ar_price:.2f} = {pct:.3f}%')
