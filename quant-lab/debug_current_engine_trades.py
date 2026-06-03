import csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection

# Load EURUSD data
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

# Run the CURRENT engine and capture every trade with full details
engine = SymmetryTrapEngine(pip_size=0.0001, symbol='EURUSD')

all_trades = []
active_trade = None

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
        sig = engine.process_bar(bar)
        
        if sig and sig.event == 'ENTRY':
            active_trade = {
                'entry_time': bar.timestamp,
                'direction': 'LONG' if sig.direction == TradeDirection.LONG else 'SHORT',
                'entry_price': sig.entry_price,
                'sl_price': sig.sl_price,
                'tp_price': sig.tp_price,
                'au_pips': sig.au_used,
            }
        
        elif sig and sig.event in ('TP_HIT', 'SL_HIT', 'EWS_EXIT'):
            if active_trade:
                active_trade['exit_time'] = bar.timestamp
                active_trade['exit_event'] = sig.event
                active_trade['exit_price'] = sig.tp_price if sig.event == 'TP_HIT' else sig.sl_price
                
                # Calculate SL distance and direction
                ep = active_trade['entry_price']
                sl = active_trade['sl_price']
                tp = active_trade['tp_price']
                direction = active_trade['direction']
                
                if direction == 'LONG':
                    sl_dist = (ep - sl) / 0.0001  # positive = SL below entry (correct)
                    tp_dist = (tp - ep) / 0.0001
                    sl_correct = sl < entry_price
                else:
                    sl_dist = (sl - ep) / 0.0001  # positive = SL above entry (correct)
                    tp_dist = (ep - tp) / 0.0001
                    sl_correct = sl > entry_price
                
                active_trade['sl_dist_pips'] = sl_dist
                active_trade['tp_dist_pips'] = tp_dist
                active_trade['sl_on_correct_side'] = sl_correct
                
                pnl = (active_trade['exit_price'] - ep) / 0.0001
                if direction == 'SHORT':
                    pnl = -pnl
                active_trade['pnl_pips'] = pnl
                
                all_trades.append(active_trade)
                active_trade = None
        
        elif sig and sig.event == 'KILL_SWITCH':
            if active_trade:
                active_trade['exit_time'] = bar.timestamp
                active_trade['exit_event'] = 'KILL_SWITCH'
                active_trade['exit_price'] = bar.close
                
                ep = active_trade['entry_price']
                sl = active_trade['sl_price']
                direction = active_trade['direction']
                
                if direction == 'LONG':
                    sl_dist = (ep - sl) / 0.0001
                    sl_correct = sl < ep
                else:
                    sl_dist = (sl - ep) / 0.0001
                    sl_correct = sl > ep
                
                active_trade['sl_dist_pips'] = sl_dist
                active_trade['sl_on_correct_side'] = sl_correct
                
                pnl = (bar.close - ep) / 0.0001
                if direction == 'SHORT':
                    pnl = -pnl
                active_trade['pnl_pips'] = pnl
                
                all_trades.append(active_trade)
                active_trade = None

# Now analyze: find trades where SL was on the WRONG side
print('=== CURRENT ENGINE (OCC extreme + buffer) ===')
print('Total trades:', len(all_trades))
print()

wrong_side = [t for t in all_trades if not t.get('sl_on_correct_side', True)]
correct_side = [t for t in all_trades if t.get('sl_on_correct_side', True)]
print('Trades with SL on CORRECT side:', len(correct_side))
print('Trades with SL on WRONG side:', len(wrong_side))
print()

if wrong_side:
    print('=== TRADES WITH SL ON WRONG SIDE ===')
    for t in wrong_side[:10]:
        print('  %s %s entry=%.5f sl=%.5f tp=%.5f | SL_dist=%.1fp TP_dist=%.1fp | exit=%s pnl=%.1fp' % (
            t['entry_time'], t['direction'], t['entry_price'], t['sl_price'], t['tp_price'],
            t.get('sl_dist_pips', 0), t.get('tp_dist_pips', 0), t['exit_event'], t['pnl_pips']))
else:
    print('NO trades with SL on wrong side. All SL placements are correct.')
    print()
    print('Sample trades (first 10):')
    for t in all_trades[:10]:
        print('  %s %s entry=%.5f sl=%.5f tp=%.5f | SL_dist=%.1fp TP_dist=%.1fp | exit=%s pnl=%.1fp' % (
            t['entry_time'], t['direction'], t['entry_price'], t['sl_price'], t['tp_price'],
            t.get('sl_dist_pips', 0), t.get('tp_dist_pips', 0), t['exit_event'], t['pnl_pips']))

# Count exit types
exit_counts = Counter(t['exit_event'] for t in all_trades)
print()
print('Exit types:', dict(exit_counts))

# WR calculation
wins = sum(1 for t in all_trades if t['pnl_pips'] > 0)
losses = sum(1 for t in all_trades if t['pnl_pips'] < 0)
print('Wins: %d | Losses: %d | WR: %.1f%%' % (wins, losses, wins/len(all_trades)*100 if all_trades else 0))
