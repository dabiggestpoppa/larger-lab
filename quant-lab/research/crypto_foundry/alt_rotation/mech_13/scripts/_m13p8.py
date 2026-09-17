from _m13base import *
from _m13base import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _entropy, _subperiod_split, _atom_series


# =========================================================================
# WS17: UPSIDE / DOWNSIDE GEOMETRY (18_UPSIDE_GEOMETRY, 19_DOWNSIDE_GEOMETRY)
# =========================================================================

def _family_field_compare(dfw, up):
    d = dfw.copy()
    if up:
        broad = (d["ev_BAND_BROAD_UPSIDE"] + d["ev_MULTI_BAND_UPSIDE"] > 0)
        iso = d["ev_ISOLATED_UPSIDE"] > 0
    else:
        broad = d["ev_COORDINATED_DOWNSIDE"] > 0
        iso = d["ev_ISOLATED_DOWNSIDE_EXTREME"] > 0
    b = d[broad]
    i = d[iso]
    rows = []
    if len(b) >= 20 and len(i) >= 20:
        for metric, col in [
            ("breadth", "top500_breadth_30d"),
            ("dispersion", "top500_dispersion_30d"),
            ("vol", "vol_med"),
            ("btc7", "btc_return_7d"),
            ("eth_rel7", "eth_btc_relative_return_7d"),
            ("concentration", "top3_share"),
            ("state_age", "age_in_cell")]:
            rows.append({"metric": metric,
                         "coordinated_or_broad_n": int(len(b)),
                         "isolated_n": int(len(i)),
                         "coordinated_median": float(b[col].median()),
                         "isolated_median": float(i[col].median())})
        rows.append({"metric": "cell_HH",
                     "coordinated_median": float((b["cell"] ==
                                                  "HIGH_BREADTH_HIGH_DISP")
                                                 .mean()),
                     "isolated_median": float((i["cell"] ==
                                               "HIGH_BREADTH_HIGH_DISP")
                                              .mean()),
                     "coordinated_or_broad_n": int(len(b)),
                     "isolated_n": int(len(i))})
    out = pd.DataFrame(rows)
    return out


def ws17_upside_geometry(dfw):
    out = _family_field_compare(dfw, up=True)
    if len(out):
        bb = out[out["metric"] == "breadth"]
        if len(bb) and bb["coordinated_median"].iloc[0] - \
                bb["isolated_median"].iloc[0] >= 0.12:
            verdict = "FIELD_SELECTIVE_UPSIDE"
        else:
            verdict = "NOT_FIELD_SELECTIVE_UPSIDE"
        out["verdict"] = verdict
    else:
        out = pd.DataFrame([{"verdict": "DATA_LIMITED"}])
    out.to_csv(OUT / "18_UPSIDE_GEOMETRY.csv", index=False)
    return out


def ws17_downside_geometry(dfw):
    out = _family_field_compare(dfw, up=False)
    if len(out):
        bb = out[out["metric"] == "breadth"]
        if len(bb) and bb["coordinated_median"].iloc[0] - \
                bb["isolated_median"].iloc[0] >= 0.12:
            verdict = "STRUCTURED_DOWNSIDE"
        else:
            # conditional structure: cross by rank depth / vol tercile
            verdict = "GLOBAL_FIELD_NEUTRAL" if \
                abs(bb["coordinated_median"].iloc[0] -
                    bb["isolated_median"].iloc[0]) < 0.05 else \
                "WEAKLY_STRUCTURED_DOWNSIDE"
        out["verdict"] = verdict
    else:
        out = pd.DataFrame([{"verdict": "DATA_LIMITED"}])
    out.to_csv(OUT / "19_DOWNSIDE_GEOMETRY.csv", index=False)
    return out


# =========================================================================
# WS18: DIRECTIONAL INFORMATION GAIN (20_DIRECTIONAL_INFORMATION_GAIN.csv)
# =========================================================================

