# ALT_MECH_1 PREREGISTRATION
## CRYPTO-ALT-MECH-1 — RANK-MIGRATION, LEAD-LAG, SECTOR-ROTATION & CAPITAL-FLOW ANATOMY

Preregistered BEFORE any outcome analysis was run. Every threshold below was fixed
before the analysis script executed. Parent: DATA-1.1 (`PASS_ALT_DATA_TRUTH_SEAL_WITH_METEORA_DEFERRED`).
Base SHA: `2c36afd0ee3f1670506b7c824513b64930e7626b`.

This checkpoint is MECHANISM RESEARCH ONLY: no PnL, no optimization, no ML,
no portfolio construction, no capital routing, no live execution.

---

## 1. INPUTS (canonical)

| File | Role |
|---|---|
| `data_1_1/ALT_DATA_1_1_PIT_UNIVERSE.parquet` | PIT universe (unchanged from DATA-1) |
| `data_1_1/ALT_DATA_1_1_ASSET_MULTISCALE_FEATURES_V2.parquet` | V2 asset features |
| `data_1_1/ALT_DATA_1_1_RANK_BAND_FEATURES.parquet` | rank-band aggregates |
| `data_1_1/ALT_DATA_1_1_SECTOR_MEMBERSHIP.parquet` | PIT sector membership |
| `data_1_1/ALT_DATA_1_1_SECTOR_FEATURES.parquet` | sector aggregates (FULL_SECTOR layer only) |
| `data_1_1/ALT_DATA_1_1_MARKET_TERRAIN_V2.parquet` | market terrain |
| `data_1_1/ALT_DATA_1_1_PERP_ELIGIBILITY.parquet` | perp eligibility (context only) |
| `data_1_1/ALT_DATA_1_1_GLOBAL_FLOW.parquet` | DefiLlama global flow |
| `data_1_1/ALT_DATA_1_1_CHAIN_FLOW.parquet` | DefiLlama chain flow |
| `data_1_1/ALT_DATA_1_1_CHAIN_MAPPING.parquet` | asset→chain mapping |
| `data_1_1/ALT_DATA_1_1_METEORA_ASSET_DAILY.parquet` | Meteora aggregate TVL proxy |

**Forbidden:** V1 relative-return/beta/residual fields (`relative_return_vs_*`,
`rolling_beta_vs_*`, `residual_return_vs_*`, `expected_return_given_*`). These columns
exist in the V2 parquet for registry-hash continuity but are NOT read by this analysis.
The loader selects an explicit allow-list of columns; any use of a forbidden column is a FAIL.

**Truth lock (must verify before analysis):**
PIT rows = 1,098,000; unique assets = 2,898; included dates = 2,196;
excluded source-gap dates = 79; V2 feature hash =
`0d666e74c0cf76adf6e6e6f2a6c47b1f52116f070fd1376c83274e6b077703ba`;
registry-definition hash = `ea7eca86a2656654c65f20971d5fc70374adfbba4186c5f9a2a48c4ce21917ef`.
NOTE: the checkpoint brief quoted the feature hash with two characters dropped
(`...adf6e6f2a6c47b...`); the canonical 64-hex hash recomputed from
`sha256(json.dumps({"version":"2.0.0","columns":sorted(cols)}, sort_keys=True))`
is the value above, matching DATA-1.1's frozen registry. Documented in the truth-lock artifact.

---

## 2. SIGN CONVENTIONS AND HORIZONS

- `rank_velocity_kd > 0` = rank improvement (verified: `rank_velocity_1d == rank_1d_ago − global_rank`).
- Horizons fixed: **1D, 3D, 7D, 14D, 30D**. No other horizon is reported except 60D/90D
  inside terrain descriptions where already present in inputs. No result-driven horizon selection.
- A transition at date t uses state at t and outcome band/rank at exactly t+h (calendar days);
  if t+h is absent from the panel (source gap or panel end), the observation is skipped — gaps are
  never bridged.

## 3. BAND DEFINITIONS (fixed)

R01_010=`1-10`, R011_025=`11-25`, R026_050=`26-50`, R051_100=`51-100`,
R101_200=`101-200`, R201_300=`201-300`, R301_500=`301-500`. Outside Top-500 = `EX500`.

## 4. EPISODE RULES (preregistered before outcome analysis)

**Band rotation episode (per band):**
- START: band median `rank_velocity_7d` ≥ P70 of that band's own trailing 252-calendar-day
  distribution (expanding min_periods=60 before day 252) **AND** band `breadth_7d` ≥ 0.50.
- ONGOING: condition holds on consecutive dates.
- END: first date the condition fails. All episodes stored, including 1-day and "failed" ones.
- Quantile P70, window 252d, breadth gate 0.50 — fixed here.

