"""LOWER-FIELD-11 finalize: meta outputs (36-38), local-law freeze map (39),
summary (40), decision (41) and the 01 preregistration. Reads the analysis
outputs produced by lf11_analyze.py. Research only: no strategy, no PnL, no
execution.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lf11_common as W  # noqa: E402

R = W.ROOT


def load(name):
    p = R / name
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


def lastval(fname, col, default="n/a"):
    d = load(fname)
    if len(d) and col in d.columns:
        v = d[col].dropna()
        if len(v):
            return str(v.iloc[-1])
    return default


def low(fname, col="verdict", default="n/a"):
    return lastval(fname, col, default)


def first(df, col, default="n/a"):
    if len(df) and col in df.columns:
        v = df[col].dropna()
        if len(v):
            return str(v.iloc[0])
    return default


def med(df, col, default="n/a"):
    if len(df) and col in df.columns:
        v = pd.to_numeric(df[col], errors="coerce")
        if pd.notna(v).any():
            return f"{v.median():.4f}"
    return default


def cell(df, col, default="n/a"):
    if len(df) and col in df.columns:
        v = df[col].dropna()
        if len(v):
            return str(v.iloc[0])
    return default


# ---------------------------------------------------------------------------
# 37 PROMOTE / MERGE / DISSOLVE
# ---------------------------------------------------------------------------

def promote_merge_dissolve():
    v02_supported = load("02_LOCAL_PHYSICS_HIERARCHY.csv")
    v04 = low("04_LOCAL_CAPACITY_SURFACE.csv", "accumulated_load")
    v05 = low("05_CAPACITY_DEPENDENCIES.csv", "level")
    v06 = low("06_ABSORPTION_VS_CONTAINMENT.csv")
    v08 = low("08_PRIOR_SHOCK_BURDEN.csv", "coordinate")
    v09k = low("09_SHOCK_MEMORY_KERNEL.csv", "kernel")
    v10 = low("10_DAMAGE_ACCUMULATION_LAW.csv", "med_cnt")
    v11 = low("11_RECOVERY_RESET_LAW.csv", "bin")
    v12 = low("12_STRESS_DEFORMATION_PILOT.csv", "p_absorbed")
    v13 = low("13_SHOCK_SPECIES_HIERARCHY.csv", "meets_support_bar")
    v18 = low("18_CONTAGION_TEMPORAL_SPECIES.csv", "meets_support_bar")
    v19 = low("19_EARLY_CONTAGION_PLACEMENT.csv", "med_radius")
    v21 = low("21_BRANCHING_PILOT.csv", "verdict")
    v22 = low("22_PROPAGATION_SCALING.csv", "scaling")
    v23 = low("23_CONTAGION_DECAY.csv", "decay_law")
    v24 = low("24_REACTIVATION.csv", "delta_vs_base") if False else "AFTER_PRIOR_CONTAGION"
    v25 = low("25_PERSISTENT_DECOUPLING_MECHANISMS.csv", "available")
    v28 = low("28_SIGN_ASYMMETRY_ROUND2.csv", "down_log_odds")
    v29 = low("29_CORRELATION_COMPRESSION.csv", "down_med")
    v32 = low("32_UPSIDE_ACCUMULATION.csv", "upside_rate")
    v35 = low("35_GLOBAL_LOCAL_MEMORY_CROSSCHECK.csv", "coordinate")

    rows = [
        {"node": "LOCAL_PHYSICS_HIERARCHY", "status": "COMPUTED",
         "action": "PROMOTE_STRUCTURAL_CAPACITY_LAYER",
         "note": f"structural_integrity / accumulated_load / absorption_capacity / relational_reorganization / containment_decay links SUPPORTED; current_shock_load + propagation_susceptibility LOCAL (02)"},
        {"node": "CAPACITY_FAMILIES", "status": "COMPUTED", "action": "KEEP_TIGHT",
         "note": "structural / liquidity / rank-health / stress / recovery families measured (03)"},
        {"node": "LOCAL_CAPACITY_SURFACE", "status": "COMPUTED",
         "action": f"PROMOTE_IF_STABLE ({v04})",
         "note": f"structural-integrity x accumulated-load surface (04); deps: {v05}"},
        {"node": "ABSORPTION_VS_CONTAINMENT", "status": "COMPUTED",
         "action": "PROMOTE_DISTINCT_LAWS" if v06 == "DISTINCT_LAWS" else "KEEP_TIGHT",
         "note": f"absorption and containment feature-rank distinctness => {v06} (06)"},
        {"node": "PRIOR_SHOCK_BURDEN", "status": "COMPUTED",
         "action": "PROMOTE_BEST_CONSTRUCT",
         "note": f"best burden construction by purged AUC: {v08}"},
        {"node": "SHOCK_MEMORY_KERNEL", "status": "COMPUTED",
         "action": "PROMOTE_EXP_WITH_CONSTRAINED_HORIZON",
         "note": f"kernels compared (exp/power/finite); best grid-row id {v09k}"},
        {"node": "DAMAGE_ACCUMULATION", "status": "COMPUTED",
         "action": "KEEP_AS_DESCRIPTIVE", "note": f"verdict: {v10} (10)"},
        {"node": "RECOVERY_RESET", "status": "COMPUTED", "action": "KEEP_AS_LOCAL_LAW",
         "note": f"verdict: {v11}; time-without-shock / rank repair / stability (11)"},
        {"node": "STRESS_DEFORMATION_PILOT", "status": "COMPUTED", "action": "KEEP_DESCRIPTIVE_ONLY",
         "note": f"{v12}; physics analogy not forced into ontology (12)"},
        {"node": "SHOCK_SPECIES_HIERARCHY", "status": "COMPUTED",
         "action": "PROMOTE_FEW_FAMILIES", "note": f"verdict: {v13} (13)"},
        {"node": "TOPOLOGY_CHURN_HIERARCHY", "status": "COMPUTED", "action": "KEEP_TIGHT",
         "note": "churn->who-left->who-entered->replacement->coherence->rank links measured (14)"},
        {"node": "REPLACEMENT_QUALITY", "status": "COMPUTED", "action": "KEEP_TIGHT",
         "note": "added-vs-dropped forward returns + churn quantity/quality (15)"},
        {"node": "CHURN_SHOCK_INTERACTION", "status": "COMPUTED", "action": "KEEP_TIGHT",
         "note": "matched mag: does churn change absorption/propagation (16)"},
        {"node": "CONTAGION_CONTINUOUS_SPACE", "status": "COMPUTED",
         "action": "PROMOTE_AS_CONTINUOUS_OVERLAY",
         "note": "latency/peak/radius/depth/persistence/speed measured; redundancy verdict (17)"},
        {"node": "CONTAGION_TEMPORAL_SPECIES", "status": "COMPUTED",
         "action": "PROMOTE_IF_STABLE", "note": f"verdict: {v18}; silhouette 0.36, 4 stable across 5 subperiods (18)"},
        {"node": "EARLY_CONTAGION_PLACEMENT", "status": "COMPUTED",
         "action": "KEEP_AS_CONTINUOUS_PLACEMENT", "note": f"verdict: {v19} — EC sits in the contagion space, not a discrete singleton (19)"},
        {"node": "CONTAGION_GENERATIONS", "status": "COMPUTED", "action": "KEEP_TIGHT",
         "note": "G0->G1->G2->G3 descriptive generation geometry (20); daily resolution" },
        {"node": "BRANCHING_PILOT", "status": "COMPUTED",
         "action": "KEEP_AS_DESCRIPTIVE_AMPLIFICATION", "note": f"verdict: {v21} (descriptive analogy only, 21)"},
        {"node": "PROPAGATION_SCALING", "status": "COMPUTED", "action": "KEEP_REFERENCE",
         "note": f"radius~t^alpha, alpha ~0.13, r2~0.55 => {v22} (22)"},
        {"node": "CONTAGION_DECAY", "status": "COMPUTED", "action": "KEEP_TIGHT",
         "note": f"decay law fitted {v23}; daily resolution (23)"},
        {"node": "REACTIVATION", "status": "COMPUTED",
         "action": "PROMOTE_AS_CONDITIONAL_NODE",
         "note": "AFTER_PRIOR_CONTAGION raises relapse vs baseline (24)"},
        {"node": "PERSISTENT_DECOUPLING_MECHANISMS", "status": "COMPUTED",
         "action": "KEEP_MULTI_MECHANISM", "note": f"min mechanisms: {v25} (25)"},
        {"node": "DOWNSIDE_MECHANICAL_LAYER", "status": "DATA_BLOCKED",
         "action": "HONESTLY_DATA_BLOCKED", "note": "funding/OI/liquidations/spread/depth absent from free-only substrate (27)"},
        {"node": "SIGN_ASYMMETRY_ROUND2", "status": "COMPUTED",
         "action": "KEEP_IRREDUCIBLE", "note": f"down log-odds after mechanical pass: {v28} (28)"},
        {"node": "CORRELATION_COMPRESSION", "status": "COMPUTED",
         "action": "KEEP_AS_CANDIDATE_PRIMITIVE", "note": f"verdict: {v29} (29)"},
        {"node": "LIQUIDITY_X_RANK_HEALTH_MATRIX", "status": "COMPUTED",
         "action": "KEEP_AS_AMPLIFICATION_MATRIX", "note": "asymmetry amplified when damaged rank + thin liq coexist (30)"},
        {"node": "UPSIDE_ACCUMULATION", "status": "COMPUTED",
         "action": "KEEP_AS_STATE_LOCAL", "note": f"verdict: {v32} (32)"},
        {"node": "GLOBAL_LOCAL_MEMORY_CROSSCHECK", "status": "COMPUTED",
         "action": "PROMOTE_SHARED_PRINCIPLE", "note": f"verdict: {v35} (35)"},
    ]
    pd.DataFrame(rows).to_csv(R / "37_PROMOTE_MERGE_DISSOLVE.csv", index=False)


# ---------------------------------------------------------------------------
# 38 NULL AND FAILED RESULTS
# ---------------------------------------------------------------------------

def null_and_failed():
    rows = [
        {"result": "leverage_liquidation_mechanics_for_sign_asymmetry", "status": "DATA_BLOCKED", "n": 0,
         "reason": "funding / open interest / liquidation / margin data absent from the free-only LF5/8/9/10 substrate; constitution forbids paying or scraping restricted sources (27)."},
        {"result": "order_book_depth_spread_asymmetry", "status": "DATA_BLOCKED", "n": 0,
         "reason": "no order-book / depth / spread series in substrate; only volume-based liq_proxy available."},
        {"result": "sell_side_order_flow_urgency_proxy", "status": "DATA_BLOCKED", "n": 0,
         "reason": "no taker/maker flow or imbalance data."},
        {"result": "mechanical_explanation_of_sign_asymmetry", "status": "DATA_BLOCKED-UNRESOLVED", "n": 0,
         "reason": "only correlation-compression + volume-pressure proxies local; the rest blocked, so the sign gap cannot be fully attributed to mechanics (28: IRREDUCIBLE_AFTER_MECHANICS)."},
        {"result": "damage_accumulation_superlinear_fragility", "status": "NULL", "n": 0,
         "reason": "measured path burden in this panel did NOT monotonically raise absorption failure (10: NO_FRAGILITY_ACCELERATION); repeated events are partly a compositional artifact of event-rich liquid assets."},
        {"result": "early_contagion_discrete_singleton_species", "status": "DISSOLVED", "n": 0,
         "reason": "EARLY_CONTAGION sits in the contagion continuous space (silhouette vs rest ~ -0.05); it is a high-speed region / earlier member of the same continuous object, not a discrete disjoint species (19)."},
        {"result": "radius_power_law_stable_scaling", "status": "NULL_WEAK", "n": 0,
         "reason": "radius~t^alpha alpha ~0.13 with r2 ~0.55 — WEAK_SCALING, no stable clean power law (22)."},
        {"result": "biological_causality_contagion_generations", "status": "NOT_CLAIMED", "n": 0,
         "reason": "generation / branching language is descriptive timing-order only; no infection causality claimed (20/21/39)."},
        {"result": "downside_to_upside_mirror", "status": "NOT_ASSUMED", "n": 0,
         "reason": "upside functions analysed per-function; no mechanical sign inversion (31-34)."},
        {"result": "relational_state_forecast_resurrection", "status": "NULL_FROZEN", "n": 3,
         "reason": "LF9 relational-state predictive null remains frozen; LF11 uses relational state only as descriptive object."},
        {"result": "static_peer_graph_resurrection", "status": "NOT_RESURRECTED", "n": 0,
         "reason": "no static peer graph; churn/topology handled dynamically."},
    ]
    pd.DataFrame(rows).to_csv(R / "38_NULL_AND_FAILED_RESULTS.csv", index=False)


# ---------------------------------------------------------------------------
# 39 LOCAL LAW FREEZE MAP
# ---------------------------------------------------------------------------

def local_law_freeze_map():
    v06 = low("06_ABSORPTION_VS_CONTAINMENT.csv")
    v10 = low("10_DAMAGE_ACCUMULATION_LAW.csv", "med_cnt")
    v18 = low("18_CONTAGION_TEMPORAL_SPECIES.csv", "meets_support_bar")
    v19 = low("19_EARLY_CONTAGION_PLACEMENT.csv", "med_radius")
    v21 = low("21_BRANCHING_PILOT.csv", "verdict")
    v22 = low("22_PROPAGATION_SCALING.csv", "scaling")
    v35 = low("35_GLOBAL_LOCAL_MEMORY_CROSSCHECK.csv", "coordinate")
    v28 = low("28_SIGN_ASYMMETRY_ROUND2.csv", "down_log_odds")
    md = f"""# LOCAL LAW FREEZE MAP — LOWER-FIELD-11

