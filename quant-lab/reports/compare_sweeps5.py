import json

base = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json'))

# Check entry counts per pair
print("=== BASELINE ENTRY COUNTS ===")
for pair in sorted(base.keys()):
    entries = base[pair] if isinstance(base[pair], list) else [base[pair]]
    days_set = set(e.get('days') for e in entries)
    triggers = sorted(set(e.get('t1_trigger') for e in entries))
    print(f"{pair}: {len(entries)} entries, days={sorted(days_set)}, triggers={triggers[:4]}...")

# The key question: CHFJPY has 18 entries with different triggers
# Are these from DIFFERENT sweep runs merged together?
print("\n=== CHFJPY ALL 18 ENTRIES ===")
chf = base['CHFJPY']
if isinstance(chf, list):
    for i, e in enumerate(chf):
        print(f"  [{i:2d}] t1={e['t1_trigger']:6.2f} | trades={e['trades']:5d} | wr={e['wr']:.1f}% | pf={e['pf']:.1f} | days={e['days']} | tr/d={e['tr_per_day']:.3f}")

# Check if the 5599 trade entry is an outlier
print("\n=== CHFJPY TRADE COUNT DISTRIBUTION ===")
if isinstance(chf, list):
    trades = [e['trades'] for e in chf]
    print(f"  Min: {min(trades)}")
    print(f"  Max: {max(trades)}")
    print(f"  Mean: {sum(trades)/len(trades):.0f}")
    print(f"  Median: {sorted(trades)[len(trades)//2]}")
    
# Check: are there entries with the SAME trigger but different trade counts?
if isinstance(chf, list):
    from collections import Counter
    trigger_counts = Counter(e['t1_trigger'] for e in chf)
    print(f"\n  Duplicate triggers: {[(t,c) for t,c in trigger_counts.items() if c > 1]}")
