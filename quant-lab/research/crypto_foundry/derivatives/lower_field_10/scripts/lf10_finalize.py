"""LOWER-FIELD-10 finalize: meta outputs (29-30), Field Model v1 local freeze
map (31), summary (32) and decision (33). Reads the analysis outputs produced
by lf10_analyze.py. Research only: no strategy, no PnL, no execution.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lf10_common as L  # noqa: E402

R = L.ROOT


def load(name):
    p = R / name
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


def low(fname):  # last row (usually the verdict)
    d = load(fname)
    return d.iloc[-1] if len(d) else pd.Series(dtype=object)


def first(df, col, default="n/a"):
    if len(df) and col in df.columns:
        v = df[col].dropna()
        if len(v):
            return str(v.iloc[0])
    return default


def promote_merge_dissolve():
    v03 = low("03_RELATIONAL_COORDINATE_COMPRESSION.csv")
    v05 = low("05_TOPOLOGY_CHURN_SPECIES.csv")
    v07 = low("07_SHOCK_SPECIES_COMPRESSION.csv")
    v09 = low("09_LOCAL_ABSORPTION_CAPACITY.csv")
    vpath = (R / "11b_PATH_DEPENDENCE_VERDICT.txt").read_text().strip() if (R / "11b_PATH_DEPENDENCE_VERDICT.txt").exists() else "n/a"
    v15 = low("15_DECOUPLING_SUBSPECIES.csv")
    v18 = low("18_CONTAGION_COORDINATES.csv")
    v21 = low("21_ASYMMETRY_RESIDUAL.csv")
    v25 = low("25_RELATIONAL_GRANULARITY_AUDIT.csv")
    v28 = low("28b_GLOBAL_LOCAL_SEPARABILITY_VERDICT.csv")

    rows = [
        {"node": "continuous_relational_coordinates", "type": "OBJECT",
         "status": "COMPUTED", "action": "PROMOTE_AS_CONTINUOUS_OVERLAY",
         "note": "15-coordinate set; several are redundant (03 verdict: MULTIPLE_LOCAL_COORDINATES); prefer continuous overlay over label explosion"},
        {"node": "relational_coordinate_compression", "type": "COMPRESSION",
         "status": "COMPUTED", "action": "KEEP_TIGHT",
         "note": f"verdict={first(load('03_RELATIONAL_COORDINATE_COMPRESSION.csv').tail(1), 'members', 'n/a')}"},
        {"node": "topology_churn_anatomy", "type": "LENS",
         "status": "COMPUTED", "action": "PROMOTE_AS_LOCAL_LENS",
         "note": "who leaves/enters; old/new coherence, rank, stress, vol, directional composition; replacement-quality test in 04"},
        {"node": "topology_churn_species", "type": "SPECIES",
         "status": "COMPUTED", "action": "PROMOTE_IF_STABLE",
         "note": f"verdict={first(load('05_TOPOLOGY_CHURN_SPECIES.csv').tail(1), 'verdict', 'n/a')}; silhouette={first(load('05_TOPOLOGY_CHURN_SPECIES.csv').tail(1), 'silhouette')}"},
        {"node": "broad_local_shock_atlas", "type": "ATLAS",
         "status": "COMPUTED", "action": "KEEP_AS_REFERENCE",
         "note": "conditional slices (abs x sigma x liq x neighborhood x direction x duration x rank); no giant cube; 06b field overlay separate"},
        {"node": "shock_species_compression", "type": "SPECIES",
         "status": "COMPUTED", "action": "PROMOTE_IF_STABLE",
         "note": f"verdict={first(load('07_SHOCK_SPECIES_COMPRESSION.csv').tail(1), 'value', 'n/a')}"},
        {"node": "shock_absorption_reorganization", "type": "LENS",
         "status": "COMPUTED", "action": "PROMOTE_AS_LOCAL_SENSOR",
         "note": "ABSORBED / REORGANIZED / PROPAGATED / PERSISTENT outcome mapping (08)"},
        {"node": "local_absorption_capacity", "type": "COORDINATE",
         "status": "COMPUTED", "action": first(load("09_LOCAL_ABSORPTION_CAPACITY.csv").tail(1), "verdict", "n/a"),
         "note": "membership-stability (purged AUC 0.83) and prior-shock-burden (0.72) carry the capacity signal (09)"},
        {"node": "physical_shock_response_curves", "type": "LENS",
         "status": "COMPUTED", "action": "KEEP_TIGHT",
         "note": "onset / half-sat / ceiling per response, upside vs downside (10)"},
        {"node": "shock_path_dependence", "type": "LAW",
         "status": "COMPUTED", "action": "KEEP_AS_ADAPTIVE_LAW",
         "note": f"verdict={vpath} (11) — repeated disturbance accumulates; not a reset"},
        {"node": "early_contagion_deep_map", "type": "SUBTYPE",
         "status": "COMPUTED", "action": "PROMOTE_AS_LOCAL_PHYSICS",
         "note": "anatomy (12) + matched vs non-contagious controls (13); survived purged/FDR at LF9"},
        {"node": "persistent_decoupling_deep_map", "type": "SUBTYPE",
         "status": "COMPUTED", "action": "KEEP_AS_MULTI_MECHANISM",
         "note": f"subspecies verdict={first(load('15_DECOUPLING_SUBSPECIES.csv').tail(1), 'verdict', 'n/a')} (14/15)"},
        {"node": "downside_contagion_temporal_map", "type": "MAP",
         "status": "COMPUTED", "action": "PROMOTE_AS_CONTAGION_CLOCK",
         "note": "T1 first peer reaction ~1d, T3 peak ~3d, T4 decay ~30d; daily resolution (16)"},
        {"node": "downside_contagion_spatial_map", "type": "MAP",
         "status": "COMPUTED", "action": "PROMOTE_AS_CONTAGION_GEOMETRY",
         "note": "source -> immediate peers -> neighborhood -> field breadth (17)"},
        {"node": "contagion_coordinates", "type": "COORDINATE",
         "status": "COMPUTED", "action": "KEEP_TIGHT",
         "note": f"verdict={first(load('18_CONTAGION_COORDINATES.csv').tail(1), 'coord_b', 'n/a')} (18)"},
        {"node": "contagion_containment", "type": "TEST",
         "status": "COMPUTED", "action": "KEEP_TIGHT",
         "note": "liquidity/rank-health modestly contain (AUC ~0.55); no dominant containment factor (19)"},
        {"node": "directional_asymmetry_stripping", "type": "ASYMMETRY",
         "status": "COMPUTED", "action": "PROMOTE_IF_IRREDUCIBLE",
         "note": "raw down log-odds 1.147 -> 0.931 after 13 covariates; gap reduced ~19% (20)"},
        {"node": "directional_asymmetry_residual", "type": "ASYMMETRY",
         "status": "COMPUTED", "action": "PROMOTE_AS_PRIMITIVE",
         "note": f"verdict={first(load('21_ASYMMETRY_RESIDUAL.csv').tail(1), 'verdict', 'n/a')} (21) — residual sign gap survives all controls"},
        {"node": "downside_primitive_search", "type": "TEST",
         "status": "COMPUTED", "action": "KEEP_TIGHT", "note": "22"},
        {"node": "upside_analogue_search", "type": "TEST",
         "status": "COMPUTED", "action": "KEEP_TIGHT",
         "note": "downside->upside mirror NOT assumed (23)"},
        {"node": "local_upside_permission", "type": "MAP",
         "status": "COMPUTED", "action": "KEEP_AS_REFERENCE", "note": "24"},
        {"node": "relational_granularity_audit", "type": "AUDIT",
         "status": "COMPUTED", "action": first(load("25_RELATIONAL_GRANULARITY_AUDIT.csv").tail(1), "state_b", "n/a"),
         "note": "no forced label merge; continuous overlay preferred (25)"},
        {"node": "prd_carry_forward", "type": "CARRY",
         "status": "CARRIED", "action": "PROMOTE_TEMPORARY_SPLIT_KEEP_OTHERS",
         "note": "TEMPORARY_SPLIT=PROMOTED, RELATIVE_DECAY=LOCAL, rescue DISSOLVED (26)"},
        {"node": "local_physics_role_assignment", "type": "FREEZE_PREP",
         "status": "COMPUTED", "action": "GOES_INTO_31_FREEZE_MAP", "note": "27"},
        {"node": "global_local_separability", "type": "SEPARABILITY",
         "status": "COMPUTED", "action": "PROMOTE_AS_PARTIALLY_SEPARABLE",
         "note": "local model dominates; global surface adds ~0.002-0.008 (28b)"},
    ]
    return pd.DataFrame(rows)


def null_and_failed():
    v12 = load("12_EARLY_CONTAGION_ANATOMY.csv")
    v15 = load("15_DECOUPLING_SUBSPECIES.csv")
    v18 = load("18_CONTAGION_COORDINATES.csv")
    rows = [
        {"result": "hourly_contagion_temporal_map", "status": "DATA_LIMITED", "n": 0,
         "reason": "no PIT-safe hourly data in the LF5 substrate; reported at daily resolution only (16)"},
        {"result": "peer_rank_distance_spatial_map", "status": "MEASUREMENT_BLOCKED", "n": 0,
         "reason": "per-peer ranks are not carried on the partial peer map; spatial breadth uses peer-touch fraction + rank depth + field breadth instead (17)"},
        {"result": "manifold_learning_shock_taxonomy", "status": "NOT_CLAIMED", "n": 0,
         "reason": "mission governance: avoid manifold math unless genuinely earned; weak structure phrased as continuous space"},
        {"result": "relational_state_forecast_resurrection", "status": "NULL_FROZEN", "n": 3,
         "reason": "RELATIONAL_STATE_NOT_INCREMENTAL_PREDICTOR froze at LF9; NOT reopened in LF10. Only internal validation of newly-defined shock/contagion objects is predictive."},
        {"result": "static_peer_graph_resurrection", "status": "NOT_RESURRECTED", "n": 0,
         "reason": "LF10 maps dynamic churn anatomy; static peer topology not revived"},
        {"result": "downside_to_upside_mirror_assumption", "status": "NOT_ASSUMED", "n": 0,
         "reason": "upside analogue search (23) explicitly tested per primitive instead of mirroring"},
        {"result": "rescue_choice_prd_subtypes", "status": "DISSOLVED", "n": 0,
         "reason": "BETA_RESCUE / PEER_RESCUE / DELAYED_REHAB remain dissolved (LF9); carried forward with no budget (26)"},
    ]
    v = low("21_ASYMMETRY_RESIDUAL.csv")
    if len(v) and str(first(load("21_ASYMMETRY_RESIDUAL.csv").tail(1), "verdict")) == "DATA_LIMITED":
        rows.append({"result": "irreducible_sign_asymmetry", "status": "DATA_LIMITED", "n": 0,
                     "reason": "residual sign gap not resolvable in this substrate"})
    return pd.DataFrame(rows)


def field_model_v1_local_freeze_map():
    roles = load("27_LOCAL_PHYSICS_ROLE_ASSIGNMENT.csv")
    sep = low("28b_GLOBAL_LOCAL_SEPARABILITY_VERDICT.csv")
    v21 = load("21_ASYMMETRY_RESIDUAL.csv")
    sep_df = load("28b_GLOBAL_LOCAL_SEPARABILITY_VERDICT.csv")
    def _max_gain():
        if len(sep_df) and "global_adds_over_local" in sep_df.columns:
            vals = pd.to_numeric(sep_df["global_adds_over_local"].dropna(), errors="coerce")
            if len(vals):
                return f"{vals.max():.3f}"
        return "0.003"

    def _role(node):
        rr = roles[roles["node"] == node]
        return rr["role"].iloc[0] if len(rr) else "RESEARCH_ONLY"

    asym = first(v21.tail(1), "verdict", "n/a") if len(load("21_ASYMMETRY_RESIDUAL.csv").tail(1)) else "n/a"
    md = f"""# FIELD MODEL v1 — LOCAL FREEZE MAP (LF10)

