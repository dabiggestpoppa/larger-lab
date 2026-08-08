# Phase 2 Data Completion Report

**Task:** CR-P2-DATA-COMPLETION-05  
**Date:** 2026-08-07  
**Capital Routing SHA:** f4b7f0aba56334003f1339f9bdb8f77d8a44e0e7  
**Parent Master SHA:** 6f29af4adbeee41305c8a52a8bf9d432a70ed1e5

---

## Executive Summary

Phase 2 gate **FAILS**. While the common window intersection coverage is 98.66% (PASS), all 10 symbols fail the full target-window coverage requirement (≥97%). 

- **EURUSD/USDCHF**: ~66% target coverage (missing 2022-2023 history)
- **Other 8 symbols**: 82-85% target coverage (unexplained gaps >24h)
- **Common window**: 98.66% intersection coverage (PASS), all 10 symbols ≥97% in common window

---

## Gap Classification Audit

### Gap Categories by Symbol (Target Window)

| Symbol | Weekend Closure | Market Holiday | Friday Late Close | Unexplained | Total Missing |
|--------|-----------------|----------------|-------------------|-------------|---------------|
| EURUSD | 5,892 | 864 | 1,095 | 8,918 | 16,769 |
| GBPUSD | 5,892 | 864 | 1,095 | 3,993 | 11,844 |
| USDJPY | 5,892 | 864 | 1,095 | 3,993 | 11,844 |
| USDCHF | 5,892 | 864 | 1,095 | 8,918 | 16,769 |
| EURGBP | 5,892 | 864 | 1,095 | 4,511 | 12,362 |
| EURJPY | 5,892 | 864 | 1,095 | 4,511 | 12,362 |
| GBPJPY | 5,892 | 864 | 1,095 | 3,993 | 11,844 |
| CHFJPY | 5,892 | 864 | 1,095 | 3,993 | 11,844 |
| EURCHF | 5,892 | 864 | 1,095 | 4,255 | 12,006 |
| GBPCHF | 5,892 | 864 | 1,095 | 3,993 | 11,844 |

### Weekend Gaps Removed from Unexplained Counts
- **5,892 hours per symbol** (standard FX weekend closure)
- **1,095 hours per symbol** (Friday late close 21:00-23:00 UTC)
- **864 hours per symbol** (documented market holidays)

### Unexplained Gaps >24h by Symbol
| Symbol | Gaps >24h | Max Gap (hours) |
|--------|-----------|-----------------|
| EURUSD | 78 | 9,488 (2022-01-01 to 2023-07-03) |
| GBPUSD | 0 | 72 |
| USDJPY | 0 | 72 |
| USDCHF | 78 | 9,480 (2022-01-01 to 2023-07-03) |
| EURGBP | 10 | 28 |
| EURJPY | 10 | 28 |
| GBPJPY | 0 | 72 |
| CHFJPY | 0 | 72 |
| EURCHF | 10 | 28 |
| GBPCHF | 0 | 72 |

---

## Data Backfill Status

### EURUSD
- **Raw data available**: 2023-07-03 to 2026-05-29 (M5)
- **Missing**: 2022-01-01 to 2023-07-02
- **Backfill source**: Not found in local library, MT5 history, or alternate raw files
- **Status**: Cannot backfill without external data source

### USDCHF
- **Raw data available**: 2023-07-03 to 2026-05-29 (M5, Unix timestamps)
- **Missing**: 2022-01-01 to 2023-07-02
- **Backfill source**: Not found in local library, MT5 history, or alternate raw files
- **Status**: Cannot backfill without external data source

### EURGBP, EURJPY, EURCHF (Common Window Investigation)
- **Issue**: ~98.68% common coverage (below 97% threshold was 95.7% before FX hours fix)
- **Root cause**: 10 gaps >24h in common window (28 hours each)
- **Pattern**: Gaps from 2023-07-07 20:00 to 2026-05-15 23:00
- **Raw data check**: M5 data exists for these periods but has 2890-min gaps (weekend closures)
- **Resolution**: Fixed by proper FX trading hours (excluded late Friday hours). Now 98.68% common coverage ✅

---

## Final Coverage Metrics

### Target Window (2022-01-01 to 2026-05-21 18:00 UTC)
- **Expected trading hours**: 25,969 (excl. weekends, late Friday, holidays)

| Symbol | Target Coverage | Passes 97% |
|--------|-----------------|------------|
| EURUSD | 65.84% | ❌ |
| GBPUSD | 84.80% | ❌ |
| USDJPY | 84.80% | ❌ |
| USDCHF | 65.83% | ❌ |
| EURGBP | 82.63% | ❌ |
| EURJPY | 82.63% | ❌ |
| GBPJPY | 84.80% | ❌ |
| CHFJPY | 84.80% | ❌ |
| EURCHF | 83.60% | ❌ |
| GBPCHF | 84.80% | ❌ |

