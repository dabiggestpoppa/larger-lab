"""Test: does process_bar crash on is_bearish?"""
import sys, os
ENGINES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engines")
sys.path.insert(0, ENGINES_DIR)
os.chdir(ENGINES_DIR)

from p90_engine import Bar
from symmetry_trap import SymmetryTrapEngine
from datetime import datetime

eng = SymmetryTrapEngine(pip_size=0.0001, symbol="EURUSD")
# Initialize with a T1 session (AR=15p)
eng.initialize_session(asian_high=1.1000, asian_low=1.09985)  # 1.5p AR... wait that's too small

# AR = 15 pips = 0.0015
eng.initialize_session(asian_high=1.1000, al=1.0985)  # AR = 15p
print(f"session_active={eng.session_active}, tier={eng.tier_name}")
print(f"AU={eng.au_pips}, trigger={eng.trigger_pips}")

# Feed a bar that triggers LONG impulse (> trigger = 12p from swing_origin)
bar1 = Bar(timestamp=datetime(2024,1,15,4,0), open=1.0985, high=1.1000, low=1.0983, close=1.0998)
sig = eng.process_bar(bar1)
print(f"Bar1: state={eng.state.value}, swing_origin={eng.swing_origin}")

# Feed a bar that exceeds trigger
bar2 = Bar(timestamp=datetime(2024,1,15,4,5), open=1.0998, high=1.09995, low=1.0996, close=1.0999)
# swing_origin = 1.0985 (first bar close). trigger = 12p = 0.0012. Need high >= 1.0985+0.0012 = 1.0997
print(f"Need high >= {eng.swing_origin + eng.trigger_pips * eng.pip_size:.5f}")
sig = eng.process_bar(bar2)
print(f"Bar2: state={eng.state.value}, impulse_dir={eng.impulse_direction}")

# Now feed a WAIT_OCC bar
bar3 = Bar(timestamp=datetime(2024,1,15,4,10), open=1.0998, high=1.1001, low=1.0997, close=1.10005)
try:
    sig = eng.process_bar(bar3)
    print(f"Bar3: state={eng.state.value}, signal={sig.event if sig else None}")
except AttributeError as e:
    print(f"CRASH: {e}")
