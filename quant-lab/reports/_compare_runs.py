"""Compare original June 4th sweep vs new cost analysis to find discrepancy."""
import json

# Load the original June 4th max accuracy sweep (the ground truth)
with open('trigger_sweep_max_accuracy.json', 'r') as f:
    orig = json.load(f)

# Load the new corrected cost analysis
with open('cost_analysis_native.json', 'r') as f:
    new = json.load(f)

print("=== EURUSD COMPARISON ===")
print()

if 'EURUSD' in orig:
    o = orig['EURUSD']
    print("ORIGINAL JUNE 4 (max_accuracy sweep):")
    # Find the entry with t1=12.0 (native trigger)
    if isinstance(o, dict):
        for key, val in o.items():
            if isinstance(val, dict) and 'trades' in val:
                print(f"  {key}: trades={val.get('trades')}, wr={val.get('wr')}, pf={val.get('pf')}")
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        print(f"  {item}")

print()

if 'EURUSD' in new:
    n = new['EURUSD']
    print("NEW COST ANALYSIS (native config):")
    raw = n['raw']
    costs = n['costs']
    adj = n['adjusted']
    delta = n['delta']
    print(f"  Raw: trades={raw['trades']}, wr={raw['wr']}%, pf={raw['pf']}")
    print(f"  Costs: spread={costs['spread_pips_per_trade']}p, comm={costs['commission_pips_per_trade']}p, total={costs['total_cost_pips_per_trade']}p")
    print(f"  Adjusted: trades={adj['trades']}, wr={adj['wr']}%, pf={adj['pf']}")
    print(f"  Delta: wr_change={delta['wr_change']}, pnl_change={delta['pnl_change_pct']}%")

print()
print("=== ALL PAIRS: Original vs New trade counts ===")
print(f"{'Pair':<10} {'Orig Trades':>12} {'New Raw Trades':>15} {'New Adj Trades':>15} {'Delta':>10}")
print("-" * 65)

# Get all pairs from both
all_pairs = sorted(set(list(orig.keys()) + list(new.keys())))
for pair in all_pairs:
    orig_trades = "N/A"
    new_raw = "N/A"
    new_adj = "N/A"
    
    if pair in orig:
        o = orig[pair]
        if isinstance(o, dict):
            # Try to get the floor (max trades) value
            if 'floor' in o:
                orig_trades = o['floor'].get('trades', 'N/A')
            elif 'trades' in o:
                orig_trades = o['trades']
            else:
                # It might be a list of sweep results
                for k, v in o.items():
                    if isinstance(v, dict) and 'trades' in v:
                        orig_trades = v['trades']
                        break
    
    if pair in new:
        new_raw = new[pair]['raw']['trades']
        new_adj = new[pair]['adjusted']['trades']
    
    if orig_trades != "N/A" and new_raw != "N/A":
        delta = int(new_raw) - int(orig_trades)
        print(f"{pair:<10} {orig_trades:>12} {new_raw:>15} {new_adj:>15} {delta:>+10}")
    else:
        print(f"{pair:<10} {str(orig_trades):>12} {str(new_raw):>15} {str(new_adj):>15}")
