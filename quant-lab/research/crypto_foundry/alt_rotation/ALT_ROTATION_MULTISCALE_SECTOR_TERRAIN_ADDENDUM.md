# QUANT BOX — Alt Rotation Multiscale + Sector Terrain Addendum

**Status:** IDEA FREEZE / RESEARCH DESIGN ADDENDUM
**Branch:** `agent/crypto-quant-foundry`
**Parent idea:** `ALT_ROTATION_IDEA_AND_DATA_REALITY_PLAN.md`
**Future lane:** `CRYPTO-ALT-ROTATION-1`
**Do not disturb:** current core ALPHA-2 experiment

---

# Purpose

This addendum freezes two major extensions to the Alt Rotation terrain concept before implementation:

1. **point-in-time multi-horizon rolling state**
2. **nested sector / universe rank structure**

The objective is to model crypto capital flow at multiple time scales and multiple structural levels without using future information.

The market should be treated as a dynamic field where each eligible asset has simultaneous coordinates in:

- the global top-500 universe,
- its sector / category,
- its rank band,
- multiple rolling horizons,
- BTC / ETH / dominance state,
- perp availability and liquidity state.

The individual coin is the final expression object, not the starting point.

---

# 1. Point-in-time rolling windows are mandatory

At every historical timestamp `t`, freeze the exact information a trader could have seen at `t`.

Primary rolling horizons:

- 1D
- 3D
- 7D
- 14D
- 30D / 1M
- 60D
- 90D

These windows must be computed causally.

No data after `t` may affect any feature at `t`.

The rolled feature panel should itself be persisted and hashed so future strategy research consumes the same historical state instead of recomputing it with changed methodology.

Suggested canonical dataset name:

`POINT_IN_TIME_MULTI_HORIZON_RANK_STATE`

---

# 2. Multi-horizon state curve

For every eligible asset, sector, rank band and market-wide basket, compute a simultaneous rolling state curve.

Example conceptual vector:

```text
[1D, 3D, 7D, 14D, 30D, 60D, 90D]
```

Each horizon should contain more than raw return.

Candidate per-window features:

```text
universe_rank
sector_rank
rank_change
rank_velocity
rank_acceleration
return
relative_return_vs_BTC
relative_return_vs_ETH
beta_vs_BTC
beta_vs_ETH
residual_return_vs_BTC
residual_return_vs_ETH
market_cap_share_change
volume_rank
volume_share_change
realized_volatility
ATR_normalized_move
breadth_contribution
sector_relative_strength
perp_volume_rank
funding_state
```

Not every feature must survive the data audit, but the architecture should support the full state vector.

---

# 3. Rolling-window disagreement

The difference between short-term and medium/long-term state is itself information.

Examples:

### Emerging rotation

```text
1D = strong
3D = strong
7D = improving
30D = weak / neutral
```

Possible interpretation:

capital is entering a previously weak asset / basket.

### Established leadership

```text
1D = strong
3D = strong
7D = strong
30D = strong
60D = strong
```

Possible interpretation:

persistent trend / accepted leadership.

### Spike / anomaly

```text
1D = extreme
3D+ = weak
```

Possible interpretation:

short-lived impulse, news shock, listing event, squeeze or early rotation.

Do not assume continuation or reversal. Measure what usually follows.

### Pullback inside trend

```text
1D = weak
3D = weak
30D = strong
60D / 90D = strong
```

Possible interpretation:

intermediate pullback / accumulation opportunity.

Again: descriptive state first, strategy later.

---

# 4. Rank-curve geometry

Treat the multi-horizon rank sequence as a shape:

```text
rank_curve = 1D -> 3D -> 7D -> 14D -> 30D -> 60D -> 90D
```

Candidate descriptors:

```text
short_mid_rank_spread
mid_long_rank_spread
rank_curve_slope
rank_curve_curvature_proxy
rank_curve_monotonicity
rank_curve_inflection_count
rank_curve_compression
rank_curve_expansion
```

Use ordinary statistics first.

Do not call a measure mathematical curvature unless the definition earns that label.

The goal is to capture the state transition represented by disagreement across time scales.

---

# 5. Peak frequency / repeated impulse tracking

Track repeated short-horizon leadership events rather than treating each one independently.

Candidate features:

```text
top_decile_hits_7d
top_decile_hits_14d
top_decile_hits_30d
top_quartile_hits_30d
consecutive_positive_rank_velocity
days_since_rank_peak
rank_peak_count_7d
rank_peak_count_14d
rank_peak_count_30d
```

