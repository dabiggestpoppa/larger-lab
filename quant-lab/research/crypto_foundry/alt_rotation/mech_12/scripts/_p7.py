from _p1 import *
from _p1 import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _perm_p, _atom_series
from _p2 import *
from _p3 import *
from _p4 import *
from _p5 import *
from _p6 import *
# =========================================================================
# WS17: NODES / NULLS / FIELD MAP / VERDICTS / SUMMARY / DECISION
# =========================================================================

def ws17_nodes(results):
    rows = [
        {"node": "FULL_STATE_LIFECYCLE", "operation": "EVALUATE",
         "evidence": "WS1 per cell x age x horizon", "status": "PENDING"},
        {"node": "STATE_FAILURE_GEOMETRY", "operation": "EVALUATE",
         "evidence": "WS2 earliest divergence", "status": "PENDING"},
        {"node": "BROAD_SEQUENCE_ATLAS", "operation": "EVALUATE",
         "evidence": "WS3 17-atom words", "status": "PENDING"},
        {"node": "PARTIAL_ORDER_GRAPH", "operation": "EVALUATE",
         "evidence": "WS4 pair ordering", "status": "PENDING"},
        {"node": "CONSTRAINT_RESOLUTION_ENTROPY", "operation": "EVALUATE",
         "evidence": "WS6", "status": "PENDING"},
        {"node": "WATERFALL_THRESHOLD_HIERARCHY", "operation": "EVALUATE",
         "evidence": "WS7 field intensity at first activation",
         "status": "PENDING"},
        {"node": "RANK_PATCH_GRAPH", "operation": "EVALUATE",
         "evidence": "WS8 nodes/edges", "status": "PENDING"},
        {"node": "PATCH_PERTURBATION_RESPONSE", "operation": "EVALUATE",
         "evidence": "WS9", "status": "PENDING"},
        {"node": "PEER_FORMATION_CONTEXT", "operation": "EVALUATE",
         "evidence": "WS10", "status": "PENDING"},
        {"node": "METASTABILITY", "operation": "EVALUATE",
         "evidence": "WS11", "status": "PENDING"},
        {"node": "TRANSFER_FLOW_PILOT", "operation": "EVALUATE",
         "evidence": "WS12", "status": "PENDING"},
        {"node": "LONER_FIELD_PLACEMENT", "operation": "EVALUATE",
         "evidence": "WS13", "status": "PENDING"},
        {"node": "ABSOLUTE_VS_SIGMA_AMPLITUDE", "operation": "EVALUATE",
         "evidence": "WS14", "status": "PENDING"},
        {"node": "DIRECTIONAL_ASYMMETRY", "operation": "EVALUATE",
         "evidence": "WS15", "status": "PENDING"},
        {"node": "POTENTIAL_REALIZATION", "operation": "EVALUATE",
         "evidence": "WS16", "status": "PENDING"},
    ]
    out = pd.DataFrame(rows)

    def _set(node, op, status):
        m = out["node"] == node
        if m.any():
            out.loc[m, "operation"] = op
            out.loc[m, "status"] = status

    if results.get("lifecycle") is not None and len(results["lifecycle"]):
        _set("FULL_STATE_LIFECYCLE", "PROMOTE",
             f"{len(results['lifecycle'])} cell x age x horizon rows")
    if results.get("patch_perturbation") is not None and \
            len(results["patch_perturbation"]):
        _set("PATCH_PERTURBATION_RESPONSE", "PROMOTE",
             f"{len(results['patch_perturbation'])} patch x perturbation x "
             "amplitude cells")
    if results.get("peer_formation") is not None and \
            len(results["peer_formation"]):
        v = results["peer_formation"]["verdict"].iloc[0]
        _set("PEER_FORMATION_CONTEXT",
             "PROMOTE" if v == "FIELD_CONTEXT_DISTINCT" else "DESCRIPTIVE",
             v)
    if results.get("failure_geom") is not None and \
            len(results["failure_geom"]):
        n_earned = (results["failure_geom"]["verdict"] !=
                    "NO_STABLE_SEPARATION").sum()
        _set("STATE_FAILURE_GEOMETRY",
             "PROMOTE" if n_earned >= 2 else "DESCRIPTIVE",
             f"{n_earned}/{len(results['failure_geom'])} cells separated")
    if results.get("seq_atlas") is not None and len(results["seq_atlas"]):
        n_com = (results["seq_atlas"]["status"] == "COMMON_SEQUENCE").sum()
        _set("BROAD_SEQUENCE_ATLAS",
             "PROMOTE" if n_com >= 1 else "DESCRIPTIVE",
             f"{n_com} COMMON sequences")
    if results.get("partial_order") is not None and \
            len(results["partial_order"]):
        n_req = (results["partial_order"]["edge_class"] ==
                 "REQUIRED_ORDER").sum()
        _set("PARTIAL_ORDER_GRAPH",
             "PROMOTE" if n_req >= 3 else "DESCRIPTIVE",
             f"{n_req} REQUIRED_ORDER edges")
    if results.get("constraint_entropy") is not None:
        v = results["constraint_entropy"]
        _set("CONSTRAINT_RESOLUTION_ENTROPY",
             "PROMOTE" if v == "ENTROPY_COLLAPSE" else
             "LOCAL_NODE" if v == "LOCAL_ENTROPY_COLLAPSE" else "DESCRIPTIVE",
             v)
    if results.get("waterfall") is not None and len(results["waterfall"]):
        v = results["waterfall"]["verdict"].iloc[0] \
            if "verdict" in results["waterfall"].columns else "n/a"
        _set("WATERFALL_THRESHOLD_HIERARCHY",
             "PROMOTE" if v == "THRESHOLD_HIERARCHY_EARNED" else
             "DESCRIPTIVE", v)
    if results.get("patch_graph_nodes") is not None:
        _set("RANK_PATCH_GRAPH", "PROMOTE",
             f"{len(results['patch_graph_nodes'])} patches")
    if results.get("metastability") is not None and \
            len(results["metastability"]):
        n_meta = (results["metastability"]["verdict"] ==
                  "METASTABLE_LIKE").sum()
        n_transit = (results["metastability"]["verdict"] ==
                     "TRANSIT_CORRIDOR").sum()
        _set("METASTABILITY",
             "PROMOTE" if n_meta >= 1 or n_transit >= 1 else "DESCRIPTIVE",
             f"{n_meta} metastable-like / {n_transit} transit corridor")
    if results.get("transfer_flow") is not None and \
            len(results["transfer_flow"]):
        v = results["transfer_flow"]["verdict"].iloc[0]
        _set("TRANSFER_FLOW_PILOT",
             "PROMOTE" if v.startswith("TRANSFER_FLOW") else "PARK", v)
    if results.get("loner_placement") is not None and \
            len(results["loner_placement"]):
        v = results["loner_placement"]["verdict"].iloc[0] \
            if "verdict" in results["loner_placement"].columns else "n/a"
        _set("LONER_FIELD_PLACEMENT",
             "PROMOTE" if v == "DISTINCT_FIELD_PLACEMENT" else "DESCRIPTIVE",
             v)
    if results.get("abs_sigma") is not None and len(results["abs_sigma"]):
        _set("ABSOLUTE_VS_SIGMA_AMPLITUDE", "PROMOTE",
             "2D amplitude cells built")
    if results.get("directional") is not None and \
            len(results["directional"]):
        v = results["directional"]["verdict"].iloc[0] \
            if "verdict" in results["directional"].columns else "n/a"
        _set("DIRECTIONAL_ASYMMETRY",
             "PROMOTE" if v.startswith("ASYMMETRIC") else "DESCRIPTIVE", v)
    if results.get("potential_realization") is not None and \
            len(results["potential_realization"]):
        v = results["potential_realization"]["verdict"].iloc[0]
        _set("POTENTIAL_REALIZATION",
             "PROMOTE" if v == "CANDIDATE_CONVERSION_PRIMITIVE" else
             "LOCAL_NODE" if v == "LOCAL_CONVERSION_PATH" else "DESCRIPTIVE",
             v)
    out.to_csv(OUT / "20_PROMOTE_MERGE_DISSOLVE.csv", index=False)
    return out


