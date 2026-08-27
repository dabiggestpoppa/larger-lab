#!/usr/bin/env python3
"""LF — Integrity & Cross-Field Readiness Audit (Tasks 2-8).

Produces:
  RESULTS/23_ROBUST_EXPLANATORY_CLIFF.csv
  RESULTS/24_CLIFF_LOCATION_SCAN.csv
  RESULTS/25_LIQUIDITY_CONDITIONED_SENSITIVITY.csv
  RESULTS/26_MOMENTUM_SHAPE_REVALIDATION.csv
  RESULTS/27_CONDITIONAL_CHAIN_SECTOR_AUDIT.csv
  RESULTS/28_CAUSALITY_LADDER_CORRECTED.csv
  RESULTS/29_REVERSAL_INDEPENDENCE_AUDIT.csv
"""
from __future__ import annotations
import sys
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor

warnings.filterwarnings("ignore", category=FutureWarning)

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "RESULTS" / "lower_field_panel.parquet"
CR = Path(__file__).resolve().parent.parent.parent.parent / "alt_rotation"
CANON_UNIVERSE = CR / "data_1_1" / "ALT_DATA_1_1_PIT_UNIVERSE.parquet"
CANON_TERRAIN = CR / "data_1_1" / "ALT_DATA_1_1_MARKET_TERRAIN_V2.parquet"

BANDS = ["1-25", "26-100", "101-250", "251-500", "501-750", "751-1000",
         "1001-1500", "1501-2000"]
RANK_BANDS = [(1, 25), (26, 100), (101, 250), (251, 500),
              (501, 750), (751, 1000), (1001, 1500), (1501, 2000)]


def band_of(rank):
    for lo, hi in RANK_BANDS:
        if lo <= rank <= hi:
            return f"{lo}-{hi}"
    return "OUT"


def load_combined():
    """Load lower-field + canonical upper bands."""
    lf = pd.read_parquet(PANEL, columns=[
        "historical_date", "cmc_id", "rank", "rank_band", "ret_1d",
        "mkt_ret_1d", "btc_ret_1d", "eth_ret_1d", "is_stablecoin",
        "flag_stale_price", "flag_zero_volume", "listing_age_days",
        "volume_24h_usd", "platform_chain", "tags", "historical_date_key"])
    lf = lf.replace([np.inf, -np.inf], np.nan)

    can = pd.read_parquet(CANON_UNIVERSE, columns=[
        "historical_date", "cmc_id", "rank", "price_usd", "is_stablecoin",
        "volume_24h_usd", "platform_chain", "tags", "date_added_cmc"])
    can = can[can["rank"] <= 500].copy()
    can["cmc_id"] = can["cmc_id"].astype(int)
    can["rank_band"] = can["rank"].apply(band_of)
    CANON_BANDS = {"1-25", "26-100", "101-250", "251-500"}
    can = can[can["rank_band"].isin(CANON_BANDS)].copy()
    can = can.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    g = can.groupby("cmc_id", sort=False)
    can["ret_1d"] = can["price_usd"] / g["price_usd"].shift(1) - 1.0
    can["ret_1d"] = can["ret_1d"].replace([np.inf, -np.inf], np.nan)

    tot = pd.read_parquet(CANON_UNIVERSE,
                          columns=["historical_date", "total_mcap"]) \
        .drop_duplicates("historical_date").sort_values("historical_date")
    tot["historical_date_key"] = tot["historical_date"].dt.strftime("%Y-%m-%d")
    tot["mkt_ret_1d"] = tot["total_mcap"].pct_change()
    can["historical_date_key"] = can["historical_date"].dt.strftime("%Y-%m-%d")
    can = can.merge(tot[["historical_date_key", "mkt_ret_1d"]],
                    on="historical_date_key", how="left")
    terr = pd.read_parquet(CANON_TERRAIN,
                           columns=["historical_date", "btc_return_1d",
                                    "eth_return_1d"])
    terr["historical_date_key"] = terr["historical_date"].dt.strftime("%Y-%m-%d")
    can = can.merge(terr[["historical_date_key", "btc_return_1d",
                          "eth_return_1d"]].rename(columns={
        "btc_return_1d": "btc_ret_1d", "eth_return_1d": "eth_ret_1d"}),
        on="historical_date_key", how="left")
    can["flag_stale_price"] = False
    can["flag_zero_volume"] = (can["volume_24h_usd"].fillna(0) == 0)
    can["listing_age_days"] = np.nan

    cols = [c for c in lf.columns if c in can.columns]
    comb = pd.concat([lf[cols], can[cols]], ignore_index=True)
    comb = comb.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    return comb


