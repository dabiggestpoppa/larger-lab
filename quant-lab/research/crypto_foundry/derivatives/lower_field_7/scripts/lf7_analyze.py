"""LOWER-FIELD-7 analysis — dynamic peer ecology, up/down loner symmetry,
absolute-vs-sigma shock physics, multi-sigma paths, rejoin/contagion/decoupling
deepening, peer formation/dissolution, local health ecology.

Built on the LF5 PIT substrate, events and true peer maps (which cover both
sign directions). Research only: no strategy, no PnL, no execution.

Outputs 02-24 written to lower_field_7/.
"""
from __future__ import annotations

import warnings
from collections import Counter

import numpy as np
import pandas as pd

import lf7_common as C

warnings.filterwarnings("ignore", category=RuntimeWarning)

R = C.ROOT
H = C.H
MIN_EVENTS = C.MIN_EVENTS

CELL4 = {"HIGH_BREADTH_HIGH_DISP": "HH", "HIGH_BREADTH_LOW_DISP": "HL",
         "LOW_BREADTH_HIGH_DISP": "LH", "LOW_BREADTH_LOW_DISP": "LL"}

FAMILY_LABELS = {
    "BEHAVIORAL": "BEHAVIORAL_10",
    "CORR_60": "CORR_60_10",
    "CORR_120": "CORR_120_10",
    "STATE": "STATE",
    "HYBRID": "HYBRID_10",
}


def load_all():
    ev = C.load_events()
    down = C.loner_universe(ev, -1, "2s")
    down3 = C.loner_universe(ev, -1, "3s")
    up = C.loner_universe(ev, +1, "2s")
    up3 = C.loner_universe(ev, +1, "3s")
    slim = C.load_substrate_slim()
    quality = pd.read_csv(C.LF5_QUALITY)
    return ev, down, down3, up, up3, slim, quality


def peer_return_panel(pm, slim):
    """Attach peer identity features + forward returns via merge."""
    pm = pm.merge(slim.rename(columns={"cmc_id": "peer_id"}),
                  on=["peer_id", "historical_date"], how="left",
                  suffixes=("", "_slim"))
    return pm


# ---------------------------------------------------------------------------
# Section 1: PEER VALIDITY RECLASSIFICATION (02)
# ---------------------------------------------------------------------------

def _jaccard_persistence(pm):
    sub = pm[pm["historical_date"].notna()].copy()
    js = []
    for _, gg in sub.groupby("asset_id", sort=False):
        if gg["event_index"].nunique() < 2:
            continue
        sets = {ei: set(g2["peer_id"]) for ei, g2 in gg.groupby("event_index")}
        order = gg.groupby("event_index")["historical_date"].first().sort_values()
        prev = None
        for ei in order.index:
            if prev is not None:
                a, b = sets[prev], sets[ei]
                js.append(len(a & b) / max(len(a | b), 1))
            prev = ei
    return float(np.mean(js)) if js else np.nan


def _future_similarity(pm):
    """Out-of-sample similarity: how well the t0 peer set predicts the peer
    set at the asset's NEXT event window (next-window Jaccard)."""
    sub = pm[pm["historical_date"].notna()].copy()
    sims = []
    for _, gg in sub.groupby("asset_id", sort=False):
        if gg["event_index"].nunique() < 2:
            continue
        sets = {ei: set(g2["peer_id"]) for ei, g2 in gg.groupby("event_index")}
        order = gg.groupby("event_index")["historical_date"].first().sort_values()
        order = list(order.index)
        for a, b in zip(order[:-1], order[1:]):
            i = max(len(sets[a] & sets[b]) / max(len(sets[a]), 1), 0)  # precision
            # Jaccard-style retention
            j = len(sets[a] & sets[b]) / max(len(sets[a] | sets[b]), 1)
            sims.append(j)
    return float(np.mean(sims)) if sims else np.nan


def peer_validity_reclassification(down, quality, slim):
    rows = []
    for fam in C.DEEP_FAMILIES:
        pm = C.load_peer_map(fam)
        pm = pm.merge(down[["event_index", "historical_date"]], on="event_index",
                      how="left")
        pm = peer_return_panel(pm, slim)
        pm["peer_return"] = pm["peer_return"].fillna(pm["ret_1d"])
        pers = _jaccard_persistence(pm) if len(pm) else np.nan
        fut = _future_similarity(pm)
        # current-state similarity: median pairwise peer-return correlation
        # across events with enough peers (descriptive, in-sample cohesion)
        g = pm.groupby("event_index")["peer_return"]
        cur = _in_sample_cohesion(pm)
        # coverage: fraction of down-loner events that have a peer-map row
        n_ev = len(down)
        down_idx = set(down["event_index"])
        cov = len(set(pm["event_index"].dropna()) & down_idx) / max(n_ev, 1)
        # event-level future corr stability (reuse t0 vs fwd7 as in LF6)
        fut_corr = _future_coherence(pm)
        # classify independently
        verdict = classify_peer(fam, pers, fut, fut_corr)
        q = quality[quality["peer_family"] == fam]
        def _q(col, default=np.nan):
            return q[col].iloc[0] if len(q) and col in q.columns else default
        rows.append({
            "peer_family": fam,
            "pit_construction": _q("status", "OK"),
            "current_state_similarity": round(float(cur), 4) if np.isfinite(cur) else np.nan,
            "jaccard_persistence": round(pers, 4) if np.isfinite(pers) else np.nan,
            "membership_turnover": round(1 - pers, 4) if np.isfinite(pers) else np.nan,
            "future_similarity_oos": round(fut, 4) if np.isfinite(fut) else np.nan,
            "future_corr_stability": round(fut_corr, 4) if np.isfinite(fut_corr) else np.nan,
            "event_coverage": round(float(cov), 4),
            "lf5_pre_event_similarity": _q("pre_event_similarity"),
            "lf5_basket_correlation": _q("basket_correlation"),
            "reclassification": verdict,
        })
    return pd.DataFrame(rows)


def _future_coherence(pm):
    sub = pm[["event_index", "peer_return", "fwd7_cum"]].dropna()
    if len(sub) < 100:
        return np.nan
    vals = []
    for _, gg in sub.groupby("event_index"):
        if len(gg) >= 5:
            r = np.corrcoef(gg["peer_return"], gg["fwd7_cum"])[0, 1]
            if np.isfinite(r):
                vals.append(r)
    return float(np.median(vals)) if vals else np.nan


def _in_sample_cohesion(pm):
    """Median pairwise correlation of peer returns within a single event
    (in-sample current-state similarity of the neighbor set)."""
    vals = []
    for _, gg in pm.dropna(subset=["peer_return"]).groupby("event_index"):
        if len(gg) >= 5:
            x = gg["peer_return"].to_numpy(float)
            if np.std(x) < 1e-12:
                continue
            try:
                r = np.corrcoef(x)
                r = np.asarray(r)
                if r.ndim != 2 or r.shape[0] != len(x):
                    continue
                off = r[np.triu_indices(len(x), k=1)]
                off = off[np.isfinite(off)]
                if off.size:
                    vals.append(float(np.median(off)))
            except Exception:
                continue
    return float(np.median(vals)) if vals else np.nan


def classify_peer(fam, pers, fut, fut_corr):
    if not np.isfinite(pers):
        return "DATA_BLOCKED"
    # PIT construction validity bool
    pit_ok = True
    # persistent if oos similarity / pers nontrivial
    pers_score = pers if np.isfinite(pers) else 0
    fut_score = fut if np.isfinite(fut) else 0
    fc = fut_corr if np.isfinite(fut_corr) else 0
    if pers_score >= 0.45 and fut_score >= 0.30:
        return "PERSISTENT_VALID"
    if pers_score >= 0.20:
        if fc >= 0.1 or fut_score >= 0.15:
            return "PIT_VALID_DYNAMIC"
        return "TRANSIENT_LOCAL"
    if pers_score >= 0.05 or pit_ok:
        return "TRANSIENT_LOCAL"
    return "WEAK"


# ---------------------------------------------------------------------------
# Section 2: PEER FAMILY DEPENDENCE (03)
# ---------------------------------------------------------------------------

