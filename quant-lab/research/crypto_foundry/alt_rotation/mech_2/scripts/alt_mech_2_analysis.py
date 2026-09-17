#!/usr/bin/env python
"""ALT_MECH_2 - Conditional Propagation, Causal Hierarchy & Field-Geometry Mapping.

Terrain research ONLY. No PnL, no strategy, no optimization, no ML, no sizing,
no deployment. All rules were fixed in 01_PREREGISTRATION.md BEFORE this script ran.

Reuses DATA-1.1 inputs and MECH-1 helpers (truth lock, block bootstrap, FDR,
sector episodes, routing states) from alt_mech_1_analysis.
"""
import json, pickle, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

SEED = 20260826
BOOT_N = 500
BLOCK_DAYS = 20
PERM_N = 200

ROOT = Path(__file__).resolve().parents[1]           # mech_2/
sys.path.insert(0, str(ROOT.parent / "mech_1" / "scripts"))
import alt_mech_1_analysis as M1                      # reuse helpers

OUT = ROOT
DATA = M1.DATA

BANDS = M1.BANDS
SUBPERIODS = M1.SUBPERIODS
FORBIDDEN = M1.FORBIDDEN_PREFIXES


# ----------------------------------------------------------------------------
# cache helpers (resume-safe; caches are transient and never committed)
# ----------------------------------------------------------------------------

def _cache_step(name, fn):
    p = OUT / f"_cache_{name}.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            obj = pickle.load(fh)
        print(f"[cache] {name} loaded")
        return obj
    print(f"[run] {name} ...")
    obj = fn()
    with open(p, "wb") as fh:
        pickle.dump(obj, fh)
    return obj


# ----------------------------------------------------------------------------
# load + truth lock
# ----------------------------------------------------------------------------

def load():
    inp = M1.load_inputs()
    tl = M1.verify_truth_lock(inp)
    return inp, tl


# ----------------------------------------------------------------------------
# Workstream A/B common factors + daily frame
# ----------------------------------------------------------------------------

def build_factors(feat, terrain, glob, rb):
    """Daily common-factor frame (all point-in-time)."""
    f = feat.copy()
    # cap-weighted market 1D return
    mkt = f.groupby("historical_date").apply(
        lambda g: float(np.nansum(g.market_cap_share * g.return_1d) /
                        max(np.nansum(g.market_cap_share), 1e-12)), include_groups=False
    ).rename("mkt_ret_1d").reset_index()
    vol = f.groupby("historical_date").realized_volatility_30d.median() \
        .rename("vol_med").reset_index()
    top3 = f.sort_values(["historical_date", "market_cap_usd"], ascending=[True, False]) \
        .groupby("historical_date").head(3).groupby("historical_date") \
        .market_cap_share.sum().rename("top3_share").reset_index()
    d = terrain[["historical_date", "btc_return_1d", "btc_return_30d", "eth_return_1d",
                 "top500_breadth_30d"]].merge(mkt, on="historical_date", how="left") \
        .merge(vol, on="historical_date", how="left") \
        .merge(top3, on="historical_date", how="left")
    sc = M1.available_next_day(glob[["historical_date", "stablecoin_change_30d"]],
                               ["stablecoin_change_30d"])
    d = d.merge(sc, on="historical_date", how="left")
    d["top3_share_chg7"] = d.top3_share.diff(7)
    d["vol_p70"] = d.vol_med.rolling(252, min_periods=60).quantile(0.70)
    d["vol_p30"] = d.vol_med.rolling(252, min_periods=60).quantile(0.30)
    # band-level series (V2 columns only)
    bm = rb[["historical_date", "rank_band", "median_return_1d",
             "median_rank_velocity_7d", "breadth_7d", "market_cap_share"]]
    return d, bm


def assign_states(d):
    d = d.copy()
    st = {}
    st["BTC_UP"] = d.btc_return_30d > 0
    st["BTC_DOWN"] = d.btc_return_30d < 0
    st["VOL_HIGH"] = d.vol_med >= d.vol_p70
    st["VOL_LOW"] = d.vol_med <= d.vol_p30
    st["BREADTH_EXPANDING"] = d.top500_breadth_30d >= 0.50
    st["BREADTH_CONTRACTING"] = d.top500_breadth_30d < 0.50
    st["SC_INFLOW"] = d.stablecoin_change_30d > 0
    st["SC_OUTFLOW"] = d.stablecoin_change_30d < 0
    st["CONC_RISING"] = d.top3_share_chg7 > 0
    st["CONC_FALLING"] = d.top3_share_chg7 < 0
    for k, v in st.items():
        d[k] = v.fillna(False)
    return d


def _resid_series(y, X, min_win=60, win=252):
    """Trailing-window OLS residual of y on X (with intercept). Causal."""
    y = np.asarray(y, float)
    n = len(y)
    out = np.full(n, np.nan)
    Xc = np.column_stack([np.ones(n), np.asarray(X, float)])
    for t in range(n):
        lo = max(0, t - win)
        sl = slice(lo, t)
        if t - lo < min_win:
            continue
        Xw, yw = Xc[sl], y[sl]
        ok = ~(np.isnan(yw) | np.isnan(Xw).any(axis=1))
        if ok.sum() < min_win:
            continue
        beta, *_ = np.linalg.lstsq(Xw[ok], yw[ok], rcond=None)
        xr = Xc[t]
        if np.isnan(xr).any():
            continue
        out[t] = y[t] - float(xr @ beta)
    return out


# ----------------------------------------------------------------------------
# Workstream A - common-factor removal (raw vs residual band lead-lag)
# ----------------------------------------------------------------------------

