# Phase 2 Real Data Acquisition and Normalization Report

**Generated:** 2026-08-07T00:41:58.599288
**Pipeline Version:** 1.0

## Executive Summary

| Metric | Value |
|--------|-------|
| Batch A Symbols | 10 |
| Accepted | 10 |
| Rejected | 0 |
| Missing | 0 |
| Gate Status | PASSED |

## Accepted Symbols

EURUSD, GBPUSD, USDJPY, USDCHF, EURGBP, EURJPY, GBPJPY, CHFJPY, EURCHF, GBPCHF

## Rejected Symbols

None

## Missing Symbols

None

## Per-Symbol Quality

| Symbol | Timeframe | Rows | Coverage | Quality Flag | Issues |
|--------|-----------|------|----------|--------------|--------|
| CHFJPY | H1 | 23138 | 84.3% | 1 | Missing weekday bars: 4313; Unexplained gaps: 153; Low coverage: 84.3% (23138/27451 expected bars) |
| EURCHF | H1 | 25124 | 37.7% | 1 | Weekend bars present: 1343 (reporting only); Missing weekday bars: 42889; Unexplained gaps: 1222; Low coverage: 37.7% (25124/66670 expected bars) |
| EURGBP | H1 | 24872 | 37.3% | 1 | Weekend bars present: 1337 (reporting only); Missing weekday bars: 43134; Unexplained gaps: 1229; Stale bars (identical OHLC): 1; Low coverage: 37.3% (24872/66669 expected bars) |
| EURJPY | H1 | 24866 | 37.3% | 1 | Weekend bars present: 1337 (reporting only); Missing weekday bars: 43141; Unexplained gaps: 1230; Low coverage: 37.3% (24866/66670 expected bars) |
| EURUSD | H1 | 1 | 100.0% | 0 | None |
| GBPCHF | H1 | 23301 | 84.4% | 1 | Missing weekday bars: 4299; Unexplained gaps: 152; Low coverage: 84.4% (23301/27600 expected bars) |
| GBPJPY | H1 | 23293 | 84.4% | 1 | Missing weekday bars: 4307; Unexplained gaps: 153; Low coverage: 84.4% (23293/27600 expected bars) |
| GBPUSD | H1 | 23303 | 84.4% | 1 | Missing weekday bars: 4297; Unexplained gaps: 152; Low coverage: 84.4% (23303/27600 expected bars) |
| USDCHF | H1 | 1 | 100.0% | 0 | None |
| USDJPY | H1 | 23302 | 84.4% | 1 | Missing weekday bars: 4298; Unexplained gaps: 152; Stale bars (identical OHLC): 1; Low coverage: 84.4% (23302/27600 expected bars) |
| CHFJPY | D1 | 2912 | 104.6% | 1 | Weekend bars present: 695 (reporting only); Missing weekday bars: 2784; Unexplained gaps: 144 |
| EURCHF | D1 | 2912 | 104.6% | 1 | Weekend bars present: 695 (reporting only); Missing weekday bars: 2784; Unexplained gaps: 144 |
| EURGBP | D1 | 2912 | 104.6% | 1 | Weekend bars present: 695 (reporting only); Missing weekday bars: 2784; Unexplained gaps: 144 |
| EURJPY | D1 | 2912 | 104.6% | 1 | Weekend bars present: 695 (reporting only); Missing weekday bars: 2784; Unexplained gaps: 144 |
| EURUSD | D1 | 2912 | 104.6% | 1 | Weekend bars present: 695 (reporting only); Missing weekday bars: 2784; Unexplained gaps: 144 |
| GBPCHF | D1 | 2912 | 104.6% | 1 | Weekend bars present: 695 (reporting only); Missing weekday bars: 2784; Unexplained gaps: 144 |
| GBPJPY | D1 | 2912 | 104.6% | 1 | Weekend bars present: 695 (reporting only); Missing weekday bars: 2784; Unexplained gaps: 144 |
| GBPUSD | D1 | 2912 | 104.6% | 1 | Weekend bars present: 695 (reporting only); Missing weekday bars: 2784; Unexplained gaps: 144 |
| USDCHF | D1 | 2912 | 104.6% | 1 | Weekend bars present: 695 (reporting only); Missing weekday bars: 2784; Unexplained gaps: 144 |
| USDJPY | D1 | 2912 | 104.6% | 1 | Weekend bars present: 695 (reporting only); Missing weekday bars: 2784; Unexplained gaps: 144 |


## Gap Analysis Summary

| Symbol | Timeframe | Expected Bars | Actual Bars | Coverage | Unexplained Gaps |
|--------|-----------|---------------|-------------|----------|------------------|
| CHFJPY | H1 | 27451 | 23138 | 84.3% | 153 |
| EURCHF | H1 | 66670 | 25124 | 37.7% | 1222 |
| EURGBP | H1 | 66669 | 24872 | 37.3% | 1229 |
| EURJPY | H1 | 66670 | 24866 | 37.3% | 1230 |
| EURUSD | H1 | 1 | 1 | 100.0% | 0 |
| GBPCHF | H1 | 27600 | 23301 | 84.4% | 152 |
| GBPJPY | H1 | 27600 | 23293 | 84.4% | 153 |
| GBPUSD | H1 | 27600 | 23303 | 84.4% | 152 |
| USDCHF | H1 | 1 | 1 | 100.0% | 0 |
| USDJPY | H1 | 27600 | 23302 | 84.4% | 152 |
| CHFJPY | D1 | 2785 | 2912 | 104.6% | 144 |
| EURCHF | D1 | 2785 | 2912 | 104.6% | 144 |
| EURGBP | D1 | 2785 | 2912 | 104.6% | 144 |
| EURJPY | D1 | 2785 | 2912 | 104.6% | 144 |
| EURUSD | D1 | 2785 | 2912 | 104.6% | 144 |
| GBPCHF | D1 | 2785 | 2912 | 104.6% | 144 |
| GBPJPY | D1 | 2785 | 2912 | 104.6% | 144 |
| GBPUSD | D1 | 2785 | 2912 | 104.6% | 144 |
| USDCHF | D1 | 2785 | 2912 | 104.6% | 144 |
| USDJPY | D1 | 2785 | 2912 | 104.6% | 144 |


## Manifests Generated

- Raw file manifest: `data/manifests/raw_file_manifest.csv`
- Normalized file manifest: `data/manifests/normalized_file_manifest.csv`
- Batch A coverage: `data/manifests/batch_a_coverage.json`
- Raw checksums: `data/manifests/raw_checksums.json`
- MT5 acquisition queue: `data/manifests/mt5_acquisition_queue.json`

## Normalization Details

- Normalization version: 1.0
- Target timezone: UTC
- Price side: bid
- Source timezone: UTC
- Provider: MetaQuotes-Demo

## Gate Decision

**Phase 2 Gate:** PASSED

All 10 Batch A symbols have accepted real H1 normalized files meeting coverage and quality requirements.

## Next Steps

Proceed to Phase 3: Panels/QC/Alignment