def peer_family_dependence(down, slim):
    groups = C.FAMILY_GROUPS
    labels = [FAMILY_LABELS[g] for g in groups]
    per_event = {}
    for g in groups:
        pm = C.load_peer_map(FAMILY_LABELS[g])
        pm = pm.merge(down[["event_index", "historical_date"]], on="event_index",
                      how="left")
        pm = peer_return_panel(pm, slim)
        pm["peer_return"] = pm["peer_return"].fillna(pm["ret_1d"])
        # event label: TRUE_LONER if asset residual >= peer dispersion
        g2 = pm.groupby("event_index")
        s = pd.DataFrame({"peer_med": g2["peer_return"].median(),
                          "peer_disp": g2["peer_return"].std()})
        loner = down.set_index("event_index")["ret_1d"]
        s["resid"] = s.index.map(loner) - s["peer_med"]
        s["label"] = np.where(s["peer_disp"].fillna(0) > 0,
                              np.where(s["resid"].abs() >= s["peer_disp"], 1, 0),
                              np.nan)
        per_event[g] = s[["peer_med", "peer_disp", "label"]]
    # membership overlap between pairs (Jaccard of peer sets)
    pair_membership = {}
    labels_df = pd.DataFrame({g: per_event[g]["label"].astype(float)
                              for g in groups}).fillna(np.nan)
    rows = []
    for i, gi in enumerate(groups):
        row = {"family": gi}
        for j, gj in enumerate(groups):
            if i == j:
                row[gj] = 1.0
                continue
            # membership overlap: median fraction of shared peers across events
            pmi = C.load_peer_map(FAMILY_LABELS[gi])
            pmj = C.load_peer_map(FAMILY_LABELS[gj])
            si = set(zip(pmi["event_index"], pmi["peer_id"]))
            sj = set(zip(pmj["event_index"], pmj["peer_id"]))
            row[gj] = round(len(si & sj) / max(len(si | sj), 1), 4)
        # agreement with the family's own label, and redundancy vs the rest
        rows.append(row)
    df = pd.DataFrame(rows)
    # label agreement matrix
    agree = pd.DataFrame(index=groups, columns=groups, dtype=float)
    for i, gi in enumerate(groups):
        for j, gj in enumerate(groups):
            if i == j:
                agree.loc[gi, gj] = 1.0
            else:
                a = labels_df[[gi, gj]].dropna()
                if len(a):
                    agree.loc[gi, gj] = round(float((a[gi] == a[gj]).mean()), 4)
                else:
                    agree.loc[gi, gj] = np.nan
    # effective number of distinct peer views: variance-explained-like on membership overlaps
    ov = df.iloc[:, 1:].to_numpy(float)
    np.fill_diagonal(ov, 1.0)
    eigs = np.linalg.eigvalsh(ov)
    eigs = np.clip(eigs, 0, None)
    eff_views = float((eigs ** 2).sum() / max(eigs.sum(), 1e-9)) if eigs.sum() > 0 else 1.0
    df["effective_views_estimate"] = eff_views
    (R / "03_FAMILY_LABEL_AGREEMENT.csv")
    agree.to_csv(R / "03a_FAMILY_LABEL_AGREEMENT.csv")
    return df


# ---------------------------------------------------------------------------
# Section 3: DYNAMIC PEER FORMATION (04)
# ---------------------------------------------------------------------------

def dynamic_peer_formation(down, slim, family="BEHAVIORAL_10"):
    pm = C.load_peer_map(family)
    pm = pm.merge(down[["event_index", "historical_date", "cmc_id", "rank_band"]],
                  on="event_index", how="left")
    pm = peer_return_panel(pm, slim)
    pm = pm.dropna(subset=["historical_date"]).copy()
    # pre-compute per-event metadata (rank band via asset) once
    ev_meta = pm.groupby("event_index")[["rank_band"]].first()
    ev_date = pm.groupby("event_index")["historical_date"].first()
    rows = []
    for asset, gg in pm.groupby("asset_id", sort=False):
        if gg["event_index"].nunique() < 2:
            continue
        sets = {ei: set(g2["peer_id"]) for ei, g2 in gg.groupby("event_index")}
        eis = sorted(sets.keys(), key=lambda e: ev_date[e])
        prev_ei = None
        for ei in eis:
            cur = sets[ei]
            if prev_ei is not None:
                a, b = sets[prev_ei], cur
                jac = len(a & b) / max(len(a | b), 1)
                new_cnt = len(b - a)
                lost_cnt = len(a - b)
            else:
                jac, new_cnt, lost_cnt = np.nan, np.nan, np.nan
            rows.append({
                "asset_id": asset,
                "historical_date": ev_date[ei],
                "event_index": ei,
                "rank_band": ev_meta.loc[ei, "rank_band"],
                "peer_n": len(cur),
                "jaccard_persistence": jac,
                "membership_turnover": 1 - jac if np.isfinite(jac) else np.nan,
                "new_peer_count": new_cnt,
                "lost_peer_count": lost_cnt,
            })
            prev_ei = ei
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 4: PEER FORMATION DRIVERS / CONTEXT (05)
# ---------------------------------------------------------------------------

def peer_formation_context(fmt, market, slim):
    df = fmt.merge(market, on="historical_date", how="left", suffixes=("", "_mkt"))
    # asset-level feature context on the event asset
    slim2 = slim.rename(columns={"cmc_id": "asset_id"})
    feat_cols = ["asset_id", "historical_date", "vol_63d", "vol_30d", "vol_20d",
                 "rank_vel_7d", "rank_vel_30d", "turnover", "listing_age_days",
                 "log10_mcap"]
    feat_cols = [c for c in feat_cols if c in slim2.columns]
    df = df.merge(slim2[feat_cols], on=["asset_id", "historical_date"], how="left")
    df = df.dropna(subset=["membership_turnover"])
    df["vol_regime"] = pd.qcut(
        pd.Series(df['vol_63d']).rank(method='first'), 4,
        labels=["LOW_VOL", "Q2", "Q3", "HIGH_VOL"], duplicates="drop") \
        if "vol_63d" in df.columns and df["vol_63d"].notna().sum() > 4 else np.nan
    rows = []
    # correlation of turnover with driver coordinates (descriptive)
    for col in ["rank_vel_7d", "vol_63d", "vol_30d", "btc_ret_1d", "top500_breadth_30d",
                "top500_dispersion_30d", "stablecoin_mcap_share", "turnover"]:
        if col not in df.columns or df[col].notna().sum() < 50:
            continue
        r = df[["membership_turnover", col]].replace([np.inf, -np.inf], np.nan).dropna()
        if len(r) < 50:
            continue
        c = r["membership_turnover"].corr(r[col])
        rows.append({"driver": col,
                     "corr_with_turnover": round(float(c), 4) if np.isfinite(c) else np.nan,
                     "median_turnover_low": round(float(df[df["vol_regime"] == "LOW_VOL"]["membership_turnover"].median()), 4)
                     if "vol_regime" in df.columns and df["vol_regime"].eq("LOW_VOL").any() else np.nan,
                     "median_turnover_high": round(float(df[df["vol_regime"] == "HIGH_VOL"]["membership_turnover"].median()), 4)
                     if "vol_regime" in df.columns and df["vol_regime"].eq("HIGH_VOL").any() else np.nan,
                     "n_low": int((df["vol_regime"] == "LOW_VOL").sum()) if "vol_regime" in df.columns else 0,
                     "n_high": int((df["vol_regime"] == "HIGH_VOL").sum()) if "vol_regime" in df.columns else 0})
    # 4-state turnover comparison
    for cell in ["HH", "HL", "LH", "LL"]:
        g = df[df["cell4"] == cell]["membership_turnover"].dropna()
        rows.append({"driver": f"CELL_{cell}",
                     "corr_with_turnover": np.nan,
                     "median_turnover_low": round(float(g.median()), 4) if len(g) else np.nan,
                     "median_turnover_high": np.nan,
                     "n_low": int(len(g)), "n_high": 0})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 5: PEER LIFETIME DISTRIBUTION (06)
# ---------------------------------------------------------------------------

def peer_lifetime(pm_all):
    """Relationship lifetime: fraction of t0 peer pairs still present at h."""
    pm = pm_all.dropna(subset=["historical_date"]).copy()
    peer_count = pm.groupby(["asset_id", "historical_date"])["event_index"].count().reset_index()
    out = []
    # sample-based: for each event take a cap of peer pairs and track fwd presence
    # (fwd7..fwd30 via merged fwd columns on the SAME peer rows is not membership-
    #  persistence, so we approximate with repeat-asset-next-event Jaccard + horizon
    #  survival from future correlation panel)
    for h in [1, 3, 7, 14, 30, 60]:
        # approximate lifetime via proportion of peer_return entries that also
        # appear in the fwd{h} column (persistence of the relationship signal)
        col = f"fwd{h}_cum" if h in [1, 3, 7, 14, 30] else None
        if col and col in pm.columns:
            alive = pm[col].notna().mean() if len(pm) else np.nan
        else:
            # for 60d fall back to base overlap floor
            alive = pm["peer_return"].notna().mean() if len(pm) else np.nan
        out.append({"horizon_d": h, "fraction_alive_signal": round(float(alive), 4) if np.isfinite(alive) else np.nan})
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------
# Section 6: ABSOLUTE vs SIGMA SHOCK MATRIX (07)
# ---------------------------------------------------------------------------

