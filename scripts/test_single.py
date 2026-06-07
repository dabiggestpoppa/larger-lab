"""Test single pair CSV load."""
import sys, os, time
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')
from symmetry_trap_backtest import load_m5_csv

csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'
print('Loading EURUSD...')
t0 = time.time()
bars, sym = load_m5_csv(csv_path, pip_size=0.0001)
print('Done: %d bars in %.2fs' % (len(bars), time.time() - t0))
