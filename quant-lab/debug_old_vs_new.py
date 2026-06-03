"""
Compare OLD engine (impulse_extreme SL) vs NEW engine (OCC extreme + buffer SL)
on the same EURUSD data, showing actual trade examples side by side.
"""
import csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

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
                bars.append(type('Bar', (), {
                    'timestamp': datetime.strptime(ts.strip(), '%Y-%m-%d %H:%M:%S'),
                    'open': float(clean.get('OPEN') or clean.get('open')),
                    'high': float(clean.get('HIGH') or clean.get('high')),
                    'low': float(clean.get('LOW') or clean.get('low')),
                    'close': float(clean.get('CLOSE') or clean.get('close'))
                })())
            except Exception:
                pass

bars.sort(key=lambda b: b['timestamp'])

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

# Simulate OLD engine behavior manually
# OLD: sl = impulse_extreme (impulse candle high for LONG, low for SHORT)
# NEW: sl = OCC extreme + spread buffer

KILL_SWITCH_PCT = 0.80
SPREAD_BUFFER_PIPS = 1.5  # for EURUSD majors
MIN_SL_BUFFER_PIPS = 8.0  # for EURUSD majors
PIP_SIZE = 0.0001

def simulate_old_engine():
    """Simulate old engine: SL = impulse_extreme (zero buffer)"""
    trades = []
    
    for sdate in sorted(sessions.keys()):
        ab = sessions[sdate]['asian']
        tb = sessions[sdate]['trading']
        if not ab or not tb:
            continue
        
        ah = max(b['high'] for b in ab)
        al = min(b['low'] for b in ab)
        if ah <= al:
            continue
        
        ar = ah - al
        ar_pips = ar / PIP_SIZE
        
        # Tier config for EURUSD
        if ar_pips <= 20:
            tier = 'T1'
            au_pips = ar_pips * 0.50
            trigger_pips = au_pips * 1.20
        elif ar_pips <= 35:
            tier = 'T2'
            au_pips = ar_pips * 0.50
            trigger_pips = au_pips * 1.20
        else:
            tier = 'T3'
            au_pips = ar_pips * 0.50
            trigger_pips = au_pips * 1.20
        
        au_price = au_pips * PIP_SIZE
        trigger_price = trigger_pips * PIP_SIZE
        
        # State machine
        state = 'SEARCH'
        swing_origin = None
        impulse_extreme = None
        impulse_direction = None
        kill_switch_level = None
        entry_price = None
        sl_price = None
        tp_price = None
        
        for bar in tb:
            if state == 'SEARCH':
                if swing_origin is None:
                    swing_origin = bar['close']
                
                up_move = bar['high'] - swing_origin
                dn_move = swing_origin - bar['low']
                
                if up_move >= trigger_price:
                    impulse_direction = 'LONG'
                    impulse_extreme = bar['high']
                    kill_switch_level = impulse_extreme - up_move * KILL_SWITCH_PCT
                    state = 'WAIT_RETRACE'
                elif dn_move >= trigger_price:
                    impulse_direction = 'SHORT'
                    impulse_extreme = bar['low']
                    kill_switch_level = impulse_extreme + dn_move * KILL_SWITCH_PCT
                    state = 'WAIT_RETRACE'
            
            elif state == 'WAIT_RETRACE':
                if impulse_direction == 'LONG':
                    pullback = impulse_extreme - bar['low']
                else:
                    pullback = bar['high'] - impulse_extreme
                
                if pullback >= au_price:
                    state = 'WAIT_OCC'
            
            elif state == 'WAIT_OCC':
                if impulse_direction == 'LONG' and bar['close'] > bar['open']:
                    # Bullish OCC
                    entry_price = bar['close']
                    sl_price = impulse_extreme  # OLD: zero buffer
                    tp_price = entry_price + au_price
                    state = 'IN_TRADE'
                elif impulse_direction == 'SHORT' and bar['close'] < bar['open']:
                    # Bearish OCC
                    entry_price = bar['close']
                    sl_price = impulse_extreme  # OLD: zero buffer
                    tp_price = entry_price - au_price
                    state = 'IN_TRADE'
            
            elif state == 'IN_TRADE':
                # Check kill switch first
                if impulse_direction == 'LONG' and bar['close'] < kill_switch_level:
                    trades.append({
                        'direction': impulse_direction,
                        'entry_price': entry_price,
                        'sl_price': sl_price,
                        'tp_price': tp_price,
                        'exit_event': 'KILL_SWITCH',
                        'exit_price': bar['close'],
                        'entry_time': entry_time if 'entry_time' in dir() else bar['timestamp'],
                        'sl_dist_pips': (entry_price - sl_price) / PIP_SIZE,
                        'sl_correct': sl_price < entry_price,
                    })
                    state = 'SEARCH'
                    swing_origin = bar['close']
                    continue
                elif impulse_direction == 'SHORT' and bar['close'] > kill_switch_level:
                    trades.append({
                        'direction': impulse_direction,
                        'entry_price': entry_price,
                        'sl_price': sl_price,
                        'tp_price': tp_price,
                        'exit_event': 'KILL_SWITCH',
                        'exit_price': bar['close'],
                        'sl_dist_pips': (sl_price - entry_price) / PIP_SIZE,
                        'sl_correct': sl_price > entry_price,
                    })
                    state = 'SEARCH'
                    swing_origin = bar['close']
                    continue
                
                # Check TP
                if impulse_direction == 'LONG' and bar['high'] >= tp_price:
                    trades.append({
                        'direction': impulse_direction,
                        'entry_price': entry_price,
                        'sl_price': sl_price,
                        'tp_price': tp_price,
                        'exit_event': 'TP_HIT',
                        'exit_price': tp_price,
                        'sl_dist_pips': (entry_price - sl_price) / PIP_SIZE,
                        'sl_correct': sl_price < entry_price,
                    })
                    state = 'SEARCH'
                    swing_origin = bar['close']
                    continue
                elif impulse_direction == 'SHORT' and bar['low'] <= tp_price:
                    trades.append({
                        'direction': impulse_direction,
                        'entry_price': entry_price,
                        'sl_price': sl_price,
                        'tp_price': tp_price,
                        'exit_event': 'TP_HIT',
                        'exit_price': tp_price,
                        'sl_dist_pips': (sl_price - entry_price) / PIP_SIZE,
                        'sl_correct': sl_price > entry_price,
                    })
                    state = 'SEARCH'
                    swing_origin = bar['close']
                    continue
                
                # Check SL (close-only)
                if impulse_direction == 'LONG' and bar['close'] <= sl_price:
                    trades.append({
                        'direction': impulse_direction,
                        'entry_price': entry_price,
                        'sl_price': sl_price,
                        'tp_price': tp_price,
                        'exit_event': 'SL_HIT',
                        'exit_price': sl_price,
                        'sl_dist_pips': (entry_price - sl_price) / PIP_SIZE,
                        'sl_correct': sl_price < entry_price,
                    })
                    state = 'SEARCH'
                    swing_origin = bar['close']
                    continue
                elif impulse_direction == 'SHORT' and bar['close'] >= sl_price:
                    trades.append({
                        'direction': impulse_direction,
                        'entry_price': entry_price,
                        'sl_price': sl_price,
                        'tp_price': tp_price,
                        'exit_event': 'SL_HIT',
                        'exit_price': sl_price,
                        'sl_dist_pips': (sl_price - entry_price) / PIP_SIZE,
                        'sl_correct': sl_price > entry_price,
                    })
                    state = 'SEARCH'
                    swing_origin = bar['close']
                    continue
    
    return trades

