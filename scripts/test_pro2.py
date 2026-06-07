"""Test PRO CSV load with timing."""
import sys, time
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

# Force reload to pick up the fix
import symmetry_trap_backtest
import importlib
importlib.reload(symmetry_trap_backtest)
from symmetry_trap_backtest import load_m5_csv

csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\AUDCAD_PRO_M5.csv'
print('Loading AUDCAD_PRO...')
t0 = time.time()
bars, sym = load_m5_csv(csv_path, pip_size=0.0001)
elapsed = time.time() - t0
print('Result: %d bars, sym=%s, time=%.1fs' % (len(bars), sym, elapsed))
