# ALT_MECH_4 — PIVOT RELEASE GATES, STALL RELEASE, PATH MEMORY & PROPAGATION DEPTH

## PREREGISTRATION (fixed before any outcome analysis)

**Anchors:** MECH-1 `b3083df1` (PASS_ALT_MECHANISM_ANATOMY) · MECH-2 `8636370a`
(PASS_ALT_TERRAIN_WITH_LIMITATIONS) · MECH-3 `23ff4c12` (PASS_ALT_MECH3_WITH_LIMITATIONS)
· dual-agent `04a09016` · field constitution `d030a1c1` · definitions `bae722a1` ·
idea update `34b592f7` · lower-field capture `85030bc4`.
**Branch:** `agent/crypto-quant-foundry`. **Role:** AGENT 1 — MAIN FIELD CARTOGRAPHER.
**Scope:** terrain / mechanism research ONLY. NO strategy, PnL, optimization, ML
predictors, sizing, deployment. All thresholds, definitions, event rules, sample
rules and model specifications below were fixed BEFORE the analysis script executed.

---

## 1. Empirical parent and canonical event set

The canonical event set is MECH-3's pivot objects, reproduced from the same daily
routing-state series (MECH-1 `assign_routing_state_frame`, MECH-3 `build_daily`):

- Concentration state: `BTC_CONCENTRATION` (daily, PIT).
- **EXIT event** (release): day `t` with state(t-1) = BTC_CONCENTRATION and
  state(t) != BTC_CONCENTRATION. Expected canonical count: **125** (MECH-3).
- **ENTRY event**: day `t` with state(t-1) != BTC_CONCENTRATION and state(t) =
  BTC_CONCENTRATION. Expected canonical count: **126** (MECH-3).
- **Destination** of an exit: first state occupied for >= 5 consecutive days after
  exit (MECH-3 canonical label; NOT altered). A destination of BTC_CONCENTRATION
  within the post-exit window is the **REENTRY/SNAPBACK** label.

Event reconciliation (03) verifies that the re-derived event ledger reproduces
MECH-3's `09_CONCENTRATION_ENTRY_EVENTS.parquet` / `10_CONCENTRATION_EXIT_EVENTS.parquet`
(126 / 125). Any mismatch is documented; MECH-3's labels remain canonical.

## 2. Workstream A — release-event reconstruction and post-release sequence

For every exit event, build the PIT-safe ledger (04) with:
event_id, entry date, exit date, episode duration (days in concentration before
exit), route into concentration (state preceding the entry), prior states
(-1/-3/-7 relative to entry), state age, release date, first destination, days to
destination, 5D canonical confirmation, cycle (subperiod), regime flags at exit
(BTC_UP/DOWN, VOL_HIGH/LOW, CONC_RISING/FALLING, BREADTH_EXPANDING/CONTRACTING,
ETH_STRONG/WEAK, RISK_ON/OFF), observable values at t (btc_ret30, btc_ret7,
top3_share, top3_share_chg7, breadth30, disp30, sc_chg30, eth_rel30, alt_share,
vol_med, chain_tvl_med_chg7), availability masks (which observables are non-null).

Post-release sequence (05): state at t+1, t+3, t+5, t+7, t+14, t+30 after exit.
Staged-propagation classification (fixed rules, evaluated over the 30D post-exit
window, state series only):

| Pattern | Rule |
|---|---|
| CONC_DIRECT_ALT | first >=5D destination is ALT family {ETH_BROADENING, LARGE_ALT_ROTATION, MID_CAP_ROTATION, SMALL_CAP_ROTATION} |
| CONC_VIA_BROAD_RISK | BROAD_RISK_EXPANSION occurs in (t, t+30] before the ALT destination |
| CONC_BROAD_RISK_ONLY | destination = BROAD_RISK_EXPANSION (no ALT in 30D) |
| CONC_MIXED | destination = MIXED_NO_CLEAR_ROUTE |
| CONC_REENTRY | destination = BTC_CONCENTRATION |
| CONC_DEFENSIVE | destination in {CAPITAL_EXIT, STABLECOIN_PARKING} |
| UNRESOLVED | no >=5D state in 30D |

