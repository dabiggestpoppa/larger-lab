# LOWER-FIELD-11 SUMMARY

**Local laws governing load, damage, absorption, propagation, memory,
containment and sign asymmetry. Start broad, compress from data, preserve
locality.**

PRIMARY PARENT: LF10 `3d90fc9b`  ·  SECONDARY: LF9 `2058bcef`
GLOBAL: MECH-17 `f49bfefd` / MECH-16 `d585ab32` · VERDICT: see
41_LOWER_FIELD_11_DECISION.md

## 1. Local physics hierarchy (02)

Supported feed-forward links: STRUCTURAL_INTEGRITY → ABSORPTION (AUC 0.76),
ABSORPTION_CAPACITY (liq) 0.68, RELATIONAL_REORGANIZATION 0.63,
CONTAINMENT_DECAY 0.61, ACCUMULATED_LOAD → absorption 0.59. Current-shock-load
and propagation-susceptibility links stayed LOCAL/weak. The field organises as
a loose hierarchy, not one causal chain.

## 2. Capacity families & surface (03-05)

Measured capacity families: STRUCTURAL / LIQUIDITY / RANK_HEALTH / STRESS /
RECOVERY (03). The structural-integrity × accumulated-load surface (04) repeats
across all 5 subperiods => **STABLE_LOCAL_CAPACITY_SURFACE**; dependencies mark it **REGIME_LOCAL_CAPACITY** (capacity
is regime-local — holds under rank-depth / global-state / shock-species /
direction / liquidity / neighborhood-stress slicing).

## 3. Absorption vs containment (06)

Feature-rank distinctness => **DISTINCT_LAWS** — absorption and containment respond to
*different* local features: absorption follows membership stability / liquidity
/ rank, containment follows liq + rank-health only modestly. These are separate
local laws.

## 4. Shock primitives, burden & memory (07-09)

Shock decomposed into magnitude / sigma-surprise / duration / acceleration /
gap-jump / liquidity / peer- and rank-relative displacement (07); sigma is
secondary within an abs band. Best prior-shock-burden construction: **days_since_prior**
by purged AUC; kernel family: best grid row **exp_half_life_180d** — memory decays over a
finite horizon rather than being a single long clock.

## 5. Damage accumulation & recovery (10-11)

**NO_FRAGILITY_ACCELERATION** — measured cumulative path burden does NOT monotonically accelerate
fragility in this panel (repeated events partly reflect event-rich liquid
assets). Recovery verdict **STATE_DEPENDENT** — time-without-shock, rank repair and
membership stabilisation restore absorption; state-dependent, no universal full
reset.

## 6. Shock species & churn (12-16)

Stress-deformation pilot: **STABLE_RESPONSE_REGIONS** (descriptive response regions; physics
analogy NOT promoted). Shock species: **FEW_FAMILIES_WITH_CONTINUOUS_OVERLAY**. Topology-churn hierarchy (14),
replacement quality (15) and churn×shock interaction (16) mapped.

## 7. Contagion continuous space & species (17-23)

Continuous contiguity coordinates built (latency / peak / radius / depth /
persistence / generations) (17). Temporal species: **FEW_TEMPORAL_SPECIES** — 4 stable species
across all subperiods. EARLY_CONTAGION: **MIXTURE_SPECIES** — a high-speed continuous
placement, not a discrete singleton. Generations (20) descriptive. Branching
analogy: **SELF_SUSTAINING_LOOKING_SPREAD** (descriptive only). Radius scaling: **WEAK** (weak). Decay
law: exponential daily (23).

## 8. Reactivation & decoupling (24-26)

Reactivation / second-wave coordinates: AFTER_PRIOR_CONTAGION ~0.558 vs ~0.51 base — prior contagion + fresh shock +
unresolved burden raise relapse (24). Persistent decoupling: multi-mechanism
(25), exit paths mapped (26).

## 9. Sign asymmetry & mechanics (27-30)

Major mechanical families (leverage/liquidation/liquidity-withdrawal/order-flow/
collateral) are **DATA_BLOCKED** in the free-only substrate; only
correlation-compression + volume-pressure are locally measurable (27). With the
available 13-gene + mechanical pass, down-side contagion log-odds stays
**IRREDUCIBLE_AFTER_MECHANICS** (28) => IRREDUCIBLE_AFTER_MECHANICS. Correlation compression probed
(29); liquidity×rank-health amplification matrix built (30).

## 10. Upside & global/local memory (31-35)

Per-function upside analogues (31); **STATE_LOCAL** accumulation (32); upside
propagation geometry (33); upside-permission hierarchy (34). Global/local
memory crosscheck: **SEPARATE_LOCAL_GLOBAL_MEMORY** — local shock memory is far stronger than global
field memory and each keeps its own clock.

## Caveats

- Daily resolution; no PIT-safe hourly.
- Contagion generation / branching language is descriptive timing-order only.
- Everything descriptive; LF9 relational predictive NULL stays frozen.
- Sign-asymmetry feeling is conditional on the DATA_BLOCKED mechanical layer.
- No strategy, no PnL, no execution, no sizing, no leverage.
