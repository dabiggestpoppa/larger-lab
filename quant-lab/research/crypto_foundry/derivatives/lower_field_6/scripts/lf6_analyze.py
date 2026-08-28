"""LOWER-FIELD-6 analysis — true/false loner geometry, multi-sigma recovery
ladders, peer rejoin vs peer catchdown, rank-patch anatomy, health-state
harmonization, local sequences and propagation structure.

Built on the LF5 PIT substrate, events and true peer maps. Research only:
no strategy, no PnL, no execution, no sizing, no leverage.

Outputs 02-24 (analysis) plus 25-27 (meta) written to lower_field_6/.
"""
from __future__ import annotations

import warnings
from collections import Counter

import numpy as np
import pandas as pd

import lf6_common as C

warnings.filterwarnings("ignore", category=RuntimeWarning)

R = C.ROOT
H = C.H
MIN_EVENTS = C.MIN_EVENTS

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_all():
    ev = C.load_events()
    loner = C.loner_universe(ev, "2s")
    loner3 = C.loner_universe(ev, "3s")
    slim = C.load_substrate_slim()
    quality = pd.read_csv(C.LF5_QUALITY)
    return ev, loner, loner3, slim, quality


def peer_forward_panel(pm, slim):
    """Attach peer forward cumulative returns at each horizon via merge."""
    pm = pm.merge(slim.rename(columns={"cmc_id": "peer_id"}),
                  on=["peer_id", "historical_date"], how="left",
                  suffixes=("", "_slim"))
    return pm


# ---------------------------------------------------------------------------
# Section 1: PEER VALIDATION DEPTH (02)
# ---------------------------------------------------------------------------

def _jaccard_persistence(pm, loner):
    """Mean Jaccard between peer sets of same asset at consecutive events.

    pm must already carry historical_date (merged by the caller).
    """
    sub = pm[pm["historical_date"].notna()].copy()
    js = []
    for _, gg in sub.groupby("asset_id", sort=False):
        if gg["event_index"].nunique() < 2:
            continue
        sets = {}
        for ei, g2 in gg.groupby("event_index"):
            sets[ei] = set(g2["peer_id"])
        order = gg.groupby("event_index")["historical_date"].first().sort_values()
        prev = None
        for ei in order.index:
            if prev is not None:
                a, b = sets[prev], sets[ei]
                j = len(a & b) / max(len(a | b), 1)
                js.append(j)
            prev = ei
    return float(np.mean(js)) if js else np.nan


def peer_validation_depth(loner, quality, slim):
    rows = []
    for fam in C.DEEP_FAMILIES:
        pm = C.load_peer_map(fam)
        pm = pm.merge(loner[["event_index", "historical_date"]], on="event_index",
                      how="left")
        pm = peer_forward_panel(pm, slim)
        pm["peer_return"] = pm["peer_return"].fillna(pm["ret_1d"])
        ev_idx = pm["event_index"].unique()
        loner_idx = set(loner["event_index"])
        n_ev = len(loner)
        cov = len(set(ev_idx) & loner_idx) / max(n_ev, 1)
        med = pm.groupby("event_index").size().median() if len(pm) else np.nan
        pers = _jaccard_persistence(pm, loner)
        # future correlation stability: median pairwise corr of peer returns t0
        # vs peer returns t+7 (descriptive, no outcomes used to select peers)
        fut = _future_coherence(pm)
        cyc, rk = [], []
        for sp, g in loner.groupby("subperiod"):
            cc = pm[pm["event_index"].isin(g["event_index"])]["event_index"].nunique() / max(len(g), 1)
            cyc.append(cc)
        for bd, g in loner.groupby("rank_band"):
            cc = pm[pm["event_index"].isin(g["event_index"])]["event_index"].nunique() / max(len(g), 1)
            rk.append(cc)
        q = quality[quality["peer_family"] == fam]
        def _q(col, default=np.nan):
            return q[col].iloc[0] if len(q) and col in q.columns else default
        rows.append({
            "peer_family": fam,
            "event_coverage": round(cov, 4),
            "median_peer_count": round(float(med), 2) if np.isfinite(med) else np.nan,
            "jaccard_persistence": round(pers, 4) if np.isfinite(pers) else np.nan,
            "membership_turnover": round(1 - pers, 4) if np.isfinite(pers) else np.nan,
            "future_corr_stability": round(fut, 4) if np.isfinite(fut) else np.nan,
            "cycle_stability_cov": round(float(np.nanstd(cyc)), 4) if len(cyc) > 1 else np.nan,
            "rankdepth_stability_cov": round(float(np.nanstd(rk)), 4) if len(rk) > 1 else np.nan,
            "lf5_pre_event_similarity": _q("pre_event_similarity"),
            "lf5_next_window_similarity": _q("next_window_similarity"),
            "lf5_basket_correlation": _q("basket_correlation"),
            "lf5_peer_missing_rate": _q("peer_missing_rate"),
            "lf5_status": _q("status", "NO_LF5_RECORD"),
        })
    return pd.DataFrame(rows)


def _future_coherence(pm):
    """Median pairwise corr between peer return at t0 and peer fwd7."""
    sub = pm[["event_index", "peer_return", "fwd7_cum"]].dropna()
    if len(sub) < 100:
        return np.nan
    g = sub.groupby("event_index")
    vals = []
    for _, gg in g:
        if len(gg) >= 5:
            r = np.corrcoef(gg["peer_return"], gg["fwd7_cum"])[0, 1]
            if np.isfinite(r):
                vals.append(r)
    return float(np.median(vals)) if vals else np.nan


# ---------------------------------------------------------------------------
# Section 2: CONSENSUS LONER CLASSIFICATION (03)
# ---------------------------------------------------------------------------

