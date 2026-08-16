# R3 — Profit Anatomy (CR-RISK-BLOCK1)

**Task:** CR-RISK-BLOCK1-R3-PROFIT-ANATOMY · **Base:** 7bc1c024 (sealed) · R2 8c0a59d7

- **Q1** median MFE: winners 1.07R (p90 2.15R) vs losers 0.03R (p90 0.59R).

- **Q2** +0.25R: 97% of winners reach (of all trades 72%), median 2h (p25 1 / p75 2); +0.5R: 90% of winners reach (of all trades 62%), median 2h (p25 1 / p75 3); +1.0R: 55% of winners reach (of all trades 34%), median 3h (p25 2 / p75 4).

- **Q3** time to MFE (all): median hour 4 (p75 5); winners median hour 5 (p75 6). Peak distribution: h1 15%; h2 11%; h3 18%; h4 17%; h5 15%; h6 24%.

- **Q4** winners retain a median 92% of peak MFE (p25 64% / p75 100%); 65% keep >=75%.

- **Q5** median giveback: winners 0.09R (8% of peak) vs losers 0.84R.

- **Q6** of trades reaching +1R: 0% finish negative, 6% finish below half peak, 100% still positive. At +0.5R: 10% finish negative.

- **Q7** remaining expectancy at each age (all states, N-weighted): h1: +0.29R (n=890); h2: +0.11R (n=882); h3: +0.04R (n=873); h4: +0.03R (n=860); h5: +0.00R (n=842).

- **Q8** by hour 3, 69% of total final PnL is already on the book; by hour 5, 88% (hour 6 is the frozen exit).

| hour | avg open PnL (R) | % final PnL | % winners positive | % winners past MFE | remaining gain (R) |
|---|---|---|---|---|---|
| 1 | -0.07 | -20% | 0% | 0% | +0.42 |
| 2 | +0.06 | 16% | 64% | 0% | +0.29 |
| 3 | +0.24 | 69% | 83% | 6% | +0.11 |
| 4 | +0.31 | 88% | 90% | 21% | +0.04 |
| 5 | +0.32 | 88% | 93% | 40% | +0.03 |
| 6 | +0.34 | 92% | 100% | 60% | +0.00 |

- **Q9** A vs B: median MFE 0.73R vs 0.70R; time to first +0.5R median 2h vs 2h; time to MFE 4h vs 4h; median capture 91% vs 94%; late-hold share of winner PnL -13% vs 42%.

- **Q10** concurrency: no-overlap median MFE 0.74R, expectancy +0.41R vs same-direction overlap MFE 0.72R, expectancy +0.28R.

- **Q11** 12h-cluster ranks: time to MFE rank1 4h vs 4+ 4h; median capture 90% vs 4+ 88%.

- **Q12** best 1% of trades produce 5% of total positive PnL; best 5% produce 17%; best 10% produce 28%. Excluding best 5%: expectancy +0.20R.

- **Q13** profit anatomy through time (R3_TEMPORAL_PROFIT_STABILITY.csv):
  - inner_sel: N=461 · median MFE 0.74R · median capture 90% · giveback 0.28R · winner-tail5 share 17%
  - inner_val: N=149 · median MFE 0.65R · median capture 96% · giveback 0.34R · winner-tail5 share 18%
  - RELATIONSHIP_CONFIRMED_OOS: N=280 · median MFE 0.69R · median capture 96% · giveback 0.32R · winner-tail5 share 18%

## Q14 — Hypotheses deserving future testing (HYPOTHESIS_ONLY)

- `HYPOTHESIS_ONLY` by hour 5, 88% of final PnL is already earned while remaining expected gain is +0.03R — possible profit-lock / time-decay concept (late-hold capital efficiency).
- `HYPOTHESIS_ONLY` trades that reach +1R still finish negative 0% of the time — possible partial/breakeven-lock concept after strong delivery.
- `HYPOTHESIS_ONLY` winners give back a median 8% of peak MFE — possible trailing/exit-smoothing concept (needs R4 risk context).

## Stop

R3 checkpoint complete. R4 (Static Risk Frontier) does NOT start until human review. No TP, early exit, trailing, breakeven, partial, family weighting, or alpha modification.