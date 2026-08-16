# CR-RISK-BLOCK-II-STATIC-ARCHITECTURE-SEAL — Report

**Status:** PASS
**Base:** 8abb7c21e907254f75618deb3c9095c971c6b9be

## Integrity recheck
- total events: 890 (890 expected) — PASS
- family A: 432 (432 expected) — PASS
- family B: 458 (458 expected) — PASS
- episodes: 482 (482 expected) — PASS
- R1 12h episode reconciliation: 482 clusters — PASS
- max concurrency: 3 (3 expected) — PASS

## The five mission questions
**Q1. What family allocation conclusions are actually supported?**
Static family allocation is SUPPORTED. 50/50 is the diversification reference
(max DD 5.2% vs A-solo 10.3% / B-solo 11.1%), 70/30 is the A-heavy robust
reference (survives 50% edge retention; where the heat cap matters most), and
100/0 A is the edge-resilience / concentration reference. No allocation is
globally best.

**Q2. What simultaneous-heat controls are actually supported?**
H1 (simple gross heat cap) is the canonical mechanism. At 70/30 + 1.0x it
reduces block-MC p95 DD ~9.5% -> ~6.3% and P(DD>=10%) ~3.6% -> 0.0% at
~5.4pp median-CAGR cost. H2 (same-direction) replicates H1 without superiority.
H3 (B-family) is supported-not-required. H4 (episode budget) is redundant. H5
(combined) is unjustified complexity.

**Q3. Is episode-level budgeting necessary?**
No. H4 is REDUNDANT: H4-1.0x rejects 180 events vs H1-1.0x's 14, with lower
CAGR (53% vs 71%). Episode memory adds complexity without incremental value.

**Q4. Is B-specific treatment necessary?**
Not required. B is the capital limiter, but an equal gross cap is stronger at
70/30 (p95 DD 9.1% vs 6.3%), and H3-0.5x destroys A/B diversification at
50/50. Keep H3 secondary/optional, not default.

**Q5. Is there enough unresolved state-dependent risk to justify R7?**
No. ~84.7% of in-drawdown hourly loss is single-position; overlap adds
short-horizon tail risk that the simple gross cap already addresses. Dynamic
drawdown conditioning has no demonstrated mechanism. R7 remains deferred.

## Reference parity
```
H0 50/50 f=1%  CAGR 71.2131% / max DD 5.1886%
H0 50/50 f=2%  CAGR 190.3112% / max DD 10.1695%
H0 70/30 f=1%  CAGR 74.5699% / max DD 6.9684%
H0 100/0 f=1%  CAGR 79.1548% / max DD 10.3039%
H1 70/30 1.0x  block-MC p95 DD 9.4974% -> 6.2557%,
               P(DD>=10%) 3.6% -> 0.0%
```
Reference parity: PASS

## Causal admission
The minimal static module reproduced frozen R6 admission decisions exactly
(H1-1.00-REJ 70/30: 64 rejected events, matching the frozen 64). Admission is strictly causal.
Causal admission: PASS

## Architecture decision
The Block-II static architecture (family classification -> static family
allocation -> simple gross heat cap -> portfolio) is VALIDATED as the minimum
architecture justified by R1-R6. The ARCHITECTURE is selected; no production
allocation / cap / size is selected.

## Edge retention
Edge retention is the BINDING constraint. Risk controls shape losses; they do
not create expectancy. 75% retained edge is viable, 50% fragile, 25%
non-viable.

## Next step
Block-II static architecture is scientifically complete. Do NOT automatically
start R7. The next useful work depends on program objective: Block-III capital
scale design (only on explicit user intent) or deployment translation (only
when alpha engines + target are ready).
