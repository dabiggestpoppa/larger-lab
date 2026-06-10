"""Profile MLR engine on full EURUSD_M5."""
import sys, time
sys.path.insert(0, 'quant-lab/ml/phase1_data')
import pandas as pd
from macro.mlr_engine import compute_mlr_features, compute_fib_targets

df = pd.read_parquet('quant-lab/ml/data/parquet/EURUSD_M5.parquet')
print(f'Data: {df.shape[0]} bars')

# Test with smaller subset first
for n in [1000, 10000, 50000, 100000, 463103]:
    subset = df.iloc[:n]
    t0 = time.time()
    r = compute_mlr_features(subset.copy())
    t1 = time.time()
    print(f'n={n:>7}: {t1-t0:.3f}s')

print('\nFib targets on full:')
t0 = time.time()
r2 = compute_fib_targets(r.copy())
t1 = time.time()
print(f'fib_targets: {t1-t0:.3f}s')
print('Done.')
