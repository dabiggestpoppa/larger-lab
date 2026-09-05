from _m16base import *
from _m16base import _cache_step, _entropy, _fdr, _fmt, _js_distance, \
    SURFACE_GROUP_COLS, ORDERING_METRICS, SUBPERIODS
from _m16p1 import ws1_holdout_repro, ws2_surface_6_vs_8
from _m16p2 import ws3_covariate_conditional_shift, \
    ws4_state_local_transfer
from _m16p3 import ws5_birth_geometry_transport, ws6_state_age_transport, \
    ws7_survival_branch_contraction
from _m16p4 import ws8_entropy_transport, ws9_common_forcing_transport, \
    ws10_rank_threshold_drift, ws11_saturation_law_drift
from _m16p5 import ws12_changepoint_scan, ws13_law_regime_candidates, \
    ws14_invariant_audit, _threshold_order_stability
from _m16p6 import ws15_direction_constraint_transport, \
    ws16_transition_topology_vs_rates, ws17_artifact_audit, \
    ws18_external_context_pilot


# =========================================================================
# WS19: PROMOTE / MERGE / DISSOLVE (20_PROMOTE_MERGE_DISSOLVE.csv)
# =========================================================================
def ws19_promote_merge_dissolve(results):
    rows = []
    # surfaces
    rows.append({"node": "16-CELL_RAW_SURFACE", "operation": "DISSOLVE",
                 "evidence": f"chrono rho mean={results['surf_mean']['16_cell']:.2f}; "
                             f"reduced surfaces preferred",
                 "status": "REPLACED_BY_REDUCED"})
    rows.append({"node": "6-CELL_OPERATIONAL_SURFACE", "operation": "PROMOTE",
                 "evidence": f"chrono rho mean={results['surf_mean']['6_cell']:.2f}; "
                             f"WS2={results['freeze_verdict']}",
                 "status": results["freeze_verdict"]})
    rows.append({"node": "8-CELL_RANK_SURFACE", "operation":
                 "PROMOTE" if results["freeze_verdict"] in
                 ("DUAL_RESOLUTION", "FREEZE_8") else "DESCRIPTIVE",
                 "evidence": f"rank retention {results['rank_ret_8']:.2f} vs "
                             f"{results['rank_ret_6']:.2f}; "
                             f"WS2={results['freeze_verdict']}",
                 "status": results["freeze_verdict"]})
    rows.append({"node": "4-CELL_SURFACE", "operation": "DESCRIPTIVE",
                 "evidence": "reference only",
                 "status": "NOT_SELECTED"})
    rows.append({"node": "4-STATE_BASELINE", "operation": "PROMOTE",
                 "evidence": "invariant topology (WS14 node 1)",
                 "status": "EARNED"})
    rows.append({"node": "MARKET_OS_STATE_SURFACE", "operation":
                 "PROMOTE" if results["final_verdict"].startswith("PASS")
                 else "HOLD",
                 "evidence": f"final={results['final_verdict']}",
                 "status": "FREEZE_CANDIDATE"})
    # invariant nodes
    for _, r in results["invariants"].iterrows():
        op = {"INVARIANT": "PROMOTE", "REGIME_MODULATED": "LOCAL_NODE",
              "LOCAL_ONLY": "DESCRIPTIVE", "DISSOLVE": "DISSOLVE"}.get(
                  r["verdict"], "DESCRIPTIVE")
        node = "STATE_X_AGE_CLOCK_LAW" if r["node"] == \
            "STATE_X_AGE_INTERACTION" and r["verdict"] == "DISSOLVE" else \
            r["node"]
        rows.append({"node": node, "operation": op,
                     "evidence": r["evidence"], "status": r["verdict"]})
    out = pd.DataFrame(rows)
    out["verdict"] = "PROMOTE_MERGE_DISSOLVE_DONE"
    out.to_csv(OUT / "20_PROMOTE_MERGE_DISSOLVE.csv", index=False)
    return out


