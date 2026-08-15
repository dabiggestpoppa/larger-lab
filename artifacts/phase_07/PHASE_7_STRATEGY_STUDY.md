# Phase 7 — Routing Translation Study (Baseline Strategies)

**Task:** CR-P7-ROUTING-TRANSLATION-01
**Base:** Phase 6 commit 5726bf02 (ACCEPTED)

> Translates the holdout-validated Phase 6 routing relationships into executable pair-space expressions and evaluates simple event-driven baselines. No CEREBUS filters, no deployment, no MT5 execution.

## 1. Frozen Relationship Families

| Family | Relationship | Validated horizons | Trade expression |
|--------|--------------|--------------------|------------------|
| A | EUR ACCUMULATION -> JPY relative weakness | 6, 8, 12h | long |
| B | EUR LIQUIDATION -> JPY relative strength | 4, 6, 8, 12h | short |
| C | JPY LIQUIDATION -> CHF relative strength | 48h | long_chf |

## 2. Alpha Promotion Gate

- **EUR_ACCUMULATION_JPY_WEAKNESS**: **PROMOTED**
  - 1_same_holdout_sign: PASS — all validated horizons same sign on holdout
  - 2_holdout_effect_50pct: PASS — 
  - 3_bootstrap_ci_excludes_zero: PASS — {'6': {'n': 147, 'effect': -0.3020290174090399, 'ci_low': -0.42616136502177726, 'ci_high': -0.16962371837797469}, '8': {'n': 147, 'effect': -0.3006502600736175, 'ci_low': -0.4154886051042858, 'ci_high': -0.16040652208541817}, '12': {'n': 147, 'effect': -0.2777291985505499, 'ci_low': -0.399331387586079, 'ci_high': -0.14089140833558053}}
  - 4_adequate_holdout_n: PASS — 
  - 5_overlap_cooldown_stability: PASS — 
  - 6_no_single_horizon_dependence: PASS — 3 validated horizons; execution plateau found
- **EUR_LIQUIDATION_JPY_STRENGTH**: **PROMOTED**
  - 1_same_holdout_sign: PASS — all validated horizons same sign on holdout
  - 2_holdout_effect_50pct: PASS — 
  - 3_bootstrap_ci_excludes_zero: PASS — {'4': {'n': 136, 'effect': 0.2805553143660999, 'ci_low': 0.1562420991946071, 'ci_high': 0.4004886324143808}, '6': {'n': 136, 'effect': 0.2908175664479989, 'ci_low': 0.1606292235885767, 'ci_high': 0.41586733704805784}, '8': {'n': 136, 'effect': 0.2565936303608915, 'ci_low': 0.1503234215978513, 'ci_high': 0.3715811814017535}, '12': {'n': 136, 'effect': 0.18244817896108967, 'ci_low': 0.05371071634145111, 'ci_high': 0.30448152688175717}}
  - 4_adequate_holdout_n: PASS — 
  - 5_overlap_cooldown_stability: PASS — 
  - 6_no_single_horizon_dependence: PASS — 4 validated horizons; execution plateau found
- **JPY_LIQUIDATION_CHF_STRENGTH**: **PROMOTED**
  - 1_same_holdout_sign: PASS — all validated horizons same sign on holdout
  - 2_holdout_effect_50pct: PASS — 
  - 3_bootstrap_ci_excludes_zero: PASS — {'48': {'n': 121, 'effect': 0.15951574290468667, 'ci_low': 0.01899200845431827, 'ci_high': 0.32370672606226975}}
  - 4_adequate_holdout_n: PASS — 
  - 5_overlap_cooldown_stability: PASS — 
  - 6_no_single_horizon_dependence: PASS — 36/48/60h same sign on inner_sel

## 3. Pair-Space Comparison (inner_sel, delay 0)

### Family A