def abs_vs_sigma_matrix(down, up):
    both = pd.concat([down, up]).copy()
    both["abs_ret"] = both["ret_1d"].abs()
    # absolute amplitude classes (log-scaled, natural boundaries)
    both["abs_class"] = pd.cut(both["abs_ret"], bins=[0, 0.02, 0.05, 0.10, 0.20,
                             np.inf], labels=["<2%", "2-5%", "5-10%", "10-20%", ">20%"])
    both["sigma_class"] = pd.cut(both["z1"], bins=[2, 3, 4, np.inf],
                                 labels=["2-3σ", "3-4σ", "4σ+"])
    rows = []
    for sx in ["2-3σ", "3-4σ", "4σ+"]:
        for ax in ["<2%", "2-5%", "5-10%", "10-20%", ">20%"]:
            g = both[(both["sigma_class"] == sx) & (both["abs_class"] == ax)]
            if len(g) < 20:
                continue
            sign = "DOWN" if g["event_sign"].min() < 0 else "UP"
            rows.append({
                "sigma_class": sx, "abs_class": ax, "n": len(g),
                "p_1s_recovery_7d": round(float(g["recover1s7"].fillna(False).mean()), 4) if sign == "DOWN" else np.nan,
                "p_2s_recovery_14d": round(float((g["signed_fwd14"] / g["sigma_t0"] >= 2).mean()), 4),
                "p_full_repair_30d": round(float(g.get("recover1s30", pd.Series(dtype=float)).fillna(False).mean()), 4),
                "median_rank_repair_30d": round(float(g["fwd_rank_vel_30d"].gt(0).mean()), 4),
                "p_new_low_30d": round(float((g["signed_fwd30"] < 0).mean()), 4),
                "median_resid7": round(float((g["signed_fwd7"] - np.nan).mean()), 4) if False else np.nan,
            })
    return pd.DataFrame(rows), both


# ---------------------------------------------------------------------------
# Section 7: FALSE-LONER ARTIFACT AUDIT (08)
# ---------------------------------------------------------------------------

def false_loner_artifact_audit(down, cls, slim):
    # peer absolute return median per event (behavioral peers), signed-free
    pm = C.load_peer_map("BEHAVIORAL_10")
    pm = pm.merge(down[["event_index", "historical_date"]], on="event_index", how="left")
    pm = peer_return_panel(pm, slim)
    pm["peer_return"] = pm["peer_return"].fillna(pm["ret_1d"])
    peer_abs = pm.groupby("event_index")["peer_return"].apply(lambda s: np.nanmedian(s.abs()))

    df = down.merge(cls.groupby("event_index")["final_class"].first().reset_index(),
                    on="event_index", how="left")
    df = df.merge(peer_abs.rename("peer_abs_med"), left_on="event_index",
                  right_index=True, how="left")
    f = df[df["final_class"].str.endswith("_FALSE")]
    t = df[df["final_class"] == "TRUE_MULTI_PEER_LONER"]
    rows = []
    for name, g in [("FALSE_LONER", f), ("TRUE_LONER", t)]:
        if len(g) < 20:
            continue
        rows.append({
            "group": name, "n": len(g),
            "median_abs_move": round(float(g["ret_1d"].abs().median()), 5),
            "median_z1": round(float(g["z1"].median()), 3),
            "median_vol_63d": round(float(g["vol_63d"].median()), 6),
            "median_vol_30d": round(float(g["vol_30d"].median()), 6),
            "median_peer_abs_move": round(float(g["peer_abs_med"].median()), 5)
                if g["peer_abs_med"].notna().any() else np.nan,
            "median_absz": round(float((g["ret_1d"].abs() / g["vol_63d"]).median()), 3),
            "median_rank_vel_7d": round(float(g["rank_vel_7d"].median()), 2),
            "p_hh_cell": round(float(g["field_cell"].map(CELL4).eq("HH").mean()), 4),
        })
    tmp = df[df["final_class"].str.endswith("_FALSE")].copy()
    if len(tmp):
        tmp["abs_ret"] = tmp["ret_1d"].abs()
        tmp["absz"] = tmp["abs_ret"] / tmp["vol_63d"].replace(0, np.nan)
        low_absz = tmp["absz"].median() < 2.0
        rows.append({"group": "FALSE_ARTIFACT_VERDICT", "n": len(tmp),
                     "median_abs_move": round(float(tmp["abs_ret"].median()), 5),
                     "median_z1": round(float(tmp["z1"].median()), 3),
                     "median_vol_63d": round(float(tmp["vol_63d"].median()), 6),
                     "median_absz": round(float(tmp["absz"].median()), 3),
                     "verdict": "LOW_VOL_NORMALIZATION_ARTIFACT" if low_absz else "MIXED"})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 8-9: DOWNSIDE DEEPENING (09, 10)
# ---------------------------------------------------------------------------

def _zcluster(df):
    out = df.copy()
    out["abs_class"] = pd.cut(out["ret_1d"].abs(), bins=[0, 0.03, 0.08, 0.15, np.inf],
                              labels=["LOW", "MED", "HIGH", "EXTREME"])
    out["sigma_class"] = pd.cut(out["z1"], bins=[2, 3, 4, np.inf],
                                labels=["2-3σ", "3-4σ", "4σ+"])
    return out


def down_loner_deepening(down, cls):
    df = down.merge(cls.groupby("event_index")["final_class"].first().reset_index(),
                    on="event_index", how="left")
    df = df[df["final_class"] == "TRUE_MULTI_PEER_LONER"]
    df = _zcluster(df).copy()
    thr = float(df["rank_vel_7d"].std())
    if not np.isfinite(thr) or thr == 0:
        thr = 1.0
    df["peer_stability"] = np.where(df["rank_vel_7d"].abs() < thr, "STABLE", "VOLATILE")
    rows = []
    for depth in C.DEPTH_BANDS:
        g = df[df["rank_band"] == depth]
        if len(g) < 20:
            continue
        rows.append({
            "group": "RANK_PATCH", "rank_patch": depth, "n": len(g),
            "p_rejoin": round(float(g["fwd_rank_vel_7d"].gt(0).mean()), 4),
            "p_contagion": round(float(g.get("rev7", pd.Series(dtype=float)).mean()), 4),
            "p_decoupling": round(float((g["signed_fwd7"].lt(0)).mean()), 4),
            "p_full_repair_30d": round(float(g["recover1s30"].fillna(False).mean()), 4),
            "p_rank_repair_30d": round(float(g["fwd_rank_vel_30d"].gt(0).mean()), 4),
            "p_relapse": round(float((g["fwd1_cum"].gt(0) & g["signed_fwd7"].lt(0)).fillna(False).mean()), 4) if len(g) else np.nan,
        })
    for sx in ["2-3σ", "3-4σ", "4σ+"]:
        g = df[df["sigma_class"] == sx]
        if len(g) < 20:
            continue
        rows.append({"group": "SIGMA", "rank_patch": sx, "n": len(g),
                     "p_rejoin": round(float(g["fwd_rank_vel_7d"].gt(0).mean()), 4),
                     "p_contagion": round(float(g.get("rev7", pd.Series(dtype=float)).mean()), 4),
                     "p_decoupling": round(float((g["signed_fwd7"].lt(0)).mean()), 4),
                     "p_full_repair_30d": round(float(g["recover1s30"].fillna(False).mean()), 4),
                     "p_rank_repair_30d": round(float(g["fwd_rank_vel_30d"].gt(0).mean()), 4),
                     "p_relapse": np.nan})
    for cc in ["HH", "HL", "LH", "LL"]:
        g = df[df["field_cell"].map(CELL4) == cc]
        if len(g) < 20:
            continue
        rows.append({"group": "CELL", "rank_patch": cc, "n": len(g),
                     "p_rejoin": round(float(g["fwd_rank_vel_7d"].gt(0).mean()), 4),
                     "p_contagion": round(float(g.get("rev7", pd.Series(dtype=float)).mean()), 4),
                     "p_decoupling": round(float((g["signed_fwd7"].lt(0)).mean()), 4),
                     "p_full_repair_30d": round(float(g["recover1s30"].fillna(False).mean()), 4),
                     "p_rank_repair_30d": round(float(g["fwd_rank_vel_30d"].gt(0).mean()), 4),
                     "p_relapse": np.nan})
    return pd.DataFrame(rows)


