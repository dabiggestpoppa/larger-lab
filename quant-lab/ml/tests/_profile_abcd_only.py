"""Profile ONLY detect_abcd on EURUSD_M5 to get time estimate."""
import sys, time
sys.path.insert(0, 'quant-lab/ml/phase1_data')
import pandas as pd
from macro.pattern_recognizer import _find_swing_points

df = pd.read_parquet('quant-lab/ml/data/parquet/EURUSD_M5.parquet')
closes = df['close'].values
highs = df['high'].values
lows = df['low'].values

print(f'Data: {len(df)} bars')

# Time swing detection
t0 = time.time()
sh, sl = _find_swing_points(closes, highs, lows)
t1 = time.time()
n_sh = sh.sum()
n_sl = sl.sum()
n_total = n_sh + n_sl
print(f'Swing detection: {t1-t0:.3f}s ({n_sh} highs, {n_sl} lows, {n_total} total)')

# Time just the AB-CD loop
from macro.pattern_recognizer import detect_abcd
t2 = time.time()
result = detect_abcd(df.copy())
t3 = time.time()
print(f'detect_abcd: {t3-t2:.3f}s')
print(f'AB-CD patterns found: {result["abcd_pattern"].sum()}')
print('Done.')
