from _p1 import *
from _p1 import _cache_step, _age_band, _perturbation_flags, _fdr, _fmt, _perm_p, _atom_series
# =========================================================================
# WS3: BROAD SEQUENCE SEARCH (04_BROAD_SEQUENCE_ATLAS.csv)
# =========================================================================

SEQ_WINDOWS = [1, 2, 3, 5, 7, 10, 14]


def _window_words(atoms, h):
    """For each day, ordered list of atom names that first fire within
    the next h days (order = first appearance)."""
    n = len(atoms)
    names = list(atoms.columns)
    arr = atoms.to_numpy()
    words = []
    for i in range(n - h):
        w = arr[i + 1:i + 1 + h]
        first = {}
        for k, name in enumerate(names):
            hits = np.where(w[:, k] > 0)[0]
            if len(hits):
                first[name] = int(hits[0])
        if first:
            ordered = [k for k, _ in sorted(first.items(), key=lambda x: x[1])]
            words.append("->".join(ordered))
        else:
            words.append("NONE")
    return words


def ws3_broad_sequences(dfw):
    df = dfw.copy()
    atoms = _atom_series(df)
    subperiod = df["subperiod"].to_numpy()
    rows = []
    for h in SEQ_WINDOWS:
        words = _window_words(atoms, h)
        # word -> per-subperiod counts
        from collections import defaultdict
        cnt = defaultdict(int)
        sub_cnt = defaultdict(lambda: defaultdict(int))
        for i, w in enumerate(words):
            if w == "NONE":
                continue
            cnt[w] += 1
            sp = subperiod[i]
            sub_cnt[w][sp] += 1
        total_windows = sum(1 for w in words if w != "NONE")
        # marginal atom rates within window h
        marg = {}
        n = len(atoms)
        for name in atoms.columns:
            c = 0
            col = atoms[name].to_numpy()
            for i in range(n - h):
                if col[i + 1:i + 1 + h].sum() > 0:
                    c += 1
            marg[name] = c / max(1, total_windows)
        for w, c in cnt.items():
            parts = w.split("->")
            exp_rate = 1.0
            for p in parts:
                exp_rate *= marg.get(p, 0.05)
            exp_c = exp_rate * total_windows
            # z-test on counts (Poisson approx)
            if exp_c > 0:
                z = (c - exp_c) / np.sqrt(exp_c)
                pval = 2 * (1 - norm.cdf(abs(z)))
            else:
                pval = np.nan
            n_sub = sum(1 for v in sub_cnt[w].values() if v >= 5)
            rows.append({"window_d": h, "sequence": w,
                         "count": c, "expected": float(exp_c),
                         "lift": float(c / exp_c) if exp_c > 0 else np.nan,
                         "p": float(pval), "n_subperiods": n_sub,
                         "n_events_total": int(c)})
    out = pd.DataFrame(rows)
    if len(out):
        q = _fdr(out["p"].to_numpy())
        out["q"] = q
        def _cls(r):
            if r["count"] >= MIN_PROMOTE_N and r["n_subperiods"] >= \
                    MIN_SUBPERIODS and r["q"] <= FDR_Q and r["lift"] > 1.0:
                return "COMMON_SEQUENCE"
            if r["count"] >= MIN_PROMOTE_N and r["n_subperiods"] >= 2:
                return "LOCAL_SEQUENCE"
            if r["count"] >= 20:
                return "RARE_SEQUENCE"
            return "NULL_SEQUENCE"
        out["status"] = out.apply(_cls, axis=1)
        out = out.sort_values("count", ascending=False).reset_index(drop=True)
    out.to_csv(OUT / "04_BROAD_SEQUENCE_ATLAS.csv", index=False)
    return out


# =========================================================================
# WS4: PARTIAL-ORDER / CONSTRAINT GRAPH (05_PARTIAL_ORDER_EDGES.csv,
#       06_CONSTRAINT_GRAPH.md)
# =========================================================================

