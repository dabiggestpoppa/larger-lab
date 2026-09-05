# CRYPTO-ALT-MECH-10 — PREREGISTRATION

**CHECKPOINT:** CRYPTO-ALT-MECH-10 — TEMPORAL DELIVERY DEEPENING,
STATE-AGE DECOMPOSITION, 4-STATE HAZARD GEOMETRY, HEALTH-STATE FIELD
STRUCTURE, PRICE-UP/RANK-DOWN LOCAL MECHANISM, PERTURBATION ROLE REFINEMENT.

**ROLE:** AGENT 1 — CANONICAL FIELD CARTOGRAPHER.
**TYPE:** Terrain / mechanism research only. NO strategy, NO PnL, NO
execution, NO entry/exit design, NO sizing, NO leverage, NO deployment, NO
signal optimization.

**DATE:** 2026-08-27.

**PRIMARY EMPIRICAL PARENTS:**
- MECH-8 `17605c28` — breadth×dispersion 4-state transition matrix, state
  age, rank-health context.
- MECH-9 `b1de1df7` — state-age dynamics, survivorship audit, local
  bifurcation search (SHARP_ROUTE_GATE_ONLY), health-state field matrix,
  perturbation response, SHMC/SHHM locality, volatility intensity role.
- LOWER-FIELD-5 `06d6da9d` — PIT peer substrate, recovery clocks,
  stress-response field.

`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`

---

## 0. Purpose

MECH-10 DEEPENS, it does not widen. Objects of study:

1. state age — what it actually means (birth quality / survival selection /
   within-state maturation decomposition),
2. 4-state temporal delivery clocks (HH/HL/LH/LL),
3. 4-state transition hazards and age-conditional exit geometry,
4. PRICE_RECOVERY_RANK_DECAY — full field geometry, vs RANK_RECOVERY,
   subtypes, health-state transitions,
5. stress-response process geometry (t0..+14) and path sequences,
6. stall-and-rot phenotype anatomy,
7. perturbation role by state age (breadth-jump vs dispersion-jump),
8. permission→realization hypothesis (breadth vs dispersion),
9. local route-gate depth (stationary vs shifting),
10. small placement tests (transition velocity, HH birth quality, SHMC/SHHM,
    volatility) and final liquidity PARK.

Primary questions:

> What does state age actually mean — quality selection, maturation,
> persistence memory, or a mixture?

> What are the temporal delivery clocks of HH/HL/LH/LL?

> Does route into a state alter when propagation/reentry/tail activity occurs?

> Why does PRICE_RECOVERY_RANK_DECAY exist in a broad field?

> What separates durable price recovery with rank decay from full health
> recovery?

> Does perturbation type matter differently by state age?

> Are any sharp route gates stable enough to become useful local geometry?

## 1. Canonical inputs (locked, reused from MECH-8/9 caches)

- **Daily frame** (`dfw`, from M8 ws3 cache): 2196 days × 123 cols incl
  `cell`, `age_in_cell`, per-family event counts (trailing + fwd1/3/7/14),
  `prop7`/`reentry7`/`mixed7`, all global field coords, canonical `state`,
  `subperiod`.
- **LF2 events** (`ev`): 177,866 PIT extreme events with family, sigma
  normalization, forward cum returns, rank velocity, momentum_state.
- **Health events** (`health`): 1,023 isolated-downside events with
  `cross_state`, `pre_rank_state`, `price_outcome`, `fwd_rank_vel_7d`.
- **fwd_rank7 / fwd_rank30**: forward rank velocity maps (t+7, t+30).
- Frozen cell thresholds: `BRD_MED=0.31`, `DISP_MED=0.307`.
- SUCCESS_LABELS = {BROAD_RISK_EXPANSION} ∪ ALT_FAMILY.
- MECH-8 `14_PRICE_RANK_TEMPORAL_ORDER.csv` for price recovery day.

No new data sources. No new thresholds computed from outcomes.

## 2. Minimum observation & promotion rules

- Named local rule: **≥ 50 effective independent observations**.
- Subperiod stability: **≥ 3 subperiods**, no single cycle > 50% of
  effective count unless labeled cycle-local.
- FDR q < 0.10 (Benjamini-Hochberg); permutation p finite-sample corrected
  `(k+1)/(B+1)`, never 0.
