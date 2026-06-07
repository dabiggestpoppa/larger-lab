import json, sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
from asset_configs import ASSET_CONFIGS

# The baseline EURUSD at t1=12.0 gives 5593 trades
# The current engine with same config gives fewer trades
# 
# Key insight from MAD's earlier analysis:
# "AR gate is the #1 suppressor — Removing it alone adds +274% trades"
# "ar_max filter (20/30/45 pips) was silently killing entire trading days"
#
# The OLD engine had DEFAULT_TIER_CONFIG with ar_max=20/30/45
# But the asset configs have DIFFERENT ar_max values
# 
# The question: did the baseline sweep use the asset config ar_max values
# or the DEFAULT_TIER_CONFIG values?

# From the .bak engine:
# DEFAULT_TIER_CONFIG = {
#     "T1": {"ar_max": 20.0, "au": 10.0, "trigger": 12.0},
#     "T2": {"ar_max": 30.0, "au": 12.0, "trigger": 15.0},
#     "T3": {"ar_max": 45.0, "au": 15.0, "trigger": 19.0},
# }

# The OLD engine's classify_tier() used tier_config which came from ASSET_CONFIGS
# So it used the asset-specific ar_max values, not the defaults

# But wait - the baseline results show EURUSD at t1=12 with 5593 trades
# Current ASSET_CONFIGS EURUSD has T1 ar_max=20, T2 ar_max=30, T3 ar_max=45
# These are CLOSE to the old defaults (20/30/45)

# Let me check: what are the current ar_max values for EURUSD?
eur = ASSET_CONFIGS['EURUSD']
print("EURUSD current config:")
for t in ['T1', 'T2', 'T3']:
    tier = eu['tiers'][t]
    print(f"  {t}: ar_max={tier['ar_max']}, au={tier['au']}, trigger={tier['trigger']}")

# EURUSD: T1 ar_max=20, T2 ar_max=30, T3 ar_max=45
# These MATCH the old DEFAULT_TIER_CONFIG exactly!
# So for EURUSD, the ar_max values haven't changed

# But for other pairs, the ar_max values are different
# CHFJPY: T1 ar_max=28, T2 ar_max=48, T3 ar_max=85 (current)
# vs old defaults: T1=20, T2=30, T3=45

# The key question: did the baseline use asset-specific ar_max or default ar_max?
# If the baseline used DEFAULT ar_max (20/30/45) for ALL pairs:
#   Then CHFJPY with ar_max=20 would filter out MORE sessions
#   But the baseline shows 5599 trades for CHFJPY - a LOT
#   So the baseline must have used asset-specific ar_max

# Let me verify: the baseline CHFJPY at t1=17 gives 5599 trades
# With asset-specific ar_max (28/48/85), more sessions pass the gate
# With default ar_max (20/30/45), fewer sessions pass
# 5599 trades is consistent with asset-specific ar_max

print("\n=== CONCLUSION ===")
print("The baseline used asset-specific ar_max values from ASSET_CONFIGS")
print("The current engine also uses asset-specific ar_max values")
print("BUT the ar_max values in ASSET_CONFIGS may have changed since June 4th")
print("")
print("Let me check if ASSET_CONFIGS was modified after June 4th...")

import os
config_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs\asset_configs.py'
mtime = os.path.getmtime(config_path)
from datetime import datetime
mod_time = datetime.fromtimestamp(mtime)
print(f"asset_configs.py last modified: {mod_time}")

# Check if there's a backup
for f in os.listdir(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs'):
    print(f"  {f}")