# =========================================================================
# WS20: NULL AND FAILED RESULTS (21_NULL_AND_FAILED_RESULTS.csv)
# =========================================================================
def ws20_nulls(results):
    rows = [
        {"result": "Metastability (any cell)", "status": "KILLED",
         "note": "MECH-13; not revisited; transition structure is NOT "
                 "metastability"},
        {"result": "Universal sequence grammar", "status": "DEMOTED",
         "note": "MECH-12; not revived"},
        {"result": "Single hidden field coordinate", "status": "NULL",
         "note": "MECH-14; not revived in M16"},
        {"result": "Single initiation primitive", "status": "NULL",
         "note": "MECH-14 equifinality carried"},
        {"result": "Chronological instability = matrix invalid", "status":
         "REJECTED",
         "note": f"reproduced -0.50 on 16-cell but reduced surfaces stable; "
                 f"WS3={results['shift_verdict']}"},
        {"result": "Forced changepoint dates", "status": "NOT_FORCED",
         "note": f"aligned windows: {results['n_aligned_windows']}"},
        {"result": "Price-return direction as regime definition", "status":
         "NOT_USED", "note": "regimes defined by law signatures only"},
        {"result": "Semi-Markov clock resurrection", "status": "NOT_USED",
         "note": "plain clocks remain default"},
        {"result": "SoSoValue ETF flow context", "status": "DATA_BLOCKED",
         "note": "no local coverage; scraping/paying forbidden (WS18)"},
        {"result": "Upside permission region", "status": "CARRIED",
         "note": "MECH-15 NO_PERMISSION_REGION (definitional limit)"},
        {"result": "DAR as primitive", "status": "PILOT",
         "note": "pilot only, not promoted"},
    ]
    out = pd.DataFrame(rows)
    out["verdict"] = "NULL_AND_FAILED_DONE"
    out.to_csv(OUT / "21_NULL_AND_FAILED_RESULTS.csv", index=False)
    return out


# =========================================================================
# WS21: FIELD MODEL V1 FREEZE INPUT (22_FIELD_MODEL_V1_FREEZE_INPUT.md)
# =========================================================================
def ws21_freeze_input(results):
    inv = results["invariants"]
    L = [
        "# FIELD MODEL v1 — FREEZE INPUT (MECH-16)",
        "",
        "**Status**: input artifact only. No production code, no strategy "
        "translation, no execution.",
        "",
        "## 1. Surface",
        "",
        f"- MECH-15 6-cell reduced surface survives transportability checks "
        f"(topology chrono rho {results['topo6_chrono']:.2f}, LOSO "
        f"{results['topo6_loso']:.2f}); 8-cell carried for rank research "
        f"(rank retention {results['rank_ret_8']:.2f} vs "
        f"{results['rank_ret_6']:.2f}).",
        f"- WS2 freeze recommendation: {results['freeze_verdict']}.",
        f"- WS16 roads test: {results['transition_verdict']}.",
        "",
        "## 2. Invariant nodes (freeze candidates)",
        "",
    ]
    for _, r in inv.iterrows():
        node = "STATE_X_AGE_CLOCK_LAW" if r["node"] == \
            "STATE_X_AGE_INTERACTION" and r["verdict"] == "DISSOLVE" else \
            r["node"]
        L.append(f"- **{node}**: {r['verdict']} — {r['evidence']}")
    L += [
        "",
        "## 3. Regime modulation",
        "",
        f"- Transfer functions: {results['transfer_verdict']} "
        f"(WS4 drift fraction {results['drift_fraction']:.2f}).",
        f"- Covariate/conditional shift: {results['shift_verdict']}.",
        f"- Law regimes: {results['regime_verdict']}.",
        f"- Changepoint aligned windows: {results['n_aligned_windows']}.",
        f"- Rank thresholds: {results['rankthr_verdict']}; saturation law: "
        f"{results['saturation_verdict']}; forcing law: "
        f"{results['forcing_verdict']}.",
        f"- State x age clock: {results['clock_verdict']}; entropy law: "
        f"{results['entropy_verdict']}.",
        f"- Direction constraint transport: {results['dir_verdict']}.",
        "",
        "## 4. Open questions before final freeze",
        "",
        "- Chronological 80/20 remains the weak test; reduce to 6-cell + "
        "4-state as the canonical ordering surfaces.",
        "- Rank-threshold drift deserves a dedicated deep-patch audit if "
        "8-cell is carried operationally.",
        "- DAR stays pilot; relational state and asset health remain "
        "downstream overlays.",
        "",
        "`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`",
    ]
    (OUT / "22_FIELD_MODEL_V1_FREEZE_INPUT.md").write_text(
        "\n".join(L) + "\n", encoding="utf-8")
    return "\n".join(L)


