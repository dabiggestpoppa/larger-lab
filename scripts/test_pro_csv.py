"""Test loading PRO CSVs."""
import sys, os, time
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')
from symmetry_trap_backtest import load_m5_csv

data_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data'
pro_files = [f for f in os.listdir(data_dir) if '_PRO_M5.csv' in f]

for fname in sorted(pro_files):
    csv_path = os.path.join(data_dir, fname)
    size = os.path.getsize(csv_path) / 1024 / 1024
    t0 = time.time()
    try:
        bars, sym = load_m5_csv(csv_path, pip_size=0.0001)
        elapsed = time.time() - t0
        print('%-25s %5.1fMB -> %6d bars in %.1fs' % (fname, size, len(bars), elapsed))
    except Exception as e:
        elapsed = time.time() - t0
        print('%-25s %5.1fMB -> ERROR: %s (%.1fs)' % (fname, size, str(e)[:50], elapsed))
