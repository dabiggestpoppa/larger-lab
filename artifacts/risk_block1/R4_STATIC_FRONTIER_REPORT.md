# R4 — Static Risk Frontier (CR-RISK-BLOCK1)

**Task:** CR-RISK-BLOCK1-R4-STATIC-FRONTIER · **Base:** 7bc1c024 (sealed) · R3.1 31fa1df1
**Book:** 890 sealed events (A 432 / B 458) · 1R = 24.5 bps (NOT a hard stop; A worst -3.66R, B worst -3.31R)

## Q1 — What does "risk 1%" actually mean?

f maps **directly** into equity: a -3R trade at f=1% costs ~-3%. 1R is the strategy's normalized expected-move unit (24.49 bps), not a stop. See `R4_RISK_UNIT_DEFINITION.md`; the ladder compounds multiplicatively (`E*(1+f*r_R)`), so drawdowns compound nonlinearly as f rises.

## Q2 — What happens historically at every static fraction?

| f% | CAGR | total x | max DD | Calmar | Sortino | worst day | worst 24h | worst 48h | ulcer |
|---|---|---|---|---|---|---|---|---|---|
| 0.05 | +5.6% | 1.17x | 0.5% | 10.52 | 3.03 | -0.3% | -0.3% | -0.3% | 0.1% |
| 0.10 | +11.4% | 1.36x | 1.1% | 10.82 | 3.11 | -0.6% | -0.6% | -0.7% | 0.3% |
| 0.15 | +17.6% | 1.59x | 1.6% | 11.14 | 3.19 | -0.8% | -0.8% | -1.0% | 0.4% |
| 0.20 | +24.1% | 1.86x | 2.1% | 11.47 | 3.28 | -1.1% | -1.1% | -1.4% | 0.5% |
| 0.25 | +31.0% | 2.17x | 2.6% | 11.81 | 3.37 | -1.4% | -1.4% | -1.7% | 0.7% |
| 0.30 | +38.2% | 2.53x | 3.1% | 12.17 | 3.47 | -1.7% | -1.7% | -2.1% | 0.8% |
| 0.40 | +53.9% | 3.44x | 4.2% | 12.92 | 3.66 | -2.2% | -2.2% | -2.8% | 1.1% |
| 0.50 | +71.2% | 4.67x | 5.2% | 13.72 | 3.87 | -2.8% | -2.8% | -3.4% | 1.3% |
| 0.60 | +90.4% | 6.33x | 6.2% | 14.59 | 4.10 | -3.4% | -3.4% | -4.1% | 1.6% |
| 0.75 | +123.2% | 9.98x | 7.7% | 16.02 | 4.47 | -4.2% | -4.2% | -5.2% | 2.0% |
| 1.00 | +190.3% | 21.18x | 10.2% | 18.71 | 5.17 | -5.6% | -5.6% | -6.8% | 2.6% |
| 1.25 | +276.7% | 44.66x | 12.6% | 21.92 | 6.02 | -6.9% | -6.9% | -8.5% | 3.3% |
| 1.50 | +387.5% | 93.50x | 15.0% | 25.78 | 7.02 | -8.3% | -8.3% | -10.2% | 3.9% |
| 2.00 | +710.9% | 401.58x | 19.7% | 36.02 | 9.66 | -10.9% | -10.9% | -13.5% | 5.2% |
| 2.50 | +1235.8% | 1677.95x | 24.3% | 50.89 | 13.44 | -13.5% | -13.5% | -16.7% | 6.5% |
| 3.00 | +2079.6% | 6821.81x | 28.7% | 72.54 | 18.84 | -16.1% | -16.1% | -19.9% | 7.8% |
| 4.00 | +5539.6% | 103899.93x | 36.9% | 149.94 | 37.65 | -21.0% | -21.0% | -26.2% | 10.3% |
| 5.00 | +13949.8% | 1419683.42x | 44.6% | 313.03 | 75.85 | -25.8% | -25.8% | -32.3% | 12.7% |

## Q3 — Where does max DD begin accelerating nonlinearly?

- Historical max DD is **near-linear in f across the whole ladder** (DD per 1% f: 7.6% .. 10.5% — the per-bps slope slightly *declines* because winners compound harder at high f).
- Historical max DD by f: 0.05% → 0.5% · 0.5% → 5.2% · 1% → 10.2% · 2% → 19.7% · 5% → 44.6%.
- The **nonlinearity lives in the tail**, not the historical path: block-bootstrap p95 max DD grows faster than f (at f=1% p95 15.1% vs historical 10.2%; at f=5% p95 59.4% vs historical 44.6%).

## Q4 — Which risk fractions survive block-bootstrap tails?

