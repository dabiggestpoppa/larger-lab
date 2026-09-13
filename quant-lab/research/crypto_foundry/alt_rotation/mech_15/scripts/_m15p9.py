from _m15base import *
from _m15base import _cache_step, _age_band, _fdr, _fmt, _entropy, \
    _subperiod_split, MC, cell_stats
from _m15p1 import ws1_raw_matrix, ws2_support_audit, ws3_cell_differentiation, \
    ws4_similarity_matrix
from _m15p2 import ws5_merge_tree, ws6_information_retention, \
    ws6_partition_at
from _m15p3 import ws7_state_age_overlay, ws8_age_effect_consistency, \
    ws9_branch_closure_surface
from _m15p4 import ws10_forcing_position, ws11_activation_depth_profile, \
    ws12_waterfall_cell_placement
from _m15p5 import ws13_initiation_archetype_mix, \
    ws14_equifinality_inside_matrix, ws15_directional_entropy_surface, \
    ws16_directional_asymmetry_surface, _archetype_adds_info
from _m15p6 import ws17_upside_permission_cells, \
    ws18_downside_localization_cells, ws19_tail_activation_surface, \
    ws20_rank_recruitment_surface
from _m15p7 import ws21_residual_disturbance_overlay, \
    ws22_transition_matrix, ws23_temporal_highway_map, \
    ws24_cell_entry_survival_exit
from _m15p8 import ws25_matrix_null_test, ws26_heldout_stability


# =========================================================================
# WS27: MARKET OS STATE-SURFACE CANDIDATE (28_MARKET_OS_STATE_SURFACE_SPEC.md)
# =========================================================================
def ws27_market_os_spec(results):
    surv = results.get("null_test")
    held = results.get("heldout")
    null_v = str(surv["matrix_verdict"].iloc[0]) if surv is not None and \
        len(surv) else "n/a"
    held_v = str(held["verdict"].iloc[0]) if held is not None and len(held) \
        else "n/a"
    survived = null_v.startswith("MATRIX_SURVIVES") and \
        held_v.startswith("STABLE")
    status = "CANDIDATE_v0.1" if survived else \
        "CONDITIONAL" if null_v.startswith("MATRIX_SURVIVES") or \
        held_v.startswith("STABLE") else "NOT_APPROVED"
    L = [
        "# MARKET OS STATE-SURFACE CANDIDATE v0.1 (ONTOLOGY SPEC)",
        "",
        "**Status**: " + status,
        "",
        "This is an ontology/specification artifact ONLY. No production code,",
        "no strategy translation, no execution. It encodes the smallest",
        "empirically surviving state surface from MECH-15.",
        "",
        "## 1. Object",
        "",
        "```",
        "MarketFieldCell {",
        "  global_state:      HH | HL | LH | LL            # breadth30 x dispersion30",
        "  spatial_activation: HA | LA                     # >=3 patches active (ppos>=0.55)",
        "  temporal_constraint: HE | LE                    # age-residualized 7D branch entropy >= 0",
        "  age_band:          AGE_1 | AGE_2_3 | AGE_4_7 | AGE_8_14 | AGE_15_PLUS",
        "  forcing_level:     float                        # PC1 of common forcing coordinate",
        "  rank_depth:        SHALLOW | MID | DEEP         # deepest activated patch tier",
        "  branch_entropy:    float                        # 7D next-state entropy (bits)",
        "  directional_entropy: float                      # P(up)/P(down) sign entropy (bits)",
        "  confidence:        ROBUST | LOCAL | SPARSE | UNUSABLE",
        "  support:           {n_days, n_subperiods, max_subperiod_share}",
        "  ontology_version:  \"crypto-field-matrix-v0.1\"",
        "}",
        "```",
        "",
        "## 2. Hierarchy (unchanged from preregistration)",
        "",
        "GLOBAL MARKET FIELD -> CONSTRAINT CONDITION -> STATE x AGE -> RANK PATCH",
        "-> RELATIONAL STATE (overlay) -> ASSET HEALTH (overlay) -> OPPORTUNITY LATER",
        "",
        "## 3. Falsification status",
        "",
        f"- Shuffle/label null: {null_v}",
        f"- Held-out stability: {held_v}",
        f"- Final checkpoint verdict: {results.get('final_verdict', 'TBD')}",
        "",
        "## 4. Governance",
        "",
        "- Not a signal matrix; no long/short rules; no cell selection by",
        "  performance; no strategy translation.",
        "- Metastability dead; universal sequence grammar demoted; no invented",
        "  latent factors; absolute and sigma amplitudes separate axes.",
    ]
    (OUT / "28_MARKET_OS_STATE_SURFACE_SPEC.md").write_text("\n".join(L) + "\n",
                                                           encoding="utf-8")
    return "\n".join(L)


