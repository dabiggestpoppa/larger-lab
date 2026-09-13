# ALT_MECH_2 — CONDITIONAL PROPAGATION, CAUSAL HIERARCHY & FIELD-GEOMETRY MAPPING

## PREREGISTRATION (fixed before any outcome analysis)

**Anchor:** MECH-1 `b3083df1` (decision `PASS_ALT_MECHANISM_ANATOMY`), merged `00e18779`.
**Branch:** `agent/crypto-quant-foundry`. **Base:** `2c36afd0…`.
**Scope:** terrain research only. NO strategy, PnL, optimization, ML, sizing, deployment.

All thresholds, windows, state definitions and sample rules below were fixed in this
document before the analysis script executed. Nothing below was chosen after seeing results.

---

## 1. Inputs (unchanged from DATA-1.1, re-verified at run start)

- `ALT_DATA_1_1_PIT_UNIVERSE.parquet` — 1,098,000 rows / 2,898 assets / 2,196 dates / 79 excluded gap dates
- `ALT_DATA_1_1_ASSET_MULTISCALE_FEATURES_V2.parquet` — V2 features only.
  V1 fields (prefixes `relative_return_vs_`, `rolling_beta_vs_`, `residual_return_vs_`,
  `expected_return_given_`) are FORBIDDEN. Relative returns are computed as
  `asset_return - market_return` from V2 return columns; no V1 field is consumed.
- `ALT_DATA_1_1_RANK_BAND_FEATURES.parquet`, `SECTOR_MEMBERSHIP`, `SECTOR_FEATURES`,
  `MARKET_TERRAIN_V2`, `PERP_ELIGIBILITY`, `GLOBAL_FLOW`, `CHAIN_FLOW`, `CHAIN_MAPPING`,
  `METEORA_ASSET_DAILY` (partial proxy only).
- DefiLlama flow dates normalized to end-of-day buckets; CMC→DefiLlama chain-name bridge
  (fixed engineering alias, as in MECH-1). `AVAILABLE_NEXT_DAY` shift applied to all
  DefiLlama flow features before they are used as information.

## 2. Common factors (Workstream A)

Fixed factor set (all causal, computed from PIT data only):

| Factor | Definition | Source |
|---|---|---|
| `mkt_ret_1d` | cap-weighted Top-500 1D return | feat (computed) |
| `btc_ret_1d` | BTC 1D return | terrain |
| `eth_ret_1d` | ETH 1D return | terrain |
| `vol_med` | median realized_volatility_30d across Top-500 | feat (computed) |
| `breadth` | top500_breadth_30d | terrain |
| `sc_change_30d` | stablecoin_change_30d (AVAILABLE_NEXT_DAY) | global flow |

Residualization: for each band-level series `m_b(t)` (see §3), fit OLS on a **trailing
252-day window, minimum 60 non-NaN observations**, take the residual. No future
information enters the fit. The residual series is `m_b^⊥(t)`.

Each band-pair relationship is produced in two forms:

- RAW: xcorr of `m_a(t)` vs `m_b(t+h)`
- RESIDUAL: xcorr of `m_a^⊥(t)` vs `m_b^⊥(t+h)`

Classification per (pair, metric):

- `STRUCTURAL_LEAD_LAG` — residual best-lag |corr| significant at p<0.05 (block bootstrap)
  AND raw best-lag has the same sign.
- `COMMON_FIELD_EFFECT` — raw significant but residual NOT significant (or sign flips).
- `WEAK` — neither raw nor residual significant at p<0.05.
- `AMBIGUOUS` — both significant but signs disagree.

## 3. Band series (Workstreams A/B)

From `RANK_BAND_FEATURES` (causal daily band aggregates), metrics:

- `ew_return_1d` (median_return_1d)
- `rank_velocity_7d` (median_rank_velocity_7d)
- `breadth_7d`
- `market_cap_share`

Bands: `1-10, 11-25, 26-50, 51-100, 101-200, 201-300, 301-500` (7 bands).

Band-pair universe (Workstream A): all ordered pairs `(a, b)` with `a` strictly higher
rank than `b` (`a<b` in index order) — 21 pairs. Metrics: `ew_return_1d`,
`rank_velocity_7d`, `breadth_7d`. xcorr lag range `[-14, 14]`, block bootstrap
`BOOT_N=500`, block `BLOCK_DAYS=20`, seed `20260826` (MECH-1 conventions).

## 4. State definitions (Workstreams B/G; fixed quantile/rule sets)

States are **single-condition** (no combinatorial explosion) and preregistered. A state
holds on day `t` using only information available at `t`:

| State id | Condition (day t) |
|---|---|
| `BTC_UP` | btc_return_30d > 0 |
| `BTC_DOWN` | btc_return_30d < 0 |
| `VOL_HIGH` | vol_med ≥ trailing-252 P70 (min 60 obs) |
| `VOL_LOW` | vol_med ≤ trailing-252 P30 (min 60 obs) |
| `BREADTH_EXPANDING` | top500_breadth_30d ≥ 0.50 |
| `BREADTH_CONTRACTING` | top500_breadth_30d < 0.50 |
| `SC_INFLOW` | stablecoin_change_30d > 0 |
| `SC_OUTFLOW` | stablecoin_change_30d < 0 |
| `CONC_RISING` | top-3 mcap share change over 7D > 0 (computed from feat) |
| `CONC_FALLING` | top-3 mcap share change over 7D < 0 |

