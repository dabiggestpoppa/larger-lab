# CRYPTO-ALT-MECH-11 — SUMMARY

**Temporal Field Physics, Multi-Scale Delivery Lattice, Semi-Markov State
Geometry, Perturbation Amplitude, Propagation Radius, Rank-Depth Sequence
Structure & Cross-Agent Health Synthesis**

AGENT 1 — CANONICAL FIELD CARTOGRAPHER · terrain research ONLY
PARENTS: MECH-10 `decf75bc` · MECH-9 `b1de1df7` · LF5 TRUE-PEER `8bd8cfbd` · POST-MECH10 SYNTHESIS `805461c9`

---

## 1. What the field physics looks like now

MECH-11 answers the checkpoint's core question — *what are the local physics
of the state* — with five structural results and a set of honest nulls.

### 1.1 Delivery is a clock lattice, not a single lag

The multi-scale lattice (02) makes the two-clock structure explicit at every
horizon. HH shows the clearest signature:

- **Exit is fast and front-loaded**: P(exit) 0.27 by +1D, 0.52 by +3D, 0.68
  by +7D (AGE_1 HH).
- **Propagation is slow and back-loaded**: P(prop) 0.27 at +1D vs 0.44 at +7D
  vs 0.67 at +30D — the longer the window, the more HH delivers.
- **Reentry reveals fast**: P(reentry) 0.49 by +1D, saturating ~0.76 by +30D
  — failure reveals within days, confirmation takes weeks.
- RANK_RECRUITMENT is the fastest-saturating clock (0.92 by +14D), consistent
  with rank-depth being a later confirmation coordinate.

### 1.2 Competing-risk geometry: probability mass migrates with age

WS4 (05/05b) formalizes the age effect as a **MASS_SHIFT_EARNED** result:

| HH age band | CI reentry 14d | CI propagation 14d |
|---|---|---|
| AGE_1 | 0.734 | 0.532 |
| AGE_15_PLUS | 0.305 | 0.944 |

Surviving HH shifts probability mass from fast failure toward delayed
propagation — the age gradient is a reallocation of competing risks, not just
a rise in one clock.

### 1.3 Semi-Markov audit: dwell time does NOT beat current state

WS3 (04): overall logloss markov 0.705 vs semi-markov 0.741 → **MARKOV_SUFFICIENT**
at the global level. The single exception: LL cell improves with dwell
(0.552 → 0.539), while HH degrades (0.869 → 0.933). Dwell time is a
state-specific descriptor, not a general transition primitive. This is the
first formal support for keeping the plain 4-state transition matrix as the
base model.

### 1.4 Sequence grammar: the common pre-propagation order is
breadth → concentration-release → dispersion → tail → rank

WS2 (03): three COMMON sequences (n≥50, 5/5 subperiods) all begin with
BREADTH_EXPANDS and include CONCENTRATION_RELEASES before rank recruitment.
The top sequence `B→C→D→T→R` (n=65, lift 7.7×) and its permutation
`C→D→R→T→B` (n=55) show the permission→realization ordering: participation
broadens, concentration releases, dispersion differentiates, tails
activate, and rank recruitment arrives last.

### 1.5 Failure mirrors: the first divergence is visible at t0

WS14 (15): the B→D→R sequence succeeds 36.5% of the time; **dispersion and
concentration-release differ at lag 0** (p=3e-10 / p=7e-5, EARLY_DIVERGENCE).
The mirror failure is not a late fade — it is a different state at birth.

---

## 2. Rank-depth physics (new sensors)

- **Propagation radius (07)**: both ANY_TAIL_DAY and HH_DAY are **LOCAL** —
  median band-ppos deltas are ≈0 at +3/+7/+14 across all rank bands. Field
  events do not systematically broadcast into deeper rank bands (median
  response); the earlier "broad propagation" reading came from mean behavior.
- **Rank-depth sequences (08)**: **WATERFALL** dominates — 77% of active days
  at +7D show ascending (shallow→deep) activation order, deep-first 12%.