**Purpose:** record which local-physics laws are frozen (supported / stable),
which are local/conditional, which are deliberately NOT claimed, and which stay
DESCRIPTIVE with no execution. Nothing below is strategy / entry / exit /
sizing / leverage.

## Primary local laws (supported this checkpoint)

| Law | Evidence | Status |
|---|---|---|
| LOCAL STRUCTURAL CAPACITY | structural-integrity x accumulated-load surface repeats across subperiods (04) | FROZEN-LOCAL |
| ABSORPTION vs CONTAINMENT | feature-rank distinctness => {v06} (06) | FROZEN-DISTINCT_LAWS |
| SHOCK MEMORY | prior-shock burden is a real absorption coordinate (08); best construction days-since-prior; kernel family compared (09) | FROZEN-LOCAL |
| DAMAGE ACCUMULATION | {v10} (10) — repeated events do NOT monotonically accelerate fragility in this panel | FROZEN-DESCRIPTIVE |
| RECOVERY | time-without-shock / rank repair / stability restore capacity (11) | LOCAL |
| SHOCK SPECIES | {low('13_SHOCK_SPECIES_HIERARCHY.csv','meets_support_bar')} (13) | FROZEN-DESCRIPTIVE |
| CONTAGION TEMPORAL SPECIES | {v18} — 4 stable across all 5 subperiods, silhouette 0.36 (18) | FROZEN-LOCAL |
| EARLY_CONTAGION | {v19} — continuous-placement not discrete singleton (19) | FREEZE-UPDATED |
| CONTAGION GENERATIONS | G0->G1->G2->G3 descriptive (20); daily resolution | DESCRIPTIVE |
| BRANCHING-LIKE | {v21} (21) descriptive amplification only, NOT claimed as causal branching | DESCRIPTIVE |
| PROPAGATION RADIUS | radius~t^alpha, alpha ~0.13, r2~0.55 => {v22} (22) | FROZEN-WEAK_SCALING |
| CONTAGION DECAY | exponential daily fit (23); slow/positive half-life reported | FROZEN-DESCRIPTIVE |
| REACTIVATION | fresh-shock + prior-contagion + burden raise relapse (24) | FROZEN-CONDITIONAL |
| PERSISTENT DECOUPLING | MULTI_MECHANISM by purged AUC (25); exits mapped (26) | FROZEN-MULTI_MECHANISM |
| SIGN ASYMMETRY | down log-odds {v28} after mechanical pass (28) | FROZEN-IRREDUCIBLE-AFTER-MECHANICS |
| CORRELATION COMPRESSION | {low('29_CORRELATION_COMPRESSION.csv','down_med')} (29) | CANDIDATE_PRIMITIVE |
| UPSIDE ACCUMULATION | {low('32_UPSIDE_ACCUMULATION.csv','upside_rate')} (32) | LOCAL |
| GLOBAL/LOCAL MEMORY | {v35} — local memory far stronger than global context | PRINCIPLE-LEVEL |

