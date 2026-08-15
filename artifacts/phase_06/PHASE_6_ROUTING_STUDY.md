# Phase 6 — Forward Routing Study (Lead-Lag)

**Task:** CR-P6-FORWARD-ROUTING-STUDY-01
**Phase 5 accepted commit:** f0fc54ab (sealed)

> This is the first empirical outcome phase. It measures what happens AFTER each frozen Phase 5 event. It does NOT build strategies, set thresholds, or claim profitability. Phase 7 strategy construction is allowed ONLY for holdout-validated relationships.

## 1. Frozen Event Universe

- Total episodes: **8076**
- BROAD_CURRENCY_EVENT: 4357
- RESIDUAL_SHOCK: 2872
- NETWORK_DISLOCATION: 847
- Origin counts: EUR 900, GBP 858, USD 842, CHF 874, JPY 883
- Severity buckets: {'LOW': 5853, 'MEDIUM': 2120, 'EXTREME': 103} (HIGH is structurally absent in the Phase 5 buckets; unchanged.)

## 2. Frozen Inputs and Split

- `p5_event_freeze.json`: SHA-256 of all six Phase 5 inputs (see file).
- Development: 2023-07-01 00:00:00+00:00 .. 2025-06-30 23:59:59+00:00 (5613 events)
- Holdout: 2025-07-01 00:00:00+00:00 .. 2026-05-31 23:59:59+00:00 (2463 events)
- Fixed horizons (h): [1, 2, 4, 6, 8, 12, 24, 48] (optional: [72, 120]).

## 3. Dominant Destination by Origin and Direction

| Origin | Direction | +1h | +4h | +12h | +24h | +48h |
|--------|-----------|-----|-----|------|------|------|
| CHF | ACCUMULATION | USD | USD | USD | USD | USD |
| CHF | LIQUIDATION | USD | GBP | USD | USD | USD |
| EUR | ACCUMULATION | USD | GBP | USD | USD | USD |
| EUR | LIQUIDATION | USD | JPY | JPY | JPY | JPY |
| GBP | ACCUMULATION | USD | USD | USD | USD | USD |
| GBP | LIQUIDATION | GBP | GBP | USD | USD | USD |
| JPY | ACCUMULATION | JPY | JPY | USD | USD | USD |
| JPY | LIQUIDATION | USD | USD | USD | USD | GBP |
| USD | ACCUMULATION | USD | USD | USD | USD | USD |
| USD | LIQUIDATION | USD | USD | USD | USD | USD |

## 4. GBP Bridge Test

- Bridge-candidate events: 4357
- Initial GBP lead rate (+1h): 0.2147
- GBP lead rate +4h: 0.2237 | +24h: 0.1886
- GBP lead decay (1h→24h): 0.02615
- Classification: **SUPPORTED**

## 5. CHF Parking Test

- Parking-candidate events: 4357
- CHF lead rate +1h: 0.1754 | +4h: 0.1781 | +24h: 0.1912
- Median time to leadership loss: 1h
- Classification: **PARTIALLY_SUPPORTED**

## 6. JPY Destination Test

- JPY-candidate events: 4357
- JPY lead rate +12h: 0.221 | +24h: 0.2264
- Median time to JPY leadership: 2.2h
- Classification: **SUPPORTED**

## 7. Residual Shock Lead-Lag

| Pair | +4h rho(shock→base) | +4h rho(shock→quote) | +24h rho |
|------|--------------------|---------------------|----------|
| CHFJPY | -0.189 | 0.3285 | -0.1367 |
| EURCHF | -0.06474 | -0.3208 | -0.04627 |
| EURGBP | -0.01292 | -0.3446 | 0.001961 |
| EURJPY | -0.009338 | -0.4452 | 0.05604 |
| EURUSD | -0.01169 | -0.1199 | -0.001176 |
| GBPCHF | -0.4954 | 0.3318 | -0.3326 |
| GBPJPY | -0.1707 | 0.2368 | -0.1787 |
| GBPUSD | -0.281 | -0.03269 | -0.2669 |
| USDCHF | -0.1005 | 0.325 | 0.01132 |
| USDJPY | 0.003565 | 0.2143 | -0.0233 |