def ws_a(d, bm):
    metrics = {"ew_return_1d": "median_return_1d",
               "rank_velocity_7d": "median_rank_velocity_7d",
               "breadth_7d": "breadth_7d"}
    Xcols = ["mkt_ret_1d", "btc_return_1d", "eth_return_1d", "vol_med",
             "top500_breadth_30d", "stablecoin_change_30d"]
    X = d[Xcols].astype(float).values
    dates = d.historical_date.values
    rng = np.random.default_rng(SEED + 1)
    rows, test_count = [], 0
    pairs = [(i, j) for i in range(len(BANDS)) for j in range(i + 1, len(BANDS))]
    for mname, col in metrics.items():
        W = bm.pivot(index="historical_date", columns="rank_band",
                     values=col).reindex(index=dates, columns=BANDS)
        resid = {b: _resid_series(W[b].values, X) for b in BANDS}
        for (i, j) in pairs:
            a, b = BANDS[i], BANDS[j]
            for variant, wA, wB in [("RAW", W[a], W[b]),
                                    ("RESID", resid[a], resid[b])]:
                xc = M1.xcorr_with_boot(np.asarray(wA, dtype=float),
                                        np.asarray(wB, dtype=float), 14, rng)
                if xc.empty:
                    continue
                best = xc.loc[xc["corr"].abs().idxmax()]
                test_count += 1
                rows.append({"metric": mname, "band_a": a, "band_b": b,
                             "variant": variant,
                             "best_lag_days_a_leads_b": int(best["lag"]),
                             "best_corr": best["corr"],
                             "boot_ci_low": best["boot_ci_low"],
                             "boot_ci_high": best["boot_ci_high"],
                             "raw_p": best["raw_p"], "n_days": best["n"]})
    df = pd.DataFrame(rows)
    if len(df):
        # classify per (metric, band_a, band_b)
        cls = []
        for (mname, a, b), g in df.groupby(["metric", "band_a", "band_b"]):
            raw = g[g.variant == "RAW"]
            rs = g[g.variant == "RESID"]
            if raw.empty or rs.empty:
                cls.append({"metric": mname, "band_a": a, "band_b": b,
                            "classification": "WEAK"})
                continue
            r_raw = raw.iloc[0]
            r_rs = rs.iloc[0]
            if r_raw.raw_p < 0.05 and r_rs.raw_p < 0.05:
                if np.sign(r_raw.best_corr) == np.sign(r_rs.best_corr):
                    cls.append({"metric": mname, "band_a": a, "band_b": b,
                                "classification": "STRUCTURAL_LEAD_LAG",
                                "raw_lag": int(r_raw.best_lag_days_a_leads_b),
                                "resid_lag": int(r_rs.best_lag_days_a_leads_b),
                                "resid_corr": r_rs.best_corr,
                                "raw_corr": r_raw.best_corr})
                else:
                    cls.append({"metric": mname, "band_a": a, "band_b": b,
                                "classification": "AMBIGUOUS",
                                "raw_lag": int(r_raw.best_lag_days_a_leads_b),
                                "resid_lag": int(r_rs.best_lag_days_a_leads_b)})
            elif r_raw.raw_p < 0.05:
                cls.append({"metric": mname, "band_a": a, "band_b": b,
                            "classification": "COMMON_FIELD_EFFECT",
                            "raw_lag": int(r_raw.best_lag_days_a_leads_b),
                            "resid_lag": int(r_rs.best_lag_days_a_leads_b)})
            elif r_rs.raw_p < 0.05:
                cls.append({"metric": mname, "band_a": a, "band_b": b,
                            "classification": "STRUCTURAL_LEAD_LAG",
                            "raw_lag": int(r_raw.best_lag_days_a_leads_b),
                            "resid_lag": int(r_rs.best_lag_days_a_leads_b),
                            "resid_corr": r_rs.best_corr,
                            "raw_corr": r_raw.best_corr})
            else:
                cls.append({"metric": mname, "band_a": a, "band_b": b,
                            "classification": "WEAK"})
        df = df.merge(pd.DataFrame(cls), on=["metric", "band_a", "band_b"], how="left")
        df.to_csv(OUT / "05_CONDITIONAL_LEAD_LAG.csv", index=False)
        # FDR over all tested cells (raw_p per variant)
        pv = df.raw_p.values.astype(float)
        df["fdr_q"] = np.round(M1.bh_fdr(pv), 4)
        df.to_csv(OUT / "05_CONDITIONAL_LEAD_LAG.csv", index=False)
    # common-factor model summary (R2 of factors per band metric)
    rows2 = []
    for mname, col in metrics.items():
        W = bm.pivot(index="historical_date", columns="rank_band",
                     values=col).reindex(index=d.historical_date.values, columns=BANDS)
        for b in BANDS:
            y = W[b].values.astype(float)
            ok = ~np.isnan(y) & ~np.isnan(X).any(axis=1)
            if ok.sum() < 120:
                continue
            Xc = np.column_stack([np.ones(ok.sum()), X[ok]])
            yv = y[ok]
            ybar = yv.mean()
            sst = float(((yv - ybar) ** 2).sum())
            beta, *_ = np.linalg.lstsq(Xc, yv, rcond=None)
            sse = float(((yv - Xc @ beta) ** 2).sum())
            rows2.append({"metric": mname, "band": b,
                          "common_factor_r2": round(1 - sse / max(sst, 1e-12), 4),
                          "n_days": int(ok.sum())})
    cf = pd.DataFrame(rows2)
    cf.to_csv(OUT / "04_COMMON_FACTOR_MODEL.csv", index=False)
    return {"a": df, "cf": cf, "test_count": test_count}


# ----------------------------------------------------------------------------
# Workstream B - conditional lead/lag under states
# ----------------------------------------------------------------------------

def _cond_xcorr(x, y, h, rng, perms=PERM_N):
    """Corr(x[t], y[t+h]) restricted to valid pairs; permutation p (block shift)."""
    n = len(x)
    if h >= 0:
        a, b = x[: n - h], y[h:]
    else:
        a, b = x[-h:], y[: n + h]
    ok = ~(np.isnan(a) | np.isnan(b))
    a, b = a[ok], b[ok]
    if len(a) < 60 or np.std(a) == 0 or np.std(b) == 0:
        return np.nan, np.nan, len(a)
    r = float(np.corrcoef(a, b)[0, 1])
    ge = 0
    for _ in range(perms):
        off = BLOCK_DAYS + int(rng.integers(1, max(2, len(a) - BLOCK_DAYS)))
        xs = np.roll(a, off % len(a))
        rs = np.corrcoef(xs, b)[0, 1]
        if abs(rs) >= abs(r):
            ge += 1
    return r, (ge + 1) / (perms + 1), len(a)