def ws4_partial_order(dfw, seq_atlas):
    df = dfw.copy()
    atoms = _atom_series(df)
    names = list(atoms.columns)
    arr = atoms.to_numpy()
    n = len(df)
    h = 7
    from collections import defaultdict
    pair_first = defaultdict(lambda: {"A_first": 0, "B_first": 0,
                                     "same": 0, "subs": defaultdict(
                                         lambda: defaultdict(int))})
    subperiod = df["subperiod"].to_numpy()
    for i in range(n - h):
        w = arr[i + 1:i + 1 + h]
        fired = {}
        for k, name in enumerate(names):
            hits = np.where(w[:, k] > 0)[0]
            if len(hits):
                fired[name] = int(hits[0])
        sp = subperiod[i]
        fl = sorted(fired.items(), key=lambda x: x[1])
        if len(fl) < 2:
            continue
        order = [x[0] for x in fl]
        pos = {name: p for p, name in enumerate(order)}
        for a in range(len(order)):
            for b in range(a + 1, len(order)):
                na, nb = order[a], order[b]
                key = tuple(sorted([na, nb]))
                if fired[na] == fired[nb]:
                    pair_first[key]["same"] += 1
                    pair_first[key]["subs"][sp]["same"] += 1
                else:
                    pair_first[key]["A_first" if na < nb else "B_first"] += 1
                    pair_first[key]["subs"][sp]["A_first" if na < nb
                                            else "B_first"] += 1
    rows = []
    for (na, nb), d in pair_first.items():
        tot = d["A_first"] + d["B_first"] + d["same"]
        if tot < 30:
            continue
        p_ab = d["A_first"] / tot
        p_ba = d["B_first"] / tot
        p_same = d["same"] / tot
        n_sub = sum(1 for s in d["subs"].values()
                    if s["A_first"] + s["B_first"] + s["same"] >= 5)
        # stable ordering test: preferred direction consistent across
        # subperiods with >=5 obs
        stable = 0
        for s, sc in d["subs"].items():
            t = sc["A_first"] + sc["B_first"] + sc["same"]
            if t >= 5:
                if sc["A_first"] >= 0.6 * t:
                    stable += 1
                elif sc["B_first"] >= 0.6 * t:
                    stable -= 1
        # classify: preferred = direction of larger share
        pref = "A" if p_ab >= p_ba else "B"
        p_pref = max(p_ab, p_ba)
        if tot >= MIN_PROMOTE_N and n_sub >= MIN_SUBPERIODS and \
                p_pref >= 0.60 and abs(stable) >= MIN_SUBPERIODS:
            cls = "REQUIRED_ORDER"
        elif tot >= MIN_PROMOTE_N and p_pref >= 0.55:
            cls = "PREFERRED_ORDER"
        elif tot >= MIN_PROMOTE_N and p_pref <= 0.60 and \
                min(p_ab, p_ba) >= 0.20:
            cls = "EXCHANGEABLE"
        else:
            cls = "NO_ORDER"
        rows.append({"atom_a": na, "atom_b": nb, "n_both": tot,
                     "p_A_before_B": float(p_ab), "p_B_before_A": float(p_ba),
                     "p_same_window": float(p_same),
                     "preferred": pref, "preferred_p": float(p_pref),
                     "n_subperiods": n_sub,
                     "stable_direction_count": int(stable),
                     "edge_class": cls})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "05_PARTIAL_ORDER_EDGES.csv", index=False)

    # 06_CONSTRAINT_GRAPH.md
    req = out[out["edge_class"] == "REQUIRED_ORDER"].sort_values(
        "preferred_p", ascending=False)
    pref = out[out["edge_class"] == "PREFERRED_ORDER"].sort_values(
        "preferred_p", ascending=False)
    lines = [
        "# MECH-12 — CONSTRAINT GRAPH (06)",
        "",
        f"Built from WS4 partial-order analysis over a {h}D rolling window.",
        f"Edges: {len(out)} pairs with n>=30; "
        f"{len(req)} REQUIRED_ORDER; {len(pref)} PREFERRED_ORDER.",
        "",
        "## REQUIRED_ORDER edges (stable across >=3 subperiods, p_pref>=0.60)",
        "",
    ]
    for _, r in req.head(25).iterrows():
        lines.append(f"- {r['atom_a']} -> {r['atom_b']} "
                     f"(p={r['preferred_p']:.2f}, n={r['n_both']}, "
                     f"subperiods={r['n_subperiods']})")
    lines += ["", "## PREFERRED_ORDER edges (p_pref>=0.55)", ""]
    for _, r in pref.head(25).iterrows():
        lines.append(f"- {r['atom_a']} -> {r['atom_b']} "
                     f"(p={r['preferred_p']:.2f}, n={r['n_both']})")
    lines += ["", "## Notes", "",
              "- Cycles are preserved; no DAG forcing was applied.",
              "- EXCHANGEABLE pairs mean either order is nearly equally "
              "likely; NO_ORDER pairs lack stable direction.",
              "- Edges describe temporal precedence, not causality "
              "(causal level <= L2)."]
    (OUT / "06_CONSTRAINT_GRAPH.md").write_text("\n".join(lines) + "\n",
                                               encoding="utf-8")
    return out


# =========================================================================
# WS5: SEQUENCE PREFIX BRANCHING (07_SEQUENCE_PREFIX_BRANCHING.csv)
# =========================================================================

