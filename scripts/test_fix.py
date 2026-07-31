"""Test PRO CSV loading after fix."""
import sys, time
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')
from symmetry_trap_backtest import load_m5_csv

# Test PRO format
csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\AUDCAD_PRO_M5.csv'
t0 = time.time()
bars, sym = load_m5_csv(csv_path, pip_size=0.0001)
print('AUDCAD_PRO: %d bars in %.2fs' % (len(bars), time.time() - t0))
if bars:
    print('  First:', bars[0].timestamp, bars[0].open, bars[0].close)
    print('  Last:', bars[-1].timestamp, bars[-1].open, bars[-1].close)

# Test regular format still works
csv_path2 = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'
t0 = time.time()
bars2, sym2 = load_m5_csv(csv_path2, pip_size=0.0001)
print('EURUSD: %d bars in %.2fs' % (len(bars2), time.time() - t0))
