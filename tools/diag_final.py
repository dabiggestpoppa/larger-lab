"""
Final diagnostic: Run Python ST engine on XAUUSD with FULL detailed output.
Count: sessions, NO-GO, active-no-trade, active-with-trade, total trades.
Then trace a few specific days to find WHERE trades are being missed.
"""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab/engines')
sys.path.insert(0, 'quant-lab/configs')

from datetime import timedelta
from collections import defaultdict, Counter
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

engine = SymmetryTrapEngine(pip_size=0.1, config=cfg)

results = {
    'total_days': 0, 'nogo': 0, 'active': 0,
    'active_no_trade': 0, 'active_with_trade': 0,
    'total_entries': 0, 'total_tp': 0, 'total_sl': 0, 'total_ks': 0,
    'impulse_no_retrace': 0, 'retrace_no_occ': 0,
    'sessions_with_impulse': 0, 'sessions_with_retrace': 0, 'sessions_with_occ': 0,
}

# Track per-session stats
session_stats = []

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
    
    results['total_days'] += 1
    engine.initialize_session(ah, al)
    
    if not engine.session_active:
        results['nogo'] += 1
        continue
    
    results['active'] += 1
    day_entries = 0
    day_tp = 0
    day_sl = 0
    day_ks = 0
    had_impulse = False
    had_retrace = False
    had_occ = False
    states_hit = set()
    
    for bar in day_bars:
        bar_est_h = (bar.timestamp.hour - 5) % 24
        if bar_est_h >= 12 and engine.state == EngineState.SEARCH:
            break
        
        prev_state = engine.state
        sig = engine.process_bar(bar)
        states_hit.add(engine.state)
        
        if engine.state != prev_state:
            if engine.state == EngineState.WAIT_RETRACE:
                had_impulse = True
            elif engine.state == EngineState.WAIT_OCC:
                had_retrace = True
            elif engine.state == EngineState.IN_TRADE:
                had_occ = True
        
        if sig:
            if sig.event == 'ENTRY':
                day_entries += 1
            elif sig.event == 'TP_HIT':
                day_tp += 1
            elif sig.event == 'SL_HIT':
                day_sl += 1
            elif sig.event == 'KILL_SWITCH':
                day_ks += 1
    
    if had_impulse:
        results['sessions_with_impulse'] += 1
    if had_retrace:
        results['sessions_with_retrace'] += 1
    if had_occ:
        results['sessions_with_occ'] += 1
    
    results['total_entries'] += day_entries
    results['total_tp'] += day_tp
    results['total_sl'] += day_sl
    results['total_ks'] += day_ks
    
    if day_entries == 0:
        results['active_no_trade'] += 1
    else:
        results['active_with_trade'] += 1
    
    session_stats.append({
        'date': dk, 'entries': day_entries, 'tp': day_tp, 'sl': day_sl,
        'ks': day_ks, 'tier': engine.tier_name, 
        'had_impulse': had_impulse, 'had_retrace': had_retrace, 'had_occ': had_occ,
        'final_state': engine.state.value
    })

print("=== XAUUSD PYTHON ENGINE FULL DIAGNOSTIC ===")
print(f"Total days with Asian data: {results['total_days']}")
print(f"NO-GO sessions: {results['nogo']} ({results['nogo']/results['total_days']*100:.1f}%)")
print(f"Active sessions: {results['active']} ({results['active']/results['total_days']*100:.1f}%)")
print(f"  With trades: {results['active_with_trade']}")
print(f"  Without trades: {results['active_no_trade']}")
print()
print(f"Total entries: {results['total_entries']}")
print(f"Total TP: {results['total_tp']}")
print(f"Total SL: {results['total_sl']}")
print(f"Total Kill Switches: {results['total_ks']}")
print(f"Completed trades: {results['total_tp'] + results['total_sl']}")
print()
print(f"Sessions with impulse detected: {results['sessions_with_impulse']}")
print(f"Sessions with retrace (WAIT_OCC): {results['sessions_with_retrace']}")
print(f"Sessions with OCC (ENTRY): {results['sessions_with_occ']}")
print()

# Funnel analysis
print("=== TRADE FUNNEL ===")
print(f"Active sessions: {results['active']}")
print(f"  → Impulse detected: {results['sessions_with_impulse']} ({results['sessions_with_impulse']/max(results['active'],1)*100:.1f}%)")
print(f"  → Retrace qualified: {results['sessions_with_retrace']} ({results['sessions_with_retrace']/max(results['sessions_with_impulse'],1)*100:.1f}% of impulses)")
print(f"  → OCC confirmed (entry): {results['sessions_with_occ']} ({results['sessions_with_occ']/max(results['sessions_with_retrace'],1)*100:.1f}% of retraces)")
print()

# Analyze the no-trade sessions
print("=== NO-TRADE SESSION ANALYSIS ===")
no_trade_tiers = Counter(s['tier'] for s in session_stats if s['entries'] == 0)
trade_tiers = Counter(s['tier'] for s in session_stats if s['entries'] > 0)
print(f"No-trade sessions by tier: {dict(no_trade_tiers)}")
print(f"Trade sessions by tier: {dict(trade_tiers)}")

no_trade_impulse = sum(1 for s in session_stats if s['entries'] == 0 and s['had_impulse'])
no_trade_retrace = sum(1 for s in session_stats if s['entries'] == 0 and s['had_retrace'])
no_trade_no_impulse = sum(1 for s in session_stats if s['entries'] == 0 and not s['had_impulse'])
print(f"No-trade sessions that HAD impulse: {no_trade_impulse}")
print(f"No-trade sessions that HAD retrace: {no_trade_retrace}")
print(f"No-trade sessions with NO impulse: {no_trade_no_impulse}")

# List sample no-trade sessions
print("\nSample no-trade sessions:")
count = 0
for s in session_stats:
    if s['entries'] == 0 and count < 5:
        print(f"  {s['date']}: tier={s['tier']}, impulse={s['had_impulse']}, retrace={s['had_retrace']}, final_state={s['final_state']}")
        count += 1

# Sample trade sessions
print("\nSample trade sessions:")
count = 0
for s in session_stats:
    if s['entries'] > 0 and count < 5:
        print(f"  {s['date']}: tier={s['tier']}, entries={s['entries']}, tp={s['tp']}, sl={s['sl']}, ks={s['ks']}")
        count += 1
