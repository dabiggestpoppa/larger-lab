"""Quick verification that tier/AU values match the PDF."""
import sys, pandas as pd
from pathlib import Path
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location(
    "full_feature_engine",
    Path("quant-lab/ml/phase1_data/full_feature_engine.py")
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
compute_asian_range = mod.compute_asian_range
get_asset_config = mod.get_asset_config

df = pd.read_parquet('quant-lab/ml/data/clean/EURUSD_clean.parquet')
df = compute_asian_range(df, 'EURUSD')

cfg = get_asset_config('EURUSD')
print('EURUSD Config Tiers:')
for tier, vals in cfg['tiers'].items():
    print(f'  {tier}: AU={vals["au"]}p, Trigger={vals["trigger"]}p')

print()
print('Tier boundaries (2x AU):')
for tier, vals in cfg['tiers'].items():
    print(f'  {tier}: < {vals["au"]*2:.1f}p')

print()
print('Actual tier distribution:')
print(df['tier'].value_counts())

print()
print('Sample AU values by tier:')
for tier in ['T1', 'T2', 'T3', 'T4_NO_GO']:
    subset = df[df['tier']==tier]
    if len(subset) > 0:
        print(f'  {tier}: AU={subset["au_pips"].iloc[0]:.1f}p, AR range={subset["asian_range_pips"].min():.1f}-{subset["asian_range_pips"].max():.1f}p')

# Verify against PDF values
print()
print('=== VERIFICATION AGAINST PDF ===')
pdf_tiers = {'T1': 10.0, 'T2': 12.0, 'T3': 15.0}
for tier, expected_au in pdf_tiers.items():
    actual_au = cfg['tiers'].get(tier, {}).get('au', 0)
    match = 'OK' if abs(actual_au - expected_au) < 0.1 else 'MISMATCH'
    print(f'  {tier}: expected={expected_au}p, actual={actual_au}p [{match}]')
