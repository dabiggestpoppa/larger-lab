import csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from p90_engine import P90Engine, Bar

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
engine = P90Engine(pip_size=0.0001, symbol='EURUSD')

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
    if not engine.session_active:
        continue
    for bar in tb:
        engine.process_bar(bar)
        total_bars += 1

signals = engine.signal_log
events = Counter(s.event for s in signals)
print('All signal events:')
for evt, cnt in events.most_common():
    print('  %s: %d' % (evt, cnt))

entries = sum(1 for s in signals if s.event == 'ENTRY')
completed = sum(1 for s in signals if s.event in ('TP_HIT', 'SL_HIT', 'EWS_EXIT'))
kill = events.get('KILL_SWITCH', 0)
pm_exit = events.get('12PM_EXIT', 0)
print()
print('Total entries: %d' % entries)
print('Completed (TP/SL/EWS): %d' % completed)
print('KILL_SWITCH: %d' % kill)
print('12PM_EXIT: %d' % pm_exit)
total_exits = completed + kill + pm_exit
print('Sum: %d + %d + %d = %d vs %d entries' % (completed, kill, pm_exit, total_exits, entries))
print()
print('If KILL_SWITCH counts as loss:')
print('  Real WR = %d / %d = %.1f%%' % (completed, total_exits, completed/total_exits*100))
print()
print('Avg TP distance check:')
tp_sigs = [s for s in signals if s.event == 'TP_HIT' and s.entry_price and s.tp_price]
if tp_sigs:
    tps = []
    for s in tp_sigs:
        if s.direction.name == 'LONG':
            tps.append((s.tp_price - s.entry_price) / 0.0001)
        else:
            tps.append((s.entry_price - s.tp_price) / 0.0001)
    print('  TP hits: %d, Avg TP: %.2f pips, Min: %.2f, Max: %.2f' % (len(tps), sum(tps)/len(tps), min(tps), max(tps)))

sl_sigs = [s for s in signals if s.event == 'SL_HIT' and s.entry_price and s.sl_price]
if sl_sigs:
    sls = []
    for s in sl_sigs:
        if s.direction.name == 'LONG':
            sls.append((s.entry_price - s.sl_price) / 0.0001)
        else:
            sls.append((s.sl_price - s.entry_price) / 0.0001)
    print('  SL hits: %d, Avg SL: %.2f pips' % (len(sls), sum(sls)/len(sls)))
else:
    print('  SL hits: 0')
