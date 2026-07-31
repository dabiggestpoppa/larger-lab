"""Count EWS variant trades vs INITIAL+CASCADE."""
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
            bars.append({'dt': dt, 'o': float(row['open']), 'h': float(row['high']),
                         'l': float(row['low']), 'c': float(row['close'])})
    bars.sort(key=lambda x: x['dt'])
    return bars

def est_hour(dt): return (dt.hour - 5) % 24

bars = load_bars(DATA_FILE)
sessions = defaultdict(lambda: {"asian": [], "trading": []})
for b in bars:
    sd = (b['dt'] + timedelta(days=1)).date() if est_hour(b['dt']) >= 19 else b['dt'].date()
    h = est_hour(b['dt'])
    sessions[sd]["asian" if (h >= 19 or h < 3) else "trading"].append(b)

all_signals = []
for sdate in sorted(sessions.keys()):
    sbars = sessions[sdate]
    if not sbars["asian"] or not sbars["trading"]: continue
    ah = max(b['h'] for b in sbars["asian"])
    al = min(b['l'] for b in sbars["asian"])
    if (ah - al) / PIP_SIZE < 3.0 or (ah - al) / PIP_SIZE > 45.0: continue
    engine = P90Engine(pip_size=PIP_SIZE, symbol='USDCHF')
    engine.initialize_session(ah, al)
    if not engine.session_active: continue
    for b in sbars["trading"]:
        bar = Bar(timestamp=b['dt'], open=b['o'], high=b['h'], low=b['l'], close=b['c'])
        sig = engine.process_bar(bar)
        if sig:
            all_signals.append(sig)

# Count exits by variant
exit_by_variant = defaultdict(int)
for s in all_signals:
    if s.event in ("TP_HIT", "SL_HIT", "EWS_EXIT"):
        v = s.variant.value if s.variant else "NONE"
        exit_by_variant[f"{v}_{s.event}"] += 1

print("EXIT signals by variant + type:")
for k, v in sorted(exit_by_variant.items(), key=lambda x: -x[1]):
    print(f"  {k:25s}: {v}")

print()
for variant_name in ["INITIAL", "CASCADE", "EWS", "NONE"]:
    entries = sum(1 for s in all_signals if s.event == "ENTRY" and s.variant and s.variant.value == variant_name)
    exits = sum(1 for s in all_signals if s.event in ("TP_HIT","SL_HIT","EWS_EXIT") and s.variant and s.variant.value == variant_name)
    print(f"{variant_name}: {entries} entries, {exits} exits")

total_entries = sum(1 for s in all_signals if s.event == "ENTRY")
total_exits = sum(1 for s in all_signals if s.event in ("TP_HIT","SL_HIT","EWS_EXIT"))
print(f"\nTOTAL: {total_entries} entries, {total_exits} exits")
print(f"EWS exits as % of total: {sum(v for k,v in exit_by_variant.items() if 'EWS_' in k) / total_exits * 100:.1f}%")