def ws18_directional_information_gain(dfw):
    d = dfw.copy()
    # directional next-day sign: net up-event vs net down-event direction
    up_cols = ["ev_BAND_BROAD_UPSIDE", "ev_MULTI_BAND_UPSIDE",
               "ev_ISOLATED_UPSIDE"]
    dn_cols = ["ev_ISOLATED_DOWNSIDE_EXTREME", "ev_LOCAL_CLUSTER_DOWNSIDE",
               "ev_COORDINATED_DOWNSIDE"]
    nup = d[up_cols].sum(axis=1)
    ndn = d[dn_cols].sum(axis=1)
    d["dir_today"] = np.sign(nup - ndn)   # +1 up-dominant, -1 down-dominant
    d["next_dir"] = d["dir_today"].shift(-1)
    d = d.dropna(subset=["next_dir"])
    y = d["next_dir"].to_numpy()
    pos = (y > 0).astype(float)
    # baseline entropy of next direction sign
    base_p = np.mean(y > 0)
    base_ent = -(base_p * np.log2(base_p) + (1 - base_p) *
                 np.log2(1 - base_p)) if 0 < base_p < 1 else 0.0
    cond_cols = ["top500_breadth_30d", "top500_dispersion_30d", "vol_med",
                 "btc_return_7d", "age_in_cell", "top3_share"]
    rows = [{"condition": "UNCONDITIONAL", "branch_entropy": float(base_ent),
             "n": int(len(d))}]
    for cc in cond_cols:
        if cc not in d.columns:
            continue
        med = float(d[cc].median())
        hi = d[d[cc] >= med]
        lo = d[d[cc] < med]
        for lbl, sub in [("HIGH", hi), ("LOW", lo)]:
            if len(sub) < 50:
                continue
            pp = float((sub["next_dir"] > 0).mean())
            ent = -(pp * np.log2(pp) + (1 - pp) * np.log2(1 - pp)) \
                if 0 < pp < 1 else 0.0
            rows.append({"condition": f"{cc}={lbl}",
                         "branch_entropy": float(ent), "n": int(len(sub))})
    # joint conditioning: by (cell, age band)
    d["ab"] = d["age_in_cell"].apply(_age_band)
    for cell in CELLS:
        for abn in ["AGE_1", "AGE_15_PLUS"]:
            sub = d[(d["cell"] == cell) & (d["ab"] == abn)]
            if len(sub) < 50:
                continue
            pp = float((sub["next_dir"] > 0).mean())
            ent = -(pp * np.log2(pp) + (1 - pp) * np.log2(1 - pp)) \
                if 0 < pp < 1 else 0.0
            rows.append({"condition": f"cell={cell}&age={abn}",
                         "branch_entropy": float(ent),
                         "n": int(len(sub))})
    out = pd.DataFrame(rows)
    out["delta_entropy"] = out["branch_entropy"] - base_ent
    # does conditioning narrow direction entropy? require a specific
    # well-populated cell to sit well below the unconditional baseline
    cond_ents = out.iloc[1:]["branch_entropy"].to_numpy()
    collapse = float(np.nanmean(cond_ents < base_ent)) if len(cond_ents) else 0
    min_e = float(np.nanmin(cond_ents)) if len(cond_ents) else np.nan
    best = out.iloc[1:]["branch_entropy"].min()
    best_n = int(out.iloc[1:].loc[out.iloc[1:]["branch_entropy"].idxmin(),
                "n"]) if len(out) > 1 else 0
    narrow = best is not None and base_ent - best >= 0.08
    out["verdict"] = ("DIRECTION_LOCALLY_CONSTRAINED" if narrow and
                      best_n >= 200 else
                     "DIRECTION_CONSTRAINED_BY_FIELD" if collapse >= 0.7 and
                     min_e is not None and base_ent - min_e >= 0.02 else
                     "DIRECTION_NOT_CONSTRAINED")
    out["best_cond"] = out["condition"].iloc[
        out["branch_entropy"].idxmin()]
    out.to_csv(OUT / "20_DIRECTIONAL_INFORMATION_GAIN.csv", index=False)
    return out