def winsorize(s, lower=0.01, upper=0.99):
    lo, hi = s.quantile(lower), s.quantile(upper)
    return s.clip(lo, hi)


# =====================================================================
# TASK 2: EXPLANATORY CLIFF ROBUSTNESS
# =====================================================================
def task2_robust_cliff(comb):
    print("=== TASK 2: ROBUST EXPLANATORY CLIFF ===", flush=True)
    rows = []
    for band in BANDS:
        bd = comb[(comb["rank_band"] == band) & comb["ret_1d"].notna()
                  & comb["mkt_ret_1d"].notna()].copy()
        n_dates = bd["historical_date_key"].nunique()
        if n_dates < 120:
            continue
        y_raw = bd["ret_1d"].values
        g = bd["mkt_ret_1d"].values
        b = bd["btc_ret_1d"].values
        e = bd["eth_ret_1d"].values

        # A: raw pooled OLS
        def r2_ols(y, Xcols):
            X = np.column_stack([np.ones(len(y))] + list(Xcols))
            try:
                beta, *_ = np.linalg.lstsq(X, y, rcond=None)
                pred = X @ beta
                ss_res = float(np.sum((y - pred) ** 2))
                ss_tot = float(np.sum((y - y.mean()) ** 2))
                return 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
            except Exception:
                return np.nan

        r2_raw = r2_ols(y_raw, [g])
        r2_raw_btc_eth = r2_ols(y_raw, [g, b, e])

        # B: winsorized
        y_w = winsorize(bd["ret_1d"]).values
        r2_win = r2_ols(y_w, [g])

        # C: clipped ±10%
        y_c = np.clip(y_raw, -0.10, 0.10)
        r2_clip = r2_ols(y_c, [g])

        # D: Huber regression
        try:
            hub = HuberRegressor(max_iter=200)
            X_h = np.column_stack([g])
            hub.fit(X_h, y_raw)
            r2_hub = hub.score(X_h, y_raw)
        except Exception:
            r2_hub = np.nan

        # E: per-date cross-sectional R²
        daily_r2 = []
        for dt, sub in bd.groupby("historical_date_key"):
            if len(sub) < 10:
                continue
            yr = sub["ret_1d"].values
            gr = sub["mkt_ret_1d"].values
            if np.std(gr) == 0 or len(yr) < 10:
                continue
            try:
                slope = np.polyfit(gr, yr, 1)[0]
                corr = np.corrcoef(gr, yr)[0, 1]
                daily_r2.append(corr ** 2)
            except Exception:
                pass
        daily_r2 = np.array(daily_r2)
        r2_cs_median = float(np.median(daily_r2)) if len(daily_r2) else np.nan
        r2_cs_mean = float(np.mean(daily_r2)) if len(daily_r2) else np.nan

        # F: band-median daily return vs market
        band_med = bd.groupby("historical_date_key")["ret_1d"].median()
        mkt_daily = bd.groupby("historical_date_key")["mkt_ret_1d"].first()
        common_dates = band_med.index.intersection(mkt_daily.index)
        if len(common_dates) > 30:
            corr_band_mkt = float(np.corrcoef(
                band_med.loc[common_dates].values,
                mkt_daily.loc[common_dates].values)[0, 1])
        else:
            corr_band_mkt = np.nan

        # G: band index return (cap-weighted) vs global
        bd_mcap = bd.dropna(subset=["market_cap_usd"]) if "market_cap_usd" in bd.columns else bd
        # Use equal-weight since we may not have mcap
        idx_ret = bd.groupby("historical_date_key")["ret_1d"].mean()
        mkt_d = bd.groupby("historical_date_key")["mkt_ret_1d"].first()
        common = idx_ret.index.intersection(mkt_d.index)
        if len(common) > 30:
            corr_idx_mkt = float(np.corrcoef(
                idx_ret.loc[common].values,
                mkt_d.loc[common].values)[0, 1])
        else:
            corr_idx_mkt = np.nan

        # H: robust variance decomposition
        resid = y_raw - np.polyval(np.polyfit(g, y_raw, 1), g)
        med_abs_resid = float(np.median(np.abs(resid)))
        total_scale = float(np.median(np.abs(y_raw - np.median(y_raw))))
        idio_share = med_abs_resid / total_scale if total_scale > 0 else np.nan

        rows.append({
            "rank_band": band, "n_asset_days": len(bd), "n_dates": n_dates,
            "R2_raw_ols": r2_raw, "R2_raw_btc_eth": r2_raw_btc_eth,
            "R2_winsorized": r2_win, "R2_clipped_10pct": r2_clip,
            "R2_huber": r2_hub,
            "R2_cs_median": r2_cs_median, "R2_cs_mean": r2_cs_mean,
            "corr_band_median_vs_mkt": corr_band_mkt,
            "corr_equal_weight_idx_vs_mkt": corr_idx_mkt,
            "median_abs_residual": med_abs_resid,
            "total_scale_mad": total_scale,
            "idiosyncratic_share": idio_share,
        })
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "RESULTS" / "23_ROBUST_EXPLANATORY_CLIFF.csv", index=False)
    print(df[["rank_band", "R2_raw_ols", "R2_winsorized", "R2_clipped_10pct",
              "R2_huber", "R2_cs_median", "corr_band_median_vs_mkt",
              "idiosyncratic_share"]].to_string(), flush=True)
    return df


