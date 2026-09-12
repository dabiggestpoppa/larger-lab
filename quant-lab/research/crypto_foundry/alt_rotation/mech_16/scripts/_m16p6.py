from _m16base import *
from _m16base import _cache_step, _entropy, _fdr, _fmt, _js_distance, \
    SUBPERIODS
from _m16p2 import _binned_entropy_slope


# =========================================================================
# WS15: DIRECTION AS SECOND-ORDER CONSEQUENCE RECHECK
#      (16_DIRECTION_CONSTRAINT_TRANSPORT.csv)
# =========================================================================
def _cond_dir_entropy(df, keys):
    tot = 0.0
    cnt = 0
    for _, g in df.groupby(keys):
        v = g["next_dir"].dropna()
        if len(v) >= 10:
            tot += len(v) * _entropy(v)
            cnt += len(v)
    return tot / cnt if cnt else np.nan


def ws15_direction_constraint_transport(df):
    rows = []
    for sp in SUBPERIODS:
        s = df[df["subperiod"] == sp]
        if len(s) < 200:
            continue
        base = _entropy(s["next_dir"].dropna())
        st = _cond_dir_entropy(s, ["state_code"])
        sage = _cond_dir_entropy(s, ["state_code", "ab"])
        sagee = _cond_dir_entropy(s, ["state_code", "ab", "ent_tier"])
        sageea = _cond_dir_entropy(s, ["state_code", "ab", "ent_tier",
                                       "act_tier"])
        sageeaf = _cond_dir_entropy(s, ["state_code", "ab", "ent_tier",
                                        "act_tier", "f_tier"])
        rows.append({
            "subperiod": sp, "base_dir_entropy": base,
            "cond_state": st, "cond_state_age": sage,
            "cond_state_age_entropy": sagee,
            "cond_state_age_entropy_activation": sageea,
            "cond_full_chain": sageeaf,
            "red_state": base - st, "red_plus_age": st - sage,
            "red_plus_entropy": sage - sagee,
            "red_plus_activation": sagee - sageea,
            "red_plus_forcing": sageea - sageeaf,
            "total_reduction": base - sageeaf,
        })
    out = pd.DataFrame(rows)
    if len(out):
        full_ok = int((out["total_reduction"] >= 0.02).sum())
        if full_ok >= 4:
            verdict = "DIRECTION_CONSTRAINT_TRANSPORTS"
        elif full_ok >= 2:
            verdict = "DIRECTION_CONSTRAINT_PARTIAL"
        else:
            verdict = "DIRECTION_CONSTRAINT_NOT_TRANSPORTED"
    else:
        verdict = "DATA_LIMITED"
    out["verdict"] = verdict
    out.to_csv(OUT / "16_DIRECTION_CONSTRAINT_TRANSPORT.csv", index=False)
    return out, verdict


# =========================================================================
# WS16: TRANSITION TOPOLOGY vs TRANSITION RATES (17_TRANSITION_TOPOLOGY_VS_RATES.csv)
# =========================================================================
def _transition_matrix(d, gc):
    v = d[[gc, gc + "_next"]].dropna()
    ct = pd.crosstab(v[gc], v[gc + "_next"], normalize="index")
    return ct


def _topology_compare(m1, m2, edge_min=0.02):
    """Compare two transition matrices. Returns edge Jaccard, dominant-exit
    agreement, mean |dp|, mean row JS."""
    keys = sorted(set(m1.index) | set(m2.index))
    edges1 = set()
    edges2 = set()
    for a in keys:
        for b in keys:
            p1 = m1.loc[a, b] if (a in m1.index and b in m1.columns) else 0.0
            p2 = m2.loc[a, b] if (a in m2.index and b in m2.columns) else 0.0
            if p1 >= edge_min:
                edges1.add((a, b))
            if p2 >= edge_min:
                edges2.add((a, b))
    jac = len(edges1 & edges2) / max(1, len(edges1 | edges2))
    agree = 0.0
    cnt = 0
    for a in keys:
        r1 = m1.loc[a] if a in m1.index else pd.Series(dtype=float)
        r2 = m2.loc[a] if a in m2.index else pd.Series(dtype=float)
        if len(r1) and len(r2):
            agree += float(r1.idxmax() == r2.idxmax())
            cnt += 1
    dom_agree = agree / cnt if cnt else np.nan
    dp = []
    js = []
    for a in keys:
        r1 = m1.loc[a] if a in m1.index else pd.Series(dtype=float)
        r2 = m2.loc[a] if a in m2.index else pd.Series(dtype=float)
        if len(r1) and len(r2):
            dp.append(float((r1 - r2.reindex(r1.index, fill_value=0)).abs()
                            .mean()))
            js.append(_js_distance(r1, r2))
    return (float(jac), float(dom_agree) if dom_agree == dom_agree else
            np.nan, float(np.mean(dp)) if dp else np.nan,
            float(np.mean(js)) if js else np.nan)


