# P7.3 — PROFIT CAPTURE REPORT

Per-trade giveback (best path PnL - final net PnL) and capture ratio on the frozen E0 exit. Measurement + hypotheses only — no trailing exits implemented.

## Giveback by entry x model (TB-B headline)

| entry | model | median gb | p75 | p90 | p95 | winners >25% | >50% | >75% | losers prev-profitable | med capture (winners) |
|---|---|---|---|---|---|---|---|---|---|---|
| 2.5 | TB-B | 0.0 | 0.1 | 5.5 | 8.3 | 14% | 7% | 3% | 60% | 1.00 |
| 3 | TB-B | 0.0 | 0.1 | 4.6 | 7.2 | 11% | 5% | 2% | 57% | 1.00 |

## Structural facts (both entries, TB-B)

- Entry z=2.5: median giveback 0.0 pips; 348 winners (median capture 1.00); 34 / 57 losers were profitable first (60%).
- Entry z=3: median giveback 0.0 pips; 171 winners (median capture 1.00); 13 / 23 losers were profitable first (57%).

## Hypotheses generated (NOT implemented)

1. **Partial realization:** if winners give back > 25% of MFE materially often, a fraction-of-target exit may lock more of the edge with less time.
2. **Profit lock:** if a material share of losers were previously profitable, a breakeven-style invalidation after profit could cut the losing tail.
3. **Time-conditioned realization:** giveback concentrates in slow trades, a time-conditioned take may improve pips/capital-hour.

Only P7.5 may test these (and only after P7.1-P7.4 freeze).

