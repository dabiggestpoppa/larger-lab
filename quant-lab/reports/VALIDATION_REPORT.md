# DATA VALIDATION REPORT — Baseline vs New Sweep
# Generated: 2026-06-07 12:00 EDT

## EXECUTIVE SUMMARY

The new sweep (trigger_sweep_forex_full.json) produces **44x fewer trades per day** 
than the baseline (trigger_sweep_max_accuracy.json) for the same pairs at the same 
trigger values. This is a SYSTEMIC issue affecting ALL 7 overlapping JPY pairs.

## DATA COMPARISON

### CHFJPY at t1=17.0 (mult=1.0, identical config):
- Baseline:  5599 trades / 1336 days = 4.19 tr/d
- New sweep:  153 trades / 1599 days = 0.096 tr/d
- Ratio: 43.7x fewer trades per day in new sweep

### All 7 overlapping JPY pairs show same pattern:
- AUDJPY: 99.4% fewer trades/day at t1=26.0
- CADJPY: 99.0% fewer trades/day at t1=23.0  
- CHFJPY: 97.7% fewer trades/day at t1=17.0
- EURJPY: 99.2% fewer trades/day at t1=35.0
- GBPJPY: 97.0% fewer trades/day at t1=23.0
- NZDJPY: 99.2% fewer trades/day at t1=24.0
- USDJPY: 97.7% fewer trades/day at t1=19.0

This is NOT pair-specific. It's systemic.

## ROOT CAUSE ANALYSIS

### What DIDN'T change:
1. Config values at mult=1.0 are IDENTICAL to raw ASSET_CONFIGS
2. CSV data file is the same (CHFJPY_M5.csv)
3. Pip size is the same (0.01 from config)
4. AR gate logic is functionally equivalent

### What DID change (engine code: symmetry_trap.py):

1. **DEFAULT_TIER_CONFIG values changed** (only affects fallback, not asset configs)
   OLD: T1={ar_max:20, au:10, trigger:12}, T2={ar_max:30, au:12, trigger:15}, T3={ar_max:45, au:15, trigger:19}
   NEW: T1={ar_max:60, au:8, trigger:10}, T2={ar_max:60, au:10, trigger:10}, T3={ar_max:60, au:12, trigger:10}

2. **classify_tier() split into two functions**
   OLD: classify_tier() at session init sets tier+trigger based on AR
   NEW: classify_tier_by_ar() gates only, classify_tier_by_impulse() at detection

3. **80% Kill Switch REMOVED** (should INCREASE trades)
   OLD: bar.close past 80% of impulse -> KILL_SWITCH -> reset
   NEW: No kill switch

4. **DZ retracement zone relaxed** (should INCREASE trades)
   OLD: Loop 1 = 32%-50%, Loop 2+ = 20%-50%
   NEW: All loops = 20%-50%

5. **4-hour loop timeout REMOVED** (should INCREASE trades)
   OLD: Loop expires after 4 hours
   NEW: No timeout

### Net effect of engine changes:
All 5 changes should INCREASE or maintain trade count. None should decrease it.
Yet we see 44x FEWER trades.

## THE ACTUAL CULPRIT

The baseline sweep used OFTEN ENGINE CODE (symmetry_trap.py.bak) which has
FUNDAMENTALLY DIFFERENT logic:

1. OLD engine classified tier at SESSION INIT and locked the trigger
   - T1 sessions: trigger=17 (for CHFJPY)
   - T2 sessions: trigger=29
   - T3 sessions: trigger=50

2. NEW engine uses T1 trigger for ALL detection, classifies AFTER
   - All sessions: trigger=17 (for CHFJPY)
   - Then classifies by impulse size

This should actually INCREASE trades in the new engine (lower trigger for T2/T3).

BUT: The OLD engine had the kill switch and 4h timeout which could RESET the 
engine, allowing it to find MORE impulses in a single session. The NEW engine
has no reset - once it enters WAIT_RETRACE, it stays there until OCC or the 
end of the session. This means:
- OLD: Kill switch fires -> reset to SEARCH -> find new impulse -> MORE trades
- NEW: No kill switch -> stuck in WAIT_RETRACE -> MISS subsequent impulses -> FEWER trades

THIS is the explanation for fewer trades. The kill switch removal is the root cause.

## ADDITIONAL FACTORS

1. The new sweep only covers 7 JPY pairs out of 28 total
2. The baseline covers all 28 pairs with varying entry counts (1-24 per pair)
3. The new sweep CSV data has 1599 days vs baseline's 1336 days for CHFJPY
   (CSV was updated with 263 more days between June 4 and June 7)

## RECOMMENDATION

1. REVERT the kill switch removal - it was incorrectly flagged as "dead code"
   but actually served a critical function (reset engine to find new impulses)
2. Re-run the full 28-pair sweep with the corrected engine
3. Verify that trade counts match baseline within reasonable tolerance (±10%)
4. Only THEN proceed with combinatorics and deployment decisions

## IMPACT

All combinatorics calculations, velocity optimizers, and deployment configs
derived from the new sweep data are INVALID until this is resolved.
