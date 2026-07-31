"""Check training data and run training."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

# Check manifest
m = json.loads(Path('quant-lab/ml/data/training/manifest.json').read_text())
print('Training data manifest:')
print(f'  Assets: {len(m)}')
total_rows = sum(v['rows'] for v in m.values())
print(f'  Total rows: {total_rows:,}')
first = list(m.values())[0]
print(f'  Features per asset: {first["features"]}')
print(f'  Feature list: {first["feature_names"][:10]}...')

# Quick check of one file
df = pd.read_parquet('quant-lab/ml/data/training/EURUSD_training.parquet')
print(f'\nEURUSD training: {df.shape}')
print(f'Columns: {list(df.columns)}')

# Check label distribution
for col in ['label_25_delivery', 'label_50_delivery', 'rekey_triggered', 'regime_at_time']:
    if col in df.columns:
        print(f'{col}: {dict(df[col].value_counts())}')

# Check for NaN in features
feat_cols = [c for c in df.columns if c not in ['label_25_delivery', 'label_50_delivery', 'rekey_triggered', 'regime_at_time']]
nan_count = df[feat_cols].isna().sum().sum()
print(f'\nTotal NaN in features: {nan_count}')
print('NaN per column:')
for c in feat_cols:
    n = df[c].isna().sum()
    if n > 0:
        print(f'  {c}: {n}')
