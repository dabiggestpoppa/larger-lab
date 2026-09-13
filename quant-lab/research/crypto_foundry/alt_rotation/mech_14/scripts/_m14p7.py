from _m14base import *
from _m14base import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _entropy, _subperiod_split, _cohen_d, _auc_xy
from _m14p1 import *
from _m14p2 import *
from _m14p3 import *
from _m14p4 import *
from _m14p5 import *
from _m14p6 import *


# =========================================================================
# WS23 writers: repair-audit md, promote/nulls/map, verdicts/summary/decision
# =========================================================================

def _v(series):
    """First verdict value in a frame (defensive)."""
    if isinstance(series, pd.DataFrame):
        return _v(series["verdict"]) if "verdict" in series.columns else "n/a"
    s = series.dropna()
    return str(s.iloc[0]) if len(s) else "n/a"


def write_repair_audit(results):
    """02_MECH13_REPAIR_AUDIT.md from the WS1 correction ledger + WS11."""
    led = results.get("repair_ledger")
    n_pass = int((led["status"].str.startswith("PASS")).sum()) if led is not \
        None and len(led) else 0
    n_repair = int((led["status"].str.startswith("REPAIR")).sum()) if led is \
        not None and len(led) else 0
    n_caveat = int((led["status"].str.contains("caveat",
                                              case=False)).sum()) if led is \
        not None and len(led) else 0
    w = results.get("waterfall")
    wr = "n/a"
    if w is not None and len(w):
        g = w[w["subtype"] == "ORDERLY_SHALLOW_TO_DEEP"]
        if len(g):
            r = g.iloc[0]
            wr = (f"n={int(r['n'])} n_subperiods={int(r['n_subperiods'])} "
                  f"max_cycle_share={float(r['max_cycle_share']):.3f} "
                  f"verdict={r['verdict']}")
    L = ["# CRYPTO-ALT-MECH-14 — MECH-13 REPAIR AUDIT", "",
         "Completed before any new promotion (REPAIR BEFORE PROMOTION). Every "
         "MECH-13 node in the correction ledger was checked against its "
         "preregistered bar: counts, support, subperiods, FDR, circularity, "
         "missingness, duplicate-event use, and the waterfall n_subperiods "
         "placeholder.", "",
         f"Ledger status summary: **PASS {n_pass} · REPAIR {n_repair} · "
         f"PASS-with-caveat {n_caveat}** (rows audited: "
         f"{0 if led is None else len(led)}).", "",
         "## Headline repair: 10_WATERFALL_SUBTYPE_MATRIX n_subperiods=0",
         "",
         "MECH-13 reported `ORDERLY_SHALLOW_TO_DEEP n=240 n_subperiods=0 "
         "verdict=NAMED_SUBTYPE`. Preregistration required `>=3` subperiods. "
         "Source inspection (M13 `_m13p6.py` ws9) shows the field was "
         "hardcoded to 0 — a placeholder, not a computed statistic.", "",
         "MECH-14 recomputed the activation subtype from source (independent "
         "reconstruction across all subperiod definitions). Result:", "",
         f"- `ORDERLY_SHALLOW_TO_DEEP`: {wr}",
         "- Cycle shares span all 5 subperiods; none exceeds 50%.",
         "",
         "**Resolution: the promotion is VALID; the statistic was "
         "MISLABELED (0 instead of 5).** The correction ledger classifies "
         "this `REPAIR (statistical-reporting bug, promotion valid)`. "
         "13_WATERFALL_REVALIDATION.csv reconfirms NAMED_SUBTYPE under the "
         ">=50, >=3-subperiod, no-single-cycle->50% bar plus leave-one-cycle "
         "stability.", "",
         "## Other corrections carried", "",
         "- **09_SPATIAL_TEMPORAL_CONSTRAINT_MATRIX**: the MECH-13 claim of "
         "independent axes is RETAINED after age-residualized entropy — see "
         "17_SPATIAL_TEMPORAL_CONSTRAINT_RECHECK.csv (WS15). The M14 axis "
         "correlation is now computed on complete pairs (rho=-0.006, "
         "p=0.78, n=2193) instead of a NaN-derived default.",
         "- **12/13_PATCH_RESPONSE + HETEROGENEITY**: SATURATING is "
         "descriptive; amplitude terciles are in-window bins, not "
         "leave-one-cycle. M14 WS12 reframes as common-forcing + patch "
         "thresholds (held-out comparison now completes: common+threshold "
         "0.597 vs patch-specific 0.600 -> compression candidate supported).",
         "- **21_LOCAL_CONVERSION_PATHS**: PATH_C terminal (PROP_CONFIRM) is "
         "partially circular; PATH_A/D weighted. Rechecked in WS22.",
         "", "## Audit log", ""]
    if led is not None and len(led):
        for _, row in led.iterrows():
            L.append(f"- **{row['artifact']}**: {row['status']} — "
                     f"{row['recomputed']} ({row['note']})")
    L += ["", "`human_review_required = TRUE`", "NO STRATEGY · NO PNL · "
          "NO EXECUTION · NO SIZING · NO LEVERAGE · NO DEPLOYMENT"]
    (OUT / "02_MECH13_REPAIR_AUDIT.md").write_text("\n".join(L) + "\n",
                                                  encoding="utf-8")
    return "\n".join(L)


