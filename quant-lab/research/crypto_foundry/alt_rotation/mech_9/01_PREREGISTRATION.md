# CRYPTO-ALT-MECH-9 — PREREGISTRATION

**CHECKPOINT:** CRYPTO-ALT-MECH-9 — STATE-AGE DYNAMICS, BREADTH×DISPERSION
GEOMETRY, LOCAL BIFURCATION SEARCH, HEALTH-STATE FIELD CONTEXT, PERTURBATION
RESPONSE & TRANSITION ANATOMY.

**ROLE:** AGENT 1 — CANONICAL FIELD CARTOGRAPHER.
**TYPE:** Terrain / mechanism research only. NO strategy, NO PnL, NO
execution, NO entry/exit design, NO sizing, NO leverage, NO deployment, NO
signal optimization.

**DATE:** 2026-08-27.

**PRIMARY EMPIRICAL PARENTS:**
- MECH-7 `1a9c565e` — global context of isolated downside vs coordinated
  upside, breadth×dispersion lifecycle, cross-agent handoff.
- MECH-8 `17605c28` — field-state deepening: 4-state transition matrix,
  pre-event isolated-downside buildup, breadth architecture, rank-health
  context, cross-agent export.
- LOWER-FIELD-3 `0a0eee7e` — local event anatomy research.
- LOWER-FIELD-5 `06d6da9d` — PIT peer substrate, health/recovery clocks,
  stress-response field.

**LENS DOCUMENTS (read, not contracted):**
- `QUEUED_RESEARCH_IDEAS_2026-08-27.md`
- `OPERATOR_RESEARCH_LENS_UPDATE_2026-08-27.md`
- `QUEUED_BASKET_TRIANGLE_GEOMETRY_2026-08-27.md`

`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`

---

## 0. Purpose

MECH-9 DEEPENS, it does not widen. Objects of study:

1. the breadth×dispersion 4-state machine (MECH-8 WS3),
2. STATE AGE inside those cells, especially HH,
3. local transition / bifurcation-like regions,
4. PRICE_RECOVERY vs RANK_HEALTH as separate field responses,
5. favorable-field stress response,
6. local rather than universal mechanisms,
7. perturbation strength and propagation of local state changes.

Primary questions:

> Why does mature HH behave so differently from young HH?

> Is state age merely elapsed persistence, or does the internal geometry of
> the state change as it matures?

> Are there identifiable transition surfaces or bifurcation-like regions
> separating persistence, collapse, propagation, and reentry?

> What global field context distinguishes PRICE_UP/RANK_UP,
> PRICE_UP/RANK_DOWN, PRICE_DOWN/RANK_UP, PRICE_DOWN/RANK_DOWN?

> What distinguishes full response, weak response, delayed response, and
> no-response under favorable perturbation?

Use advanced lenses ONLY if the empirical geometry earns them.

---

## 1. Canonical inputs (locked, reused from MECH-8)

- **Daily frame** (`M4.build_daily` via MECH-8 loader): 2196 days × ~74 cols,
  global field coordinates (breadth 30/7D, dispersion 30/7D, top3 share,
  BTC return/dominance, ETH relative, rank-band medians, volatility,
  stablecoin/DEX/TVL, canonical `state` labels, `subperiod`).
- **Breadth features** (`M8._add_breadth_features`): breadth velocity,
  acceleration, axis, persistence, exhaustion, divergence, oscillation,
  `rank_depth_rel` (201-500 minus 11-50 median 30D return).
- **Cell assignment** (frozen, pre-outcome): `BRD_MED=0.31`, `DISP_MED=0.307`
  → `HIGH_BREADTH_HIGH_DISP` (HH) / HIGH_LOW (HL) / LOW_HIGH (LH) /
  LOW_LOW (LL).
- **LF2 extreme-event frame** (`M8.load_lf2_events`): PIT event catalog with
  family (ISOLATED_DOWNSIDE_EXTREME etc.), sigma-t0 normalization, forward
  cumulative returns, rank velocity, volume, age, mcap, momentum_state,
  reversal, subperiod.
- **Event counts attached to daily** (`M8._attach_event_counts`): per-family
  daily and forward 1/3/7/14D counts.
- **Canonical field `state`** labels: BTC_CONCENTRATION, MIXED_NO_CLEAR_ROUTE,
  BROAD_RISK_EXPANSION, LARGE_ALT_ROTATION, MID_CAP_ROTATION,
  ETH_BROADENING, CAPITAL_EXIT, STABLECOIN_PARKING.
- **SUCCESS_LABELS** = {BROAD_RISK_EXPANSION} ∪ ALT_FAMILY.
- **Price-rank health events** (MECH-8 WS8 `13b_PRICE_RANK_HEALTH_EVENTS.parquet`):
  isolated-downside events with `price_outcome`, `pre_rank_state`,
  `cross_state` (PRICE_RECOVERY_RANK_RECOVERY etc.), forward rank velocity.

