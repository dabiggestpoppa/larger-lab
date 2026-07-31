"""
Trace ALL P90 backtest signals to find where the 180 missing trades come from.
"""
import sys, os, csv
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
os.environ['PYTHONPATH'] = 'quant-lab'
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime, timedelta, time
from collections import defaultdict

from p90_engine import (
    P90Engine, P90Variant, TradeDirection, Bar,
    DEFAULT_P90_THRESHOLDS, DEFAULT_TIER_CONFIG,
)

DATA_FILE = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\USDCHFPRO_M5_MAD.csv'
SYMBOL = 'USDCHF'
PIP_SIZE = 0.0001

def load_bars(path):
    bars = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = row['timestamp']
            if isinstance(ts, str):
                dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
            else:
                dt = datetime.fromtimestamp(int(ts))
            bars.append({
                'dt': dt,
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
            })
    bars.sort(key=lambda x: x['dt'])
    return bars

def est_hour(dt):
    return (dt.hour - 5) % 24

def session_date(dt):
    h = est_hour(dt)
    if h >= 19:
        return (dt + timedelta(days=1)).date()
    return dt.date()

def run_trace(bars):
    sessions = defaultdict(lambda: {"asian": [], "trading": []})
    for b in bars:
        sd = session_date(b['dt'])
        h = est_hour(b['dt'])
        if h >= 19 or h < 3:
            sessions[sd]["asian"].append(b)
        elif 2 <= h < 12:
            sessions[sd]["trading"].append(b)

    total_entries = 0
    total_exits = 0
    variant_counts = defaultdict(int)
    exit_type_counts = defaultdict(int)
    event_counts = defaultdict(int)
    trades_by_variant = defaultdict(list)
    
    entries_without_exit = 0
    sessions_with_unresolved = []

    for sdate in sorted(sessions.keys()):
        sbars = sessions[sdate]
        if not sbars["asian"] or not sbars["trading"]:
            continue

        ah = max(b['high'] for b in sbars["asian"])
        al = min(b['low'] for b in sbars["asian"])
        ar = (ah - al) / PIP_SIZE
        
        if ar < 3.0 or ar > 45.0:
            continue

        engine = P90Engine(pip_size=PIP_SIZE, symbol=SYMBOL)
        engine.initialize_session(ah, al)
        if not engine.session_active:
            continue

        session_entries = 0
        had_entry = False
        
        for b in sbars["trading"]:
            bar = Bar(timestamp=b['dt'], open=b['open'], high=b['high'], low=b['low'], close=b['close'])
            sig = engine.process_bar(bar)
            if sig:
                event_counts[sig.event] += 1
                if sig.event == "ENTRY":
                    total_entries += 1
                    variant_counts[sig.variant.value] += 1
                    had_entry = True
                    session_entries += 1
                    
                    # Store trade info
                    trades_by_variant[sig.variant.value].append({
                        'date': sdate,
                        'session_entries': session_entries,
                        'entry_price': sig.entry_price,
                        'sl': sig.sl_price,
                        'tp': sig.tp_price,
                        'direction': sig.direction.value,
                    })
                elif sig.event in ("TP_HIT", "SL_HIT", "EWS_EXIT"):
                    total_exits += 1
                    exit_type_counts[sig.event] += 1

        # Check if session ended with unresolved position
        if engine.in_trade:
            entries_without_exit += 1
            sessions_with_unresolved.append(sdate)

    print("=" * 60)
    print("P90 TRADE TRACE — USDCHF")
    print("=" * 60)
    print(f"\nTotal ENTRY signals:  {total_entries}")
    print(f"Total EXIT signals:   {total_exits}")
    print(f"Entries without exit:  {entries_without_exit}")
    
    print(f"\n── Event breakdown ──")
    for evt, cnt in sorted(event_counts.items(), key=lambda x: -x[1]):
        print(f"  {evt:15s}: {cnt:5d}")
    
    print(f"\n── Variant breakdown (ENTRY only) ──")
    for v, cnt in sorted(variant_counts.items(), key=lambda x: -x[1]):
        print(f"  {v:15s}: {cnt:5d}")
    
    print(f"\n── Exit type breakdown ──")
    for e, cnt in sorted(exit_type_counts.items(), key=lambda x: -x[1]):
        print(f"  {e:15s}: {cnt:5d}")
    
    total_variant = sum(variant_counts.values())
    print(f"\nSum of all variants:  {total_variant}")
    print(f"Entries - Exits:      {total_entries - total_exits}")
    
    print(f"\n── Sessions with unresolved positions: {entries_without_exit} ──")
    if sessions_with_unresolved:
        for s in sessions_with_unresolved[:5]:
            print(f"  {s}")
        if len(sessions_with_unresolved) > 5:
            print(f"  ... and {len(sessions_with_unresolved)-5} more")
    
    # Now look at signal log for the last session
    all_signals = engine.signal_log
    print(f"\n── Last engine signal log ({len(all_signals)} signals in last session) ──")
    for s in all_signals[-20:]:
        v = s.variant.value if s.variant else "NONE"
        d = s.direction.value if s.direction else "NONE"
        print(f"  {s.event:15s} | {v:10s} | {d:5s} | entry={s.entry_price} sl={s.sl_price} tp={s.tp_price}")

    return event_counts, variant_counts, exit_type_counts


if __name__ == '__main__':
    print(f"Loading {DATA_FILE}...")
    bars = load_bars(DATA_FILE)
    print(f"Loaded {len(bars)} bars")
    print(f"Range: {bars[0]['dt']} to {bars[-1]['dt']}")
    run_trace(bars)
