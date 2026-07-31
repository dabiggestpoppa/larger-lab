"""Debug — trace every swing_origin change"""
import sys, json
from datetime import datetime, timezone, timedelta
sys.path.insert(0, 'quant-lab/engines')
from symmetry_trap_simple_sl import SymmetryTrapEngineSimpleSL, Bar

with open('quant-lab/data/btc_5m_4yr.json') as f:
    candles = json.load(f)

config = {'pip_value': 1.0, 'tiers': {'T1': {'ar_max': 3000.0, 'au': 120.0, 'trigger': 140.0}}}

# Monkey-patch to trace swing_origin changes
orig_init = SymmetryTrapEngineSimpleSL.initialize_session
def traced_init(self, ah, al):
    orig_init(self, ah, al)
    print("  .init: swing=%s" % self.swing_origin)
SymmetryTrapEngineSimpleSL.initialize_session = traced_init

orig_reset = SymmetryTrapEngineSimpleSL._reset_state
def traced_reset(self, new_origin):
    print("  .reset: swing %s -> %s" % (self.swing_origin, new_origin))
    orig_reset(self, new_origin)
SymmetryTrapEngineSimpleSL._reset_state = traced_reset

engine = SymmetryTrapEngineSimpleSL(config=config, symbol='BTCUSD')
EST = timezone(timedelta(hours=-5))
current_date = None

for i, c in enumerate(candles[:500]):
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
            print("Day %s: init (swing was %s)" % (bar_date, engine.swing_origin))
            engine.initialize_session(ah, al)

    if dt.hour == 12 and dt.minute == 0:
        print("Day %s: hard_exit (swing was %s)" % (bar_date, engine.swing_origin))
        engine.hard_exit()

    if not engine.session_active:
        continue

    # Trace swing_origin changes in process_bar
    old_swing = engine.swing_origin
    signal = engine.process_bar(bar)
    if engine.swing_origin != old_swing:
        print("  Bar %d (%s): swing %s -> %s" % (i, dt.strftime("%H:%M"), old_swing, engine.swing_origin))

    if signal:
        print("SIGNAL: %s at %s" % (signal.event, dt.strftime("%H:%M")))
        break