# =========================================================================
# WS19: LOCAL CONVERSION PATHS (21_LOCAL_CONVERSION_PATHS.csv)
# =========================================================================

def ws19_local_conversion_paths(dfw):
    d = dfw.copy()
    atoms = _atom_series(d)
    n = len(d)
    state = d["state"].to_numpy()
    H = 14
    # define a family of local "conversion scaffolds" -- ordered prefixes that
    # avoid requiring the full 6-chain. Each scaffold is a target prefix.
    scaffolds = [
        ("PATH_A", ["BREADTH_EXPANDS", "CONCENTRATION_RELEASES",
                    "DISPERSION_EXPANDS", "TAIL_UP_ACTIVATES",
                    "RANK_RECRUITS"]),
        ("PATH_B", ["BREADTH_EXPANDS", "CONCENTRATION_RELEASES",
                    "DISPERSION_EXPANDS"]),
        ("PATH_C", ["BREADTH_EXPANDS", "DISPERSION_EXPANDS",
                    "RANK_RECRUITS", "PROPAGATION_CONFIRMS"]),
        ("PATH_D", ["CONCENTRATION_RELEASES", "DISPERSION_EXPANDS",
                    "TAIL_UP_ACTIVATES"]),
    ]
    names = list(atoms.columns)
    arr = atoms.to_numpy()
    rows = []
    base_prop = np.zeros(n)
    for i in range(n - H):
        j = min(i + H, n - 1)
        base_prop[i] = pd.Series(state[i + 1:j + 1]).isin(
            SUCCESS_LABELS).any()
    base_rate = float(np.nanmean(base_prop)) if (base_prop > 0).any() \
        else np.nan
    for pname, chain in scaffolds:
        hit = np.zeros(n)
        for i in range(n - H):
            w = arr[i + 1:i + 1 + H]
            fired = {}
            for k, name in enumerate(names):
                hits_i = np.where(w[:, k] > 0)[0]
                if len(hits_i):
                    fired[name] = int(hits_i[0])
            order = [k for k, _ in sorted(fired.items(),
                                          key=lambda x: x[1])]
            pos = {kk: p for p, kk in enumerate(order)}
            streak = 0
            last = -1
            for a in chain:
                if a in pos and pos[a] > last:
                    streak += 1
                    last = pos[a]
                else:
                    break
            hit[i] = streak / len(chain)
        # rows per prefix depth (dedup full-chain depth)
        for depth in sorted(set([2, 3, 4, len(chain)])):
            if depth > len(chain):
                continue
            sel = hit >= depth / len(chain) - 1e-9
            if sel.sum() < 30:
                continue
            prop_rate = float(np.nanmean(np.where(sel, base_prop, np.nan)))
            rows.append({
                "path": pname, "prefix_len": int(depth),
                "atom_seq": "->".join(chain[:depth]),
                "n_days": int(sel.sum()),
                "prop_rate_14d": prop_rate,
                "lift_vs_base": float(prop_rate / max(1e-9, base_rate)),
                "n_subperiods": int(d.loc[
                    sel, "subperiod"].nunique())})
    out = pd.DataFrame(rows)
    if len(out):
        named = out[(out["n_days"] >= MIN_PROMOTE_N) &
                    (out["n_subperiods"] >= MIN_SUBPERIODS) &
                    (out["lift_vs_base"] >= 1.3)]
        out["verdict"] = ("LOCAL_CONVERSION_PATHS" if len(named) >= 2 else
                         "LOCAL_CONVERSION_PATH_SINGLE" if len(named) == 1
                         else "NO_STABLE_LOCAL_PATH")
        out["n_named_paths"] = int(len(named))
    out.to_csv(OUT / "21_LOCAL_CONVERSION_PATHS.csv", index=False)
    return out