import csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection

bars = []
with open('quant-lab/data/EURUSD_M5.csv', newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        clean = {k.strip().strip('<').strip('>'): v for k, v in row.items()}
        ts = clean.get('timestamp') or clean.get('Timestamp') or ''
        if not ts:
            dv = clean.get('date') or clean.get('Date') or ''
            tv = clean.get('time') or clean.get('Time') or ''
            if dv and tv:
                ts = dv.strip() + ' ' + tv.strip()
        if ts:
            try:
                bars.append(Bar(
                    timestamp=datetime.strptime(ts.strip(), '%Y-%m-%d %H:%M:%S'),
                    open=float(clean.get('OPEN') or clean.get('open')),
                    high=float(clean.get('HIGH') or clean.get('high')),
                    low=float(clean.get('LOW') or clean.get('low')),
                    close=float(clean.get('CLOSE') or clean.get('close'))
                ))
            except Exception:
                pass

bars.sort(key=lambda b: b.timestamp)
engine = SymmetryTrapEngine(pip_size=0.0001, symbol='EURUSD')

ASIAN_START_H, ASIAN_END_H, TRADING_START_H, TRADING_END_H = 19, 3, 3, 12

def est_hour(dt):
    return (dt.hour - 5) % 24

def session_date(dt):
    h = est_hour(dt)
    if h >= ASIAN_START_H:
        return (dt + timedelta(days=1)).date()
    return dt.date()

sessions = defaultdict(lambda: {'asian': [], 'trading': []})
for bar in bars:
    sdate = session_date(bar.timestamp)
    h = est_hour(bar.timestamp)
    if h >= ASIAN_START_H or h < ASIAN_END_H:
        sessions[sdate]['asian'].append(bar)
    elif TRADING_START_H <= h < TRADING_END_H:
        sessions[sdate]['trading'].append(bar)

for sdate in sessions:
    sessions[sdate]['asian'].sort(key=lambda b: b.timestamp)
    sessions[sdate]['trading'].sort(key=lambda b: b.timestamp)

# Run ST engine session by session
total_bars = 0
for sdate in sorted(sessions.keys()):
    ab = sessions[sdate]['asian']
    tb = sessions[sdate]['trading']
    if not ab or not tb:
        continue
    ah = max(b.high for b in ab)
    al = min(b.low for b in ab)
    if ah <= al:
        continue
    engine.initialize_session(ah, al)
    for bar in tb:
        engine.process_bar(bar)
        total_bars += 1

signals = engine.signal_log
events = Counter(s.event for s in signals)
print('ST Engine - All signal events:')
for evt, cnt in events.most_common():
    print('  %s: %d' % (evt, cnt))

entries = sum(1 for s in signals if s.event == 'ENTRY')
tp_hits = sum(1 for s in signals if s.event == 'TP_HIT')
sl_hits = sum(1 for s in signals if s.event == 'SL_HIT')
kill = sum(1 for s in signals if s.event == 'KILL_SWITCH')  # ST may not have this
no_go = sum(1 for s in signals if s.event == 'NO_GO')

print()
print('Total entries: %d' % entries)
print('TP_HIT: %d' % tp_hits)
print('SL_HIT: %d' % sl_hits)
print('KILL_SWITCH: %d' % kill)
print('NO_GO: %d' % no_go)
print('Total exits: %d' % (tp_hits + sl_hits + kill + no_go))

if entries > 0:
    print()
    if tp_hits + sl_hits > 0:
        print('WR (TP vs SL only): %d / %d = %.1f%%' % (tp_hits, tp_hits + sl_hits, tp_hits/(tp_hits+sl_hits)*100))
    print('WR (all entries): %d / %d = %.1f%%' % (tp_hits, entries, tp_hits/entries*100))

# Check a few SL/TP distances
print()
print('Sample TP hits (first 5):')
tp_sigs = [s for s in signals if s.event == 'TP_HIT' and s.entry_price and s.tp_price][:5]
for s in tp_sigs:
    if s.direction and s.direction.name == 'LONG':
        dist = (s.tp_price - s.entry_price) / 0.0001
    else:
        dist = (s.entry_price - s.tp_price) / 0.0001
    print('  entry=%.5f tp=%.5f dist=%.1fp dir=%s' % (s.entry_price, s.tp_price, dist, s.direction))

print()
print('Sample SL hits (first 5):')
sl_sigs = [s for s in signals if s.event == 'SL_HIT' and s.entry_price and s.sl_price][:5]
for s in sl_sigs:
    if s.direction and s.direction.name == 'LONG':
        dist = (s.entry_price - s.sl_price) / 0.0001
    else:
        dist = (s.sl_price - s.entry_price) / 0.0001
    print('  entry=%.5f sl=%.5f dist=%.1fp dir=%s' % (s.entry_price, s.sl_price, dist, s.direction))
