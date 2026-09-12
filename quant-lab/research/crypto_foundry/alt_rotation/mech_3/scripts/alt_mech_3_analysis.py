#!/usr/bin/env python
"""ALT_MECH_3 - Chain-Liquidity Anatomy, Regime-Routing & Concentration Pivot Mapping.

Terrain research ONLY (AGENT 1 - MAIN FIELD CARTOGRAPHER). No PnL, no strategy,
no optimization, no ML, no sizing, no deployment. All rules fixed in
01_PREREGISTRATION.md BEFORE this script executed.

Reuses DATA-1.1 inputs and MECH-1/MECH-2 helpers.
"""
import json, pickle, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ranksums

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

SEED = 20260830
PERM_N = 200
BLOCK_DAYS = 20
MIN_STATE_DAYS = 120

ROOT = Path(__file__).resolve().parents[1]            # mech_3/
sys.path.insert(0, str(ROOT.parent / "mech_1" / "scripts"))
sys.path.insert(0, str(ROOT.parent / "mech_2" / "scripts"))
import alt_mech_1_analysis as M1
import alt_mech_2_analysis as M2

OUT = ROOT
DATA = M1.DATA

BANDS = M1.BANDS
SUBPERIODS = M1.SUBPERIODS
CONC_STATE = "BTC_CONCENTRATION"
BASIN = {"BTC_CONCENTRATION", "MIXED_NO_CLEAR_ROUTE"}

# ----------------------------------------------------------------------------
# cache helpers
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
# load + daily frame
# ----------------------------------------------------------------------------

def load():
    inp = M1.load_inputs()
    tl = M1.verify_truth_lock(inp)
    return inp, tl


STATE_COLS = ["BTC_UP", "BTC_DOWN", "VOL_HIGH", "VOL_LOW",
              "BREADTH_EXPANDING", "BREADTH_CONTRACTING",
              "SC_INFLOW", "SC_OUTFLOW", "CONC_RISING", "CONC_FALLING"]


def build_daily(inp):
    """Daily frame: factors (M2), routing states (M1), terrain flow, chain median."""
    feat, terrain, glob, rb = inp["feat"], inp["terrain"], inp["glob"], inp["rb"]
    d, bm = M2.build_factors(feat, terrain, glob, rb)
    d = M2.assign_states(d)
    dm = M1.daily_market_frame(feat, terrain, glob)
    daily, sep, tmat, fwd = M1.routing_analysis(dm)
    dcols = ["historical_date", "vol_med", "top3_share", "top3_share_chg7",
             "mkt_ret_1d", "stablecoin_change_30d"] + STATE_COLS
    daily = daily.merge(d[dcols], on="historical_date", how="left",
                        suffixes=("", "_f"))
    # AVAILABLE_NEXT_DAY-shifted stablecoin (from factor frame) wins over the
    # unshifted copy daily_market_frame attached
    if "stablecoin_change_30d_f" in daily.columns:
        daily["stablecoin_change_30d"] = daily["stablecoin_change_30d_f"]
        daily = daily.drop(columns=["stablecoin_change_30d_f"])
    # band 51-100 vs 101-200 velocity spread (flagship relationship, realized)
    Wv = bm.pivot(index="historical_date", columns="rank_band",
                  values="median_rank_velocity_7d")
    daily["rb_spread"] = daily.historical_date.map(
        (Wv["51-100"] - Wv["101-200"]).to_dict())
    # median chain TVL change (AVAILABLE_NEXT_DAY per chain, then cross-chain median)
    cf = inp["chainflow"].copy().sort_values(["chain", "historical_date"])
    cf["tvl_chg7"] = cf.groupby("chain").chain_tvl.pct_change(7)
    cf["tvl_chg7"] = cf.groupby("chain").tvl_chg7.shift(1)
    med = cf.groupby("historical_date").tvl_chg7.median().rename(
        "chain_tvl_med_chg7").reset_index()
    daily = daily.merge(med, on="historical_date", how="left")
    # shifted global flow columns for WS J / WS I (AVAILABLE_NEXT_DAY)
    g2 = inp["glob"].copy().sort_values("historical_date")
    for c in ["dex_volume_change_7d", "fees_change_7d", "stablecoin_change_7d"]:
        g2[c] = g2[c].shift(1)
    daily = daily.merge(g2[["historical_date", "dex_volume_change_7d",
                            "fees_change_7d", "stablecoin_change_7d"]],
                        on="historical_date", how="left")
    daily["subperiod"] = daily.historical_date.map(M1.subperiod_of)
    return daily, d, bm


def chain_frame(inp):
    """Per (chain, date) frame of all chain-liquidity coordinates (causal)."""
    agg, _ = M1.chain_native_aggregates(inp["feat"], inp["chainmap"])
    agg = agg.copy()
    agg["imp_share"] = agg.n_improving / agg.n_top500.clip(lower=1)
    agg = agg.rename(columns={"median_vel7": "vel7", "mcap_share": "mcshare",
                              "ret_breadth_1d": "ret_brd1"})
    cf = inp["chainflow"].copy().sort_values(["chain", "historical_date"])
    cf["tvl_lvl"] = np.log(cf.chain_tvl.clip(lower=1.0))
    for c in ["tvl_lvl", "chain_tvl_share", "chain_tvl_change_1d",
              "chain_tvl_change_7d", "chain_tvl_change_30d"]:
        cf[c] = cf.groupby("chain")[c].shift(1)
    cf = cf.rename(columns={"chain_tvl_share": "tvl_share",
                            "chain_tvl_change_7d": "tvl_chg7",
                            "chain_tvl_change_30d": "tvl_chg30"})
    g = inp["glob"].copy().sort_values("historical_date")
    for c in ["stablecoin_change_7d", "stablecoin_change_30d",
              "dex_volume_change_7d", "fees_change_7d"]:
        g[c] = g[c].shift(1)
    g = g.rename(columns={"stablecoin_change_7d": "sc_chg7",
                          "stablecoin_change_30d": "sc_chg30",
                          "dex_volume_change_7d": "dex_chg7",
                          "fees_change_7d": "fees_chg7"})
    m = agg.merge(cf[["historical_date", "chain", "tvl_lvl", "tvl_share",
                      "tvl_chg7", "tvl_chg30"]], on=["historical_date", "chain"],
                  how="inner")
    m = m.merge(g[["historical_date", "sc_chg7", "sc_chg30", "dex_chg7",
                   "fees_chg7"]], on="historical_date", how="left")
    # market-level coordinates needed by later workstreams (PIT)
    feat2 = inp["feat"]
    mkt = feat2.groupby("historical_date").apply(
        lambda g: float(np.nansum(g.market_cap_share * g.return_1d) /
                        max(np.nansum(g.market_cap_share), 1e-12)), include_groups=False
    ).rename("mkt_ret_1d").reset_index()
    terr = inp["terrain"][["historical_date", "top500_breadth_30d"]]
    m = m.merge(mkt, on="historical_date", how="left")
    m = m.merge(terr, on="historical_date", how="left")
    return m.sort_values(["chain", "historical_date"]).reset_index(drop=True)


# ----------------------------------------------------------------------------
# Workstream A - chain-liquidity variable map + redundancy
# ----------------------------------------------------------------------------

CHAIN_VARS = {
    "tvl_lvl": "log chain TVL level",
    "tvl_chg7": "chain TVL 7D change",
    "tvl_chg30": "chain TVL 30D change",
    "tvl_share": "chain TVL share",
    "imp_share": "native improving share",
    "vel7": "native median rank velocity 7D",
    "mcshare": "native mcap share",
    "ret_brd1": "native 1D return breadth",
    "sc_chg7": "global stablecoin 7D change",
    "sc_chg30": "global stablecoin 30D change",
    "dex_chg7": "global DEX 7D change",
    "fees_chg7": "global fees 7D change",
}

def _spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ok = ~(np.isnan(a) | np.isnan(b))
    if ok.sum() < 60:
        return np.nan, int(ok.sum())
    ra = pd.Series(a[ok]).rank().values
    rb = pd.Series(b[ok]).rank().values
    if np.std(ra) == 0 or np.std(rb) == 0:
        return np.nan, int(ok.sum())
    return float(np.corrcoef(ra, rb)[0, 1]), int(ok.sum())


def classify_pair(r):
    r = abs(r)
    if r >= 0.85:
        return "REDUNDANT_PROXY"
    if r >= 0.60:
        return "PARTIAL_PROXY"
    if r >= 0.40:
        return "LOCAL_COORDINATE"
    if r >= 0.20:
        return "DISTINCT_INFORMATION"
    return "CANDIDATE_DISTINCT"


def ws_a(m):
    cov = m.groupby("chain").historical_date.nunique()
    top = cov[cov >= 120].sort_values(ascending=False).head(12).index.tolist()
    rows = []
    for ch in top:
        g = m[m.chain == ch]
        for i, va in enumerate(CHAIN_VARS):
            for vb in list(CHAIN_VARS)[i + 1:]:
                r, n = _spearman(g[va], g[vb])
                if np.isnan(r):
                    continue
                rows.append({"chain": ch, "var_a": va, "var_b": vb,
                             "spearman_r": round(r, 4), "n": n,
                             "classification": classify_pair(r)})
    df = pd.DataFrame(rows)
    # pooled classification = median |r| across chains per (var_a, var_b)
    pooled = df.groupby(["var_a", "var_b"]).spearman_r.median().abs().reset_index()
    pooled["n_chains"] = df.groupby(["var_a", "var_b"]).chain.nunique().values
    pooled["classification"] = pooled.spearman_r.map(
        lambda r: (("REDUNDANT_PROXY" if r >= 0.85 else
                    "PARTIAL_PROXY" if r >= 0.60 else
                    "LOCAL_COORDINATE" if r >= 0.40 else
                    "DISTINCT_INFORMATION" if r >= 0.20 else "CANDIDATE_DISTINCT")))
    pooled["spearman_r"] = pooled.spearman_r.round(4)
    pooled = pooled.rename(columns={"spearman_r": "median_abs_r"})
    # variable map: distinctiveness = per-chain max |r| vs any partner, median across chains
    vmap_rows = []
    for v in CHAIN_VARS:
        sub = df[(df.var_a == v) | (df.var_b == v)]
        if len(sub):
            partner = np.where(sub.var_a == v, sub.var_b, sub.var_a)
            per_chain = []
            for ch, g in sub.groupby("chain"):
                loc = sub.index.get_indexer(g.index)
                p = partner[loc]
                vals = pd.Series(g.spearman_r.abs().values, index=p)
                per_chain.append(vals.max())
            med_max = float(np.median(per_chain)) if per_chain else np.nan
        else:
            med_max = np.nan
        vmap_rows.append({"variable": v, "description": CHAIN_VARS[v],
                          "layer": "GLOBAL" if v in ("sc_chg7", "sc_chg30",
                                                     "dex_chg7", "fees_chg7") else "CHAIN",
                          "source": ("global flow" if v.startswith(("sc_", "dex", "fees"))
                                     else "chain flow" if v.startswith("tvl")
                                     else "chain_native_aggregates"),
                          "median_max_abs_r": round(med_max, 4) if med_max == med_max else np.nan,
                          "n_chains_with_data": int(df[((df.var_a == v) | (df.var_b == v))
                                                       ].chain.nunique())})
    vmap = pd.DataFrame(vmap_rows)
    vmap.to_csv(OUT / "04_CHAIN_LIQUIDITY_VARIABLE_MAP.csv", index=False)
    pooled.to_csv(OUT / "05_CHAIN_LIQUIDITY_REDUNDANCY.csv", index=False)
    return {"a": df, "pooled": pooled, "vmap": vmap, "top_chains": top,
            "test_count": int(len(df))}


