import pandas as pd
from pathlib import Path

combined_dir = Path('quant-lab/ml/data')
labels_dir = Path('quant-lab/ml/data/labels')
features_dir = Path('quant-lab/ml/data/features')
macro_dir = Path('quant-lab/ml/data/macro_features')

MICRO = ['asian_range_pips','vol_ratio_3am_9am','hour_est','spread_vs_20d_avg','impulse_to_ar_ratio','day_of_week','consecutive_losses','prior_session_wr']
MACRO = ['dist_to_25_pips','dist_to_50_pips','dist_to_132_pips','dist_to_mlr_high_pips','dist_to_mlr_low_pips','regime_ratio','ilm_state','is_wednesday_pm','hours_since_mlr','minutes_to_12pm_est','mlr_range_pips','bias_encoded']

# Check combined
combined = pd.read_parquet(combined_dir / 'EURUSD_combined.parquet')
print(f'Combined columns ({len(combined.columns)}):')
for c in sorted(combined.columns):
    print(f'  {c}')

print('\nMICRO features:')
for f in MICRO:
    status = 'YES' if f in combined.columns else 'MISSING'
    print(f'  {f}: {status}')

print('\nMACRO features:')
for f in MACRO:
    status = 'YES' if f in combined.columns else 'MISSING'
    print(f'  {f}: {status}')

# Check labels
print('\n--- Labels dir ---')
if labels_dir.exists():
    for f in sorted(labels_dir.glob('*.parquet')):
        print(f'  {f.name}')
else:
    print('  labels dir does not exist')

# Check features
print('\n--- Features dir ---')
if features_dir.exists():
    for f in sorted(features_dir.glob('*.parquet')):
        print(f'  {f.name}')
else:
    print('  features dir does not exist')

# Check macro_features
print('\n--- Macro features dir ---')
if macro_dir.exists():
    for f in sorted(macro_dir.glob('*.parquet')):
        print(f'  {f.name}')
else:
    print('  macro_features dir does not exist')
