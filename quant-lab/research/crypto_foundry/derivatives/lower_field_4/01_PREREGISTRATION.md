# CRYPTO-ALT-LOWER-FIELD-4 PREREGISTRATION

## Scope
LF4 tests true peer and nearest-neighbor geometry around lower-field extreme events. It is descriptive terrain research only: no strategy, PnL, execution, sizing, leverage, or deployment.

## Frozen event universe
Use the LF2 causal sigma construction and LF3 event families. Primary events are same-date asset observations in rank bands 501-750, 751-1000, 1001-1500, and 1501-2000, with comparison bands 26-100, 101-250, and 251-500 only where repaired features are valid. Primary thresholds are |z1| >= 2 and >= 3; raw 10%, 15%, and 20% thresholds are sensitivity lenses. Downside and upside are never pooled for interpretation.

## Peer families
1. Same-date rank windows ±25/±50/±100.
2. PIT behavioral nearest neighbors using only pre-event rank, market cap, volume/liquidity proxy, listing age, trailing volatility, 7D return, and 30D return.
3. PIT trailing-correlation nearest neighbors using 60D/120D returns with minimum overlap.
4. State neighbors sharing momentum, volatility, rank band, liquidity bucket, and environment.
5. Dynamic local baskets by depth, volatility, liquidity, and age.
6. Sector/chain are descriptive only.

No future return, outcome, or Agent-1 label is used to define peers.

## Primary tests
- Coverage, overlap stability, turnover, out-of-sample similarity, missingness, and peer-basket correlation for every peer family.
- Compare rank-only loners with multi-neighborhood loners and false loners.
- Pre/post peer paths at -30 through +14 days.
- Price recovery and rank-health clocks at 3/7/14/30 days.
- 1σ recovery timing and later outcomes.
- Reconcile rank deterioration after harmonizing sign, threshold, purge, event family, and date deduplication.
- Broad-up versus broad-down sign×rank×participation geometry.
- Active liquidity/volume conditional tests with rank, z1, age, breadth, dispersion, BTC, and volatility controls.
- Audit LF3 basket dispersion and triangle semantics, then run only A=Top500 breadth, B=lower-field dispersion, C=tail share.

## Inference and minimum sample
Use asset-clustered or purged summaries, leave-one-quarter/cycle-out checks where available, and BH-FDR for broad lens scans. Named sequences/nodes require >=50 effective events and >=3 quarters/subperiods. No low-N family is promoted.

## Decision vocabulary
PROMOTION_CANDIDATE, LOCAL_NODE, MERGE, DISSOLVE, NULL, DATA_BLOCKED, or DESCRIPTIVE_ONLY. Statistical validity and executability remain separate. All output nodes carry `EXECUTABILITY_STATUS=NOT_YET_AUDITED`.

## Limitations fixed in advance
Behavioral/correlation peers are marked unavailable rather than fabricated if required source columns or a valid PIT lookback are absent. No hidden-state compression is attempted. Causal claims remain L0/L1 unless strictly lagged evidence and common-factor controls justify a higher level.
