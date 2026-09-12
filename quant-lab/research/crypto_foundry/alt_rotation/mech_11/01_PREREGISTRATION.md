# CRYPTO-ALT-MECH-11 — PREREGISTRATION

**Temporal Field Physics, Multi-Scale Delivery Lattice, Semi-Markov State
Geometry, Perturbation Amplitude, Propagation Radius, Rank-Depth Sequence
Structure, Cross-Agent Health Synthesis**

ROLE: AGENT 1 — CANONICAL FIELD CARTOGRAPHER
BRANCH: `agent/crypto-quant-foundry`
PARENTS: MECH-10 `decf75bc` · MECH-9 `b1de1df7` · LF5 TRUE-PEER REBUILD `8bd8cfbd` · POST-MECH10 SYNTHESIS `805461c9`

GOVERNANCE: NO STRATEGY. NO PNL. NO EXECUTION. NO ENTRY/EXIT. NO SIZING.
NO LEVERAGE. NO DEPLOYMENT.
`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`

This document is written BEFORE outcome analysis. All thresholds, methods,
and verdict rules are locked here.

---

## 0. Purpose

Move from "WHAT IS THE STATE?" toward "WHAT ARE THE LOCAL PHYSICS OF THE
STATE?". The desired output is a network of local rules under global
constraints — NOT universal laws.

## 1. Data & reuse

- Daily field frame: MECH-9 `_cache_dfw.pkl` (2196 days, 2020-2026, 5
  subperiods, 4-state cell + state-age + event families + field coordinates).
- Health/event frames: MECH-9 `_cache_health.pkl` (isolated-downside events
  with price/rank health outcomes) and `_cache_ev.pkl` (MECH-9 cross-agent
  context export).
- LF5 true-peer rebuild: `derivatives/lower_field_5/` artifacts — peer-path
  residuals (15_POST_EVENT_PEER_PATHS.csv), PIT band panel rebuilt from
  `cache/lf5_events.parquet` into a daily × rank-band panel
  (med_ret, ppos, ptail per band 1-25 … 1501-2000).
- Loner classification: reconstructed at event level from behavioral-peer
  residual z = |asset residual| / peer dispersion at h=1; FALSE_LONER if
  z < 1 (reproduces LF5 audit exactly: 18.4% overall, per-band matches).
- Chain/DEX activity: dfw `chain_tvl_med_chg7`, `dex_volume_change_7d`,
  `stablecoin_change_7d` — descriptive sensors only; DATA_BLOCKED where null.

## 2. Locked definitions

### 2.1 State cells (unchanged, inherited)
HH = HIGH_BREADTH_HIGH_DISP, HL = HIGH_BREADTH_LOW_DISP,
LH = LOW_BREADTH_HIGH_DISP, LL = LOW_BREADTH_LOW_DISP.
Thresholds: MECH-8/9 canonical medians (BRD_MED, DISP_MED).

### 2.2 State age bands (unchanged)
AGE_1, AGE_2_3, AGE_4_7, AGE_8_14, AGE_15_PLUS.

### 2.3 Outcomes (unchanged, inherited from MECH-8/9)
- PROPAGATION = fwd state in SUCCESS_LABELS (canonical state labels)
- REENTRY = fwd state == REENTRY_LABEL
- Tail events: dfw daily event families (ISOLATED_DOWN, BAND_BROAD_UP,
  MULTI_BAND_UP, COORDINATED_DOWN, LOCAL_CLUSTER_DOWN)
- Rank recruitment: `rank_depth_rel` / `rank_depth_rel_chg`

### 2.4 Event-level loner (WS10)
- Universe: LF5 isolated-down events with behavioral peer match.
- FALSE_LONER: z = |residual_BEHAVIORAL_10| / dispersion_BEHAVIORAL_10 < 1
  at h=1. TRUE_LONER otherwise. RECONSTRUCTED (not LF5 event labels) —
  verified against LF5 audit (18.4% overall; per-band within 0.5pp).

### 2.5 Clock families (WS1/WS4)
FAILURE_CLOCK (reentry/snapback), PROPAGATION_CLOCK (sustained propagation
confirmation), TAIL_CLOCK (extreme event arrival), REENTRY_CLOCK,
RANK_RECRUITMENT_CLOCK, EXIT_CLOCK (state exit).

## 3. Workstreams

