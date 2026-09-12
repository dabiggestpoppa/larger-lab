#!/usr/bin/env python3
"""ALT-DATA-1 — compute the numbers used by the quality/coverage/report
documents from the frozen parquet artifacts. Deterministic, no network.

Emits data_1/derived/report_numbers.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BANDS = [(1, 10), (11, 25), (26, 50), (51, 100), (101, 200), (201, 300),
         (301, 500)]
WINDOWS = [1, 3, 7, 14, 30, 60, 90]


def main() -> int:
    u = pd.read_parquet(ROOT / "ALT_DATA_1_PIT_UNIVERSE.parquet")
    f = pd.read_parquet(ROOT / "ALT_DATA_1_ASSET_MULTISCALE_FEATURES.parquet")
    e = pd.read_parquet(ROOT / "ALT_DATA_1_PERP_ELIGIBILITY.parquet")
    b = pd.read_parquet(ROOT / "ALT_DATA_1_RANK_BAND_FEATURES.parquet")
    s = pd.read_parquet(ROOT / "ALT_DATA_1_SECTOR_FEATURES.parquet")
    sm = pd.read_parquet(ROOT / "ALT_DATA_1_SECTOR_MEMBERSHIP.parquet")
    t = pd.read_parquet(ROOT / "ALT_DATA_1_MARKET_TERRAIN_FEATURES.parquet")
    i = pd.read_parquet(ROOT / "ALT_DATA_1_IDENTITY_MAP.parquet")
    sv = pd.read_parquet(ROOT / "ALT_DATA_1_SURVIVORSHIP.parquet")
    reg = json.loads((ROOT / "ALT_DATA_1_FEATURE_REGISTRY_HASH.json")
                     .read_text(encoding="utf-8"))

    out = {}
    out["date_range"] = [str(u["historical_date"].min().date()),
                         str(u["historical_date"].max().date())]
    out["n_dates"] = int(u["historical_date"].nunique())
    out["n_assets"] = int(u["cmc_id"].nunique())
    out["universe_rows"] = int(len(u))
    out["registry_hash"] = reg["feature_registry_sha256"]

    # feature coverage per window (fraction of rows with non-NaN)
    cov = {}
    for w in WINDOWS:
        cov[f"return_{w}d"] = float(f[f"return_{w}d"].notna().mean())
        cov[f"rank_change_{w}d"] = float(f[f"rank_change_{w}d"].notna().mean())
        cov[f"realized_volatility_{w}d"] = float(
            f[f"realized_volatility_{w}d"].notna().mean())
        cov[f"relative_return_vs_BTC_{w}d"] = float(
            f[f"relative_return_vs_BTC_{w}d"].notna().mean())
    out["feature_coverage"] = cov

    # eligibility
    out["eligibility_rows"] = int(len(e))
    out["eligibility_by_venue"] = {k: int(v) for k, v in
                                   e["venue"].value_counts().items()}
    out["eligibility_by_status"] = {k: int(v) for k, v in
                                    e["eligibility_status"]
                                    .value_counts().items()}
    out["mature_30d_rows"] = int(e["mature_30d_at_t"].sum())
    out["eligible_ex_liquidity_rows"] = int(
        (e["eligibility_status"] == "ELIGIBLE_EX_LIQUIDITY").sum())
    out["eligible_ex_liquidity_assets"] = int(
        e[e["eligibility_status"] == "ELIGIBLE_EX_LIQUIDITY"]
        ["cmc_id"].nunique())

    # unique asset-date eligibility by band (any venue, per date band)
    ex = e[e["eligibility_status"] == "ELIGIBLE_EX_LIQUIDITY"]
    ex_u = ex[["historical_date", "cmc_id", "rank"]].drop_duplicates(
        ["historical_date", "cmc_id"]).dropna(subset=["rank"])
    m = ex_u.copy()
    m["rank"] = m["rank"].astype(int)
    m["band"] = m["rank"].apply(
        lambda r: next((f"{lo}-{hi}" for lo, hi in BANDS
                        if lo <= r <= hi), "OUT"))
    by_band = m.groupby("band").size().to_dict()
    out["eligible_ex_liquidity_by_band"] = {k: int(v) for k, v in
                                            by_band.items()}
    out["eligible_ex_liquidity_by_band_frac"] = {
        k: round(v / (out["n_dates"] * (hi - lo + 1)), 4)
        for (lo, hi), (k, v) in zip(BANDS, by_band.items())}

    # sector
    out["sector_feature_rows"] = int(len(s))
    out["sector_membership_rows"] = int(len(sm))
    out["n_tags"] = int(sm["sector"].nunique())
    out["sector_mapped_asset_dates"] = int(len(sm))
    out["sector_statuses"] = sorted(set(s["sector_status"]))
    out["unmapped_asset_dates"] = int(
        len(u) - u["tags"].ne("").sum())
    out["sector_status_fraction"] = {
        "HISTORICAL_APPROXIMATION": float(u["tags"].ne("").mean()),
        "UNMAPPED": float(u["tags"].eq("").mean())}

    # band features
    out["band_feature_rows"] = int(len(b))
    out["band_counts_by_date_ok"] = bool(
        (b.groupby("historical_date")["member_count"].sum() == 500).all())

    # terrain
    out["terrain_rows"] = int(len(t))
    out["btc_dominance_range"] = [round(float(t["btc_dominance"].min()), 4),
                                  round(float(t["btc_dominance"].max()), 4)]
    out["stablecoin_share_range"] = [
        round(float(t["stablecoin_mcap_share"].min()), 4),
        round(float(t["stablecoin_mcap_share"].max()), 4)]

    # identity
    out["identity_rows"] = int(len(i))
    out["collision_classes"] = {k: int(v) for k, v in
                                Counter(i["collision_class"]).items()}
    out["cg_join_high"] = int((i["cg_join"] == "HIGH").sum())
    out["cp_join_high"] = int((i["cp_join"] == "HIGH").sum())

    # survivorship
    out["survivorship_rows"] = int(len(sv))
    out["n_exited_assets"] = int(sv["exited_top500"].sum())
    out["n_assets_still_present"] = int(
        sv["cmc_id"].nunique() - sv["exited_top500"].sum())

    # data quality metrics
    q = {}
    q["n_dates_with_500"] = int(u.groupby("historical_date")["rank"]
                                .nunique().eq(500).sum())
    q["duplicate_rank_dates"] = int(
        (u.groupby("historical_date")["rank"].nunique() != 500).sum())
    q["negative_volume_rows"] = int((u["volume_24h_usd"] < 0).sum())
    q["negative_price_rows"] = int((u["price_usd"] < 0).sum())
    q["missing_mcap_rows"] = int(u["market_cap_usd"].isna().sum())
    q["missing_volume_rows"] = int(u["volume_24h_usd"].isna().sum())
    q["rank_out_of_range"] = int(((u["rank"] < 1) | (u["rank"] > 500)).sum())
    q["mcap_share_sum_max_dev"] = float(
        np.abs(u.groupby("historical_date")["market_cap_share"].sum() - 1)
        .max())
    q["non_causal_columns_in_features"] = sorted(
        set(f.columns) & {"exited_top500", "days_until_exit"})
    out["quality"] = q

    # top decile/quartile membership persistence (context)
    out["top10_assets_present_all_dates"] = int(
        u[u["rank"] <= 10].groupby("cmc_id").size()
        .eq(out["n_dates"]).sum())

    (ROOT / "derived" / "report_numbers.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
