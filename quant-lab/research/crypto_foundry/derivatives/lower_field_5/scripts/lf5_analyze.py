"""LOWER-FIELD-5 comprehensive analysis — TRUE PEER FAMILIES (optimized).

Rebuilds all downstream analyses (sections 6-21 of the preregistration)
using the five peer systems built in lf5_peer_maps.py. Vectorized where
possible; avoids per-event Python loops.

No strategy. No PnL. No execution. Research only.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import lf5_common as C

warnings.filterwarnings("ignore", category=RuntimeWarning)

R = C.ROOT
H = [1, 2, 3, 5, 7, 10, 14, 21, 30]
MIN_EVENTS = 50


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_all():
    df = pd.read_parquet(C.SUBSTRATE)
    df["historical_date"] = pd.to_datetime(df["historical_date"])
    ev = pd.read_parquet(C.CACHE / "lf5_events.parquet")
    ev["historical_date"] = pd.to_datetime(ev["historical_date"])
    rk = pd.read_parquet(R / "07_RANK_PEERS.parquet")
    beh = pd.read_parquet(R / "08_BEHAVIORAL_PEERS.parquet")
    corr = pd.read_parquet(R / "09_CORRELATION_PEERS.parquet")
    st = pd.read_parquet(R / "10_STATE_PEERS.parquet")
    hy = pd.read_parquet(R / "11_HYBRID_LOCAL_BASKETS.parquet")
    return df, ev, rk, beh, corr, st, hy


def _loner_down(ev, amp="2s"):
    mask = (ev["participation"] == "ISOLATED") & (ev["event_sign"] < 0)
    if amp == "3s":
        mask = mask & (ev["z1"] >= 3)
    return ev[mask & ev["rank_band"].isin(C.PRIMARY_BANDS + C.COMPARE_BANDS)].copy()


def _loner_up(ev, amp="2s"):
    mask = (ev["participation"] == "ISOLATED") & (ev["event_sign"] > 0)
    if amp == "3s":
        mask = mask & (ev["z1"] >= 3)
    return ev[mask & ev["rank_band"].isin(C.PRIMARY_BANDS + C.COMPARE_BANDS)].copy()


def _loner_all(ev, amp="2s"):
    mask = ev["participation"] == "ISOLATED"
    if amp == "3s":
        mask = mask & (ev["z1"] >= 3)
    return ev[mask & ev["rank_band"].isin(C.PRIMARY_BANDS + C.COMPARE_BANDS)].copy()


# ---------------------------------------------------------------------------
# Peer summary per event
# ---------------------------------------------------------------------------

def peer_event_summary(peer_df, family, ev_idx):
    sub = peer_df[(peer_df["peer_family"] == family) &
                  (peer_df["event_index"].isin(ev_idx))]
    if len(sub) == 0:
        return pd.DataFrame()
    g = sub.groupby("event_index")
    agg = g.agg(
        peer_n=("peer_id", "count"),
        peer_median_return=("peer_return", "median"),
        peer_dispersion=("peer_return", "std"),
        peer_same_sign=("peer_return", lambda x: (np.sign(x) == np.sign(x.median())).mean()),
        peer_tail_frac=("peer_return", lambda x: (x.abs() > 2 * max(x.std(), 1e-12)).mean()),
        nearest_return=("peer_return", "first"),
    ).reset_index()
    worst = g["peer_return"].min().rename("peer_worst_return").reset_index()
    agg = agg.merge(worst, on="event_index", how="left")
    return agg


def build_peer_panels(events, rk, beh, corr, st, hy):
    ev_idx = set(events.index)
    families = {
        "RANK_50": rk, "BEHAVIORAL_10": beh, "CORR_60_10": corr,
        "STATE": st, "HYBRID_10": hy,
    }
    panels = {}
    for fam_name, peer_df in families.items():
        ps = peer_event_summary(peer_df, fam_name, ev_idx)
        if len(ps) == 0:
            panels[fam_name] = events.copy()
            for c in ["peer_n", "peer_median_return", "peer_dispersion",
                       "peer_same_sign", "peer_tail_frac", "nearest_return", "peer_worst_return"]:
                panels[fam_name][c] = np.nan
            continue
        merged = events.merge(ps, left_index=True, right_on="event_index", how="left")
        merged["asset_peer_residual"] = merged["ret_1d"] - merged["peer_median_return"]
        merged["standardized_residual"] = merged["asset_peer_residual"] / (
            merged["peer_dispersion"].replace(0, np.nan))
        panels[fam_name] = merged
    return panels


# ---------------------------------------------------------------------------
# Section 6+7: TRUE LONER vs FALSE LONER TAXONOMY
# ---------------------------------------------------------------------------

def true_false_loner_audit(panels, events):
    rows = []
    for band in sorted(events["rank_band"].unique()):
        sub = events[events["rank_band"] == band]
        n = len(sub)
        for fam_name in ["RANK_50", "BEHAVIORAL_10", "CORR_60_10", "STATE", "HYBRID_10"]:
            panel = panels.get(fam_name)
            if panel is None:
                continue
            psub = panel[panel["rank_band"] == band]
            has_peer = psub["peer_n"].notna() & (psub["peer_n"] > 0)
            n_peer = has_peer.sum()

            if fam_name in ("BEHAVIORAL_10", "CORR_60_10", "HYBRID_10"):
                within = (psub["asset_peer_residual"].abs() <
                          psub["peer_dispersion"].replace(0, np.nan))
                n_false = int((has_peer & within).sum())
                n_true = int((has_peer & ~within).sum())
            else:
                n_false = 0
                n_true = np.nan

            rows.append({
                "rank_band": band, "peer_family": fam_name,
                "n_events": n, "n_peer_matched": int(n_peer),
                "true_loners": n_true if n_true == n_true else np.nan,
                "false_loners": n_false if n_false > 0 else np.nan,
                "pct_false": round(n_false / max(n_peer, 1) * 100, 1) if n_false > 0 else np.nan,
                "status": "COMPUTED" if n_peer > 0 else "NO_PEERS",
            })

    # Cross-band totals for behavioral/corr/hybrid
    for fam_name in ["BEHAVIORAL_10", "CORR_60_10", "HYBRID_10"]:
        panel = panels.get(fam_name)
        if panel is None:
            continue
        has_peer = panel["peer_n"].notna() & (panel["peer_n"] > 0)
        within = (panel["asset_peer_residual"].abs() <
                  panel["peer_dispersion"].replace(0, np.nan))
        total = int(has_peer.sum())
        false_n = int((has_peer & within).sum())
        true_n = int((has_peer & ~within).sum())
        rows.append({
            "rank_band": "ALL", "peer_family": fam_name,
            "n_events": len(panel), "n_peer_matched": total,
            "true_loners": true_n, "false_loners": false_n if false_n > 0 else np.nan,
            "pct_false": round(false_n / max(total, 1) * 100, 1) if false_n > 0 else np.nan,
            "status": "CROSS_BAND_TOTAL",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 8: PRE-EVENT PEER DIVERGENCE (vectorized)
# ---------------------------------------------------------------------------

def pre_event_divergence(events, df, panels):
    """Build -30D to t0 paths using vectorized merge instead of per-event loop."""
    horizons = [-30, -21, -14, -10, -7, -5, -3, -2, -1, 0]
    # Create shifted date columns for each horizon
    ev_idx = events.index.name or events.index
    asset_dates = events[["historical_date", "cmc_id", "rank_band"]].copy()
    asset_dates["event_index"] = asset_dates.index
    for h in horizons:
        asset_dates[f"target_date_{h}"] = asset_dates["historical_date"] + pd.Timedelta(days=h)

    # Build a lookup from (cmc_id, date) -> features
    df_idx = df.set_index(["cmc_id", "historical_date"])

    # Collect all needed target dates
    all_rows = []
    for _, row in asset_dates.iterrows():
        cid = row["cmc_id"]
        for h in horizons:
            td = row[f"target_date_{h}"]
            if (cid, td) in df_idx.index:
                r = df_idx.loc[(cid, td)]
                all_rows.append({
                    "event_index": row["event_index"],
                    "asset_id": cid,
                    "rank_band": row["rank_band"],
                    "days_before": h,
                    "asset_ret_1d": r.get("ret_1d", np.nan),
                    "asset_rank": r.get("rank", np.nan),
                    "asset_vol_63d": r.get("vol_63d", np.nan),
                    "asset_volume": r.get("volume_24h_usd", np.nan),
                    "rank_vel_3d": r.get("rank_vel_3d", np.nan),
                    "rank_vel_7d": r.get("rank_vel_7d", np.nan),
                    "momentum_state": str(r.get("momentum_state", np.nan)),
                })
            else:
                all_rows.append({
                    "event_index": row["event_index"], "asset_id": cid,
                    "rank_band": row["rank_band"], "days_before": h,
                    "asset_ret_1d": np.nan, "asset_rank": np.nan,
                    "asset_vol_63d": np.nan, "asset_volume": np.nan,
                    "rank_vel_3d": np.nan, "rank_vel_7d": np.nan,
                    "momentum_state": "nan",
                })

    path_df = pd.DataFrame(all_rows)
    summary = path_df.groupby(["rank_band", "days_before"]).agg(
        n=("event_index", "nunique"),
        median_ret_1d=("asset_ret_1d", "median"),
        median_rank=("asset_rank", "median"),
        median_vol=("asset_vol_63d", "median"),
        median_rank_vel_3d=("rank_vel_3d", "median"),
        median_rank_vel_7d=("rank_vel_7d", "median"),
        pct_short_hot=("momentum_state", lambda x: x.str.contains("SHORT_HOT", na=False).mean()),
    ).reset_index()
    return path_df, summary


# ---------------------------------------------------------------------------
# Section 9: POST-EVENT PEER PATHS
# ---------------------------------------------------------------------------

def post_event_peer_paths(events, panels):
    horizons = [1, 2, 3, 5, 7, 10, 14, 21, 30]
    rows = []
    for _, ev in events.iterrows():
        for h in horizons:
            rows.append({
                "event_index": ev.name,
                "asset_id": ev["cmc_id"],
                "rank_band": ev["rank_band"],
                "z1": ev["z1"],
                "horizon": h,
                "asset_signed_return": ev.get(f"signed_fwd{h}", np.nan),
                "reversal": ev.get(f"rev{h}", np.nan),
                "recover_1s": ev.get(f"recover1s{h}", np.nan),
                "rank_vel": ev.get(f"fwd_rank_vel_{h}d", np.nan),
            })

    path_df = pd.DataFrame(rows)
    for fam_name, panel in panels.items():
        cols = ["event_index", "peer_median_return", "peer_dispersion",
                "peer_same_sign", "asset_peer_residual"]
        avail = [c for c in cols if c in panel.columns]
        if avail:
            sub = panel[avail].drop_duplicates("event_index")
            path_df = path_df.merge(sub, on="event_index", how="left",
                                    suffixes=("", f"_{fam_name}"))

    summary = path_df.groupby(["rank_band", "horizon"]).agg(
        n=("event_index", "count"),
        median_asset_return=("asset_signed_return", "median"),
        pct_reversal=("reversal", "mean"),
        pct_1s_recovery=("recover_1s", "mean"),
        median_rank_vel=("rank_vel", "median"),
    ).reset_index()
    return path_df, summary


# ---------------------------------------------------------------------------
# Section 10: TEMP SHOCK vs CONTAGION
# ---------------------------------------------------------------------------

def temp_shock_vs_contagion(events, panels):
    events = events.copy()
    r7 = events.get("recover1s7", pd.Series(False, index=events.index))
    rv7 = events.get("rev7", pd.Series(False, index=events.index))
    sf7 = events.get("signed_fwd7", pd.Series(0.0, index=events.index))
    sig = events.get("sigma_t0", pd.Series(1.0, index=events.index))

    events["outcome_class"] = np.select(
        [r7 == True, rv7 == True],
        ["EARLY_RECOVERY", "REVERSAL"],
        default="AMBIGUOUS"
    )
    ambig = events["outcome_class"] == "AMBIGUOUS"
    events.loc[ambig, "outcome_class"] = np.select(
        [sf7[ambig] < -sig[ambig], sf7[ambig] > 0],
        ["CONTINUED_DECLINE", "PARTIAL_RECOVERY"],
        default="AMBIGUOUS"
    )

    pre_features = ["z1", "vol_63d", "turnover", "rank_vel_7d", "rank_vel_14d",
                    "listing_age_days", "log10_mcap", "btc_ret_1d",
                    "top500_breadth_30d", "top500_dispersion_30d"]

    rows = []
    for band in sorted(events["rank_band"].unique()):
        sub = events[events["rank_band"] == band]
        for cls in sub["outcome_class"].unique():
            cs = sub[sub["outcome_class"] == cls]
            if len(cs) < 5:
                continue
            row = {"rank_band": band, "class": cls, "n": len(cs)}
            for f in pre_features:
                if f in cs.columns:
                    row[f"median_{f}"] = C.safe_median(cs[f])
            for fam_name, panel in panels.items():
                if "asset_peer_residual" in panel.columns:
                    merged = cs.merge(
                        panel[["event_index", "asset_peer_residual", "peer_dispersion"]],
                        left_index=True, right_on="event_index", how="left")
                    row[f"median_residual_{fam_name}"] = C.safe_median(merged["asset_peer_residual"])
                    row[f"median_peer_disp_{fam_name}"] = C.safe_median(merged["peer_dispersion"])
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 11-12: 1σ RECOVERY CLOCK
# ---------------------------------------------------------------------------

def sigma_recovery_clock(events):
    horizons = [1, 2, 3, 5, 7, 10, 14, 21, 30]
    rows = []
    for _, ev in events.iterrows():
        sigma = ev["sigma_t0"]
        if pd.isna(sigma) or sigma <= 0:
            continue
        for h in horizons:
            signed = ev.get(f"signed_fwd{h}", np.nan)
            rec_sigma = signed / sigma if pd.notna(signed) else np.nan
            rows.append({
                "event_index": ev.name, "asset_id": ev["cmc_id"],
                "rank_band": ev["rank_band"], "z1": ev["z1"],
                "horizon": h, "signed_return": signed,
                "recovery_sigma": rec_sigma, "sigma": sigma,
            })

    clock = pd.DataFrame(rows)
    if len(clock) == 0:
        return clock, pd.DataFrame()

    rc_rows = []
    for band in sorted(events["rank_band"].unique()):
        band_idx = set(events[events["rank_band"] == band].index)
        bc = clock[clock["event_index"].isin(band_idx)]

        for label, filt in [
            ("1SIGMA_BY_1D", lambda c: (c["horizon"] == 1) & (c["recovery_sigma"] >= 1.0)),
            ("1SIGMA_BY_2D", lambda c: (c["horizon"] == 2) & (c["recovery_sigma"] >= 1.0)),
            ("1SIGMA_BY_3D", lambda c: (c["horizon"] == 3) & (c["recovery_sigma"] >= 1.0)),
            ("1SIGMA_BY_5D", lambda c: (c["horizon"] == 5) & (c["recovery_sigma"] >= 1.0)),
            ("1SIGMA_BY_7D", lambda c: (c["horizon"] == 7) & (c["recovery_sigma"] >= 1.0)),
            ("NO_1SIGMA_BY_7D", lambda c: (c["horizon"] == 7) & (c["recovery_sigma"] < 1.0)),
        ]:
            q = bc[filt(bc)]
            hit_idx = set(q["event_index"])
            at7 = bc[(bc["horizon"] == 7) & (bc["event_index"].isin(hit_idx))]
            if "NO" not in label and len(at7) > 0:
                p_full = round(float((at7["recovery_sigma"] >= 2.0).mean()), 3)
                p_new_low = round(float((at7["recovery_sigma"] < 0).mean()), 3)
            else:
                p_full = np.nan
                p_new_low = np.nan

            rc_rows.append({
                "rank_band": band, "class": label,
                "n": len(q),
                "p_full_repair_7d": p_full,
                "p_new_low_7d": p_new_low,
                "status": "COMPUTED" if len(q) >= MIN_EVENTS else "LOW_N",
            })

    return clock, pd.DataFrame(rc_rows)


# ---------------------------------------------------------------------------
# Section 13: PRICE vs RANK HEALTH CLOCKS
# ---------------------------------------------------------------------------

def price_rank_clocks(events):
    rows = []
    for _, ev in events.iterrows():
        for h in [3, 7, 14, 30]:
            rec = ev.get(f"recover1s{h}", False)
            rv = ev.get(f"fwd_rank_vel_{h}d", np.nan)
            price_state = "PRICE_UP" if rec else "PRICE_DOWN"
            rank_state = "RANK_UP" if (pd.notna(rv) and rv > 0) else "RANK_DOWN"
            rows.append({
                "event_index": ev.name, "asset_id": ev["cmc_id"],
                "rank_band": ev["rank_band"], "z1": ev["z1"], "horizon": h,
                "price_state": price_state, "rank_state": rank_state,
                "cross_state": f"{price_state}_{rank_state}",
                "signed_return": ev.get(f"signed_fwd{h}", np.nan),
                "rank_vel": rv,
                "recovery_sigma": ev.get(f"signed_fwd{h}", np.nan) / ev["sigma_t0"]
                    if pd.notna(ev.get(f"signed_fwd{h}")) and ev["sigma_t0"] > 0 else np.nan,
            })

    cross = pd.DataFrame(rows)
    if len(cross) == 0:
        return pd.DataFrame()

    summary = cross.groupby(["rank_band", "horizon", "cross_state"]).agg(
        n=("event_index", "count"),
        median_return=("signed_return", "median"),
        median_rank_vel=("rank_vel", "median"),
    ).reset_index()
    summary["pct_of_band"] = summary.groupby(["rank_band", "horizon"])["n"].transform(
        lambda x: x / x.sum())
    return summary


# ---------------------------------------------------------------------------
# Section 14: HEALTH STRESS RESPONSE
# ---------------------------------------------------------------------------

def health_stress_response(events, df):
    rows = []
    df_idx = df.set_index(["cmc_id", "historical_date"]).sort_index()

    for _, ev in events.iterrows():
        pre_rv7 = ev.get("rank_vel_7d", np.nan)
        if pd.isna(pre_rv7) or pre_rv7 >= 0:
            continue
        cid = ev["cmc_id"]
        ev_date = ev["historical_date"]
        fwd7 = ev.get("signed_fwd7", np.nan)
        fwd7_rv = ev.get("fwd_rank_vel_7d", np.nan)
        if pd.isna(fwd7):
            continue

        # Check BTC support in next 7D
        btc_supportive = False
        for d in range(1, 8):
            td = ev_date + pd.Timedelta(days=d)
            if (cid, td) in df_idx.index:
                r = df_idx.loc[(cid, td)]
                if r.get("btc_ret_1d", 0) > 0:
                    btc_supportive = True
                    break

        if fwd7 > 0 and pd.notna(fwd7_rv) and fwd7_rv > 0:
            response = "HEALTHY_RESPONSE"
        elif fwd7 > 0:
            response = "PRICE_ONLY_RESPONSE"
        elif pd.notna(fwd7_rv) and fwd7_rv > 0:
            response = "RANK_ONLY_RESPONSE"
        elif fwd7 < -ev["sigma_t0"]:
            response = "WEAK_RESPONSE"
        else:
            response = "NO_RESPONSE"

        rows.append({
            "event_index": ev.name, "asset_id": cid,
            "rank_band": ev["rank_band"], "pre_rank_vel_7d": pre_rv7,
            "btc_supportive": btc_supportive, "response": response,
            "fwd7_return": fwd7, "fwd7_rank_vel": fwd7_rv,
        })

    resp_df = pd.DataFrame(rows)
    if len(resp_df) == 0:
        return resp_df
    summary = resp_df.groupby(["rank_band", "response"]).agg(
        n=("event_index", "count"),
        median_fwd7_return=("fwd7_return", "median"),
        pct_btc_supportive=("btc_supportive", "mean"),
    ).reset_index()
    return summary


# ---------------------------------------------------------------------------
# Section 15: RECONCILIATION
# ---------------------------------------------------------------------------

def rank_reconciliation(events):
    rows = []
    for band in sorted(events["rank_band"].unique()):
        sub = events[events["rank_band"] == band]
        if len(sub) < 10:
            continue
        outcomes = {
            "1s_recovery_7d": ("recover1s7", "mean"),
            "full_recovery_30d": ("recover1s30", "mean"),
            "reversal_7d": ("rev7", "mean"),
            "rank_recovery_30d": ("fwd_rank_vel_30d", "median"),
            "new_low_30d": ("rev30", "mean"),
        }
        for label, (col, agg) in outcomes.items():
            if col in sub.columns:
                val = getattr(sub[col], agg)()
            else:
                val = np.nan
            rows.append({
                "rank_band": band, "outcome": label,
                "value": round(val, 3) if pd.notna(val) else np.nan,
                "n": len(sub), "status": "COMPUTED",
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 16: ACTIVE LIQUIDITY
# ---------------------------------------------------------------------------

def active_liquidity(events):
    rows = []
    for band in sorted(events["rank_band"].unique()):
        sub = events[events["rank_band"] == band].copy()
        if len(sub) < 10:
            continue
        try:
            sub["vol_tercile"] = pd.qcut(sub["volume_24h_usd"].rank(method="first"),
                                         3, labels=["LOW", "MED", "HIGH"], duplicates="drop")
        except ValueError:
            continue
        for vt in sub["vol_tercile"].unique():
            qs = sub[sub["vol_tercile"] == vt]
            rows.append({
                "rank_band": band, "liquidity_bucket": str(vt), "n": len(qs),
                "pct_1s_recovery_7d": C.safe_mean(qs.get("recover1s7", pd.Series(dtype=float))),
                "pct_reversal_7d": C.safe_mean(qs.get("rev7", pd.Series(dtype=float))),
                "pct_full_recovery_30d": C.safe_mean(qs.get("recover1s30", pd.Series(dtype=float))),
                "median_turnover": C.safe_median(qs["turnover"]),
                "status": "COMPUTED",
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 17: BROAD UP/DOWN
# ---------------------------------------------------------------------------

def broad_up_down(events):
    rows = []
    for band in sorted(events["rank_band"].unique()):
        for part in ["ISOLATED", "LOCAL_CLUSTER", "BAND_BROAD"]:
            for sign, label in [(-1, "DOWN"), (1, "UP")]:
                sub = events[(events["rank_band"] == band) &
                             (events["participation"] == part) &
                             (events["event_sign"] == sign)]
                if len(sub) < 5:
                    continue
                rows.append({
                    "rank_band": band, "participation": part, "sign": label,
                    "n": len(sub), "median_z1": C.safe_median(sub["z1"]),
                    "pct_reversal_7d": C.safe_mean(sub.get("rev7", pd.Series(dtype=float))),
                    "pct_recovery_1s_7d": C.safe_mean(sub.get("recover1s7", pd.Series(dtype=float))),
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 18: HH ANATOMY
# ---------------------------------------------------------------------------

def hh_true_peer_anatomy(events, panels):
    rows = []
    for state in ["SHORT_HOT_MEDIUM_HOT", "SHORT_HOT_MEDIUM_COLD",
                  "SHORT_COLD_MEDIUM_HOT", "SHORT_COLD_MEDIUM_COLD"]:
        sub = events[events["momentum_state"] == state]
        if len(sub) < 5:
            continue
        row = {"momentum_state": state, "n_events": len(sub),
               "pct_isolated": (sub["participation"] == "ISOLATED").mean(),
               "median_z1": C.safe_median(sub["z1"])}
        for fam_name, panel in panels.items():
            merged = sub.merge(
                panel[["event_index", "peer_n", "peer_median_return",
                        "peer_dispersion", "asset_peer_residual"]],
                left_index=True, right_on="event_index", how="left")
            row[f"median_peer_n_{fam_name}"] = C.safe_median(merged["peer_n"])
            row[f"median_residual_{fam_name}"] = C.safe_median(merged["asset_peer_residual"])
        row["pct_reversal_7d"] = C.safe_mean(sub.get("rev7", pd.Series(dtype=float)))
        row["pct_recovery_7d"] = C.safe_mean(sub.get("recover1s7", pd.Series(dtype=float)))
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 19: BASKET DISPERSION
# ---------------------------------------------------------------------------

def basket_dispersion(events, panels):
    groups = {
        "TRUE_LONER": events[events["participation"] == "ISOLATED"],
        "LOCAL_CLUSTER": events[events["participation"] == "LOCAL_CLUSTER"],
        "BAND_BROAD": events[events["participation"] == "BAND_BROAD"],
        "EARLY_1SIGMA": events[events.get("recover1s3", pd.Series(False, index=events.index)) == True],
        "NO_1SIGMA": events[events.get("recover1s7", pd.Series(True, index=events.index)) == False],
        "COORDINATED_UP": events[(events["event_sign"] > 0) &
                                  events["participation"].isin(["BAND_BROAD", "MULTI_BAND"])],
    }
    rows = []
    for name, g in groups.items():
        for band in sorted(g["rank_band"].unique()):
            bg = g[g["rank_band"] == band]
            if len(bg) < 5:
                continue
            row = {"basket": name, "rank_band": band, "n": len(bg),
                   "median_return": C.safe_median(bg["ret_1d"]),
                   "dispersion": C.safe_median(bg["ret_1d"].abs()),
                   "breadth": C.safe_mean(bg["ret_1d"] > 0),
                   "tail_share": C.safe_mean(bg["z1"] >= 3)}
            for fam_name in ["BEHAVIORAL_10", "CORR_60_10"]:
                panel = panels.get(fam_name)
                if panel is not None and "peer_same_sign" in panel.columns:
                    merged = bg.merge(
                        panel[["event_index", "peer_same_sign"]],
                        left_index=True, right_on="event_index", how="left")
                    row[f"peer_norm_rate_{fam_name}"] = C.safe_mean(merged["peer_same_sign"] > 0.5)
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 20: TRIANGLE PILOT
# ---------------------------------------------------------------------------

def triangle_pilot(events, panels):
    by_date = events.groupby("historical_date").agg(
        A_breadth=("top500_breadth_30d", "first"),
        n_isolated=("participation", lambda x: (x == "ISOLATED").sum()),
        n_total=("participation", "count"),
        pct_tail=("z1", lambda x: (x >= 3).mean()),
        btc=("btc_ret_1d", "first"),
    ).reset_index()

    # Add peer dispersion (only first family to avoid suffix conflicts)
    for fam_name, panel in panels.items():
        if "peer_dispersion" not in panel.columns:
            continue
        if "median_peer_disp" in by_date.columns:
            continue
        ev_map = events[["historical_date"]].reset_index().rename(columns={"index": "event_index"})
        pd_sub = panel[["event_index", "peer_dispersion"]].drop_duplicates("event_index")
        pd_sub = pd_sub.merge(ev_map, on="event_index", how="left")
        dd = pd_sub.groupby("historical_date")["peer_dispersion"].median().reset_index()
        dd.columns = ["historical_date", "median_peer_disp"]
        by_date = by_date.merge(dd, on="historical_date", how="left")

    rows = []
    for band in sorted(events["rank_band"].unique()):
        band_dates = events[events["rank_band"] == band]["historical_date"].unique()
        bd = by_date[by_date["historical_date"].isin(band_dates)].copy()
        if len(bd) < 10:
            continue
        for x, y in [("A_breadth", "n_isolated"), ("n_isolated", "pct_tail"),
                      ("A_breadth", "pct_tail")]:
            if x in bd.columns and y in bd.columns:
                rows.append({
                    "rank_band": band, "relation": f"{x}-{y}",
                    "metric": "pearson_correlation",
                    "value": round(float(bd[x].corr(bd[y])), 4),
                    "n_dates": len(bd),
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Section 21: LOCAL SEQUENCES
# ---------------------------------------------------------------------------

def local_sequences(events, panels):
    sequences = []
    for fam_name, panel in panels.items():
        if "asset_peer_residual" not in panel.columns:
            continue
        merged = events.merge(
            panel[["event_index", "asset_peer_residual", "peer_dispersion"]],
            left_index=True, right_on="event_index", how="left")
        diverge = merged[merged["asset_peer_residual"].abs() >
                         merged["peer_dispersion"].replace(0, np.nan)]
        early_1s = diverge[diverge.get("recover1s3", pd.Series(False, index=diverge.index)) == True]
        no_1s = diverge[diverge.get("recover1s7", pd.Series(True, index=diverge.index)) == False]
        sequences.append({
            "sequence": f"PEER_DIVERGENCE -> TRUE_LONER -> EARLY_1SIGMA ({fam_name})",
            "n_total": len(diverge), "n_early_1sigma": len(early_1s),
            "n_no_1sigma": len(no_1s),
            "pct_early_1sigma": round(len(early_1s) / max(len(diverge), 1), 3),
            "status": "COMPUTED" if len(diverge) >= MIN_EVENTS else "LOW_N",
        })

    rank_decay = events[events.get("rank_vel_14d", pd.Series(0, index=events.index)).fillna(0) < -5]
    if len(rank_decay) >= MIN_EVENTS:
        price_rec = rank_decay[rank_decay.get("recover1s7", pd.Series(False, index=rank_decay.index)) == True]
        still_decay = price_rec[price_rec.get("fwd_rank_vel_7d", pd.Series(0, index=price_rec.index)).fillna(0) < 0]
        sequences.append({
            "sequence": "RANK_DECAY -> SHOCK -> PRICE_RECOVERY -> RANK_STILL_DECAYS",
            "n_total": len(rank_decay), "n_price_recovery": len(price_rec),
            "n_still_decays": len(still_decay),
            "pct_still_decays": round(len(still_decay) / max(len(price_rec), 1), 3),
            "status": "COMPUTED",
        })

    hh = events[events["momentum_state"] == "SHORT_HOT_MEDIUM_HOT"]
    hh_loner = hh[hh["participation"] == "ISOLATED"]
    if len(hh_loner) >= 5:
        fast_norm = hh_loner[hh_loner.get("recover1s5", pd.Series(False, index=hh_loner.index)) == True]
        sequences.append({
            "sequence": "HH -> TRUE_LONER -> FAST_NORMALIZATION",
            "n_total": len(hh_loner), "n_fast_norm": len(fast_norm),
            "pct_fast_norm": round(len(fast_norm) / max(len(hh_loner), 1), 3),
            "status": "COMPUTED" if len(hh_loner) >= MIN_EVENTS else "LOW_N",
        })
    return pd.DataFrame(sequences)


# ---------------------------------------------------------------------------
# Meta outputs (31-33)
# ---------------------------------------------------------------------------

def promote_merge_dissolve():
    outputs = [
        ("true_false_loner_taxonomy", "COMPUTED", "tradability_audit"),
        ("pre_event_divergence", "COMPUTED", "conditional_models"),
        ("post_event_peer_paths", "COMPUTED", "classification_validation"),
        ("sigma_recovery_clock", "COMPUTED", "conditioning_analysis"),
        ("price_rank_health_matrix", "COMPUTED", "stability_validation"),
        ("health_stress_response", "COMPUTED", "perturbation_design"),
        ("active_liquidity", "COMPUTED", "joint_model"),
        ("broad_up_down_mirror", "COMPUTED", "peer_controlled_recheck"),
        ("hh_true_peer_anatomy", "COMPUTED", "field_context_integration"),
        ("basket_dispersion", "DESCRIPTIVE", "none"),
        ("triangle_pilot", "COMPUTED", "subperiod_validation"),
        ("local_sequences", "PARTIAL", "purged_fdr_validation"),
    ]
    return pd.DataFrame([{
        "output": o, "status": s,
        "recommendation": "PROMOTE_TO_NEXT_CHECKPOINT" if s == "COMPUTED" else s,
        "requires": r,
    } for o, s, r in outputs])


def null_and_failed(seq_df):
    rows = []
    if seq_df is not None:
        for _, r in seq_df.iterrows():
            if r.get("status") == "LOW_N":
                rows.append({
                    "result": r.get("sequence", ""), "status": "LOW_N",
                    "n": r.get("n_total", 0),
                    "reason": "insufficient effective events",
                })
    if not rows:
        rows.append({"result": "none", "status": "ALL_COMPUTED", "n": 0,
                      "reason": "all preregistered analyses produced results"})
    return pd.DataFrame(rows)


def alpha_role_registry():
    roles = [
        {"role": "TRUE_LONER_TAXONOMY", "description": "Classifies isolated events by true peer isolation",
         "maturity": "COMPUTED", "next_step": "tradability_audit"},
        {"role": "PRE_EVENT_DIVERGENCE", "description": "-30D asset vs peer paths",
         "maturity": "COMPUTED", "next_step": "conditional_models"},
        {"role": "POST_EVENT_PEER_PATHS", "description": "+1 to +30D trajectories",
         "maturity": "COMPUTED", "next_step": "classification_validation"},
        {"role": "SIGMA_RECOVERY_CLOCK", "description": "1σ recovery from shock anchor",
         "maturity": "COMPUTED", "next_step": "conditioning_analysis"},
        {"role": "PRICE_RANK_MATRIX", "description": "Cross-state of price x rank health",
         "maturity": "COMPUTED", "next_step": "stability_validation"},
        {"role": "HEALTH_STRESS", "description": "Response to favorable perturbations",
         "maturity": "COMPUTED", "next_step": "perturbation_design"},
        {"role": "BASKET_GEOMETRY", "description": "Peer basket dispersion",
         "maturity": "DESCRIPTIVE", "next_step": "none"},
        {"role": "TRIANGLE", "description": "Breadth-dispersion-tail relation",
         "maturity": "COMPUTED", "next_step": "subperiod_validation"},
        {"role": "SEQUENCE_ATLAS", "description": "Repeated event sequences",
         "maturity": "PARTIAL", "next_step": "purged_fdr_validation"},
    ]
    return pd.DataFrame(roles)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading data...", flush=True)
    df, ev, rk, beh, corr, st, hy = load_all()

    loner_down = _loner_down(ev, "2s")
    loner_up = _loner_up(ev, "2s")
    loner_all = _loner_all(ev, "2s")
    print(f"Isolated-down (2s): {len(loner_down)}, up: {len(loner_up)}, all: {len(loner_all)}", flush=True)

    print("Building peer panels...", flush=True)
    panels = build_peer_panels(loner_down, rk, beh, corr, st, hy)
    for k, v in panels.items():
        print(f"  {k}: {v['peer_n'].notna().sum()} with peers", flush=True)

    # Section 6+7
    print("\n=== 6+7: True/False Loner Audit ===", flush=True)
    loner_audit = true_false_loner_audit(panels, loner_down)
    loner_audit.to_csv(R / "12_TRUE_FALSE_LONER_AUDIT.csv", index=False)
    print(loner_audit[loner_audit["status"] == "CROSS_BAND_TOTAL"].to_string(index=False))

    # Section 8
    print("\n=== 8: Pre-Event Divergence ===", flush=True)
    _, pre_sum = pre_event_divergence(loner_down, df, panels)
    pre_sum.to_csv(R / "14_PRE_EVENT_PEER_DIVERGENCE.csv", index=False)
    print(f"  {len(pre_sum)} rows")

    # Section 9
    print("\n=== 9: Post-Event Peer Paths ===", flush=True)
    post_path, post_sum = post_event_peer_paths(loner_down, panels)
    post_path.to_csv(R / "15_POST_EVENT_PEER_PATHS.csv", index=False)
    post_sum.to_csv(R / "16_PEER_CONTAGION_NORMALIZATION.csv", index=False)
    print(f"  paths: {len(post_path)}, summary: {len(post_sum)}")

    # Section 10
    print("\n=== 10: Temp Shock vs Contagion ===", flush=True)
    ts = temp_shock_vs_contagion(loner_down, panels)
    ts.to_csv(R / "17_TEMP_SHOCK_VS_CONTAGION.csv", index=False)
    print(f"  {len(ts)} rows")

    # Section 11-12
    print("\n=== 11-12: 1σ Recovery Clock ===", flush=True)
    sigma_clock, rc_sum = sigma_recovery_clock(loner_down)
    rc_sum.to_csv(R / "19_ONE_SIGMA_RECOVERY_CLOCK.csv", index=False)
    print(rc_sum.to_string(index=False))

    # Section 13
    print("\n=== 13: Price vs Rank Health Clocks ===", flush=True)
    price_rows, rank_rows = [], []
    for band in sorted(loner_down["rank_band"].unique()):
        sub = loner_down[loner_down["rank_band"] == band]
        for h in [3, 7, 14, 30]:
            signed = sub.get(f"signed_fwd{h}", pd.Series(dtype=float))
            rec = sub.get(f"recover1s{h}", pd.Series(dtype=float))
            rv = sub.get(f"fwd_rank_vel_{h}d", pd.Series(dtype=float))
            price_rows.append({
                "rank_band": band, "horizon": h, "n": len(sub),
                "pct_1s_recovery": C.safe_mean(rec),
                "median_return": C.safe_median(signed),
            })
            rank_rows.append({
                "rank_band": band, "horizon": h, "n": len(sub),
                "pct_rank_improving": C.safe_mean(rv > 0),
                "median_rank_vel": C.safe_median(rv),
            })
    pd.DataFrame(price_rows).to_csv(R / "20_PRICE_RECOVERY_CLOCK.csv", index=False)
    pd.DataFrame(rank_rows).to_csv(R / "21_RANK_HEALTH_CLOCK.csv", index=False)

    cross = price_rank_clocks(loner_down)
    if isinstance(cross, pd.DataFrame) and len(cross) > 0:
        cross.to_csv(R / "22_PRICE_RANK_HEALTH_MATRIX.csv", index=False)
    else:
        pd.DataFrame([{"status": "COMPUTED", "note": "cross-state matrix in separate file"}]).to_csv(
            R / "22_PRICE_RANK_HEALTH_MATRIX.csv", index=False)
    print("  price/rank clocks computed")

    # Section 14
    print("\n=== 14: Health Stress ===", flush=True)
    hs = health_stress_response(loner_down, df)
    if isinstance(hs, pd.DataFrame) and len(hs) > 0:
        hs.to_csv(R / "23_HEALTH_STRESS_RESPONSE.csv", index=False)
        print(f"  {len(hs)} rows")
    else:
        pd.DataFrame([{"status": "NO_PRE_DECAY_EVENTS"}]).to_csv(
            R / "23_HEALTH_STRESS_RESPONSE.csv", index=False)

    # Section 15
    print("\n=== 15: Reconciliation ===", flush=True)
    recon = rank_reconciliation(loner_down)
    recon.to_csv(R / "24_RANK_DETERIORATION_RECONCILIATION.csv", index=False)

    # Section 16
    print("\n=== 16: Active Liquidity ===", flush=True)
    liq = active_liquidity(loner_down)
    liq.to_csv(R / "25_ACTIVE_LIQUIDITY_SHOCK_ABSORPTION.csv", index=False)
    print(f"  {len(liq)} rows")

    # Section 17
    print("\n=== 17: Broad Up/Down ===", flush=True)
    bu = broad_up_down(ev)
    bu.to_csv(R / "26_BROAD_UP_DOWN_PEER_CONTROLLED.csv", index=False)
    print(f"  {len(bu)} rows")

    # Section 18
    print("\n=== 18: HH Anatomy ===", flush=True)
    hh = hh_true_peer_anatomy(loner_all, panels)
    hh.to_csv(R / "27_HH_TRUE_PEER_ANATOMY.csv", index=False)
    print(f"  {len(hh)} rows")

    # Section 19
    print("\n=== 19: Basket Dispersion ===", flush=True)
    basket = basket_dispersion(loner_all, panels)
    basket.to_csv(R / "28_REPAIRED_LOCAL_BASKET_GEOMETRY.csv", index=False)
    print(f"  {len(basket)} rows")

    # Section 20
    print("\n=== 20: Triangle Pilot ===", flush=True)
    tri = triangle_pilot(loner_all, panels)
    tri.to_csv(R / "29_TRIANGLE_TRUE_PEER_DISPERSION.csv", index=False)
    print(f"  {len(tri)} rows")

    # Section 21
    print("\n=== 21: Sequences ===", flush=True)
    seq = local_sequences(loner_all, panels)
    seq.to_csv(R / "30_LOCAL_SEQUENCE_ATLAS.csv", index=False)
    print(f"  {len(seq)} rows")

    # Meta 31-33
    promote_merge_dissolve().to_csv(R / "31_PROMOTE_MERGE_DISSOLVE.csv", index=False)
    null_and_failed(seq).to_csv(R / "32_NULL_AND_FAILED_RESULTS.csv", index=False)
    alpha_role_registry().to_csv(R / "33_ALPHA_ROLE_REGISTRY.csv", index=False)

    print("\n=== ALL ANALYSES COMPLETE ===", flush=True)
    return loner_audit, rc_sum, cross, seq


if __name__ == "__main__":
    main()
