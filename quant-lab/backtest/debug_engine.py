"""Debug engine signal generation"""
import sys, json
from datetime import datetime, timezone, timedelta
sys.path.insert(0, 'quant-lab/engines')
from symmetry_trap_simple_sl import SymmetryTrapEngineSimpleSL, Bar, TradeDirection

with open('quant-lab/data/btc_5m_4yr.json') as f:
    candles = json.load(f)

config = {'pip_value': 1.0, 'tiers': {'T1': {'ar_max': 3000.0, 'au': 120.0, 'trigger': 140.0}}}
engine = SymmetryTrapEngineSimpleSL(config=config, symbol='BTCUSD')
EST = timezone(timedelta(hours=-5))
current_date = None

for i, c in enumerate(candles[:2000]):
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
            engine.initialize_session(ah, al)
            print("Session %s: active=%s, swing=%.1f, trigger=%.1f, state=%s" % (
                bar_date, engine.session_active, engine.swing_origin or 0, engine.trigger_pips, engine.state))

    if dt.hour == 12 and dt.minute == 0: engine.hard_exit()
    if not engine.session_active: continue

    signal = engine.process_bar(bar)
    if signal:
        print("  SIGNAL: %s %s at %s" % (signal.event, signal.direction, dt.strftime("%H:%M")))
        if signal.event == "ENTRY":
            print("  Entry=%.1f SL=%.1f TP=%.1f tier=%s" % (
                signal.entry_price, signal.sl_price, signal.tp_price, engine.tier_name))
            break

print("Total trades: %d" % engine.total_trades)
