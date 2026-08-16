# BLOCK-I EDGE-DEGRADATION DOCTRINE (R4 authoritative)

Method A (documented): positive returns scaled by the edge state; losses preserved
exactly. Block bootstrap, 5000 paths.

## f = 1% landmark (exact artifact values)

| edge | expected CAGR | p95 max DD | P(DD>=20%) | P(DD>=40%) | P(DD>=50%) |
|---|---|---|---|---|---|

| 100% (EDGE-FULL) | +191% | 15% | 0% | 0% | 0% |
| 75% (EDGE-ROBUST) | +75% | 20% | 0% | 0% | 0% |
| 50% (EDGE-FRAGILE) | +5% | 43% | 16% | 1% | 0% |
| 25% (EDGE-BROKEN) | -37% | 83% | 83% | 61% | 47% |

## Viability classification (descriptive, not a safety claim)

- **EDGE-FULL / EDGE-ROBUST** (100/75%): viable at f=1-3%; tail risk manageable.
- **EDGE-FRAGILE** (50%): expected CAGR collapses to ~5% at f=1% and p95 DD
  balloons to 43% - the strategy becomes a low-return/high-tail-risk proposition.
- **EDGE-BROKEN** (25%): expected CAGR negative at every fraction; p95 DD 83%+ at
  f=1%. Not viable at any static fraction.

**The binding constraint of this strategy is edge retention, not static sizing.**
Never assume 100% historical edge in production planning.
