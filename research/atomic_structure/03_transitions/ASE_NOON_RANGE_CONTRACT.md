# ASE_NOON_RANGE_CONTRACT.md

Checkpoint: ASE-2.2-NOON-AND-POST25-EVENT-GEOMETRY-REPAIR
Branch: agent/atomic-structure-foundry
Base: 7d712ccd66ef854f4efa1f8cf9d9501dde02a2c9

## Purpose

Freeze the exact pre-noon extreme anchors and noon decision-time price used
for every noon-lock calculation. Replaces the single ambiguous 03:00-12:00
"H_AM / L_AM" used in ASE-2.1.

## Noon knowledge boundary

- Research day D runs 19:00 (D-1) -> next 03:00 (D+1), America/New_York.
- Noon is 12:00 New York on day D.
- All states assigned to completed M5 bars strictly before 12:00.
- `P_12` = last completed M5 close before 12:00 = the **11:55 close** for
  regular sessions (verified in the repaired ledger `P_12_time`).
- The 12:00-12:05 bar is never used for noon knowledge.

## Two pre-noon range objects (kept separate, never collapsed)

A. LONDON_NY_MORNING_RANGE
   window: 03:00 -> 12:00 day D
   fields: H_3_12, L_3_12

B. FULL_PRE_NOON_DAY_RANGE
   window: 19:00 (D-1) -> 12:00 day D (includes Asia + London + NY overlap)
   fields: H_PRE12, L_PRE12

The primary noon-lock hypothesis is tested against H_PRE12 / L_PRE12.
The 03:00-12:00 object is retained as a secondary descriptive comparison.

## Violation semantics (post-noon, all bars with local >= 12:00)

TOUCH   high > H_PRE12 (up) or low < L_PRE12 (down)
CLOSE   close > H_PRE12 (up) or close < L_PRE12 (down)

Side-specific busts reported separately (viol_up_full, viol_dn_full).

## Horizons

- H17: 12:00 -> 17:00  (AFTERNOON_LOCK)
- H19: 12:00 -> 19:00  (REST_OF_NY_LOCK)
- H03: 12:00 -> next 03:00 (FULL_RESEARCH_DAY_LOCK)

Each horizon is computed from raw bars only within that window; they are not
cumulative by default.

## Headline repaired numbers (H17, FULL_PRE_NOON anchor, touch)

- overall: 23.3% of sessions hold without touching a new pre-noon extreme
- T1: 19.4% hold (n=??)    -> see ASE_NOON_EXTREME_HOLD_REPAIRED.csv
- T2: 22.3% hold
- T3: 36.1% hold
- NO-GO: excluded from tier tables (kept in OVERALL)

Source claim "T3 noon hold ~98%" is NOT reproduced under the repaired
FULL_PRE_NOON definition; it is marked DISAGREE_UNDER_REPAIRED_DEFINITION
(see ASE_MECHANISM_SOURCE_COMPARISON_REPAIRED.csv).

## Files produced

- ASE_NOON_EXTREME_LEDGER_REPAIRED.parquet
- ASE_NOON_EXTREME_HOLD_REPAIRED.csv
- ASE_NOON_HORIZON_MATRIX.csv