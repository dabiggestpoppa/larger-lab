import json

with open('quant-lab/reports/dmr_reconstructed_results.json') as f:
    v1 = json.load(f)['results']

with open('quant-lab/reports/dmr_v2_multi_entry_results.json') as f:
    v2 = json.load(f)

print('='*90)
print('v1 (single entry per day) vs v2 (multi-entry per 2hr window)')
print('='*90)
print(f'{"Pair":<10} {"v1 TR":>6} {"v1 WR":>6} {"v1 PnL":>10} {"v2 TR":>6} {"v2 WR":>6} {"v2 PnL":>10} {"Delta":>10}')
print('-'*90)

v1_total = 0
v2_total = 0
v1_pnl = 0
v2_pnl = 0

for sym in sorted(v2.keys()):
    v1s = v1.get(sym, {})
    v2s = v2.get(sym, {})
    
    v1_tr = v1s.get('total', 0)
    v2_tr = v2s.get('total', 0)
    v1_wr = v1s.get('wr', 0)
    v2_wr = v2s.get('wr', 0)
    v1_p = v1s.get('pnl', 0)
    v2_p = v2s.get('pnl', 0)
    
    delta = v2_p - v1_p
    v1_total += v1_tr
    v2_total += v2_tr
    v1_pnl += v1_p
    v2_pnl += v2_p
    
    print(f'{sym:<10} {v1_tr:6d} {v1_wr:5.1f}% {v1_p:+10.1f} {v2_tr:6d} {v2_wr:5.1f}% {v2_p:+10.1f} {delta:+10.1f}')

print('-'*90)

# Calculate blended WR from per-pair WR and trade count
v1_wins = sum(v1[s]['wr'] * v1[s]['total'] / 100 for s in v1 if v1[s]['total'] > 0)
v2_wins = sum(v2[s]['wr'] * v2[s]['total'] / 100 for s in v2 if v2[s]['total'] > 0)
v1_wr = v1_wins / v1_total * 100 if v1_total > 0 else 0
v2_wr = v2_wins / v2_total * 100 if v2_total > 0 else 0

print(f'{"TOTAL":<10} {v1_total:6d} {v1_wr:5.1f}% {v1_pnl:+10.1f} {v2_total:6d} {v2_wr:5.1f}% {v2_pnl:+10.1f} {v2_pnl-v1_pnl:+10.1f}')
print()
print(f'Trade count: {v1_total} -> {v2_total} (+{v2_total-v1_total}, +{(v2_total-v1_total)/v1_total*100:.0f}%)')
print(f'PnL: {v1_pnl:+,.0f}p -> {v2_pnl:+,.0f}p (+{v2_pnl-v1_pnl:+,.0f}p, +{(v2_pnl-v1_pnl)/abs(v1_pnl)*100:.0f}%)')
print(f'WR: {v1_wr:.1f}% -> {v2_wr:.1f}% ({v2_wr-v1_wr:+.1f}pp)')
