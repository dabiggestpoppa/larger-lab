# CRYPTO-ALT-LOWER-FIELD-0 — PREREGISTRATION
## Fixed before any outcome analysis

**Checkpoint:** `CRYPTO-ALT-LOWER-FIELD-0`
**Agent:** AGENT 2
**Branch:** `agent/crypto-quant-foundry`
**Anchor commits:** Constitution `d030a1c1`, Definitions `bae722a1`, Idea Update `34b592f7`,
Lower-Field Hypothesis `85030bc4`, Dual-Agent `04a09016`, MECH-1 `b3083df1`, MECH-2 `8636370a`,
ALT-MECH-1 `b3083df1`, ALT-MECH-2 (`2c36afd0` base, decision PASS_ALT_TERRAIN_WITH_LIMITATIONS).
**Date frozen:** 2026-08-26 (before the collection run and before any lower-field outcome was viewed).
**Scope:** terrain research only. NO strategy, PnL, optimization, ML, sizing, deployment.

All thresholds, bands, horizons, state definitions, sample rules and control
procedures below are fixed HERE. Nothing below was chosen after seeing results.
Only data-source capability probes (HTTP reachability of ranks 501+ via the
canonical CMC endpoint) were performed before freezing; no price/return outcomes
were viewed.

---

## 1. Inputs

| Input | Role | Source |
|---|---|---|
| Canonical PIT Top-500 panel | ranks 1-500 reference + global terrain | `alt_rotation/data_1_1/ALT_DATA_1_1_PIT_UNIVERSE.parquet` (frozen) |
| Canonical asset features (V2) | returns/rank features for ranks 1-500 | `alt_rotation/data_1_1/ALT_DATA_1_1_ASSET_MULTISCALE_FEATURES_V2.parquet` (frozen) |
| Canonical market terrain | BTC/ETH returns, breadth, stablecoin share | `alt_rotation/data_1_1/ALT_DATA_1_1_MARKET_TERRAIN_V2.parquet` (frozen) |
| Canonical sector membership | tags for ranks 1-500 | `alt_rotation/data_1_1/ALT_DATA_1_1_SECTOR_MEMBERSHIP.parquet` (frozen) |
| **NEW: Lower-field PIT snapshots** | ranks 501-2000, same 2,196 dates | CMC internal historical-listings endpoint `start=1, limit=2000` (this checkpoint; panel keeps 501-2000, rows 1-500 used only for parity audit vs the frozen canonical panel) |

Collection authority for the new snapshots: same endpoint and access class
(`WEB_ONLY`, `PRIMARY_EMPIRICALLY_VERIFIED_WEB_ENDPOINT`) already verified in
ALT-DATA-0/1. Rank 501-2000 reachability was probed before freezing:
`start=501&limit=1500` returns ranks 501-2000, and `limit=2000` returns ranks
1-2000, for dates 2020-06-01 through 2026-08-20 (verified for 2020-06-01,
2022-01-01, 2024-06-01, 2026-08-20). The full 1-2000 fetch is used so the
same-FETCH ranks 1-500 can be verified row-by-row against the frozen canonical
Top-500 panel (parity audit; the 1-500 rows enter NO analysis).

## 2. Universe rules (frozen)

- **Rank window:** 501-2000 (cmcRank at snapshot date). Rows with cmcRank < 501
  or > 2000 are excluded from the panel. The same-fetch rows 1-500 are used ONLY
  for the parity audit against the frozen canonical panel and enter no analysis.
- **Calendar:** the 2,196 dates present in the canonical panel (2020-06-01 →
  2026-08-23), so lower-field and canonical panels align 1:1 by date. Gap dates
  (79) excluded exactly as canonical.
- **Identity:** `cmc_id` (CMC id) anchored; slug/symbol/name as recorded per
  snapshot (rebrands preserved via stable cmc_id).
- **Stablecoins:** CMC `is_stablecoin` flag. Primary asset-level tests EXCLUDE
  stablecoin rows (flagged `is_stablecoin=True`); counts of excluded rows are
  reported in every analysis and a sensitivity pass re-runs key elasticity
  results with stablecoins INCLUDED (reported in NULLS, not promoted).