# =====================================================================
# TASK 3: CLIFF LOCATION SENSITIVITY
# =====================================================================
def task3_cliff_scan(comb):
    print("\n=== TASK 3: CLIFF LOCATION SCAN ===", flush=True)
    rows = []
    for win in [25, 50, 100]:
        max_rank = int(comb["rank"].max())
        for center in range(win // 2 + 1, max_rank - win // 2, win // 2):
            lo = center - win // 2
            hi = center + win // 2
            bd = comb[(comb["rank"] >= lo) & (comb["rank"] <= hi)
                      & comb["ret_1d"].notna() & comb["mkt_ret_1d"].notna()]
            n_dates = bd["historical_date_key"].nunique()
            if n_dates < 60 or len(bd) < 500:
                continue
            y = bd["ret_1d"].values
            g = bd["mkt_ret_1d"].values
            if np.std(g) == 0:
                continue
            try:
                X = np.column_stack([np.ones(len(y)), g])
                beta, *_ = np.linalg.lstsq(X, y, rcond=None)
                pred = X @ beta
                ss_res = float(np.sum((y - pred) ** 2))
                ss_tot = float(np.sum((y - y.mean()) ** 2))
                r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
            except Exception:
                r2 = np.nan
            # band-median correlation
            bm = bd.groupby("historical_date_key")["ret_1d"].median()
            md = bd.groupby("historical_date_key")["mkt_ret_1d"].first()
            ci = bm.index.intersection(md.index)
            corr_bm = float(np.corrcoef(bm.loc[ci].values,
                                        md.loc[ci].values)[0, 1]) if len(ci) > 10 else np.nan
            rows.append({
                "window": win, "rank_lo": lo, "rank_hi": hi,
                "center": center, "n_asset_days": len(bd),
                "n_dates": n_dates, "R2_pooled": r2,
                "corr_band_median": corr_bm,
            })
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "RESULTS" / "24_CLIFF_LOCATION_SCAN.csv", index=False)
    print(df.to_string(), flush=True)
    return df