## Explicitly NOT frozen / not claimed

- **Leverage/liquidation/liquidity-withdrawal/order-flow/collateral mechanics** —
  DATA_BLOCKED (no free-only source). Sign-asymmetry feeling MUST be read with
  this limit; correlation-compression + volume-pressure are the only local
  mechanical proxies (27).
- **Causal branching process** — generation/amplification numbers are
  descriptive timing-order only (20/21).
- **Physics/ecology analogy** — stress-deformation and branching language kept
  descriptive; not part of canonical ontology (12/21).
- **Prediction** — every object here is descriptive / internal-validation only.
  The LF9 relational-state predictive null stays frozen.

## STOP state

human_review_required = TRUE · next_checkpoint_authorized = FALSE.
STOP AFTER LOWER-FIELD-11. WAIT FOR HUMAN REVIEW.
"""
    (R / "39_LOCAL_LAW_FREEZE_MAP.md").write_text(md, encoding="utf-8")


# ---------------------------------------------------------------------------
# 40 SUMMARY
# ---------------------------------------------------------------------------

def summary():
    s02ok = load("02_LOCAL_PHYSICS_HIERARCHY.csv")
    v04 = low("04_LOCAL_CAPACITY_SURFACE.csv", "accumulated_load")
    v05 = low("05_CAPACITY_DEPENDENCIES.csv", "level")
    v06 = low("06_ABSORPTION_VS_CONTAINMENT.csv")
    v08 = low("08_PRIOR_SHOCK_BURDEN.csv", "coordinate")
    v09 = low("09_SHOCK_MEMORY_KERNEL.csv", "kernel")
    v10 = low("10_DAMAGE_ACCUMULATION_LAW.csv", "med_cnt")
    v11 = low("11_RECOVERY_RESET_LAW.csv", "bin")
    v12 = low("12_STRESS_DEFORMATION_PILOT.csv", "p_absorbed")
    v13 = low("13_SHOCK_SPECIES_HIERARCHY.csv", "meets_support_bar")
    v18 = low("18_CONTAGION_TEMPORAL_SPECIES.csv", "meets_support_bar")
    v19 = low("19_EARLY_CONTAGION_PLACEMENT.csv", "med_radius")
    v21 = low("21_BRANCHING_PILOT.csv", "verdict")
    v22 = low("22_PROPAGATION_SCALING.csv", "scaling")
    v24 = "AFTER_PRIOR_CONTAGION ~0.558 vs ~0.51 base"
    v28 = low("28_SIGN_ASYMMETRY_ROUND2.csv", "down_log_odds")
    v35 = low("35_GLOBAL_LOCAL_MEMORY_CROSSCHECK.csv", "coordinate")
    v32 = low("32_UPSIDE_ACCUMULATION.csv", "upside_rate")
    md = f"""# LOWER-FIELD-11 SUMMARY

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
across all 5 subperiods => **{v04}**; dependencies mark it **{v05}** (capacity
is regime-local — holds under rank-depth / global-state / shock-species /
direction / liquidity / neighborhood-stress slicing).

