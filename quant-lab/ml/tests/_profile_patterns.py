"""Profile pattern detection on EURUSD_M5."""
import sys, time
sys.path.insert(0, 'quant-lab/ml/phase1_data')
import pandas as pd
import numpy as np
from macro.pattern_recognizer import (
    _find_swing_points, _detect_3leg_pattern,
    detect_alpha_leg, detect_beta_leg, detect_abcd, detect_occ_extreme
)

df = pd.read_parquet('quant-lab/ml/data/parquet/EURUSD_M5.parquet')
closes = df['close'].values
highs = df['high'].values
lows = df['low'].values
n = len(df)
print(f'Data: {n} bars')

for size in [1000, 10000, 50000, 100000, 463103]:
    c = closes[:size]
    h = highs[:size]
    l = lows[:size]

    t0 = time.time()
    sh, sl = _find_swing_points(c, h, l)
    t1 = time.time()
    n_swings = sh.sum() + sl.sum()

    t2 = time.time()
    _detect_3leg_pattern(c, h, l, 0.72)
    t3 = time.time()

    print(f'n={size:>7}: swing={t1-t0:.3f}s ({n_swings} swings), 3leg={t3-t2:.3f}s')

print('\nOcc extreme on full:')
t0 = time.time()
detect_occ_extreme(df.copy())
t1 = time.time()
print(f'occ_extreme: {t1-t0:.3f}s')

print('\nAlpha on full:')
t2 = time.time()
detect_alpha_leg(df.copy())
t3 = time.time()
print(f'alpha: {t3-t2:.3f}s')

print('\nDone.')
