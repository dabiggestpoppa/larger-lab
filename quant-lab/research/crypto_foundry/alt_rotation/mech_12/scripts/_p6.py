from _p1 import *
from _p1 import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _perm_p, _atom_series
# =========================================================================
# WS15: UP vs DOWN FIELD ASYMMETRY (18_DIRECTIONAL_ASYMMETRY_FIELD.csv)
# =========================================================================

FAMILIES = {
    "ISOLATED_DOWNSIDE": "ev_ISOLATED_DOWNSIDE_EXTREME",
    "LOCAL_CLUSTER_DOWN": "ev_LOCAL_CLUSTER_DOWNSIDE",
    "ISOLATED_UPSIDE": "ev_ISOLATED_UPSIDE",
    "BAND_BROAD_UP": "ev_BAND_BROAD_UPSIDE",
    "MULTI_BAND_UP": "ev_MULTI_BAND_UPSIDE",
    "COORDINATED_DOWN": "ev_COORDINATED_DOWNSIDE",
}


def ws15_directional_asymmetry(dfw):
    d = dfw.copy()
    rows = []
    for fname, col in FAMILIES.items():
        sub = d[d[col] > 0]
        if len(sub) < 10:
            continue
        rows.append({
            "family": fname, "sign": "DOWN" if "DOWN" in fname or
            "DOWN" in col else "UP",
            "n_events": int(len(sub)),
            "p_HH": float((sub["cell"] == "HIGH_BREADTH_HIGH_DISP").mean()),
            "p_LL": float((sub["cell"] == "LOW_BREADTH_LOW_DISP").mean()),
            "med_breadth": float(sub["top500_breadth_30d"].median()),
            "med_dispersion": float(sub["top500_dispersion_30d"].median()),
            "med_top3_share": float(sub["top3_share"].median()),
            "med_vol": float(sub["vol_med"].median()),
            "med_btc7": float(sub["btc_return_7d"].median()),
            "med_eth_rel7": float(sub["eth_btc_relative_return_7d"].median())
            if "eth_btc_relative_return_7d" in sub.columns else np.nan,
            "med_rank_depth": float(sub["rank_depth_rel"].median())
            if "rank_depth_rel" in sub.columns else np.nan,
            "med_age": float(sub["age_in_cell"].median()),
            "p_BROAD_RISK": float((sub["state"] ==
                                   "BROAD_RISK_EXPANSION").mean()),
            "p_BTC_CONC": float((sub["state"] ==
                                 "BTC_CONCENTRATION").mean()),
            "p_MIXED": float((sub["state"] ==
                              "MIXED_NO_CLEAR_ROUTE").mean()),
            "n_subperiods": int(sub["subperiod"].nunique())})
    out = pd.DataFrame(rows)
    # asymmetry test: family-level field geometry spread (not pooled sign)
    verdict = "INCONCLUSIVE"
    if len(out) >= 2:
        br = out["med_breadth"].to_numpy()
        spread = float(np.nanmax(br) - np.nanmin(br))
        if spread >= 0.15:
            verdict = "ASYMMETRIC_FIELD_GEOMETRY"
        else:
            verdict = "SYMMETRIC_FIELD_GEOMETRY"
        out["spread_med_breadth"] = spread
    out["verdict"] = verdict
    out.to_csv(OUT / "18_DIRECTIONAL_ASYMMETRY_FIELD.csv", index=False)
    return out


# =========================================================================
# WS16: POTENTIAL -> REALIZATION REVISIT (19_POTENTIAL_REALIZATION_REVISIT.csv)
# =========================================================================

POTENTIAL_CHAIN = [
    ("BREADTH_EXPANDS", "PARTICIPATION_CAPACITY"),
    ("CONCENTRATION_RELEASES", "CAPITAL_DECONCENTRATION"),
    ("DISPERSION_EXPANDS", "DIFFERENTIATED_MOVEMENT"),
    ("TAIL_UP_ACTIVATES", "TAIL_ACTIVATION"),
    ("RANK_RECRUITS", "RANK_RECRUITMENT"),
    ("PROPAGATION_CONFIRMS", "PROPAGATION"),
]


