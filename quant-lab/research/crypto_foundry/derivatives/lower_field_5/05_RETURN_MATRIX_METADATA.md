# PIT RETURN MATRIX METADATA

Long-form source: `PIT_RETURNS_LONG.parquet`; key `(historical_date, cmc_id)`;
value `ret_1d` (close-to-close from the PIT snapshot price). Wide cache:
`cache/pit_returns_wide.parquet` (float32, dates x cmc_id).

## Coverage
- Date range: 2020-06-01 through 2026-08-23
- Days: 2,195 (80 calendar days in the window lack snapshots; see lower_field/DATA_TRUTH/collection_log.txt)
- Assets: 7,658
- Rows: 4,389,902
- Ret_1d missing: 37,465 (0.85%)
- Wide matrix: 2,194 dates x 7,208 assets, 27.5% observed

## Missingness rules
- Missing observations are retained as NaN. Never zero-filled.
- An asset absent from the top-2000 on a day has no row that day; ret_1d after
  a re-entry gap is NaN (no forward/back fill across absence).
- Assets enter when first listed in the top-2000 (no survivor backprojection).

## Usage
- Trailing 60D/120D correlations are computed causally from windows ending at
  t-1 in the peer builder (`lf5_peer_maps.py`); no full-sample matrix is stored.
- Outcome fields (fwd*_cum, fwd_rank_*d) live in the substrate and are never
  consumed by feature construction or peer matching.

## Provenance
- Source: `C:\Users\wifik\Desktop\larger-lab-crypto\quant-lab\research\crypto_foundry\derivatives\lower_field\DATA_TRUTH\raw` (lf_snapshot_YYYYMMDD_r1_2000.json, CMC historical listings
  endpoint, WEB_ONLY access class; parity with canonical top-500 verified in
  lower_field/DATA_TRUTH/lf_parity_audit.csv).
- Substrate SHA-256 (first 16): `9574b3d40efb47a7`
- Rebuild: `python scripts/lf5_build_substrate.py`
