"""
Check if Asian bars trigger impulse detection in Python engine.
The Nautilus strategy explicitly skips Asian bars - Python does NOT.
This could cause Python to detect impulses during Asian hours that
either: (a) lead to early kill switches, or (b) miss valid setups.
"""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab/engines')
sys.path.insert(0, 'quant-lab/configs')

from datetime import timedelta
from collections import defaultdict
from symmetry_trap import SymmetryTrapEngine, EngineState
from symmetry_trap_backtest import load_m5_csv
from quant_lab.configs.asset_configs import ASSET_CONFIGS

bars, _ = load_m5_csv('quant-lab/data/XAUUSD_M5.csv')
cfg = ASSET_CONFIGS['XAUUSD']

days = defaultdict(list)
for b in bars:
    est_dt = b.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime('%Y-%m-%d')
    days[dk].append(b)

engine = SymmetryTrapEngine(pip_size=0.1, config=cfg)

asian_impulse_count = 0
asian_trigger_sessions = []
total_active = 0

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
        continue

    total_active += 1
    impulse_in_asian = False
    impulse_bar_time = None

    for bar in day_bars:
        bar_est_h = (bar.timestamp.hour - 5) % 24
        if bar_est_h >= 12 and engine.state == EngineState.SEARCH:
            break

        prev_state = engine.state
        sig = engine.process_bar(bar)

        # Check if impulse was detected during Asian hours
        if (bar_est_h >= 19 or bar_est_h < 3) and engine.state == EngineState.WAIT_RETRACE and prev_state == EngineState.SEARCH:
            impulse_in_asian = True
            impulse_bar_time = f"{bar.timestamp} EST={bar_est_h}h"

    if impulse_in_asian:
        asian_impulse_count += 1
        if len(asian_trigger_sessions) < 10:
            asian_trigger_sessions.append((dk, impulse_bar_time, engine.tier_name, f"{engine.asian_range_pips:.1f}p"))

print(f"Total active sessions: {total_active}")
print(f"Sessions with impulse during Asian hours: {asian_impulse_count} ({asian_impulse_count/total_active*100:.1f}%)")
print(f"\nSample sessions with Asian impulse:")
for dk, time, tier, ar in asian_trigger_sessions:
    print(f"  {dk}: impulse at {time}, tier={tier}, AR={ar}")

# Now: what % of these Asian-impulse sessions end up with NO valid trade?
# Reset and re-run to check
print("\n=== Checking if Asian impulse leads to failed sessions ===")
no_trade_asian_impulse = 0
trade_asian_impulse = 0
no_trade_no_asian = 0
trade_no_asian = 0

engine2 = SymmetryTrapEngine(pip_size=0.1, config=cfg)

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

    engine2.initialize_session(ah, al)
    if not engine2.session_active:
        continue

    impulse_in_asian = False
    entries = 0

    for bar in day_bars:
        bar_est_h = (bar.timestamp.hour - 5) % 24
        if bar_est_h >= 12 and engine2.state == EngineState.SEARCH:
            break
        prev_state = engine2.state
        sig = engine2.process_bar(bar)
        if (bar_est_h >= 19 or bar_est_h < 3) and engine2.state == EngineState.WAIT_RETRACE and prev_state == EngineState.SEARCH:
            impulse_in_asian = True
        if sig and sig.event == 'ENTRY':
            entries += 1

    if impulse_in_asian:
        if entries == 0:
            no_trade_asian_impulse += 1
        else:
            trade_asian_impulse += 1
    else:
        if entries == 0:
            no_trade_no_asian += 1
        else:
            trade_no_asian += 1

print(f"Asian impulse -> no trade: {no_trade_asian_impulse}")
print(f"Asian impulse -> has trade: {trade_asian_impulse}")
print(f"No Asian impulse -> no trade: {no_trade_no_asian}")
print(f"No Asian impulse -> has trade: {trade_no_asian}")
print(f"\nTrade rate with Asian impulse: {trade_asian_impulse/(trade_asian_impulse+no_trade_asian_impulse)*100:.1f}%")
print(f"Trade rate without Asian impulse: {trade_no_asian/(trade_no_asian+no_trade_no_asian)*100:.1f}%")