Test (WS A core): are BROAD_RISK and ALT competing routes or is BROAD_RISK an
intermediate depth? Metrics: (a) P(ALT within 30D | BROAD_RISK seen first) vs
P(ALT within 30D | BROAD_RISK never seen); (b) distribution of days-from-exit to
ALT conditional on BROAD_RISK presence; (c) median time-to-destination per route.
Classification: COMPETING_ROUTES / INTERMEDIATE_DEPTH / UNRESOLVED.

## 3. Workstream B — hierarchical release gates

n = 125 exits; class imbalance is severe (ALT family 9, defensive 2). NO flat
multiclass ML. Hierarchical binary questions only, with simple L2-regularized
logistic regression on a FIXED feature set (pre-exit precursor medians over
[-7,-1]: btc_ret30, btc_ret7, top3_share, top3_share_chg7, breadth30, disp30,
sc_chg30, eth_rel30, vol_med, chain_tvl_med_chg7 — 10 features, z-scored on the
training split). Fixed gate cascade:

| Gate | Split | n (expected) |
|---|---|---|
| G1 ESCAPE vs SNAPBACK | destination != BTC_CONCENTRATION vs == | 73 vs 52 |
| G2 STABLE DESTINATION | among escapers: MIXED vs PROPAGATION vs DEFENSIVE | 44 vs 27 vs 2 |
| G3 PROPAGATION | BROAD_RISK+ALT family vs (REENTRY+MIXED) | 27 vs 96 |
| G4 DEPTH | among propagation: BROAD_RISK (18) vs ALT family (9) | 18 vs 9 |

G2 is evaluated as two binary comparisons (MIXED vs PROPAGATION, and DEFENSIVE
reported descriptively only — n=2). G4 treated as exploratory (n=9): report
effect sizes and permutation p only, no promotion.

Evaluation per gate: held-out log loss, Brier score, calibration (predicted vs
observed decile means), AUC; 5-fold temporal CV (fixed split by date order);
permutation null (shuffle labels 200x, seeded); leave-one-subperiod-out and
leave-one-cycle-out; episode bootstrap (resample episodes, block 20D) for CIs on
AUC/log-loss differences. NO threshold selection on outcomes; decision rule =
G1/G3 log-loss improvement over intercept-only model with permutation p < 0.05.

## 4. Workstream C — present state vs path memory

Nested representations on the G3 outcome (PROPAGATION vs not; n=125):

- **M0**: current observable state only (the 10 features above).
- **M1**: M0 + route into concentration (one-hot of the pre-entry state among the
  9 non-concentration routing states; collapsed to 3 fixed categories:
  RISK_STATE {BROAD_RISK_EXPANSION}, MIXED, OTHER — fixed before outcomes).
- **M2**: M1 + state age (log concentration-duration) + number of boundary
  oscillations (entries/exits into concentration in the prior 180D, capped at 5).
- **M3**: M2 + episode trajectory: entry velocity (btc_ret30 change 7D before
  entry), prior 1D/3D/7D weakness (precursor means over [-7,-1] as in MECH-3 WS E),
  concentration slope/curvature (top3_share_chg7 linear fit slope over the
  episode; squared term), prior failed release attempts (exits that re-entered
  within 7D earlier in the same episode).

Primary question: does knowing HOW the field entered concentration add stable
information after present state? Metrics: held-out log loss / Brier delta
(Mk vs M0), conditional mutual information I(path | state; outcome) via
discretized contingency (3-bin quantiles) with bias-corrected estimate, episode
bootstrap CI, permutation test on path features only (shuffle M1-M3 features,
200x). If path-history improvement is in-sample only: retain
HYSTERESIS_DESCRIPTIVE, and classify HYSTERESIS_PREDICTIVE_MECHANISM as
DISSOLVED unless held-out permutation p < 0.05 AND delta-Brier >= 0.005.

## 5. Workstream D — Markov vs semi-Markov (duration dependence)

On the daily concentration-state series (all 2,196 days):
- Hazard / duration audit: for each concentration spell (contiguous run), record
  duration; empirical hazard h(a) = P(exit at age a | survived to a), binned at
  ages {1, 2, 3, 4, 5-7, 8-14, 15-30, 31+}.