- Below bar → `LOW_SAMPLE_CURIOSITY` / `DESCRIPTIVE_ONLY`.
- Bifurcation language only if a raw-coordinate discontinuity survives
  bootstrap + LOO-cycle + bin changes + purged validation; otherwise
  SHARP_ROUTE_GATE_ONLY / SMOOTH_GRADIENT / NOT_EARNED.

## 3. Workstreams (locked contract)

| WS | Output | Question |
|----|--------|----------|
| 1 | 02_STATE_AGE_MECHANISM_DECOMPOSITION.csv | Decompose state age: BIRTH_QUALITY / SURVIVAL_SELECTION / WITHIN_STATE_MATURATION |
| 2 | 03_CONDITIONAL_LANDMARKS.csv | At ages 1/3/5/7/10/15 conditional-on-survival: P(stay 1/3/7D), P(prop 3/7/14D), P(reentry), P(tail), P(exit to each cell) |
| 3 | 04_4STATE_TEMPORAL_DELIVERY.csv | Per-state delivery clocks: median latency, hazard, cumulative incidence to first tail/prop/reentry/exit |
| 4 | 05_4STATE_EXIT_HAZARDS.csv + 06_AGE_CONDITIONAL_EXIT_GEOMETRY.csv | Exit hazard by state; destination geometry by age band 1/2-3/4-7/8-14/15+ |
| 5 | 07_ROUTE_INTO_STATE_BY_AGE.csv | HH entry route (FROM_HL/LH/LL/CONTINUED) × age: does route matter after conditioning on age? |
| 6 | 08_PRICE_UP_RANK_DOWN_FIELD_MATRIX.csv | Full field geometry of PRICE_RECOVERY_RANK_DECAY at t0..+30 |
| 7 | 09_PRICE_UP_RANK_DOWN_VS_RANK_UP.csv | PRICE_RECOVERY_RANK_DECAY vs PRICE_RECOVERY_RANK_RECOVERY: pre/event/post, first divergence (beta rescue vs rehabilitation) |
| 8 | 10_PRICE_UP_RANK_DOWN_SUBTYPES.csv | Subtype families of PRICE_UP/RANK_DOWN (stable ≥50, else descriptive quantiles) |
| 9 | 11_HEALTH_STATE_TRANSITIONS.csv | Health-state machine transitions at 3/7/14/30D |
| 10 | 12_STRESS_RESPONSE_PROCESS.csv | Response process t0..+14: first response/rank/peer/field difference |
| 11 | 13_STRESS_RESPONSE_SEQUENCES.csv | Repeated trajectories FIELD_IMPROVES→PRICE→RANK (≥50) |
| 12 | 14_STALL_AND_ROT_ANATOMY.csv | Is stall-and-rot one phenotype or several? price flat/decline, rank decay velocity, field, later breakdown |
| 13 | 15_PERTURBATION_RESPONSE_AGE_CONDITIONAL.csv | Breadth-jump vs dispersion-jump inside HH by age band; perturbation type by state age |
| 14 | 16_PERMISSION_REALIZATION_TEST.csv | BREADTH=permission vs DISPERSION=realization: order sequences and outcomes |
| 15 | 17_LOCAL_ROUTE_GATE_DEPTH.csv | Steepest-region location, width, subperiod stability, age-dependence of sharp gates |
| 16 | 18_TRANSITION_VELOCITY_FINAL_PLACEMENT.csv | Velocity within HH entry/exit, PRICE_UP/RANK_DOWN, stress response; else PARK |
| 17 | 19_HH_BIRTH_QUALITY_FINAL_PLACEMENT.csv | Entry quality vs maturity / perturbation resilience / exit route; else PARK |
| 18 | 20_SHMC_SHHM_LOCAL_PLACEMENT.csv | Locality depth: state, age, health cell, stress class, route |
| 19 | 21_VOLATILITY_LOCAL_ROLE_DEPTH.csv | Vol intensity by HH age, perturbation type, route, health persistence |
| 20 | 22_TEMPORAL_LOCALITY_HIGHWAY_MAP.csv | Timed road segments: node, state, age, route, delivery/exit clock, perturbation, health, valid/invalid region, confidence |
| 21 | 23_PROMOTE_MERGE_DISSOLVE.csv, 24_NULL_AND_FAILED_RESULTS.csv, 25_MECH10_SUMMARY.md, 26_MECH10_DECISION.md | Node adjudication + closeout |
| — | 27_LIQUIDITY (PARK, default) | No new liquidity tests unless a direct interaction appears in health-state or HH analysis |