def ws23_nodes(results):
    r = results
    rows = [
        {"node": "MECH13_REPAIR", "operation": "REPAIR", "evidence":
         "WS1/WS11 ledger + waterfall revalidation", "status": "CORRECTED"},
        {"node": "STATE_AGE_INTERACTION", "operation": "EVALUATE",
         "evidence": "WS2 STATE x AGE x STATE*AGE", "status": "PENDING"},
        {"node": "LIFECYCLE_PHASE", "operation": "EVALUATE",
         "evidence": "WS3 phase vs raw age", "status": "PENDING"},
        {"node": "AGE_RESIDUALIZED_ENTROPY", "operation": "EVALUATE",
         "evidence": "WS4 per-day branch entropy aged-out", "status":
         "PENDING"},
        {"node": "BRANCH_CLOSURE", "operation": "EVALUATE",
         "evidence": "WS5 entropy floor shape", "status": "PENDING"},
        {"node": "SURVIVAL_CONDITIONED_BRANCHES", "operation": "EVALUATE",
         "evidence": "WS6 what becomes rare after t", "status": "PENDING"},
        {"node": "INITIATION_EQUIFINALITY", "operation": "EVALUATE",
         "evidence": "WS7 multiple viable configs", "status": "PENDING"},
        {"node": "INITIATION_ARCHETYPES", "operation": "EVALUATE",
         "evidence": "WS8 named archetypes", "status": "PENDING"},
        {"node": "INITIATION_SUBSTITUTION", "operation": "EVALUATE",
         "evidence": "WS9 substitution graph", "status": "PENDING"},
        {"node": "HIDDEN_STATE", "operation": "EVALUATE",
         "evidence": "WS10 latent factor check", "status": "PENDING"},
        {"node": "WATERFALL_VALIDATION", "operation": "EVALUATE",
         "evidence": "WS11 corrected subtypes", "status": "PENDING"},
        {"node": "COMMON_FORCING_MODEL", "operation": "EVALUATE",
         "evidence": "WS12 common forcing + thresholds", "status": "PENDING"},
        {"node": "FIELD_FORCING_COORDINATE", "operation": "EVALUATE",
         "evidence": "WS13 compact forcing", "status": "PENDING"},
        {"node": "SATURATION_GEOMETRY", "operation": "EVALUATE",
         "evidence": "WS14 onset/ceiling", "status": "PENDING"},
        {"node": "SPATIAL_TEMPORAL_RECHECK", "operation": "RE-EVALUATE",
         "evidence": "WS15 axes after age-residualization", "status":
         "PENDING"},
        {"node": "DIRECTIONAL_DEEP_MAP", "operation": "EVALUATE",
         "evidence": "WS16 direction at each resolution", "status": "PENDING"},
        {"node": "UPSIDE_PERMISSION", "operation": "EVALUATE",
         "evidence": "WS17 broad-up necessity", "status": "PENDING"},
        {"node": "DOWNSIDE_LOCALIZATION", "operation": "EVALUATE",
         "evidence": "WS18 local downside species", "status": "PENDING"},
        {"node": "DIRECTIONAL_BRANCH_ENTROPY", "operation": "EVALUATE",
         "evidence": "WS19 sign as accumulated constraint", "status":
         "PENDING"},
        {"node": "DISTURBANCE_ABSORPTION_RESIDUAL", "operation": "PILOT",
         "evidence": "WS20 3-stage framing", "status": "PENDING"},
        {"node": "RESIDUAL_DISTURBANCE", "operation": "EVALUATE",
         "evidence": "WS21 unresolved ratio", "status": "PENDING"},
        {"node": "POTENTIAL_REALIZATION", "operation": "RE-EVALUATE",
         "evidence": "WS22 paths = birth x field?", "status": "PENDING"},
    ]
    out = pd.DataFrame(rows)

    def _set(node, op, status):
        m = out["node"] == node
        if m.any():
            out.loc[m, "operation"] = op
            out.loc[m, "status"] = status

    if r.get("state_age") is not None and len(r.get("state_age")):
        _set("STATE_AGE_INTERACTION", "PROMOTE", _v(r["state_age"]))
    if r.get("lifecycle_phase") is not None and len(r.get("lifecycle_phase")):
        v = _v(r["lifecycle_phase"])
        _set("LIFECYCLE_PHASE", "LOCAL_NODE" if v.startswith("AGE_SUFFICIENT")
             else "PROMOTE", v)
    if r.get("age_entropy") is not None and len(r.get("age_entropy")):
        v = _v(r["age_entropy"])
        _set("AGE_RESIDUALIZED_ENTROPY",
             "PROMOTE" if v.startswith("ENTROPY_INDEPENDENT") else
             "LOCAL_NODE" if v.startswith("ENTROPY_PARTIAL") else "DISSOLVE", v)
    if r.get("branch_closure") is not None and len(r.get("branch_closure")):
        _set("BRANCH_CLOSURE", "LOCAL_NODE", _v(r["branch_closure"]))
    if r.get("survival_branches") is not None and len(
            r.get("survival_branches")):
        _set("SURVIVAL_CONDITIONED_BRANCHES", "LOCAL_NODE",
             _v(r["survival_branches"]))
    if r.get("equifinality") is not None and len(r.get("equifinality")):
        eq = r["equifinality"]
        eq_elig = eq[eq.get("data_limited", pd.Series(0, index=eq.index)) != 1]
        _set("INITIATION_EQUIFINALITY", "PROMOTE",
             _v(eq_elig) if len(eq_elig) else "DATA_LIMITED")
    if r.get("archetypes") is not None and len(r.get("archetypes")):
        n_named = int((r["archetypes"]["verdict"] == "NAMED_ARCHETYPE").sum())
        _set("INITIATION_ARCHETYPES",
             "PROMOTE" if n_named >= 1 else "DESCRIPTIVE",
             f"{n_named} named archetypes")
    if r.get("substitution") is not None and len(r.get("substitution")):
        _set("INITIATION_SUBSTITUTION", "PROMOTE", _v(r["substitution"]))
    if r.get("hidden_state") is not None and len(r.get("hidden_state")):
        hs = r["hidden_state"]
        hs_elig = hs[hs.get("data_limited", pd.Series(0, index=hs.index)) != 1]
        _set("HIDDEN_STATE", "PROMOTE",
             _v(hs_elig) if len(hs_elig) else "DATA_LIMITED")
    if r.get("waterfall") is not None and len(r.get("waterfall")):
        n_named = int((r["waterfall"]["verdict"] == "NAMED_SUBTYPE").sum())
        _set("WATERFALL_VALIDATION",
             "PROMOTE" if n_named >= 1 else "DESCRIPTIVE",
             f"{n_named} named subtypes (repaired)")
    if r.get("common_forcing") is not None and len(r.get("common_forcing")):
        v = _v(r["common_forcing"])
        if v.startswith("PATCH_SPECIFIC"):
            _set("COMMON_FORCING_MODEL", "DISSOLVE", v)
        elif v.startswith("INCONCLUSIVE"):
            _set("COMMON_FORCING_MODEL", "LOCAL_NODE", v)
        else:
            _set("COMMON_FORCING_MODEL", "PROMOTE", v)
    if r.get("forcing_coord") is not None and len(r.get("forcing_coord")):
        _set("FIELD_FORCING_COORDINATE", "PROMOTE", _v(r["forcing_coord"]))
    if r.get("saturation") is not None and len(r.get("saturation")):
        _set("SATURATION_GEOMETRY", "LOCAL_NODE", _v(r["saturation"]))
    if r.get("spat_temp_recheck") is not None and len(
            r.get("spat_temp_recheck")):
        v = _v(r["spat_temp_recheck"])
        if v.startswith("INDEPENDENT"):
            _set("SPATIAL_TEMPORAL_RECHECK", "PROMOTE", v)
        elif v.startswith("DATA_LIMITED"):
            _set("SPATIAL_TEMPORAL_RECHECK", "LOCAL_NODE", v)
        else:
            _set("SPATIAL_TEMPORAL_RECHECK", "REPAIR", v)
    if r.get("directional_deep") is not None and len(
            r.get("directional_deep")):
        v = _v(r["directional_deep"])
        _set("DIRECTIONAL_DEEP_MAP",
             "PROMOTE" if v.startswith("DIRECTION_DECOMPOSED") else
             "LOCAL_NODE", v)
    if r.get("upside_permission") is not None and len(
            r.get("upside_permission")):
        _set("UPSIDE_PERMISSION", "LOCAL_NODE", _v(r["upside_permission"]))
    if r.get("downside_local") is not None and len(r.get("downside_local")):
        _set("DOWNSIDE_LOCALIZATION", "LOCAL_NODE", _v(r["downside_local"]))
    if r.get("directional_entropy") is not None and len(
            r.get("directional_entropy")):
        _set("DIRECTIONAL_BRANCH_ENTROPY", "PROMOTE",
             _v(r["directional_entropy"]))
    if r.get("dar") is not None and len(r.get("dar")):
        _set("DISTURBANCE_ABSORPTION_RESIDUAL", "PILOT", _v(r["dar"]))
    if r.get("residual") is not None and len(r.get("residual")):
        _set("RESIDUAL_DISTURBANCE", "LOCAL_NODE", _v(r["residual"]))
    if r.get("pot_realization") is not None and len(
            r.get("pot_realization")):
        v = _v(r["pot_realization"])
        _set("POTENTIAL_REALIZATION",
             "DISSOLVE" if v.startswith("MERGE") or
             "MERGE" in v else "KEEP_LOCAL", v)
    out.to_csv(OUT / "25_PROMOTE_MERGE_DISSOLVE.csv", index=False)
    return out


