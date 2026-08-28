from _m15base import *
from _m15base import _cache_step, _age_band, _fdr, _fmt, _entropy, \
    _subperiod_split, MC, cell_stats


def _unresolved_ratios(e):
    init = e["ret_1d"].abs().replace(0, np.nan)
    out = {}
    for col, hc in [("fwd1_cum", 1), ("fwd3_cum", 3), ("fwd7_cum", 7),
                    ("fwd14_cum", 14), ("fwd30_cum", 30)]:
        if col in e.columns:
            out[f"unresolved_{hc}d"] = (e[col].abs() / init).clip(upper=10.0)
        else:
            out[f"unresolved_{hc}d"] = np.nan
    return out


# =========================================================================
# WS21: RESIDUAL DISTURBANCE OVERLAY (22_RESIDUAL_DISTURBANCE_OVERLAY.csv)
# =========================================================================
def ws21_residual_disturbance_overlay(df, ev):
    e = ev.copy()
    e["d"] = pd.to_datetime(e["historical_date"]).dt.normalize()
    e = e.dropna(subset=["ret_1d"])
    r = _unresolved_ratios(e)
    for k, v in r.items():
        e[k] = v
    dmap = df.set_index("d")["mcell"]
    e["mcell"] = e["d"].map(dmap)
    rows = []
    for mc in MC:
        g = e[e["mcell"] == mc]
        if len(g) < 100:
            rows.append({"mcell": mc, "n_events": int(len(g)),
                         "verdict": "DATA_LIMITED"})
            continue
        row = {"mcell": mc, "n_events": int(len(g)),
               "median_initial_abs_move": float(g["ret_1d"].abs().median())}
        for hc in [1, 3, 7, 14, 30]:
            c = g[f"unresolved_{hc}d"]
            row[f"median_residual_{hc}d"] = float(c.median()) if \
                c.notna().any() else np.nan
        row["verdict"] = "RESIDUAL_OVERLAY_MAPPED"
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "22_RESIDUAL_DISTURBANCE_OVERLAY.csv", index=False)
    return out


# =========================================================================
# WS22: TRANSITION MATRIX (23_CELL_TRANSITION_MATRIX.csv)
# =========================================================================
def ws22_transition_matrix(df):
    g = df.dropna(subset=["mcell", "mcell_next"]).copy()
    g = g[g["mcell"].isin(MC) & g["mcell_next"].isin(MC)]
    rows = []
    for h, col in [(1, "mcell_next")]:
        ct = pd.crosstab(g["mcell"], g[col])
        for a in MC:
            if a not in ct.index:
                continue
            row = ct.loc[a] if a in ct.index else pd.Series(dtype=int)
            total = int(row.sum())
            if total == 0:
                continue
            for b in MC:
                n = int(row[b]) if b in row.index else 0
                rows.append({"from": a, "to": b, "horizon": h,
                             "n": n, "prob": float(n / total)})
    # t+3 and t+7 where support allows (shifted mcell)
    for h, col in [(3, "mcell_p3"), (7, "mcell_p7")]:
        g[col] = g["mcell"].shift(-h)
        sub = g.dropna(subset=[col]).copy()
        sub = sub[sub[col].isin(MC)]
        if len(sub) < 500:
            continue
        ct = pd.crosstab(sub["mcell"], sub[col])
        for a in MC:
            if a not in ct.index:
                continue
            row = ct.loc[a]
            total = int(row.sum())
            if total == 0:
                continue
            for b in MC:
                n = int(row[b]) if b in row.index else 0
                rows.append({"from": a, "to": b, "horizon": h,
                             "n": n, "prob": float(n / total)})
    out = pd.DataFrame(rows)
    # per-cell transition entropy + self-transition share, attached to every
    # (from, to, horizon) row so the CSV carries BOTH the full 16x16 matrix
    # and the source-cell summary
    summ = []
    for h in [1, 3, 7]:
        sub = out[out["horizon"] == h]
        for a in MC:
            r = sub[sub["from"] == a]
            if len(r) == 0 or r["n"].sum() < 50:
                continue
            p = r["prob"].to_numpy()
            ent = float(-(p[p > 0] * np.log2(p[p > 0])).sum())
            selfp = float(r.loc[r["to"] == a, "prob"].iloc[0]) if \
                (r["to"] == a).any() else 0.0
            summ.append({"from": a, "horizon": h,
                         "transition_entropy": ent,
                         "self_transition_share": selfp,
                         "dominant_exit": str(r.sort_values("n",
                             ascending=False).iloc[0]["to"])})
    s = pd.DataFrame(summ)
    s["verdict"] = "TRANSITION_MATRIX_BUILT"
    out = out.merge(s.drop(columns=["verdict"]), on=["from", "horizon"],
                    how="left")
    out["verdict"] = "TRANSITION_MATRIX_BUILT"
    out.to_csv(OUT / "23_CELL_TRANSITION_MATRIX.csv", index=False)
    return out, s


