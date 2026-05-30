"""
Quick gap analysis: why does variant breakdown (371+484=855) not match total (1035)?
Hypothesis: EWS_EXIT events produce variant-tagable exits, but 
some exits may not have associated variant tags.
"""
import sys, os, csv
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
os.environ['PYTHONPATH'] = 'quant-lab'
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime, timedelta
from collections import defaultdict

from p90_engine import P90Engine, P90Variant, TradeDirection, Bar

DATA_FILE = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\USDCHFPRO_M5_MAD.csv'
PIP_SIZE = 0.0001

def load_bars(path):
    bars = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
            bars.append({'dt': dt, 'open': float(row['open']), 'high': float(row['high']),
                         'low': float(row['low']), 'close': float(row['close'])})
    bars.sort(key=lambda x: x['dt'])
    return bars

def est_hour(dt): return (dt.hour - 5) % 24

bars = load_bars(DATA_FILE)
sessions = defaultdict(lambda: {"asian": [], "trading": []})
for b in bars:
    sd = (b['dt'] + timedelta(days=1)).date() if est_hour(b['dt']) >= 19 else b['dt'].date()
    h = est_hour(b['dt'])
    sessions[sd]["asian" if (h >= 19 or h < 3) else "trading"].append(b)

variant_entry_count = defaultdict(int)
variant_exit_count = defaultdict(int)
no_variant_exit = 0
total_entry = 0
total_exit = 0
exit_events = defaultdict(int)
last_variant_per_session = []

for sdate in sorted(sessions.keys()):
    sbars = sessions[sdate]
    if not sbars["asian"] or not sbars["trading"]: continue
    ah = max(b['high'] for b in sbars["asian"])
    al = min(b['low'] for b in sbars["asian"])
    ar = (ah - al) / PIP_SIZE
    if ar < 3.0 or ar > 45.0: continue
    
    engine = P90Engine(pip_size=PIP_SIZE, symbol='USDCHF')
    engine.initialize_session(ah, al)
    if not engine.session_active: continue
    
    last_variant = None
    for b in sbars["trading"]:
        bar = Bar(timestamp=b['dt'], open=b['open'], high=b['high'], low=b['low'], close=b['close'])
        sig = engine.process_bar(bar)
        if sig:
            if sig.event == "ENTRY":
                total_entry += 1
                v = sig.variant.value if sig.variant else "NONE"
                variant_entry_count[v] += 1
                last_variant = v
            elif sig.event in ("TP_HIT", "SL_HIT", "EWS_EXIT"):
                total_exit += 1
                exit_events[sig.event] += 1
                # What variant does this exit belong to?
                # The exit signal itself doesn't carry variant - it's the engine's current state
                if hasattr(engine, 'current_variant') and engine.current_variant:
                    ve = engine.current_variant.value
                    variant_exit_count[ve] += 1
                else:
                    # Try last known variant in this session
                    if last_variant:
                        variant_exit_count[f"{last_variant}_EXIT_NO_STATE"] += 1
                    else:
                        no_variant_exit += 1
    
    last_variant_per_session.append(last_variant)

print("=" * 60)
print(f"Total ENTRY: {total_entry}")
print(f"Total EXIT:  {total_exit}")
print(f"Gap:         {total_entry - total_exit}")
print()
print("ENTRY by variant:")
for v, c in sorted(variant_entry_count.items(), key=lambda x: -x[1]):
    print(f"  {v:15s}: {c}")
print(f"  SUM:          {sum(variant_entry_count.values())}")
print()
print("EXIT by variant (from engine.current_variant):")
for v, c in sorted(variant_exit_count.items(), key=lambda x: -x[1]):
    print(f"  {v:30s}: {c}")
print(f"  SUM with state:    {sum(v for k,v in variant_exit_count.items() if 'NO_STATE' not in k and not k.startswith('EXIT'))}")
print()
print("Exit events:")
for e, c in sorted(exit_events.items(), key=lambda x: -x[1]):
    print(f"  {e:15s}: {c}")
print()
print(f"No variant exit: {no_variant_exit}")