- Test 1 (escape probability): P(exit within 7D | age bin) across bins — Kruskal-
  Wallis on age-bin exit rates; trend via Spearman rho of bin vs rate.
- Test 2 (destination by age): destination distribution for short (< median) vs
  long (>= median) spells — chi-square with exact permutation p (n >= 20).
- Test 3 (reentry hazard): hazard of exit-and-reentry (destination =
  BTC_CONCENTRATION) vs age bin.
- Test 4 (broad-risk clustering): do BROAD_RISK destinations cluster at specific
  episode ages? Compare age-at-release distribution for BROAD_RISK vs others
  (ranksums).
- Semi-Markov EARNED if: Test 1 trend |rho| >= 0.50 OR Test 2 p < 0.05 AND the
  duration-conditioned model beats the current-state model on held-out G1/G3 log
  loss by >= 0.005 with permutation p < 0.05. Otherwise duration is descriptive.
- NO HMM unless the above leaves stable structured residuals (checked by residual
  autocorrelation of a duration-conditioned model; reported, not promoted).

## 6. Workstream E — stall -> activation (P1 CHAIN_LIQ_NO_NATIVE)

Plateau P1: per chain-day, tvl_chg7 > 0 AND vel7 < 0 (MECH-3 WS I definition),
pooled over the top-12 chains by coverage, episodes = contiguous runs >= 3 days.
Expected ~797 episodes (MECH-3). Questions (all fixed before outcomes):

1. **Activation-first**: does native improving-share change BEFORE plateau end?
   Event study on episode end: imp_share change over [-5,-1] vs [-1,+3]
   (pre-release vs post-release), and vs matched controls (same chain, same
   subperiod, non-plateau days, seeded 5:1).
2. **Conditional information**: logistic on release-within-3D (episode end within
   3D) with base controls {tvl_chg7, btc_ret30, vol_med, breadth30, eth_rel30,
   in_conc_flag} vs base + {imp_share, vel7}. Delta log loss, permutation p.
3. **Velocity parallel**: repeat (1)-(2) with vel7 in place of imp_share.
4. **Capacity vs activation**: is tvl_chg7 level uninformative about release
   after native variables are controlled (delta log loss of removing tvl from
   base+activation model)?
5. **Release coordinate -> destination**: group P1 releases by first-changed
   coordinate (MECH-3 WS I triggers) and compare 7D/30D forward routing-state
   outcomes (reentry/mixed/broad/alt share).
6. **P1 x concentration overlap**: fraction of P1 episode-days where the global
   state is BTC_CONCENTRATION; if P1 ends before a concentration exit, does it
   precede it (lead: median days from P1 end to next concentration exit within
   30D)? Compare P1-end-to-conc-exit vs random-day-to-conc-exit (permutation).

Classification (fixed): if (1) AND (2) hold -> NEW_NODE NATIVE_ACTIVATION (and
NEW_NODE CAPACITY_WITHOUT_ACTIVATION if (4) confirms tvl adds nothing after
native); if (6) shows P1 systematically precedes concentration exits ->
consider MERGE of P1-stall with the concentration-entry precursor chain; if (1)
and (2) fail -> DISSOLVE the capacity/activation interpretation (NULL).

## 7. Workstream F — release initiation vs route selection

Separate two targets on the 125 exits:
- **INITIATION** (G1: escape vs snapback): which variables change immediately
  before the boundary exit (standardized logistic coefficients, permutation p).
- **ROUTE** (G3: propagation vs not, among all exits): which variables determine
  destination.
Compare the feature-significance sets: coefficient |z| ranks and sign patterns.
NEW_NODE RELEASE_TRIGGER if >= 1 feature significant (p < 0.05) for INITIATION
but not ROUTE; NEW_NODE ROUTE_GATE if >= 1 feature significant for ROUTE but not
INITIATION; if the sets overlap heavily, report MERGE (same gate).

## 8. Workstream G — volatility as routing temperature

VOLATILITY was MECH-3's sole GLOBAL_CANDIDATE_PRIMITIVE (removal dR2=0.0054, a
narrow margin). Terrain question only: does volatility alter TRANSITION
ACCESSIBILITY without specifying direction?

