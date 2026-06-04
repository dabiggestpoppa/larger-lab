"""Corrected PRO vs non-PRO analysis + loop investigation."""
import json, os

baskets_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports/baskets'
data_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data'

# Build pair -> csv file mapping
pair_to_csv = {}
for f in os.listdir(data_dir):
    if not f.endswith('_M5.csv'):
        continue
    # Extract pair name from filename like "EURUSD_M5.csv" or "EURGBP_PRO_M5.csv"
    name = f.replace('_M5.csv', '')
    is_pro = '_PRO' in name
    pair_name = name.replace('_PRO', '')
    pair_to_csv[pair_name] = (f, is_pro)

print("=== PRO vs NON-PRO TRADE EFFICIENCY (CORRECTED) ===")
print("  {:<12} {:>8} {:>8} {:>8} {:<6} {:<30}".format("Pair", "Trades", "Days", "Tr/Day", "Type", "CSV File"))
print("  " + "-" * 80)

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
            if isinstance(res, dict) and sym not in all_pairs:
                trades = res.get('trades', 0)
                wr = res.get('wr', 0)
                days = res.get('data_days', 0)
                bars = res.get('data_bars', 0)
                tr_per_day = round(trades / days, 3) if days else 0
                csv_info = pair_to_csv.get(sym, ('???', False))
                csv_file, is_pro = csv_info
                ftype = 'PRO' if is_pro else 'ORIG'
                all_pairs[sym] = (trades, wr, days, bars, tr_per_day, ftype, csv_file)

pro_trades_list = []
pro_days_list = []
orig_trades_list = []
orig_days_list = []

for sym in sorted(all_pairs.keys()):
    trades, wr, days, bars, tr_per_day, ftype, csv_file = all_pairs[sym]
    print("  {:<12} {:>8} {:>8} {:>8.3f} {:<6} {:<30}".format(sym, trades, days, tr_per_day, ftype, csv_file[:30]))
    if ftype == 'PRO':
        pro_trades_list.append(trades)
        pro_days_list.append(days)
    else:
        orig_trades_list.append(trades)
        orig_days_list.append(days)

print("\n--- SUMMARY ---")
print("PRO pairs:  {} pairs, {} total trades, {} total days".format(len(pro_trades_list), sum(pro_trades_list), sum(pro_days_list)))
print("ORIG pairs: {} pairs, {} total trades, {} total days".format(len(orig_trades_list), sum(orig_trades_list), sum(orig_days_list)))
if pro_days_list:
    print("PRO avg trades/day:  {:.3f}".format(sum(pro_trades_list) / sum(pro_days_list)))
if orig_days_list:
    print("ORIG avg trades/day: {:.3f}".format(sum(orig_trades_list) / sum(orig_days_list)))

# Now check: what's the date range difference?
print("\n=== DATA RANGE ANALYSIS ===")
for sym in sorted(all_pairs.keys()):
    trades, wr, days, bars, tr_per_day, ftype, csv_file = all_pairs[sym]
    if days > 0:
        years = days / 365.25
        print("  {:<12} {:>5} days ({:.1f} yrs) {:>8} trades  {:.3f} tr/day".format(sym, days, years, trades, tr_per_day))

# Check if the backtest engine has loop capability
print("\n=== LOOP CAPABILITY CHECK ===")
engine_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py'
with open(engine_path) as f:
    engine = f.read()

loop_count = engine.lower().count('loop')
print("Engine 'loop' references: {}".format(loop_count))
for i, line in enumerate(engine.split('\n'), 1):
    if 'loop' in line.lower():
        print("  L{}: {}".format(i, line.strip()[:100]))

# Check the backtest runner for loop handling
print("\n=== BACKTEST RUNNER LOOP CHECK ===")
runner_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtest\run_basket_backtest.py'
with open(runner_path) as f:
    runner = f.read()

for i, line in enumerate(runner.split('\n'), 1):
    if 'loop' in line.lower():
        print("  L{}: {}".format(i, line.strip()[:100]))

# Check the backtest engine (SymmetryTrapBacktest) for loop handling
print("\n=== SYMMETRY TRAP BACKTEST CLASS LOOP CHECK ===")
bt_path = r':\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap_backtest.py'
bt_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap_backtest.py'
with open(bt_path) as f:
    bt = f.read()

for i, line in enumerate(bt.split('\n'), 1):
    if 'loop' in line.lower():
        print("  L{}: {}".format(i, line.strip()[:100]))
