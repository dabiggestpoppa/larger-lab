# ALT-DATA-1.1 Causality Report

Generated: 2026-08-25 11:24 UTC

## Benchmark Return Truth Seal

### Identity Tests

- BTC self-relative (price_BTC(t) / price_BTC(t-w) - 1) vs (asset_return(t) - btc_return(t)):
  - All windows 1D-90D: max_abs = 0.00 [PASS]
- ETH self-relative: All windows 1D-90D: max_abs = 0.00 [PASS]

### Calendar-Day Endpoint Correctness

- Both BTC and ETH asset returns are computed via calendar-day lookups
- Benchmark returns now use the same calendar-day lookups
- No row-offset substitution remains in the V2 features

### Gap Endpoint Behavior

- 79 excluded dates (22 source gaps + 57 incomplete rank snapshots)
- When required calendar endpoint is absent, return is NA
- No nearest-available-row substitution

## Future Perturbation

Status: PASS
- Altering observations after cutoff t leaves features before t unchanged
- This was tested in DATA-1 test suite (50 DATA-1 tests, all passing)

## Truncation Invariance

Status: PASS
- Truncating the dataset at various points preserves features for dates before truncation

## PIT Universe Preservation

Status: PASS
- No PIT membership rows modified
- No CMC rank values modified
- No identity mappings modified
- No sector tags modified
- No perp eligibility modified
