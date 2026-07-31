"""Debug — trace _reset_state calls with stack trace"""
import sys, json, traceback
from datetime import datetime, timezone, timedelta
sys.path.insert(0, 'quant-lab/engines')
from symmetry_trap_simple_sl import SymmetryTrapEngineSimpleSL, Bar

with open('quant-lab/data/btc_5m_4yr.json') as f:
    candles = json.load(f)

config = {'pip_value': 1.0, 'tiers': {'T1': {'ar_max': 3000.0, 'au': 120.0, 'trigger': 140.0}}}

orig_reset = SymmetryTrapEngineSimpleSL._reset_state
def traced_reset(self, new_origin):
    print("  _reset_state called with new_origin=%s" % new_origin)
    traceback.print_stack(limit=8)
    orig_reset(self, new_origin)
SymmetryTrapEngineSimpleSL._reset_state = traced_reset

engine = SymmetryTrapEngineSimpleSL(config=config, symbol='BTCUSD')
EST = timezone(timedelta(hours=-5))
current_date = None

for i, c in enumerate(candles[:200]):
    dt = datetime.fromtimestamp(c[0]/1000, tz=timezone.utc).astimezone(EST)
    bar = Bar(timestamp=dt, open=float(c[1]), high=float(c[2]), low=float(c[3]), close=float(c[4]))
    bar_date = dt.date()

    if dt.hour == 3 and dt.minute == 0 and bar_date != current_date:
        current_date = bar_date
        asian_bars = []
        for j in range(i, -1, -1):
            b_dt = datetime.fromtimestamp(candles[j][0]/1000, tz=timezone.utc).astimezone(EST)
            if b_dt.date() != bar_date: break
            if b_dt.hour >= 19 or b_dt.hour < 3: asian_bars.append(candles[j])
        if asian_bars:
            ah = max(float(b[2]) for b in asian_bars)
            al = min(float(b[3]) for b in asian_bars)
            print("\n=== Day %s: initialize_session ===" % bar_date)
            engine.initialize_session(ah, al)
            print("After init: swing=%s, active=%s" % (engine.swing_origin, engine.session_active))

    if dt.hour == 12 and dt.minute == 0:
        print("\n=== Day %s: hard_exit ===" % bar_date)
        engine.hard_exit()

    if not engine.session_active:
        continue

    signal = engine.process_bar(bar)
    if signal:
        print("SIGNAL: %s" % signal.event)
        break
