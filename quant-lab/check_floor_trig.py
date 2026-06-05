import json
orig = json.load(open('reports/trigger_sweep_max_accuracy.json'))
for pair in sorted(orig.keys()):
    pts = orig[pair]
    if pts:
        first = pts[0]
        last = pts[-1]
        print('%s: T1=%.1f tr=%d wr=%.1f%% pf=%.2f tr/d=%.2f' % (pair, first['t1_trigger'], first['trades'], first['wr'], first['pf'], first['tr_per_day']))