# =====================================================================
# TASK 4: LIQUIDITY-CONDITIONED SENSITIVITY
# =====================================================================
def task4_liquidity(comb):
    print("\n=== TASK 4: LIQUIDITY-CONDITIONED SENSITIVITY ===", flush=True)
    # Only lower field for liquidity analysis
    lf = comb[comb["rank"] >= 501].copy()
    lf["vol_quint"] = lf.groupby("historical_date_key")["volume_24h_usd"].transform(
        lambda s: pd.qcut(s, 5, labels=[1, 2, 3, 4, 5], duplicates="drop"))
    lf["vol_decile"] = lf.groupby("historical_date_key")["volume_24h_usd"].transform(
        lambda s: pd.qcut(s.rank(method="first"), 10,
                           labels=range(1, 11), duplicates="drop"))
    mkt = lf["mkt_ret_1d"].dropna()
    q10, q90 = np.percentile(mkt, [10, 90])
    pos = lf[lf["mkt_ret_1d"] >= q90]
    neg = lf[lf["mkt_ret_1d"] <= q10]

    rows = []
    # By volume quintile
    for vq in sorted(lf["vol_quint"].dropna().unique()):
        sub_pos = pos[pos["vol_quint"] == vq]
        sub_neg = neg[neg["vol_quint"] == vq]
        rows.append({
            "filter": f"vol_quint_{vq}", "band": "ALL_LOWER",
            "n_pos": len(sub_pos), "n_neg": len(sub_neg),
            "median_ret_pos": float(sub_pos["ret_1d"].median()) if len(sub_pos) else np.nan,
            "median_ret_neg": float(sub_neg["ret_1d"].median()) if len(sub_neg) else np.nan,
        })
    # By rank band × volume quintile
    for band in ["501-750", "751-1000", "1001-1500", "1501-2000"]:
        for vq in [1, 3, 5]:
            sub_pos = pos[(pos["rank_band"] == band) & (pos["vol_quint"] == vq)]
            sub_neg = neg[(neg["rank_band"] == band) & (neg["vol_quint"] == vq)]
            rows.append({
                "filter": f"vol_quint_{vq}", "band": band,
                "n_pos": len(sub_pos), "n_neg": len(sub_neg),
                "median_ret_pos": float(sub_pos["ret_1d"].median()) if len(sub_pos) else np.nan,
                "median_ret_neg": float(sub_neg["ret_1d"].median()) if len(sub_neg) else np.nan,
            })
    # Zero-volume exclusion
    nz = lf[lf["volume_24h_usd"] > 0]
    nz_pos = nz[nz["mkt_ret_1d"] >= q90]
    nz_neg = nz[nz["mkt_ret_1d"] <= q10]
    rows.append({
        "filter": "zero_vol_excluded", "band": "ALL_LOWER",
        "n_pos": len(nz_pos), "n_neg": len(nz_neg),
        "median_ret_pos": float(nz_pos["ret_1d"].median()),
        "median_ret_neg": float(nz_neg["ret_1d"].median()),
    })
    # Stale exclusion
    ns = lf[~lf["flag_stale_price"]]
    ns_pos = ns[ns["mkt_ret_1d"] >= q90]
    ns_neg = ns[ns["mkt_ret_1d"] <= q10]
    rows.append({
        "filter": "stale_excluded", "band": "ALL_LOWER",
        "n_pos": len(ns_pos), "n_neg": len(ns_neg),
        "median_ret_pos": float(ns_pos["ret_1d"].median()),
        "median_ret_neg": float(ns_neg["ret_1d"].median()),
    })
    # Listing age control (>30d)
    la = lf[lf["listing_age_days"] > 30]
    la_pos = la[la["mkt_ret_1d"] >= q90]
    la_neg = la[la["mkt_ret_1d"] <= q10]
    rows.append({
        "filter": "listing_age_gt30d", "band": "ALL_LOWER",
        "n_pos": len(la_pos), "n_neg": len(la_neg),
        "median_ret_pos": float(la_pos["ret_1d"].median()),
        "median_ret_neg": float(la_neg["ret_1d"].median()),
    })
    # High-volume lower-field (vol quintile 4-5)
    hv = lf[lf["vol_quint"].isin([4, 5])]
    hv_pos = hv[hv["mkt_ret_1d"] >= q90]
    hv_neg = hv[hv["mkt_ret_1d"] <= q10]
    rows.append({
        "filter": "high_vol_q4_5", "band": "ALL_LOWER",
        "n_pos": len(hv_pos), "n_neg": len(hv_neg),
        "median_ret_pos": float(hv_pos["ret_1d"].median()),
        "median_ret_neg": float(hv_neg["ret_1d"].median()),
    })

    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "RESULTS" / "25_LIQUIDITY_CONDITIONED_SENSITIVITY.csv", index=False)
    print(df.to_string(), flush=True)
    return df