def ws16_potential_realization(dfw, seq_atlas, partial_order):
    d = dfw.copy()
    atoms = _atom_series(d)
    arr = atoms.to_numpy()
    names = list(atoms.columns)
    state = d["state"].to_numpy()
    n = len(d)
    h = 14
    # for each day, does the full chain (all 6 atoms in listed order) fire
    # within 14D, and does propagation confirm?
    chain_atoms = [a for a, _ in POTENTIAL_CHAIN]
    chain_hits = np.zeros(n)
    chain_counts = np.zeros(n)
    prop_after_chain = np.zeros(n)
    for i in range(n - h):
        w = arr[i + 1:i + 1 + h]
        fired = {}
        for k, name in enumerate(names):
            hits = np.where(w[:, k] > 0)[0]
            if len(hits):
                fired[name] = int(hits[0])
        order = [x[0] for x in sorted(fired.items(), key=lambda x: x[1])]
        # longest prefix of chain that appears in order
        pos = {name: p for p, name in enumerate(order)}
        streak = 0
        last_pos = -1
        for a in chain_atoms:
            if a in pos and pos[a] > last_pos:
                streak += 1
                last_pos = pos[a]
            else:
                break
        chain_counts[i] = streak
        if streak >= 5:
            chain_hits[i] = 1
            j = min(i + h, n - 1)
            if pd.Series(state[i + 1:j + 1]).isin(SUCCESS_LABELS).any():
                prop_after_chain[i] = 1
    # baseline propagation rate
    base_prop = np.zeros(n)
    for i in range(n - h):
        j = min(i + h, n - 1)
        base_prop[i] = pd.Series(state[i + 1:j + 1]).isin(
            SUCCESS_LABELS).any()
    rows = []
    for stage_i in range(1, 7):
        stage_name = POTENTIAL_CHAIN[stage_i - 1][1]
        hit = chain_counts >= stage_i
        if hit.sum() < 30:
            continue
        prop_rate = float(np.nanmean(np.where(hit, base_prop, np.nan)))
        rows.append({
            "stage": stage_name,
            "chain_atom": POTENTIAL_CHAIN[stage_i - 1][0],
            "n_days_reached": int(hit.sum()),
            "prop_within_14d_given_stage": float(np.nanmean(
                np.where(hit, base_prop, np.nan))),
            "lift_vs_base": float(np.nanmean(np.where(hit, base_prop,
                                                      np.nan)) /
                                  max(1e-9, np.nanmean(base_prop)))})
    out = pd.DataFrame(rows)
    if len(out):
        # PROPAGATION stage is the outcome itself (circular); base the
        # verdict on the last non-outcome stage (RANK_RECRUITMENT)
        non_outcome = out[out["stage"] != "PROPAGATION"]
        last = non_outcome.iloc[-1] if len(non_outcome) else out.iloc[-1]
        if last["n_days_reached"] >= MIN_PROMOTE_N and \
                last["lift_vs_base"] >= 1.5:
            verdict = "CANDIDATE_CONVERSION_PRIMITIVE"
        elif last["n_days_reached"] >= MIN_PROMOTE_N and \
                last["lift_vs_base"] >= 1.25:
            verdict = "LOCAL_CONVERSION_PATH"
        else:
            verdict = "NO_SINGLE_PATH"
        out["verdict"] = verdict
        out.loc[out["stage"] == "PROPAGATION", "verdict"] = verdict
    else:
        out = pd.DataFrame([{"verdict": "NULL",
                             "stage": "", "chain_atom": "",
                             "n_days_reached": 0,
                             "prop_within_14d_given_stage": np.nan,
                             "lift_vs_base": np.nan}])
    out.to_csv(OUT / "19_POTENTIAL_REALIZATION_REVISIT.csv", index=False)
    return out
