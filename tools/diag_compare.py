"""
Compare Python ST engine vs Nautilus ST strategy for XAUUSD.
Focus on finding WHY Python produces fewer trades.
"""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab')
sys.path.insert(0, 'quant-lab/engines')
sys.path.insert(0, 'quant-lab/configs')
sys.path.insert(0, 'quant-lab/strategies')

from datetime import timedelta, time as dtime
from collections import defaultdict
from symmetry_trap import SymmetryTrapEngine, Bar, EngineState, TradeDirection, classify_tier
from symmetry_trap_backtest import load_m5_csv

# Load data
bars, _ = load_m5_csv('quant-lab/data/XAUUSD_M5.csv')
print(f'Loaded {len(bars)} bars')

# Group by EST date
days = defaultdict(list)
for b in bars:
    est_dt = b.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    days[dk].append(b)

# XAUUSD config (same as Nautilus uses)
cfg = {
    'pip_value': 0.1,
    'tiers': {
        'T1': {'ar_max': 32.0, 'au': 16.0, 'trigger': 19.0},
        'T2': {'ar_max': 58.0, 'au': 29.0, 'trigger': 35.0},
        'T3': {'ar_max': 95.0, 'au': 48.0, 'trigger': 58.0},
    }
}

# Simulate the Python campaign runner
engine = SymmetryTrapEngine(pip_size=0.1, config=cfg)

total_active = 0
total_nogo = 0
total_no_trade = 0
session_details = []

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
    if not engine.session_active:
        total_nogo += 1
        continue
    
    total_active += 1
    day_trades = 0
    impulse_detected = False
    retrace_detected = False
    
    for bar in day_bars:
        bar_est_h = (bar.timestamp.hour - 5) % 24
        if bar_est_h >= 12 and engine.state == EngineState.SEARCH:
            break
        
        sig = engine.process_bar(bar)
        if sig:
            if sig.event == 'ENTRY':
                day_trades += 1  # Count entries (will be completed or not)
            if 'Impulse' in str(sig.reason):
                impulse_detected = True
            if 'DZ' in str(sig.reason):
                retrace_detected = True
    
    if day_trades == 0:
        total_no_trade += 1
        if total_no_trade <= 10:
            pass  # debug later
    else:
        session_details.append(day_trades)

print(f'Python Results:')
print(f'Active sessions: {total_active}')
print(f'NO-GO sessions: {total_nogo}')
print(f'Active sessions with 0 trades: {total_no_trade}')
print(f'Active sessions with trades: {total_active - total_no_trade}')
print(f'Total entries across all sessions: {sum(session_details)}')
if session_details:
    print(f'Max trades in a session: {max(session_details)}')
    print(f'Mean trades per active session: {sum(session_details)/len(session_details):.2f}')
    from collections import Counter
    dist = Counter(session_details)
    for k in sorted(dist):
        print(f'  {k} trades: {dist[k]} sessions')

# Now let me trace a SPECIFIC session in detail to find the gap
# Pick a day where we know Nautilus found trades but Python didn't
print('\n=== Detailed session trace (first 3 active sessions) ===')
count = 0
for dk in sorted(days.keys()):
    if count >= 3:
        break
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
    if not engine.session_active:
        continue
    
    count += 1
    print(f'\n--- {dk} ---')
    print(f'Asian: high={ah:.2f}, low={al:.2f}, AR={engine.asian_range_pips:.1f}p, tier={engine.tier_name}')
    print(f'AU={engine.au_pips}p, trigger={engine.trigger_pips}p, active={engine.session_active}')
    
    entries = 0
    for bar in day_bars:
        bar_est_h = (bar.timestamp.hour - 5) % 24
        if bar_est_h >= 12 and engine.state == EngineState.SEARCH:
            print(f'  BREAK at {bar.timestamp} EST={bar_est_h} (SEARCH state, past noon)')
            break
        
        sig = engine.process_bar(bar)
        if sig and sig.event in ('ENTRY', 'KILL_SWITCH', 'TP_HIT', 'SL_HIT'):
            print(f'  {bar.timestamp} EST={bar_est_h}: {sig.event} - {sig.reason[:80]}')
            if sig.event == 'ENTRY':
                entries += 1
    if entries == 0:
        print(f'  NO ENTRIES this session')
    else:
        print(f'  Total entries: {entries}')
