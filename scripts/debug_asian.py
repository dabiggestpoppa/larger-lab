"""Debug: check Asian range detection and session initialization."""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

import importlib
import symmetry_trap
import symmetry_trap_backtest
importlib.reload(symmetry_trap)
importlib.reload(symmetry_trap_backtest)

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv
from symmetry_trap import SymmetryTrapEngine, EngineState
from copy import deepcopy
from datetime import timedelta

pair = 'EURUSD'
csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'

cfg = deepcopy(ASSET_CONFIGS[pair])
cfg['tiers'] = {
    'T1': {'ar_max': 60.0, 'au': 10.0, 'trigger': 12.0},
    'T2': {'ar_max': 60.0, 'au': 12.0, 'trigger': 15.0},
    'T3': {'ar_max': 60.0, 'au': 15.0, 'trigger': 19.0},
}
pip_value = cfg.get('pip_value', 0.0001)

bars, _ = load_m5_csv(csv_path, pip_size=pip_value)

est_offset = -5
days = {}
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=est_offset)
    dk = est_dt.strftime("%Y-%m-%d")
    if dk not in days:
        days[dk] = []
    days[dk].append(bar)

# Check Asian range for first few days
print('First 10 days Asian range check:')
for dk in sorted(days.keys())[:10]:
    day_bars = sorted(days[dk], key=lambda b: b.timestamp)
    ah, al = 0.0, 99999.0
    for b in day_bars:
        h = (b.timestamp.hour + est_offset) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    
    ar_pips = (ah - al) / pip_value if ah > 0 and al < 99999 else 0
    print(f'  {dk}: AH={ah:.5f}, AL={al:.5f}, AR={ar_pips:.1f}p, bars={len(day_bars)}')

# Count active vs NO_GO
active = 0
no_go = 0
for dk in sorted(days.keys()):
    day_bars = sorted(days[dk], key=lambda b: b.timestamp)
    ah, al = 0.0, 99999.0
    for b in day_bars:
        h = (b.timestamp.hour + est_offset) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    if ah <= 0 or al >= 99999:
        continue
    ar_pips = (ah - al) / pip_value
    if ar_pips > 60:
        no_go += 1
    else:
        active += 1

print(f'\nSession summary:')
print(f'  Active (AR<=60): {active}')
print(f'  NO_GO (AR>60): {no_go}')
print(f'  Total with data: {active + no_go}')