## 4. Pre-registered definitions

- **HH episode**: maximal consecutive run of cell == HIGH_BREADTH_HIGH_DISP.
- **Entry route**: cell at t-1 (FROM_HL / FROM_LH / FROM_LL / CONTINUED_HH).
- **Exit destination**: cell at t+1 after last day of episode.
- **P(prop within h)**: canonical state at t+h ∈ SUCCESS_LABELS.
- **Tail delivery**: ev_*_fwd7 counts (isolated-down / band-up) from daily.
- **Temporal delivery clocks** (WS3): per state, per age: time to first event
  of each family (within 30D, censored at end-of-sample); hazard =
  conditional probability of event arrival at each horizon; cumulative
  incidence = Kaplan-Meier-style.
- **State-age decomposition** (WS1): for each HH episode record entry
  quality coords (breadth, dispersion, BTC30, rank_depth_rel, top3_share,
  vol_med), survival (duration), and within-episode fwd-prop trajectory.
  BIRTH = entry coords predict duration; SELECTION = conditional-on-survival
  hazard of young vs mature; MATURATION = within-episode change in P(leave)/
  fwd prop between early and late days of the SAME episode (needs n≥10).
  Verdict: BIRTH / SELECTION / MATURATION / MIXED / UNRESOLVED.
- **Perturbation types** (WS13, from MECH-9 flags): brd_jump / brd_drop /
  disp_jump / disp_drop / btc_shock / conc_shock / vol_shock (5D changes).
- **Permission→realization** (WS14): sequence of breadth/dispersion crossing
  into HH: BREADTH_FIRST (brd crossed into HH before disp), DISP_FIRST,
  SIMULTANEOUS (both within 1 day of entry). Outcomes: tail activation
  latency, prop7, coord-up onset, rank recruitment, survival.
- **Route-gate depth** (WS15): for each axis (rank_depth_rel, breadth,
  dispersion, vol, top3_share, age), location of max |dP/dx| bin, width of
  the steep region (bins where slope ≥ 50% of max), subperiod stability,
  and whether the steepest bin location shifts across age bands of the
  conditioning cell. Verdict: STABLE_GATE / SHIFTING_GATE / SMOOTH /
  INCONCLUSIVE.
- **Health-state transitions** (WS9): cross_state at t → cross_state at
  t+3/7/14/30 (from forward cum returns + fwd rank vel; recomputed per
  horizon using the MECH-8 cross-state rule but with horizon-specific
  price/rank flags).

## 5. Statistical protocol

- Wilcoxon rank-sum; chi-square; FDR (BH) per table.
- Bootstrap 400 (cluster by date); permutation 300, corrected.
- Purged chronological CV (5 folds, 7D embargo) for fitted models.
- No causal claim above L2 anywhere in this checkpoint.

## 6. Node adjudication (WS21)

Re-review: HH_STATE_AGE_MATURITY, HH_BIRTH_QUALITY, LOCAL_BIFURCATION_SEARCH
(SHARP_ROUTE_GATE_ONLY), SECOND_ORDER_STATE_PATHS, TRANSITION_VELOCITY,
PERTURBATION_RESPONSE, HEALTH_STATE_FIELD_MATRIX, STRESS_RESPONSE_*, SHMC/SHHM,
VOLATILITY_LOCALITY, LIQUIDITY (PARK default).

Allowed: NEW_NODE / LOCAL_NODE / CONDITIONAL_NODE / DESCRIPTIVE_ONLY /
MERGE / DISSOLVE / NULL / DATA_BLOCKED / PARK / LOW_SAMPLE_CURIOSITY.

## 7. Governance

- NO strategy, PnL, execution, entry/exit, sizing, leverage, deployment.
- Do not force bifurcation language. Do not force one master mechanism.
- LOCAL + TEMPORAL GEOMETRY IS A VALID RESULT.
- `human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`.
