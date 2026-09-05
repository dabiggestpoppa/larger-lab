# MECH-3 DATA TRUTH

**Checkpoint:** CRYPTO-ALT-MECH-3 · **Branch:** `agent/crypto-quant-foundry`
**Anchors:** MECH-1 `b3083df1` · MECH-2 `8636370a` · HEAD at run start: `04a09016`.

## 1. Truth lock (run at start, all checks)

| Check | Expected | Result |
|---|---|---|
| PIT universe rows | 1,098,000 | PASS |
| Unique assets | 2,898 | PASS |
| Included dates | 2,196 | PASS |
| Excluded source-gap dates | 79 | PASS |
| Rank unchanged from DATA-1 | yes | PASS |
| V2 benchmark identity tests | valid | PASS |
| DefiLlama global flow present | yes | PASS |
| DefiLlama chain flow present | yes | PASS |

`02_DATA_TRUTH.json` holds the machine-readable record (`all_pass: true`).

## 2. Inputs used

- `ALT_DATA_1_1_PIT_UNIVERSE.parquet` (universe, rows/assets/dates as above)
- `ALT_DATA_1_1_ASSET_MULTISCALE_FEATURES_V2.parquet` — V2 fields only; V1 prefixes
  (`relative_return_vs_`, `rolling_beta_vs_`, `residual_return_vs_`,
  `expected_return_given_`) are asserted absent from the consumed column set.
- `ALT_DATA_1_1_RANK_BAND_FEATURES.parquet`, `SECTOR_MEMBERSHIP`,
  `SECTOR_FEATURES`, `MARKET_TERRAIN_V2`, `PERP_ELIGIBILITY`, `GLOBAL_FLOW`,
  `CHAIN_FLOW`, `CHAIN_MAPPING`, `METEORA_ASSET_DAILY` (aggregate proxy only).
- All DefiLlama flow dates normalized to end-of-day buckets; CMC→DefiLlama
  chain-name bridge applied (fixed engineering alias, unchanged from MECH-1/2).

## 3. Point-in-time / causality handling

- All flow features (chain TVL changes, stablecoin changes, DEX/fees changes) are
  shifted by `AVAILABLE_NEXT_DAY` **within chain** (per-chain group shift) before any
  use. No same-day flow information enters day-t state.
- Market-cap-share-weighted market returns computed from V2 `market_cap_share ×
  return_1d`; no V1 relative-return fields.
- Routing states, precursor windows, plateau masks, event definitions all use only
  information available at day t (or strictly trailing windows for precursors).
- No forward-fill / interpolation of structurally missing flow data; gaps remain
  NaN and drop out of correlation/event computations.
- No future classification defines any state at t: concentration entry/exit events
  are defined from the day-t state series only; forward outcomes (7/14/30D) are
  computed as *outcomes*, never as state inputs.

## 4. Preserved entities

- Delisted/dead/migrated assets remain in the PIT universe (survivorship untouched).
- Chains present in only one source (CMC or DefiLlama) are excluded per coverage
  rules (≥ 120 merged days), never inferred.
- Meteora pool-level history remains DEFERRED; only the aggregate asset-level proxy
  exists and it failed to support relationships in MECH-1 — carried forward as a
  documented limitation, not patched.

## 5. Leakage audit

- Cross-check: no analysis column is constructed from a future window of the same
  series. Precursor windows use `.shift(1)` after trailing rolling means.
- The only forward-looking quantities in artifacts are explicitly labeled
  `fwd_*` / `mean_fwd_*` outcomes (WS C/I) and `next_state_*` / `destination_state`
  (WS E/G), which describe what happened after the event — never used to define it.

## 6. Chain-liquidity variable family provenance

| Coordinate | Source | Shift |
|---|---|---|
| tvl_lvl, tvl_share, tvl_chg7, tvl_chg30 | CHAIN_FLOW (DefiLlama) | per-chain AVAILABLE_NEXT_DAY |
| imp_share, vel7, mcshare, ret_brd1 | computed from FEATURES × CHAIN_MAPPING (PIT) | none (PIT-native) |
| sc_chg7/30, dex_chg7, fees_chg7 | GLOBAL_FLOW (DefiLlama) | AVAILABLE_NEXT_DAY |

Per-chain stablecoin supply, bridge flows, perp OI/funding, lending TVL, staking,
active addresses, exchange flows, wallet identities are **not available** and are
never synthesized (see 03_OBSERVATION_LIMITS.md).
