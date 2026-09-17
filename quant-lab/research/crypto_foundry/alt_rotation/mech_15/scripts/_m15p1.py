from _m15base import *
from _m15base import _cache_step, _age_band, _fdr, _fmt, _entropy, \
    _subperiod_split, _cohen_d, _ztest_prop, _proportion_and_n, MC, \
    build_matrix_frame, cell_stats


def _support_grade(n, nsp, max_share):
    if n >= 100 and nsp >= 4 and max_share == max_share and max_share < 0.5:
        return "ROBUST"
    if n >= 50 and nsp >= 3:
        return "LOCAL"
    if n >= 20:
        return "SPARSE"
    return "UNUSABLE"


# =========================================================================
# WS1: RAW 16-CELL MATRIX (02_RAW_16_CELL_MATRIX.csv)
# =========================================================================
def ws1_raw_matrix(df):
    rows = []
    for mc in MC:
        g = df[df["mcell"] == mc]
        r = cell_stats(df, mc)
        if r is not None:
            rows.append(r)
    out = pd.DataFrame(rows)
    out["support"] = out.apply(lambda r: _support_grade(
        r["n_days"], r["n_subperiods"], r["max_subperiod_share"]), axis=1)
    out.to_csv(OUT / "02_RAW_16_CELL_MATRIX.csv", index=False)
    return out


# =========================================================================
# WS2: SUPPORT / SPARSITY AUDIT (03_CELL_SUPPORT_AUDIT.csv)
# =========================================================================
def ws2_support_audit(df):
    rows = []
    for mc in MC:
        g = df[df["mcell"] == mc]
        sp = g["subperiod"].replace("UNKNOWN", np.nan).dropna()
        vc = sp.value_counts()
        nsp = int(sp.nunique()) if len(sp) else 0
        max_share = float(vc.max() / vc.sum()) if len(vc) else np.nan
        rows.append({"mcell": mc, "n_days": int(len(g)),
                     "n_subperiods": nsp, "max_subperiod_share": max_share,
                     "grade": _support_grade(len(g), nsp, max_share),
                     "subperiod_counts": dict(vc)})
    out = pd.DataFrame(rows)
    out["verdict"] = "SUPPORT_AUDIT_COMPLETE"
    out.to_csv(OUT / "03_CELL_SUPPORT_AUDIT.csv", index=False)
    return out


