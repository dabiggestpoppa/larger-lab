import json

# Let's look at CHFJPY max_accuracy entries — it has 18 entries
# with triggers from 17.0 to 37.25
# And the individual CHFJPY file has 8 entries with triggers from 7.7 to 11.7

max_acc = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json'))

print("=== CHFJPY max_accuracy entries (18 total) ===")
chf = max_acc['CHFJPY']
if isinstance(chf, list):
    for e in sorted(chf, key=lambda x: x['t1_trigger']):
        print(f"  t1={e['t1_trigger']:6.2f} | trades={e['trades']:5d} | wr={e['wr']:.1f}% | pf={e['pf']:.1f} | days={e['days']}")

print("\n=== So the max_accuracy file has triggers at 17.0 (FLOOR) up to 37.25 (CEILING) ===")
print("The individual file has triggers at 7.7 to 11.7 (max trades / floor sweep)")

# Check EURUSD
print("\n=== EURUSD max_accuracy entries (12 total) ===")
eu = max_acc['EURUSD']
if isinstance(eu, list):
    for e in sorted(eu, key=lambda x: x['t1_trigger']):
        print(f"  t1={e['t1_trigger']:6.2f} | trades={e['trades']:5d} | wr={e['wr']:.1f}% | pf={e['pf']:.1f} | days={e['days']}")

# The max_accuracy file has triggers starting at the config T1 value (12.0 for EURUSD)
# and going UP (14, 16, 18, ... 27) — this is the ACCURACY sweep (ceiling direction)

# The individual files have triggers starting BELOW the config T1 value
# and going up — this is the TRADES sweep (floor direction)

# SO: the June 4th run had TWO sweeps:
# 1. Max trades (floor): sweep triggers DOWN from config T1 to find max trades
# 2. Max accuracy (ceiling): sweep triggers UP from config T1 to find max WR
# The max_accuracy.json file contains BOTH sets merged together

# The FLOOR value for CHFJPY at t1=17.0 gives 5599 trades
# But wait — the individual file has LOWER triggers (7.7-11.7) but isn't in max_accuracy?
# Let me check if max_accuracy has entries at those lower triggers...

print("\n=== CHECKING IF MAX_ACCURACY HAS FLOOR ENTRIES ===")
for pair in ['EURUSD', 'CHFJPY', 'GBPJPY']:
    entries = max_acc[pair]
    if isinstance(entries, list):
        triggers = sorted(e['t1_trigger'] for e in entries)
        print(f"{pair}: {len(entries)} entries, triggers from {triggers[0]:.1f} to {triggers[-1]:.1f}")
        print(f"  Full: {triggers}")