- P(escape within 7D | in concentration) under VOL_HIGH vs VOL_LOW (>= P70 /
  <= P30 trailing 252D; both require >= 120 days).
- P(reentry within 7D | escape) under VOL_HIGH vs VOL_LOW.
- P(propagation (G3 positive) | escape) under VOL_HIGH vs VOL_LOW.
- P(ALT depth | propagation) under VOL_HIGH vs VOL_LOW (n small; descriptive).
- Rank-band transmission: |corr(vel_a[t], vel_b[t+1])| for the 6 adjacent band
  pairs under VOL_HIGH vs VOL_LOW — mean |corr| difference (paired by band pair).
- Directional bias check: P(escape into BROAD_RISK | escape) under VOL_HIGH vs
  VOL_LOW — is volatility direction-agnostic (temperature) or direction-biased?

Classification: ROUTING_TEMPERATURE_SUPPORTED if VOL_HIGH vs VOL_LOW differs on
>= 2 accessibility metrics (escape/reentry/propagation prob, |corr| strength) in
the same direction (high vol -> more accessible) AND the directional-bias metric
shows no significant difference. Otherwise NOT_SUPPORTED.

## 9. Workstream H — state-conditioned routing graph

Nodes: 7 rank bands. Edge (a->b): corr(vel7_a[t], vel7_b[t+1]) with permutation
p < 0.05 (block shift, 200 surrogates). Computed for all 21 ordered band pairs
and under each state: BTC_UP/BTC_DOWN, VOL_HIGH/VOL_LOW, CONC_RISING/CONC_FALLING,
BREADTH_EXPANDING/CONTRACTING, ETH_STRONG/ETH_WEAK, RISK_ON/RISK_OFF (12 states;
each requires >= 120 days else INSUFFICIENT_SAMPLE).

Per state: edge set (appearance/disappearance vs unconditional graph), edge sign,
edge direction (which band leads). Metrics: fraction of edges appearing in a
state that are absent unconditionally; fraction of edges with sign flip vs
unconditional; adjacency similarity (Jaccard) between state graphs. BH-FDR over
all (pair x state) cells. **GRAPH_RECONFIGURATION_SUPPORTED** if >= 20% of tested
edges appear in some state graph but not the unconditional graph (q < 0.05) OR
>= 10% flip sign across states (q < 0.05), with >= 3 of 5 subperiods showing the
same edge-set change. Otherwise the unconditional graph stands (no reconfiguration).

## 10. Workstream 13 — MECH-2 vs MECH-3 flagship reconciliation

Target: `51-100 -> 101-200` rank-velocity lead.
MECH-2 (`05b_CONDITIONAL_LEAD_LAG_STATES.csv`): unconditional best |corr| over
lags [-7,-3,-1,1,3,7] = **-0.3044 at h=-7** (101-200 leads 51-100 at 7D).
MECH-3 (`08_ROUTING_FLIP_MAP.csv`): unconditional best |corr| over forward lags
[1,3,7] = **+0.1333 at h=+1** (51-100 leads 101-200 at 1D). Conditional values
(BTC_DOWN ~ +0.63/+0.64, VOL_HIGH ~ +0.67) reproduce across both.

Audit steps (all fixed): recompute on the SAME daily frame (a) MECH-2's
unconditional cell (max |corr| over [-7..7]); (b) MECH-3's unconditional cell
(max |corr| over [1,3,7]); (c) the conditional BTC_DOWN/VOL_HIGH cells under both
lag grids; (d) sign/lag interpretation of each. Also check: universe (same PIT
frame), dates (same 2,196), estimator (_cond_xcorr both), lag direction
convention, aggregation (band median velocity), missing data (same daily frame).
Classification (fixed vocabulary): DEFINITION_CHANGE / SAMPLE_CHANGE /
ESTIMATOR_CHANGE / CONDITIONING_CHANGE / DATA_VERSION_CHANGE / BUG /
OTHER_DOCUMENTED. Canonical unconditional claim is NOT carried forward until
resolved; the resolved statement is recorded in 19.

