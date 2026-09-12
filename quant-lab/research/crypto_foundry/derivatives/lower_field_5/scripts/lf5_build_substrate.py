"""LOWER-FIELD-5 STAGE A — canonical PIT asset-date substrate.

Rebuilds the PIT peer-history substrate from the RAW top-2000 snapshots
(ranks 1-2000, 2020-06-01 .. 2026-08-23) instead of the band-truncated LF2
cache. All rolling/state features are computed on continuous per-asset
histories BEFORE any rank-band filtering. This is the infrastructure fix that
unblocks correlation peers, future rank-health clocks, and comparison-band
(26-500) research.

Memory-conscious: snapshots are parsed in batches, downcast aggressively, and
only the columns the research actually consumes are retained.

Outputs:
  cache/pit_raw_panel.parquet       parsed snapshot rows (lean identity+mkt)
  04_PIT_ASSET_DATE_FEATURES.parquet full PIT feature substrate (all ranks)
  PIT_RETURNS_LONG.parquet          long (date, cmc_id, ret_1d) with flags
  cache/pit_returns_wide.parquet    dates x cmc_id float32 matrix (NaN=missing)
  cache/lf5_identity_map.parquet    cmc_id -> symbol history
  05_RETURN_MATRIX_METADATA.md      schema/coverage/missingness documentation
"""
from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

import lf5_common as C

RAW = C.RAW
OUT = C.ROOT
BATCH = 150


def norm_symbol(s: str) -> str:
    return (s or "").strip().upper()


def _stable(tags, sym) -> bool:
    if sym in C.STABLE_SYMS:
        return True
    if not tags:
        return False
    return any(t in C.STABLE_TAGS for t in tags)


