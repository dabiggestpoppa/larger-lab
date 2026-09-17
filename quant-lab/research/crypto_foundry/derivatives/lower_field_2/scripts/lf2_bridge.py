"""LOWER-FIELD-2 cross-field breadth bridge audit (17) + local sequence map (18).

17. Does Top-500 breadth (level / 7D velocity / 7D acceleration) predict
    lower-field normalized-tail share, delivery latency, cluster share and
    reversal -- controlling for BTC return, global vol, local vol, age, liquidity?
    Implemented as daily-panel OLS (per band). If breadth coefficients stay
    significant with the correct sign after controls -> retain PROMOTION_CANDIDATE;
    if they collapse to BTC/common factor -> demote.

18. Local sequence map: daily band-state table (dispersion regime, tail-day flag,
    breadth regime). Detect common 1->2->3-day state transitions (sequence atoms)
    that precede a tail-delivery day with >=50 effective days and >=3 subperiods.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import lf2_common as C
import lf2_load as L


def _daily_state(df: pd.DataFrame) -> pd.DataFrame:
    """Per (date, band): share of 2s+ moves, dispersion, median z1, tail share,
    cluster share, plus per-date market regressors (BTC, global vol, breadth)."""
    d = df.copy()
    s1 = d["sigma_t0"]
    z1 = d["ret_1d"].abs() / s1
    g = pd.DataFrame({
        "date": pd.to_datetime(d["historical_date"]),
        "band": d["rank_band"], "z1": z1, "ret": d["ret_1d"], "sig": s1,
    })
    # per-date breadth / vol / btc (from a single representative row: they are
    # date-constant in the panel)
    date_basic = d.groupby(pd.to_datetime(d["historical_date"])).agg(
        btc_ret=("btc_ret_1d", "last"), mkt_vol=("mkt_vol_30d", "last"),
        top500_breadth=("top500_breadth_30d", "last"))
    g = g.merge(date_basic, left_on="date", right_index=True, how="left")
    # lower-field breadth (ret>0 share) per band-date
    g["pos"] = (g["ret"] > 0).astype(int)
    band = g.groupby(["date", "band"]).agg(
        lo_positive_share=("pos", "mean"),
        lo_tail2_share=("z1", lambda s: (s >= 2).mean()),
        lo_tail3_share=("z1", lambda s: (s >= 3).mean()),
        lo_disp=("ret", lambda s: s.std(ddof=1)),
        lo_med_z1=("z1", "median"),
        n=("z1", "size")).reset_index()
    band["date"] = pd.to_datetime(band["date"])
    band = band.merge(date_basic, left_on="date", right_index=True, how="left")
    band = band.sort_values(["band", "date"])
    for w in [7]:
        for col in ["top500_breadth"]:
            band[f"{col}_vel{w}"] = band.groupby("band")[col].diff(w)
        band["top500_breadth_acc"] = band.groupby("band")["top500_breadth"].diff(w).diff(1)
    return band


def breadth_bridge(daily: pd.DataFrame) -> pd.DataFrame:
    """Daily-panel OLS per band: lower-field tail share vs breadth + controls."""
    import statsmodels.api as sm

    rows = []
    for yname, rowcol in [("lo_tail2_share", "tail2"), ("lo_tail3_share", "tail3")]:
        X = daily[["top500_breadth", "top500_breadth_vel7",
                   "mkt_vol", "btc_ret"]].copy()
        X["intercept"] = 1.0
        X = X[["intercept", "top500_breadth", "top500_breadth_vel7",
               "mkt_vol", "btc_ret"]]
        y = daily[rowcol] if False else daily[yname]
        for band in C.PRIMARY_BANDS:
            m = daily["band"] == band
            sub = daily[m].dropna(subset=[yname, "top500_breadth",
                                          "top500_breadth_vel7", "mkt_vol", "btc_ret"])
            if len(sub) < 200:
                continue
            try:
                Xb = sm.add_constant(sub[["top500_breadth", "top500_breadth_vel7",
                                          "mkt_vol", "btc_ret"]])
                res = sm.OLS(sub[yname], Xb).fit()
                rows.append({
                    "rank_band": band, "outcome": yname, "n_days": int(len(sub)),
                    "breadth_coef": float(res.params["top500_breadth"]),
                    "breadth_p": float(res.pvalues["top500_breadth"]),
                    "breadth_vel_coef": float(res.params["top500_breadth_vel7"]),
                    "breadth_vel_p": float(res.pvalues["top500_breadth_vel7"]),
                    "mkt_vol_coef": float(res.params["mkt_vol"]),
                    "btc_ret_coef": float(res.params["btc_ret"]),
                    "r2": float(res.rsquared),
                })
            except Exception as e:
                rows.append({"rank_band": band, "outcome": yname,
                             "error": str(e)})
    out = pd.DataFrame(rows)
    return out


def local_sequences(daily: pd.DataFrame, min_days=50, min_periods=3) -> pd.DataFrame:
    """18. band-state sequence atoms preceding tail-delivery days."""
    # build a daily ternary regime per band-date: dispersion high/low vs median
    daily = daily.sort_values(["band", "date"]).copy()
    daily["subperiod"] = daily["date"].dt.to_period("Q").astype(str)
    disp_med = daily.groupby("band")["lo_disp"].transform("median")
    daily["disp_regime"] = np.where(daily["lo_disp"] > disp_med, "DISP_HI", "DISP_LO")
    daily["br_regime"] = np.where(daily["top500_breadth"] > daily.groupby("band")["top500_breadth"].transform("median"),
                                  "BRD_HI", "BRD_LO")
    daily["tail_day"] = daily["lo_tail3_share"] > daily.groupby("band")["lo_tail3_share"].transform("median")
    # a "delivery" next-day event: tail share jumps tomorrow
    daily["deliver"] = daily.groupby("band")["lo_tail3_share"].shift(-1) > \
        daily.groupby("band")["lo_tail3_share"].transform("median")
    daily["seq"] = (daily["disp_regime"] + "|" + daily["br_regime"])
    # P(deliver | today's seq), and P(deliver | yesterday seq -> today seq) atoms
    rows = []
    for band in C.PRIMARY_BANDS:
        b = daily[daily["band"] == band].dropna(subset=["deliver", "seq"])
        if len(b) < min_days:
            continue
        for seq, g in b.groupby("seq"):
            if len(g) < min_days:
                continue
            sp = g.groupby("subperiod").size()
            if len(sp) < min_periods:
                continue
            base = b["deliver"].mean()
            lift = g["deliver"].mean() - base
            rows.append({
                "rank_band": band, "atoms": seq, "lag": 0, "n_days": int(len(g)),
                "n_subperiods": int(len(sp)), "p_deliver": float(g["deliver"].mean()),
                "base_p_deliver": float(base), "lift": float(lift),
            })
    # two-step atoms: P(deliver | state(t-1)=a & state(t)=b)
    for band in C.PRIMARY_BANDS:
        b = daily[daily["band"] == band].dropna(subset=["deliver", "seq"]).copy()
        if len(b) < min_days:
            continue
        prev = b.groupby("band")["seq"].shift(1)
        b["prev_seq"] = prev
        pair = b.dropna(subset=["prev_seq"])
        for pp, g in pair.groupby(["prev_seq", "seq"]):
            if len(g) < min_days:
                continue
            sp = g.groupby("subperiod").size()
            if len(sp) < min_periods:
                continue
            base = b["deliver"].mean()
            rows.append({
                "rank_band": band,
                "atoms": f"{pp[0]} -> {pp[1]}", "lag": 1,
                "n_days": int(len(g)), "n_subperiods": int(len(sp)),
                "p_deliver": float(g["deliver"].mean()), "base_p_deliver": float(base),
                "lift": float(g["deliver"].mean() - base),
            })
    out = pd.DataFrame(rows)
    return out


def main():
    df = L.load()
    daily = _daily_state(df)
    bb = breadth_bridge(daily)
    bb.to_csv(C.RESULTS / "17_BREADTH_BRIDGE_AUDIT.csv", index=False)
    ls = local_sequences(daily)
    ls.to_csv(C.RESULTS / "18_LOCAL_SEQUENCE_MAP.csv", index=False)
    print("== 17 breadth-bridge (tail-share outcome) ==")
    t = bb[bb["outcome"] == "lo_tail2_share"]
    print(t[["rank_band", "n_days", "breadth_coef", "breadth_p", "breadth_vel_coef",
             "breadth_vel_p", "mkt_vol_coef", "btc_ret_coef", "r2"]].to_string(index=False))
    print("\n== 18 local sequences: top lift (1-step) per band ==")
    top = ls[ls["lag"] == 0].sort_values("lift", ascending=False).groupby("rank_band").head(3)
    print(top[["rank_band", "atoms", "n_days", "n_subperiods", "p_deliver",
               "base_p_deliver", "lift"]].to_string(index=False))


if __name__ == "__main__":
    main()