"""Test: trace a full session through the engine."""
import sys, os
ENGINES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engines")
sys.path.insert(0, ENGINES_DIR)
os.chdir(ENGINES_DIR)

from p90_engine import Bar
from p90_backtest import load_bars_csv
from symmetry_trap import SymmetryTrapEngine
from symmetry_trap_backtest import SymmetryTrapBacktest
from datetime import datetime, timedelta
from collections import defaultdict

csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "EURUSDPRO_M5_2023_2026.csv")
all_bars = load_bars_csv(csv_path)

days = defaultdict(list)
for bar in all_bars:
    est_dt = bar.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime("%Y-%m-%d")
    days[dk].append(bar)

bt = SymmetryTrapBacktest(pip_size=0.0001, symbol="EURUSD")

crash_count = 0
success_count = 0
for dk in sorted(days.keys())[:30]:
    day_bars = sorted(days[dk], key=lambda b: b.timestamp)
    ah, al = bt._find_asian_range(day_bars)
    if ah <= 0 or al >= 99999:
        continue
    ar_pips = (ah - al) / 0.0001
    
    eng = SymmetryTrapEngine(pip_size=0.0001, symbol="EURUSD")
    eng.initialize_session(ah, al)
    if not eng.session_active:
        continue
    
    crashed = False
    for bar in day_bars:
        try:
            sig = eng.process_bar(bar)
            if sig and sig.event == "ENTRY":
                success_count += 1
        except AttributeError as e:
            crash_count += 1
            if crash_count <= 3:
                print(f"CRASH on {dk} (AR={ar_pips:.1f}p, tier={eng.tier_name}): {e}")
                print(f"  State={eng.state.value}, swing_origin={eng.swing_origin}")
            crashed = True
            break
    
    if not crashed:
        pass  # No entry triggered

print(f"\nCrashes: {crash_count} | ENTRY signals: {success_count}")
