# BLOCK-I LOSS DOCTRINE (R2 authoritative)

All figures measured on the sealed 890-event A/B book (A 432 / B 458).

## Winner vs loser adverse excursion (R units)

- winner median MAE **-0.09R**; p90 -0.03R
- **95% of winners stay above -0.57R**; worst winner MAE -1.69R
- loser median MAE **-0.88R**

## Breach behavior (final-outcome-recovery, R2_FAILURE_SPEED)

| threshold | losers breaching | median time | recovery to profit | final expectancy after |
|---|---|---|---|---|
| -0.5R | 262.0 | 2h | 15.5% | -0.79R |
| -1.0R | 134.0 | 3h | 0.0% | -1.52R |
| -2.0R | 33.0 | 4h | 0.0% | -2.46R |

**HISTORICAL RECOVERY OBSERVATION: zero trades recovered to a profitable frozen
exit after breaching -1R.** This is an observation, NOT a stop rule.

## Failure speed

- FAST (reveal <= 2h, n=158): median loss -0.86R,
  recovery after -0.5R breach 11%
- MEDIUM (n=72), SLOW (n=103): median loss
  -0.32R, recovery 0%
- Losers breach -0.5R by median 2h, -1R by 3h (p75 4h).

## Tail concentration

- worst **1%** of trades (n=9, 1.0%) carry a
  mean **-3.02R** loss = 9.7%
  of total losses and 45% of the worst-24h loss
- worst **10%** (n=89) carry **60%**
  of total losses, 92% of the max-DD window,
  81% of the worst-24h loss.

## Family downside

- B: median MAE -0.26R, P(<-1R) 14%,
  worst -3.31R
- A: median MAE -0.22R, P(<-1R) 10%,
  worst -3.66R

## Streaks

- max 10 consecutive losing trades (block-bootstrap p95 11, max 13);
  max 6 consecutive negative days; worst 24h window
  -153 bps (-6.3R).

## Temporal stability

R2_TEMPORAL_STABILITY: median MAE and P(<-1R) stable across inner_sel / inner_val /
RELATIONSHIP_CONFIRMED_OOS (documented in the CSV; the OOS segment is NOT untouched
w.r.t. relationship discovery).

## Doctrine

- Descriptive cliffs (recovery collapse, failure speed) are **HYPOTHESIS_ONLY**
  inputs for future invalidation testing. No stop was created.
