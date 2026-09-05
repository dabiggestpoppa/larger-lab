# CRYPTO-ALT-MECH-16 — PREREGISTRATION

**State-Surface Drift, Topology vs Transfer-Function Stability, 6-Cell vs 8-Cell Representation, Conditional Law Change, Common-Forcing Transportability, State x Age Hazard Drift, Entropy / Branch-Closure Stability, Rank-Recruitment Law, Birth-Geometry Transport, Field-Law Changepoints, Market-OS Surface Freeze Audit**

AGENT 1 — CANONICAL FIELD CARTOGRAPHER · terrain research only
NO STRATEGY · NO PNL · NO EXECUTION · NO ENTRY/EXIT · NO SIZING · NO LEVERAGE · NO DEPLOYMENT

---

## 0. Purpose

MECH-15 found:

- raw 16-cell matrix survives permutation falsification
- LOSO ordering stability strong (rho ~0.98)
- early-vs-late half stability strong (rho ~0.83)
- chronological final-20% propagation ordering NEGATIVE (rho ~-0.50)
- 6-cell surface compresses strongly (mean retention 0.915)
- 8-cell surface preserves rank recruitment materially better (0.962 vs 0.743)

This checkpoint does NOT treat that as "unstable matrix". The primary question:

> IS THE MARKET-STATE TOPOLOGY STABLE WHILE THE CONDITIONAL RESPONSE /
> TRANSFER FUNCTION CHANGES ACROSS REGIMES?

Five candidate explanations are distinguished:

1. STATE TOPOLOGY DRIFT — the state assignment itself changed meaning
2. STATE OCCUPANCY / COVARIATE SHIFT — inputs move, conditional law holds
3. CONDITIONAL RESPONSE / TRANSFER-FUNCTION DRIFT — P(outcome|state) changed
4. OUTCOME BASE-RATE SHIFT — outcomes move everywhere, not state-specifically
5. MEASUREMENT / SAMPLE ARTIFACT — support, universe, coverage, single-cycle dominance

## 1. Carried results (verify implementation consistency, do not silently re-derive)

- STATE_AGE_INTERACTION (MECH-14 WS2, MECH-15 WS7/8) — AGE_PARTIAL_OVERLAY
- AGE-RESIDUALIZED ENTROPY = independent coordinate (MECH-14 WS4, MECH-15 base)
- Spatial x temporal constraint axes independent after age residualization (MECH-14 WS15)
- INITIATION_EQUIFINALITY + archetypes where support met (MECH-14 WS7/8)
- COMMON_FORCING_WITH_THRESHOLDS (MECH-14 WS12) — compression candidate, NOT yet frozen
- ORDERLY_SHALLOW_TO_DEEP waterfall repaired + validated (MECH-14 WS11)
- Direction emerges through accumulated constraint specification (MECH-13/14/15)
- DAR framing remains PILOT only (MECH-14 WS20-21)
- MECH-15 6-cell recommended surface + 8-cell reference partition (deterministic replay)

Do NOT resurrect: metastability, universal sequence grammar, single initiation
primitive, single hidden field coordinate, semi-Markov clocks (plain clocks
remain default), price-return direction as a regime definition.

## 2. Surfaces under test

| surface | definition | source |
|---|---|---|
| 16-cell raw | mcell = state x constraint | MECH-15 WS1 |
| 8-cell | average-linkage cut 8 | MECH-15 WS5/6 (deterministic replay) |
| 6-cell | average-linkage cut 6 | MECH-15 recommended |
| 4-cell | average-linkage cut 4 | MECH-15 reference |
| 4-state | HH/HL/LH/LL | MECH-9..15 |

All surfaces are derived from the SAME per-day frame; group labels are
deterministic functions of (mcell, partition).

## 3. Period definitions

- SUBPERIOD: 2020-2021, 2022, 2023, 2024, 2025-2026 (UNKNOWN days excluded from
  subperiod-specific analysis but kept in full-sample analysis)
- CHRONOLOGICAL 80/20: first 80% of days vs last 20%
- EARLY/LATE HALVES: first half vs second half of full span
- LOSO: leave-one-subperiod-out vs full sample
- ROLLING: 365-day windows, step 30 days, where support allows

## 4. Workstreams (pre-registered)

### WS1 — Holdout failure reproduction (02)
Reproduce chronological 80/20, LOSO, halves for ALL five surfaces. Track SIX
orderings per surface: propagation (prop7), reentry (ren7), directional
entropy (next_dir), rank recruitment (rank7), transition (self-transition
share / modal exit), branch entropy (fbe). Each ordering = Spearman rho of
per-group means between periods. Diagnose the -0.50: artifact if it vanishes
under ROBUST-only support restriction or under the reduced surfaces.

### WS2 — 6-cell vs 8-cell freeze audit (03)
Compare 6 vs 8 under chronological stability, LOSO stability, rank
recruitment, propagation, reentry, directional entropy, branch entropy,
transition structure, forcing placement. Allowed: FREEZE_6 / FREEZE_8 /
DUAL_RESOLUTION / NO_FREEZE_YET.

### WS3 — Covariate vs conditional shift (04)
Early vs late: P(X) for breadth, dispersion, forcing, age, entropy, vol,
BTC7, rank activation depth, concentration, stablecoin; P(cell); P(outcome);
P(outcome|cell). Verdict: COVARIATE_SHIFT / TRANSFER_FUNCTION_DRIFT /
MIXED_DRIFT / NO_SHIFT.

### WS4 — State-local transfer functions (05)
Per 6-cell group and subperiod: forcing->propagation, forcing->rank
recruitment, age->propagation, age->reentry, entropy->propagation,
entropy->directional constraint, activation depth->propagation. Simple
interpretable slopes (logistic coefficient or binned slope). No model
optimization. Identify which laws are invariant and which slopes move.