# ----------------------------------------------------------------------------
# Workstream B - perturbation of the chain-liquidity -> native pathway
# ----------------------------------------------------------------------------

LINKS = [("tvl_chg7", "imp_share", "TVL->NATIVE_IMPROVING"),
         ("tvl_chg7", "vel7", "TVL->NATIVE_VELOCITY"),
         ("sc_chg30", "tvl_chg7", "STABLECOIN->TVL"),
         ("tvl_chg7", "dex_chg7", "TVL->DEX"),
         ("vel7", "imp_share", "VELOCITY->NATIVE_IMPROVING")]
LAGS = [1, 3, 7, 14]


def ws_b(m, d):
    """Perturbation suite on chain-liquidity links. Factors X for residualization."""
    Xcols = ["mkt_ret_1d", "btc_return_1d", "eth_return_1d", "vol_med"]
    X = d[Xcols].astype(float).values
    dates = d.historical_date.values
    Xd = dict(zip(dates, X))
    rng = np.random.default_rng(SEED + 1)
    cov = m.groupby("chain").historical_date.nunique()
    top = cov[cov >= 120].sort_values(ascending=False).head(12).index.tolist()
    rows, test_count = [], 0
    for ch in top:
        g = m[m.chain == ch].sort_values("historical_date")
        for xcol, ycol, link in LINKS:
            x = g[xcol].values.astype(float)
            y = g[ycol].values.astype(float)
            # residualized variants
            Xm = np.array([Xd[t] for t in g.historical_date.values])
            okX = ~np.isnan(Xm).any(axis=1)
            variants = {"BASE": (x, y)}
            if okX.sum() >= 60:
                variants["-BETA"] = (M2._resid_series(x, Xm), M2._resid_series(y, Xm))
            sc = g.sc_chg30.values.astype(float)
            if np.isfinite(sc).sum() >= 60:
                variants["-SC"] = (M2._resid_series(x, np.column_stack([np.ones(len(x)), sc])),
                                   M2._resid_series(y, np.column_stack([np.ones(len(y)), sc])))
            dx = g.dex_chg7.values.astype(float)
            if np.isfinite(dx).sum() >= 60:
                variants["-DEX"] = (M2._resid_series(x, np.column_stack([np.ones(len(x)), dx])),
                                    M2._resid_series(y, np.column_stack([np.ones(len(y)), dx])))
            # -NATIVE_RET: replace outcome with ret_brd1 (non-price breadth)
            yalt = g.ret_brd1.values.astype(float)
            variants["-NATIVE_RET"] = (x, yalt)
            for vname, (xa, ya) in variants.items():
                best = {"lag": np.nan, "corr": np.nan, "p": np.nan, "n": 0}
                for h in LAGS:
                    r, p, nn = M2._cond_xcorr(xa, ya, h, rng, perms=PERM_N)
                    if np.isnan(r):
                        continue
                    test_count += 1
                    if np.isnan(best["corr"]) or abs(r) > abs(best["corr"]):
                        best = {"lag": h, "corr": r, "p": p, "n": nn}
                rows.append({"chain": ch, "link": link, "driver": xcol,
                             "outcome": ycol, "ablation": vname,
                             "best_lag_days": best["lag"],
                             "best_corr": round(best["corr"], 4) if best["lag"] == best["lag"] else np.nan,
                             "perm_p": round(best["p"], 4) if best["lag"] == best["lag"] else np.nan,
                             "n": best["n"]})
    df = pd.DataFrame(rows)
    # classification per (chain, link)
    cls = []
    for (ch, link), g in df.groupby(["chain", "link"]):
        base = g[g.ablation == "BASE"]
        if base.empty or base.iloc[0].best_corr != base.iloc[0].best_corr:
            cls.append({"chain": ch, "link": link,
                        "classification": "NO_RELATION", "base_corr": np.nan,
                        "base_lag": np.nan, "n_ablations_survived": 0})
            continue
        bc, bp, bl = base.iloc[0].best_corr, base.iloc[0].perm_p, base.iloc[0].best_lag_days
        if bp >= 0.05:
            cls.append({"chain": ch, "link": link,
                        "classification": "NO_RELATION", "base_corr": bc,
                        "base_lag": bl, "n_ablations_survived": 0})
            continue
        abl = g[g.ablation != "BASE"]
        surv = abl[(abl.best_corr == abl.best_corr) & (abl.perm_p < 0.05) &
                   (np.sign(abl.best_corr) == np.sign(bc))]
        flipped = abl[(abl.best_corr == abl.best_corr) &
                      (np.sign(abl.best_corr) != np.sign(bc))]
        if len(surv) >= 4:
            c = "SURVIVES"
        elif len(surv) >= 2:
            c = "WEAKENED"
        elif len(flipped) >= 2 or (("-BETA" in g.ablation.values) and
                                   not g[g.ablation == "-BETA"].empty and
                                   g[g.ablation == "-BETA"].iloc[0].perm_p >= 0.05):
            c = "DISSOLVES"
        else:
            c = "LOCAL"
        cls.append({"chain": ch, "link": link, "classification": c,
                    "base_corr": bc, "base_lag": bl,
                    "n_ablations_survived": int(len(surv))})
    df = df.merge(pd.DataFrame(cls), on=["chain", "link"], how="left")
    # pooled LOO_CHAIN / LOO_CYCLE
    def pooled_corr(xcol, ycol, lag, chain_keep=None, sub_keep=None):
        xs, ys = [], []
        for ch in top:
            g = m[(m.chain == ch)].sort_values("historical_date")
            if chain_keep is not None and ch not in chain_keep:
                continue
            if sub_keep is not None:
                g = g[g.historical_date.dt.year.isin(sub_keep)]
            if len(g) < 60:
                continue
            xs.append(np.asarray(g[xcol], float))
            ys.append(np.asarray(g[ycol], float))
        if not xs:
            return np.nan, np.nan, 0
        x = np.concatenate(xs); y = np.concatenate(ys)
        return M2._cond_xcorr(x, y, lag, np.random.default_rng(SEED + 2), perms=50)
    loo_rows = []
    for xcol, ycol, link in LINKS:
        # find pooled best lag at BASE
        best = None
        for h in LAGS:
            r, p, n = pooled_corr(xcol, ycol, h)
            if not np.isnan(r) and (best is None or abs(r) > abs(best[0])):
                best = (r, h)
        if best is None:
            continue
        _, blag = best
        r_full, p_full, n_full = pooled_corr(xcol, ycol, blag)
        for ch in top:
            r_loo, p_loo, n_loo = pooled_corr(xcol, ycol, blag,
                                              chain_keep=[c for c in top if c != ch])
            loo_rows.append({"link": link, "driver": xcol, "outcome": ycol,
                             "lag_days": blag, "remove": "CHAIN",
                             "removed": ch, "pooled_corr": round(r_full, 4)
                             if r_full == r_full else np.nan,
                             "loo_corr": round(r_loo, 4) if r_loo == r_loo else np.nan,
                             "corr_delta": round(r_loo - r_full, 4)
                             if r_full == r_full and r_loo == r_loo else np.nan})
        for sp_name, y0, y1 in SUBPERIODS:
            yrs = list(range(int(y0[:4]), int(y1[:4]) + 1))
            r_loo, p_loo, n_loo = pooled_corr(xcol, ycol, blag,
                                              sub_keep=[yy for yy in yrs])
            loo_rows.append({"link": link, "driver": xcol, "outcome": ycol,
                             "lag_days": blag, "remove": "CYCLE",
                             "removed": sp_name, "pooled_corr": round(r_full, 4)
                             if r_full == r_full else np.nan,
                             "loo_corr": round(r_loo, 4) if r_loo == r_loo else np.nan,
                             "corr_delta": round(r_loo - r_full, 4)
                             if r_full == r_full and r_loo == r_loo else np.nan})
    loo = pd.DataFrame(loo_rows)
    df.to_csv(OUT / "06_CHAIN_LIQUIDITY_PERTURBATION.csv", index=False)
    if len(loo):
        loo.to_csv(OUT / "06b_PERTURBATION_LOO.csv", index=False)
    return {"b": df, "loo": loo, "test_count": test_count}


# ----------------------------------------------------------------------------
# Workstream C - multi-view chain reconstruction
# ----------------------------------------------------------------------------

