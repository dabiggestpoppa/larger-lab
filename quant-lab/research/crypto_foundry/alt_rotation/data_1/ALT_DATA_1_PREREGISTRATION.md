# ALT-DATA-1 PREREGISTRATION

**Checkpoint:** CRYPTO-ALT-DATA-1-CANONICAL-POINT-IN-TIME-UNIVERSE-AND-MULTISCALE-FEATURE-PANEL
**Parent:** CRYPTO-ALT-DATA-0.1-FOUNDATION-TRUTH-REPAIR (PASS_ALT_POINT_IN_TIME_UNIVERSE_FOUNDATION)
**Base SHA:** 922ddf480cb75f4e6dd6ecbbb1f71590a858df9e

This document freezes every design decision BEFORE building the canonical
panel. It is the reference for the feature registry, the collection
contract, and the tests. Later checkpoints must consume the frozen panel;
they must NOT silently alter these definitions.

---

## 1. Scope

Build the first CANONICAL historical altcoin terrain dataset:

- point-in-time (PIT) top-500 universe per date
- perp eligibility ledger (venue-specific)
- multiscale asset features (1D/3D/7D/14D/30D/60D/90D)
- rank-band, sector, and market-terrain aggregate panels
- BTC/ETH relative and beta/residual inputs (descriptive, no strategy)

NO strategy PNL. NO optimization. NO signal construction.

## 2. Date range and frequency

- **Start:** 2020-06-01 (earliest empirically verified CMC snapshot date;
  deeper history UNVERIFIED — no extrapolation)
- **End:** 2026-08-23 (latest complete UTC day before the run date
  2026-08-24; avoids partial current-day information)
- **Frequency:** DAILY snapshots (empirically feasible, ~0.7s/request;
  no downsampling)
- **Total dates:** 2,275 calendar days

## 3. Snapshot timing semantics (frozen)

- Each dated snapshot reflects the ranked top-500 **as of end of UTC day t**
  (CMC `lastUpdated` = `tT23:59:00Z`).
- Normalized observation timestamp = end-of-day UTC `t` (23:59:59).
- Feature rows dated `t` may use ONLY data from snapshots with date ≤ t.
- No timestamp mixing across sources: all daily panels key on the
  calendar date `t`.

## 4. Universe (frozen)

- Research universe at t = historical top-500 at t (by CMC rank).
- No current-universe backfill. No symbol-only joins. An asset that falls
  out of the top-500 disappears from the universe AFTER that date, never
  from its own history.

## 5. Eligibility dimensions (frozen)

Separate, non-interchangeable dimensions:

| dimension | meaning |
|---|---|
| TOP500_MEMBER | present in dated top-500 snapshot at t |
| COIN_AGE_ELIGIBLE | CMC dateAdded ≤ t (trivially true for all top-500; kept explicit) |
| CONTRACT_EXISTENCE_ELIGIBLE | venue contract existed and tradable at t |
| CONTRACT_MATURITY_ELIGIBLE | contract age ≥ 30 calendar days at t |
| HISTORICAL_DATA_ELIGIBLE | historical price/funding/volume data available at t |
| LIQUIDITY_PROXY_ELIGIBLE | volume-proxy evidence (NOT true historical liquidity) |
| FINAL_RESEARCH_ELIGIBLE_EX_LIQUIDITY | terminal status; liquidity NOT verified |

`FULLY_ELIGIBLE` is NOT used. Terminal status is
`ELIGIBLE_EX_LIQUIDITY` (liquidity dimension explicitly unverified).

## 6. Perp venues (frozen)

- **Hyperliquid** — verified in-environment. Listing = first valid funding
  timestamp (authority `INFERRED_FIRST_DATA_TIMESTAMP`); delisting = last
  funding timestamp + `isDelisted` meta flag
  (`INFERRED_LAST_FUNDING_TS`). Pre-listing zero-volume candles are NOT
  used as listing evidence. Known gap: HL-purged delisted coins
  unrecoverable via public API → PARTIAL.
- **OKX SWAP** — verified in-environment. Listing = official `listTime`
  (authority `OFFICIAL_LIST_TIME`). Delisted swaps silently omitted from
  current list → delisting history PARTIAL.
- **Binance USD-M** — live API geo-blocked (451) from this environment.
  Archive method verified (data.binance.vision, 2020-01+, incl. delisted
  contracts + funding). Per-asset archive verification NOT collected in
  this checkpoint → `UNVERIFIABLE_FROM_ENV`.
- **Bybit Linear** — live API geo-blocked (403) from this environment →
  `UNVERIFIABLE_FROM_ENV`.

