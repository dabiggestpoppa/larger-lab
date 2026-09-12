"""LOWER-FIELD-1 — 07 TAIL_ACTIVATION_REVALIDATION & 13 REVERSAL_DECAY_GEOMETRY.

Uses the sigma-normalized event set + momentum_state (3D x 14D).

Outputs:
  RESULTS/07_TAIL_ACTIVATION_REVALIDATION.csv  (state x band x sigma move probs)
  RESULTS/13_REVERSAL_DECAY_GEOMETRY.csv      (UP/DOWN x band x reversal stats)
"""
import numpy as np
import pandas as pd

import lf1_common as C

FWD_H = 7


def main():
    ev = pd.read_parquet(C.ROOT / "EVENTS" / "lf1_event_set.parquet")
    print("events", len(ev))

    # momentum state at t0 and forward-cumulative ret (fwd 7d) added from panel
    p = pd.read_parquet(C.PANEL)
    p = C.add_momentum_shape(p)
    # forward cumulative 7d per asset, causal
    byg = p.groupby("cmc_id", sort=False)["ret_1d"]
    fdf = pd.DataFrame(index=p.index)
    for k in range(1, FWD_H + 1):
        fdf[f"f{k}"] = byg.transform(lambda s, kk=k: s.shift(-kk))
    fmat = fdf.to_numpy(float)
    fwd7 = np.nansum(fmat, axis=1)
    p["fwd7"] = fwd7
    p = p[["historical_date", "cmc_id", "momentum_state", "fwd7",
           "ret_14d", "ret_30d", "mkt_vol_30d", "btc_ret_1d", "eth_ret_1d"]]

    ev = ev.merge(p, on=["historical_date", "cmc_id"], how="left", validate="one_to_one")
    # sigma at event t0 from event set
    sig = ev["sigma_t0"].astype(float)

    # sign events from ret_1d at t0 (the triggering move)
    ev["event_sign"] = np.sign(ev["ret_1d"])

    print("\n=== 07 TAIL ACTIVATION (moves inside next 7d) by state x band ===")
    out = []
    for band in C.PRIMARY_BANDS:
        b = ev[ev["rank_band"] == band]
        for state in b["momentum_state"].dropna().unique():
            sb = b[b["momentum_state"] == state]
            if len(sb) < 100:
                continue
            mag = sb["fwd7"].abs()
            sigb = sb["sigma_t0"]
            n = len(sb)
            out.append({
                "rank_band": band, "state": state, "n": n,
                "P_gt_1sigma": round(float((mag > sigb).mean()), 4),
                "P_gt_2sigma": round(float((mag > 2*sigb).mean()), 4),
                "P_gt_3sigma": round(float((mag > 3*sigb).mean()), 4),
                "P_up_extreme": round(float(((sb["fwd7"] > 0) & (mag > 2*sigb)).mean()), 4),
                "P_dn_extreme": round(float(((sb["fwd7"] < 0) & (mag > 2*sigb)).mean()), 4),
            })
    d07 = pd.DataFrame(out)
    d07.to_csv(C.RESULTS / "07_TAIL_ACTIVATION_REVALIDATION.csv", index=False)
    tv = d07[d07["state"] == "SHORT_HOT_MEDIUM_COLD"][["rank_band", "n", "P_gt_2sigma", "P_gt_3sigma", "P_up_extreme", "P_dn_extreme"]]
    print(tv.to_string(index=False))

    print("\n=== 13 REVERSAL / DECAY GEOMETRY (UP vs DOWN extremes) ===")
    # raw-sign-based reversal: does the forward 7d move oppose the event direction
    out13 = []
    for band in C.PRIMARY_BANDS:
        b = ev[ev["rank_band"] == band]
        up = b[b["event_sign"] > 0]
        dn = b[b["event_sign"] < 0]
        for lbl, grp in [("UP", up), ("DOWN", dn)]:
            if len(grp) == 0:
                continue
            # reversal = fwd7 * event_sign < 0
            fws = np.sign(grp["fwd7"].to_numpy())
            es = grp["event_sign"].to_numpy()
            mag = grp["fwd7"].abs().to_numpy()
            rev = (fws == -es) & (mag > 0)
            # median giveback: fraction of t0 move given back
            giveback = (-grp["fwd7"].to_numpy() * es) / grp["ret_1d"].abs().to_numpy()
            out13.append({
                "rank_band": band, "sign": lbl, "n": int(len(grp)),
                "P_rev_7d": round(float(rev.mean()), 4),
                "median_giveback_pct": round(float(np.nanmedian(np.clip(giveback, -2, 2))), 4),
                "P_cont_7d": round(float(((fws == es) & (mag > 0)).mean()), 4),
                "median_fwd7_sigma": round(float((grp["fwd7"]/grp["sigma_t0"]).median()), 4),
            })
    d13 = pd.DataFrame(out13)
    d13.to_csv(C.RESULTS / "13_REVERSAL_DECAY_GEOMETRY.csv", index=False)
    print(d13.to_string(index=False))
    print("\nwrote 07 and 13")


if __name__ == "__main__":
    main()