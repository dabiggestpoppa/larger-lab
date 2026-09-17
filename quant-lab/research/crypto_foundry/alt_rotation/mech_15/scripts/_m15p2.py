from _m15base import *
from _m15base import _cache_step, _age_band, _fdr, _fmt, _entropy, \
    _subperiod_split, _proportion_and_n, MC, cell_stats


def _cell_dist(df, a, b):
    """Behavioral distance between two cells (used by BOTH the merge tree and
    the partition replay so the merge hierarchy is self-consistent)."""
    ga = df[df["mcell"] == a]
    gb = df[df["mcell"] == b]
    if len(ga) < 10 or len(gb) < 10:
        return np.nan
    ds = []
    for col in ["prop7", "ren7", "rank7", "tail7"]:
        pa, na = _proportion_and_n(ga[col].to_numpy())
        pb, nb = _proportion_and_n(gb[col].to_numpy())
        if pa == pa and pb == pb:
            ds.append(min(1.0, abs(pa - pb)))
    for col in ["next_dir", "next_dir"]:
        for sgn in [1, -1]:
            pa = float((ga[col] > 0 if sgn == 1 else ga[col] < 0).mean())
            pb = float((gb[col] > 0 if sgn == 1 else gb[col] < 0).mean())
            if pa == pa and pb == pb:
                ds.append(min(1.0, abs(pa - pb)))
    for col in ["forcing", "rank_depth_rel"]:
        xa = ga[col].to_numpy(dtype=float); xb = gb[col].to_numpy(dtype=float)
        xa = xa[~np.isnan(xa)]; xb = xb[~np.isnan(xb)]
        if len(xa) >= 10 and len(xb) >= 10:
            ma, mb = float(np.mean(xa)), float(np.mean(xb))
            ds.append(min(1.0, abs(ma - mb) / max(1e-9, max(abs(ma),
                                                             abs(mb)))))
    ea = _entropy(ga["next_cell"].dropna()) if ga["next_cell"].notna().sum() \
        >= 20 else np.nan
    eb = _entropy(gb["next_cell"].dropna()) if gb["next_cell"].notna().sum() \
        >= 20 else np.nan
    if ea == ea and eb == eb:
        ds.append(min(1.0, abs(ea - eb) / max(1e-9, max(ea, eb))))
    return float(np.mean(ds)) if ds else np.nan


def _distance_matrix(df, names):
    n = len(names)
    D = np.full((n, n), np.inf)
    for i in range(n):
        for j in range(i + 1, n):
            d = _cell_dist(df, names[i], names[j])
            D[i][j] = d
            D[j][i] = d
    return D


def _agglomerate(D, names, ncells):
    """Average-linkage agglomeration down to ncells. Returns (clusters,
    steps) where clusters is a list of index-lists and steps records every
    merge in order."""
    n = len(names)
    clusters = [[i] for i in range(n)]
    steps = []
    step_no = 1
    while len(clusters) > ncells:
        best = None
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                d = np.nanmean([D[a][b] for a in clusters[i]
                                for b in clusters[j]])
                if np.isnan(d):
                    continue
                if best is None or d < best[0]:
                    best = (d, i, j)
        if best is None:
            break
        d, i, j = best
        merged = sorted(clusters[i] + clusters[j])
        steps.append({"step": step_no,
                      "n_clusters_after": len(clusters) - 1,
                      "merge_distance": float(d),
                      "merged_members": "+".join(names[k] for k in merged)})
        new_clusters = [c for k, c in enumerate(clusters) if k not in (i, j)]
        new_clusters.append(merged)
        clusters = new_clusters
        step_no += 1
    return clusters, steps


# =========================================================================
# WS5: COLLAPSE / MERGE SEARCH (06_COLLAPSE_MERGE_TREE.csv)
# =========================================================================
def ws5_merge_tree(df, names):
    D = _distance_matrix(df, names)
    clusters, steps = _agglomerate(D, names, 1)
    out = pd.DataFrame(steps)
    # mark which reduced cuts each merge belongs to
    for cut, ncells in [("cut_16", 16), ("cut_12", 12), ("cut_8", 8),
                        ("cut_6", 6), ("cut_4", 4)]:
        out[cut] = (out["n_clusters_after"] <= ncells).astype(int)
    out["verdict"] = "MERGE_TREE_BUILT"
    out.to_csv(OUT / "06_COLLAPSE_MERGE_TREE.csv", index=False)
    return out, D


def ws6_partition_at(df, names, ncells):
    """Partition of cells at a given cluster count (deterministic replay of
    the same average-linkage rule used for the merge tree)."""
    D = _distance_matrix(df, names)
    clusters, _ = _agglomerate(D, names, ncells)
    return clusters


# =========================================================================
# WS6: INFORMATION RETENTION CURVE (07_INFORMATION_RETENTION_CURVE.csv)
# =========================================================================
def ws6_information_retention(df, names):
    outcomes = {
        "prop7": "propagation", "ren7": "reentry",
        "dir_entropy": "directional_entropy",
        "rank7": "rank_recruitment", "tail7": "tail_activation",
        "next_cell": "next_state_distribution",
    }

    def _between_var(sub, col):
        rows = []
        for _, g in sub.groupby("grp"):
            if len(g) < 20:
                continue
            if col == "next_cell":
                v = _entropy(g["next_cell"].dropna())
                if np.isnan(v):
                    continue
            elif col == "dir_entropy":
                v = _entropy(g["next_dir"].dropna())
                if np.isnan(v):
                    continue
            else:
                v = float(g[col].mean())
                if np.isnan(v):
                    continue
            rows.append((len(g), v))
        if len(rows) < 2:
            return np.nan
        tot = sum(w for w, _ in rows)
        mu = sum(w * v for w, v in rows) / tot
        return sum(w * (v - mu) ** 2 for w, v in rows) / tot

    # reference: 16-cell between-cell variance
    dfr = df[df["mcell"].isin(names)].copy()
    dfr["grp"] = dfr["mcell"].astype("category").cat.codes
    ref = {col: _between_var(dfr, col) for col in outcomes}
    rows = []
    for ncells in [16, 12, 8, 6, 4]:
        if ncells == 16:
            part = [[i] for i in range(len(names))]
        else:
            part = ws6_partition_at(df, names, ncells)
        mcell2grp = {}
        for gi, grp in enumerate(part):
            for mi in grp:
                mcell2grp[names[mi]] = gi
        dfp = df[df["mcell"].isin(mcell2grp)].copy()
        dfp["grp"] = dfp["mcell"].map(mcell2grp)
        row = {"n_cells": ncells, "n_groups": len(part)}
        for col, label in outcomes.items():
            bv = _between_var(dfp, col)
            if np.isnan(bv) or np.isnan(ref[col]) or ref[col] <= 0:
                row[label] = np.nan
            else:
                # retained fraction capped at 1.0 (between-group variance of a
                # coarser partition can exceed the reference; that is an
                # artifact, not information gain)
                row[label] = float(min(1.0, bv / ref[col]))
        rows.append(row)
    out = pd.DataFrame(rows)
    out["verdict"] = "INFORMATION_RETENTION_CURVE_BUILT"
    out.to_csv(OUT / "07_INFORMATION_RETENTION_CURVE.csv", index=False)
    return out
