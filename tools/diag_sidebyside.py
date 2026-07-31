"""
Side-by-side comparison: Python ST engine vs Nautilus ST strategy for XAUUSD.
Pick ONE active session and trace impulse-by-impulse.
"""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab')
sys.path.insert(0, 'quant-lab/engines')
sys.path.insert(0, 'quant-lab/configs')
sys.path.insert(0, 'quant-lab/strategies')

from datetime import timedelta, time as dtime
from collections import defaultdict
from symmetry_trap import SymmetryTrapEngine, Bar, EngineState, TradeDirection
from symmetry_trap_backtest import load_m5_csv
from quant_lab.configs.asset_configs import ASSET_CONFIGS

bars, _ = load_m5_csv('quant-lab/data/XAUUSD_M5.csv')
cfg = ASSET_CONFIGS['XAUUSD']

# Group by EST date
days = defaultdict(list)
for b in bars:
    est_dt = b.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    days[dk].append(b)

# Find the FIRST active session (not NO-GO)
engine = SymmetryTrapEngine(pip_size=0.1, config=cfg)
first_dk = None
first_day_bars = None

for dk in sorted(days.keys()):
    day_bars = sorted(days[dk], key=lambda b: b.timestamp)
    ah, al = 0.0, 99999.0
    for b in day_bars:
        est_h = (b.timestamp.hour - 5) % 24
        if est_h >= 19 or est_h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    if ah <= 0 or al >= 99999:
        continue
    engine.initialize_session(ah, al)
    if engine.session_active:
        first_dk = dk
        first_day_bars = day_bars
        break

print(f'First active session: {first_dk}')
print(f'Asian: high={engine.asian_high:.2f}, low={engine.asian_low:.2f}')
print(f'AR={engine.asian_range_pips:.1f}p, tier={engine.tier_name}')
print(f'AU={engine.au_pips}p, trigger={engine.trigger_pips}p')

# Now trace every bar in this day through the Python engine
# Log state machine transitions
os.makedirs('tools/logs', exist_ok=True)
log_lines = []
entries = 0
state_changes = 0
prev_state = engine.state

for bar in first_day_bars:
    bar_est_h = (bar.timestamp.hour - 5) % 24
    
    if bar_est_h >= 12 and engine.state == EngineState.SEARCH:
        log_lines.append(f'{bar.timestamp} EST={bar_est_h}: BREAK (SEARCH at noon)')
        break
    
    sig = engine.process_bar(bar)
    
    if engine.state != prev_state:
        state_changes += 1
        log_lines.append(f'{bar.timestamp} EST={bar_est_h}: STATE {prev_state.value} -> {engine.state.value}')
        prev_state = engine.state
    
    if sig is not None:
        log_lines.append(f'{bar.timestamp} EST={bar_est_h}: SIGNAL {sig.event} (loop={sig.loop_count}) - {sig.reason[:100]}')
        if sig.event == 'ENTRY':
            entries += 1

print(f'Total entries in first session: {entries}')
print(f'State changes: {state_changes}')

print('\nDetailed trace:')
for line in log_lines:
    print(line)

# Now compare: what would Nautilus do differently on this same day?
# Key differences to check:
# 1. Nautilus sets swing_origin from init bar and returns (skipping impulse check on init bar)
# 2. Python processes ALL bars through process_bar including Asian ones
# 3. Nautilus explicitly returns during Asian hours
# 4. Python's impulse detection runs on Asian bars too (after init)

# The most important question: does the Python engine process Asian bars AFTER session init?
# If it does, impulse detection runs during Asian hours too.
# During Asian hours, price is ranging, so impulse could be triggered by noise.

print('\n=== Checking Asian bar processing in Python run() ===')
for bar in first_day_bars[:10]:
    est_h = (bar.timestamp.hour - 5) % 24
    is_asian = est_h >= 19 or est_h < 3
    print(f'{bar.timestamp} EST={est_h} asian={is_asian}')
