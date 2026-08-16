# P7.4 — STRUCTURAL INVALIDATION REPORT (measurement only)

P(eventual convergence | current |z|, age) and E(remaining PnL) from frozen E0 trades (TB-B). Min support N >= 15; low-N cells (esp. |z| >= 4.5) are never declared. NO stop is adopted in this phase.

## Distance x age surface (P(conv) %, Wilson CI)

### Entry z = 2.5
| |z| bin | age 0-30 | 30-60 | 60-120 | 120-180 | 180-240 | 240-360 | 360+ |
|---|---|---|---|---|---|---|---|
| [0.0,2.5) | 68% (N=1151.0) | 69% (N=1704.0) | 67% (N=3445.0) | 63% (N=3075.0) | 62% (N=2319.0) | 53% (N=1781.0) | 36% (N=439.0) |
| [2.5,3.0) | 66% (N=557.0) | 57% (N=365.0) | 45% (N=492.0) | 36% (N=190.0) | 19% (N=67.0) | 20% (N=25.0) | — |
| [3.0,3.5) | 58% (N=203.0) | 52% (N=195.0) | 48% (N=180.0) | 53% (N=59.0) | — | — | — |
| [3.5,4.0) | 55% (N=60.0) | 51% (N=57.0) | 56% (N=43.0) | 33% (N=15.0) | — | — | — |
| [4.0,4.5) | 33% (N=18.0) | 50% (N=20.0) | — | — | — | — | — |
| [4.5,5.0) | — | — | — | — | — | — | — |
| [5.0,5.5) | — | — | — | — | — | — | — |
| [5.5,6.0) | — | — | — | — | — | — | — |
| [6.0,inf) | — | — | — | — | — | — | — |

### Entry z = 3
| |z| bin | age 0-30 | 30-60 | 60-120 | 120-180 | 180-240 | 240-360 | 360+ |
|---|---|---|---|---|---|---|---|
| [0.0,2.5) | 78% (N=260.0) | 71% (N=642.0) | 65% (N=1578.0) | 65% (N=1485.0) | 64% (N=1155.0) | 44% (N=777.0) | 18% (N=191.0) |
| [2.5,3.0) | 67% (N=309.0) | 54% (N=245.0) | 42% (N=266.0) | 43% (N=95.0) | 11% (N=36.0) | 24% (N=17.0) | — |
| [3.0,3.5) | 54% (N=247.0) | 47% (N=145.0) | 48% (N=98.0) | 55% (N=31.0) | — | — | — |
| [3.5,4.0) | 55% (N=87.0) | 57% (N=37.0) | 57% (N=21.0) | — | — | — | — |
| [4.0,4.5) | 43% (N=28.0) | — | — | — | — | — | — |
| [4.5,5.0) | — | — | — | — | — | — | — |
| [5.0,5.5) | — | — | — | — | — | — | — |
| [5.5,6.0) | — | — | — | — | — | — | — |
| [6.0,inf) | — | — | — | — | — | — | — |

## Failure modes

### Entry z = 2.5
- **A (distance-only):** marginal P(conv) by |z| bin:
  - |z| 0.0: P(conv) 63% (N=13914)
  - |z| 2.5: P(conv) 52% (N=1696)
  - |z| 3.0: P(conv) 53% (N=637)
  - |z| 3.5: P(conv) 52% (N=175)
  - |z| 4.0: P(conv) 42% (N=38)
- **B (age-only):** marginal P(conv) by age bin:
  - age 0: P(conv) 66% (N=1989)
  - age 30: P(conv) 65% (N=2341)
  - age 60: P(conv) 63% (N=4160)
  - age 120: P(conv) 61% (N=3339)
  - age 180: P(conv) 61% (N=2386)
  - age 240: P(conv) 52% (N=1806)
  - age 360: P(conv) 36% (N=439)
- **C (distance x age):** same |z| at different ages (recovery differs?):
  - |z| 0.0: 68% @0.0m, 69% @30.0m, 67% @60.0m, 63% @120.0m, 62% @180.0m, 53% @240.0m, 36% @360.0m
  - |z| 2.5: 66% @0.0m, 57% @30.0m, 45% @60.0m, 36% @120.0m, 19% @180.0m, 20% @240.0m
  - |z| 3.0: 58% @0.0m, 52% @30.0m, 48% @60.0m, 53% @120.0m
  - |z| 3.5: 55% @0.0m, 51% @30.0m, 56% @60.0m, 33% @120.0m
  - |z| 4.0: 33% @0.0m, 50% @30.0m