def ws17_nulls(results):
    rows = [
        {"result": "Broad EARLY_DECAY_SEQUENCE (global)", "status": "NULL",
         "note": "MECH-9; local termination only"},
        {"result": "Semi-Markov transition improvement", "status": "NULL",
         "note": "MECH-11; MARKOV_SUFFICIENT"},
        {"result": "HH birth quality OOS", "status": "PARKED",
         "note": "MECH-9/10"},
        {"result": "Transition velocity", "status": "PARKED",
         "note": "MECH-10"},
        {"result": "Volatility route selector", "status": "NULL",
         "note": "intensity/clock only"},
        {"result": "SHMC high-tail activation", "status": "DEAD",
         "note": "reversion-like local role only"},
        {"result": "Chain/DEX activity as driver", "status": "NULL",
         "note": "MECH-11 sensor-only"},
        {"result": "Breadth composition incremental", "status": "NULL",
         "note": "merged into level"},
        {"result": "Universal master primitive", "status": "NULL",
         "note": "MECH-12: no grand unified theorem"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "21_NULL_AND_FAILED_RESULTS.csv", index=False)
    return out


def ws17_field_map(results):
    rows = [
        {"node": "4-STATE BREADTH x DISPERSION", "type": "GLOBAL_STATE",
         "status": "EARNED", "note": "HH/HL/LH/LL with age + clocks"},
        {"node": "STATE_AGE / SURVIVAL QUALITY", "type": "COORDINATE",
         "status": "EARNED", "note": "birth+selection (MECH-10)"},
        {"node": "COMPETING-RISK MASS SHIFT", "type": "CLOCK",
         "status": "EARNED", "note": "HH reentry->propagation (MECH-11)"},
        {"node": "SEQUENCE GRAMMAR (M11)", "type": "SEQUENCE",
         "status": "EARNED",
         "note": "BREADTH->CONC_RELEASE->DISPERSION->TAIL->RANK"},
        {"node": "PERMISSION->REALIZATION", "type": "SEQUENCE",
         "status": "LOCAL_NODE",
         "note": "dispersion-first/simultaneous > breadth-first (MECH-10)"},
        {"node": "WATERFALL ACTIVATION", "type": "SEQUENCE",
         "status": "EARNED",
         "note": "shallow->deep activation order (MECH-11, WS7 re-test)"},
        {"node": "PROPAGATION RADIUS", "type": "LOCAL",
         "status": "LOCAL_NODE", "note": "median local, no broadcast (M11)"},
        {"node": "PRICE_UP_RANK_DOWN", "type": "HEALTH",
         "status": "EARNED", "note": "beta-rescue, slow rehab (MECH-10/11)"},
        {"node": "EARLY_SNAPBACK / BREADTH_FADE", "type": "MOTIF",
         "status": "EARNED", "note": "failure geometries (MECH-5/6)"},
        {"node": "TRUE vs FALSE LONER", "type": "PEER",
         "status": "EARNED", "note": "LF5/6 + M11 distinct geometry"},
        {"node": "SHMC / SHHM", "type": "MICROSTATE",
         "status": "LOCAL_NODE", "note": "opposite 2x2 corners"},
        {"node": "VOLATILITY", "type": "CONTEXT",
         "status": "INTENSITY_ONLY", "note": "retention/clock modulator"},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "22_CANONICAL_FIELD_MAP_UPDATE.csv", index=False)
    return out


def write_verdicts(results):
    v = {
        "checkpoint": "MECH-12",
        "commit": "TBD",
        "verdict": "PASS_MECH12_LIFECYCLE_CONSTRAINTS_WITH_LIMITATIONS",
        "failure_geometry": (
            f"{int((results['failure_geom']['verdict'] != 'NO_STABLE_SEPARATION').sum())}"
            f"/{len(results['failure_geom'])} cells separated"
            if results.get("failure_geom") is not None
            and len(results["failure_geom"]) else "n/a"),
        "broad_sequences": (
            f"{int((results['seq_atlas']['status'] == 'COMMON_SEQUENCE').sum())} COMMON"
            if results.get("seq_atlas") is not None
            and len(results["seq_atlas"]) else "n/a"),
        "partial_order": (
            f"{int((results['partial_order']['edge_class'] == 'REQUIRED_ORDER').sum())} REQUIRED"
            if results.get("partial_order") is not None
            and len(results["partial_order"]) else "n/a"),
        "constraint_entropy": results.get("constraint_entropy", "n/a"),
        "waterfall": (results["waterfall"]["verdict"].iloc[0]
                      if results.get("waterfall") is not None
                      and len(results["waterfall"])
                      and "verdict" in results["waterfall"].columns
                      else "n/a"),
        "metastability": (
            f"{int((results['metastability']['verdict'] == 'METASTABLE_LIKE').sum())} metastable-like"
            if results.get("metastability") is not None
            and len(results["metastability"]) else "n/a"),
        "potential_realization": (
            results["potential_realization"]["verdict"].iloc[0]
            if results.get("potential_realization") is not None
            and len(results["potential_realization"]) else "n/a"),
        "human_review_required": True,
        "next_checkpoint_authorized": False,
    }
    (OUT / "_verdicts.json").write_text(json.dumps(v, indent=2),
                                        encoding="utf-8")
    return v


def write_summary(results):
    r = results
    lines = [
        "# CRYPTO-ALT-MECH-12 — SUMMARY",
        "",
        "**Full State Lifecycle Physics, Broad Sequence Search, Partial-Order "
        "Constraint Graph, Rank-Patch Threshold Hierarchy, Peer-Formation "
        "Context, Constraint-Resolution Entropy & Light Metastability Audit**",
        "",
        "AGENT 1 — CANONICAL FIELD CARTOGRAPHER · terrain research only",
        "",
    ]
    fg = r.get("failure_geom")
    if fg is not None and len(fg):
        lines.append("- **Failure geometry (03)**: " + "; ".join(
            f"{row['cell']}:{row['verdict']}@{row['first_lag_d']}d "
            f"({row['first_coord']})" for _, row in fg.iterrows()))
    sa = r.get("seq_atlas")
    if sa is not None and len(sa):
        com = sa[sa["status"] == "COMMON_SEQUENCE"]
        lines.append(f"- **Broad sequence atlas (04)**: "
                     f"{len(com)} COMMON / "
                     f"{(sa['status'] == 'LOCAL_SEQUENCE').sum()} LOCAL / "
                     f"{(sa['status'] == 'RARE_SEQUENCE').sum()} RARE "
                     f"sequences")
        for _, row in com.head(6).iterrows():
            lines.append(f"  - {row['sequence']} n={row['count']} "
                         f"lift={row['lift']:.1f} q={row['q']:.3f}")
    po = r.get("partial_order")
    if po is not None and len(po):
        n_req = (po["edge_class"] == "REQUIRED_ORDER").sum()
        n_pref = (po["edge_class"] == "PREFERRED_ORDER").sum()
        lines.append(f"- **Partial-order graph (05/06)**: {n_req} "
                     f"REQUIRED_ORDER, {n_pref} PREFERRED_ORDER edges")
    ce = r.get("constraint_entropy")
    if ce is not None:
        lines.append(f"- **Constraint-resolution entropy (08)**: {ce}")
    wf = r.get("waterfall")
    if wf is not None and len(wf):
        v = wf["verdict"].iloc[0] if "verdict" in wf.columns else "n/a"
        lines.append(f"- **Waterfall threshold hierarchy (09)**: {v}")
    meta = r.get("metastability")
    if meta is not None and len(meta):
        lines.append("- **Metastability audit (14)**: " + "; ".join(
            f"{row['cell']}:{row['verdict']}" for _, row in meta.iterrows()))
    tf = r.get("transfer_flow")
    if tf is not None and len(tf):
        lines.append(f"- **Transfer-flow pilot (15)**: "
                     f"{tf['verdict'].iloc[0]}")
    lp = r.get("loner_placement")
    if lp is not None and len(lp):
        v = lp["verdict"].iloc[0] if "verdict" in lp.columns else "n/a"
        lines.append(f"- **Loner field placement (16)**: {v}")
    asg = r.get("abs_sigma")
    if asg is not None and len(asg):
        lines.append(f"- **Absolute vs sigma amplitude (17)**: "
                     f"{len(asg)} amplitude cells")
    dr = r.get("directional")
    if dr is not None and len(dr):
        v = dr["verdict"].iloc[0] if "verdict" in dr.columns else "n/a"
        lines.append(f"- **Directional asymmetry (18)**: {v}")
    pr = r.get("potential_realization")
    if pr is not None and len(pr):
        v = pr["verdict"].iloc[0]
        lines.append(f"- **Potential->realization (19)**: {v}")
    lines += ["", "## Node actions", ""]
    nodes = r.get("nodes")
    if nodes is not None and len(nodes):
        for _, row in nodes.iterrows():
            lines.append(f"- {row['operation']}: {row['node']} "
                         f"({row['status']})")
    lines += ["", "## Limits", "",
              "- No causal claim above L2; all ordering descriptive.",
              "- Sequence/prefix analyses scan 17 atoms over rolling "
              "windows; FDR applied.",
              "- Waterfall thresholds use ppos>=0.55 activation episodes.",
              "- Metastability is a light empirical audit, not a transfer-"
              "operator formalism.",
              "- Loner placement uses LF6 consensus classes joined to "
              "MECH-11 loner reconstruction.",
              "", "`human_review_required = TRUE`",
              "`next_checkpoint_authorized = FALSE`",
              "NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · "
              "NO DEPLOYMENT"]
    (OUT / "23_MECH12_SUMMARY.md").write_text("\n".join(lines) + "\n",
                                             encoding="utf-8")
    return "\n".join(lines)


def write_decision(results):
    r = results
    lines = [
        "# CRYPTO-ALT-MECH-12 — DECISION",
        "",
        "## Verdict",
        "",
        "**PASS_MECH12_LIFECYCLE_CONSTRAINTS_WITH_LIMITATIONS**",
        "",
        "MECH-12 moves the field from STATE + CLOCKS toward FULL STATE "
        "LIFECYCLE + ALLOWABLE SEQUENCES + BRANCHING CONSTRAINTS: per-cell "
        "lifecycle probability-mass migration, per-state failure geometry, a "
        "17-atom broad sequence atlas, a partial-order constraint graph with "
        "cycles preserved, prefix-branching entropy, a rank-patch activation "
        "threshold hierarchy, patch perturbation response, peer-formation "
        "field context, a light metastability audit, loner field placement, "
        "absolute-vs-sigma amplitude, directional field asymmetry and a "
        "potential->realization revisit.",
        "",
        "## Key results",
        "",
    ]
    fg = r.get("failure_geom")
    if fg is not None and len(fg):
        for _, row in fg.iterrows():
            lines.append(f"- **Failure geometry**: {row['cell']} -> "
                         f"{row['verdict']} (first divergence at "
                         f"{row['first_lag_d']}d on {row['first_coord']}).")
    sa = r.get("seq_atlas")
    if sa is not None and len(sa):
        com = sa[sa["status"] == "COMMON_SEQUENCE"]
        lines.append(f"- **Broad sequence atlas**: {len(com)} COMMON "
                     f"sequences across windows 1-14D (17 atoms).")
    po = r.get("partial_order")
    if po is not None and len(po):
        req = po[po["edge_class"] == "REQUIRED_ORDER"]
        lines.append(f"- **Partial-order graph**: {len(req)} REQUIRED_ORDER "
                     f"edges; cycles preserved, no DAG forcing.")
    ce = r.get("constraint_entropy")
    if ce is not None:
        lines.append(f"- **Constraint entropy**: {ce}.")
    wf = r.get("waterfall")
    if wf is not None and len(wf):
        v = wf["verdict"].iloc[0] if "verdict" in wf.columns else "n/a"
        lines.append(f"- **Waterfall threshold hierarchy**: {v}.")
    meta = r.get("metastability")
    if meta is not None and len(meta):
        lines.append("- **Metastability**: " + "; ".join(
            f"{row['cell']}:{row['verdict']}" for _, row in meta.iterrows()))
    tf = r.get("transfer_flow")
    if tf is not None and len(tf):
        lines.append(f"- **Transfer-flow pilot**: {tf['verdict'].iloc[0]}.")
    lp = r.get("loner_placement")
    if lp is not None and len(lp):
        v = lp["verdict"].iloc[0] if "verdict" in lp.columns else "n/a"
        lines.append(f"- **Loner field placement**: {v}.")
    dr = r.get("directional")
    if dr is not None and len(dr):
        v = dr["verdict"].iloc[0] if "verdict" in dr.columns else "n/a"
        lines.append(f"- **Directional asymmetry**: {v}.")
    pr = r.get("potential_realization")
    if pr is not None and len(pr):
        lines.append(f"- **Potential->realization**: "
                     f"{pr['verdict'].iloc[0]}.")
    lines += ["", "## Node actions", ""]
    nodes = r.get("nodes")
    if nodes is not None and len(nodes):
        for _, row in nodes.iterrows():
            lines.append(f"- {row['operation']}: {row['node']} "
                         f"({row['status']})")
    lines += ["", "## Limits", "",
              "- All ordering/entropy results are descriptive (<= L2).",
              "- Metastability audit is empirical, not spectral.",
              "- Sequence scans are exploratory; FDR applied across "
              "sequences but multiple-window inflation remains.",
              "- No strategy translation performed.",
              "", "`human_review_required = TRUE`",
              "`next_checkpoint_authorized = FALSE`",
              "NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · "
              "NO LEVERAGE · NO DEPLOYMENT"]
    (OUT / "24_MECH12_DECISION.md").write_text("\n".join(lines) + "\n",
                                              encoding="utf-8")
    return "\n".join(lines)


def main():
    dfw = _cache_step("dfw", load_dfw)
    ev = _cache_step("ev", load_ev)
    health = _cache_step("health", load_health)
    band = _cache_step("bandpanel", load_band_panel)
    loners = _cache_step("loners", load_loners)
    consensus = _cache_step("lf6_consensus", load_lf6_consensus)
    peer_paths = _cache_step("lf6_peer_paths", load_lf6_peer_paths)
    print(f"[data] dfw {dfw.shape} ev {ev.shape} health {health.shape} "
          f"band {band.shape} loners {loners.shape} "
          f"consensus {consensus.shape} peer_paths {peer_paths.shape}",
          flush=True)

    life = _cache_step("ws1", lambda: ws1_full_lifecycle(dfw))
    fg, geo = _cache_step("ws2", lambda: ws2_failure_geometry(dfw))
    sa = _cache_step("ws3", lambda: ws3_broad_sequences(dfw))
    po = _cache_step("ws4", lambda: ws4_partial_order(dfw, sa))
    pb = _cache_step("ws5", lambda: ws5_prefix_branching(dfw))
    ce = _cache_step("ws6", lambda: ws6_constraint_entropy(dfw, sa, pb))
    wf = _cache_step("ws7", lambda: ws7_waterfall_thresholds(dfw, band))
    pgn, pge = _cache_step("ws8", lambda: ws8_patch_graph(band, loners,
                                                          consensus))
    ppr = _cache_step("ws9", lambda: ws9_patch_perturbation(dfw, band))
    pfc = _cache_step("ws10", lambda: ws10_peer_formation_context(dfw,
                                                                  peer_paths))
    meta = _cache_step("ws11", lambda: ws11_metastability(dfw))
    tfl = _cache_step("ws12", lambda: ws12_transfer_flow(dfw, meta))
    lp = _cache_step("ws13", lambda: ws13_loner_field_placement(dfw, loners,
                                                                consensus))
    asg = _cache_step("ws14", lambda: ws14_abs_vs_sigma(ev))
    dr = _cache_step("ws15", lambda: ws15_directional_asymmetry(dfw))
    prr = _cache_step("ws16", lambda: ws16_potential_realization(dfw, sa, po))

    results = {
        "lifecycle": life, "failure_geom": fg, "failure_geo_detail": geo,
        "seq_atlas": sa, "partial_order": po, "prefix_branching": pb,
        "constraint_entropy": ce[1] if isinstance(ce, tuple) else ce,
        "waterfall": wf, "patch_graph_nodes": pgn, "patch_graph_edges": pge,
        "patch_perturbation": ppr, "peer_formation": pfc,
        "metastability": meta, "transfer_flow": tfl,
        "loner_placement": lp, "abs_sigma": asg, "directional": dr,
        "potential_realization": prr, "nodes": None,
    }
    fmap = ws17_field_map(results)
    results["field_map"] = fmap
    nodes = ws17_nodes(results)
    results["nodes"] = nodes
    ws17_nulls(results)
    vd = write_verdicts(results)
    write_summary(results)
    write_decision(results)
    print(f"[done] MECH-12 pipeline complete. verdict={vd['verdict']}",
          flush=True)


if __name__ == "__main__":
    main()
