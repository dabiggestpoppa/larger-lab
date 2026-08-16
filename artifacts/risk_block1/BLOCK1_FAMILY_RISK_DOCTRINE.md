# BLOCK-I FAMILY RISK DOCTRINE (R4 authoritative)

## Static equal-f result (R4_FAMILY_RISK_FRONTIER)

| f | A max DD | B max DD | pooled max DD | capital-limiting |
|---|---|---|---|---|
| 0.50% | 5.3% | 5.7% | 5.2% | B |
| 1.00% | 10.3% | 11.1% | 10.2% | B |
| 2.00% | 19.8% | 21.1% | 19.7% | B |
| 5.00% | 43.4% | 45.7% | 44.6% | B |

**B currently appears capital-limiting under static equal-f risk** (higher solo
max DD at every tested f) - consistent with R2's worse typical downside for B.

- A-only CAGR vs B-only CAGR at f=1%: 79% vs 62% (both positive; pooled 190%
  from compounding of combined exposure).
- R2 family downside: B worse median MAE and P(<-1R); A holds the single worst
  trade (-3.66R vs -3.31R).

This is a **descriptive static result**. Family-specific allocation is NOT
authorized - it is Block-II research (R5).
