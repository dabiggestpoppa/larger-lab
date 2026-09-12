# MECH-7 — EVENT FAMILY SCHEMA

Definitions reconstructed **identically** to LOWER-FIELD-2 (`lf2_events.py
cluster_anatomy`) from `derivatives/lower_field_2/RESULTS/lf2_feature_frame.parquet`
(ranks 501-2000, continuous-causal sigma and forward cumsums).

## 1. Extreme event (base unit)

- `z1 = |ret_1d| / sigma_t0`
- extreme row: `z1 >= 2` and `ret_1d != 0`

## 2. Cluster class (same-day same-band same-sign count `ns`)

group key: [historical_date, rank_band, sign(ret_1d)]

| ns | cls |
|---|---|
| 1 | ISOLATED |
| 2..5 | LOCAL_CLUSTER |
| 6..20 | BAND_BROAD |
| >20 | MULTI_BAND |

## 3. MECH-7 families

| family | cls | sign |
|---|---|---|
| ISOLATED_DOWNSIDE_EXTREME | ISOLATED | -1 |
| LOCAL_CLUSTER_DOWNSIDE | LOCAL_CLUSTER | -1 |
| BAND_BROAD_UPSIDE | BAND_BROAD | +1 |
| MULTI_BAND_UPSIDE | MULTI_BAND | +1 |
| ISOLATED_UPSIDE | ISOLATED | +1 |
| COORDINATED_DOWNSIDE | BAND_BROAD or MULTI_BAND | -1 |

## 4. Outcome fields (from LF2 frame)

- `fwd7_cum`: cumulative 7D forward return (continuous, PIT-safe).
- `sigma_t0`: trailing 63D continuous sigma.
- fwd7 sigma: `fwd7_cum / (sigma_t0 * sqrt(7))`.
- REVERSAL: sign(fwd7_cum) == -event_sign and |fwd7_cum| > 0.
- COORDINATED_UP continuation: fwd7 sigma > 0; giveback: < 0; failure: < -1.

## 5. Cross-agent export key

`20_CROSS_AGENT_FIELD_CONTEXT.parquet` keyed by:

- `event_id` (per-asset extreme event id: `LF2EV_{cmc_id}_{date}`)
- `asset_id` (cmc_id)
- `date` (event day)

Columns: family, cls, sign, rank_band, ret_1d, sigma_t0, z1, fwd7_cum,
fwd7_sigma, reversal flag, plus the full canonical global field-state
coordinate set at t0 (breadth, dispersion, concentration, BTC/ETH, vol,
depth, canonical state, regime flags) and at t0-1D/3D/7D for lagged context.
NO forward outcome columns beyond the PIT-safe LF2 fwd fields already present
in the source frame (no target leakage).
