# ALT_MECH_3 — CHAIN-LIQUIDITY ANATOMY, REGIME-ROUTING & CONCENTRATION PIVOT MAPPING

## PREREGISTRATION (fixed before any outcome analysis)

**Anchors:** MECH-1 `b3083df1` (PASS_ALT_MECHANISM_ANATOMY) · MECH-2 `8636370a`
(PASS_ALT_TERRAIN_WITH_LIMITATIONS) · field constitution `d030a1c1` · field
definitions `bae722a1` · idea update `34b592f7` · lower-field capture `85030bc4` ·
dual-agent architecture `04a09016`.
**Branch:** `agent/crypto-quant-foundry`. **Role:** AGENT 1 — MAIN FIELD CARTOGRAPHER.
**Scope:** terrain research only. NO strategy, PnL, optimization, ML, sizing, deployment.

All thresholds, windows, state definitions, classification rules and sample rules
below were fixed in this document BEFORE the analysis script executed. Nothing was
chosen after inspecting outcomes.

---

## 1. Inputs (unchanged from DATA-1.1; re-verified at run start)

Same canonical set as MECH-1/MECH-2:

- `ALT_DATA_1_1_PIT_UNIVERSE.parquet` — 1,098,000 rows / 2,898 assets / 2,196 dates / 79 excluded gap dates
- `ALT_DATA_1_1_ASSET_MULTISCALE_FEATURES_V2.parquet` — V2 features only; V1 prefixes
  (`relative_return_vs_`, `rolling_beta_vs_`, `residual_return_vs_`,
  `expected_return_given_`) are FORBIDDEN. Relative returns computed from V2 columns only.
- `ALT_DATA_1_1_RANK_BAND_FEATURES.parquet`, `SECTOR_MEMBERSHIP`, `SECTOR_FEATURES`,
  `MARKET_TERRAIN_V2`, `PERP_ELIGIBILITY`, `GLOBAL_FLOW`, `CHAIN_FLOW`, `CHAIN_MAPPING`,
  `METEORA_ASSET_DAILY` (aggregate proxy only; pool-level history remains DEFERRED).
- DefiLlama flow dates normalized to end-of-day buckets; CMC→DefiLlama chain-name bridge
  (fixed engineering alias, as MECH-1/2); `AVAILABLE_NEXT_DAY` shift applied to all
  DefiLlama flow features before use.

Truth lock identical to MECH-1: rows/assets/dates/gap counts, rank unchanged, V2
benchmark identity valid, flow files present. If any check fails: STOP.

## 2. Chain-liquidity variable family (Workstream A)

Observable per-chain / global coordinates (all causal):

| Id | Variable | Source |
|---|---|---|
| `tvl_lvl` | log chain TVL level | chainflow |
| `tvl_chg1/7/30` | chain TVL change 1D/7D/30D (AVAILABLE_NEXT_DAY) | chainflow |
| `tvl_share` | chain TVL share of total tracked TVL | chainflow |
| `imp_share` | native improving_share = n_improving/n_top500 | chain_native_aggregates |
| `vel7` | native median rank velocity 7D | chain_native_aggregates |
| `mcshare` | native market-cap share sum | chain_native_aggregates |
| `ret_brd1` | native 1D return breadth | chain_native_aggregates |
| `sc_chg7/30` | global stablecoin change 7D/30D | global flow |
| `dex_chg7` | global DEX volume change 7D | global flow |
| `fees_chg7` | global fees change 7D | global flow |

NOT OBSERVABLE (documented in 03_OBSERVATION_LIMITS.md, not synthesized):
per-chain stablecoin supply, bridge in/out, perp OI, lending TVL, staking flows,
active addresses, exchange in/outflows, wallet identities.

**Redundancy classification** (per pair of series within a chain, pooled across top-12
chains by coverage; Spearman correlation, block-bootstrap p):

| |r| | Class |
|---|---|---|
| ≥ 0.85 | REDUNDANT_PROXY |
| 0.60–0.85 | PARTIAL_PROXY |
| 0.40–0.60 | LOCAL_COORDINATE |
| 0.20–0.40 | DISTINCT_INFORMATION |
| < 0.20 | CANDIDATE_DISTINCT (needs WS J audit) |

Family-level redundancy: after pairwise classification, variables that are
REDUNDANT_PROXY to one another and to no distinct coordinate form an informational
family (MERGE candidate); variables with no |r| ≥ 0.60 partner are candidate
independent coordinates.