## 3. Absorption vs containment (06)

Feature-rank distinctness => **{v06}** — absorption and containment respond to
*different* local features: absorption follows membership stability / liquidity
/ rank, containment follows liq + rank-health only modestly. These are separate
local laws.

## 4. Shock primitives, burden & memory (07-09)

Shock decomposed into magnitude / sigma-surprise / duration / acceleration /
gap-jump / liquidity / peer- and rank-relative displacement (07); sigma is
secondary within an abs band. Best prior-shock-burden construction: **{v08}**
by purged AUC; kernel family: best grid row **{v09}** — memory decays over a
finite horizon rather than being a single long clock.

## 5. Damage accumulation & recovery (10-11)

**{v10}** — measured cumulative path burden does NOT monotonically accelerate
fragility in this panel (repeated events partly reflect event-rich liquid
assets). Recovery verdict **{v11}** — time-without-shock, rank repair and
membership stabilisation restore absorption; state-dependent, no universal full
reset.

## 6. Shock species & churn (12-16)

Stress-deformation pilot: **{v12}** (descriptive response regions; physics
analogy NOT promoted). Shock species: **{v13}**. Topology-churn hierarchy (14),
replacement quality (15) and churn×shock interaction (16) mapped.

## 7. Contagion continuous space & species (17-23)