No new data sources. No new thresholds computed from outcomes.

## 2. Minimum observation & promotion rules

- Named local rule / node: **≥ 50 effective independent observations**.
- Subperiod stability: **≥ 3 subperiods**, no single cycle > 50% of effective
  count unless explicitly labeled cycle-local.
- FDR threshold: q < 0.10 (Benjamini-Hochberg).
- Permutation p: finite-sample corrected `(k+1)/(B+1)`, never 0.0.
- Below bar → `LOW_SAMPLE_CURIOSITY` or `DESCRIPTIVE_ONLY`; no promotion.
- Bifurcation language ONLY if a raw-coordinate discontinuity survives:
  bootstrap, leave-one-cycle-out, reasonable bin changes, purged temporal
  validation. Otherwise `SHARP_ROUTE_GATE_ONLY` / `SMOOTH_GRADIENT` /
  `NOT_EARNED`.
- Survivorship: age effects must be separated from episode-quality selection
  (landmark analysis, conditional-on-survival hazards, matched young-HH).

## 3. Workstreams (locked contract)

| WS | Output | Question |
|----|--------|----------|
| 1 | 02_STATE_AGE_CONTINUOUS_SURFACE.csv | Continuous state-age surfaces (P(stay), P(exit), exit destination, fwd propagation/reentry/tails) for HH/HL/LH/LL |
| 2 | 03_STATE_AGE_SURVIVORSHIP_AUDIT.csv | Is maturity genuine within-episode evolution or survivorship selection? Landmark analysis + conditional hazards |
| 3 | 04_HH_MATURATION_ANATOMY.csv | What changes internally as HH matures (breadth, dispersion, rank-depth, leadership width, tails, concentration, BTC, ETH, vol)? |
| 4 | 05_HH_BIRTH_QUALITY.csv | Can long-lived HH be recognized at inception (duration buckets by entry-day coords; purged validation)? |
| 5 | 06_SECOND_ORDER_STATE_PATHS.csv | A→B→C second-order paths (LL→HL→HH etc.), ≥50 effective, outcomes |
| 6 | 07_TRANSITION_VELOCITY.csv | Transition speed/size: distance from threshold, days near boundary, overshoot; SOFT/MODERATE/HARD outcome geometry |
| 7 | 08_LOCAL_BIFURCATION_SEARCH.csv | Local bifurcation-like search on raw coordinates (breadth, dispersion, age, rank-depth, concentration, vol) |
| 8 | 09_STATE_SPACE_VECTOR_FIELD.csv | Low-dim state vector X(t); local transition averages; attractor/corridor/loop checks |
| 9 | 10_PERTURBATION_RESPONSE.csv | Discrete field-change perturbations → P(survive/change/propagate), recovery latency by cell × age |
| 10 | 11_HEALTH_STATE_FIELD_MATRIX.csv | Field context (−14..+30) for the four PRICE×RANK health states |
| 11 | 12_PRICE_UP_RANK_DOWN_ANATOMY.csv | PRICE_RECOVERY_RANK_DECAY deep dive: field, cell, relapse, 30D rank recovery |
| 12 | 13_STRESS_RESPONSE_CLASSES.csv + 14_STRESS_RESPONSE_FIRST_DIVERGENCE.csv | Stratify RESPONDS / WEAK_DELAYED / NO_RESPONSE; first divergence |
| 13 | 15_STRESS_RESPONSE_SURFACE.csv | Field-improvement strength × prior health → response; linear/saturating/threshold |
| 14 | 16_NO_RESPONSE_FAILURE_ANATOMY.csv | Repeated failure sequences among NO_RESPONSE assets |
| 15 | 17_LIQUIDITY_FINAL_PLACEMENT.csv | Final liquidity placement check (HH resilience, price-up/rank-down, stress latency) |
| 16 | 18_SHMC_SHHM_LOCALITY.csv | Locality map of SHMC/SHHM (cell, age, rank depth, shock type, health state) |
| 17 | 19_VOLATILITY_LOCALITY.csv | Where volatility matters as intensity/retention (HH persistence, transition velocity, perturbation response, recovery latency) |
| 18 | 20_LOCALITY_HIGHWAY_REGISTRY.csv | Local road segments: valid/invalid region, state/rank/time context, confidence |
| 19 | 21_CROSS_AGENT_CONTEXT_MECH9.parquet + 21b schema | Event-level field context for Agent-2 joins; NO forward leakage |
| 20 | 22_PROMOTE_MERGE_DISSOLVE.csv, 23_NULL_AND_FAILED_RESULTS.csv, 24_MECH9_SUMMARY.md, 25_MECH9_DECISION.md | Node adjudication + closeout |

## 4. Pre-registered outcome/state definitions

