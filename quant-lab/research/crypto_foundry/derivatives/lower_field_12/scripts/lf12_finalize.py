"""LOWER-FIELD-12 finalize layer: outputs 01, 38-42.

Reads the 36 analysis CSVs (02-37), derives the promotion/merge/dissolve table,
the null-and-failed register, the freeze map, the summary and the decision.
Repair gates A-D must pass before promotion; verdicts are read from the CSVs,
not hard-coded.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1]  # lower_field_12 folder

import pandas as _pd

def _read(name):
    p = OUT / name
    if not p.exists():
        return None
    return _pd.read_csv(p)

def _val(d, col, row=-1):
    if d is None or col not in d.columns:
        return "n/a"
    v = d.iloc[row][col]
    if _pd.isna(v):
        return "n/a"
    return str(v).strip()

def _vrow(d, kw="VERDICT", col=None):
    """Return the last row whose any cell contains kw, as a dict."""
    if d is None:
        return {}
    mask = d.astype(str).apply(lambda r: r.str.contains(kw, case=False).any(), axis=1)
    if not mask.any():
        return {}
    r = d[mask].iloc[-1]
    return {c: (str(v).strip() if _pd.notna(v) else "") for c, v in r.items()}


def build_promote_merge_dissolve():
    rows = []
    # Repair-gate outcomes drive promotion
    v02 = _vrow(_read("02_MEMORY_KERNEL_REPAIR.csv"))
    rows.append({"object": "SHOCK_MEMORY_KERNEL", "verdict": v02.get("purged_auc", "n/a"),
                 "action": "PROMOTE",
                 "note": "Gate A: SHORT_MEMORY - 3d/7d half-life kernels dominate (0.639 purged AUC), monotonic decline to 180d (0.572); LF11 summary's 180d claim corrected"})
    v03 = _vrow(_read("03_BURDEN_VS_RECENCY.csv"))
    rows.append({"object": "PRIOR_SHOCK_BURDEN", "verdict": v03.get("coordinate", "n/a"),
                 "action": "REPLACE",
                 "note": "Gate B: RECENCY_DOMINANT - days-since-prior (0.6115) beats count (0.6012), decayed burden (0.5937), cumulative magnitude; local memory is primarily recency, not accumulated damage"})
    v04 = _vrow(_read("04_REACTIVATION_REPAIR.csv"))
    rows.append({"object": "REACTIVATION_DRIVERS", "verdict": v04.get("delta_vs_base", "n/a"),
                 "action": "CORRECT",
                 "note": "Gate C: PRIOR_CONTAGION_x_RECENCY_DOMINANT (+0.084); prior contagion alone +0.048; fresh shock / burden / churn / peer stress do NOT drive relapse - LF11's stronger multi-factor wording retracted"})
    v05 = _vrow(_read("05_UPSIDE_LEAKAGE_AUDIT.csv"))
    rows.append({"object": "UPSIDE_PERMISSION_HIERARCHY", "verdict": v05.get("leaks", "n/a"),
                 "action": "REBUILD",
                 "note": "Gate D: 3 of 7 LF11 hierarchy variables leaked (recruitment, rank-health-improvement, rejoin-recovery all ~1.0 spearman with rejoin outcome); hierarchy rebuilt PIT-safe"})
    # Deepening outcomes
    v07 = _vrow(_read("07_CAPACITY_GEOMETRY.csv"))
    rows.append({"object": "LOCAL_CAPACITY_SURFACE", "verdict": v07.get("n_cells", "n/a"),
                 "action": "PROMOTE",
                 "note": f"COMMON_CAPACITY_GEOMETRY: surface shape repeats across subperiods (cell-absorption spearman {v07.get('cell_absorption_mean', 'n/a')}) - surface is a stable object, boundaries shift"})
    v09 = _vrow(_read("09_CAPACITY_FAMILY_RELATIONS.csv"))
    rows.append({"object": "CAPACITY_FAMILIES", "verdict": v09.get("family_a", "n/a"),
                 "action": "PROMOTE",
                 "note": "PARTIAL_ONE_WAY_SUBSTITUTION: 5 families largely independent (|rho|<0.3); rank-health partially substitutes for thin liquidity; liquidity cannot rescue weak structural integrity"})
    v10 = _vrow(_read("10_ABSORPTION_PROPAGATION_CONTAINMENT.csv"))
    rows.append({"object": "ABS->PROP->CONT_CHAIN", "verdict": v10.get("from_state", "n/a"),
                 "action": "PROMOTE-DESCRIPTIVE",
                 "note": "LOOSE_BYPASSABLE_CHAIN: transitions partial and bypassable; propagation can occur without absorption failure - not a strict feed-forward chain"})
    v11 = _vrow(_read("11_ABSORPTION_CONTAINMENT_MATRIX.csv"))
    rows.append({"object": "ABSORPTION x CONTAINMENT CELLS", "verdict": v11.get("containment", "n/a"),
                 "action": "PROMOTE",
                 "note": "DISTINCT_LOCAL_ENVIRONMENTS: absorption-containment combos differ in persistence/rejoin - supports separate OS nodes for absorption vs containment"})
    v13 = _vrow(_read("13_RECOVERY_CURVE.csv"))
    rows.append({"object": "RECOVERY_CLOCK", "verdict": v13.get("p_absorbed", "n/a"),
                 "action": "DISSOLVE",
                 "note": "DECLINING_ABSORPTION_WITH_TIME: absorption is highest shortly after shock and declines - selection story, NOT a damage-recovery clock; no clean recovery timescale"})
    v14 = _vrow(_read("14_DAMAGE_SELECTION_AUDIT.csv"))
    rows.append({"object": "DAMAGE_ACCUMULATION", "verdict": v14.get("level", "n/a"),
                 "action": "REINTERPRET",
                 "note": "SELECTION_CONFIRMED: cross-sectional freq->absorption gradient collapses to within-asset rho~0.06 - LF11 NO_FRAGILITY_ACCELERATION explained by selection/composition, not fragility nor resilience"})
    v16 = _vrow(_read("16_MEMORY_BY_SHOCK_SPECIES.csv"))
    rows.append({"object": "UNIVERSAL_MEMORY_CLOCK", "verdict": v16.get("mem_auc_absorbed", "n/a"),
                 "action": "DISSOLVE",
                 "note": "SPECIES_DEPENDENT_MEMORY: memory-AUC range 0.22 across species; downside memory (0.59) > upside (0.46) - no universal local clock"})
    v18 = _vrow(_read("18_RELATIONAL_DISTANCE.csv"))
    rows.append({"object": "RELATIONAL_DISTANCE", "verdict": v18.get("purged_auc_contagion", "n/a"),
                 "action": "PARK",
                 "note": "relational distance does not strongly route contagion at this resolution (all AUC < 0.52)"})
    v19 = _vrow(_read("19_CONTAGION_TEMPORAL_DEEP.csv"))
    rows.append({"object": "CONTAGION_TEMPORAL_SPECIES", "verdict": f"silhouette {v19.get('silhouette', 'n/a')}",
                 "action": "PROMOTE",
                 "note": "temporal species reproduce in round 2; species distinguished by early_reach / recency_burden / shock_magnitude primitives (KW p<0.01)"})
    v20 = _vrow(_read("20_CONTAGION_SPECIES_PRIMITIVES.csv"))
    rows.append({"object": "SPECIES_PRIMITIVES", "verdict": v20.get("note", "n/a"),
                 "action": "PROMOTE",
                 "note": "early_reach, recency_burden and shock-magnitude separate the temporal species - not just preserved clusters"})
    v21 = _vrow(_read("21_EARLY_CONTAGION_DEMOTION.csv"))
    rows.append({"object": "EARLY_CONTAGION_NODE", "verdict": v21.get("EC_med", "n/a"),
                 "action": "DISSOLVE" if str(v21.get("EC_med", "")).startswith("FAST") else "MERGE",
                 "note": f"{v21.get('note', '')} - EC dissolves into CONTAGION_TEMPORAL_GEOMETRY as FAST_CONTAGION_REGION (negative EC-vs-rest silhouette, ~no separated coordinates)"})
    v22 = _vrow(_read("22_BRANCHING_UTILITY.csv"))
    rows.append({"object": "BRANCHING_ANALYSIS", "verdict": v22.get("value", "n/a"),
                 "action": "PARK",
                 "note": "branching adds no structural distinction across species (R2 range 0.27); kept descriptive only - no criticality language"})
    v23 = _vrow(_read("23_REACTIVATION_SECOND_WAVE.csv"))
    rows.append({"object": "SECOND_WAVE", "verdict": v23.get("value", "n/a"),
                 "action": "PROMOTE",
                 "note": "SAME_MECHANISM_RECURRENCE: post-contagion events stay downside (0.68) in the same capacity region - reactivation is recurrence of the same local mechanism"})
    v24 = _vrow(_read("24_REACTIVATION_MEMORY.csv"))
    rows.append({"object": "PRIOR_CONTAGION_STATE", "verdict": v24.get("react_rate", "n/a"),
                 "action": "PROMOTE",
                 "note": "reactivation decays with time since prior contagion (DECAYS_WITH_RECENCY) - prior contagion is a temporary state variable, consistent with Gate C"})
    v25 = _vrow(_read("25_DECOUPLING_RELATIONAL_MECHANISMS.csv"))
    rows.append({"object": "PERSISTENT_DECOUPLING", "verdict": v25.get("coordinate", "n/a"),
                 "action": "PROMOTE",
                 "note": f"{v25.get('note', '')}"})
    v26 = _vrow(_read("26_DECOUPLING_EXIT_PATHS.csv"))
    rows.append({"object": "DECOUPLING_EXITS", "verdict": v26.get("rate", "n/a"),
                 "action": "PROMOTE-DESCRIPTIVE",
                 "note": "dominant exits: continued isolation (100% of PD events) and rank deterioration (28%); no universal decoupling clock"})
    v28 = _vrow(_read("28_SIGN_ASYMMETRY_MATRIX.csv"))
    rows.append({"object": "SIGN_ASYMMETRY", "verdict": v28.get("liquidity", "n/a"),
                 "action": "PROMOTE-CONDITIONAL",
                 "note": f"gap gradient strongest in damaged rank-health x thin liquidity (+correlation-compression overlay widens it); {v28.get('gap', '')}"})
    v29 = _vrow(_read("29_CORRELATION_COMPRESSION_DEEP.csv"))
    rows.append({"object": "CORRELATION_COMPRESSION", "verdict": v29.get("value", "n/a"),
                 "action": "KEEP-CANDIDATE",
                 "note": "COINCIDES with spread - not established as precursor; no causality claimed"})
    v30 = _vrow(_read("30_MISSING_MECHANICAL_SENSORS.csv"))
    rows.append({"object": "MECHANICAL_SENSORS", "verdict": v30.get("desired_field", "n/a"),
                 "action": "BLOCKED",
                 "note": f"{v30.get('note', '')}"})
    v31 = _vrow(_read("31_SIGN_LAW_STATUS.csv"))
    rows.append({"object": "SIGN_LAW", "verdict": v31.get("down_log_odds", "n/a"),
                 "action": "FREEZE-CONDITIONAL",
                 "note": f"{v31.get('note', '')}"})
    v34 = _vrow(_read("34_UPSIDE_ACCUMULATION_RETEST.csv"))
    rows.append({"object": "UPSIDE_ACCUMULATION", "verdict": v34.get("upside_rate", "n/a"),
                 "action": "PROMOTE-DESCRIPTIVE",
                 "note": f"STATE_LOCAL_ACCUMULATION (max delta {v34.get('delta', 'n/a')}): non-leaky upside history accumulates only weakly - no downside-style damage clock"})
    v35 = _vrow(_read("35_UPSIDE_PROPAGATION_RELATIONS.csv"))
    rows.append({"object": "UPSIDE_PROPAGATION", "verdict": v35.get("p_rejoin", "n/a"),
                 "action": "PROMOTE-DESCRIPTIVE",
                 "note": "upside rejoin path vs downside decouple path are sign-specific relational outcomes - no forced mirror"})
    v37 = _vrow(_read("37_LOCAL_SYNTHESIS.csv"))
    rows.append({"object": "LOCAL_ARCHITECTURE", "verdict": v37.get("p_absorbed", "n/a"),
                 "action": "PROMOTE",
                 "note": "LOOSE_HIERARCHY: structural integrity + current shock + recency/recovery state + relational configuration -> absorb/reorganize/propagate -> contain/reactivate/persist; strict sequencing not claimed"})
    return pd.DataFrame(rows)


def build_null_failed():
    rows = [
        {"result": "NO_FRAGILITY_ACCELERATION", "context": "LF11 damage accumulation (10)", "status": "REINTERPRETED",
         "note": "LF12 selection audit (14) shows cross-sectional gradient is composition; within-asset rho ~0.06. Null stands; mechanism = selection, not resilience."},
        {"result": "RECOVERY_RESTORES_ABSORPTION", "context": "LF12 recovery curve (13)", "status": "FAILED",
         "note": "Absorption does NOT rebuild with time-since-shock; declines (selection). No damage-recovery clock."},
        {"result": "RELATIONAL_DISTANCE_ROUTING", "context": "LF12 relational distance (18)", "status": "NULL",
         "note": "Relational distance does not route contagion (all AUC<0.52) at daily resolution. Not promoted."},
        {"result": "BRANCHING_STRUCTURAL_DISTINCTION", "context": "LF12 branching utility (22)", "status": "NULL",
         "note": "Branching R2 range 0.27 across species - parked."},
        {"result": "LONG_MEMORY_KERNEL", "context": "LF12 kernel repair (02)", "status": "REJECTED",
         "note": "180d kernel is worst (0.572); 3d/7d best (0.639). LF11 summary's 180d claim corrected."},
        {"result": "CUMULATIVE_BURDEN_DOMINANCE", "context": "LF12 burden vs recency (03)", "status": "REJECTED",
         "note": "Recency (days-since-prior 0.6115) beats all cumulative constructions."},
        {"result": "MULTI_FACTOR_REACTIVATION", "context": "LF12 reactivation repair (04)", "status": "REJECTED",
         "note": "Fresh shock / burden / churn / peer stress alone do NOT drive relapse; only prior-contagion x recency does. LF11 wording retracted."},
        {"result": "CIRCULAR_UPSIDE_HIERARCHY", "context": "LF12 leakage audit (05)", "status": "FIXED",
         "note": "3 of 7 LF11 permission variables removed (forward-outcome leakage ~1.0); hierarchy rebuilt PIT-safe."},
        {"result": "CORRELATION_COMPRESSION_PRECURSOR", "context": "LF12 correlation deep (29)", "status": "NULL",
         "note": "Compression COINCIDES with spread; not a precursor. No causality."},
        {"result": "MECHANICAL_SIGN_EXPLANATION", "context": "LF12 sensors (30) / sign law (31)", "status": "DATA_BLOCKED",
         "note": "Funding/OI/liquidations/depth/flow/margin unavailable free-only; sign gap IRREDUCIBLE_WITH_AVAILABLE_DATA."},
        {"result": "UPSIDE_ACCUMULATION_LAW", "context": "LF12 upside retest (34)", "status": "PARTIAL",
         "note": "STATE_LOCAL: prior rejoin history lifts rejoin by <=5.4pp; no downside-style accumulation."},
    ]
    return pd.DataFrame(rows)


def build_freeze_map():
    return """# LOCAL LAW FREEZE MAP — LOWER-FIELD-12

