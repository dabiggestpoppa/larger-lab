"""LOWER-FIELD-2 TAIL-ACTIVATION STABILITY + SCALE ROBUSTNESS.

Outputs:
  12_TAIL_GRADIENT_ROLLING_STABILITY.csv   rolling/expanding window lift of SHMC state
  13_TAIL_GRADIENT_SCALE_ROBUSTNESS.csv    SHMC tail-state under alternate sigma scales

Tail state = SHORT_HOT_MEDIUM_COLD (ret_3d>0, ret_14d<=0), the LF1-flagged state.
Tail displacement = |fwd7_cum| normalized by a 7-day scale (1-day scale * sqrt(7),
horizon-matched). Alternate 1-day volatility estimates (20d/30d/63d realized,
EWMA, MAD, downside-semivol) are all causal.

Measure per band x state:
  P(|fwd7| > 1/2/3 7-d-sigma)
  P(up extreme fwd7 > 2 sigma), P(down extreme fwd7 < -2 sigma)  [direction split]
  lift vs band non-SHMC baseline, risk ratio, odds ratio, bootstrap 95% CI.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import lf2_common as C
import lf2_load as L

TAIL_STATE = "SHORT_HOT_MEDIUM_COLD"
K = [1, 2, 3]
SIGNAL_COLS = ["ret_1d", "historical_date", "cmc_id", "rank_band", "rank",
               "momentum_state", "fwd7_cum", "ret_3d", "ret_14d"]


def _scales7(df: pd.DataFrame) -> dict:
    """Per-asset causal 1-day scale (multiple defs) x sqrt(7), on full series."""
    out = {}
    for scale in ["20d", "30d", "63d", "ewma", "mad", "semivol"]:
        s = C.scale_sigma(df, scale, "ret_1d")
        out[scale] = (s * np.sqrt(7)).to_numpy(float)
    return out


def _stats(g: pd.DataFrame, z7: np.ndarray, k_list):
    z = z7
    row = {}
    for k in k_list:
        row[f"p_abs_gt{k}s"] = float((np.abs(z) >= k).mean())
    row["p_up_gt2s"] = float((z >= 2).mean())
    row["p_dn_gt2s"] = float((z <= -2).mean())
    row["med_fwd7_sig"] = float(np.nanmedian(z))
    row["n"] = int(len(g))
    return row


def base_stats(df: pd.DataFrame) -> pd.DataFrame:
    """12. rolling/expanding stability of SHMC tail lift vs non-SHMC baseline."""
    sig7 = _scales7(df)["63d"]          # primary scale for stability analysis
    df = df[SIGNAL_COLS].copy()
    df["z7"] = df["fwd7_cum"].to_numpy() / sig7
    df["is_shmc"] = (df["momentum_state"] == TAIL_STATE)
    df = df.sort_values("historical_date")
    dates = df["historical_date"]
    t = pd.to_datetime(dates)
    rows = []
    wins = [("365D", 365), ("730D", 730), ("expanding", None)]
    for wname, wdays in wins:
        for band in C.PRIMARY_BANDS:
            b = df[df["rank_band"] == band]
            if len(b) < 5000:
                continue
            base = b[~b["is_shmc"]]["z7"].dropna()
            sh = b[b["is_shmc"]]["z7"].dropna()
            tt = t.loc[b.index]
            if wdays is None:
                windows = [(tt.min(), tt.max())]
                lab = "expanding"
            else:
                wins = []
                for day in pd.date_range(start=tt.min(), end=tt.max(), freq="90D"):
                    w0 = day - pd.Timedelta(days=wdays)
                    wins.append((w0, day))
                windows = wins
            for (w0, w1) in windows:
                m = (tt >= w0) & (tt <= w1)
                sb = b[m]
                if sb.empty:
                    continue
                for st, zcol in [("nonSHMC", sb[~sb["is_shmc"]]["z7"]),
                                 ("SHMC", sb[sb["is_shmc"]]["z7"])]:
                    zz = zcol.dropna()
                    if len(zz) < 50:
                        continue
                    rows.append({
                        "window": lab if wdays is None else wname,
                        "win_start": str(w0.date()), "win_end": str(w1.date()),
                        "rank_band": band, "state": st,
                        "n": int(len(zz)),
                        **{f"p_abs_gt{k}s": float((np.abs(zz) >= k).mean())
                           for k in K},
                        "p_up_gt2s": float((zz >= 2).mean()),
                        "p_dn_gt2s": float((zz <= -2).mean()),
                        "med_fwd7_sig": float(zz.median()),
                    })
    return pd.DataFrame(rows)


def scale_robustness(df: pd.DataFrame) -> pd.DataFrame:
    """13. SHMC tail gradient under alternate 1-day scale definitions."""
    scales = _scales7(df)
    df = df[SIGNAL_COLS].copy()
    df["is_shmc"] = (df["momentum_state"] == TAIL_STATE)
    rows = []
    for scale, z7 in scales.items():
        fwd = df["fwd7_cum"].to_numpy(float)
        z7 = np.asarray(z7, dtype=float)
        dz = np.where(np.isfinite(z7) & np.isfinite(fwd) & (z7 > 0),
                      fwd / z7, np.nan)
        df["z7s"] = dz
        for band in C.PRIMARY_BANDS:
            b = df[df["rank_band"] == band]
            for st, zcol in [("NON_SHMC", b[~b["is_shmc"]]["z7s"]),
                             ("SHMC", b[b["is_shmc"]]["z7s"])]:
                zz = zcol.dropna()
                if len(zz) < 100:
                    continue
                base = b["z7s"].dropna()
                pb = (np.abs(base) >= 2).mean()
                pz = (np.abs(zz) >= 2).mean()
                pb3 = (np.abs(base) >= 3).mean()
                pz3 = (np.abs(zz) >= 3).mean()
                rows.append({
                    "scale": scale, "rank_band": band, "state": st,
                    "n": int(len(zz)),
                    "p_abs_gt1s": float((np.abs(zz) >= 1).mean()),
                    "p_abs_gt2s": float(pz),
                    "p_abs_gt3s": float(pz3),
                    "p_up_gt2s": float((zz >= 2).mean()),
                    "p_dn_gt2s": float((zz <= -2).mean()),
                    "bd_base_p_gt2s": float(pb), "bd_base_p_gt3s": float(pb3),
                    "lift_2s": float(pz - pb), "risk_ratio_2s": float(pz / pb if pb else np.nan),
                    "odds_2s": float((pz / (1 - pz) if 0 < pz < 1 else np.nan)),
                    "med_fwd7_sig": float(zz.median()),
                })
    return pd.DataFrame(rows)


def main():
    df = L.load()
    st = base_stats(df)
    st.to_csv(C.RESULTS / "12_TAIL_GRADIENT_ROLLING_STABILITY.csv", index=False)
    rr = scale_robustness(df)
    rr.to_csv(C.RESULTS / "13_TAIL_GRADIENT_SCALE_ROBUSTNESS.csv", index=False)
    print("12 rows", len(st))
    # highlight: 365D SHMC vs nonSHMC P(>2s) lift per band (latest window)
    s365 = st[(st["window"] == "365D") & (st["state"] == "SHMC")]
    print("\n== 365D SHMC P(>2s) by band (latest 365d) ==")
    for b in C.PRIMARY_BANDS:
        s = s365[(s365["rank_band"] == b)].sort_values("win_end").tail(1)
        if len(s):
            print(f"  {b}: P>2s={s['p_abs_gt2s'].iloc[0]:.3f} up={s['p_up_gt2s'].iloc[0]:.3f} "
                  f"dn={s['p_dn_gt2s'].iloc[0]:.3f} n={s['n'].iloc[0]}")
    print("\n== 13 scale robustness SHMC vs NON_SHMC P(>2s) per scale (5001-2000 empty check) ==")
    sh = rr[rr["state"] == "SHMC"]
    ns = rr[rr["state"] == "NON_SHMC"]
    pv = sh.merge(ns[["scale", "rank_band", "p_abs_gt2s"]],
                  on=["scale", "rank_band"], suffixes=("_shmc", "_base"))
    pv["lift"] = pv["p_abs_gt2s_shmc"] - pv["p_abs_gt2s_base"]
    for b in C.PRIMARY_BANDS:
        sub = pv[pv["rank_band"] == b][["scale", "p_abs_gt2s_shmc", "lift"]]
        print(f"  {b}:"); print(sub.to_string(index=False))


if __name__ == "__main__":
    main()