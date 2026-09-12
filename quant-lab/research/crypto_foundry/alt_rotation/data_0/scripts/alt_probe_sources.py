#!/usr/bin/env python3
"""ALT-DATA-0 live source probe harness.

Fetches small, representative samples from every audited provider,
persists raw bodies + sidecar metadata with full provenance
(retrieved_at, params, row counts, access class, limitations).

Read-only GET/POST requests. No keys required. Bounded call counts.
Rate-limit friendly sleeps.

Usage:
    python scripts/alt_probe_sources.py [--out ../probes/raw] [--only NAME,...]

Every persisted sample lands under <out>/<name>.json (raw body) and
<out>/<name>.meta.json (provenance sidecar).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept": "application/json"})

SCHEMA_VERSION = "1.0.0"
RUN_START = datetime.now(timezone.utc).isoformat(timespec="seconds")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(name: str, method: str, url: str, *, params=None, json_body=None,
          timeout: int = 25, headers=None, retries: int = 2) -> dict:
    """Perform one probe. Returns meta dict; raw body saved by caller."""
    attempts = 0
    last_err: Exception | None = None
    resp = None
    while attempts <= retries:
        attempts += 1
        try:
            resp = SESSION.request(method, url, params=params, json=json_body,
                                   timeout=timeout, headers=headers)
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.5)
    if resp is None:
        return {"ok": False, "error": f"{type(last_err).__name__}: {last_err}"}
    body = resp.content
    return {
        "ok": True,
        "status": resp.status_code,
        "final_url": resp.url,
        "body": body,
        "headers": dict(resp.headers),
    }


def summarize_json(raw: bytes) -> tuple[int, object, object]:
    """Best-effort (row_count, first_record, last_record) for a JSON body."""
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return 0, None, None
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        # common envelope keys
        for k in ("data", "result", "rows", "coins", "instruments", "universe"):
            if isinstance(data.get(k), list):
                rows = data[k]
                break
        else:
            rows = []
    else:
        rows = []
    first = rows[0] if rows else None
    last = rows[-1] if rows else None
    return len(rows), first, last


def save(out_dir: Path, name: str, method: str, url: str, params, json_body,
         meta_extra: dict, timeout: int = 25) -> dict:
    meta = fetch(name, method, url, params=params, json_body=json_body,
                 timeout=timeout)
    raw = meta.pop("body", b"")
    status = meta.get("status")
    # header blob for provenance (strip sensitive headers)
    hdrs = meta.pop("headers", {})
    hdrs_safe = {k: v for k, v in hdrs.items()
                 if k.lower() not in ("set-cookie", "x-api-key")}
    row_count, first, last = summarize_json(raw)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "probe": name,
        "method": method,
        "url": url,
        "request_params": params,
        "request_json": json_body,
        "request_headers": {"User-Agent": UA, "Accept": "application/json"},
        "retrieved_at": _now(),
        "http_status": status,
        "ok": meta.get("ok"),
        "error": meta.get("error"),
        "row_count": row_count,
        "first_record": first,
        "last_record": last,
        "sha256": sha256_bytes(raw),
        "bytes": len(raw),
        "access_class": meta_extra.get("access_class", "PUBLIC"),
        "historical_date": meta_extra.get("historical_date"),
        "known_limitations": meta_extra.get("known_limitations", ""),
        "notes": meta_extra.get("notes", ""),
        "final_url": meta.get("final_url"),
        "response_headers_safe": hdrs_safe,
    }
    (out_dir / f"{name}.json").write_bytes(raw)
    (out_dir / f"{name}.meta.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return payload


def probe_loop(out_dir: Path, name: str, desc: str, rows: list[dict],
               access_class: str, sleep: float = 0.25) -> None:
    """Probe a list of (label, method, url, params, json_body) rows and
    persist a single composite result with per-row status."""
    results = []
    for r in rows:
        meta = fetch(r["label"], r["method"], r["url"], params=r.get("params"),
                     json_body=r.get("json_body"), timeout=20)
        raw = meta.pop("body", b"")
        row_count, first, last = summarize_json(raw)
        results.append({
            "label": r["label"],
            "method": r["method"],
            "url": r["url"],
            "params": r.get("params"),
            "json_body": r.get("json_body"),
            "http_status": meta.get("status"),
            "ok": meta.get("ok"),
            "error": meta.get("error"),
            "row_count": row_count,
            "first_record": first,
            "last_record": last,
            "sha256": sha256_bytes(raw),
            "bytes": len(raw),
        })
        time.sleep(sleep)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "probe": name,
        "description": desc,
        "retrieved_at": _now(),
        "access_class": access_class,
        "rows": results,
        "known_limitations": "Composite probe; per-row status recorded.",
    }
    (out_dir / f"{name}.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8")
    (out_dir / f"{name}.meta.json").write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "probe": name,
                    "description": desc, "retrieved_at": _now(),
                    "access_class": access_class,
                    "composite": True, "n_rows": len(results)},
                   indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--only", default=None,
                    help="comma-separated probe name prefixes to run")
    args = ap.parse_args()

    out_dir = Path(args.out) if args.out else (
        Path(__file__).resolve().parent.parent / "probes" / "raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    only = [p.strip() for p in args.only.split(",")] if args.only else None

    def should(name: str) -> bool:
        return only is None or any(name.startswith(p) for p in only)

    summary = []

    def run(name: str, method: str, url: str, *, params=None, json_body=None,
            access_class: str = "PUBLIC", sleep: float = 0.0,
            historical_date: str | None = None,
            limitations: str = "", notes: str = "",
            timeout: int = 25) -> None:
        if not should(name):
            return
        if sleep:
            time.sleep(sleep)
        p = save(out_dir, name, method, url, params, json_body, {
            "access_class": access_class,
            "historical_date": historical_date,
            "known_limitations": limitations,
            "notes": notes,
        }, timeout=timeout)
        summary.append((name, p.get("http_status"), p.get("row_count"),
                        p.get("sha256", "")[:12], p.get("error", "")))
        print(f"[{p.get('http_status')}] {name:44s} rows={p.get('row_count'):>7}"
              f" sha={p.get('sha256','')[:12]} {p.get('error','')}",
              flush=True)

    # ------------------------------------------------------------------
    # COINGECKO (free demo tier, ~10-15 calls/min without key)
    # ------------------------------------------------------------------
    CG = "https://api.coingecko.com/api/v3"
    run("coingecko_ping", "GET", f"{CG}/ping", sleep=2.0,
        notes="connectivity probe")
    run("coingecko_coins_list", "GET", f"{CG}/coins/list?include_platform=true",
        sleep=6.0, access_class="PUBLIC_RATELIMITED",
        notes="full coin registry incl. inactive/dead coins; platform "
              "contract addresses. Registry, NOT a top-N list.",
        limitations="free tier; ~20k rows; list may lag delistings")
    run("coingecko_markets_top250", "GET", f"{CG}/coins/markets",
        params={"vs_currency": "usd", "order": "market_cap_desc",
                "per_page": 250, "page": 1, "sparkline": "false"},
        sleep=7.0, access_class="PUBLIC_RATELIMITED",
        historical_date="2026-08-24",
        notes="CURRENT top-250 snapshot (never used as historical truth)")
    run("coingecko_categories_list", "GET", f"{CG}/coins/categories/list",
        sleep=7.0, access_class="PUBLIC_RATELIMITED",
        notes="category taxonomy ids (current)")
    run("coingecko_btc_market_chart_max", "GET",
        f"{CG}/coins/bitcoin/market_chart",
        params={"vs_currency": "usd", "days": "max"},
        sleep=8.0, access_class="PUBLIC_RATELIMITED",
        notes="historical price/mcap/total_volumes for BTC (enrichment)",
        limitations="free tier granularity; mcap is derived series")
    run("coingecko_lunc_market_chart_max", "GET",
        f"{CG}/coins/terra-luna-classic/market_chart",
        params={"vs_currency": "usd", "days": "max"},
        sleep=8.0, access_class="PUBLIC_RATELIMITED",
        notes="DEAD coin (LUNC crash 2022-05) historical series — "
              "rank-survivorship evidence",
        limitations="free tier granularity")
    run("coingecko_ftt_market_chart_max", "GET",
        f"{CG}/coins/ftx-token/market_chart",
        params={"vs_currency": "usd", "days": "max"},
        sleep=8.0, access_class="PUBLIC_RATELIMITED",
        notes="DEAD coin (FTT crash 2022-11) historical series",
        limitations="free tier granularity")
    run("coingecko_serum_market_chart_max", "GET",
        f"{CG}/coins/serum/market_chart",
        params={"vs_currency": "usd", "days": "max"},
        sleep=8.0, access_class="PUBLIC_RATELIMITED",
        notes="FAILED coin (SRM) historical series",
        limitations="free tier granularity")
    run("coingecko_btc_meta", "GET", f"{CG}/coins/bitcoin",
        params={"localization": "false", "tickers": "false",
                "market_data": "false", "community_data": "false",
                "developer_data": "false"},
        sleep=7.0, access_class="PUBLIC_RATELIMITED",
        notes="coin metadata: categories, links, genesis date")
    run("coingecko_global", "GET", f"{CG}/global", sleep=7.0,
        access_class="PUBLIC_RATELIMITED",
        notes="current global market cap (context only)")

    # ------------------------------------------------------------------
    # COINPAPRIKA (free; generous rate limits)
    # ------------------------------------------------------------------
    CP = "https://api.coinpaprika.com/v1"
    run("coinpaprika_coins", "GET", f"{CP}/coins", sleep=0.8,
        notes="full coin list incl. is_active flag; ID = stable-ish slug",
        limitations="id is a slug; renames change id")
    run("coinpaprika_tickers_top20", "GET", f"{CP}/tickers",
        params={"quotes": "USD", "limit": 20}, sleep=0.8,
        historical_date="2026-08-24",
        notes="current top-20 with rank + mcap (never historical truth)")
    run("coinpaprika_btc_historical_rank", "GET",
        f"{CP}/tickers/btc-bitcoin/historical",
        params={"start": "2024-05-25", "end": "2024-06-05", "interval": "1d"},
        sleep=0.8, access_class="PUBLIC",
        historical_date="2024-06-01",
        notes="daily RANK + mcap per coin — key PIT rank reconstruction "
              "mechanism (per-coin daily rank). Expect 402 on free plan.")
    run("coinpaprika_btc_historical_recent", "GET",
        f"{CP}/tickers/btc-bitcoin/historical",
        params={"start": "2026-08-20", "end": "2026-08-24",
                "interval": "1d"},
        sleep=0.8, access_class="PUBLIC",
        historical_date="2026-08-20",
        notes="boundary probe: is ANY historical window free, or is all "
              "pre-now history paid-gated?")
    run("coinpaprika_btc_ticker_current", "GET", f"{CP}/tickers/btc-bitcoin",
        params={"quotes": "USD"}, sleep=0.8, access_class="PUBLIC",
        historical_date="2026-08-24",
        notes="current single ticker incl. rank (free-plan baseline)")
    run("coinpaprika_lunc_historical_rank", "GET",
        f"{CP}/tickers/terra-luna/historical",
        params={"start": "2022-04-25", "end": "2022-05-15", "interval": "1d"},
        sleep=0.8, access_class="PUBLIC",
        historical_date="2022-05-10",
        notes="DEAD coin daily rank around LUNA crash — survivorship evidence",
        limitations="id 'terra-luna' vs 'terra-luna-classic' naming")
    run("coinpaprika_ftt_historical_rank", "GET",
        f"{CP}/tickers/ftx-token/historical",
        params={"start": "2022-10-25", "end": "2022-11-15", "interval": "1d"},
        sleep=0.8, access_class="PUBLIC",
        historical_date="2022-11-10",
        notes="DEAD coin (FTT) daily rank around FTX collapse")
    run("coinpaprika_serum_meta", "GET", f"{CP}/coins/serum", sleep=0.8,
        notes="inactive coin metadata (rank=0, is_active=false)")
    run("coinpaprika_global", "GET", f"{CP}/global", sleep=0.8,
        notes="current global snapshot (context)")

    # ------------------------------------------------------------------
    # COINMARKETCAP — web historical page + paid API probe
    # ------------------------------------------------------------------
    run("coinmarketcap_web_historical_20240601", "GET",
        "https://coinmarketcap.com/historical/20240601/", sleep=1.0,
        access_class="WEB_ONLY",
        historical_date="2024-06-01",
        notes="web snapshot page probe; classify anti-bot behavior",
        limitations="page is JS-rendered; rank depth per page unknown until "
                    "rendered")
    run("coinmarketcap_api_historical_no_key", "GET",
        "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/historical",
        params={"date": "2024-06-01", "start": 1, "limit": 100},
        sleep=1.0, access_class="PAID",
        historical_date="2024-06-01",
        notes="Pro API historical listings WITHOUT key — expect 401 "
              "(documents PAID_REQUIRED)")
    run("coinmarketcap_web_api_historical_probe", "GET",
        "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/historical",
        params={"id": 1, "convertId": 2781, "timeStart": 1717200000000,
                "timeEnd": 1717286400000},
        sleep=1.0, access_class="WEB_ONLY",
        historical_date="2024-06-01",
        notes="internal data-api used by the website — classify availability",
        limitations="internal endpoint; behavior may change; do not rely on")

    # ------------------------------------------------------------------
    # DEXSCREENER
    # ------------------------------------------------------------------
    run("dexscreener_tokens_weth", "GET",
        "https://api.dexscreener.com/latest/dex/tokens/"
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", sleep=1.0,
        timeout=45,
        notes="WETH token -> pairs with pairCreatedAt, liquidity, volume, fdv",
        limitations="current pairs only; historical liquidity NOT available; "
                    "endpoint slow from some networks")
    run("dexscreener_token_pairs_v1_weth", "GET",
        "https://api.dexscreener.com/token-pairs/v1/ethereum/"
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", sleep=1.0,
        timeout=45,
        notes="token-pairs v1 endpoint (pairCreatedAt evidence)")

    # ------------------------------------------------------------------
    # DEXPAPRIKA
    # ------------------------------------------------------------------
    DP = "https://api.dexpaprika.com/api/v1"
    run("dexpaprika_networks", "GET", f"{DP}/networks", sleep=1.0,
        notes="supported networks list (api/v1 base path)")
    run("dexpaprika_token_weth", "GET",
        f"{DP}/tokens/ethereum/0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        sleep=1.0,
        notes="token detail incl. pairs; pair created_at evidence")
    run("dexpaprika_pairs_weth_usdc", "GET",
        f"{DP}/pairs/ethereum/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        sleep=1.0,
        notes="specific pair detail (created_at / liquidity history?)",
        limitations="probe may 404 if pair address unknown; recorded as-is")

    # ------------------------------------------------------------------
    # BINANCE USD-M
    # ------------------------------------------------------------------
    BN = "https://fapi.binance.com"
    run("binance_fapi_ping", "GET", f"{BN}/fapi/v1/ping", sleep=0.4,
        notes="connectivity probe — classifies geo-block scope")
    run("binance_spot_ping", "GET", "https://api.binance.com/api/v3/ping",
        sleep=0.4, notes="spot main API connectivity probe")
    run("binance_spot_mirror_klines", "GET",
        "https://data-api.binance.vision/api/v3/klines",
        params={"symbol": "BTCUSDT", "interval": "1d", "limit": 3},
        sleep=0.4,
        notes="public spot data mirror (not geo-blocked) — spot klines work "
              "from this environment")
    run("binance_fapi_mirror_exchange_info", "GET",
        "https://data-api.binance.vision/fapi/v1/exchangeInfo", sleep=0.4,
        notes="probe whether USD-M mirror exists on data-api.binance.vision")
    run("binance_fapi_exchange_info", "GET", f"{BN}/fapi/v1/exchangeInfo",
        sleep=0.4,
        notes="current USD-M contracts incl. onboardDate, deliveryDate, "
              "status; contractType 1000x naming visible",
        limitations="delisted contracts NOT in exchangeInfo; endpoint may be "
                    "geo-blocked from some locations (451)")
    run("binance_fapi_btc_klines_oldest", "GET",
        f"{BN}/fapi/v1/klines",
        params={"symbol": "BTCUSDT", "interval": "1d", "startTime": 0,
                "limit": 1000},
        sleep=0.4,
        notes="oldest BTCUSDT daily bars (INFERRED_FIRST_DATA_TIMESTAMP)")
    run("binance_fapi_btc_funding_oldest", "GET",
        f"{BN}/fapi/v1/fundingRate",
        params={"symbol": "BTCUSDT", "startTime": 0, "limit": 1000},
        sleep=0.4,
        notes="oldest BTCUSDT funding records (listing lower bound)")
    probe_loop(out_dir, "binance_delisted_candidates", "Binance USD-M "
               "delisted-contract recovery probe", [
        {"label": "SRMUSDT-funding",
         "method": "GET", "url": f"{BN}/fapi/v1/fundingRate",
         "params": {"symbol": "SRMUSDT", "limit": 3}},
        {"label": "SRMUSDT-klines",
         "method": "GET", "url": f"{BN}/fapi/v1/klines",
         "params": {"symbol": "SRMUSDT", "interval": "1d", "limit": 3}},
        {"label": "FTTUSDT-funding",
         "method": "GET", "url": f"{BN}/fapi/v1/fundingRate",
         "params": {"symbol": "FTTUSDT", "limit": 3}},
        {"label": "FTTUSDT-klines",
         "method": "GET", "url": f"{BN}/fapi/v1/klines",
         "params": {"symbol": "FTTUSDT", "interval": "1d", "limit": 3}},
        {"label": "BTCSTUSDT-funding",
         "method": "GET", "url": f"{BN}/fapi/v1/fundingRate",
         "params": {"symbol": "BTCSTUSDT", "limit": 3}},
        {"label": "BTCSTUSDT-klines",
         "method": "GET", "url": f"{BN}/fapi/v1/klines",
         "params": {"symbol": "BTCSTUSDT", "interval": "1d", "limit": 3}},
        {"label": "LUNA2USDT-funding",
         "method": "GET", "url": f"{BN}/fapi/v1/fundingRate",
         "params": {"symbol": "LUNA2USDT", "limit": 3}},
        {"label": "HOTUSDT-klines",
         "method": "GET", "url": f"{BN}/fapi/v1/klines",
         "params": {"symbol": "HOTUSDT", "interval": "1d", "limit": 3}},
        {"label": "BTSUSDT-klines",
         "method": "GET", "url": f"{BN}/fapi/v1/klines",
         "params": {"symbol": "BTSUSDT", "interval": "1d", "limit": 3}},
        {"label": "DREPUSDT-klines",
         "method": "GET", "url": f"{BN}/fapi/v1/klines",
         "params": {"symbol": "DREPUSDT", "interval": "1d", "limit": 3}},
    ], access_class="PUBLIC", sleep=0.4)
    run("binance_fapi_trading_status", "GET", f"{BN}/fapi/v1/tradingStatus",
        sleep=0.4, notes="account-free status endpoint (context)")

    # ------------------------------------------------------------------
    # BYBIT LINEAR
    # ------------------------------------------------------------------
    BB = "https://api.bybit.com/v5/market"
    run("bybit_instruments_linear_p1", "GET",
        f"{BB}/instruments-info",
        params={"category": "linear", "limit": 1000}, sleep=0.5,
        notes="linear instrument info page 1: launchTime, deliveryTime, "
              "status, contractType, baseCoin/quoteCoin/settleCoin",
        limitations="1000/page; page 2 fetched below; delisted may or may "
                    "not be included")
    run("bybit_instruments_linear_p2", "GET",
        f"{BB}/instruments-info",
        params={"category": "linear", "limit": 1000, "cursor": ""},
        sleep=0.5,
        notes="page 2 to count total + closed instruments")
    probe_loop(out_dir, "bybit_delisted_candidates",
               "Bybit delisted linear recovery probe", [
        {"label": "SRMUSDT-instrument",
         "method": "GET", "url": f"{BB}/instruments-info",
         "params": {"category": "linear", "symbol": "SRMUSDT"}},
        {"label": "SRMUSDT-kline",
         "method": "GET", "url": f"{BB}/kline",
         "params": {"category": "linear", "symbol": "SRMUSDT", "interval": "D",
                    "limit": 3}},
        {"label": "FTTUSDT-instrument",
         "method": "GET", "url": f"{BB}/instruments-info",
         "params": {"category": "linear", "symbol": "FTTUSDT"}},
        {"label": "LUNA2USDT-instrument",
         "method": "GET", "url": f"{BB}/instruments-info",
         "params": {"category": "linear", "symbol": "LUNA2USDT"}},
        {"label": "BTCSTUSDT-instrument",
         "method": "GET", "url": f"{BB}/instruments-info",
         "params": {"category": "linear", "symbol": "BTCSTUSDT"}},
        {"label": "HOTUSDT-instrument",
         "method": "GET", "url": f"{BB}/instruments-info",
         "params": {"category": "linear", "symbol": "HOTUSDT"}},
    ], access_class="PUBLIC", sleep=0.5)
    run("bybit_funding_btc_oldest", "GET", f"{BB}/funding/history",
        params={"category": "linear", "symbol": "BTCUSDT",
                "startTime": 0, "endTime": 1600000000000, "limit": 200},
        sleep=0.5,
        notes="oldest BTCUSDT funding records (listing lower bound)")

    # ------------------------------------------------------------------
    # OKX SWAP
    # ------------------------------------------------------------------
    OK = "https://www.okx.com/api/v5/public"
    run("okx_instruments_swap", "GET", f"{OK}/instruments",
        params={"instType": "SWAP"}, sleep=0.5,
        notes="SWAP instruments: listTime, state, ctVal, settleCcy",
        limitations="delisted instruments expected absent; state values "
                    "recorded")
    run("okx_btc_swap_funding_oldest", "GET",
        f"{OK}/funding-rate-history",
        params={"instId": "BTC-USDT-SWAP", "after": "0", "limit": "100"},
        sleep=0.5,
        notes="oldest BTC-USDT-SWAP funding (listing lower bound)")
    probe_loop(out_dir, "okx_delisted_candidates",
               "OKX delisted SWAP recovery probe", [
        {"label": "FTT-USDT-SWAP-instrument",
         "method": "GET", "url": f"{OK}/instruments",
         "params": {"instType": "SWAP", "instId": "FTT-USDT-SWAP"}},
        {"label": "FTT-USDT-SWAP-funding",
         "method": "GET", "url": f"{OK}/funding-rate-history",
         "params": {"instId": "FTT-USDT-SWAP", "limit": "3"}},
        {"label": "SRM-USDT-SWAP-instrument",
         "method": "GET", "url": f"{OK}/instruments",
         "params": {"instType": "SWAP", "instId": "SRM-USDT-SWAP"}},
        {"label": "BTC-USDT-SWAP-instrument",
         "method": "GET", "url": f"{OK}/instruments",
         "params": {"instType": "SWAP", "instId": "BTC-USDT-SWAP"}},
    ], access_class="PUBLIC", sleep=0.5)

    # ------------------------------------------------------------------
    # HYPERLIQUID
    # ------------------------------------------------------------------
    HL = "https://api.hyperliquid.xyz/info"
    run("hyperliquid_meta", "POST", HL, json_body={"type": "meta"},
        sleep=0.8,
        notes="current perp universe (names, szDecimals, maxLeverage)",
        limitations="CURRENT only; no historical universe versioning via API")
    run("hyperliquid_meta_and_asset_ctxs", "POST", HL,
        json_body={"type": "metaAndAssetCtxs"}, sleep=0.8,
        notes="universe + context: funding, openInterest, markPx, dayNtlVlm",
        limitations="CURRENT snapshot only")
    run("hyperliquid_funding_btc_oldest", "POST", HL,
        json_body={"type": "fundingHistory", "coin": "BTC", "startTime": 0,
                   "endTime": 2000000000000}, sleep=0.8,
        notes="oldest BTC funding records (INFERRED first-existence lower "
              "bound)",
        limitations="500-row window; oldest returned when startTime=0")
    run("hyperliquid_candles_btc_oldest", "POST", HL,
        json_body={"type": "candleSnapshot",
                   "req": {"coin": "BTC", "interval": "1d", "startTime": 0,
                           "endTime": 2000000000000}},
        sleep=0.8,
        notes="oldest BTC daily candles (INFERRED_FIRST_DATA_TIMESTAMP)")
    probe_loop(out_dir, "hyperliquid_delisted_candidates",
               "Hyperliquid delisted-coin recovery probe (funding history "
               "for coins absent from current meta)", [
        {"label": "LUNA2-funding",
         "method": "POST", "url": HL,
         "json_body": {"type": "fundingHistory", "coin": "LUNA2",
                       "startTime": 0, "endTime": 2000000000000}},
        {"label": "LUNC-funding",
         "method": "POST", "url": HL,
         "json_body": {"type": "fundingHistory", "coin": "LUNC",
                       "startTime": 0, "endTime": 2000000000000}},
        {"label": "FTT-funding",
         "method": "POST", "url": HL,
         "json_body": {"type": "fundingHistory", "coin": "FTT",
                       "startTime": 0, "endTime": 2000000000000}},
        {"label": "SRM-funding",
         "method": "POST", "url": HL,
         "json_body": {"type": "fundingHistory", "coin": "SRM",
                       "startTime": 0, "endTime": 2000000000000}},
        {"label": "HOT-funding",
         "method": "POST", "url": HL,
         "json_body": {"type": "fundingHistory", "coin": "HOT",
                       "startTime": 0, "endTime": 2000000000000}},
        {"label": "BTS-funding",
         "method": "POST", "url": HL,
         "json_body": {"type": "fundingHistory", "coin": "BTS",
                       "startTime": 0, "endTime": 2000000000000}},
    ], access_class="PUBLIC", sleep=0.8)

    # ------------------------------------------------------------------
    # wrap up
    # ------------------------------------------------------------------
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "run_started_at": RUN_START,
        "run_finished_at": _now(),
        "probe_count": len(summary),
        "probes": [{"name": n, "http_status": s, "row_count": r,
                    "sha256_prefix": h, "error": e}
                   for n, s, r, h, e in summary],
    }
    (out_dir / "_run_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n{len(summary)} probes persisted under {out_dir}")


if __name__ == "__main__":
    sys.exit(main())
