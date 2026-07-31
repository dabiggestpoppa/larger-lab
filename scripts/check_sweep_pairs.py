"""Check which pairs have t1=12 in sweep and validate all."""
import json, os

with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json') as f:
    sweep = json.load(f)

print('Pairs in sweep with t1=12 entry:')
for pair in sorted(sweep.keys()):
    entries = sweep[pair]
    if not entries:
        continue
    for e in entries:
        if abs(e['t1_trigger'] - 12.0) < 0.1:
            csv_path = os.path.join(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data', '%s_M5.csv' % pair)
            exists = os.path.exists(csv_path)
            print('  %-12s trades=%-6d wr=%.1f%% pf=%.1f csv=%s' % (pair, e['trades'], e['wr'], e['pf'], exists))
            break

print()
print('All pairs in sweep:')
for pair in sorted(sweep.keys()):
    entries = sweep[pair]
    if entries:
        t1_vals = sorted(set(e['t1_trigger'] for e in entries))
        print('  %-12s entries=%-3d t1_range=%s' % (pair, len(entries), t1_vals[:5]))