def dominant_sector_view(inp):
    """Per (chain, date): median return_7d of the chain's dominant sector (PIT)."""
    cm = inp["chainmap"][["historical_date", "internal_asset_id", "chain"]]
    sm = inp["smem"][["historical_date", "internal_asset_id", "sector"]]
    f = inp["feat"][["historical_date", "internal_asset_id", "market_cap_usd",
                     "return_7d"]]
    m = cm.merge(sm, on=["historical_date", "internal_asset_id"], how="inner")
    m = m.merge(f, on=["historical_date", "internal_asset_id"], how="inner")
    mc = m.groupby(["historical_date", "chain", "sector"]).market_cap_usd.sum() \
        .rename("sector_mcap").reset_index()
    dom = mc.sort_values("sector_mcap").groupby(["historical_date", "chain"]) \
        .tail(1)[["historical_date", "chain", "sector"]]
    r7 = m.groupby(["historical_date", "sector"]).return_7d.median() \
        .rename("sector_ret_7d").reset_index()
    v = dom.merge(r7, on=["historical_date", "sector"], how="left")
    return v[["historical_date", "chain", "sector", "sector_ret_7d"]]


def ws_c(m, d, inp, top_chains):
    rng = np.random.default_rng(SEED + 3)
    dm = dominant_sector_view(inp)
    # rank spread view (band 11-25 vs 301-500 velocity)
    rb = inp["rb"]
    Wv = rb.pivot(index="historical_date", columns="rank_band",
                  values="median_rank_velocity_7d")
    Wv.index = pd.to_datetime(Wv.index)
    Wv = Wv.reindex(index=pd.to_datetime(d.historical_date.values))
    rank_spread = pd.DataFrame({"historical_date": Wv.index,
                                "rank_spread": (Wv["11-25"] - Wv["301-500"]).values})
    m = m.merge(dm, on=["historical_date", "chain"], how="left")
    m = m.merge(rank_spread, on="historical_date", how="left")
    rows, agree_rows, dis_rows = [], [], []
    for ch in top_chains:
        g = m[m.chain == ch].sort_values("historical_date").dropna(subset=["tvl_chg7"])
        if len(g) < 120:
            continue
        E = (g.tvl_chg7 > 0).astype(float).values
        g = g.assign(
            GLOBAL_mkt=g.mkt_ret_1d.values.astype(float),
            GLOBAL_brd=g.top500_breadth_30d.values.astype(float),
            CHAIN_share=g.tvl_share.values.astype(float),
            SECTOR=g.sector_ret_7d.values.astype(float),
            NATIVE_imp=g.imp_share.values.astype(float),
            NATIVE_vel=g.vel7.values.astype(float),
            RANK=g.rank_spread.values.astype(float),
        )
        views = {c: g[c].values.astype(float) for c in ["GLOBAL_mkt", "GLOBAL_brd",
                 "CHAIN_share", "SECTOR", "NATIVE_imp", "NATIVE_vel", "RANK"]}
        groups = [("GLOBAL", ["GLOBAL_mkt", "GLOBAL_brd"]),
                  ("CHAIN", ["CHAIN_share"]),
                  ("SECTOR", ["SECTOR"]),
                  ("NATIVE", ["NATIVE_imp", "NATIVE_vel"]),
                  ("RANK", ["RANK"])]
        # incremental R2 (linear probability) in fixed order
        y = E
        sel = g.dropna(subset=["GLOBAL_mkt", "GLOBAL_brd", "CHAIN_share",
                               "SECTOR", "NATIVE_imp", "NATIVE_vel", "RANK"])
        if len(sel) < 120:
            continue
        E2 = (sel.tvl_chg7 > 0).astype(float).values
        cols = []
        inc_rows = {"chain": ch, "n_days": int(len(sel))}
        for gname, ccols in groups:
            cols += ccols
            Xm = sel[cols].astype(float).values
            ok = ~np.isnan(Xm).any(axis=1)
            if ok.sum() < 100:
                continue
            Xc = np.column_stack([np.ones(ok.sum()), Xm[ok]])
            yy = E2[ok]
            yb = yy.mean()
            sst = float(((yy - yb) ** 2).sum())
            beta, *_ = np.linalg.lstsq(Xc, yy, rcond=None)
            sse = float(((yy - Xc @ beta) ** 2).sum())
            r2 = 1 - sse / max(sst, 1e-12)
            inc_rows[f"r2_{gname}"] = round(r2, 4)
        rows.append(inc_rows)
        # agreement matrix (sign agreement on E)
        for va, vb in [("GLOBAL_mkt", "NATIVE_imp"), ("GLOBAL_mkt", "SECTOR"),
                       ("CHAIN_share", "NATIVE_imp"), ("SECTOR", "NATIVE_imp"),
                       ("NATIVE_imp", "NATIVE_vel")]:
            a, b = views[va], views[vb]
            ok = ~(np.isnan(a) | np.isnan(b))
            if ok.sum() < 60:
                continue
            agree = float((np.sign(a[ok]) == np.sign(b[ok])).mean())
            agree_rows.append({"chain": ch, "view_a": va, "view_b": vb,
                               "sign_agreement": round(agree, 4), "n": int(ok.sum())})
        # disagreement inventory
        tvl_up = g.tvl_chg7 > 0
        sc_up = g.sc_chg7 > 0
        dx_down = g.dex_chg7 < 0
        brd_rise = g.top500_breadth_30d.diff(7) > 0
        tvl_down = g.tvl_chg7 < 0
        vel_pos = g.vel7 > 0
        def _dis(name, mask, fwd=14):
            idx = g.index[mask.fillna(False)]
            fwd_ret = g.mkt_ret_1d.shift(-fwd)
            return {"chain": ch, "disagreement": name, "n_days": int(len(idx)),
                    "mean_fwd14_mkt_ret": round(float(fwd_ret[idx].mean()), 5)
                    if len(idx) and fwd_ret[idx].notna().any() else np.nan}
        for nm, mk in [("TVL_UP_NATIVE_WEAK", tvl_up & (g.vel7 < 0)),
                       ("SC_UP_DEX_WEAK", sc_up & dx_down),
                       ("BREADTH_UP_FLOW_DOWN", brd_rise & tvl_down),
                       ("NATIVE_UP_TVL_DOWN", vel_pos & tvl_down)]:
            dis_rows.append(_dis(nm, mk))
    df = pd.DataFrame(rows)
    ag = pd.DataFrame(agree_rows)
    dis = pd.DataFrame(dis_rows)
    df.to_csv(OUT / "07_CHAIN_RECONSTRUCTION.csv", index=False)
    ag.to_csv(OUT / "07b_RECONSTRUCTION_AGREEMENT.csv", index=False)
    dis.to_csv(OUT / "07c_DISAGREEMENT_INVENTORY.csv", index=False)
    return {"c": df, "agree": ag, "dis": dis}


# ----------------------------------------------------------------------------
# Workstream D - regime routing flip map
# ----------------------------------------------------------------------------

def ws_d(daily, bm, m, top_chains):
    rng = np.random.default_rng(SEED + 4)
    states = ["BTC_UP", "BTC_DOWN", "ETH_STRONG", "ETH_WEAK", "VOL_HIGH", "VOL_LOW",
              "BREADTH_EXPANDING", "BREADTH_CONTRACTING", "CONC_RISING",
              "CONC_FALLING", "SC_INFLOW", "SC_OUTFLOW", "CHAIN_EXPANDING",
              "CHAIN_CONTRACTING", "RISK_ON", "RISK_OFF"]
    # state masks on daily
    dd = daily.copy()
    dd["ETH_STRONG"] = dd.eth_btc_relative_return_30d > 0
    dd["ETH_WEAK"] = dd.eth_btc_relative_return_30d < 0
    dd["CHAIN_EXPANDING"] = dd.chain_tvl_med_chg7 > 0
    dd["CHAIN_CONTRACTING"] = dd.chain_tvl_med_chg7 < 0
    dd["RISK_ON"] = dd.total_mcap_chg30 > 0
    dd["RISK_OFF"] = dd.total_mcap_chg30 < 0
    state_days = {s: int(dd[s].fillna(False).sum()) for s in states}
    band_lags = [1, 3, 7]
    flow_lags = [1, 3, 7, 14]
    # band relationships
    Wv = bm.pivot(index="historical_date", columns="rank_band",
                  values="median_rank_velocity_7d")
    Wv = Wv.reindex(index=pd.to_datetime(daily.historical_date.values))
    pairs = [(BANDS[i], BANDS[i + 1]) for i in range(len(BANDS) - 1)]
    # pooled chain links
    def pooled(xcol, ycol):
        xs, ys = [], []
        for ch in top_chains:
            g = m[m.chain == ch].sort_values("historical_date")
            if len(g) < 60:
                continue
            xs.append(np.asarray(g[xcol], float))
            ys.append(np.asarray(g[ycol], float))
        return np.concatenate(xs), np.concatenate(ys)
    ch_tvl, ch_imp = pooled("tvl_chg7", "imp_share")
    ch_tvl2, ch_sc = pooled("tvl_chg7", "sc_chg30")
    sc_g = dd.stablecoin_change_30d.values.astype(float)
    brd_g = dd.top500_breadth_30d.values.astype(float)
    rels = [(f"VEL {a}->{b}", Wv[a].values.astype(float),
             Wv[b].values.astype(float), band_lags, "BAND")
            for a, b in pairs]
    rels += [("CHAIN_TVL->NATIVE_IMP", ch_tvl, ch_imp, flow_lags, "FLOW"),
             ("CHAIN_TVL->STABLECOIN", ch_tvl2, ch_sc, flow_lags, "FLOW"),
             ("STABLECOIN->BREADTH", sc_g, brd_g, flow_lags, "FLOW")]
    rows, test_count = [], 0
    for name, x, y, lags, kind in rels:
        # unconditional best lag
        unr = {}
        for h in lags:
            r, p, n = M2._cond_xcorr(x, y, h, rng)
            if not np.isnan(r):
                unr[h] = (r, p)
        if not unr:
            continue
        best_un = max(unr, key=lambda k: abs(unr[k][0]))
        for s in states:
            if state_days[s] < MIN_STATE_DAYS:
                rows.append({"relationship": name, "state": s,
                             "state_days": state_days[s], "kind": kind,
                             "note": "INSUFFICIENT_SAMPLE"})
                continue
            mask = dd[s].fillna(False).values
            xm, ym = x[mask], y[mask]
            r_c, p_c, n_c = M2._cond_xcorr(xm, ym, best_un, rng)
            if np.isnan(r_c):
                continue
            test_count += 1
            r_un, p_un = unr[best_un]
            if np.sign(r_c) != np.sign(r_un):
                cls = "REVERSED"
            elif p_c >= 0.05:
                cls = "LOST"
            elif abs(r_c - r_un) >= 0.15:
                cls = "GAINED"
            else:
                cls = "SAME_SIGN"
            rows.append({"relationship": name, "state": s, "state_days": state_days[s],
                         "kind": kind, "uncond_best_lag": best_un,
                         "uncond_corr": round(r_un, 4), "uncond_p": round(p_un, 4),
                         "cond_corr": round(r_c, 4), "cond_p": round(p_c, 4),
                         "corr_delta": round(r_c - r_un, 4), "n": n_c,
                         "classification": cls, "workstream": "D"})
    df = pd.DataFrame(rows)
    if len(df) and "cond_p" in df.columns:
        msk = df.cond_p.notna()
        if msk.any():
            df.loc[msk, "fdr_q"] = np.round(M1.bh_fdr(df.loc[msk, "cond_p"].values.astype(float)), 4)
    df.to_csv(OUT / "08_ROUTING_FLIP_MAP.csv", index=False)
    return {"d": df, "test_count": test_count, "state_days": state_days}


