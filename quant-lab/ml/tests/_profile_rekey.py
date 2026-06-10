"""Profile rekey_state on EURUSD_M5."""
import sys, time
sys.path.insert(0, 'quant-lab/ml/phase1_data')
import pandas as pd
from macro.mlr_engine import compute_mlr_features, compute_fib_targets
from macro.kill_switch import compute_132_proximity, compute_rekey_state

df = pd.read_parquet('quant-lab/ml/data/parquet/EURUSD_M5.parquet')
print(f'Data: {len(df)} bars')

# Pre-compute everything up to rekey_state
t0 = time.time()
r = compute_mlr_features(df.copy())
r = compute_fib_targets(r)
r = compute_132_proximity(r, pip_size=0.0001)
t1 = time.time()
print(f'Pre-MLR+prox: {t1-t0:.3f}s')

# Now profile rekey_state alone
t2 = time.time()
r2 = compute_rekey_state(r, pip_size=0.0001)
t3 = time.time()
print(f'rekey_state: {t3-t2:.3f}s')
print(f'Rekey states: {r2["rekey_state"].value_counts().to_dict()}')
print(f'Breached: {(r2["rekey_state"] == 3).sum()}')
print('Done.')
