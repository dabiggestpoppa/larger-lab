#!/usr/bin/env python3
"""ALT-DATA-0 wave-3 probes.

- CMC internal data-api: full ranked snapshots (top-N) for all 5
  preregistered prototype dates — the PIT rank universe evidence
- Binance public data archive (data.binance.vision): USD-M monthly klines
  for current AND delisted symbols — delisted-contract bar recovery
- OKX funding history depth probe
- CoinPaprika historical cross-check for in-window prototype dates
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept": "application/json"})
SCHEMA_VERSION = "1.0.0"

DATES = ["2024-06-01", "2025-01-01", "2025-06-01", "2026-01-01", "2026-08-20"]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def persist(out: Path, name: str, raw: bytes, meta: dict):
    (out / f"{name}.json").write_bytes(raw)
    meta.update({"sha256": sha256_bytes(raw), "bytes": len(raw),
                 "retrieved_at":
                 datetime.now(timezone.utc).isoformat(timespec="seconds")})
    (out / f"{name}.meta.json").write_text(
        json.dumps(meta, indent=2, default=str), encoding="utf-8")


def get(out: Path, name: str, url: str, *, params=None, notes="",
         limitations="", access="WEB_ONLY", sleep_after=0.0) -> bytes:
    try:
        r = S.get(url, params=params, timeout=40)
        raw = r.content
        meta = {"probe": name, "method": "GET", "url": r.url,
                "request_params": params, "http_status": r.status_code,
                "ok": r.status_code < 400, "access_class": access,
                "notes": notes, "known_limitations": limitations}
    except Exception as e:  # noqa: BLE001
        raw = b""
        meta = {"probe": name, "method": "GET", "url": url,
                "request_params": params, "http_status": None,
                "ok": False, "error": f"{type(e).__name__}: {e}",
                "access_class": access, "notes": notes,
                "known_limitations": limitations}
    persist(out, name, raw, meta)
    rc = "n/a"
    if raw:
        try:
            rc = len(json.loads(raw.decode("utf-8")))
        except Exception:
            rc = len(raw)
    print(f"[{meta.get('http_status')}] {name:48s} bytes={len(raw):>9} "
          f"sha={sha256_bytes(raw)[:12]} {meta.get('error','')}", flush=True)
    if sleep_after:
        time.sleep(sleep_after)
    return raw


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = Path(args.out) if args.out else (
        Path(__file__).resolve().parent.parent / "probes" / "raw")
    out.mkdir(parents=True, exist_ok=True)

    # ---- CMC ranked snapshots for all prototype dates ----
    for dt in DATES:
        get(out, f"cmc_snapshot_{dt.replace('-', '')}_top500",
            "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listings/historical",
            params={"date": dt, "start": 1, "limit": 500, "convertId": 2781},
            notes=f"PIT ranked snapshot for {dt} (limit 500) via CMC "
                  "internal data-api (web-only)",
            limitations="internal endpoint; TOS: web scraping terms apply; "
                        "verify limit=500 honored via row count",
            sleep_after=1.0)

    # ---- Binance public data archive: USD-M monthly klines ----
    get(out, "binance_archive_btcusdt_2024_06",
        "https://data.binance.vision/data/futures/um/monthly/klines/"
        "BTCUSDT/1d/BTCUSDT-1d-2024-06.zip",
        access="PUBLIC", sleep_after=0.5,
        notes="official bulk archive: USD-M monthly klines (BTCUSDT 2024-06)",
        limitations="zip body; provenance hash over zip bytes")
    get(out, "binance_archive_srmusdt_2022_10",
        "https://data.binance.vision/data/futures/um/monthly/klines/"
        "SRMUSDT/1d/SRMUSDT-1d-2022-10.zip",
        access="PUBLIC", sleep_after=0.5,
        notes="delisted SRMUSDT monthly klines from official archive "
              "(delisted-contract bar recovery test)",
        limitations="zip body; 404 = archive does not retain this symbol")
    get(out, "binance_archive_fttusdt_2022_11",
        "https://data.binance.vision/data/futures/um/monthly/klines/"
        "FTTUSDT/1d/FTTUSDT-1d-2022-11.zip",
        access="PUBLIC", sleep_after=0.5,
        notes="delisted FTTUSDT monthly klines from official archive",
        limitations="zip body")
    get(out, "binance_archive_luna2usdt_2022_07",
        "https://data.binance.vision/data/futures/um/monthly/klines/"
        "LUNA2USDT/1d/LUNA2USDT-1d-2022-07.zip",
        access="PUBLIC", sleep_after=0.5,
        notes="renamed-contract LUNA2USDT monthly klines from archive",
        limitations="zip body")

    # ---- OKX funding depth ----
    get(out, "okx_btc_swap_funding_recent",
        "https://www.okx.com/api/v5/public/funding-rate-history",
        params={"instId": "BTC-USDT-SWAP", "limit": "5"},
        access="PUBLIC", sleep_after=0.5,
        notes="OKX funding history recent rows (depth classification)")
    get(out, "okx_btc_swap_funding_before_2023",
        "https://www.okx.com/api/v5/public/funding-rate-history",
        params={"instId": "BTC-USDT-SWAP", "before": "1672531200000",
                "limit": "5"},
        access="PUBLIC", sleep_after=0.5,
        notes="OKX funding history before 2023-01-01 — tests how far back "
              "funding history is retained")

    # ---- CoinPaprika cross-check for in-window dates ----
    CP = "https://api.coinpaprika.com/v1"
    get(out, "coinpaprika_historical_20260820_btc",
        f"{CP}/tickers/btc-bitcoin/historical",
        params={"start": "2026-08-19", "end": "2026-08-21",
                "interval": "1d"},
        access="PUBLIC", sleep_after=0.5,
        notes="CoinPaprika in-window cross-check (2026-08-20)")
    get(out, "coinpaprika_historical_20260101_btc",
        f"{CP}/tickers/btc-bitcoin/historical",
        params={"start": "2025-12-31", "end": "2026-01-02",
                "interval": "1d"},
        access="PUBLIC", sleep_after=0.5,
        notes="CoinPaprika in-window cross-check (2026-01-01)")


if __name__ == "__main__":
    sys.exit(main())
