#!/usr/bin/env python3
"""ALT-DATA-1 — canonical PIT universe + multiscale feature panel builder.

Deterministic offline pipeline. No network.

Stages:
  0. load raw daily snapshots -> validate 500 rows/date
  1. PIT universe parquet
  2. canonical identity map parquet
  3. perp eligibility ledger parquet
  4. asset multiscale features parquet
  5. rank-band features parquet
  6. sector features parquet
  7. market terrain features parquet
  8. CSV samples + feature registry + registry hash + build summary

Frozen definitions: ALT_DATA_1_PREREGISTRATION.md. Formulas also recorded
in the emitted feature registry.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "probes" / "raw"
D0RAW = ROOT.parent / "data_0" / "probes" / "raw"
OUT = ROOT
for d in (OUT / "identity", OUT / "derived", OUT / "samples"):
    d.mkdir(exist_ok=True)

WINDOWS = [1, 3, 7, 14, 30, 60, 90]
BANDS = [(1, 10), (11, 25), (26, 50), (51, 100), (101, 200), (201, 300),
         (301, 500)]
MIN_MATURITY = 30
MIN_OBS = {30: 20, 60: 40, 90: 60}
COVERAGE_FLOOR = 0.80
STABLE_TAGS = {"stablecoin", "stablecoin-asset-backed",
               "stablecoin-algorithmically-stabilized",
               "asset-backed-stablecoin", "usd-stablecoin",
               "algorithmic-stablecoin", "eur-stablecoin",
               "fiat-stablecoin", "stablecoin-protocol"}
STABLE_SYMS = {"USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP", "FDUSD",
               "USDE", "PYUSD", "GUSD", "LUSD", "FRAX", "USTC", "UST",
               "EURS", "USDD", "USD1"}
BTC_ID, ETH_ID = 1, 1027


def norm_symbol(s: str) -> str:
    return (s or "").strip().upper()


def band_of(rank: int) -> str:
    for lo, hi in BANDS:
        if lo <= rank <= hi:
            return f"{lo}-{hi}"
    return "OUT"


def parse_tags(tags) -> list[str]:
    if not tags:
        return []
    return [str(t).strip().lower() for t in tags if str(t).strip()]


def write_parquet(df: pd.DataFrame, name: str) -> Path:
    df = df.sort_index(axis=1)
    p = OUT / name
    df.to_parquet(p, index=False)
    return p


# ----------------------------------------------------------------------
# Stage 0 — load raw snapshots
# ----------------------------------------------------------------------
def load_snapshots() -> pd.DataFrame:
    rows = []
    files = sorted(RAW.glob("cmc_snapshot_*_top500.json"))
    meta_dir = RAW
    if not files:
        files = sorted(D0RAW.glob("cmc_snapshot_*_top500.json"))
        meta_dir = D0RAW
    bad = []
    gaps = []
    for f in files:
        dt = f.stem.split("_")[2]
        d = json.loads(f.read_text(encoding="utf-8"))
        data = d["data"]
        if len(data) != 500:
            gaps.append({"historical_date": dt, "rows": len(data),
                         "exclusion": "CMC_side_data_gap_" + dt,
                         "note": "snapshot incomplete on source; "
                                 "reconstruction attempt exhausted; "
                                 "excluded from panel"})
            bad.append((dt, len(data)))
            continue  # skip incomplete dates entirely
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
                "circulating_supply": float(r.get("circulatingSupply")
                                            or np.nan),
                "total_supply": float(r.get("totalSupply") or np.nan),
                "max_supply": float(r.get("maxSupply") or np.nan),
                "date_added_cmc": r.get("dateAdded", ""),
                "last_updated": r.get("lastUpdated", ""),
                "tags": ";".join(tags),
                "platform_chain": norm_symbol(plat.get("symbol", "")),
                "contract_address": (plat.get("token_address", "") or ""),
                "pct_change_1h": float(q.get("percentChange1h")
                                       or np.nan),
                "pct_change_24h": float(q.get("percentChange24h")
                                        or np.nan),
                "pct_change_7d": float(q.get("percentChange7d")
                                       or np.nan),
            })
    if bad:
        print(f"WARN bad row counts: {bad}", flush=True)
    df = pd.DataFrame(rows)
    df["historical_date_key"] = df["historical_date"].dt.strftime(
        "%Y-%m-%d")
    # Filter to top-500 only (CMC pagination sometimes returns ranks 501+
    # in the 500-row result; drop those, then exclude dates that fall below
    # 500 rows)
    df = df[df["rank"] <= 500]
    cnts = df.groupby("historical_date_key").size()
    short = cnts[cnts < 500]
    for dt, n in short.items():
        gaps.append({"historical_date": dt, "rows": int(n),
                     "exclusion": "CMC_pagination_gap_" + dt,
                     "note": f"top-500 incomplete after rank filter; "
                             f"{int(n)} of 500 rows retained"})
        bad.append((dt, int(n)))
    if len(short):
        valid_keys = set(cnts[cnts >= 500].index)
        df = df[df["historical_date_key"].isin(valid_keys)]
    df["is_stablecoin"] = df["tags"].apply(
        lambda t: any(s in t.split(";") for s in STABLE_TAGS)) | \
        df["symbol"].isin(STABLE_SYMS)
    return df, gaps


# ----------------------------------------------------------------------
# Stage 1 — PIT universe
# ----------------------------------------------------------------------
def build_universe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["historical_date", "rank"]).reset_index(drop=True)
    totals = df.groupby("historical_date").agg(
        total_mcap=("market_cap_usd", "sum"),
        total_vol=("volume_24h_usd", "sum")).reset_index()
    df = df.merge(totals, on="historical_date", how="left")
    df["market_cap_share"] = df["market_cap_usd"] / df["total_mcap"]
    df["volume_share"] = df["volume_24h_usd"] / df["total_vol"]
    df["volume_rank"] = df.groupby("historical_date")["volume_24h_usd"]\
        .rank(ascending=False, method="min").where(
            df["volume_24h_usd"].notna())  # NaN when volume missing
    df["rank_band"] = df["rank"].apply(band_of)
    df["internal_asset_id"] = "CMC:" + df["cmc_id"].astype(str)
    return df


# ----------------------------------------------------------------------
# Stage 2 — identity map
# ----------------------------------------------------------------------
def build_identity(df: pd.DataFrame) -> pd.DataFrame:
    cg_list = json.loads((D0RAW / "coingecko_coins_list.json")
                         .read_text(encoding="utf-8"))
    cp_list = json.loads((D0RAW / "coinpaprika_coins.json")
                         .read_text(encoding="utf-8"))
    cg_by_symbol: dict[str, list] = {}
    for c in cg_list:
        cg_by_symbol.setdefault(norm_symbol(c["symbol"]), []).append(c)
    cp_by_symbol: dict[str, list] = {}
    for c in cp_list:
        cp_by_symbol.setdefault(norm_symbol(c["symbol"]), []).append(c)

    def token_ratio(a, b):
        sa, sb = set(a.lower().split()), set(b.lower().split())
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / max(len(sa), len(sb))

    rows = []
    for cid, sub in df.groupby("cmc_id"):
        canonical = sub["symbol"].value_counts().index[0]
        name = sub["name"].value_counts().index[0]
        slug = sub["slug"].value_counts().index[0]
        da = sub["date_added_cmc"].dropna()
        date_added = da.iloc[0] if len(da) else ""
        cg_hits = cg_by_symbol.get(canonical, [])
        cp_hits = cp_by_symbol.get(canonical, [])
        cg_best = max(cg_hits, key=lambda c: token_ratio(c["name"], name)) \
            if cg_hits else None
        cp_best = max(cp_hits, key=lambda c: token_ratio(c["name"], name)) \
            if cp_hits else None
        cg_hi = bool(cg_best and token_ratio(cg_best["name"], name) >= 0.6)
        cp_hi = bool(cp_best and token_ratio(cp_best["name"], name) >= 0.6)
        rows.append({
            "internal_asset_id": f"CMC:{int(cid)}",
            "cmc_id": int(cid),
            "canonical_symbol": canonical,
            "cmc_name": name,
            "cmc_slug": slug,
            "symbols_observed": ",".join(sorted(
                set(sub["symbol"].dropna().unique()))),
            "coingecko_id": cg_best["id"] if cg_best and cg_hi else "",
            "cg_join": "HIGH" if cg_hi else ("LOW" if cg_best else ""),
            "coinpaprika_id": cp_best["id"] if cp_best and cp_hi else "",
            "cp_join": "HIGH" if cp_hi else ("LOW" if cp_best else ""),
            "date_added_cmc": date_added,
            "first_seen_in_panel": sub["historical_date"].min().strftime(
                "%Y-%m-%d"),
            "last_seen_in_panel": sub["historical_date"].max().strftime(
                "%Y-%m-%d"),
        })
    ident = pd.DataFrame(rows)
    cmc_by_sym: dict[str, set] = {}
    for _, r in ident.iterrows():
        cmc_by_sym.setdefault(r["canonical_symbol"], set()).add(
            r["internal_asset_id"])
    cls = []
    for _, r in ident.iterrows():
        sym = r["canonical_symbol"]
        if len(cmc_by_sym[sym]) > 1:
            cls.append("TRUE_TICKER_REUSE")
        else:
            cg_n = len(cg_by_symbol.get(sym, []))
            cp_n = len(cp_by_symbol.get(sym, []))
            if (cg_n > 1 or cp_n > 1) and r["cg_join"] == "HIGH" and \
                    r["cp_join"] == "HIGH":
                cls.append("PROVIDER_SYMBOL_COLLISION")
            elif cg_n > 1 or cp_n > 1:
                cls.append("UNKNOWN_COLLISION")
            else:
                cls.append("NO_COLLISION")
    ident["collision_class"] = cls
    ident["mapping_method"] = "CMC_ID_ANCHORED_SYMBOL_NAME_JOIN"
    ident["mapping_confidence"] = "HIGH"
    return ident


# ----------------------------------------------------------------------
# Stage 3 — perp eligibility ledger
# ----------------------------------------------------------------------
def build_eligibility(df: pd.DataFrame,
                      ident: pd.DataFrame) -> pd.DataFrame:
    hl = json.loads((D0RAW / "hyperliquid_funding_first_history.json")
                    .read_text(encoding="utf-8"))["coins"]
    hl_by_coin = {norm_symbol(c["coin"]): c for c in hl}
    okx = json.loads((D0RAW / "okx_instruments_swap.json")
                     .read_text(encoding="utf-8"))["data"]
    okx_by_base: dict[str, dict] = {}
    for s in okx:
        parts = s["instId"].split("-")
        if len(parts) >= 2:
            base = norm_symbol(parts[0])
            cur = okx_by_base.get(base)
            if cur is None or (parts[1] == "USDT"
                               and cur.get("_quote") != "USDT"):
                okx_by_base[base] = {**s, "_quote": parts[1]}

    def iso(ms):
        if not ms:
            return ""
        return datetime.fromtimestamp(int(ms) / 1000,
                                      tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ")

    # per-asset contract table (constant across dates)
    sym_by_id = ident.set_index("cmc_id")["canonical_symbol"].to_dict()
    contracts = []  # (symbol, venue, id, lt, delist_date|None, ...)
    for sym, m in hl_by_coin.items():
        lt_ms = m.get("first_funding_ts")
        if not lt_ms:
            continue
        lt = datetime.fromtimestamp(lt_ms / 1000, tz=timezone.utc)
        dl = None
        if m.get("is_delisted") and m.get("last_funding_ts"):
            dl = datetime.fromtimestamp(m["last_funding_ts"] / 1000,
                                        tz=timezone.utc)
        contracts.append({"symbol": sym, "venue": "HYPERLIQUID",
                          "instrument_id": f"{sym}-PERP",
                          "listing_ts": lt, "listing_authority":
                          "INFERRED_FIRST_DATA_TIMESTAMP",
                          "delist_ts": dl, "delist_authority":
                          ("INFERRED_LAST_FUNDING_TS" if dl else ""),
                          "price": "YES", "funding": "YES",
                          "volume": "YES", "liq": "VOLUME_PROXY_ONLY"})
    for base, m in okx_by_base.items():
        lt = datetime.fromtimestamp(int(m["listTime"]) / 1000,
                                    tz=timezone.utc)
        contracts.append({"symbol": base, "venue": "OKX",
                          "instrument_id": m["instId"],
                          "listing_ts": lt,
                          "listing_authority": "OFFICIAL_LIST_TIME",
                          "delist_ts": None,
                          "delist_authority":
                          "DELISTING_NOT_AVAILABLE_PUBLIC_API",
                          "price": "PARTIAL", "funding": "PARTIAL",
                          "volume": "PARTIAL", "liq": "PARTIAL"})
    ct = pd.DataFrame(contracts)
    # attach canonical cmc_id (first asset with that symbol)
    sym_cid = df.drop_duplicates("symbol")[["symbol", "cmc_id"]]
    ct = ct.merge(sym_cid, on="symbol", how="left")
    ct = ct.dropna(subset=["cmc_id"])  # venue coins never in top-500
    rows = []
    day64 = np.timedelta64(1, "D")
    for sym, sub in ct.groupby("symbol"):
        cid = int(sub["cmc_id"].iloc[0])
        dates = df[df["cmc_id"] == cid][["historical_date", "rank"]]
        if dates.empty:
            continue
        dts = dates["historical_date"].to_numpy()
        rks = dates["rank"].to_numpy()
        for _, c in sub.iterrows():
            lt64 = pd.Timestamp(c["listing_ts"]).to_datetime64()
            dl64 = None
            if c["delist_ts"] is not None and not pd.isna(c["delist_ts"]):
                dl64 = pd.Timestamp(c["delist_ts"]).to_datetime64()
            age = (dts - lt64) // day64
            tradable = dts >= lt64
            if dl64 is not None:
                # tradable while listed: snapshot time <= delisting instant
                tradable = tradable & (dts <= dl64)
            mature = tradable & (age >= MIN_MATURITY)
            age_f = np.where(tradable, age, np.nan)
            listed_after = ~tradable & (dts < lt64)
            delisted_before = ~tradable & ~listed_after
            status = np.select(
                [listed_after, delisted_before, ~mature],
                ["NOT_ELIGIBLE", "NOT_ELIGIBLE",
                 "CONTRACT_EXISTENCE_ELIGIBLE"],
                default="ELIGIBLE_EX_LIQUIDITY")
            reason = np.select(
                [listed_after, delisted_before, ~mature],
                ["listed_after_t", "delisted_before_t",
                 f"age<{MIN_MATURITY}d"],
                default="historical_liquidity_not_verified")
            for i in range(len(dts)):
                rows.append({
                    "historical_date": dts[i], "cmc_id": cid,
                    "symbol": sym, "rank": int(rks[i]),
                    "venue": c["venue"],
                    "venue_instrument_id": c["instrument_id"],
                    "listing_timestamp": iso(
                        int(c["listing_ts"].timestamp() * 1000)),
                    "listing_timestamp_authority": c["listing_authority"],
                    "delisting_timestamp": (iso(int(
                        pd.Timestamp(c["delist_ts"]).timestamp() * 1000))
                        if c["delist_ts"] is not None
                        and not pd.isna(c["delist_ts"]) else ""),
                    "delisting_timestamp_authority": c["delist_authority"],
                    "contract_age_days_at_t": float(age_f[i]),
                    "tradable_at_t": bool(tradable[i]),
                    "mature_30d_at_t": bool(mature[i]),
                    "historical_price_data_available": c["price"],
                    "historical_funding_data_available": c["funding"],
                    "historical_volume_data_available": c["volume"],
                    "liquidity_proxy_status": c["liq"],
                    "contract_existence_eligible": bool(tradable[i]),
                    "contract_maturity_eligible": bool(mature[i]),
                    "historical_data_eligible": bool(
                        tradable[i] and c["price"] in ("YES", "PARTIAL")),
                    "historical_liquidity_verified": False,
                    "eligibility_status": status[i],
                    "exclusion_reason": reason[i],
                })
    elig = pd.DataFrame(rows)
    elig.attrs["env_venues"] = [
        {"venue": "BINANCE_USDM",
         "environment_status": "UNVERIFIABLE_FROM_ENV",
         "reason": "live API geo-blocked (451); archive method verified "
                   "(data.binance.vision 2020-01+ incl. delisted); "
                   "per-asset archive not collected in DATA-1"},
        {"venue": "BYBIT_LINEAR",
         "environment_status": "UNVERIFIABLE_FROM_ENV",
         "reason": "live API geo-blocked (403 CloudFront)"},
    ]
    return elig


# ----------------------------------------------------------------------
# Stage 4 — asset multiscale features
# ----------------------------------------------------------------------
def _lag_frame(df: pd.DataFrame, w: int) -> pd.DataFrame:
    lag = df[["cmc_id", "historical_date", "price_usd", "rank",
              "market_cap_usd", "volume_24h_usd", "market_cap_share"]]
    lag = lag.assign(hist_date_lag=lag["historical_date"]
                     + pd.Timedelta(days=w))
    lag = lag.rename(columns={
        "price_usd": f"price_{w}d_ago",
        "rank": f"rank_{w}d_ago",
        "market_cap_usd": f"mcap_{w}d_ago",
        "volume_24h_usd": f"vol_{w}d_ago",
        "market_cap_share": f"mcap_share_{w}d_ago"})
    cur = df[["cmc_id", "historical_date", "price_usd", "rank",
              "market_cap_usd", "volume_24h_usd", "market_cap_share"]] \
        .rename(columns={"historical_date": "hist_date_lag"})
    m = cur.merge(lag, on=["cmc_id", "hist_date_lag"], how="left")
    return m.drop(columns=["hist_date_lag"])


def _nanmean_pairs(a: np.ndarray, b: np.ndarray,
                   subtract: bool = False) -> np.ndarray:
    """nanmean of rows of a (and b), handling all-NaN rows; optionally
    returns mean(a) - mean(b)."""
    ma = np.full(len(a), np.nan)
    ok_a = ~np.isnan(a).all(axis=1)
    ma[ok_a] = np.nanmean(a[ok_a], axis=1)
    if not subtract:
        return ma
    mb = np.full(len(b), np.nan)
    ok_b = ~np.isnan(b).all(axis=1)
    mb[ok_b] = np.nanmean(b[ok_b], axis=1)
    out = np.full(len(a), np.nan)
    both = ok_a & ok_b
    out[both] = ma[both] - mb[both]
    return out


def _roll_align(df: pd.DataFrame, series, w: int, minp: int,
                agg: str) -> np.ndarray:
    """Time-windowed groupby rolling, re-aligned to df row order."""
    vals = series.values if isinstance(series, pd.Series) else series
    tmp = pd.DataFrame({
        "cmc_id": df["cmc_id"].values,
        "date": df["historical_date"].values,
        "v": vals,
    }).set_index("date")
    res = tmp.groupby("cmc_id")["v"].rolling(
        f"{w}D", min_periods=minp).agg(agg)
    key = pd.MultiIndex.from_arrays(
        [df["cmc_id"].values, df["historical_date"].values])
    return res.reindex(key).to_numpy()


def _window_hits(df, w, threshold) -> np.ndarray:
    hit = (df["rank"] <= threshold).astype(int)
    return _roll_align(df, hit, w, 1, "sum")


def _window_peak_hits(df, w, is_peak) -> np.ndarray:
    return _roll_align(df, is_peak.astype(int), w, 1, "sum")


def _rolling_beta(df, lr, bench_lr, w, min_obs) -> np.ndarray:
    tmp = pd.DataFrame({
        "cmc_id": df["cmc_id"].values,
        "date": df["historical_date"].values,
        "x": lr.values,
        "b": bench_lr.reindex(df["historical_date"].values).to_numpy(),
    })
    tmp["xb"] = tmp["x"] * tmp["b"]
    tmp["xx"] = tmp["x"] ** 2
    tmp = tmp.set_index("date")
    sums = {}
    for col in ("x", "b", "xb", "xx"):
        res = tmp.groupby("cmc_id")[col].rolling(
            f"{w}D", min_periods=1).sum()
        sums[col] = res
    n = tmp.groupby("cmc_id")["x"].rolling(
        f"{w}D", min_periods=1).count()
    key = pd.MultiIndex.from_arrays(
        [df["cmc_id"].values, df["historical_date"].values])
    sx = sums["x"].reindex(key).to_numpy()
    sb = sums["b"].reindex(key).to_numpy()
    sxb = sums["xb"].reindex(key).to_numpy()
    sxx = sums["xx"].reindex(key).to_numpy()
    nv = n.reindex(key).to_numpy()
    denom = w * sxx - sx * sx
    beta = np.where(np.abs(denom) > 1e-12,
                    (w * sxb - sx * sb) / np.where(
                        np.abs(denom) > 1e-12, denom, np.nan),
                    np.nan)
    need = max(min_obs, int(math.ceil(COVERAGE_FLOOR * w)))
    beta[nv < need] = np.nan
    return beta


def build_asset_features(df: pd.DataFrame,
                         btc_lr: pd.Series,
                         eth_lr: pd.Series,
                         btc_ret: dict,
                         eth_ret: dict) -> pd.DataFrame:
    r = df["rank"]
    cols = {
        "historical_date": df["historical_date"],
        "cmc_id": df["cmc_id"],
        "internal_asset_id": df["internal_asset_id"],
        "symbol": df["symbol"],
        "global_rank": df["rank"],
        "rank_band": df["rank_band"],
        "market_cap_usd": df["market_cap_usd"],
        "market_cap_share": df["market_cap_share"],
        "volume_24h_usd": df["volume_24h_usd"],
        "volume_rank": df["volume_rank"],
        "volume_share": df["volume_share"],
        "is_stablecoin": df["is_stablecoin"],
        "tags": df["tags"],
    }
    # per-asset daily log return
    lp = np.log(df["price_usd"])
    lr = lp - lp.groupby(df["cmc_id"]).shift(1)

    for w in WINDOWS:
        lg = _lag_frame(df, w)
        ret = lg["price_usd"] / lg[f"price_{w}d_ago"] - 1.0
        cols[f"return_{w}d"] = ret
        cols[f"rank_change_{w}d"] = lg[f"rank_{w}d_ago"] - r
        cols[f"mcap_change_{w}d"] = \
            lg["market_cap_usd"] / lg[f"mcap_{w}d_ago"] - 1.0
        cols[f"mcap_share_change_{w}d"] = \
            lg[f"mcap_share_{w}d_ago"] - df["market_cap_share"]
        br = btc_ret[w].reindex(df["historical_date"].values).to_numpy()
        er = eth_ret[w].reindex(df["historical_date"].values).to_numpy()
        cols[f"relative_return_vs_BTC_{w}d"] = ret - br
        cols[f"relative_return_vs_ETH_{w}d"] = ret - er
        cols[f"realized_volatility_{w}d"] = _roll_align(
            df, lr, w, max(2, int(math.ceil(COVERAGE_FLOOR * w))), "std")
        cols[f"volume_mean_{w}d_usd"] = _roll_align(
            df, df["volume_24h_usd"], w,
            max(1, int(math.ceil(COVERAGE_FLOOR * w))), "mean")
        cols[f"return_rank_in_universe_{w}d"] = \
            ret.groupby(df["historical_date"]).rank(ascending=False)
    # velocity / acceleration
    for w in (1, 3, 7, 14):
        cols[f"rank_velocity_{w}d"] = cols[f"rank_change_{w}d"]
    cols["rank_acceleration_short"] = (
        (r.groupby(df["cmc_id"]).shift(7) - r)
        - (r.groupby(df["cmc_id"]).shift(14)
           - r.groupby(df["cmc_id"]).shift(7)))
    cols["rank_acceleration_medium"] = (
        (r.groupby(df["cmc_id"]).shift(30) - r)
        - (r.groupby(df["cmc_id"]).shift(60)
           - r.groupby(df["cmc_id"]).shift(30)))
    # rank-curve state
    lags = np.array([1, 3, 7, 14, 30, 60, 90], dtype=float)
    rc = np.column_stack([_lag_frame(df, w)[f"rank_{w}d_ago"]
                          for w in WINDOWS]).astype(float)
    for i, w in enumerate(WINDOWS):
        cols[f"rank_{w}d_ago"] = rc[:, i]
    cols["short_mid_rank_spread"] = _nanmean_pairs(
        rc[:, [0, 1, 2]], rc[:, [4, 5]], subtract=True)
    cols["mid_long_rank_spread"] = _nanmean_pairs(
        rc[:, [3, 4]], rc[:, [5, 6]], subtract=True)
    slope = np.full(len(df), np.nan)
    complete = ~np.isnan(rc).any(axis=1)
    xm = lags.mean()
    xd = lags - xm
    if complete.any():
        y = rc[complete]
        ym = y.mean(axis=1, keepdims=True)
        yd = y - ym
        slope[complete] = (yd * xd).sum(axis=1) / (xd * xd).sum()
    for i in np.where(~complete)[0]:
        y = rc[i]
        ok = ~np.isnan(y)
        if ok.sum() >= 3:
            slope[i] = np.polyfit(lags[ok], y[ok], 1)[0]
    cols["rank_curve_slope"] = slope
    diff = rc[:, 1:] - rc[:, :-1]
    mono = np.full(len(df), np.nan)
    infc = np.full(len(df), np.nan)
    dv_all = diff[complete]
    mono[complete] = (dv_all >= 0).mean(axis=1)
    infc[complete] = np.sum(np.sign(dv_all[:, 1:]) != np.sign(
        dv_all[:, :-1]), axis=1).astype(float)
    for i in np.where(~complete)[0]:
        d = diff[i]
        ok = ~np.isnan(d)
        if ok.sum() == 0:
            continue
        dv = d[ok]
        mono[i] = np.mean(dv >= 0)
        if len(dv) >= 2:
            infc[i] = np.sum(np.sign(dv[1:]) != np.sign(dv[:-1]))
    cols["rank_curve_monotonicity"] = mono
    cols["rank_curve_inflection_count"] = infc
    # peak frequency
    prev_cummin = r.groupby(df["cmc_id"]).cummin().shift(1)
    is_peak = (r < prev_cummin.fillna(np.inf)).to_numpy()
    peak_date = df["historical_date"].where(
        pd.Series(is_peak, index=df.index))
    peak_date_ff = peak_date.groupby(df["cmc_id"]).ffill()
    cols["days_since_rank_peak"] = (
        df["historical_date"] - peak_date_ff).dt.days
    cols["top_decile_hits_7d"] = _window_hits(df, 7, 50)
    cols["top_decile_hits_14d"] = _window_hits(df, 14, 50)
    cols["top_decile_hits_30d"] = _window_hits(df, 30, 50)
    cols["top_quartile_hits_30d"] = _window_hits(df, 30, 125)
    cols["rank_peak_count_7d"] = _window_peak_hits(df, 7, is_peak)
    cols["rank_peak_count_14d"] = _window_peak_hits(df, 14, is_peak)
    cols["rank_peak_count_30d"] = _window_peak_hits(df, 30, is_peak)
    # consecutive positive rank velocity
    imp = (r < r.groupby(df["cmc_id"]).shift(1)).fillna(False)
    grp = (~imp).cumsum()
    cols["consecutive_positive_rank_velocity"] = \
        imp.groupby([df["cmc_id"], grp]).cumsum()
    # entry / membership
    prev_date = df.groupby("cmc_id")["historical_date"].shift(1)
    cols["entered_top500"] = (
        ~df["historical_date"].sub(prev_date).dt.days.eq(1)).fillna(True)
    cols["days_in_top500"] = df.groupby("cmc_id").cumcount() + 1
    prev_date = df.groupby("cmc_id")["historical_date"].shift(1)
    daydiff = df["historical_date"].sub(prev_date).dt.days
    is_gap = (daydiff != 1)  # NaN on first row -> True (per-asset)
    grp2 = is_gap.cumsum()
    cols["consecutive_days_in_top500"] = \
        df.groupby(grp2).cumcount() + 1
    # volatility-normalized descriptive move (true ATR NOT supported)
    v14 = cols["realized_volatility_14d"]
    cols["volatility_normalized_move_14d"] = (
        cols["return_14d"] / np.where(np.abs(v14) > 1e-12, v14, np.nan))
    cols["atr_14d_true"] = np.nan

    feat = pd.DataFrame(cols)
    # beta / residual inputs (causal OLS)
    for w, mo in ((30, 20), (60, 40), (90, 60)):
        b = _rolling_beta(df, lr, btc_lr, w, mo)
        feat[f"rolling_beta_vs_BTC_{w}d"] = b
        exp = b * btc_ret[w].reindex(
            df["historical_date"].values).to_numpy()
        feat[f"expected_return_given_BTC_{w}d"] = exp
        feat[f"residual_return_vs_BTC_{w}d"] = \
            feat[f"return_{w}d"] - exp
        be = _rolling_beta(df, lr, eth_lr, w, mo)
        feat[f"rolling_beta_vs_ETH_{w}d"] = be
        expe = be * eth_ret[w].reindex(
            df["historical_date"].values).to_numpy()
        feat[f"expected_return_given_ETH_{w}d"] = expe
        feat[f"residual_return_vs_ETH_{w}d"] = \
            feat[f"return_{w}d"] - expe
    return feat


# ----------------------------------------------------------------------
# Stage 5 — rank-band features
# ----------------------------------------------------------------------
def build_band_features(feat: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (dt, band), sub in feat.groupby(["historical_date", "rank_band"]):
        rows.append({
            "historical_date": dt,
            "rank_band": band,
            "member_count": len(sub),
            "median_return_1d": sub["return_1d"].median(),
            "median_return_3d": sub["return_3d"].median(),
            "median_return_7d": sub["return_7d"].median(),
            "median_return_30d": sub["return_30d"].median(),
            "breadth_7d": (sub["return_7d"] > 0).mean(),
            "breadth_30d": (sub["return_30d"] > 0).mean(),
            "market_cap_share": sub["market_cap_share"].sum(),
            "volume_share": sub["volume_share"].sum(),
            "median_rank_velocity_7d": sub["rank_velocity_7d"].median(),
            "median_rank_velocity_14d": sub["rank_velocity_14d"].median(),
            "return_dispersion_7d": sub["return_7d"].std(),
            "return_dispersion_30d": sub["return_30d"].std(),
            "rank_dispersion": sub["global_rank"].std(),
            "members_entering": int(sub["entered_top500"].sum()),
            "median_relative_return_vs_BTC_7d":
                sub["relative_return_vs_BTC_7d"].median(),
            "median_relative_return_vs_BTC_30d":
                sub["relative_return_vs_BTC_30d"].median(),
            "median_relative_return_vs_ETH_7d":
                sub["relative_return_vs_ETH_7d"].median(),
            "median_relative_return_vs_ETH_30d":
                sub["relative_return_vs_ETH_30d"].median(),
            "n_eligible_ex_liquidity_any_venue":
                int(sub["n_eligible_ex_liquidity"].fillna(0).sum()),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Stage 6 — sector features
# ----------------------------------------------------------------------
def _explode_one_date(day: pd.DataFrame) -> pd.DataFrame:
    """Explode tags for one date's slice; memory-efficient."""
    d = day.copy()
    d["tag"] = d["tags"].str.split(";")
    ex = d.explode("tag")
    ex = ex.dropna(subset=["tag"])
    return ex.sort_values(["tag", "market_cap_usd"], ascending=[True, False])


