# CRYPTO-ALT-MECH-8 — PREREGISTRATION

**Checkpoint:** CRYPTO-ALT-MECH-8 — FIELD-STATE DEEPENING:
BREADTH×DISPERSION TRANSITION LATTICE, PRE-EVENT ISOLATED-DOWNSIDE BUILDUP,
BREADTH ARCHITECTURE, RANK-HEALTH CONTEXT & CROSS-AGENT SYNTHESIS SUPPORT

**Role:** AGENT 1 — MAIN FIELD CARTOGRAPHER (canonical terrain bank).

**Empirical parents:**
- MECH-6 `9c3dcd32` (PASS_MECH6_MICROSTATE_SEQUENCE_ATLAS)
- MECH-7 `1a9c565e` (PASS_MECH7_FIELD_CONTEXT_WITH_LIMITATIONS)
- LOWER-FIELD-2 `af2ed678`
- LOWER-FIELD-3 `0a0eee7e`

**Governance:** terrain/mechanism research only. NO strategy, NO PnL,
NO entries/exits, NO sizing, NO leverage, NO deployment, NO signal
optimization. `human_review_required = TRUE`, `next_checkpoint_authorized = FALSE`.

---

## 0. Purpose

MECH-8 is a DEEPENING checkpoint. No new broad research lanes. It asks:

1. Can the isolated-downside reversal mechanism be detected earlier than -14D?
2. What state evolution occurs during the -30D → event window?
3. Is BREADTH×DISPERSION a true state machine (full 4-state transition system)?
4. Does state age alter the meaning of a 2×2 cell?
5. What is the full HIGH_BREADTH+HIGH_DISPERSION lifecycle (pre→entry→dwell→exit→post)?
6. Are there distinct breadth architectures beneath the same breadth level?
7. Does breadth composition add anything beyond level?
8. Is rank health separate from price recovery (PRIORITY matrix)?
9. Do price-recovery/rank-decay states exist reproducibly?
10. Does favorable field improvement expose weak/dead-like response (stress-response pilot)?
11. Does active liquidity/volume independently help shock absorption?
12. Does SHMC/SHHM have a legitimate local role (one focused recheck)?
13. Does volatility add anything after breadth/dispersion (parked role check)?
14. Why did Agent 1 and Agent 2 disagree on rank deterioration (reconciliation)?
15. Which nodes deserve next-stage synthesis?
16. Did field topology materially change?

## 1. Canonical inputs (frozen)

- M4 canonical daily frame (2196 days, 74 cols): `mech_4/_cache_daily.pkl`
  (built by `M4.build_daily(inp)` from frozen M4 inputs).
- M4 rank-band frame `bm` (7 bands × breadth_7d, median_rank_velocity_7d,
  market_cap_share).
- LF2 feature frame: `derivatives/lower_field_2/RESULTS/lf2_feature_frame.parquet`
  (3,290,806 rows, ranks 501–2000). Event reconstruction identical to MECH-7:
  z1 = |ret_1d|/sigma_t0 ≥ 2, sign, class ISOLATED/LOCAL_CLUSTER/BAND_BROAD/MULTI_BAND,
  family ISOLATED_DOWNSIDE_EXTREME / LOCAL_CLUSTER_DOWNSIDE / BAND_BROAD_UPSIDE /
  MULTI_BAND_UPSIDE / ISOLATED_UPSIDE / COORDINATED_DOWNSIDE.
- M4 `feat` frame (top-500 per-day asset panel): returns, rank, rank velocity,
  realized volatility, volume, market-cap share, days-in-top500.
- M4 `smem` frame: sector membership per asset-day (sector, sector_member_count).

## 2. Frozen thresholds (computed pre-outcome, full-sample)

- BRD_MED = 0.31 (top500_breadth_30d median)
- DISP_MED = 0.307 (top500_dispersion_30d median)
- 2×2 cell: HIGH/LOW breadth × HIGH/LOW dispersion.
- Subperiods: 2020-2021 / 2022 / 2023 / 2024 / 2025-2026.
- Minimum named-rule observations: n_effective ≥ 50 AND ≥ 3 subperiods.

## 3. Pre-registered event-time lattice (WS1/WS2)

Isolated-downside events aligned at t0. Lags:
-30, -21, -14, -10, -7, -5, -3, -2, -1, 0, +1, +2, +3, +5, +7, +10, +14.

Outcome classes (pre-registered, hierarchical, computed from LF2 forward
cumulative returns and rank velocity; mutually exclusive by precedence order):