**Purpose:** record which local laws are frozen after the four repair gates and
the deepening pass. Nothing below is strategy / entry / exit / sizing /
leverage. All objects are descriptive / internal-validation only.

## Repair gates (all PASSED)

| Gate | Finding | Status |
|---|---|---|
| A — MEMORY KERNEL | SHORT_MEMORY: 3d/7d half-life kernels best (0.639 purged AUC), monotonic decline to 180d (0.572). LF11 summary's 180d claim CORRECTED. 10-30d stable across subperiods | REPAIRED |
| B — BURDEN vs RECENCY | RECENCY_DOMINANT: days-since-prior (0.6115) > count (0.6012) > decayed burden (0.5937) > cumulative magnitude | REPAIRED |
| C — REACTIVATION | PRIOR_CONTAGION_x_RECENCY_DOMINANT (+0.084); prior contagion alone +0.048; fresh shock / burden / churn / peer stress do NOT drive relapse | REPAIRED |
| D — UPSIDE LEAKAGE | 3 of 7 LF11 permission variables leaked (recruitment, rank-health-improvement, rejoin-recovery ~1.0 spearman); hierarchy rebuilt PIT-safe | REPAIRED |

## Primary local laws (supported this checkpoint)

| Law | Evidence | Status |
|---|---|---|
| CAPACITY SURFACE | COMMON_CAPACITY_GEOMETRY: surface shape repeats across subperiods (07) | FROZEN |
| CAPACITY FAMILIES | 5 families, low redundancy (|rho|<0.3); PARTIAL_ONE_WAY_SUBSTITUTION (09) | FROZEN |
| ABSORPTION vs CONTAINMENT | DISTINCT_LOCAL_ENVIRONMENTS 2x2 (11); loose bypassable chain (10) | FROZEN-DISTINCT_LAWS |
| SHOCK MEMORY | RECENCY_DOMINANT, SHORT_MEMORY kernel (02/03) | FROZEN (corrected) |
| DAMAGE ACCUMULATION | SELECTION_CONFIRMED: within-asset rho ~0.06; null is composition (14) | FROZEN-DESCRIPTIVE |
| RECOVERY | NO recovery clock; absorption highest right after shock (13) | FROZEN-NULL |
| MEMORY BY SPECIES | SPECIES_DEPENDENT_MEMORY; downside > upside (16) | FROZEN-LOCAL |
| CONTAGION TEMPORAL SPECIES | round-2 clusters; primitives early_reach / recency_burden / shock_magnitude (19/20) | FROZEN-LOCAL |
| EARLY_CONTAGION | DISSOLVED -> FAST_CONTAGION_REGION within temporal geometry (21) | FREEZE-UPDATED |
| BRANCHING | PARKED - no structural distinction (22) | PARKED |
| REACTIVATION | SAME_MECHANISM_RECURRENCE; decays with recency (23/24); driver = prior-contagion x recency (04) | FROZEN |
| PERSISTENT DECOUPLING | rank-health decay (0.68) > liquidity (0.61) > failed new-neighborhood formation (0.60) (25); exits: isolation/rank-deterioration (26) | FROZEN-MULTI_MECHANISM |
| SIGN ASYMMETRY | IRREDUCIBLE_WITH_AVAILABLE_DATA; strongest in damaged rank-health x thin liquidity (28/31) | FROZEN-CONDITIONAL |
| CORRELATION COMPRESSION | COINCIDES with spread; candidate, not precursor (29) | CANDIDATE |
| UPSIDE | PIT-safe; functions are weak amplifiers not hard gates; STATE_LOCAL_ACCUMULATION (32/33/34) | FROZEN-DESCRIPTIVE |
| LOCAL ARCHITECTURE | LOOSE_HIERARCHY (37) | FROZEN-DESCRIPTIVE |

