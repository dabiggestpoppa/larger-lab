"""
Compare OLD engine (impulse_extreme SL) vs NEW engine (OCC extreme + buffer SL)
on the same EURUSD data, showing actual trade examples side by side.
"""
import csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

class Bar:
    def __init__(self, ts, o, h, l, c):
        self.timestamp = ts
        self.open = o
        self.high = h
        self.low = l
        self.close = c

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
                    datetime.strptime(ts.strip(), '%Y-%m-%d %H:%M:%S'),
                    float(clean.get('OPEN') or clean.get('open')),
                    float(clean.get('HIGH') or clean.get('high')),
                    float(clean.get('LOW') or clean.get('low')),
                    float(clean.get('CLOSE') or clean.get('close'))
                ))
            except Exception:
                pass

bars.sort(key=lambda b: b.timestamp)
print('Loaded %d bars' % len(bars))

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

KILL_SWITCH_PCT = 0.80
PIP_SIZE = 0.0001

def simulate_engine(use_old_sl):
    """
    Simulate engine with either OLD or NEW SL method.
    use_old_sl=True: SL = impulse_extreme (old buggy method)
    use_old_sl=False: SL = OCC extreme + spread buffer (new fixed method)
    """
    SPREAD_BUFFER_PIPS = 1.5
    MIN_SL_BUFFER_PIPS = 8.0
    trades = []
    
    for sdate in sorted(sessions.keys()):
        ab = sessions[sdate]['asian']
        tb = sessions[sdate]['trading']
        if not ab or not tb:
            continue
        
        ah = max(b.high for b in ab)
        al = min(b.low for b in ab)
        if ah <= al:
            continue
        
        ar = ah - al
        ar_pips = ar / PIP_SIZE
        
        # Tier config
        if ar_pips <= 20:
            tier = 'T1'
        elif ar_pips <= 35:
            tier = 'T2'
        else:
            tier = 'T3'
        
        au_pips = ar_pips * 0.50
        trigger_pips = au_pips * 1.20
        au_price = au_pips * PIP_SIZE
        trigger_price = trigger_pips * PIP_SIZE
        
        state = 'SEARCH'
        swing_origin = None
        impulse_extreme = None
        impulse_direction = None
        kill_switch_level = None
        entry_price = None
        sl_price = None
        tp_price = None
        entry_bar_low = None
        entry_bar_high = None
        
        for bar in tb:
            if state == 'SEARCH':
                if swing_origin is None:
                    swing_origin = bar.close
                
                up_move = bar.high - swing_origin
                dn_move = swing_origin - bar.low
                
                if up_move >= trigger_price:
                    impulse_direction = 'LONG'
                    impulse_extreme = bar.high
                    kill_switch_level = impulse_extreme - up_move * KILL_SWITCH_PCT
                    state = 'WAIT_RETRACE'
                elif dn_move >= trigger_price:
                    impulse_direction = 'SHORT'
                    impulse_extreme = bar.low
                    kill_switch_level = impulse_extreme + dn_move * KILL_SWITCH_PCT
                    state = 'WAIT_RETRACE'
            
            elif state == 'WAIT_RETRACE':
                if impulse_direction == 'LONG':
                    pullback = impulse_extreme - bar.low
                else:
                    pullback = bar.high - impulse_extreme
                
                if pullback >= au_price:
                    state = 'WAIT_OCC'
            
            elif state == 'WAIT_OCC':
                if impulse_direction == 'LONG' and bar.close > bar.open:
                    entry_price = bar.close
                    tp_price = entry_price + au_price
                    entry_bar_low = bar.low
                    entry_bar_high = bar.high
                    
                    if use_old_sl:
                        sl_price = impulse_extreme  # OLD
                    else:
                        # NEW: OCC low - spread buffer, with min floor
                        sl_new = bar.low - SPREAD_BUFFER_PIPS * PIP_SIZE
                        min_sl = entry_price - MIN_SL_BUFFER_PIPS * PIP_SIZE
                        sl_price = min(sl_new, min_sl)  # lower of the two
                    
                    state = 'IN_TRADE'
                    
                elif impulse_direction == 'SHORT' and bar.close < bar.open:
                    entry_price = bar.close
                    tp_price = entry_price - au_price
                    entry_bar_low = bar.low
                    entry_bar_high = bar.high
                    
                    if use_old_sl:
                        sl_price = impulse_extreme  # OLD
                    else:
                        # NEW: OCC high + spread buffer, with min floor
                        sl_new = bar.high + SPREAD_BUFFER_PIPS * PIP_SIZE
                        min_sl = entry_price + MIN_SL_BUFFER_PIPS * PIP_SIZE
                        sl_price = max(sl_new, min_sl)  # higher of the two
                    
                    state = 'IN_TRADE'
            
            elif state == 'IN_TRADE':
                # Kill switch
                if impulse_direction == 'LONG' and bar.close < kill_switch_level:
                    trades.append(make_trade(impulse_direction, entry_price, sl_price, tp_price,
                        'KILL_SWITCH', bar.close, PIP_SIZE))
                    state = 'SEARCH'
                    swing_origin = bar.close
                    continue
                elif impulse_direction == 'SHORT' and bar.close > kill_switch_level:
                    trades.append(make_trade(impulse_direction, entry_price, sl_price, tp_price,
                        'KILL_SWITCH', bar.close, PIP_SIZE))
                    state = 'SEARCH'
                    swing_origin = bar.close
                    continue
                
                # TP check
                if impulse_direction == 'LONG' and bar.high >= tp_price:
                    trades.append(make_trade(impulse_direction, entry_price, sl_price, tp_price,
                        'TP_HIT', tp_price, PIP_SIZE))
                    state = 'SEARCH'
                    swing_origin = bar.close
                    continue
                elif impulse_direction == 'SHORT' and bar.low <= tp_price:
                    trades.append(make_trade(impulse_direction, entry_price, sl_price, tp_price,
                        'TP_HIT', tp_price, PIP_SIZE))
                    state = 'SEARCH'
                    swing_origin = bar.close
                    continue
                
                # SL check (close-only)
                if impulse_direction == 'LONG' and bar.close <= sl_price:
                    trades.append(make_trade(impulse_direction, entry_price, sl_price, tp_price,
                        'SL_HIT', sl_price, PIP_SIZE))
                    state = 'SEARCH'
                    swing_origin = bar.close
                    continue
                elif impulse_direction == 'SHORT' and bar.close >= sl_price:
                    trades.append(make_trade(impulse_direction, entry_price, sl_price, tp_price,
                        'SL_HIT', sl_price, PIP_SIZE))
                    state = 'SEARCH'
                    swing_origin = bar.close
                    continue
    
    return trades