# =========================================================================
# WS23: TEMPORAL HIGHWAY MAP (24_TEMPORAL_HIGHWAY_MAP.csv)
# =========================================================================
def ws23_temporal_highway_map(out):
    rows = []
    t1 = out[out["horizon"] == 1]
    for a in MC:
        r = t1[t1["from"] == a]
        if len(r) == 0 or r["n"].sum() < 50:
            rows.append({"from": a, "verdict": "DATA_LIMITED"})
            continue
        total = int(r["n"].sum())
        exits = r[r["to"] != a]
        exits = exits.sort_values("n", ascending=False)
        if len(exits) == 0:
            rows.append({"from": a, "verdict": "NO_STABLE_ROUTE"})
            continue
        top = exits.iloc[0]
        top_share = float(top["n"] / total)
        n_common = int((r["n"] >= 0.10 * total).sum())
        if top_share >= 0.25 and n_common <= 2:
            lab = "LOCAL_HIGHWAY"
        elif top_share >= 0.15:
            lab = "COMMON_EXIT"
        elif top_share < 0.05:
            lab = "RARE_EXIT"
        else:
            lab = "NO_STABLE_ROUTE"
        rows.append({"from": a, "n": total,
                     "top_exit": str(top["to"]),
                     "top_exit_share": top_share,
                     "n_common_exits_ge10pct": n_common,
                     "verdict": lab})
    out2 = pd.DataFrame(rows)
    out2.to_csv(OUT / "24_TEMPORAL_HIGHWAY_MAP.csv", index=False)
    return out2


# =========================================================================
# WS24: MATRIX CELL BIRTH / DEATH (25_CELL_ENTRY_SURVIVAL_EXIT.csv)
# =========================================================================
def ws24_cell_entry_survival_exit(df):
    g = df.dropna(subset=["mcell"]).copy()
    chg = (g["mcell"] != g["mcell"].shift(1)).to_numpy()
    ep = np.cumsum(chg)
    ep_first = g.groupby(ep)["mcell"].first()
    ep_last = g.groupby(ep)["mcell"].last()
    ep_len = g.groupby(ep).size()
    rows = []
    for mc in MC:
        eps = [e for e, c in ep_first.items() if c == mc]
        if len(eps) < 30:
            rows.append({"mcell": mc, "n_episodes": int(len(eps)),
                         "verdict": "DATA_LIMITED"})
            continue
        dwell = ep_len.loc[eps]
        exits = ep_last.loc[eps]
        # entry sources: previous episode's cell
        sources = []
        for e in eps:
            prev = ep_first.loc[e - 1] if (e - 1) in ep_first.index else None
            sources.append(prev)
        src_vc = pd.Series([s for s in sources if s is not None])
        # entropy change while inside: mean fbe inside vs global mean
        fbe_in = g[g["mcell"] == mc]["fbe"]
        global_fbe = df["fbe"].mean()
        rows.append({"mcell": mc, "n_episodes": int(len(eps)),
                     "median_dwell_days": float(dwell.median()),
                     "mean_dwell_days": float(dwell.mean()),
                     "dominant_exit": str(exits.mode().iloc[0]),
                     "exit_entropy": float(_entropy(exits)) if
                     exits.nunique() >= 2 else np.nan,
                     "dominant_entry_source": str(src_vc.mode().iloc[0])
                     if len(src_vc) else "",
                     "entry_source_entropy": float(_entropy(src_vc)) if
                     len(src_vc) >= 2 and src_vc.nunique() >= 2 else np.nan,
                     "mean_fbe_inside": float(fbe_in.mean()) if
                     fbe_in.notna().any() else np.nan,
                     "global_mean_fbe": float(global_fbe),
                     "n_subperiods": int(g[g["mcell"] == mc]["subperiod"]
                                          .replace("UNKNOWN", np.nan)
                                          .dropna().nunique()),
                     "verdict": "ENTRY_SURVIVAL_EXIT_MAPPED"})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "25_CELL_ENTRY_SURVIVAL_EXIT.csv", index=False)
    return out