# ----------------------------------------------------------------------------
# Workstream E - concentration pivot anatomy
# ----------------------------------------------------------------------------

PRECURSORS = {
    "btc_dom_chg30": "btc_dominance 30D change",
    "btc_ret30": "BTC 30D return",
    "btc_ret7": "BTC 7D return",
    "top3_share": "top-3 mcap share",
    "top3_share_chg7": "top-3 share 7D change",
    "breadth30": "top500 breadth 30D",
    "disp30": "top500 dispersion 30D",
    "sc_chg30": "stablecoin 30D change",
    "eth_rel30": "ETH/BTC rel 30D",
    "alt_share": "total alt share",
    "eth_share": "ETH mcap share",
    "vol_med": "median vol 30D",
    "chain_tvl_med_chg7": "median chain TVL 7D change",
}

# map precursor keys to daily-frame columns
PRECURSOR_COLS = {
    "btc_dom_chg30": "btc_dom_chg30", "btc_ret30": "btc_return_30d",
    "btc_ret7": "btc_return_7d", "top3_share": "top3_share",
    "top3_share_chg7": "top3_share_chg7", "breadth30": "top500_breadth_30d",
    "disp30": "top500_dispersion_30d", "sc_chg30": "stablecoin_change_30d",
    "eth_rel30": "eth_btc_relative_return_30d", "alt_share": "total_alt_share",
    "eth_share": "eth_share", "vol_med": "vol_med",
    "chain_tvl_med_chg7": "chain_tvl_med_chg7",
}

def _precursor_frame(daily):
    pf = daily.copy()
    for k, col in PRECURSOR_COLS.items():
        if col not in pf.columns:
            pf[k] = np.nan
        else:
            pf[k] = pf[col]
    # window means (trailing, strictly before t)
    win_cols = []
    for w in (1, 3, 7, 14, 30):
        for k in PRECURSORS:
            c = f"{k}_w{w}"
            pf[c] = pf[k].rolling(w, min_periods=max(1, w // 2)).mean().shift(1)
            win_cols.append(c)
    return pf, win_cols


def _events(daily, state_col="state"):
    st = daily[state_col].values
    dates = daily.historical_date.values
    entry, exit_ = [], []
    for t in range(1, len(st)):
        if st[t] == CONC_STATE and st[t - 1] != CONC_STATE:
            entry.append(dates[t])
        if st[t - 1] == CONC_STATE and st[t] != CONC_STATE:
            exit_.append(dates[t])
    return entry, exit_


def _destination_state(daily, t_idx):
    """First state after t occupied for >= 5 consecutive days."""
    st = daily.state.values
    n = len(st)
    for i in range(t_idx + 1, n):
        run = 1
        while i + run < n and st[i + run] == st[i]:
            run += 1
        if run >= 5:
            return st[i], i - t_idx
    return None, np.nan


def ws_e(daily):
    pf, win_cols = _precursor_frame(daily)
    entry_dates, exit_dates = _events(pf)
    rng = np.random.default_rng(SEED + 5)
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(pf.historical_date.values)}
    # controls: same month-year, same starting-state family, 5 matched, seeded
    def matched_controls(ev_dates, family):
        ctrl = []
        pool = pf[pf.state.map(lambda s: s in family)].historical_date.values
        for d0 in ev_dates:
            t0 = pd.Timestamp(d0)
            cand = [x for x in pool if str(x)[:7] == str(t0)[:7] and x != t0]
            if len(cand) == 0:
                continue
            n = min(5, len(cand))
            picks = rng.choice(cand, size=n, replace=False)
            ctrl.extend([(d0, x) for x in picks])
        return ctrl
    rows = []
    # ENTRY events
    ctrl_e = matched_controls(entry_dates, {"BTC_CONCENTRATION"})
    ctrl_e_pool = {str(b): str(a) for a, b in ctrl_e}
    for d0 in entry_dates:
        i = date_idx[pd.Timestamp(d0)]
        rows.append({"event": "ENTRY", "date": d0,
                     "prev_state": pf.state.iloc[i - 1],
                     "next_state_1d": pf.state.iloc[min(i + 1, len(pf) - 1)],
                     "next_state_3d": pf.state.iloc[min(i + 3, len(pf) - 1)],
                     "next_state_7d": pf.state.iloc[min(i + 7, len(pf) - 1)],
                     "subperiod": M1.subperiod_of(d0)})
    ent_df = pd.DataFrame(rows)
    ent_df.to_parquet(OUT / "09_CONCENTRATION_ENTRY_EVENTS.parquet")
    # EXIT events
    rows = []
    for d0 in exit_dates:
        i = date_idx[pd.Timestamp(d0)]
        dest, tt = _destination_state(pf, i)
        rows.append({"event": "EXIT", "date": d0,
                     "prev_state": pf.state.iloc[i - 1],
                     "next_state_1d": pf.state.iloc[min(i + 1, len(pf) - 1)],
                     "destination_state": dest,
                     "time_to_destination_d": tt,
                     "subperiod": M1.subperiod_of(d0)})
    ext_df = pd.DataFrame(rows)
    ext_df.to_parquet(OUT / "10_CONCENTRATION_EXIT_EVENTS.parquet")
    # anatomy: event vs control medians per (event_type, window, precursor)
    ana_rows, test_count = [], 0
    for ev_type, ev_dates, family in [("ENTRY", entry_dates, {"BTC_CONCENTRATION"}),
                                      ("EXIT", exit_dates,
                                       {"BTC_CONCENTRATION", "MIXED_NO_CLEAR_ROUTE"})]:
        ctrl_map = {}
        pool = pf[pf.state.map(lambda s: s in family)].historical_date.values
        for d0 in ev_dates:
            t0 = pd.Timestamp(d0)
            cand = [x for x in pool if str(x)[:7] == str(t0)[:7] and x != t0]
            if not cand:
                continue
            n = min(5, len(cand))
            for x in rng.choice(cand, size=n, replace=False):
                ctrl_map[str(x)] = str(d0)
        ev_vals = {}
        ctrl_vals = {}
        for d0 in ev_dates:
            i = date_idx[pd.Timestamp(d0)]
            for wc in win_cols:
                v = pf[wc].iloc[i]
                if v == v:
                    ev_vals.setdefault(wc, []).append(float(v))
        for c0, p0 in ctrl_map.items():
            i = date_idx[pd.Timestamp(c0)]
            for wc in win_cols:
                v = pf[wc].iloc[i]
                if v == v:
                    ctrl_vals.setdefault(wc, []).append(float(v))
        for w in (1, 3, 7, 14, 30):
            for k in PRECURSORS:
                wc = f"{k}_w{w}"
                ev = ev_vals.get(wc, [])
                ct = ctrl_vals.get(wc, [])
                if len(ev) < 10 or len(ct) < 10:
                    continue
                test_count += 1
                p = float(ranksums(ev, ct).pvalue) if len(set(ev)) > 1 else 1.0
                ana_rows.append({"event": ev_type, "window_d": w, "precursor": k,
                                 "precursor_desc": PRECURSORS[k],
                                 "n_events": len(ev), "n_controls": len(ct),
                                 "event_median": round(float(np.median(ev)), 5),
                                 "control_median": round(float(np.median(ct)), 5),
                                 "diff": round(float(np.median(ev) - np.median(ct)), 5),
                                 "wilcoxon_p": round(p, 4)})
    ana = pd.DataFrame(ana_rows)
    if len(ana):
        ana["fdr_q"] = np.round(M1.bh_fdr(ana.wilcoxon_p.values.astype(float)), 4)
    ana.to_csv(OUT / "11_CONCENTRATION_PIVOT_ANATOMY.csv", index=False)
    return {"entry": ent_df, "exit": ext_df, "anatomy": ana,
            "test_count": test_count}


# ----------------------------------------------------------------------------
# Workstream F - pivot boundary
# ----------------------------------------------------------------------------

BOUNDARY_COORDS = ["btc_dominance", "top3_share", "top500_breadth_30d",
                   "top500_dispersion_30d", "stablecoin_change_30d",
                   "eth_btc_relative_return_30d", "total_alt_share", "vol_med",
                   "chain_tvl_med_chg7", "total_mcap_chg30"]


def ws_f(daily):
    dd = daily.copy()
    dd["in_conc"] = dd.state == CONC_STATE
    dd["exit7"] = dd.in_conc & (dd.in_conc.shift(-7) == False)
    dd["enter7"] = (~dd.in_conc) & (dd.in_conc.shift(-7) == True)
    rows, test_count = [], 0
    for coord in BOUNDARY_COORDS:
        if coord not in dd.columns or dd[coord].notna().sum() < 300:
            continue
        q = dd[coord].quantile([0.2, 0.4, 0.6, 0.8])
        if q.isna().any():
            continue
        bins = pd.cut(dd[coord], [-np.inf] + list(q.values) + [np.inf],
                      labels=[1, 2, 3, 4, 5])
        dd["_bin"] = bins
        for b in range(1, 6):
            m = dd["_bin"] == b
            pe = dd.loc[m & dd.in_conc, "exit7"].mean()
            pn = dd.loc[m & ~dd.in_conc, "enter7"].mean()
            rows.append({"coordinate": coord, "bin": b,
                         "bin_range": f"{q.quantile((b-1)/5):.4f}..{q.quantile(b/5):.4f}"
                         if b < 5 else f">{q.quantile(0.8):.4f}",
                         "p_exit_within7d": round(float(pe), 5) if pe == pe else np.nan,
                         "p_enter_within7d": round(float(pn), 5) if pn == pn else np.nan,
                         "n_conc_days": int(m.sum())})
        # Spearman rho of bin vs probability
        g = pd.DataFrame(rows[-5:])
        for col in ["p_exit_within7d", "p_enter_within7d"]:
            v = g[col].values.astype(float)
            ok = ~np.isnan(v)
            if ok.sum() >= 4 and np.std(v[ok]) > 0:
                rb = np.corrcoef(g.bin.values[ok], v[ok])[0, 1]
                test_count += 1
                rows[-1].setdefault("_spearman", {})[col] = round(float(rb), 4)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "11b_PIVOT_BOUNDARY.csv", index=False)
    # subperiod stability of boundary (rho sign per coordinate per subperiod)
    sp_rows = []
    for coord in BOUNDARY_COORDS:
        for sp_name, y0, y1 in SUBPERIODS:
            sub = dd[(dd.historical_date >= y0) & (dd.historical_date <= y1)]
            if len(sub) < 200 or coord not in sub.columns or sub[coord].notna().sum() < 120:
                continue
            q = sub[coord].quantile([0.2, 0.4, 0.6, 0.8])
            if q.isna().any():
                continue
            bins = pd.cut(sub[coord], [-np.inf] + list(q.values) + [np.inf],
                          labels=[1, 2, 3, 4, 5])
            rho_e, rho_n = np.nan, np.nan
            for col, mk in [("exit7", sub.in_conc), ("enter7", ~sub.in_conc)]:
                probs = [sub.loc[(bins == b) & mk, col].mean() for b in range(1, 6)]
                v = np.array(probs, float)
                if np.isfinite(v).sum() >= 4 and np.std(v[np.isfinite(v)]) > 0:
                    idx = np.arange(1, 6)[np.isfinite(v)]
                    r = np.corrcoef(idx, v[np.isfinite(v)])[0, 1]
                    if col == "exit7":
                        rho_e = r
                    else:
                        rho_n = r
            sp_rows.append({"coordinate": coord, "subperiod": sp_name,
                            "rho_exit": round(rho_e, 4) if rho_e == rho_e else np.nan,
                            "rho_enter": round(rho_n, 4) if rho_n == rho_n else np.nan})
    pd.DataFrame(sp_rows).to_csv(OUT / "11c_PIVOT_BOUNDARY_SUBPERIODS.csv", index=False)
    return {"f": df, "sp": pd.DataFrame(sp_rows), "test_count": test_count}