# =====================================================================
# TASK 5: MOMENTUM SHAPE REVALIDATION
# =====================================================================
def task5_momentum(comb):
    print("\n=== TASK 5: MOMENTUM SHAPE REVALIDATION ===", flush=True)
    # Needs ret_3d, ret_14d from the patched panel
    lf_full = pd.read_parquet(PANEL, columns=[
        "historical_date", "cmc_id", "rank", "rank_band", "ret_1d",
        "ret_3d", "ret_7d", "ret_14d", "ret_30d", "mkt_ret_1d",
        "volume_24h_usd", "flag_stale_price", "listing_age_days",
        "historical_date_key", "is_stablecoin"])
    lf_full = lf_full.replace([np.inf, -np.inf], np.nan)
    lf_full = lf_full[~lf_full["is_stablecoin"].astype(bool)]
    lf_full = lf_full.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)

    # Forward 7d return (correct)
    ok = lf_full["ret_1d"].notna() & (lf_full["ret_1d"] > -1.0)
    logf = np.where(ok, np.log1p(lf_full["ret_1d"].clip(lower=-0.9999)), np.nan)
    lf_full["_logf"] = logf
    lf_full["_cs"] = lf_full.groupby("cmc_id", sort=False)["_logf"].cumsum()
    cs_fwd = lf_full.groupby("cmc_id")["_cs"].transform(lambda s: s.shift(-7))
    lf_full["fwd_ret_7d"] = np.expm1(cs_fwd - lf_full["_cs"])
    lf_full = lf_full.drop(columns=["_logf", "_cs"])

    lf_full["short_hot"] = (lf_full["ret_3d"] > 0).astype(int)
    lf_full["med_hot"] = (lf_full["ret_14d"] > 0).astype(int)

    SHAPES = [("SHORT_HOT_MEDIUM_HOT", 1, 1), ("SHORT_HOT_MEDIUM_COLD", 1, 0),
              ("SHORT_COLD_MEDIUM_HOT", 0, 1), ("SHORT_COLD_MEDIUM_COLD", 0, 0)]

    rows = []
    for band in BANDS:
        bd = lf_full[lf_full["rank_band"] == band]
        for name, sh, mh in SHAPES:
            sub = bd[(bd["short_hot"] == sh) & (bd["med_hot"] == mh)]
            r7 = sub["fwd_ret_7d"].dropna()
            if len(r7) < 100:
                continue
            rows.append({
                "rank_band": band, "shape": name, "n": len(sub),
                "n_fwd": len(r7),
                "median_fwd_7d": float(r7.median()),
                "mean_fwd_7d": float(r7.mean()),
                "std_fwd_7d": float(r7.std()),
                "p_extreme_up": float((r7 > 0.15).mean()),
                "p_extreme_dn": float((r7 < -0.15).mean()),
                "p_extreme_any": float((r7.abs() > 0.15).mean()),
                "continuation_rate": float((r7 > 0).mean()),
                "reversal_rate": float((r7 < 0).mean()),
            })
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "RESULTS" / "26_MOMENTUM_SHAPE_REVALIDATION.csv", index=False)
    print(df.to_string(), flush=True)
    return df