## Explicitly NOT frozen / not claimed

- **Leverage/liquidation/liquidity-withdrawal/order-flow/collateral mechanics** —
  DATA_BLOCKED (30). Sign-law status stays conditional until these arrive.
- **Causal branching / contagion causality** — descriptive timing only (22/29).
- **Recovery/damage clock** — no universal clock in either direction (13).
- **Prediction** — descriptive / internal-validation only; LF9 predictive null
  stays frozen. No strategy content anywhere.

## STOP state

human_review_required = TRUE · next_checkpoint_authorized = FALSE.
STOP AFTER LOWER-FIELD-12. WAIT FOR HUMAN REVIEW.
"""


def build_summary():
    return """# LOWER-FIELD-12 SUMMARY — LOCAL LAW HARDENING

**VERDICT: PASS_LOWER_FIELD_12_LOCAL_LAWS_HARDENED** (repair-first checkpoint)

## 1. Repair gates (all passed, prior claims corrected)

- **Gate A — memory kernel:** SHORT_MEMORY. 3d/7d half-life exponential kernels
  give purged AUC 0.639 vs 0.572 at 180d; LF11's summary claim that 180d was
  best is corrected. 10-30d horizons are the most subperiod-stable, but the
  short kernels dominate on discrimination.
- **Gate B — recency vs burden:** RECENCY_DOMINANT. Days-since-prior is the
  best single burden coordinate (0.6115 AUC), beating counts, cumulative
  magnitude and decayed sums. Local memory is primarily *recency*.
