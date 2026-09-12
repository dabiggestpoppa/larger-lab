# ALT-DATA-1 COVERAGE REPORT

**Checkpoint:** CRYPTO-ALT-DATA-1-CANONICAL-POINT-IN-TIME-UNIVERSE-AND-MULTISCALE-FEATURE-PANEL

Coverage is reported on UNIQUE point-in-time assets per date (never
asset×venue rows). Final figures are in `derived/report_numbers.json` and
`derived/build_summary.json`.

## 1. Universe

- Date range: 2020-06-01 → 2026-08-23 (daily snapshots; end = latest
  complete UTC day before the run date).
- Included dates: (n_dates) of 2,275 calendar days; excluded CMC-side
  data-gap dates documented in the data-quality report.
- Rows: (universe_rows) = n_dates × 500.
- Unique assets: (n_assets).

## 2. Multiscale feature coverage (fraction of universe rows with data)

| window | return | rank_change | realized_volatility | relative vs BTC |
|---|---|---|---|---|
| 1D | (filled) | | | |
| 3D | | | | |
| 7D | | | | |
| 14D | | | | |
| 30D | | | | |
| 60D | | | | |
| 90D | | | | |

Coverage decays with window length as required by the frozen rule: a w-day
feature is present only when the asset was in the top-500 at t AND at t−w
(returns/rank) or had ≥80% of the w-day window observed (vol/beta).
90D coverage is the lowest by construction, never backfilled.

## 3. Perp eligibility (unique asset-dates)

| venue | rows | eligible_ex_liquidity | mature ≥30d | tradable |
|---|---|---|---|---|
| HYPERLIQUID | (filled) | | | |
| OKX | | | | |
| BINANCE_USDM | — | UNVERIFIABLE_FROM_ENV (archive method documented) | | |
| BYBIT_LINEAR | — | UNVERIFIABLE_FROM_ENV | | |

Eligibility by rank band (any venue, unique asset-dates):

| band | eligible_ex_liquidity | fraction of band×dates |
|---|---|---|
| 1-10 | (filled) | |
| 11-25 | | |
| 26-50 | | |
| 51-100 | | |
| 101-200 | | |
| 201-300 | | |
| 301-500 | | |

The lower half of the top-500 is partially perp-tradable; much of 201-500
is structurally non-tradable (wrapped / LST / stable / niche assets
without perps), consistent with the DATA-0.1 finding.

## 4. Sector coverage

- Sector source: snapshot-associated CMC tags (multi-tag allowed).
- Status: HISTORICAL_APPROXIMATION (frozen; never POINT_IN_TIME_VERIFIED).
- Mapped asset-dates: (sector_mapped_asset_dates) of (universe_rows)
  ((fraction)); UNMAPPED (no tags): the remainder.
- Distinct tags: (n_tags). Tag vocabulary drifts over time (provider
  taxonomy); sector features are computed per (date, tag).
- Sector feature rows: (sector_feature_rows) (TOP1/3/5/10/FULL layers).
- Sector membership rows: (sector_membership_rows) — per-asset
  (date, sector) sector_rank coordinates for dual-rank (global+sector).

## 5. Identity

- Identity rows: (identity_rows), anchored on cmc_id
  (internal_asset_id = "CMC:{id}").
- CG join HIGH: (cg_join_high); CP join HIGH: (cp_join_high).
- Collision classes: (collision_classes). Unknown collisions are never
  auto-resolved.

## 6. Market terrain

- Rows: (terrain_rows) — one per included date.
- BTC dominance range: (btc_dominance_range) (denominator = top-500 total
  mcap at t, stablecoins included — frozen).
- Stablecoin mcap share range: (stablecoin_share_range).

## 7. Survivorship

- Survivorship rows: (survivorship_rows); exited labels: (n_exited_assets);
  assets still present at panel end: (n_assets_still_present).
- NON-CAUSAL annotations isolated in ALT_DATA_1_SURVIVORSHIP.parquet.

## 8. Feature registry

- FROZEN at sha256 (registry_hash) (see
  ALT_DATA_1_FEATURE_REGISTRY_HASH.json).
