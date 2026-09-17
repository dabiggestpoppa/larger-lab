"""LOWER-FIELD-2 normalized-displacement lenses.

Outputs:
  09_NORMALIZED_DISPLACEMENT_LENSES.csv   per-lens x band P(>=k sigma) + amplitude quantiles
  10_SECTOR_DISPLACEMENT_ATLAS.csv        per-sector x band full displacement anatomy
  11_SECTOR_RESIDUAL_EFFECTS.csv          sector residual after controls

Displacement coordinate: z1 = |ret_1d| / sigma_t0 (continuous causal sigma).
Frame is built lean and mutated IN PLACE once, then reused by all three outputs
to bound memory (3.29M rows, ~44 source columns).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import lf2_common as C
import lf2_load as L

K_SIG = [1, 2, 3, 4]
KEEP = [
    "historical_date", "cmc_id", "rank", "rank_band", "ret_1d", "sigma_t0",
    "tags", "platform_chain", "volume_24h_usd", "log10_mcap", "mkt_vol_30d",
    "listing_age_days", "top500_breadth_30d", "btc_ret_1d", "eth_ret_1d",
    "fwd7_cum", "momentum_state", "num_market_pairs",
]


def _sector(s: pd.Series) -> pd.Series:
    return (s.fillna("").astype(str)
            .str.split("[,;]", regex=True).str[0]
            .str.strip().str.replace("-ecosystem", "", regex=False)
            .replace("", np.nan))


def prep() -> pd.DataFrame:
    d = pd.read_parquet(L.CACHE, columns=KEEP)   # read only lean columns
    d["z1"] = d["ret_1d"].abs() / d["sigma_t0"]
    d["sector"] = _sector(d["tags"])
    d["chain"] = d["platform_chain"].fillna("UNK")
    # vectorized date-wise quintiles
    for col, out in [("volume_24h_usd", "volq"), ("log10_mcap", "mcapq"),
                     ("mkt_vol_30d", "mvq")]:
        pr = d.groupby("historical_date", sort=False)[col].rank(pct=True)
        prv = (pr * 5).to_numpy(float)
        lab = np.full(len(d), np.nan, dtype=object)
        ok = np.isfinite(prv)
        lab[ok] = "Q" + np.clip(prv[ok].astype(int), 1, 5).astype(str)
        d[out] = lab
    # age tertiles
    apr = d["listing_age_days"].rank(pct=True)
    d["ageg"] = np.select([apr <= 1 / 3, apr <= 2 / 3], ["YOUNG", "MID"],
                          default="MATURE")
    d.loc[apr.isna(), "ageg"] = np.nan
    # band daily breadth / dispersion (mutating; original not reused)
    bb = d.groupby(["historical_date", "rank_band"], sort=False)["ret_1d"]
    d["band_pos_share"] = bb.transform("mean").gt(0).astype(int)
    d["band_disp"] = bb.transform(lambda s: s.std(ddof=1))
    # regimes (available-at-t)
    s = np.sign(d["ret_1d"])
    d["rev7"] = ((np.sign(d["fwd7_cum"]) != s) & d["fwd7_cum"].notna()
                 & (d["ret_1d"].abs() > 0))
    d["btc_dir"] = np.where(d["btc_ret_1d"] > 0, "BTC_UP", "BTC_DOWN")
    d["eth_dir"] = np.where(d["eth_ret_1d"] > 0, "ETH_STRONG", "ETH_WEAK")
    d["breadth_reg"] = np.where(
        d["top500_breadth_30d"] > d["top500_breadth_30d"].median(),
        "BRD_HIGH", "BRD_LOW")
    d["vol_reg"] = np.where(d["mkt_vol_30d"] > d["mkt_vol_30d"].median(),
                            "VOL_HIGH", "VOL_LOW")
    # drop heaviest original columns we no longer need
    d = d.drop(columns=["tags", "platform_chain", "btc_ret_1d", "eth_ret_1d",
                        "top500_breadth_30d", "num_market_pairs"])
    return d


def _band_baseline(d: pd.DataFrame) -> pd.Series:
    return (d["z1"] >= 3).groupby(d["rank_band"]).mean()


def _prob_row(lens, label, band, g):
    z = g["z1"].dropna()
    if len(z) < 200:
        return None
    row = {"lens": lens, "value": str(label), "rank_band": band, "n": int(len(z)),
           "n_assets": int(g["cmc_id"].nunique())}
    for k in K_SIG:
        row[f"p_ge{k}s"] = float((z >= k).mean())
    row["med_z"] = float(z.median())
    row["p90_z"] = float(z.quantile(0.90))
    row["p95_z"] = float(z.quantile(0.95))
    row["p99_z"] = float(z.quantile(0.99))
    return row


def lenses(d: pd.DataFrame) -> pd.DataFrame:
    bl = _band_baseline(d)
    rows = []
    for col, name in [("sector", "sector"), ("chain", "chain"), ("ageg", "age_group"),
                      ("volq", "liquidity_quintile"), ("mcapq", "mcap_quintile"),
                      ("mvq", "volatility_quintile"), ("btc_dir", "btc_regime"),
                      ("eth_dir", "eth_regime"), ("breadth_reg", "breadth_regime"),
                      ("vol_reg", "vol_regime")]:
        for band in C.PRIMARY_BANDS:
            b = d[d["rank_band"] == band]
            for label, g in b.groupby(col, dropna=False):
                r = _prob_row(name, label, band, g)
                if r:
                    rows.append(r)
    out = pd.DataFrame(rows)
    if len(out):
        from scipy.stats import norm
        out["baseline_ge3s"] = out["rank_band"].map(bl)
        diff = out["p_ge3s"] - out["baseline_ge3s"]
        se = np.sqrt(out["baseline_ge3s"] * (1 - out["baseline_ge3s"]) / out["n"])
        with np.errstate(divide="ignore", invalid="ignore"):
            zt = diff / se
            out["zstat"] = zt.round(3)
            out["pvalue"] = np.clip(2 * norm.sf(np.abs(zt)), 1e-300, 1.0)
            out.loc[se <= 0, ["zstat", "pvalue"]] = np.nan
        out["sig_bh5"] = C.bh_fdr(out["pvalue"].to_numpy())
        out["lift_ge3s"] = diff
    return out


def sector_atlas(d: pd.DataFrame) -> pd.DataFrame:
    bl = _band_baseline(d)
    rows = []
    for band in C.PRIMARY_BANDS:
        b = d[d["rank_band"] == band]
        for label, g in b.groupby("sector", dropna=False):
            z = g["z1"].dropna()
            if len(z) < 300 or g["cmc_id"].nunique() < 3:
                continue
            sig = g["sigma_t0"]
            up = g[g["ret_1d"] > 0]
            dn = g[g["ret_1d"] < 0]
            fwd = (g["fwd7_cum"] / sig).dropna()
            upz = (up["ret_1d"] / up["sigma_t0"]).dropna()
            dnz = (-dn["ret_1d"] / dn["sigma_t0"]).dropna()
            rows.append({
                "rank_band": band, "sector": str(label),
                "n_assets": int(g["cmc_id"].nunique()),
                "n_obs": int(len(g)),
                "n_events_ge3s": int((z >= 3).sum()),
                "p_ge3s": float((z >= 3).mean()),
                "baseline_band_ge3s": float(bl[band]),
                "lift_ge3s": float((z >= 3).mean() - bl[band]),
                "med_z": float(z.median()), "p95_z": float(z.quantile(0.95)),
                "up_med_z": float(upz.median()) if len(upz) else np.nan,
                "dn_med_z": float(dnz.median()) if len(dnz) else np.nan,
                "up_pge2s": float((upz >= 2).mean()) if len(upz) else np.nan,
                "dn_pge2s": float((dnz >= 2).mean()) if len(dnz) else np.nan,
                "rev7_p": float(g["rev7"].mean()) if g["rev7"].notna().any() else np.nan,
                "fwd7_med_sig": float(fwd.median()) if len(fwd) else np.nan,
                "momenta_mode": (g["momentum_state"].dropna().mode().iloc[0]
                                 if g["momentum_state"].dropna().size else np.nan),
            })
    return pd.DataFrame(rows)


def sector_residual(d: pd.DataFrame) -> pd.DataFrame:
    # mean-center WITHIN (band, volatility-quintile, age-group) cells so residuals
    # are zero-mean by construction. Median-centering a strongly right-skewed
    # ratio artifactually biases every sector's mean residual positive (mean>median);
    # mean-centering gives a genuine test of above-average displacement.
    d = d[d["z1"].notna()].copy()
    cell = d.groupby(["rank_band", "mvq", "ageg"], sort=False)["z1"].transform("mean")
    d["resid"] = d["z1"] - cell
    rows = []
    for lens in ["sector", "chain"]:
        for band in C.PRIMARY_BANDS:
            b = d[d["rank_band"] == band]
            grp = b.groupby(lens, dropna=True)["resid"]
            agg = pd.DataFrame({"n": grp.size(), "mean": grp.mean(),
                                "std": grp.std(ddof=1)}).reset_index()
            agg = agg[agg["n"] >= 300]
            if agg.empty:
                continue
            agg["lens"] = lens
            agg["rank_band"] = band
            agg["label"] = agg[lens]
            from scipy.stats import norm
            se = agg["std"] / np.sqrt(agg["n"])
            agg["tstat"] = agg["mean"] / se
            agg["pvalue"] = np.clip(2 * norm.sf(np.abs(agg["tstat"])), 1e-15, 1.0)
            rows.append(agg[["lens", "rank_band", "label", "n", "mean", "std",
                             "tstat", "pvalue"]])
    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if len(out):
        out["sig_bh5"] = C.bh_fdr(out["pvalue"].to_numpy())
    return out


def main():
    d = prep()
    ln = lenses(d).to_csv(C.RESULTS / "09_NORMALIZED_DISPLACEMENT_LENSES.csv",
                          index=False)
    sa = sector_atlas(d)
    sa.to_csv(C.RESULTS / "10_SECTOR_DISPLACEMENT_ATLAS.csv", index=False)
    sr = sector_residual(d)
    sr.to_csv(C.RESULTS / "11_SECTOR_RESIDUAL_EFFECTS.csv", index=False)
    print("09 rows", len(pd.read_csv(C.RESULTS / "09_NORMALIZED_DISPLACEMENT_LENSES.csv")),
          "| lenses:", sorted(pd.read_csv(C.RESULTS / "09_NORMALIZED_DISPLACEMENT_LENSES.csv")["lens"].unique()))
    print("10 rows", len(sa), "| sectors:", int(sa["sector"].nunique()))
    print("11 rows", len(sr), "| BH-sig:", int(sr["sig_bh5"].sum()) if len(sr) else 0)
    if len(sr):
        sig = sr[sr["sig_bh5"]].head(15)
        print(sig[["lens", "rank_band", "label", "n", "mean", "pvalue"]].to_string(index=False))


if __name__ == "__main__":
    main()