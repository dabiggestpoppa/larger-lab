# LF3 EVENT AND NEIGHBOR SCHEMA

## Core event key

`historical_date`, `cmc_id`, `rank_band`, `rank`, `event_sign`, `event_gate`, `z1`, `ret_1d`, `sigma_t0`.

The key is PIT-safe at the asset-date level. An event is never deduplicated across assets. Asset-level overlap purging is applied only to inference summaries.

## Neighborhood columns

| family | columns | definition |
|---|---|---|
| rank | `rank_neighbor_n`, `rank_neighbor_median_ret`, `rank_neighbor_p10_ret`, `rank_neighbor_p90_ret`, `rank_neighbor_same_sign`, `rank_neighbor_tail_share` | same-date PIT rank windows ±25/±50/±100, with the active implementation using ±50 |
| behavioral | `behavior_neighbor_n`, `behavior_neighbor_median_ret`, `behavior_neighbor_same_sign` | nearest available same-date peers by rank, market cap, volume, age, and trailing-volatility rank coordinates |
| correlation | `corr_neighbor_n`, `corr_neighbor_median_ret`, `corr_neighbor_same_sign` | nearest causal trailing-correlation peers when a valid lookback and sufficient overlap exist |
| state | `state_neighbor_n`, `state_neighbor_median_ret`, `state_neighbor_same_sign` | same momentum state, rank band, volatility regime, and liquidity bucket |
| topology | `sector_neighbor_n`, `chain_neighbor_n` | descriptive peer counts only; no causal sector/chain interpretation |

## Isolation scores

Each score is kept separate and has no optimized combination:

- `absolute_isolation = 1 - same_sign_fraction`;
- `rank_context_isolation = abs(asset_ret - rank_neighbor_median) / local_dispersion`;
- `behavioral_isolation = abs(asset_ret - behavior_neighbor_median) / local_dispersion`;
- `correlation_isolation = 1 - correlation-neighbor same-sign share`;
- `state_isolation = 1 - state-neighbor same-sign share`.

The committed first implementation includes rank-window isolation and a date-keyed extension schema for the remaining neighborhood families. Missing neighborhoods are explicit, never imputed as zero isolation.

## Outcome columns

Forward columns use existing continuous causal returns: `fwd1_cum`, `fwd2_cum`, `fwd3_cum`, `fwd5_cum`, `fwd7_cum`, `fwd10_cum`, `fwd14_cum`, `fwd21_cum`, `fwd30_cum`. Derived signed coordinates: `signed_fwd_h = event_sign*fwdh_cum`; `giveback_h = max(0,-signed_fwd_h)/abs(ret_1d)`; `full_reversal_h = signed_fwd_h < 0`; `new_extreme_h = signed_fwd_h >= abs(ret_1d)`.

## Deferred MECH-7 join

The core event generation does not depend on MECH-7. A stable join table uses `historical_date` as the primary key and stores the required context fields (`top500_breadth`, `top500_dispersion`, propagation state, concentration, BTC/ETH, risk state). If/when MECH-7 is available, it can be joined to the event table by date without regenerating events or changing event membership.

`EXECUTABILITY_STATUS=NOT_YET_AUDITED` for all columns and nodes. This is not an instrument-availability statement.