# =========================================================================
# WS28: CELL LABELING GUIDE (29_CELL_LABELING_GUIDE.md)
# =========================================================================
def ws28_cell_labeling_guide(results):
    raw = results.get("raw")
    closure = results.get("branch_closure")
    dents = results.get("dir_entropy")
    L = ["# MECH-15 CELL LABELING GUIDE", "",
         "## Canonical names (primary, deterministic)",
         "",
         "HH_HA_HE  HH_HA_LE  HH_LA_HE  HH_LA_LE", 
         "HL_HA_HE  HL_HA_LE  HL_LA_HE  HL_LA_LE",
         "LH_HA_HE  LH_HA_LE  LH_LA_HE  LH_LA_LE",
         "LL_HA_HE  LL_HA_LE  LL_LA_HE  LL_LA_LE",
         "",
         "## Descriptive labels (optional, only where stable)",
         ""]
    if closure is not None and len(closure):
        L.append("Branch-closure labels (per cell, from 10_BRANCH_CLOSURE_SURFACE.csv):")
        for _, r in closure.iterrows():
            L.append(f"- {r['mcell']}: {r['closure_label']} "
                     f"(subperiod-consistent {r['label_subperiod_consistency']:.0%})")
        L.append("")
    if dents is not None and len(dents):
        L.append("Directional-context labels (from 16_DIRECTIONAL_ENTROPY_SURFACE.csv):")
        for _, r in dents.iterrows():
            L.append(f"- {r['mcell']}: dir_entropy={r['dir_entropy']:.2f} bits "
                     f"(reduction vs state {r['reduction_vs_state']:+.2f})")
        L.append("")
    L += ["## Rules",
          "",
          "- Descriptive names are proposed only after analysis and only for",
          "  cells whose behavior is stable (>=3 subperiods) and genuinely",
          "  distinct (WS3 DISTINCT).",
          "- No cute names invented up front; canonical codes remain primary.",
          "`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`"]
    (OUT / "29_CELL_LABELING_GUIDE.md").write_text("\n".join(L) + "\n",
                                                  encoding="utf-8")
    return "\n".join(L)


def _v(series):
    if isinstance(series, pd.DataFrame):
        return _v(series["verdict"]) if "verdict" in series.columns else "n/a"
    s = series.dropna()
    return str(s.iloc[0]) if len(s) else "n/a"


