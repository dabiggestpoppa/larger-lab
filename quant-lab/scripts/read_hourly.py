"""Read hourly stats from existing JSON results."""
import json, os

# The individual pair JSONs should be in reports/baskets/
# But the basket runner doesn't save hourly stats. Let me check the single-pair JSONs
# from the earlier single-pair backtest runs

# Check if there are any single-pair JSONs with hourly data
reports_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'
for f in os.listdir(reports_dir):
    if f.endswith('.json') and 'hourly' not in f:
        fp = os.path.join(reports_dir, f)
        try:
            with open(fp) as fh:
                data = json.load(fh)
            if 'hourly' in data:
                print("=== {} ===".format(f))
                hourly = data['hourly']
                total = sum(h['trades'] for h in hourly.values())
                for h in sorted(hourly.keys(), key=int):
                    hs = hourly[h]
                    pct = hs['trades'] / total * 100 if total else 0
                    print("  {:02d}:00 | {:>4} tr ({:>4.1f}%) | {:.1f}% WR | {:>+7.1f}p".format(
                        int(h), hs['trades'], pct, hs.get('wr', 0), hs.get('pnl', 0)))
                print()
        except:
            pass

# Also check the st_multi_asset_results.json
fp = os.path.join(reports_dir, 'st_multi_asset_results.json')
if os.path.exists(fp):
    with open(fp) as f:
        data = json.load(f)
    print("=== st_multi_asset_results.json ===")
    print("Keys:", list(data.keys())[:10])
    if isinstance(data, dict):
        for k in list(data.keys())[:3]:
            v = data[k]
            if isinstance(v, dict):
                print("  {}: {}".format(k, list(v.keys())[:10]))
