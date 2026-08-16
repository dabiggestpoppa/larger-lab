# R2 — Loss Anatomy (CR-RISK-BLOCK1)

**Task:** CR-RISK-BLOCK1-R2-LOSS-ANATOMY · **Base:** 7bc1c024 (sealed) · R1 32374cc0

## Answers

- **Q1** (family A): median MAE — winners -0.10R vs losers -0.87R; loser p25 -1.35R / p75 -0.56R.
  **Q2** (family A): 90% of winners stay above -0.46R; 95% above -0.55R.
- **Q1** (family B): median MAE — winners -0.07R vs losers -0.89R; loser p25 -1.35R / p75 -0.57R.
  **Q2** (family B): 90% of winners stay above -0.46R; 95% above -0.59R.
- **Q1** (family A+B): median MAE — winners -0.09R vs losers -0.88R; loser p25 -1.35R / p75 -0.56R.
  **Q2** (family A+B): 90% of winners stay above -0.46R; 95% above -0.57R.

- **Q3** recovery to profit after breach (all trades that reached the level): after -0.5R: 15% recover (final expectancy -0.79R); after -1.0R: 0% recover (final expectancy -1.52R); after -1.5R: 0% recover (final expectancy -2.04R); after -2.0R: 0% recover (final expectancy -2.46R)

- **Q4** recovery probability by trade age at MAE in [-0.75,-1.00)R: 1-2h 3%; 2-3h 2%; 3-4h 5%; 4-5h 5%; 5-6h 5%.

- **Q5** empirical recovery cliffs: see R2_RECOVERY_CLIFFS.md (descriptive, HYPOTHESIS_ONLY).

- **Q6** losing routes reveal themselves quickly: median time to -0.5R: 2.0h (p25 1.0 / p75 3.0) · median time to -1.0R: 3.0h (p25 2.0 / p75 4.0) · median time to -2.0R: 4.0h (p25 3.0 / p75 5.0).

- **Q7** fast failures (first to breach -0.5R): median final loss -0.86R vs slow -0.32R; recovery-to-profit after -0.5R breach: fast 11% vs slow 0%.

- **Q8** worst 1% of trades carry 10% of total losses (worst 10%: 60%).

- **Q9** trades entered with 0 existing positions: expectancy +0.38R, P(<-1R) 11%; entered with 2+ concurrent: expectancy +0.25R, P(<-1R) 6%.

- **Q10** 12h-cluster rank: P(<-1R) rank1 11% vs rank2 14% vs 4+ 17%; p95 loss -1.71R / 4+ -2.20R.

- **Q11** Family A vs B downside: median MAE -0.22R vs -0.26R; P(<-1R) 10% vs 14%; recovery from -1R 0% vs 0%; worst loss -3.7R vs -3.3R.

- **Q12** downside stability through time (R2_TEMPORAL_STABILITY.csv):
  - inner_sel: N=461 · median MAE -0.22R · p95 loss -1.78R · P(<-1R) 14% · tail5 share 38%
  - inner_val: N=149 · median MAE -0.20R · p95 loss -1.95R · P(<-1R) 9% · tail5 share 42%
  - RELATIONSHIP_CONFIRMED_OOS: N=280 · median MAE -0.28R · p95 loss -1.50R · P(<-1R) 11% · tail5 share 34%

## Q13 — Hypotheses deserving future stop/invalidation testing

Each hypothesis is labelled HYPOTHESIS_ONLY — descriptive input for a future phase, NOT execution logic. No stop is implemented.

- `HYPOTHESIS_ONLY` MAE reaching -1.00 to -1.50R or deeper is associated with 0% eventual recovery (pooled, N>=30, earliest at age 2-3h) — possible MAE invalidation zone (needs exact threshold research).
- `HYPOTHESIS_ONLY` losers typically breach -1R by 3h (p75 4h) — possible time+MAE invalidation (trades still adverse at that age rarely recover).
- `HYPOTHESIS_ONLY` worst 1% of trades carry 10% of total losses with 100% fast failures — possible failure-speed invalidation.

## Stop

R2 checkpoint complete. R3 (Profit Anatomy) does NOT start until human review. No stops, no early exits, no filters, no allocation change, no alpha modification.