1. EARLY_1SIGMA_RECOVERY — fwd1 or fwd2 cum ≥ +1.0σ (early stabilization)
2. LATE_RECOVERY — not early; fwd7 cum > 0
3. PARTIAL_REBOUND — fwd7 cum ≤ 0 but fwd14 cum > 0 (or fwd7 > -0.5σ & fwd14 > 0)
4. FULL_REVERSAL — fwd14 or fwd30 cum ≥ +1.0σ (full price reversal)
5. CONTINUED_DECLINE — fwd14 and fwd30 < 0, no full reversal
6. NEW_EXTREME — fwd7 or fwd14 ≤ -2.0σ (new downside extreme)

Rank outcome (orthogonal):
- RANK_RECOVERY — fwd7 rank velocity > 0
- RANK_STABLE — rank velocity ≈ 0
- RANK_CONTINUED_DETERIORATION — fwd7 rank velocity < 0

## 4. Pre-registered tests

### WS1 — Pre-event buildup to -30D
For isolated-downside events split by outcome, compute field coordinates at
each lag (breadth level/chg, dispersion, BTC 1/7/30D, dominance, ETH relative,
concentration level/chg, depth bands, volatility). Report medians by outcome,
ranksum p with FDR. Primary question: does reversal-vs-continuation separation
begin before -14D (i.e., is MECH-7's -14D finding the true beginning or an
artifact of the previously-tested window)?

### WS2 — First-divergence curves (not just first significant day)
For breadth, dispersion, BTC support, depth, concentration, volatility:
effect size by lag over -30..+14, FDR, direction, monotonicity, peak lag.

### WS3 — Full 4-state transition matrix (PRIMARY)
16 transitions LL/HL/LH/HH → LL/HL/LH/HH. For each: frequency, probability,
median dwell-before-transition, forward 1/3/7/14D tail activity, isolated-down
frequency, coordinated-up frequency, reversal, continuation, rank recruitment,
concentration movement, BTC/ETH state, volatility, propagation/reentry/mixed
outcomes, subperiod persistence.

### WS4 — State age / maturity
For each cell: age buckets DAY_1 / DAY_2_3 / DAY_4_7 / DAY_8_14 / DAY_15_PLUS.
Measure tail delivery, isolated down, coordinated up, continuation, giveback,
rank recruitment, concentration rebuild, P(leave), next-state distribution.

### WS5 — HH full lifecycle
Pool HH episodes. Pre-entry state (origin cell), entry order
(BRD_FIRST/DISP_FIRST/SYNCHRONOUS/FRESH), dwell, tail mix, exit order
(BRD_FIRST_EXIT/DISP_FIRST_EXIT/COUPLED_EXIT), post-exit state (7D/30D),
reentry. Named paths require n_effective ≥ 50 and ≥ 3 subperiods.

### WS6 — Breadth architecture
On high-breadth days (top500_breadth_30d > BRD_MED), decompose the share of
positive participation by: rank layer (1-25/26-100/101-250/251-500), age
cohort, liquidity cohort (mcap share), volatility cohort, rank-health cohort,
move magnitude (<1σ / 1σ+ / 2σ+). Also entropy/diversity of contributors,
strong-move vs marginal-positive share. Unsupervised clustering only if
stable under perturbation, interpretable, ≥50 episodes/group, multi-cycle.

### WS7 — Breadth level vs architecture
Nested incremental models (M0 level; M1 +rank composition; M2 +age;
M3 +liquidity; M4 +move-magnitude; M5 +rank-health; M6 +all). Purged
chronological CV (embargo 7D), leave-one-cycle-out, Δlogloss/ΔBrier/ΔAUC.
Targets: upper propagation success (ledger), isolated-down reversal, HH entry.
If composition does not help → MERGE into breadth level.

### WS8 — Rank health vs price recovery (PRIORITY)
Isolated-downside events classified by pre-event rank state over
3/7/14/30D (IMPROVING/STABLE/DETERIORATING from rank_vel). Price outcome
(early 1σ recovery, 7D rebound, full reversal, new low, 14/30D repair) ×
rank outcome (recovery/stabilization/continued decay). Cross matrix:
PRICE_RECOVERY×RANK_RECOVERY / PRICE_RECOVERY×RANK_DECAY /
PRICE_DECAY×RANK_RECOVERY / PRICE_DECAY×RANK_DECAY. Temporal order:
does rank recover before or after price?

