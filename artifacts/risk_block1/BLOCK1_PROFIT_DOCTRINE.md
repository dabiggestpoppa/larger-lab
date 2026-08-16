# BLOCK-I PROFIT DOCTRINE (R3 + repaired R3.1 authoritative)

## MFE

- winners median MFE **1.07R**, p90 2.15R,
  p99 4.26R; losers median 0.03R
- winners peak at median **hour 5** (p75 hour 6); losers peak at hour 2.

## Time to first profit (R3.1 repaired shares - all in [0,1])

- +0.25R: 96.6% of winners / 72.2% of all trades reach,
  median 2h
- +0.50R: 90.1% of winners reach, median 2h
- +1.00R: 54.9% of winners / 34.4% of all trades reach, median 3h; after reaching +1R
  **0% finish negative** (n=306) - descriptive, not an exit rule.

## Capture / giveback

- winners retain a median **92%** of peak MFE
  (p25 64% / p75 100%)
- median winner giveback 0.09R (8% of peak)

## Delivery curve (hour-by-hour)

| hour | avg open PnL (R) | % of final PnL | winners positive | past MFE | remaining gain (R) |
|---|---|---|---|---|---|
| 1 | -0.07 | -20% | 0% | 0% | +0.42 |
| 2 | +0.06 | 16% | 64% | 0% | +0.29 |
| 3 | +0.24 | 69% | 83% | 6% | +0.11 |
| 4 | +0.31 | 88% | 90% | 21% | +0.04 |
| 5 | +0.32 | 88% | 93% | 40% | +0.03 |
| 6 | +0.34 | 92% | 100% | 60% | +0.00 |

- **~70% of total final PnL is on the book by hour 3, ~88% by hour 4.**

## Maturity states

R3_PROFIT_MATURITY: LATE_DELIVERY (n=303, win 98%,
expectancy +1.42R) is the money-maker;
NOT_YET_DELIVERED (n=247, win 8%,
-0.95R) is the core loser;
PEAKED_AND_GIVING_BACK (n=141, +0.06R) parks capital.

## Winner tails

- best 1% = 5% of positive PnL;
  best 5% = 17%; best 10% = 28%
- excluding the best 5% leaves expectancy **+0.20R** (vs +0.35R full)

## Temporal

R3_TEMPORAL_PROFIT_STABILITY: median MFE / capture / winner-tail share stable
across inner_sel / inner_val / RELATIONSHIP_CONFIRMED_OOS.

## Doctrine

Hour-5 delivery, +1R behavior and maturity states are **descriptive evidence**.
Profit-lock / early-exit concepts are **HYPOTHESIS_ONLY**. No exit was created.
