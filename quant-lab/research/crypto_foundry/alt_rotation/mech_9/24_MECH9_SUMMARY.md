# CRYPTO-ALT-MECH-9 — SUMMARY

**State-age dynamics, breadth×dispersion geometry, local bifurcation search,
health-state field context, perturbation response & transition anatomy.**

**PARENTS:** MECH-7 `1a9c565e` · MECH-8 `17605c28` · LOWER-FIELD-3 `0a0eee7e` ·
LOWER-FIELD-5 `06d6da9d`
**VERDICT:** **PASS_MECH9_STATE_AGE_DYNAMICS_WITH_LIMITATIONS**
(see `25_MECH9_DECISION.md`)
**TESTS:** 28/28 pass · **ARTIFACTS:** 25 required files + 7 plots

---

## 0. Headline interpretation

1. **State age is a real coordinate, and HH maturity is genuine — but it is
   PARTLY selection.** The continuous HH surface shows P(leave next day)
   falling from 0.27 (day 1) to ~0.10 by day 21 while fwd7 propagation rises
   to ~1.0 at the tail; the landmark analysis confirms fwd7 prop 0.48
   (age≥1) → 0.67 (age≥15) and P(leave) 0.10 → 0.04. However, entry-coordinate
   differences show long-lived HH episodes were born different: higher entry
   breadth (0.68 vs 0.43, p=0.002), higher dispersion (0.47 vs 0.37,
   p=0.013), higher BTC 30D (0.18 vs 0.07, p=0.0003). The within-episode test
   (n=19 episodes ≥10D) is directionally right (early prop7 0.00 → mature
   0.38) but p=0.19 — **not separable from selection at this sample size**.
   Both mechanisms likely contribute; HH_BIRTH_QUALITY is DIRECTIONAL_ONLY.

2. **There is no novel multidimensional bifurcation boundary.** The
   raw-coordinate binned surfaces show sharp regions (rank_depth_rel
   BIFURCATION_CANDIDATE max jump 0.31, 4/5 subperiods; breadth
   SHARP_TRANSITION_REGION 0.26, 4/5), but these are projections of the
   ALREADY-EARNED breadth/rank-depth route gates, not evidence of a new
   market bifurcation. **Classification: SHARP_ROUTE_GATE_ONLY (descriptive).**
   MECH-4's BIFURCATION_STRONG_FORM stays NOT_EARNED.

3. **The four PRICE×RANK health states live in distinct field geometry.**
   PRICE_RECOVERY_RANK_DECAY (n=282) sits in the broadest field at t0
   (breadth 0.388, dispersion 0.341, BTC 30D +0.054) — price recovers into
   a strong field that does NOT rescue rank. PRICE_RECOVERY_RANK_RECOVERY
   (n=339) sits in a weaker field (breadth 0.252) — the asset itself led.
   PRICE_DECAY_RANK_DECAY (n=293) is broad-but-declining (breadth 0.362,
   rank_depth −0.039).

4. **Stress response is separable but only contemporaneously.** RESPONDS
   (n=382) vs NO_RESPONSE (n=210) differ on field improvement over the next
   14D (0.172 vs 0.129), breadth at t0 (0.359 vs 0.309), and rank recovery
   (0.647 vs 0.133), but the first-divergence lattice shows NO pre-event or
   t0 separation survives FDR — divergence appears at **+3D** (breadth
   p=0.010, dispersion p=0.021, raw). The response surface is
   **NO_STABLE_RESPONSE** (grid P(RESPONDS) 0.48–0.70, no threshold).

5. **Perturbation response is local, not universal.** 8 cell×perturbation
   cells with n≥50 show |Δprop7| ≥ 0.05. Breadth JUMPS into HH *lower*
   fwd7 prop (−0.125) — the field was already there; dispersion JUMPS into
   HH *raise* it (+0.099) — dispersion arrival adds realization. Recovery
   latency is fast (median 1D) across cells.