### WS9 — Failed-recovery stress-response pilot (limited)
For deteriorating-rank assets (pre-event), identify whether the field improves
in the following 14D (top500 breadth up, peer band up). Ask whether the asset
responds: RESPONDS / WEAK_RESPONSE / DELAYED_RESPONSE / NO_RESPONSE. Named only
if ≥ 50 effective events. No DEATH label.

### WS10 — Active liquidity / volume
Does volume/volume-percentile add independent information for: isolated-down
early recovery, full reversal, HH tail realization, coordinated-up retention,
after controlling rank, breadth, dispersion, BTC, volatility, age, amplitude?
Volume fields: volume_24h_usd, vol_prev7_med, volume share (from feat/LF2).

### WS11 — SHMC/SHHM one focused recheck
Compare field context (breadth, dispersion, BTC/ETH, rank depth, 2×2 cell,
isolated vs coordinated prevalence, reversal, continuation) for SHMC vs SHHM
among extreme events. One recheck only.

### WS12 — Volatility parked role check
Does VOL state condition: HH persistence, isolated-down early 1σ recovery,
coordinated-up retention — after controlling breadth/dispersion/rank? If not
robust → leave parked as intensity context.

### WS13 — Agent1/Agent2 reconciliation
Compare MECH-7 `14_RANK_DETERIORATION_SHOCK_BRIDGE.csv` vs LF3
`13_RANK_DETERIORATION_SHOCK_BRIDGE.csv`. Reconcile definitions (event gate,
rank velocity sign, isolation definition, purge), harmonized estimate, verdict.

### WS14 — Dead/subtle node audit
One-pass review: breadth oscillation, BREADTH_FADE, EARLY_SNAPBACK, SHMC,
volatility intensity, rank deterioration, liquidity Q4, accumulation-like,
breadth acceleration, RETEST_RELOAD, termination breadth-first motif.
NO_ACTION / MERGE / LOCAL_ROLE / QUEUED / DISSOLVE.

### WS15 — Cross-agent export
`20_CROSS_AGENT_FIELD_CONTEXT_MECH8.parquet` keyed by event_id/asset_id/date
with field coordinates at -30/-21/-14/-10/-7/-5/-3/-2/-1/0 plus 2×2 cell,
state age, HH lifecycle stage, breadth architecture components, rank-health
context, liquidity/volume state. NO TARGET LEAKAGE (no forward fields).

## 5. Required outputs (25 files)

01_PREREGISTRATION.md (this file)
02_HARMONIZED_EVENT_SCHEMA.md
03_ISOLATED_DOWN_PRE30_CONTEXT.parquet
04_ISOLATED_DOWN_EFFECT_CURVES.csv
05_ISOLATED_DOWN_PRE_EVENT_SEQUENCE_ATLAS.csv
06_BRD_DISP_4STATE_TRANSITION_MATRIX.csv
07_BRD_DISP_STATE_AGE.csv
08_HH_FULL_LIFECYCLE.csv
09_HH_TRANSITION_LATTICE.csv
10_BREADTH_ARCHITECTURE_COMPONENTS.csv
11_BREADTH_ARCHITECTURE_CLASSES.csv
12_BREADTH_LEVEL_VS_ARCHITECTURE_AUDIT.csv
13_PRICE_RANK_HEALTH_MATRIX.csv
14_PRICE_RANK_TEMPORAL_ORDER.csv
15_FAILED_RECOVERY_STRESS_RESPONSE.csv
16_ACTIVE_LIQUIDITY_SHOCK_ABSORPTION.csv
17_SHMC_SHHM_FIELD_RECHECK.csv
18_VOLATILITY_PARKED_ROLE_CHECK.csv
19_AGENT1_AGENT2_DEFINITION_RECONCILIATION.csv
20_CROSS_AGENT_FIELD_CONTEXT_MECH8.parquet
20b_CROSS_AGENT_FIELD_CONTEXT_MECH8_SCHEMA.md
21_DEAD_SUBTLE_NODE_AUDIT.csv
22_PROMOTE_MERGE_DISSOLVE.csv
23_NULL_AND_FAILED_RESULTS.csv
24_MECH8_SUMMARY.md
25_MECH8_DECISION.md

## 6. Statistical standards

- Permutation p-values use finite-sample correction (k+1)/(B+1); never report 0.
- FDR via Benjamini-Hochberg.
- Purged chronological CV with embargo ≥ 7 days for nested-model claims.
- Effect claims require bootstrap CI or permutation support; no L3+ causal claims.
- A finding that is descriptive or unvalidated under perturbation stays
  DESCRIPTIVE_ONLY / LOCAL_NODE, never promoted without the ≥50/≥3 rule.
