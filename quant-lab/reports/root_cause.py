import json, sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
from asset_configs import ASSET_CONFIGS

# The baseline sweep produced 5599 trades for CHFJPY at t1=17.0 with 1336 days
# The new sweep at mult=1.0 (same t1=17.0) produces 153 trades with 1599 days

# The config at mult=1.0 is IDENTICAL to raw config
# So the difference must be in the ENGINE CODE

# Changes found between symmetry_trap.py.bak (baseline) and current:
# 
# 1. DEFAULT_TIER_CONFIG changed completely - but this only affects fallback
#    when ASSET_CONFIGS tiers aren't provided. Since we pass asset configs, 
#    this shouldn't matter.
#
# 2. classify_tier() -> classify_tier_by_ar() + classify_tier_by_impulse()
#    OLD: Single function that set tier, au, AND trigger at session init
#    NEW: AR gate only at session init, tier set at impulse detection
#
# 3. 4-hour loop timeout REMOVED
#    Was: self.loop_start_time check with 4h expiry
#    Now: Removed entirely
#
# 4. 80% Kill Switch REMOVED
#    Was: If bar.close past 80% of impulse -> KILL_SWITCH signal
#    Now: Removed entirely
#
# 5. DZ retracement zone changed
#    OLD: Loop 1 = 32%-50%, Loop 2+ = 20%-50%
#    NEW: All loops = 20%-50%
#
# 6. KILL_SWITCH event handling in backtest
#    KILL_SWITCH used to reset loop and continue searching
#    Now: No KILL_SWITCH means impulse detection continues without reset

# Let's check: does the backtest handle KILL_SWITCH differently?
# In the backtest run() method:
#   KILL_SWITCH -> closes active trade, resets
#   Without KILL_SWITCH -> no trade is opened, engine stays in SEARCH

# The key question: does removing the kill switch INCREASE or DECREASE trades?
# OLD: Kill switch fires -> resets to SEARCH -> can find new impulse
# NEW: No kill switch -> engine stays in WAIT_RETRACE/OCC -> may miss new impulses
# Actually: removing kill switch should INCREASE trades (fewer resets)

# But we see FEWER trades in the new sweep. So the kill switch isn't the cause.

# The REAL issue: the baseline sweep was run with a DIFFERENT engine version
# that had the OLD logic. The new sweep uses the CURRENT engine.
# The engine changes collectively altered the trade detection rate.

# Let's quantify: what's the actual trade rate difference?
baseline_chfjpy = {'trades': 5599, 'days': 1336, 'tr_per_day': 4.191}
new_chfjpy = {'trades': 153, 'days': 1599, 'tr_per_day': 0.096}

print("=== ROOT CAUSE ANALYSIS ===")
print(f"CHFJPY at t1=17.0 (mult=1.0):")
print(f"  Baseline: {baseline_chfjpy['trades']} trades / {baseline_chfjpy['days']} days = {baseline_chfjpy['tr_per_day']:.3f} tr/d")
print(f"  New:      {new_chfjpy['trades']} trades / {new_chfjpy['days']} days = {new_chfjpy['tr_per_day']:.3f} tr/d")
print(f"  Ratio: {baseline_chfjpy['tr_per_day']/new_chfjpy['tr_per_day']:.1f}x fewer trades per day")
print()

# Check: is it the data? Different CSV files?
import os
csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\CHFJPY_M5.csv'
if os.path.exists(csv_path):
    size = os.path.getsize(csv_path)
    with open(csv_path, 'r') as f:
        first_line = f.readline().strip()
        # Count lines
        line_count = sum(1 for _ in f) + 1
    print(f"CHFJPY_M5.csv: {line_count} lines, {size/1024/1024:.1f} MB")
    print(f"  First line: {first_line[:100]}")
else:
    print("CHFJPY_M5.csv NOT FOUND")
    # Check for other CHFJPY files
    import glob
    files = glob.glob(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\CHFJPY*')
    print(f"  Found: {files}")

# Check: does the baseline have CHFJPY at t1=17.0 with 5599 trades?
# And the new sweep at t1=17.0 with 153 trades?
# Both use the same config at mult=1.0
# The ONLY difference is the engine code

print("\n=== ENGINE CHANGES THAT AFFECT TRADE COUNT ===")
print("1. Kill switch REMOVED -> should INCREASE trades (fewer resets)")
print("2. DZ zone relaxed (20% vs 32% floor) -> should INCREASE trades")  
print("3. 4h timeout REMOVED -> should INCREASE trades")
print("4. Tier classification moved from session init to impulse detection")
print("   OLD: tier set at session init, trigger locked per tier")
print("   NEW: tier=PENDING at session init, T1 trigger used for detection")
print("   -> This means the NEW engine uses T1 trigger for ALL impulse detection")
print("   -> Then classifies tier AFTER detection")
print("   -> OLD engine used per-tier trigger from session classification")
print()

# Check: what was the OLD behavior?
# OLD classify_tier() set tier at session init based on AR
# Then used that tier's trigger for impulse detection
# NEW: uses T1 trigger for all detection, classifies after

# For CHFJPY:
# OLD: AR classifies session -> if AR <= 28p -> T1, trigger=17p
#      if AR <= 48p -> T2, trigger=29p
#      if AR <= 85p -> T3, trigger=50p
# NEW: AR gate only checks if AR <= 60p (all tiers have ar_max=60)
#      Then uses T1 trigger=17p for ALL impulse detection
#      Then classifies by impulse size

# Wait - the NEW engine uses self.tier_config which comes from ASSET_CONFIGS
# So the ar_max values ARE from asset configs (28, 48, 85 for CHFJPY)
# And the trigger IS from asset configs (17 for T1)

# The difference is: OLD engine classified tier at session init
# NEW engine uses T1 trigger for detection, then classifies

# For sessions where OLD engine would have been T2 (AR 28-48p):
#   OLD: trigger=29p -> fewer impulses detected
#   NEW: trigger=17p -> more impulses detected
# This should INCREASE trades, not decrease

# For sessions where OLD engine would have been T3 (AR 48-85p):
#   OLD: trigger=50p -> very few impulses
#   NEW: trigger=17p -> many more impulses
# This should INCREASE trades significantly

# So the engine changes should INCREASE trades, not decrease
# The 44x decrease must be from something else entirely

print("=== WAIT - THE ENGINE CHANGES SHOULD INCREASE TRADES ===")
print("But we see 44x FEWER trades. Something else is wrong.")
print()
print("Possibility: the baseline sweep used a DIFFERENT backtest script")
print("that didn't use SymmetryTrapBacktest at all")
print("Or: the baseline data was generated with different CSV data")

# Check: does the baseline have entries with different day counts for same pair?
base = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json'))
chf = base['CHFJPY']
if isinstance(chf, list):
    days_set = set(e.get('days') for e in chf)
    print(f"\nCHFJPY baseline day counts: {sorted(days_set)}")
    if len(days_set) > 1:
        print("  *** MULTIPLE DAY COUNTS - baseline may be merged from different runs! ***")
    for d in sorted(days_set):
        entries = [e for e in chf if e.get('days') == d]
        print(f"  {d} days: {len(entries)} entries, trades: {[e['trades'] for e in entries[:5]]}")