### WS1 — MULTI-SCALE DELIVERY LATTICE (02_MULTI_SCALE_DELIVERY_LATTICE.csv)
For each cell × age band: cumulative/conditional occurrence by
+1/+2/+3/+5/+7/+10/+14/+21/+30 for: exit, reentry, propagation,
rank recruitment, tail activation, isolated downside, coordinated upside,
coordinated downside. Report p_by_h per horizon. LOCKED verdict: descriptive.

### WS2 — SEQUENCE GRAMMAR (03_SEQUENCE_GRAMMAR.csv)
For days that propagate within 7D, encode order of first appearance of
atoms: BREADTH_EXPANDS, DISPERSION_EXPANDS, RANK_RECRUITS, TAIL_ACTIVATES,
CONCENTRATION_RELEASES, PROPAGATION_CONFIRMS. Symbolic string B→D→R→T→C→P.
Count sequences; require >=50 effective examples + >=3 subperiods + FDR vs
uniform baseline. Verdict: COMMON / LOCAL / RARE / NULL.

### WS3 — SEMI-MARKOV AUDIT (04_SEMI_MARKOV_AUDIT.csv)
MARKOV baseline P(next|cell) vs SEMI-MARKOV P(next|cell, age_band).
Compare logloss, Brier, likelihood ratio; purged chronological split
(80/20). Verdict: SEMI_MARKOV_EARNED / MARKOV_SUFFICIENT / INCONCLUSIVE.

### WS4 — COMPETING-RISK CLOCKS (05_COMPETING_RISK_CLOCKS.csv)
Per cell × age band: cumulative incidence + cause-specific hazards over
h=1..30 for PROPAGATION, REENTRY, EXIT_TO_OTHER, TAIL_EVENT. Key question:
does HH survival to age 7/10/15 shift probability mass from REENTRY toward
PROPAGATION? Verdict: MASS_SHIFT_EARNED / NO_SHIFT / DATA_LIMITED.

### WS5 — PERTURBATION AMPLITUDE (06_PERTURBATION_AMPLITUDE.csv)
Perturbations: breadth jump/drop, dispersion jump/drop, BTC shock, vol
shock, concentration shock. Standardize amplitude (SMALL/MEDIUM/LARGE via
terciles of |delta|). Outcomes: 3D/7D state survival, state displacement,
fwd7 propagation, tail arrival, recovery latency. Verdict per perturbation:
SMOOTH / SATURATING / THRESHOLD_REGION / NO_STABLE_RESPONSE.

### WS6 — PROPAGATION RADIUS (07_PROPAGATION_RADIUS.csv)
For local field events (tail day, HH day): measure rank-band response at
+1/+3/+7/+14 in bands 26-100 … 1501-2000 from PIT band panel. Radius
metrics: NUMBER_OF_BANDS_AFFECTED, MAX_DEPTH_REACHED, TAIL_SHARE_SHIFT,
BREADTH_SHIFT, DISPERSION_SHIFT. Verdict: LOCAL / REGIONAL / BROAD_FIELD /
DATA_LIMITED.

### WS7 — RANK-DEPTH SEQUENCES (08_RANK_DEPTH_SEQUENCES.csv)
Temporal order of participation by rank band (ppos, med_ret, tail) at
1/3/5/7/14D. Test waterfall 26-100→101-250→251-500 vs deep-first vs
simultaneous vs fragmented. Verdict: WATERFALL / DEEP_FIRST / SIMULTANEOUS /
FRAGMENTED / NO_STABLE_ORDER.

### WS8 — RANK PATCH GEOMETRY (09_RANK_PATCH_GEOMETRY.csv)
Patches: UPPER_CORE (26-100), UPPER_MID (101-250), MID (251-500),
LOWER_MID (501-750), TRANSITION (751-1000). Per patch: internal correlation,
breadth (ppos), dispersion, loner density, tail synchrony, state
persistence, rank migration, cross-patch coupling. Verdict per patch:
COHERENT / WEAK / FRAGMENTED.

### WS9 — PATCH COUPLING (10_PATCH_COUPLING.csv)
Pairwise same-day / 1D / 3D / 7D lead-lag correlation for ppos, med_ret,
tail activity between patch pairs. Verdict: SYNC / LEAD_LAG / DECOUPLED.

### WS10 — TRUE vs FALSE LONER FIELD CONTEXT (11_TRUE_FALSE_LONER_FIELD_CONTEXT.csv)
Compare field context at -14/-7/-3/-1/t0/+1/+3/+7/+14 for TRUE_LONER vs
FALSE_LONER: breadth, dispersion, 4-state cell, state age, rank depth, BTC,
ETH, vol, concentration, SHMC/SHHM. Verdict: DISTINCT_GEOMETRY /
OVERLAPPING / DATA_LIMITED.