# =====================================================================
# TASK 6: CONDITIONAL CHAIN/SECTOR AUDIT
# =====================================================================
def task6_conditional(comb):
    print("\n=== TASK 6: CONDITIONAL CHAIN/SECTOR AUDIT ===", flush=True)
    lf = comb[comb["rank"] >= 501].copy()
    lf["vol_terc"] = pd.qcut(lf["volume_24h_usd"].rank(method="first"), 3,
                              labels=["VOL_LOW", "VOL_MED", "VOL_HIGH"])
    lf["btc_regime"] = np.where(lf["btc_ret_1d"] > 0, "BTC_UP", "BTC_DOWN")
    # Residual after band+impulse
    med = lf.groupby(["rank_band"])[["mkt_ret_1d"]].transform("median")
    lf["band_ret_median"] = lf.groupby(["rank_band", "historical_date_key"])["ret_1d"].transform("median")
    lf["resid"] = lf["ret_1d"] - lf["band_ret_median"]

    rows = []
    # Chain × condition
    top_chains = lf["platform_chain"].replace("", np.nan).value_counts().head(8).index.tolist()
    for ch in top_chains:
        sub = lf[lf["platform_chain"] == ch]
        for btc in ["BTC_UP", "BTC_DOWN"]:
            for vol in ["VOL_LOW", "VOL_HIGH"]:
                sc = sub[(sub["btc_regime"] == btc) & (sub["vol_terc"] == vol)]
                if len(sc) < 100:
                    continue
                rows.append({
                    "lens": "chain", "object": ch,
                    "condition": f"{btc}_{vol}",
                    "n": len(sc),
                    "median_resid": float(sc["resid"].median()),
                    "iqr_resid": float(sc["resid"].quantile(0.75) - sc["resid"].quantile(0.25)),
                    "median_ret": float(sc["ret_1d"].median()),
                })
    # Sector × condition
    tag_cols = lf["tags"].fillna("").str.split(";")
    tag_counts = pd.Series([t for lst in tag_cols for t in lst if t]).value_counts()
    top_tags = tag_counts.head(8).index.tolist()
    for tg in top_tags:
        sub = lf[lf["tags"].fillna("").str.split(";").apply(lambda lst: tg in lst)]
        for btc in ["BTC_UP", "BTC_DOWN"]:
            for vol in ["VOL_LOW", "VOL_HIGH"]:
                sc = sub[(sub["btc_regime"] == btc) & (sub["vol_terc"] == vol)]
                if len(sc) < 100:
                    continue
                rows.append({
                    "lens": "sector", "object": tg,
                    "condition": f"{btc}_{vol}",
                    "n": len(sc),
                    "median_resid": float(sc["resid"].median()),
                    "iqr_resid": float(sc["resid"].quantile(0.75) - sc["resid"].quantile(0.25)),
                    "median_ret": float(sc["ret_1d"].median()),
                })
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "RESULTS" / "27_CONDITIONAL_CHAIN_SECTOR_AUDIT.csv", index=False)
    # Simple multiple-testing: |resid| < 0.5% threshold (same as original)
    if len(df):
        df["dissolved"] = df["median_resid"].abs() < 0.005
    print(df.to_string(), flush=True)
    return df


# =====================================================================
# TASK 7: CAUSALITY LADDER
# =====================================================================
def task7_causality():
    print("\n=== TASK 7: CAUSALITY LADDER CORRECTION ===", flush=True)
    rows = [
        {"claim": "EXPLANATORY_CLIFF: BTC+ETH explain 13.5% at ranks 26-100",
         "measure": "Pooled OLS R²", "ladder_level": "L0_DESCRIPTIVE_CO_MOVEMENT",
         "note": "Same-day returns; X and Y are contemporaneous. Not L2."},
        {"claim": "EXPLANATORY_CLIFF: R² drops to <0.1% at ranks 101-2000",
         "measure": "Pooled OLS R²", "ladder_level": "L0_DESCRIPTIVE_CO_MOVEMENT",
         "note": "Same-day returns; contemporaneous co-movement only."},
        {"claim": "BAND-MEDIAN RETURN correlates with market",
         "measure": "Cross-day correlation of band-median daily return vs mkt_ret_1d",
         "ladder_level": "L1_TEMPORAL_ORDERING",
         "note": "Band-median at t is compared to market at t. Contemporaneous. However, if market leads (open→close), partial L1."},
        {"claim": "POSITIVE_ELASTICITY declines with rank",
         "measure": "Median return on top-decile market days",
         "ladder_level": "L0_DESCRIPTIVE_CO_MOVEMENT",
         "note": "Conditioning on same-day market move. Descriptive."},
        {"claim": "MOMENTUM_SHAPE predicts extreme forward moves",
         "measure": "P(|fwd7d|>15%) conditional on 3D×14D sign state",
         "ladder_level": "L1_TEMPORAL_ORDERING",
         "note": "Momentum state at t, forward return at t+1..t+7. Temporal ordering present. Not causal."},
        {"claim": "REVERSAL after extreme events",
         "measure": "Forward return sign opposite to event sign",
         "ladder_level": "L1_TEMPORAL_ORDERING",
         "note": "Event at t, forward return at t+1..t+30. Temporal ordering present."},
        {"claim": "CHAIN_SECTOR_NULL",
         "measure": "Median residual after band conditioning",
         "ladder_level": "L0_DESCRIPTIVE_CO_MOVEMENT",
         "note": "Descriptive cross-sectional analysis."},
        {"claim": "TAIL_ACTIVATION_GRADIENT",
         "measure": "Extreme forward move probability by rank",
         "ladder_level": "L1_TEMPORAL_ORDERING",
         "note": "Momentum state at t, extreme forward return at t+1..t+7. Temporal ordering."},
    ]
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "RESULTS" / "28_CAUSALITY_LADDER_CORRECTED.csv", index=False)
    print(df.to_string(), flush=True)
    return df


