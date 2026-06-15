"""Debug — minimal"""
import sys, json
from datetime import datetime, timezone, timedelta
sys.path.insert(0, 'quant-lab/engines')
from symmetry_trap_simple_sl import SymmetryTrapEngineSimpleSL, Bar

with open('quant-lab/data/btc_5m_4yr.json') as f:
    candles = json.load(f)

config = {'pip_value': 1.0, 'tiers': {'T1': {'ar_max': 3000.0, 'au': 120.0, 'trigger': 140.0}}}
engine = SymmetryTrapEngineSimpleSL(config=config, symbol='BTCUSD')
EST = timezone(timedelta(hours=-5))

# Just test first session
c = candles[100]  # Around 3AM on first day
dt = datetime.fromtimestamp(c[0]/1000, tz=timezone.utc).astimezone(EST)
print(f"Bar: {dt}, hour={dt.hour}")

# Find 3AM bar
for i, c in enumerate(candles[:500]):
    dt = datetime.fromtimestamp(c[0]/1000, tz=timezone.utc).astimezone(EST)
    if dt.hour == 3 and dt.minute == 0:
        print(f"Found 3AM at bar {i}: {dt}")
        # Get Asian bars
        asian_bars = []
        for j in range(i, -1, -1):
            b_dt = datetime.fromtimestamp(candles[j][0]/1000, tz=timezone.utc).astimezone(EST)
            if b_dt.date() != dt.date(): break
            if b_dt.hour >= 19 or b_dt.hour < 3: asian_bars.append(candles[j])
        print(f"Asian bars: {len(asian_bars)}")
        if asian_bars:
            ah = max(float(b[2]) for b in asian_bars)
            al = min(float(b[3]) for b in asian_bars)
            print(f"AR: {ah-al:.1f} pips")
            engine.initialize_session(ah, al)
            print(f"session_active: {engine.session_active}")
            print(f"tier_name: {engine.tier_name}")
            print(f"asian_range_pips: {engine.asian_range_pips}")
            # Now process next bar
            if i+1 < len(candles):
                nc = candles[i+1]
                ndt = datetime.fromtimestamp(nc[0]/1000, tz=timezone.utc).astimezone(EST)
                nbar = Bar(timestamp=ndt, open=float(nc[1]), high=float(nc[2]), low=float(nc[3]), close=float(nc[4]))
                sig = engine.process_bar(nbar)
                print(f"Next bar signal: {sig}")
                print(f"Engine state: {engine.state}, active: {engine.session_active}")
        break