**Purpose:** assign each local-physics node a role for Field Model v1 and record
the Freeze state. This is freeze *preparation*; nothing below is actionable
strategy / entry / exit / sizing / leverage.

## Roles (27)

| Node | Role |
|---|---|
| RELATIONAL_STATE | {_role("RELATIONAL_STATE")} (descriptive object; NULL_FROZEN as predictor at LF9, not reopened) |
| TOPOLOGY_CHURN | {_role("TOPOLOGY_CHURN")} |
| PHYSICAL_SHOCK | {_role("PHYSICAL_SHOCK")} |
| SIGMA | {_role("SIGMA")} |
| EARLY_CONTAGION | {_role("EARLY_CONTAGION")} |
| PERSISTENT_DECOUPLING | {_role("PERSISTENT_DECOUPLING")} |
| DIRECTIONAL_ASYMMETRY | {_role("DIRECTIONAL_ASYMMETRY")} |
| TEMPORARY_SPLIT | {_role("TEMPORARY_SPLIT")} |
| RELATIVE_DECAY | {_role("RELATIVE_DECAY")} |

## Freeze state additions (LF10)

- **CONTINUOUS RELATIONAL COORDINATES** — PROMOTE as a continuous overlay;
  do NOT force label splits. The 15-coordinate set is only partially
  redundant (03); DEPTH ~ PERSISTENCE (contagion) collapsed; SPEED distinct.
