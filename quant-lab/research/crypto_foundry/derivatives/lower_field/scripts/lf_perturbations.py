#!/usr/bin/env python3
"""LF — perturbation suite (prereg P1-P6) applied to the headline rank-elasticity
and asymmetry results.

  P1 impulse substitution  mkt_ret_1d -> btc_ret_1d
  P2 stablecoin inclusion  elasticity with stablecoins INCLUDED
  P3 stale exclusion       elasticity excluding stale_price rows
  P4 subperiod split       elasticity by year block (2020-21, 2022, 2023, 2024, 2025-26)
  P5 index form            equal-weighted vs cap-weighted market impulse
  P6 truncation            recompute on data before 2025-01-01

Output: RESULTS/20a_PERTURBATION_SUITE.csv
"""
from __future__ import annotations

import gc
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "RESULTS" / "lower_field_panel.parquet"
CR = Path(__file__).resolve().parent.parent.parent.parent / "alt_rotation"
CANON_UNIVERSE = CR / "data_1_1" / "ALT_DATA_1_1_PIT_UNIVERSE.parquet"

BANDS = ["1-25", "26-100", "101-250", "251-500", "501-750", "751-1000",
         "1001-1500", "1501-2000"]
CANON_BANDS = {"1-25", "26-100", "101-250", "251-500"}
RANK_BANDS = [(1, 25), (26, 100), (101, 250), (251, 500),
              (501, 750), (751, 1000), (1001, 1500), (1501, 2000)]


def band_of(rank: int) -> str:
    for lo, hi in RANK_BANDS:
        if lo <= rank <= hi:
            return f"{lo}-{hi}"
    return "OUT"


def load_combined() -> pd.DataFrame:
    """Load lower-field panel + canonical Top-500, return slim combined df."""
    # Lower-field panel — only columns we need
    lf = pd.read_parquet(PANEL, columns=[
        "historical_date", "cmc_id", "rank", "rank_band", "ret_1d",
        "mkt_ret_1d", "btc_ret_1d", "is_stablecoin", "flag_stale_price",
        "historical_date_key"])
    lf = lf.replace([np.inf, -np.inf], np.nan)

    # Canonical Top-500
    can = pd.read_parquet(CANON_UNIVERSE, columns=[
        "historical_date", "cmc_id", "rank", "price_usd", "is_stablecoin"])
    can = can[can["rank"] <= 500].copy()
    can["cmc_id"] = can["cmc_id"].astype(int)
    can["rank_band"] = can["rank"].apply(band_of)
    can = can[can["rank_band"].isin(CANON_BANDS)].copy()
    can = can.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    g = can.groupby("cmc_id", sort=False)
    can["ret_1d"] = can["price_usd"] / g["price_usd"].shift(1) - 1.0
    can["ret_1d"] = can["ret_1d"].replace([np.inf, -np.inf], np.nan)

    # Global context from canonical
    tot = pd.read_parquet(CANON_UNIVERSE,
                          columns=["historical_date", "total_mcap"]) \
        .drop_duplicates("historical_date").sort_values("historical_date")
    tot["historical_date_key"] = tot["historical_date"].dt.strftime("%Y-%m-%d")
    tot["mkt_ret_1d"] = tot["total_mcap"].pct_change()

    can["historical_date_key"] = can["historical_date"].dt.strftime("%Y-%m-%d")
    can = can.merge(tot[["historical_date_key", "mkt_ret_1d"]],
                    on="historical_date_key", how="left")
    # btc_ret_1d from terrain
    terr = pd.read_parquet(CR / "data_1_1" / "ALT_DATA_1_1_MARKET_TERRAIN_V2.parquet",
                           columns=["historical_date", "btc_return_1d"])
    terr["historical_date_key"] = terr["historical_date"].dt.strftime("%Y-%m-%d")
    can = can.merge(terr[["historical_date_key", "btc_return_1d"]].rename(
        columns={"btc_return_1d": "btc_ret_1d"}),
        on="historical_date_key", how="left")
    can["flag_stale_price"] = False

    cols = ["historical_date", "historical_date_key", "cmc_id", "rank",
            "rank_band", "ret_1d", "mkt_ret_1d", "btc_ret_1d",
            "is_stablecoin", "flag_stale_price"]
    comb = pd.concat([lf[cols], can[cols]], ignore_index=True)
    comb = comb.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    del lf, can, tot, terr
    gc.collect()
    return comb


def median_ret_by_band(df, imp_col, classes):
    out = []
    for band in BANDS:
        bd = df[df["rank_band"] == band]
        for cl in classes:
            sub = bd[bd[imp_col] == cl]
            r = sub["ret_1d"].dropna()
            out.append({"rank_band": band, "impulse": cl,
                        "n_asset_days": int(len(r)), "n_days": int(sub["historical_date_key"].nunique()),
                        "median": float(r.median()) if len(r) else np.nan,
                        "mean": float(r.mean()) if len(r) else np.nan})
    return pd.DataFrame(out)


def classify(s, q10, q40, q60, q90):
    out = pd.Series("ALL", index=s.index)
    out[s >= q90] = "POSITIVE_MARKET"
    out[s <= q10] = "NEGATIVE_MARKET"
    out[(s >= q40) & (s <= q60)] = "CALM"
    return out