# =====================================================================
# TASK 8: REVERSAL INDEPENDENCE AUDIT
# =====================================================================
def task8_reversal(comb):
    print("\n=== TASK 8: REVERSAL INDEPENDENCE AUDIT ===", flush=True)
    lf = pd.read_parquet(PANEL, columns=[
        "historical_date", "cmc_id", "rank", "rank_band", "ret_1d",
        "mkt_ret_1d", "is_stablecoin", "historical_date_key"])
    lf = lf.replace([np.inf, -np.inf], np.nan)
    lf = lf[~lf["is_stablecoin"].astype(bool)]
    lf = lf.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)

    # Forward returns
    ok = lf["ret_1d"].notna() & (lf["ret_1d"] > -1.0)
    logf = np.where(ok, np.log1p(lf["ret_1d"].clip(lower=-0.9999)), np.nan)
    lf["_logf"] = logf
    lf["_cs"] = lf.groupby("cmc_id", sort=False)["_logf"].cumsum()
    for w in [1, 3, 7, 14, 30]:
        cs_sh = lf.groupby("cmc_id")["_cs"].transform(lambda s: s.shift(-w))
        lf[f"fwd_ret_{w}d"] = np.expm1(cs_sh - lf["_cs"])
    lf = lf.drop(columns=["_logf", "_cs"])

    # Extreme events: trailing-252d P2.5/P97.5
    obs_count = lf.groupby("cmc_id")["ret_1d"].transform("count")
    lf = lf[obs_count >= 120].copy()
    grp = lf.groupby("cmc_id")["ret_1d"]
    hi_t = grp.transform(lambda s: s.shift(1).rolling(252, min_periods=120).quantile(0.975))
    lo_t = grp.transform(lambda s: s.shift(1).rolling(252, min_periods=120).quantile(0.025))
    ev = lf[(lf["ret_1d"] >= hi_t) | (lf["ret_1d"] <= lo_t)].copy()
    ev["event_sign"] = np.where(ev["ret_1d"] > 0, "UP", "DOWN")

    rows = []
    for band in BANDS:
        bd = ev[ev["rank_band"] == band]
        for sign in ["UP", "DOWN"]:
            sub = bd[bd["event_sign"] == sign]
            # Deduplicate: if same asset has events within 7d, keep only first
            sub = sub.sort_values(["cmc_id", "historical_date"])
            sub["prev_event_date"] = sub.groupby("cmc_id")["historical_date"].shift(1)
            sub["days_since_prev"] = (sub["historical_date"] - sub["prev_event_date"]).dt.days
            deduped = sub[sub["days_since_prev"] > 7 | sub["days_since_prev"].isna()]
            # Effective independent count
            n_raw = len(sub)
            n_deduped = len(deduped)
            for w in [1, 3, 7, 14, 30]:
                col = f"fwd_ret_{w}d"
                r = deduped[col].dropna()
                if len(r) < 10:
                    continue
                rows.append({
                    "rank_band": band, "event_sign": sign,
                    "horizon": w, "n_raw": n_raw, "n_deduped": n_deduped,
                    "median_fwd": float(r.median()),
                    "reversal_rate": float(
                        (np.sign(r) != np.sign(deduped.loc[r.index, "ret_1d"])).mean()),
                    "p_up": float((r > 0).mean()),
                    "p_down": float((r < 0).mean()),
                })
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "RESULTS" / "29_REVERSAL_INDEPENDENCE_AUDIT.csv", index=False)
    print(df.to_string(), flush=True)
    return df


# =====================================================================
def main() -> int:
    print("Loading combined panel...", flush=True)
    comb = load_combined()
    print(f"Combined: {len(comb)} rows, {comb['rank_band'].nunique()} bands", flush=True)

    task2_robust_cliff(comb)
    task3_cliff_scan(comb)
    task4_liquidity(comb)
    task5_momentum(comb)
    task6_conditional(comb)
    task7_causality()
    task8_reversal(comb)

    print("\n=== ALL AUDIT TASKS COMPLETE ===", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