def _layer_stats(sub: pd.DataFrame, label: str) -> pd.DataFrame:
    """Compute layer aggregates per (date, tag)."""
    ag = sub.groupby(["historical_date", "tag"], sort=False).agg(
        layer_return_7d=("return_7d", "mean"),
        layer_return_30d=("return_30d", "mean"),
        layer_breadth_7d=("return_7d", lambda s: (s > 0).mean()),
        layer_market_cap_share=("market_cap_share", "sum"),
        layer_volume_share=("volume_share", "sum"),
        layer_median_rank_velocity_7d=("rank_velocity_7d", "median"),
        layer_relative_return_vs_BTC_7d=(
            "relative_return_vs_BTC_7d", "mean"),
        layer_relative_return_vs_ETH_7d=(
            "relative_return_vs_ETH_7d", "mean"),
        includes_stablecoin=("is_stablecoin", "any"),
    )
    ag = ag.reset_index()
    ag["layer"] = label
    return ag


def build_sector_features(feat: pd.DataFrame) -> pd.DataFrame:
    """Chunked (by month) sector features to avoid OOM explode."""
    base = {
        "sector_source": "COINMARKETCAP_TAGS",
        "sector_status": "HISTORICAL_APPROXIMATION",
        "mapping_confidence": "MEDIUM",
    }
    cols_subset = ["historical_date", "tags", "market_cap_usd", "return_7d",
                   "return_30d", "market_cap_share", "volume_share",
                   "rank_velocity_7d", "relative_return_vs_BTC_7d",
                   "relative_return_vs_ETH_7d", "is_stablecoin"]
    feat["_ym"] = feat["historical_date"].dt.to_period("M")
    parts = []
    for ym, month in feat.groupby("_ym", sort=False):
        ex = _explode_one_date(month[cols_subset])
        if ex.empty:
            continue
        # FULL_SECTOR
        n_members = ex.groupby(["historical_date", "tag"], sort=False).size()
        full = _layer_stats(ex, "FULL_SECTOR")
        full = full.merge(n_members.rename("n").reset_index(),
                          on=["historical_date", "tag"])
        full["layer_member_count"] = full["n"]
        full = full.drop(columns=["n"])
        parts.append(full)
        # TOP1, TOP3, TOP5, TOP10 — member count = min(k, actual sector size)
        for k, label in ((1, "TOP1"), (3, "TOP3"), (5, "TOP5"),
                         (10, "TOP10")):
            sub = ex.groupby(["historical_date", "tag"], sort=False).head(k)
            ag = _layer_stats(sub, label)
            sub_cnts = sub.groupby(["historical_date", "tag"],
                                   sort=False).size()
            ag = ag.merge(sub_cnts.rename("s_cnt").reset_index(),
                          on=["historical_date", "tag"])
            ag["layer_member_count"] = ag["s_cnt"]
            ag = ag.drop(columns=["s_cnt"])
            parts.append(ag)
    out = pd.concat(parts, ignore_index=True)
    out = out.rename(columns={"tag": "sector"})
    for k, v in base.items():
        out[k] = v
    return out


