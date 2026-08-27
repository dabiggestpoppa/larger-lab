"""LOWER-FIELD-2 reversal manifold + conditioning + purged robustness + surface.

Outputs:
  05_REVERSAL_MANIFOLD.csv            band x sign x amplitude x horizon
  06_REVERSAL_CONDITIONAL_MAP.csv     condition reversal on global/local/asset/pre-event state
  07_REVERSAL_PURGED_ROBUSTNESS.csv   overlap-purged + asset-clustered N + headline stats
  08_CONTINUOUS_RANK_REVERSAL_SURFACE.csv  rolling PIT-rank windows

Definitions (frozen in 01_PREREGISTRATION.md):
  move day sign        s = sign(ret_1d)
  fwd{h}_cum           sum of ret_1d over t+1..t+h
  sign reversal at h   sign(f)>0 != sign(s>0)  (strict opposite direction)
  giveback frac        max(0, -f / ret_1d)       (fraction of the move retraced; 0 if forward continues)
  continuation         same direction, nonzero fwd
  MFE/MAE (sigma u.)   max/min over horizons of (fwd_h_cum / sigma_t0)
  time-to-reversal     smallest h in REV_HORIZONS with sign(f_h) != sign(s)
  time-to-new-extreme  smallest h with |fwd_h| >= |ret_1d| and same sign
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import lf2_common as C
import lf2_load as L

H = C.REV_HORIZONS                       # [1,2,3,5,7,10,14,21,30]
FWD_COLS = [f"fwd{h}_cum" for h in H]


def event_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Rows (asset-days) where |ret_1d|/sigma_t0 >= 2 (primary normalized gate)
    OR raw |ret_1d| >= 10% (raw gate). Attach sign, fwd columns, reversal flags."""
    z = df["ret_1d"].abs() / df["sigma_t0"]
    r = df["ret_1d"]
    m = (z >= 2.0) | (r.abs() >= 0.10)
    ev = df[m].copy()
    ev["z_move"] = z[m]
    ev["s"] = np.sign(ev["ret_1d"])
    # normalized displacement over forward horizons
    for h in H:
        c = f"fwd{h}_cum"
        ev[f"fwd{h}_sig"] = ev[c] / ev["sigma_t0"]
        ev[f"rev{h}"] = (np.sign(ev[c]) != ev["s"]) & ev[c].notna() & (ev["ret_1d"].abs() > 0)
        ev[f"gb{h}"] = np.where(
            (np.sign(ev[c]) != ev["s"]), np.clip(-ev[c] / ev["ret_1d"], 0, 10), 0.0)
        # time accumulators
        ev[f"t2rev{h}"] = np.where(ev[f"rev{h}"], h, np.nan)
        ev[f"t2ne{h}"] = np.where(
            (ev[c].abs() >= ev["ret_1d"].abs()) & (np.sign(ev[c]) == ev["s"]),
            h, np.nan)
    # MFE / MAE in sigma units (best/worst fwd excursion across horizons)
    fwd_sig = ev[[f"fwd{h}_sig" for h in H]].to_numpy()
    with np.errstate(invalid="ignore"):
        ev["mfe_sig"] = np.where(ev["s"] > 0, np.nanmax(fwd_sig, axis=1),
                                 -np.nanmin(fwd_sig, axis=1))
        ev["mae_sig"] = np.where(ev["s"] < 0, np.nanmax(fwd_sig, axis=1),
                                 -np.nanmin(fwd_sig, axis=1))
    gsigs = pd.cut(z[m], bins=[2, 3, 4, np.inf],
                   labels=["2s", "3s", "4s+"], right=False)
    ev["amp_sig"] = gsigs.astype(str)
    graw = pd.cut(r[m].abs(), bins=[0.10, 0.15, 0.20, np.inf],
                  labels=["10%", "15%", "20%+"], right=False)
    ev["amp_raw"] = graw.astype(str)
    # reversal at the 7D reference horizon for conditioning
    ev["rev_7d"] = ev["rev7"]
    ev["gb_7d"] = ev["gb7"]
    return ev


def _sig_rev_cols(ev: pd.DataFrame):
    return [f"rev{h}" for h in H], [f"gb{h}" for h in H], [f"t2rev{h}" for h in H]