| Pair | Hold | n | Mean bps | Win | MFE | MAE | Cost | RoutingEff |
|------|------|---|----------|-----|-----|-----|------|------------|
| USDJPY | 4h | 213 | +8.810 | 0.592 | 16.51 | -10.01 | 1.35 | 9.348 |
| GBPJPY | 4h | 213 | +10.117 | 0.700 | 18.95 | -10.03 | 2.15 | 6.720 |
| CHFJPY | 4h | 213 | +4.772 | 0.638 | 14.53 | -10.87 | 1.82 | 5.948 |
| EURJPY | 4h | 213 | -1.217 | 0.531 | 8.62 | -8.64 | 1.67 | 4.258 |
| USDJPY | 6h | 213 | +11.453 | 0.667 | 23.76 | -12.13 | 1.42 | 11.161 |
| GBPJPY | 6h | 213 | +14.444 | 0.728 | 27.83 | -12.26 | 2.22 | 8.774 |
| CHFJPY | 6h | 213 | +8.612 | 0.648 | 21.54 | -12.93 | 1.83 | 7.724 |
| EURJPY | 6h | 213 | -2.293 | 0.498 | 11.79 | -13.03 | 1.70 | 4.648 |
| USDJPY | 8h | 213 | +12.093 | 0.643 | 27.26 | -14.46 | 1.50 | 11.661 |
| GBPJPY | 8h | 213 | +15.253 | 0.709 | 31.66 | -14.09 | 2.30 | 9.428 |
| CHFJPY | 8h | 213 | +8.646 | 0.638 | 24.72 | -14.64 | 1.85 | 8.504 |
| EURJPY | 8h | 213 | -1.829 | 0.521 | 14.78 | -16.65 | 1.74 | 4.746 |
| USDJPY | 12h | 213 | +12.251 | 0.620 | 34.08 | -20.44 | 1.65 | 11.339 |
| GBPJPY | 12h | 213 | +15.684 | 0.676 | 37.46 | -18.72 | 2.45 | 10.133 |
| CHFJPY | 12h | 213 | +8.045 | 0.629 | 29.00 | -18.49 | 1.87 | 8.829 |
| EURJPY | 12h | 213 | -1.017 | 0.526 | 18.72 | -20.15 | 1.81 | 5.270 |

### Family B

| Pair | Hold | n | Mean bps | Win | MFE | MAE | Cost | RoutingEff |
|------|------|---|----------|-----|-----|-----|------|------------|
| USDJPY | 4h | 251 | +11.628 | 0.625 | 19.23 | -9.68 | 1.05 | 5.733 |
| EURJPY | 4h | 251 | -1.612 | 0.454 | 10.33 | -9.82 | 1.53 | 5.306 |
| CHFJPY | 4h | 251 | +6.665 | 0.594 | 15.89 | -9.39 | 1.78 | 3.503 |
| GBPJPY | 4h | 251 | +13.912 | 0.721 | 20.55 | -8.16 | 1.85 | 2.549 |
| USDJPY | 6h | 251 | +14.107 | 0.629 | 28.18 | -12.86 | 0.98 | 6.215 |
| EURJPY | 6h | 251 | -1.099 | 0.486 | 14.49 | -13.34 | 1.50 | 6.161 |
| CHFJPY | 6h | 251 | +10.517 | 0.633 | 23.82 | -11.92 | 1.77 | 3.952 |
| GBPJPY | 6h | 251 | +18.662 | 0.705 | 31.44 | -10.45 | 1.78 | 2.675 |
| USDJPY | 8h | 251 | +13.860 | 0.594 | 32.88 | -15.71 | 0.90 | 7.485 |
| EURJPY | 8h | 251 | -1.720 | 0.498 | 17.51 | -16.38 | 1.46 | 7.041 |
| CHFJPY | 8h | 251 | +9.841 | 0.610 | 27.07 | -14.31 | 1.75 | 4.317 |
| GBPJPY | 8h | 251 | +18.133 | 0.653 | 36.00 | -12.54 | 1.70 | 2.882 |
| USDJPY | 12h | 251 | +14.012 | 0.574 | 38.72 | -19.71 | 0.75 | 9.404 |
| EURJPY | 12h | 251 | -3.645 | 0.482 | 21.11 | -21.68 | 1.39 | 8.278 |
| CHFJPY | 12h | 251 | +8.684 | 0.610 | 31.97 | -17.87 | 1.73 | 4.747 |
| GBPJPY | 12h | 251 | +18.155 | 0.625 | 42.47 | -16.44 | 1.55 | 3.355 |

