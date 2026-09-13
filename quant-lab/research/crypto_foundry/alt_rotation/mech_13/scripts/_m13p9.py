from _m13base import *
from _m13base import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _entropy, _subperiod_split
from _m13p2 import *
from _m13p3 import *
from _m13p4 import *
from _m13p5 import *
from _m13p6 import *
from _m13p7 import *
from _m13p8 import *


def ws20_nodes(results):
    rows = [
        {"node": "LIFECYCLE_DEEP_MAP", "operation": "EVALUATE",
         "evidence": "WS1 state-specific lifecycle profiles", "status":
         "PENDING"},
        {"node": "STATE_MASS_MIGRATION", "operation": "EVALUATE",
         "evidence": "WS2 per cell x age law", "status": "PENDING"},
        {"node": "INITIATION_GEOMETRY", "operation": "EVALUATE",
         "evidence": "WS3 birth coordinates", "status": "PENDING"},
        {"node": "INITIATION_PRIMITIVE_AUDIT", "operation": "EVALUATE",
         "evidence": "WS4 necessity/sufficiency", "status": "PENDING"},
        {"node": "ENTROPY_DEEP_MAP", "operation": "EVALUATE",
         "evidence": "WS5", "status": "PENDING"},
        {"node": "ENTROPY_PRIMITIVE_AUDIT", "operation": "EVALUATE",
         "evidence": "WS6 entropy-collapse driver", "status": "PENDING"},
        {"node": "ENTROPY_PROPAGATION", "operation": "EVALUATE",
         "evidence": "WS7 patch entropy propagation", "status": "PENDING"},
        {"node": "SPATIAL_TEMPORAL_CONSTRAINT_MATRIX", "operation":
         "EVALUATE", "evidence": "WS8 2x2", "status": "PENDING"},
        {"node": "WATERFALL_SUBTYPE_MATRIX", "operation": "EVALUATE",
         "evidence": "WS9 subtypes", "status": "PENDING"},
        {"node": "ACTIVATION_THRESHOLD_SURFACES", "operation": "EVALUATE",
         "evidence": "WS10", "status": "PENDING"},
        {"node": "PATCH_RESPONSE_CURVES", "operation": "EVALUATE",
         "evidence": "WS11", "status": "PENDING"},
        {"node": "RESPONSE_CURVE_HETEROGENEITY", "operation": "EVALUATE",
         "evidence": "WS12", "status": "PENDING"},
        {"node": "METASTABILITY_RECHECK", "operation": "EVALUATE",
         "evidence": "WS13 confirm-or-kill", "status": "PENDING"},
        {"node": "ABSOLUTE_SIGMA_SHOCK", "operation": "EVALUATE",
         "evidence": "WS14", "status": "PENDING"},
        {"node": "SHOCK_MATERIALITY", "operation": "EVALUATE",
         "evidence": "WS15", "status": "PENDING"},
        {"node": "DIRECTIONAL_ASYMMETRY_ATLAS", "operation": "EVALUATE",
         "evidence": "WS16 full map", "status": "PENDING"},
        {"node": "UPSIDE_GEOMETRY", "operation": "EVALUATE",
         "evidence": "WS17 up", "status": "PENDING"},
        {"node": "DOWNSIDE_GEOMETRY", "operation": "EVALUATE",
         "evidence": "WS17 down", "status": "PENDING"},
        {"node": "DIRECTIONAL_INFORMATION_GAIN", "operation": "EVALUATE",
         "evidence": "WS18", "status": "PENDING"},
        {"node": "LOCAL_CONVERSION_PATHS", "operation": "EVALUATE",
         "evidence": "WS19", "status": "PENDING"},
    ]
    out = pd.DataFrame(rows)

    def _set(node, op, status):
        m = out["node"] == node
        if m.any():
            out.loc[m, "operation"] = op
            out.loc[m, "status"] = status

    if results.get("lifecycle") is not None and len(results["lifecycle"]):
        _set("LIFECYCLE_DEEP_MAP", "PROMOTE",
             f"{len(results['lifecycle'])} cell x stage rows")
    if results.get("mass_law") is not None and len(results["mass_law"]):
        _set("STATE_MASS_MIGRATION", "PROMOTE",
             f"{len(results['mass_law'])} cell laws")
    if results.get("initiation") is not None and len(results["initiation"]):
        n_sig = int((results["initiation"]["q"] <= FDR_Q).sum()) \
            if "q" in results["initiation"].columns else 0
        _set("INITIATION_GEOMETRY",
             "PROMOTE" if n_sig >= 3 else
             "LOCAL_NODE" if n_sig >= 1 else "DESCRIPTIVE",
             f"{n_sig} significant birth coordinates")
    if results.get("init_audit") is not None and \
            len(results["init_audit"]):
        n_nec = (results["init_audit"]["necessity"] ==
                 "NECESSARY_LOCAL").sum()
        n_suff = (results["init_audit"]["necessity"] ==
                  "SUFFICIENT_LOCAL").sum()
        n_cond = (results["init_audit"]["necessity"] ==
                  "CONDITIONAL").sum()
        _set("INITIATION_PRIMITIVE_AUDIT",
             "PROMOTE" if (n_nec + n_suff) >= 1 else
             "LOCAL_NODE" if n_cond >= 1 else "DESCRIPTIVE",
             f"{n_nec} NEC / {n_suff} SUFF / {n_cond} COND coords")
    if results.get("entropy_deep") is not None and \
            len(results["entropy_deep"]):
        _set("ENTROPY_DEEP_MAP", "PROMOTE",
             f"{len(results['entropy_deep'])} entropy groups")
    if results.get("entropy_primitive") is not None and \
            len(results["entropy_primitive"]):
        v = results["entropy_primitive"]["verdict"].iloc[0] \
            if "verdict" in results["entropy_primitive"].columns else "n/a"
        _set("ENTROPY_PRIMITIVE_AUDIT",
             "PROMOTE" if v.startswith("GLOBAL") else
             "LOCAL_NODE" if v.startswith("LOCAL") else "DESCRIPTIVE", v)
    if results.get("entropy_prop") is not None and len(results[
            "entropy_prop"]):
        v = results["entropy_prop"]["verdict"].iloc[0]
        _set("ENTROPY_PROPAGATION",
             "PROMOTE" if v in ("PATCH_PROPAGATION",
                                "SYNCHRONIZED_NO_LAG_PROPAGATION") else
             "DESCRIPTIVE", v)
    if results.get("spat_temp") is not None and len(results["spat_temp"]):
        v = results["spat_temp"]["verdict"].iloc[0]
        _set("SPATIAL_TEMPORAL_CONSTRAINT_MATRIX",
             "PROMOTE" if v.startswith("INDEPENDENT") else "DESCRIPTIVE", v)
    if results.get("waterfall_subtypes") is not None and \
            len(results["waterfall_subtypes"]):
        n_named = (results["waterfall_subtypes"]["verdict"] ==
                   "NAMED_SUBTYPE").sum()
        _set("WATERFALL_SUBTYPE_MATRIX",
             "PROMOTE" if n_named >= 1 else "DESCRIPTIVE",
             f"{n_named} named subtypes")
    if results.get("activation_surfaces") is not None and \
            len(results["activation_surfaces"]):
        n_mono = (results["activation_surfaces"]["surface_type"] ==
                  "MONOTONIC_THRESHOLD_SURFACE").sum()
        _set("ACTIVATION_THRESHOLD_SURFACES",
             "PROMOTE" if n_mono >= 3 else "DESCRIPTIVE",
             f"{n_mono} monotonic patch surfaces")
    if results.get("patch_resp") is not None and len(results["patch_resp"]):
        _set("PATCH_RESPONSE_CURVES", "PROMOTE",
             f"{len(results['patch_resp'])} patch x pert x amp rows")
    if results.get("resp_het") is not None and len(results["resp_het"]):
        v = results["resp_het"]["verdict"].iloc[0]
        _set("RESPONSE_CURVE_HETEROGENEITY",
             "PROMOTE" if v == "HETEROGENEOUS_TRANSFER_FUNCTIONS" else
             "DESCRIPTIVE", v)
    if results.get("meta_recheck") is not None and len(results["meta_recheck"]):
        n_meta = (results["meta_recheck"]["verdict"].isin(
            ["METASTABLE_CONFIRMED", "METASTABLE_LOCAL"])).sum()
        _set("METASTABILITY_RECHECK",
             "PROMOTE" if n_meta >= 1 else "DISSOLVE",
             f"{n_meta} metastable cells (shake-out)")
    if results.get("abs_sigma") is not None and len(results["abs_sigma"]):
        _set("ABSOLUTE_SIGMA_SHOCK", "PROMOTE",
             f"{len(results['abs_sigma'])} shock cells")
    if results.get("materiality") is not None and \
            len(results["materiality"]):
        v = results["materiality"]["verdict"].iloc[0]
        _set("SHOCK_MATERIALITY",
             "PROMOTE" if v == "MATERIALITY_PRIMITIVE" else
             "LOCAL_NODE" if v == "LOCAL_MATERIALITY_RULE" else "DESCRIPTIVE",
             v)
    if results.get("directional") is not None and \
            len(results["directional"]):
        v = results["directional"]["verdict"].iloc[0]
        _set("DIRECTIONAL_ASYMMETRY_ATLAS",
             "PROMOTE" if v.startswith("ASYMMETRIC") else "DESCRIPTIVE", v)
    if results.get("upside") is not None and len(results["upside"]):
        v = results["upside"]["verdict"].iloc[0]
        _set("UPSIDE_GEOMETRY",
             "PROMOTE" if v == "FIELD_SELECTIVE_UPSIDE" else "DESCRIPTIVE", v)
    if results.get("downside") is not None and len(results["downside"]):
        v = results["downside"]["verdict"].iloc[0]
        _set("DOWNSIDE_GEOMETRY", "DESCRIPTIVE", v)
    if results.get("dir_gain") is not None and len(results["dir_gain"]):
        v = results["dir_gain"]["verdict"].iloc[0]
        _set("DIRECTIONAL_INFORMATION_GAIN",
             "PROMOTE" if v.startswith("DIRECTION_CONSTRAINED") else
             "DESCRIPTIVE", v)
    if results.get("conv_paths") is not None and \
            len(results["conv_paths"]):
        v = results["conv_paths"]["verdict"].iloc[0]
        _set("LOCAL_CONVERSION_PATHS",
             "PROMOTE" if v == "LOCAL_CONVERSION_PATHS" else
             "LOCAL_NODE" if "SINGLE" in v else "DESCRIPTIVE", v)
    out.to_csv(OUT / "22_PROMOTE_MERGE_DISSOLVE.csv", index=False)
    return out