def load_raw_snapshots() -> pd.DataFrame:
    """Parse daily top-2000 snapshots into shard parquets, then load the panel.

    Each batch becomes its own parquet shard so no giant in-RAM concat is ever
    needed; the final panel is assembled on disk via pyarrow.
    """
    import orjson
    import pyarrow as pa
    import pyarrow.parquet as pq
    files = sorted(RAW.glob("lf_snapshot_*_r1_2000.json"))
    if not files:
        sys.exit("no raw snapshots found")
    shard_dir = C.CACHE / "shards"
    shard_dir.mkdir(exist_ok=True)
    short_dates = {}
    t0 = time.time()
    n = len(files)
    cols = ["_dkey", "cmc_id", "rank", "symbol", "price_usd",
            "market_cap_usd", "volume_24h_usd", "date_added_cmc",
            "is_stablecoin"]
    for shard_i, start in enumerate(range(0, n, BATCH)):
        rows = []
        for f in files[start:start + BATCH]:
            dt = f.name[12:20]
            try:
                data = orjson.loads(f.read_bytes())["data"]
            except Exception as e:  # noqa: BLE001
                print(f"WARN parse fail {f.name}: {e}", flush=True)
                continue
            if len(data) < 2000:
                short_dates[dt] = len(data)
            for r in data:
                q = (r.get("quotes") or [{}])[0]
                sym = norm_symbol(r.get("symbol", ""))
                tags = r.get("tags") or []
                rows.append((
                    int(dt), int(r["id"]), int(r["cmcRank"]), sym,
                    float(q.get("price") or np.nan),
                    float(q.get("marketCap") or np.nan),
                    float(q.get("volume24h") or np.nan),
                    (r.get("dateAdded") or "")[:10],
                    _stable(tags, sym),
                ))
        arr = [pa.array([r[i] for r in rows]) for i in range(len(cols))]
        t = pa.table(dict(zip(cols, arr)))
        pq.write_table(t, shard_dir / f"shard_{shard_i:03d}.parquet",
                       compression="zstd")
        del rows, arr, t
        if shard_i % 5 == 0:
            print(f"parsed {min(start + BATCH, n) * 2000:,}/{n * 2000:,} rows "
                  f"elapsed {time.time() - t0:.0f}s", flush=True)
    # Assemble on disk (memory-mapped, no giant concat).
    tables = [pq.read_table(shard_dir / f"shard_{i:03d}.parquet")
              for i in range((n + BATCH - 1) // BATCH)]
    all_t = pa.concat_tables(tables)
    df = all_t.to_pandas(split_blocks=True, self_destruct=True)
    df["historical_date"] = pd.to_datetime(df["_dkey"].astype(str), format="%Y%m%d") \
        + pd.Timedelta(hours=23, minutes=59, seconds=59)
    df = df.drop(columns=["_dkey"])
    df["date_added_cmc"] = pd.to_datetime(df["date_added_cmc"], errors="coerce")
    for c in ["cmc_id", "rank"]:
        df[c] = df[c].astype(np.int32)
    df["symbol"] = df["symbol"].astype("category")
    print(f"parsed {len(df):,} rows from {len(files)} snapshots in "
          f"{time.time() - t0:.0f}s; short dates: {len(short_dates)}", flush=True)
    if short_dates:
        print("short dates:", list(short_dates.items())[:10], flush=True)
    return df


def _grp(df, col="cmc_id"):
    return df.groupby(col, sort=False)


def add_causal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Continuous per-asset features BEFORE any band filtering."""
    df = df.sort_values(["cmc_id", "historical_date"], kind="stable").reset_index(drop=True)
    g = _grp(df)

    df["price_prev"] = g["price_usd"].shift(1)
    df["rank_prev"] = g["rank"].shift(1)
    df["vol_prev7_med"] = g["volume_24h_usd"].shift(1) \
        .groupby(df["cmc_id"], sort=False).rolling(7, min_periods=3).median() \
        .reset_index(level=0, drop=True)
    df["ret_1d"] = df["price_usd"] / df["price_prev"] - 1.0
    df["ret_1d_raw"] = df["ret_1d"]

    ok = df["ret_1d"].notna() & (df["ret_1d"] > -1.0)
    logf = pd.Series(np.where(ok, np.log1p(df["ret_1d"].clip(lower=-0.9999)), np.nan),
                     index=df.index)
    cs = logf.groupby(df["cmc_id"], sort=False).cumsum()
    for w in C.RET_H:
        if w == 1:
            continue
        cs_shift = cs.groupby(df["cmc_id"], sort=False).shift(w)
        df[f"ret_{w}d"] = np.expm1(cs - cs_shift)

    for scale in ["63d", "30d", "20d"]:
        win = {"63d": 63, "30d": 30, "20d": 20}[scale]
        minp = min(max(win // 2, 15), win)
        s = g["ret_1d"].shift(1)
        df[f"vol_{scale}"] = s.groupby(df["cmc_id"], sort=False) \
            .rolling(win, min_periods=minp).std().reset_index(level=0, drop=True)
    s = g["ret_1d"].shift(1)
    df["vol_ewma"] = s.groupby(df["cmc_id"], sort=False) \
        .ewm(span=20, adjust=False, min_periods=20).std() \
        .reset_index(level=0, drop=True)
    df["sigma_t0"] = df["vol_63d"]

    for w in C.RANK_H:
        df[f"rank_vel_{w}d"] = g["rank"].transform(lambda s: s.shift(w) - s)

    df["vol_accel"] = df["volume_24h_usd"] / df["vol_prev7_med"].replace(0, np.nan)
    df["turnover"] = df["volume_24h_usd"] / df["market_cap_usd"].replace(0, np.nan)
    # Listing age (causal; CMC dateAdded is a LIVE attribute in historical
    # snapshots and can postdate observations or change over time, so we take
    # the earliest observed listing date per asset as the canonical birth date;
    # rows before that date get NaN age instead of a fabricated negative).
    first_added = df.groupby("cmc_id", sort=False)["date_added_cmc"] \
        .transform("min")
    df["date_added_cmc"] = first_added
    df["listing_age_days"] = (df["historical_date"] - df["date_added_cmc"]).dt.days
    df.loc[df["listing_age_days"] < 0, "listing_age_days"] = np.nan

    df["log10_mcap"] = np.log10(df["market_cap_usd"].clip(lower=1))
    df["log10_vol"] = np.log10(df["volume_24h_usd"].clip(lower=1))
    df["liq_proxy"] = np.log10(df["market_cap_usd"].clip(lower=1)
                               * np.sqrt(df["volume_24h_usd"].clip(lower=1)))

    # Cross-sectional ranks within date (fast: per-date sort-based ranking).
    df["vol_pct_within_date"] = df.groupby("historical_date")["volume_24h_usd"] \
        .rank(pct=True)
    df["mcap_q_within_date"] = df.groupby("historical_date")["log10_mcap"] \
        .transform(lambda s: pd.qcut(s, 4, labels=False, duplicates="drop"))
    df["vol_regime"] = np.where(df.groupby("historical_date")["vol_63d"]
                                .transform(lambda s: s >= s.median()),
                                "HIGH_VOL", "LOW_VOL")
    df["liq_bucket"] = df.groupby("historical_date")["volume_24h_usd"] \
        .transform(lambda s: pd.qcut(s, 3, labels=["LOW", "MED", "HIGH"],
                                     duplicates="drop"))

    s3 = np.sign(df["ret_3d"].to_numpy(float))
    s14 = np.sign(df["ret_14d"].to_numpy(float))
    out = np.empty(len(df), dtype=object)
    hh = (s3 > 0) & (s14 > 0)
    hc = (s3 > 0) & (s14 <= 0)
    ch = (s3 <= 0) & (s14 > 0)
    out[hh] = "SHORT_HOT_MEDIUM_HOT"
    out[hc] = "SHORT_HOT_MEDIUM_COLD"
    out[ch] = "SHORT_COLD_MEDIUM_HOT"
    out[~(hh | hc | ch)] = "SHORT_COLD_MEDIUM_COLD"
    out[np.isnan(s3) | np.isnan(s14)] = np.nan
    df["momentum_state"] = pd.Series(out, index=df.index).astype("category")
    return df


def add_forward_and_future(df: pd.DataFrame) -> pd.DataFrame:
    """Forward cumulative returns and FUTURE PIT ranks (outcome data only)."""
    ok = df["ret_1d"].notna() & (df["ret_1d"] > -1.0)
    logf = pd.Series(np.where(ok, np.log1p(df["ret_1d"].clip(lower=-0.9999)), np.nan),
                     index=df.index)
    cs = logf.groupby(df["cmc_id"], sort=False).cumsum()
    for h in C.H:
        lead = cs.groupby(df["cmc_id"], sort=False).shift(-h)
        df[f"fwd{h}_cum"] = np.expm1(lead - cs)
        df[f"fwd_rank_{h}d"] = df.groupby("cmc_id", sort=False)["rank"].shift(-h)
    return df


def add_global_context(df: pd.DataFrame) -> pd.DataFrame:
    df["historical_date_key"] = df["historical_date"].dt.strftime("%Y-%m-%d")
    terr = pd.read_parquet(C.TERRAIN)
    terr["historical_date_key"] = terr["historical_date"].dt.strftime("%Y-%m-%d")
    tcols = ["historical_date_key", "btc_return_1d", "btc_return_30d",
             "eth_return_1d", "eth_btc_relative_return_1d",
             "eth_btc_relative_return_30d", "top500_breadth_30d",
             "top500_dispersion_30d", "btc_dominance",
             "stablecoin_mcap_share", "total_alt_share"]
    terr = terr[[c for c in tcols if c in terr.columns]] \
        .rename(columns={"btc_return_1d": "btc_ret_1d", "eth_return_1d": "eth_ret_1d"})
    df = df.merge(terr, on="historical_date_key", how="left")
    feats = pd.read_parquet(C.FEATURES_V2,
                            columns=["internal_asset_id", "historical_date",
                                     "realized_volatility_30d"])
    feats["historical_date_key"] = feats["historical_date"].dt.strftime("%Y-%m-%d")
    mvol = feats.groupby("historical_date_key")["realized_volatility_30d"] \
        .median().rename("mkt_vol_30d").reset_index()
    df = df.merge(mvol, on="historical_date_key", how="left")
    df["field_cell"] = [C.cell_of(b, d) for b, d in
                        zip(df["top500_breadth_30d"], df["top500_dispersion_30d"])]
    df["rank_band"] = df["rank"].apply(C.band_of)
    return df


def add_quality_flags(df: pd.DataFrame) -> pd.DataFrame:
    mkt_move = df["btc_ret_1d"].abs() > 0.005
    df["flag_stale_price"] = ((df["price_usd"] == df["price_prev"]) & mkt_move)
    df["flag_zero_volume"] = (df["volume_24h_usd"].fillna(0) == 0)
    df["flag_missing_price"] = df["price_usd"].isna()
    df["flag_listing_day"] = df["listing_age_days"] <= 3
    df["flag_suspicious_volume"] = ((df["vol_accel"] > 10) & (df["ret_1d"].abs() < 0.001))
    df["flag_any_quality"] = (df["flag_stale_price"] | df["flag_zero_volume"]
                              | df["flag_missing_price"] | df["flag_listing_day"])
    return df


def wide_returns(df: pd.DataFrame) -> pd.DataFrame:
    long = df[["historical_date", "cmc_id", "ret_1d"]].copy()
    wide = long.pivot_table(index="historical_date", columns="cmc_id",
                            values="ret_1d").astype(np.float32)
    return wide.sort_index()


def build() -> pd.DataFrame:
    raw = load_raw_snapshots()
    raw.to_parquet(C.RAW_PANEL, index=False)
    print("raw panel cached", len(raw), flush=True)

    df = add_causal_features(raw)
    df = add_forward_and_future(df)
    df = add_global_context(df)
    df = add_quality_flags(df)
    df = df.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)

    df.to_parquet(C.SUBSTRATE, index=False)
    print("substrate written", len(df), "rows", flush=True)

    ret = df[["historical_date", "cmc_id", "ret_1d", "flag_stale_price",
              "flag_missing_price"]].copy()
    ret.to_parquet(C.RETURNS_LONG, index=False)

    wide = wide_returns(df)
    wide.to_parquet(C.RETURNS_WIDE, index=True)
    print("wide returns", wide.shape, flush=True)

    ident = df[["cmc_id", "symbol"]].drop_duplicates("cmc_id")
    ident["first_date"] = df.groupby("cmc_id")["historical_date"].min() \
        .reindex(ident["cmc_id"]).dt.strftime("%Y-%m-%d").values
    ident["last_date"] = df.groupby("cmc_id")["historical_date"].max() \
        .reindex(ident["cmc_id"]).dt.strftime("%Y-%m-%d").values
    ident.to_parquet(C.CACHE / "lf5_identity_map.parquet", index=False)
    return df


def write_matrix_metadata(df: pd.DataFrame, wide: pd.DataFrame):
    sha = hashlib.sha256(C.SUBSTRATE.read_bytes()).hexdigest()[:16]
    n_missing = int(df["ret_1d"].isna().sum())
    total = len(df)
    meta = f"""# PIT RETURN MATRIX METADATA

Long-form source: `PIT_RETURNS_LONG.parquet`; key `(historical_date, cmc_id)`;
value `ret_1d` (close-to-close from the PIT snapshot price). Wide cache:
`cache/pit_returns_wide.parquet` (float32, dates x cmc_id).

## Coverage
- Date range: {df['historical_date'].min().date()} through {df['historical_date'].max().date()}
- Days: {df['historical_date'].nunique():,} (80 calendar days in the window lack snapshots; see lower_field/DATA_TRUTH/collection_log.txt)
- Assets: {df['cmc_id'].nunique():,}
- Rows: {total:,}
- Ret_1d missing: {n_missing:,} ({n_missing / max(total, 1):.2%})
- Wide matrix: {wide.shape[0]:,} dates x {wide.shape[1]:,} assets, {100 * wide.notna().sum().sum() / wide.size:.1f}% observed

## Missingness rules
- Missing observations are retained as NaN. Never zero-filled.
- An asset absent from the top-2000 on a day has no row that day; ret_1d after
  a re-entry gap is NaN (no forward/back fill across absence).
- Assets enter when first listed in the top-2000 (no survivor backprojection).

## Usage
- Trailing 60D/120D correlations are computed causally from windows ending at
  t-1 in the peer builder (`lf5_peer_maps.py`); no full-sample matrix is stored.
- Outcome fields (fwd*_cum, fwd_rank_*d) live in the substrate and are never
  consumed by feature construction or peer matching.

## Provenance
- Source: `{C.RAW}` (lf_snapshot_YYYYMMDD_r1_2000.json, CMC historical listings
  endpoint, WEB_ONLY access class; parity with canonical top-500 verified in
  lower_field/DATA_TRUTH/lf_parity_audit.csv).
- Substrate SHA-256 (first 16): `{sha}`
- Rebuild: `python scripts/lf5_build_substrate.py`
"""
    (C.ROOT / "05_RETURN_MATRIX_METADATA.md").write_text(meta, encoding="utf-8")


def downcast(df: pd.DataFrame) -> pd.DataFrame:
    """Downcast float64 -> float32 and int64 -> int32 to cut memory in half."""
    for c in df.columns:
        if df[c].dtype == np.float64:
            df[c] = df[c].astype(np.float32)
        elif df[c].dtype == np.int64:
            df[c] = df[c].astype(np.int32)
    return df


def main():
    import gc
    df = build()
    df = downcast(df)
    df.to_parquet(C.SUBSTRATE, index=False)
    del df
    gc.collect()
    wide = pd.read_parquet(C.RETURNS_WIDE)
    write_matrix_metadata(pd.read_parquet(C.SUBSTRATE, columns=["historical_date", "cmc_id", "ret_1d"]), wide)
    print("STAGE A substrate complete:", flush=True)
    s = pd.read_parquet(C.SUBSTRATE, columns=["historical_date", "cmc_id"])
    print(len(s), "rows,", s["cmc_id"].nunique(), "assets,",
          s["historical_date"].nunique(), "dates")


if __name__ == "__main__":
    main()