- **Rank patches (09)**: all five patches are **COHERENT** (internal ppos
  correlation 0.95–0.97) but have distinct identities: UPPER_CORE carries
  the highest false-loner density (32.7%, matching LF5), TRANSITION the
  lowest (12%). Tail share rises monotonically with rank depth.
- **Patch coupling (10)**: all pairs SYNC same-day (r>0.93); no stable
  lead-lag — patches are one synchronized field, not a cascade.

---

## 3. Cross-agent synthesis support

- **Loner field context (11)**: **DISTINCT_GEOMETRY**. FALSE_LONER sits in
  a broader field (breadth 0.379 vs 0.314), higher dispersion, more HH
  (42% vs 35%), older state (median age 9 vs 7). Reconstructed labels match
  LF5's audit exactly (18.4% overall, per-band within 0.5pp).
- **Sigma recovery lattice (12)**: **AMPLITUDE_GRADIENT_NO_FIELD_GRADIENT** —
  recovery probability rises with event amplitude (p_EARLY 0.16 → 0.23 from
  2σ to 4σ+), but t0 field breadth is flat across sigma classes. Recovery
  depth is amplitude-driven, not field-strength-driven.
- **Health transitions (13/14)**: definitions reconciled (M9-health is a
  68.8%-overlapping subset of LF5; gates and rank-velocity thresholds differ).
  PRD→PRU 29.4% at 30D; PRD stays PRD 35.3%; PRD→decay 6.3%. Rehabilitation
  is a slow minority path, consistent with MECH-10.

---

## 4. Local placements

- **Perturbation amplitude (06)**: dispersion jumps show a
  **THRESHOLD_REGION** in fwd7 propagation (0.29 → 0.46 SMALL→LARGE); breadth
  jumps are SMOOTH; volatility shock LARGE collapses propagation (0.33 →
  0.03). Amplitude encodes perturbation strength nonlinearly for dispersion.
- **SHMC/SHHM (16)**: **LOCAL_ALIGNMENT** — SHHM concentrates in HH (51.7%),
  SHMC in LL (45.0%); SHHM is the older/continuation shape, SHMC the
  reversion shape. Local momentum states, not standalone factors.
- **Volatility (17)**: PARKED in 9 cells; CLOCK_MODULATOR in 3 (LH exit
  latency 2D→8D across vol terciles). No route-selector role — consistent
  with MECH-5/9/10.
- **Chain sensors (18)**: TVL velocity informative in HH/LL
  (corr 0.16–0.17), stablecoin activity informative in HH/HL/LH
  (0.20–0.30, LH negative −0.30). DEX volume NULL everywhere. Descriptive
  sensors only.

---

## 5. Node actions (20)

- PROMOTE: MULTI_SCALE_DELIVERY_LATTICE, SEQUENCE_GRAMMAR (3 COMMON),
  COMPETING_RISK_CLOCKS (MASS_SHIFT_EARNED), LONER_FIELD_CONTEXT
  (DISTINCT_GEOMETRY)
- KEEP: HEALTH_DEFINITIONS, VOLATILITY (intensity-only), CHAIN_ACTIVITY
  (sensor), SHMC_SHHM (local)
- DESCRIPTIVE: SEMI_MARKOV (MARKOV_SUFFICIENT), PROPAGATION_RADIUS (LOCAL),
  PERTURBATION_AMPLITUDE, RANK_DEPTH_SEQUENCES (WATERFALL),
  RANK_PATCH_GEOMETRY (COHERENT), FAILURE_MIRRORS (EARLY_DIVERGENCE)

## 6. Nulls carried (21)

- Semi-Markov global improvement: NULL (MARKOV_SUFFICIENT)
- Propagation radius beyond local: NULL (median response ≈0)
- Field-strength gradient in sigma recovery: NULL (amplitude-only)
- DEX volume as participation sensor: NULL
- Patch lead-lag: NULL (synchronized)
- Volatility route selector: NULL (permanent)

## 7. Limits

- Loner labels reconstructed from LF5 residuals (verified against audit).
- Band panel spans LF5 PIT coverage; early-2020 bands thin.
- Health lattice inherits M9 event universe; LF5 cross-check documented,
  not merged (definitions differ).
- No causal claim above L2.

`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`
NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · NO DEPLOYMENT
