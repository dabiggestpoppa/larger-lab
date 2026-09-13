"""LOWER-FIELD-1 — 14 CROSS_FIELD_ALIGNMENT, 15 CROSS_FIELD_HANDOFF_TESTS, 16 FORM_CHANGE_BY_RANK.

Uses frozen lower-field band state (30_CROSS_FIELD_HANDOFF_READY.parquet, already
defined WITHOUT looking at Agent-1 outcomes) and Agent-1 MECH-4 EXIT dates as
event coordinates.

Outputs:
  RESULTS/14_CROSS_FIELD_ALIGNMENT.csv   (post-exit window variance vs trailing baseline)
  RESULTS/15_CROSS_FIELD_HANDOFF_TESTS.csv (lagged lower-field response, common-factor controlled)
  RESULTS/16_FORM_CHANGE_BY_RANK.csv      (corr/disp/tail/breadth/cluster by rank depth)
"""
import numpy as np
import pandas as pd

import lf1_common as C

WINDOWS = {"0D": 0, "1D": 1, "2-3D": (2, 3), "4-7D": (4, 7), "8-14D": (8, 14), "15-30D": (15, 30)}


def main():
    h = pd.read_parquet(C.HANDBF).copy()
    h["date"] = pd.to_datetime(h["date"])
    h = h.dropna(subset=["dispersion"])
    h = h[h["date"] >= "2020-09-01"]

    # EXIT event dates
    m = pd.read_csv(C.MECH4_LATTICE)
    exits = pd.to_datetime(m["exit_date"]).dt.normalize().dropna().tolist()
    exits = sorted(set(exits))
    print("MECH-4 exit events:", len(exits))
    edf = pd.DataFrame({"exit_date": exits})
    edf["baseline_end"] = edf["exit_date"] - pd.Timedelta(days=1)
    edf["baseline_start"] = edf["exit_date"] - pd.Timedelta(days=60)

    # --- 16 FORM CHANGE BY RANK (continuous across depth; band-level means here)
    # deeper bands show higher dispersion and higher tail share / lower breadth-corr
    rows16 = []
    for band in C.PRIMARY_BANDS:
        b = h[h["rank_band"] == band]
        rows16.append({
            "rank_band": band,
            "depth_rank_mid": int(band.split("-")[0]) + (int(band.split("-")[1]) - int(band.split("-")[0])) // 2,
            "mean_dispersion": round(float(b["dispersion"].mean()), 5),
            "p95_dispersion": round(float(b["dispersion"].quantile(0.95)), 5),
            "mean_extreme_share": round(float((b["extreme_up_share"] + b["extreme_dn_share"]).mean()), 5),
            "mean_breadth": round(float(b["breadth"].mean()), 4),
            "corr_band_btc": round(float(b["median_ret"].corr(b["btc_ret_1d"])), 4),
            "mean_shmc_share": round(float(b["short_hot_medium_cold_share"].mean()), 4),
            "mean_rank_migration": round(float(b["rank_migration_7d"].mean()), 4),
        })
    d16 = pd.DataFrame(rows16)
    d16.to_csv(C.RESULTS / "16_FORM_CHANGE_BY_RANK.csv", index=False)
    print("\n=== 16 FORM CHANGE ===")
    print(d16.to_string(index=False))

    # --- align windows & controls ---
    # common-factor control: residualize each band series on same-day btc/eth/mkt
    targets = ["dispersion", "tail_ratio", "extreme_up_share", "extreme_dn_share", "median_ret"]
    resid_frames = []
    for band in C.PRIMARY_BANDS:
        b = h[h["rank_band"] == band].dropna(
            subset=["btc_ret_1d", "eth_ret_1d", "mkt_ret_1d"]
        ).copy()
        X = np.column_stack([np.ones(len(b)), b["btc_ret_1d"], b["eth_ret_1d"], b["mkt_ret_1d"]])
        for target in targets:
            y = b[target].to_numpy(float)
            idx = np.isfinite(y)
            beta, *_ = np.linalg.lstsq(X[idx], y[idx], rcond=None)
            r = np.full(len(b), np.nan)
            r[idx] = y[idx] - X[idx] @ beta
            b[f"{target}_resid"] = r
        resid_frames.append(b)
    h = pd.concat(resid_frames, ignore_index=True)
    piv = {}
    for band in C.PRIMARY_BANDS:
        b = h[h["rank_band"] == band].dropna(subset=["dispersion_resid", "tail_ratio_resid"])
        piv[band] = (b.set_index("date")
                      .reindex(pd.date_range(h["date"].min(), h["date"].max(), freq="D"))
                      .sort_index())
    h = h.set_index(["date", "rank_band"]).reset_index()

    # --- 14 & 15: post-exit window response vs trailing baseline, per band (via piv!) ---
    align_rows = []
    agg_rows = {}
    d15 = pd.DataFrame()
    for band in C.PRIMARY_BANDS:
        b = piv[band]
        test_rows = []
        for _, e in edf.iterrows():
            d0 = e["exit_date"]
            base = b.loc[b.index < d0]
            pre = base[base.index >= e["baseline_start"]]
            for target in ["dispersion_resid", "tail_ratio_resid", "extreme_up_share",
                           "extreme_dn_share", "median_ret_resid"]:
                if target not in b.columns:
                    continue
                base_series = pre[target].dropna()
                if len(base_series) == 0:
                    continue
                base_val = float(base_series.iloc[-1])
                for wname, wdef in WINDOWS.items():
                    if wname == "0D":
                        w = b.loc[b.index == d0]
                    elif wname == "1D":
                        w = b.loc[b.index == d0 + pd.Timedelta(days=1)]
                    else:
                        lo, hi = wdef
                        w = b.loc[(b.index >= d0 + pd.Timedelta(days=lo)) &
                                  (b.index <= d0 + pd.Timedelta(days=hi))]
                    wv = w[target].dropna()
                    if len(wv) == 0:
                        continue
                    resp = float(wv.mean()) - base_val
                    test_rows.append({"band": band, "target": target, "lag": wname,
                                      "response": round(resp, 6)})
        if test_rows:
            d15 = pd.concat([d15, pd.DataFrame(test_rows)], ignore_index=True)
        # 14 alignment
        tot = up = dn = 0
        for _, e in edf.iterrows():
            d0 = e["exit_date"]
            pre = b.loc[(b.index >= e["baseline_start"]) & (b.index < d0), "dispersion_resid"].dropna()
            post = b.loc[(b.index >= d0) & (b.index <= d0 + pd.Timedelta(days=7)), "dispersion_resid"].dropna()
            if len(pre) > 5 and len(post) > 2:
                dpre = float(pre.std())
                dpost = float(post.std())
                if np.isfinite(dpre) and dpre > 0:
                    tot += 1
                    if dpost > dpre:
                        up += 1
                    else:
                        dn += 1
        align_rows.append({"band": band, "n_exits_valid": tot,
                           "frac_7d_disp_rise": round(up / max(1, tot), 3),
                           "frac_7d_disp_fall": round(dn / max(1, tot), 3), "n_rise": up, "n_fall": dn})
    d14 = pd.DataFrame(align_rows)
    if len(d15):
        agg = d15.groupby(["band", "target", "lag"], as_index=False)["response"].agg(["mean", "count", "std"])
        agg.columns = ["band", "target", "lag", "mean_response", "n_exits", "std_response"]
        agg.to_csv(C.RESULTS / "15_CROSS_FIELD_HANDOFF_TESTS.csv", index=False)
        print("\n=== 15 mean post-exit dispersion_resid response by band x lag ===")
        disp = agg[agg["target"] == "dispersion_resid"].pivot(index="lag", columns="band", values="mean_response")
        print(disp.round(5).to_string())

    else:
        print("\n=== 15: no valid window responses computed ===")
    d14.to_csv(C.RESULTS / "14_CROSS_FIELD_ALIGNMENT.csv", index=False)
    print("\n=== 14 alignment: does post-exit 7d dispersion RISE vs trailing 60d? ===")
    print(d14.to_string(index=False))
    print("\nwrote 14, 15, 16")


if __name__ == "__main__":
    main()