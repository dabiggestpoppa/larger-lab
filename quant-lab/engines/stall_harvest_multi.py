#!/usr/bin/env python3
"""Multi-pair stall harvest test"""
import sys, glob
sys.path.insert(0, 'quant-lab/engines')
from rekey_dead_simple import run

results = []
for f in sorted(glob.glob('quant-lab/data/*_PRO_M5*.csv'))[:20]:
    sym = f.split('/')[-1].replace('_PRO_M5.csv','').replace('_M5.csv','')
    try:
        trades = run(f, sym)
        wins = len([t for t in trades if t.pnl > 0])
        losses = len([t for t in trades if t.pnl < 0])
        net = sum(t.pnl for t in trades)
        wr = wins/len(trades)*100 if trades else 0
        results.append((sym, len(trades), wr, net))
    except Exception as e:
        print(f'{sym}: ERROR {e}')

print()
print(f"{'Pair':<12} {'Trades':>8} {'WR':>8} {'Net PnL':>12}")
print('-'*42)
for sym, tr, wr, net in sorted(results, key=lambda x: x[3], reverse=True):
    print(f"{sym:<12} {tr:>8} {wr:>7.1f}% {net:>+11.1f}p")