- **Missing data:** NaN never backfilled. An asset-date row enters a test only if
  all features required by that test are non-NaN. Coverage per test reported.
- **Dead/delisted/rebranded assets are preserved** by construction (dated
  snapshots); no modern-survivor universe is created.

## 3. Rank bands (frozen; exactly the brief's candidate set)

`1-25`, `26-100`, `101-250`, `251-500`, `501-750`, `751-1000`, `1001-1500`, `1501-2000`
(8 bands; first four read from the canonical panel, last four from the new panel).

## 4. Global market impulse (frozen)

| Variable | Definition | Source |
|---|---|---|
| `mkt_ret_1d` | cap-weighted Top-500 1D return (total mcap of ranks 1-500 at t vs t-1) | computed from canonical panel (same definition as ALT-MECH-2) |
| `btc_ret_1d` | BTC 1D return | canonical terrain |
| `eth_ret_1d` | ETH 1D return | canonical terrain |
| `mkt_vol_30d` | cross-sectional median realized vol 30d | computed from canonical features (as ALT-MECH-2) |
| `breadth_30d` | top-500 30d breadth | canonical terrain |

Impulse classification (frozen, percentile-based on the full-sample empirical
distribution of `mkt_ret_1d`; percentiles computed from canonical panel only):

| Impulse class | Condition on mkt_ret_1d |
|---|---|
| POSITIVE_MARKET (extreme up) | ≥ P90 |
| NEGATIVE_MARKET (extreme down) | ≤ P10 |
| CALM | [P40, P60] |
| ALL | unconditional |

Robustness family (secondary, all cells reported, counted in reconciliation):
fixed-threshold impulses `mkt_ret_1d > +2%`, `< −2%`, `|mkt_ret_1d| < 0.5%`.

## 5. Asset extreme-event thresholds (frozen; Phase B)

Per-asset daily return (1D, in USD) empirical percentiles over the asset's own
observed life within the panel (min 120 observed days to be eligible):

- Family A: top/bottom 1% (|ret| ≥ P99 / ≤ P1)
- Family B: top/bottom 2.5% (P97.5 / P2.5)
- Family C: top/bottom 5% (P95 / P5)

ALL THREE families are computed and reported. No family is selected post hoc.
Cells with < 30 events are reported but not tested for significance.

## 6. Horizons (frozen; Phases F/G/H)

Returns: 1D, 3D, 7D, 14D, 30D, 60D. Horizon feature at t uses close-to-close
returns strictly before t (causal). 60D reported only where the asset has ≥ 80%
of the window observed; otherwise NaN.

## 7. Lenses (frozen; Phase B event catalog + Phase J)

Per extreme event, record (all from information available at event time t, causal):

- rank at t, rank band, market-cap band (log10 mcap quartiles)
- mkt_ret_1d, btc_ret_1d, eth_ret_1d (the global impulse)
- global breadth_30d, mkt_vol_30d, market concentration (top-3 mcap share)
- sector / subsector (CMC tags; HISTORICAL_APPROXIMATION status inherited)
- chain (platform_chain)
- prior volume acceleration: vol_24h(t) / median vol_24h over prior 7d
- prior rank velocity: Δrank over 3D and 7D
- prior returns: 1D, 3D, 7D, 14D, 30D, 60D
- listing age (days since CMC dateAdded)
- liquidity condition: dollar-volume quartile (cross-sectional within band-date)
- stale flag (see §8)
- stablecoin flag

Lenses are recorded for every event; they are NOT filters.

## 8. Data-quality flags (frozen)

| Flag | Definition |
|---|---|
| `stale_price` | price_usd unchanged vs prior date AND \|mkt_ret_1d\| > 0.5% |
| `zero_volume` | volume_24h_usd == 0 or missing |
| `missing_price` | price_usd missing/NaN |
| `suspicious_volume` | volume_24h_usd > 10× prior 7d median AND price change < 0.1% (fake-volume heuristic; recorded, never asserted as fact) |
| `listing_day` | days since CMC dateAdded ≤ 3 |