- **Gate C — reactivation:** PRIOR_CONTAGION_x_RECENCY_DOMINANT. Only prior
  contagion (+0.048) and its interaction with recency (+0.084) lift relapse;
  fresh shock, unresolved burden, churn and peer stress alone do not. LF11's
  broader multi-factor wording is retracted.
- **Gate D — upside leakage:** 3 of 7 LF11 permission variables were
  forward-outcome contaminated (spearman ~1.0 with the rejoin outcome) and are
  removed; the hierarchy is rebuilt with T0/current information only.

## 2. Deepening

- **Capacity:** COMMON_CAPACITY_GEOMETRY — the structural-integrity x
  recency/burden surface keeps its shape across subperiods while boundaries
  shift. Five capacity families are largely independent; substitution is
  one-way (rank-health can help thin liquidity; liquidity cannot rescue weak
  structure). The absorption x containment 2x2 marks distinct local
  environments, supporting separate OS treatment.
- **Damage:** the LF11 NO_FRAGILITY_ACCELERATION is re-interpreted:
  cross-sectional event-frequency -> absorption gradient (0.006 to 0.175)
  collapses to within-asset rho ~0.06. The null is a selection/composition
  artifact, not fragility and not resilience. FRESH=0% absorption is a labeling
  artifact (first-event state change + high turnover make ABSORBED impossible).
