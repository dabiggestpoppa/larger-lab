import sys
from datetime import datetime, timedelta
import MetaTrader5 as mt5

EST_OFFSET = -5
def est_hour(dt): return (dt.hour + EST_OFFSET) % 24

if not mt5.initialize(): print('MT5 fail'); sys.exit()
bars = mt5.copy_rates_from_pos('USDCHF.PRO', mt5.TIMEFRAME_M5, 0, 50000)
mt5.shutdown()
if bars is None or len(bars) == 0: print('No bars'); sys.exit()

result = []
for bar in bars:
    dt = datetime.fromtimestamp(bar['time'])
    result.append({'dt': dt, 'est_h': est_hour(dt), 'o': bar['open'], 'h': bar['high'], 'l': bar['low'], 'c': bar['close']})

sessions = {}
for bar in result:
    d = bar['dt'].date()
    if bar['est_h'] < 3: d = (bar['dt'] + timedelta(hours=EST_OFFSET)).date()
    sessions.setdefault(str(d), []).append(bar)

pm = 10000
def ppip(price): return price * pm
def ppt(pips): return pips / pm

dates = sorted(sessions.keys())
count = 0
for d in dates[100:200]:
    db = sessions[d]
    asian = [b for b in db if b['est_h'] >= 19 or b['est_h'] < 3]
    if len(asian) < 2: continue
    ah = max(b['h'] for b in asian)
    al = min(b['l'] for b in asian)
    ar = ppip(ah - al)
    if ar < 13 or ar > 60: continue
    au = 11 if ar < 18 else (15 if ar < 24 else 18)
    bw = [b for b in db if 3 <= b['est_h'] < 11]
    bias = 0
    bi = -1
    for i, b in enumerate(bw):
        if b['c'] > ah: bias = 1; bi = i; break
        if b['c'] < al: bias = -1; bi = i; break
    if bias == 0: continue
    post = bw[bi:]
    for i in range(len(post)-1):
        b = post[i]
        body = abs(b['c'] - b['o'])
        bp = ppip(body)
        is_bull = b['c'] > b['o']
        is_bear = b['c'] < b['o']
        nb = post[i+1]
        if bias == 1 and is_bull and bp >= au * 0.5 and nb['c'] < nb['o']:
            entry = nb['c']
            t25 = ah + ppt(ar * -0.25)
            t50 = ah + ppt(ar * -0.50)
            reward25 = ppip(entry - t25)
            risk = ppip(ah - entry)
            count += 1
            arrow = '<-' if entry >= ah else '  '
            print(f'{d} SHORT entry={entry:.5f} t25={t25:.5f} reward25={reward25:+.1f}p risk={risk:+.1f}p RR={reward25/max(risk,0.01):.1f} {arrow}ah={ah:.5f}')
            break
        if bias == -1 and is_bear and bp >= au * 0.5 and nb['c'] > nb['o']:
            entry = nb['c']
            t25 = al + ppt(ar * 0.25)
            t50 = al + ppt(ar * 0.50)
            reward25 = ppip(t25 - entry)
            risk = ppip(entry - al)
            count += 1
            arrow = '->' if entry <= al else '  '
            print(f'{d} LONG  entry={entry:.5f} t25={t25:.5f} reward25={reward25:+.1f}p risk={risk:+.1f}p RR={reward25/max(risk,0.01):.1f} {arrow}al={al:.5f}')
            break
    if count >= 8: break