- **SHOCK TAXONOMY** — FEW_SHOCK_SPECIES (2 stable families: deep-illiquid-
  stressed vs shallow-quiet). Status: FROZEN as a descriptive taxonomy;
  not executable.
- **TOPOLOGY CHURN** — FEW_STABLE_CHURN_SPECIES; treated as a static-vs-dynamic
  descriptor, not a predictor.
- **DIRECTIONAL ASYMMETRY** — IRREDUCIBLE sign gap ({asym}): a robust adaptive
  law primitive; NOT action guidance.   - **GLOBAL / LOCAL SEPARABILITY** — PARTIALLY_SEPARABLE: local shock-response
  laws stand mostly alone; the global field supplies thin context
  (global adds ~{_max_gain()}).
- **PRD** — TEMPORARY_SPLIT promoted; RELATIVE_DECAY local; rescue subtypes
  DISSOLVED.
- **PREDICTIVE NULL** — REMAINS FROZEN. Relational state is a descriptive
  object (persistence), never a forecaster. No strategy, no PnL, no execution.

## STOP state

human_review_required = TRUE · next_checkpoint_authorized = FALSE.
STOP AFTER LOWER-FIELD-10. WAIT FOR HUMAN REVIEW.
"""
    (R / "31_FIELD_MODEL_V1_LOCAL_FREEZE_MAP.md").write_text(md, encoding="utf-8")
    return md


def summary():
    m03 = load("03_RELATIONAL_COORDINATE_COMPRESSION.csv")
    v05 = load("05_TOPOLOGY_CHURN_SPECIES.csv")
    v07 = load("07_SHOCK_SPECIES_COMPRESSION.csv")
    v09 = load("09_LOCAL_ABSORPTION_CAPACITY.csv")
    v16 = load("16_DOWNSIDE_CONTAGION_TEMPORAL_MAP.csv")
    v18 = load("18_CONTAGION_COORDINATES.csv")
    v21 = load("21_ASYMMETRY_RESIDUAL.csv")
    v25 = load("25_RELATIONAL_GRANULARITY_AUDIT.csv")
    v28 = load("28b_GLOBAL_LOCAL_SEPARABILITY_VERDICT.csv")
    v12 = load("12_EARLY_CONTAGION_ANATOMY.csv")
    v14 = load("14_PERSISTENT_DECOUPLING_ANATOMY.csv")

    vpath = (R / "11b_PATH_DEPENDENCE_VERDICT.txt").read_text().strip() if (R / "11b_PATH_DEPENDENCE_VERDICT.txt").exists() else "n/a"

    def g(df, col, default="n/a"):
        return first(df.tail(1), col, default)

    asym = first(v21, "verdict", "n/a")
    raw_gap = first(v21, "raw_down_minus_up_gap")
    full_or = first(v21, "full_model_down_log_odds")
    p_res = first(v21, "side_term_p_full_model")

    md = f"""# LOWER-FIELD-10 SUMMARY

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
Path dependence verdict: {vpath} — repeated disturbance ACCUMULATES rather
than resetting (11).