### WS5 — Birth geometry transport (06)
MECH-5 birth coordinates (breadth30, breadth change, top3 concentration, BTC
return, ETH relative, volatility, rank dispersion/depth, leadership width):
re-test discrimination per subperiod, plus whether the SAME birth cohort
produces different later outcomes. Verdict: BIRTH_GEOMETRY_DRIFT /
POST_BIRTH_DYNAMICS_DRIFT / BOTH / NEITHER.

### WS6 — State x age transport (07)
Propagation / reentry / exit hazard and rank recruitment by state x age band
per subperiod. Allowed: INVARIANT_CLOCK / REGIME_MODULATED_CLOCK /
STATE_LOCAL_CLOCK / UNSTABLE_CLOCK.

### WS7 — Survival branch contraction (08)
Condition on survival to 3/5/7/10/14/21D: next-state branch count / entropy
from that point, per subperiod. Question: does time still close branches
consistently across regimes even when outcome ordering changes?

### WS8 — Entropy law transport (09)
entropy->branch closure, entropy->propagation, entropy->directional info:
sign + relative magnitude per subperiod. Allowed: ENTROPY_TOPOLOGY_INVARIANT /
ENTROPY_RESPONSE_DRIFT / ENTROPY_FULL_DRIFT.

### WS9 — Common-forcing law transport (10)
Separate forcing coordinate stability (loadings), threshold stability
(per-patch 50% activation forcing), gain stability (response slope), and
saturation ceiling stability. Allowed: COMMON_FORCING_INVARIANT /
THRESHOLD_DRIFT / GAIN_DRIFT / FULL_FORCING_DRIFT.

### WS10 — Rank-threshold drift (11)
Per rank patch (26-100 .. 1501-2000): common-field intensity for 25/50/75%
activation probability per subperiod and rolling. Are deeper-rank thresholds
stationary? (Candidate explanation for MECH-15 chronological instability.)

### WS11 — Saturation-law drift (12)
Per cycle and coarse patch: onset, ceiling, slope, shape of saturating
response. Allowed: SAME_SHAPE_MOVED_THRESHOLD / SAME_THRESHOLD_CHANGED_GAIN /
SHAPE_CHANGE / STABLE.

### WS12 — Field-law changepoint scan (13)
Rolling estimates + CUSUM-like detection + segmented regression on: state
propagation, rank activation threshold, state-age hazard, entropy-response
slope, forcing-response slope. Name a break ONLY if multiple coordinates
align within a window, >=50 effective observations each side, >1 method.

### WS13 — Law regime candidates (14)
Cluster subperiods by transfer-function signatures (WS4 slopes, WS10
thresholds, WS6 hazards). Name LAW_REGIME_A/B only if clearly earned.
Regimes are defined by law changes, never by price direction.

### WS14 — Invariant node audit (15)
Audit: breadth x dispersion topology, state x age interaction, spatial
activation coordinate, age-residualized entropy, common forcing coordinate,
threshold hierarchy, physical-vs-sigma separation, local highways/exits.
Each: INVARIANT / REGIME_MODULATED / LOCAL_ONLY / DISSOLVE. Freeze input.

### WS15 — Direction as second-order consequence recheck (16)
Directional entropy reduction per period under the constraint chain
STATE -> +AGE -> +ENTROPY -> +BREADTH/ACTIVATION -> +FORCING. If sign
constraint survives while propagation ranking changes, direction and
delivery stay separate OS objects.

### WS16 — Transition topology vs rates (17)
For 6/8-cell: which transitions exist, near-zero, dominant exits,
probabilities per period. Allowed: TOPOLOGY_STABLE_RATES_DRIFT /
TOPOLOGY_DRIFT / FULL_STABILITY / NO_STABLE_STRUCTURE. The core highway test.

### WS17 — Null / artifact audit (18)
Changing support, universe composition, survivorship, rank-band population,
volatility-scale shift, stablecoin coverage, missing-data pattern,
single-cycle dominance. Fail closed.

### WS18 — Free external context pilot (19)
Only sources verified free in CRYPTO_MARKET_OS_TECH_STACK_v0.2_FREE_ONLY.md.
SoSoValue free ETF-flow history IF sufficient local coverage. No scraping,
no paid APIs. Expected DATA_BLOCKED (no local ETF-flow data present).

### WS19-23 — Promote/merge/dissolve, nulls, freeze input, summary, decision

## 5. Decision questions

1. Was the MECH-15 chronological failure reproduced?
2. Is it topology drift or transfer-function drift?
3. Does 6-cell or 8-cell representation survive better?
4. Should Market OS carry dual resolution?
5. Is state x age transportable?
6. Is entropy transportable?
7. Is common forcing transportable?
8. Are rank activation thresholds drifting?
9. Are roads stable while traffic rates change?
10. Did birth geometry change?
11. Which nodes qualify as near-invariants?
12. Is Field Model v1 ready for freeze after this checkpoint?

Possible verdicts:

- PASS_MECH16_TOPOLOGY_STABLE_TRANSFER_DRIFT
- PASS_MECH16_REGIME_MODULATED_FIELD
- PASS_MECH16_STABLE_FIELD_SURFACE
- PASS_MECH16_PARTIAL_INVARIANTS
- FAIL_MECH16_SURFACE_NOT_TRANSPORTABLE

## 6. Governance

- Not a signal matrix. No return optimization. No state definition chosen by
  performance. No PnL columns. No strategy translation.
- Do not force changepoints; do not force external-data explanations.
- Fail closed on artifacts.
- STOP AFTER MECH-16. WAIT FOR HUMAN REVIEW.

`human_review_required = TRUE`
`next_checkpoint_authorized = FALSE`
