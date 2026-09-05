# ================================================================ 35 global law hierarchy
def global_law_hierarchy():
    # stage feature sets, cumulative; compare ascending vs descending order
    from sklearn.metrics import roc_auc_score
    gap = p16 - p26
    stages = {
        "FORCING_FAMILY": ["forcing"],
        "THRESHOLD_SAT": ["thr_pos", "sat"],
        "EXIT_AVAIL_PRESSURE": ["p1", "ent"],
        "ROUTE_COMMITMENT": ["gap"],
        "TRANSFER_REALIZATION": ["te"],
    }
    featmap = {"forcing": fc_arr, "thr_pos": thr_pos, "sat": field_act,
               "p1": p16, "ent": ent6, "gap": gap, "te": te_arr}
    y = (prop7 >= 0.5).astype(float)   # realized-propagation flag
    m0 = np.isfinite(prop7)
    order_asc = ["FORCING_FAMILY", "THRESHOLD_SAT", "EXIT_AVAIL_PRESSURE", "ROUTE_COMMITMENT", "TRANSFER_REALIZATION"]
    order_desc = list(reversed(order_asc))
    rows = []
    Xall = np.column_stack([featmap[c] for st in stages for c in stages[st]])
    mall = m0 & np.isfinite(Xall).all(1)
    split = int(np.sum(mall) * 0.7)
    idx = np.where(mall)[0]; rng = np.random.RandomState(0); rng.shuffle(idx)
    itr, ite = idx[:split], idx[split:]
    from sklearn.model_selection import train_test_split
    def auc_for(keys):
        try:
            X = np.column_stack([featmap[c] for st in keys for c in stages[st]])
            m = m0 & np.isfinite(X).all(1)
            sy, sz = y[m], (X[m] - X[m].mean(0)) / (X[m].std(0) + 1e-9)
            t1, t2 = train_test_split(np.arange(len(sy)), test_size=0.3, random_state=0, stratify=sy)
            lr = LogisticRegression(max_iter=2000).fit(sz[t1], sy[t1])
            return float(roc_auc_score(sy[t2], lr.predict_proba(sz[t2])[:, 1]))
        except Exception:
            return np.nan
    for order, label in ((order_asc, "ASC_TOPOLOGY"), (order_desc, "DESC_TRANSFER")):
        acc = []
        for k in range(1, 6):
            acc.append(auc_for(order[:k]))
        rows.append(dict(order=label, auc_stage_1=round(acc[0], 3),
                         auc_stage_2=round(acc[1], 3), auc_stage_3=round(acc[2], 3),
                         auc_stage_4=round(acc[3], 3), auc_stage_5=round(acc[4], 3),
                         gain_first_3=round(acc[2] - acc[0], 3),
                         gain_last_2=round(acc[4] - acc[2], 3)))
    dfh = pd.DataFrame(rows)
    g_mid_a = dfh[dfh["order"] == "ASC_TOPOLOGY"]["gain_first_3"].iloc[0]
    g_mid_d = dfh[dfh["order"] == "DESC_TRANSFER"]["gain_first_3"].iloc[0]
    if g_mid_a > 0.04 and g_mid_d <= 0.02:
        verd = "LOOSE_HIERARCHY"
    elif max(g_mid_a, g_mid_d) <= 0.02:
        verd = "PARALLEL_CONSTRAINT_SYSTEM"
    else:
        verd = "HYBRID"
    dfh["hierarchy_verdict"] = verd
    W("35_GLOBAL_LAW_HIERARCHY.csv")(dfh.round(3))

