"""LOWER-FIELD-2 event-time progression (14), delivery clock (15), cluster vs
isolated anatomy (16).

Uses the continuous-causal feature frame (already carries fwd1..fwd30_cum,
sigma_t0, top500_breadth_30d, mkt_vol_30d, listing_age_days, momentum_state).
Tail potential population: normalized 1-day move |ret_1d|/sigma_t0 >= 2.
Delivery at horizon h: |cumulative fwd h| >= k * (sigma_t0 * sqrt(h)).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import lf2_common as C
import lf2_load as L

H = [1, 2, 3, 5, 7, 10, 14, 21, 30]
FWD = {h: f"fwd{h}_cum" for h in H}


def event_time(df):
    """14. potential(|z1|>=2) -> REALIZED(|fwd7|>=2*sigma7) vs NON_DELIVERY.
    Reports realization rate by breadth regime, and per-feature cohen's d
    (available-at-t features) between realized and non-delivery cells."""
    df = df.copy()
    df["z1"] = df["ret_1d"].abs() / df["sigma_t0"]
    pot = df[df["z1"] >= 2].copy()
    sig7 = pot["sigma_t0"] * np.sqrt(7)
    pot["realized"] = np.where(pot["fwd7_cum"].abs() >= 2 * sig7, 1,
                               np.where(pot["fwd7_cum"].abs() < 1 * sig7, 0, np.nan))
    pt = pot.dropna(subset=["realized"])
    # realization summary by band x breadth (median-split within band)
    summary = []
    for band in C.PRIMARY_BANDS:
        pb = pt[pt["rank_band"] == band]
        medb = pb["top500_breadth_30d"].median()
        for hi, lab in [(True, "HIGH"), (False, "LOW")]:
            sub = pb[pb["top500_breadth_30d"] > medb] if hi else \
                pb[pb["top500_breadth_30d"] <= medb]
            if len(sub) < 50:
                continue
            summary.append({
                "rank_band": band, "breadth": lab, "n_potential": int(len(sub)),
                "p_realized": float(sub["realized"].mean()),
                "med_sig7_fwd": float((sub["fwd7_cum"] / sig7.loc[sub.index]).median()),
            })
    # per-feature discriminators (all-band + per-band) cohen's d realized vs not
    fcols = ["top500_breadth_30d", "mkt_vol_30d", "volume_24h_usd",
             "listing_age_days", "rank"]
    discr = []
    for band in ["ALL"] + C.PRIMARY_BANDS:
        tgt = pt if band == "ALL" else pt[pt["rank_band"] == band]
        if band == "ALL":
            r1 = pt[pt["realized"] == 1]
            r0 = pt[pt["realized"] == 0]
        else:
            r1 = tgt[tgt["realized"] == 1]
            r0 = tgt[tgt["realized"] == 0]
        for col in fcols:
            a = r1[col].dropna()
            b = r0[col].dropna()
            if len(a) < 30 or len(b) < 30:
                continue
            pooled = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
            d = (a.mean() - b.mean()) / pooled if pooled > 0 else np.nan
            discr.append({"band": band, "discriminator": col, "cohen_d": d,
                          "realized_n": int(len(a)), "nondeliv_n": int(len(b))})
    return (pd.DataFrame(summary), pd.DataFrame(discr))


def delivery_clock(df):
    """15. time to 1/2/3 sigma delivery (vs move sign) and time to max cumulative."""
    df = df.copy()
    sig = np.sign(df["ret_1d"].to_numpy(float))
    ev = df[df["ret_1d"].abs() / df["sigma_t0"] >= 2].copy()
    ev = ev[ev["ret_1d"].abs() > 0]
    eidx = ev.index
    sig_e = sig[eidx]
    s1 = ev["sigma_t0"].to_numpy(float)
    rows = []
    for k in [1, 2, 3]:
        deft = np.full(len(ev), np.nan)
        for h in H:
            fwdh = ev[FWD[h]].to_numpy(float) * sig_e
            reach = fwdh >= k * s1 * np.sqrt(h)
            deft = np.where(np.isnan(deft) & reach, h, deft)
        ev[f"t{k}s"] = deft
        rows.append({"metric": f"t{k}s", "units": "days-to-ksigma-forward"})
    # peak horizon = h with max absolute forward cumulative
    peak = np.zeros(len(ev), dtype=int)
    maxabs = -np.ones(len(ev))
    for h in H:
        a = ev[FWD[h]].abs().to_numpy(float)
        take = a > maxabs
        peak = np.where(take, h, peak)
        maxabs = np.where(take, a, maxabs)
    ev["t_peak"] = peak
    ev["lat_peak"] = maxabs / (ev["ret_1d"].abs().to_numpy(float))

    # conditioning
    ev["breadth"] = np.where(ev["top500_breadth_30d"] > ev["top500_breadth_30d"].median(),
                             "HIGH", "LOW")
    ev["vol"] = np.where(ev["mkt_vol_30d"] > ev["mkt_vol_30d"].median(), "HIGH", "LOW")
    ev["age"] = np.where(ev["listing_age_days"] > ev["listing_age_days"].median(),
                         "MATURE", "YOUNG")
    ev["updown"] = np.where(sig_e > 0, "UP", "DOWN")
    ev["shmc"] = np.where(ev["momentum_state"] == "SHORT_HOT_MEDIUM_COLD", "SHMC", "OTHER")
    out = []
    for cname in ["breadth", "vol", "age", "updown", "shmc"]:
        for band in C.PRIMARY_BANDS:
            b = ev[ev["rank_band"] == band]
            for val in pd.unique(b[cname]):
                bb = b[b[cname] == val]
                if len(bb) < 30:
                    continue
                for metric in ["t1s", "t2s", "t3s", "t_peak"]:
                    arr = bb[metric].astype(float)
                    out.append({
                        "condition": cname, "value": str(val), "rank_band": band,
                        "metric": metric, "n": int(len(bb)),
                        "median": float(arr.median()), "p25": float(arr.quantile(0.25)),
                        "p90": float(arr.quantile(0.90)),
                        "lat_peak_med": float(np.nanmedian(bb["lat_peak"])),
                    })
    return pd.DataFrame(out)


def cluster_anatomy(df):
    """16. isolated vs local-cluster vs band-broad vs multi-band extremes."""
    df = df.copy()
    z = df["ret_1d"].abs() / df["sigma_t0"]
    is_ext = z >= 2
    tmp = pd.DataFrame({"date": df["historical_date"], "band": df["rank_band"],
                        "z1": z, "ret": df["ret_1d"],
                        "sign": np.sign(df["ret_1d"].to_numpy(float)),
                        "fwd7_sig": df["fwd7_cum"].to_numpy() /
                                    (df["sigma_t0"].to_numpy() * np.sqrt(7))})
    cnt = (tmp[(tmp["z1"] >= 2) & (tmp["sign"] != 0)]
           .groupby(["date", "band", "sign"]).size().rename("ns").reset_index())
    ev = tmp[(tmp["z1"] >= 2) & (tmp["sign"] != 0)].merge(
        cnt, on=["date", "band", "sign"], how="left")
    ev["ns"] = ev["ns"].fillna(1).astype(int)
    ev["cls"] = np.where(ev["ns"] == 1, "ISOLATED",
                         np.where(ev["ns"] <= 5, "LOCAL_CLUSTER",
                                  np.where(ev["ns"] <= 20, "BAND_BROAD", "MULTI_BAND")))
    # reversal flag precomputed (fwd7 cumulative has opposite sign to move day)
    ev["rev7"] = (np.sign(ev["fwd7_sig"]) != ev["sign"]) & (ev["fwd7_sig"].notna())
    agg = ev.groupby(["band", "cls"]).agg(
        n=("z1", "size"), med_z1=("z1", "median"), p_ge3=("z1", lambda s: (s >= 3).mean()),
        med_ret=("ret", "median"), med_fwd7_sig=("fwd7_sig", "median"),
        p_rev7=("rev7", "mean"),
    ).reset_index()
    return agg


def main():
    df = L.load()
    summ, discr = event_time(df)
    summ.to_csv(C.RESULTS / "14_EVENT_TIME_SUMMARY.csv", index=False)
    discr.to_csv(C.RESULTS / "14_POTENTIAL_REALIZATION_DIVERGENCE.csv", index=False)
    dc = delivery_clock(df)
    dc.to_csv(C.RESULTS / "15_DELIVERY_CLOCK_CONDITIONAL.csv", index=False)
    ca = cluster_anatomy(df)
    ca.to_csv(C.RESULTS / "16_CLUSTER_VS_ISOLATED_ANATOMY.csv", index=False)
    print("== 14 p_realized by breadth (potential >=2s -> fwd7 >=2s7) ==")
    print(summ.pivot(index="rank_band", columns="breadth", values="p_realized").round(3).to_string())
    print("\ntop discriminators (all-band):")
    print(discr[discr["band"] == "ALL"].reindex(
        discr[discr["band"] == "ALL"]["cohen_d"].abs().sort_values(ascending=False).index)
        [["discriminator", "cohen_d", "realized_n", "nondeliv_n"]].to_string(index=False))
    print("\n== 15 clock median t2s / t_peak by band (across conditions) ==")
    dcq = dc[dc["metric"].isin(["t2s", "t3s", "t_peak"])].copy()
    pivot = dcq.pivot_table(index="rank_band", columns="metric",
                            values="median", aggfunc="median").round(1)
    print(pivot.reindex(C.PRIMARY_BANDS).to_string())
    print("\n== 16 cluster anatomy ==")
    print(ca.to_string(index=False))


if __name__ == "__main__":
    main()