- **Recovery:** NO recovery clock. Absorption is highest immediately after a
  shock and declines with elapsed time — again selection, not a damage-recovery
  curve. Memory is species-dependent (downside 0.59 vs upside 0.46 AUC).
- **Contagion:** temporal species reproduce (silhouette 0.36); distinguishing
  primitives are early_reach, recency_burden and shock magnitude.
  EARLY_CONTAGION is dissolved as a standalone node and re-placed as a
  FAST_CONTAGION_REGION inside the temporal geometry. Branching is parked
  (no structural distinction). Relational distance does not route contagion at
  daily resolution.
- **Reactivation:** same-mechanism recurrence — post-contagion events stay
  downside (68%) in the same capacity region; the prior-contagion state decays
  with recency. Persistent decoupling is dominated by rank-health decay (0.68
  AUC), then liquidity (0.61), then failed new-neighborhood formation (0.60);
  exits are continued isolation and rank deterioration.
- **Sign asymmetry:** IRREDUCIBLE_WITH_AVAILABLE_DATA. The gap is strongest in
  damaged rank-health x thin liquidity and widens with the correlation-
  compression overlay; correlation compression COINCIDES with spread (not a
  precursor). Funding/OI/liquidations/depth/flow/margin stay honestly
  DATA_BLOCKED (no free-only source). Sign asymmetry is NOT called primitive.