6. **Volatility re-earns a local intensity role inside HH**: HH P(stay)
   0.83 → 0.95, median dwell 4.5D → 30D, fwd7 prop 0.31 → 0.59 across
   VOL_LO→VOL_HI. NOT a route selector; an intensity/retention context.

7. **Correction of MECH-8's HH episode count**: MECH-8 summary reported
   "367 HH episodes pooled" — that figure is the SUM of n_episodes across
   lifecycle-table dimensions (double counting). The true count is **79
   HH episodes** (consistent with the underlying run structure). All MECH-9
   episode-level claims use the corrected count.

---

## 1. Continuous state-age surfaces (WS1, `02_STATE_AGE_CONTINUOUS_SURFACE.csv`)

- 69 cell×age rows (floor n≥10, ages 1–30).
- **HH**: ages 1–21; P(leave) 0.27 → 0.10; fwd7 prop 0.23 → ~1.0 at the
  long tail (small-n tail — use landmark rows for robustness).
- **HL**: ages 1–8; P(leave) flat 0.33–0.36 — no maturity gradient.
- **LH**: ages 1–10; P(leave) 0.47 → 0.20; fwd7 prop ~0.06 (disorder cell).
- **LL**: ages 1–30; P(leave) 0.40 → 0.30; compression is sticky but not
  maturity-graded like HH.

## 2. Survivorship audit (WS2, `03_STATE_AGE_SURVIVORSHIP_AUDIT.csv`)

- Landmark (age≥1 vs age≥15): **fwd7 prop 0.484 → 0.666; P(leave) 0.103 →
  0.041** — conditional-on-survival maturity is real.
- Within-episode (n=19 episodes ≥10D): early 0.00 vs mature 0.38, p=0.19 —
  directionally consistent, underpowered.
- Episode-entry: long-lived HH entered with higher breadth/dispersion/BTC-30D
  (3/6 significant) — **selection contributes to the age effect**.

## 3. HH birth quality (WS4, `05`/`05b`/`05c`)

- 79 episodes; long-lived (≥6D) = 29.
- Purged chronological CV (5 folds, 7D embargo): AUC 0.675, logloss 0.669,
  Brier 0.233, **perm p = 0.80** → NOT robust out-of-sample.
- Univariate: breadth / dispersion / BTC-30D significant at entry, but the
  multivariate model does not clear permutation → **DIRECTIONAL_ONLY**.

## 4. Local bifurcation search (WS7, `08_LOCAL_BIFURCATION_SEARCH.csv`)

| axis | verdict | max jump | sharp subperiods |
|---|---|---|---|
| rank_depth_rel | BIFURCATION_CANDIDATE | 0.310 | 4/5 |
| top500_breadth_30d | SHARP_TRANSITION_REGION | 0.263 | 4/5 |
| vol_med | SHARP_TRANSITION_REGION | 0.219 | 3/5 |
| top3_share | SHARP_TRANSITION_REGION | 0.179 | 3/5 |
| top500_dispersion_30d | SHARP_TRANSITION_REGION | 0.149 | 3/5 |
| age_in_cell | NONLINEAR_REGION | 0.114 | 5/5 |

Sharp regions are route-gate projections on already-earned gates.
**No novel bifurcation boundary. SHARP_ROUTE_GATE_ONLY.**

## 5. State-space vector field (WS8, `09_STATE_SPACE_VECTOR_FIELD.csv`)

- LL is an attractor-like region (mean |ΔX| 0.50 inside vs 0.76 outside).
- HH is NOT quiescent in state-space (0.77 vs 0.60) — high dispersion cell
  is internally active, but **stabilizes with age**: young |ΔX| 1.04 vs
  mature 0.63, p=1.1e-13.
- HL/LH are transient corridors (median dwell 3–4D, near-zero net drift).
- 2-step/1-step magnitude ratio 1.77 (> √2 ≈ 1.41) — trending, not
  oscillating, at the daily state level.

## 6. Second-order paths (WS5, `06_SECOND_ORDER_STATE_PATHS.csv`)

