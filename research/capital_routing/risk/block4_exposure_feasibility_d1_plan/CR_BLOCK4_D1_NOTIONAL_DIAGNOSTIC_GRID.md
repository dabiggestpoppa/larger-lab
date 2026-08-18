# CR-BLOCK4-D1 NOTIONAL DIAGNOSTIC GRID (PREREGISTERED)

## Rule

D1.1 must show ALL preregistered cells. No dropping poor cells, no adding
thresholds because performance looks good, no interpolating an optimal
threshold. The grid is a stress surface.

`diagnostic_grid_optimized_on_performance = false`.

## Thresholds (anchored mechanically to the observed pooled distribution)

Each limit L is a notional/equity cap for lane A: an event survives iff
`target_notional / equity <= L`. Thresholds were chosen to span the observed
distribution: below median (1.984), around median, upper body
(p75 = 3.513), tail (p95 = 7.610), deep tail
(p99 = 16.036), near observed max (32.766), and beyond
observed max (unbounded headroom reference).

| L (notional/equity) | pooled n surviving | pooled % | A % | B % |
|---|---|---|---|---|
| 0.5 | 39 | 4.72% | 0.54% | 8.13% |
| 1 | 178 | 21.55% | 4.58% | 35.38% |
| 2 | 417 | 50.48% | 20.75% | 74.73% |
| 4 | 655 | 79.30% | 61.19% | 94.07% |
| 8 | 786 | 95.16% | 89.76% | 99.56% |
| 16 | 817 | 98.91% | 97.84% | 99.78% |
| 32 | 825 | 99.88% | 99.73% | 100.00% |
| 64 | 826 | 100.00% | 100.00% | 100.00% |

## Quantile bins (frozen, pooled accepted)

Feasibility is reported within these bins; bins are frozen before results:

| bin |
|---|
| 0-25% |
| 25-50% |
| 50-75% |
| 75-95% |
| 95-99% |
| 99-100% |

## Notional vs discretization feasibility

- NOTIONAL feasibility (lane A) is account-size invariant: `target_notional / equity`.
- DISCRETIZATION feasibility (lane B) depends on lot minimum, lot step, absolute
  quantity limits and absolute margin, and is therefore account-size dependent.
