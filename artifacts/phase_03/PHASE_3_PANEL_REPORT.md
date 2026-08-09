# Phase 3 — Canonical Common Market Panel

**Task:** CR-P3-COMMON-PANEL-01  
**Date:** 2026-08-09  
**Gate:** ✅ PASS  
**Phase 4 Cleared:** ✅ TRUE

---

## Executive Summary

Built the canonical synchronized H1/H4/D1 research panel from **accepted Phase 2
normalized datasets only**. The panel is timestamp-indexed, calendar-aware, and
preserves all missing observations (no forward-filling). All QC gates pass.

**Gate result:** ✅ PASS  
**Phase 4 cleared:** ✅ TRUE

---

## Universe

EURUSD, GBPUSD, USDJPY, USDCHF, EURGBP, EURJPY, GBPJPY, CHFJPY, EURCHF, GBPCHF

- **Asset class:** all FX
- **Source:** Phase 2 accepted normalized H1 (`data/normalized/h1/*_H1.parquet`)
- **Provider:** mt5_pro
- **Session calendars:** Group 1 (7 majors) Mon 00:00-Fri 23:00 UTC; Group 2 (3 EUR crosses) Mon 00:00-Fri 19:00 UTC

---

## Panel Dimensions

| View | Rows |
|------|------|
| H1 Master Panel (union) | 24848 |
| H1 Strict Common Panel | 17273 |
| H4 Master Panel | 7431 |
| D1 Master Panel | 2446 |

**Master H1 range:** 2023-07-03 00:00:00+00:00 → 2026-05-21 18:00:00+00:00

---

## Research Windows

**Strict Common Window (all 10 symbols present & open):**

- **Earliest:** 2023-07-03 00:00:00+00:00
- **Latest:** 2026-05-21 18:00:00+00:00
- **Intersection valid hours:** 17273

This is the canonical window on which all subsequent Capital Routing empirical
research will run.

---

## Per-Symbol Common-Window Coverage

| Symbol | Coverage |
|--------|----------|
| EURUSD | 99.79% |
| GBPUSD | 99.84% |
| USDJPY | 99.83% |
| USDCHF | 99.83% |
| EURGBP | 99.54% |
| EURJPY | 99.50% |
| GBPJPY | 99.78% |
| CHFJPY | 99.75% |
| EURCHF | 99.50% |
| GBPCHF | 99.83% |

---

## Largest Unexpected Market-Open Gaps

| Symbol | Largest gap (hours) |
|--------|---------------------|
| EURUSD | 9h |
| GBPUSD | 5h |
| USDJPY | 5h |
| USDCHF | 5h |
| EURGBP | 5h |
| EURJPY | 8h |
| GBPJPY | 8h |
| CHFJPY | 13h |
| EURCHF | 8h |
| GBPCHF | 6h |

> Unexpected missing = market open (per calendar) but no observation. Weekend
> and scheduled closures are excluded, never counted as missing.
> Largest gap in the strict common window: **13h** (all ≤24h).

---

## Cross-Rate Identity QC

Validated synchronization via triangulation residuals (actual log-return minus
predicted log-return from base/quote pair):

| Identity | N | Mean Residual | Std Residual | Max Abs Residual |
|----------|---|---------------|--------------|------------------|
| EURGBP~EURUSD/GBPUSD | 17245 | 4.3e-07 | 0.0008407 | 0.00780501 |
| GBPCHF~GBPUSD/USDCHF | 18111 | -1.362e-05 | 0.00204183 | 0.02997074 |
| EURCHF~EURUSD/USDCHF | 17240 | -1.025e-05 | 0.00192441 | 0.02686936 |
| EURJPY~EURUSD/USDJPY | 17240 | 1.028e-05 | 0.00212784 | 0.02771213 |
| GBPJPY~GBPUSD/USDJPY | 23138 | 1.437e-05 | 0.00266481 | 0.05466587 |
| CHFJPY~USDCHF/USDJPY | 17946 | 2.391e-05 | 0.00200356 | 0.03789111 |

> Small residuals confirm the 10-pair panel is internally synchronized.

---

## Staleness Flag

Repeated close values during market-open hours (flagged, not dropped):

| Symbol | Stale candidates |
|--------|------------------|
| EURUSD | 141 |
| GBPUSD | 129 |
| USDJPY | 98 |
| USDCHF | 159 |
| EURGBP | 287 |
| EURJPY | 89 |
| GBPJPY | 67 |
| CHFJPY | 68 |
| EURCHF | 221 |
| GBPCHF | 143 |

---

## Outlier QC (flagged, not dropped)

| Symbol | Impossible OHLC | Nonpositive | Extreme Return |
|--------|-----------------|-------------|----------------|
| EURUSD | 0 | 0 | 10 |
| GBPUSD | 0 | 0 | 25 |
| USDJPY | 0 | 0 | 30 |
| USDCHF | 0 | 0 | 9 |
| EURGBP | 0 | 0 | 65 |
| EURJPY | 0 | 0 | 33 |
| GBPJPY | 0 | 0 | 20 |
| CHFJPY | 0 | 0 | 17 |
| EURCHF | 0 | 0 | 31 |
| GBPCHF | 0 | 0 | 13 |

---

## Masks & Transforms Generated

- `availability_masks.parquet` — valid observation present per symbol
- `market_open_masks.parquet` — expected market-open per calendar
- `price_transforms.parquet` — simple/log returns, range, volatility (raw OHLC untouched)
- `missingness_classification` — present / closed / unexpected_missing

Raw OHLC in `h1_master_panel.parquet` is **untouched**; all transforms live in
separate columns/artifacts.

---

## Orientation Convention

- `EURUSD` positive return = EUR strength / USD weakness
- `USDCHF` positive return = USD strength / CHF weakness
- `USDJPY` positive return = USD strength / JPY weakness
- All 10 pairs documented in `CURRENCY_ORIENTATION`.

Never compare raw pair returns without orientation.

---

## Do NOT do yet (Phase 4 does this)

- Fit routing models / optimize thresholds
- Claim EUR origin / GBP bridge / CHF parking / JPY destination
- Rank sleeper trades / lead-lag selection / correlation optimization

Phase 3 created the laboratory. Phase 4 begins measuring.

---

## Artifacts (capital-routing/artifacts/phase_03/)

- `input_manifest.json`
- `h1_master_panel.parquet`
- `h1_strict_common_panel.parquet`
- `h4_master_panel.parquet`
- `d1_master_panel.parquet`
- `availability_masks.parquet`
- `market_open_masks.parquet`
- `price_transforms.parquet`
- `coverage_matrix.csv`
- `cross_rate_identity_qc.csv`
- `staleness_report.csv`
- `outlier_report.csv`
- `common_overlap_report.json`
- `phase_3_gate.json`
- `PHASE_3_PANEL_REPORT.md` (this file)
