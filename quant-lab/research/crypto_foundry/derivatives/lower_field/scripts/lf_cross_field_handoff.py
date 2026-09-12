#!/usr/bin/env python3
"""LF — Cross-Field Handoff Artifact (Task 9).

Creates daily PIT-safe lower-field state measures for each rank band:
  501-750, 751-1000, 1001-1500, 1501-2000

Measures per band per date:
  - median_ret: median 1d return
  - mean_ret: mean 1d return
  - breadth: fraction of assets with positive return
  - dispersion: IQR of returns
  - extreme_up_share: fraction with ret > P95
  - extreme_dn_share: fraction with ret < P5
  - tail_ratio: extreme_up / extreme_dn
  - short_hot_medium_cold_share: fraction in SHORT_HOT_MEDIUM_COLD state
  - rank_migration_7d: median rank velocity over 7d
  - vol_quality_share: fraction with non-zero volume
  - stale_share: fraction with stale prices
  - n_assets: number of assets in band

Output: RESULTS/30_CROSS_FIELD_HANDOFF_READY.parquet
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "RESULTS" / "lower_field_panel.parquet"
BANDS = ["501-750", "751-1000", "1001-1500", "1501-2000"]


def main() -> int:
    print("loading panel...", flush=True)
    lf = pd.read_parquet(PANEL, columns=[
        "historical_date", "historical_date_key", "cmc_id", "rank",
        "rank_band", "ret_1d", "ret_3d", "ret_14d",
        "mkt_ret_1d", "btc_ret_1d", "eth_ret_1d",
        "volume_24h_usd", "flag_stale_price", "flag_zero_volume",
        "is_stablecoin"])
    lf = lf.replace([np.inf, -np.inf], np.nan)
    lf = lf[~lf["is_stablecoin"].astype(bool)]
    lf = lf[lf["rank_band"].isin(BANDS)]
    lf = lf.sort_values(["historical_date_key", "rank_band", "cmc_id"])

    # Forward 7d return for SHORT_HOT_MEDIUM_COLD classification
    lf = lf.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    ok = lf["ret_1d"].notna() & (lf["ret_1d"] > -1.0)
    logf = np.where(ok, np.log1p(lf["ret_1d"].clip(lower=-0.9999)), np.nan)
    lf["_logf"] = logf
    lf["_cs"] = lf.groupby("cmc_id", sort=False)["_logf"].cumsum()
    cs_fwd7 = lf.groupby("cmc_id")["_cs"].transform(lambda s: s.shift(-7))
    lf["fwd_ret_7d"] = np.expm1(cs_fwd7 - lf["_cs"])
    lf = lf.drop(columns=["_logf", "_cs"])

    # Rank velocity 7d
    lf["rank_vel_7d"] = lf.groupby("cmc_id")["rank"].transform(
        lambda s: s.shift(7) - s)

    # Momentum shape states
    lf["short_hot"] = (lf["ret_3d"] > 0).astype(float)
    lf["med_hot"] = (lf["ret_14d"] > 0).astype(float)
    lf["is_sh_mc"] = ((lf["short_hot"] == 1) & (lf["med_hot"] == 0)).astype(float)

    rows = []
    for dt, gdate in lf.groupby("historical_date_key"):
        for band in BANDS:
            bg = gdate[gdate["rank_band"] == band]
            if len(bg) < 10:
                continue
            r = bg["ret_1d"].dropna()
            rows.append({
                "date": dt,
                "rank_band": band,
                "n_assets": int(len(bg)),
                "median_ret": float(r.median()) if len(r) else np.nan,
                "mean_ret": float(r.mean()) if len(r) else np.nan,
                "breadth": float((r > 0).mean()) if len(r) else np.nan,
                "dispersion": float(r.quantile(0.75) - r.quantile(0.25)) if len(r) else np.nan,
                "extreme_up_share": float((r > r.quantile(0.95)).mean()) if len(r) > 20 else np.nan,
                "extreme_dn_share": float((r < r.quantile(0.05)).mean()) if len(r) > 20 else np.nan,
                "tail_ratio": (float((r > r.quantile(0.95)).mean()) /
                               max(float((r < r.quantile(0.05)).mean()), 1e-9))
                    if len(r) > 20 else np.nan,
                "short_hot_medium_cold_share": float(bg["is_sh_mc"].mean()),
                "rank_migration_7d": float(bg["rank_vel_7d"].median()),
                "vol_quality_share": float((bg["volume_24h_usd"].fillna(0) > 0).mean()),
                "stale_share": float(bg["flag_stale_price"].mean()),
                "mkt_ret_1d": float(bg["mkt_ret_1d"].iloc[0]) if bg["mkt_ret_1d"].notna().any() else np.nan,
                "btc_ret_1d": float(bg["btc_ret_1d"].iloc[0]) if bg["btc_ret_1d"].notna().any() else np.nan,
                "eth_ret_1d": float(bg["eth_ret_1d"].iloc[0]) if bg["eth_ret_1d"].notna().any() else np.nan,
            })

    df = pd.DataFrame(rows)
    df = df.sort_values(["date", "rank_band"]).reset_index(drop=True)
    df.to_parquet(ROOT / "RESULTS" / "30_CROSS_FIELD_HANDOFF_READY.parquet", index=False)
    print(f"handoff artifact: {len(df)} rows, {df['date'].nunique()} dates, "
          f"{df['rank_band'].nunique()} bands", flush=True)
    print(df.head(20).to_string(), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