def ws20_nulls(results):
    rows = [
        {"result": "Broad EARLY_DECAY_SEQUENCE (global)", "status": "NULL",
         "note": "MECH-9; local termination only"},
        {"result": "Semi-Markov transition improvement", "status": "NULL",
         "note": "MECH-11 MARKOV_SUFFICIENT"},
        {"result": "HH birth quality OOS", "status": "PARKED",
         "note": "MECH-9/10"},
        {"result": "Transition velocity main driver", "status": "PARKED",
         "note": "MECH-10"},
        {"result": "Volatility route selector", "status": "NULL",
         "note": "intensity/retention only"},
        {"result": "SHMC high-tail activation", "status": "DEAD",
         "note": "reversion-like local role only"},
        {"result": "Chain/DEX activity as driver", "status": "NULL",
         "note": "sensor only"},
        {"result": "Breadth composition incremental beyond level",
         "status": "NULL", "note": "MECH-11/12 merged into level"},
        {"result": "MECH-11 universal sequence grammar", "status": "DEMOTED",
         "note": "MECH-12: conditional delivery ordering only"},
        {"result": "MECH-12 metastability interpretation", "status":
         "RECHECKED", "note": "WS13 confirm-or-kill; carry verdict"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "23_NULL_AND_FAILED_RESULTS.csv", index=False)
    return out


def ws20_field_map(results):
    rows = [
        {"node": "4-STATE BREADTH x DISPERSION", "type": "GLOBAL_STATE",
         "status": "EARNED", "note": "HH/HL/LH/LL with age + clocks"},
        {"node": "STATE_AGE / SURVIVAL QUALITY", "type": "COORDINATE",
         "status": "EARNED", "note": "birth+selection + mass migration"},
        {"node": "INITIATION GEOMETRY", "type": "LOCAL",
         "status": "EVALUATED", "note": "birth coords -> initiation (WS3/4)"},
        {"node": "CONSTRAINT-ENTROPY", "type": "COORDINATE",
         "status": "EARNED", "note": "age + spatial/temporal axes (WS5/6/8)"},
        {"node": "WATERFALL SUBTYPES", "type": "SEQUENCE",
         "status": "EVALUATED", "note": "threshold/subtype matrix (WS9/10)"},
        {"node": "PATCH RESPONSE", "type": "LOCAL",
         "status": "EARNED", "note": "response curves + heterogeneity (11/12)"},
        {"node": "METASTABILITY", "type": "LOCAL",
         "status": "RECHECKED", "note": "confirm-or-kill (WS13)"},
        {"node": "SHOCK MATERIALITY", "type": "DISTURBANCE",
         "status": "EVALUATED", "note": "abs x sigma geometry (14/15)"},
        {"node": "DIRECTIONAL ASYMMETRY", "type": "ASYMMETRY",
         "status": "EARNED", "note": "upside field-selective (16/17)"},
        {"node": "PRICE_RECOVERY_RANK_DECAY", "type": "HEALTH",
         "status": "EARNED", "note": "beta-rescue (MECH-10/11)"},
        {"node": "EARLY_SNAPBACK / BREADTH_FADE", "type": "MOTIF",
         "status": "EARNED", "note": "failure geometries (MECH-5/6)"},
        {"node": "TRUE vs FALSE LONER", "type": "PEER",
         "status": "EARNED", "note": "LF5/6 distinct geometry"},
        {"node": "SHMC / SHHM", "type": "MICROSTATE",
         "status": "LOCAL_NODE", "note": "opposite 2x2 corners"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "24_CANONICAL_FIELD_MAP_UPDATE.csv", index=False)
    return out


def write_verdicts(results):
    fptr = "n/a"
    if results.get("patch_resp") is not None and \
            len(results["patch_resp"]):
        fptr = f"{len(results['patch_resp'])} response cells"
    asg = "n/a"
    if results.get("abs_sigma") is not None and \
            len(results["abs_sigma"]) and "delta_auc_abs_adds" in \
            results["abs_sigma"].columns:
        asg = _fmt(results["abs_sigma"]["delta_auc_abs_adds"].iloc[0])
    v = {
        "checkpoint": "MECH-13",
        "commit": "TBD",
        "verdict": "PASS_MECH13_LIFECYCLE_DEEPENING_WITH_LIMITATIONS",
        "initiation_geometry": (
            f"{int((results['initiation']['q'] <= FDR_Q).sum())} sig coords"
            if results.get("initiation") is not None
            and "q" in results["initiation"].columns else "n/a"),
        "entropy": (
            results["entropy_deep"]["verdict"].iloc[0]
            if results.get("entropy_deep") is not None
            and len(results["entropy_deep"]) else "n/a"),
        "constraint_axes": (
            results["spat_temp"]["verdict"].iloc[0]
            if results.get("spat_temp") is not None
            and len(results["spat_temp"]) else "n/a"),
        "waterfall_subtypes": (
            f"{int((results['waterfall_subtypes']['verdict'] == 'NAMED_SUBTYPE').sum())} named"
            if results.get("waterfall_subtypes") is not None
            and len(results["waterfall_subtypes"]) else "n/a"),
        "metastability": (
            "; ".join(f"{r['cell']}:{r['verdict']}"
                      for _, r in results["meta_recheck"].iterrows())
            if results.get("meta_recheck") is not None
            and len(results["meta_recheck"]) else "n/a"),
        "abs_sigma_delta_auc": asg,
        "directional_asymmetry": (
            results["directional"]["verdict"].iloc[0]
            if results.get("directional") is not None
            and len(results["directional"]) else "n/a"),
        "patch_response": fptr,
        "dir_info_gain": (
            results["dir_gain"]["verdict"].iloc[0]
            if results.get("dir_gain") is not None
            and len(results["dir_gain"]) else "n/a"),
        "human_review_required": True,
        "next_checkpoint_authorized": False,
    }
    (OUT / "_verdicts.json").write_text(json.dumps(v, indent=2),
                                        encoding="utf-8")
    return v


def write_summary(results):
    r = results
    L = ["# CRYPTO-ALT-MECH-13 — SUMMARY", "",
         "**Lifecycle Deepening, Initiation Geometry, Constraint-Entropy "
         "Propagation, Waterfall Subtype Matrix, Patch Response Curves, "
         "Metastability Recheck, Absolute x Sigma Shock Geometry, Full "
         "Directional Asymmetry Map**", "",
         "AGENT 1 — CANONICAL FIELD CARTOGRAPHER · terrain research only", ""]
    ig = r.get("initiation")
    if ig is not None and len(ig):
        sig = ig[ig["q"] <= FDR_Q] if "q" in ig.columns else ig.head(0)
        L.append(f"- **Initiation geometry (04)**: {len(sig)} significant "
                 f"birth coordinates; top: " +
                 ("; ".join(f"{row['cell']}:{row['coord']}(d={row['cohens_d']:.2f})"
                 for _, row in sig.sort_values("cohens_d",
                   key=lambda s: s.abs(), ascending=False).head(4).iterrows())
                 if len(sig) else "none"))
    ia = r.get("init_audit")
    if ia is not None and len(ia):
        n_nec = (ia["necessity"] == "NECESSARY_LOCAL").sum()
        L.append(f"- **Initiation primitive audit (05)**: {n_nec} "
                 f"NECESSARY_LOCAL coordinates")
    ed = r.get("entropy_deep")
    if ed is not None and len(ed):
        L.append(f"- **Entropy deep map (06)**: {len(ed)} groups; "
                 f"{ed.groupby('group').size().to_dict()}")
    ep = r.get("entropy_primitive")
    if ep is not None and len(ep):
        v = ep["verdict"].iloc[0]
        L.append(f"- **Entropy primitive audit (07)**: {v}")
    epr = r.get("entropy_prop")
    if epr is not None and len(epr):
        L.append(f"- **Entropy propagation (08)**: {epr['verdict'].iloc[0]}")
    st = r.get("spat_temp")
    if st is not None and len(st):
        L.append(f"- **Spatial/temporal constraint matrix (09)**: "
                 f"{st['verdict'].iloc[0]} (axis rho={st['axis_spearman'].iloc[0]:.2f})")
    ws = r.get("waterfall_subtypes")
    if ws is not None and len(ws):
        n_named = (ws["verdict"] == "NAMED_SUBTYPE").sum()
        L.append(f"- **Waterfall subtype matrix (10)**: {n_named} named "
                 f"subtypes")
    asu = r.get("activation_surfaces")
    if asu is not None and len(asu):
        n_mono = (asu["surface_type"] ==
                  "MONOTONIC_THRESHOLD_SURFACE").sum()
        L.append(f"- **Activation threshold surfaces (11)**: {n_mono}/"
                 f"{len(asu)} monotonic patch surfaces")
    pr = r.get("patch_resp")
    if pr is not None and len(pr):
        n_sh = pr["response_shape"].value_counts().to_dict() if \
            "response_shape" in pr.columns else {}
        L.append(f"- **Patch response curves (12)**: {len(pr)} rows; "
                 f"shapes {n_sh}")
    rh = r.get("resp_het")
    if rh is not None and len(rh):
        L.append(f"- **Response-curve heterogeneity (13)**: "
                 f"{rh['verdict'].iloc[0]}")
    meta = r.get("meta_recheck")
    if meta is not None and len(meta):
        L.append("- **Metastability recheck (14)**: " + "; ".join(
            f"{row['cell']}:{row['verdict']}" for _, row in meta.iterrows()))
    asg = r.get("abs_sigma")
    if asg is not None and len(asg):
        dA = asg["delta_auc_abs_adds"].iloc[0] if \
            "delta_auc_abs_adds" in asg.columns else np.nan
        L.append(f"- **Absolute x sigma shock geometry (15)**: "
                 f"{len(asg)} cells; ΔAUC abs-adds={_fmt(dA)}")
    mat = r.get("materiality")
    if mat is not None and len(mat):
        L.append(f"- **Shock materiality audit (16)**: {mat['verdict'].iloc[0]}")
    dr = r.get("directional")
    if dr is not None and len(dr):
        L.append(f"- **Directional asymmetry atlas (17)**: "
                 f"{dr['verdict'].iloc[0]}")
    up = r.get("upside")
    if up is not None and len(up):
        L.append(f"- **Upside geometry (18)**: {up['verdict'].iloc[0]}")
    dn = r.get("downside")
    if dn is not None and len(dn):
        L.append(f"- **Downside geometry (19)**: {dn['verdict'].iloc[0]}")
    dg = r.get("dir_gain")
    if dg is not None and len(dg):
        L.append(f"- **Directional information gain (20)**: "
                 f"{dg['verdict'].iloc[0]}")
    cp = r.get("conv_paths")
    if cp is not None and len(cp):
        L.append(f"- **Local conversion paths (21)**: {cp['verdict'].iloc[0]} "
                 f"({int(cp['n_named_paths'].iloc[0])} named)")
    L += ["", "## Node actions", ""]
    nodes = r.get("nodes")
    if nodes is not None and len(nodes):
        for _, row in nodes.iterrows():
            L.append(f"- {row['operation']}: {row['node']} ({row['status']})")
    L += ["", "## Limits", "",
          "- Initiation/necessity findings are descriptive field anatomy "
          "(<= L2), not trade gates.",
          "- Entropy is a constraint description, neither prediction nor "
          "certainty.",
          "- Metastability recheck is empirical, not spectral.",
          "- Directional asymmetry is research terrain; no directional "
          "signal designed.",
          "- Waterfall subtypes require >=50 observations to name; below "
          "that DESCRIPTIVE.",
          "", "`human_review_required = TRUE`",
          "`next_checkpoint_authorized = FALSE`",
          "NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · "
          "NO DEPLOYMENT"]
    (OUT / "25_MECH13_SUMMARY.md").write_text("\n".join(L) + "\n",
                                             encoding="utf-8")
    return "\n".join(L)


def write_decision(results):
    r = results
    L = ["# CRYPTO-ALT-MECH-13 — DECISION", "", "## Verdict", "",
         "**PASS_MECH13_LIFECYCLE_DEEPENING_WITH_LIMITATIONS**", "",
         "MECH-13 deepens MECH-12's objects: state lifecycle stage profiles, "
         "per-cell mass-migration laws, failure-birth -> initiation geometry, "
         "a necessity/sufficiency audit of initiation coordinates, a deep "
         "constraint-entropy map with driver and propagation tests, an "
         "activation-capacity x resolution-entropy 2x2, waterfall subtype "
         "matrix and activation threshold surfaces, patch response curves "
         "with heterogeneity, a metastability confirm-or-kill recheck, full "
         "absolute x sigma shock geometry and materiality audit, and a "
         "full directional asymmetry atlas with upside/downside deepening.",
         "", "## Key results", ""]
    ig = r.get("initiation")
    if ig is not None and len(ig):
        sig = ig[ig["q"] <= FDR_Q] if "q" in ig.columns else ig.head(0)
        L.append(f"- **Initiation geometry**: {len(sig)} significant birth "
                 f"coordinates; failure mirrors are "
                 f"{ig['verdict'].iloc[0] if 'verdict' in ig.columns else 'n/a'}.")
    ia = r.get("init_audit")
    if ia is not None and len(ia):
        n_nec = (ia["necessity"] == "NECESSARY_LOCAL").sum()
        L.append(f"- **Initiation primitive audit**: {n_nec} NECESSARY_LOCAL; "
                 f"{int((ia['necessity'] == 'SUBSTITUTABLE').sum())} "
                 f"SUBSTITUTABLE.")
    st = r.get("spat_temp")
    if st is not None and len(st):
        L.append(f"- **Spatial/temporal constraint axes**: "
                 f"{st['verdict'].iloc[0]} "
                 f"(ax rho={st['axis_spearman'].iloc[0]:.2f}).")
    meta = r.get("meta_recheck")
    if meta is not None and len(meta):
        L.append("- **Metastability recheck**: " + "; ".join(
            f"{row['cell']}:{row['verdict']}" for _, row in meta.iterrows()))
    asg = r.get("abs_sigma")
    if asg is not None and len(asg):
        L.append(f"- **Absolute x sigma shocks**: {len(asg)} cells; "
                 f"abs adds ΔAUC "
                 f"{_fmt(asg['delta_auc_abs_adds'].iloc[0]) if 'delta_auc_abs_adds' in asg.columns else 'n/a'}.")
    dr = r.get("directional")
    if dr is not None and len(dr):
        L.append(f"- **Directional asymmetry atlas**: {dr['verdict'].iloc[0]}.")
    cp = r.get("conv_paths")
    if cp is not None and len(cp):
        L.append(f"- **Local conversion paths**: {cp['verdict'].iloc[0]} "
                 f"({int(cp['n_named_paths'].iloc[0])} named).")
    L += ["", "## Node actions", ""]
    nodes = r.get("nodes")
    if nodes is not None and len(nodes):
        for _, row in nodes.iterrows():
            L.append(f"- {row['operation']}: {row['node']} ({row['status']})")
    L += ["", "## Limits", "",
          "- All ordering/initiation/entropy results are descriptive (<= L2).",
          "- Metastability recheck is empirical, not spectral; volatility "
          "stays intensity/retention context.",
          "- No strategy translation; directional deepening is research only.",
          "", "`human_review_required = TRUE`",
          "`next_checkpoint_authorized = FALSE`",
          "NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · "
          "NO LEVERAGE · NO DEPLOYMENT"]
    (OUT / "26_MECH13_DECISION.md").write_text("\n".join(L) + "\n",
                                              encoding="utf-8")
    return "\n".join(L)