### WS11 — SIGMA RECOVERY FIELD LATTICE (12_SIGMA_RECOVERY_FIELD_LATTICE.csv)
For isolated-downside events by sigma class (1σ/2σ/3σ): recovery outcome
(EARLY/MID/LATE/NEVER) × field state at t0. Verdict: FIELD_STRENGTH_GRADIENT /
NO_GRADIENT / DATA_LIMITED.

### WS12 — HEALTH DEFINITION RECONCILIATION (13_HEALTH_DEFINITION_RECONCILIATION.csv)
Documentation-only table reconciling Agent-1 (MECH-9/10) vs Agent-2 (LF5)
health definitions: EVENT_UNIVERSE, PRICE_THRESHOLD, PRICE_ANCHOR,
RANK_THRESHOLD, RANK_HORIZON, ISOLATION_DEFINITION, VERDICT. NO population
synthesis until definitions match.

### WS13 — HEALTH TRANSITION LATTICE (14_HEALTH_TRANSITION_LATTICE.csv)
Condition on harmonized health states (PRD/PRU/PDD/PUU where
definitions permit): transitions at 3/7/14/30D conditioned on cell, age,
rank depth, loner class, perturbation strength. Verdict: LOCAL_PATHS /
MERGED / DATA_BLOCKED.

### WS14 — FAILURE MIRRORS (15_FAILURE_MIRROR_ANALYSIS.csv)
For every promoted sequence (WS2/WS13), measure its failure counterpart:
what first diverges (field coordinate, latency). Verdict per mirror:
EARLY_DIVERGENCE / COINCIDENT / NO_MIRROR_DATA.

### WS15 — SHMC/SHHM SEQUENCE PLACEMENT (16_SHMC_SHHM_SEQUENCE_PLACEMENT.csv)
Local momentum states (SHMC = SHORT_HOT_MEDIUM_COLD, SHHM =
SHORT_HOT_MEDIUM_HOT) aligned with: delivery sequence position, loner
class, patch type, state age. If no incremental structure: LEAVE_LOCAL.
Verdict: LOCAL_ALIGNMENT / NO_INCREMENTAL_STRUCTURE.

### WS16 — VOLATILITY CLOCK ROLE (17_VOLATILITY_CLOCK_ROLE.csv)
Volatility as INTENSITY/RETENTION/CLOCK MODULATOR only: effect on
propagation latency, exit latency, perturbation response amplitude, by
cell × age. NO directional role. Verdict: CLOCK_MODULATOR / PARKED.

### WS17 — CHAIN ACTIVITY OVERLAY (18_CHAIN_ACTIVITY_OVERLAY.csv)
DEX volume / TVL velocity / stablecoin activity overlaid on 4-state × age.
Verdict per sensor: INFORMATIVE / NULL / DATA_BLOCKED.

### WS18 — CANONICAL LOCAL FIELD MAP (19_CANONICAL_LOCAL_FIELD_MAP.csv)
Node registry: GLOBAL STATE, LOCAL PATCH, STATE AGE, SEQUENCE, CLOCK,
PERTURBATION, RADIUS, HEALTH, PEER CONTEXT, STATUS (PROMOTE / KEEP /
MERGE / DISSOLVE / PARK). Locked promotion bar: >=50 effective observations
+ >=3 subperiods + meaningful baseline difference (>=0.05 absolute lift).

### WS19 — SUMMARY + DECISION (22_MECH11_SUMMARY.md, 23_MECH11_DECISION.md)
Auto-generated from results + enriched with interpretation.

## 4. Minimum promotion bar (locked)

- Named local node/sequence: >=50 effective independent observations,
  >=3 subperiods, baseline lift >=0.05 absolute, FDR q<=0.10 where
  comparisons apply.
- Below bar: LOW_SAMPLE_CURIOSITY / DESCRIPTIVE.
- Nulls are valid outcomes. Do not force compression.

## 5. Anti-goals (locked)

- No universal mechanism claims.
- No directional trading interpretation.
- No repeated rescue mining of dead nodes.
- No new global breadth-derivative indicators beyond inherited dfw columns.
- Chain/DEX used only as descriptive sensors, never as drivers.

## 6. Sign-off

Written before outcome analysis: 2026-08-28.
Method locked. Outcomes recorded in 20_PROMOTE_MERGE_DISSOLVE.csv,
21_NULL_AND_FAILED_RESULTS.csv, 22_MECH11_SUMMARY.md, 23_MECH11_DECISION.md.
