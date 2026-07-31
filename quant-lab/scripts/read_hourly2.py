"""Read hourly stats from the detailed single-pair JSONs in reports."""
import json, os, glob

# Look for all JSON files that might have hourly data
reports_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'

# Check the nautilus ground truth matrix
fp = os.path.join(reports_dir, 'nautilus_ground_truth_matrix.json')
if os.path.exists(fp):
    with open(fp) as f:
        data = json.load(f)
    print("=== nautilus_ground_truth_matrix.json ===")
    if isinstance(data, dict):
        for k in sorted(data.keys())[:5]:
            v = data[k]
            if isinstance(v, dict):
                print("  {}: trades={}, wr={}".format(k, v.get('trades', '?'), v.get('wr', '?')))
                if 'hourly' in v:
                    hourly = v['hourly']
                    for h in sorted(hourly.keys(), key=int):
                        hs = hourly[h]
                        print("    {:02d}:00 | {} tr".format(int(h), hs.get('trades', '?')))
    print()

# Check all JSON files for hourly data
for fp in glob.glob(os.path.join(reports_dir, '*.json')):
    try:
        with open(fp) as f:
            data = json.load(f)
        if isinstance(data, dict) and 'hourly' in data:
            hourly = data['hourly']
            if hourly:
                print("=== {} ===".format(os.path.basename(fp)))
                total = sum(h.get('trades', 0) for h in hourly.values()) if isinstance(list(hourly.values())[0], dict) else 0
                for h in sorted(hourly.keys(), key=int):
                    hs = hourly[h]
                    if isinstance(hs, dict):
                        pct = hs['trades'] / total * 100 if total else 0
                        print("  {:02d}:00 | {:>4} tr ({:>4.1f}%) | {:.1f}% WR".format(int(h), hs['trades'], pct, hs.get('wr', 0)))
                print()
    except:
        pass

# Now the key question: check what the EURUSD hourly looks like from the backtest
# by reading the engine source to understand the est_offset
print("=== ENGINE SESSION TIMING ===")
engine_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap_backtest.py'
with open(engine_path) as f:
    src = f.read()

for i, line in enumerate(src.split('\n'), 1):
    if 'est_offset' in line.lower() or 'est_hour' in line.lower():
        print("  L{}: {}".format(i, line.strip()))