# =========================================================================
# WS29: PROMOTE / MERGE / DISSOLVE (30_PROMOTE_MERGE_DISSOLVE.csv)
# =========================================================================
def ws29_promote_merge_dissolve(results):
    raw = results["raw"]
    support = results["support"]
    diff = results["differentiation"]
    merge = results["merge_tree"]
    ret = results["retention"]
    rows = []
    # per-cell decision
    rec_cut = results["recommended_cells"]
    names = list(MC)
    reps = {}       # mcell -> representative mcell of its merge group
    group_members = {}
    if rec_cut < 16:
        part = ws6_partition_at(results["frame"], names, rec_cut)
        n_by = dict(zip(support["mcell"], support["n_days"]))
        for gi, grp in enumerate(part):
            if len(grp) == 1:
                continue
            members = [names[mi] for mi in grp]
            rep = max(members, key=lambda c: n_by.get(c, 0))
            group_members[rep] = members
            for m in members:
                if m != rep:
                    reps[m] = rep
    for _, r in support.iterrows():
        mc = r["mcell"]
        raw_row = raw[raw["mcell"] == mc]
        if r["grade"] == "UNUSABLE":
            rows.append({"node": mc, "operation": "DATA_BLOCKED",
                         "evidence": f"n={r['n_days']}", "status":
                         "UNUSABLE"})
            continue
        if mc in reps:
            rows.append({"node": mc, "operation": "MERGE",
                         "evidence": f"merged into {reps[mc]} at "
                                     f"{rec_cut}-cell cut",
                         "status": "MERGED"})
            continue
        if mc in group_members:
            # representative of a merge group
            if r["grade"] == "ROBUST":
                op = "PROMOTE"
            elif r["grade"] == "LOCAL":
                op = "LOCAL_NODE"
            else:
                op = "DESCRIPTIVE"
            rows.append({"node": mc, "operation": op,
                         "evidence": f"rep of {', '.join(group_members[mc])} "
                                     f"at {rec_cut}-cell cut; grade="
                                     f"{r['grade']} n={r['n_days']} "
                                     f"sp={r['n_subperiods']}", "status": op})
            continue
        if r["grade"] == "ROBUST":
            op = "PROMOTE"
        elif r["grade"] == "LOCAL":
            op = "LOCAL_NODE"
        else:
            op = "DESCRIPTIVE"
        rows.append({"node": mc, "operation": op,
                     "evidence": f"grade={r['grade']} n={r['n_days']} "
                                 f"sp={r['n_subperiods']}", "status": op})
    # representation-level decisions
    n_distinct = int((diff["verdict"] == "DISTINCT").sum()) if diff is not \
        None and len(diff) else 0
    n_pairs = len(diff) if diff is not None else 0
    rows.append({"node": "16-CELL_MATRIX", "operation":
                 "PROMOTE" if results["final_verdict"].startswith(
                     "PASS_MECH15_16") else
                 "LOCAL_NODE" if results["final_verdict"].startswith(
                     "PASS_MECH15_LOCAL") else "DISSOLVE",
                 "evidence": f"{n_distinct}/{n_pairs} DISTINCT pairs; "
                             f"null={results.get('null_verdict','n/a')}; "
                             f"heldout={results.get('heldout_verdict','n/a')}",
                 "status": results["final_verdict"]})
    for cut in [12, 8, 6, 4]:
        rows.append({"node": f"{cut}-CELL_REDUCED", "operation":
                     "PROMOTE" if results["recommended_cells"] == cut else
                     "DESCRIPTIVE",
                     "evidence": f"retention (mean) = "
                                 f"{results['retention_by_cut'].get(cut, np.nan):.3f}",
                     "status": "CANDIDATE" if results["recommended_cells"] ==
                     cut else "NOT_SELECTED"})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "30_PROMOTE_MERGE_DISSOLVE.csv", index=False)
    return out


# =========================================================================
# WS29: NULLS / FIELD MAP / SUMMARY / DECISION
# =========================================================================
def ws29_nulls(results):
    rows = [
        {"result": "Universal sequence grammar", "status": "DEMOTED",
         "note": "MECH-12; not revived"},
        {"result": "Metastability (any cell)", "status": "KILLED",
         "note": "MECH-13; not revisited; transition structure is NOT "
                 "metastability"},
        {"result": "Single necessary initiation primitive", "status": "NULL",
         "note": "MECH-13/14: equifinality instead"},
        {"result": "Single hidden field coordinate", "status": "NULL",
         "note": "MECH-14: MULTIPLE_LOCAL_COORDINATES"},
        {"result": "16-cell matrix as automatically valid", "status":
         "TESTED", "note": results.get("null_verdict", "n/a")},
        {"result": "Age redundant inside matrix", "status":
         results.get("age_verdict", "n/a"),
         "note": "MECH-15 WS7 state x age overlay"},
        {"result": "Common forcing + patch thresholds", "status": "SUPPORTED",
         "note": "MECH-14 WS12"},
        {"result": "DAR as primitive", "status": "PILOT",
         "note": "MECH-14/15: pilot only, not promoted"},
    ]
    for _, r in results.get("support", pd.DataFrame()).iterrows():
        if r["grade"] in ("SPARSE", "UNUSABLE"):
            rows.append({"result": f"cell {r['mcell']}", "status": "SPARSE",
                         "note": f"n={r['n_days']} subperiods="
                                 f"{r['n_subperiods']}"})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "31_NULL_AND_FAILED_RESULTS.csv", index=False)
    return out