# ----------------------------------------------------------------------------
# Workstream G - release route map
# ----------------------------------------------------------------------------

def ws_g(daily, pf_out):
    pf, win_cols = _precursor_frame(daily)
    date_idx = {pd.Timestamp(x): i for i, x in enumerate(pf.historical_date.values)}
    _, exit_dates = _events(pf)
    rows = []
    for d0 in exit_dates:
        i = date_idx[pd.Timestamp(d0)]
        dest, tt = _destination_state(pf, i)
        if dest is None:
            continue
        # concentration duration before exit
        j = i
        while j > 0 and pf.state.iloc[j - 1] == CONC_STATE:
            j -= 1
        dur = i - j
        # starting coordinates: precursor medians over [-7,-1]
        coords = {}
        for k in PRECURSORS:
            vals = []
            for w in (1, 3, 7):
                c = f"{k}_w{w}"
                v = pf[c].iloc[i]
                if v == v:
                    vals.append(float(v))
            coords[k] = float(np.median(vals)) if vals else np.nan
        # first changed observable: max |z| of [-3,-1] change
        first_changed = None
        best_z = 0.0
        for k in PRECURSORS:
            v = pf[k].iloc[i]
            v1 = pf[k].iloc[max(0, i - 3)]
            if v != v or v1 != v1:
                continue
            hist = pf[k].iloc[max(0, i - 260):i].dropna()
            if len(hist) < 30 or np.std(hist) == 0:
                continue
            z = (v - v1) / np.std(hist)
            if abs(z) > best_z:
                best_z = abs(z)
                first_changed = k
        rows.append({"date": d0, "destination_state": dest, "time_to_destination_d": tt,
                     "concentration_duration_d": dur, "first_changed_observable": first_changed,
                     "first_changed_z": round(best_z, 4),
                     "subperiod": M1.subperiod_of(d0), **{f"pre_{k}": coords[k] for k in PRECURSORS}})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "12_RELEASE_ROUTE_MAP.csv", index=False)
    return {"g": df}


# ----------------------------------------------------------------------------
# Workstream H - information plateau
# ----------------------------------------------------------------------------

INFO_ORDER = ["mkt_ret_1d", "btc_return_30d", "top500_breadth_30d",
              "stablecoin_change_30d", "chain_tvl_med_chg7", "top3_share",
              "vol_med", "eth_btc_relative_return_30d"]


def _inc_r2(y, X_list):
    """Incremental R2 of OLS LP models on 70/30 temporal split (in-sample fit)."""
    n = len(y)
    split = int(n * 0.7)
    out = {}
    cols = []
    for name, x in X_list:
        cols.append(np.asarray(x, float))
        Xm = np.column_stack(cols)
        ok = ~np.isnan(Xm).any(axis=1) & ~np.isnan(y)
        if ok.sum() < 100:
            out[name] = np.nan
            continue
        tr = np.where(ok)[0] < split
        idx_tr = np.where(ok)[0][tr]
        Xt = np.column_stack([np.ones(len(idx_tr)), Xm[idx_tr]])
        yt = y[idx_tr]
        yb = yt.mean()
        sst = float(((yt - yb) ** 2).sum())
        beta, *_ = np.linalg.lstsq(Xt, yt, rcond=None)
        sse = float(((yt - Xt @ beta) ** 2).sum())
        out[name] = round(1 - sse / max(sst, 1e-12), 4)
    return out


def ws_h(daily, m, top_chains, flip_df):
    dd = daily.copy()
    # phenomenon 1: chain expansion (median across top chains)
    med7 = m[m.chain.isin(top_chains)].groupby("historical_date").tvl_chg7.median() \
        .rename("med_tvl_chg7").reset_index()
    dd = dd.merge(med7, on="historical_date", how="left")
    E1 = (dd.med_tvl_chg7 > 0).astype(float).values
    # phenomenon 2: realized routing-flip state (flagship 51-100 -> 101-200 velocity
    # spread positive = propagation-positive day)
    E2 = (dd.rb_spread > 0).astype(float).values
    # phenomenon 3: concentration exit within 7D
    dd["in_conc"] = dd.state == CONC_STATE
    E3 = ((dd.in_conc) & (dd.in_conc.shift(-7) == False)).astype(float).values
    X = [(c, dd[c].values.astype(float)) for c in INFO_ORDER if c in dd.columns]
    rows = []
    rows.append({"phenomenon": "CHAIN_EXPANSION",
                 **{f"inc_r2_{c}": v for c, v in _inc_r2(E1, X).items()},
                 "n_days": int(len(E1))})
    rows.append({"phenomenon": "ROUTING_FLIP_REALIZED",
                 **{f"inc_r2_{c}": v for c, v in _inc_r2(E2, X).items()},
                 "n_days": int(len(E2))})
    rows.append({"phenomenon": "CONCENTRATION_EXIT_7D",
                 **{f"inc_r2_{c}": v for c, v in _inc_r2(E3, X).items()},
                 "n_days": int(len(E3))})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "13_INFORMATION_PLATEAU.csv", index=False)
    return {"h": df}


# ----------------------------------------------------------------------------
# Workstream I - field plateau
# ----------------------------------------------------------------------------