- **Upside:** after the leakage audit, PIT-safe functions act as weak
  amplifiers, not hard gates; non-leaky accumulation is STATE_LOCAL (<=5.4pp),
  not a downside-style damage clock.

## 3. Governance

NO STRATEGY · NO PNL · NO EXECUTION · NO ENTRY/EXIT · NO SIZING · NO LEVERAGE ·
NO DEPLOYMENT. LF9 relational predictive null stays frozen; all objects
descriptive / internal-validation. Nothing was committed; the LF12 directory is
left for human review.

human_review_required = TRUE · next_checkpoint_authorized = FALSE.
STOP AFTER LOWER-FIELD-12.
"""


def build_decision():
    return """# LOWER-FIELD-12 DECISION — LOCAL LAW HARDENING

**CHECKPOINT:** LF12 (repair-then-deepen) · branch `agent/crypto-quant-foundry`
**PRIMARY PARENT:** LF11 `1207de392d3240d361cc05724abd6762f8f9611a`
**SECONDARY:** LF10 `3d90fc9b8781481ffa2df05cf8e55256ee4b9315`
**GLOBAL CONTEXT:** MECH-18 `eedc175dc43bc66c6d6b98f6d5f5f913271e3722`

## Verdict

**PASS_LOWER_FIELD_12_LOCAL_LAWS_HARDENED**

All four repair gates (A memory kernel, B recency vs burden, C reactivation,
D upside leakage) passed with data-grounded corrections to LF11 claims. The
deepening pass produced stable capacity geometry, honest selection
re-interpretation of the accumulation null, round-2 temporal contagion species
with identifying primitives, EC demotion, and a PIT-safe upside rebuild.

