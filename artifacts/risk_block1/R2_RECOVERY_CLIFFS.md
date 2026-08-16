# R2.4 — Recovery Cliff Detection (descriptive, HYPOTHESIS_ONLY)

Zones below are descriptive findings, NOT execution logic. A 'cliff' requires: adequate N (>= 30), a win-probability collapse below 0.35 that persists in the next-deeper bin, and/or negative remaining expectancy.

## Family A

| age bin | first MAE bin with win<0.35 (N>=30) | first bin with remaining exp < 0 |
|---|---|---|
| 0-1h | - | - |
| 1-2h | - | - |
| 2-3h | - | - |
| 3-4h | - | - |
| 4-5h | -1.00 to -1.50R | -1.00 to -1.50R |
| 5-6h | - | - |

## Family B

| age bin | first MAE bin with win<0.35 (N>=30) | first bin with remaining exp < 0 |
|---|---|---|
| 0-1h | - | - |
| 1-2h | - | - |
| 2-3h | - | - |
| 3-4h | - | -0.50 to -0.75R |
| 4-5h | - | -1.00 to -1.50R |
| 5-6h | - | - |

## Family A+B

| age bin | first MAE bin with win<0.35 (N>=30) | first bin with remaining exp < 0 |
|---|---|---|
| 0-1h | - | - |
| 1-2h | -0.75 to -1.00R | -0.75 to -1.00R |
| 2-3h | -1.00 to -1.50R | -0.75 to -1.00R |
| 3-4h | -1.00 to -1.50R | -0.75 to -1.00R |
| 4-5h | -1.00 to -1.50R | -0.75 to -1.00R |
| 5-6h | -1.00 to -1.50R | - |

## Reading

A win-cliff marks the state zone beyond which eventual profitable frozen exits become uncommon; a negative remaining-expectancy zone marks where capital is, on average, economically spent. Both are HYPOTHESIS_ONLY inputs for future statistical invalidation research - no stop is created.