- 14 A→B→C triples with n≥10; **0 clear the ≥50 naming bar** → DESCRIPTIVE.
- Highest-n: HL→LL→HL (n=34) and LL→HL→LL (n=31) — breadth oscillation
  through compression; both near baseline fwd7 prop (0.18/0.23 vs 0.18
  baseline).
- LL→HL→HH (n=14) and LL→HH→LL (n=13) have elevated fwd7 prop (0.21–0.38)
  — the LL→HL→HH ramp is the propagation-adjacent route, consistent with
  MECH-8's HL→HH edge.

## 7. Transition velocity (WS6, `07_TRANSITION_VELOCITY.csv`)

- 282 crossing days (after NaN filtering); SOFT 16 / MODERATE 47 / HARD 219.
- fwd7 prop 0.25 (SOFT) → 0.12 (HARD); reentry 0.25 → 0.36 — harder
  crossings tend toward failure, but **soft-vs-hard p = 0.38** → NOT
  statistically robust. DESCRIPTIVE.

## 8. Perturbation response (WS9, `10_PERTURBATION_RESPONSE.csv`)

- 28 cell×perturbation rows; 23 with n≥50; **8 with |Δprop7| ≥ 0.05**.
- Breadth jump into HH: Δprop −0.125 (n=286) — premature excitement.
- Dispersion jump into HH: Δprop +0.099 (n=343) — realization arrives with
  dispersion.
- Dispersion jump into LL: +0.101 (n=51); vol shock in HL: −0.214 (n=39,
  below bar).
- Recovery latency median 1D across cells — states snap back fast.

## 9. Health-state field matrix (WS10, `11_HEALTH_STATE_FIELD_MATRIX.csv`)

- 40 state×lag rows (−14…+30).
- **PRICE_RECOVERY_RANK_DECAY**: broadest field (breadth 0.388 t0), price
  recovers into a strong field that fails to rescue rank.
- **PRICE_RECOVERY_RANK_RECOVERY**: weakest field (breadth 0.252) — asset-led
  recovery.
- **PRICE_DECAY_RANK_DECAY**: broad-but-declining (breadth 0.362,
  rank_depth −0.039).
- **PRICE_DECAY_RANK_RECOVERY** (n=109, smallest): mid field, rank-led.

## 10. PRICE_UP_RANK_DOWN deep dive (WS11, `12_PRICE_UP_RANK_DOWN_ANATOMY.csv`)

- n=282 events; 39.7% in HH, 31.2% in LL at t0.
- Price recovers (by construction) but rank keeps decaying: median fwd rank
  vel −25.5 (7D) / −27.0 (30D); only **31.6% recover rank by 30D**.
- Price relapse (fwd7 > 0 → fwd30 < 0): only 9.9% — the rebound is durable
  in price.
- Field context: breadth 0.388 vs other states (p=0.046), dispersion 0.341
  (p=0.026) — **these events cluster in broad, high-dispersion fields**.

## 11. Stress-response stratification (WS12/13, `13`/`14`/`15`)

- 672 deteriorating-rank isolated downsides: RESPONDS 382, WEAK_DELAYED 80,
  NO_RESPONSE 210.
- Field improvement over next 14D: 0.172 vs 0.222 vs 0.129 (RESPONDS /
  WEAK_DELAYED / NO_RESPONSE).
- Rank recovery 7D: 0.647 / 0.225 / 0.133.
- **First divergence**: no FDR-significant pre-event or t0 coordinate;
  breadth+dispersion separate at **+3D** (raw p 0.010 / 0.021). The
  response-vs-no-response distinction is CONTEMPORANEOUS.
- **Response surface: NO_STABLE_RESPONSE** — P(RESPONDS) 0.48–0.70 across
  the improvement×deterioration grid; no threshold region.

## 12. No-response failure anatomy (WS14, `16`/`16b`)

- 209 NO_RESPONSE events: 85% also rank-decay, 83% continued rank decay,
  54% stall while peers rise, 7% price relapse.
- Dominant motif: **NO_PRICE_RESPONSE + RANK_DECAY (85%)**; pure
  rank-decay-without-price-stall is ~0% — the no-response population is
  essentially "stall and rot" rather than "stall then crash".

