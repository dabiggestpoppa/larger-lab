"""LOWER-FIELD-1 — 12 CONDITIONAL_CHAIN_SECTOR.

Residual approach: for each asset-date, residual = ret_1d - (band x date median ret).
Under each earned regime (section 4), test each chain / sector's mean residual
non-zero with a one-sample t-test. BH-FDR 5% across the full grid.

Output: RESULTS/12_CONDITIONAL_CHAIN_SECTOR.csv
"""
import numpy as np
import pandas as pd

import lf1_common as C

REGIMES = {
    "BTC_UP": lambda d: d["btc_ret_1d"] > 0,
    "BTC_DOWN": lambda d: d["btc_ret_1d"] < 0,
    "VOL_HIGH": None,  # set below using mkt_vol_30d vs its median
    "ETH_STRONG": lambda d: d["eth_ret_1d"] > 0,
    "BREADTH_EXPANDING": lambda d: d["top500_breadth_30d"] > 0,
}


def bh_fdr(pvals):
    """Benjamini-Hochberg corrected; returns boolean significance at 5%."""
    p = np.asarray(pvals, dtype=float)
    m = len(p)
    order = np.argsort(np.argsort(p))  # ranks preserving ties
    ps = np.sort(p)
    ps = np.minimum.accumulate((ps * m) / np.arange(1, m + 1))[::-1][::-1]
    return (ps <= 0.05)[order]


def main():
    p = pd.read_parquet(C.PANEL)
    # residual vs band-date median, WINDSORIZED to +-5pp to kill spurious dead/spike artifacts
    med = p.groupby(["historical_date", "rank_band"], sort=False)["ret_1d"].transform("median")
    p["resid"] = (p["ret_1d"] - med).clip(-0.05, 0.05)

    # fill VOL_HIGH regime
    vmed = p["mkt_vol_30d"].median()
    REGIMES["VOL_HIGH"] = lambda d: d["mkt_vol_30d"] > vmed
    REGIMES["BREADTH_CONTRACTING"] = lambda d: d["top500_breadth_30d"] < 0

    # candidate labels: platform_chain and primary sector tag (split commas AND semicolons)
    tags_clean = p["tags"].fillna("").astype(str)
    p["sector"] = (
        tags_clean.str.split("[,;]", regex=True)
        .str[0].str.strip().str.replace("-ecosystem", "", regex=False)
    )

    rows = []
    for regime, cond in REGIMES.items():
        mask = cond(p)
        sub = p[mask]
        for lens, col in [("chain", "platform_chain"), ("sector", "sector")]:
            for band in C.PRIMARY_BANDS:
                b = sub[sub["rank_band"] == band]
                if b.empty or col not in b:
                    continue
                grp = b.groupby(col, dropna=False)["resid"]
                agg = pd.DataFrame({
                    "n": grp.size(),
                    "mean_resid": grp.mean(),
                    "std_resid": grp.std(ddof=1),
                }).reset_index()
                agg = agg[agg["n"] >= 200].copy()
                if agg.empty:
                    continue
                se = agg["std_resid"] / np.sqrt(agg["n"])
                t = agg["mean_resid"] / se
                from scipy.stats import norm
                pv = 2 * norm.sf(np.abs(t))
                agg["regime"] = regime
                agg["lens"] = lens
                agg["band"] = band
                agg["label"] = agg[col]
                agg["tstat"] = t.round(3)
                agg["pvalue"] = np.clip(pv, 1e-15, 1.0).round(6)
                agg["mean_resid"] = agg["mean_resid"].round(5)
                rows.append(agg[["regime", "lens", "band", "label", "n",
                                "mean_resid", "tstat", "pvalue"]])
    df = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    # BH-FDR across full grid
    if len(df):
        df["sig_bh5"] = bh_fdr(df["pvalue"].to_numpy())
        df["abs_mean_resid_pct"] = df["mean_resid"].abs()
        df.to_csv(C.RESULTS / "12_CONDITIONAL_CHAIN_SECTOR.csv", index=False)

        sig = df[df["sig_bh5"]] if len(df[df["sig_bh5"]]) else pd.DataFrame()
        print(f"=== 12 total cells {len(df)}, BH-significant {len(sig)} ===")
        if len(sig):
            top = sig.reindex(sig["abs_mean_resid_pct"].sort_values(ascending=False).index).head(20)
            print(top[["regime", "lens", "band", "label", "n", "mean_resid", "pvalue"]].to_string(index=False))
        else:
            print("NO BH-significant chain/sector pockets across any regime/band.")
    else:
        print("no cells")

    print("\nwrote 12_CONDITIONAL_CHAIN_SECTOR.csv")


def _erf(x):
    from math import erf
    return erf(x)


if __name__ == "__main__":
    main()