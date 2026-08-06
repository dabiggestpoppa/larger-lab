# Phase 2 Truth Reclassification Report

**Task:** CR-P2-REAL-DATA-REPAIR-01
**Timestamp:** 2026-08-06T15:00:00Z
**Parent Commit:** cf01b754d22656b6554259e9fb27272e3ff7573e
**Capital Routing Commit:** 03d2bf9d803bdcccfba44cb40359cb6cf76a7ca4

## Current Assessment

| Component | Status |
|-----------|--------|
| Phase 2 Scaffold | Implemented |
| Phase 2 Real Acquisition | Not Complete |
| Phase 2 Real Normalization | Not Complete |
| Batch A Queue | Pending |
| Synthetic Output | Test-Only / Untrusted |

## Issues Found

1. **Synthetic Data Generation**: `src/capital_routing/phases/phase_2.py` generates synthetic random market data using NumPy (`np.random.normal`, `np.random.randint`, `np.random.uniform`) instead of loading, preserving, and normalizing actual historical price files.

2. **Unknown Provider/Timezone/Price Side**: Batch A queue reports all 10 symbols as pending with `provider=unknown`, `timeframe=unknown`, and no source provenance.

3. **No Real Raw Files**: No real raw files exist in the repository; the `data/` directory contains only synthetic CSV files created during the previous Phase 2 run.

4. **No Checksums**: No SHA-256 checksums recorded for any raw or normalized files.

5. **No Source Provenance**: Normalized output does not retain source file path, provider, timezone, or price side information.

6. **Synthetic Output Presented as Historical**: The previous Phase 2 run produced `processed_data.json` with synthetic data that was presented as if it were real historical market data.

## Required Actions

1. **Remove Synthetic Production Path**: Refactor `src/capital_routing/phases/phase_2.py` to remove `_generate_sample_data_points`, all `np.random` market-price generation, simulated provider processing, and automatic `status="completed"` when real files are absent.

2. **Quarantine Synthetic Generators**: Move any synthetic data generation to `tests/fixtures/synthetic_market_data.py` with clear labeling.

3. **Implement Real Raw-Data Acquisition**: Support existing local data-library files, MT5 exported CSV files, ZIP files containing CSV/Parquet, and existing Parquet files.

4. **Create MT5 Adapter**: Locate and wrap the user's existing MT5 historical-data export script.

5. **Implement Canonical Normalization**: Create `normalize.py`, `ohlc_validation.py`, `gap_analysis.py`, `provenance.py` with strict schema requirements.

5. **Produce Real Output Files**: Create raw/normalized directory structure with manifests and checksums.

6. **Implement Fail-Closed Gate**: Phase 2 passes only when all 10 Batch A symbols have accepted real H1 normalized files meeting coverage and quality requirements.

7. **Add Comprehensive Tests**: 16 specific test cases covering production rejection of synthetic input, UTC conversion, duplicate handling, malformed OHLC rejection, etc.

8. **Fix CI Workflow**: Operate from Capital Routing directory, use small committed fixture files for pipeline tests, distinguish fixture tests from real-data acceptance.

## Non-Negotiable Rules

1. Production Phase 2 must never generate random OHLC or volume.
2. Synthetic data is allowed only under `tests/fixtures/` and must be clearly labeled synthetic.
3. No Phase 2 PASS unless real raw files exist and their hashes are recorded.
4. Do not mark a symbol processed merely because it exists in the acquisition queue.
5. Provider, timezone and price side may not default to "unknown" while still passing the gate.
6. Do not forward-fill OHLC bars.
7. Preserve raw source files unchanged.
8. Every normalized file must retain source provenance.