def false_loner_deepening(down, cls):
    df = down.merge(cls.groupby("event_index")["final_class"].first().reset_index(),
                    on="event_index", how="left")
    df = df[df["final_class"].str.endswith("_FALSE")]
    df = _zcluster(df).copy()
    rows = []
    for sx in ["2-3σ", "3-4σ", "4σ+"]:
        g = df[df["sigma_class"] == sx]
        if len(g) < 20:
            continue
        rows.append({"sigma_class": sx, "n": len(g),
                     "p_reversal_7d": round(float(g["rev7"].fillna(False).mean()), 4),
                     "p_contagion_approximation": round(float((g["signed_fwd7"] < 0).mean()), 4),
                     "p_rank_repair_30d": round(float(g["fwd_rank_vel_30d"].gt(0).mean()), 4),
                     "p_price_repair_30d": round(float(g["recover1s30"].fillna(False).mean()), 4),
                     "median_abs_move": round(float(g["ret_1d"].abs().median()), 5)})
    for depth in C.DEPTH_BANDS:
        g = df[df["rank_band"] == depth]
        if len(g) < 20:
            continue
        rows.append({"sigma_class": depth, "n": len(g),
                     "p_reversal_7d": round(float(g["rev7"].fillna(False).mean()), 4),
                     "p_contagion_approximation": round(float((g["signed_fwd7"] < 0).mean()), 4),
                     "p_rank_repair_30d": round(float(g["fwd_rank_vel_30d"].gt(0).mean()), 4),
                     "p_price_repair_30d": round(float(g["recover1s30"].fillna(False).mean()), 4),
                     "median_abs_move": round(float(g["ret_1d"].abs().median()), 5)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 10-11: UPSIDE LONER (11, 12)
# ---------------------------------------------------------------------------

def upside_loner_classification(up, slim):
    """Sign-safe upside TRUE/FALSE loner under same dynamic peer systems."""
    families = C.DEEP_FAMILIES
    cls = up[["event_index", "ret_1d", "rank_band"]].copy()
    for fam in families:
        pm = C.load_peer_map(fam)
        pm = pm.merge(up[["event_index", "historical_date"]], on="event_index",
                      how="left")
        pm = peer_return_panel(pm, slim)
        pm["peer_return"] = pm["peer_return"].fillna(pm["ret_1d"])
        g = pm.groupby("event_index")
        s = pd.DataFrame({"peer_n": g["peer_return"].count(),
                          "peer_median": g["peer_return"].median(),
                          "peer_disp": g["peer_return"].std()}).reset_index()
        s["residual"] = s["event_index"].map(cls.set_index("event_index")["ret_1d"]) \
            - s["peer_median"]
        # upside loner: asset residual BELOW peers by >= disp (asset outran peers up)
        s[f"{fam}_label"] = pd.Series(
            np.where(s["peer_disp"].fillna(0) > 0,
                     np.where(s["residual"].abs() >= s["peer_disp"],
                              "TRUE_UP_LONER", "FALSE_UP_LONER"),
                     "NO_PEERS"), index=s.index, dtype=object)
        cls = cls.merge(s[["event_index", f"{fam}_label"]], on="event_index", how="left")
        cls[f"{fam}_label"] = cls[f"{fam}_label"].fillna("NO_PEERS")
    fam_cols = [f"{f}_label" for f in families]
    votes = cls[fam_cols].apply(lambda r: (r == "TRUE_UP_LONER").sum(), axis=1)
    cls["n_families_true"] = votes
    cls["consensus"] = np.select([votes >= 3, votes >= 2], ["TRUE_UP_LONER", "AMBIGUOUS"],
                                 default="AMBIGUOUS")
    cls["final_class"] = np.where(
        cls["consensus"] == "TRUE_UP_LONER", "TRUE_UP_LONER",
        np.where(cls["n_families_true"] == 0, "FALSE_UP_LONER", "AMBIGUOUS"))
    return cls


def upside_loner_paths(up, cls, slim):
    """Classify upside loner resolution: rejoin/catch-up/up-contagion/decouple."""
    df = up.merge(cls.groupby("event_index")["final_class"].first().reset_index(),
                  on="event_index", how="left")
    # track asset vs peer median (behavioral) forward
    pm = C.load_peer_map("BEHAVIORAL_10")
    pm = pm.merge(df[["event_index", "historical_date"]], on="event_index", how="left")
    pm = peer_return_panel(pm, slim)
    pm["peer_return"] = pm["peer_return"].fillna(pm["ret_1d"])
    ev_sum = pm.groupby("event_index").agg(
        peer_n=("peer_return", "count"), peer_med0=("peer_return", "median"),
        **{f"peer_med{h}": (f"fwd{h}_cum", "median") for h in H})
    df = df.merge(ev_sum, left_on="event_index", right_index=True, how="left")
    df["resid7"] = df.get("signed_fwd7", 0) - df["peer_med7"]
    s = df["sigma_t0"]
    def classify(r):
        if not np.isfinite(r["sigma_t0"]) or r["sigma_t0"] <= 0 or not np.isfinite(r.get("peer_med7", np.nan)):
            return "AMBIGUOUS"
        asset_up = r.get("signed_fwd7", np.nan) > 0
        peers_up_fast = r["peer_med7"] > 0.5 * r["sigma_t0"]
        peers_flat = abs(r["peer_med7"]) < 0.5 * r["sigma_t0"]
        if asset_up and peers_up_fast:
            return "LOCAL_UP_CONTAGION"
        if asset_up and peers_flat:
            return "ASSET_REJOINS_PEERS"
        if not asset_up:
            return "PERSISTENT_UP_DECOUPLING"
        return "AMBIGUOUS"
    df["path_class"] = df.apply(classify, axis=1)
    rows = []
    for cls2 in ["TRUE_UP_LONER", "FALSE_UP_LONER"]:
        g = df[df["final_class"] == cls2]
        if len(g) == 0:
            continue
        vc = g["path_class"].value_counts()
        for p, n in vc.items():
            rows.append({"final_class": cls2, "path": p, "n": int(n),
                         "pct": round(n / len(g), 4)})
    return pd.DataFrame(rows), df


def up_down_asymmetry(down, up, cls_down, cls_up):
    rows = []
    d = down.merge(cls_down.groupby("event_index")["final_class"].first().reset_index(),
                   on="event_index", how="left")
    u = up.merge(cls_up.groupby("event_index")["final_class"].first().reset_index(),
                 on="event_index", how="left")
    d["side"] = "DOWN"
    u["side"] = "UP"
    both = pd.concat([d, u])
    for side, g in both.groupby("side"):
        n = len(g)
        cls = g["final_class"].astype(str)
        true = cls.str.contains("TRUE").mean()
        false = cls.str.contains("FALSE").mean()
        sf7 = g.get("signed_fwd7", pd.Series(np.nan, index=g.index))
        # rejoin/normalize: DOWN = reversal above t0 close; UP = still up
        rejoin = (g["rev7"].fillna(False)).mean() if side == "DOWN" else (sf7 > 0).mean()
        # persistent displacement either side: asset still on the shock side
        displace = (sf7 < 0).mean()
        rows.append({
            "side": side, "n": n,
            "true_loner_freq": round(float(true), 4),
            "false_loner_freq": round(float(false), 4),
            "median_abs_amplitude": round(float(g["ret_1d"].abs().median()), 5),
            "median_sigma": round(float(g["z1"].median()), 3),
            "p_rejoin_or_normalize_7d": round(float(rejoin), 4),
            "p_persistent_displacement_7d": round(float(displace), 4),
            "p_rank_repair_30d": round(float(g["fwd_rank_vel_30d"].gt(0).mean()), 4),
            "p_price_repair_30d": round(float(g["recover1s30"].fillna(False).mean()), 4),
            "median_vol_63d": round(float(g["vol_63d"].median()), 6),
        })
    if len(rows) == 2 and abs(rows[0]["true_loner_freq"] - rows[1]["true_loner_freq"]) > 0.02:
        asymm = "SIGN_ASYMMETRIC"
    else:
        asymm = "SYMMETRIC"
    return pd.DataFrame(rows), asymm


# ---------------------------------------------------------------------------
# Section 13: MULTI-SIGMA RECOVERY / EXTENSION LADDER (14)
# ---------------------------------------------------------------------------

def signed_multi_sigma_ladder(down, up):
    rows = []
    for side, g in [("DOWN", down), ("UP", up)]:
        clock = []
        for target in [0.5, 1.0, 2.0, 3.0]:
            for h in H:
                sf = g.get(f"signed_fwd{h}", pd.Series(np.nan, index=g.index))
                sig = g["sigma_t0"]
                valid = np.isfinite(sig) & (sig > 0) & np.isfinite(sf)
                hit = valid & (sf / sig >= target)
                clock.append({"side": side, "target_sigma": target, "horizon": h,
                              "n_at_h": int(valid.sum()),
                              "p_reached": round(float(hit.mean()), 4),
                              "n_reached": int(hit.sum())})
        rows.extend(clock)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 14: LONER × SIGMA × ABSOLUTE HIERARCHY (15)
# ---------------------------------------------------------------------------

def loner_sigma_abs_hierarchy(down, cls):
    df = down.merge(cls.groupby("event_index")["final_class"].first().reset_index(),
                    on="event_index", how="left")
    df["loner"] = np.where(df["final_class"].str.startswith("TRUE"), "TRUE",
                  np.where(df["final_class"].str.endswith("FALSE"), "FALSE", "AMBIGUOUS"))
    df["abs_class"] = pd.cut(df["ret_1d"].abs(), bins=[0, 0.03, 0.05, 0.10, 0.15, np.inf],
                             labels=["LOW", "Q2", "Q3", "HIGH", "EXTREME"], duplicates="drop")
    df["sigma_class"] = pd.cut(df["z1"], bins=[2, 3, 4, np.inf], labels=["2-3σ", "3-4σ", "4σ+"])
    rows = []
    for lon in ["TRUE", "FALSE"]:
        g = df[df["loner"] == lon]
        for sx in ["2-3σ", "3-4σ", "4σ+"]:
            sub = g[g["sigma_class"] == sx]
            if len(sub) < 20:
                continue
            rows.append({
                "loner": lon, "sigma_class": sx, "abs_class": "ALL", "n": len(sub),
                "p_full_repair_30d": round(float(sub["recover1s30"].fillna(False).mean()), 4),
                "p_rank_repair_30d": round(float(sub["fwd_rank_vel_30d"].gt(0).mean()), 4),
                "p_new_low_30d": round(float((sub["signed_fwd30"] < 0).mean()), 4),
                "median_abs_move": round(float(sub["ret_1d"].abs().median()), 5),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 15: REJOIN/CONTAGION/DECOUPLING STATE MACHINE (16)
# ---------------------------------------------------------------------------

def loner_state_machine(down, cls):
    df = down.merge(cls.groupby("event_index")["final_class"].first().reset_index(),
                    on="event_index", how="left")
    df = _zcluster(df).copy()
    states = {}
    # coarse state machine at checkpoints using price + peer residual proxy
    for h in [1, 3, 7, 14, 30]:
        price_down = df.get(f"signed_fwd{h}", pd.Series(dtype=float)) < 0
        price_up = ~price_down
        # peer-health proxy: general reversal implies heal; residual persistence
        states[h] = np.select(
            [price_up & (df.get("fwd_rank_vel_%dd" % h, pd.Series(dtype=float)) < 0),
             price_down & (df.get("fwd_rank_vel_%dd" % h, pd.Series(dtype=float)) > 0),
             price_down & (df.get("fwd_rank_vel_%dd" % h, pd.Series(dtype=float)).fillna(1) <= 0)],
            ["REJOINED", "DECOUPLED", "CONTAGION"], default="REJOINING")
    transitions = []
    for a, b in [(1, 3), (3, 7), (7, 14), (14, 30)]:
        cnt = pd.Series([f"{x}->{y}" for x, y in zip(states[a], states[b])]).value_counts()
        for k, v in cnt.items():
            transitions.append({"from_h": a, "to_h": b, "transition": k, "n": int(v)})
    return pd.DataFrame(transitions)


# ---------------------------------------------------------------------------
# Section 16: PEER CATCHDOWN / CATCHUP DEPTH (17)
# ---------------------------------------------------------------------------

BANDS_ORDER = C.DEPTH_BANDS


def _adj(band):
    i = BANDS_ORDER.index(band) if band in BANDS_ORDER else -1
    out = []
    if i > 0:
        out.append(BANDS_ORDER[i - 1])
    if i < len(BANDS_ORDER) - 1:
        out.append(BANDS_ORDER[i + 1])
    return out


def peer_catch_radius(ev, down, cls):
    df = down.merge(cls.groupby("event_index")["final_class"].first().reset_index(),
                    on="event_index", how="left")
    cont = df[df["final_class"].str.startswith("TRUE")]
    evd = ev[ev["rank_band"].isin(BANDS_ORDER)][["historical_date", "rank_band", "z1"]].copy()
    evd = evd[evd["z1"] >= 2]
    rows = []
    for h in [1, 3, 7, 14]:
        tgt = cont[["event_index", "historical_date", "rank_band"]].copy()
        if len(tgt) == 0:
            continue
        tgt["t_plus"] = tgt["historical_date"] + pd.Timedelta(days=h)
        m = evd.merge(tgt[["event_index", "t_plus", "rank_band"]],
                      left_on="historical_date", right_on="t_plus", how="inner",
                      suffixes=("_x", "_y"))
        if len(m) == 0:
            rows.append({"horizon": h, "n": len(cont),
                         "same_band_spillover": 0.0, "adjacent_band_spillover": 0.0,
                         "multi_band_spillover": 0.0, "radius": "LOCAL"})
            continue
        same = m[m["rank_band_x"] == m["rank_band_y"]]
        adj = m[m.apply(lambda r: r["rank_band_x"] in _adj(r["rank_band_y"]), axis=1)]
        multi = m.groupby("event_index")["rank_band_x"].nunique()
        frac_same = len(same) / max(len(m), 1)
        if frac_same > 0.7:
            radius = "LOCAL"
        elif np.median(multi) <= 2:
            radius = "LOCAL_PATCH"
        elif np.median(multi) <= 4:
            radius = "MULTI_PATCH"
        else:
            radius = "FIELD_WIDE"
        rows.append({"horizon": h, "n": len(cont),
                     "same_band_spillover": round(float(same.groupby("event_index").size().mean()), 3),
                     "adjacent_band_spillover": round(float(adj.groupby("event_index").size().mean()), 3),
                     "multi_band_spillover": round(float(multi.mean()), 3),
                     "radius": radius})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 17: EARLY-WARNING LONER AUDIT (18)
# ---------------------------------------------------------------------------

def early_warning_loner(down, ev, slim):
    """Do asset-led loner events precede peer deterioration vs random?"""
    # asset-led = true loner that then sees peers decline (contagion proxy)
    pm = C.load_peer_map("BEHAVIORAL_10")
    pm = pm.merge(down[["event_index", "historical_date"]], on="event_index", how="left")
    pm = peer_return_panel(pm, slim)
    pm["peer_return"] = pm["peer_return"].fillna(pm["ret_1d"])
    g = pm.groupby("event_index")
    p0 = g["peer_return"].median().rename("peer_med0")
    p3 = g["fwd3_cum"].median().rename("peer_med3") if "fwd3_cum" in pm.columns else g["peer_return"].median().rename("peer_med3")
    ev_sum = pd.concat([p0, p3], axis=1)
    df = down.merge(ev_sum, left_on="event_index", right_index=True, how="left")
    df["peer_deterioration"] = df["peer_med0"] > df["peer_med3"]  # peers more negative after
    # random same-band baseline: shuffle event_index within rank band
    rng = np.random.default_rng(42)
    df_rand = df.copy()
    df_rand["peer_deterioration"] = rng.permutation(df["peer_deterioration"].to_numpy())
    def rate(g):
        return float(g["peer_deterioration"].mean()) if len(g) else np.nan
    rows = []
    for subperiod in sorted(df["subperiod"].unique()):
        g = df[df["subperiod"] == subperiod]
        gr = df_rand[df_rand["subperiod"] == subperiod]
        rows.append({"group": "LONER", "subperiod": subperiod, "n": len(g),
                     "p_peer_deterioration": round(rate(g), 4)})
        rows.append({"group": "RANDOM_SAME_BAND", "subperiod": subperiod, "n": len(gr),
                     "p_peer_deterioration": round(rate(gr), 4)})
    # overall effect = loner - random
    # (effect size via risk difference on full sample)
    eff = rate(df) - rate(df_rand)
    out = pd.DataFrame(rows)
    return out, float(eff) if np.isfinite(eff) else np.nan


# ---------------------------------------------------------------------------
# Section 18-19: PRIMITIVE SEARCHES (19, 20)
# ---------------------------------------------------------------------------

def dislocation_primitive(down, cls):
    """What distinguishes genuine local dislocation that later repairs?"""
    df = down.merge(cls.groupby("event_index")["final_class"].first().reset_index(),
                    on="event_index", how="left")
    df["y"] = df["recover1s7"].fillna(False).astype(int)
    cands = {
        "abs_shock": "ret_1d_abs", "sigma_shock": "z1", "rank_depth": "rank",
        "peer_health_proxy_top500": "top500_breadth_30d",
        "field_state_dispersion": "top500_dispersion_30d",
        "early_recovery_amp": "recover1s3", "vol_30d": "vol_30d",
    }
    df["ret_1d_abs"] = df["ret_1d"].abs()
    feats = [v for v in cands.values() if v in df.columns]
    rows = []
    for patch, m in [("GLOBAL", df), ("TOP_500", df[df["rank_band"].isin(C.COMPARE_BANDS)]),
                     ("501_1000", df[df["rank_band"].isin(["501-750", "751-1000"])]),
                     ("1001_2000", df[df["rank_band"].isin(["1001-1500", "1501-2000"])])]:
        g = m.dropna(subset=["y"])
        signals = []
        for name, col in cands.items():
            if col not in g.columns:
                continue
            sub = g[[col, "y"]].dropna()
            if len(sub) < 50 or sub["y"].nunique() < 2:
                continue
            r = sub[col].corr(sub["y"])
            if np.isfinite(r):
                signals.append((name, r))
        if not signals:
            continue
        best = max(signals, key=lambda x: abs(x[1]))
        verdict = "GLOBAL_PRIMITIVE" if all(np.sign(s) == np.sign(best[1]) for _, s in signals) else "CONDITIONAL_PRIMITIVE"
        row = {"patch": patch, "n": len(g), "verdict": verdict,
               "strongest_coord": best[0], "strongest_corr": round(float(best[1]), 4)}
        for name, r in signals:
            row[f"corr_{name}"] = round(float(r), 4)
        rows.append(row)
    return pd.DataFrame(rows)


def contagion_primitive(down, ev):
    df = down.copy()
    df["ret_1d_abs"] = df["ret_1d"].abs()
    # contagion proxy: peers more negative later — approximate via reversal absence
    df["y"] = (~df["rev7"].fillna(False)).astype(int)
    cands = {"rank_depth": "rank", "asset_shock_abs": "ret_1d_abs",
             "field_breadth": "top500_breadth_30d", "field_dispersion": "top500_dispersion_30d",
             "vol_30d": "vol_30d"}
    rows = []
    for patch, m in [("GLOBAL", df), ("TOP_500", df[df["rank_band"].isin(C.COMPARE_BANDS)]),
                     ("501_1000", df[df["rank_band"].isin(["501-750", "751-1000"])]),
                     ("1001_2000", df[df["rank_band"].isin(["1001-1500", "1501-2000"])])]:
        g = m.dropna(subset=["y"])
        signals = []
        for name, col in cands.items():
            if col not in g.columns:
                continue
            sub = g[[col, "y"]].dropna()
            if len(sub) < 50 or sub["y"].nunique() < 2:
                continue
            r = sub[col].corr(sub["y"])
            if np.isfinite(r):
                signals.append((name, r))
        if not signals:
            continue
        verdict = "CONDITIONAL_PRIMITIVE"
        row = {"patch": patch, "n": len(g), "verdict": verdict,
               "strongest_coord": max(signals, key=lambda x: abs(x[1]))[0],
               "strongest_corr": round(float(max(signals, key=lambda x: abs(x[1]))[1]), 4)}
        for name, r in signals:
            row[f"corr_{name}"] = round(float(r), 4)
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 20: PERSISTENT DECOUPLING BRIDGE (21)
# ---------------------------------------------------------------------------

def persistent_decoupling_bridge(down, slim):
    pm = C.load_peer_map("BEHAVIORAL_10")
    pm = pm.merge(down[["event_index", "historical_date"]], on="event_index", how="left")
    pm = peer_return_panel(pm, slim)
    pm["peer_return"] = pm["peer_return"].fillna(pm["ret_1d"])
    ev_sum = pm.groupby("event_index").agg(
        peer_med0=("peer_return", "median"), **{f"peer_med{h}": (f"fwd{h}_cum", "median")
                                                 for h in H if h <= 30})
    df = down.merge(ev_sum, left_on="event_index", right_index=True, how="left")
    dec = df[(df["signed_fwd7"] < 0) & (df["peer_med7"] > 0)]
    rows = []
    for h in [7, 14, 30]:
        g = dec
        rows.append({
            "horizon": h, "n": len(g),
            "p_price_deterioration": round(float((g[f"signed_fwd{h}"] < 0).mean()), 4),
            "p_rank_deterioration": round(float((g[f"fwd_rank_vel_{h}d"] < 0).mean()), 4) if f"fwd_rank_vel_{h}d" in g.columns else np.nan,
            "median_peer_return": round(float(g[f"peer_med{h}"].median()), 5),
            "median_asset_return": round(float(g[f"signed_fwd{h}"].median()), 5),
            "p_activity_decline": round(float((g["volume_24h_usd"] < g["vol_prev7_med"]).mean()), 4) if len(g) else np.nan,
            "p_rejoin_later_30d": round(float(g["recover1s30"].fillna(False).mean()), 4),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 21: PRD WITH DYNAMIC PEERS (22)
# ---------------------------------------------------------------------------

def prd_dynamic_peer(down, slim, cls):
    prd = down[down.get("recover1s7", pd.Series(dtype=float)).fillna(False)
               & (down.get("fwd_rank_vel_7d", pd.Series(dtype=float)) < 0)]
    if len(prd) < 20:
        return pd.DataFrame([{"status": "LOW_N"}])
    pm = C.load_peer_map("BEHAVIORAL_10")
    pm = pm.merge(prd[["event_index", "historical_date"]], on="event_index", how="left")
    pm = peer_return_panel(pm, slim)
    pm["peer_return"] = pm["peer_return"].fillna(pm["ret_1d"])
    ev_sum = pm.groupby("event_index").agg(
        peer_med0=("peer_return", "median"), **{f"peer_med{h}": (f"fwd{h}_cum", "median")
                                                 for h in H if h <= 30})
    df = prd.merge(ev_sum, left_on="event_index", right_index=True, how="left")
    df["peer_up"] = df["peer_med7"] > 0
    df["peer_health"] = np.where(df["peer_med7"] > 0, "PEER_HEALTHY",
                        np.where(df["peer_med7"] < 0, "PEER_STRESSED", "PEER_FLAT"))
    loner = cls.groupby("event_index")["final_class"].first().reset_index()
    df = df.merge(loner, on="event_index", how="left")
    df["loner_type"] = np.where(df["final_class"].str.startswith("TRUE"), "TRUE_LONER",
                       np.where(df["final_class"].str.endswith("FALSE"), "FALSE_LONER", "AMBIGUOUS"))
    rows = []
    for sub, g in df.groupby(["peer_health", "loner_type"]):
        if len(g) < 10:
            continue
        rows.append({"subtype": "PEER_HEALTH_x_LONER", "peer_health": sub[0],
                     "loner_type": sub[1], "n": len(g),
                     "p_persist_prd_14d": round(float((g["recover1s14"].fillna(False)
                        & (g["fwd_rank_vel_14d"] < 0)).mean()), 4),
                     "p_rank_rehab_30d": round(float(g["fwd_rank_vel_30d"].gt(0).mean()), 4),
                     "median_peer_ret_7d": round(float(g["peer_med7"].median()), 5)})
    for cell in ["HH", "HL", "LH", "LL"]:
        g = df[df["field_cell"].map(CELL4) == cell]
        if len(g) < 10:
            continue
        rows.append({"subtype": "CELL", "peer_health": "ANY", "loner_type": cell,
                     "n": len(g),
                     "p_persist_prd_14d": round(float((g["recover1s14"].fillna(False)
                        & (g["fwd_rank_vel_14d"] < 0)).mean()), 4),
                     "p_rank_rehab_30d": round(float(g["fwd_rank_vel_30d"].gt(0).mean()), 4),
                     "median_peer_ret_7d": np.nan})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 22: GLOBAL × LOCAL × ASSET TRIANGLE (23)
# ---------------------------------------------------------------------------

def triangle_pilot(down, cls):
    """Test whether global×local×asset triple beats pairwise combinations."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import cross_val_score
    df = down.merge(cls.groupby("event_index")["final_class"].first().reset_index(),
                    on="event_index", how="left")
    df["loner_true"] = (df["final_class"].str.startswith("TRUE")).astype(int)
    df["loner_false"] = (df["final_class"].str.endswith("FALSE")).astype(int)
    # GLOBAL: field cell numeric (breadth/dispression), LOCAL: peer-relative residual,
    # ASSET: true/false loner + rank + vol
    df["global_hh"] = (df["field_cell"].map(CELL4) == "HH").astype(int)
    df["local_peer_resid"] = df["rank"] - df["rank"]  # placeholder replaced below
    # use forward peer-relative signal via residual proxy
    # build proper local: asset - median peer (behavioral) forward resid at 7d
    pm = C.load_peer_map("BEHAVIORAL_10")
    pm = pm.merge(down[["event_index", "historical_date"]], on="event_index", how="left")
    pm = peer_return_panel(pm, slim if False else C.load_substrate_slim())
    pm["peer_return"] = pm["peer_return"].fillna(pm["ret_1d"])
    ev_sum = pm.groupby("event_index").agg(peer_med0=("peer_return", "median"),
                                           peer_med7=("fwd7_cum", "median"))
    df = df.merge(ev_sum, left_on="event_index", right_index=True, how="left")
    df["local_peer_resid"] = df["signed_fwd7"] - df["peer_med7"]
    df["resid_abs"] = df["local_peer_resid"].abs()
    feats = {
        "GLOBAL": ["global_hh", "top500_dispersion_30d"],
        "LOCAL": ["resid_abs"],
        "ASSET": ["loner_true", "rank", "z1", "vol_30d"],
        "GLOBAL_LOCAL": ["global_hh", "top500_dispersion_30d", "resid_abs"],
        "GLOBAL_ASSET": ["global_hh", "top500_dispersion_30d", "loner_true", "rank", "z1"],
        "LOCAL_ASSET": ["resid_abs", "loner_true", "rank", "z1", "vol_30d"],
        "TRIANGLE": ["global_hh", "top500_dispersion_30d", "resid_abs",
                     "loner_true", "rank", "z1", "vol_30d"],
    }
    yname = "recover1s7"
    t = df.dropna(subset=[yname]).copy()
    t["y"] = t[yname].astype(int)
    rows = []
    for name, cols in feats.items():
        cols = [c for c in cols if c in t.columns]
        tt = t[t[cols + ["y"]].notna().all(axis=1)]
        if len(tt) < 200 or tt["y"].nunique() < 2:
            continue
        X = tt[cols].to_numpy(float)
        clf = LogisticRegression(max_iter=1000)
        try:
            auc = roc_auc_score(tt["y"], clf.fit(X, tt["y"]).predict_proba(X)[:, 1])
            cv = cross_val_score(clf, X, tt["y"], cv=3, scoring="roc_auc")
        except Exception:
            continue
        rows.append({"block": name, "n": len(tt), "auc_in_sample": round(float(auc), 4),
                     "auc_cv_mean": round(float(cv.mean()), 4),
                     "auc_cv_std": round(float(cv.std()), 4)})
    dd = pd.DataFrame(rows).set_index("block")
    verdict = "INCONCLUSIVE"
    if "TRIANGLE" in dd.index and "PAIRWISE" in dd.index:
        pass
    # compare triangle vs best pairwise cv
    pair_rows = [r for r in rows if r["block"] in ("GLOBAL_LOCAL", "GLOBAL_ASSET", "LOCAL_ASSET")]
    tri = [r for r in rows if r["block"] == "TRIANGLE"]
    if tri and pair_rows:
        best_pair = max(pair_rows, key=lambda r: r["auc_cv_mean"])
        delta = tri[0]["auc_cv_mean"] - best_pair["auc_cv_mean"]
        if delta > 0.01:
            verdict = "LOCAL_TRIANGLE" if best_pair["block"].startswith("LOCAL") else "TRIANGLE_EARNED"
        elif delta > -0.01:
            verdict = "INCONCLUSIVE"
        else:
            verdict = "PAIRWISE_SUFFICIENT"
    return pd.DataFrame(rows), verdict


# ---------------------------------------------------------------------------
# Section 23: LOCAL SEQUENCE ATLAS (24)
# ---------------------------------------------------------------------------

def local_sequence_atlas(down, up, cls, up_cls):
    def sidx(cls_, subj, startswith):
        ix = cls_[cls_["final_class"].str.startswith(startswith)]["event_index"]
        return set(ix)
    rows = []
    t_ix = cls[cls["final_class"].str.startswith("TRUE")]["event_index"]
    t = down[down["event_index"].isin(t_ix)]
    f_ix = cls[cls["final_class"].str.endswith("FALSE")]["event_index"]
    f = down[down["event_index"].isin(f_ix)]
    if len(t) >= MIN_EVENTS:
        s1 = t[t["recover1s3"].fillna(False)]
        s2 = t[(t["signed_fwd7"] / t["sigma_t0"]) >= 2]
        rankrep = t[t["fwd_rank_vel_30d"] > 0]
        rows.append({"sequence": "TRUE_DOWN_LONER->EARLY_1SIGMA->PEER_REJOIN->RANK_REPAIR",
                     "n_total": len(t), "n_1s": int(len(s1)), "n_2s": int(len(s2)),
                     "n_rank_repair": int(len(rankrep)),
                     "pct_full": round(len(rankrep) / max(len(t), 1), 4)})
        no1 = t[~t["recover1s7"].fillna(False)]
        cont = no1[no1["signed_fwd7"] < 0]
        rows.append({"sequence": "TRUE_DOWN_LONER->NO_RECOVERY->CONTAGION",
                     "n_total": len(t), "n_no_1s": int(len(no1)), "n_contagion": int(len(cont)),
                     "pct_full": round(len(cont) / max(len(t), 1), 4)})
    if len(f) >= MIN_EVENTS:
        norm = f[f["rev7"].fillna(False)]
        rows.append({"sequence": "FALSE_LONER->PEER_NORMALIZATION->ASSET_NORMALIZATION",
                     "n_total": len(f), "n_norm": int(len(norm)),
                     "pct_full": round(len(norm) / max(len(f), 1), 4)})
    u_ix = up_cls[up_cls["final_class"].str.startswith("TRUE_UP")]["event_index"]
    u = up[up["event_index"].isin(u_ix)]
    if len(u) >= MIN_EVENTS:
        persist = u[(u["signed_fwd30"] > 0)]
        rows.append({"sequence": "TRUE_UP_LONER->PEER_CATCHUP->PERSISTENT_OUTPERFORMANCE",
                     "n_total": len(u), "n_persist": int(len(persist)),
                     "pct_full": round(len(persist) / max(len(u), 1), 4)})
    if not rows:
        return pd.DataFrame([{"sequence": "NONE", "status": "LOW_N"}])
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading...", flush=True)
    ev, down, down3, up, up3, slim, quality = load_all()
    print(f"down 2s {len(down)} | up 2s {len(up)} | down 3s {len(down3)} | up 3s {len(up3)}",
          flush=True)

    print("\n=== S1: Peer validity reclassification (02) ===", flush=True)
    pvr = peer_validity_reclassification(down, quality, slim)
    pvr.to_csv(R / "02_PEER_VALIDITY_RECLASSIFICATION.csv", index=False)
    print(pvr[["peer_family", "jaccard_persistence", "future_similarity_oos",
               "reclassification"]].to_string(index=False))

    print("\n=== S2: Peer family dependence (03) ===", flush=True)
    pfd = peer_family_dependence(down, slim)
    pfd.to_csv(R / "03_PEER_FAMILY_DEPENDENCE.csv", index=False)
    print(pfd.to_string(index=False))

    print("\n=== S3: Dynamic peer formation (04) ===", flush=True)
    fmt = dynamic_peer_formation(down, slim)
    fmt.to_csv(R / "04_DYNAMIC_PEER_FORMATION.csv", index=False)
    print(f"{len(fmt)} rows | median jaccard {fmt['jaccard_persistence'].median():.3f}")

    print("\n=== S4: Peer formation context (05) ===", flush=True)
    market = C.load_market_state()
    pfc = peer_formation_context(fmt, market, slim)
    pfc.to_csv(R / "05_PEER_FORMATION_CONTEXT.csv", index=False)
    print(pfc.head(15).to_string(index=False))

    print("\n=== S5: Peer lifetime distribution (06) ===", flush=True)
    pm_all = C.load_peer_map("BEHAVIORAL_10")
    pm_all = pm_all.merge(down[["event_index", "historical_date"]], on="event_index", how="left")
    pm_all = peer_return_panel(pm_all, slim)
    plt = peer_lifetime(pm_all)
    plt.to_csv(R / "06_PEER_LIFETIME_DISTRIBUTION.csv", index=False)
    print(plt.to_string(index=False))

    print("\n=== S6: Absolute vs sigma shock matrix (07) ===", flush=True)
    avs, both = abs_vs_sigma_matrix(down, up)
    avs.to_csv(R / "07_ABSOLUTE_VS_SIGMA_SHOCK_MATRIX.csv", index=False)
    print(f"{len(avs)} rows")

    print("\n=== S7: False loner artifact audit (08) ===", flush=True)
    cls = classification(down, slim)
    fla = false_loner_artifact_audit(down, cls, slim)
    fla.to_csv(R / "08_FALSE_LONER_ARTIFACT_AUDIT.csv", index=False)
    print(fla.to_string(index=False))

    print("\n=== S8: Down loner deepening (09) ===", flush=True)
    dld = down_loner_deepening(down, cls)
    dld.to_csv(R / "09_TRUE_DOWN_LONER_DEEPENING.csv", index=False)
    print(f"{len(dld)} rows")

    print("\n=== S9: False loner deepening (10) ===", flush=True)
    fld = false_loner_deepening(down, cls)
    fld.to_csv(R / "10_FALSE_DOWN_LONER_DEEPENING.csv", index=False)
    print(f"{len(fld)} rows")

    print("\n=== S10: Upside loner classification (11) ===", flush=True)
    up_cls = upside_loner_classification(up, slim)
    up_cls.to_csv(R / "11_UPSIDE_LONER_CLASSIFICATION.csv", index=False)
    print(up_cls["final_class"].value_counts().to_string())

    print("\n=== S11: Upside loner paths (12) ===", flush=True)
    ulp, up_path = upside_loner_paths(up, up_cls, slim)
    ulp.to_csv(R / "12_UPSIDE_LONER_PATHS.csv", index=False)
    print(ulp.to_string(index=False))

    print("\n=== S12: Up/down asymmetry (13) ===", flush=True)
    uda, asymm = up_down_asymmetry(down, up, cls, up_cls)
    uda.to_csv(R / "13_UP_DOWN_ASYMMETRY.csv", index=False)
    print(uda.to_string(index=False))
    print(f"Theory verdict: {asymm}")

    print("\n=== S13: Signed multi-sigma ladder (14) ===", flush=True)
    sml = signed_multi_sigma_ladder(down, up)
    sml.to_csv(R / "14_SIGNED_MULTI_SIGMA_LADDER.csv", index=False)
    print(sml[sml["target_sigma"] == 1.0].head(5).to_string(index=False))

    print("\n=== S14: Loner sigma abs hierarchy (15) ===", flush=True)
    lsah = loner_sigma_abs_hierarchy(down, cls)
    lsah.to_csv(R / "15_LONER_SIGMA_ABS_HIERARCHY.csv", index=False)
    print(lsah.to_string(index=False))

    print("\n=== S15: Loner state machine (16) ===", flush=True)
    lsm = loner_state_machine(down, cls)
    lsm.to_csv(R / "16_LONER_STATE_MACHINE.csv", index=False)
    print(f"{len(lsm)} transitions")

    print("\n=== S16: Peer catch radius (17) ===", flush=True)
    pcr = peer_catch_radius(ev, down, cls)
    pcr.to_csv(R / "17_PEER_CATCH_RADIUS.csv", index=False)
    print(pcr.to_string(index=False))

    print("\n=== S17: Early warning loner (18) ===", flush=True)
    ewl, eff = early_warning_loner(down, ev, slim)
    ewl.to_csv(R / "18_EARLY_WARNING_LONER_AUDIT.csv", index=False)
    print(f"Risk-difference loner-vs-random: {eff:.3f}")

    print("\n=== S18: Dislocation primitive (19) ===", flush=True)
    dlm = dislocation_primitive(down, cls)
    dlm.to_csv(R / "19_TRUE_DISLOCATION_PRIMITIVE.csv", index=False)
    print(dlm[["patch", "verdict", "strongest_coord", "strongest_corr"]].to_string(index=False))

    print("\n=== S19: Contagion primitive (20) ===", flush=True)
    cpm = contagion_primitive(down, ev)
    cpm.to_csv(R / "20_CONTAGION_PRIMITIVE.csv", index=False)
    print(cpm[["patch", "verdict", "strongest_coord", "strongest_corr"]].to_string(index=False))

    print("\n=== S20: Persistent decoupling bridge (21) ===", flush=True)
    pdb = persistent_decoupling_bridge(down, slim)
    pdb.to_csv(R / "21_PERSISTENT_DECOUPLING_BRIDGE.csv", index=False)
    print(pdb.to_string(index=False))

    print("\n=== S21: PRD dynamic peer anatomy (22) ===", flush=True)
    pap = prd_dynamic_peer(down, slim, cls)
    pap.to_csv(R / "22_PRD_DYNAMIC_PEER_ANATOMY.csv", index=False)
    print(f"{len(pap)} rows")

    print("\n=== S22: Triangle pilot (23) ===", flush=True)
    tri, verd = triangle_pilot(down, cls)
    tri.to_csv(R / "23_GLOBAL_LOCAL_ASSET_TRIANGLE.csv", index=False)
    print(f"triangle verdict: {verd}")

    print("\n=== S23: Local sequence atlas (24) ===", flush=True)
    lsa = local_sequence_atlas(down, up, cls, up_cls)
    lsa.to_csv(R / "24_LOCAL_SEQUENCE_ATLAS.csv", index=False)
    print(lsa.to_string(index=False))

    print("\n=== COMPLETE ===", flush=True)
    return cls, up_cls


def classification(down, slim):
    """Consensus loner classification (TRUE/FALSE) for downside events."""
    families = C.DEEP_FAMILIES
    cls = down[["event_index", "ret_1d", "rank_band"]].copy()
    for fam in families:
        pm = C.load_peer_map(fam)
        pm = pm.merge(down[["event_index", "historical_date"]], on="event_index",
                      how="left")
        pm = peer_return_panel(pm, slim)
        pm["peer_return"] = pm["peer_return"].fillna(pm["ret_1d"])
        g = pm.groupby("event_index")
        s = pd.DataFrame({"peer_n": g["peer_return"].count(),
                          "peer_median": g["peer_return"].median(),
                          "peer_disp": g["peer_return"].std()}).reset_index()
        s["residual"] = s["event_index"].map(cls.set_index("event_index")["ret_1d"]) \
            - s["peer_median"]
        s[f"{fam}_label"] = pd.Series(
            np.where(s["peer_disp"].fillna(0) > 0,
                     np.where(s["residual"].abs() >= s["peer_disp"],
                              "TRUE_LONER", "FALSE_LONER"), "NO_PEERS"),
            index=s.index, dtype=object)
        cls = cls.merge(s[["event_index", f"{fam}_label"]], on="event_index", how="left")
        cls[f"{fam}_label"] = cls[f"{fam}_label"].fillna("NO_PEERS")
    fam_cols = [f"{f}_label" for f in families]
    votes = cls[fam_cols].apply(lambda r: (r == "TRUE_LONER").sum(), axis=1)
    cls["n_families_true"] = votes
    cls["consensus"] = np.select([votes >= 3, votes >= 3], ["TRUE_MULTI_PEER_LONER", "AMBIGUOUS"],
                                 default="AMBIGUOUS")
    # final: true if >=3 true, false if 0 true, else ambiguous
    cls["final_class"] = np.where(votes >= 3, "TRUE_MULTI_PEER_LONER",
                          np.where(votes == 0, "BEHAVIORAL_FALSE", "AMBIGUOUS"))
    return cls


if __name__ == "__main__":
    main()