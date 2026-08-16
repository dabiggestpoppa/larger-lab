# P6.2 — FURTHER-EXTENSION ANATOMY REPORT (measurement only)

For every baseline (z=2.5) signal: post-entry |z| path, max further extension, time-to-max, levels reached, outcome, per-model PnL, MFE/MAE.
No entry/exit rule is derived here — this is the measurement layer for a future (human-approved) optimization phase.

## Class summary (path classes)

| class | N | share | WR | EV TB-B | EV TB-C-5% | MFE med | MAE med | conv med |
|---|---|---|---|---|---|---|---|---|
| DEEP_CONVERGED | 23 | 6% | 100.0% | 20.01 | 18.33 | 12.9 | -28.1 | 250 |
| DEEP_FAILED | 21 | 5% | 0.0% | -6.01 | -8.33 | 5.6 | -31.3 | nan |
| IMMEDIATE_CONVERGENCE | 135 | 33% | 100.0% | 26.20 | 25.50 | 23.0 | -10.2 | 155 |
| IMMEDIATE_PERSISTED | 48 | 12% | 0.0% | 9.03 | 7.81 | 15.5 | -12.3 | nan |
| SHALLOW_CONVERGED | 109 | 27% | 100.0% | 26.03 | 24.74 | 22.8 | -18.7 | 215 |
| SHALLOW_FAILED | 69 | 17% | 0.0% | 1.33 | -0.23 | 6.1 | -22.6 | nan |

## P(convergence) and E[PnL] by max |z| reached

| max|z| bin | N | P(conv) | P(SL) | P(timeout) | EV TB-A | EV TB-B | EV TB-C5% |
|---|---|---|---|---|---|---|---|
| [2.50, 2.75) | 79 | 66% | 0% | 34% | 11.6 | 17.9 | 16.9 |
| [2.75, 3.00) | 68 | 60% | 0% | 40% | 10.5 | 18.0 | 17.0 |
| [3.00, 3.25) | 51 | 67% | 0% | 33% | 7.6 | 19.2 | 17.6 |
| [3.25, 3.50) | 46 | 70% | 0% | 30% | 8.7 | 18.0 | 16.7 |
| [3.50, 4.00) | 48 | 52% | 0% | 48% | -3.1 | 9.6 | 8.0 |
| [4.00, 4.50) | 20 | 55% | 0% | 45% | -7.2 | 9.4 | 7.3 |
| [4.50, 5.00) | 1 | 0% | 0% | 100% | -15.3 | -16.9 | -17.5 |
| [5.00, 5.50) | 3 | 33% | 0% | 67% | -2.8 | 10.9 | 8.9 |
| [5.50, 6.00) | 1 | 100% | 0% | 0% | -57.2 | 108.5 | 96.0 |
| [6.00, inf) | 2 | 0% | 100% | 0% | -35.7 | -30.9 | -32.7 |

## Hypotheses (quantitative, none assumed true)

- **A (extension → higher expectancy):** rank correlation of EV(TB-B) vs max-|z| bin = 0.02; first-bin EV 17.9, last-bin EV -30.9 → NOT supported.
- **B (inverted-U / structural failure zone):** peak bin EV 108.5 vs final-bin EV -30.9 → inverted-U pattern present.
- **C (extreme extension = regime break):** max|z| >= 4.5: N=7, P(conv)=29% (vs 67% below 4.5), EV(TB-B) 8.9 vs 18.0 → regime-break evidence.
- **D (differs by vol regime / session):** see class x vol / class x session table below (full data in P6_FURTHER_EXTENSION_PATHS.csv).

## Class x volatility regime / session third (EV TB-B | P(conv))

| | early | mid | late | LOW vol | MED vol | HIGH vol |
|---|---|---|---|---|---|---|
| IMMEDIATE_CONVERGENCE | 26.1 | 100% | 23.2 | 100% | 65.5 | 100% | 20.3 | 100% | 26.9 | 100% | 40.2 | 100% |
| SHALLOW_CONVERGED | 30.1 | 100% | 19.5 | 100% | 16.6 | 100% | 22.4 | 100% | 26.4 | 100% | 31.2 | 100% |
| DEEP_CONVERGED | 22.8 | 100% | 17.9 | 100% | 2.9 | 100% | 12.3 | 100% | 16.8 | 100% | 48.8 | 100% |
| SHALLOW_FAILED | 2.2 | 0% | 2.5 | 0% | -2.1 | 0% | -0.6 | 0% | 3.3 | 0% | 2.5 | 0% |
| DEEP_FAILED | -9.2 | 0% | 8.6 | 0% | -17.5 | 0% | -2.9 | 0% | -26.6 | 0% | -12.4 | 0% |

## Hazard surface (P(convergence | current |z|, time since signal))

Full 2D surface in P6_EXTENSION_CONVERGENCE_SURFACE.csv (surface = z_t_hazard). Headline cells:
| |z| bucket | t bucket | N obs | P(conv) | EV TB-B (cond) |
|---|---|---|---|---|---|
| [2.5,3.0) | [0,15) | 205 | 67% | 18.2 |
| [2.5,3.0) | [15,30) | 160 | 66% | 19.2 |
| [2.5,3.0) | [30,60) | 160 | 59% | 15.4 |
| [2.5,3.0) | [60,120) | 145 | 46% | 12.4 |
| [2.5,3.0) | [120,240) | 60 | 38% | 9.4 |
| [2.5,3.0) | [240,inf) | 8 | 12% | 6.3 |
| [3.0,3.5) | [0,15) | 72 | 62% | 16.5 |
| [3.0,3.5) | [15,30) | 80 | 57% | 15.5 |
| [3.0,3.5) | [30,60) | 85 | 56% | 14.2 |
| [3.0,3.5) | [60,120) | 68 | 51% | 10.6 |
| [3.0,3.5) | [120,240) | 22 | 45% | 6.1 |
| [3.0,3.5) | [240,inf) | 3 | 0% | 3.3 |
| [3.5,4.0) | [0,15) | 21 | 67% | 19.6 |
| [3.5,4.0) | [15,30) | 29 | 41% | 8.3 |
| [3.5,4.0) | [30,60) | 27 | 59% | 12.8 |
| [3.5,4.0) | [60,120) | 23 | 57% | 9.0 |
| [3.5,4.0) | [120,240) | 6 | 33% | -10.3 |
| [3.5,4.0) | [240,inf) | 1 | 0% | 6.3 |
| [4.0,5.0) | [0,15) | 6 | 50% | 5.6 |
| [4.0,5.0) | [15,30) | 9 | 33% | 21.1 |
| [4.0,5.0) | [30,60) | 12 | 50% | 15.8 |
| [4.0,5.0) | [60,120) | 7 | 71% | 27.5 |
| [4.0,5.0) | [120,240) | 1 | 0% | -32.7 |
| [5.0,6.0) | [0,15) | 2 | 0% | 7.1 |
| [5.0,6.0) | [15,30) | 2 | 100% | 63.6 |
| [5.0,6.0) | [30,60) | 1 | 100% | 108.5 |
| [5.0,6.0) | [60,120) | 1 | 100% | 108.5 |
| [6.0,inf) | [0,15) | 2 | 0% | -30.9 |