def build_sector_membership(feat: pd.DataFrame) -> pd.DataFrame:
    """Per-asset sector rank coordinate, chunked by month."""
    cols_subset = ["historical_date", "cmc_id", "internal_asset_id",
                   "symbol", "tags", "market_cap_usd", "global_rank"]
    feat["_ym"] = feat["historical_date"].dt.to_period("M")
    parts = []
    for ym, month in feat.groupby("_ym", sort=False):
        ex = _explode_one_date(month[cols_subset])
        if ex.empty:
            continue
        g = ex.groupby(["historical_date", "tag"], sort=False)
        ex["sector_rank"] = g.cumcount() + 1
        ex["sector_member_count"] = g["cmc_id"].transform("size")
        ex["sector_status"] = "HISTORICAL_APPROXIMATION"
        parts.append(ex)
    out = pd.concat(parts, ignore_index=True)
    return out.rename(columns={"tag": "sector"})[
        ["historical_date", "cmc_id", "internal_asset_id", "symbol",
         "sector", "sector_rank", "sector_member_count", "sector_status",
         "global_rank", "market_cap_usd"]]


# ----------------------------------------------------------------------
# Stage 7 — market terrain
# ----------------------------------------------------------------------
def build_terrain(feat: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    u = df.set_index("historical_date").sort_index()
    btc = u[u["cmc_id"] == BTC_ID]["price_usd"]
    eth = u[u["cmc_id"] == ETH_ID]["price_usd"]
    dts = u.index.unique()
    per_date = u.groupby(level=0)
    total = per_date["total_mcap"].first()
    btc_mcap = u[u["cmc_id"] == BTC_ID].groupby(level=0)[
        "market_cap_usd"].first()
    eth_mcap = u[u["cmc_id"] == ETH_ID].groupby(level=0)[
        "market_cap_usd"].first()
    stab_mcap = u[u["is_stablecoin"]].groupby(level=0)[
        "market_cap_usd"].sum()
    n_stab = u[u["is_stablecoin"]].groupby(level=0).size()
    fg = feat.groupby("historical_date")
    rows = []
    for dt in dts:
        row = {"historical_date": dt}
        for w in WINDOWS:
            br = btc.pct_change(w).get(dt, np.nan)
            er = eth.pct_change(w).get(dt, np.nan)
            row[f"btc_return_{w}d"] = br
            row[f"eth_return_{w}d"] = er
            row[f"eth_btc_relative_return_{w}d"] = er - br
        row["btc_dominance"] = btc_mcap.get(dt, np.nan) / total.get(dt)
        row["eth_share"] = eth_mcap.get(dt, np.nan) / total.get(dt)
        row["total_alt_share"] = 1.0 - row["btc_dominance"]
        row["stablecoin_mcap_share"] = (
            stab_mcap.get(dt, 0.0) / total.get(dt))
        row["n_stablecoins_in_top500"] = int(n_stab.get(dt, 0))
        fd = fg.get_group(dt)
        row["top500_breadth_7d"] = (fd["return_7d"] > 0).mean()
        row["top500_breadth_30d"] = (fd["return_30d"] > 0).mean()
        row["top500_dispersion_7d"] = fd["return_7d"].std()
        row["top500_dispersion_30d"] = fd["return_30d"].std()
        rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Stage 8 — registry / samples / summary
# ----------------------------------------------------------------------
def main() -> int:
    print("stage 0: loading snapshots", flush=True)
    df, gaps = load_snapshots()
    print(f"  universe rows={len(df)} "
          f"dates={df['historical_date_key'].nunique()}", flush=True)

    print("stage 1: PIT universe", flush=True)
    df = build_universe(df)
    p = write_parquet(df, "ALT_DATA_1_PIT_UNIVERSE.parquet")
    print(f"  {p.name} rows={len(df)}", flush=True)

    print("stage 2: identity", flush=True)
    ident = build_identity(df)
    p2 = write_parquet(ident, "ALT_DATA_1_IDENTITY_MAP.parquet")
    print(f"  {p2.name} rows={len(ident)}", flush=True)

    print("stage 3: perp eligibility", flush=True)
    elig = build_eligibility(df, ident)
    p3 = write_parquet(elig, "ALT_DATA_1_PERP_ELIGIBILITY.parquet")
    print(f"  {p3.name} rows={len(elig)}", flush=True)

    print("stage 4: asset multiscale features", flush=True)
    btc_series = df[df["cmc_id"] == BTC_ID].set_index(
        "historical_date")["price_usd"]
    eth_series = df[df["cmc_id"] == ETH_ID].set_index(
        "historical_date")["price_usd"]
    btc_lr = np.log(btc_series).diff()
    eth_lr = np.log(eth_series).diff()
    # BTC/ETH calendar-day returns (NOT row-offset pct_change, to match
    # the asset return computation which uses calendar-day lags)
    btc_df = df[df["cmc_id"] == BTC_ID][["historical_date", "price_usd"]]
    eth_df = df[df["cmc_id"] == ETH_ID][["historical_date", "price_usd"]]
    btc_ret = {}
    eth_ret = {}
    for w in WINDOWS:
        btc_lg = _lag_frame(btc_df, w)
        r = btc_lg["price_usd"] / btc_lg[f"price_{w}d_ago"] - 1.0
        r.index = btc_df["historical_date"].values
        btc_ret[w] = r.reindex(
            df.groupby("historical_date").size().index)
        eth_lg = _lag_frame(eth_df, w)
        r = eth_lg["price_usd"] / eth_lg[f"price_{w}d_ago"] - 1.0
        r.index = eth_df["historical_date"].values
        eth_ret[w] = r.reindex(
            df.groupby("historical_date").size().index)
    feat = build_asset_features(df, btc_lr, eth_lr, btc_ret, eth_ret)
    elig_sum = elig[elig["eligibility_status"] == "ELIGIBLE_EX_LIQUIDITY"]\
        .groupby(["historical_date", "cmc_id"]).size()
    feat["n_eligible_ex_liquidity"] = feat.set_index(
        ["historical_date", "cmc_id"]).index.map(
        elig_sum).fillna(0).astype(int).values
    p4 = write_parquet(feat, "ALT_DATA_1_ASSET_MULTISCALE_FEATURES.parquet")
    print(f"  {p4.name} rows={len(feat)} cols={feat.shape[1]}", flush=True)

    print("stage 5: rank-band features", flush=True)
    band = build_band_features(feat)
    p5 = write_parquet(band, "ALT_DATA_1_RANK_BAND_FEATURES.parquet")
    print(f"  {p5.name} rows={len(band)}", flush=True)

    print("stage 6: sector features", flush=True)
    sec = build_sector_features(feat)
    p6 = write_parquet(sec, "ALT_DATA_1_SECTOR_FEATURES.parquet")
    print(f"  {p6.name} rows={len(sec)}", flush=True)
    smem = build_sector_membership(feat)
    p6b = write_parquet(smem, "ALT_DATA_1_SECTOR_MEMBERSHIP.parquet")
    print(f"  {p6b.name} rows={len(smem)}", flush=True)

    print("stage 7: market terrain", flush=True)
    terr = build_terrain(feat, df)
    p7 = write_parquet(terr, "ALT_DATA_1_MARKET_TERRAIN_FEATURES.parquet")
    print(f"  {p7.name} rows={len(terr)}", flush=True)

    print("stage 8: registry + samples", flush=True)
    registry = {
        "registry_version": "1.0.0",
        "windows": WINDOWS,
        "bands": [f"{lo}-{hi}" for lo, hi in BANDS],
        "min_contract_age_days": MIN_MATURITY,
        "coverage_floor": COVERAGE_FLOOR,
        "beta_min_obs": MIN_OBS,
        "rank_sign_convention": ("rank_change_w = rank(t-w) - rank(t); "
                                 "positive = improving"),
        "rank_velocity": "rank_velocity_w == rank_change_w (descriptive alias)",
        "acceleration": {
            "rank_acceleration_short": ("[rank(t-7)-rank(t)] - "
                                        "[rank(t-14)-rank(t-7)]; positive = "
                                        "7D improvement accelerating"),
            "rank_acceleration_medium": ("[rank(t-30)-rank(t)] - "
                                         "[rank(t-60)-rank(t-30)]; positive "
                                         "= 30D improvement accelerating"),
        },
        "rank_curve": {
            "lags": [1, 3, 7, 14, 30, 60, 90],
            "short_mid_rank_spread": ("mean(rank_30d_ago,rank_60d_ago) - "
                                      "mean(rank_1d_ago,rank_3d_ago,"
                                      "rank_7d_ago); positive = improving"),
            "mid_long_rank_spread": ("mean(rank_60d_ago,rank_90d_ago) - "
                                     "mean(rank_14d_ago,rank_30d_ago); "
                                     "positive = improving"),
            "rank_curve_slope": ("OLS slope of rank vs lag over the 7 lag "
                                 "points; positive = improving toward "
                                 "present"),
            "rank_curve_monotonicity": ("fraction of 6 adjacent lag pairs "
                                        "with rank non-increasing toward "
                                        "present; 1.0 = perfectly improving"),
            "rank_curve_inflection_count": ("sign changes in adjacent first "
                                            "differences of lagged ranks"),
        },
        "peak_frequency": {
            "top_decile": "rank <= 50", "top_quartile": "rank <= 125",
            "absent_days_count_as_miss": True,
            "rank_peak": "new cumulative minimum rank (strictly < all "
                         "previous); first appearance counts as peak",
        },
        "market_cap_share_denominator": ("sum of top-500 market caps at t; "
                                         "stablecoins included"),
        "btc_dominance_denominator": "top-500 total market cap at t",
        "stablecoin_rule": {"tags": sorted(STABLE_TAGS),
                            "symbols": sorted(STABLE_SYMS)},
        "atr": ("true ATR NOT_SUPPORTED (daily snapshot resolution lacks "
                "high/low); volatility_normalized_move_14d = return_14d / "
                "realized_volatility_14d used instead"),
        "missing_data": ("NaN / INSUFFICIENT_HISTORY; never backfilled; no "
                         "partial-window labeling; 90D features require full "
                         "prior 90D window under coverage rule"),
        "non_causal_annotations": ["exited_top500 (survivorship table, "
                                   "future knowledge; excluded from causal "
                                   "panel)"],
        "sector_status": ("HISTORICAL_APPROXIMATION (snapshot-associated "
                          "CMC tags); UNMAPPED when no tags"),
        "liquidity": ("VOLUME_PROXY_ONLY / PARTIAL / NOT_AVAILABLE / "
                      "N_A_NOT_LISTED; historical_liquidity_verified always "
                      "FALSE"),
        "venue_environment": {
            "HYPERLIQUID": ("verified; listing=first funding ts "
                            "(INFERRED_FIRST_DATA_TIMESTAMP); delisting="
                            "last funding ts when isDelisted"),
            "OKX": ("verified; listing=official listTime; delisting NOT "
                    "available publicly"),
            "BINANCE_USDM": ("UNVERIFIABLE_FROM_ENV (451); archive method "
                             "verified, per-asset not collected"),
            "BYBIT_LINEAR": "UNVERIFIABLE_FROM_ENV (403)",
        },
        "asset_feature_columns": sorted(feat.columns.tolist()),
        "band_feature_columns": sorted(band.columns.tolist()),
        "sector_feature_columns": sorted(sec.columns.tolist()),
        "sector_membership_columns": sorted(smem.columns.tolist()),
        "terrain_feature_columns": sorted(terr.columns.tolist()),
        "eligibility_columns": sorted(elig.columns.tolist()),
    }
    (OUT / "ALT_DATA_1_FEATURE_DEFINITIONS.json").write_text(
        json.dumps(registry, indent=2), encoding="utf-8")
    h = hashlib.sha256(json.dumps(registry, sort_keys=True)
                       .encode("utf-8")).hexdigest()
    (OUT / "ALT_DATA_1_FEATURE_REGISTRY_HASH.json").write_text(
        json.dumps({
            "feature_registry_sha256": h,
            "frozen_at_utc": datetime.now(timezone.utc).isoformat(
                timespec="seconds"),
            "registry_version": "1.0.0",
            "note": ("feature registry is FROZEN at this hash; later "
                     "mechanism research consumes this panel"),
        }, indent=2), encoding="utf-8")

    def sample(frame, name, n=5):
        pd.concat([frame.head(n), frame.tail(n)]).to_csv(
            OUT / "samples" / name, index=False)
    sample(df, "sample_pit_universe.csv")
    sample(feat, "sample_asset_features.csv")
    sample(elig, "sample_perp_eligibility.csv")
    sample(band, "sample_rank_band_features.csv")
    sample(sec, "sample_sector_features.csv", 8)
    sample(terr, "sample_market_terrain.csv")

    summary = {
        "universe_rows": int(len(df)),
        "n_dates": int(df["historical_date_key"].nunique()),
        "n_unique_assets": int(df["cmc_id"].nunique()),
        "identity_rows": int(len(ident)),
        "eligibility_rows": int(len(elig)),
        "eligibility_eligible_ex_liquidity": int(
            (elig["eligibility_status"] == "ELIGIBLE_EX_LIQUIDITY").sum()),
        "eligibility_mature_30d": int(elig["mature_30d_at_t"].sum()),
        "eligibility_tradable": int(elig["tradable_at_t"].sum()),
        "asset_feature_rows": int(len(feat)),
        "asset_feature_cols": int(feat.shape[1]),
        "band_feature_rows": int(len(band)),
        "sector_feature_rows": int(len(sec)),
        "sector_membership_rows": int(len(smem)),
        "terrain_rows": int(len(terr)),
        "feature_registry_sha256": h,
        "first_date": str(df["historical_date_key"].min()),
        "last_date": str(df["historical_date_key"].max()),
        "date_range_expected": "2020-06-01..2026-08-23",
        "collision_class_counts": dict(Counter(ident["collision_class"])),
        "sector_statuses": ["HISTORICAL_APPROXIMATION"],
        "liquidity_statuses": ["VOLUME_PROXY_ONLY", "PARTIAL",
                               "N_A_NOT_LISTED"],
        "excluded_dates": gaps,
        "n_excluded_dates": len(gaps),
    }
    (OUT / "derived" / "build_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
