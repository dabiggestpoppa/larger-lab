# LF4 PEER MAP SCHEMA

## Event key
`historical_date`, `cmc_id`, `rank`, `rank_band`, `ret_1d`, `sigma_t0`, `z1`, `event_sign`, `participation`.

## Peer families
- `rank25/50/100`: same-date assets within the stated PIT rank distance, excluding the asset.
- `behavioral`: standardized pre-event coordinates (rank, market cap if available, volume/liquidity proxy, age, trailing volatility, ret7, ret30); nearest same-date peers only.
- `correlation`: trailing 60D/120D return correlation with minimum valid overlap; no future data.
- `state`: same momentum, volatility, rank-band, liquidity, and environment state.
- `local_basket`: same depth with similar pre-event volatility, liquidity, and age.
- sector/chain: descriptive labels, never causal peer definitions.

Every map reports neighbor count, median/p10/p90 return, same-sign share, tail share, dispersion, breadth, residual, and missingness. Behavioral/correlation/state maps are explicitly nullable when the LF2 cache lacks the required historical columns.

## Isolation coordinates
`absolute_isolation`, `rank_context_isolation`, `behavioral_isolation`, `correlation_isolation`, `state_isolation`, and `local_basket_residual` remain separate. No master score is created.

## Outcome classes
All isolated downside shocks are retained. Outcome labels are descriptive and event-time based: rebound, repair, partial recovery, continued decline, peer catch-down/catch-up, contagion, rejoin, or persistent decoupling. A named family requires >=50 effective events and >=3 subperiods.

## Recovery/rank clocks
Price clocks use signed forward returns relative to the event sign. Rank clocks use PIT rank differences and explicitly distinguish numerical rank improvement from worsening. Missing future observations are censored, not zero-filled.

## Quality statuses
`VALID`, `WEAK`, `UNSTABLE`, `NULL`, and `DATA_BLOCKED` are used per peer family. `EXECUTABILITY_STATUS=NOT_YET_AUDITED`.