Core research question:

> Does repeated short-term rank leadership predict medium-term persistence, broadening, exhaustion or reversal?

Possible examples to test:

- repeated 1D peaks precede sustained 14D / 30D leadership,
- repeated 1D peaks without breadth expansion precede exhaustion,
- repeated 3D leadership before a 30D rank breakout identifies an early capital-routing transition.

No assumption should be privileged before evidence.

---

# 6. Rank-band rolling state

Apply the same rolling framework to rank bands, not just coins.

Initial bands remain:

- 1–10
- 11–25
- 26–50
- 51–100
- 101–200
- 201–300
- 301–500

For each band and horizon measure:

```text
median_return
median_rank_velocity
breadth
market_cap_share
volume_share
sector_composition
realized_volatility
dispersion
members_entering
members_exiting
relative_return_vs_BTC
relative_return_vs_ETH
```

This is intended to reveal how a capital wave propagates through the ranked universe.

Example descriptive question:

> If the 201–300 band accelerates on 1D and 3D while the 101–200 band already has strong 14D breadth, does the 201–300 band usually continue, rotate upward, or mean-revert?

---

# 7. Sector is a core coordinate system

Each asset must have two simultaneous ranking coordinates where a defensible sector mapping exists:

```text
global_universe_rank
sector_rank
```

Example:

```text
Global rank: 146
Sector: AI
Sector rank: 4
```

This is more informative than global rank alone.

Sector must be treated as a dynamic basket with internal structure rather than a static label.

---

# 8. Nested market hierarchy

The intended structural hierarchy is:

```text
BTC / ETH / dominance regime
    -> Top-500 universe
        -> global rank band
            -> sector
                -> sector participation tier
                    -> individual eligible perp
```

A coin state should therefore be interpretable at all levels.

Example:

```text
BTC.D weakening
ETH/BTC strengthening
101-200 global band gaining breadth
AI sector gaining market-cap share
AI top-5 gaining global rank
coin = global rank 146 / sector rank 4
coin residual return vs BTC positive
perp mature and liquid
```

This is a terrain description, not yet a trade signal.

---

# 9. Sector participation curve

For each sector, explicitly track participation from leader concentration to broad expansion.

Core participation levels:

```text
TOP1
TOP3
TOP5
TOP10
FULL_SECTOR
```

Candidate measures at each level:

```text
return
rank_velocity
breadth
market_cap_share
volume_share
relative_strength_vs_BTC
relative_strength_vs_ETH
perp_volume_share
```

This creates a second structural axis alongside the rolling-time axis.

Time axis:

```text
1D -> 3D -> 7D -> 14D -> 30D -> 60D -> 90D
```

Participation axis:

```text
TOP1 -> TOP3 -> TOP5 -> TOP10 -> FULL_SECTOR
```

The intersection of these two axes is a major part of the future terrain map.

---

# 10. Candidate sector states

Do not force labels before data, but the system should be able to discover / represent states similar to:

### EARLY_CONCENTRATED_ROTATION

Top-1 / Top-3 strengthen while sector breadth remains weak.

### LEADERSHIP_BROADENING

Top-3 strength begins propagating into Top-5 / Top-10.

### BROAD_SECTOR_EXPANSION

Top-10 and median sector member both strengthen.

### LATE_STAGE_SATURATION

Most of sector strong across short and medium horizons.

### LEADER_FAILURE

Top sector leaders weaken while lower-ranked members continue chasing.

### SECTOR_RECONCENTRATION

Breadth collapses back toward top leaders.

### SECTOR_BREAKAWAY

Sector strengthens materially against BTC / ETH and the rest of top-500.

These are conceptual labels only until empirically derived.

---

# 11. Sector breadth and concentration

Track at minimum:

```text
sector_member_count
sector_members_in_top500
sector_members_in_top100
sector_top3_breadth
sector_top5_breadth
sector_top10_breadth
sector_full_breadth
sector_market_cap_share
sector_volume_share
sector_perp_volume_share
sector_leader_market_cap_share
sector_top5_market_cap_share
sector_concentration_hhi
```

This differentiates:

- one leader pumping,
- top leaders moving together,
- broad sector participation,
- full-market rotation.

---

# 12. Dispersion / sigma-style terrain

The sector/universe structure should explicitly measure dispersion.

Candidate measures:

```text
return_dispersion
rank_dispersion
beta_dispersion
volatility_dispersion
residual_return_dispersion
volume_dispersion
market_cap_dispersion
```

At least four levels should be available:

```text
coin
sector
rank_band
top500_universe
```

This allows questions such as:

> Is volatility increasing everywhere, or only inside one sector?

> Is a sector moving because all members participate, or because two leaders dominate?

> Is a rank band becoming more internally coherent or more dispersed?

The term sigma may be used descriptively, but actual statistical definitions must be explicit.

---

# 13. Leader / follower spread

For each sector calculate a leader-versus-body structure.

Candidate features:

```text
sector_leader_gap
sector_top3_vs_median
sector_top5_vs_median
sector_top10_vs_full
leader_rank_velocity_minus_sector_median
leader_return_minus_sector_median
```

Core hypothesis class:

> leaders may move first, and the sector may later broaden.

Competing hypothesis:

> leader concentration may instead mark exhaustion if breadth fails to confirm.

Both must be tested.

---

# 14. Sector-to-universe flow

Track whether sector-level moves alter the composition of the global top-500.

Candidate variables:

```text
sector_members_entering_top500
sector_members_exiting_top500
sector_members_entering_top300
sector_members_entering_top200
sector_members_entering_top100
sector_global_rank_velocity
sector_global_rank_acceleration
```

Example research question:

> If the sector top-5 gain global rank for 3D and 7D, does the rest of that sector subsequently gain representation in the top-500 / top-300 / top-200?

This directly maps capital migration through the universe.

---

# 15. Cross-level sequence research

The future mechanism engine should be able to discover sequences such as:

```text
BTC impulse
-> BTC dominance peaks / slows
-> ETH relative strength rises
-> one sector top-3 strengthens
-> sector top-10 broadens
-> sector membership migrates upward globally
-> neighboring rank band gains breadth
```

or competing sequences such as:

```text
sector leaders spike
-> breadth fails
-> global rank migration stalls
-> sector mean-reverts
```

Do not hard-code either path as truth.

---

# 16. Two-dimensional terrain surface

A practical first terrain representation can use two major coordinates:

### Axis A — time-scale state

```text
1D / 3D / 7D / 14D / 30D / 60D / 90D
```

### Axis B — participation depth

```text
coin / sector leader / top3 / top5 / top10 / full sector / rank band / universe
```

Then add contextual state variables:

- BTC / ETH trend,
- ETH/BTC,
- BTC dominance,
- stablecoin share,
- market breadth,
- market-cap share,
- volume share,
- perp liquidity,
- funding.

This may later be embedded / visualized as a dynamic market surface.

No advanced topology is required to call this terrain.

---

# 17. Topology / graph integration

The multiscale + sector features provide richer node attributes for the future network model.

Each asset node can contain:

```text
multi_horizon_rank_curve
sector_rank_curve
sector_participation_state
global_rank_band
relative_strength
beta
volatility
liquidity
perp_availability
```

Sector nodes can contain:

```text
participation_curve
breadth
concentration
dispersion
market_cap_share
volume_share
rank_velocity
```

Graph edges may represent:

- contemporaneous correlation,
- lagged correlation,
- beta,
- residual co-movement,
- shared sector,
- DEX liquidity relationship,
- capital-flow similarity.

Advanced topology remains conditional on proving incremental information beyond simpler methods.

---

# 18. Expanded data-source stack

The alt-rotation lane should not depend on a single aggregator.

## Point-in-time ranking

Primary candidate:

- CoinMarketCap Historical Snapshots

Independent / enrichment candidates:

- CoinPaprika
- CoinGecko

## Market cap / volume / metadata / category

- CoinMarketCap
- CoinPaprika
- CoinGecko

## DEX / on-chain liquidity context

- DexScreener
- DexPaprika where useful
- CoinGecko on-chain endpoints
- native DEX / chain sources already used by QUANT BOX

## Perpetual listing / instrument truth

- Binance USD-M Futures
- Bybit Linear Perpetuals
- OKX SWAP
- Hyperliquid

The data audit must determine historical completeness before accepting any source as canonical.

---

# 19. Nomics

Nomics should be treated as an archive-only / legacy source if useful historical dumps can be recovered.

Do not make the new lane operationally dependent on Nomics.

Possible use:

- independent historical cross-check,
- old market-cap / exchange coverage validation,
- archival universe reconstruction if downloadable data is available.

Status until verified:

`LEGACY_ARCHIVE_CANDIDATE`

---

# 20. DexScreener role

DexScreener is not the primary historical rank source.

Its main value is in the lower / more on-chain portion of the universe.

Potential fields / roles:

- chain identity,
- token contract identity,
- DEX pair creation time,
- liquidity,
- volume,
- FDV / market-cap context,
- multi-DEX presence,
- pair depth / activity,
- early on-chain activity before major CEX listing.

This creates an important distinction:

> market-cap rank movement

versus

> actual liquidity / capital migration.

A coin that rises in market-cap rank without meaningful liquidity growth should not automatically be treated as a strong capital-routing event.

---

# 21. Multi-layer rank migration

Where data permits, calculate parallel ranking systems:

```text
market_cap_rank
DEX_liquidity_rank
spot_volume_rank
perp_volume_rank
open_interest_rank (only if trustworthy historical data exists)
funding_extremity_rank
```

This allows states such as:

### CONFIRMED_CAPITAL_MIGRATION

market-cap rank improves
+
DEX liquidity rank improves
+
perp volume rank improves

### THIN_RANK_REPRICE

market-cap rank improves
but liquidity / volume ranks do not.

### DERIVATIVES_LED_MOVE

perp volume / funding / OI accelerate before market-cap rank.

### ONCHAIN_LED_MOVE

DEX liquidity / volume expand before perp and market-cap ranking.

Do not predeclare which is predictive.

---

# 22. Historical sector mapping caveat

Sector / category membership can change through time.

The future data audit must record:

```text
asset_id
sector_id
sector_name
source
effective_from
effective_to
mapping_confidence
mapping_method
```

If point-in-time sector history cannot be recovered, do not silently apply today's categories to the past without labeling the approximation.

Possible status classes:

```text
POINT_IN_TIME_VERIFIED
HISTORICAL_APPROXIMATION
CURRENT_ONLY
UNMAPPED
```

The research should prefer broad, stable sectors before fragile niche categories.

---

# 23. Canonical future feature panel

A useful future row may resemble:

```text
timestamp
asset_id
historical_global_rank
historical_sector
historical_sector_rank
rank_band
perp_eligible
perp_age_days
liquidity_bucket

return_1d
return_3d
return_7d
return_14d
return_30d
return_60d
return_90d

global_rank_change_1d
global_rank_change_3d
global_rank_change_7d
global_rank_change_14d
global_rank_change_30d
global_rank_change_60d
global_rank_change_90d

sector_rank_change_1d
sector_rank_change_3d
sector_rank_change_7d
sector_rank_change_14d
sector_rank_change_30d
sector_rank_change_60d
sector_rank_change_90d

relative_BTC_1d ... relative_BTC_90d
relative_ETH_1d ... relative_ETH_90d

sector_top3_breadth
sector_top5_breadth
sector_top10_breadth
sector_full_breadth
sector_mcap_share
sector_volume_share
sector_dispersion

BTC_state
ETH_state
ETHBTC_state
BTC_dominance_state
universe_breadth_state
```

This is descriptive terrain data, not a strategy signal table.

---

# 24. Research order update

The future lane should proceed in this order:

## CRYPTO-ALT-DATA-0

`POINT-IN-TIME-RANKING-AND-PERP-UNIVERSE-REALITY-AUDIT`

Prove the historical universe can be reconstructed without survivorship / listing look-ahead.

## CRYPTO-ALT-DATA-1

Build the canonical point-in-time eligibility ledger plus frozen multi-horizon rolling feature panel.

## CRYPTO-ALT-MECH-1

Study:

- BTC / ETH lead-lag,
- rank migration,
- multi-horizon rank curves,
- peak frequency,
- sector hierarchy,
- sector participation curves,
- dispersion,
- rank-band propagation,
- relative resistance / weakness.

## CRYPTO-ALT-MECH-2

Build the market terrain / graph representation and test whether topology adds incremental information.

## CRYPTO-ALT-ALPHA-1

Generate frozen strategies only from supported mechanisms:

- channel-the-wave relative-value,
- move-with-stream directional trend,
- sector rotation,
- relative resistance / weakness,
- ATR-normalized execution.

## CRYPTO-ALT-ALPHA-2

Backtest / falsify against point-in-time eligible perpetual universe.

---

# 25. Governing concept

**Each asset has a location in time-scale, sector, universe rank, liquidity and BTC/ETH capital-flow space.**

The system should map movement through those coordinates instead of chasing named coins.

The intended hierarchy is:

```text
MARKET REGIME
-> BTC / ETH / dominance
-> rank-band flow
-> sector flow
-> sector participation
-> individual relative strength
-> real perpetual availability
-> execution
```

The key object is not the coin.

The key object is the **capital-routing state** the coin currently occupies.