## 11. Workstream 14 — information-gap localization

Re-run MECH-3 WS H reconstruction for CONCENTRATION_EXIT (R2=0.076) and ROUTING
(R2=0.041) with an EXTENDED fixed feature set: the 8 MECH-3 variables + path
history (M1 one-hot), state age (log duration), plateau/P1 flag, native
activation (imp_share median 7D), regime interaction (VOL_HIGH x btc_ret30,
BREADTH x btc_ret30). Incremental R2 in the fixed order. **GAP_CLOSED** if R2
gains >= 0.05 for CONCENTRATION_EXIT or >= 0.03 for ROUTING; otherwise the gap is
localized as UNOBSERVED and the missing-sensor priority map (21) is built from
mechanistic relevance to route selection, PIT feasibility, historical
availability, likely incremental information, integration cost (each ranked 1-5;
priority = relevance + availability + info, minus cost).

## 12. Statistical discipline

- n=125 exits; rare classes (ALT 9, DEFENSIVE 2) never promoted.
- No high-dimensional fitting; 10 features max, L2-regularized logistic.
- Dependence: block bootstrap (20D), episode resampling, cluster counts; cross-
  sectional rows never treated as IID.
- BH-FDR within each workstream family (A patterns, B gates, D tests, E tests,
  G metrics, H edges); q<0.05 promotion, q<0.10 marginal.
- Subperiod stability: fixed partition 2020-21 / 2022 / 2023 / 2024 / 2025-26;
  promoted claims require same-sign presence in >= 3 of 5 subperiods (22).
- All tested cells retained (23_NULL_AND_FAILED_RESULTS.csv); no result shopping.

## 13. Causal evidence ladder (fixed)

L0 DESCRIPTIVE_CO_MOVEMENT · L1 TEMPORAL_ORDERING · L2 CONDITIONAL_LEAD_LAG ·
L3 COMMON_FACTOR_ROBUST · L4 CROSS_REGIME_STABLE · L5 MECHANISM_SUPPORTED ·
L6 QUASI_CAUSAL_OR_CAUSAL. No relationship skips levels. Release/pivot anatomy is
descriptive (L1-L2) unless path-memory or activation ordering survives the
permutation/held-out tests (L3+).

## 14. Pass / fail logic

- PASS_ALT_RELEASE_GATE_MECHANISM requires: >= 1 of A-F stable additions survive
  (path memory beyond state; duration dependence; stall->activation ordering;
  trigger/route separation; graph reconfiguration; reproducible release gate)
  AND the MECH2/3 reconciliation resolved AND nulls preserved.
- PASS_ALT_MECH4_WITH_LIMITATIONS: structure survives with documented limits but
  no single A-F addition is fully stable (or only descriptive ones).
- FAIL_ALT_RELEASE_GATE_MECHANISM: all A-F additions fail their tests and the
  reconciliation reveals a bug that invalidates the flagship claims.
- DATA_BLOCKED_ALT_RELEASE_GATE_MECHANISM: truth lock fails or PIT integrity
  breaks mid-run.

## 15. Artifacts

01_PREREGISTRATION.md, 02_DATA_TRUTH.md/json, 03-18 CSVs/parquet (as in brief),
19_MECH2_MECH3_FLAGSHIP_RECONCILIATION.md, 20_INFORMATION_GAIN_AND_PLATEAU.csv,
21_OBSERVATION_GAP_PRIORITY.md, 22_SUBPERIOD_STABILITY.csv,
23_NULL_AND_FAILED_RESULTS.csv, 24_CAUSALITY_LADDER.csv,
25_NEW_NODE_MERGE_DISSOLVE.csv, 26_FORMALISM_READINESS.md,
27_TEST_COUNT_RECONCILIATION.md, 28_MECH4_SUMMARY.md, 29_DECISION.md, plus
scripts/, tests/, plots/. Commit cadence M4.0-M4.6; fetch/reconcile Agent-2 work
before every push; never force-push.

## 16. No strategy design

No entries/exits/stops/sizing/PF/backtesting/ML predictors/deployment. The
decision is about terrain structure only. human_review_required = true;
next_checkpoint_authorized = false.