def summarize_reversal(ev: pd.DataFrame, group_cols: list[str],
                       min_n: int = 30) -> pd.DataFrame:
    rows = []
    revcols, gbcols, t2rcols = _sig_rev_cols(ev)
    for keys, g in ev.groupby(group_cols, sort=False):
        n = int(len(g))
        if n < min_n:
            continue
        rr = g[revcols].mean().to_numpy()
        gb_med_all = g[gbcols].median().to_numpy()
        gb_med_give = []
        for c in gbcols:
            gg = g[g[c] > 1e-6][c]
            gb_med_give.append(gg.median() if len(gg) > 5 else np.nan)
        gb_p75 = g[gbcols].quantile(0.75).to_numpy()
        gb_p90 = g[gbcols].quantile(0.90).to_numpy()
        cont_med = []
        for h in H:
            c = f"fwd{h}_cum"
            gg = g[(np.sign(g[c]) == g["s"]) & (g[c].abs() > 0)]["ret_1d"]
            cont_med.append(np.nanmean((g[np.sign(g[c]) == g["s"]][c]
                                        if (np.sign(g[c]) == g["s"]).any()
                                        else pd.Series([np.nan]))))
        cont_med = [np.nanmean(g[np.sign(g[f"fwd{h}_cum"]) == g["s"]][f"fwd{h}_cum"])
                    if (np.sign(g[f"fwd{h}_cum"]) == g["s"]).any() else np.nan
                    for h in H]
        # fwd median (all events, sigma units at each horizon)
        fwd_med = [np.nanmedian(g[f"fwd{h}_sig"]) for h in H]
        # time-to-reversal: first h where rev true (min over t2r)
        t2col = [f"t2rev{h}" for h in H]
        t2rev_med = np.nanmedian(g[t2col].min(axis=1))
        t2ne_med = np.nanmedian(g[[f"t2ne{h}" for h in H]].min(axis=1))
        rec = {"n_events": n, "unique_assets": int(g["cmc_id"].nunique())}
        rec["horizon"] = H
        rec.update({f"p_rev_{h}d": float(rr[i]) for i, h in enumerate(H)})
        rec.update({f"gb_med_{h}d": float(gb_med_all[i]) for i, h in enumerate(H)})
        rec.update({f"gb_med_give_{h}d": gb_med_give[i] for i, h in enumerate(H)})
        rec.update({f"gb_p75_{h}d": float(gb_p75[i]) for i, h in enumerate(H)})
        rec.update({f"gb_p90_{h}d": float(gb_p90[i]) for i, h in enumerate(H)})
        rec.update({f"fwd_med_sig_{h}d": float(fwd_med[i]) for i, h in enumerate(H)})
        rec.update({f"cont_med_{h}d": float(cont_med[i]) for i, h in enumerate(H)})
        rec["mfe_sig_med"] = float(np.nanmedian(g["mfe_sig"]))
        rec["mae_sig_med"] = float(np.nanmedian(g["mae_sig"]))
        if len(keys) == len(group_cols):
            keys = list(keys)
        else:
            keys = list(keys) if isinstance(keys, tuple) else [keys]
        for kcol, kv in zip(group_cols, keys):
            rec[kcol] = kv
        # unpack horizon-specific separately for a long (melted) frame instead
        rows.append(rec)
    return pd.DataFrame(rows)