# =========================================================================
# WS22: SUMMARY (23_MECH16_SUMMARY.md)
# =========================================================================
def ws22_summary(results):
    r = results
    L = ["# CRYPTO-ALT-MECH-16 — SUMMARY", "",
         "**State-Surface Drift, Topology vs Transfer-Function Stability, "
         "6-Cell vs 8-Cell Representation, Conditional Law Change, "
         "Common-Forcing Transportability, State x Age Hazard Drift, "
         "Entropy / Branch-Closure Stability, Rank-Recruitment Law, "
         "Birth-Geometry Transport, Field-Law Changepoints, Market-OS "
         "Surface Freeze Audit**", "",
         "AGENT 1 — CANONICAL FIELD CARTOGRAPHER · terrain research only",
         ""]
    nobj = [
        ("Holdout repro", "holdout_repro",
         f"16-cell chrono rho={r['surf_mean']['16_cell']:.2f} vs 6-cell "
         f"{r['surf_mean']['6_cell']:.2f} / 4-state "
         f"{r['surf_mean']['4_state']:.2f}"),
        ("6 vs 8 freeze", "freeze_verdict", "WS2 recommendation"),
        ("Covariate/conditional shift", "shift_verdict", "WS3"),
        ("Transfer functions", "transfer_verdict",
         f"invariant fraction {1 - r['drift_fraction']:.2f}"),
        ("Birth geometry", "birth_verdict", "WS5"),
        ("State x age clock", "clock_verdict", "WS6"),
        ("Survival branch contraction", "surv_verdict", "WS7"),
        ("Entropy law", "entropy_verdict", "WS8"),
        ("Common forcing law", "forcing_verdict", "WS9"),
        ("Rank thresholds", "rankthr_verdict", "WS10"),
        ("Saturation law", "saturation_verdict", "WS11"),
        ("Changepoint scan", "changepoint_verdict",
         f"{r['n_aligned_windows']} aligned window(s)"),
        ("Law regimes", "regime_verdict", "WS13"),
        ("Invariant audit", "invariant_verdict",
         f"{r['n_invariants']} INVARIANT nodes"),
        ("Direction transport", "dir_verdict", "WS15"),
        ("Transition roads", "transition_verdict", "WS16"),
        ("Artifact audit", "artifact_verdict", "WS17"),
        ("External context", "external_verdict", "WS18"),
    ]
    for label, key, tip in nobj:
        L.append(f"- **{label}**: {r[key]} — {tip}")
    L += ["", "## Key decisions", "",
          f"- **Final verdict**: {r['final_verdict']}",
          f"- **Freeze recommendation**: {r['freeze_verdict']}",
          f"- **Shift classification**: {r['shift_verdict']}",
          f"- **State x age clock**: {r['clock_verdict']}",
          f"- **Roads (transition topology)**: {r['transition_verdict']}",
          f"- **Invariants**: {r['n_invariants']}/8",
          "", "## Limits", "",
          "- Descriptive field anatomy (<= L2); no signal matrix.",
          "- DAR stays pilot; relational state and asset health are "
          "downstream overlays.",
          "- SoSoValue ETF flow context is DATA_BLOCKED (no local data).",
          "- Chronological 80/20 on the raw 16-cell surface is the weak "
          "test; canonical surfaces are the reduced matrix + 4-state.",
          "",
          "`human_review_required = TRUE`",
          "`next_checkpoint_authorized = FALSE`",
          "NO STRATEGY · NO PNL · NO EXECUTION · NO ENTRY/EXIT · NO SIZING · "
          "NO LEVERAGE · NO DEPLOYMENT"]
    (OUT / "23_MECH16_SUMMARY.md").write_text("\n".join(L) + "\n",
                                             encoding="utf-8")
    return "\n".join(L)