def main() -> int:
    comb = load_combined()

    # Equal-weighted market index (from canonical panel)
    eq = comb.groupby("historical_date_key")["ret_1d"].mean().rename(
        "mkt_eq_ret_1d").reset_index()
    comb = comb.merge(eq, on="historical_date_key", how="left")

    out = []
    # ---- baseline (cap-weighted) ----
    base = comb[~comb["is_stablecoin"].astype(bool)].copy()
    mkt = base["mkt_ret_1d"].dropna()
    q10, q40, q60, q90 = np.percentile(mkt, [10, 40, 60, 90])
    base["imp"] = classify(base["mkt_ret_1d"], q10, q40, q60, q90)
    r0 = median_ret_by_band(base, "imp", ["POSITIVE_MARKET", "NEGATIVE_MARKET"])
    r0["perturbation"] = "P0_BASELINE_CAPW"
    out.append(r0)
    print("P0 done", flush=True)

    # ---- P1: BTC impulse ----
    p1 = base.dropna(subset=["btc_ret_1d"])
    bq = np.percentile(p1["btc_ret_1d"], [10, 40, 60, 90])
    p1 = p1.copy()
    p1["imp"] = classify(p1["btc_ret_1d"], *bq)
    r1 = median_ret_by_band(p1, "imp", ["POSITIVE_MARKET", "NEGATIVE_MARKET"])
    r1["perturbation"] = "P1_BTC_IMPULSE"
    out.append(r1)
    del p1
    gc.collect()
    print("P1 done", flush=True)

    # ---- P2: stablecoin inclusion ----
    p2 = comb.copy()
    p2["imp"] = classify(p2["mkt_ret_1d"], q10, q40, q60, q90)
    r2 = median_ret_by_band(p2, "imp", ["POSITIVE_MARKET", "NEGATIVE_MARKET"])
    r2["perturbation"] = "P2_STABLES_INCLUDED"
    out.append(r2)
    del p2
    gc.collect()
    print("P2 done", flush=True)

    # ---- P3: stale exclusion ----
    p3 = base[~base["flag_stale_price"]].copy()
    p3["imp"] = classify(p3["mkt_ret_1d"], q10, q40, q60, q90)
    r3 = median_ret_by_band(p3, "imp", ["POSITIVE_MARKET", "NEGATIVE_MARKET"])
    r3["perturbation"] = "P3_STALE_EXCLUDED"
    out.append(r3)
    del p3
    gc.collect()
    print("P3 done", flush=True)

    # ---- P4: subperiod split ----
    base["year_block"] = pd.cut(base["historical_date"].dt.year,
                                bins=[2019, 2021, 2022, 2023, 2024, 2027],
                                labels=["2020-21", "2022", "2023", "2024",
                                        "2025-26"])
    for blk in ["2020-21", "2022", "2023", "2024", "2025-26"]:
        sb = base[base["year_block"] == blk].copy()
        sbq = np.percentile(sb["mkt_ret_1d"].dropna(), [10, 40, 60, 90])
        sb["imp"] = classify(sb["mkt_ret_1d"], *sbq)
        r4 = median_ret_by_band(sb, "imp",
                                ["POSITIVE_MARKET", "NEGATIVE_MARKET"])
        r4["perturbation"] = f"P4_SUBPERIOD_{blk}"
        out.append(r4)
    del base
    gc.collect()
    print("P4 done", flush=True)

    # ---- P5: equal-weighted index ----
    p5 = comb.dropna(subset=["mkt_eq_ret_1d"]).copy()
    p5 = p5[~p5["is_stablecoin"].astype(bool)]
    eqq = np.percentile(p5["mkt_eq_ret_1d"], [10, 40, 60, 90])
    p5["imp"] = classify(p5["mkt_eq_ret_1d"], *eqq)
    r5 = median_ret_by_band(p5, "imp", ["POSITIVE_MARKET", "NEGATIVE_MARKET"])
    r5["perturbation"] = "P5_EQW_IMPULSE"
    out.append(r5)
    del p5
    gc.collect()
    print("P5 done", flush=True)

    # ---- P6: truncation before 2025-01-01 ----
    p6 = comb[comb["historical_date"] < "2025-01-01"].copy()
    p6 = p6[~p6["is_stablecoin"].astype(bool)]
    p6q = np.percentile(p6["mkt_ret_1d"].dropna(), [10, 40, 60, 90])
    p6["imp"] = classify(p6["mkt_ret_1d"], *p6q)
    r6 = median_ret_by_band(p6, "imp", ["POSITIVE_MARKET", "NEGATIVE_MARKET"])
    r6["perturbation"] = "P6_TRUNCATED_PRE2025"
    out.append(r6)
    print("P6 done", flush=True)

    res = pd.concat(out, ignore_index=True)
    res.to_csv(ROOT / "RESULTS" / "20a_PERTURBATION_SUITE.csv", index=False)
    print("\nperturbations done:", res.shape)
    print(res[res["impulse"] == "POSITIVE_MARKET"]
          .pivot(index="rank_band", columns="perturbation",
                 values="median").round(4).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