def manifold(ev: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for ampcol in ["amp_sig", "amp_raw"]:
        for sign in [1, -1]:
            sub = ev[ev["s"] == sign]
            if len(sub) == 0:
                continue
            for band in C.PRIMARY_BANDS:
                b = sub[sub["rank_band"] == band]
                # drop rows that did not actually qualify under this amplitude
                # lens (NaN bucket from the other gate) to avoid pollution
                bq = b[b[ampcol].notna()]
                g = bq.groupby(ampcol, sort=False)
                for amp, gg in g:
                    if len(gg) < 30:
                        continue
                    parts.append(pd.DataFrame([_manifold_row(gg, band, sign, amp)]))
    out = pd.concat(parts, ignore_index=True)
    return out


def _manifold_row(g: pd.DataFrame, band: str, sign: int, amp: str) -> dict:
    revcols = [f"rev{h}" for h in H]
    rr = g[revcols].mean().to_numpy()
    gb_all = g[[f"gb{h}" for h in H]].to_numpy()
    gb_all = np.where(np.isnan(gb_all), 0.0, gb_all)
    gb_med = g[[f"gb{h}" for h in H]].median().to_numpy()
    gb_p75 = g[[f"gb{h}" for h in H]].quantile(0.75).to_numpy()
    fwd_med = [np.nanmedian(g[f"fwd{h}_sig"]) for h in H]
    t2rev = np.nanmedian(g[[f"t2rev{h}" for h in H]].min(axis=1))
    t2ne = np.nanmedian(g[[f"t2ne{h}" for h in H]].min(axis=1))
    # continuation probability & median cont amplitude (sigma units)
    cont_prob, cont_amp = [], []
    for h in H:
        c = f"fwd{h}_cum"
        same = np.sign(g[c]) == g["s"]
        cont_prob.append(float((same & (g[c].abs() > 0)).mean()))
        if same.any():
            cont_amp.append(float(np.nanmedian(g.loc[same, f"fwd{h}_sig"])))
        else:
            cont_amp.append(np.nan)
    row = {
        "rank_band": band, "sign": "UP" if sign > 0 else "DOWN",
        "amplitude": str(amp), "n_events": int(len(g)),
        "unique_assets": int(g["cmc_id"].nunique()),
        "horizon": H,
    }
    for i, h in enumerate(H):
        row[f"p_rev_{h}d"] = float(rr[i])
        row[f"gb_med_{h}d"] = float(gb_med[i])
        row[f"gb_p75_{h}d"] = float(gb_p75[i])
        row[f"cont_prob_{h}d"] = cont_prob[i]
        row[f"cont_amp_{h}d"] = cont_amp[i]
        row[f"fwd_med_sig_{h}d"] = float(fwd_med[i])
    row["mfe_sig_med"] = float(np.nanmedian(g["mfe_sig"]))
    row["mae_sig_med"] = float(np.nanmedian(g["mae_sig"]))
    row["time_to_reversal_med"] = float(t2rev) if np.isfinite(t2rev) else np.nan
    row["time_to_new_extreme_med"] = float(t2ne) if np.isfinite(t2ne) else np.nan
    row["any_giveback_p"] = float((gb_all[:, 0] > 1e-6).mean())
    return row


def _melt_manifold(mm: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in mm.iterrows():
        for h in H:
            rows.append({
                "rank_band": r["rank_band"], "sign": r["sign"],
                "amplitude": r["amplitude"], "n_events": r["n_events"],
                "unique_assets": r["unique_assets"], "horizon": f"{h}D",
                "p_rev": r[f"p_rev_{h}d"], "gb_med": r[f"gb_med_{h}d"],
                "gb_p75": r[f"gb_p75_{h}d"], "cont_prob": r[f"cont_prob_{h}d"],
                "cont_amp_sig": r[f"cont_amp_{h}d"],
                "fwd_med_sig": r[f"fwd_med_sig_{h}d"],
            })
    return pd.DataFrame(rows)


def condition_map(ev: pd.DataFrame) -> pd.DataFrame:
    """Reversal (7D reference) conditioned on global/local/asset/pre-event state.
    Report P(rev7), median giveback7, n, among DOWN extremes (primary asymmetry)
    and UP extremes separately."""
    ev = ev.copy()
    ev["btc_dir"] = np.where((ev["btc_ret_1d"].isna()), "NA",
                             np.where(ev["btc_ret_1d"] > 0, "BTC_UP", "BTC_DOWN"))
    ev["vol_reg"] = np.where(ev["mkt_vol_30d"] > ev["mkt_vol_30d"].median(),
                             "VOL_HIGH", "VOL_LOW")
    ev["breadth_reg"] = np.where(
        ev["top500_breadth_30d"] > ev["top500_breadth_30d"].median(),
        "BRD_HIGH", "BRD_LOW")
    ev["eth_dir"] = np.where((ev["eth_ret_1d"].isna()), "NA",
                             np.where(ev["eth_ret_1d"] > 0, "ETH_STRONG", "ETH_WEAK"))
    ev["shmc"] = np.where(ev["momentum_state"] == "SHORT_HOT_MEDIUM_COLD",
                          "SHMC", "NON_SHMC")
    ev["age"] = pd.qcut(ev["listing_age_days"].rank(method="first"), 3,
                        labels=["YOUNG", "MID", "MATURE"]).astype("str") \
        if ev["listing_age_days"].notna().sum() > 30 else "NA"
    ev["volq"] = pd.qcut(ev["volume_24h_usd"].rank(method="first"), 4,
                         labels=["Q1", "Q2", "Q3", "Q4"]).astype("str") \
        if ev["volume_24h_usd"].notna().sum() > 30 else "NA"
    ev["stale"] = ev["flag_stale_price"].fillna(False).astype(bool)
    ev["zero_v"] = ev["flag_zero_volume"].fillna(False).astype(bool)

    conds = ["btc_dir", "vol_reg", "breadth_reg", "eth_dir", "shmc", "age",
             "volq", "stale", "zero_v"]
    rows = []
    for sign in [1, -1]:
        sub = ev[ev["s"] == sign]
        for band in C.PRIMARY_BANDS:
            b = sub[sub["rank_band"] == band]
            for cond in conds:
                for val, gg in b.groupby(cond, sort=False):
                    if len(gg) < 30:
                        continue
                    rows.append({
                        "rank_band": band, "sign": "UP" if sign > 0 else "DOWN",
                        "condition": cond, "value": str(val),
                        "n": int(len(gg)),
                        "p_rev_7d": float((gg["rev7"]).mean()),
                        "gb_med_7d": float(gg["gb7"].median()),
                        "gb_p75_7d": float(gg["gb7"].quantile(0.75)),
                        "fwd_med_sig_7d": float(np.nanmedian(gg["fwd7_sig"])),
                    })
    return pd.DataFrame(rows)


def purge_robustness(df: pd.DataFrame, ev: pd.DataFrame) -> pd.DataFrame:
    """Recompute headline reversal stats after overlap purging within bands."""
    # headline cells: band x sign, horizon 3/7/14, amplitude bucket 3s+
    ev3 = ev[ev["amp_sig"].isin(["3s", "4s+"])].copy()
    ev3 = ev3.sort_values("historical_date")
    rows = []
    for purge in [None] + C.PURGE_D:
        for band in C.PRIMARY_BANDS:
            b = ev3[ev3["rank_band"] == band]
            for sign in [1, -1]:
                g = b[(b["s"] == sign)].copy()
                n0 = len(g)
                if purge:
                    g = purge_by_asset(g, purge)
                nm = len(g)
                for h in [3, 7, 14]:
                    rows.append({
                        "purge_d": "RAW" if purge is None else f"{purge}D",
                        "rank_band": band,
                        "sign": "UP" if sign > 0 else "DOWN",
                        "n_raw": n0, "n_purged": nm,
                        "unique_assets": int(g["cmc_id"].nunique()),
                        "horizon": f"{h}D",
                        "p_rev": float(g[f"rev{h}"].mean()) if nm else np.nan,
                        "gb_med": float(g[f"gb{h}"].median()) if nm else np.nan,
                    })
    return pd.DataFrame(rows)


def purge_by_asset(g: pd.DataFrame, window: int) -> pd.DataFrame:
    """Greedy non-overlapping purge per asset: after taking an event day,
    skip the next `window` days for that asset (already band-sorted)."""
    g = g.sort_values(["cmc_id", "historical_date"])
    keep = []
    last = {}
    for cid in pd.unique(g["cmc_id"]):
        sub = g[g["cmc_id"] == cid]
        prev = None
        for _, row in sub.iterrows():
            d = row["historical_date"]
            if prev is None or (d - prev).days > window:
                keep.append(row.name)
                prev = d
    return g.loc[keep]


def continuous_surface(df: pd.DataFrame, width=100) -> pd.DataFrame:
    """PIT-rank rolling windows (width) -> P(rev) | UP/DOWN extreme at 7D,
    median giveback, n. Uses sigma>=3 gate population for clean extremes."""
    ev = df[(df["ret_1d"].abs() / df["sigma_t0"]) >= 3.0].copy()
    ev = ev[~ev["rank"].isna()]
    ev["s"] = np.sign(ev["ret_1d"])
    ev["rev7"] = (np.sign(ev["fwd7_cum"]) != ev["s"]) & ev["fwd7_cum"].notna() & (ev["ret_1d"].abs() > 0)
    ev["gb7"] = np.where((np.sign(ev["fwd7_cum"]) != ev["s"]),
                          np.clip(-ev["fwd7_cum"] / ev["ret_1d"], 0, 10), 0.0)
    lo, hi = 450, 2050
    ev["rank"] = ev["rank"].astype(int)
    rows = []
    for center in range(lo, hi + 1, width // 2):
        c0, c1 = center, center + width
        w = ev[(ev["rank"] >= c0) & (ev["rank"] < c1)]
        for sign in [1, -1]:
            g = w[w["s"] == sign]
            if len(g) < 30:
                continue
            rows.append({
                "rank_lo": c0, "rank_hi": c1 - 1, "width": width,
                "sign": "UP" if sign > 0 else "DOWN",
                "n": int(len(g)),
                "p_rev_7d": float(g["rev7"].mean()),
                "gb_med_7d": float(g["gb7"].median()),
                "gb_p75_7d": float(g["gb7"].quantile(0.75)),
            })
    return pd.DataFrame(rows)


def main():
    df = L.load()
    ev = event_frame(df)
    mm = _melt_manifold(manifold(ev))
    mm.to_csv(C.RESULTS / "05_REVERSAL_MANIFOLD.csv", index=False)

    cm = condition_map(ev)
    cm.to_csv(C.RESULTS / "06_REVERSAL_CONDITIONAL_MAP.csv", index=False)

    pur = purge_robustness(df, ev)
    pur.to_csv(C.RESULTS / "07_REVERSAL_PURGED_ROBUSTNESS.csv", index=False)

    # combine widths into one csv
    parts = []
    for width in [50, 100, 200]:
        parts.append(continuous_surface(df, width))
    srf = pd.concat(parts, ignore_index=True)
    srf.to_csv(C.RESULTS / "08_CONTINUOUS_RANK_REVERSAL_SURFACE.csv", index=False)

    print("event frame rows:", len(ev))
    for w in [50, 100, 200]:
        sub = srf[srf["width"] == w]
        print(f" width {w}: {len(sub)} cells")
    print("05 samples:")
    print(mm.groupby(["rank_band", "sign"])[["n_events"]].sum().to_string())


if __name__ == "__main__":
    main()