### Entry z = 3
- **A (distance-only):** marginal P(conv) by |z| bin:
  - |z| 0.0: P(conv) 62% (N=6088)
  - |z| 2.5: P(conv) 52% (N=968)
  - |z| 3.0: P(conv) 51% (N=521)
  - |z| 3.5: P(conv) 56% (N=145)
  - |z| 4.0: P(conv) 43% (N=28)
- **B (age-only):** marginal P(conv) by age bin:
  - age 0: P(conv) 65% (N=931)
  - age 30: P(conv) 63% (N=1069)
  - age 60: P(conv) 61% (N=1963)
  - age 120: P(conv) 63% (N=1611)
  - age 180: P(conv) 62% (N=1191)
  - age 240: P(conv) 44% (N=794)
  - age 360: P(conv) 18% (N=191)
- **C (distance x age):** same |z| at different ages (recovery differs?):
  - |z| 0.0: 78% @0.0m, 71% @30.0m, 65% @60.0m, 65% @120.0m, 64% @180.0m, 44% @240.0m, 18% @360.0m
  - |z| 2.5: 67% @0.0m, 54% @30.0m, 42% @60.0m, 43% @120.0m, 11% @180.0m, 24% @240.0m
  - |z| 3.0: 54% @0.0m, 47% @30.0m, 48% @60.0m, 55% @120.0m
  - |z| 3.5: 55% @0.0m, 57% @30.0m, 57% @60.0m

- **D (velocity/persistence):** P(conv) by 15-min |z| change at the state (rising +0.1, falling -0.1, flat otherwise):

- Entry z=2.5:
  - |z| 0.0, falling: P(conv) 65% (N=7597)
  - |z| 0.0, flat: P(conv) 58% (N=2521)
  - |z| 0.0, rising: P(conv) 59% (N=3158)
  - |z| 2.5, falling: P(conv) 48% (N=486)
  - |z| 2.5, flat: P(conv) 48% (N=248)
  - |z| 2.5, rising: P(conv) 48% (N=580)
  - |z| 3.0, falling: P(conv) 39% (N=137)
  - |z| 3.0, flat: P(conv) 49% (N=81)
  - |z| 3.0, rising: P(conv) 54% (N=303)
  - |z| 3.5, falling: P(conv) 67% (N=27)
  - |z| 3.5, flat: P(conv) 53% (N=15)
  - |z| 3.5, rising: P(conv) 45% (N=98)
  - |z| 4.0, rising: P(conv) 48% (N=27)

- Entry z=3:
  - |z| 0.0, falling: P(conv) 64% (N=3578)
  - |z| 0.0, flat: P(conv) 56% (N=1140)
  - |z| 0.0, rising: P(conv) 58% (N=1255)
  - |z| 2.5, falling: P(conv) 46% (N=385)
  - |z| 2.5, flat: P(conv) 43% (N=141)
  - |z| 2.5, rising: P(conv) 50% (N=241)
  - |z| 3.0, falling: P(conv) 42% (N=122)
  - |z| 3.0, flat: P(conv) 49% (N=61)
  - |z| 3.0, rising: P(conv) 51% (N=176)
  - |z| 3.5, falling: P(conv) 69% (N=26)
  - |z| 3.5, flat: P(conv) 53% (N=15)
  - |z| 3.5, rising: P(conv) 47% (N=59)
  - |z| 4.0, rising: P(conv) 44% (N=16)

## Recovery cliffs (CI disjoint from both neighbors)

- entry 2.5: |z| [0.0,2.5) age [60.0-120.0) P(conv) 67% CI [65,68] N=3445.0
- entry 2.5: |z| [0.0,2.5) age [180.0-240.0) P(conv) 62% CI [60,64] N=2319.0
- entry 2.5: |z| [0.0,2.5) age [240.0-360.0) P(conv) 53% CI [51,55] N=1781.0
- entry 3: |z| [0.0,2.5) age [180.0-240.0) P(conv) 64% CI [61,67] N=1155.0
- entry 3: |z| [2.5,3.0) age [0.0-30.0) P(conv) 67% CI [62,72] N=309.0
- entry 3: |z| [0.0,2.5) age [30.0-60.0) P(conv) 71% CI [68,75] N=642.0

See P7_INVALIDATION_SURFACE.csv for the full surface (N>=15 cells only).

