import json

# Deep dive: the new sweep has MULTIPLIER-based entries
# The baseline has single entries per trigger value
# The new sweep sweeps across multipliers (0.3, 0.4, 0.5, ...)
# But the baseline swept across absolute trigger values

# Key finding: CHFJPY at mult=0.3, t1=5.1 gives 2148 trades at 1.34 tr/d
# But baseline CHFJPY at t1=17.0 gives 5599 trades at 4.19 tr/d
# These are DIFFERENT trigger values, so not directly comparable

# The real comparison: what does the new sweep give at the SAME trigger as baseline?
# And what does the baseline give at mult=1.0?

# Let me check: does the baseline have mult=1.0 entries?
base = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json'))

print("=== BASELINE STRUCTURE ===")
for pair in ['EURUSD', 'CHFJPY', 'EURJPY']:
    entries = base[pair] if isinstance(base[pair], list) else [base[pair]]
    print(f"\n{pair}: {len(entries)} entries")
    for e in entries[:3]:
        print(f"  {e}")
    print(f"  ...")
    for e in entries[-2:]:
        print(f"  {e}")

# Check: the baseline EURUSD has 12 entries - is this a sweep across triggers?
# And the new sweep has entries across multipliers
# These are DIFFERENT sweep dimensions!
print("\n=== SWEEP DIMENSION ANALYSIS ===")
eu_base = base['EURUSD']
if isinstance(eu_base, list):
    triggers = [e['t1_trigger'] for e in eu_base]
    print(f"EURUSD baseline triggers: {sorted(triggers)}")
    print(f"  -> Sweep across {len(triggers)} trigger values")
    print(f"  -> Days: {eu_base[0]['days']} (all same)")
    print(f"  -> This is a TRIGGER sweep at fixed config")

# New sweep
new = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_forex_full.json'))
chf_new = new['CHFJPY']
multipliers = [e.get('multiplier') for e in chf_new]
print(f"\nCHFJPY new multipliers: {sorted(multipliers)}")
print(f"  -> Sweep across {len(multipliers)} multiplier values")
print(f"  -> Days: {chf_new[0]['days']} (all same)")
print(f"  -> This is a MULTIPLIER sweep (trigger = base_trigger * multiplier)")

# So the question is: what's the BASE trigger for CHFJPY?
# If base trigger is 17.0 (from deploy_config), then:
# mult=0.3 -> t1=5.1
# mult=0.5 -> t1=8.5
# mult=1.0 -> t1=17.0
# But the new sweep at mult=1.0 shows t1=17.0 with only 153 trades!
# While baseline at t1=17.0 shows 5599 trades!

print("\n=== CRITICAL: CHFJPY at t1=17.0 ===")
chf_base = base['CHFJPY']
if isinstance(chf_base, list):
    for e in chf_base:
        if abs(e['t1_trigger'] - 17.0) < 0.1:
            print(f"Baseline: trades={e['trades']}, wr={e['wr']:.1f}%, pf={e['pf']:.1f}, days={e['days']}, tr/d={e['tr_per_day']:.3f}")

chf_new_entries = new['CHFJPY']
for e in chf_new_entries:
    if abs(e['t1_trigger'] - 17.0) < 0.1:
        print(f"New:      trades={e['trades']}, wr={e['wr']:.1f}%, pf={e['pf']:.1f}, days={e['days']}, tr/d={e['tr_per_day']:.3f}")
        print(f"  multiplier={e.get('multiplier')}")

# The days are different: 1336 vs 1599
# But even normalized by days, the trade rate is way off
# Baseline: 5599/1336 = 4.19 tr/d
# New: 153/1599 = 0.096 tr/d
# That's a 97.7% difference!

print("\n=== THE SMOKING GUN ===")
print("CHFJPY at t1=17.0:")
print(f"  Baseline: 5599 trades / 1336 days = 4.19 tr/d")
print(f"  New:      153 trades / 1599 days = 0.096 tr/d")
print(f"  Ratio: {4.19/0.096:.1f}x difference in trade rate!")
print()
print("This is NOT a data window issue.")
print("The new sweep is finding 44x FEWER trades per day.")
print("Something fundamental changed in the engine or config.")