- **HH episode**: maximal consecutive-days run where cell == HIGH_BREADTH_HIGH_DISP.
- **State age** (`age_in_cell`): run position within current cell (1-based).
- **P(leave next day)**: next-day cell != current cell, conditional on
  observed next day.
- **fwd propagation**: canonical `state` at t+7 ∈ SUCCESS_LABELS.
- **Transition velocity** (WS6): per crossing day, breadth delta =
  `top500_breadth_30d[t] - top500_breadth_30d[t-1]`, dispersion delta
  analogous; distance from threshold before transition = min distance from
  BRD_MED/DISP_MED over prior 5 days; overshoot = max excursion past
  threshold within 3 days post-crossing. Bins: SOFT (both |Δ| < 0.03),
  MODERATE, HARD (either |Δ| ≥ 0.06) — natural tercile fallback if degenerate.
- **Perturbation events** (WS9): |breadth 5D change| ≥ 0.04 (JUMP if > 0,
  DROP if < 0), |dispersion 5D change| ≥ 0.04, |btc 5D return| ≥ 0.08,
  |top3_share_chg7| ≥ 0.02, |vol_med chg| ≥ 1σ of its own series. Recovery
  latency = days until cell returns to pre-perturbation cell.
- **Health cross states** (from MECH-8): PRICE_RECOVERY_RANK_RECOVERY,
  PRICE_RECOVERY_RANK_DECAY, PRICE_DECAY_RANK_RECOVERY, PRICE_DECAY_RANK_DECAY.
- **Stress-response classes** (MECH-8 price_response re-derived with
  hierarchy): RESPONDS (fwd1/fwd2 ≥ +1σ, or fwd7 ≥ +1σ), WEAK (fwd14 ≥
  +0.5σ), DELAYED (fwd14 > 0 but < +0.5σ), NO_RESPONSE (else). For the
  stratification the brief's RESPONDS / WEAK_DELAYED / NO_RESPONSE three-class
  mapping is used: RESPONDS; WEAK_DELAYED = {WEAK, DELAYED}; NO_RESPONSE.
- **Bifurcation verdicts**: SMOOTH_GRADIENT / NONLINEAR_REGION /
  SHARP_TRANSITION_REGION / BIFURCATION_CANDIDATE / NO_STRUCTURE, each gated
  on ≥3-subperiod stability of a raw-coordinate binned surface.
- **State-space vector field** (WS8): X = [breadth, dispersion, state_age,
  rank_depth_rel, top3_share, btc_return_30d, vol_med] (all standardized);
  ΔX(t→t+1); local averages by X-quintile neighborhood; attractor check =
  mean |ΔX| inside vs outside HH/LL; corridor check = HL/LH mean dwell and
  net drift; loop check = sign consistency of ΔX cycle (2-step return).

## 5. Statistical protocol

- Wilcoxon rank-sum for two-group comparisons; chi-square for contingency.
- FDR (BH) across all multiple comparisons within each table.
- Bootstrap: 400 resamples (cluster by date for event-level tables).
- Permutation: 300, finite-sample corrected p.
- Purged chronological CV (5 folds, embargo 7D) for any fitted model
  (HH birth quality; stress-response surface), reporting AUC / Δlogloss /
  ΔBrier.
- No claim above L2 (conditional lead-lag) anywhere in this checkpoint.

## 6. Node adjudication (WS20)

Re-review (from MECH-5/6/7/8 + LF2/3/5):
ROUTE_GATE / DURATION_STRUCTURED_ESCAPE / RETEST_RELOAD /
ACCUMULATION_LIKE / BIFURCATION / VOLATILITY_LIFECYCLE_ROLE / HH_LIFECYCLE /
STATE_AGE_MATURITY / BREADTH_ARCHITECTURE / PRICE_RANK_HEALTH_SPLIT /
EARLY_SNAPBACK / BREADTH_FADE / SHMC_TAIL_ACTIVATION / ACTIVE_LIQUIDITY /
BREADTH_OSCILLATION / RANK_DETERIORATION_SHOCK_BRIDGE / TERMINATION_MOTIFS /
SECOND_ORDER_PATHS / PERTURBATION_RESPONSE.

Allowed: NEW_NODE / LOCAL_NODE / CONDITIONAL_NODE / DESCRIPTIVE_ONLY /
MERGE / DISSOLVE / NULL / DATA_BLOCKED / LOW_SAMPLE_CURIOSITY.

## 7. Governance

- NO strategy, PnL, execution, entry/exit, sizing, leverage, deployment.
- Do not force a universal state machine.
- LOCAL RULES ARE ALLOWED TO REMAIN LOCAL.
- Preserve MECH-8 corrected claim: isolated-downside reversal-vs-continuation
  divergence is essentially contemporaneous on global coordinates (only
  `rank_depth_rel@-21D` survived FDR pre-event). MECH-9 does not re-open that
  global pre-event lane except via WS10/WS11 health-state field context.
- `human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`.