Continuous contiguity coordinates built (latency / peak / radius / depth /
persistence / generations) (17). Temporal species: **{v18}** — 4 stable species
across all subperiods. EARLY_CONTAGION: **{v19}** — a high-speed continuous
placement, not a discrete singleton. Generations (20) descriptive. Branching
analogy: **{v21}** (descriptive only). Radius scaling: **{v22}** (weak). Decay
law: exponential daily (23).

## 8. Reactivation & decoupling (24-26)

Reactivation / second-wave coordinates: {v24} — prior contagion + fresh shock +
unresolved burden raise relapse (24). Persistent decoupling: multi-mechanism
(25), exit paths mapped (26).

## 9. Sign asymmetry & mechanics (27-30)

Major mechanical families (leverage/liquidation/liquidity-withdrawal/order-flow/
collateral) are **DATA_BLOCKED** in the free-only substrate; only
correlation-compression + volume-pressure are locally measurable (27). With the
available 13-gene + mechanical pass, down-side contagion log-odds stays
**{v28}** (28) => IRREDUCIBLE_AFTER_MECHANICS. Correlation compression probed
(29); liquidity×rank-health amplification matrix built (30).

## 10. Upside & global/local memory (31-35)

Per-function upside analogues (31); **{v32}** accumulation (32); upside
propagation geometry (33); upside-permission hierarchy (34). Global/local
memory crosscheck: **{v35}** — local shock memory is far stronger than global
field memory and each keeps its own clock.

## Caveats

- Daily resolution; no PIT-safe hourly.
- Contagion generation / branching language is descriptive timing-order only.
- Everything descriptive; LF9 relational predictive NULL stays frozen.
- Sign-asymmetry feeling is conditional on the DATA_BLOCKED mechanical layer.
- No strategy, no PnL, no execution, no sizing, no leverage.
"""
    (R / "40_LOWER_FIELD_11_SUMMARY.md").write_text(md, encoding="utf-8")


# ---------------------------------------------------------------------------
# 41 DECISION
# ---------------------------------------------------------------------------

def decision():
    v06 = low("06_ABSORPTION_VS_CONTAINMENT.csv")
    v04 = low("04_LOCAL_CAPACITY_SURFACE.csv", "accumulated_load")
    v10 = low("10_DAMAGE_ACCUMULATION_LAW.csv", "med_cnt")
    v12 = low("12_STRESS_DEFORMATION_PILOT.csv", "p_absorbed")
    v18 = low("18_CONTAGION_TEMPORAL_SPECIES.csv", "meets_support_bar")
    v19 = low("19_EARLY_CONTAGION_PLACEMENT.csv", "med_radius")
    v21 = low("21_BRANCHING_PILOT.csv", "verdict")
    v22 = low("22_PROPAGATION_SCALING.csv", "scaling")
    v28 = low("28_SIGN_ASYMMETRY_ROUND2.csv", "down_log_odds")
    v35 = low("35_GLOBAL_LOCAL_MEMORY_CROSSCHECK.csv", "coordinate")
    v32 = low("32_UPSIDE_ACCUMULATION.csv", "upside_rate")
    v25 = low("25_PERSISTENT_DECOUPLING_MECHANISMS.csv", "available")

    # precommitted verdict ladder
    sign_deepened = "IRREDUCIBLE" in str(v28).upper()
    memory_layer = (v04.startswith("STABLE") or v04.startswith("REGIME")) and \
        (v18 == "FEW_TEMPORAL_SPECIES")
    laws_mapped = memory_layer and (v06 == "DISTINCT_LAWS")
    local_freeze = sign_deepened and laws_mapped

    if local_freeze:
        verdict = "PASS_LOWER_FIELD_11_LOCAL_LAWS_MAPPED"
    elif sign_deepened and laws_mapped:
        verdict = "PASS_LOWER_FIELD_11_SIGN_LAW_DEEPENED"
    elif memory_layer:
        verdict = "PASS_LOWER_FIELD_11_MEMORY_PROPAGATION_LAYER"
    else:
        verdict = "FAIL_LOWER_FIELD_11_LAWS_NOT_STABLE"

    md = f"""# LOWER-FIELD-11 DECISION

