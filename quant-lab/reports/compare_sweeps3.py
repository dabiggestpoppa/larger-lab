import json

base = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json'))
new = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_forex_full.json'))

print("=== NORMALIZED COMPARISON (trades/day at same trigger) ===")
overlap = sorted(set(base.keys()) & set(new.keys()))

print(f"\n{'Pair':<10} {'Trigger':>7} {'B_Tr/d':>8} {'N_Tr/d':>8} {'Delta%':>8} {'B_Days':>7} {'N_Days':>7}")
print("-" * 60)

for pair in overlap:
    b_entries = base[pair] if isinstance(base[pair], list) else [base[pair]]
    n_entries = new[pair] if isinstance(new[pair], list) else [new[pair]]
    
    # Get all baseline triggers
    b_triggers = set(e['t1_trigger'] for e in b_entries)
    n_triggers = set(e['t1_trigger'] for e in n_entries)
    common = b_triggers & n_triggers
    
    if not common:
        # Find closest
        for bt in sorted(b_triggers)[:3]:
            closest = min(n_triggers, key=lambda x: abs(x - bt))
            b_e = [e for e in b_entries if e['t1_trigger'] == bt][0]
            n_e = [e for e in n_entries if e['t1_trigger'] == closest][0]
            b_td = b_e['tr_per_day']
            n_td = n_e['tr_per_day']
            delta_pct = ((b_td - n_td) / b_td * 100) if b_td > 0 else 0
            print(f"{pair:<10} {bt:>7.1f} {b_td:>8.3f} {n_td:>8.3f} {delta_pct:>+7.1f}% {b_e['days']:>7} {n_e['days']:>7}")
    else:
        for t in sorted(common)[:3]:
            b_e = [e for e in b_entries if e['t1_trigger'] == t][0]
            n_e = [e for e in n_entries if e['t1_trigger'] == t][0]
            b_td = b_e['tr_per_day']
            n_td = n_e['tr_per_day']
            delta_pct = ((b_td - n_td) / b_td * 100) if b_td > 0 else 0
            print(f"{pair:<10} {t:>7.1f} {b_td:>8.3f} {n_td:>8.3f} {delta_pct:>+7.1f}% {b_e['days']:>7} {n_e['days']:>7}")

# Now the critical question: WHY do days differ?
# Baseline: 1336-1343 days for some pairs, 3101-3103 for others
# New: 1599, 1607, 3888

print("\n=== DAY COUNT ANALYSIS ===")
print("Baseline groups:")
for days in sorted(set(e.get('days',0) for p in base for e in (base[p] if isinstance(base[p],list) else [base[p]]))):
    pairs_at_days = []
    for pair, entries in base.items():
        elist = entries if isinstance(entries, list) else [entries]
        if any(e.get('days') == days for e in elist):
            pairs_at_days.append(pair)
    print(f"  {days} days: {len(pairs_at_days)} pairs - {pairs_at_days[:5]}...")

print("\nNew sweep groups:")
for days in sorted(set(e.get('days',0) for p in new for e in (new[p] if isinstance(new[p],list) else [new[p]]))):
    pairs_at_days = []
    for pair, entries in new.items():
        elist = entries if isinstance(entries, list) else [entries]
        if any(e.get('days') == days for e in elist):
            pairs_at_days.append(pair)
    print(f"  {days} days: {len(pairs_at_days)} pairs - {pairs_at_days}")

# The real question: same pair, different days = different data windows
# This means the sweeps are running on DIFFERENT HISTORICAL DATA
print("\n=== ROOT CAUSE CHECK ===")
print("CHFJPY: baseline days=1336, new days=1599")
print("  -> Different data windows!")
print("  -> Baseline: ~3.7 years of data")
print("  -> New: ~4.4 years of data")
print("  -> The new sweep has 263 MORE days of data")
print("  -> But produces FEWER trades per day (1.34 vs 4.19)")
print("  -> This means the EXTRA 263 days are producing NEAR-ZERO trades")
print("  -> Something in the engine is filtering out trades in that extra period")

# Check: does the new sweep have a different config?
print("\n=== CHECKING NEW SWEEP ENTRIES FOR CONFIG HINTS ===")
for pair in ['EURJPY', 'CHFJPY']:
    entries = new[pair]
    print(f"\n{pair} new sweep entries:")
    for e in entries[:5]:
        print(f"  mult={e.get('multiplier','?')} t1={e['trades']:4d} tr={e['trades']:4d} wr={e['wr']:.1f}% days={e['days']} tr/d={e['tr_per_day']:.3f}")