## 7. Maturity rule (frozen, NOT optimized)

- `MIN_CONTRACT_AGE = 30` calendar days.
- `contract_age_days_at_t` is stored explicitly so later sensitivity
  testing can be done in a separate checkpoint WITHOUT rewriting history.

## 8. Multiscale windows (frozen, NOT optimized)

1D, 3D, 7D, 14D, 30D, 60D, 90D (calendar days). No extra windows.

## 9. Return and history rules (frozen)

- `return_w` = price_t / price_{t−w} − 1, requiring the asset to be
  present in the universe (have a snapshot price) at BOTH endpoints t and
  t−w. Otherwise NaN (INSUFFICIENT_HISTORY).
- Volatility / beta / rank-curve features over window w require the asset
  to be observed on ≥ 80% of the daily snapshots within (t−w, t]. Otherwise
  NaN (INSUFFICIENT_HISTORY). Rationale: the top-500 panel may miss an
  asset on days it ranked > 500; a full-100% rule would erase legitimate
  long-window features for most of the lower bands. The threshold is
  frozen here, is NOT tuned, and is recorded per feature.
- No partial-window statistic is ever labeled with its full window name.

## 10. Rank-motion sign convention (frozen)

- Lower numeric rank = stronger.
- `rank_change_w` = rank(t−w) − rank(t). **Positive = improving.**
- `rank_velocity_w` = rank_change_w (same quantity, descriptive name).
- `rank_acceleration_short` = [rank(t−7) − rank(t)] − [rank(t−14) −
  rank(t−7)]. Positive = 7D improvement accelerating over the prior 7D.
- `rank_acceleration_medium` = [rank(t−30) − rank(t)] − [rank(t−60) −
  rank(t−30)]. Positive = 30D improvement accelerating.
- Rank-curve lags: rank_1d_ago, rank_3d_ago, rank_7d_ago, rank_14d_ago,
  rank_30d_ago, rank_60d_ago, rank_90d_ago (rank at t−w).

## 11. Rank-curve descriptors (frozen formulas)

- `short_mid_rank_spread` = mean(rank_30d_ago, rank_60d_ago) −
  mean(rank_1d_ago, rank_3d_ago, rank_7d_ago). Positive = recent ranks
  better than mid-lag → improving.
- `mid_long_rank_spread` = mean(rank_60d_ago, rank_90d_ago) −
  mean(rank_14d_ago, rank_30d_ago). Positive = improving.
- `rank_curve_slope` = OLS slope of rank vs lag over the 7 lag points
  (lags 1,3,7,14,30,60,90). Positive slope = older ranks worse (higher)
  → improving toward present.
- `rank_curve_monotonicity` = fraction of the 6 adjacent lag pairs
  (ordered 1→3→7→14→30→60→90) where rank is non-increasing toward the
  present (i.e., rank(t−lag_early) ≥ rank(t−lag_late)). 1.0 = perfectly
  improving curve.
- `rank_curve_inflection_count` = number of sign changes in the sequence
  of adjacent first differences of the lagged rank vector.

## 12. Peak frequency (frozen, PIT only)

- top_decile = rank ≤ 50; top_quartile = rank ≤ 125 (of 500).
- `top_decile_hits_w` / `top_quartile_hits_w` = count of days in
  (t−w, t] where the asset was observed with rank ≤ threshold. Days the
  asset is absent from the panel count as NOT hit (rank > 500).
- `rank_peak` = best (minimum) rank achieved by the asset from its first
  appearance through t (cumulative PIT minimum).
- `days_since_rank_peak` = days since the last day that set a new
  cumulative minimum rank; 0 if rank(t) is a new peak.
- `rank_peak_count_w` = number of days in (t−w, t] that set a new
  cumulative minimum rank.
- `consecutive_positive_rank_velocity` = consecutive days up to t with
  rank(t) < rank(t−1) (strict improvement), ≥ 1.

## 13. Global rank bands (frozen, NOT optimized)

1-10, 11-25, 26-50, 51-100, 101-200, 201-300, 301-500.

## 14. Market-cap share and dominance (frozen denominator)

- `market_cap_share` = asset mcap / SUM(mcap of all top-500 members at t).
- Denominator includes every top-500 member (stablecoins included —
  stablecoin handling is explicit, see §15).
- `BTC_dominance` = BTC mcap / same top-500 total.
- `ETH_share` = ETH mcap / top-500 total.
- Denominator never mixes definitions across time.
- `total_alt_share` = 1 − BTC_dominance (top-500 denominator).