### Family C

| Pair | Hold | n | Mean bps | Win | MFE | MAE | Cost | RoutingEff |
|------|------|---|----------|-----|-----|-----|------|------------|
| CHFJPY | 24h | 210 | +7.379 | 0.543 | 35.32 | -23.23 | 1.94 | 8.406 |
| USDCHF | 24h | 210 | +1.254 | 0.500 | 27.06 | -23.22 | 0.85 | 7.941 |
| EURCHF | 24h | 210 | -1.474 | 0.467 | 19.06 | -19.55 | 1.53 | 6.885 |
| GBPCHF | 24h | 210 | -0.427 | 0.467 | 26.23 | -23.39 | 1.25 | 6.263 |
| USDCHF | 36h | 211 | -0.026 | 0.512 | 31.53 | -28.15 | 0.47 | 12.648 |
| GBPCHF | 36h | 211 | -2.602 | 0.483 | 30.97 | -29.05 | 0.87 | 9.153 |
| CHFJPY | 36h | 211 | +7.405 | 0.555 | 41.72 | -27.75 | 2.01 | 8.575 |
| EURCHF | 36h | 211 | -0.970 | 0.483 | 23.29 | -23.15 | 1.39 | 7.473 |
| USDCHF | 48h | 211 | +0.311 | 0.507 | 34.82 | -31.66 | 0.09 | 55.108 |
| GBPCHF | 48h | 211 | -0.682 | 0.502 | 36.34 | -33.03 | 0.49 | 16.030 |
| EURCHF | 48h | 211 | -1.402 | 0.488 | 26.33 | -26.63 | 1.25 | 9.294 |
| CHFJPY | 48h | 211 | +6.034 | 0.540 | 46.42 | -32.53 | 2.07 | 8.671 |
| GBPCHF | 60h | 215 | +0.003 | 0.479 | 39.24 | -35.20 | 0.12 | 60.050 |
| EURCHF | 60h | 215 | -1.193 | 0.451 | 28.51 | -28.74 | 1.12 | 10.907 |
| CHFJPY | 60h | 215 | +4.589 | 0.540 | 51.23 | -36.09 | 2.14 | 8.830 |
| USDCHF | 60h | 215 | +1.198 | 0.521 | 38.38 | -34.91 | -0.28 | nan |
| EURCHF | 72h | 215 | -2.330 | 0.474 | 31.87 | -31.62 | 0.98 | 12.641 |
| CHFJPY | 72h | 215 | +4.669 | 0.521 | 57.66 | -41.41 | 2.21 | 8.563 |
| GBPCHF | 72h | 215 | -0.510 | 0.456 | 42.49 | -38.59 | -0.26 | nan |
| USDCHF | 72h | 215 | +1.439 | 0.502 | 42.15 | -38.54 | -0.66 | nan |

## 4. Entry Delay Plateaus (inner_sel)

### Family A: recommended delay=2h, hold=6h
  - delay 0h: holds [4, 6, 8, 12] (rep 12h, +8.741 bps)
  - delay 1h: holds [4, 6, 8, 12] (rep 6h, +8.519 bps)
  - delay 2h: holds [4, 6, 8, 12] (rep 6h, +9.152 bps)
  - delay 3h: holds [4, 6, 8, 12] (rep 12h, +1.396 bps)
### Family B: recommended delay=1h, hold=6h
  - delay 0h: holds [4, 6, 8, 12] (rep 6h, +10.547 bps)
  - delay 1h: holds [4, 6, 8, 12] (rep 6h, +10.838 bps)
  - delay 2h: holds [4, 6, 8, 12] (rep 4h, +10.429 bps)
  - delay 3h: holds [4, 6, 8] (rep 4h, +1.591 bps)
### Family C: recommended delay=0h, hold=48h
  - delay 0h: holds [24, 36, 48, 60, 72] (rep 24h, +1.683 bps)
  - delay 1h: holds [24, 36, 48, 60] (rep 36h, +0.771 bps)
  - delay 2h: holds [24, 36, 48, 60, 72] (rep 36h, +1.533 bps)
  - delay 3h: holds [24, 36, 48, 60] (rep 36h, +0.823 bps)