## 13. Liquidity final placement (WS15, `17_LIQUIDITY_FINAL_PLACEMENT.csv`)

- PRICE_UP_RANK_UP is more common in LOW_LIQ quartile (0.44) than HIGH_LIQ
  (0.30); PRICE_UP_RANK_DOWN rises with liquidity (0.24 → 0.29).
- Median price-recovery day = 1 in all quartiles — liquidity does not change
  recovery latency.
- HH resilience flat across field-liquidity. **PARK** — no stable
  incremental role.

## 14. SHMC/SHHM locality (WS16, `18_SHMC_SHHM_LOCALITY.csv`)

- SHMC (n=23,364) concentrates in **LOW_BREADTH_LOW_DISP** (10,523 events);
  SHHM (n=79,755) concentrates in **HH** (41,205). The two momentum shapes
  are localized to opposite 2×2 corners.
- Reversal 0.583 vs 0.561, p=7e-7 — SHMC remains the reversion-like shape,
  SHHM the continuation-like shape, but only as LOCAL_ROLE.

## 15. Volatility locality (WS17, `19_VOLATILITY_LOCALITY.csv`)

- In HH: VOL_LO → VOL_HI raises P(stay) 0.83 → 0.95, median dwell 4.5D →
  30D, fwd7 prop 0.31 → 0.59.
- Volatility is an **intensity/retention context inside HH** — not a route
  selector.

## 16. Locality highway registry (WS18, `20_LOCALITY_HIGHWAY_REGISTRY.csv`)

Local roads recorded: HH_STATE_AGE_MATURITY (valid HH age ≥8D), BIFURCATION
regions (route-gate projections only), SECOND_ORDER paths (descriptive),
HH_BIRTH_QUALITY (directional only).

## 17. Cross-agent export (WS19, `21_CROSS_AGENT_CONTEXT_MECH9.parquet`)

- 177,866 event rows keyed by event_id / cmc_id / date, 39 columns.
- Trailing-only field context (t0 and t-lag coords); forward labels
  (cross_state, price_outcome, response_class) explicitly flagged as
  outcomes in `21b_CROSS_AGENT_CONTEXT_SCHEMA.md`.

---

## 18. Nodes (`22_PROMOTE_MERGE_DISSOLVE.csv`)

- **PROMOTE**: HH_STATE_AGE_MATURITY (NEW_NODE, within-HH age coordinate).
- **NEW_NODE**: PERTURBATION_RESPONSE (LOCAL_NODE), HEALTH_STATE_FIELD_MATRIX
  (PRIORITY_MATRIX_EARNED), STRESS_RESPONSE_STRATIFICATION (SUPPORTED,
  contemporaneous), SHMC_SHHM_LOCALITY (LOCAL_ROLE),
  VOLATILITY_LOCALITY (LOCAL_ROLE_INTENSITY).
- **KEEP/DESCRIPTIVE**: HH_MATURITY_WITHIN_EPISODE (NOT_EARNED_SEPARATELY),
  HH_BIRTH_QUALITY (DIRECTIONAL_ONLY), LOCAL_BIFURCATION_SEARCH
  (SHARP_ROUTE_GATE_ONLY), SECOND_ORDER_STATE_PATHS (below bar),
  TRANSITION_VELOCITY (not robust).
- **PARK**: LIQUIDITY_LOCAL_PLACEMENT.

## 19. Nulls (`23_NULL_AND_FAILED_RESULTS.csv`)

- Global pre-event isolated-down divergence: NULL (carried from MECH-8).
- Universal bifurcation boundary: NOT_EARNED (route-gate projections only).
- HH maturity separable from selection: NOT_EARNED_SEPARATELY (n=19).
- Liquidity incremental recovery: PARKED. Volatility route selector: NULL.
- SHMC high-tail activation: NULL (locality only).
- RETEST_RELOAD separability: NULL (carried).
- Breadth composition beyond level: NULL (carried MERGE).

`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`
NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · NO DEPLOYMENT