# Run old engine simulation
print('=== OLD ENGINE (impulse_extreme SL) ===')
old_trades = simulate_old_engine()
print('Total trades:', len(old_trades))

old_wrong = [t for t in old_trades if not t.get('sl_correct', True)]
old_correct = [t for t in old_trades if t.get('sl_correct', True)]
print('SL on correct side:', len(old_correct))
print('SL on WRONG side:', len(old_wrong))

old_exits = Counter(t['exit_event'] for t in old_trades)
print('Exit types:', dict(old_exits))

old_wins = sum(1 for t in old_trades if 
    (t['direction'] == 'LONG' and t['exit_price'] > t['entry_price']) or
    (t['direction'] == 'SHORT' and t['exit_price'] < t['entry_price']))
old_losses = len(old_trades) - old_wins
print('Wins: %d | Losses: %d | WR: %.1f%%' % (old_wins, old_losses, old_wins/len(old_trades)*100 if old_trades else 0))

print()
print('=== FIRST 10 TRADES — OLD ENGINE ===')
for t in old_trades[:10]:
    ep = t['entry_price']
    sl = t['sl_price']
    tp = t['tp_price']
    
    if t['direction'] == 'LONG':
        sl_dist = (ep - sl) / PIP_SIZE  # positive = below entry (correct)
        tp_dist = (tp - ep) / PIP_SIZE
    else:
        sl_dist = (sl - ep) / PIP_SIZE  # positive = above entry (correct)
        tp_dist = (ep - tp) / PIP_SIZE
    
    pnl = (t['exit_price'] - ep) / PIP_SIZE
    if t['direction'] == 'SHORT':
        pnl = -pnl
    
    print('  %s entry=%.5f sl=%.5f tp=%.5f | SL=%s(%.1fp) TP=%.1fp | exit=%s pnl=%.1fp' % (
        t['direction'], ep, sl, tp,
        'CORRECT' if t.get('sl_correct') else 'WRONG', sl_dist, tp_dist,
        t['exit_event'], pnl))

print()
print('=== TRADES WITH SL ON WRONG SIDE (first 10) ===')
for t in old_wrong[:10]:
    ep = t['entry_price']
    sl = t['sl_price']
    tp = t['tp_price']
    
    if t['direction'] == 'LONG':
        sl_dist = (ep - sl) / PIP_SIZE
        tp_dist = (tp - ep) / PIP_SIZE
    else:
        sl_dist = (sl - ep) / PIP_SIZE
        tp_dist = (ep - tp) / PIP_SIZE
    
    pnl = (t['exit_price'] - ep) / PIP_SIZE
    if t['direction'] == 'SHORT':
        pnl = -pnl
    
    print('  %s entry=%.5f sl=%.5f tp=%.5f | SL_dist=%.1fp TP_dist=%.1fp | exit=%s pnl=%.1fp' % (
        t['direction'], ep, sl, tp, sl_dist, tp_dist, t['exit_event'], pnl))