- EURGBP: **NOT_SUPPORTED** (-0.01292)
- EURJPY: **NOT_SUPPORTED** (-0.009338)
- EURCHF: **NOT_SUPPORTED** (-0.06474)

## 8. Residual Decay

| Pair | n | median half-life (h) | P(decayed ≤12h) | P(decayed ≤24h) |
|------|---|---------------------|-----------------|-----------------|
| CHFJPY | 258 | 1 | 1 | 1 |
| EURCHF | 422 | 1 | 0.9905 | 0.9929 |
| EURGBP | 247 | 1 | 0.9879 | 0.9879 |
| EURJPY | 245 | 1 | 0.9918 | 0.9918 |
| EURUSD | 411 | 1 | 0.9927 | 0.9951 |
| GBPCHF | 150 | 1 | 1 | 1 |
| GBPJPY | 152 | 1 | 0.9868 | 0.9934 |
| GBPUSD | 478 | 1 | 0.9874 | 0.9895 |
| USDCHF | 252 | 1 | 0.9881 | 0.9921 |
| USDJPY | 257 | 1 | 0.9728 | 0.9728 |

## 9. Network Dislocation Outcomes

- Mean dispersion change (24h): -1.008e-05 | P(normalize): 0.5549 | P(expand): 0.4168
- Dominant future leader at +24h: USD (0.2692)
- Classification: **PARTIALLY_SUPPORTED**

## 10. Sleeper Candidate Score

| Horizon | n | rank corr(score→future move) | bucket5−bucket1 mean |
|---------|---|------------------------------|---------------------|
| +1h | 80260 | 0.1869 | 0.0005609 |
| +2h | 80280 | 0.1752 | 0.0007078 |
| +4h | 80280 | 0.1411 | 0.0008732 |
| +6h | 80280 | 0.1314 | 0.0009785 |
| +8h | 80280 | 0.1184 | 0.001051 |
| +12h | 80280 | 0.1179 | 0.00116 |
| +24h | 80290 | 0.1177 | 0.001446 |
| +48h | 80330 | 0.09624 | 0.001555 |
- Classification: **SUPPORTED**

## 11. Multiple-Testing Control

- Development hypotheses tested: 840
- FDR-significant at q ≤ 0.10 (Benjamini-Hochberg within origin×direction families): 67

## 12. Frozen Candidates and Holdout Validation

- Candidate relationships frozen from development: **27**
- Holdout labels: {'VALIDATED': 8, 'WEAKENED': 9, 'FAILED': 10, 'INCONCLUSIVE': 0}