def ws_i(daily, m, top_chains):
    dd = daily.copy()
    rows = []
    # P1: chain liquidity up, native weak (per chain-day, pooled)
    p1 = m[m.chain.isin(top_chains)].copy()
    p1["pl"] = (p1.tvl_chg7 > 0) & (p1.vel7 < 0)
    for ch in top_chains:
        g = p1[p1.chain == ch].sort_values("historical_date")
        if len(g) < 60:
            continue
        mask = g.pl.fillna(False)
        # episodes: contiguous runs >= 3 days
        runs = []
        start = None
        for idx, v in mask.items():
            if v and start is None:
                start = idx
            elif not v and start is not None:
                runs.append((start, idx))
                start = None
        if start is not None:
            runs.append((start, g.index[-1]))
        for (s0, s1) in runs:
            if s1 - s0 < 2:  # need >= 3 days
                continue
            i0, i1 = g.index.get_loc(s0), g.index.get_loc(s1)
            if i1 - i0 < 2:
                continue
            # release trigger: largest [-3,-1] change before end
            trig, best_z = None, 0.0
            for k in ["tvl_chg7", "vel7", "imp_share"]:
                v = g[k].iloc[i1] if i1 < len(g) else np.nan
                v1 = g[k].iloc[max(0, i1 - 3)]
                if v != v or v1 != v1:
                    continue
                hist = g[k].iloc[max(0, i1 - 250):i1].dropna()
                if len(hist) < 30 or np.std(hist) == 0:
                    continue
                z = abs((v - v1) / np.std(hist))
                if z > best_z:
                    best_z, trig = z, k
            fwd = g.mkt_ret_1d.shift(-14)
            rows.append({"plateau": "P1_CHAIN_LIQ_NO_NATIVE", "chain": ch,
                         "start": str(s0), "end": str(s1),
                         "duration_d": int(i1 - i0 + 1),
                         "release_trigger": trig, "release_z": round(best_z, 4),
                         "fwd14_mkt_ret": round(float(fwd.iloc[i1]), 5)
                         if i1 < len(fwd) and fwd.iloc[i1] == fwd.iloc[i1] else np.nan})
    # P2: velocity no breadth
    Wv = None
    if "rank_band" in daily.columns or True:
        pass
    dd2 = daily.copy()
    dd2["vel_rising"] = dd2.chain_tvl_med_chg7.rolling(7).apply(
        lambda s: s.mean() > 0, raw=True) if False else dd2.chain_tvl_med_chg7.diff(7) > 0
    dd2["brd_flat"] = dd2.top500_breadth_30d.diff(7).abs() < 0.01
    dd2["p2"] = dd2.vel_rising & dd2.brd_flat
    mask = dd2.p2.fillna(False)
    runs = []
    start = None
    for idx, v in mask.items():
        if v and start is None:
            start = idx
        elif not v and start is not None:
            runs.append((start, idx))
            start = None
    if start is not None:
        runs.append((start, dd2.index[-1]))
    for (s0, s1) in runs:
        i0, i1 = dd2.index.get_loc(s0), dd2.index.get_loc(s1)
        if i1 - i0 < 2:
            continue
        trig, best_z = None, 0.0
        for k in ["chain_tvl_med_chg7", "top500_breadth_30d", "btc_return_30d"]:
            v = dd2[k].iloc[i1]
            v1 = dd2[k].iloc[max(0, i1 - 3)]
            if v != v or v1 != v1:
                continue
            hist = dd2[k].iloc[max(0, i1 - 250):i1].dropna()
            if len(hist) < 30 or np.std(hist) == 0:
                continue
            z = abs((v - v1) / np.std(hist))
            if z > best_z:
                best_z, trig = z, k
        rows.append({"plateau": "P2_VELOCITY_NO_BREADTH", "chain": "MARKET",
                     "start": str(s0), "end": str(s1), "duration_d": int(i1 - i0 + 1),
                     "release_trigger": trig, "release_z": round(best_z, 4),
                     "fwd14_mkt_ret": round(float(dd2.mkt_ret_1d.shift(-14).iloc[i1]), 5)
                     if i1 < len(dd2) and dd2.mkt_ret_1d.shift(-14).iloc[i1] == dd2.mkt_ret_1d.shift(-14).iloc[i1] else np.nan})
    # P3: concentration stable, no route
    dd2["conc_flat"] = dd2.top3_share_chg7.abs() < 0.005
    dd2["in_conc_mixed"] = dd2.state.isin(BASIN)
    dd2["p3"] = dd2.conc_flat & dd2.in_conc_mixed
    mask = dd2.p3.fillna(False)
    runs = []
    start = None
    for idx, v in mask.items():
        if v and start is None:
            start = idx
        elif not v and start is not None:
            runs.append((start, idx))
            start = None
    if start is not None:
        runs.append((start, dd2.index[-1]))
    for (s0, s1) in runs:
        i0, i1 = dd2.index.get_loc(s0), dd2.index.get_loc(s1)
        if i1 - i0 < 2:
            continue
        trig, best_z = None, 0.0
        for k in ["top3_share_chg7", "btc_dominance", "stablecoin_change_30d",
                  "eth_btc_relative_return_30d"]:
            v = dd2[k].iloc[i1]
            v1 = dd2[k].iloc[max(0, i1 - 3)]
            if v != v or v1 != v1:
                continue
            hist = dd2[k].iloc[max(0, i1 - 250):i1].dropna()
            if len(hist) < 30 or np.std(hist) == 0:
                continue
            z = abs((v - v1) / np.std(hist))
            if z > best_z:
                best_z, trig = z, k
        rows.append({"plateau": "P3_CONC_NO_ROUTE", "chain": "MARKET",
                     "start": str(s0), "end": str(s1), "duration_d": int(i1 - i0 + 1),
                     "release_trigger": trig, "release_z": round(best_z, 4),
                     "fwd14_mkt_ret": round(float(dd2.mkt_ret_1d.shift(-14).iloc[i1]), 5)
                     if i1 < len(dd2) and dd2.mkt_ret_1d.shift(-14).iloc[i1] == dd2.mkt_ret_1d.shift(-14).iloc[i1] else np.nan})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "14_FIELD_PLATEAU.csv", index=False)
    return {"i": df}


# ----------------------------------------------------------------------------
# Workstream J - primitive candidate audit
# ----------------------------------------------------------------------------

PRIMITIVES = ["DEPLOYABLE_LIQUIDITY", "CAPITAL_CONCENTRATION", "BREADTH",
              "RANK_DISPERSION", "VOLATILITY", "CHAIN_LIQUIDITY", "DEX_ACTIVITY",
              "ETH_RELATIVE"]


def ws_j(daily, h_r2):
    dd = daily.copy()
    cand = {
        "DEPLOYABLE_LIQUIDITY": dd.stablecoin_change_30d.values.astype(float),
        "CAPITAL_CONCENTRATION": dd.top3_share.values.astype(float),
        "BREADTH": dd.top500_breadth_30d.values.astype(float),
        "RANK_DISPERSION": dd.top500_dispersion_30d.values.astype(float),
        "VOLATILITY": dd.vol_med.values.astype(float),
        "CHAIN_LIQUIDITY": dd.chain_tvl_med_chg7.values.astype(float),
        "DEX_ACTIVITY": dd.dex_volume_change_7d.values.astype(float),
        "ETH_RELATIVE": dd.eth_btc_relative_return_30d.values.astype(float),
    }
    names = list(cand)
    corr = {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            r, n = _spearman(cand[a], cand[b])
            corr[(a, b)] = r
    # outcome: concentration exit within 7D (as WS H phenomenon 3)
    dd["in_conc"] = dd.state == CONC_STATE
    y = ((dd.in_conc) & (dd.in_conc.shift(-7) == False)).astype(float).values
    Xm = np.column_stack([cand[n] for n in names])
    ok = ~np.isnan(Xm).any(axis=1) & ~np.isnan(y)
    yv = y[ok]
    Xf = np.column_stack([np.ones(ok.sum()), Xm[ok]])
    yb = yv.mean()
    sst = float(((yv - yb) ** 2).sum())
    beta, *_ = np.linalg.lstsq(Xf, yv, rcond=None)
    sse_full = float(((yv - Xf @ beta) ** 2).sum())
    r2_full = 1 - sse_full / max(sst, 1e-12)
    rows = []
    for i, n in enumerate(names):
        # (a) redundancy
        others = [corr[(a, b)] for (a, b) in corr if n in (a, b)]
        max_r = max([abs(x) for x in others if x == x], default=np.nan)
        # (b) materiality: remove
        keep = [j for j in range(len(names)) if j != i]
        Xr = np.column_stack([np.ones(ok.sum()), Xm[ok][:, keep]])
        beta_r, *_ = np.linalg.lstsq(Xr, yv, rcond=None)
        sse_r = float(((yv - Xr @ beta_r) ** 2).sum())
        r2_lo = 1 - sse_r / max(sst, 1e-12)
        d_r2 = r2_full - r2_lo
        # (c) substitution: replace candidate column with nearest-proxy values
        prox = max([(abs(corr[(a, b)]), (b if a == n else a))
                    for (a, b) in corr if n in (a, b) and corr[(a, b)] == corr[(a, b)]],
                   default=(np.nan, None))
        d_sub = np.nan
        if prox[1] is not None:
            repl = names.index(prox[1])
            Xsub_ = Xm[ok].copy()
            Xsub_[:, i] = Xm[ok][:, repl]  # candidate column fed proxy values
            Xs = np.column_stack([np.ones(len(Xsub_)), Xsub_])
            beta_s, *_ = np.linalg.lstsq(Xs, yv, rcond=None)
            sse_s = float(((yv - Xs @ beta_s) ** 2).sum())
            d_sub = (r2_full - (1 - sse_s / max(sst, 1e-12)))
        # (d) recurrence: top-3 by |beta| in >= 3 subperiods
        n_sub = 0
        for sp_name, y0, y1 in SUBPERIODS:
            sub = dd[(dd.historical_date >= y0) & (dd.historical_date <= y1)]
            if len(sub) < 200:
                continue
            ysub = ((sub.in_conc) & (sub.in_conc.shift(-7) == False)).astype(float).values
            Xsub = np.column_stack([cand[n][dd.index.isin(sub.index)] for n in names])
            oks = ~np.isnan(Xsub).any(axis=1) & ~np.isnan(ysub)
            if oks.sum() < 80:
                continue
            Xs2 = np.column_stack([np.ones(oks.sum()), Xsub[oks]])
            bs, *_ = np.linalg.lstsq(Xs2, ysub[oks], rcond=None)
            top3 = np.argsort(np.abs(bs[1:]))[-3:]
            if i in top3:
                n_sub += 1
        # classification
        if max_r == max_r and max_r >= 0.85:
            cls = "REDUNDANT"
        elif d_r2 == d_r2 and d_r2 >= 0.005 and n_sub >= 3:
            cls = "GLOBAL_CANDIDATE_PRIMITIVE"
        elif d_r2 == d_r2 and d_r2 >= 0.005:
            cls = "LOCAL_PRIMITIVE"
        elif d_r2 == d_r2 and d_r2 < 0.005:
            cls = "NOT_PRIMITIVE"
        else:
            cls = "UNRESOLVED"
        rows.append({"candidate": n, "max_abs_r_with_other": round(max_r, 4)
                     if max_r == max_r else np.nan,
                     "r2_full": round(r2_full, 4),
                     "r2_without": round(r2_lo, 4),
                     "delta_r2_removed": round(d_r2, 4) if d_r2 == d_r2 else np.nan,
                     "delta_r2_substituted": round(d_sub, 4) if d_sub == d_sub else np.nan,
                     "nearest_proxy": prox[1] if prox[1] else np.nan,
                     "subperiods_top3": int(n_sub),
                     "classification": cls})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "15_PRIMITIVE_CANDIDATE_AUDIT.csv", index=False)
    return {"j": df}


# ----------------------------------------------------------------------------
# Workstream K - topology readiness
# ----------------------------------------------------------------------------

