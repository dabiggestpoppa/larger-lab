# LOWER-FIELD-10 SUMMARY

**Shock & contagion cartography: the internal dimensions / species / temporal
geometry of local physical shock, contagion, decoupling and directional
asymmetry. Start broad, then compress from data; preserve locality.**

PRIMARY PARENT: LF9 `2058bcef` · SECONDARY: LF8 `2d789005` · GLOBAL: MECH-16
`d585ab32` / MECH-15 `8104130d` · VERDICT: see 33_LOWER_FIELD_10_DECISION.md

## 1. Continuous coordinates (02-03)

15 continuous local coordinates measured under the existing relational labels:
peer residual magnitude, neighborhood coherence, membership turnover/entropy,
state-transition rate, decoupling degree, rejoin velocity, contagion breadth,
peer stress / dispersion, rank-health differential, neighborhood momentum,
time-since-transition and persistence duration. Several are redundant
(time_since_transition == persist_duration rho 1.0). PCA pilot: 7 dims retain
eigenvalue > 1. Verdict: MULTIPLE_LOCAL_COORDINATES — a compact basis exists
but not a single factor; keep as a continuous overlay, do not force label
splits (25: CONTINUOUS_OVERLAY_ONLY_PREFERRED).

## 2. Topology churn (04-05)

High-churn events mapped: who leaves / enters, old/new coherence, rank
migration, stress, directional composition, and the forward health of dropped
vs added neighbors. Replacement-quality test in 04 (added-cohort vs
dropped-cohort forward return). Verdict: FEW_STABLE_CHURN_SPECIES
(3 clusters, silhouette ~0.40, all 5 subperiods) — churn is not pure noise;
replacement quality and sign composition carry structure.

## 3. Shock atlas & species (06-08)

Broad local-shock atlas as conditional slices (abs x sigma x liquidity x
neighborhood x direction x duration x rank; global field as overlay in 06b).
Shock species verdict: FEW_SHOCK_SPECIES — two stable families
(deep-illiquid-stressed vs shallow-quiet), each present in all 5 subperiods.
Absorption outcome (ABSORBED/REORGANIZED/PROPAGATED/PERSISTENT) mapped across
all slices (08). Local absorption capacity is a real coordinate (09):
membership stability (purged AUC 0.83) and prior-shock burden (0.72) matter.

## 4. Response curves & path dependence (10-11)

Michaelis-Menten response geometry fit per response, upside vs downside (10).
Path dependence verdict: ACCUMULATION — repeated disturbance ACCUMULATES rather
than resetting (11).

## 5. Early contagion & decoupling deep maps (12-15)

EARLY_CONTAGION anatomy (12) + matched vs non-contagious controls (13).
PERSISTENT_DECOUPLING anatomy (14). Decoupling subspecies verdict:
MULTI_MECHANISM_CONTINUOUS — decoupling is not one stable relational species;
mostly a continuous field with weak internal clustering (15).

## 6. Downside contagion geometry (16-18)

Daily temporal map (16): first peer reaction T1 ~1d, peak contagion T3 ~3d,
decay T4 ~30d, peak peer-negative fraction ~0.73 (n/a downside
contagion events). Spatial map source -> immediate peers -> neighborhood ->
field breadth (17). Contagion coordinates (18): DEPTH and PERSISTENCE are
redundant (rho 0.91); SPEED and RADIUS distinct — report at most 3 coordinates.

## 7. Containment (19)

No dominant single container. Liquidity (purged AUC 0.56) and rank health
(0.55) modestly contain; peer stress and turnover do not. Containment is a
multi-factor, local phenomenon.

## 8. Directional asymmetry — primitive stripping (20-21)

Raw down/up contagion gap 0.2034 (down log-odds 0.931 after 13
covariates, residual p 0.0). Progressive control reduces the gap only
~19% (LIQ and RANK_HEALTH are the largest single reducers; CONCENTRATION
adds back). Verdict: IRREDUCIBLE_SIGN_ASYMMETRY.

## 9. Upside analogue + local permission (22-24)

Per-primitive upside analogue search — downside->upside mirror explicitly NOT
assumed (23). Local upside permission mapped under global-cell overlays (24).

## 10. Granularity + PRD + separability (25-28)

Relational granularity (25): continuous overlay preferred; no forced label
merge (which would destroy the TRUE/FALSE-ISOLATED QC distinction). PRD carry
(26): TEMPORARY_SPLIT PROMOTED, RELATIVE_DECAY LOCAL, rescue DISSOLVED. Roles
assigned (27). Global/local separability (28): PARTIALLY_SEPARABLE — the local
model dominates, global surface adds thin context.

## 11. Key caveats

- Contagion temporal/spatial maps are at DAILY resolution — no PIT-safe hourly
  data in the LF5 substrate (16 states so explicitly).
- Per-peer rank distance not measurable (partial peer map); spatial breadth
  uses touch-fraction + rank depth + field breadth (17).
- Shock/churn "species" and the relational taxonomy are descriptive objects,
  NOT predictors — the LF9 predictive null remains frozen (25/31).
- The 20/21 asymmetry stripping is a descriptive decomposition, not feature
  selection for forecasting.
- No strategy, no PnL, no execution, no sizing, no leverage.