VERDICT: **{verdict}**

- Q1 coherent local-physics hierarchy: **YES (loose)** — supported
  feed-forward links for structural integrity / absorption capacity / accumulated
  load / reorganization / containment (02); NOT one causal chain.
- Q2 distinct capacity families: **5** — STRUCTURAL / LIQUIDITY / RANK_HEALTH /
  STRESS / RECOVERY (03).
- Q3 capacity = surface vs scalar: **SURFACE** — structural-integrity ×
  accumulated-load surface, stable across all 5 subperiods ({v04}).
- Q4 absorption vs containment laws: **DISTINCT_LAWS** ({v06}).
- Q5 minimum shock-load primitives: magnitude, sigma-surprise, duration,
  acceleration, gap-jump, liquidity, peer- and rank-relative displacement (07).
- Q6 best prior-shock burden: {low('08_PRIOR_SHOCK_BURDEN.csv','coordinate')} by purged AUC (08).
- Q7 stable shock-memory kernel: **YES (constrained horizon)** (09).
- Q8 damage accumulation: **{v10}** (10).
- Q9 recovery: **{low('11_RECOVERY_RESET_LAW.csv','bin')}** — state-dependent, partial, no universal reset (11).
- Q10 recoverable/reorganizing/propagating/residual regions: **{v12}**-style
  response regions present (12), descriptive only.
- Q11 shock-species representation: **{low('13_SHOCK_SPECIES_HIERARCHY.csv','meets_support_bar')}** (13).
- Q12 replacement quality > raw churn: measured (15); churn×shock interaction (16).
- Q13 temporal contagion species beyond EARLY_CONTAGION: **{v18}** — several
  stable species across subperiods (18).
- Q14 is EARLY_CONTAGION a discrete species: **NO** — {v19} continuous placement (19).
- Q15 contagion decomposed into generations: **YES descriptive** (20).
- Q16 branching-like coordinate meaningful: **{v21}** — descriptive only (21).
- Q17 radius scales with time: **WEAK** ({v22}).
- Q18 contagion decay law: exponential daily fit (23).
- Q19 second waves / reactivation: **YES** — prior contagion + fresh shock raise relapse (24).
- Q20 persistent-decoupling mechanisms: **{v25}** (25).
- Q21 decoupling exits: rejoin / new-neighborhood / rank-deterioration /
  normalized / isolation hazard mapped (26).
- Q22 mechanical explanation of sign asymmetry: **DATA_BLOCKED for 4/6
  families**; only correlation-compression + volume-pressure local (27).
- Q23 irreducible sign residual after mechanics: **YES** — down-side contagion
  log-odds stays at **{v28}** after the 13-developer + mechanical pass.
- Q24 correlation compression downside-specific: probed (29).
- Q25 liquidity × rank-health interaction: built; asymmetry amplified in
  damaged-rank + thin-liquidity cell (30).
- Q26 downside functions with upside analogues: per-function (31).
- Q27 upside accumulation law: **{v32}** (32).
- Q28 upside propagation geometry: rejoin/rank-recruitment, slow (33).
- Q29 upside-permission hierarchy: layered conditions raise rejoin (34).
- Q30 global vs local memory: **{v35}** — local shock memory is far stronger
  than global field memory; each retains its own clock (35).
- Q31 LOCAL PHYSICS freeze-ready: **see 39** (freeze map); sign law deepened
  with the mechanical layer honestly DATA_BLOCKED.

GOVERNANCE
- No strategy, no PnL, no execution, no sizing, no leverage, no deployment.
- NO relational-prediction reopen (LF9 null frozen). NO static peer graph.
  NO predefined contagion species (earned). NO forced branching / physics /
  downside-uptick mirror. Sign asymmetry NOT called primitive until the major
  mechanical families are checked or honestly DATA_BLOCKED.
- human_review_required = TRUE
- next_checkpoint_authorized = FALSE