## 3. Chain-liquidity perturbation (Workstream B)

Target pathway (MECH-2 supported): `chain TVL → native improving share / velocity`.
For each of the top-12 chains and each link in
{`tvl_chg7→imp_share`, `tvl_chg7→vel7`, `sc_chg30→tvl_chg7`, `tvl_chg7→dex_chg7`,
`vel7→imp_share`}, lags h ∈ {1,3,7,14}, measure best-lag corr under ablations:

1. BASE — raw series.
2. `-BETA` — both series residualized on (mkt_ret_1d, btc_ret_1d, eth_ret_1d, vol_med)
   via trailing 252D OLS (min 60 obs), as MECH-2 A.
3. `-SC` — both series residualized on stablecoin_change_30d (trailing OLS).
4. `-DEX` — both series residualized on dex_volume_change_7d (trailing OLS).
5. `-NATIVE_RET` — replace imp_share outcome with ret_brd1 (drop price-ish native return).
6. `LOO_CHAIN` — recompute the pooled (across chains) best-lag corr excluding each chain.
7. `LOO_CYCLE` — recompute pooled corr excluding each of the 5 subperiods.

Per (chain, link) classification:

- SURVIVES — best-lag corr significant at p<0.05 in BASE and in ≥ 4 of the 5
  single-ablation variants (`-BETA`,`-SC`,`-DEX`,`-NATIVE_RET`, plus BASE), same sign.
- WEAKENED — significant in BASE and ≥ 2 ablations, same sign, |corr| drop ≥ 0.15 in any.
- LOCAL — significant only in ≥ 1 chain but not pooled, or only in one subperiod class.
- DISSOLVES — not significant after `-BETA`, or sign flips in ≥ 2 ablations.
- NO_RELATION — not significant in BASE.

LOO_CHAIN / LOO_CYCLE report the range (min–max) of pooled corr across removals;
survival requires the range to exclude 0 with same sign.

## 4. Multi-view chain reconstruction (Workstream C)

Phenomenon: chain expansion state `E_t = (tvl_chg7 > 0)` per chain-day (AVAILABLE_NEXT_DAY).

Views (all at day t, causal):

- GLOBAL: mkt_ret_7d, top500_breadth_30d
- CHAIN: tvl_chg7, tvl_share
- SECTOR: median return_7d of the chain's dominant sector (sector with max member
  mcap-share among chain members that day)
- NATIVE: imp_share, vel7
- RANK: band 11-25 vs 301-500 median velocity spread (from rank-band features)

Per chain and per view: mean P(E | view above vs below its trailing median) and
point-biserial corr with E. **Reconstruction score** for the view set: incremental R²
of an OLS linear-probability model on E with views added in the fixed order
GLOBAL → CHAIN → SECTOR → NATIVE → RANK (5 steps). Agreement matrix: pairwise
fraction of days views agree on E. **Disagreement inventory** (fixed definitions):

- TVL_UP_NATIVE_WEAK: E=1 and vel7 < 0
- SC_UP_DEX_WEAK: sc_chg7 > 0 and dex_chg7 < 0
- BREADTH_UP_FLOW_DOWN: top500_breadth_30d rising and chain TVL falling
- NATIVE_UP_TVL_DOWN: vel7 > 0 and tvl_chg7 < 0

Counts and forward outcomes (7/14/30D mkt ret) recorded; disagreement days are NOT
dropped — they are candidate hidden-state / measurement-lag observations.

## 5. Regime routing flip map (Workstream D)

Relationships (from MECH-2 surviving structure; 9 base relationships):

1. 6 adjacent band-pair rank-velocity leads at h=+1:
   (1-10→11-25), (11-25→26-50), (26-50→51-100), (51-100→101-200),
   (101-200→201-300), (201-300→301-500)
2. chain TVL→native improving share (pooled top-12 chains), h=+1
3. chain TVL→stablecoin change (pooled), h=+7
4. stablecoin change→top500 breadth, h=+1

States (single-condition; ≥ 120 days required; else INSUFFICIENT_SAMPLE):