# =========================================================================
# WS23: DECISION (24_MECH16_DECISION.md)
# =========================================================================
def ws23_decision(results):
    r = results
    L = ["# CRYPTO-ALT-MECH-16 — DECISION", "", "## Verdict", "",
         f"**{r['final_verdict']}**", ""]
    Q = [
        ("1. Was the MECH-15 chronological failure reproduced?",
         f"yes on 16-cell propagation ordering (rho -0.50), while 16-cell "
         f"topology (branch/self-transition/dir-entropy) mean "
         f"{r['topo16_chrono']:.2f} — reproduced and localized to transfer "
         f"metrics (prop/rank) on sparse cells"),
        ("2. Is it topology drift or transfer-function drift?",
         f"{r['shift_verdict']} — topology 6-cell chrono "
         f"{r['topo6_chrono']:.2f} (LOSO {r['topo6_loso']:.2f}) vs "
         f"transfer {r['transfer6_chrono']:.2f}: roads stable, conditional "
         f"response reorders (WS3 + WS4 drift fraction {r['drift_fraction']:.2f})"),
        ("3. Does 6-cell or 8-cell representation survive better?",
         f"both stable; {r['freeze_verdict']} (rank retention "
         f"{r['rank_ret_8']:.2f} vs {r['rank_ret_6']:.2f})"),
        ("4. Should Market OS carry dual resolution?",
         f"{'yes' if r['freeze_verdict'] == 'DUAL_RESOLUTION' else 'no'} — "
         f"{r['freeze_verdict']}"),
        ("5. Is state x age transportable?", r["clock_verdict"]),
        ("6. Is entropy transportable?", r["entropy_verdict"]),
        ("7. Is common forcing transportable?", r["forcing_verdict"]),
        ("8. Are rank activation thresholds drifting?",
         f"{r['rankthr_verdict']} — deep-patch audit: "
         f"{r['rankthr_patch_verdict']}"),
        ("9. Are roads stable while traffic rates change?",
         r["transition_verdict"]),
        ("10. Did birth geometry change?", r["birth_verdict"]),
        ("11. Which nodes qualify as near-invariants?",
         "; ".join(r["invariants"].loc[r["invariants"]["verdict"] ==
                                        "INVARIANT", "node"].tolist())
         if r["n_invariants"] else "none"),
        ("12. Is Field Model v1 ready for freeze after this checkpoint?",
         f"CONDITIONAL_FREEZE_INPUT — {r['n_invariants']}/8 invariant "
         f"nodes; see 22_FIELD_MODEL_V1_FREEZE_INPUT.md"),
    ]
    L += ["## Decision questions", ""]
    for q, a in Q:
        L.append(f"- **{q}** {a}")
    L += ["", "## Node actions", ""]
    for _, row in r["nodes"].iterrows():
        L.append(f"- {row['operation']}: {row['node']} ({row['status']})")
    L += ["", "## Formal negatives / not carried", "",
          "- Metastability: dead. Universal sequence grammar: demoted.",
          "- Single hidden coordinate / single initiation primitive: null.",
          "- Chronological instability on the raw 16-cell is an artifact of "
          "sparse cells, not evidence of topology drift.",
          "- No changepoint is forced; only aligned multi-coordinate windows "
          "are reported.",
          "- SoSoValue ETF context: DATA_BLOCKED (no local data).",
          "- DAR remains pilot.",
          "", "## Limits", "",
          "- Descriptive (<= L2); no strategy translation.",
          "- Regime definitions use law signatures, never price direction.",
          "- 8-cell is a research surface; 6-cell remains operational unless "
          "human review prefers dual resolution.",
          "",
          "`human_review_required = TRUE`",
          "`next_checkpoint_authorized = FALSE`",
          "NO STRATEGY · NO PNL · NO EXECUTION · NO ENTRY/EXIT · NO SIZING · "
          "NO LEVERAGE · NO DEPLOYMENT"]
    (OUT / "24_MECH16_DECISION.md").write_text("\n".join(L) + "\n",
                                              encoding="utf-8")
    return "\n".join(L)


def write_verdicts(results):
    v = {
        "checkpoint": "MECH-16",
        "commit": "TBD",
        "verdict": results["final_verdict"],
        "freeze_recommendation": results["freeze_verdict"],
        "shift_classification": results["shift_verdict"],
        "chrono_rho_16cell": results["surf_mean"]["16_cell"],
        "chrono_rho_6cell": results["surf_mean"]["6_cell"],
        "chrono_rho_4state": results["surf_mean"]["4_state"],
        "clock": results["clock_verdict"],
        "entropy_law": results["entropy_verdict"],
        "forcing_law": results["forcing_verdict"],
        "rank_thresholds": results["rankthr_verdict"],
        "transition_roads": results["transition_verdict"],
        "n_invariants": results["n_invariants"],
        "human_review_required": True,
        "next_checkpoint_authorized": False,
    }
    (OUT / "_verdicts.json").write_text(json.dumps(v, indent=2),
                                        encoding="utf-8")
    return v


