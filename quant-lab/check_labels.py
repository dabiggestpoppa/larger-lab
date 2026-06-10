import pandas as pd
df = pd.read_parquet('ml/data/training/EURUSD_training.parquet')
print('Shape:', df.shape)
print('Label columns:')
for c in df.columns:
    if 'label' in c.lower() or 'target' in c.lower() or 'hit' in c.lower():
        vals = df[c].dropna()
        if len(vals) > 0:
            print(f'  {c}: {vals.value_counts().to_dict()}')
        else:
            print(f'  {c}: all NaN')