| State | Condition (day t) |
|---|---|
| BTC_UP / BTC_DOWN | btc_return_30d > 0 / < 0 |
| ETH_STRONG / ETH_WEAK | eth_btc_relative_return_30d > 0 / < 0 |
| VOL_HIGH / VOL_LOW | vol_med ≥ P70 / ≤ P30 (trailing 252D) |
| BREADTH_EXPANDING / CONTRACTING | top500_breadth_30d ≥ 0.50 / < 0.50 |
| CONC_RISING / FALLING | top3_share_chg7 > 0 / < 0 |
| SC_INFLOW / OUTFLOW | stablecoin_change_30d > 0 / < 0 |
| CHAIN_EXPANDING / CONTRACTING | median chain tvl_chg7 (across top-12) > 0 / < 0 |
| RISK_ON / RISK_OFF | mkt_ret_30d > 0 / < 0 |

Per (relationship, state) cell: corr at the relationship's unconditional best lag,
permutation p (block shift, 200 surrogates, seeded), sample count. Classification vs
unconditional best-lag corr:

- SAME_SIGN — same sign, |Δcorr| < 0.15
- GAINED — same sign, |corr| gain ≥ 0.15
- REVERSED — opposite sign (regardless of magnitude)
- LOST — sign same but no longer significant (p ≥ 0.05)
- CHANGED_LAG — best |lag| differs by ≥ 3 days (measured at fixed candidate lags
  {1,3,7,14} for flow links, {1,3,7} for band links)

BH-FDR across all tested (relationship, state) cells. A REVERSED or GAINED cell at
q<0.05 is a **routing flip**. Stability: flip must recur in ≥ 3 of 5 subperiods to be
promoted (recorded in 08).

## 6. Concentration pivot anatomy (Workstream E)

State series: MECH-1 routing states (daily). `BTC_CONCENTRATION` = the field's pivot
state (MECH-2). Events (causal — state at t uses info at t only):

- ENTRY event: day t with state(t-1) ≠ BTC_CONCENTRATION and state(t) = BTC_CONCENTRATION.
- EXIT event: day t with state(t-1) = BTC_CONCENTRATION and state(t) ≠ BTC_CONCENTRATION.

Precursor windows (mean over trailing window, shifted to end strictly before t):
{1, 3, 7, 14, 30} days. Precursor variables (all PIT):

- btc_dominance change, btc_return_30d, btc_return_7d
- top3_share and its 7D change
- top500_breadth_30d, top500_dispersion_30d
- stablecoin_change_30d, eth_btc_relative_return_30d
- total_alt_share, eth_share
- vol_med, median chain tvl_chg7

Controls: for each event date, 5 matched non-event dates with the same month-year and
same starting routing-state family (concentration for exit controls, non-concentration
for entry controls), seeded. Report event vs control medians per window; Wilcoxon
rank-sum p (dependency-aware: cluster counts reported, not treated as IID).

Release classification at exit (WS E): next state label at t+1, t+3, t+7 and the
**destination state** = first state occupied for ≥ 5 consecutive days after exit.
Candidate release types: ETH_BROADENING, LARGE_ALT_ROTATION, MID_CAP_ROTATION,
SMALL_CAP_ROTATION, BROAD_RISK_EXPANSION, MIXED_NO_CLEAR_ROUTE, CAPITAL_EXIT,
STABLECOIN_PARKING, NARROW_LEADERSHIP, REENTRY (back to concentration within 7D).

## 7. Pivot boundary (Workstream F)

For each candidate coordinate (btc_dominance, top3_share, top500_breadth_30d,
top500_dispersion_30d, stablecoin_change_30d, eth_btc_relative_return_30d,
total_alt_share, vol_med, median chain tvl_chg7, mkt_ret_30d): bin the coordinate into
5 fixed quantile bins (quintiles over the full sample, computed once). For each bin
measure:

- P(exit concentration within 7D | in concentration, bin)
- P(enter concentration within 7D | not in concentration, bin)

Descriptive transition surface per coordinate = the bin→probability profile.
**Boundary detected** for a coordinate if the Spearman rank correlation between bin
index and probability has |ρ| ≥ 0.80 AND the extreme bins differ by ≥ 2× (max/min ≥ 2
with min > 0). **Stability:** boundary must be detected in ≥ 3 of 5 subperiods
(ρ sign consistent). No thresholds are taken from intuition; quintiles are fixed.

## 8. Release route map (Workstream G)

For every EXIT event: record starting state coordinates (precursor medians over
[-7,-1]), first changed observable (the precursor whose [-3,-1] change is largest in
|z| relative to its own trailing distribution), route (destination state label),
time-to-route (days from exit to destination occupation), concentration duration
before exit, and eventual 30D outcome (mkt ret, breadth). Route hierarchy = routes
sorted by frequency and by median time-to-route. **Route predictability** (terrain
inference only): fraction of exits whose first-changed observable matches the modal
first-changed observable of their eventual route class.

