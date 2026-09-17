# LF5 PIT SUBSTRATE SCHEMA

## Identity and timing
`historical_date`, `cmc_id`, `symbol` where available, and PIT `rank`. One row per asset-date; duplicate asset-date rows are an integrity failure.

## Feature groups
- Returns: `ret_1d`, repaired cumulative `ret_3d`, `ret_7d`, `ret_14d`, `ret_30d`.
- Volatility: continuous pre-event `sigma_t0` and available 20D/30D/63D scales.
- Activity: `volume_24h_usd`, turnover proxy when market cap exists, volume percentile.
- Age: `listing_age_days`.
- Rank health: pre-event rank velocities; future rank fields are generated only where source histories permit.
- State: existing momentum state and global context joins where available.

## Matrix
The return matrix is long-form and keyed by `(historical_date, cmc_id)` with explicit missingness. A wide matrix may be generated as a derived cache for correlation windows, but missing values are never zero-filled.

## Peer maps
Every peer row contains event/date, asset, peer family, peer id, distance/similarity, lookback, valid overlap, and status. Membership is frozen at event t0 for primary outcome analysis. Future peer rematching is a sensitivity only.

## Integrity rules
All rolling windows are computed on continuous asset histories before filtering; trailing correlation uses dates strictly before the event date; listing age is causal; rank sign is documented; finite values and minimum overlap are enforced.
