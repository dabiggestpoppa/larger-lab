"""Debug: count sessions and trade opportunities."""
import sys, time
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

import importlib
import symmetry_trap
import symmetry_trap_backtest
importlib.reload(symmetry_trap)
importlib.reload(symmetry_trap_backtest)

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv
from copy import deepcopy

pair = 'EURUSD'
csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'

# Test with BIBLE config
cfg = deepcopy(ASSET_CONFIGS[pair])
cfg['tiers'] = {
    'T1': {'ar_max': 60.0, 'au': 10.0, 'trigger': 10.0},
    'T2': {'ar_max': 60.0, 'au': 12.0, 'trigger': 10.0},
    'T3': {'ar_max': 60.0, 'au': 15.0, 'trigger': 10.0},
}
pip_value = cfg.get('pip_value', 0.0001)

bars, _ = load_m5_csv(csv_path, pip_size=pip_value)

# Manually run the backtest with debug counting
from datetime import timedelta
from symmetry_trap import SymmetryTrapEngine, EngineState

est_offset = -5
days = {}
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=est_offset)
    dk = est_dt.strftime("%Y-%m-%d")
    if dk not in days:
        days[dk] = []
    days[dk].append(bar)

engine = SymmetryTrapEngine(pip_size=pip_value, symbol=pair, config=cfg)

total_sessions = 0
no_go_sessions = 0
sessions_with_trades = 0
total_entries = 0
total_tp = 0
total_sl = 0
total_eod = 0

for dk in sorted(days.keys()):
    day_bars = sorted(days[dk], key=lambda b: b.timestamp)
    
    # Find Asian range
    ah, al = 0.0, 99999.0
    for b in day_bars:
        h = (b.timestamp.hour + est_offset) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    
    if ah <= 0 or al >= 99999:
        continue
    
    engine.initialize_session(ah, al)
    total_sessions += 1
    
    if not engine.session_active:
        no_go_sessions += 1
        continue
    
    day_entries = 0
    
    for bar in day_bars:
        bar_est_h = (bar.timestamp.hour + est_offset) % 24
        
        if bar_est_h >= 19 or bar_est_h < 3:
            continue
        
        if bar_est_h >= 16 and engine.state == EngineState.SEARCH:
            break
        
        signal = engine.process_bar(bar)
        
        if signal and signal.event == "ENTRY":
            day_entries += 1
            total_entries += 1
        elif signal and signal.event == "TP_HIT":
            total_tp += 1
        elif signal and signal.event == "SL_HIT":
            total_sl += 1
    
    if day_entries > 0:
        sessions_with_trades += 1

print(f'Session stats:')
print(f'  Total sessions: {total_sessions}')
print(f'  NO_GO sessions (AR>60): {no_go_sessions}')
print(f'  Active sessions: {total_sessions - no_go_sessions}')
print(f'  Sessions with trades: {sessions_with_trades}')
print(f'  Total entries: {total_entries}')
print(f'  TP hits: {total_tp}')
print(f'  SL hits: {total_sl}')
print(f'  Entries without exit signal: {total_entries - total_tp - total_sl}')
print(f'  Avg trades per active session: {total_entries / (total_sessions - no_go_sessions):.2f}')
