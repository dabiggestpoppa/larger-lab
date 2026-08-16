# MVE R0.5.4 DATA LOADER AUDIT — MVE_R05_DATA_LOADER_AUDIT.md

## Implementation

`src/mve/data_loader.py` provides:

- `CanonicalDataSpec` — frozen canonical dataset record (path + full SHA-256 + schema).
- `load_canonical_m5(spec=CANONICAL_EURUSD, repo_root=None)` — fail-closed loader.
- `select_volume_field(df, candidates)` — deterministic volume-field policy.
- `resample_m5_to_h1(m5)` — committed M5→H1 resampler (frozen conventions).
- `slice_data(df, start, end)` — chronological slicing interface with holdout guards.

The runner's `_load_research_data()` now calls the loader and returns real H1
OHLCV series (was: empty `pd.Series()` placeholders).

## Runtime validation order (each failure raises `DataPipelineError`)

1. canonical file exists (else: "missing")
2. SHA-256 matches frozen hash (else: "SHA-256 mismatch")
3. file size matches frozen size
4. CSV parses
5. timestamps parse explicitly (epoch `time`, else `%Y-%m-%d %H:%M:%S` UTC)
6. non-empty
7. required OHLC columns present
8. timestamps monotonic
9. no duplicate timestamps
10. OHLC numeric and positive
11. OHLC relationships valid (H≥L, H≥O, H≥C, L≤O, L≤C)

No automatic fallback, no alternate-file selection, no random/demo data, no
silent continuation.

## Volume field policy

`real_volume` is used only if it has meaningful positive observations;
otherwise `tick_volume` is used. For the canonical file `real_volume` is
all-zero, so `tick_volume` is selected and recorded in DataFrame metadata.
Fields are never combined.

## Tests

`tests/mve/test_data_pipeline.py` — 21 tests: valid canonical load, missing
file, wrong hash, empty file, corrupt schema, duplicate timestamp, non-monotonic
time, invalid OHLC, negative price, invalid timestamp, volume-field selection,
unsupported volume field, resampler OHLC/volume/boundary/weekend/incomplete-hour/
no-forward-fill/determinism, independent-audit equality, alternate-file
protection, and slice holdout guards. All pass.