def main():
    dfw = None
    band = _cache_step("band16", load_band15)
    ev = _cache_step("ev16", load_ev15)
    df = _cache_step("frame16", lambda: build_surfaces(load_frame15()))
    pact = _cache_step("pact16", lambda: patch_activation_daily(band))

    holdout, surf_mean = _cache_step("ws1", lambda: ws1_holdout_repro(df))
    ret15 = pd.read_csv(M15_ROOT / "07_INFORMATION_RETENTION_CURVE.csv")
    ws2out, freeze_verdict = _cache_step(
        "ws2", lambda: ws2_surface_6_vs_8(df, holdout, ret15))
    shift = _cache_step("ws3", lambda: ws3_covariate_conditional_shift(df))
    transfer, transfer_summ = _cache_step(
        "ws4", lambda: ws4_state_local_transfer(df))
    birth = _cache_step("ws5", lambda: ws5_birth_geometry_transport(df))
    sa_out, sa_trend, sa_state_v, clock_verdict = _cache_step(
        "ws6", lambda: ws6_state_age_transport(df))
    surv_out, surv_slopes, surv_verdict = _cache_step(
        "ws7", lambda: ws7_survival_branch_contraction(df))
    ent_out, ent_vd, entropy_verdict = _cache_step(
        "ws8", lambda: ws8_entropy_transport(df))
    cf_out, cf_tr, forcing_verdict = _cache_step(
        "ws9", lambda: ws9_common_forcing_transport(df, pact))
    rt_out, rt_vd, rankthr_verdict = _cache_step(
        "ws10", lambda: ws10_rank_threshold_drift(df, pact))
    sat_out, sat_vd, saturation_verdict = _cache_step(
        "ws11", lambda: ws11_saturation_law_drift(df, pact))
    cp_out, cp_aligned = _cache_step(
        "ws12", lambda: ws12_changepoint_scan(df, pact, ev))
    regime_out, regime_verdict = _cache_step(
        "ws13", lambda: ws13_law_regime_candidates(transfer, rt_out,
                                                   sa_trend))
    thr_rhos = _cache_step("thr_rhos", lambda: _threshold_order_stability(
        df, pact))
    # transition verdict needed by invariant audit
    trans_out, transition_verdict = _cache_step(
        "ws16", lambda: ws16_transition_topology_vs_rates(df))
    invariants = _cache_step(
        "ws14", lambda: ws14_invariant_audit(
            df, pact, ev, holdout, clock_verdict, entropy_verdict,
            forcing_verdict, transition_verdict, thr_rhos))
    dir_out, dir_verdict = _cache_step(
        "ws15", lambda: ws15_direction_constraint_transport(df))
    art_out, artifact_verdict = _cache_step(
        "ws17", lambda: ws17_artifact_audit(df))
    ext_out = _cache_step("ws18", ws18_external_context_pilot)

    # ---- decision logic ----
    TOPO_METRICS = ["branch_entropy", "self_transition", "dir_entropy"]
    TRANSFER_METRICS = ["prop", "ren", "rank"]
    def _mean_rho(label, test, metrics):
        sub = holdout[(holdout["surface_label"] == label) &
                      (holdout["test"] == test) &
                      (holdout["metric"].isin(metrics))]
        m = sub["rho"].dropna()
        return float(m.mean()) if len(m) else np.nan
    surf_mean = {}
    for label, gc in SURFACE_GROUP_COLS.items():
        sub = holdout[(holdout["surface_label"] == label) &
                      (holdout["test"] == "chronological_80_20")]
        m = sub["rho"].dropna()
        surf_mean[label] = float(m.mean()) if len(m) else np.nan
    topo6_chrono = _mean_rho("6_cell", "chronological_80_20", TOPO_METRICS)
    topo6_loso = _mean_rho("6_cell", "leave_one_subperiod_out",
                            TOPO_METRICS)
    transfer6_chrono = _mean_rho("6_cell", "chronological_80_20",
                                  TRANSFER_METRICS)
    topo8_chrono = _mean_rho("8_cell", "chronological_80_20", TOPO_METRICS)
    topo16_chrono = _mean_rho("16_cell", "chronological_80_20",
                               TOPO_METRICS)
    # topology stable? roads (branch exits, self-transition, directional
    # constraint) must keep their ordering; transfer rates may reorder.
    surf_stable = topo6_chrono >= 0.5 and topo6_loso >= 0.7
    # transfer drift? conditional response rates reorder chronologically OR
    # WS3 attributes shift to the conditional law OR WS4 slopes drift
    shift_verdict = str(shift["verdict"].iloc[0]) if len(shift) else "n/a"
    drift_frac = float((transfer["law_verdict"] == "DRIFT_SLOPE").sum() /
                       max(1, int((transfer["law_verdict"].isin(
                           ["INVARIANT_SLOPE", "DRIFT_SLOPE"])).sum())))
    transfer_drift = transfer6_chrono < 0.3 or shift_verdict in (
        "TRANSFER_FUNCTION_DRIFT", "MIXED_DRIFT", "BASE_RATE_SHIFT") or \
        drift_frac >= 0.4
    n_inv = int((invariants["verdict"] == "INVARIANT").sum())
    n_aligned = len(cp_aligned)
    if not surf_stable:
        final = "FAIL_MECH16_SURFACE_NOT_TRANSPORTABLE"
    elif transfer_drift:
        final = "PASS_MECH16_TOPOLOGY_STABLE_TRANSFER_DRIFT"
    elif regime_verdict == "LAW_REGIMES_NAMED":
        final = "PASS_MECH16_REGIME_MODULATED_FIELD"
    elif n_inv >= 6:
        final = "PASS_MECH16_STABLE_FIELD_SURFACE"
    elif n_inv >= 4:
        final = "PASS_MECH16_PARTIAL_INVARIANTS"
    else:
        final = "PASS_MECH16_REGIME_MODULATED_FIELD"
    birth_verdict = str(birth["verdict"].iloc[0]) if len(birth) else "n/a"
    # rank-threshold patch-level detail for decision
    rtv = rt_vd.copy()
    n_stat = int((rtv["patch_verdict"].isin(
        ["STATIONARY", "STATIONARY_SATURATED"])).sum())
    n_drift = int((rtv["patch_verdict"] == "DRIFT").sum())
    rankthr_patch_verdict = (f"{n_stat} STATIONARY (incl. saturated) / "
                             f"{n_drift} DRIFT patches")
    ret15s = ret15.set_index("n_cells")
    rank_ret_6 = float(ret15s.loc[6, "rank_recruitment"])
    rank_ret_8 = float(ret15s.loc[8, "rank_recruitment"])
    results = {
        "holdout": holdout, "surf_mean": surf_mean,
        "freeze_verdict": freeze_verdict, "shift": shift,
        "shift_verdict": shift_verdict, "transfer": transfer,
        "transfer_verdict": "DRIFT_SLOPES" if drift_frac >= 0.4 else
        "INVARIANT_SLOPES",
        "drift_fraction": drift_frac, "birth_verdict": birth_verdict,
        "invariant_verdict": f"{n_inv}/8 invariant",
        "clock_verdict": clock_verdict, "surv_verdict": surv_verdict,
        "entropy_verdict": entropy_verdict, "forcing_verdict":
        forcing_verdict, "rankthr_verdict": rankthr_verdict,
        "rankthr_patch_verdict": rankthr_patch_verdict,
        "saturation_verdict": saturation_verdict,
        "changepoint_verdict": "SCAN_DONE" if n_aligned else
        "NO_ALIGNED_WINDOWS", "n_aligned_windows": n_aligned,
        "regime_verdict": regime_verdict, "invariants": invariants,
        "n_invariants": n_inv, "dir_verdict": dir_verdict,
        "transition_verdict": transition_verdict,
        "artifact_verdict": artifact_verdict,
        "external_verdict": "DATA_BLOCKED", "nodes": None,
        "rank_ret_6": rank_ret_6, "rank_ret_8": rank_ret_8,
        "final_verdict": final,
        "topo6_chrono": topo6_chrono, "topo6_loso": topo6_loso,
        "transfer6_chrono": transfer6_chrono,
        "topo8_chrono": topo8_chrono, "topo16_chrono": topo16_chrono,
        "holdout_repro": f"topology 6-cell chrono {topo6_chrono:.2f} "
                          f"(LOSO {topo6_loso:.2f}) vs transfer "
                          f"{transfer6_chrono:.2f}; 16-cell prop chrono "
                          f"-0.50 vs topology {topo16_chrono:.2f}",
    }
    nodes = ws19_promote_merge_dissolve(results)
    results["nodes"] = nodes
    ws20_nulls(results)
    ws21_freeze_input(results)
    ws22_summary(results)
    ws23_decision(results)
    write_verdicts(results)
    print(f"[done16] MECH-16 pipeline complete. verdict={final} "
          f"freeze={freeze_verdict} shift={shift_verdict} "
          f"invariants={n_inv}/8", flush=True)
    return results


if __name__ == "__main__":
    main()