## 9. Information plateau (Workstream H)

Three phenomena:

1. chain expansion E (as WS C)
2. routing flip (WS D promoted flips)
3. concentration exit within 7D

Fixed variable addition order (same for all three):
[mkt_ret_30d, btc_return_30d, top500_breadth_30d, stablecoin_change_30d,
median chain tvl_chg7, top3_share, vol_med, eth_btc_relative_return_30d].
Incremental R² of OLS linear-probability models with variables added in this order
(trailing-window evaluation on a 70/30 temporal split, fixed split at 70th percentile
date). **INFORMATION_PLATEAU** = first step where incremental R² < 0.005. Plateau
variable count and the plateau R² are recorded per phenomenon.

## 10. Field plateau (Workstream I)

Fixed plateau state definitions (date-level):

| Plateau | Definition |
|---|---|
| P1 CHAIN_LIQ_NO_NATIVE | chain tvl_chg7 > 0 AND vel7 < 0 (per chain-day, pooled) |
| P2 VELOCITY_NO_BREADTH | band 11-25 median velocity rising 7D AND top500_breadth_30d |chg| < 0.01 |
| P3 CONC_NO_ROUTE | |top3_share_chg7| < 0.005 AND state ∈ {BTC_CONCENTRATION, MIXED_NO_CLEAR_ROUTE} |

For each plateau episode (contiguous run ≥ 3 days): duration, the variable whose
[-3,-1] change is largest before release (plateau end), release direction
(continuation = same-sign forward momentum vs reversal), forward mkt ret 7/14/30D.
**Release trigger candidates** = modal largest-changed variable before release per
plateau type.

## 11. Primitive candidate audit (Workstream J)

Candidate families (global daily series; fixed list):

| Candidate | Proxy |
|---|---|
| DEPLOYABLE_LIQUIDITY | stablecoin_total_mcap level + change_30d |
| CAPITAL_CONCENTRATION | top3_share |
| BREADTH | top500_breadth_30d |
| RANK_DISPERSION | top500_dispersion_30d |
| VOLATILITY | vol_med |
| CHAIN_LIQUIDITY | median chain tvl_chg7 |
| DEX_ACTIVITY | dex_volume_change_7d |
| ETH_RELATIVE | eth_btc_relative_return_30d |

Tests per candidate:
(a) redundancy: max |Spearman corr| with other candidates;
(b) materiality: ΔR² when removed from the WS H concentration-exit reconstruction
    (full-variable R² minus leave-one-out R²);
(c) substitution resistance: ΔR² when replaced by its nearest proxy;
(d) recurrence: appears among the top-3 contributors (by |beta| in full model) in
    ≥ 3 of 5 subperiods.

Classification (fixed rule):
- GLOBAL_CANDIDATE_PRIMITIVE: (b) ≥ 0.005 AND (a) < 0.85 AND (d) true
- LOCAL_PRIMITIVE: (b) ≥ 0.005 AND (d) false
- REDUNDANT: (a) ≥ 0.85
- NOT_PRIMITIVE: (b) < 0.005
- UNRESOLVED: otherwise

## 12. Topology readiness (Workstream K)

Graph: nodes = top-12 chains (by merged coverage); edge (i,j) if
|corr(vel7_i, vel7_j)| ≥ 0.50 over the full sample. Compute per subperiod and full
sample: connected components (union-find), density, articulation points/bridges
(Tarjan), and component-membership persistence (Jaccard between consecutive
subperiods). **TOPOLOGY_EARNED = YES** if the full-sample graph has a component with
≥ 3 nodes that persists (≥ 2 of its members co-clustered) in ≥ 3 of 5 subperiods AND
graph density < 0.9. Otherwise NO. No persistent homology — it is only earned if
simple graph structure supports it.

## 13. Dynamical-system readiness (Workstream L)

On the 10-state routing series: per-subperiod transition matrices. Metrics:
self-transition stability (std of diagonal entries across subperiods), basin test —
P(stay in {BTC_CONCENTRATION, MIXED_NO_CLEAR_ROUTE} | in basin) per subperiod,
hysteresis test — exit-route distribution conditioned on entry route (chi-square p
with counts), and sojourn distributions. **Attractor-like** if basin self-transition
≥ 0.60 in all 5 subperiods AND entry-route-dependence of exit route is detectable
(chi-square p < 0.05 with ≥ 20 exit events).

