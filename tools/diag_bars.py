"""Quick comparison: bar counts and session analysis."""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab/engines')
sys.path.insert(0, 'quant-lab/configs')

from symmetry_trap_backtest import load_m5_csv
from quant_lab.configs.asset_configs import ASSET_CONFIGS

bars, _ = load_m5_csv('quant-lab/data/XAUUSD_M5.csv')
print(f'Python CSV loader: {len(bars)} bars')
print(f'Date range: {bars[0].timestamp} to {bars[-1].timestamp}')

# Count unique dates
from datetime import timedelta
dates = set()
for b in bars:
    est_dt = b.timestamp + timedelta(hours=-5)
    dates.add(est_dt.strftime('%Y-%m-%d'))
print(f'Unique EST dates: {len(dates)}')

# Count bars per date
from collections import defaultdict
day_bars = defaultdict(int)
for b in bars:
    est_dt = b.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    day_bars[dk] += 1

total = len(day_bars)
under_200 = sum(1 for v in day_bars.values() if v < 200)
over_288 = sum(1 for v in day_bars.values() if v > 288)
print(f'Dates with <200 bars: {under_200}')
print(f'Dates with >288 bars: {over_288}')
print(f'Avg bars per day: {len(bars)/total:.0f}')

# Check Nautilus bar count from its report
cfg = ASSET_CONFIGS['XAUUSD']
total_days_minimal = sum(1 for v in day_bars.values() if v > 0)
print(f'\nTotal days: {total_days_minimal}')
print(f'Config: pip={cfg["pip_value"]}, tiers={cfg["tiers"]}')

# Nautilus got 1718 trades, Python got 604
# Ratio: 2.84x
# Nautilus sessions_processed = same number of days
# But Nautilus trades_per_session = 1718/total_active_sessions_sessions

# For Python: we know 316 active sessions out of ~1362 days
# That's because 71% of sessions are NO-GO (AR > 95 pips)

# Hmm, let me check: What if Nautilus does NOT use the 95 pips T3 max?
# What if it falls back to EURUSD tiers (T3 max = 45 pips)?
# No wait, that would make MORE NO-GO sessions, not fewer.
# And Nautilus has MORE trades, not fewer.

# WAIT - what if Nautilus is NOT using the tier config override correctly?
# What if it uses DEFAULT_TIER_CONFIG with EURUSD tiers?
# EURUSD tiers: T1=20p, T2=30p, T3=45p
# With EURUSD tiers for XAUUSD:
# More sessions would be NO-GO (45p max vs 95p max)
# That would give FEWER trades, not more.

# Let me try the opposite: what if Nautilus uses VERY WIDE tiers?
# Or what if Nautilus ignores tiers entirely and processes all sessions?

# Actually, let me re-read the Nautilus _classify_tier
from symmetry_trap_strategy import DEFAULT_TIER_CONFIG, SYMBOL_TIER_CONFIGS
print(f'\nEURUSD tiers: {DEFAULT_TIER_CONFIG}')
print(f'XAUUSD tiers: {SYMBOL_TIER_CONFIGS.get("XAUUSD", "NOT FOUND")}')

# Hmm, let me check what the Nautilus strategy ACTUALLY uses.
# In the runner, tier_override is passed. But let me check:
# tier_override = {'T1': {'ar_max': 32.0, ...}, 'T2': {...}, 'T3': {...}}
# Then: strat_config = SymmetryTrapConfig(tier_config_override=tier_override)
# In SymmetryTrapStrategy.__init__:
#   if config.tier_config_override is not None:
#       self.tier_config = config.tier_config_override
# So it SHOULD use the XAUUSD tiers.

# Unless... the runner is passing wrong data?
# Let me check what the runner actually passes
import inspect
from run_cerebus_backtest_fixed import run_backtest
src = inspect.getsource(run_backtest)
for i, line in enumerate(src.split('\n')):
    if 'tier' in line.lower() or 'config' in line.lower():
        if i > 150 and i < 200:
            print(f'  L{i}: {line.rstrip()}')