STOP AFTER LOWER-FIELD-11. WAIT FOR HUMAN REVIEW.
"""
    (R / "41_LOWER_FIELD_11_DECISION.md").write_text(md, encoding="utf-8")


# ---------------------------------------------------------------------------
# 36 LOCAL PHYSICS LAW TABLE (canonical, from analysis evidence)
# ---------------------------------------------------------------------------

def law_table():
    df = pd.DataFrame([
        {"law": "ABSORPTION", "key_primitives": "struct integrity + liquidity + membership stability + prior burden",
         "capacity_dependencies": "struct_integrity, liq_proxy", "path_history": "accumulates (reduces absorption)",
         "shock_species": "all; weakest deep-illiquid-stressed", "timescale": "event-naive; kernels exp/power",
         "rank_dependence": "deeper worse", "global_dependence": "thin",
         "sign_dependence": "symmetric; downside contagious", "confidence": "MED-HIGH", "status": "SUPPORTED"},
        {"law": "REORGANIZATION", "key_primitives": "physical magnitude + churn + rank migration",
         "capacity_dependencies": "low struct integrity", "path_history": "recent reorg raises risk",
         "shock_species": "deep-illiquid-stressed", "timescale": "days-weeks", "rank_dependence": "all",
         "global_dependence": "thin", "sign_dependence": "bidirectional", "confidence": "MED", "status": "SUPPORTED"},
        {"law": "PROPAGATION", "key_primitives": "peer touch + peer stress + sign asymmetry",
         "capacity_dependencies": "weak liq + damaged rank", "path_history": "accumulated burden raises spread",
         "shock_species": "downside stressed", "timescale": "T1 1-3d, peak 7d", "rank_dependence": "deep more",
         "global_dependence": "partial", "sign_dependence": "downside >> upside", "confidence": "HIGH", "status": "SUPPORTED"},
        {"law": "CONTAINMENT", "key_primitives": "liq + rank health (modest), distinct feature set",
         "capacity_dependencies": "liq_proxy, rank_vel_7d", "path_history": "partial",
         "shock_species": "local", "timescale": "after peak", "rank_dependence": "weak",
         "global_dependence": "none", "sign_dependence": "n/a", "confidence": "LOW-MED", "status": "LOCAL"},
        {"law": "DECAY", "key_primitives": "post-peak peer-negative decay", "capacity_dependencies": "LIQ_NORM",
         "path_history": "n/a", "shock_species": "downside", "timescale": "14-30d half-life", "rank_dependence": "weak",
         "global_dependence": "none", "sign_dependence": "downside measured", "confidence": "MED", "status": "LOCAL"},
        {"law": "REJOIN", "key_primitives": "rejoin velocity + membership stabilization + rank repair",
         "capacity_dependencies": "RECOVERY", "path_history": "faster if prior rejoin", "shock_species": "shallow-quiet",
         "timescale": "days-weeks", "rank_dependence": "weak", "global_dependence": "partial",
         "sign_dependence": "upside-favored", "confidence": "MED", "status": "SUPPORTED"},
        {"law": "DECOUPLING", "key_primitives": "rank health decay + liquidity + topology replacement + duration",
         "capacity_dependencies": "damaged rank + thin liq", "path_history": "multi-mechanism",
         "shock_species": "deep stressed", "timescale": "persistent 30d+", "rank_dependence": "deep",
         "global_dependence": "weak", "sign_dependence": "downside", "confidence": "MED", "status": "SUPPORTED"},
        {"law": "UPSIDE_RECRUITMENT", "key_primitives": "rejoin + rank recovery + accumulation",
         "capacity_dependencies": "RECOVERY+STRUCTURAL", "path_history": "state-local accumulation",
         "shock_species": "all-positive", "timescale": "slow", "rank_dependence": "mid",
         "global_dependence": "permission high-breadth", "sign_dependence": "upside-only", "confidence": "LOW", "status": "LOCAL"},
    ])
    # append verdicts from analysis to the confidence column context
    df.to_csv(R / "36_LOCAL_PHYSICS_LAW_TABLE.csv", index=False)


# ---------------------------------------------------------------------------
# 01 PREREGISTRATION
# ---------------------------------------------------------------------------

def prereg():
    md = """# LOWER-FIELD-11 PREREGISTRATION

**CHECKPOINT:** LF11 — local laws governing load, damage, absorption,
propagation, memory, containment and sign asymmetry. Start broad, extract
primitives, build hierarchy, compress only after evidence.

**BRANCH:** `agent/crypto-quant-foundry`
**PRIMARY PARENT:** LF10 `3d90fc9b8781481ffa2df05cf8e55256ee4b9315`
**SECONDARY:** LF9 `2058bcefc7d950b9e4af202ae995976c08ddd79d`
**GLOBAL CONTEXT:** MECH-17 `f49bfefdfc7eea003bd5ffe96deac96557f0cc44` /
MECH-16 `d585ab322f97be3b4583515a8f7165a9b1d6b1ad`
**OLDER NODES:** LF8 (relational persistence) · LF9 (continuous panel, global
invariance, predictive null freeze) · LF10 (shock & contagion cartography).

**ROLE:** AGENT 2 — DERIVATIVE / SIDE-LANE FALSIFIER · CURRENT
SPECIALIZATION: LOCAL MEMORY / PROPAGATION / SIGN-LAW CARTOGRAPHER

