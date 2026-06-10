"""Profile full macro feature builder on EURUSD_M5."""
import sys, time
sys.path.insert(0, 'quant-lab/ml/phase1_data')
import pandas as pd
from macro.macro_feature_builder import build_macro_feature_matrix

df = pd.read_parquet('quant-lab/ml/data/parquet/EURUSD_M5.parquet')
print(f'Data: {df.shape[0]} bars')

# Without patterns
t0 = time.time()
r = build_macro_feature_matrix(df, pip_size=0.0001, include_patterns=False, include_time_blocks=True)
t1 = time.time()
print(f'Full pipeline (no patterns): {t1-t0:.2f}s')

# With patterns
t2 = time.time()
r2 = build_macro_feature_matrix(df, pip_size=0.0001, include_patterns=True, include_time_blocks=True)
t3 = time.time()
print(f'Full pipeline (with patterns): {t3-t2:.2f}s')

print(f'\nOutput cols: {len(r.columns)}')
print('Done.')