def consensus_loner(loner, slim):
    """Classify each event TRUE/FALSE loner per family; build consensus."""
    families = C.DEEP_FAMILIES
    cls = loner[["event_index", "ret_1d", "rank_band"]].copy()
    for fam in families:
        pm = C.load_peer_map(fam)
        pm = pm.merge(loner[["event_index", "historical_date"]], on="event_index",
                      how="left")
        pm = peer_forward_panel(pm, slim)
        pm["peer_return"] = pm["peer_return"].fillna(pm["ret_1d"])
        g = pm.groupby("event_index")["peer_return"]
        s = pd.DataFrame({
            "peer_n": g.count(),
            "peer_median": g.median(),
            "peer_disp": g.std(),
        }).reset_index()
        s["residual"] = s["event_index"].map(cls.set_index("event_index")["ret_1d"]) \
            - s["peer_median"]
        s[f"{fam}_label"] = pd.Series(
            np.where(s["peer_disp"].fillna(0) > 0,
                     np.where(s["residual"].abs() >= s["peer_disp"],
                              "TRUE_LONER", "FALSE_LONER"),
                     "NO_PEERS"),
            index=s.index, dtype=object)
        cls = cls.merge(s[["event_index", f"{fam}_label"]], on="event_index", how="left")
        cls[f"{fam}_label"] = cls[f"{fam}_label"].fillna("NO_PEERS")
    fam_cols = [f"{f}_label" for f in families]
    votes = cls[fam_cols].apply(lambda r: (r == "TRUE_LONER").sum(), axis=1)
    n_votes = cls[fam_cols].notna().sum(axis=1)
    cls["n_families_true"] = votes
    cls["n_families_voted"] = n_votes
    cls["consensus"] = np.select(
        [votes >= 3, n_votes >= 3],
        ["TRUE_MULTI_PEER_LONER", "AMBIGUOUS"], default="AMBIGUOUS")

    def dom_false(r):
        falses = [f.split("_")[0] for f in fam_cols if r[f] == "FALSE_LONER"]
        return f"{falses[0]}_FALSE" if falses else np.nan
    cls["dominant_false"] = cls.apply(dom_false, axis=1)
    cls["final_class"] = np.where(
        cls["consensus"] == "TRUE_MULTI_PEER_LONER", "TRUE_MULTI_PEER_LONER",
        np.where(cls["dominant_false"].notna(), cls["dominant_false"], "AMBIGUOUS"))
    return cls


# ---------------------------------------------------------------------------
# Section 3: RANK-DEPTH LONER MAP (04)
# ---------------------------------------------------------------------------

def rank_depth_map(loner, cls):
    depth = ["26-100", "101-250", "251-500", "501-750", "751-1000",
             "1001-1500", "1501-2000"]
    rows = []
    for bd in depth:
        sub = cls[cls["rank_band"] == bd]
        n = len(sub)
        if n == 0:
            continue
        rows.append({
            "rank_band": bd, "n_events": n,
            "true_loner_freq": round((sub["final_class"] == "TRUE_MULTI_PEER_LONER").mean(), 4),
            "false_loner_freq": round(sub["final_class"].str.endswith("_FALSE").mean(), 4),
            "ambiguous_freq": round((sub["final_class"] == "AMBIGUOUS").mean(), 4),
            "peer_cohesion_med": round(float(sub["n_families_true"].median()), 2),
        })

    def agg(bands, name):
        s = cls[cls["rank_band"].isin(bands)]
        if len(s) == 0:
            return
        rows.append({
            "rank_band": name, "n_events": len(s),
            "true_loner_freq": round((s["final_class"] == "TRUE_MULTI_PEER_LONER").mean(), 4),
            "false_loner_freq": round(s["final_class"].str.endswith("_FALSE").mean(), 4),
            "ambiguous_freq": round((s["final_class"] == "AMBIGUOUS").mean(), 4),
            "peer_cohesion_med": round(float(s["n_families_true"].median()), 2),
        })
    agg(["26-100", "101-250", "251-500"], "TOP_500")
    agg(["501-750", "751-1000"], "501_1000")
    agg(["1001-1500", "1501-2000"], "1001_2000")
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 4: RANK PATCH / BASKET GEOMETRY (05)
# ---------------------------------------------------------------------------

