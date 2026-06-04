"""Final investigation: read actual trade counts from JSON results."""
import json, os

baskets_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports/baskets'

print("=== ACTUAL TRADE COUNTS FROM JSON (using 'trades' key) ===")
print("  {:<12} {:>8} {:>8} {:>10} {:>8} {:>10}".format("Pair", "Trades", "WR%", "Days", "Tr/Day", "Bars"))
print("  " + "-" * 60)

all_pairs = {}
for f in sorted(os.listdir(baskets_dir)):
    if not f.endswith('_results.json'):
        continue
    fp = os.path.join(baskets_dir, f)
    with open(fp) as fh:
        data = json.load(fh)
    results = data.get('results', {})
    if isinstance(results, dict):
        for sym, res in sorted(results.items()):
            if isinstance(res, dict):
                trades = res.get('trades', 0)
                wr = res.get('wr', 0)
                days = res.get('data_days', 0)
                bars = res.get('data_bars', 0)
                tr_per_day = round(trades / days, 3) if days else 0
                if sym not in all_pairs:
                    all_pairs[sym] = []
                all_pairs[sym].append((trades, wr, days, bars, tr_per_day))

for sym, entries in sorted(all_pairs.items()):
    # Use the first entry (they should be the same across baskets)
    trades, wr, days, bars, tr_per_day = entries[0]
    print("  {:<12} {:>8} {:>8.1f} {:>10} {:>8.3f} {:>10,}".format(sym, trades, wr, days, tr_per_day, bars))

# Now check: are the original pairs (non-PRO) producing fewer trades per day?
print("\n\n=== PRO vs NON-PRO TRADE EFFICIENCY ===")
print("  {:<12} {:>8} {:>8} {:>8} {:<6}".format("Pair", "Trades", "Days", "Tr/Day", "Type"))
print("  " + "-" * 50)

data_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data'
for sym in sorted(all_pairs.keys()):
    trades, wr, days, bars, tr_per_day = all_pairs[sym][0]
    # Find the CSV file
    csv_file = None
    for f in os.listdir(data_dir):
        if f.startswith(sym) and f.endswith('_M5.csv'):
            csv_file = f
            break
    is_pro = csv_file and '.PRO' in csv_file if csv_file else False
    is_orig = csv_file and '.PRO' not in csv_file if csv_file else False
    ftype = 'PRO' if is_pro else ('ORIG' if is_orig else 'UNKNOWN')
    print("  {:<12} {:>8} {:>8} {:>8.3f} {:<6}".format(sym, trades, days, tr_per_day, ftype))

# Summary stats
print("\n\n=== SUMMARY ===")
pro_trades = []
orig_trades = []
pro_days = []
orig_days = []
for sym, entries in all_pairs.items():
    trades, wr, days, bars, tr_per_day = entries[0]
    csv_file = None
    for f in os.listdir(data_dir):
        if f.startswith(sym) and f.endswith('_M5.csv'):
            csv_file = f
            break
    is_pro = csv_file and '.PRO' in csv_file if csv_file else False
    if is_pro:
        pro_trades.append(trades)
        pro_days.append(days)
    else:
        orig_trades.append(trades)
        orig_days.append(days)

print("PRO pairs:  {} pairs, {} total trades, {} total days".format(len(pro_trades), sum(pro_trades), sum(pro_days)))
print("ORIG pairs: {} pairs, {} total trades, {} total days".format(len(orig_trades), sum(orig_trades), sum(orig_days)))
if pro_days:
    print("PRO avg trades/day:  {:.3f}".format(sum(pro_trades) / sum(pro_days)))
if orig_days:
    print("ORIG avg trades/day: {:.3f}".format(sum(orig_trades) / sum(orig_days)))