## 15. Stablecoins (frozen)

- An asset is flagged `is_stablecoin` if the snapshot at t carries a tag
  from the frozen set {stablecoin, stablecoin-asset-backed,
  stablecoin-algorithmically-stabilized, asset-backed-stablecoin,
  usd-stablecoin, algorithmic-stablecoin, eur-stablecoin,
  fiat-stablecoin, stablecoin-protocol} OR canonical symbol ∈ {USDT,
  USDC, BUSD, DAI, TUSD, USDP, FDUSD, USDE, PYUSD, GUSD, LUSD, FRAX,
  USTC, UST, EURS, USDD, USD1}. Both sets are recorded in the feature
  registry (the tag set was widened to the tags actually observed across
  the DATA-0 prototype snapshots).
- `stablecoin_mcap_share` = sum(stablecoin mcap) / top-500 total.
- Stablecoins remain in the universe (rank/mcap context) but are flagged;
  the perp ledger excludes them naturally (no perps) and the sector
  features are computed with an explicit `includes_stablecoins` flag.

## 16. Sector mapping (frozen statuses)

- Sector evidence = snapshot-associated CMC tags at t (multi-tag allowed).
- Status per (asset, date, tag): `HISTORICAL_APPROXIMATION` (tags are a
  provider taxonomy, not a verifiable PIT classification).
- Assets with no tags at t → `UNMAPPED`.
- `POINT_IN_TIME_VERIFIED` is NOT claimed for any CMC-tag sector.
- `CURRENT_ONLY` is used where a tag comes from a current-only source
  (not in this panel).

## 17. Liquidity statuses (frozen)

- `liquidity_proxy_status` ∈ {VOLUME_PROXY_ONLY, PARTIAL, NOT_AVAILABLE,
  N_A_NOT_LISTED, BLOCKED_FROM_ENV}.
- No "verified liquidity" language. No L2 depth, no executable spread.
- `historical_liquidity_verified` = FALSE for every row.

## 18. Beta / residual inputs (frozen)

- Windows 30/60/90d, OLS of asset daily log-returns on BTC (resp. ETH)
  daily log-returns over the window.
- Min observations: 20 (30d), 40 (60d), 60 (90d). Also require the 80%
  coverage rule.
- `expected_return_given_BTC_w` = beta × BTC return over w.
- `residual_return_vs_BTC_w` = asset return over w − expected return.
- Insufficient history → NaN, never backfilled.

## 19. Entry/exit tracking (frozen)

- `entered_top500` (causal): present at t and absent (or rank > 500) at
  t−1.
- `days_in_top500` / `consecutive_days_in_top500` (causal): consecutive
  membership up to t.
- `exited_top500` (NON-causal annotation, separate survivorship table):
  true on the last observed membership day; uses future knowledge
  (t+1). Stored OUTSIDE the causal feature panel and explicitly labeled
  `NOT_CAUSAL`. Never used by a causal feature.

## 20. Storage design (frozen)

- Canonical layers as Parquet:
  1. ALT_DATA_1_IDENTITY_MAP.parquet
  2. ALT_DATA_1_PIT_UNIVERSE.parquet
  3. ALT_DATA_1_PERP_ELIGIBILITY.parquet
  4. ALT_DATA_1_ASSET_MULTISCALE_FEATURES.parquet
  5. ALT_DATA_1_RANK_BAND_FEATURES.parquet
  6. ALT_DATA_1_SECTOR_FEATURES.parquet
  7. ALT_DATA_1_MARKET_TERRAIN_FEATURES.parquet
- Compact CSV samples under `samples/` for human review.
- Raw snapshot JSON bodies kept on disk under `probes/raw/` (gitignored,
  ~880 MB); per-date `.meta.json` sidecars committed (~2 MB) with SHA256;
  the provenance manifest chains raw → normalized → features.
- All pandas writes use explicit utf-8; `.gitattributes` pins byte-exact
  storage for provenance-critical files.

## 21. What this checkpoint explicitly does NOT do

- No long/short signals, ATR stops/targets, PF/WR, ML, topology (TDA),
  sector/band/window selection, or optimization of any frozen value.
- No DATA-1 rollover work (MECH-1) — lead-lag, rank-migration anatomy,
  capital-routing transitions are explicitly deferred.

## 22. Decision gate

PASS_ALT_CANONICAL_MULTISCALE_DATA_FOUNDATION requires the 16 conditions
listed in the checkpoint brief, including the future-perturbation test
(all features at t invariant to post-t perturbations).
