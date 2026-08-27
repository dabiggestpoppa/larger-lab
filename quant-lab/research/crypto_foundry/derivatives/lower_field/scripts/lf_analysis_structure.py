#!/usr/bin/env python3
"""LF — Phase E (explanatory hierarchy), F (momentum horizon redundancy),
G (momentum shape), H (persistence/decay).

Thresholds per 02_PREREGISTRATION.md (frozen). Outputs:
  RESULTS/09_EXPLANATORY_HIERARCHY.csv
  RESULTS/10_MOMENTUM_HORIZON_REDUNDANCY.csv
  RESULTS/11_MOMENTUM_STATE_GEOMETRY.csv
  RESULTS/12_PERSISTENCE_DECAY.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "RESULTS" / "lower_field_panel.parquet"

CR = Path(__file__).resolve().parent.parent.parent.parent / "alt_rotation"
CANON_UNIVERSE = CR / "data_1_1" / "ALT_DATA_1_1_PIT_UNIVERSE.parquet"
CANON_TERRAIN = CR / "data_1_1" / "ALT_DATA_1_1_MARKET_TERRAIN_V2.parquet"

BANDS = ["1-25", "26-100", "101-250", "251-500", "501-750", "751-1000",
         "1001-1500", "1501-2000"]
HORIZONS = [1, 3, 7, 14, 30, 60]
MIN_CELL_DAYS = 120

CANON_BANDS = {"1-25", "26-100", "101-250", "251-500"}
RANK_BANDS = [(1, 25), (26, 100), (101, 250), (251, 500),
              (501, 750), (751, 1000), (1001, 1500), (1501, 2000)]


def band_of(rank: int) -> str:
    for lo, hi in RANK_BANDS:
        if lo <= rank <= hi:
            return f"{lo}-{hi}"
    return "OUT"


def load_canonical_upper() -> pd.DataFrame:
    """Load canonical Top-500 panel, compute derived features for bands 1-500."""
    can = pd.read_parquet(CANON_UNIVERSE)
    can = can[can["rank"] <= 500].copy()
    can["cmc_id"] = can["cmc_id"].astype(int)
    can["rank_band"] = can["rank"].apply(band_of)
    can = can[can["rank_band"].isin(CANON_BANDS)].copy()

    # global context: mkt_ret_1d from total_mcap
    tot = pd.read_parquet(CANON_UNIVERSE,
                          columns=["historical_date", "total_mcap"]) \
        .drop_duplicates("historical_date").sort_values("historical_date")
    tot["historical_date_key"] = tot["historical_date"].dt.strftime("%Y-%m-%d")
    tot["mkt_ret_1d"] = tot["total_mcap"].pct_change()
    tot["mkt_ret_1d"] = tot["mkt_ret_1d"].where(
        tot["mkt_ret_1d"].notna() & np.isfinite(tot["mkt_ret_1d"]))

    # terrain: btc/eth returns
    terr = pd.read_parquet(CANON_TERRAIN)
    terr["historical_date_key"] = terr["historical_date"].dt.strftime("%Y-%m-%d")
    terr_cols = ["historical_date_key", "btc_return_1d", "eth_return_1d"]
    terr = terr[terr_cols].rename(columns={
        "btc_return_1d": "btc_ret_1d", "eth_return_1d": "eth_ret_1d"})

    can["historical_date_key"] = can["historical_date"].dt.strftime("%Y-%m-%d")
    can = can.merge(tot[["historical_date_key", "mkt_ret_1d"]],
                    on="historical_date_key", how="left")
    can = can.merge(terr, on="historical_date_key", how="left")

    # derived features
    can = can.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    g = can.groupby("cmc_id", sort=False)
    can["price_prev"] = g["price_usd"].shift(1)
    can["ret_1d"] = can["price_usd"] / can["price_prev"] - 1.0
    can["ret_1d"] = can["ret_1d"].replace([np.inf, -np.inf], np.nan)

    # multi-day returns via log-cumsum
    ok = can["ret_1d"].notna() & (can["ret_1d"] > -1.0)
    logf = np.where(ok, np.log1p(can["ret_1d"].clip(lower=-0.9999)), np.nan)
    can["_logf"] = logf
    cs = can.groupby("cmc_id", sort=False)["_logf"].cumsum()
    for w in HORIZONS:
        if w == 1:
            continue
        cs_shift = can.groupby("cmc_id", sort=False)["_logf"].transform(
            lambda s: s.shift(w))
        can[f"ret_{w}d"] = np.expm1(cs - cs_shift)
    can = can.drop(columns=["_logf"])

    # rank velocity
    for w in HORIZONS:
        can[f"rank_vel_{w}d"] = can["rank"].transform(
            lambda s: s.shift(w) - s)

    # volume acceleration
    can["vol_prev7_med"] = can.groupby("cmc_id", sort=False)[
        "volume_24h_usd"].transform(
        lambda s: s.shift(1).rolling(7, min_periods=3).median())
    can["vol_accel"] = can["volume_24h_usd"] / can["vol_prev7_med"].replace(0, np.nan)

    # listing age
    can["date_added_cmc"] = pd.to_datetime(can["date_added_cmc"],
                                           errors="coerce", utc=True) \
        .dt.tz_localize(None)
    can["listing_age_days"] = (can["historical_date"] - can["date_added_cmc"]).dt.days

    # is_stablecoin
    can["is_stablecoin"] = can.get("is_stablecoin", False)

    return can


def main() -> int:
    lf = pd.read_parquet(PANEL)
    lf = lf.replace([np.inf, -np.inf], np.nan)
    lf = lf[~lf["is_stablecoin"].astype(bool)].copy()
    lf["historical_date_key"] = lf["historical_date"].dt.strftime("%Y-%m-%d")

    # load canonical upper bands
    can = load_canonical_upper()
    can = can[~can["is_stablecoin"].astype(bool)].copy()

    # combine panels
    cols_needed = ["historical_date", "historical_date_key", "cmc_id", "rank",
                   "rank_band", "ret_1d", "ret_3d", "ret_7d", "ret_14d",
                   "ret_30d", "ret_60d", "mkt_ret_1d", "btc_ret_1d",
                   "eth_ret_1d", "platform_chain", "tags", "volume_24h_usd",
                   "rank_vel_7d", "vol_accel", "listing_age_days",
                   "is_stablecoin"]
    common = [c for c in cols_needed if c in lf.columns and c in can.columns]
    comb = pd.concat([lf[common], can[common]], ignore_index=True)
    comb = comb.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)

    print(f"combined panel: {len(comb)} rows, bands: {comb['rank_band'].nunique()}",
          flush=True)
    print(comb["rank_band"].value_counts().sort_index(), flush=True)

    # =====================================================================
    # PHASE E — explanatory hierarchy by rank band (sequential R2)
    # =====================================================================
    e_rows = []
    # one-hot chain / sector: top-N by row coverage (from combined)
    top_chains = comb["platform_chain"].replace("", np.nan).value_counts() \
        .head(8).index.tolist()
    tag_cols = comb["tags"].fillna("").str.split(";")
    tag_counts = pd.Series([t for lst in tag_cols for t in lst
                            if t]).value_counts()
    top_tags = tag_counts.head(8).index.tolist()
    for band in BANDS:
        bd = comb[(comb["rank_band"] == band) & comb["ret_1d"].notna()
                  & comb["mkt_ret_1d"].notna() & comb["btc_ret_1d"].notna()
                  & comb["eth_ret_1d"].notna()]
        if bd["historical_date_key"].nunique() < MIN_CELL_DAYS:
            e_rows.append({"rank_band": band, "tested": False,
                           "n_asset_days": int(len(bd)),
                           "R2_global": np.nan, "R2_global_btc": np.nan,
                           "R2_global_btc_eth": np.nan,
                           "R2_all_obs": np.nan, "R2_global_add": np.nan,
                           "R2_btc_add": np.nan, "R2_eth_add": np.nan,
                           "R2_chain_add": np.nan, "R2_sector_add": np.nan,
                           "residual_share": np.nan})
            continue
        y = bd["ret_1d"].values
        def r2(xcols):
            X = np.column_stack([np.ones(len(y))] + list(xcols))
            try:
                beta, *_ = np.linalg.lstsq(X, y, rcond=None)
                pred = X @ beta
                ss_res = float(np.sum((y - pred) ** 2))
                ss_tot = float(np.sum((y - y.mean()) ** 2))
                return 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
            except Exception:  # noqa: BLE001
                return np.nan
        g_vals = bd["mkt_ret_1d"].values
        b_vals = bd["btc_ret_1d"].values
        e_vals = bd["eth_ret_1d"].values
        chain_dummies = []
        for c in top_chains:
            chain_dummies.append((bd["platform_chain"] == c).astype(float).values)
        tag_dummies = []
        for t in top_tags:
            tag_dummies.append(
                bd["tags"].fillna("").str.split(";")
                .apply(lambda lst: t in lst).astype(float).values)
        r_global = r2([g_vals])
        r_gb = r2([g_vals, b_vals])
        r_gbe = r2([g_vals, b_vals, e_vals])
        r_all = r2([g_vals, b_vals, e_vals] + chain_dummies + tag_dummies)
        e_rows.append({
            "rank_band": band, "tested": True,
            "n_asset_days": int(len(bd)),
            "R2_global": r_global, "R2_global_btc": r_gb,
            "R2_global_btc_eth": r_gbe, "R2_all_obs": r_all,
            "R2_global_add": r_global,
            "R2_btc_add": r_gb - r_global,
            "R2_eth_add": r_gbe - r_gb,
            "R2_chain_add": r2([g_vals, b_vals, e_vals] + chain_dummies) - r_gbe,
            "R2_sector_add": r2([g_vals, b_vals, e_vals] + chain_dummies + tag_dummies)
            - r2([g_vals, b_vals, e_vals] + chain_dummies),
            "residual_share": 1 - r_all,
        })
    hier = pd.DataFrame(e_rows)
    hier.to_csv(ROOT / "RESULTS" / "09_EXPLANATORY_HIERARCHY.csv", index=False)
    print("phase E done:", hier.shape, flush=True)

    # =====================================================================
    # PHASE F — momentum horizon redundancy by band
    # =====================================================================
    f_rows = []
    for band in BANDS:
        bd = comb[comb["rank_band"] == band].copy()
        bd = bd.sort_values(["cmc_id", "historical_date"])
        g_ = bd.groupby("cmc_id", sort=False)
        bd["fwd_ret_1d"] = g_["ret_1d"].shift(-1)
        # forward 7d return: log-cumsum approach
        ok = bd["ret_1d"].notna() & (bd["ret_1d"] > -1.0)
        logf = np.where(ok, np.log1p(bd["ret_1d"].clip(lower=-0.9999)), np.nan)
        bd["_logf"] = logf
        cs = bd.groupby("cmc_id", sort=False)["_logf"].cumsum()
        cs_shift7 = bd.groupby("cmc_id", sort=False)["_logf"].transform(
            lambda s: s.shift(-7))
        cs_f7 = bd.groupby("cmc_id", sort=False)["_logf"].transform(
            lambda s: s.shift(-7))
        bd["fwd_ret_7d"] = np.expm1(cs_f7 - bd["_logf"])
        bd = bd.drop(columns=["_logf"])

        bd["fwd_rank_vel_7d"] = bd["rank"].transform(
            lambda s: s - s.shift(-7))
        bd["fwd_vol_1d"] = bd["volume_24h_usd"].transform(
            lambda s: s.shift(-1))
        # horizon correlation matrix (pairwise complete obs)
        hcols = [f"ret_{w}d" for w in HORIZONS]
        # ensure columns exist
        for hc in hcols:
            if hc not in bd.columns:
                bd[hc] = np.nan
        corr = bd[hcols].corr()
        # incremental predictive R2 for fwd_ret_1d
        def inc_r2(target, order):
            used = []
            out = {}
            for h in order:
                col = f"ret_{h}d"
                if col not in bd.columns:
                    continue
                sub = bd[bd[col].notna() & bd[target].notna() & bd["mkt_ret_1d"].notna()]
                if len(sub) < 100:
                    continue
                y = sub[target].values
                Xs = [np.ones(len(y))] + [sub[c].values
                                          for c in [f"ret_{u}d" for u in used]]
                Xs.append(sub[col].values)
                X = np.column_stack(Xs)
                try:
                    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
                except np.linalg.LinAlgError:
                    used.append(h)
                    continue
                pred = X @ beta
                ss_res = float(np.sum((y - pred) ** 2))
                ss_tot = float(np.sum((y - y.mean()) ** 2))
                r2v = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
                used.append(h)
                out[h] = r2v
            prev = 0.0
            incs = {}
            for h in order:
                if h in out:
                    incs[h] = out[h] - prev
                    prev = out[h]
            return incs
        inc_fwd = inc_r2("fwd_ret_1d", HORIZONS)
        inc_rev = inc_r2("fwd_ret_1d", list(reversed(HORIZONS)))
        for h in HORIZONS:
            col = f"ret_{h}d"
            corr_val = np.nan
            if col in corr.columns and "ret_1d" in corr.columns:
                corr_val = corr.loc["ret_1d", col]
            f_rows.append({
                "rank_band": band, "horizon": h,
                "corr_1d": corr_val,
                "corr_3d": corr.loc["ret_3d", col] if "ret_3d" in corr.index and col in corr.columns else np.nan,
                "corr_7d": corr.loc["ret_7d", col] if "ret_7d" in corr.index and col in corr.columns else np.nan,
                "corr_14d": corr.loc["ret_14d", col] if "ret_14d" in corr.index and col in corr.columns else np.nan,
                "corr_30d": corr.loc["ret_30d", col] if "ret_30d" in corr.index and col in corr.columns else np.nan,
                "corr_60d": corr.loc["ret_60d", col] if "ret_60d" in corr.index and col in corr.columns else np.nan,
                "inc_r2_fwd_1d_shortest_first": inc_fwd.get(h, np.nan),
                "inc_r2_fwd_1d_longest_first": inc_rev.get(h, np.nan),
            })
    horiz = pd.DataFrame(f_rows)
    horiz.to_csv(ROOT / "RESULTS" / "10_MOMENTUM_HORIZON_REDUNDANCY.csv",
                 index=False)
    print("phase F done:", horiz.shape, flush=True)

    # =====================================================================
    # PHASE G — momentum shape (short 3D x medium 14D sign states)
    # =====================================================================
    g_rows = []
    SHAPES = [("SHORT_HOT_MEDIUM_HOT", 1, 1), ("SHORT_HOT_MEDIUM_COLD", 1, 0),
              ("SHORT_COLD_MEDIUM_HOT", 0, 1), ("SHORT_COLD_MEDIUM_COLD", 0, 0)]
    for band in BANDS:
        bd = comb[comb["rank_band"] == band].copy()
        bd = bd.sort_values(["cmc_id", "historical_date"])
        # fwd 7d return
        ok = bd["ret_1d"].notna() & (bd["ret_1d"] > -1.0)
        logf = np.where(ok, np.log1p(bd["ret_1d"].clip(lower=-0.9999)), np.nan)
        bd["_logf"] = logf
        cs = bd.groupby("cmc_id", sort=False)["_logf"].cumsum()
        cs_f7 = bd.groupby("cmc_id", sort=False)["_logf"].transform(
            lambda s: s.shift(-7))
        bd["fwd_ret_7d"] = np.expm1(cs_f7 - bd["_logf"])
        bd = bd.drop(columns=["_logf"])
        bd["fwd_rank_vel_7d"] = bd["rank"].transform(
            lambda s: s - s.shift(-7))
        bd["fwd_vol_1d"] = bd["volume_24h_usd"].transform(
            lambda s: s.shift(-1))
        bd["short_hot"] = (bd["ret_3d"] > 0).astype(int) if "ret_3d" in bd.columns else 0
        bd["med_hot"] = (bd["ret_14d"] > 0).astype(int) if "ret_14d" in bd.columns else 0
        for name, sh, mh in SHAPES:
            sub = bd[(bd["short_hot"] == sh) & (bd["med_hot"] == mh)]
            r7 = sub["fwd_ret_7d"].dropna()
            if sub["historical_date_key"].nunique() < MIN_CELL_DAYS \
                    or len(r7) < 100:
                g_rows.append({"rank_band": band, "shape": name,
                               "tested": False, "n": int(len(sub)),
                               "continuation_rate": np.nan,
                               "median_fwd_7d": np.nan,
                               "median_fwd_rank_vel_7d": np.nan,
                               "extreme_move_prob": np.nan,
                               "median_fwd_vol_ratio": np.nan})
                continue
            fv = sub["fwd_vol_1d"] / sub["volume_24h_usd"].replace(0, np.nan)
            g_rows.append({
                "rank_band": band, "shape": name, "tested": True,
                "n": int(len(sub)),
                "continuation_rate": float((r7 > 0).mean()),
                "median_fwd_7d": float(r7.median()),
                "median_fwd_rank_vel_7d": float(
                    sub["fwd_rank_vel_7d"].median()),
                "extreme_move_prob": float((r7.abs() > 0.15).mean()),
                "median_fwd_vol_ratio": float(fv.median()),
            })
    shape = pd.DataFrame(g_rows)
    shape.to_csv(ROOT / "RESULTS" / "11_MOMENTUM_STATE_GEOMETRY.csv", index=False)
    print("phase G done:", shape.shape, flush=True)

    # =====================================================================
    # PHASE H — persistence/decay after extreme moves
    # =====================================================================
    lf2 = comb.copy()
    obs_count = lf2.groupby("cmc_id")["ret_1d"].transform("count")
    lf2 = lf2[obs_count >= 120].copy()
    lf2 = lf2.sort_values(["cmc_id", "historical_date"])
    grp = lf2.groupby("cmc_id")["ret_1d"]

    ev_parts = []
    # full-sample definition
    hi = grp.transform(lambda s: s.quantile(0.975))
    lo = grp.transform(lambda s: s.quantile(0.025))
    e1 = lf2[(lf2["ret_1d"] >= hi) | (lf2["ret_1d"] <= lo)].copy()
    e1["event_def"] = "FULL_SAMPLE"
    ev_parts.append(e1)
    # trailing-252d causal definition
    hi_t = grp.transform(lambda s: s.shift(1).rolling(252, min_periods=120)
                         .quantile(0.975))
    lo_t = grp.transform(lambda s: s.shift(1).rolling(252, min_periods=120)
                         .quantile(0.025))
    e2 = lf2[(lf2["ret_1d"] >= hi_t) | (lf2["ret_1d"] <= lo_t)].copy()
    e2["event_def"] = "TRAILING_252D"
    ev_parts.append(e2)
    ev = pd.concat(ev_parts, ignore_index=True)
    ev = ev.sort_values(["cmc_id", "historical_date"])

    # forward returns at each horizon via log-cumsum
    ok = ev["ret_1d"].notna() & (ev["ret_1d"] > -1.0)
    logf = np.where(ok, np.log1p(ev["ret_1d"].clip(lower=-0.9999)), np.nan)
    ev["_logf"] = logf
    ev_csid = ev["cmc_id"].values
    ev_dates = ev["historical_date"].values
    # group-level cumsum
    cs_ev = ev.groupby("cmc_id", sort=False)["_logf"].cumsum()
    ev["_cs"] = cs_ev.values
    for w in [1, 3, 7, 14, 30]:
        cs_sh = ev.groupby("cmc_id", sort=False)["_logf"].transform(
            lambda s: s.shift(-w))
        ev[f"fwd_ret_{w}d"] = np.expm1(cs_sh - ev["_logf"])
    ev = ev.drop(columns=["_logf", "_cs"])

    # chain confirmation: median same-chain event-day return (causal at t)
    chain_med = ev.groupby(["historical_date", "platform_chain"])["ret_1d"] \
        .transform("median")
    ev["chain_confirms"] = np.sign(chain_med) == np.sign(ev["ret_1d"])
    ev["event_sign"] = np.where(ev["ret_1d"] > 0, "UP", "DOWN")
    h_rows = []
    for band in BANDS:
        bd = ev[ev["rank_band"] == band]
        for edef in ["FULL_SAMPLE", "TRAILING_252D"]:
            be = bd[bd["event_def"] == edef]
            for sign in ["UP", "DOWN"]:
                sub = be[be["event_sign"] == sign]
                for confirm in [True, False]:
                    sc = sub[sub["chain_confirms"] == confirm]
                    row = {"rank_band": band, "event_def": edef,
                           "event_sign": sign, "chain_confirms": confirm,
                           "n": int(len(sc)),
                           "n_days": int(sc["historical_date_key"].nunique())}
                    for w in [1, 3, 7, 14, 30]:
                        col = f"fwd_ret_{w}d"
                        r = sc[col].dropna()
                        row[f"median_fwd_{w}d"] = float(r.median()) if len(r) else np.nan
                        row[f"mean_fwd_{w}d"] = float(r.mean()) if len(r) else np.nan
                        row[f"reversal_rate_{w}d"] = float(
                            (np.sign(r) != np.sign(sc.loc[r.index, "ret_1d"])).mean()) \
                            if len(r) else np.nan
                    h_rows.append(row)
    persist = pd.DataFrame(h_rows)
    persist.to_csv(ROOT / "RESULTS" / "12_PERSISTENCE_DECAY.csv", index=False)
    print("phase H done:", persist.shape, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
