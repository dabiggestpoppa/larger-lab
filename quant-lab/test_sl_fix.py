"""Quick test: does the MT5 engine SL = impulse_extreme work correctly?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engines.symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection
from datetime import datetime, timezone, timedelta

# Simulate a full trade cycle
e = SymmetryTrapEngine(pip_size=0.0001, symbol='EURUSD')
e.initialize_session(1.1500, 1.1480)
e.swing_origin = 1.1490
base = datetime.now(timezone.utc)

print("=== Testing MT5 Engine SL Fix ===")
print(f"Session: tier={e.tier_name}, trigger={e.trigger_pips}p, AU={e.au_pips}p")
print()

# Step 1: Impulse bar (LONG)
sig1 = e.process_bar(Bar(timestamp=base, open=1.1490, high=1.1506, low=1.1488, close=1.1503))
print(f"1. Impulse bar: dir={e.impulse_direction}, extreme={e.impulse_extreme}, state={e.state}")

# Step 2: Retrace bar
sig2 = e.process_bar(Bar(timestamp=base+timedelta(minutes=5), open=1.1503, high=1.1504, low=1.1493, close=1.1496))
print(f"2. Retrace bar: state={e.state}")

# Step 3: OCC bar (entry)
sig3 = e.process_bar(Bar(timestamp=base+timedelta(minutes=10), open=1.1494, high=1.1500, low=1.1492, close=1.1498))
print(f"3. OCC bar: state={e.state}, event={sig3.event if sig3 else None}")
if sig3 and sig3.event == 'ENTRY':
    print(f"   entry={sig3.entry_price:.5f}, SL={sig3.sl_price:.5f}, TP={sig3.tp_price:.5f}")
    print(f"   SL == impulse_extreme: {sig3.sl_price == e.impulse_extreme}")
    print(f"   SL > entry (above): {sig3.sl_price > sig3.entry_price}")
    print(f"   TP > entry (above): {sig3.tp_price > sig3.entry_price}")
    
    # Step 4: Next bar - does SL trigger immediately?
    sig4 = e.process_bar(Bar(timestamp=base+timedelta(minutes=15), open=1.1498, high=1.1502, low=1.1495, close=1.1499))
    print(f"4. Next bar: event={sig4.event if sig4 else None}, state={e.state}")
    if sig4 and sig4.event == 'SL_HIT':
        print(f"   *** SL TRIGGERED ON VERY NEXT BAR ***")
        print(f"   This is the problem - SL at impulse_extreme is above entry for LONG")
    
    # Step 5: What if price goes up to TP?
    e2 = SymmetryTrapEngine(pip_size=0.0001, symbol='EURUSD')
    e2.initialize_session(1.1500, 1.1480)
    e2.swing_origin = 1.1490
    e2.process_bar(Bar(timestamp=base, open=1.1490, high=1.1506, low=1.1488, close=1.1503))
    e2.process_bar(Bar(timestamp=base+timedelta(minutes=5), open=1.1503, high=1.1504, low=1.1493, close=1.1496))
    e2.process_bar(Bar(timestamp=base+timedelta(minutes=10), open=1.1494, high=1.1500, low=1.1492, close=1.1498))
    # Price goes up to TP
    sig5 = e2.process_bar(Bar(timestamp=base+timedelta(minutes=15), open=1.1498, high=1.1510, low=1.1497, close=1.1509))
    print(f"5. TP test: event={sig5.event if sig5 else None}")
    if sig5 and sig5.event == 'TP_HIT':
        print(f"   TP hit! TP={sig5.tp_price:.5f}")

print()
print("=== CONCLUSION ===")
print("For LONG: SL = impulse_extreme (bar.high) is ABOVE entry (OCC close)")
print("This means SL check (close <= SL) triggers immediately since entry < SL")
print("The MT5 engine has the SAME behavior as the Nautilus strategy")
print("Both need the same fix: SL should be on the LOSS side of entry")