All analyses report results with stale/zero-volume/missing-price rows both
INCLUDED (raw) and EXCLUDED (clean) where feasible. Promotion requires the CLEAN
result; divergence between raw and clean is reported in NULLS.

## 9. Statistical procedures (frozen)

- **FDR:** BH-FDR at q = 0.05 for all multi-cell tests. Every cell reported.
- **Block bootstrap:** block length 20 days, 500 replicates, seed fixed
  `20260826` (project convention), for CIs and permutation p-values on
  time-series aggregates. Circular-shift permutation for lead-lag (shift ≥ 20d).
- **Minimum sample:** state/cell with ≥ 120 event-days (band-date) tested;
  30-119 reported-not-tested; < 30 recorded only.
- **Subperiod checks:** full sample split into year blocks (2020-21, 2022, 2023,
  2024, 2025-26). A cross-sample-stable claim requires the sign/direction to
  hold in ≥ 3 of 5 blocks with the magnitude not flipping in any block. Cycle
  exclusion reported per block.
- **Multiple testing ledger:** every family × band × threshold × horizon × lens
  combination is enumerated in 17_TEST_COUNT_RECONCILIATION.md.
- **Significance threshold:** two-sided α = 0.05 for single tests; FDR-adjusted
  for families.

## 10. Latent-state / HMM authorization gate (frozen)

HMM-like models are tested ONLY IF, after observable-state conditioning:

1. structured residuals remain (e.g., elasticity residual varies beyond
   BTC_UP/DOWN × VOL_HIGH/LOW segmentation); AND
2. repeated transition behavior is visible; AND
3. observed relationships systematically flip or cluster; AND
4. a lower-dimensional latent-state explanation is plausible.

Before any HMM: transparent k-means / Gaussian-mixture clustering on causal
features, conditional distributions, and observable-state transition matrices.
Any fitted latent model must be compared against observable-state baselines;
features must be causal; states never named from future outcomes. If the gate
fails, the checkpoint reports "latent-state work NOT justified at this
observation resolution" with the residual evidence shown.

## 11. Outcome classification (frozen)

Every tested derivative receives exactly one of:
`NEW_NODE` (survives controls, non-redundant), `MERGE` (redundant with an
existing node), `DISSOLVE` (pattern disappears under the correct control),
`NULL` (no structure found), `DATA_BLOCKED` (observation layer insufficient).

## 12. Promotion gate (frozen)

A finding may become a PROMOTION_CANDIDATE for Agent 1 only if:
data contract clear; observation layer sufficient; no PIT leakage; common
factors/redundancy addressed; survives perturbation (impulse substitution,
stablecoin inclusion, stale exclusion, subperiod split); null alternatives
documented; test counts reconciled; claim language matches the causal ladder
(L0-L6). Nothing becomes canonical automatically.

## 13. First-checkpoint decision (one of, chosen at the end)

`PASS_LOWER_FIELD_DISTINCT_STRUCTURE` /
`PASS_LOWER_FIELD_WITH_LIMITATIONS` /
`NO_DISTINCT_LOWER_FIELD_STRUCTURE` /
`BLOCKED_LOWER_FIELD_DATA`

## 14. Perturbation suite (frozen; applied to headline results)

| P-ID | Perturbation |
|---|---|
| P1 | Impulse substitution: mkt_ret_1d → btc_ret_1d (repeat elasticity core) |
| P2 | Stablecoin inclusion: repeat key tests with stablecoins included |
| P3 | Stale exclusion: repeat key tests excluding stale_price rows |
| P4 | Subperiod split: repeat by year block |
| P5 | Index form: cap-weighted vs equal-weighted market impulse |
| P6 | Truncation: recompute using data before 2025-01-01 only (no 2025-26 bull leg) |

## 15. Guardrails (frozen)

NO strategy design, NO entry/exit/stops, NO Kelly/sizing, NO PnL, NO Sharpe/PF
selection, NO ML predictors, NO backtests of trading rules, NO live deployment,
NO edits to Agent-1 canonical files. Seasonality only as a residual explanation
after lower-field structure is mapped. No result shopping.