def make_trade(direction, entry, sl, tp, exit_event, exit_price, pip_size):
    if direction == 'LONG':
        sl_dist = (entry - sl) / pip_size
        sl_correct = sl < entry
        pnl = (exit_price - entry) / pip_size
    else:
        sl_dist = (sl - entry) / pip_size
        sl_correct = sl > entry
        pnl = (entry - exit_price) / pip_size
    
    tp_dist = abs(tp - entry) / pip_size
    
    return {
        'direction': direction,
        'entry_price': entry,
        'sl_price': sl,
        'tp_price': tp,
        'exit_event': exit_event,
        'exit_price': exit_price,
        'sl_dist_pips': sl_dist,
        'tp_dist_pips': tp_dist,
        'sl_correct': sl_correct,
        'pnl_pips': pnl,
    }

# Run both simulations
print()
print('========================================')
print('OLD ENGINE (impulse_extreme SL)')
print('========================================')
old_trades = simulate_engine(use_old_sl=True)
print('Total trades:', len(old_trades))

old_wrong = [t for t in old_trades if not t['sl_correct']]
old_correct = [t for t in old_trades if t['sl_correct']]
print('SL on correct side:', len(old_correct))
print('SL on WRONG side:', len(old_wrong))

old_exits = Counter(t['exit_event'] for t in old_trades)
print('Exit types:', dict(old_exits))

old_wins = sum(1 for t in old_trades if t['pnl_pips'] > 0)
old_losses = sum(1 for t in old_trades if t['pnl_pips'] < 0)
print('Wins: %d | Losses: %d | WR: %.1f%%' % (old_wins, old_losses, old_wins/len(old_trades)*100 if old_trades else 0))
print('Total PnL: %.1f pips' % sum(t['pnl_pips'] for t in old_trades))

print()
print('========================================')
print('NEW ENGINE (OCC extreme + buffer SL)')
print('========================================')
new_trades = simulate_engine(use_old_sl=False)
print('Total trades:', len(new_trades))

new_wrong = [t for t in new_trades if not t['sl_correct']]
new_correct = [t for t in new_trades if t['sl_correct']]
print('SL on correct side:', len(new_correct))
print('SL on WRONG side:', len(new_wrong))

new_exits = Counter(t['exit_event'] for t in new_trades)
print('Exit types:', dict(new_exits))

new_wins = sum(1 for t in new_trades if t['pnl_pips'] > 0)
new_losses = sum(1 for t in new_trades if t['pnl_pips'] < 0)
print('Wins: %d | Losses: %d | WR: %.1f%%' % (new_wins, new_losses, new_wins/len(new_trades)*100 if new_trades else 0))
print('Total PnL: %.1f pips' % sum(t['pnl_pips'] for t in new_trades))

print()
print('========================================')
print('SIDE-BY-SIDE: FIRST 10 TRADES')
print('========================================')
print()
print('--- OLD ENGINE ---')
for i, t in enumerate(old_trades[:10]):
    print('%d. %s entry=%.5f sl=%.5f tp=%.5f | SL=%s(%.1fp) TP=%.1fp | exit=%s pnl=%.1fp' % (
        i+1, t['direction'], t['entry_price'], t['sl_price'], t['tp_price'],
        'OK' if t['sl_correct'] else 'WRONG', t['sl_dist_pips'], t['tp_dist_pips'],
        t['exit_event'], t['pnl_pips']))

print()
print('--- NEW ENGINE ---')
for i, t in enumerate(new_trades[:10]):
    print('%d. %s entry=%.5f sl=%.5f tp=%.5f | SL=%s(%.1fp) TP=%.1fp | exit=%s pnl=%.1fp' % (
        i+1, t['direction'], t['entry_price'], t['sl_price'], t['tp_price'],
        'OK' if t['sl_correct'] else 'WRONG', t['sl_dist_pips'], t['tp_dist_pips'],
        t['exit_event'], t['pnl_pips']))

print()
print('========================================')
print('OLD ENGINE: TRADES WITH SL ON WRONG SIDE')
print('========================================')
for i, t in enumerate(old_wrong[:15]):
    print('%d. %s entry=%.5f sl=%.5f tp=%.5f | SL_dist=%.1fp TP_dist=%.1fp | exit=%s pnl=%.1fp' % (
        i+1, t['direction'], t['entry_price'], t['sl_price'], t['tp_price'],
        t['sl_dist_pips'], t['tp_dist_pips'], t['exit_event'], t['pnl_pips']))
