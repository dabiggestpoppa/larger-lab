# ASE_R2_2_REPORT.md

Checkpoint: ASE-2.2-NOON-AND-POST25-EVENT-GEOMETRY-REPAIR
Branch: agent/atomic-structure-foundry
Base: 7d712ccd66ef854f4efa1f8cf9d9501dde02a2c9
Dataset: EURUSDPRO M5 (2023-2025), SHA256 46e81261f5799fdebb4a2d2aed045c91ad5f2bbe3324c0275cb3cc322f18b13b
Development: 2023-01-03 .. 2024-12-31 (442 sessions)

## What was wrong with the old noon test

ASE-2.1 anchored H_AM / L_AM on the 03:00-12:00 path only, testing
"post-noon violation of the London/NY morning range", not the full pre-noon
day extreme. It also used the closing price of the 12:00-12:05 bar
(sometimes the next day's), breaking the noon knowledge boundary.

## Repaired noon contract

- FULL_PRE_NOON_DAY_RANGE = 19:00 (D-1) -> 12:00 (H_PRE12 / L_PRE12) is the
  primary anchor.
- LONDON_NY_MORNING_RANGE = 03:00 -> 12:00 remains secondary.
- P_12 = last completed M5 close before 12:00 (11:55 close).
- Horizons: 12->17, 12->19, 12->next 03, each from raw bars.

## How often does the FULL pre-noon daily extreme hold after 12?

touch semantics, H17 (12:00->17:00):
  overall hold 23.3% (touch) / 29.9% (close)
  T1 19.4% / 25.4%
  T2 22.3% / 29.5%
  T3 36.1% / 44.3%
H03 (next 03:00): overall 16.7% (touch) / 21.7% (close) / 83.3% violated.

So noon DOES NOT seal the day's extremes: roughly 3 of 4 sessions touch a new
pre-noon extreme in the afternoon; T3 holds most (36%), never ~98%.

## What % of variance remains after noon under each denominator?

RV shares (median over 442 days):
  share_17      33.1%   (RV_AFTERNOON / RV_19_TO_17)
  share_next03  29.0%   (RV_AFTERNOON / RV_19_TO_NEXT_03)
  share_24h     31.5%   (RV_AFTERNOON / RV_24H_19_TO_19)
Range contributions: 17h=29.1%, next03=23.8%.
The 10-15% source claim is not reproduced under any audited denominator
(see ASE_VARIANCE_CLOCK_AUDIT.md).

## What was wrong with the old -25 event test? And the E25/E50 levels

ASE-2.1 treated a second touch of the SAME +/-25% level as "another 25
extension" (a retouch, not an extension). Repaired geometry:

E25 = band +/- 0.25*AR
E50 = band +/- 0.50*AR     <- the "ANOTHER_25_EXTENSION" event
E100 = band +/- 1.00*AR

Retouch vs extension are separate first-event candidates.

Also two direction/bias contracts were separated:
  E25_RAW_FIRST_SIDE  (whichever side first)
  E25_CEREBUS_VALID   (only the side of the first M5 close beyond the Asian
                       band, i.e. bias lock)
plus touch- vs close-completion variants, and same-bar ambiguity resolution.

## True post-25 opposite-band hold rate

E25_CEREBUS_VALID (touch completion; opposite band touched later):
  T1 59.6% reversal (n=218)
  T2 47.6% reversal (n=126)
  T3 23.1% reversal (n=52)
  overall 50.2% reversal (n=404)

Close-completion variant (E25_CEREBUS_VALID_CLOSE): overall 46.2% reversal.
This is a strong tier gradient but nowhere near the ~4.2% reversal claim.

## What happens first after -25?

First-event ordering (E25_CEREBUS_VALID touch):
  E25_RETOUCH       81%
  E50_EXTENSION     10%
  ASIAN_MIDPOINT     0.8%
  SAME_BAR_ORDER_UNRESOLVED  8%
  E100 / OPPOSITE_BAND / TERMINAL negligible before first event.

Opposite band touched later: 50% overall; T1 60% -> T3 23% (median ~4.25h).

## Does R_LOCK work?

R_LOCK = FULL pre-noon gap (H_PRE12-P_12 or P_12-L_PRE12) divided by
cross-fitted expected afternoon max excursion (prior development dates only).
Violation probability falls monotonically with R_LOCK bucket:

R_LOCK_UP:  87%,55%,28%,13%,7% (buckets 0.2..3.9), spearman -0.59
R_LOCK_DN:  79%,62%,37%,28%,7%, spearman -0.54
bootstrap p05/p95 of spearman both < -0.39 (n=431/day-unit, seed 20260821)

YES: the ratio is monotonically informative out of sample.

## Does state improve walk-forward remaining-range forecasts?

Matched evaluation (same dates, chronological prior-only quantile medians):
  HIERARCHY (B5..B0 fallback) vs B0:
  03AM -0.24 MAE worse, 06AM -0.25 worse, 09AM -0.53 worse, 12PM -0.24 worse
  overall: HIER 17.55 vs B0 17.23 MAE  (hierarchy does NOT beat B0)
  % of dates where hierarchy beat B0: 39.9%
  bootstrap: delta distribution (-0.30 median; p95 -0.14, prob>0 = 0.0005)

Stated plainly: adding tier/state/loop/balance to the historical median does
NOT reduce remaining-range forecast error out of sample; the earlier in-sample
summary tables overstated the gain.

## Does transition conditioning beat naive baselines?

Next-loop direction walk-forward probability scoring (n=10,820 events):
  T0 unconditional  LL 0.6954, Brier 0.2503
  T1 +direction     0.6957  0.2504
  T2 +completion    0.6959  0.2505
  T3 +tier          0.6972  0.2511
  T4 +checkpoint    0.7019  0.2533  (fallback 22.3%)
  T5 +balance       0.7003  0.2526  (fallback 63.9%)
Richer Atomic state does NOT improve direction calibration; most complexity
is fallback-dominated. FAILURE_TYPE_HAS_LOW_DIRECTIONAL_INFORMATION.

## Decision

Authority: ASE-2 may graduate only if PATH MECHANISMS, PREDICTIVE VALUE,
REMAINING RANGE, TRANSITIONS, CAUSALITY, SAMPLE SUPPORT.

Repaired geometry is complete and honest (noon, post-25, variance denominator,
walk-forward scoring, transition scoring, R_LOCK, source claims).

Predictive evidence is negative:
  remaining-range hierarchy does not beat B0
  transition conditioning does not beat naive baselines
  noon lock and 25-lock claims falsified under repaired definitions
R_LOCK monotonicity IS real and repeats.

Decision: PARTIAL_TRANSITION_STRUCTURE

- SCALE: arrows
- NORMALIZATION: PASS (carried)
- STATE: PARTIAL (3AM state differentiates; transition-direction low)
- TIME: PARTIAL (remaining-range variance contracts with checkpoint)
- CAUSALITY: PASS

ASE-3 remains unauthorized. strategy_pnl_computed=false, optimization=false,
confirmation/holdout not consumed.

## Files

ASE_NOON_EXTREME_LEDGER_REPAIRED.parquet, ASE_NOON_EXTREME_HOLD_REPAIRED.csv,
ASE_NOON_HORIZON_MATRIX.csv, ASE_POST25_EVENT_LEDGER_REPAIRED.parquet,
ASE_POST25_REVERSAL_MATRIX_REPAIRED.csv, ASE_POST25_FIRST_EVENT_ORDERING_REPAIRED.csv,
ASE_POST25_TOUCH_VS_CLOSE.csv, ASE_LOCK_RATIO_ANALYSIS_REPAIRED.csv,
ASE_REMAINING_RANGE_SCORE_SUMMARY.csv, ASE_TRANSITION_PREDICTIVE_SCORE_REPAIRED.csv,
ASE_MECHANISM_SOURCE_COMPARISON_REPAIRED.csv, ASE2_2_BOOTSTRAP.csv,
ASE_NOON_RANGE_CONTRACT.md, ASE_POST25_EVENT_CONTRACT_AUDIT.md, ASE_VARIANCE_CLOCK_AUDIT.md,
ASE_VARIANCE_CLOCK_REPAIRED.csv