**Sector rotation episode (per sector, FULL_SECTOR layer):**
- START: sector median member `rank_velocity_7d` ≥ P70 of sector's own trailing 252d distribution
  (min_periods=60) **AND** sector breadth_7d (fraction of members with positive 7d rank velocity,
  computed from membership+features) ≥ 0.40.
- END / storage identical to band episodes.

**Chain-native breadth episode (per mapped chain):** count of Top-500 chain-native assets with
positive 7d rank velocity ≥ P70 of chain's trailing 252d distribution AND count ≥ 3 assets.

No episode start may be defined by any outcome measured after its start date (tested).

## 5. STATE CLASSIFICATION (capital routing; descriptive, data-separable only)

Daily states assigned by fixed rules on preregistered variables:
BTC 30d return, ETH 30d return, ETH−BTC 30d relative return, Top-10-ex-BTC/ETH median 30d
return vs BTC, mid-band (51-200) median 30d return vs BTC, small-band (201-500) same,
stablecoin 30d change, top500_breadth_30d, BTC dominance change 30d.

Priority order evaluated top-down; first match wins:
1. STABLECOIN_PARKING: stablecoin 30d change > +1% AND top500_breadth_30d < 0.40 AND BTC 30d ret < −10%
2. CAPITAL_EXIT: BTC 30d ret < −20% AND total crypto mcap 30d change < −20%
3. BROAD_RISK_EXPANSION: all of {BTC, ETH, large, mid, small} 30d rel-vs-BTC medians > 0 AND breadth_30d ≥ 0.60
4. NARROW_LEADERSHIP: large-alt median 30d rel > 0 but mid & small ≤ 0 AND breadth_30d < 0.45
5. LARGE_ALT_ROTATION: large(11-50) median 30d rel > +2% AND ETH 30d rel ≤ 0
6. MID_CAP_ROTATION: mid(51-200) median 30d rel > +2% AND large ≤ +2%
7. SMALL_CAP_ROTATION: small(201-500) median 30d rel > +2% AND mid ≤ +2%
8. ETH_BROADENING: ETH−BTC 30d > +5% AND large-alt 30d rel > 0
9. BTC_CONCENTRATION: BTC 30d ret > alt medians AND btc_dominance rising over 30d
10. MIXED_NO_CLEAR_ROUTE otherwise

State separability is then MEASURED (state-transition entropy, silhouette-free separation via
between/within variance ratio of defining variables). Overlap is reported honestly.

Thresholds above were chosen from round numbers BEFORE looking at outcomes.

## 6. UNCERTAINTY AND DEPENDENCE

- Date-block bootstrap: blocks of 20 calendar days, 500 resamples, seed 20260825, deterministic.
- Clustered (by entry-date block) Wilson CIs for transition probabilities.
- Effective episode counts reported next to raw counts everywhere.
- BH-FDR applied within each scan family (band cascade scans, sector scans, lead-lag scans).
  Promotion requires q < 0.25 plus criteria below.

## 7. REGIME SPLITS (fixed)

BTC 30d up/down (sign), realized vol tercile edges computed on full-sample terrain
(fixed quantiles 33/66 — descriptive), stablecoin expanding/contracting (sign of 30d change),
breadth broad/narrow (top500_breadth_30d ≥/< 0.50).

Subperiods (preregistered): 2020-06-01..2021-12-31, 2022, 2023, 2024, 2025-01-01..end.

## 8. PROMOTION STANDARD (mechanism → SUPPORTED)

SUPPORTED requires ALL of:
1. economic coherence (stated per mechanism);
2. raw observations ≥ 500 AND effective episodes ≥ 30;
3. consistent direction across subperiods (≥ 4 of 5 same sign/direction);
4. not dominated by one subperiod (no single subperiod contributes > 60% of effect mass);
5. survives BH-FDR where the family applies (q < 0.25);
6. causal construction verified (tests pass).

WEAK: meets 2–3 of 1–6 partially (documented). INCONCLUSIVE: insufficient episodes/power.
NOT_SUPPORTED: direction inconsistent or fails FDR badly (q ≥ 0.5) with adequate power.

## 9. LAYER INCREMENTAL VALUE (informational, not ML)

L1 rank-only → L2 +band → L3 +sector → L4 +breadth → L5 +stablecoin/chain flow → L6 +DEX/protocol context.
Value metric: reduction in conditional entropy of next-7D band-transition class versus base rate,
using empirical binned conditional probability tables (NO fitted model). A layer adds information
if ΔH > 0.005 nats out-of-sample-ish (last-third holdout slice, fixed split at 2/3 of dates).

## 10. METEORA

Aggregate TVL only, labeled PARTIAL_PROXY_ONLY everywhere. No pool-level claims. Pool-level analysis DEFERRED.

## 11. FORBIDDEN OUTPUTS

No PnL columns, no trade entries/exits, no portfolio weights, no alpha score, no strategy contracts.