def ws16_transition_topology_vs_rates(df):
    d = df.sort_values("d").reset_index(drop=True)
    cut = int(0.8 * len(d))
    early, late = d.iloc[:cut], d.iloc[cut:]
    rows = []
    for label, gc in [("6_cell", "grp6"), ("8_cell", "grp8")]:
        m1 = _transition_matrix(early, gc)
        m2 = _transition_matrix(late, gc)
        jac, dom, dp, js = _topology_compare(m1, m2)
        rows.append({"surface": label, "comparison": "early80_vs_late20",
                     "edge_jaccard": jac, "dominant_exit_agreement": dom,
                     "mean_abs_dp": dp, "mean_row_js": js})
    # adjacent-subperiod summary
    for label, gc in [("6_cell", "grp6"), ("8_cell", "grp8")]:
        mats = {}
        for sp in SUBPERIODS:
            s = d[d["subperiod"] == sp]
            if len(s) >= 100:
                mats[sp] = _transition_matrix(s, gc)
        jacs = []
        doms = []
        dpm = []
        sps = sorted(mats)
        for i in range(len(sps) - 1):
            jac, dom, dp, _ = _topology_compare(mats[sps[i]], mats[sps[i + 1]])
            if jac == jac:
                jacs.append(jac)
            if dom == dom:
                doms.append(dom)
            if dp == dp:
                dpm.append(dp)
        rows.append({"surface": label, "comparison": "adjacent_subperiods",
                     "edge_jaccard": float(np.mean(jacs)) if jacs else np.nan,
                     "dominant_exit_agreement": float(np.mean(doms))
                     if doms else np.nan,
                     "mean_abs_dp": float(np.mean(dpm)) if dpm else np.nan,
                     "n_pairs": len(jacs)})
    out = pd.DataFrame(rows)
    # verdict on 6-cell early-vs-late: dominant-exit identity is the primary
    # topology signal (all cells keeping their modal exit = same roads);
    # edge-set Jaccard is secondary (low-prob edges crossing a 0.02 cutoff
    # are noisy).
    r6 = out[(out["surface"] == "6_cell") &
             (out["comparison"] == "early80_vs_late20")].iloc[0]
    jac6, dp6, dom6 = r6["edge_jaccard"], r6["mean_abs_dp"], \
        r6["dominant_exit_agreement"]
    if jac6 == jac6 and dp6 == dp6:
        if dom6 >= 0.83:
            verdict = "TOPOLOGY_STABLE_RATES_DRIFT" if dp6 >= 0.03 else \
                "FULL_STABILITY"
        elif jac6 >= 0.7:
            verdict = "TOPOLOGY_DRIFT"
        else:
            verdict = "NO_STABLE_STRUCTURE"
    else:
        verdict = "DATA_LIMITED"
    out["verdict"] = "TRANSITION_TOPOLOGY_VS_RATES_DONE"
    out["transition_verdict"] = verdict
    out.to_csv(OUT / "17_TRANSITION_TOPOLOGY_VS_RATES.csv", index=False)
    return out, verdict


# =========================================================================
# WS17: NULL / ARTIFACT AND COMPOSITION AUDIT (18_ARTIFACT_AND_COMPOSITION_AUDIT.csv)
# =========================================================================
def ws17_artifact_audit(df):
    d = df.copy()
    d["d"] = pd.to_datetime(d["d"])
    rows = []
    flags = []
    for sp in SUBPERIODS:
        s = d[d["subperiod"] == sp]
        n = len(s)
        if n < 50:
            continue
        vc = s["grp6"].value_counts()
        max_share = float(vc.max() / n) if n else np.nan
        single_dom = max_share > 0.50
        if single_dom:
            flags.append(f"{sp}:single_cell_dominance")
        rows.append({
            "subperiod": sp, "n_days": n,
            "n_cells_used": int((vc >= 20).sum()),
            "max_cell_share": max_share,
            "single_cell_dominance": single_dom,
            "n_stablecoins_mean": float(s["n_stablecoins_in_top500"].mean()),
            "stablecoin_na_frac": float(s["stablecoin_change_7d"].isna()
                                        .mean()),
            "vol_med_mean": float(s["vol_med"].mean()),
            "rank_depth_mean": float(s["rank_depth_rel"].mean()),
            "rank_depth_sd": float(s["rank_depth_rel"].std()),
            "forcing_na": int(s["forcing"].isna().sum()),
            "ent_resid_na": int(s["ent_resid"].isna().sum()),
            "nbranch_na": int(s["nbranch7"].isna().sum()),
            "total_mcap_mean": float(s["total_mcap"].mean()),
        })
    out = pd.DataFrame(rows)
    # universe composition shift across subperiods
    if len(out) >= 2:
        sd_nsc = float(out["n_stablecoins_mean"].std())
        sd_vol = float(out["vol_med_mean"].std() / max(1e-12, out[
            "vol_med_mean"].mean()))
        sd_mcap = float(out["total_mcap_mean"].std() / max(1e-12, out[
            "total_mcap_mean"].mean()))
    else:
        sd_nsc = sd_vol = sd_mcap = np.nan
    out["verdict"] = "ARTIFACT_AUDIT_DONE"
    out["artifact_flags"] = ";".join(flags)
    out["sd_stablecoin_count"] = sd_nsc
    out["cv_vol_scale"] = sd_vol
    out["cv_mcap_scale"] = sd_mcap
    out.to_csv(OUT / "18_ARTIFACT_AND_COMPOSITION_AUDIT.csv", index=False)
    has_flags = len(flags) > 0
    return out, ("ARTIFACTS_DETECTED" if has_flags else "NO_ARTIFACTS_DETECTED")


# =========================================================================
# WS18: FREE EXTERNAL CONTEXT PILOT (19_FREE_EXTERNAL_CONTEXT_PILOT.csv)
# =========================================================================
def ws18_external_context_pilot():
    rows = [{
        "source": "SoSoValue_free_ETF_flow_history",
        "local_coverage_days": 0,
        "required_coverage": "free ETF-flow history sufficient to span the "
                             "recent regime",
        "status": "DATA_BLOCKED",
        "reason": "No local ETF-flow data present; scraping and paid APIs "
                  "are forbidden by the free-only tech stack gate. "
                  "Exploratory pilot only; not a core MECH-16 requirement.",
        "verdict": "DATA_BLOCKED",
    }]
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "19_FREE_EXTERNAL_CONTEXT_PILOT.csv", index=False)
    return out
