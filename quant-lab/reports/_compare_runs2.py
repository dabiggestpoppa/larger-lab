"""Compare original June 4th sweep vs new cost analysis."""
import json

with open('trigger_sweep_max_accuracy.json', 'r') as f:
    orig = json.load(f)

with open('cost_analysis_native.json', 'r') as f:
    new = json.load(f)

print("=== EURUSD: Original June 4th sweep (all trigger levels) ===")
print()
if 'EURUSD' in orig:
    for entry in orig['EURUSD']:
        t1 = entry['t1_trigger']
        trades = entry['trades']
        wr = entry['wr']
        pf = entry['pf']
        tr_d = entry['tr_per_day']
        print(f"  T1={t1:>5.1f}p | trades={trades:>5} | WR={wr:>5.1f}% | PF={pf:>5.2f} | tr/d={tr_d:.2f}")

print()
print("=== EURUSD: New cost analysis ===")
if 'EURUSD' in new:
    raw = new['EURUSD']['raw']
    print(f"  Raw: trades={raw['trades']}, WR={raw['wr']}%, PF={raw['pf']}")

print()
print("=== KEY COMPARISON: Original floor (T1=12) vs New raw ===")
print()

# For each pair, find the original entry with T1=12 (or closest to native)
# and compare with new raw
pairs = sorted(set(list(orig.keys()) + list(new.keys())))
print(f"{'Pair':<10} {'Orig T1=12':>12} {'Orig WR':>8} {'Orig PF':>8} {'New Raw':>10} {'New WR':>8} {'New PF':>8} {'Trade Δ':>10}")
print("-" * 80)

for pair in pairs:
    orig_t12 = None
    new_raw = None
    
    if pair in orig:
        for entry in orig[pair]:
            if abs(entry['t1_trigger'] - 12.0) < 0.1:
                orig_t12 = entry
                break
        if orig_t12 is None:
            # Find the entry with max trades (floor)
            orig_t12 = max(orig[pair], key=lambda x: x['trades'])
    
    if pair in new:
        new_raw = new[pair]['raw']
    
    if orig_t12 and new_raw:
        delta = new_raw['trades'] - orig_t12['trades']
        print(f"{pair:<10} {orig_t12['trades']:>12} {orig_t12['wr']:>7.1f}% {orig_t12['pf']:>7.2f} {new_raw['trades']:>10} {new_raw['wr']:>7.1f}% {new_raw['pf']:>7.2f} {delta:>+10}")
    elif orig_t12:
        print(f"{pair:<10} {orig_t12['trades']:>12} {orig_t12['wr']:>7.1f}% {orig_t12['pf']:>7.2f} {'N/A':>10} {'N/A':>8} {'N/A':>8} {'N/A':>10}")
    elif new_raw:
        print(f"{pair:<10} {'N/A':>12} {'N/A':>8} {'N/A':>8} {new_raw['trades']:>10} {new_raw['wr']:>7.1f}% {new_raw['pf']:>7.2f} {'N/A':>10}")