# =========================================================================
# WS3: CELL DIFFERENTIATION (04_CELL_DIFFERENTIATION.csv)
# =========================================================================
# Pairwise two-sample tests on 9 metrics; BH-FDR over ALL pair x metric
# comparisons. DISTINCT = >=3 metrics differ at q<=0.10; PARTIALLY_DISTINCT
# = 1-2; REDUNDANT = 0; DATA_LIMITED when either cell is not usable.
def ws3_cell_differentiation(df):
    usable = [mc for mc in MC
              if len(df[df["mcell"] == mc]) >= 50]
    metric_defs = [
        ("prop7", "prop", "PROPORTION"),
        ("ren7", "reentry", "PROPORTION"),
        ("rank7", "rank_recruit", "PROPORTION"),
        ("tail7", "tail_share", "PROPORTION"),
        ("next_dir", "dir_entropy", "ENTROPY"),
        ("next_cell", "next_cell_entropy", "ENTROPY"),
        ("forcing", "forcing", "CONTINUOUS"),
        ("rank_depth_rel", "activation_depth", "CONTINUOUS"),
        ("fam_broad_up", "upside_mix", "PROPORTION"),
    ]
    rows = []
    pairs = []
    for i in range(len(usable)):
        for j in range(i + 1, len(usable)):
            pairs.append((usable[i], usable[j]))
    for a, b in pairs:
        ga = df[df["mcell"] == a]
        gb = df[df["mcell"] == b]
        base = {"cell_a": a, "cell_b": b,
                "n_a": int(len(ga)), "n_b": int(len(gb))}
        for col, mname, kind in metric_defs:
            if kind == "PROPORTION":
                pa, na = _proportion_and_n(ga[col].to_numpy())
                pb, nb = _proportion_and_n(gb[col].to_numpy())
                z, p = _ztest_prop(pa, na, pb, nb)
                d = _cohen_d(ga[col].to_numpy(), gb[col].to_numpy())
            elif kind == "CONTINUOUS":
                xa = ga[col].to_numpy(dtype=float)
                xb = gb[col].to_numpy(dtype=float)
                xa = xa[~np.isnan(xa)]; xb = xb[~np.isnan(xb)]
                if len(xa) < 10 or len(xb) < 10:
                    p = np.nan
                else:
                    _, p = ranksums(xa, xb)
                d = _cohen_d(xa, xb)
            else:  # ENTROPY: descriptive difference only (no sampling test)
                ea = _entropy(ga[col].dropna()) if ga[col].notna().sum() >= 20 \
                    else np.nan
                eb = _entropy(gb[col].dropna()) if gb[col].notna().sum() >= 20 \
                    else np.nan
                p = np.nan
                d = float(ea - eb) if (ea == ea and eb == eb) else np.nan
            rows.append(dict(base, metric=mname, p=p, d=d))
    out = pd.DataFrame(rows)
    # FDR across testable (non-entropy) pair x metric rows only
    pvals = out["p"].to_numpy(dtype=float)
    qs = np.full(len(out), np.nan)
    ok = ~np.isnan(pvals)
    if ok.sum():
        qs[ok] = _fdr(pvals[ok])
    out["q"] = qs
    out["sig"] = (out["q"] <= FDR_Q).astype(int)
    n_sig = out.groupby(["cell_a", "cell_b"])["sig"].sum().reset_index(
        name="n_sig_metrics")
    n_metrics = len([m for _, m, k in metric_defs if k != "ENTROPY"])
    def _verdict(r):
        if r["n_sig_metrics"] >= 3:
            return "DISTINCT"
        if r["n_sig_metrics"] >= 1:
            return "PARTIALLY_DISTINCT"
        return "REDUNDANT"
    n_sig["verdict"] = n_sig.apply(_verdict, axis=1)
    n_sig["n_metrics_tested"] = n_metrics
    # descriptive entropy gap (mean |delta| over the two entropy metrics)
    ent = out[out["metric"].isin(["dir_entropy", "next_cell_entropy"])]
    egap = ent.groupby(["cell_a", "cell_b"])["d"].apply(
        lambda s: float(np.nanmean(s.abs())) if s.notna().any() else np.nan)
    n_sig["entropy_gap"] = n_sig.merge(egap.rename("eg"), on=["cell_a",
        "cell_b"], how="left")["eg"]
    n_sig["max_pair_n"] = [max(int(out.loc[(out.cell_a == r.cell_a) &
                                          (out.cell_b == r.cell_b), "n_a"].iloc[0]),
                               int(out.loc[(out.cell_a == r.cell_a) &
                                          (out.cell_b == r.cell_b), "n_b"].iloc[0]))
                           for _, r in n_sig.iterrows()]
    n_sig.loc[n_sig["max_pair_n"] < 50, "verdict"] = "DATA_LIMITED"
    n_sig.to_csv(OUT / "04_CELL_DIFFERENTIATION.csv", index=False)
    return n_sig


# =========================================================================
# WS4: CELL SIMILARITY MATRIX (05_CELL_SIMILARITY_MATRIX.csv)
# =========================================================================
# Simple behavioral distance: mean over metrics of |cohen_d| clipped to 1,
# or absolute proportion/entropy difference scaled to [0,1].
def ws4_similarity_matrix(df, raw):
    metrics = [
        ("p_prop_7d", "PROP"), ("p_reentry_7d", "PROP"),
        ("rank_recruit", "PROP"), ("tail_share", "PROP"),
        ("next_cell_entropy", "CONT"), ("dir_entropy", "CONT"),
        ("forcing", "CONT"), ("rank_depth_rel", "CONT"),
        ("p_up", "PROP"), ("p_down", "PROP"),
    ]
    cell_rows = {}
    for mc in MC:
        g = df[df["mcell"] == mc]
        if len(g) == 0:
            continue
        r = raw[raw["mcell"] == mc]
        if len(r):
            cell_rows[mc] = r.iloc[0]
    names = list(cell_rows.keys())
    D = np.zeros((len(names), len(names)))
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            if i == j:
                continue
            ds = []
            ra = cell_rows[a]; rb = cell_rows[b]
            for col, kind in metrics:
                va = float(ra[col]) if col in ra and pd.notna(ra[col]) \
                    else np.nan
                vb = float(rb[col]) if col in rb and pd.notna(rb[col]) \
                    else np.nan
                if np.isnan(va) or np.isnan(vb):
                    continue
                if kind == "PROP":
                    ds.append(min(1.0, abs(va - vb)))
                else:
                    ds.append(min(1.0, abs(va - vb) /
                                  max(1e-9, max(abs(va), abs(vb)))))
            D[i, j] = float(np.mean(ds)) if ds else np.nan
    out = pd.DataFrame(D, index=names, columns=names)
    out.index.name = "mcell"
    out.to_csv(OUT / "05_CELL_SIMILARITY_MATRIX.csv")
    return out, names
