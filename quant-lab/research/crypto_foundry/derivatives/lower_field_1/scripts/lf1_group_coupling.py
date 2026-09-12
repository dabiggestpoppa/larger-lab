"""LOWER-FIELD-1 — 10 GROUP_BEHAVIOR_CLASSIFICATION & 11 LOCAL_COUPLING.

Classification at band-day level + event-level. Uses daily band-state table.

Outputs:
  RESULTS/10_GROUP_BEHAVIOR_CLASSIFICATION.csv
  RESULTS/11_LOCAL_COUPLING_MATRIX.csv
"""
import numpy as np
import pandas as pd

import lf1_common as C


def main():
    p = pd.read_parquet(C.PANEL)
    p["z_cross"] = p.groupby("historical_date", sort=False)["ret_1d"].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )
    p["sigma_t0"] = C.compute_sigma(p)

    # --- daily band-level state (participation, dispersion, simultaneous movers)
    g = p.groupby(["historical_date", "rank_band"], sort=False)
    band = g["ret_1d"].agg(
        n="size",
        participation=lambda s: float((s > 0).mean()),
        dispersion=lambda s: float(s.std(ddof=0)),
        median_ret=lambda s: float(s.median()),
    ).reset_index()
    # simultaneous 2-sigma movers: fraction of band rows with |ret| >= 2*sigma
    frac2 = (
        (p["ret_1d"].abs() >= 2 * p["sigma_t0"])
        .groupby([p["historical_date"], p["rank_band"]], sort=False)
        .mean().rename("frac_2sig").reset_index()
    )
    band = band.merge(frac2, on=["historical_date", "rank_band"], how="left")

    # leader concentration: top gross mover share of band net absolute move
    def leader_share(g):
        a = g["ret_1d"].abs()
        if len(g) == 0 or a.sum() == 0:
            return np.nan
        top = g["ret_1d"].loc[a.idxmax()]
        return float(abs(top) / a.sum())
    lc = g.apply(leader_share).rename("leader_share").reset_index()
    band = band.merge(lc, on=["historical_date", "rank_band"], how="left")
    band["date"] = band["historical_date"]

    # date-level global breadth (whole field) for GLOBAL_SYNC classification
    global_breadth = p.groupby("historical_date")["ret_1d"].apply(lambda s: (s > 0).mean())
    global_breadth90 = global_breadth.quantile(0.90)
    band = band.merge(global_breadth.rename("global_breadth"), on="historical_date", how="left")

    # adjacent band participation for MULTI_BAND
    def classify(r):
        part = r["participation"]
        # protection for NaN
        if pd.isna(part):
            return "NA"
        if part < 0.25:
            return "ISOLATED"
        elif part < 0.55:
            return "LOCAL_CLUSTER"
        elif part < 0.85:
            return "BAND_BROAD"
        else:
            return "GLOBAL_SYNC" if r["global_breadth"] >= global_breadth90 else "BAND_BROAD"
    band["group_class"] = band.apply(classify, axis=1)

    d10 = band[["historical_date", "rank_band", "n", "participation", "dispersion",
               "median_ret", "frac_2sig", "leader_share", "global_breadth", "group_class"]]
    d10.to_csv(C.RESULTS / "10_GROUP_BEHAVIOR_CLASSIFICATION.csv", index=False)
    print("=== 10 group class counts by band ===")
    print(pd.crosstab(d10["rank_band"], d10["group_class"]).to_string())

    # --- 11 local coupling: same-day correlation of band v BTC/ETH, plus event coupling
    # band-median ret vs BTC/ETH same-day corr
    btc = p.groupby("historical_date")["btc_ret_1d"].last()
    eth = p.groupby("historical_date")["eth_ret_1d"].last()
    mkt = p.groupby("historical_date")["mkt_ret_1d"].last()
    dd = d10.merge(btc.rename("btc"), on="historical_date", how="left")
    dd = dd.merge(eth.rename("eth"), on="historical_date", how="left")
    dd = dd.merge(mkt.rename("mkt"), on="historical_date", how="left")

    # also get event-level coupling: what fraction of band-day extremes co-move with btc/eth/mkt
    ev = pd.read_parquet(C.ROOT / "EVENTS" / "lf1_event_set.parquet")
    # co-direction of extreme events with btc/eth/mkt same-day
    ev = ev.merge(btc.rename("btc_t"), on="historical_date", how="left")
    ev = ev.merge(eth.rename("eth_t"), on="historical_date", how="left")
    ev = ev.merge(mkt.rename("mkt_t"), on="historical_date", how="left")
    ev["co_btc"] = (np.sign(ev["ret_1d"]) == np.sign(ev["btc_t"])) & ev["btc_t"].abs() > 1e-12
    ev["co_eth"] = (np.sign(ev["ret_1d"]) == np.sign(ev["eth_t"])) & ev["eth_t"].abs() > 1e-12
    ev["co_mkt"] = (np.sign(ev["ret_1d"]) == np.sign(ev["mkt_t"])) & ev["mkt_t"].abs() > 1e-12

    rows = []
    for band in C.PRIMARY_BANDS:
        bd = dd[dd["rank_band"] == band]
        corr_btc = bd["median_ret"].corr(bd["btc"])
        corr_eth = bd["median_ret"].corr(bd["eth"])
        corr_mkt = bd["median_ret"].corr(bd["mkt"])
        # correlation between band dispersion and btc abs move (local coupling to stress)
        eb = ev[ev["rank_band"] == band]
        rows.append({
            "rank_band": band,
            "corr_band_btc_sameday": round(float(corr_btc), 4),
            "corr_band_eth_sameday": round(float(corr_eth), 4),
            "corr_band_mkt_sameday": round(float(corr_mkt), 4),
            "corr_band_disp_lag0": round(float(bd["dispersion"].corr(bd["mkt"].abs())), 4),
            "n_events": int(len(eb)),
            "frac_event_co_btc": round(float(eb["co_btc"].mean()) if len(eb) else np.nan, 4),
            "frac_event_co_eth": round(float(eb["co_eth"].mean()) if len(eb) else np.nan, 4),
            "frac_event_co_mkt": round(float(eb["co_mkt"].mean()) if len(eb) else np.nan, 4),
            # conditional lift: fraction of extreme events occurring when BTC_UP (vs expected 0.5)
            "frac_events_btc_up": round(float((eb["btc_t"] > 0).mean()) if len(eb) else np.nan, 4),
        })
    d11 = pd.DataFrame(rows)
    d11.to_csv(C.RESULTS / "11_LOCAL_COUPLING_MATRIX.csv", index=False)
    print("\n=== 11 local coupling ===")
    print(d11.to_string(index=False))
    print("\nwrote 10 and 11")


if __name__ == "__main__":
    main()