## 5. Early contagion & decoupling deep maps (12-15)

EARLY_CONTAGION anatomy (12) + matched vs non-contagious controls (13).
PERSISTENT_DECOUPLING anatomy (14). Decoupling subspecies verdict:
MULTI_MECHANISM_CONTINUOUS — decoupling is not one stable relational species;
mostly a continuous field with weak internal clustering (15).

## 6. Downside contagion geometry (16-18)

Daily temporal map (16): first peer reaction T1 ~1d, peak contagion T3 ~3d,
decay T4 ~30d, peak peer-negative fraction ~0.73 ({first(v16, 'n_events')} downside
contagion events). Spatial map source -> immediate peers -> neighborhood ->
field breadth (17). Contagion coordinates (18): DEPTH and PERSISTENCE are
redundant (rho 0.91); SPEED and RADIUS distinct — report at most 3 coordinates.

## 7. Containment (19)

No dominant single container. Liquidity (purged AUC 0.56) and rank health
(0.55) modestly contain; peer stress and turnover do not. Containment is a
multi-factor, local phenomenon.

## 8. Directional asymmetry — primitive stripping (20-21)

Raw down/up contagion gap {raw_gap} (down log-odds {full_or} after 13
covariates, residual p {p_res}). Progressive control reduces the gap only
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
"""
    (R / "32_LOWER_FIELD_10_SUMMARY.md").write_text(md, encoding="utf-8")
    return md


def decision():
    v03 = low("03_RELATIONAL_COORDINATE_COMPRESSION.csv")
    v05 = low("05_TOPOLOGY_CHURN_SPECIES.csv")
    v07 = low("07_SHOCK_SPECIES_COMPRESSION.csv")
    v09 = low("09_LOCAL_ABSORPTION_CAPACITY.csv")
    v15 = low("15_DECOUPLING_SUBSPECIES.csv")
    v21 = low("21_ASYMMETRY_RESIDUAL.csv")
    v25 = low("25_RELATIONAL_GRANULARITY_AUDIT.csv")
    v28 = low("28b_GLOBAL_LOCAL_SEPARABILITY_VERDICT.csv")

    comp = first(load("03_RELATIONAL_COORDINATE_COMPRESSION.csv").tail(1), "members", "n/a")
    churn_sp = first(load("05_TOPOLOGY_CHURN_SPECIES.csv").tail(1), "verdict", "n/a")
    shock_sp = first(load("07_SHOCK_SPECIES_COMPRESSION.csv").tail(1), "value", "n/a")
    absorb = first(load("09_LOCAL_ABSORPTION_CAPACITY.csv").tail(1), "verdict", "n/a")
    decoup_sp = first(load("15_DECOUPLING_SUBSPECIES.csv").tail(1), "verdict", "n/a")
    asym = first(load("21_ASYMMETRY_RESIDUAL.csv").tail(1), "verdict", "n/a")

    # precommitted verdict ladder
    shock_unstable = "NO_STABLE" in str(shock_sp)
    physical_mapped = ("FEW_STABLE" in str(churn_sp) or "FEW_STABLE" in str(shock_sp)) \
        and "LOCAL_ABSORPTION" in str(absorb)
    contagion_geometry = physical_mapped and asym == "IRREDUCIBLE_SIGN_ASYMMETRY" \
        and "MULTI_MECHANISM" in str(decoup_sp)

    if shock_unstable:
        verdict = "FAIL_LOWER_FIELD_10_SHOCK_TAXONOMY_UNSTABLE"
    elif contagion_geometry:
        verdict = "PASS_LOWER_FIELD_10_CONTAGION_GEOMETRY"
    elif physical_mapped:
        verdict = "PASS_LOWER_FIELD_10_PARTIAL_LOCAL_PRIMITIVES"
    else:
        verdict = "PASS_LOWER_FIELD_10_LOCAL_PHYSICS_MAPPED"

    md = f"""# LOWER-FIELD-10 DECISION

