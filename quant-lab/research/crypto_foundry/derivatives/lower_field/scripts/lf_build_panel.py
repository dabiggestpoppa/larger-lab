#!/usr/bin/env python3
"""LF — build the point-in-time lower-field panel (ranks 501-2000).

Consumes: DATA_TRUTH/raw/lf_snapshot_*.json (collected from the canonical CMC
internal historical endpoint), the frozen canonical ALT-DATA-1.1 PIT universe
(ranks 1-500), canonical asset features V2 (realized vol), canonical market
terrain V2 (BTC/ETH returns, breadth, dispersion, dominance).

Outputs:
  RESULTS/lower_field_panel.parquet   — asset-dates ranks 501-2000, causal features
  DATA_TRUTH/lf_identity_map.parquet  — cmc_id -> name/symbol/slug history
  DATA_TRUTH/lf_parity_audit.csv      — same-fetch ranks 1-500 vs canonical panel
  DATA_TRUTH/lf_panel_summary.json    — coverage/flag summary for the docs

All features are causal (computed strictly from data at or before date t).
NaN is never backfilled.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "DATA_TRUTH" / "raw"
OUT = ROOT / "RESULTS"
OUT.mkdir(parents=True, exist_ok=True)

CR = Path(__file__).resolve().parent.parent.parent.parent / "alt_rotation"
CANON_UNIVERSE = CR / "data_1_1" / "ALT_DATA_1_1_PIT_UNIVERSE.parquet"
CANON_FEATURES = CR / "data_1_1" / "ALT_DATA_1_1_ASSET_MULTISCALE_FEATURES_V2.parquet"
CANON_TERRAIN = CR / "data_1_1" / "ALT_DATA_1_1_MARKET_TERRAIN_V2.parquet"

STABLE_TAGS = {"stablecoin", "stablecoin-asset-backed",
               "stablecoin-algorithmically-stabilized",
               "asset-backed-stablecoin", "usd-stablecoin",
               "algorithmic-stablecoin", "eur-stablecoin",
               "fiat-stablecoin", "stablecoin-protocol"}
STABLE_SYMS = {"USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP", "FDUSD",
               "USDE", "PYUSD", "GUSD", "LUSD", "FRAX", "USTC", "UST",
               "EURS", "USDD", "USD1"}

HORIZONS = [1, 3, 7, 14, 30, 60]
RANK_BANDS = [(1, 25), (26, 100), (101, 250), (251, 500),
              (501, 750), (751, 1000), (1001, 1500), (1501, 2000)]


def norm_symbol(s: str) -> str:
    return (s or "").strip().upper()


def band_of(rank: int) -> str:
    for lo, hi in RANK_BANDS:
        if lo <= rank <= hi:
            return f"{lo}-{hi}"
    return "OUT"


def parse_tags(tags) -> list[str]:
    if not tags:
        return []
    return [str(t).strip().lower() for t in tags if str(t).strip()]


import orjson

def load_raw_snapshots() -> pd.DataFrame:
    files = sorted(RAW.glob("lf_snapshot_*_r1_2000.json"))
    if not files:
        sys.exit("no raw snapshots found")
    rows = []
    short_dates = {}
    for i, f in enumerate(files):
        if i % 250 == 0:
            print(f"parsing file {i}/{len(files)}", flush=True)
        dt = f.name[12:20]  # lf_snapshot_YYYYMMDD_r1_2000.json
        try:
            data = orjson.loads(f.read_bytes())["data"]
        except Exception as e:  # noqa: BLE001
            print(f"WARN parse fail {f.name}: {e}", flush=True)
            continue
        if len(data) < 2000:
            short_dates[dt] = len(data)
        for r in data:
            q = (r.get("quotes") or [{}])[0]
            tags = parse_tags(r.get("tags"))
            plat = r.get("platform") or {}
            rows.append({
                "historical_date": pd.Timestamp(dt + "T23:59:59"),
                "cmc_id": int(r["id"]),
                "rank": int(r["cmcRank"]),
                "symbol": norm_symbol(r.get("symbol", "")),
                "name": r.get("name", ""),
                "slug": r.get("slug", ""),
                "price_usd": float(q.get("price") or np.nan),
                "market_cap_usd": float(q.get("marketCap") or np.nan),
                "volume_24h_usd": float(q.get("volume24h") or np.nan),
                "circulating_supply": float(r.get("circulatingSupply") or np.nan),
                "total_supply": float(r.get("totalSupply") or np.nan),
                "max_supply": float(r.get("maxSupply") or np.nan),
                "date_added_cmc": r.get("dateAdded", ""),
                "last_updated": r.get("lastUpdated", ""),
                "tags": ";".join(tags),
                "platform_chain": norm_symbol(plat.get("symbol", "")),
                "contract_address": (plat.get("token_address", "") or ""),
                "num_market_pairs": r.get("numMarketPairs"),
            })
    df = pd.DataFrame(rows)
    df["historical_date_key"] = df["historical_date"].dt.strftime("%Y-%m-%d")
    df["is_stablecoin"] = (
        df["tags"].apply(lambda t: any(s in t.split(";") for s in STABLE_TAGS))
        | df["symbol"].isin(STABLE_SYMS))
    print(f"parsed {len(df)} rows from {len(files)} snapshots; "
          f"short dates: {len(short_dates)}", flush=True)
    if short_dates:
        print("short dates (rows < 2000):", list(short_dates.items())[:10],
              flush=True)
    return df, short_dates


def parity_audit(raw_all: pd.DataFrame) -> pd.DataFrame:
    """Compare same-fetch rows ranks 1-500 against the frozen canonical panel."""
    can = pd.read_parquet(CANON_UNIVERSE,
                          columns=["historical_date", "cmc_id", "rank",
                                   "price_usd"])
    can["historical_date_key"] = can["historical_date"].dt.strftime("%Y-%m-%d")
    raw = raw_all[raw_all["rank"] <= 500].copy()
    raw = raw.rename(columns={"price_usd": "price_lf"})
    m = raw.merge(can[["historical_date_key", "cmc_id", "rank", "price_usd"]],
                  on=["historical_date_key", "cmc_id"], how="inner")
    m["price_diff_abs"] = (m["price_lf"] - m["price_usd"]).abs()
    m["price_rel"] = m["price_diff_abs"] / m["price_usd"].replace(0, np.nan)
    rows = []
    for dt, g in m.groupby("historical_date_key"):
        rows.append({
            "date": dt,
            "matched_ids": len(g),
            "price_identical": int((g["price_rel"] < 1e-9).sum()),
            "price_rel_lt_1pct": int((g["price_rel"] < 0.01).sum()),
            "max_price_rel_diff": float(g["price_rel"].max()),
            "n_canonical_500": int(can[can["historical_date_key"] == dt].shape[0]),
        })
    audit = pd.DataFrame(rows)
    return audit


def merge_canonical_series(df: pd.DataFrame) -> pd.DataFrame:
    """Extend per-asset price/rank series with the frozen canonical Top-500
    panel so features (returns, rank velocity) are continuous across the
    rank-500 boundary for assets that migrate in/out of the lower field."""
    can = pd.read_parquet(CANON_UNIVERSE,
                          columns=["historical_date", "cmc_id", "rank",
                                   "price_usd"])
    can["cmc_id"] = can["cmc_id"].astype(int)
    can["from_canonical"] = True
    mine = df[["historical_date", "cmc_id", "rank", "price_usd"]].copy()
    mine["from_canonical"] = False
    comb = pd.concat([can, mine], ignore_index=True)
    comb = comb.sort_values(["cmc_id", "historical_date"])
    # NOTE: no ffill. A missing (cmc_id, date) means the asset was not ranked
    # 1-2000 that day; shift-based features then yield NaN across the gap
    # (entry/re-entry artifact), which is documented rather than fabricated.
    # re-attach the enriched series to my panel rows (ranks 501-2000)
    out = df.merge(
        comb[["historical_date", "cmc_id", "rank", "price_usd"]] \
            .rename(columns={"rank": "rank_full", "price_usd": "price_full"}),
        on=["historical_date", "cmc_id"], how="left")
    # fall back to own values where no canonical extension exists
    out["rank"] = out["rank_full"].fillna(out["rank"]).astype(int)
    out["price_usd"] = out["price_full"].fillna(out["price_usd"])
    out = out.drop(columns=["rank_full", "price_full"])
    return out


def add_causal_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    g = df.groupby("cmc_id", sort=False)

    df["price_prev"] = g["price_usd"].shift(1)
    df["rank_prev"] = g["rank"].shift(1)
    df["vol_prev7_med"] = g["volume_24h_usd"].transform(
        lambda s: s.shift(1).rolling(7, min_periods=3).median())
    df["ret_1d"] = df["price_usd"] / df["price_prev"] - 1.0

    # multi-day returns: cumulative product of daily returns over the window,
    # computed in log space via cumsum diff (exact, vectorized per group).
    # Full observed window required (NaN propagates), matching the canonical
    # t / t-w presence rule; stricter than the 80% floor in the prereg and
    # documented as such in 04_PIT_UNIVERSE_AUDIT.md.
    ok = df["ret_1d"].notna() & (df["ret_1d"] > -1.0)
    logf = np.where(ok, np.log1p(df["ret_1d"].clip(lower=-0.9999)), np.nan)
    df["_logf"] = logf
    df["_cs"] = df.groupby("cmc_id", sort=False)["_logf"].cumsum()
    for w in HORIZONS:
        if w == 1:
            df["ret_1d_raw"] = df["ret_1d"]
            continue
        cs_shift = df.groupby("cmc_id")["_cs"].transform(
            lambda s: s.shift(w))
        df[f"ret_{w}d"] = np.expm1(df["_cs"] - cs_shift)
    df = df.drop(columns=["_logf", "_cs"])

    # rank velocity: rank(t-w) - rank(t); positive = improving
    for w in HORIZONS:
        df[f"rank_vel_{w}d"] = df.groupby("cmc_id")["rank"].transform(
            lambda s: s.shift(w) - s)

    # volume acceleration: vol(t) / median(vol t-1..t-7)
    df["vol_accel"] = df["volume_24h_usd"] / df["vol_prev7_med"].replace(0, np.nan)

    # listing age (days since CMC dateAdded); CMC timestamps are tz-aware
    df["date_added_cmc"] = pd.to_datetime(df["date_added_cmc"],
                                          errors="coerce", utc=True) \
        .dt.tz_localize(None)
    df["listing_age_days"] = (
        df["historical_date"] - df["date_added_cmc"]).dt.days

    # cross-sectional mcap quartile within date (log10)
    df["log10_mcap"] = np.log10(df["market_cap_usd"].clip(lower=1))
    df["mcap_q_within_date"] = df.groupby("historical_date")["log10_mcap"] \
        .transform(lambda s: pd.qcut(s, 4, labels=False,
                                     duplicates="drop"))
    return df


def add_global_context(df: pd.DataFrame) -> pd.DataFrame:
    # mkt_ret_1d: cap-weighted Top-500 1D return from canonical total mcap
    can = pd.read_parquet(CANON_UNIVERSE,
                          columns=["historical_date", "total_mcap"])
    can = can.drop_duplicates("historical_date").sort_values("historical_date")
    can["historical_date_key"] = can["historical_date"].dt.strftime("%Y-%m-%d")
    can["mkt_ret_1d"] = can["total_mcap"].pct_change()
    can["mkt_ret_1d"] = can["mkt_ret_1d"].where(
        can["mkt_ret_1d"].notna() & np.isfinite(can["mkt_ret_1d"]))
    mkt = can[["historical_date_key", "mkt_ret_1d"]]

    terr = pd.read_parquet(CANON_TERRAIN)
    terr["historical_date_key"] = terr["historical_date"].dt.strftime("%Y-%m-%d")
    terr_cols = ["historical_date_key", "btc_return_1d", "eth_return_1d",
                 "top500_breadth_30d", "top500_dispersion_30d",
                 "btc_dominance", "stablecoin_mcap_share",
                 "total_alt_share"]
    terr = terr[terr_cols].rename(columns={
        "btc_return_1d": "btc_ret_1d", "eth_return_1d": "eth_ret_1d"})

    feats = pd.read_parquet(CANON_FEATURES,
                            columns=["internal_asset_id", "historical_date",
                                     "realized_volatility_30d"])
    feats["historical_date_key"] = feats["historical_date"].dt.strftime("%Y-%m-%d")
    vol = feats.groupby("historical_date_key")["realized_volatility_30d"] \
        .median().rename("mkt_vol_30d").reset_index()

    df["historical_date_key"] = df["historical_date"].dt.strftime("%Y-%m-%d")
    df = df.merge(mkt, on="historical_date_key", how="left")
    df = df.merge(terr, on="historical_date_key", how="left")
    df = df.merge(vol, on="historical_date_key", how="left")

    # data-quality flags
    mkt_move = df["mkt_ret_1d"].abs() > 0.005
    df["flag_stale_price"] = ((df["price_usd"] == df["price_prev"]) & mkt_move)
    df["flag_zero_volume"] = (df["volume_24h_usd"].fillna(0) == 0)
    df["flag_missing_price"] = df["price_usd"].isna()
    df["flag_listing_day"] = df["listing_age_days"] <= 3
    df["flag_suspicious_volume"] = (
        (df["vol_accel"] > 10) & (df["ret_1d"].abs() < 0.001))
    df["flag_any_quality"] = (df["flag_stale_price"]
                              | df["flag_zero_volume"]
                              | df["flag_missing_price"]
                              | df["flag_listing_day"])
    return df


def main() -> int:
    raw_all, short_dates = load_raw_snapshots()
    audit = parity_audit(raw_all)
    audit.to_csv(ROOT / "DATA_TRUTH" / "lf_parity_audit.csv",
                 index=False)
    print("parity audit:", audit["price_rel_lt_1pct"].mean(),
          "avg pct rows within 1% of canonical", flush=True)

    lf = raw_all[(raw_all["rank"] >= 501) & (raw_all["rank"] <= 2000)].copy()
    lf["rank_band"] = lf["rank"].apply(band_of)
    lf = merge_canonical_series(lf)
    lf = add_causal_features(lf)
    lf = add_global_context(lf)

    lf = lf.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    lf.to_parquet(OUT / "lower_field_panel.parquet", index=False)

    # identity map
    ident = lf[["cmc_id", "name", "symbol", "slug"]].drop_duplicates("cmc_id")
    ident["n_dates_observed"] = lf.groupby("cmc_id").size().reindex(
        ident["cmc_id"]).values
    ident["first_date"] = lf.groupby("cmc_id")["historical_date"].min() \
        .reindex(ident["cmc_id"]).dt.strftime("%Y-%m-%d").values
    ident["last_date"] = lf.groupby("cmc_id")["historical_date"].max() \
        .reindex(ident["cmc_id"]).dt.strftime("%Y-%m-%d").values
    ident.to_parquet(ROOT / "DATA_TRUTH" / "lf_identity_map.parquet", index=False)

    summary = {
        "rows": int(len(lf)),
        "unique_assets": int(lf["cmc_id"].nunique()),
        "n_dates": int(lf["historical_date"].nunique()),
        "date_min": str(lf["historical_date"].min().date()),
        "date_max": str(lf["historical_date"].max().date()),
        "rank_min": int(lf["rank"].min()),
        "rank_max": int(lf["rank"].max()),
        "n_stablecoin_rows": int(lf["is_stablecoin"].sum()),
        "n_stale_rows": int(lf["flag_stale_price"].sum()),
        "n_zero_vol_rows": int(lf["flag_zero_volume"].sum()),
        "n_missing_price_rows": int(lf["flag_missing_price"].sum()),
        "n_listing_day_rows": int(lf["flag_listing_day"].sum()),
        "n_suspicious_vol_rows": int(lf["flag_suspicious_volume"].sum()),
        "coverage_price": float(lf["price_usd"].notna().mean()),
        "coverage_vol": float(lf["volume_24h_usd"].notna().mean()),
        "coverage_mcap": float(lf["market_cap_usd"].notna().mean()),
        "coverage_platform": float(lf["platform_chain"].ne("").mean()),
        "coverage_tags": float(lf["tags"].ne("").mean()),
        "coverage_date_added": float(lf["date_added_cmc"].notna().mean()),
        "short_dates": short_dates,
        "parity": {
            "n_dates": int(len(audit)),
            "mean_matched_ids": float(audit["matched_ids"].mean()),
            "mean_price_identical_pct": float(
                (audit["price_identical"] / audit["matched_ids"]).mean()),
            "mean_price_within_1pct_pct": float(
                (audit["price_rel_lt_1pct"] / audit["matched_ids"]).mean()),
        },
    }
    (ROOT / "DATA_TRUTH" / "lf_panel_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items()
                      if k != "short_dates"}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