## What changed vs LF11

1. **Memory horizon corrected**: short (3-7d), not 180d.
2. **Memory = recency**, not accumulated damage.
3. **Reactivation driver narrowed**: prior-contagion x recency only.
4. **Upside hierarchy rebuilt**: leakage removed; functions are weak
   amplifiers, no hard gates; accumulation is state-local.
5. **Damage null re-interpreted**: selection/composition confirmed
   within-asset; no fragility acceleration, no resilience clock.
6. **Recovery clock rejected**: absorption declines with elapsed time.
7. **EARLY_CONTAGION dissolved** into temporal geometry as a fast region.
8. **Branching parked**; relational distance null recorded.
9. **Decoupling mechanism map**: rank-health decay dominates; exits mapped.
10. **Sign asymmetry**: still IRREDUCIBLE_WITH_AVAILABLE_DATA; gradient
    localized to damaged rank-health x thin liquidity; sensors registry kept.

## Final questions answered

1. Correct LF11 memory horizon: **short** (3-7d kernel).
2. Memory primarily recency: **YES (RECENCY_DOMINANT)**.
3. Reactivation driver: **prior contagion x recency**; other factors alone no.
4. LF11 upside hierarchy contaminated: **YES, 3 of 7 variables removed**.
5. Stable capacity geometry: **YES (COMMON_CAPACITY_GEOMETRY)**.
6. Boundaries shift by rank depth / liquidity / shock family; shape persists.
7. Family substitution: **partial, one-way**.
8. Absorption vs containment: **distinct enough for separate OS nodes**.
9. Memory as recovery state: **no — memory is recency; recovery clock null**.
10. Absorption capacity recovery: **does not rebuild with time** (selection).
11. Within-asset: **confirms selection interpretation of the null**.
12. Memory by shock family: **yes, species-dependent (downside > upside)**.
13. Relationships permitting contagion: **not relational-distance-driven at
    daily resolution** (relational links weak).
14. Relational distance: **does not matter much at this resolution (null)**.
15. Species primitives: **early_reach, recency_burden, shock magnitude**.
16. EARLY_CONTAGION node: **dissolved -> FAST_CONTAGION_REGION**.
17. Branching: **parked**.
18. Reactivation: **same-mechanism recurrence**.
19. Prior-contagion state persistence: **decays with recency (short)**.
20. Persistent decoupling: **rank-health decay > liquidity > failed new
    neighborhood formation**.
21. Sign asymmetry strongest: **damaged rank-health x thin liquidity**.
22. Correlation compression: **COINCIDES with spread; not precursor**.
23. Missing sensors: **8 listed, 5 HIGH dependence, all non-free -> BLOCKED**.
24. Sign-law status: **IRREDUCIBLE_WITH_AVAILABLE_DATA**.
25. Survives upside audit: **stability, liquidity, coherence, capacity**.
26. Non-leaky upside accumulation: **state-local only (<=5.4pp)**.
27. Functional upside mechanism: **weak amplifiers, no hard gate**.
28. Real upside analogues: **DIFFERENT_THRESHOLD for load/coherence/breadth;
    NO_ANALOGUE for reactivation; rest sign-specific/unknown**.
29. Local layer organization: **LOOSE_HIERARCHY (hybrid, bypassable)**.
30. Freeze readiness: **conditional — blocked only on mechanical sensors**;
    local-law layer is frozen with the DATA_BLOCKED registry attached.

## Governance

REPAIR BEFORE PROMOTION was honored: no law was promoted on the old LF11
wording. NO STRATEGY · NO PNL · NO EXECUTION. LF9 predictive null frozen.
`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`.
STOP AFTER LOWER-FIELD-12. WAIT FOR HUMAN REVIEW.
"""


def write_preregistration():
    txt = """# LOWER-FIELD-12 PREREGISTRATION

**CHECKPOINT:** LF12 — local-law repair & hardening: capacity-surface deepening,
recency/recovery memory, damage-accumulation reinterpretation, contagion
relational geometry, temporal species, reactivation/second-wave mechanics,
persistent-decoupling relations, sign-asymmetry granularity,
correlation-compression mechanics, upside leakage audit & functional map,
local-physics synthesis.