Sample rule: a state must hold on **≥120 trading days** to be tested. States that fail
the sample rule are reported but not tested (recorded in 17_NULL_AND_FAILED_RESULTS.csv).

### Workstream B conditional lead/lag

Pairs: the 6 **adjacent** band pairs `(1-10→11-25, 11-25→26-50, 26-50→51-100,
51-100→101-200, 101-200→201-300, 201-300→301-500)`. Metrics: `ew_return_1d`,
`rank_velocity_7d`. Lags tested: `h ∈ {-7,-3,-1,1,3,7}` (positive h ⇒ earlier band leads
later band). p-values by circular-shift permutation (shift ≥ BLOCK_DAYS, 200 surrogates,
seeded). A relationship is `STATE_CONDITIONED` if the conditional best-lag differs in
sign or |lag| ≥ 3 from the unconditional best-lag at p<0.05. BH-FDR across all tested
(state, pair, metric, lag) cells.

## 5. Rank migration precursors (Workstream C)

Event: upward migration = day `t` where `band_code(asset, t) < band_code(asset, t-1)`
(band strictly improves). Window before event: `{1,3,7,14,30}` days. Precursor features
per event (all from V2 fields or computed):

- rank_velocity_7d, rank_acceleration_short
- rel_ret_1d = return_1d − mkt_ret_1d (computed)
- mcap_share_change_7d, volume_share_change_7d
- realized_volatility_30d (level)
- sector strength: median rank_velocity_7d of the asset's sector members that day
- chain strength: improving_share of the asset's chain that day (chain_native_aggregates)

Success definition: migration succeeded if asset is still in the higher band (or higher)
at `t+14`. Failed = fell back to original band by `t+14`.

Control sample: for each event, matched controls = same (date, starting band) assets that
did NOT migrate, sampled up to 5 per event (seeded). Precursor medians compared event vs
control per window; Wilcoxon rank-sum p (dependency-aware: p reported with cluster
counts, not treated as IID).

Report: median precursor values per (event band transition, window), event-vs-control
differences, success/failure rates per transition.

## 6. Leader-first sector propagation (Workstream D)

Sector episodes: reuse MECH-1 `detect_sector_episodes` (P70 trailing threshold +
breadth_7d ≥ 0.40 gate). Within each episode:

- Leader = highest mcap member at episode start (PIT).
- Peers = other members at episode start.
- Same-day beta: mean correlation of leader 1D return with peer 1D returns on the same
  day (episode days).
- Delayed propagation: mean correlation of leader 1D return at `t` with peer median 1D
  return at `t+k`, `k ∈ {1,3,7,14}`.
- TRUE_DELAYED_PROPAGATION if delayed mean corr at any k ≥ 3 significantly exceeds
  same-day beta (block bootstrap CI non-overlapping or paired test p<0.05) AND survives
  common-factor removal (leader/peer returns residualized on mkt_ret_1d).
- Leader persistence: across consecutive episodes of the same sector, fraction where the
  leader asset repeats (vs expected under random relabeling = 1/member_count).
- Follower confirmation: share of peers with positive rank_velocity_7d within 30D
  (reproduces MECH-1; not a strategy).

## 7. Chain / liquidity hierarchy (Workstream E)

Links tested (each direction, lags `h ∈ {1,3,7,14}`; permutation p as in §4):

1. global stablecoin change → chain TVL change (per chain)
2. chain TVL change → native-asset improving share (per chain)
3. chain TVL change → chain DEX volume change (per chain; total_dex_volume global proxy)
4. native improving share → native median rank velocity (per chain)
5. alternative orderings: TVL→stablecoin, native→TVL (to falsify the canonical ordering)

Chains: all chains with ≥120 days of merged (chain_flow × chain_native) data, top 12 by
coverage. Each link classified LEAD / LAG / CONTEMPORANEOUS / NO_RELATION by best-lag
significance (p<0.05). BH-FDR across all (chain, link, lag) cells. No causal claim
beyond ordering evidence.

## 8. Propagation failures / exhaustion signatures (Workstream F)

Fixed failure-pattern definitions (date-level, PIT):

| Pattern | Definition |
|---|---|
| `LEADER_WITHOUT_BREADTH` | top-3 mcap assets of a sector have positive 7D rel_ret but sector breadth_7d < 0.50 |
| `VELOCITY_WITHOUT_SHARE` | asset rank_velocity_7d > 0 but mcap_share_change_7d < 0 |
| `TVL_WITHOUT_PARTICIPATION` | chain TVL change 7D > 0 but chain improving_share 7D decline |
| `BREADTH_AND_CONCENTRATION` | top500_breadth_30d rising 7D AND top-3 mcap share rising 7D |
| `LOWER_RANK_ACCELERATION` | 301-500 band velocity rising while 1-10 band velocity falling (7D) |

