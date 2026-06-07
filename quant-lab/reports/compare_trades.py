import json
import os
import glob

reports_dir = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports"

print("=" * 80)
print("CROSS-REPORT TRADE COUNT COMPARISON (same pair, different sweep files)")
print("=" * 80)

# Collect all sweep files
sweep_files = {}
for fname in glob.glob(os.path.join(reports_dir, "trigger_sweep_*.json")):
    bname = os.path.basename(fname)
    try:
        with open(fname) as f:
            data = json.load(f)
        if isinstance(data, dict):
            for pair in data:
                if pair not in sweep_files:
                    sweep_files[pair] = {}
                entries = data[pair]
                if isinstance(entries, list) and entries:
                    # Store min/max trades from this sweep
                    max_tr = max(entries, key=lambda x: x.get("trades", 0))
                    min_tr = min(entries, key=lambda x: x.get("trades", 0))
                    sweep_files[pair][bname] = {
                        "max_trades": max_tr["trades"],
                        "min_trades": min_tr["trades"],
                        "max_wr": max_tr.get("wr", 0),
                        "min_wr": min_tr.get("wr", 0),
                    }
    except Exception as e:
        print(f"Error reading {bname}: {e}")

# Now compare across files for each pair
print(f"\n{'Pair':<10} {'File':<40} {'MaxTr':>8} {'MinTr':>8} {'Delta':>8}")
print("-" * 80)

for pair in sorted(sweep_files.keys()):
    files = sweep_files[pair]
    if len(files) > 1:
        print(f"\n  [{pair}] - appears in {len(files)} sweep files:")
        all_max = []
        all_min = []
        for fname, info in sorted(files.items()):
            print(f"  {pair:<10} {fname:<40} {info['max_trades']:>8} {info['min_trades']:>8} {info['max_trades']-info['min_trades']:>8}")
            all_max.append(info["max_trades"])
            all_min.append(info["min_trades"])
        # Cross-file variance
        cross_max = max(all_max)
        cross_min = min(all_max)
        print(f"  {'':>10} ** CROSS-FILE MAX variance: {cross_max} vs {cross_min} = delta {cross_max-cross_min}")

print("\n" + "=" * 80)
print("Now checking: same config (FLOOR/CEILING) across different sweep runs")
print("=" * 80)

# Specifically check EURUSD across all files
target_pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "EURNZD", "GBPNZD", "EURJPY"]
for pair in target_pairs:
    if pair in sweep_files:
        print(f"\n{pair}:")
        for fname, info in sorted(sweep_files[pair].items()):
            print(f"  {fname:<45} max={info['max_trades']:>6} min={info['min_trades']:>6} wr_max={info['max_wr']:.1f}% wr_min={info['min_wr']:.1f}%")