def ws5_prefix_branching(dfw):
    df = dfw.copy()
    atoms = _atom_series(df)
    names = list(atoms.columns)
    arr = atoms.to_numpy()
    n = len(df)
    h = 7
    from collections import defaultdict
    prefix_next = defaultdict(lambda: defaultdict(int))
    for i in range(n - h):
        w = arr[i + 1:i + 1 + h]
        fired = {}
        for k, name in enumerate(names):
            hits = np.where(w[:, k] > 0)[0]
            if len(hits):
                fired[name] = int(hits[0])
        if len(fired) < 2:
            continue
        order = sorted(fired.items(), key=lambda x: x[1])
        prefix = order[0][0]
        for j in range(1, len(order)):
            nxt = order[j][0]
            prefix_next[prefix][nxt] += 1
    rows = []
    for prefix, d in prefix_next.items():
        tot = sum(d.values())
        if tot < 30:
            continue
        ps = np.array([v / tot for v in d.values()])
        ent = float(-(ps * np.log2(ps)).sum())
        dom = float(ps.max())
        top = sorted(d.items(), key=lambda x: -x[1])[:5]
        rows.append({"prefix": prefix, "n_branches": len(d),
                     "n_events": tot, "branch_entropy": ent,
                     "dominant_share": dom,
                     "top_branches": ";".join(f"{k}:{v}" for k, v in top)})
    out = pd.DataFrame(rows).sort_values("n_events", ascending=False)
    out.to_csv(OUT / "07_SEQUENCE_PREFIX_BRANCHING.csv", index=False)
    return out


# =========================================================================
# WS6: CONSTRAINT-RESOLUTION ENTROPY (08_CONSTRAINT_RESOLUTION_ENTROPY.csv)
# =========================================================================

def ws6_constraint_entropy(dfw, seq_atlas, prefix_rows):
    df = dfw.copy()
    # Branch entropy of next-day cell transition by cell and age band
    df["next_cell"] = df["cell"].shift(-1)
    df["age_band"] = df["age_in_cell"].apply(_age_band)
    rows = []
    for cell in CELLS:
        for ab in [b[2] for b in AGE_BANDS]:
            sub = df[(df["cell"] == cell) & (df["age_band"] == ab)]
            sub = sub.dropna(subset=["next_cell"])
            if len(sub) < 30:
                continue
            vc = sub["next_cell"].value_counts(normalize=True)
            ent = float(-(vc * np.log2(vc)).sum())
            dom = float(vc.max())
            rows.append({"scope": "cell_age", "cell": cell, "age_band": ab,
                         "n": int(len(sub)), "branch_entropy": ent,
                         "dominant_share": dom})
    # depth-based: entropy of next atom given prefix length from WS5
    pr = prefix_rows
    if len(pr):
        # single-prefix entropy (depth 1) = branch_entropy above
        base_ent = float(np.nanmean(pr["branch_entropy"]))
        base_dom = float(np.nanmean(pr["dominant_share"]))
    else:
        base_ent, base_dom = np.nan, np.nan
    # check collapse: entropy vs prefix n (more common prefix -> narrower?)
    corr = np.nan
    if len(pr) >= 10:
        corr, _ = spearmanr(pr["n_events"], pr["branch_entropy"])
    if len(rows) and not np.isnan(base_ent):
        age_collapse = 0
        for cell in CELLS:
            g = [r for r in rows if r["cell"] == cell]
            if len(g) >= 3:
                ents = [r["branch_entropy"] for r in g]
                if ents[-1] < ents[0] * 0.85:
                    age_collapse += 1
        verdict = ("ENTROPY_COLLAPSE" if age_collapse >= 3
                   else "LOCAL_ENTROPY_COLLAPSE" if age_collapse >= 1
                   else "NO_STABLE_COLLAPSE")
    else:
        verdict = "INCONCLUSIVE"
    summary = pd.DataFrame([{
        "verdict": verdict,
        "mean_prefix_entropy": float(base_ent) if not np.isnan(base_ent)
        else np.nan,
        "mean_prefix_dominant_share": float(base_dom) if not np.isnan(base_dom)
        else np.nan,
        "entropy_vs_frequency_spearman": float(corr) if not np.isnan(corr)
        else np.nan,
        "cells_with_age_collapse": int(age_collapse) if
        "age_collapse" in dir() else 0}])
    full = pd.concat([pd.DataFrame(rows), summary], ignore_index=True)
    full.to_csv(OUT / "08_CONSTRAINT_RESOLUTION_ENTROPY.csv", index=False)
    return full, verdict