## 5. Excursion Geometry (structural risk envelopes, no optimization)

### Family A

| Pair | Hold | n | MAE p50 | MAE p90 | MFE p50 | MFE p90 | med tMFE | med tMAE |
|------|------|---|---------|---------|---------|---------|----------|----------|
| CHFJPY | 4h | 213 | -4.72 | 0.00 | 9.02 | 36.46 | 4.0h | 2.0h |
| EURJPY | 4h | 213 | -4.56 | 0.00 | 4.02 | 24.66 | 3.0h | 3.0h |
| GBPJPY | 4h | 213 | -3.45 | 0.00 | 12.11 | 49.43 | 4.0h | 2.0h |
| USDJPY | 4h | 213 | -5.08 | 0.00 | 8.00 | 46.30 | 3.0h | 2.0h |
| CHFJPY | 6h | 213 | -5.32 | 0.00 | 16.13 | 50.96 | 5.0h | 3.0h |
| EURJPY | 6h | 213 | -6.80 | 0.00 | 6.06 | 34.33 | 3.0h | 3.0h |
| GBPJPY | 6h | 213 | -4.89 | 0.00 | 18.49 | 62.13 | 5.0h | 2.0h |
| USDJPY | 6h | 213 | -6.41 | 0.00 | 13.61 | 60.04 | 5.0h | 3.0h |
| CHFJPY | 8h | 213 | -6.85 | 0.00 | 18.27 | 58.62 | 5.0h | 3.0h |
| EURJPY | 8h | 213 | -9.55 | 0.00 | 9.55 | 39.51 | 4.0h | 4.0h |
| GBPJPY | 8h | 213 | -5.08 | 0.00 | 21.96 | 72.00 | 5.0h | 2.0h |
| USDJPY | 8h | 213 | -8.17 | 0.00 | 14.76 | 64.65 | 5.0h | 3.0h |
| CHFJPY | 12h | 213 | -8.30 | 0.00 | 20.80 | 69.26 | 6.0h | 3.0h |
| EURJPY | 12h | 213 | -11.69 | 0.00 | 11.15 | 45.05 | 6.0h | 5.0h |
| GBPJPY | 12h | 213 | -6.40 | 0.00 | 28.53 | 89.18 | 7.0h | 3.0h |
| USDJPY | 12h | 213 | -8.91 | 0.00 | 21.69 | 88.58 | 7.0h | 3.0h |

### Family B

| Pair | Hold | n | MAE p50 | MAE p90 | MFE p50 | MFE p90 | med tMFE | med tMAE |
|------|------|---|---------|---------|---------|---------|----------|----------|
| CHFJPY | 4h | 251 | -5.34 | 0.00 | 8.30 | 39.38 | 2.0h | 3.0h |
| EURJPY | 4h | 251 | -5.40 | 0.00 | 4.23 | 28.05 | 3.0h | 2.0h |
| GBPJPY | 4h | 251 | -4.01 | 0.00 | 11.84 | 52.35 | 2.0h | 4.0h |
| USDJPY | 4h | 251 | -4.21 | 0.00 | 8.47 | 48.25 | 2.0h | 4.0h |
| CHFJPY | 6h | 251 | -7.70 | 0.00 | 15.74 | 56.58 | 3.0h | 4.0h |
| EURJPY | 6h | 251 | -7.33 | 0.00 | 7.00 | 39.77 | 3.0h | 3.0h |
| GBPJPY | 6h | 251 | -6.12 | 0.00 | 20.57 | 73.56 | 2.0h | 5.0h |
| USDJPY | 6h | 251 | -6.74 | 0.00 | 16.02 | 68.50 | 3.0h | 4.0h |
| CHFJPY | 8h | 251 | -8.01 | 0.00 | 17.60 | 59.47 | 3.0h | 5.0h |
| EURJPY | 8h | 251 | -9.55 | 0.00 | 10.10 | 45.09 | 4.0h | 4.0h |
| GBPJPY | 8h | 251 | -7.84 | 0.00 | 23.28 | 85.70 | 3.0h | 5.0h |
| USDJPY | 8h | 251 | -7.91 | 0.00 | 20.00 | 74.36 | 3.0h | 5.0h |
| CHFJPY | 12h | 251 | -10.47 | 0.00 | 21.20 | 66.93 | 4.0h | 6.0h |
| EURJPY | 12h | 251 | -12.70 | 0.00 | 12.51 | 50.86 | 6.0h | 5.0h |
| GBPJPY | 12h | 251 | -9.16 | 0.00 | 26.30 | 95.90 | 3.0h | 7.0h |
| USDJPY | 12h | 251 | -11.06 | 0.00 | 24.71 | 87.67 | 4.0h | 5.0h |