def ws_b(d, bm):
    metrics = {"ew_return_1d": "median_return_1d",
               "rank_velocity_7d": "median_rank_velocity_7d"}
    pairs = [(i, i + 1) for i in range(len(BANDS) - 1)]
    states = ["BTC_UP", "BTC_DOWN", "VOL_HIGH", "VOL_LOW",
              "BREADTH_EXPANDING", "BREADTH_CONTRACTING",
              "SC_INFLOW", "SC_OUTFLOW", "CONC_RISING", "CONC_FALLING"]
    lags = [-7, -3, -1, 1, 3, 7]
    dates = d.historical_date.values
    rng = np.random.default_rng(SEED + 2)
    rows, test_count = [], 0
    state_days = {s: int(d[s].sum()) for s in states}
    for mname, col in metrics.items():
        W = bm.pivot(index="historical_date", columns="rank_band",
                     values=col).reindex(index=dates, columns=BANDS)
        for (i, j) in pairs:
            a, b = BANDS[i], BANDS[j]
            xa, xb = W[a].values.astype(float), W[b].values.astype(float)
            # unconditional reference
            rng2 = np.random.default_rng(SEED + 3)
            unr = {}
            for h in lags:
                r, p, nn = _cond_xcorr(xa, xb, h, rng2)
                unr[h] = (r, p)
            for s in states:
                mask = d[s].values
                if state_days[s] < 120:
                    rows.append({"metric": mname, "band_a": a, "band_b": b,
                                 "state": s, "state_days": state_days[s],
                                 "note": "INSUFFICIENT_SAMPLE",
                                 "workstream": "B"})
                    continue
                for h in lags:
                    r, p, nn = _cond_xcorr(xa[mask], xb[mask], h, rng)
                    if np.isnan(r):
                        continue
                    test_count += 1
                    best_uncond = max(unr, key=lambda k: abs(unr[k][0]))
                    shifted = (np.sign(r) != np.sign(unr[best_uncond][0])) or \
                              (abs(h - best_uncond) >= 3)
                    rows.append({"metric": mname, "band_a": a, "band_b": b,
                                 "state": s, "state_days": state_days[s],
                                 "lag_days": h, "corr": round(r, 4),
                                 "perm_p": round(p, 4), "n": nn,
                                 "uncond_best_lag": best_uncond,
                                 "uncond_best_corr": round(unr[best_uncond][0], 4),
                                 "state_conditioned": bool(shifted and p < 0.05),
                                 "workstream": "B"})
    df = pd.DataFrame(rows)
    if len(df) and "perm_p" in df.columns:
        m = df.perm_p.notna()
        if m.any():
            df.loc[m, "fdr_q"] = np.round(
                M1.bh_fdr(df.loc[m, "perm_p"].values.astype(float)), 4)
        df.to_csv(OUT / "05b_CONDITIONAL_LEAD_LAG_STATES.csv", index=False)
    state_sum = pd.DataFrame([{"state": s, "days": state_days[s]} for s in states])
    state_sum.to_csv(OUT / "03_STATE_DEFINITIONS_support.csv", index=False)
    return {"b": df, "test_count": test_count, "state_days": state_days}


# ----------------------------------------------------------------------------
# Workstream C - rank migration precursors
# ----------------------------------------------------------------------------