- f = 0.50%: block-bootstrap p95 max DD 7.8%, p99 9.4%, median CAGR +71.1% (p5 +53.5% / p95 +91.0%), P(technical ruin) 0.00%.
- f = 1.00%: block-bootstrap p95 max DD 15.1%, p99 18.0%, median CAGR +189.0% (p5 +132.7% / p95 +260.1%), P(technical ruin) 0.00%.
- f = 2.00%: block-bootstrap p95 max DD 28.5%, p99 33.7%, median CAGR +693.6% (p5 +415.1% / p95 +1132.5%), P(technical ruin) 0.00%.
- f = 3.00%: block-bootstrap p95 max DD 40.2%, p99 46.9%, median CAGR +1973.2% (p5 +987.1% / p95 +3913.3%), P(technical ruin) 0.00%.
- f = 5.00%: block-bootstrap p95 max DD 59.4%, p99 67.0%, median CAGR +12174.4% (p5 +4075.5% / p95 +36778.6%), P(technical ruin) 0.00%.

## Q5 — P(10/20/30/40/50% DD) at each f

| f% | P(10%) | P(20%) | P(30%) | P(40%) | P(50%) | P(tech ruin) |
|---|---|---|---|---|---|---|
| 0.25 | 0% | 0% | 0% | 0% | 0% | 0.00% |
| 0.50 | 0% | 0% | 0% | 0% | 0% | 0.00% |
| 0.75 | 0% | 0% | 0% | 0% | 0% | 0.00% |
| 1.00 | 1% | 0% | 0% | 0% | 0% | 0.00% |
| 1.50 | 4% | 0% | 0% | 0% | 0% | 0.00% |
| 2.00 | 8% | 1% | 0% | 0% | 0% | 0.00% |
| 3.00 | 16% | 4% | 1% | 0% | 0% | 0.00% |
| 5.00 | 31% | 12% | 5% | 1% | 0% | 0.00% |

## Q6 — How does the frontier change if edge falls to 75/50/25%?

- Edge 100% @ f=1%: expected CAGR +190.9%, p95 max DD 15.0%, P(DD≥20%) 0%, P(DD≥50%) 0%.
- Edge 75% @ f=1%: expected CAGR +75.1%, p95 max DD 20.3%, P(DD≥20%) 0%, P(DD≥50%) 0%.
- Edge 50% @ f=1%: expected CAGR +5.1%, p95 max DD 42.6%, P(DD≥20%) 16%, P(DD≥50%) 0%.
- Edge 25% @ f=1%: expected CAGR -37.1%, p95 max DD 83.1%, P(DD≥20%) 83%, P(DD≥50%) 47%.

## Q7 — How sensitive is survival to amplified left tails?

- historical: max DD 10.0% (baseline 10.0%), terminal 20.80x.
- worst5_x1_25: max DD 10.4% (baseline 10.0%), terminal 18.43x.
- worst5_x1_50: max DD 12.3% (baseline 10.0%), terminal 16.31x.
- worst5_x2_00: max DD 16.0% (baseline 10.0%), terminal 12.74x.
- insert_worst_1: max DD 10.0% (baseline 10.0%), terminal 20.04x.
- insert_worst_2_consec: max DD 10.9% (baseline 10.0%), terminal 19.38x.
- insert_p99_loss_cluster: max DD 17.6% (baseline 10.0%), terminal 17.92x.

## Q8 — What happens during 10-15 loss streaks?

- 10-streak @ loser 50% (-0.64R), f=0.5%: equity 0.97x, DD 3.2%.
- 10-streak @ loser 50% (-0.64R), f=1.0%: equity 0.94x, DD 6.3%.
- 10-streak @ loser 50% (-0.64R), f=2.0%: equity 0.88x, DD 12.2%.
- 13-streak @ loser 50% (-0.64R), f=0.5%: equity 0.96x, DD 4.1%.
- 13-streak @ loser 50% (-0.64R), f=1.0%: equity 0.92x, DD 8.1%.
- 13-streak @ loser 50% (-0.64R), f=2.0%: equity 0.84x, DD 15.5%.
- 10-streak @ loser 90% (-0.10R), f=0.5%: equity 1.00x, DD 0.5%.
- 10-streak @ loser 90% (-0.10R), f=1.0%: equity 0.99x, DD 1.0%.
- 10-streak @ loser 90% (-0.10R), f=2.0%: equity 0.98x, DD 1.9%.
- 13-streak @ loser 90% (-0.10R), f=0.5%: equity 0.99x, DD 0.6%.
- 13-streak @ loser 90% (-0.10R), f=1.0%: equity 0.99x, DD 1.3%.
- 13-streak @ loser 90% (-0.10R), f=2.0%: equity 0.97x, DD 2.5%.