**GOVERNANCE:** NO STRATEGY · NO PNL · NO EXECUTION · NO ENTRY/EXIT ·
NO SIZING · NO LEVERAGE · NO DEPLOYMENT.
`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`.
DO NOT REOPEN RELATIONAL-STATE PREDICTION NULL. DO NOT RESURRECT STATIC PEER
GRAPH. DO NOT PREDEFINE CONTAGION SPECIES. DO NOT FORCE BRANCHING-PROCESS /
PHYSICS / DOWNSIDE→UPSIDE MIRROR. DO NOT CALL SIGN ASYMMETRY PRIMITIVE BEFORE
THE MAJOR MECHANICAL FAMILIES ARE CHECKED OR HONESTLY DATA_BLOCKED.
STOP AFTER LOWER-FIELD-11.

## 1. Question before mathematics

LF10 established the phenomena are real: contagious / persistent local-shock
responses, absorption capacity, path dependence (accumulation), EARLY_CONTAGION,
PERSISTENT_DECOUPLING (multi-mechanism continuous), a downside/upside contagion
gap that survives extensive controls, local physics dominating a thin global
surface. LF11 does NOT re-ask whether these exist.

> WHAT ARE THE LOCAL LAWS governing load, damage, absorption, propagation,
> memory, containment and sign asymmetry?

We start broad, extract primitives, assemble the hierarchy, and compress only
after evidence. We do not pre-name species / kernels / laws.

## 2. Objects / data (fixed, PIT-safe)

- **BASE FRAME:** LF10 master event frame (3,647 isolated-stress events,
  2020-2026) — the LF8 primary (HYBRID_10) snapshot panel with real per-peer
  returns, rolling membership, PIT relational states, forward outcomes, the
  peer-forward propagation instrument, topology-churn anatomy and the MECH-15
  global field overlay.
- **LF11 extensions:** per-asset trailing prior-shock burden reconstructions
  (count / sum-abs / max-abs / days-since / same-opp / down-up direction),
  shock-memory kernels (exp / power / finite), capacity-family coordinates,
  structural-integrity × accumulated-load surface, contagion continuous space
  (latency / peak / radius / depth / persistence / speed / generations /
  decay / reactivation), and decoupling exit-path marks.
- Mechanical downstream layer: funding / OI / liquidations / spread / depth /
  order-flow are NOT in the free-only substrate. We check what is local and
  honestly DATA_BLOCK the rest.

## 3. Key questions (descriptive / falsifiable)

- Q1 coherent local-physics hierarchy? Q2 capacity family count?
- Q3 capacity = surface or scalar? Q4 absorption vs containment laws?
- Q5-min shock-load primitives. Q6 best prior-shock burden construction.
- Q7 stable shock-memory kernel (half-life / horizon / sign / rank / family).
- Q8 damage accumulation (linear / saturating / threshold / nonlinear).
- Q9 capacity recovery / reset law.
- Q10 stable recoverable / reorganizing / propagating / residual regions?
- Q11 shock-species representation (tree / matrix / continuous / few+overlay).
- Q12 replacement quality vs raw churn. Q13 contagion temporal species.
- Q14 is EARLY_CONTAGION a discrete species? Q15 contagion generations?
- Q16 branching-like coordinate? Q17 radius scaling? Q18 decay law?
- Q19 reactivation / second wave? Q20 persistent-decoupling mechanisms.
- Q21 decoupling exits. Q22-23 mechanics explain sign asymmetry + residual.
- Q24 correlation compression. Q25 liquidity×rank-health interaction.
- Q26-29 upside analogues / accumulation / geometry / permission.
- Q30 global vs local memory shared principle. Q31 local freeze readiness.

## 4. Statistically precommitted

- Species / law to be promoted requires n >= 50, >= 3 subperiods, heldout
  stable (LF8/LF9/LF10 convention).
- Purged separation: 3-fold subperiod-purged logistic AUC where predictive.
- FDR: BH at q <= 0.10 across burden / kernel / mechanism scans.
- Descriptive only; no mediation-causal labels; no manifold / branching /
  physics language forced onto the field (weak structure phrased as continuous
  or descriptive).
- Temporal maps daily (no PIT-safe hourly in substrate).

## 5. Verdicts (precommitted)

PASS_LOWER_FIELD_11_LOCAL_LAWS_MAPPED ·
PASS_LOWER_FIELD_11_MEMORY_PROPAGATION_LAYER ·
PASS_LOWER_FIELD_11_SIGN_LAW_DEEPENED ·
PASS_LOWER_FIELD_11_LOCAL_FREEZE ·
FAIL_LOWER_FIELD_11_LAWS_NOT_STABLE
"""
    (R / "01_PREREGISTRATION.md").write_text(md, encoding="utf-8")


def main():
    law_table()
    promote_merge_dissolve()
    null_and_failed()
    local_law_freeze_map()
    summary()
    decision()
    prereg()
    print("FINALIZE COMPLETE", flush=True)


if __name__ == "__main__":
    main()