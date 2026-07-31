import sys, os
sys.path.insert(0, 'engines')
sys.path.insert(0, 'configs')
from symmetry_trap_backtest import SymmetryTrapBacktest, DEFAULT_TIER_CONFIG
from asset_configs import get_config

pair = 'EURUSD'
cfg = get_config(pair)
print('Config tiers:', cfg['tiers'])
print()
print('DEFAULT_TIER_CONFIG:', DEFAULT_TIER_CONFIG)
print()

# Check if session_cutoff is set
bt = SymmetryTrapBacktest(
    pip_size=0.0001, tier_config=cfg['tiers'], symbol=pair,
    config={'pip_value': 0.0001, 'tiers': cfg['tiers'], 'name': pair}
)
print('session_cutoff:', getattr(bt, 'session_cutoff', 'NOT SET'))
print('ar_expansion:', getattr(bt, 'ar_expansion', 'NOT SET'))