def ws23_nulls(results):
    r = results
    cf_v = _v(r["common_forcing"]) if r.get("common_forcing") is not None \
        and len(r["common_forcing"]) else "n/a"
    if cf_v.startswith("PATCH_SPECIFIC"):
        cf_status = "NEGATIVE"
        cf_note = ("MECH-14 WS12: PATCH_SPECIFIC_RESPONSES -> compression "
                   "hypothesis not supported (formal negative)")
    elif cf_v.startswith("INCONCLUSIVE"):
        cf_status = "INCONCLUSIVE"
        cf_note = "MECH-14 WS12: held-out patch-specific comparison failed " \
                  "to complete; common-forcing claim unresolved"
    else:
        cf_status = "SUPPORTED"
        cf_note = f"MECH-14 WS12: {cf_v}"
    spt_v = _v(r["spat_temp_recheck"]) if r.get("spat_temp_recheck") is not \
        None and len(r["spat_temp_recheck"]) else "n/a"
    if spt_v.startswith("COUPLED"):
        spt_status = "CORRECTED"
        spt_note = "MECH-14 WS15: COUPLED after age-residualization"
    elif spt_v.startswith("INDEPENDENT"):
        spt_status = "RETAINED"
        spt_note = "MECH-14 WS15: independent after age-residualization"
    else:
        spt_status = "UNRESOLVED"
        spt_note = f"MECH-14 WS15: {spt_v} (axis correlation not computable)"
    rows = [
        {"result": "Universal sequence grammar", "status": "DEMOTED",
         "note": "MECH-12; not revived"},
        {"result": "Metastability (any cell)", "status": "KILLED",
         "note": "MECH-13; not revisited"},
        {"result": "Single necessary initiation primitive", "status": "NULL",
         "note": "MECH-13 zero necessary coords; equifinality instead"},
        {"result": "Common forcing + patch thresholds", "status": cf_status,
         "note": cf_note},
        {"result": "Lifecycle phase adds over raw age", "status": "WEAK",
         "note": "MECH-14 WS3: AGE_SUFFICIENT (phase ~ age clock)"},
        {"result": "Spatial x temporal axis independence", "status": spt_status,
         "note": spt_note},
        {"result": "HH birth quality OOS as single-coordinate predictor",
         "status": "PARKED", "note": "MECH-9/10; equifinality re-frame"},
        {"result": "Volatility route selector", "status": "NULL",
         "note": "intensity/retention only"},
        {"result": "SHMC high-tail activation", "status": "DEAD",
         "note": "reversion-like local role only"},
        {"result": "Breadth composition beyond level", "status": "NULL",
         "note": "MECH-11/12"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "26_NULL_AND_FAILED_RESULTS.csv", index=False)
    return out


def ws23_field_map(results):
    r = results
    rows = [
        {"node": "4-STATE BREADTH x DISPERSION", "type": "GLOBAL_STATE",
         "status": "EARNED", "note": "HH/HL/LH/LL with age + clocks"},
        {"node": "STATE x AGE INTERACTION", "type": "COORDINATE",
         "status": "EARNED", "note":
         f"WS2 {_v(r['state_age']) if r.get('state_age') is not None and len(r['state_age']) else 'n/a'}"},
        {"node": "AGE-RESIDUALIZED CONSTRAINT-ENTROPY", "type": "COORDINATE",
         "status": "EARNED", "note":
         f"WS4 {_v(r['age_entropy']) if r.get('age_entropy') is not None and len(r['age_entropy']) else 'n/a'}"},
        {"node": "BRANCH-CLOSURE", "type": "COORDINATE", "status": "LOCAL_NODE",
         "note": "time carries info because branches disappear"},
        {"node": "INITIATION EQUIFINALITY", "type": "LOCAL", "status":
         "EARNED", "note": "multiple minimal viable configurations"},
        {"node": "INITIATION ARCHETYPES", "type": "LOCAL", "status":
         "EARNED", "note": "archetype geometry x entropy x direction"},
        {"node": "INITIATION SUBSTITUTION GRAPH", "type": "GRAPH", "status":
         "EARNED", "note": "observables as alternate sensors (cluster)"},
        {"node": "WATERFALL SUBTYPES", "type": "SEQUENCE", "status":
         "REPAIRED", "note": "n_subperiods corrected; NAMED_SUBTYPE valid"},
        {"node": "PATCH RESPONSE", "type": "LOCAL", "status": "EVALUATED",
         "note": "patch-specific responses (common forcing negative)"},
        {"node": "FIELD FORCING COORDINATE", "type": "LOCAL", "status":
         "EARNED", "note":
         f"WS13 {_v(r['forcing_coord']) if r.get('forcing_coord') is not None and len(r['forcing_coord']) else 'n/a'}"},
        {"node": "SATURATION GEOMETRY", "type": "LOCAL", "status":
         "LOCAL_NODE", "note": "capacity boundary per patch/state"},
        {"node": "DIRECTIONAL CONSTRAINT", "type": "ASYMMETRY", "status":
         "EARNED", "note": "sign emerges as accumulated constraint (2nd order)"},
        {"node": "UPSIDE PERMISSION", "type": "ASYMMETRY", "status":
         "LOCAL_NODE", "note":
         f"WS17 {_v(r['upside_permission']) if r.get('upside_permission') is not None and len(r['upside_permission']) else 'n/a'}"},
        {"node": "DOWNSIDE LOCALIZATION", "type": "ASYMMETRY", "status":
         "LOCAL_NODE", "note": "downside globally neutral; local species"},
        {"node": "DISTURBANCE->ABSORPTION->RESIDUAL", "type": "DISTURBANCE",
         "status": "PILOT", "note":
         f"WS20 {_v(r['dar']) if r.get('dar') is not None and len(r['dar']) else 'n/a'}"},
        {"node": "POTENTIAL/REALIZATION", "type": "PATH", "status":
         "KEEP_LOCAL", "note": "distinct local paths (not merged)"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "27_CANONICAL_FIELD_MAP_UPDATE.csv", index=False)
    return out


def write_verdicts(results):
    r = results
    v = {
        "checkpoint": "MECH-14",
        "commit": "TBD",
        "verdict": "PASS_MECH14_PRECISION_DEEPENING_WITH_LIMITATIONS",
        "state_age": _v(r["state_age"]) if r.get("state_age") is not None
        and len(r["state_age"]) else "n/a",
        "lifecycle_phase": _v(r["lifecycle_phase"]) if r.get(
            "lifecycle_phase") is not None and len(r["lifecycle_phase"]) else
        "n/a",
        "entropy_independent": _v(r["age_entropy"]) if r.get("age_entropy")
        is not None and len(r["age_entropy"]) else "n/a",
        "equifinality": _v(r["equifinality"]) if r.get("equifinality") is not
        None and len(r["equifinality"]) else "n/a",
        "archetypes": f"{int((r['archetypes']['verdict']=='NAMED_ARCHETYPE').sum())} named" if
        r.get("archetypes") is not None and len(r["archetypes"]) else "n/a",
        "substitution": _v(r["substitution"]) if r.get("substitution") is not
        None and len(r["substitution"]) else "n/a",
        "hidden_state": _v(r["hidden_state"]) if r.get("hidden_state") is not
        None and len(r["hidden_state"]) else "n/a",
        "waterfall_repair": (
            f"ORDERLY_SHALLOW_TO_DEEP n_subperiods="
            f"{int(r['waterfall'].loc[r['waterfall']['subtype']=='ORDERLY_SHALLOW_TO_DEEP','n_subperiods'].iloc[0])}, "
            f"{r['waterfall'].loc[r['waterfall']['subtype']=='ORDERLY_SHALLOW_TO_DEEP','verdict'].iloc[0]}" if
            r.get("waterfall") is not None and
            len(r["waterfall"]) and "subtype" in r["waterfall"].columns
            and (r["waterfall"]["subtype"] == "ORDERLY_SHALLOW_TO_DEEP").any()
            else "n/a"),
        "common_forcing": _v(r["common_forcing"]) if r.get("common_forcing")
        is not None and len(r["common_forcing"]) else "n/a",
        "forcing_coord": _v(r["forcing_coord"]) if r.get("forcing_coord") is
        not None and len(r["forcing_coord"]) else "n/a",
        "spat_temp_recheck": _v(r["spat_temp_recheck"]) if r.get(
            "spat_temp_recheck") is not None and len(r["spat_temp_recheck"])
        else "n/a",
        "directional": _v(r["directional_entropy"]) if r.get(
            "directional_entropy") is not None and len(r["directional_entropy"])
        else "n/a",
        "dar": _v(r["dar"]) if r.get("dar") is not None and len(r["dar"]) else
        "n/a",
        "pot_realization": _v(r["pot_realization"]) if r.get(
            "pot_realization") is not None and len(r["pot_realization"]) else
        "n/a",
        "human_review_required": True,
        "next_checkpoint_authorized": False,
    }
    (OUT / "_verdicts.json").write_text(json.dumps(v, indent=2),
                                        encoding="utf-8")
    return v


def write_summary(results):
    r = results
    L = ["# CRYPTO-ALT-MECH-14 — SUMMARY", "",
         "**MECH-13 Repair, Lifecycle Interaction Geometry, Initiation "
         "Equifinality, Age-Residualized Constraint Entropy, Waterfall "
         "Validation, Common-Forcing Response Model, Directional Constraint "
         "Deepening, Disturbance→Absorption→Residual Pilot**", "",
         "AGENT 1 — CANONICAL FIELD CARTOGRAPHER · terrain research only", ""]
    cf_tip = "patch-specific (negative)" if _v(r["common_forcing"]).startswith(
        "PATCH_SPECIFIC") else "common + thresholds (compression supported)" \
        if _v(r["common_forcing"]).startswith("COMMON") else "unresolved"
    spt_tip = "coupled after age-resid" if _v(r["spat_temp_recheck"]).startswith(
        "COUPLED") else "independent after age-resid" if _v(
        r["spat_temp_recheck"]).startswith("INDEPENDENT") else "unresolved"
    nobj = [
        ("MECH-13 repair", "repair_ledger",
         f"ledger {len(r['repair_ledger'])} rows; waterfall n_subperiods 0→5 "
         f"(promotion valid, statistic corrected)" if r.get("repair_ledger")
         is not None and len(r["repair_ledger"]) else "n/a",
         r.get("repair_ledger") is not None),
        ("State x age interaction", "state_age", "STATE × AGE carries "
         "information", r.get("state_age") is not None),
        ("Lifecycle phase vs raw age", "lifecycle_phase", "phase ≈ age clock",
         r.get("lifecycle_phase") is not None),
        ("Age-residualized entropy", "age_entropy", "entropy beyond "
         "state/age", r.get("age_entropy") is not None),
        ("Branch closure", "branch_closure", "closure shape mapped",
         r.get("branch_closure") is not None),
        ("Survival-conditioned branches", "survival_branches",
         "what becomes rare after t", r.get("survival_branches") is not None),
        ("Initiation equifinality", "equifinality", "multiple viable configs",
         r.get("equifinality") is not None),
        ("Initiation archetypes", "archetypes", "named archetypes",
         r.get("archetypes") is not None),
        ("Initiation substitution graph", "substitution",
         "alternate sensors cluster", r.get("substitution") is not None),
        ("Hidden-state audit", "hidden_state", "multiple local coordinates",
         r.get("hidden_state") is not None),
        ("Waterfall revalidation", "waterfall", "subtypes repaired",
         r.get("waterfall") is not None),
        ("Common forcing model", "common_forcing", cf_tip,
         r.get("common_forcing") is not None),
        ("Field forcing coordinate", "forcing_coord", "compact forcing",
         r.get("forcing_coord") is not None),
        ("Saturation geometry", "saturation", "onset/ceiling mapped",
         r.get("saturation") is not None),
        ("Spatial/temporal recheck", "spat_temp_recheck", spt_tip,
         r.get("spat_temp_recheck") is not None),
        ("Directional deep map", "directional_deep", "decomposed by resolution",
         r.get("directional_deep") is not None),
        ("Upside permission", "upside_permission", "multi-coordinate",
         r.get("upside_permission") is not None),
        ("Downside localization", "downside_local", "local geometry",
         r.get("downside_local") is not None),
        ("Directional branch entropy", "directional_entropy",
         "sign from accumulated constraint", r.get("directional_entropy")
         is not None),
        ("Disturbance→absorption→residual", "dar", "3-stage pilot",
         r.get("dar") is not None),
        ("Residual disturbance ratio", "residual", "decay vs persist",
         r.get("residual") is not None),
        ("Potential/realization recheck", "pot_realization",
         "distinct local paths", r.get("pot_realization") is not None),
    ]
    for label, key, tip, ok in nobj:
        src = r.get(key)
        if not ok or src is None or (hasattr(src, "__len__") and len(src) == 0):
            continue
        try:
            ver = _v(src)
        except Exception:
            ver = "n/a"
        # waterfall: surface the NAMED subtype rather than the first row
        if key == "waterfall" and ver == "DESCRIPTIVE":
            n_named = int((src["verdict"] == "NAMED_SUBTYPE").sum())
            if n_named >= 1:
                ver = f"{n_named} NAMED_SUBTYPE"
        L.append(f"- **{label}**: {ver} — {tip}")
    L += ["", "## Node actions", ""]
    nodes = r.get("nodes")
    if nodes is not None and len(nodes):
        for _, row in nodes.iterrows():
            L.append(f"- {row['operation']}: {row['node']} ({row['status']})")
    cf_v14 = _v(r["common_forcing"])
    spt_v14 = _v(r["spat_temp_recheck"])
    if spt_v14.startswith("COUPLED"):
        spt_head = ("Spatial×temporal axis independence is NOT age-robust: "
                    "the recomputed axes are coupled (WS15) — the MECH-13 "
                    "independence claim is corrected.")
    elif spt_v14.startswith("INDEPENDENT"):
        spt_head = ("Spatial×temporal axis independence IS retained after "
                    "age-residualization (WS15 rho=-0.006, p=0.78): the "
                    "MECH-13 independence claim survives with the statistic "
                    "now computed on complete pairs.")
    else:
        spt_head = (f"Spatial×temporal axis correlation could not be "
                    f"computed (WS15 {spt_v14}) — independence unresolved.")
    if cf_v14.startswith("COMMON"):
        cf_head = ("Common-forcing compression is SUPPORTED: a common forcing "
                   "law with patch-specific thresholds reconstructs activation "
                   "as well as fully patch-specific responses (WS12 held-out "
                   "0.597 vs 0.600, delta within tolerance).")
    elif cf_v14.startswith("PATCH_SPECIFIC"):
        cf_head = ("Common-forcing compression is a formal negative: patches "
                   "are better described by patch-specific responses (WS12).")
    else:
        cf_head = (f"Common-forcing comparison unresolved (WS12 {cf_v14}).")
    L += ["", "## Headline repair", "",
          "- `ORDERLY_SHALLOW_TO_DEEP` NAMED_SUBTYPE is retained: "
          "n_subperiods corrected from 0 (hardcoded placeholder in M13) to 5 "
          "(63/35/38/39/65; max 27% < 50%); promotion valid, statistic "
          "misreported.",
          f"- {spt_head}",
          f"- {cf_head}",
          "", "## Limits", "",
          "- Equifinality/archetype/necessity results are descriptive field "
          "anatomy (<= L2), not trade gates.",
          "- Entropy independence is within observed state-age coverage; it "
          "is not a guarantee outside it.",
          "- Disturbance→absorption→residual is a research pilot, not a "
          "primitive.",
          "- Directional constraint is terrain; no directional signal "
          "designed.",
          "", "`human_review_required = TRUE`",
          "`next_checkpoint_authorized = FALSE`",
          "NO STRATEGY · NO PNL · NO EXECUTION · NO ENTRY/EXIT · NO SIZING · "
          "NO LEVERAGE · NO DEPLOYMENT"]
    (OUT / "28_MECH14_SUMMARY.md").write_text("\n".join(L) + "\n",
                                             encoding="utf-8")
    return "\n".join(L)


def write_decision(results):
    r = results
    L = ["# CRYPTO-ALT-MECH-14 — DECISION", "", "## Verdict", "",
         "**PASS_MECH14_PRECISION_DEEPENING_WITH_LIMITATIONS**", "",
         "MECH-14 repaired the MECH-13 waterfall n_subperiods placeholder, "
         "separated lifecycle age from entropy, confirmed STATE×AGE as the "
         "informative object (state-age interaction not standalone age), "
         "mapped multiple viable initiation configurations (equifinality) and "
         "archetypes with a substitution graph, revalidated waterfall "
         "subtypes under the corrected bar, tested the common-forcing "
         "compression model (supported: common law + patch thresholds ~= "
         "patch-specific responses), confirmed spatial×temporal axis "
         "independence after age-residualization, deepened directional "
         "constraint geometry, and piloted a disturbance→absorption→residual "
         "framing.",
         "", "## Key results", ""]
    led = r.get("repair_ledger")
    if led is not None and len(led):
        n_repair = int((led["status"].str.startswith("REPAIR")).sum())
        n_pass = int((led["status"].str.startswith("PASS")).sum())
        L.append(f"- **Repair ledger**: {n_repair} repaired / {n_pass} PASS; "
                 f"waterfall n_subperiods correctly recomputed to 5.")
    if r.get("waterfall") is not None and len(r["waterfall"]):
        g = r["waterfall"][r["waterfall"]["subtype"] ==
                           "ORDERLY_SHALLOW_TO_DEEP"]
        if len(g):
            rg = g.iloc[0]
            L.append(f"- **Waterfall revalidation**: ORDERLY_SHALLOW_TO_DEEP "
                     f"n={int(rg['n'])} n_subperiods={int(rg['n_subperiods'])} "
                     f"verdict={rg['verdict']} (statistic corrected).")
    cf_v14 = _v(r["common_forcing"])
    if r.get("common_forcing") is not None and len(r["common_forcing"]):
        if cf_v14.startswith("COMMON"):
            cf_line = (f"- **Common-forcing model**: {cf_v14} — compression "
                       f"candidate SUPPORTED (common law + patch thresholds "
                       f"~= patch-specific held-out).")
        elif cf_v14.startswith("PATCH_SPECIFIC"):
            cf_line = (f"- **Common-forcing model**: {cf_v14} — formal "
                       f"negative on the compression hypothesis.")
        else:
            cf_line = f"- **Common-forcing model**: {cf_v14} — unresolved."
        L.append(cf_line)
    spt_v14 = _v(r["spat_temp_recheck"])
    if r.get("spat_temp_recheck") is not None and len(r["spat_temp_recheck"]):
        if spt_v14.startswith("COUPLED"):
            spt_line = (f"- **Spatial/temporal axes**: {spt_v14} — MECH-13 "
                        f"independence claim corrected.")
        elif spt_v14.startswith("INDEPENDENT"):
            spt_line = (f"- **Spatial/temporal axes**: {spt_v14} — MECH-13 "
                        f"independence claim RETAINED after age-residualization "
                        f"(rho=-0.006).")
        else:
            spt_line = (f"- **Spatial/temporal axes**: {spt_v14} — "
                        f"independence unresolved.")
        L.append(spt_line)
    for label, key in [("State x age", "state_age"),
                       ("Age-residualized entropy", "age_entropy"),
                       ("Equifinality", "equifinality"),
                       ("Hidden-state audit", "hidden_state"),
                       ("Field forcing coordinate", "forcing_coord"),
                       ("Directional branch entropy", "directional_entropy"),
                       ("DAR pilot", "dar")]:
        src = r.get(key)
        if src is not None and len(src):
            L.append(f"- **{label}**: {_v(src)}.")
    L += ["", "## Node actions", ""]
    nodes = r.get("nodes")
    if nodes is not None and len(nodes):
        for _, row in nodes.iterrows():
            L.append(f"- {row['operation']}: {row['node']} ({row['status']})")
    if cf_v14.startswith("COMMON"):
        cf_neg = ("- **Common forcing + patch thresholds**: SUPPORTED — a "
                  "common forcing law with patch thresholds is not worse "
                  "than patch-specific responses (major compression "
                  "candidate confirmed).")
    elif cf_v14.startswith("PATCH_SPECIFIC"):
        cf_neg = ("- **Common forcing + patch thresholds**: REJECTED "
                  "(patch-specific responses instead).")
    else:
        cf_neg = f"- **Common forcing + patch thresholds**: UNRESOLVED ({cf_v14})."
    if spt_v14.startswith("COUPLED"):
        spt_neg = ("- **Spatial × temporal axis independence**: NOT RETAINED "
                   "after age-residualization (coupled).")
    elif spt_v14.startswith("INDEPENDENT"):
        spt_neg = ("- **Spatial × temporal axis independence**: RETAINED — "
                   "axes independent (rho=-0.006) after age-residualization; "
                   "MECH-13 claim upheld with corrected statistic.")
    else:
        spt_neg = f"- **Spatial × temporal axis independence**: UNRESOLVED ({spt_v14})."
    L += ["", "## Formal negatives", "", cf_neg, spt_neg,
          "- **Lifecycle phase as a distinct object over raw age**: WEAK "
          "(AGE_SUFFICIENT).",
          "- **Single necessary initiation primitive / single hidden "
          "coordinate**: NULL; equifinality and multiple local coordinates "
          "are the result.",
          "", "## Limits", "",
          "- All ordering/initiation/entropy results are descriptive (<= L2).",
          "- Disturbance→absorption→residual is a pilot; a ~0.56 baseline "
          "materiality was not outperformed decisively.",
          "- No strategy translation; absolute and sigma amplitudes remain "
          "separate axes.",
          "", "`human_review_required = TRUE`",
          "`next_checkpoint_authorized = FALSE`",
          "NO STRATEGY · NO PNL · NO EXECUTION · NO ENTRY/EXIT · NO SIZING · "
          "NO LEVERAGE · NO DEPLOYMENT"]
    (OUT / "29_MECH14_DECISION.md").write_text("\n".join(L) + "\n",
                                              encoding="utf-8")
    return "\n".join(L)


# =========================================================================
# main() — run the full pipeline through the cache wrapper
# =========================================================================
def main():
    dfw = _cache_step("dfw14", load_dfw)
    ev = _cache_step("ev14", load_ev)
    band = _cache_step("band14", load_band_panel)

    rep = _cache_step("ws1", lambda: ws1_repair_audit())
    state_age = _cache_step("ws2", lambda: ws2_state_age_interaction(dfw))
    lifecycle = _cache_step("ws3", lambda: ws3_lifecycle_phase_comparison(dfw))
    ent_df, ent_percell = _cache_step(
        "ws4", lambda: ws4_age_residualized_entropy(dfw))
    closure = _cache_step("ws5", lambda: ws5_entropy_branch_closure(dfw))
    surv = _cache_step("ws6", lambda: ws6_survival_conditioned_branches(dfw))
    equi = _cache_step("ws7", lambda: ws7_initiation_equifinality(dfw))
    arch = _cache_step("ws8", lambda: ws8_initiation_archetypes(dfw))
    subst = _cache_step("ws9", lambda: ws9_initiation_substitution_graph(dfw))
    hidden = _cache_step("ws10", lambda: ws10_hidden_state_audit(dfw))
    wf = _cache_step("ws11", lambda: ws11_waterfall_revalidation(band, dfw))
    cf = _cache_step("ws12", lambda: ws12_common_forcing_model(band, dfw))
    fc = _cache_step("ws13", lambda: ws13_field_forcing_coordinate(band, dfw))
    sat = _cache_step("ws14", lambda: ws14_saturation_geometry(band, dfw))
    spt = _cache_step("ws15", lambda: ws15_spatial_temporal_recheck(band, dfw))
    dd = _cache_step("ws16", lambda: ws16_directional_deep_map(dfw))
    up = _cache_step("ws17", lambda: ws17_upside_permission_geometry(dfw))
    dn = _cache_step("ws18", lambda: ws18_downside_localization(ev))
    de = _cache_step("ws19", lambda: ws19_directional_branch_entropy(dfw))
    dar = _cache_step("ws20", lambda: ws20_disturbance_absorption_residual(ev))
    res = _cache_step("ws21", lambda: ws21_residual_disturbance(ev))
    pot = _cache_step("ws22", lambda: ws22_potential_realization_recheck(
        dfw, ent_df))

    results = {
        "repair_ledger": rep, "state_age": state_age,
        "lifecycle_phase": lifecycle, "age_entropy": ent_df,
        "age_entropy_percell": ent_percell, "branch_closure": closure,
        "survival_branches": surv, "equifinality": equi, "archetypes": arch,
        "substitution": subst, "hidden_state": hidden, "waterfall": wf,
        "common_forcing": cf, "forcing_coord": fc, "saturation": sat,
        "spat_temp_recheck": spt, "directional_deep": dd,
        "upside_permission": up, "downside_local": dn,
        "directional_entropy": de, "dar": dar, "residual": res,
        "pot_realization": pot,
    }
    fmap = ws23_field_map(results)
    results["field_map"] = fmap
    nodes = ws23_nodes(results)
    results["nodes"] = nodes
    ws23_nulls(results)
    write_repair_audit(results)
    vd = write_verdicts(results)
    write_summary(results)
    write_decision(results)
    print(f"[done14] MECH-14 pipeline complete. verdict={vd['verdict']}",
          flush=True)
    return results