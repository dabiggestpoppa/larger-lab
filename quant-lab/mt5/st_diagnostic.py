"""Quick diagnostic: why is ST engine not firing?"""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab')

from engines.symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection, classify_tier
from datetime import datetime, timedelta
import random

# Simulate a session with GBPAUD-like data
# T3 day: AR ~40 pips, AU=15p, trigger=19p

engine = SymmetryTrapEngine(pip_size=0.0001, symbol="GBPAUD.PRO")
engine.initialize_session(
    asian_high=1.87500,
    asian_low=1.87100,
)

print(f"Session active: {engine.session_active}")
print(f"Tier: {engine.tier_name}, AU: {engine.au_pips}p, Trigger: {engine.trigger_pips}p")
print(f"AR: {engine.asian_range_pips:.1f}p")
print()

# Simulate M5 bars during trading session
# Start with some bars that move gradually (no impulse)
base_price = 1.87300  # middle of Asian range

# Phase 1: small bars, no impulse
print("=== PHASE 1: Small bars (< trigger) ===")
for i in range(10):
    noise = random.uniform(-0.0003, 0.0003)
    bar = Bar(
        timestamp=datetime(2026, 6, 2, 3, i*5),
        open=base_price,
        high=base_price + 0.0002,
        low=base_price - 0.0002,
        close=base_price + noise,
    )
    sig = engine.process_bar(bar)
    if sig:
        print(f"  Bar {i}: {sig.event} - {sig.reason}")

print(f"State after phase 1: {engine.state.value}, swing_origin: {engine.swing_origin}")

# Phase 2: impulse bar (move 25 pips down)
print("\n=== PHASE 2: Impulse bar (25 pip move) ===")
impulse_bar = Bar(
    timestamp=datetime(2026, 6, 2, 3, 50),
    open=base_price,
    high=base_price + 0.0001,
    low=base_price - 0.0025,  # 25 pip drop
    close=base_price - 0.0023,
)
sig = engine.process_bar(impulse_bar)
if sig:
    print(f"  Signal: {sig.event} - {sig.reason}")
print(f"State: {engine.state.value}")
print(f"Impulse direction: {engine.impulse_direction}")
print(f"Impulse extreme: {engine.impulse_extreme}")
print(f"Impulse size: {engine.impulse_size_pips:.1f}p")
print(f"Kill switch: {engine.kill_switch_level:.5f}")

# Phase 3: retracement into DZ
print("\n=== PHASE 3: Retracement into DZ ===")
# DZ = 32-50% of 25 pips = 8-12.5 pips from extreme
# Extreme is at 1.8705, so DZ is 1.8705 + 0.0008 to 1.8705 + 0.00125
# = 1.8713 to 1.87175
retrace_target = 1.8715  # in the DZ

for i in range(5):
    bar = Bar(
        timestamp=datetime(2026, 6, 2, 3, 55 + i*5),
        open=base_price - 0.0023 + i*0.0002,
        high=base_price - 0.0023 + i*0.0003,
        low=base_price - 0.0023 + i*0.0001,
        close=base_price - 0.0023 + i*0.0002,
    )
    sig = engine.process_bar(bar)
    if sig:
        print(f"  Bar {i}: {sig.event} - {sig.reason}")
        if sig.event == "ENTRY":
            print(f"    Entry: {sig.entry_price:.5f}, SL: {sig.sl_price:.5f}, TP: {sig.tp_price:.5f}")
    else:
        print(f"  Bar {i}: state={engine.state.value}, pullback_pips not in DZ yet")

print(f"State: {engine.state.value}")

# Phase 4: OCC confirmation
if engine.state.value == "WAIT_OCC":
    print("\n=== PHASE 4: OCC confirmation (bullish bar for SHORT) ===")
    # For SHORT, we need a bearish OCC candle (close < open, closing in impulse direction)
    # Wait — for SHORT impulse, OCC should close DOWN (in impulse direction)
    occ_bar = Bar(
        timestamp=datetime(2026, 6, 2, 4, 25),
        open=1.8715,
        high=1.8717,
        low=1.8710,
        close=1.8711,  # bearish, closing down
    )
    sig = engine.process_bar(occ_bar)
    if sig:
        print(f"  Signal: {sig.event}")
        if sig.event == "ENTRY":
            print(f"    Entry: {sig.entry_price:.5f}, SL: {sig.sl_price:.5f}, TP: {sig.tp_price:.5f}")
            sl_pips = abs(sig.sl_price - sig.entry_price) / 0.0001
            tp_pips = abs(sig.tp_price - sig.entry_price) / 0.0001
            print(f"    SL distance: {sl_pips:.1f}p, TP distance: {tp_pips:.1f}p")
    else:
        print(f"  No signal, state: {engine.state.value}")

print("\n=== DIAGNOSIS ===")
print(f"Final state: {engine.state.value}")
print(f"Loop count: {engine.loop_count}")
print(f"Session active: {engine.session_active}")