## Q9 — What account heat occurs during actual overlap?

- 0_position: 81% of in-market hours, gross R median 0.00R / max 0.00R, net R max 0.00R.
- 1_position: 17% of in-market hours, gross R median 0.76R / max 1.00R, net R max 1.00R.
- 2_opposing: 1% of in-market hours, gross R median 1.49R / max 1.91R, net R max 0.59R.
- 2_same_dir: 1% of in-market hours, gross R median 1.41R / max 1.82R, net R max 1.82R.
- 3_positions: 0% of in-market hours, gross R median 2.22R / max 2.39R, net R max 2.39R.
- At f=1%: worst portfolio CAE 3.06R → 3.1% account impact; 3-position effective risk 3.0%.

## Q10 — Is A or B the capital-limiting family?

- f=0.50%: A max DD 5.3% vs B 5.7% → limiting: B.
- f=1.00%: A max DD 10.3% vs B 11.1% → limiting: B.
- f=2.00%: A max DD 19.8% vs B 21.1% → limiting: B.

## Q11 — Preservation / balanced / growth / full-press envelopes

- **RM-S0_PRESERVATION**: f = 1.50% → exp CAGR +392.1%, p95 max DD 22%, P(DD≥20%) 0%, P(DD≥40%) 0%, P(tech) 0.00%.
- **RM-S1_CONSERVATIVE**: f = 3.00% → exp CAGR +2152.0%, p95 max DD 40%, P(DD≥20%) 4%, P(DD≥40%) 0%, P(tech) 0.00%.
- **RM-S2_BALANCED**: f = 5.00% → exp CAGR +15247.6%, p95 max DD 59%, P(DD≥20%) 12%, P(DD≥40%) 1%, P(tech) 0.00%.
- **RM-S3_GROWTH**: f = 5.00% → exp CAGR +15247.6%, p95 max DD 59%, P(DD≥20%) 12%, P(DD≥40%) 1%, P(tech) 0.00%.
- **RM-S4_FULL_PRESS**: f = 5.00% → exp CAGR +15247.6%, p95 max DD 59%, P(DD≥20%) 12%, P(DD≥40%) 1%, P(tech) 0.00%.

Envelope table (max f per constraint, block bootstrap):

| envelope | edge | max f% | P(DD≥40%) | P(DD≥50%) | P(tech) |
|---|---|---|---|---|---|
| SURVIVAL | 100% | 5.00 | 1% | 0% | 0.00% |
| AGGRESSIVE | 100% | 5.00 | 1% | 0% | 0.00% |
| VERY_AGGRESSIVE | 100% | 5.00 | 1% | 0% | 0.00% |
| PROP | 100% | 1.50 | 0% | 0% | 0.00% |
| SURVIVAL | 75% | 5.00 | 7% | 3% | 0.00% |
| AGGRESSIVE | 75% | 5.00 | 7% | 3% | 0.00% |
| VERY_AGGRESSIVE | 75% | 5.00 | 7% | 3% | 0.00% |
| PROP | 75% | 1.00 | 0% | 0% | 0.00% |
| SURVIVAL | 50% | 1.50 | 6% | 2% | 0.00% |
| AGGRESSIVE | 50% | 1.50 | 6% | 2% | 0.00% |
| VERY_AGGRESSIVE | 50% | 3.00 | 29% | 19% | 0.00% |
| PROP | 50% | 0.30 | 0% | 0% | 0.00% |

## Q12 — What does each envelope mean in dollars ($5k-$100k)?

| zone | f% | acct | 1R $ | -3R $ | A-worst $ | exp gain $ | 2-pos risk $ |
|---|---|---|---|---|---|---|---|
| RM-S2_BALANCED | 5.00 | $5,000 | $250 | $750 | $914 | $87.32 | $500 |
| RM-S2_BALANCED | 5.00 | $100,000 | $5,000 | $15,000 | $18,277 | $1,746.43 | $10,000 |
| RM-S3_GROWTH | 5.00 | $5,000 | $250 | $750 | $914 | $87.32 | $500 |
| RM-S3_GROWTH | 5.00 | $100,000 | $5,000 | $15,000 | $18,277 | $1,746.43 | $10,000 |
| RM-S4_FULL_PRESS | 5.00 | $5,000 | $250 | $750 | $914 | $87.32 | $500 |
| RM-S4_FULL_PRESS | 5.00 | $100,000 | $5,000 | $15,000 | $18,277 | $1,746.43 | $10,000 |

## Stop

R4 checkpoint complete. **No 'best size' is selected** — the zones are research profiles. Block II (compounding families, allocation, episode sizing, heat management, DD-adaptive, Kelly, hybrid) does NOT start until human review. Alpha, entries, exits, and trade management untouched.