### Common Window (2023-07-03 to 2026-05-21 18:00 UTC)
- **Expected trading hours**: 17,101 (excl. weekends, late Friday, holidays)
- **Intersection coverage**: 98.66% ✅

| Symbol | Common Coverage | Passes 97% |
|--------|-----------------|------------|
| EURUSD | 99.98% | ✅ |
| GBPUSD | 99.97% | ✅ |
| USDJPY | 99.97% | ✅ |
| USDCHF | 99.97% | ✅ |
| EURGBP | 98.68% | ✅ |
| EURJPY | 98.68% | ✅ |
| GBPJPY | 99.97% | ✅ |
| CHFJPY | 99.97% | ✅ |
| EURCHF | 98.68% | ✅ |
| GBPCHF | 99.97% | ✅ |

---

## Per-Symbol Final Timestamps

| Symbol | First Timestamp | Last Timestamp | Rows |
|--------|-----------------|----------------|------|
| EURUSD | 2023-07-03T00:00:00Z | 2026-05-29T00:00:00Z | 18,089 |
| GBPUSD | 2022-01-03T00:00:00Z | 2026-05-29T23:00:00Z | 23,303 |
| USDJPY | 2022-01-03T00:00:00Z | 2026-05-29T23:00:00Z | 23,302 |
| USDCHF | 2023-07-03T00:00:00Z | 2026-05-29T23:00:00Z | 18,120 |
| EURGBP | 2015-10-12T20:00:00Z | 2026-06-03T20:00:00Z | 23,535 |
| EURJPY | 2015-10-12T20:00:00Z | 2026-06-03T21:00:00Z | 23,529 |
| GBPJPY | 2022-01-03T00:00:00Z | 2026-05-29T23:00:00Z | 23,293 |
| CHFJPY | 2022-01-03T00:00:00Z | 2026-05-21T18:00:00Z | 23,138 |
| EURCHF | 2015-10-12T20:00:00Z | 2026-06-03T21:00:00Z | 23,781 |
| GBPCHF | 2022-01-03T00:00:00Z | 2026-05-29T23:00:00Z | 23,301 |

---

## Quality Metrics (All Symbols)

| Metric | Result |
|--------|--------|
| Real raw file exists | ✅ All 10 |
| Raw SHA-256 valid | ✅ All 10 |
| Normalized H1 exists | ✅ All 10 |
| Provider known (mt5_pro) | ✅ All 10 |
| Timezone known (UTC) | ✅ All 10 |
| Price side known (bid) | ✅ All 10 |
| Malformed OHLC = 0 | ✅ All 10 |
| Duplicates = 0 | ✅ All 10 |
| Target coverage ≥ 97% | ❌ All 10 |
| No unexplained gap >24h | ❌ 5/10 |
| No synthetic source | ✅ All 10 |
| Hashes reproducible | ✅ All 10 |
| Common intersection ≥ 97% | ✅ 98.66% |

---

## Regression Tests

| Test | Result |
|------|--------|
| Weekend gaps not classified as unexplained | PASS |
| Holiday exclusions | PASS |
| Provider outage classification | PASS |
| True missing 48h weekday gap still fails | PASS |
| Partial interval backfill merges deterministically | NOT TESTED (no backfill) |
| Duplicate overlap during backfill resolves deterministically | NOT TESTED (no backfill) |
| Provider mismatch during backfill fails | NOT TESTED (no backfill) |

---

## Phase Status

- **phase_2_complete:** false
- **phase_3_cleared:** false

---

## Blocking Issues

1. **EURUSD/USDCHF missing 2022-2023 history** - No older raw data found in local library, MT5 history, or alternate files. Cannot backfill without external data source.

2. **All symbols below 97% target coverage** - Even with proper FX trading hours, coverage is 65-85% due to missing early history and persistent gaps.

3. **Unexplained gaps >24h for 5 symbols** - EURUSD, USDCHF (massive early gaps), EURGBP, EURJPY, EURCHF (10 gaps of ~28h each in common window).

---

## Artifacts Generated

- `data/manifests/batch_a_coverage_v3.json`
- `data/manifests/batch_a_common_window_v2.json`
- `artifacts/audits/p2_data_quality_by_symbol_v3.csv`
- `artifacts/audits/p2_gap_classification.csv`
- `artifacts/audits/p2_gap_classification_summary.json`
- `artifacts/audits/p2_gate_result_v3.json`
- `artifacts/reports/P2_DATA_COMPLETION_REPORT.md` (this file)

---

## Conclusion

Phase 2 **does not pass** the full target-window gate. While the common window (2023-07-03 onward) achieves 98.66% intersection coverage with all 10 symbols ≥97%, the full target window (2022-01-01 onward) fails for all symbols due to:

1. **EURUSD/USDCHF**: Missing 2022-2023 history entirely (no raw data available)
2. **Other symbols**: 82-85% coverage with unexplained gaps >24h

**Phase 3 is NOT cleared.** External data acquisition for EURUSD/USDCHF 2022-2023 history is required before proceeding.