| Relationship | dev effect | dev q | holdout effect | label |
|--------------|-----------|-------|----------------|-------|
| CHF_ACCUMULATION_TO_GBP_H6 | -0.1506 | 0.0708 | -0.01289 | **WEAKENED** |
| CHF_ACCUMULATION_TO_GBP_H24 | -0.1678 | 0.0439 | 0.03566 | **FAILED** |
| CHF_ACCUMULATION_TO_GBP_H48 | -0.1779 | 0.0439 | 0.05452 | **FAILED** |
| EUR_ACCUMULATION_TO_GBP_H4 | 0.3226 | 2.37e-07 | -0.04031 | **FAILED** |
| EUR_ACCUMULATION_TO_GBP_H6 | 0.3528 | 2.21e-08 | -0.02923 | **FAILED** |
| EUR_ACCUMULATION_TO_GBP_H8 | 0.3552 | 2.21e-08 | -0.06409 | **FAILED** |
| EUR_ACCUMULATION_TO_GBP_H12 | 0.2937 | 2.98e-06 | -0.1028 | **FAILED** |
| EUR_ACCUMULATION_TO_JPY_H4 | -0.3477 | 2.38e-08 | -0.1535 | **WEAKENED** |
| EUR_ACCUMULATION_TO_JPY_H6 | -0.3771 | 4.69e-09 | -0.302 | **VALIDATED** |
| EUR_ACCUMULATION_TO_JPY_H8 | -0.3473 | 2.38e-08 | -0.3007 | **VALIDATED** |
| EUR_ACCUMULATION_TO_JPY_H12 | -0.2757 | 1.23e-05 | -0.2777 | **VALIDATED** |
| EUR_LIQUIDATION_TO_GBP_H4 | -0.3884 | 5.9e-11 | -0.05934 | **WEAKENED** |
| EUR_LIQUIDATION_TO_GBP_H6 | -0.4043 | 1.49e-11 | -0.04728 | **WEAKENED** |
| EUR_LIQUIDATION_TO_GBP_H8 | -0.3643 | 7.83e-10 | -0.02904 | **WEAKENED** |
| EUR_LIQUIDATION_TO_GBP_H12 | -0.3085 | 1.97e-07 | 0.04441 | **FAILED** |
| EUR_LIQUIDATION_TO_GBP_H24 | -0.2546 | 2.37e-05 | 0.05635 | **FAILED** |
| EUR_LIQUIDATION_TO_GBP_H48 | -0.2412 | 5.82e-05 | -0.02182 | **WEAKENED** |
| EUR_LIQUIDATION_TO_JPY_H4 | 0.3218 | 5.86e-08 | 0.2806 | **VALIDATED** |
| EUR_LIQUIDATION_TO_JPY_H6 | 0.3454 | 5.39e-09 | 0.2908 | **VALIDATED** |
| EUR_LIQUIDATION_TO_JPY_H8 | 0.303 | 2.95e-07 | 0.2566 | **VALIDATED** |
| EUR_LIQUIDATION_TO_JPY_H12 | 0.2481 | 3.66e-05 | 0.1824 | **VALIDATED** |
| EUR_LIQUIDATION_TO_JPY_H24 | 0.1648 | 0.0111 | 0.06839 | **WEAKENED** |
| EUR_LIQUIDATION_TO_JPY_H48 | 0.1601 | 0.0134 | 0.009789 | **WEAKENED** |
| JPY_LIQUIDATION_TO_CHF_H48 | 0.1597 | 0.0356 | 0.1595 | **VALIDATED** |
| JPY_LIQUIDATION_TO_GBP_H4 | 0.177 | 0.0203 | 0.01072 | **WEAKENED** |
| JPY_LIQUIDATION_TO_GBP_H6 | 0.1748 | 0.0203 | -0.01862 | **FAILED** |
| JPY_LIQUIDATION_TO_GBP_H8 | 0.173 | 0.0203 | -0.04059 | **FAILED** |

## 13. Thesis Classification (Section 33)

| Thesis | Verdict |
|--------|---------|
| GBP_bridge | **SUPPORTED** |
| CHF_parking | **PARTIALLY_SUPPORTED** |
| JPY_destination | **SUPPORTED** |
| EURGBP_residual_lead | **NOT_SUPPORTED** |
| EURJPY_residual_lead | **NOT_SUPPORTED** |
| EURCHF_residual_lead | **NOT_SUPPORTED** |
| EUR_origin_routing | **NOT_SUPPORTED** |
| network_dislocation | **PARTIALLY_SUPPORTED** |
| sleeper_score | **SUPPORTED** |

## 14. Phase 6 Gate

- gate_passed: **True** | phase_7_cleared: **True**

## 15. Phase 7 Eligibility

- 8 holdout-validated relationship(s) are eligible for Phase 7 strategy construction:
  - EUR ACCUMULATION -> JPY relative weakness, horizon 6h (family MEDIUM)
  - EUR ACCUMULATION -> JPY relative weakness, horizon 8h (family MEDIUM)
  - EUR ACCUMULATION -> JPY relative weakness, horizon 12h (family MEDIUM)
  - EUR LIQUIDATION -> JPY relative strength, horizon 4h (family SHORT)
  - EUR LIQUIDATION -> JPY relative strength, horizon 6h (family MEDIUM)
  - EUR LIQUIDATION -> JPY relative strength, horizon 8h (family MEDIUM)
  - EUR LIQUIDATION -> JPY relative strength, horizon 12h (family MEDIUM)
  - JPY LIQUIDATION -> CHF relative strength, horizon 48h (family LONG)
