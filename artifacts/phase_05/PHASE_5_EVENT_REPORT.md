# Phase 5 — Routing Event Engine

**Task:** CR-P5-ROUTING-EVENT-ENGINE-01

## Summary

- Total event episodes: **8076**
- BROAD_CURRENCY_EVENT: 4357
- RESIDUAL_SHOCK: 2872
- NETWORK_DISLOCATION: 847

## Sample-Size Classifications

| Family | Count | Classification |
|--------|-------|----------------|
| BROAD_CURRENCY_EVENT | 4357 | ADEQUATE_SAMPLE |
| RESIDUAL_SHOCK | 2872 | ADEQUATE_SAMPLE |
| NETWORK_DISLOCATION | 847 | ADEQUATE_SAMPLE |
| ORIGIN_EUR | 900 | ADEQUATE_SAMPLE |
| ORIGIN_GBP | 858 | ADEQUATE_SAMPLE |
| ORIGIN_USD | 842 | ADEQUATE_SAMPLE |
| ORIGIN_CHF | 874 | ADEQUATE_SAMPLE |
| ORIGIN_JPY | 883 | ADEQUATE_SAMPLE |

## Threshold Manifest

- Method: trailing rolling percentiles / MAD / z-score over a fixed run_length. Fixed from statistical logic, NOT chosen using future returns.
- Origin factor p95 threshold: 0.00505192
- Residual p95 threshold: 0.00501945
- Network RMSE p95: 0.000873233
- Hysteresis entry/reset: {'entry_percentile': 0.95, 'reset_percentile': 0.8}

## Severity Distribution

| severity   |   count |
|:-----------|--------:|
| EXTREME    |     103 |
| LOW        |    5853 |
| MEDIUM     |    2120 |
