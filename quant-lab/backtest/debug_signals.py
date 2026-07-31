"""Debug signal generation for Simple SL engine"""
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
            if engine.session_active:
                print(f"Session {bar_date}: AR={(ah-al)/engine.pip_size:.1f}p, swing={engine.swing_origin:.1f}, trigger={engine.trigger_pips:.1f}p")

    if dt.hour == 12 and dt.minute == 0: engine.hard_exit()

    signal = engine.process_bar(bar)
    if signal:
        print(f"Signal: {signal.event} {signal.direction} at {dt.strftime('%m-%d %H:%M')}")
        if signal.event == "ENTRY":
            print(f"  Entry={signal.entry_price:.1f} SL={signal.sl_price:.1f} TP={signal.tp_price:.1f} tier={engine.tier_name}")
            break

print(f"Total trades: {engine.total_trades}, Wins: {engine.wins}, Losses: {engine.losses}")