def ws29_field_map(results):
    rows = [
        {"node": "GLOBAL FIELD STATE (HH/HL/LH/LL)", "type": "GLOBAL_STATE",
         "status": "EARNED", "note": "MECH-9..15"},
        {"node": "CONSTRAINT CONDITION (HA/LA x HE/LE)", "type": "AXIS",
         "status": "EARNED", "note": "MECH-14 WS15 age-residualized; "
         "spatial x temporal independent"},
        {"node": "16-CELL MARKET FIELD MATRIX", "type": "SURFACE",
         "status": results["final_verdict"], "note":
         f"recommended surface = {results['recommended_cells']} cells"},
        {"node": "STATE x AGE INTERACTION", "type": "OVERLAY", "status":
         "EARNED", "note": "MECH-14 WS2; MECH-15 WS7/8"},
        {"node": "AGE-RESIDUALIZED CONSTRAINT-ENTROPY", "type": "COORDINATE",
         "status": "EARNED", "note": "MECH-14 WS4"},
        {"node": "COMMON FORCING + PATCH THRESHOLDS", "type": "FORCING",
         "status": "EARNED", "note": "MECH-14 WS12; MECH-15 WS10/11/20"},
        {"node": "INITIATION EQUIFINALITY + ARCHETYPES", "type": "LOCAL",
         "status": "EARNED", "note": "MECH-14 WS7/8; MECH-15 WS13/14"},
        {"node": "WATERFALL SUBTYPES", "type": "SEQUENCE", "status":
         "REPAIRED", "note": "n_subperiods corrected; threshold ordering "
         "under common forcing"},
        {"node": "DIRECTIONAL CONSTRAINT", "type": "ASYMMETRY", "status":
         "EARNED", "note": "sign is 2nd-order accumulated constraint"},
        {"node": "DISTURBANCE->ABSORPTION->RESIDUAL", "type": "DISTURBANCE",
         "status": "PILOT", "note": "pilot only"},
        {"node": "RELATIONAL STATE (Agent 2)", "type": "OVERLAY", "status":
         "DOWNSTREAM", "note": "not part of core matrix"},
        {"node": "ASSET HEALTH (PRD)", "type": "OVERLAY", "status":
         "DOWNSTREAM", "note": "not part of core matrix"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "32_CANONICAL_FIELD_MAP_UPDATE.csv", index=False)
    return out


def ws29_summary(results):
    r = results
    L = ["# CRYPTO-ALT-MECH-15 — SUMMARY", "",
         "**16-Cell Market Field Matrix, State x Constraint Surface, Cell "
         "Differentiation, Collapse/Merge Tests, State-Age Overlay, "
         "Forcing/Threshold Positioning, Directional Entropy, Rank "
         "Recruitment, Initiation Archetype Mix, Branch-Closure Geometry, "
         "Market-OS State Surface Candidate**", "",
         "AGENT 1 — CANONICAL FIELD CARTOGRAPHER · terrain research only", ""]
    nobj = [
        ("Support audit", "support",
         f"{int((r['support']['grade']=='ROBUST').sum())} ROBUST / "
         f"{int((r['support']['grade']=='LOCAL').sum())} LOCAL / "
         f"{int((r['support']['grade']=='SPARSE').sum())} SPARSE / "
         f"{int((r['support']['grade']=='UNUSABLE').sum())} UNUSABLE"),
        ("Differentiation", "differentiation",
         f"{int((r['differentiation']['verdict']=='DISTINCT').sum())} DISTINCT / "
         f"{int((r['differentiation']['verdict']=='PARTIALLY_DISTINCT').sum())} PARTIAL / "
         f"{int((r['differentiation']['verdict']=='REDUNDANT').sum())} REDUNDANT pairs"),
        ("Merge tree", "merge_tree", "average-linkage deterministic"),
        ("Information retention", "retention", "retained fraction by cut"),
        ("State x age overlay", "age_overlay", _v(r["age_overlay"])),
        ("Age consistency", "age_consistency", "per-metric consistency label"),
        ("Branch closure", "branch_closure", _v(r["branch_closure"])),
        ("Forcing position", "forcing", "cells on common forcing coordinate"),
        ("Activation depth", "depth_profile", "SHALLOW/MID/DEEP/BROAD profile"),
        ("Waterfall placement", "waterfall", "cell hosting of waterfall roles"),
        ("Archetype mix", "archetype_mix", "per-cell archetype distribution"),
        ("Equifinality inside", "equifinality_inside", _v(r["equifinality_inside"])),
        ("Directional entropy", "dir_entropy", _v(r["dir_entropy"])),
        ("Asymmetry surface", "asymmetry", "family x cell geometry"),
        ("Upside permission", "upside", _v(r["upside"])),
        ("Downside localization", "downside", _v(r["downside"])),
        ("Tail activation", "tail", _v(r["tail"])),
        ("Rank recruitment", "rank", _v(r["rank"])),
        ("Residual overlay", "residual", _v(r["residual"])),
        ("Transitions", "transitions", "t+1/3/7 transition structure"),
        ("Highway map", "highway", "local highways / common exits"),
        ("Entry/survival/exit", "ese", _v(r["ese"])),
        ("Shuffle null", "null_test", r["null_verdict"]),
        ("Held-out stability", "heldout", r["heldout_verdict"]),
    ]
    for label, key, tip in nobj:
        src = r.get(key)
        if src is None or (hasattr(src, "__len__") and len(src) == 0):
            continue
        try:
            if key == "null_test":
                ver = r["null_verdict"]
            elif key == "heldout":
                ver = r["heldout_verdict"]
            elif key == "support":
                ver = f"{int((src['grade']=='ROBUST').sum())}R/{int((src['grade']=='LOCAL').sum())}L/{int((src['grade']=='SPARSE').sum())}S/{int((src['grade']=='UNUSABLE').sum())}U"
            elif key == "differentiation":
                ver = f"{int((src['verdict']=='DISTINCT').sum())} DISTINCT / {int((src['verdict']=='PARTIALLY_DISTINCT').sum())} PARTIAL / {int((src['verdict']=='REDUNDANT').sum())} REDUNDANT"
            else:
                ver = _v(src)
        except Exception:
            ver = "n/a"
        L.append(f"- **{label}**: {ver} — {tip}")
    L += ["", "## Key decisions", "",
          f"- **Final verdict**: {r['final_verdict']}",
          f"- **Recommended surface**: {r['recommended_cells']} cells",
          f"- **Shuffle null**: {r['null_verdict']}",
          f"- **Held-out stability**: {r['heldout_verdict']}",
          f"- **Age overlay**: {r['age_verdict']}",
          "", "## Limits", "",
          "- All cell behavior is descriptive field anatomy (<= L2), not a "
          "signal matrix.",
          "- Sparse cells are reported, not interpreted.",
          "- DAR remains pilot; residual overlay is descriptive.",
          "- Relational state and asset health are downstream overlays.",
          "", "`human_review_required = TRUE`",
          "`next_checkpoint_authorized = FALSE`",
          "NO STRATEGY · NO PNL · NO EXECUTION · NO ENTRY/EXIT · NO SIZING · "
          "NO LEVERAGE · NO DEPLOYMENT"]
    (OUT / "33_MECH15_SUMMARY.md").write_text("\n".join(L) + "\n",
                                             encoding="utf-8")
    return "\n".join(L)


def ws29_decision(results):
    r = results
    L = ["# CRYPTO-ALT-MECH-15 — DECISION", "", "## Verdict", "",
         f"**{r['final_verdict']}**", ""]
    # answer the 14 decision questions
    support = r["support"]
    n_robust = int((support["grade"] == "ROBUST").sum())
    n_local = int((support["grade"] == "LOCAL").sum())
    n_sparse = int((support["grade"] == "SPARSE").sum())
    n_unusable = int((support["grade"] == "UNUSABLE").sum())
    diff = r["differentiation"]
    n_dist = int((diff["verdict"] == "DISTINCT").sum())
    n_part = int((diff["verdict"] == "PARTIALLY_DISTINCT").sum())
    n_red = int((diff["verdict"] == "REDUNDANT").sum())
    Q = [
        ("1. Is the raw 16-cell matrix empirically valid?",
         f"support {n_robust} ROBUST / {n_local} LOCAL / {n_sparse} SPARSE / "
         f"{n_unusable} UNUSABLE; {n_dist} DISTINCT / {n_part} "
         f"PARTIALLY_DISTINCT / {n_red} REDUNDANT pairs"),
        ("2. How many cells are robust/local/sparse/unusable?",
         f"{n_robust}/{n_local}/{n_sparse}/{n_unusable}"),
        ("3. Which cells are genuinely distinct?",
         "; ".join(sorted(diff.loc[diff["verdict"] == "DISTINCT", "cell_a"]
                          .unique()))[:400] if n_dist else "none"),
        ("4. Which cells should merge?",
         "; ".join(diff.loc[diff["verdict"] == "REDUNDANT"].apply(
             lambda x: f"{x.cell_a}~{x.cell_b}", axis=1))[:400]
         if n_red else "none"),
        ("5. What is the minimum matrix preserving structural information?",
         f"{r['recommended_cells']} cells (mean retention "
         f"{r['retention_by_cut'].get(r['recommended_cells'], np.nan):.3f})"),
        ("6. Does age still add information after matrix position?",
         r["age_verdict"]),
        ("7. Which cells show strongest branch closure?",
         "; ".join(r["branch_closure"].loc[
             r["branch_closure"]["closure_label"] == "LOCKED_BRANCH",
             "mcell"]) if "branch_closure" in r and len(r["branch_closure"])
         else "none"),
        ("8. Which cells constrain direction most?",
         "; ".join(r["dir_entropy"].nsmallest(4, "dir_entropy")["mcell"]) if
         "dir_entropy" in r and len(r["dir_entropy"]) else "n/a"),
        ("9. Which cells activate deepest rank patches?",
         "; ".join(r["depth_profile"].loc[
             r["depth_profile"]["depth_profile"].isin(
                 ["DEEP_FIELD", "BROAD_FULL_FIELD"]), "mcell"]) if
         "depth_profile" in r and len(r["depth_profile"]) else "none"),
        ("10. Where does ORDERLY_SHALLOW_TO_DEEP live?",
         "; ".join(r["waterfall"].loc[
             r["waterfall"]["ORDERLY_SHALLOW_TO_DEEP"] > 0, "mcell"])
         if "waterfall" in r and len(r["waterfall"]) else "n/a"),
        ("11. Does initiation equifinality survive inside matrix cells?",
         r["equifinality_inside_verdict"]),
        ("12. Does common forcing explain matrix positioning?",
         r["forcing_verdict"]),
        ("13. Does the matrix survive held-out and shuffle nulls?",
         f"null={r['null_verdict']}; heldout={r['heldout_verdict']}"),
        ("14. Should this become Market OS State Surface v0.1?",
         r["marketos_status"]),
    ]
    L += ["## Decision questions", ""]
    for q, a in Q:
        L.append(f"- **{q}** {a}")
    L += ["", "## Node actions", ""]
    nodes = r["nodes"]
    if nodes is not None and len(nodes):
        for _, row in nodes.iterrows():
            L.append(f"- {row['operation']}: {row['node']} ({row['status']})")
    L += ["", "## Formal negatives / not carried", "",
          "- Metastability: dead (not revived).",
          "- Universal sequence grammar: demoted (not revived).",
          "- Single initiation primitive / single hidden coordinate: null.",
          "- 16 cells are not force-retained; the smallest surviving surface "
          "is selected.",
          "", "## Limits", "",
          "- Cell behavior is descriptive (<= L2); no strategy translation.",
          "- Sparse cells are not interpreted; relational/asset-health "
          "overlays are downstream.",
          "- DAR remains pilot.",
          "", "`human_review_required = TRUE`",
          "`next_checkpoint_authorized = FALSE`",
          "NO STRATEGY · NO PNL · NO EXECUTION · NO ENTRY/EXIT · NO SIZING · "
          "NO LEVERAGE · NO DEPLOYMENT"]
    (OUT / "34_MECH15_DECISION.md").write_text("\n".join(L) + "\n",
                                              encoding="utf-8")
    return "\n".join(L)


def write_verdicts(results):
    r = results
    v = {
        "checkpoint": "MECH-15",
        "commit": "TBD",
        "verdict": r["final_verdict"],
        "recommended_cells": r["recommended_cells"],
        "support": f"{int((r['support']['grade']=='ROBUST').sum())} ROBUST / "
                   f"{int((r['support']['grade']=='LOCAL').sum())} LOCAL / "
                   f"{int((r['support']['grade']=='SPARSE').sum())} SPARSE / "
                   f"{int((r['support']['grade']=='UNUSABLE').sum())} UNUSABLE",
        "differentiation": f"{int((r['differentiation']['verdict']=='DISTINCT').sum())} DISTINCT pairs",
        "null_test": r["null_verdict"],
        "heldout": r["heldout_verdict"],
        "age_overlay": r["age_verdict"],
        "equifinality_inside": r["equifinality_inside_verdict"],
        "market_os_candidate": r["marketos_status"],
        "human_review_required": True,
        "next_checkpoint_authorized": False,
    }
    (OUT / "_verdicts.json").write_text(json.dumps(v, indent=2),
                                        encoding="utf-8")
    return v


def _recommended_surface(retention):
    """Smallest cut in {16,12,8,6,4} whose mean retention >= 0.85."""
    means = {}
    for _, row in retention.iterrows():
        cols = [c for c in ["propagation", "reentry", "directional_entropy",
                            "rank_recruitment", "tail_activation",
                            "next_state_distribution"]]
        vals = [row[c] for c in cols if row[c] == row[c]]
        means[int(row["n_cells"])] = float(np.mean(vals)) if vals else np.nan
    for cut in [4, 6, 8, 12, 16]:
        if means.get(cut) is not None and means[cut] >= 0.85:
            return cut, means
    # fall back to the best cut below 16
    best = 16
    for cut in [4, 6, 8, 12]:
        if means.get(cut) is not None and means[cut] is not np.nan:
            if means[cut] >= means.get(best, 0) - 0.02:
                best = cut
    return best, means


def main():
    dfw = _cache_step("dfw15", load_dfw)
    ev = _cache_step("ev15", load_ev)
    band = _cache_step("band15", load_band_panel)
    frame = _cache_step("frame15", lambda: build_matrix_frame(dfw, band))

    raw = _cache_step("ws1", lambda: ws1_raw_matrix(frame))
    support = _cache_step("ws2", lambda: ws2_support_audit(frame))
    diff = _cache_step("ws3", lambda: ws3_cell_differentiation(frame))
    sim, names = _cache_step("ws4", lambda: ws4_similarity_matrix(
        frame, raw))
    merge, _D = _cache_step("ws5", lambda: ws5_merge_tree(frame, MC))
    ret = _cache_step("ws6", lambda: ws6_information_retention(frame, MC))
    age_ov = _cache_step("ws7", lambda: ws7_state_age_overlay(frame))
    age_cons = _cache_step("ws8", lambda: ws8_age_effect_consistency(frame))
    closure = _cache_step("ws9", lambda: ws9_branch_closure_surface(frame))
    forcing = _cache_step("ws10", lambda: ws10_forcing_position(frame, band))
    depth = _cache_step("ws11", lambda: ws11_activation_depth_profile(
        frame, band))
    wf = _cache_step("ws12", lambda: ws12_waterfall_cell_placement(frame,
                                                                   band))
    archmix = _cache_step("ws13", lambda: ws13_initiation_archetype_mix(
        frame))
    equi_in = _cache_step("ws14", lambda: ws14_equifinality_inside_matrix(
        frame))
    dents = _cache_step("ws15", lambda: ws15_directional_entropy_surface(
        frame))
    asym = _cache_step("ws16", lambda: ws16_directional_asymmetry_surface(
        frame))
    upside = _cache_step("ws17", lambda: ws17_upside_permission_cells(frame))
    downside = _cache_step("ws18", lambda: ws18_downside_localization_cells(
        frame, ev))
    tail = _cache_step("ws19", lambda: ws19_tail_activation_surface(frame,
                                                                    band))
    rank = _cache_step("ws20", lambda: ws20_rank_recruitment_surface(frame,
                                                                     band))
    resid = _cache_step("ws21", lambda: ws21_residual_disturbance_overlay(
        frame, ev))
    trans, trans_summ = _cache_step("ws22", lambda: ws22_transition_matrix(
        frame))
    highway = _cache_step("ws23", lambda: ws23_temporal_highway_map(trans))
    ese = _cache_step("ws24", lambda: ws24_cell_entry_survival_exit(frame))
    nullt = _cache_step("ws25", lambda: ws25_matrix_null_test(frame))
    held = _cache_step("ws26", lambda: ws26_heldout_stability(frame))

    # ---- decision logic ----
    rec_cut, ret_means = _recommended_surface(ret)
    null_verdict = str(nullt["matrix_verdict"].iloc[0]) if len(nullt) else \
        "n/a"
    heldout_verdict = str(held["verdict"].iloc[0]) if len(held) else "n/a"
    age_verdict = str(age_ov["verdict"].iloc[0]) if len(age_ov) else "n/a"
    equi_in_verdict = str(equi_in["verdict"].iloc[0]) if len(equi_in) else \
        "n/a"
    forcing_verdict = str(forcing["verdict"].iloc[0]) if len(forcing) else \
        "n/a"
    # archetype adds info?
    auc_c, auc_ca = _archetype_adds_info(frame)
    if auc_c == auc_c and auc_ca == auc_ca:
        arch_verdict = ("ARCHETYPE_ADDS_LOCAL_INFO"
                        if auc_ca - auc_c >= 0.01 else
                        "ARCHETYPE_REDUNDANT_WITH_CELL")
    else:
        arch_verdict = "DATA_LIMITED"
    # final verdict
    n_robust = int((support["grade"] == "ROBUST").sum())
    n_unusable = int((support["grade"] == "UNUSABLE").sum())
    if null_verdict.startswith("MATRIX_DECORATIVE"):
        final = "FAIL_MECH15_MATRIX_REDUNDANT"
    elif not heldout_verdict.startswith(("STABLE", "PARTIAL")):
        final = "FAIL_MECH15_MATRIX_UNSTABLE"
    elif n_robust < 4:
        final = "PASS_MECH15_LOCAL_MATRIX"
    elif rec_cut < 16:
        final = "PASS_MECH15_REDUCED_MATRIX"
    else:
        final = "PASS_MECH15_16_CELL_MATRIX"
    marketos_status = ("CANDIDATE_v0.1" if null_verdict.startswith(
        "MATRIX_SURVIVES") and heldout_verdict.startswith("STABLE") else
        "CONDITIONAL" if null_verdict.startswith("MATRIX_SURVIVES") or
        heldout_verdict.startswith("STABLE") else "NOT_APPROVED")

    results = {
        "frame": frame, "raw": raw, "support": support,
        "differentiation": diff, "similarity": sim, "merge_tree": merge,
        "retention": ret, "age_overlay": age_ov, "age_consistency": age_cons,
        "branch_closure": closure, "forcing": forcing, "depth_profile": depth,
        "waterfall": wf, "archetype_mix": archmix,
        "equifinality_inside": equi_in, "dir_entropy": dents,
        "asymmetry": asym, "upside": upside, "downside": downside,
        "tail": tail, "rank": rank, "residual": resid,
        "transitions": trans_summ, "highway": highway, "ese": ese,
        "null_test": nullt, "heldout": held,
        "recommended_cells": rec_cut, "retention_by_cut": ret_means,
        "null_verdict": null_verdict, "heldout_verdict": heldout_verdict,
        "age_verdict": age_verdict, "equifinality_inside_verdict":
        equi_in_verdict, "forcing_verdict": forcing_verdict,
        "arch_verdict": arch_verdict,
        "auc_arch_cell": auc_c, "auc_arch_cell_plus_arch": auc_ca,
        "final_verdict": final, "marketos_status": marketos_status,
    }
    spec = ws27_market_os_spec(results)
    results["marketos_status"] = marketos_status
    ws28_cell_labeling_guide(results)
    nodes = ws29_promote_merge_dissolve(results)
    results["nodes"] = nodes
    ws29_nulls(results)
    ws29_field_map(results)
    ws29_summary(results)
    ws29_decision(results)
    write_verdicts(results)
    print(f"[done15] MECH-15 pipeline complete. verdict={final} "
          f"surface={rec_cut}", flush=True)
    return results


if __name__ == "__main__":
    main()