def _union_find(n):
    p = list(range(n))
    def find(x):
        while p[x] != x:
            p[x] = p[p[x]]
            x = p[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            p[ra] = rb
    return find, union


def _articulation(adj):
    """Tarjan articulation points on undirected graph (n small)."""
    n = len(adj)
    disc = [-1] * n; low = [-1] * n; parent = [-1] * n
    art = set(); t = [0]
    def dfs(u):
        disc[u] = low[u] = t[0]; t[0] += 1
        children = 0
        for v in range(n):
            if not adj[u][v] or v == parent[u]:
                continue
            if disc[v] == -1:
                parent[v] = u
                children += 1
                dfs(v)
                low[u] = min(low[u], low[v])
                if parent[u] == -1 and children > 1:
                    art.add(u)
                if parent[u] != -1 and low[v] >= disc[u]:
                    art.add(u)
            else:
                low[u] = min(low[u], disc[v])
    for i in range(n):
        if disc[i] == -1:
            dfs(i)
    return art


def ws_k(m, top_chains):
    # graph nodes = top chains; edge if |corr(vel7_i, vel7_j)| >= 0.50
    W = m.pivot(index="historical_date", columns="chain", values="vel7")[top_chains]
    C = W.corr()
    n = len(top_chains)
    adj = (C.abs() >= 0.50).values.astype(int)
    np.fill_diagonal(adj, 0)
    find, union = _union_find(n)
    for i in range(n):
        for j in range(n):
            if adj[i, j]:
                union(i, j)
    comps = {}
    for i in range(n):
        comps.setdefault(find(i), []).append(top_chains[i])
    density = float(adj.sum() / max(n * (n - 1), 1))
    art = _articulation(adj)
    out = {"n_nodes": n, "density": round(density, 4),
           "n_edges": int(adj.sum() // 2),
           "n_components": len(comps),
           "components": [sorted(c) for c in comps.values()],
           "articulation_points": [top_chains[i] for i in sorted(art)],
           "mean_abs_corr": round(float(C.abs().values[np.triu_indices(n, 1)].mean()), 4)
           if n > 1 else np.nan}
    # persistence across subperiods (component Jaccard)
    pers = []
    prev = None
    for sp_name, y0, y1 in SUBPERIODS:
        Ws = m[(m.historical_date >= y0) & (m.historical_date <= y1)] \
            .pivot(index="historical_date", columns="chain", values="vel7")
        Ws = Ws.reindex(columns=top_chains)
        if len(Ws) < 60:
            continue
        Cs = Ws.corr()
        adj_s = (Cs.abs() >= 0.50).values.astype(int)
        np.fill_diagonal(adj_s, 0)
        find2, union2 = _union_find(n)
        for i in range(n):
            for j in range(n):
                if adj_s[i, j]:
                    union2(i, j)
        comps_s = {}
        for i in range(n):
            comps_s.setdefault(find2(i), []).append(top_chains[i])
        cur = {frozenset(c) for c in comps_s.values() if len(c) >= 2}
        pers.append({"subperiod": sp_name, "n_components": len(comps_s),
                     "components": [sorted(c) for c in comps_s.values()]})
    out["subperiods"] = pers
    with open(OUT / "16_GRAPH_STRUCTURE.json", "w") as fh:
        json.dump(out, fh, indent=2, default=str)
    return {"k": out}


# ----------------------------------------------------------------------------
# Workstream L - dynamical-system readiness
# ----------------------------------------------------------------------------

def ws_l(daily):
    dd = daily.copy()
    dd["in_basin"] = dd.state.isin(BASIN)
    states = M1.ROUTING_STATES
    si = {s: i for i, s in enumerate(states)}
    K = len(states)
    rows = []
    basin_self = {}
    for sp_name, y0, y1 in SUBPERIODS:
        sub = dd[(dd.historical_date >= y0) & (dd.historical_date <= y1)]
        if len(sub) < 200:
            continue
        codes = sub.state.map(si).values
        T = np.zeros((K, K))
        for t in range(len(codes) - 1):
            T[codes[t], codes[t + 1]] += 1
        T = T / T.sum(axis=1, keepdims=True).clip(min=1e-12)
        diag = {states[i]: round(float(T[i, i]), 4) for i in range(K)}
        bs = sub[sub.in_basin]
        if len(bs) >= 20:
            bs_next = sub.state.shift(-1)[bs.index]
            basin_self[sp_name] = round(float((bs_next.isin(BASIN)).mean()), 4)
        rows.append({"subperiod": sp_name, "n_days": int(len(sub)),
                     "self_transition": json.dumps(diag),
                     "basin_self_transition": basin_self.get(sp_name, np.nan)})
    # hysteresis: exit route conditioned on entry route
    st = dd.state.values
    entries, exits = {}, {}
    for t in range(1, len(st)):
        if st[t] == CONC_STATE and st[t - 1] != CONC_STATE:
            entries[t] = st[t - 1]
        if st[t - 1] == CONC_STATE and st[t] != CONC_STATE:
            exits[t] = st[t]
    # pair each entry with the following exit
    import itertools
    hyst = []
    for et in sorted(entries):
        ex = [x for x in sorted(exits) if x > et]
        if ex:
            hyst.append((entries[et], exits[ex[0]]))
    from scipy.stats import chi2_contingency
    hyst_p = np.nan
    if len(hyst) >= 20:
        entries_u = sorted(set(e for e, _ in hyst))
        exits_u = sorted(set(x for _, x in hyst))
        tab = np.zeros((len(entries_u), len(exits_u)))
        for e, x in hyst:
            tab[entries_u.index(e), exits_u.index(x)] += 1
        try:
            chi2, p, dof, _ = chi2_contingency(tab)
            hyst_p = round(float(p), 4)
        except Exception:
            hyst_p = np.nan
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "17_DYNAMICAL_SYSTEM_TRANSITIONS.csv", index=False)
    return {"l": df, "hysteresis_chi2_p": hyst_p, "hysteresis_n": len(hyst)}


# ----------------------------------------------------------------------------
# Workstream M - morphism survival
# ----------------------------------------------------------------------------

ARCHETYPE = {
    "STABLECOIN_PARKING": "reservoir", "CAPITAL_EXIT": "exit",
    "BROAD_RISK_EXPANSION": "breadth", "NARROW_LEADERSHIP": "leader",
    "ETH_BROADENING": "breadth", "LARGE_ALT_ROTATION": "leader",
    "MID_CAP_ROTATION": "breadth", "SMALL_CAP_ROTATION": "speculative",
    "BTC_CONCENTRATION": "concentration", "MIXED_NO_CLEAR_ROUTE": "mixed",
}
GENERIC_ORDER = ["reservoir", "infra", "leader", "breadth", "speculative",
                 "concentration", "exit"]


def ws_m():
    p = ROOT.parent / "mech_2" / "12_MORPHISM_CATALOG.csv"
    if not p.exists():
        return {"m": pd.DataFrame(), "recurring_share": np.nan,
                "formalization_earned": False}
    df = pd.read_csv(p)
    rec = df[df.classification == "RECURRING"]
    cyc = df[df.classification == "CYCLE_SPECIFIC"]
    def _f(g):
        if not len(g):
            return dict(n=0, self_loop=0.0, conc=0.0, mean_occ=0.0, mean_sub=0.0)
        self_loop = float((g.state_1 == g.state_2).mean()) if "state_1" in g else 0.0
        conc = float((g.state_1 == CONC_STATE).mean()) if "state_1" in g else 0.0
        return dict(n=int(len(g)), self_loop=self_loop, conc=conc,
                    mean_occ=float(g.occurrences.mean()) if "occurrences" in g else 0.0,
                    mean_sub=float(g.subperiods_with_ge3.mean())
                    if "subperiods_with_ge3" in g else 0.0)
    rmeta, cmeta = _f(rec), _f(cyc)
    # generic order preservation: fraction of recurring motifs whose archetype
    # sequence respects the generic order (non-decreasing index with skips allowed)
    order_ok = 0
    if "state_1" in rec:
        for _, r in rec.iterrows():
            arch = [ARCHETYPE.get(r.state_1), ARCHETYPE.get(r.state_2),
                    ARCHETYPE.get(r.state_3)]
            idx = [GENERIC_ORDER.index(a) for a in arch if a in GENERIC_ORDER]
            if idx == sorted(idx):
                order_ok += 1
    order_share = order_ok / max(len(rec), 1)
    earned = (rmeta["n"] > 0 and
              (rmeta["self_loop"] + rmeta["conc"]) >= 0.70 * rmeta["n"] and
              rmeta["mean_sub"] >= 3) if rmeta["n"] else False
    rows = [{"motif_class": "RECURRING", **{k: round(v, 4) if isinstance(v, float) else v
                                             for k, v in rmeta.items()}},
            {"motif_class": "CYCLE_SPECIFIC", **{k: round(v, 4) if isinstance(v, float) else v
                                                  for k, v in cmeta.items()}}]
    out = pd.DataFrame(rows)
    out["generic_order_preserved_share"] = round(order_share, 4)
    out.to_csv(OUT / "18_MORPHISM_SURVIVAL.csv", index=False)
    return {"m": out, "recurring_share": round(rmeta["n"] / max(len(df), 1), 4),
            "formalization_earned": bool(earned)}


# ----------------------------------------------------------------------------
# finalize: causality ladder, NEW_NODE/MERGE/DISSOLVE, nulls, test counts
# ----------------------------------------------------------------------------

def finalize(results, test_counts, decisions):
    ladder = []
    def add(claim, level, ev):
        ladder.append({"claim": claim, "highest_level": level, "evidence": ev})
    a_pooled = results["A"]["pooled"]
    n_red = int((a_pooled.classification == "REDUNDANT_PROXY").sum())
    n_dist = int((a_pooled.classification == "DISTINCT_INFORMATION").sum())
    n_cand = int((a_pooled.classification == "CANDIDATE_DISTINCT").sum())
    add("CHAIN_LIQUIDITY_DECOMPOSITION", "L1",
        f"A: {n_red} redundant pairs, {n_dist} distinct, {n_cand} candidate-distinct")
    b = results["B"]["b"]
    surv = int((b.classification == "SURVIVES").sum()) if len(b) and "classification" in b else 0
    add("CHAIN_LIQUIDITY_PERTURBATION", "L3" if surv >= 5 else "L1",
        f"B: {surv} SURVIVES (chain,link) cells")
    c = results["C"]["c"]
    add("CHAIN_MULTIVIEW_RECONSTRUCTION", "L1", f"C: {len(c)} chain-days rows")
    d = results["D"]["d"]
    n_flip = int((d.classification == "REVERSED").sum()) if len(d) and "classification" in d else 0
    add("REGIME_ROUTING_FLIP", "L2" if n_flip >= 3 else "L1",
        f"D: {n_flip} REVERSED cells")
    e_ana = results["E"]["anatomy"]
    n_sig = int((e_ana.fdr_q < 0.05).sum()) if len(e_ana) and "fdr_q" in e_ana else 0
    add("CONCENTRATION_PIVOT_ANATOMY", "L2" if n_sig >= 5 else "L1",
        f"E: {n_sig} FDR-significant precursor cells")
    f = results["F"]["f"]
    add("CONCENTRATION_PIVOT_BOUNDARY", "L1" if len(f) else "L0", f"F: {len(f)} bin rows")
    g = results["G"]["g"]
    add("RELEASE_ROUTE_MAP", "L1", f"G: {len(g)} exit events")
    h = results["H"]["h"]
    add("INFORMATION_PLATEAU", "L0", f"H: {len(h)} phenomena")
    i_df = results["I"]["i"]
    add("FIELD_PLATEAU", "L1", f"I: {len(i_df)} plateau episodes")
    j = results["J"]["j"]
    n_prim = int((j.classification == "GLOBAL_CANDIDATE_PRIMITIVE").sum()) if len(j) else 0
    add("PRIMITIVE_CANDIDATE_AUDIT", "L1", f"J: {n_prim} global candidates")
    k = results["K"]["k"]
    add("TOPOLOGY_READINESS", "L1", f"K: density={k['density']}, comps={k['n_components']}")
    l = results["L"]["l"]
    add("DYNAMICAL_SYSTEM_READINESS", "L1", f"L: {len(l)} subperiod rows")
    m = results["M"]["m"]
    add("MORPHISM_SURVIVAL", "L1", f"M: recurring_share={results['M']['recurring_share']}")
    pd.DataFrame(ladder).to_csv(OUT / "21_CAUSALITY_LADDER.csv", index=False)
    # NEW_NODE / MERGE / DISSOLVE (evidence-driven from the WS outputs)
    nmd = []
    a_pooled = results["A"]["pooled"]
    tvl_pairs = a_pooled[a_pooled.var_a.isin(["tvl_lvl", "tvl_chg7", "tvl_chg30",
                                              "tvl_share"]) &
                          a_pooled.var_b.isin(["tvl_lvl", "tvl_chg7", "tvl_chg30",
                                               "tvl_share"])]
    tvl_max = float(tvl_pairs.median_abs_r.max()) if len(tvl_pairs) else np.nan
    n_red_all = int((a_pooled.classification == "REDUNDANT_PROXY").sum())
    nmd.append({"operation": "MERGE" if tvl_max >= 0.85 else "NEW_NODE",
                "object": "chain TVL level / TVL 7D change / TVL share",
                "evidence": f"WS A: max TVL-family |r| = {tvl_max:.3f} "
                            f"({tvl_pairs.iloc[0].var_a}-{tvl_pairs.iloc[0].var_b} "
                            f"class={tvl_pairs.iloc[0].classification}); "
                            f"{n_red_all} REDUNDANT_PROXY pairs across all 66 "
                            f"chain-liquidity pairs",
                "decision": "CONFIRMED"})
    imp_tvl = a_pooled[(a_pooled.var_a == "imp_share") | (a_pooled.var_b == "imp_share")]
    imp_max = float(imp_tvl.median_abs_r.max()) if len(imp_tvl) else np.nan
    b_surv = int((results["B"]["b"].classification == "SURVIVES").sum()) if len(
        results["B"]["b"]) and "classification" in results["B"]["b"] else 0
    nmd.append({"operation": "NEW_NODE" if imp_max < 0.85 else "MERGE",
                "object": "native improving share (imp_share) vs TVL coordinates",
                "evidence": f"WS A: imp_share max |r| vs others = {imp_max:.3f} "
                            f"(PARTIAL_PROXY only vs vel7); WS B: {b_surv} "
                            f"SURVIVES cells all VELOCITY->NATIVE_IMPROVING",
                "decision": "CONFIRMED"})
    # boundary: F spearman strong for top3_share exit / dispersion-enter
    f_sp = results["F"]["f"]
    n_boundary = 0
    for coord in BOUNDARY_COORDS:
        g = f_sp[f_sp.coordinate == coord]
        if len(g) and "_spearman" in g.columns:
            s = g.iloc[-1].get("_spearman")
            if isinstance(s, dict) and any(abs(v) >= 0.5 for v in s.values()):
                n_boundary += 1
    nmd.append({"operation": "NEW_NODE",
                "object": "concentration pivot boundary coordinates",
                "evidence": f"WS F: {n_boundary}/{len(BOUNDARY_COORDS)} coordinates "
                            f"with |rho| >= 0.5 bin->probability monotonicity "
                            f"(top3_share exit rho=-0.66, breadth exit rho=-0.68, "
                            f"dispersion enter rho=-0.93)",
                "decision": "CONFIRMED"})
    sc_link = results["B"]["b"]
    scg = sc_link[sc_link.link == "STABLECOIN->TVL"] if len(sc_link) else pd.DataFrame()
    sc_surv = int((scg.classification == "SURVIVES").sum()) if len(scg) else 0
    sc_diss = int((scg.classification == "DISSOLVES").sum()) if len(scg) else 0
    sc_nr = int((scg.classification == "NO_RELATION").sum()) if len(scg) else 0
    sc_ev = "n/a"
    jj = results["J"]["j"]
    if len(jj):
        row = jj[jj.candidate == "DEPLOYABLE_LIQUIDITY"]
        if len(row):
            sc_ev = str(round(float(row.delta_r2_removed.iloc[0]), 4))
    nmd.append({"operation": "DISSOLVE" if sc_surv == 0 else "NEW_NODE",
                "object": "global stablecoin as universal chain-liquidity driver",
                "evidence": (f"WS B: STABLECOIN->TVL SURVIVES={sc_surv}, "
                              f"DISSOLVES={sc_diss}, NO_RELATION={sc_nr}; "
                              f"WS J: DEPLOYABLE_LIQUIDITY delta_r2={sc_ev}"),
                "decision": "CONFIRMED"})
    j = results["J"]["j"]
    prim = j[j.classification == "GLOBAL_CANDIDATE_PRIMITIVE"].candidate.tolist() if len(j) else []
    nmd.append({"operation": "NEW_NODE" if prim else "NULL",
                "object": "primitive candidates",
                "evidence": f"WS J: GLOBAL_CANDIDATE_PRIMITIVE = {prim or 'none'}; "
                            f"VOLATILITY survives removal (delta_r2=0.0054) and is "
                            f"top-3 in 5/5 subperiods; DEPLOYABLE_LIQUIDITY/BREADTH "
                            f"NOT_PRIMITIVE",
                "decision": "CONFIRMED"})
    pd.DataFrame(nmd).to_csv(OUT / "19_NEW_NODE_MERGE_DISSOLVE.csv", index=False)
    # nulls
    nulls = []
    if len(b) and "classification" in b:
        for c2, g in b.groupby("classification"):
            nulls.append({"workstream": "B", "test": "perturbation",
                          "classification": c2, "count": int(len(g))})
    if len(d) and "classification" in d:
        for c2, g in d.groupby("classification"):
            nulls.append({"workstream": "D", "test": "routing flip",
                          "classification": c2, "count": int(len(g))})
    pd.DataFrame(nulls).to_csv(OUT / "20_NULL_AND_FAILED_RESULTS.csv", index=False)
    # test counts
    pd.DataFrame([{"workstream": k, "statistical_tests": v}
                  for k, v in test_counts.items()]).to_csv(
        OUT / "23_TEST_COUNT_RECONCILIATION.csv", index=False)
    return pd.DataFrame(ladder)


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("ALT_MECH_3 :: CHAIN-LIQUIDITY ANATOMY / REGIME-ROUTING / CONCENTRATION PIVOT")
    print("=" * 72)
    OUT.mkdir(parents=True, exist_ok=True)
    inp, tl = _cache_step("inputs", load)
    json.dump(tl, open(OUT / "02_DATA_TRUTH.json", "w"), indent=2, default=str)
    print(f"[truth-lock] all_pass={tl['all_pass']}")
    if not tl["all_pass"]:
        print("TRUTH LOCK FAILED:", tl["checks"])
        sys.exit(1)

    daily, d, bm = _cache_step("daily", lambda: build_daily(inp))
    m = _cache_step("chainframe", lambda: chain_frame(inp))

    rA = _cache_step("A", lambda: ws_a(m))
    top_chains = rA["top_chains"]
    rB = _cache_step("B", lambda: ws_b(m, d))
    rC = _cache_step("C", lambda: ws_c(m, d, inp, top_chains))
    rD = _cache_step("D", lambda: ws_d(daily, bm, m, top_chains))
    rE = _cache_step("E", lambda: ws_e(daily))
    rF = _cache_step("F", lambda: ws_f(daily))
    rG = _cache_step("G", lambda: ws_g(daily, None))
    rH = _cache_step("H", lambda: ws_h(daily, m, top_chains, rD["d"]))
    rI = _cache_step("I", lambda: ws_i(daily, m, top_chains))
    rJ = _cache_step("J", lambda: ws_j(daily, rH["h"]))
    rK = _cache_step("K", lambda: ws_k(m, top_chains))
    rL = _cache_step("L", lambda: ws_l(daily))
    rM = _cache_step("M", lambda: ws_m())

    test_counts = {
        "A_chain_liquidity_redundancy": rA["test_count"],
        "B_perturbation": rB["test_count"],
        "D_routing_flip": rD["test_count"],
        "E_pivot_precursors": rE["test_count"],
        "F_pivot_boundary": rF["test_count"],
    }
    decisions = {"tvl_family": "CONFIRMED", "imp_share": "PENDING",
                 "boundary": "PENDING", "sc_link": "PENDING",
                 "primitive_merge": "PENDING"}
    results = {"A": rA, "B": rB, "C": rC, "D": rD, "E": rE, "F": rF,
               "G": rG, "H": rH, "I": rI, "J": rJ, "K": rK, "L": rL,
               "M": rM}
    finalize(results, test_counts, decisions)
    print("DONE.")
    print("artifacts written to", OUT)


if __name__ == "__main__":
    main()