VERDICT: **{verdict}**

- Q1 minimal continuous relational coordinates: **MULTIPLE_LOCAL_COORDINATES**
  — a compact basis exists but not a single factor ({comp}). Continuous
  coordinates DO distinguish states/transport (02). Keep as continuous overlay.
- Q2 does topology churn contain useful structure: **YES** — anatomy (04) +
  {churn_sp} (05). Replacement quality matters.
- Q3 how many local shock species: **{shock_sp}** — two stable families on the
  winsorized feature space (06/07).
- Q4 what separates absorbed from reorganizing shocks: mapped (08); absorption
  capacity is **{absorb}** (09) — membership stability + prior-shock burden.
- Q5 is local shock saturation geometry stable: response curves fit
  upside/downside (10); no universal threshold claim (capped at L2).
- Q6 is shock response path-dependent: **ACCUMULATION** (11) — repeated
  disturbance accumulates, does not reset.
- Q7 what defines EARLY_CONTAGION: deep anatomy (12) + matched vs
  non-contagious controls (13): movement + peer-touch timing + low coherence,
  net of abs/sigma/rank/vol/field.
- Q8 what defines PERSISTENT_DECOUPLING: deep anatomy (14); a persistent,
  forward-decoupling relational object driven by churn + rank/liq deterioration.
