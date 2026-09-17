#!/usr/bin/env python3
"""ALT-DATA-0 second-wave probes.

Targets remaining unknowns after wave 1:
- CMC internal data-api: per-coin historical quotes (recent window),
  historical ranked listings (snapshot) — the decisive PIT-rank test
- Binance web bapi: USD-M exchange-info + delisted archive guesses
- DexPaprika: correct base paths (networks, token, pools search, pool,
  OHLCV)
- DexScreener retry
- OKX funding pagination semantics (walk to oldest)
- Hyperliquid: probe real delisted coin names (from web research)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept": "application/json"})
SCHEMA_VERSION = "1.0.0"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def summarize(raw: bytes):
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return 0, None, None
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        rows = data.get("data")
        if isinstance(rows, list):
            pass
        elif isinstance(rows, dict):
            rows = [rows]
        else:
            rows = []
    else:
        rows = []
    return len(rows), (rows[0] if rows else None), (rows[-1] if rows else None)


def probe(out: Path, name: str, method: str, url: str, *, params=None,
          json_body=None, timeout: int = 30, access="PUBLIC",
          notes="", limitations="", sleep_after: float = 0.0):
    meta = {"ok": False}
    try:
        r = S.request(method, url, params=params, json=json_body,
                      timeout=timeout)
        meta = {"ok": True, "status": r.status_code, "final_url": r.url,
                "headers": dict(r.headers)}
        raw = r.content
    except Exception as e:  # noqa: BLE001
        meta = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        raw = b""
    rc, first, last = summarize(raw)
    payload = {
        "schema_version": SCHEMA_VERSION, "probe": name, "method": method,
        "url": url, "request_params": params, "request_json": json_body,
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "http_status": meta.get("status"), "ok": meta.get("ok"),
        "error": meta.get("error"), "row_count": rc, "first_record": first,
        "last_record": last, "sha256": sha256_bytes(raw), "bytes": len(raw),
        "access_class": access, "notes": notes,
        "known_limitations": limitations,
    }
    (out / f"{name}.json").write_bytes(raw)
    (out / f"{name}.meta.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"[{payload.get('http_status')}] {name:46s} rows={rc:>7} "
          f"sha={payload['sha256'][:12]} {payload.get('error','')}", flush=True)
    if sleep_after:
        time.sleep(sleep_after)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = Path(args.out) if args.out else (
        Path(__file__).resolve().parent.parent / "probes" / "raw")
    out.mkdir(parents=True, exist_ok=True)

    # --- CMC internal data-api ---
    probe(out, "cmc_dataapi_btc_recent_window", "GET",
          "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/historical",
          params={"id": 1, "convertId": 2781, "timeStart": 1755648000000,
                  "timeEnd": 1755820800000},
          access="WEB_ONLY",
          notes="recent-window test: does per-coin historical ever return "
                "quotes on the internal data-api?",
          limitations="internal endpoint; may require web session")
    time.sleep(1)
    probe(out, "cmc_dataapi_listings_historical_20240601", "GET",
          "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listings/historical",
          params={"date": "2024-06-01", "start": 1, "limit": 100},
          access="WEB_ONLY",
          notes="ranked snapshot guess: the endpoint the historical page "
                "would call; if it returns ranked rows this is the PIT "
                "snapshot path",
          limitations="guess at endpoint shape")
    time.sleep(1)
    probe(out, "cmc_dataapi_listings_historical_20240601_v2", "GET",
          "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listings/historical",
          params={"date": "2024-06-01", "start": 1, "limit": 100,
                  "convertId": 2781, "sortBy": "market_cap",
                  "sortType": "desc"},
          access="WEB_ONLY",
          notes="variant with convertId/sort params")
    time.sleep(1)
    probe(out, "cmc_dataapi_spotlight_historical_20240601", "GET",
          "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/spotlight",
          params={"date": "2024-06-01"},
          access="WEB_ONLY",
          notes="spotlight variant probe")

    # --- Binance web bapi guesses ---
    probe(out, "binance_bapi_futures_exchange_info", "GET",
          "https://www.binance.com/bapi/futures/v1/public/future/common/get-exchange-info",
          access="WEB_ONLY", sleep_after=0.5,
          notes="web bapi USD-M exchange info (may bypass 451 geo-block)",
          limitations="guess at bapi path")
    probe(out, "binance_bapi_delist_list", "GET",
          "https://www.binance.com/bapi/futures/v1/public/future/common/delist-list",
          access="WEB_ONLY", sleep_after=0.5,
          notes="delisted futures archive guess",
          limitations="guess at bapi path")

    # --- DexPaprika (correct base) ---
    DP = "https://api.dexpaprika.com"
    probe(out, "dexpaprika_networks_v2", "GET", f"{DP}/networks",
          access="PUBLIC", notes="networks list (correct base path)")
    time.sleep(1)
    probe(out, "dexpaprika_token_weth_v2", "GET",
          f"{DP}/networks/ethereum/tokens/0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
          access="PUBLIC",
          notes="token detail: added_at (token creation), summary liquidity/volume")
    time.sleep(1)
    probe(out, "dexpaprika_pools_search_weth", "GET",
          f"{DP}/networks/ethereum/pools/search",
          params={"token_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                  "limit": 5},
          access="PUBLIC",
          notes="pool search: creation date filter capability + pool addresses")
    time.sleep(1)
    probe(out, "dexpaprika_search_uniswap", "GET", f"{DP}/search",
          params={"query": "uniswap"}, access="PUBLIC",
          notes="search endpoint sanity")
    time.sleep(1)
    probe(out, "dexpaprika_ohlcv_guess", "GET",
          f"{DP}/networks/ethereum/pools/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640/ohlcv",
          params={"time_start": "2024-06-01T00:00:00Z",
                  "time_end": "2024-06-08T00:00:00Z"},
          access="PUBLIC",
          notes="historical OHLCV guess for a pool",
          limitations="guess at endpoint shape; may 404")

    # --- DexScreener retry ---
    probe(out, "dexscreener_tokens_weth_retry", "GET",
          "https://api.dexscreener.com/latest/dex/tokens/0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
          timeout=60, access="PUBLIC",
          notes="retry after wave-1 timeout",
          limitations="endpoint slow/unreachable from some networks")

    # --- OKX funding pagination semantics ---
    probe(out, "okx_btc_swap_funding_after_2021", "GET",
          "https://www.okx.com/api/v5/public/funding-rate-history",
          params={"instId": "BTC-USDT-SWAP", "after": "1640000000000",
                  "limit": "5"},
          access="PUBLIC", sleep_after=0.5,
          notes="funding pagination: records older than 2021-12-20? "
                "(walks toward oldest)")

    # --- Hyperliquid real delisted names (from web research) ---
    HL = "https://api.hyperliquid.xyz/info"
    for coin in ["WIF", "GALA", "AXS", "NEO"]:
        probe(out, f"hyperliquid_funding_{coin.lower()}_oldest", "POST", HL,
              json_body={"type": "fundingHistory", "coin": coin,
                         "startTime": 0, "endTime": 2000000000000},
              access="PUBLIC", sleep_after=0.5,
              notes=f"oldest funding for {coin} — probes delisted-recovery "
                    "semantics")


if __name__ == "__main__":
    sys.exit(main())
