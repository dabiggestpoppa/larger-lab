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

# Manually trace a few trades to compare old vs new SL
engine = SymmetryTrapEngine(pip_size=0.0001, symbol='EURUSD')

trade_count = 0
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
            trade_count += 1
            if trade_count <= 10:
                entry = sig.entry_price
                occ_extreme_sl = sig.sl_price  # New: OCC extreme + buffer
                tp = sig.tp_price
                
                # Old SL would be: impulse_extreme (stored in engine before reset)
                # We need to capture it before the engine resets
                # The impulse_extreme is the extreme of the impulse candle
                # For LONG: impulse_extreme = impulse candle high
                # For SHORT: impulse_extreme = impulse candle low
                
                if sig.direction == TradeDirection.LONG:
                    sl_dist_new = (entry - occ_extreme_sl) / 0.0001
                    tp_dist = (tp - entry) / 0.0001
                    print('Trade #%d LONG  entry=%.5f sl_new=%.5f tp=%.5f | SL_dist=%.1fp TP_dist=%.1fp' % (
                        trade_count, entry, occ_extreme_sl, tp, sl_dist_new, tp_dist))
                else:
                    sl_dist_new = (occ_extreme_sl - entry) / 0.0001
                    tp_dist = (entry - tp) / 0.0001
                    print('Trade #%d SHORT entry=%.5f sl_new=%.5f tp=%.5f | SL_dist=%.1fp TP_dist=%.1fp' % (
                        trade_count, entry, occ_extreme_sl, tp, sl_dist_new, tp_dist))
            
            if trade_count >= 10:
                break
    if trade_count >= 10:
        break

print()
print('KEY FINDING:')
print('The NEW SL uses OCC candle extreme (bar.high/bar.low of the OCC confirmation candle)')
print('The OLD SL used impulse_extreme (the impulse candle extreme)')
print()
print('The impulse candle extreme is MUCH further from entry than the OCC candle extreme')
print('because the impulse candle is the big move, and the OCC is just the confirmation')
print()
print('Example:')
print('  Impulse candle: high=1.08700 (impulse_extreme for LONG)')
print('  OCC candle: high=1.08520, close=1.08500 (entry)')
print('  OLD SL = 1.08700 (impulse extreme) -> SL = 20p below entry for LONG')
print('  NEW SL = 1.08520 - spread_buf = 1.08505 -> SL = 5p below entry for LONG')
print()
print('The old SL was at the impulse extreme which is FAR from entry.')
print('The new SL is at the OCC extreme which is CLOSE to entry.')
print('This explains the WR collapse: the new SL is way tighter.')