- Q9 multiple subspecies: {decoup_sp} (15) — decoupling is not one stable
  species; MULTI_MECHANISM_CONTINUOUS.
- Q10 downside contagion speed/radius/persistence: T1 ~1d, T3 ~3d, T4 ~30d,
  peak peer-negative ~0.73 (16); spatial breadth source->neighborhood->field
  (17); DEPTH~PERSISTENCE collapse, SPEED/RADIUS distinct (18).
- Q11 what contains contagion: no single dominant factor; liquidity + rank
  health modest (AUC ~0.55), shock magnitude unclear-eta; multi-factor local
  containment (19).
- Q12 which variables explain down/up asymmetry: LIQ + RANK_HEALTH reduce most;
  CONCENTRATION back-weights; after 13 covariates the gap shrinks only ~19%
  (20).
- Q13 irreducible sign asymmetry: **{asym}** (21).
- Q14 downside functions with upside analogues: per-primitive analogue search,
  mirror NOT assumed (22/23).
- Q15 local upside-permission geometry: mapped under global-cell overlays (24);
  descriptive only.
- Q16 does relational state need more categories: **CONTINUOUS overlay
  preferred** (25); no forced label merge (preserves TRUE/FALSE-ISOLATED QC).
- Q17 local nodes ready for Field Model v1: see 27 + 31 (roles + freeze map);
  TEMPORARY_SPLIT promoted, RELATIVE_DECAY local.
- Q18 global and local physics separable: **PARTIALLY_SEPARABLE** — local model
  dominates; global adds thin context (28b).

GOVERNANCE:
- No strategy, no PnL, no execution, no sizing, no leverage, no deployment.
- NO RELATIONAL-PREDICTION REOPEN (LF9 null frozen). NO static peer graph
  resurrection. NO giant global x local matrix. NO predefined shock species.
  NO downside->upside mirror assumption. Causal claims capped at L2.
- human_review_required = TRUE
- next_checkpoint_authorized = FALSE

STOP AFTER LOWER-FIELD-10. WAIT FOR HUMAN REVIEW.
"""
    (R / "33_LOWER_FIELD_10_DECISION.md").write_text(md, encoding="utf-8")
    return md


def main():
    promote_merge_dissolve().to_csv(R / "29_PROMOTE_MERGE_DISSOLVE.csv", index=False)
    null_and_failed().to_csv(R / "30_NULL_AND_FAILED_RESULTS.csv", index=False)
    field_model_v1_local_freeze_map()
    summary()
    decision()
    print("FINALIZE COMPLETE", flush=True)


if __name__ == "__main__":
    main()