## 14. Morphism survival (Workstream M)

Read MECH-2 `12_MORPHISM_CATALOG.csv` (committed). Distinguish the RECURRING motifs
(16% of MECH-2) from CYCLE_SPECIFIC on: fraction that are self-loops
(s1==s2==s3), fraction involving BTC_CONCENTRATION, mean occurrences, and mean
subperiod coverage. **CATEGORY_STYLE_FORMALIZATION_EARNED = YES** if ≥ 70% of
RECURRING motifs are self-loops or concentration-pivot loops AND the recurring set
spans ≥ 3 subperiods. Relational-structure check: do recurring motifs preserve order
of the generic form reservoir→infra→leader→breadth→speculative→concentration→exit
(mapped via routing-state archetype table fixed below)? Report fraction preserving
order.

Archetype map (fixed): STABLECOIN_PARKING→reservoir; CAPITAL_EXIT→exit;
BROAD_RISK_EXPANSION→breadth; NARROW_LEADERSHIP→leader; ETH_BROADENING→breadth;
LARGE_ALT_ROTATION→leader; MID_CAP_ROTATION→breadth; SMALL_CAP_ROTATION→speculative;
BTC_CONCENTRATION→concentration; MIXED_NO_CLEAR_ROUTE→mixed.

## 15. Observation limits (Workstream N)

Documented in 03_OBSERVATION_LIMITS.md: for every major finding, classify
DIRECTLY_OBSERVED / INDIRECTLY_INFERRED / PARTIALLY_OBSERVED / UNOBSERVED. No gap is
filled with narrative. Unavailable: per-chain stablecoin, bridges, perp OI, lending,
staking, addresses, exchange flows, wallet identities, private treasury/OTC flows.

## 16. Agent-2 promotion inbox (Workstream O)

Read `crypto_foundry/derivatives/` (if a `PROMOTION_CANDIDATE.md` exists) and the
committed lower-field capture `85030bc4`. For each candidate classify:
ACCEPT_FOR_CANONICAL_TEST / REJECT_INSUFFICIENT / DUPLICATE / CONFLICTS_WITH_CANONICAL /
NEEDS_DATA / DEFER. Accepted candidates are NOT merged automatically; they are
independently validated before any canonical promotion. If no candidates exist, the
review records that explicitly.

## 17. Multiple-testing & dependence control

- BH-FDR applied within each workstream family (A, B, D, E precursor tests);
  q<0.05 for promotion, q<0.10 recorded as marginal.
- Block bootstrap (20D) for correlations; block-shift permutation surrogates for
  conditional tests; effective/cluster counts for event studies; cross-sectional rows
  never treated as IID.
- All tested cells retained in outputs (no result shopping); nulls to
  20_NULL_AND_FAILED_RESULTS.csv.

## 18. Subperiod stability

Fixed partition (MECH-1): 2020-21, 2022, 2023, 2024, 2025-26. Promoted claims
require same-sign presence in ≥ 3 of 5 subperiods (per-workstream rule above);
otherwise flagged UNSTABLE.

## 19. Test-count reconciliation

Exact counts (hypotheses, states, lags, windows, groups, total tests) recorded at
runtime into 23_TEST_COUNT_RECONCILIATION.md from counters, not reconstructed after.

## 20. Stop / fail / decision conditions

- STOP if truth lock fails or PIT integrity breaks.
- BLOCKED_ALT_MECH3_DATA if required flow data is missing/unreliable.
- FAIL_ALT_MECH3_STRUCTURE if chain-liquidity support collapses under basic
  perturbation, or routing flips are unstable artifacts, or pivot has no reproducible
  precursor geometry, or primitives collapse into redundant beta proxies.
- PASS_ALT_MECH3_WITH_LIMITATIONS if structure survives with documented limits.
- PASS_ALT_FIELD_PRIMITIVE_MAP requires ≥ 1 GLOBAL_CANDIDATE_PRIMITIVE AND ≥ 3
  routing flips stable across subperiods AND concentration pivot anatomy with
  reproducible entry/exit geometry AND nulls preserved.

## 21. Artifacts

`01_PREREGISTRATION.md` … `25_DECISION.md` as required, plus `plots/` figures and
`scripts/`, `tests/`, `_cache_*` (transient, not committed).

## 22. No strategy design

No entry/exit thresholds, no sizing, no PF, no backtesting, no ML predictors, no
deployment. The decision is about terrain structure only.
