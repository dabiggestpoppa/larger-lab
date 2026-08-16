# CR-RISK-BLOCK-II — R7 (DD-Adaptive) Necessity Assessment

**Task:** CR-RISK-BLOCK-II-INTERMEDIATE-SEAL · Classification: **R7_DEFERRED_SIMPLE_STATIC_STRUCTURE_SUFFICIENT**

## The five seal questions

**Q1 — What family-allocation conclusions are actually supported?**
Static family allocation is SUPPORTED as a diversification mechanism, not
as a selected winner. 50/50 (diversification reference, max DD ~5.2% vs
~10.3%/11.1% solo), 70/30 (robust A-heavy reference, survives 50% edge
retention), 100/0 A (edge-resilience reference). No best allocation.

**Q2 — What simultaneous-heat controls are actually supported?**
A simple gross heat cap (H1) is SUPPORTED: at 70/30 a 1.0x cap cuts
block-MC p95 max DD 9.5% -> 6.26% and
P(DD>=10%) 3.6% -> 0.0% at
~5.4pp median-CAGR cost. Same-direction (H2) matches gross
without increment; B-family (H3) supported-not-required; combined (H5)
optional only.

**Q3 — Is episode-level budgeting necessary?**
No. H4 is REDUNDANT with instantaneous gross caps (H4-1.0x strictly worse
than H1-1.0x; H4-1.5x equals H1-1.5x).

**Q4 — Is B-specific treatment necessary?**
No. B is the capital limiter (higher deep-loss frequency + longer streaks)
and an H3 cap is a supported mechanism, but it is weaker than an equal
gross cap at 70/30 and destroys A/B diversification at 50/50. A gross cap
already constrains B when B contributes the limiting heat.

**Q5 — Is there enough unresolved state-dependent risk to justify R7
drawdown-adaptive sizing?**
No. Reasons:
- Most drawdown comes from single-position ordinary losses (84.7% of
  in-drawdown hourly loss), not from overlap states a dynamic rule would
  condition on.
- Simple static caps already solve the overlap tail (70/30 p95 DD
  9.5% -> 6.26%, P(DD>=10%) ->
  0.0%).
- Edge retention dominates risk outcome; no conditioning rule recovers a
  halved edge.
- No causal evidence that recent losses forecast materially elevated
  conditional loss was produced in R1-R6.

## R7 label
**R7_DEFERRED_SIMPLE_STATIC_STRUCTURE_SUFFICIENT** — R7 (DD-adaptive) stays
defined and researchable, but the evidence does not justify starting it now.
r7_authorized = false. A Block-II static-architecture seal is recommended.