# ================================================================ 36 promote merge dissolve
def promote_merge_dissolve():
    rows = []
    def add(obj, role, action, note, verdicts=None):
        rows.append(dict(object=obj, os_role=role, action=action, note=note[:160]))
    # carried objects with MECH-19 verdict actions (finalized after reviewing CSVs)
    add("ROAD_TOPOLOGY_4STATE", "STRUCTURAL_CORE", "FREEZE", "carried; not reopened in MECH-19")
    add("EDGE_REGISTRY_93", "STRUCTURAL_CORE", "FREEZE", "MECH-18 93-edge registry")
    add("MULTI_FORCING_FAMILY", "ADAPTIVE_LAW", "PROMOTE", "deep primitives/signatures round 2")
    add("ROUTE_COMMITMENT", "ADAPTIVE_LAW", "PROMOTE", "commitment gradient from p1 vs reopening")
    add("PRESSURE_CONCENTRATION", "ADAPTIVE_LAW", "PROMOTE", "mechanics localized per state")
    add("EDGE_PRUNING", "ADAPTIVE_LAW", "PROMOTE", "resolution mechanism; see 05")
    add("CONCENTRATION_PHASES", "ADAPTIVE_LAW", "LOCAL", "gradient > discrete phases recommend")
    add("RESPONSE_NODES", "ADAPTIVE_LAW", "PROMOTE", "coupling/PCA geometry; see 12-14")
    add("SATURATION_WITHOUT_DELIVERY", "LOCAL_PHYSICS", "PROMOTE", "matched without-delivery anatomy; see 16")
    add("THRESHOLD_INVERSION", "ADAPTIVE_LAW", "LOCAL", "species taxonomy; see 18")
    add("DEEP_RANK_HYSTERESIS", "LOCAL_PHYSICS", "LOCAL", "survival range; see 19-20")
    add("BIRTH_FAILURE_MECHANISM", "ADAPTIVE_LAW", "PROMOTE", "demand-overload in unresolved route set")
    add("LOAD_COMMITMENT_MISMATCH", "ADAPTIVE_LAW", "LOCAL", "candidate; see 22")
    add("POTENTIAL_REALIZATION", "ADAPTIVE_LAW", "PROMOTE", "parallel constraints + lattice; see 24-27")
    add("FAILURE_MOTIFS", "ADAPTIVE_LAW", "LOCAL", "distinctness; see 26")
    add("2022_STRUCTURAL_SCAR", "RESEARCH_ONLY", "PROMOTE", "survives unclamped repair; see 28-31")
    add("GLOBAL_MEMORY_KERNEL", "CONTEXT_ONLY", "DISSOLVE", "not re-earned; carried gone")
    add("UNIVERSAL_STATE_AGE", "CONTEXT_ONLY", "DISSOLVE", "remains dead")
    W("36_PROMOTE_MERGE_DISSOLVE.csv")(pd.DataFrame(rows))

# ================================================================ 37 null and failed
def null_failed():
    rows = []
    for f in sorted(OUT.glob("*.csv")):
        try:
            d = pd.read_csv(f)
        except Exception:
            continue
        na = int(d.isna().sum().sum()); total = int(d.size)
        flags = []
        for val in ("DATA_LIMITED", "NO_EVENT_BLOCK_FOUND", "NULL", "DATA_BLOCKED",
                    "NO_STABLE", "ARTIFACT", "LEVEL_SUFFICIENT", "WEAK"):
            for c in d.columns:
                nv = int((d[c].astype(str) == val).sum())
                if nv:
                    flags.append(f"{val}:{nv}")
        rows.append(dict(file=f.name, n_rows=len(d), n_cells=total, null_cells=na,
                         null_frac=round(na / max(total, 1), 3),
                         failed_flags=";".join(sorted(set(flags))[:6])))
    W("37_NULL_AND_FAILED_RESULTS.csv")(pd.DataFrame(rows))

# ================================================================ RUNNER
if __name__ == "__main__":
    # ensure snapback exists for downstream 2022 files
    if isinstance(EV_UNC, dict) and EV_UNC.get("snap_base") is None:
        EV_UNC["snap_base"] = EV_UNC.get("peak")
    # internal-writing deliverables not invoked at module level
    route_commitment()
    saturation_mechanism()
    response_node_coupling()
    response_coordinate_pilot()
    saturation_without_delivery()
    threshold_inversion_species()
    deep_hysteresis_map()
    hysteresis_boundaries()
    birth_failure_mechanism()
    load_commitment_mismatch()
    birth_recovery()
    potential_realization_constraints()
    constraint_combination_lattice()
    failure_motif_decomposition()
    realization_geometry()
    unclamped_repair()
    event_reestimate()
    surface_vs_law_recovery()
    structural_scar()
    reexcursions()
    event_end()
    precedence_map()
    global_law_hierarchy()
    promote_merge_dissolve()
    null_failed()
    print("MECH-19 BUILD COMPLETE")