def ws_c(feat, inp, sd=None):
    f = feat.copy()
    f = f.sort_values(["internal_asset_id", "historical_date"])
    f["band"] = f.global_rank.map(M1.band_code)
    f["prev_band"] = f.groupby("internal_asset_id").band.shift(1)
    f["band_next14"] = f.groupby("internal_asset_id").band.shift(-14)
    f["rel_ret_1d"] = f.return_1d - f.return_1d.groupby(f.historical_date).transform("mean")
    # sector strength + chain strength (PIT)
    if sd is None:
        sd, _ = M1.sector_daily(inp)
    sec_strength = sd[["historical_date", "sector", "median_member_vel7"]]
    sm = inp["smem"][["historical_date", "internal_asset_id", "sector"]] \
        .drop_duplicates(["historical_date", "internal_asset_id"])
    f = f.merge(sm, on=["historical_date", "internal_asset_id"], how="left")
    f = f.merge(sec_strength, on=["historical_date", "sector"], how="left")
    chain_agg, _ = M1.chain_native_aggregates(feat, inp["chainmap"])
    ch_str = chain_agg[["historical_date", "chain",
                        "n_improving", "n_top500"]].copy()
    ch_str["improving_share"] = ch_str.n_improving / ch_str.n_top500.clip(lower=1)
    cm = inp["chainmap"][["historical_date", "internal_asset_id", "chain"]] \
        .drop_duplicates(["historical_date", "internal_asset_id"])
    f = f.merge(cm, on=["historical_date", "internal_asset_id"], how="left")
    f = f.merge(ch_str[["historical_date", "chain", "improving_share"]],
                on=["historical_date", "chain"], how="left")
    rng = np.random.default_rng(SEED + 4)
    windows = {1: 1, 3: 3, 7: 7, 14: 14, 30: 30}
    pre_cols = ["rel_ret_1d", "rank_velocity_7d", "rank_acceleration_short",
                "mcap_share_change_7d", "realized_volatility_30d",
                "median_member_vel7", "improving_share"]
    f = f.sort_values(["internal_asset_id", "historical_date"])
    # rolling window means (trailing, shifted so info is strictly before t)
    for w, wl in windows.items():
        agg = f.groupby("internal_asset_id")[pre_cols].transform(
            lambda s: s.rolling(wl, min_periods=max(1, wl // 2)).mean().shift(1))
        for pre in pre_cols:
            f[f"{pre}_win{w}"] = agg[pre]
    # events: upward migration (band improved vs prev day)
    ev = f[(f.band.notna()) & (f.prev_band.notna()) & (f.band < f.prev_band)].copy()
    ev = ev[ev.prev_band != M1.EX_CODE].copy()
    ctrl_pool = f[(f.band.notna()) & (f.prev_band.notna()) &
                  (f.band == f.prev_band)].copy()
    rows = []
    for w in windows:
        wcols = [f"{p}_win{w}" for p in pre_cols]
        for (d0, pb), g in ev.groupby(["historical_date", "prev_band"]):
            pool = ctrl_pool[(ctrl_pool.historical_date == d0) &
                             (ctrl_pool.band == pb)]
            if len(pool) == 0 or len(g) == 0:
                continue
            n_ctrl = min(5 * len(g), len(pool))
            ctrl = pool.sample(n_ctrl, random_state=int(rng.integers(0, 2**31)))
            ev_med = g[wcols].median()
            ctrl_med = ctrl[wcols].median()
            succ = float((g.band_next14 < pb).mean()) \
                if g.band_next14.notna().any() else np.nan
            rows.append({"date": d0, "from_band": M1.CODE_TO_BAND[int(pb)],
                         "window_d": w, "n_events": int(len(g)),
                         "n_controls": n_ctrl,
                         "success_rate_14d": round(succ, 4) if succ == succ else np.nan,
                         **{f"ev_{p}_win{w}": round(float(ev_med[f"{p}_win{w}"]), 5)
                            for p in pre_cols},
                         **{f"ctrl_{p}_win{w}": round(float(ctrl_med[f"{p}_win{w}"]), 5)
                            for p in pre_cols}})
    df = pd.DataFrame(rows)
    if len(df):
        df.to_csv(OUT / "06_RANK_MIGRATION_PRECURSORS.csv", index=False)
        # summary by transition
        summ = []
        for (pb, nb), g in ev.groupby(["prev_band", "band"]):
            s14 = g.band_next14
            succ = float((s14 < pb).mean()) if s14.notna().any() else np.nan
            summ.append({"from_band": M1.CODE_TO_BAND[int(pb)],
                         "to_band": M1.CODE_TO_BAND[int(nb)],
                         "n_events": int(len(g)),
                         "success_rate_14d": round(succ, 4) if succ == succ else np.nan})
        pd.DataFrame(summ).to_csv(OUT / "06_RANK_MIGRATION_PRECURSORS_transitions.csv",
                                  index=False)
    return {"c": df}


# ----------------------------------------------------------------------------
# Workstream D - leader-first sector propagation
# ----------------------------------------------------------------------------

def ws_d(sd, mem, feat=None):
    eps = M1.detect_sector_episodes(sd)
    if len(eps) == 0:
        return {"d": pd.DataFrame()}
    mem = mem.copy()
    mem["historical_date"] = pd.to_datetime(mem["historical_date"])
    if feat is None:
        raise ValueError("ws_d requires feat for market return")
    mkt_ret = feat.groupby("historical_date").apply(
        lambda g: float(np.nansum(g.market_cap_share * g.return_1d) /
                        max(np.nansum(g.market_cap_share), 1e-12)), include_groups=False
    ).rename("mkt_ret_1d").reset_index()
    mem = mem.merge(mkt_ret, on="historical_date", how="left")
    mem["rel_ret_1d"] = mem.return_1d - mem.mkt_ret_1d
    rng = np.random.default_rng(SEED + 5)
    rows, test_count = [], 0
    lags = [0, 1, 3, 7, 14]
    # per-sector pre-grouped date-indexed frames
    by_sec = {sec: g.sort_values("historical_date") for sec, g in mem.groupby("sector")}
    for _, ep in eps.iterrows():
        sec, s0, s1 = ep.source, pd.Timestamp(ep.start_date), pd.Timestamp(ep.end_date)
        g = by_sec.get(sec)
        if g is None:
            continue
        eg = g[(g.historical_date >= s0) & (g.historical_date <= s1)]
        if len(eg) < 5:
            continue
        start_day = eg[eg.historical_date == s0]
        if start_day.empty:
            continue
        leader = start_day.loc[start_day.market_cap_usd.idxmax()]
        peers = eg[eg.internal_asset_id != leader.internal_asset_id]
        if len(peers) == 0:
            continue
        lead_ser = eg[eg.internal_asset_id == leader.internal_asset_id] \
            .set_index("historical_date")
        peer_med = peers.groupby("historical_date")["rel_ret_1d"].median()
        dts = sorted(set(lead_ser.index) & set(peer_med.index))
        if len(dts) < 5:
            continue
        x = lead_ser["rel_ret_1d"].reindex(dts).values.astype(float)
        y = peer_med.reindex(dts).values.astype(float)
        lagrow = {"sector": sec, "episode_start": ep.start_date, "episode_end": ep.end_date,
                  "leader_symbol": leader.symbol, "leader_rank": int(leader.global_rank),
                  "n_peers": int(len(peers)), "n_days": len(dts)}
        for k in lags:
            if k == 0:
                ok = ~(np.isnan(x) | np.isnan(y))
                if ok.sum() >= 5 and np.std(x[ok]) > 0 and np.std(y[ok]) > 0:
                    lagrow["same_day_corr"] = round(float(np.corrcoef(x[ok], y[ok])[0, 1]), 4)
            elif k < len(dts):
                a, b = x[: len(x) - k], y[k:]
                ok = ~(np.isnan(a) | np.isnan(b))
                if ok.sum() >= 5 and np.std(a[ok]) > 0 and np.std(b[ok]) > 0:
                    lagrow[f"delay{k}_corr"] = round(float(np.corrcoef(a[ok], b[ok])[0, 1]), 4)
                else:
                    lagrow[f"delay{k}_corr"] = np.nan
            else:
                lagrow[f"delay{k}_corr"] = np.nan
            test_count += 1
        rows.append(lagrow)
    df = pd.DataFrame(rows)
    if len(df):
        df.to_csv(OUT / "07_SECTOR_PROPAGATION.csv", index=False)
        # leader persistence across consecutive episodes per sector
        pers = []
        for sec, g in eps.groupby("source"):
            g = g.sort_values("start_date")
            if len(g) < 2:
                continue
            for k in range(1, len(g)):
                pers.append({"sector": sec,
                             "prev_episode": g.iloc[k - 1].start_date,
                             "episode": g.iloc[k].start_date})
        pers_df = pd.DataFrame(pers)
        pers_df.to_csv(OUT / "07_SECTOR_PROPAGATION_episodes.csv", index=False)
    return {"d": df}


# ----------------------------------------------------------------------------
# Workstream E - chain / liquidity hierarchy
# ----------------------------------------------------------------------------

def _chain_flow_ready(chainflow):
    """Per-chain TVL change + AVAILABLE_NEXT_DAY (shift within chain, not globally)."""
    cf = chainflow.copy().sort_values(["chain", "historical_date"])
    cf["tvl_chg7"] = cf.groupby("chain").chain_tvl.pct_change(7)
    for c in ["chain_tvl_change_7d", "chain_tvl_change_30d", "tvl_chg7"]:
        if c in cf.columns:
            cf[c] = cf.groupby("chain")[c].shift(1)
    return cf


def _glob_ready(glob):
    g = glob.copy().sort_values("historical_date")
    for c in ["stablecoin_change_7d", "stablecoin_change_30d",
              "dex_volume_change_7d", "dex_volume_change_30d"]:
        if c in g.columns:
            g[c] = g[c].shift(1)
    return g


def ws_e(feat, inp):
    chain_agg, _ = M1.chain_native_aggregates(feat, inp["chainmap"])
    ca = chain_agg.copy()
    ca["improving_share"] = ca.n_improving / ca.n_top500.clip(lower=1)
    cf = _chain_flow_ready(inp["chainflow"])
    g = _glob_ready(inp["glob"])
    merged = ca.merge(cf[["historical_date", "chain", "chain_tvl_change_7d",
                          "chain_tvl_change_30d", "tvl_chg7"]],
                      on=["historical_date", "chain"], how="inner") \
        .merge(g[["historical_date", "stablecoin_change_7d", "stablecoin_change_30d",
                  "dex_volume_change_7d", "dex_volume_change_30d"]],
               on="historical_date", how="left")
    chains = merged.groupby("chain").historical_date.nunique().sort_values(
        ascending=False).head(12).index.tolist()
    links = [("stablecoin_change_30d", "tvl_chg7", "STABLECOIN_LEADS_TVL"),
             ("tvl_chg7", "improving_share", "TVL_LEADS_NATIVE"),
             ("tvl_chg7", "dex_volume_change_7d", "TVL_LEADS_DEX"),
             ("improving_share", "median_vel7", "NATIVE_LEADS_VELOCITY"),
             ("tvl_chg7", "stablecoin_change_30d", "TVL_LEADS_STABLECOIN"),
             ("median_vel7", "improving_share", "VELOCITY_LEADS_NATIVE")]
    rng = np.random.default_rng(SEED + 6)
    lags = [1, 3, 7, 14]
    rows, test_count = [], 0
    for ch in chains:
        g = merged[merged.chain == ch].sort_values("historical_date")
        if len(g) < 120:
            continue
        for xcol, ycol, link in links:
            x = g[xcol].values.astype(float)
            y = g[ycol].values.astype(float)
            for h in lags:
                r, p, nn = _cond_xcorr(x, y, h, rng)
                if np.isnan(r):
                    continue
                test_count += 1
                rows.append({"chain": ch, "link": link, "driver": xcol,
                             "outcome": ycol, "lead_days": h, "corr": round(r, 4),
                             "perm_p": round(p, 4), "n": nn})
    df = pd.DataFrame(rows)
    if len(df):
        df["fdr_q"] = np.round(M1.bh_fdr(df.perm_p.values.astype(float)), 4)
        df.to_csv(OUT / "08_CHAIN_FLOW_PROPAGATION.csv", index=False)
    return {"e": df, "test_count": test_count}


# ----------------------------------------------------------------------------
# Workstream F - propagation failures / exhaustion signatures
# ----------------------------------------------------------------------------

def ws_f(d, bm, feat, inp):
    f = feat.copy()
    # pattern 2: asset-level velocity without share
    f["vel_pos"] = f.rank_velocity_7d > 0
    f["share_neg"] = f.mcap_share_change_7d < 0
    vws_days = f[f.vel_pos & f.share_neg].groupby("historical_date").size() \
        .rename("n_vel_no_share").reset_index()
    vws_share = f.groupby("historical_date").apply(
        lambda g: float(((g.rank_velocity_7d > 0) & (g.mcap_share_change_7d < 0)).mean()),
        include_groups=False).rename("vel_no_share_share").reset_index()
    # pattern 4: breadth AND concentration rising
    d = d.copy()
    d["brd_rising"] = d.top500_breadth_30d.diff(7) > 0
    d["conc_rising"] = d.top3_share_chg7 > 0
    # pattern 5: lower-rank acceleration while leaders stall
    Wv = bm.pivot(index="historical_date", columns="rank_band",
                  values="median_rank_velocity_7d").reindex(
        index=d.historical_date.values, columns=BANDS)
    d["low_rising"] = Wv["301-500"].diff(7) > 0
    d["top_falling"] = Wv["1-10"].diff(7) < 0
    patterns = {
        "BREADTH_AND_CONCENTRATION": d.brd_rising & d.conc_rising,
        "LOWER_RANK_ACCELERATION": d.low_rising & d.top_falling,
    }
    rows = []
    for pname, mask in patterns.items():
        idx = d.index[mask.fillna(False)]
        comp = d.index[~mask.fillna(False)]
        for h in (7, 14, 30):
            fwd = d.btc_return_30d.shift(-h)
            rel = (Wv["11-25"] - Wv["301-500"]).shift(-h)
            rows.append({
                "pattern": pname, "forward_window_d": h,
                "n_pattern_days": int(len(idx)), "n_complement_days": int(len(comp)),
                "mean_fwd_btc_ret30_pattern": round(float(fwd[idx].mean()), 5)
                if len(idx) else np.nan,
                "mean_fwd_btc_ret30_complement": round(float(fwd[comp].mean()), 5)
                if len(comp) else np.nan,
                "mean_fwd_band_11_25_minus_301_500_pattern":
                    round(float(rel[idx].mean()), 5) if len(idx) else np.nan,
                "mean_fwd_band_11_25_minus_301_500_complement":
                    round(float(rel[comp].mean()), 5) if len(comp) else np.nan,
            })
    df = pd.DataFrame(rows)
    # asset-level VWS pattern forward outcomes
    f["fwd_ret14"] = f.groupby("internal_asset_id").return_14d.shift(-14)
    f["fwd_ret30"] = f.groupby("internal_asset_id").return_30d.shift(-30)
    vws = f[f.vel_pos & f.share_neg].copy()
    no = f[~(f.vel_pos & f.share_neg)].copy()
    for lbl, sub in [("PATTERN", vws), ("COMPLEMENT", no)]:
        df = pd.concat([df, pd.DataFrame([{
            "pattern": "VELOCITY_WITHOUT_SHARE", "forward_window_d": 14,
            "n_pattern_days": int(len(sub)) if lbl == "PATTERN" else np.nan,
            "n_complement_days": int(len(sub)) if lbl == "COMPLEMENT" else np.nan,
            "mean_asset_fwd_ret14": round(float(sub.fwd_ret14.mean()), 5)
            if sub.fwd_ret14.notna().any() else np.nan,
            "mean_asset_fwd_ret30": round(float(sub.fwd_ret30.mean()), 5)
            if sub.fwd_ret30.notna().any() else np.nan,
        }])], ignore_index=True)
    df.to_csv(OUT / "09_PROPAGATION_FAILURES.csv", index=False)
    return {"f": df}


# ----------------------------------------------------------------------------
# Workstream G - morphisms (routing-state n-grams across subperiods)
# ----------------------------------------------------------------------------

def ws_g(daily):
    daily = daily.copy()
    daily["subperiod"] = daily.historical_date.map(M1.subperiod_of)
    seq = daily.state.values
    grams = {}
    for t in range(len(seq) - 2):
        key = (seq[t], seq[t + 1], seq[t + 2])
        grams.setdefault(key, []).append(daily.historical_date.iloc[t + 2])
    rows = []
    for key, dts in grams.items():
        sub_counts = daily[daily.historical_date.isin(dts)].subperiod.value_counts()
        n_sub = int((sub_counts >= 3).sum())
        total = len(dts)
        cls = ("RECURRING" if n_sub >= 2 else
               "PARTIALLY_RECURRING" if n_sub == 1 else "CYCLE_SPECIFIC")
        rows.append({"state_1": key[0], "state_2": key[1], "state_3": key[2],
                     "occurrences": total, "subperiods_with_ge3": n_sub,
                     "classification": cls,
                     "subperiod_counts": json.dumps(sub_counts.to_dict())})
    df = pd.DataFrame(rows).sort_values("occurrences", ascending=False)
    df.to_csv(OUT / "12_MORPHISM_CATALOG.csv", index=False)
    catalog = df.head(40).to_dict(orient="records")
    with open(OUT / "12_MORPHISM_CATALOG.json", "w") as fh:
        json.dump({"motif_total": int(len(df)),
                   "recurring": int((df.classification == "RECURRING").sum()),
                   "partially_recurring": int(
                       (df.classification == "PARTIALLY_RECURRING").sum()),
                   "cycle_specific": int((df.classification == "CYCLE_SPECIFIC").sum()),
                   "top_motifs": catalog}, fh, indent=2, default=str)
    return {"g": df}


# ----------------------------------------------------------------------------
# Workstream H - hierarchy discovery (variance decomposition per sector/chain)
# ----------------------------------------------------------------------------

def ws_h(feat, inp, sd=None):
    if sd is None:
        sd, _ = M1.sector_daily(inp)
    f = feat[["historical_date", "internal_asset_id", "return_7d",
              "market_cap_share"]].copy()
    sm = inp["smem"][["historical_date", "internal_asset_id", "sector"]] \
        .drop_duplicates(["historical_date", "internal_asset_id"])
    m = f.merge(sm, on=["historical_date", "internal_asset_id"], how="inner")
    chain_agg, _ = M1.chain_native_aggregates(feat, inp["chainmap"])
    cm = inp["chainmap"][["historical_date", "internal_asset_id", "chain"]] \
        .drop_duplicates(["historical_date", "internal_asset_id"])
    m = m.merge(cm, on=["historical_date", "internal_asset_id"], how="left")
    # global factor
    mkt = f.groupby("historical_date").apply(
        lambda g: float(np.nansum(g.market_cap_share * g.return_7d) /
                        max(np.nansum(g.market_cap_share), 1e-12)), include_groups=False
    ).rename("mkt_ret_7d").reset_index()
    m = m.merge(mkt, on="historical_date", how="left")
    # chain factor: chain median member return 7d per day
    chf = m.groupby(["historical_date", "chain"]).return_7d.median() \
        .rename("chain_ret_7d").reset_index()
    m = m.merge(chf, on=["historical_date", "chain"], how="left")
    # sector factor: sector median member return 7d per day
    sef = m.groupby(["historical_date", "sector"]).return_7d.median() \
        .rename("sector_ret_7d").reset_index()
    m = m.merge(sef, on=["historical_date", "sector"], how="left")
    sectors = m.groupby("sector").historical_date.nunique()
    sectors = sectors[sectors >= 120].index.tolist()
    rows = []
    for sec in sectors:
        g = m[m.sector == sec].dropna(subset=["return_7d", "mkt_ret_7d"])
        if len(g) < 500:
            continue
        y = g.return_7d.values.astype(float)
        X1 = g.mkt_ret_7d.values.astype(float)
        ybar = y.mean()
        sst = float(((y - ybar) ** 2).sum())
        b1, *_ = np.linalg.lstsq(np.column_stack([np.ones_like(X1), X1]), y, rcond=None)
        r1 = y - np.column_stack([np.ones_like(X1), X1]) @ b1
        r2g = 1 - float((r1 ** 2).sum()) / max(sst, 1e-12)
        # chain layer on residual
        okc = g.chain_ret_7d.notna()
        if okc.sum() >= 200:
            X2 = np.column_stack([np.ones(okc.sum()),
                                  g.loc[okc, "chain_ret_7d"].values.astype(float)])
            b2, *_ = np.linalg.lstsq(X2, r1[okc], rcond=None)
            r2 = r1.copy()
            r2[okc] = r1[okc] - X2 @ b2
            r2c = 1 - float((r2 ** 2).sum()) / max(sst, 1e-12)
        else:
            r2c, r2 = r2g, r1.copy()
        # sector layer on residual
        oks = g.sector_ret_7d.notna()
        if oks.sum() >= 200:
            X3 = np.column_stack([np.ones(oks.sum()),
                                  g.loc[oks, "sector_ret_7d"].values.astype(float)])
            b3, *_ = np.linalg.lstsq(X3, r2[oks], rcond=None)
            r3 = r2.copy()
            r3[oks] = r2[oks] - X3 @ b3
            r2s = 1 - float((r3 ** 2).sum()) / max(sst, 1e-12)
        else:
            r2s = r2c
        rows.append({"cluster": "SECTOR", "name": sec,
                     "share_global": round(max(r2g, 0), 4),
                     "share_chain_incremental": round(max(r2c - r2g, 0), 4),
                     "share_sector_incremental": round(max(r2s - r2c, 0), 4),
                     "share_idio": round(max(1 - r2s, 0), 4),
                     "n_member_days": int(len(g))})
    # chains
    chains = m[m.chain.notna()].groupby("chain").historical_date.nunique()
    chains = chains[chains >= 120].index.tolist()
    for ch in chains:
        g = m[m.chain == ch].dropna(subset=["return_7d", "mkt_ret_7d"])
        if len(g) < 500:
            continue
        y = g.return_7d.values.astype(float)
        X1 = g.mkt_ret_7d.values.astype(float)
        sst = float(((y - y.mean()) ** 2).sum())
        b1, *_ = np.linalg.lstsq(np.column_stack([np.ones_like(X1), X1]), y, rcond=None)
        r1 = y - np.column_stack([np.ones_like(X1), X1]) @ b1
        r2g = 1 - float((r1 ** 2).sum()) / max(sst, 1e-12)
        oks = g.sector_ret_7d.notna()
        if oks.sum() >= 200:
            X3 = np.column_stack([np.ones(oks.sum()),
                                  g.loc[oks, "sector_ret_7d"].values.astype(float)])
            b3, *_ = np.linalg.lstsq(X3, r1[oks], rcond=None)
            r3 = r1.copy()
            r3[oks] = r1[oks] - X3 @ b3
            r2s = 1 - float((r3 ** 2).sum()) / max(sst, 1e-12)
        else:
            r2s = r2g
        rows.append({"cluster": "CHAIN", "name": ch,
                     "share_global": round(max(r2g, 0), 4),
                     "share_chain_incremental": 0.0,
                     "share_sector_incremental": round(max(r2s - r2g, 0), 4),
                     "share_idio": round(max(1 - r2s, 0), 4),
                     "n_member_days": int(len(g))})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "10_HIERARCHY_MAP.csv", index=False)
    with open(OUT / "10_HIERARCHY_MAP.json", "w") as fh:
        json.dump(df.to_dict(orient="records"), fh, indent=2, default=str)
    return {"h": df}


# ----------------------------------------------------------------------------
# Workstream J - information flow (transfer entropy + surrogates)
# ----------------------------------------------------------------------------

def _te(x, y, lag=1, bins=3):
    """TE X->Y at lag: I(Y_{t+lag}; X_t | Y_t) with tercile binning (nats)."""
    def _bin(v):
        v = np.asarray(v, float)
        q = np.nanquantile(v, [1 / 3, 2 / 3])
        if np.isnan(q).any():
            return np.full(len(v), bins, dtype=int)
        d = np.digitize(v, q)
        d[np.isnan(v)] = bins
        return d.astype(int)
    dx = _bin(x)
    dy = _bin(y)
    n = len(y)
    yt = dy[: n - lag]
    xt = dx[: n - lag]
    yf = dy[lag:]
    # joint counts y_{t+lag}, y_t
    def _H(counts, tot):
        p = counts[counts > 0] / tot
        return -float((p * np.log(p)).sum())
    tot = len(yt)
    c_yf = np.bincount(yf, minlength=bins + 1)
    c_yt = np.bincount(yt, minlength=bins + 1)
    c_yf_yt = np.bincount(yt * (bins + 1) + yf, minlength=(bins + 1) ** 2)
    H_yf = _H(c_yf, tot)
    H_yf_yt = _H(c_yf_yt, tot)
    # conditional entropy H(Y_{t+lag} | Y_t, X_t)
    H_yf_yt_xt = 0.0
    for xv in range(bins + 1):
        for yv in range(bins + 1):
            m = (xt == xv) & (yt == yv)
            nm = int(m.sum())
            if nm < 10:
                continue
            cnt = np.bincount(yf[m], minlength=bins + 1)
            H_yf_yt_xt += nm / tot * _H(cnt, nm)
    return max(H_yf_yt - H_yf_yt_xt, 0.0)


def ws_j(d, bm, a_df, feat, inp):
    dates = d.historical_date.values
    Wv = bm.pivot(index="historical_date", columns="rank_band",
                  values="median_rank_velocity_7d").reindex(index=dates, columns=BANDS)
    pairs = [
        ("STABLECOIN->BAND11_25_VEL", d.stablecoin_change_30d.values, Wv["11-25"].values),
        ("STABLECOIN->BREADTH", d.stablecoin_change_30d.values,
         d.top500_breadth_30d.values),
    ]
    chain_agg, _ = M1.chain_native_aggregates(feat, inp["chainmap"])
    cf = _chain_flow_ready(inp["chainflow"])
    ca = chain_agg.copy()
    ca["improving_share"] = ca.n_improving / ca.n_top500.clip(lower=1)
    # top chain by merged coverage (avoids mapping-only names like ABSTRACT)
    cov = ca.merge(cf[["historical_date", "chain", "tvl_chg7"]],
                   on=["historical_date", "chain"], how="inner") \
        .groupby("chain").size().sort_values(ascending=False)
    top_ch = cov.index[0]
    ca = ca[ca.chain == top_ch].sort_values("historical_date")
    cf = cf[cf.chain == top_ch].sort_values("historical_date")
    mrg = ca.merge(cf[["historical_date", "tvl_chg7"]], on="historical_date", how="inner")
    pairs.append(("CHAIN_TVL->NATIVE_IMPROVING",
                  mrg.tvl_chg7.values.astype(float),
                  mrg.improving_share.values.astype(float)))
    rng = np.random.default_rng(SEED + 7)
    rows = []
    for name, x, y in pairs:
        te_obs = _te(x, y)
        ge = 0
        for _ in range(PERM_N):
            off = BLOCK_DAYS + int(rng.integers(1, max(2, len(x) - BLOCK_DAYS)))
            xs = np.roll(x, off)
            if _te(xs, y) >= te_obs:
                ge += 1
        rows.append({"pair": name, "te_nats": round(te_obs, 5),
                     "surrogate_p": round((ge + 1) / (PERM_N + 1), 4),
                     "n": int(len(x))})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "16_INFORMATION_FLOW.csv", index=False)
    return {"j": df}


# ----------------------------------------------------------------------------
# Topology (band/sector correlation graphs)
# ----------------------------------------------------------------------------

def ws_topology(d, bm, sd):
    dates = d.historical_date.values
    Wr = bm.pivot(index="historical_date", columns="rank_band",
                  values="median_return_1d").reindex(index=dates, columns=BANDS)
    C = Wr.corr()
    # threshold: |corr| >= 0.8 adjacency
    adj = (C.abs() >= 0.8).values.astype(int)
    np.fill_diagonal(adj, 0)
    # connected components (union-find)
    n = len(BANDS)
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    for i in range(n):
        for j in range(n):
            if adj[i, j]:
                union(i, j)
    comps = {}
    for i in range(n):
        comps.setdefault(find(i), []).append(BANDS[i])
    density = float(adj.sum() / (n * (n - 1)))
    # sector graph (top 20 sectors by active days)
    sec_top = sd.groupby("sector").historical_date.nunique().sort_values(
        ascending=False).head(20).index.tolist()
    Ws = sd[sd.sector.isin(sec_top)].pivot(index="historical_date", columns="sector",
                                           values="median_ret_7d")
    Cs = Ws.corr()
    adj_s = (Cs.abs() >= 0.5).values.astype(int)
    np.fill_diagonal(adj_s, 0)
    dens_s = float(adj_s.sum() / max(len(sec_top) * (len(sec_top) - 1), 1))
    out = {"band_graph": {"nodes": BANDS, "density": round(density, 4),
                          "connected_components": [c for c in comps.values()]},
           "sector_graph": {"n_sectors": len(sec_top), "density": round(dens_s, 4),
                            "mean_abs_corr": round(float(Cs.abs().values[np.triu_indices(
                                len(sec_top), 1)].mean()), 4) if len(sec_top) > 1 else np.nan}}
    with open(OUT / "14_TOPOLOGY_REPORT.json", "w") as fh:
        json.dump(out, fh, indent=2, default=str)
    return out


# ----------------------------------------------------------------------------
# causality ladder + nulls + subperiod stability + test counts
# ----------------------------------------------------------------------------

def finalize(a_df, b_df, c_df, d_df, e_df, f_df, g_df, h_df, j_df, state_days,
             test_counts):
    # ---- causality ladder ----
    ladder_rows = []
    def add_claim(claim, levels, evidence):
        ladder_rows.append({"claim": claim, "highest_level": levels,
                            "evidence": evidence})
    a_cls = a_df.classification.value_counts() if len(a_df) else {}
    add_claim("BAND_LEAD_LAG_STRUCTURAL",
              "L3" if a_cls.get("STRUCTURAL_LEAD_LAG", 0) >= 5 else
              ("L1" if a_cls.get("STRUCTURAL_LEAD_LAG", 0) >= 1 else "L0"),
              f"A: {a_cls.to_dict()}")
    b_cond = int((b_df.state_conditioned == True).sum()) if len(b_df) and \
        "state_conditioned" in b_df.columns else 0
    add_claim("STATE_CONDITIONED_LEAD_LAG",
              "L2" if b_cond >= 3 else "L1",
              f"B: {b_cond} state-conditioned cells")
    if len(c_df):
        add_claim("RANK_MIGRATION_PRECURSORS",
                  "L1" if len(c_df) else "L0",
                  f"C: {len(c_df)} event-date rows")
    if len(d_df):
        same = d_df.same_day_corr.median() if "same_day_corr" in d_df.columns else np.nan
        add_claim("LEADER_FIRST_SECTOR_PROPAGATION",
                  "L1", f"D: {len(d_df)} episodes; same-day corr med {same}")
    if len(e_df):
        sig = int((e_df.fdr_q < 0.05).sum()) if "fdr_q" in e_df.columns else 0
        add_claim("CHAIN_FLOW_HIERARCHY",
                  "L3" if sig >= 10 else ("L1" if sig >= 1 else "L0"),
                  f"E: {sig} FDR-significant chain links")
    add_claim("PROPAGATION_FAILURE_SIGNATURES", "L1",
              f"F: {len(f_df)} pattern-outcome rows")
    add_claim("RECURRING_MORPHISMS", "L1",
              f"G: {g_df.recurring.sum() if 'recurring' in g_df.columns else 'n/a'} recurring motifs")
    add_claim("HIERARCHY_GLOBAL_DOMINANCE",
              "L1" if len(h_df) and h_df.share_global.median() > 0.3 else "L0",
              f"H: {len(h_df)} clusters")
    add_claim("INFORMATION_FLOW",
              "L2" if len(j_df) and (j_df.surrogate_p < 0.05).any() else "L0",
              f"J: {len(j_df)} pairs")
    ladder = pd.DataFrame(ladder_rows)
    ladder.to_csv(OUT / "11_CAUSALITY_LADDER.csv", index=False)
    # ---- nulls ----
    null_rows = []
    if len(a_df):
        null_rows.append({"workstream": "A", "test": "band lead-lag",
                          "classification": "WEAK",
                          "count": int((a_df.classification == "WEAK").sum())})
        null_rows.append({"workstream": "A", "test": "band lead-lag",
                          "classification": "COMMON_FIELD_EFFECT",
                          "count": int((a_df.classification == "COMMON_FIELD_EFFECT").sum())})
    if len(b_df):
        for s, g in b_df.groupby("state"):
            null_rows.append({"workstream": "B", "test": f"state={s}",
                              "classification": "NOT_STATE_CONDITIONED",
                              "count": int((g.state_conditioned == False).sum())})
    if len(e_df):
        for l, g in e_df.groupby("link"):
            ns = int((g.fdr_q >= 0.05).sum()) if "fdr_q" in g.columns else int(len(g))
            null_rows.append({"workstream": "E", "test": f"link={l}",
                              "classification": "NOT_SIGNIFICANT", "count": ns})
    pd.DataFrame(null_rows).to_csv(OUT / "17_NULL_AND_FAILED_RESULTS.csv", index=False)
    # ---- subperiod stability ----
    sp_rows = []
    if len(e_df) and "fdr_q" in e_df.columns:
        sig_links = e_df[e_df.fdr_q < 0.05].link.unique()
        for l in sig_links[:10]:
            g = e_df[e_df.link == l]
            n_pos = int((g["corr"] > 0).sum())
            n_tot = int(len(g))
            sp_rows.append({"mechanism": f"CHAIN:{l}", "subperiod": "all",
                            "effect": "LEAD",
                            "direction": "POS" if n_pos / max(n_tot, 1) > 0.5 else "NEG",
                            "n_pos_links": n_pos, "n_links": n_tot})
    if len(a_df) and "classification" in a_df.columns:
        for cls in ["STRUCTURAL_LEAD_LAG", "COMMON_FIELD_EFFECT"]:
            g = a_df[a_df.classification == cls]
            if len(g):
                n_pos = int((g.best_corr > 0).sum()) if "best_corr" in g.columns else 0
                sp_rows.append({"mechanism": f"BAND:{cls}", "subperiod": "all",
                                "effect": "LEAD",
                                "direction": "POS" if n_pos / max(len(g), 1) > 0.5 else "NEG",
                                "n_pos_links": n_pos, "n_links": int(len(g))})
    pd.DataFrame(sp_rows).to_csv(OUT / "18_SUBPERIOD_STABILITY.csv", index=False)
    # ---- test counts ----
    tc = pd.DataFrame([{"workstream": k, "statistical_tests": v}
                       for k, v in test_counts.items()])
    tc.to_csv(OUT / "19_TEST_COUNT_RECONCILIATION.csv", index=False)
    return ladder, pd.DataFrame(null_rows)


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("ALT_MECH_2 :: CONDITIONAL PROPAGATION / CAUSAL HIERARCHY / FIELD GEOMETRY")
    print("=" * 70)
    OUT.mkdir(parents=True, exist_ok=True)
    inp, tl = _cache_step("inputs", load)
    json.dump(tl, open(OUT / "02_DATA_TRUTH.json", "w"), indent=2, default=str)
    print(f"[truth-lock] all_pass={tl['all_pass']}")
    if not tl["all_pass"]:
        print("TRUTH LOCK FAILED:", tl["checks"])
        sys.exit(1)
    feat, terrain, glob, rb = inp["feat"], inp["terrain"], inp["glob"], inp["rb"]

    d, bm = _cache_step("factors", lambda: build_factors(feat, terrain, glob, rb))
    d = assign_states(d)
    d.to_csv(OUT / "03_STATE_DEFINITIONS_daily.csv", index=False)
    d["historical_date"] = pd.to_datetime(d.historical_date)

    rA = _cache_step("A", lambda: ws_a(d, bm))
    rB = _cache_step("B", lambda: ws_b(d, bm))
    sd_sector, mem_sector = _cache_step(
        "sector", lambda: M1.sector_daily(inp))
    rC = _cache_step("C", lambda: ws_c(feat, inp, sd=sd_sector))
    rD = _cache_step("D", lambda: ws_d(sd_sector, mem_sector, feat=feat))
    rE = _cache_step("E", lambda: ws_e(feat, inp))
    rF = _cache_step("F", lambda: ws_f(d, bm, feat, inp))
    daily = M1.daily_market_frame(feat, terrain, glob)
    daily, sep, tmat, fwd = M1.routing_analysis(daily)
    daily.to_csv(OUT / "15_DYNAMICAL_STATE_daily.csv", index=False)
    tmat.to_csv(OUT / "15_DYNAMICAL_STATE_TRANSITIONS.csv")
    rG = _cache_step("G", lambda: ws_g(daily))
    rH = _cache_step("H", lambda: ws_h(feat, inp, sd=sd_sector))
    rJ = _cache_step("J", lambda: ws_j(d, bm, rA["a"], feat, inp))
    topo = _cache_step("topology", lambda: ws_topology(d, bm, sd_sector))

    test_counts = {
        "A_common_factor_band_leadlag": rA["test_count"],
        "B_conditional_leadlag": rB["test_count"],
        "E_chain_hierarchy": rE["test_count"],
        "D_leader_first": len(rD["d"]) if len(rD["d"]) else 0,
    }
    ladder, nulls = finalize(rA["a"], rB["b"], rC["c"], rD["d"], rE["e"], rF["f"],
                             rG["g"], rH["h"], rJ["j"], rB["state_days"], test_counts)

    print("DONE.")
    print("artifacts written to", OUT)


if __name__ == "__main__":
    main()
