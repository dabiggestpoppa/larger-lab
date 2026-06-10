"""Profile the macro engine on EURUSD_M2 to find bottlenecks."""
import sys, time
sys.path.insert(0, 'quant-lab/ml/phase1_data')

import pandas as pd
from macro.macro_feature_builder import build_macro_feature_matrix
from macro.ilm_detector import _get_session_series, _compute_daily_df, compute_ilm_state, compute_regime_ratio
from macro.mlr_engine import compute_mlr_features, compute_fib_targets
from macro.kill_switch import compute_132_proximity, compute_rekey_state

df = pd.read_parquet('quant-lab/ml/data/parquet/EURUSD_M5.parquet')
print(f'Data: {df.shape[0]} bars')

t0 = time.time()
session_s = _get_session_series(df.index)
t1 = time.time()
print(f'_get_session_series: {t1-t0:.2f}s')

daily = _compute_daily_df(df, 0.0001)
t2 = time.time()
print(f'_compute_daily_df: {t2-t1:.2f}s')

# Test map speed
r = session_s.map(daily['regime_ratio'])
t3 = time.time()
print(f'session_s.map(): {t3-t2:.2f}s')

# Test full ILM
df2 = compute_ilm_state(df.copy(), 0.0001)
t4 = time.time()
print(f'compute_ilm_state: {t4-t3:.2f}s')

df2 = compute_regime_ratio(df2, 0.0001)
t5 = time.time()
print(f'compute_regime_ratio: {t5-t4:.2f}s')

# Test MLR
df3 = compute_mlr_features(df.copy())
t6 = time.time()
print(f'compute_mlr_features: {t6-t5:.2f}s')

df3 = compute_fib_targets(df3)
t7 = time.time()
print(f'compute_fib_targets: {t7-t6:.2f}s')

df3 = compute_132_proximity(df3, pip_size=0.0001)
t8 = time.time()
print(f'compute_132_proximity: {t8-t7:.2f}s')

df3 = compute_rekey_state(df3, pip_size=0.0001)
t9 = time.time()
print(f'compute_rekey_state: {t9-t8:.2f}s')

print(f'\nTotal would be: {t9-t0:.2f}s (without patterns/timeblocks)')
print('Done.')
