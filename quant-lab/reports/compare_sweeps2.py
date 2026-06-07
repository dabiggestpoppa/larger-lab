import json

base = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json'))
new = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_forex_full.json'))

# Key comparison: EURUSD baseline has 12 entries (sweep across triggers)
# Let's compare EURUSD at similar trigger values
print("=== EURUSD BASELINE (12 entries) ===")
for e in base['EURUSD']:
    print(f"  t1={e['t1_trigger']:5.1f} | trades={e['trades']:5d} | wr={e['wr']:.1f}% | pf={e['pf']:.1f} | pnl={e['pnl']:.0f} | tr/d={e['tr_per_day']:.2f}")

print("\n=== EURUSD NEW SWEEP ===")
if 'EURUSD' in new:
    for e in new['EURUSD']:
        mult = e.get('multiplier', '?')
        print(f"  t1={e['t1_trigger']:5.1f} | mult={mult} | trades={e['trades']:5d} | wr={e['wr']:.1f}% | pf={e['pf']:.1f} | pnl={e['pnl']:.0f} | tr/d={e['tr_per_day']:.2f}")
else:
    print("  EURUSD NOT IN NEW SWEEP")

# Now compare overlapping JPY pairs at CLOSEST trigger values
print("\n=== JPY PAIRS: BASELINE vs NEW at similar triggers ===")
overlap = sorted(set(base.keys()) & set(new.keys()))

for pair in overlap:
    b_entries = base[pair] if isinstance(base[pair], list) else [base[pair]]
    n_entries = new[pair] if isinstance(new[pair], list) else [new[pair]]
    
    # Get baseline at its "best" or most common trigger
    # Get new at mult=1.0 (closest to baseline)
    
    # Baseline: pick the entry with most trades (FLOOR-like)
    b_best = max(b_entries, key=lambda x: x.get('trades', 0))
    
    # New: pick mult=1.0 or closest
    n_at_1 = [e for e in n_entries if abs(e.get('multiplier', 0) - 1.0) < 0.01]
    if n_at_1:
        n_cmp = n_at_1[0]
        tag = "mult=1.0"
    else:
        n_cmp = n_entries[len(n_entries)//2]
        tag = f"mult={n_cmp.get('multiplier','?')}"
    
    b_tr = b_best['trades']
    n_tr = n_cmp['trades']
    delta = b_tr - n_tr
    pct = (delta / b_tr * 100) if b_tr > 0 else 0
    
    print(f"\n{pair}:")
    print(f"  Baseline: t1={b_best['t1_trigger']:.1f} | trades={b_tr:5d} | wr={b_best['wr']:.1f}% | pf={b_best['pf']:.1f} | days={b_best['days']}")
    print(f"  New:      t1={n_cmp['t1_trigger']:.1f} | {tag} | trades={n_tr:5d} | wr={n_cmp['wr']:.1f}% | pf={n_cmp['pf']:.1f} | days={n_cmp['days']}")
    print(f"  DELTA: {delta:+d} trades ({pct:+.1f}%)")
    
    # Also check: is the days count different? That would explain trade count diff
    if b_best['days'] != n_cmp['days']:
        print(f"  *** DAYS DIFFER: baseline={b_best['days']} vs new={n_cmp['days']} ***")

# Summary stats
print("\n=== SUMMARY ===")
print(f"Baseline pairs: {len(base)}")
print(f"New sweep pairs: {len(new)}")
print(f"Overlap: {len(overlap)}")

# Check if baseline has entries with different day counts (indicating different data windows)
day_counts_base = set()
for pair, entries in base.items():
    if isinstance(entries, list):
        for e in entries:
            day_counts_base.add(e.get('days', 0))
    else:
        day_counts_base.add(entries.get('days', 0))

day_counts_new = set()
for pair, entries in new.items():
    if isinstance(entries, list):
        for e in entries:
            day_counts_new.add(e.get('days', 0))
    else:
        day_counts_new.add(entries.get('days', 0))

print(f"\nBaseline day counts: {sorted(day_counts_base)}")
print(f"New sweep day counts: {sorted(day_counts_new)}")
