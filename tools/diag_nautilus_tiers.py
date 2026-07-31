"""
Check what tiers Nautilus is ACTUALLY using for XAUUSD.
The Python engine uses ASSET_CONFIGS['XAUUSD'] which has specific tiers.
But what if the Nautilus runner passes them differently, or the Nautilus
strategy reads them wrong?
"""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab')
sys.path.insert(0, 'quant-lab/configs')

from quant_lab.configs.asset_configs import ASSET_CONFIGS

# What the runner passes:
cfg = ASSET_CONFIGS['XAUUSD']
print("ASSET_CONFIGS['XAUUSD']:")
for k, v in cfg.items():
    print(f"  {k}: {v}")

# The runner builds tier_override like this:
tier_override = {}
for tier_name in ['T1', 'T2', 'T3']:
    t = cfg['tiers'][tier_name]
    tier_override[tier_name] = {
        'ar_max': t['ar_max'],
        'au': t['au'],
        'trigger': t['trigger']
    }
print(f"\ntier_override passed to SymmetryTrapConfig:")
print(f"  {tier_override}")

# Now check Nautilus SYMBOL_TIER_CONFIGS
from symmetry_trap_strategy import SYMBOL_TIER_CONFIGS, DEFAULT_TIER_CONFIG, PIP_DIVISORS

print(f"\nSYMBOL_TIER_CONFIGS has XAUUSD? {'XAUUSD' in SYMBOL_TIER_CONFIGS}")
print(f"SYMBOL_TIER_CONFIGS has XAU/USD? {'XAU/USD' in SYMBOL_TIER_CONFIGS}")

nt_xau = SYMBOL_TIER_CONFIGS.get('XAUUSD', 'NOT FOUND')
print(f"Nautilus XAUUSD tiers: {nt_xau}")

# These should match tier_override... let me check
print(f"\ntier_override == nt_xau: {tier_override == nt_xau}")

# But wait - what if the runner is CONFIGURED to use XAUUSD but the
# actual instrument_id is 'XAU/USD' or something else?
# Let me check what the runner does:
# instrument, venue_name = get_instrument_and_venue(symbol)
# For XAUUSD: pair = f"{symbol[:3]}/{symbol[3:]}" = "XAU/USD"
# instrument = TestInstrumentProvider.default_fx_ccy("XAU/USD", ...)
# instrument.id = InstrumentId("XAU/USD.OANDA")

# So instrument_id = "XAU/USD.OANDA" and instrument_id.symbol = "XAU/USD"
# In SymmetryTrapStrategy.__init__:
#   sym_str = str(self.instrument_id.symbol)  # "XAU/USD"
#   sym_key = sym_str.replace("/", "").replace(".", "")  # "XAUUSD"
#   self.pip_divisor = PIP_DIVISORS.get(sym_str, PIP_DIVISORS.get(sym_key, 10000.0))
#   self.tier_config = SYMBOL_TIER_CONFIGS.get(sym_str, SYMBOL_TIER_CONFIGS.get(sym_key, DEFAULT_TIER_CONFIG))

# IF config.tier_config_override is not None:
#     self.tier_config = config.tier_config_override

# So if tier_config_override is provided, it OVERRIDES the lookup.
# The override comes from ASSET_CONFIGS['XAUUSD']['tiers'].

# BUT WAIT: what if ASSET_CONFIGS doesn't have XAUUSD?
print(f"\n'XAUUSD' in ASSET_CONFIGS? {'XAUUSD' in ASSET_CONFIGS}")

# Hmm, let me check the ACTUAL runner code for the Nautilus backtest
# that produced 1718 trades. That was run_cerebus_backtest_fixed.py.
# It calls ASSET_CONFIGS.get(symbol) where symbol = 'XAUUSD'
# So cfg = ASSET_CONFIGS['XAUUSD']

# The config pip_value is 0.1. The Nautilus strategy pip_divisor for XAUUSD is 10.0.
# 1/0.1 = 10.0. So they're equivalent.

# CRITICAL: But what about the AR conversion?
# Python: ar_pips = (asian_high - asian_low) / pip_size   = (ah - al) / 0.1
# Nautilus: ar_pips = (asian_high - asian_low) * pip_divisor = (ah - al) * 10.0
# These are THE SAME: (ah - al) * 10.0 = (ah - al) / 0.1

# OK so the AR and tier classification should be identical.

# What else differs? Let me check: in the Python run() method,
# the est_offset is -5 (UTC to EST). But the Nautilus on_bar uses:
# utc_hour = (bar.ts_event // 3_600_000_000_000) % 24
# return (utc_hour + est_offset) % 24  where est_offset = -5

# In Python run():
# bar_est_h = (bar.timestamp.hour + self.est_offset) % 24

# BOTH use the same = (hour - 5) % 24.

# WRONG! In the Python code:
# self.est_offset = -5  (passed to constructor)
# bar_est_h = self._get_est_hour(bar.timestamp)  # (bar.timestamp.hour + self.est_offset) % 24
# = (bar.timestamp.hour + (-5)) % 24 = (bar.timestamp.hour - 5) % 24

