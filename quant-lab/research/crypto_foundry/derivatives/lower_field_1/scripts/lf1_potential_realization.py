"""LOWER-FIELD-1 — 08 POTENTIAL_REALIZATION_PANEL & 09 DIVERGENCE.

REALIZED vs NON_DELIVERY for SHORT_HOT_MEDIUM_COLD states (prereg sec 7).

Also emits a reusable daily band-state table (RESULTS/band_daily_state.parquet)
for group-behavior and cross-field analyses.

Outputs:
  RESULTS/08_POTENTIAL_REALIZATION_PANEL.parquet
  RESULTS/09_POTENTIAL_REALIZATION_DIVERGENCE.csv
  RESULTS/band_daily_state.parquet
"""
import numpy as np
import pandas as pd

import lf1_common as C

MAX_H = 14


def build_daily_band_state(p):
    """Per (date, rank_band): breadth, dispersion, tail share, median ret, mean rank."""
    g = p.groupby(["historical_date", "rank_band"], sort=False)["ret_1d"]
    state = g.agg(
        breadth=lambda s: float((s > 0).mean()),
        dispersion=lambda s: float(s.std(ddof=0)),
        tail_share=lambda s: float((s.abs() >= 0.15).mean()),
        median_ret=lambda s: float(s.median()),
        n=lambda s: int(len(s)),
    ).reset_index()
    return state


def main():
    p = pd.read_parquet(C.PANEL)
    print("panel", len(p))
    p["sigma_t0"] = C.compute_sigma(p)
    p = C.add_momentum_shape(p)
    # forward cumulative rets per asset to +14
    byg = p.groupby("cmc_id", sort=False)["ret_1d"]
    fdf = pd.DataFrame(index=p.index)
    for k in range(1, MAX_H + 1):
        fdf[f"fwd{k}"] = byg.transform(lambda s, kk=k: s.shift(-kk))
    fmat = np.cumsum(fdf.to_numpy(float), axis=1)  # fmat[i,h] = cum t+1..t+h (h>=1)
    # panel columns for forward horizon |cum|
    for h in range(1, MAX_H + 1):
        p[f"fwdabs{h}"] = np.abs(fmat[:, h - 1])
        p[f"fwd{h}"] = fmat[:, h - 1]

    # band daily state
    band_state = build_daily_band_state(p)
    band_state.to_parquet(C.RESULTS / "band_daily_state.parquet", index=False)
    bs = band_state.rename(columns={
        "breadth": "band_breadth", "dispersion": "band_dispersion",
        "tail_share": "band_tail_share", "median_ret": "band_median_ret",
        "n": "band_n",
    })

    # SHORT_HOT_MEDIUM_COLD rows (full panel, not just events)
    shmc = p[p["momentum_state"] == "SHORT_HOT_MEDIUM_COLD"].copy()
    print("SHMC rows", len(shmc))

    # classify delivery
    sig = shmc["sigma_t0"].astype(float)
    fwd7 = shmc.get("fwd7") if "fwd7" in shmc else None
    fwd7abs = shmc["fwdabs7"]
    real = fwd7abs >= 2 * sig
    nondel = fwd7abs < 1 * sig
    shmc["delivery_class"] = np.where(real, "REALIZED", np.where(nondel, "NON_DELIVERY", "AMBIGUOUS"))

    # merge band daily state + per-asset discriminators
    shmc = shmc.merge(bs, on=["historical_date", "rank_band"], how="left", validate="many_to_one")

    # listing age, rank vel, region context already in panel for most; add BTC/ETH/vol
    feat_cols = [
        "rank", "listing_age_days", "volume_24h_usd", "rank_vel_7d", "rank_vel_14d",
        "mkt_vol_30d", "btc_ret_1d", "eth_ret_1d", "mkt_ret_1d", "top500_breadth_30d",
        "band_breadth", "band_dispersion", "band_tail_share", "band_median_ret",
        "ret_3d", "ret_7d", "ret_14d", "ret_30d",
    ]
    feat_cols = [c for c in feat_cols if c in shmc.columns]
    core = shmc[["historical_date", "cmc_id", "rank_band", "rank", "delivery_class",
                 "sigma_t0", "ret_1d", "is_stablecoin", "flag_any_quality"] + feat_cols].copy()
    # forward profile
    for h in [0, 1, 2, 3, 5, 7, 14]:
        if h == 0:
            core["fwd_cum_h0"] = shmc["ret_1d"]
        else:
            core[f"fwd_cum_h{h}"] = shmc[f"fwd{h}"]
    core = core.loc[:, ~core.columns.duplicated()]
    core["n_realized"] = int((real).sum())
    core.to_parquet(C.RESULTS / "08_POTENTIAL_REALIZATION_PANEL.parquet", index=False)

    # ---- divergence: Cohen's-d time course on discriminators
    rows = []
    for band in C.PRIMARY_BANDS:
        b = shmc[shmc["rank_band"] == band]
        rr = b[b["delivery_class"] == "REALIZED"]
        nn = b[b["delivery_class"] == "NON_DELIVERY"]
        if len(rr) < 50 or len(nn) < 50:
            continue
        for col in ["volume_24h_usd", "rank_vel_7d", "mkt_vol_30d", "btc_ret_1d",
                    "eth_ret_1d", "top500_breadth_30d", "band_breadth", "band_dispersion",
                    "band_tail_share", "listing_age_days", "ret_3d", "ret_14d"]:
            if col not in b.columns:
                continue
            a = rr[col].astype(float).dropna()
            c = nn[col].astype(float).dropna()
            if len(a) < 30 or len(c) < 30:
                continue
            ap = np.percentile(a, [25, 50, 75])
            cp = np.percentile(c, [25, 50, 75])
            sd = np.sqrt((a.var() + c.var()) / 2)
            d = (np.median(a) - np.median(c)) / (sd + 1e-12)
            rows.append({
                "rank_band": band, "feature": col,
                "n_realized": int(len(a)), "n_nondelivery": int(len(c)),
                "realized_med": round(float(ap[1]), 5),
                "nondelivery_med": round(float(cp[1]), 5),
                "cohens_d": round(float(d), 4),
            })
    d09 = pd.DataFrame(rows)
    d09.to_csv(C.RESULTS / "09_POTENTIAL_REALIZATION_DIVERGENCE.csv", index=False)

    # earliest-separation: pick strongest |d| per band
    print("\n=== 09 largest |cohens_d| per band (realized vs non-delivery) ===")
    for band in C.PRIMARY_BANDS:
        sub = d09[d09["rank_band"] == band].copy()
        if sub.empty:
            continue
        sub["absd"] = sub["cohens_d"].abs()
        sub = sub.sort_values("absd", ascending=False)
        top = sub.head(4)[["feature", "cohens_d", "realized_med", "nondelivery_med"]]
        print(f"\n{band}:")
        print(top.to_string(index=False))

    print(f"\nwrote 08 ({len(core)} rows), 09, band_daily_state.parquet")


if __name__ == "__main__":
    main()