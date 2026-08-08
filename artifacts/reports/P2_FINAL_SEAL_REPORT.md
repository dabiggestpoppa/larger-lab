# Phase 2 Final Seal Report

**Task:** CR-P2-FINAL-SEAL-04  
**Date:** 2026-08-07  
**Capital Routing SHA:** 4751ff6745d2127be73a4e73096ec1a161727086  
**Parent Master SHA:** 7b629d15a36889e312393728fdf82130dbc39c81

---

## Executive Summary

The Phase 2 Final Seal gate **FAILS**. All 10 Batch A symbols fail the target-window coverage requirement (≥97%) and have unexplained gaps >24h. The common window intersection coverage is 95.48%, with 3 symbols (EURGBP, EURJPY, EURCHF) below 97% even in the common window.

---

## Target Window

- **Start:** 2022-01-01 00:00 UTC
- **End:** 2026-05-21 18:00 UTC (latest common timestamp across all 10 pairs)
- **Expected FX H1 Hours:** 27,451 (weekdays only, excluding weekends)

---

## Per-Symbol Target Window Coverage

| Symbol | First Timestamp | Last Timestamp | Rows | Target Coverage | Gaps >24h | Passes 97% |
|--------|-----------------|----------------|------|-----------------|-----------|------------|
| EURUSD | 2023-07-03T00:00:00Z | 2026-05-29T00:00:00Z | 18,089 | **65.44%** | 154 | ❌ |
| GBPUSD | 2022-01-03T00:00:00Z | 2026-05-29T23:00:00Z | 23,303 | **84.35%** | 232 | ❌ |
| USDJPY | 2022-01-03T00:00:00Z | 2026-05-29T23:00:00Z | 23,302 | **84.34%** | 232 | ❌ |
| USDCHF | 2023-07-03T00:00:00Z | 2026-05-29T23:00:00Z | 18,120 | **65.47%** | 154 | ❌ |
| EURGBP | 2015-10-11T20:00:00Z | 2026-06-03T20:00:00Z | 24,872 | **80.26%** | 232 | ❌ |
| EURJPY | 2015-10-11T20:00:00Z | 2026-06-03T21:00:00Z | 24,866 | **80.23%** | 232 | ❌ |
| GBPJPY | 2022-01-03T00:00:00Z | 2026-05-29T23:00:00Z | 23,293 | **84.31%** | 232 | ❌ |
| CHFJPY | 2022-01-03T00:00:00Z | 2026-05-21T18:00:00Z | 23,138 | **84.29%** | 232 | ❌ |
| EURCHF | 2015-10-11T20:00:00Z | 2026-06-03T21:00:00Z | 25,124 | **81.15%** | 232 | ❌ |
| GBPCHF | 2022-01-03T00:00:00Z | 2026-05-29T23:00:00Z | 23,301 | **84.34%** | 232 | ❌ |

**All 10 symbols fail target-window coverage (≥97%).**

---

## Common Window Analysis

- **Common Start:** 2023-07-03 00:00 UTC (latest first timestamp)
- **Common End:** 2026-05-21 18:00 UTC (earliest last timestamp)
- **Expected Common Hours:** 18,091
- **Intersection Hours:** 17,273
- **Intersection Coverage:** 95.48%

### Per-Symbol Common Window Coverage

| Symbol | Common Coverage | Passes 97% |
|--------|-----------------|------------|
| EURUSD | 99.29% | ✅ |
| GBPUSD | 99.34% | ✅ |
| USDJPY | 99.34% | ✅ |
| USDCHF | 99.34% | ✅ |
| EURGBP | 95.74% | ❌ |
| EURJPY | 95.71% | ❌ |
| GBPJPY | 99.29% | ✅ |
| CHFJPY | 99.25% | ✅ |
| EURCHF | 95.71% | ❌ |
| GBPCHF | 99.33% | ✅ |

**3 symbols fail common-window coverage (EURGBP, EURJPY, EURCHF).**

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
| No unexplained gap >24h | ❌ All 10 |
| No synthetic source | ✅ All 10 |
| Hashes reproducible | ✅ All 10 |

---

## Gate Requirements Check

| Requirement | Status |
|-------------|--------|
| real_raw_file_exists | PASS |
| raw_sha_valid | PASS |
| normalized_h1_exists | PASS |
| provider_known | PASS |
| timezone_known | PASS |
| price_side_known | PASS |
| malformed_ohlc_zero | PASS |
| duplicates_zero | PASS |
| target_coverage_ge_97 | **FAIL** |
| no_unexplained_gap_gt_24h | **FAIL** |
| no_synthetic_source | PASS |
| hashes_reproducible | PASS |

**Overall Gate: FAIL**

---

## Regression Tests

| Test | Result |
|------|--------|
| One bar over multi-year target ≠ 100% | PASS |
| Coverage cannot exceed 100% | PASS |
| Missing raw path fails | PASS |
| Missing SHA fails | PASS |
| 96.9% coverage fails | PASS |
| 97.0% coverage passes (if other reqs met) | PASS |
| Common window math reconciles | PASS |

---

## Blocking Issues

1. **Target-window coverage below 97% for all 10 symbols** - Data only starts from 2022-01-01 for some pairs, but EURUSD/USDCHF only have data from 2023-07-03
2. **Unexplained gaps >24h for all 10 symbols** - 154-232 gaps per symbol exceeding 24 hours
3. **Common-window coverage below 97% for 3 symbols** - EURGBP (95.74%), EURJPY (95.71%), EURCHF (95.71%)

---

## Phase Status

- **phase_2_complete:** false
- **phase_3_cleared:** false

---

## Artifacts Generated

- `data/manifests/batch_a_common_window.json`
- `data/manifests/batch_a_coverage_v2.json`
- `artifacts/audits/p2_coverage_reconciliation.json`
- `artifacts/audits/p2_gate_result_v2.json`
- `artifacts/reports/P2_FINAL_SEAL_REPORT.md` (this file)

---

## Conclusion

The repaired real Batch A files **do not** satisfy the research coverage contract for the full target window (2022-01-01 through latest common timestamp). While the common window (2023-07-03 onward) shows excellent coverage for 7/10 symbols, the target-window coverage requirement of ≥97% is not met by any symbol due to late data start dates for EURUSD and USDCHF, and persistent gaps >24h across all symbols.

**Phase 3 is NOT cleared.** Additional data acquisition or gap-filling is required before proceeding.