### Family C

| Pair | Hold | n | MAE p50 | MAE p90 | MFE p50 | MFE p90 | med tMFE | med tMAE |
|------|------|---|---------|---------|---------|---------|----------|----------|
| CHFJPY | 24h | 210 | -14.72 | 0.00 | 25.08 | 84.35 | 11.0h | 6.5h |
| EURCHF | 24h | 210 | -11.58 | 0.00 | 12.31 | 45.94 | 9.0h | 9.0h |
| GBPCHF | 24h | 210 | -17.03 | 0.00 | 16.73 | 70.53 | 9.0h | 8.0h |
| USDCHF | 24h | 210 | -16.54 | 0.00 | 17.78 | 65.46 | 8.0h | 9.0h |
| CHFJPY | 36h | 211 | -18.15 | 0.00 | 29.05 | 93.74 | 14.0h | 7.0h |
| EURCHF | 36h | 211 | -14.61 | 0.00 | 14.12 | 52.27 | 13.0h | 12.0h |
| GBPCHF | 36h | 211 | -20.58 | 0.00 | 20.63 | 75.54 | 13.0h | 10.0h |
| USDCHF | 36h | 211 | -19.87 | 0.00 | 22.06 | 72.91 | 12.0h | 11.0h |
| CHFJPY | 48h | 211 | -21.94 | 0.00 | 35.20 | 100.16 | 17.0h | 10.0h |
| EURCHF | 48h | 211 | -15.74 | 0.00 | 16.67 | 62.09 | 14.0h | 15.0h |
| GBPCHF | 48h | 211 | -23.85 | 0.00 | 23.49 | 91.31 | 14.0h | 12.0h |
| USDCHF | 48h | 211 | -22.30 | 0.00 | 25.03 | 74.10 | 15.0h | 12.0h |
| CHFJPY | 60h | 215 | -23.65 | 0.00 | 37.14 | 116.34 | 18.0h | 11.0h |
| EURCHF | 60h | 215 | -17.94 | -0.00 | 17.59 | 71.13 | 14.0h | 15.0h |
| GBPCHF | 60h | 215 | -25.03 | -0.00 | 25.10 | 101.47 | 16.0h | 12.0h |
| USDCHF | 60h | 215 | -23.24 | -0.00 | 29.33 | 82.84 | 15.0h | 13.0h |
| CHFJPY | 72h | 215 | -29.12 | -0.32 | 43.07 | 124.43 | 20.0h | 16.0h |
| EURCHF | 72h | 215 | -23.50 | -0.25 | 22.96 | 75.04 | 17.0h | 18.0h |
| GBPCHF | 72h | 215 | -26.83 | -0.00 | 27.67 | 108.85 | 19.0h | 15.0h |
| USDCHF | 72h | 215 | -25.07 | -0.00 | 32.31 | 95.87 | 19.0h | 17.0h |

## 6. Mirrored EUR Routing Symmetry (A long vs B short, inner_sel)

