# R5 — Family Dependency Report

## Correlation (realized PnL, causal alignment)
- same-hour realized correlation: **-0.038**
- same-day realized correlation: **-0.085**
- rolling 90-day daily correlation (mean): **-0.113**

Daily family PnL is near-zero correlated and slightly NEGATIVE - the two
families' realized outcomes are close to independent, which is what makes
pooling diversifying (no same-day co-loss tendency).

## Coincidence (losses / tails, daily)
- base P(B loss day) 23.5% ; P(A loss day) 20.8%
- **P(B loss | A loss) 12.0%** vs base 23.5%
  (no elevation - A loss days do NOT raise B loss odds)
- **P(B tail loss | A tail loss) 0.0%** -
  A deep days never coincide with B deep days (n=52)
- P(A tail loss | B tail loss) 0.0%

## Overlap conditioning
- A loss rate when B position open vs not: 42.5% vs 35.5%
- B loss rate when A position open vs not: 49.0% vs 37.3%

## Episodes (12h) + overlap hours
- A events inside 12h clusters that also contain B: **45.4%**;
  26% of all clusters contain both
- overlap hours: A_A 156 · B_B 211 ·
  A_B 228 (opposing 228,
  same-direction 367)

**Reading:** A and B are near-independent at daily granularity with no
co-loss/co-tail tendency; the diversification in the allocation frontier comes
from this independence, not from cancellation of the same instrument.
