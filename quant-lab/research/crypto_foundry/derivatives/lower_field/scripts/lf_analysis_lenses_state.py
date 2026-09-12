#!/usr/bin/env python3
"""LF — Phase J (chain/sector/age/liquidity lenses), Phase K (redundancy
compression), Phase L (hidden-state gate), plus the NULL ledger.

Outputs:
  RESULTS/13_CHAIN_LENS.csv
  RESULTS/14_SECTOR_LENS.csv
  RESULTS/15b_REDUNDANCY_COMPRESSION.csv
  RESULTS/15c_HIDDEN_STATE_GATE.csv
  NULLS/16_NULLS_AND_DISSOLVED_PATTERNS.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "RESULTS" / "lower_field_panel.parquet"

BANDS = ["501-750", "751-1000", "1001-1500", "1501-2000"]
LOWER_ALL = ["501-750", "751-1000", "1001-1500", "1501-2000"]
MIN_CELL_DAYS = 120


def main() -> int:
    lf = pd.read_parquet(PANEL)
    lf = lf.replace([np.inf, -np.inf], np.nan)
    lf = lf[~lf["is_stablecoin"].astype(bool)].copy()
    lf["historical_date_key"] = lf["historical_date"].dt.strftime("%Y-%m-%d")

    # impulse classes (same percentiles as analysis-events)
    mkt = lf["mkt_ret_1d"].dropna()
    q10, q40, q60, q90 = np.percentile(mkt, [10, 40, 60, 90])
    lf["impulse"] = "ALL"
    lf.loc[lf["mkt_ret_1d"] >= q90, "impulse"] = "POSITIVE_MARKET"
    lf.loc[lf["mkt_ret_1d"] <= q10, "impulse"] = "NEGATIVE_MARKET"
    lf.loc[(lf["mkt_ret_1d"] >= q40) & (lf["mkt_ret_1d"] <= q60),
           "impulse"] = "CALM"

    # =====================================================================
    # PHASE J — chain lens (residual after band+impulse conditioning)
    # =====================================================================
    # residual = asset ret minus band-median ret within impulse class
    med = lf.groupby(["rank_band", "impulse"])["ret_1d"] \
        .transform("median")
    lf["band_resid"] = lf["ret_1d"] - med
    chain_cover = lf["platform_chain"].replace("", np.nan)
    top_chains = chain_cover.value_counts().head(12).index.tolist()
    j_rows = []
    for ch in top_chains:
        sub = lf[lf["platform_chain"] == ch]
        pos = sub[sub["impulse"] == "POSITIVE_MARKET"]
        neg = sub[sub["impulse"] == "NEGATIVE_MARKET"]
        j_rows.append({
            "chain": ch,
            "n_asset_days": int(len(sub)),
            "n_dates": int(sub["historical_date_key"].nunique()),
            "n_assets": int(sub["cmc_id"].nunique()),
            "median_resid_all": float(sub["band_resid"].median()),
            "median_ret_pos_mkt": float(pos["ret_1d"].median())
            if len(pos) else np.nan,
            "median_ret_neg_mkt": float(neg["ret_1d"].median())
            if len(neg) else np.nan,
            "iqr_resid": float(sub["band_resid"].quantile(0.75)
                               - sub["band_resid"].quantile(0.25)),
            "stale_rate": float(sub["flag_stale_price"].mean()),
            "zero_vol_rate": float(sub["flag_zero_volume"].mean()),
        })
    chain_lens = pd.DataFrame(j_rows)
    chain_lens.to_csv(ROOT / "RESULTS" / "13_CHAIN_LENS.csv", index=False)
    print("phase J chain done:", chain_lens.shape, flush=True)

    # =====================================================================
    # PHASE J — sector lens
    # =====================================================================
    tag_counts = pd.Series([t for lst in
                            lf["tags"].fillna("").str.split(";") for t in lst
                            if t]).value_counts()
    top_tags = tag_counts.head(15).index.tolist()
    s_rows = []
    for tg in top_tags:
        sub = lf[lf["tags"].fillna("").str.split(";")
                 .apply(lambda lst: tg in lst)]
        pos = sub[sub["impulse"] == "POSITIVE_MARKET"]
        neg = sub[sub["impulse"] == "NEGATIVE_MARKET"]
        s_rows.append({
            "sector": tg,
            "n_asset_days": int(len(sub)),
            "n_dates": int(sub["historical_date_key"].nunique()),
            "n_assets": int(sub["cmc_id"].nunique()),
            "median_resid_all": float(sub["band_resid"].median()),
            "median_ret_pos_mkt": float(pos["ret_1d"].median())
            if len(pos) else np.nan,
            "median_ret_neg_mkt": float(neg["ret_1d"].median())
            if len(neg) else np.nan,
            "iqr_resid": float(sub["band_resid"].quantile(0.75)
                               - sub["band_resid"].quantile(0.25)),
        })
    sector_lens = pd.DataFrame(s_rows)
    sector_lens.to_csv(ROOT / "RESULTS" / "14_SECTOR_LENS.csv", index=False)
    print("phase J sector done:", sector_lens.shape, flush=True)

    # listing-age and liquidity lenses
    age_bins = [(-1, 30), (30, 180), (180, 730), (730, 10 ** 9)]
    age_labels = ["0-30d", "31-180d", "181-730d", ">730d"]
    lf["age_bin"] = pd.cut(lf["listing_age_days"], bins=[b[0] - 0.1 for b in age_bins]
                           + [10 ** 9], labels=age_labels)
    liq = lf.groupby(["age_bin", "impulse"])["ret_1d"].median().reset_index()
    liq["measure"] = "median_ret_by_age"
    liq.to_csv(ROOT / "RESULTS" / "15a_AGE_LENS.csv", index=False)

    # =====================================================================
    # PHASE L — hidden-state gate (observable conditioning first)
    # =====================================================================
    l_rows = []
    # residual dispersion by (impulse class x vol tercile x BTC regime)
    lf["vol_terc"] = pd.qcut(lf["mkt_vol_30d"].rank(method="first"), 3,
                             labels=["VOL_LOW", "VOL_MED", "VOL_HIGH"])
    lf["btc_regime"] = np.where(lf["btc_ret_1d"] > 0, "BTC_UP", "BTC_DOWN")
    for imp in ["POSITIVE_MARKET", "NEGATIVE_MARKET", "CALM"]:
        sub = lf[lf["impulse"] == imp]
        for vt in ["VOL_LOW", "VOL_MED", "VOL_HIGH"]:
            sv = sub[sub["vol_terc"] == vt]
            for br in ["BTC_UP", "BTC_DOWN"]:
                sb = sv[sv["btc_regime"] == br]
                r = sb["band_resid"].dropna()
                l_rows.append({
                    "impulse": imp, "vol_terc": vt, "btc_regime": br,
                    "n_asset_days": int(len(sb)),
                    "n_days": int(sb["historical_date_key"].nunique()),
                    "median_resid": float(r.median()) if len(r) else np.nan,
                    "iqr_resid": float(r.quantile(0.75) - r.quantile(0.25))
                    if len(r) else np.nan,
                    "std_resid": float(r.std()) if len(r) else np.nan,
                })
    gate = pd.DataFrame(l_rows)
    gate.to_csv(ROOT / "RESULTS" / "15c_HIDDEN_STATE_GATE.csv", index=False)
    print("phase L gate done:", gate.shape, flush=True)

    # =====================================================================
    # PHASE K — redundancy compression (proxy substitution checks)
    # =====================================================================
    k_rows = []
    # K1: global proxy correlations (mkt vs btc vs eth vs breadth)
    gcols = lf[["mkt_ret_1d", "btc_ret_1d", "eth_ret_1d",
                "top500_breadth_30d", "mkt_vol_30d"]].corr()
    for a, b in [("mkt_ret_1d", "btc_ret_1d"), ("mkt_ret_1d", "eth_ret_1d"),
                 ("btc_ret_1d", "eth_ret_1d"),
                 ("mkt_ret_1d", "top500_breadth_30d"),
                 ("mkt_ret_1d", "mkt_vol_30d")]:
        k_rows.append({"pair": f"{a}|{b}",
                       "corr": float(gcols.loc[a, b]),
                       "class": "REDUNDANT_PROXY" if abs(gcols.loc[a, b]) > 0.9
                       else ("PARTIAL_PROXY" if abs(gcols.loc[a, b]) > 0.6
                             else "DISTINCT_INFORMATION")})
    # K2: horizon redundancy — adjacent-horizon correlation within lower field
    hcorr = lf[["ret_1d", "ret_3d", "ret_7d", "ret_14d", "ret_30d",
                "ret_60d"]].corr()
    for h in ["ret_1d", "ret_3d", "ret_7d", "ret_14d", "ret_30d"]:
        hw = int(h.replace("ret_", "").replace("d", ""))
        next_h = {1:3, 3:7, 7:14, 14:30, 30:60}[hw]
        c = hcorr.loc[h, f"ret_{next_h}d"]
        k_rows.append({"pair": f"{h}|next", "corr": float(c), "class": ""})
    k = pd.DataFrame(k_rows)
    # fill classes for horizon pairs
    k.loc[k["pair"].str.contains("ret_"), "class"] = \
        np.where(k.loc[k["pair"].str.contains("ret_"), "corr"].abs() > 0.85,
                 "REDUNDANT_PROXY",
                 np.where(k.loc[k["pair"].str.contains("ret_"), "corr"].abs()
                          > 0.6, "PARTIAL_PROXY", "DISTINCT_INFORMATION"))
    k.to_csv(ROOT / "RESULTS" / "15b_REDUNDANCY_COMPRESSION.csv", index=False)
    print("phase K done:", k.shape, flush=True)

    # =====================================================================
    # NULL ledger — every pattern that failed or dissolved
    # =====================================================================
    null_rows = []
    # N1: no-distinct-structure check — compare lower-field vs top-band
    #     dispersion and elasticity: reported from analysis-events (frozen
    #     thresholds); here we record the tests we will run in reconciliation.
    # N2: stale-exclusion sensitivity is run in the nulls script (below).
    # N3: chain/sector residual |median| < 0.5% -> dissolved lens
    for _, r in chain_lens.iterrows():
        if abs(r["median_resid_all"]) < 0.005:
            null_rows.append({
                "test_id": "J_CHAIN_RESID",
                "object": r["chain"],
                "finding": "chain residual within +/-0.5% of band-impulse median",
                "verdict": "DISSOLVE" if r["n_asset_days"] > 5000 else "SPARSE",
                "n": int(r["n_asset_days"]),
                "evidence": f"median_resid={r['median_resid_all']:.4f}",
            })
    for _, r in sector_lens.iterrows():
        if abs(r["median_resid_all"]) < 0.005:
            null_rows.append({
                "test_id": "J_SECTOR_RESID",
                "object": r["sector"],
                "finding": "sector residual within +/-0.5% of band-impulse median",
                "verdict": "DISSOLVE" if r["n_asset_days"] > 5000 else "SPARSE",
                "n": int(r["n_asset_days"]),
                "evidence": f"median_resid={r['median_resid_all']:.4f}",
            })
    # N4: hidden-state gate outcome (recorded after inspecting gate table)
    null_rows.append({
        "test_id": "L_HIDDEN_STATE_GATE",
        "object": "residual structure after impulse x vol x btc conditioning",
        "finding": "assessed in 15c_HIDDEN_STATE_GATE.csv; verdict in decision doc",
        "verdict": "PENDING",
        "n": int(len(lf)),
        "evidence": "residual std by cell in 15c",
    })
    nulls = pd.DataFrame(null_rows)
    nulls.to_csv(ROOT / "NULLS" / "16_NULLS_AND_DISSOLVED_PATTERNS.csv",
                 index=False)
    print("nulls done:", nulls.shape, flush=True)

    # global proxy correlation output for redundancy doc
    (ROOT / "RESULTS" / "15d_GLOBAL_PROXY_CORR.csv").write_text(
        gcols.round(4).to_csv(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