| Pair | Hold | A mean | A win | B mean | B win | asymmetry |
|------|------|--------|-------|--------|-------|------------|
| CHFJPY | 4h | +4.772 | 0.610 | +6.665 | 0.582 | 0.7160 |
| EURJPY | 4h | -1.217 | 0.474 | -1.612 | 0.410 | 0.7548 |
| GBPJPY | 4h | +10.117 | 0.648 | +13.912 | 0.665 | 0.7272 |
| USDJPY | 4h | +8.810 | 0.554 | +11.628 | 0.606 | 0.7576 |
| CHFJPY | 6h | +8.612 | 0.615 | +10.517 | 0.594 | 0.8188 |
| EURJPY | 6h | -2.293 | 0.446 | -1.099 | 0.454 | 2.0867 |
| GBPJPY | 6h | +14.444 | 0.704 | +18.662 | 0.673 | 0.7740 |
| USDJPY | 6h | +11.453 | 0.638 | +14.107 | 0.610 | 0.8118 |
| CHFJPY | 8h | +8.646 | 0.610 | +9.841 | 0.586 | 0.8785 |
| EURJPY | 8h | -1.829 | 0.493 | -1.720 | 0.466 | 1.0632 |
| GBPJPY | 8h | +15.253 | 0.671 | +18.133 | 0.629 | 0.8412 |
| USDJPY | 8h | +12.093 | 0.638 | +13.860 | 0.582 | 0.8725 |
| CHFJPY | 12h | +8.045 | 0.596 | +8.684 | 0.594 | 0.9263 |
| EURJPY | 12h | -1.017 | 0.507 | -3.645 | 0.454 | 0.2789 |
| GBPJPY | 12h | +15.684 | 0.653 | +18.155 | 0.610 | 0.8639 |
| USDJPY | 12h | +12.251 | 0.606 | +14.012 | 0.562 | 0.8743 |

## 7. Baseline Results

### P7_EUR_JPY_BASELINE

| Split | Trades | Win | Expect/bps | PF | Sharpe | Sortino | MaxDD | Calmar | CostDrag |
|-------|--------|-----|------------|----|--------|---------|-------|--------|----------|
| inner_sel | 211 | 0.668 | +10.062 | 2.4267 | 4.0426 | 4.0891 | 0.9688 | 1,482.8167 | 0.0907 |
| inner_val | 77 | 0.623 | +7.521 | 1.8994 | 2.9829 | 3.1838 | 0.8748 | 1,372.8389 | 0.0650 |
| untouched | 144 | 0.604 | +10.135 | 2.3891 | 3.9554 | 5.2647 | 0.1899 | 8,677.9374 | 0.0930 |
| inner_sel | 250 | 0.628 | +7.419 | 1.8646 | 3.0759 | 3.3274 | 1.1372 | 1,105.2383 | 0.0512 |
| inner_val | 72 | 0.639 | +10.533 | 2.5704 | 4.2001 | 4.9620 | 0.3134 | 5,027.6628 | 0.0435 |
| untouched | 136 | 0.574 | +6.175 | 1.8098 | 2.8856 | 3.2119 | 1.1498 | 822.4805 | 0.0690 |

### P7_JPY_CHF_BASELINE

| Split | Trades | Win | Expect/bps | PF | Sharpe | Sortino | MaxDD | Calmar | CostDrag |
|-------|--------|-----|------------|----|--------|---------|-------|--------|----------|
| inner_sel | 211 | 0.507 | +0.755 | 1.0373 | 0.1648 | 0.1698 | 1.7520 | 61.4169 | 0.0029 |
| inner_val | 68 | 0.647 | +34.559 | 3.9276 | 6.0819 | 9.7862 | 0.2553 | 19,516.9504 | 0.0016 |
| untouched | 121 | 0.455 | +1.173 | 1.0512 | 0.2205 | 0.2530 | 3.4425 | 46.9095 | 0.0027 |

## 8. Decision

- **Gate: PASS**
- Family EUR_ACCUMULATION_JPY_WEAKNESS: PROMOTED
- Family EUR_LIQUIDATION_JPY_STRENGTH: PROMOTED
- Family JPY_LIQUIDATION_CHF_STRENGTH: PROMOTED
- validation_policy: Phase 6 holdout (2025-07..2026-05) used ONCE after rules frozen on nested inner_sel/inner_val within dev.
- no_parameter_rescue: True
- no_cerebus: True
- no_deploy: True

---
STOP after baseline strategy evaluation. No CEREBUS filters, no deploy, no MT5 execution.