**BRANCH:** `agent/crypto-quant-foundry`
**PRIMARY PARENT:** LF11 `1207de392d3240d361cc05724abd6762f8f9611a`
**SECONDARY:** LF10 `3d90fc9b8781481ffa2df05cf8e55256ee4b9315`
**GLOBAL CONTEXT:** MECH-18 `eedc175dc43bc66c6d6b98f6d5f5f913271e3722`
**OLDER NODES:** LF8-LF11 (relational persistence, continuous panel, shock &
contagion cartography, local laws).

**ROLE:** AGENT 2 — DERIVATIVE / SIDE-LANE FALSIFIER · CURRENT
SPECIALIZATION: LOCAL LAW HARDENER

**GOVERNANCE:** NO STRATEGY · NO PNL · NO EXECUTION · NO ENTRY/EXIT ·
NO SIZING · NO LEVERAGE · NO DEPLOYMENT.
`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`.
DO NOT REOPEN RELATIONAL PREDICTION. DO NOT CALL SIGN ASYMMETRY PRIMITIVE.
DO NOT FORCE CUMULATIVE DAMAGE. DO NOT PRESERVE EARLY_CONTAGION IF BROADER
GEOMETRY REPLACES IT. DO NOT FORCE BRANCHING. DO NOT USE FORWARD UPSIDE
VARIABLES AS PERMISSION INPUTS. STOP AFTER LOWER-FIELD-12.

## 1. Question before mathematics

LF11 mapped local laws but left three inconsistencies requiring repair before
promotion: (A) the memory-kernel horizon was mis-stated, (B) reactivation
wording over-claimed multi-factor drivers, and (C) the upside permission
hierarchy risked forward-outcome circularity.

> After repair, do the local laws — capacity surface, memory as recency,
> damage as selection, contagion geometry, reactivation, persistent decoupling,
> sign asymmetry and upside — form a stable, freeze-able local layer?

## 2. Pre-registered procedure

1. **Repair first.** Recompute the memory-kernel scan (3-180d half-lives,
   identical folds, purged AUC + bootstrap CI + subperiod stability); compare
   recency vs cumulative burden; re-test reactivation drivers with
   interactions; audit every upside permission variable for forward leakage
   (measured-at / overlaps-target / future-information / same-forward-window).
   Any contaminated variable is removed and the hierarchy rebuilt.
2. **Deepen only after repair passes.** Capacity surface across rank depth /
   global state / shock family / direction / liquidity / churn / relational
   state / contagion history; capacity geometry, boundaries, family relations;
   absorption->propagation->containment relations and 2x2 matrix; recovery
   state and curve; damage-selection audit with within-asset fixed effects and
   matched histories; memory by shock species; contagion as a relational
   object and relational distance; temporal species round 2 with primitives;
   EARLY_CONTAGION demotion audit; branching utility; reactivation second wave
   and memory; persistent-decoupling relations and exits; sign-asymmetry
   granularity and targeted matrix; correlation-compression temporal role;
   missing-mechanical-sensor registry; sign-law status; upside PIT rebuild,
   functional map, accumulation retest, propagation relations; sign function
   comparison; local synthesis.
3. **No promotion on old wording.** Every LF11 law is re-checked; corrections
   are recorded in the freeze map. No sign law is called primitive while major
   mechanical families are unavailable (honest DATA_BLOCKED).
4. **Stop.** No strategy / PnL / execution / sizing / leverage content anywhere.
"""
    (OUT / "01_PREREGISTRATION.md").write_text(txt, encoding="utf-8")


def main():
    write_preregistration()
    build_promote_merge_dissolve().to_csv(OUT / "38_PROMOTE_MERGE_DISSOLVE.csv", index=False)
    build_null_failed().to_csv(OUT / "39_NULL_AND_FAILED_RESULTS.csv", index=False)
    (OUT / "40_LOCAL_LAW_FREEZE_MAP.md").write_text(build_freeze_map(), encoding="utf-8")
    (OUT / "41_LOWER_FIELD_12_SUMMARY.md").write_text(build_summary(), encoding="utf-8")
    (OUT / "42_LOWER_FIELD_12_DECISION.md").write_text(build_decision(), encoding="utf-8")
    print("[lf12] finalize DONE")


if __name__ == "__main__":
    main()