For each pattern day: forward outcomes over `{7,14,30}` days — mkt return, band
11-25 vs 301-500 relative return, reversal probability (share of Top-500 with negative
30D return), and (for asset-level patterns) asset-level forward return. Contrasted
against complement days. Reported as descriptive conditional outcomes with counts.

## 9. Morphisms (Workstream G)

Object: daily routing-state sequence (MECH-1 `routing_analysis` states, 10 states).
N-gram motifs: all ordered 3-state sequences. A motif is `RECURRING` if it occurs
≥ 3 times in ≥ 2 of the 5 fixed subperiods (2020-21, 2022, 2023, 2024, 2025-26);
`PARTIALLY_RECURRING` if ≥ 3 times in exactly 1 subperiod; `CYCLE_SPECIFIC` otherwise.
Also test the generic form reservoir→infrastructure→leader→breadth→concentration→
exhaustion by mapping routing states to those archetypes and measuring mean sojourn
times + transition probabilities along the chain (descriptive only).

## 10. Hierarchy discovery (Workstream H)

Variance decomposition (descriptive, cross-sectional, not causal): for each sector with
≥ 120 active days, decompose the cross-section of member 7D returns on each day into
variance explained by (in order of entry):

1. global factor (mkt_ret_7d) — R²_global
2. chain factor (chain TVL change or chain median member return) — incremental R²_chain
3. sector factor (sector median return) — incremental R²_sector
4. residual = idiosyncratic share

Aggregated over days (median of daily R²). Output per sector AND per chain: share of
variance per layer. Also per-asset: best reference frame = the layer with the highest
incremental R² for that asset's sector-cluster. Independent islands = sectors where
R²_global < 0.05.

## 11. Causality ladder (Workstream I)

Every major claim is assigned a level from the fixed ladder:

| Level | Meaning |
|---|---|
| L0 | descriptive co-movement |
| L1 | temporal ordering (x precedes y) |
| L2 | conditional lead-lag (state-conditioned) |
| L3 | robust to common-factor removal |
| L4 | robust across subperiods / regimes |
| L5 | supported mechanism (MECH-1 promotion standard) |
| L6 | quasi-causal evidence (only with explicitly defended assumptions) |

Assignment is mechanical: a claim inherits the highest level for which all lower tests
pass. Levels are recorded in `11_CAUSALITY_LADDER.csv` with the evidence row for each.

## 12. Information flow (Workstream J)

Transfer entropy on selected pairs (fixed): `SC change → band 11-25 velocity`,
`SC change → top500 breadth`, `chain TVL → native improving share` (top chain),
`leader return → peer median return` (aggregated across episodes). Discretization:
terciles (within-series). TE = I(target_{t+1}; source_t | target_t) at lag 1. Null:
200 surrogates, source block-shuffled (block=20D, seeded); p = fraction of surrogates
with TE ≥ observed. Positive TE only claimed at p<0.05 and after §2 common-factor
conditioning (residualized series). Reported as nats with surrogate p.

## 13. Multiple-testing & dependence control

- Every Workstream with ≥ 10 tested cells gets BH-FDR across its cells; q<0.05 (or 0.10
  where preregistered for exploratory scans — default q<0.05) is required for promotion.
- Dependence: block bootstrap (20D) for correlations; permutation surrogates with
  block shifts for TE; cluster/effective counts reported for event studies; cross-
  sectional rows are never treated as IID.
- All tested cells are retained in outputs (no result shopping); nulls go to
  `17_NULL_AND_FAILED_RESULTS.csv`.

## 14. Subperiod stability

Fixed partition (as MECH-1): 2020-21, 2022, 2023, 2024, 2025-26. For each promoted
relationship: direction recorded per subperiod; promotion requires the effect to be
present with the same sign in ≥ 3 of 5 subperiods (for §5/§6/§7) — otherwise
`UNSTABLE` flag in `18_SUBPERIOD_STABILITY.csv`.

## 15. Test-count reconciliation

Exact counts of hypotheses, state conditions, lags, windows, groups, and total
statistical tests are recorded in `19_TEST_COUNT_RECONCILIATION.md` from run-time
counters, not reconstructed afterwards.

## 16. Stop / fail conditions

- STOP if truth lock fails or PIT integrity breaks.
- FAIL_ALT_PROPAGATION_EVIDENCE if §7 chain hierarchy collapses after common-factor
  removal, or results are driven by one cycle, or multiple-testing correction eliminates
  all promoted structure.
- BLOCKED_DATA_INSUFFICIENT if required data (chain flow, stablecoin, sectors) is
  missing or unreliable.

## 17. Artifact numbering

`01_PREREGISTRATION.md` … `21_DECISION.md` as required, plus `plots/` figures and
`scripts/`, `tests/`, `_cache_*` (transient, not committed).

## 18. No strategy design

No entry/exit thresholds, no sizing, no PF, no backtesting, no ML predictors, no
deployment. The final decision is about terrain structure only.