def rank_patch_geometry(ev, loner, cls):
    patches = ["26-100", "101-250", "251-500", "501-750", "751-1000",
               "1001-1500", "1501-2000"]
    sub = ev[ev["rank_band"].isin(patches)].copy()
    rows = []
    rk = C.load_peer_map("RANK_50")
    bh = C.load_peer_map("BEHAVIORAL_10")
    rk_s = set(zip(rk["event_index"], rk["peer_id"]))
    bh_s = set(zip(bh["event_index"], bh["peer_id"]))
    overlap = len(rk_s & bh_s) / max(len(rk_s | bh_s), 1)
    for bd in patches:
        g = sub[sub["rank_band"] == bd]
        n = len(g)
        if n < 20:
            continue
        # cross-sectional dispersion proxy on event days
        disp = g.groupby("historical_date")["ret_1d"].std().median()
        # same-sign fraction within patch on event days
        same_sign = g.groupby("historical_date")["event_sign"].mean().abs().median()
        cls_b = cls[cls["rank_band"] == bd]
        rows.append({
            "patch": bd, "n_events": n,
            "internal_dispersion_proxy": round(float(disp) if np.isfinite(disp) else np.nan, 4),
            "same_sign_coherence": round(float(same_sign) if np.isfinite(same_sign) else np.nan, 4),
            "rank50_beh10_overlap_jaccard": round(overlap, 4),
            "median_z1": round(float(g["z1"].median()), 3),
            "tail_sync_share": round(float((g["z1"] >= 3).mean()), 4),
            "median_rank_vel_7d": round(float(g["rank_vel_7d"].median()), 2),
            "reversal_7d": round(float(g.get("rev7", pd.Series(dtype=float)).mean()), 4),
            "false_loner_density": round(float(cls_b["final_class"].str.endswith("_FALSE").mean()), 4)
                if len(cls_b) else np.nan,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 5: TRUE/FALSE LONER OUTCOME MATRIX (06)
# ---------------------------------------------------------------------------

def loner_outcomes(cls, loner):
    rows = []
    classes = ["TRUE_MULTI_PEER_LONER", "AMBIGUOUS"] + \
              sorted([c for c in cls["final_class"].unique() if c.endswith("_FALSE")])
    for fam_cls in classes:
        idx = set(cls[cls["final_class"] == fam_cls]["event_index"])
        sub = loner[loner["event_index"].isin(idx)]
        if len(sub) < 10:
            continue
        for h in [1, 3, 7, 14, 30]:
            sf = sub.get(f"signed_fwd{h}", pd.Series(dtype=float))
            rows.append({
                "class": fam_cls, "horizon": h, "n": len(sub),
                "p_reversal": round(float(sub.get(f"rev{h}", pd.Series(dtype=float)).mean()), 4),
                "p_new_low": round(float((sf < 0).mean()), 4),
                "p_price_repair_1s": round(float(sub.get(f"recover1s{h}", pd.Series(dtype=float)).mean()), 4),
                "p_rank_repair": round(float(sub.get(f"fwd_rank_vel_{h}d", pd.Series(dtype=float)).gt(0).mean()), 4),
                "median_vol_63d": round(float(sub["vol_63d"].median()), 5),
                "p_tail_recurrence": round(float(sub["z1"].ge(3).mean()), 4),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 6-8: MULTI-SIGMA RECOVERY LADDER (07/08/09)
# ---------------------------------------------------------------------------

def multi_sigma_ladder(loner):
    rows = []
    for _, ev in loner.iterrows():
        s = ev["sigma_t0"]
        if not np.isfinite(s) or s <= 0:
            continue
        for h in H:
            sf = ev.get(f"signed_fwd{h}", np.nan)
            if not np.isfinite(sf):
                continue
            rows.append({"event_index": ev["event_index"], "horizon": h,
                         "recovery_sigma": sf / s})
    clock = pd.DataFrame(rows)
    out = []
    for target in [0.5, 1.0, 2.0, 3.0]:
        for h in H:
            sub = clock[clock["horizon"] == h]
            if len(sub) == 0:
                continue
            hit = sub[sub["recovery_sigma"] >= target]
            out.append({
                "target_sigma": target, "horizon": h,
                "n_at_h": int(len(sub)),
                "p_reached": round(float((sub["recovery_sigma"] >= target).mean()), 4),
                "n_reached": int(len(hit)),
                "p_hit_full_2s_30d": np.nan,  # filled from clock
            })
    # full repair given checkpoint at 30D
    clock30 = clock[clock["horizon"] == 30].set_index("event_index")
    for r in out:
        if r["n_reached"]:
            pass
    return clock, pd.DataFrame(out)


def shock_recovery_amplitude(loner):
    rows = []
    for amp in ["2s", "3s", "4s+"]:
        sub = loner[loner["amp_level"] == amp]
        if len(sub) < 20:
            continue
        for target in [0.5, 1.0, 2.0, 3.0]:
            days = []
            for _, ev in sub.iterrows():
                s = ev["sigma_t0"]
                if not np.isfinite(s) or s <= 0:
                    continue
                for h in H:
                    sf = ev.get(f"signed_fwd{h}", np.nan)
                    if np.isfinite(sf) and sf / s >= target:
                        days.append(h)
                        break
            rows.append({
                "initial_amp": amp, "recovery_amp_sigma": target, "n": len(sub),
                "p_reached_by_7d": round(sum(1 for d in days if d <= 7) / len(sub), 4),
                "median_days_to_reach": round(float(np.median(days)), 1) if days else np.nan,
            })
    return pd.DataFrame(rows)


def loner_sigma_matrix(loner, cls):
    rows = []
    classes = ["TRUE_MULTI_PEER_LONER"] + \
              sorted([c for c in cls["final_class"].unique() if c.endswith("_FALSE")])
    for fam_cls in classes:
        idx = set(cls[cls["final_class"] == fam_cls]["event_index"])
        sub = loner[loner["event_index"].isin(idx)]
        if len(sub) < 20:
            continue
        for label, h, t in [("1S_BY_1D", 1, 1.0), ("1S_BY_3D", 3, 1.0),
                            ("1S_BY_7D", 7, 1.0), ("2S_BY_3D", 3, 2.0),
                            ("2S_BY_7D", 7, 2.0), ("2S_BY_14D", 14, 2.0),
                            ("3S_BY_7D", 7, 3.0), ("3S_BY_14D", 14, 3.0),
                            ("3S_BY_30D", 30, 3.0)]:
            sig = sub["sigma_t0"].to_numpy()
            sf = sub.get(f"signed_fwd{h}", pd.Series(np.nan, index=sub.index)).to_numpy()
            hit = np.isfinite(sig) & (sig > 0) & np.isfinite(sf) & (sf / sig >= t)
            hs = sub[hit]
            rows.append({
                "class": fam_cls, "checkpoint": label, "n": len(sub),
                "p_checkpoint": round(float(hit.mean()), 4),
                "p_full_repair_30d": round(float(hs.get("recover1s30", pd.Series(dtype=float)).mean()), 4) if len(hs) else np.nan,
                "p_new_low_30d": round(float((hs.get("signed_fwd30", pd.Series(dtype=float)) < 0).mean()), 4) if len(hs) else np.nan,
                "p_rank_recovery_30d": round(float(hs.get("fwd_rank_vel_30d", pd.Series(dtype=float)).gt(0).mean()), 4) if len(hs) else np.nan,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 9: PEER REJOIN vs PEER CATCHDOWN (10) — PRIMARY
# ---------------------------------------------------------------------------

def peer_rejoin_catchdown(loner, slim, family="BEHAVIORAL_10"):
    """Freeze t0 peers; track asset, peer median, residual -7..+30."""
    pm = C.load_peer_map(family)
    pm = pm.merge(loner[["event_index", "historical_date", "ret_1d"]],
                  on="event_index", how="left")
    pm = peer_forward_panel(pm, slim)
    pm["peer_return"] = pm["peer_return"].fillna(pm["ret_1d"])
    ev_sum = pm.groupby("event_index").agg(
        peer_n=("peer_return", "count"),
        peer_med0=("peer_return", "median"),
        **{f"peer_med{h}": (f"fwd{h}_cum", "median") for h in H},
    )
    out = loner.merge(ev_sum, left_on="event_index", right_index=True, how="left")
    out["residual0"] = out["ret_1d"] - out["peer_med0"]
    for h in H:
        out[f"resid{h}"] = out.get(f"signed_fwd{h}", 0) - out[f"peer_med{h}"]

    def classify(r):
        s = r["sigma_t0"]
        if not np.isfinite(s) or s <= 0 or not np.isfinite(r.get("peer_med7", np.nan)):
            return "AMBIGUOUS"
        asset_up = r.get("signed_fwd7", np.nan) > 0
        peers_down = r["peer_med7"] < -0.5 * s
        peers_flat = abs(r["peer_med7"]) < 0.5 * s
        resid_shrank = abs(r["resid7"]) < abs(r["residual0"])
        if asset_up and peers_down:
            return "BOTH_NORMALIZE"
        if peers_down:
            return "LOCAL_CONTAGION"
        if asset_up and peers_flat and resid_shrank:
            return "ASSET_REJOINS_PEERS"
        if asset_up and not peers_flat:
            return "AMBIGUOUS"
        if not asset_up and peers_flat:
            return "PERSISTENT_DECOUPLING"
        return "AMBIGUOUS"
    out["path_class"] = out.apply(classify, axis=1)
    return out, pm


# ---------------------------------------------------------------------------
# Section 10: PEER CATCHDOWN LEAD-LAG (11)
# ---------------------------------------------------------------------------

def catchdown_leadlag(path_df):
    sub = path_df[path_df["path_class"].isin(["LOCAL_CONTAGION"])]
    rows = []
    for h in [1, 2, 3, 5, 7]:
        rows.append({
            "horizon": h, "n": len(sub),
            "p_peer_negative": round(float((sub[f"peer_med{h}"] < 0).mean()), 4),
            "median_peer_return": round(float(sub[f"peer_med{h}"].median()), 5),
            "median_asset_return": round(float(sub.get(f"signed_fwd{h}", pd.Series(dtype=float)).median()), 5),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 11-12: DISLOCATION / FALSE-LONER SEQUENCES (12/13)
# ---------------------------------------------------------------------------

def true_dislocation_sequence(path_df):
    sub = path_df[path_df["path_class"] == "ASSET_REJOINS_PEERS"]
    seqs = []
    for _, ev in sub.iterrows():
        order = []
        for name, h in [("STABILIZATION", 2), ("1SIGMA", 3), ("2SIGMA", 7),
                        ("PRICE_REPAIR", 14)]:
            sf = ev.get(f"signed_fwd{h}", np.nan)
            s = ev["sigma_t0"]
            if np.isfinite(sf) and np.isfinite(s) and s > 0 and sf / s >= 1.0:
                order.append(name)
        if order:
            seqs.append("->".join(order))
    cnt = Counter(seqs)
    return pd.DataFrame([{"sequence": k, "n": v,
                          "pct": round(v / max(len(seqs), 1), 4)}
                         for k, v in cnt.most_common(10)])


def false_loner_sequence(cls, loner, slim):
    idx = set(cls[cls["final_class"].str.endswith("_FALSE")]["event_index"])
    sub = loner[loner["event_index"].isin(idx)].copy()
    if len(sub) < 20:
        return pd.DataFrame()
    # peer stress before vs asset shock: use behavioral peers at t0
    pm = C.load_peer_map("BEHAVIORAL_10")
    pm = pm.merge(sub[["event_index", "historical_date"]], on="event_index", how="left")
    pm = peer_forward_panel(pm, slim)
    pm["peer_return"] = pm["peer_return"].fillna(pm["ret_1d"])
    pmed = pm.groupby("event_index")["peer_return"].median().rename("peer_med_t0")
    sub = sub.merge(pmed, left_on="event_index", right_index=True, how="left")
    rows = []
    for lead, thr in [("PEER_LEADS", -0.5), ("SIMULTANEOUS", -0.25)]:
        pass
    # classify by t0 peer stress relative to asset shock
    sub["peer_stressed"] = sub["peer_med_t0"] < 0
    for grp, m in sub.groupby("peer_stressed"):
        pass
    out = sub[["event_index", "peer_med_t0", "z1", "rank_band", "sigma_t0",
               "ret_1d"]].copy()
    out["timing"] = np.where(
        out["peer_med_t0"] < 0,
        np.where(out["peer_med_t0"] < -0.5 * out["z1"] * out["sigma_t0"].fillna(0),
                 "PEER_LEADS", "SIMULTANEOUS"), "ASSET_LEADS")
    return out


# ---------------------------------------------------------------------------
# Section 13-16: PRD HARMONIZATION (14-17)
# ---------------------------------------------------------------------------

def prd_counts_agent2(loner):
    """Agent-2 (LF5) PRD counts per horizon using LF5 price/rank rules."""
    rows = []
    for h in [3, 7, 14, 30]:
        pr = loner.get(f"recover1s{h}", pd.Series(dtype=float)).fillna(False)
        rv = loner.get(f"fwd_rank_vel_{h}d", pd.Series(dtype=float))
        prd = (pr == True) & (rv < 0)
        rows.append({"horizon": h, "n_total": len(loner),
                     "n_prd": int(prd.sum()), "p_prd": round(float(prd.mean()), 4)})
    return pd.DataFrame(rows)


def harmonized_price_rank(loner, cls):
    rows = []
    df = loner.copy()
    df = df.merge(cls[["event_index", "final_class"]], on="event_index", how="left")
    for h in [3, 7, 14, 30]:
        pr = df.get(f"recover1s{h}", pd.Series(dtype=float)).fillna(False)
        rv = df.get(f"fwd_rank_vel_{h}d", pd.Series(dtype=float))
        df[f"state{h}"] = np.select(
            [(pr == True) & (rv > 0), (pr == True) & (rv <= 0),
             (pr == False) & (rv > 0)],
            ["PRICE_UP_RANK_UP", "PRICE_UP_RANK_DOWN", "PRICE_DOWN_RANK_UP"],
            default="PRICE_DOWN_RANK_DOWN")
        for bd, bands in [("26-500", C.COMPARE_BANDS),
                          ("501-1000", ["501-750", "751-1000"]),
                          ("1001-2000", ["1001-1500", "1501-2000"])]:
            g = df[df["rank_band"].isin(bands)]
            for st in ["PRICE_UP_RANK_UP", "PRICE_UP_RANK_DOWN",
                       "PRICE_DOWN_RANK_UP", "PRICE_DOWN_RANK_DOWN"]:
                m = g[f"state{h}"] == st
                rows.append({"horizon": h, "rank_region": bd, "state": st,
                             "n": int(m.sum()), "pct": round(float(m.mean()), 4)})
    return pd.DataFrame(rows)


def prd_beta_rescue(loner, slim, family="BEHAVIORAL_10"):
    prd = loner[loner.get("recover1s7", pd.Series(dtype=float)).fillna(False)
                & (loner.get("fwd_rank_vel_7d", pd.Series(dtype=float)) < 0)]
    if len(prd) < 20:
        return pd.DataFrame()
    pm = C.load_peer_map(family)
    pm = pm.merge(prd[["event_index", "historical_date"]], on="event_index", how="left")
    pm = peer_forward_panel(pm, slim)
    rows = []
    for h in [0, 3, 7, 14, 30]:
        if h == 0:
            med = pm.groupby("event_index")["peer_return"].median()
        else:
            med = pm.groupby("event_index")[f"fwd{h}_cum"].median()
        rows.append({
            "horizon": h, "n": len(prd),
            "median_peer_return": round(float(med.median()), 5) if len(med) else np.nan,
            "median_global_breadth": round(float(prd["top500_breadth_30d"].median()), 4),
            "median_asset_rank": round(float(prd["rank"].median()), 1),
        })
    return pd.DataFrame(rows)


def health_transitions(loner):
    rows = []
    df = loner.copy()
    for h in [3, 7, 14, 30]:
        pr = df.get(f"recover1s{h}", pd.Series(dtype=float)).fillna(False)
        rv = df.get(f"fwd_rank_vel_{h}d", pd.Series(dtype=float))
        df[f"st{h}"] = np.select(
            [(pr == True) & (rv > 0), (pr == True) & (rv <= 0),
             (pr == False) & (rv > 0)],
            ["PRU", "PRD", "PDU"], default="PDD")
    for a, b in [(3, 7), (7, 14), (14, 30)]:
        cnt = df.groupby([f"st{a}", f"st{b}"]).size().reset_index(name="n")
        cnt["transition"] = cnt[f"st{a}"] + "->" + cnt[f"st{b}"]
        for _, r in cnt.iterrows():
            rows.append({"from_h": a, "to_h": b, "transition": r["transition"],
                         "n": int(r["n"])})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 17-19: REVERSAL DEPTH / PRIMITIVE / FAILURE MIRRORS (18/19/20)
# ---------------------------------------------------------------------------

def reversal_depth_blocks(loner, cls):
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    df = loner.copy()
    df = df.merge(cls[["event_index", "final_class"]], on="event_index", how="left")
    df["y"] = df["rev7"].fillna(False).astype(int)
    df["isolation"] = (df["final_class"] == "TRUE_MULTI_PEER_LONER").astype(int)
    blocks = {
        "rank_only": ["rank"],
        "rank_plus_amp": ["rank", "z1"],
        "rank_plus_isolation": ["rank", "isolation"],
        "rank_plus_field": ["rank", "top500_breadth_30d", "top500_dispersion_30d"],
        "full": ["rank", "z1", "isolation", "top500_breadth_30d", "top500_dispersion_30d"],
    }
    rows = []
    t = df[np.isfinite(df["y"]) & df[["rank", "z1"]].notna().all(axis=1)].copy()
    for name, cols in blocks.items():
        tt = t[t[cols].notna().all(axis=1)]
        if len(tt) < 200 or tt["y"].nunique() < 2:
            continue
        X = tt[cols].to_numpy()
        try:
            clf = LogisticRegression(max_iter=500)
            clf.fit(X, tt["y"])
            auc = roc_auc_score(tt["y"], clf.predict_proba(X)[:, 1])
            rows.append({"block": name, "n": len(tt), "auc": round(auc, 4),
                         "coefs": {c: round(float(w), 4) for c, w in zip(cols, clf.coef_[0])}})
        except Exception:
            continue
    return pd.DataFrame(rows)


def reversal_primitive_audit(loner, cls):
    df = loner.copy()
    df = df.merge(cls[["event_index", "final_class"]], on="event_index", how="left")
    df["isolation"] = (df["final_class"] == "TRUE_MULTI_PEER_LONER").astype(int)
    primitives = {
        "shock_amplitude": "z1", "true_isolation": "isolation",
        "early_1sigma": "recover1s3", "rank_depth": "rank",
        "breadth": "top500_breadth_30d", "dispersion": "top500_dispersion_30d",
    }
    patches = {"26-500": C.COMPARE_BANDS, "501-1000": ["501-750", "751-1000"],
               "1001-2000": ["1001-1500", "1501-2000"]}
    rows = []
    for name, col in primitives.items():
        if col not in df.columns:
            continue
        signs = []
        for bd, bands in patches.items():
            g = df[df["rank_band"].isin(bands)].dropna(subset=[col, "rev7"])
            if len(g) < 50:
                continue
            r = np.corrcoef(g[col].to_numpy(float), g["rev7"].astype(float).to_numpy())[0, 1]
            if np.isfinite(r):
                signs.append(r)
        if not signs:
            verdict = "NULL"
        elif all(s > 0 for s in signs) or all(s < 0 for s in signs):
            verdict = "GLOBAL_PRIMITIVE"
        elif len(set(np.sign(signs))) == 1:
            verdict = "GLOBAL_PRIMITIVE"
        else:
            verdict = "LOCAL_NODE"
        rows.append({"primitive": name, "n_patches": len(signs),
                     "signs": [round(s, 3) for s in signs], "verdict": verdict})
    return pd.DataFrame(rows)


def failure_mirrors(loner, cls):
    df = loner.copy()
    df = df.merge(cls[["event_index", "final_class"]], on="event_index", how="left")
    m_true = df["final_class"] == "TRUE_MULTI_PEER_LONER"
    m_false = df["final_class"].str.endswith("_FALSE")
    pairs = [
        ("TRUE+EARLY_RECOVERY vs TRUE+NO_RECOVERY",
         m_true & df["recover1s3"].fillna(False),
         m_true & ~df["recover1s3"].fillna(False)),
        ("FALSE+PEER_RECOVERY vs FALSE+PEER_CONTAGION",
         m_false & df["rev7"].fillna(False),
         m_false & ~df["rev7"].fillna(False)),
    ]
    feats = ["z1", "rank", "vol_63d", "turnover", "rank_vel_7d",
             "top500_breadth_30d", "top500_dispersion_30d"]
    rows = []
    for name, m_s, m_f in pairs:
        s, f = df[m_s], df[m_f]
        if len(s) < 20 or len(f) < 20:
            continue
        for col in feats:
            if col not in df.columns:
                continue
            a, b = s[col].dropna(), f[col].dropna()
            if len(a) < 10 or len(b) < 10:
                continue
            d = (a.mean() - b.mean()) / max(a.std() + b.std(), 1e-9)
            rows.append({"pair": name, "feature": col,
                         "success_mean": round(float(a.mean()), 4),
                         "failure_mean": round(float(b.mean()), 4),
                         "cohend": round(float(d), 3),
                         "n_success": len(s), "n_failure": len(f)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 20: PROPAGATION RADIUS (21)
# ---------------------------------------------------------------------------

BAND_ORDER = ["26-100", "101-250", "251-500", "501-750", "751-1000",
              "1001-1500", "1501-2000"]


def _adjacent(band):
    i = BAND_ORDER.index(band) if band in BAND_ORDER else -1
    if i < 0:
        return []
    out = []
    if i > 0:
        out.append(BAND_ORDER[i - 1])
    if i < len(BAND_ORDER) - 1:
        out.append(BAND_ORDER[i + 1])
    return out


def propagation_radius(ev, loner):
    """Per-event extreme-event spillover at t0+h: same band, adjacent bands,
    distinct bands touched. Descriptive classification."""
    rows = []
    evd = ev[ev["rank_band"].isin(BAND_ORDER)][["historical_date", "rank_band",
                                                  "event_index", "z1"]].copy()
    evd = evd[evd["z1"] >= 2]
    for h in [1, 3, 7, 14]:
        tgt = loner[["event_index", "historical_date", "rank_band"]].copy()
        tgt["t_plus"] = tgt["historical_date"] + pd.Timedelta(days=h)
        m = evd.merge(tgt[["event_index", "t_plus", "rank_band"]],
                      left_on=["historical_date"], right_on=["t_plus"], how="inner")
        m = m[m["event_index_x"] != m["event_index_y"]]
        if len(m) == 0:
            rows.append({"horizon": h, "n_events": len(loner),
                         "band_spillover_per_event": 0.0,
                         "adjacent_band_spillover_per_event": 0.0,
                         "multi_band_spillover_per_event": 0.0,
                         "pct_events_with_band_spillover": 0.0})
            continue
        same_band = m[m["rank_band_x"] == m["rank_band_y"]]
        adj_mask = m.apply(lambda r: r["rank_band_x"] in _adjacent(r["rank_band_y"]),
                           axis=1)
        adj = m[adj_mask]
        multi = m.groupby("event_index_y")["rank_band_x"].nunique()
        sb = same_band.groupby("event_index_y").size()
        rows.append({
            "horizon": h, "n_events": len(loner),
            "band_spillover_per_event": round(float(sb.mean()), 4),
            "adjacent_band_spillover_per_event": round(float(adj.groupby("event_index_y").size().mean()), 4),
            "multi_band_spillover_per_event": round(float(multi.mean()), 4),
            "pct_events_with_band_spillover": round(float((sb > 0).mean()), 4),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 21-22: 4-STATE AGE + SHMC/SHHM (22/23)
# ---------------------------------------------------------------------------

def loner_4state_age(loner, cls):
    df = loner.copy()
    df = df.merge(cls[["event_index", "final_class"]], on="event_index", how="left")
    df["loner"] = np.where(df["final_class"] == "TRUE_MULTI_PEER_LONER", "TRUE",
                  np.where(df["final_class"].str.endswith("_FALSE"), "FALSE", "AMBIGUOUS"))
    df = C.merge_age(df)
    cell_map = {"HIGH_BREADTH_HIGH_DISP": "HH", "HIGH_BREADTH_LOW_DISP": "HL",
                "LOW_BREADTH_HIGH_DISP": "LH", "LOW_BREADTH_LOW_DISP": "LL"}
    df["cell4"] = df["field_cell"].map(cell_map)
    rows = []
    for cell4 in ["HH", "HL", "LH", "LL"]:
        for ab in ["AGE_1", "AGE_2_3", "AGE_4_7", "AGE_8_14", "AGE_15_PLUS"]:
            g = df[(df["cell4"] == cell4) & (df["age_band"] == ab)]
            if len(g) < 20:
                continue
            for lon in ["TRUE", "FALSE"]:
                gg = g[g["loner"] == lon]
                if len(gg) < 10:
                    continue
                rows.append({
                    "cell": cell4, "age_band": ab, "loner": lon, "n": len(gg),
                    "p_1s_recovery_7d": round(float(gg["recover1s7"].fillna(False).mean()), 4),
                    "p_reversal_7d": round(float(gg["rev7"].fillna(False).mean()), 4),
                    "p_new_low_30d": round(float((gg["signed_fwd30"] < 0).mean()), 4),
                    "p_rank_repair_30d": round(float(gg["fwd_rank_vel_30d"].gt(0).mean()), 4),
                })
    return pd.DataFrame(rows)


def shmc_placement(loner, cls):
    df = loner.copy()
    df = df.merge(cls[["event_index", "final_class"]], on="event_index", how="left")
    df["grp"] = np.where(df["momentum_state"] == "SHORT_HOT_MEDIUM_COLD", "SHMC",
                np.where(df["momentum_state"] == "SHORT_HOT_MEDIUM_HOT", "SHHM", "OTHER"))
    rows = []
    for grp in ["SHMC", "SHHM"]:
        g = df[df["grp"] == grp]
        if len(g) < 20:
            continue
        rows.append({
            "group": grp, "n": len(g),
            "p_true_loner": round(float((g["final_class"] == "TRUE_MULTI_PEER_LONER").mean()), 4),
            "p_false_loner": round(float(g["final_class"].str.endswith("_FALSE").mean()), 4),
            "p_1s_recovery_7d": round(float(g["recover1s7"].fillna(False).mean()), 4),
            "p_reversal_7d": round(float(g["rev7"].fillna(False).mean()), 4),
            "median_z1": round(float(g["z1"].median()), 3),
        })
    if not rows:
        return pd.DataFrame([{"group": "NONE", "status": "LOW_N"}])
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 23: LOCAL SEQUENCE ATLAS (24)
# ---------------------------------------------------------------------------

def local_sequence_atlas(loner, cls, path_df):
    rows = []
    t_idx = cls[cls["final_class"] == "TRUE_MULTI_PEER_LONER"]["event_index"]
    t = loner[loner["event_index"].isin(t_idx)]
    if len(t) >= MIN_EVENTS:
        s1 = t[t["recover1s3"].fillna(False)]
        s2 = t[(t["signed_fwd7"] / t["sigma_t0"]) >= 2]
        rejoin = path_df[path_df["path_class"] == "ASSET_REJOINS_PEERS"]["event_index"]
        rank_rep = t[t["fwd_rank_vel_30d"] > 0]
        rows.append({"sequence": "TRUE_LONER->1SIGMA->2SIGMA->PEER_REJOIN->RANK_REPAIR",
                     "n_total": len(t), "n_1s": int(len(s1)), "n_2s": int(len(s2)),
                     "n_rejoin": int(len(rejoin)), "n_rank_repair": int(len(rank_rep)),
                     "pct_full": round(len(rank_rep) / max(len(t), 1), 4)})
        no1 = t[~t["recover1s7"].fillna(False)]
        newlow = no1[no1["signed_fwd30"] < 0]
        rows.append({"sequence": "TRUE_LONER->NO_1SIGMA->NEW_LOW",
                     "n_total": len(t), "n_no_1s": int(len(no1)), "n_new_low": int(len(newlow)),
                     "pct_full": round(len(newlow) / max(len(t), 1), 4)})
    f_idx = cls[cls["final_class"].str.endswith("_FALSE")]["event_index"]
    f = loner[loner["event_index"].isin(f_idx)]
    if len(f) >= MIN_EVENTS:
        cont = path_df[path_df["path_class"] == "LOCAL_CONTAGION"]["event_index"]
        rows.append({"sequence": "FALSE_LONER->PEER_STRESS->LOCAL_CONTAGION",
                     "n_total": len(f), "n_contagion": int(len(cont)),
                     "pct_full": round(len(cont) / max(len(f), 1), 4)})
    prd = loner[loner.get("recover1s7", pd.Series(dtype=float)).fillna(False)
                & (loner.get("fwd_rank_vel_7d", pd.Series(dtype=float)) < 0)]
    if len(prd) >= MIN_EVENTS:
        still_up = prd[prd.get("recover1s14", pd.Series(dtype=float)).fillna(False)]
        rank_fail = still_up[still_up.get("fwd_rank_vel_14d", pd.Series(dtype=float)).fillna(0) < 0]
        rows.append({"sequence": "PRD->PEER_HEALTHY->PRICE_STAYS_UP->RANK_FAILS",
                     "n_total": len(prd), "n_price_stays_up": int(len(still_up)),
                     "n_rank_fails": int(len(rank_fail)),
                     "pct_full": round(len(rank_fail) / max(len(prd), 1), 4)})
    if not rows:
        return pd.DataFrame([{"sequence": "NONE", "status": "LOW_N"}])
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading...", flush=True)
    ev, loner, loner3, slim, quality = load_all()
    print(f"events {len(ev)} | loner 2s {len(loner)} | 3s {len(loner3)}", flush=True)

    print("\n=== S1: Peer validation depth (02) ===", flush=True)
    vd = peer_validation_depth(loner, quality, slim)
    vd.to_csv(R / "02_PEER_VALIDATION_DEPTH.csv", index=False)
    print(vd[["peer_family", "event_coverage", "jaccard_persistence"]].to_string(index=False))

    print("\n=== S2: Consensus loner (03) ===", flush=True)
    cls = consensus_loner(loner, slim)
    cls.to_csv(R / "03_CONSENSUS_LONER_CLASSIFICATION.csv", index=False)
    print(cls["final_class"].value_counts().to_string())

    print("\n=== S3: Rank-depth loner map (04) ===", flush=True)
    rdm = rank_depth_map(loner, cls)
    rdm.to_csv(R / "04_RANK_DEPTH_LONER_MAP.csv", index=False)
    print(rdm.to_string(index=False))

    print("\n=== S4: Rank patch geometry (05) ===", flush=True)
    rpg = rank_patch_geometry(ev, loner, cls)
    rpg.to_csv(R / "05_RANK_PATCH_BASKET_GEOMETRY.csv", index=False)
    print(rpg.to_string(index=False))

    print("\n=== S5: Loner outcomes (06) ===", flush=True)
    lo = loner_outcomes(cls, loner)
    lo.to_csv(R / "06_TRUE_FALSE_LONER_OUTCOMES.csv", index=False)
    print(f"{len(lo)} rows")

    print("\n=== S6: Multi-sigma ladder (07) ===", flush=True)
    clock, ladder = multi_sigma_ladder(loner)
    ladder.to_csv(R / "07_MULTI_SIGMA_RECOVERY_LADDER.csv", index=False)
    print(ladder.head(8).to_string(index=False))

    print("\n=== S7: Shock-recovery amplitude (08) ===", flush=True)
    sra = shock_recovery_amplitude(loner)
    sra.to_csv(R / "08_SHOCK_RECOVERY_AMPLITUDE_MATRIX.csv", index=False)
    print(sra.to_string(index=False))

    print("\n=== S8: Loner sigma matrix (09) ===", flush=True)
    lsm = loner_sigma_matrix(loner, cls)
    lsm.to_csv(R / "09_LONER_SIGMA_MATRIX.csv", index=False)
    print(f"{len(lsm)} rows")

    print("\n=== S9: Peer rejoin/catchdown (10) PRIMARY ===", flush=True)
    path_df, pm = peer_rejoin_catchdown(loner, slim)
    path_df.to_csv(R / "10_PEER_REJOIN_CATCHDOWN.csv", index=False)
    print(path_df["path_class"].value_counts().to_string())

    print("\n=== S10: Catchdown lead-lag (11) ===", flush=True)
    cll = catchdown_leadlag(path_df)
    cll.to_csv(R / "11_PEER_CATCHDOWN_LEADLAG.csv", index=False)
    print(cll.to_string(index=False))

    print("\n=== S11: True dislocation sequence (12) ===", flush=True)
    tds = true_dislocation_sequence(path_df)
    tds.to_csv(R / "12_TRUE_DISLOCATION_SEQUENCE.csv", index=False)
    print(tds.to_string(index=False))

    print("\n=== S12: False loner sequence (13) ===", flush=True)
    fls = false_loner_sequence(cls, loner, slim)
    if len(fls):
        fls.to_csv(R / "13_FALSE_LONER_SEQUENCE.csv", index=False)
        print(fls["timing"].value_counts().to_string())
    else:
        pd.DataFrame([{"status": "LOW_N"}]).to_csv(R / "13_FALSE_LONER_SEQUENCE.csv", index=False)

    print("\n=== S13: PRD harmonization counts (for 14) ===", flush=True)
    prd2 = prd_counts_agent2(loner)
    print(prd2.to_string(index=False))

    print("\n=== S14: Harmonized price-rank matrix (15) ===", flush=True)
    hpr = harmonized_price_rank(loner, cls)
    hpr.to_csv(R / "15_HARMONIZED_PRICE_RANK_MATRIX.csv", index=False)
    print(hpr[hpr["horizon"] == 7].to_string(index=False))

    print("\n=== S15: PRD beta rescue anatomy (16) ===", flush=True)
    pbr = prd_beta_rescue(loner, slim)
    if len(pbr):
        pbr.to_csv(R / "16_PRD_BETA_RESCUE_ANATOMY.csv", index=False)
        print(pbr.to_string(index=False))
    else:
        pd.DataFrame([{"status": "LOW_N"}]).to_csv(R / "16_PRD_BETA_RESCUE_ANATOMY.csv", index=False)

    print("\n=== S16: Health transitions (17) ===", flush=True)
    ht = health_transitions(loner)
    ht.to_csv(R / "17_HEALTH_TRANSITION_SEQUENCES.csv", index=False)
    print(ht.head(10).to_string(index=False))

    print("\n=== S17: Reversal depth blocks (18) ===", flush=True)
    rdb = reversal_depth_blocks(loner, cls)
    rdb.to_csv(R / "18_REVERSAL_DEPTH_TRUE_PEER_CONTROL.csv", index=False)
    print(rdb.to_string(index=False))

    print("\n=== S18: Reversal primitive audit (19) ===", flush=True)
    rpa = reversal_primitive_audit(loner, cls)
    rpa.to_csv(R / "19_REVERSAL_PRIMITIVE_AUDIT.csv", index=False)
    print(rpa.to_string(index=False))

    print("\n=== S19: Failure mirrors (20) ===", flush=True)
    fm = failure_mirrors(loner, cls)
    fm.to_csv(R / "20_FAILURE_MIRRORS.csv", index=False)
    print(f"{len(fm)} rows")

    print("\n=== S20: Propagation radius (21) ===", flush=True)
    pr = propagation_radius(ev, loner)
    pr.to_csv(R / "21_PROPAGATION_RADIUS.csv", index=False)
    print(pr.to_string(index=False))

    print("\n=== S21: Loner 4-state age (22) ===", flush=True)
    l4s = loner_4state_age(loner, cls)
    l4s.to_csv(R / "22_LONER_4STATE_AGE_MATRIX.csv", index=False)
    print(f"{len(l4s)} rows")

    print("\n=== S22: SHMC/SHHM placement (23) ===", flush=True)
    shmc = shmc_placement(loner, cls)
    shmc.to_csv(R / "23_SHMC_SHHM_PEER_PLACEMENT.csv", index=False)
    print(shmc.to_string(index=False))

    print("\n=== S23: Local sequence atlas (24) ===", flush=True)
    lsa = local_sequence_atlas(loner, cls, path_df)
    lsa.to_csv(R / "24_LOCAL_SEQUENCE_ATLAS.csv", index=False)
    print(lsa.to_string(index=False))

    print("\n=== COMPLETE ===", flush=True)
    return cls, path_df


if __name__ == "__main__":
    main()