# In Nautilus:
# self.est_offset = -5  (from config)
# utc_hour = (bar.ts_event // 3_600_000_000_000) % 24
# return (utc_hour + est_offset) % 24
# = (utc_hour - 5) % 24

# Same thing. Both convert UTC to EST as (hour - 5) % 24.

# NAH — I just realized something. The Nautilus BarDataWrangler takes
# a DataFrame with UTC timestamps and produces Nautilus Bar objects.
# The bar.ts_event is the bar OPEN time in UTC nanoseconds.
# But the PYTHON CSV loader uses timestamps as-is without UTC conversion.
# When the Python run() adds timedelta(hours=-5) to convert to EST,
# it's converting from a UTC timestamp stored as naive datetime.
# The Nautilus bar.ts_event is in UTC nanoseconds.
# Both should be equivalent IF the CSV timestamps are in UTC.

# But what if they're NOT in UTC? What if the XAUUSD_M5.csv has timestamps
# in a different timezone? Let me check.

import pandas as pd
data = pd.read_csv('quant-lab/data/XAUUSD_M5.csv', nrows=10)
print(f"\nFirst 10 timestamps from XAUUSD_M5.csv:")
for i, ts in enumerate(data['timestamp']):
    print(f"  {ts}")

# The server is in America/New_York (EST/EDT)
# MT5 data is typically in the server's timezone
# But these look like they could be UTC or EST
# Let me check against known gold prices

# If these are UTC timestamps, then 2022-01-03 00:00:00 UTC = 2022-01-02 19:00:00 EST
# Gold price around that time: ~$1828 at close on Jan 3.
# The data shows open=1828.69 at 2022-01-03 00:00:00
# So this IS the 00:00 UTC = 19:00 EST bar.

# For the Asian session (19:00-03:00 EST):
# In UTC: 00:00-08:00 UTC
# So Asian bars in UTC: hour 0-7

# Python run() groups by EST date using: est_dt = bar.timestamp + timedelta(hours=-5)
# This converts UTC to EST by subtracting 5 hours.
# BUT this doesn't account for DST! During EDT (Mar-Nov), UTC-4 is correct, not UTC-5.

# Nautilus on_bar: est_offset = -5 (from config)
# Same issue: hardcoded -5 offset regardless of DST.

# So both have the same DST issue. It shouldn't cause systematic difference.

# Hmm, let me look at this from the COMPLETELY OPPOSITE direction.
# What if the answer is simple: the Nautilus backtest ran with a DIFFERENT config file
# or the runner used DEFAULT_TIER_CONFIG instead of XAUUSD tiers?

# If Nautilus used EURUSD tiers (T1=20, T2=30, T3=45):
# For XAUUSD with median AR=151pips, ALL sessions would be NO-GO
# -> 0 trades. That doesn't match 1718.

# What if Nautilus used WIDER tiers, like generic ones that let everything through?
# ar_max = infinity → all sessions active → 1362 active sessions
# But with that many sessions, even at 1.26 trades/session average = 1718 trades.

# Actually wait. 1.26 trades/session is EXACTLY what we see:
# Python: 604 trades / 316 active sessions = 1.91 trades/active_session
# Nautilus: 1718 trades / 1362 total_sessions = 1.26 trades/session

# If Nautilus processes ALL 1362 sessions (no NO-GO), it averages 1.26 per session.
# Python processes only 316 sessions, at 1.91 per session.
# 316 * 1.91 = 604 (Python)
# 1362 * 1.26 = 1718 (Nautilus)

# So the Nautilus backtest either:
# A) Has a wider tier config (higher ar_max), OR
# B) Does NOT tier-filter at all (all sessions active)

# MAD said the Nautilus backtest results ARE correct and match manual expectations.
# This means the Nautilus config might be RIGHT and the Python tier config MIGHT be WRONG.

# But where would the Nautilus config come from?
# The runner passes tier_config_override from ASSET_CONFIGS.
# Unless... was there a DIFFERENT version of ASSET_CONFIGS at the time?

# OR: what if Nautilus DID NOT receive the tier override correctly?
# What if tier_config_override = None, and Nautilus fell back to 
# SYMBOL_TIER_CONFIGS.get('XAU/USD') which might DEFAULT to something wider?

print("\nChecking Nautilus symbol lookup for XAU/USD:")
from symmetry_trap_strategy import SYMBOL_TIER_CONFIGS
for key in SYMBOL_TIER_CONFIGS:
    if 'XAU' in key or 'USD' in key:
        print(f"  '{key}': {SYMBOL_TIER_CONFIGS[key]}")

# Also check: what does DEFAULT_TIER_CONFIG give?
print(f"\nDEFAULT_TIER_CONFIG: {DEFAULT_TIER_CONFIG}")
print(f"Default T3 ar_max: {DEFAULT_TIER_CONFIG['T3']['ar_max']}")

# If Nautilus used DEFAULT_TIER_CONFIG for XAUUSD:
# T1: ar_max=20, T2: ar_max=30, T3: ar_max=45
# With XAUUSD median AR=151p, ALL sessions -> NO-GO -> 0 trades
# So that can't be it.

# What if the Nautilus runner was run with DIFFERENT asset config?
# Let me check if there are multiple versions
