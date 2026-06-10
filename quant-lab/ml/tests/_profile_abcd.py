"""Profile AB-CD detection on EURUSD_M5."""
import sys, time
sys.path.insert(0, 'quant-lab/ml/phase1_data')
import pandas as pd
from macro.pattern_recognizer import detect_abcd, detect_beta_leg

df = pd.read_parquet('quant-lab/ml/data/parquet/EURUSD_M5.parquet')
print(f'Data: {len(df)} bars')

t0 = time.time()
r = detect_beta_leg(df.copy())
t1 = time.time()
print(f'beta_leg: {t1-t0:.3f}s')

t2 = time.time()
r2 = detect_abcd(df.copy())
t3 = time.time()
print(f'abcd: {t3-t2:.3f}s')

print('Done.')
