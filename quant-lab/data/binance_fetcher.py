"""
Binance Historical Data Fetcher
================================
Fetches OHLCV candlestick data from Binance public API with pagination.
Supports multi-year historical 5m data.

Binance API: https://api.binance.com/api/v3/klines
- Max 1000 candles per request
- Supports endTime pagination
- No API key needed
"""

from __future__ import annotations

import time
import urllib.request
import json
from datetime import datetime, timezone


def fetch_binance_candles(
    symbol: str = "BTCUSDT",
    interval: str = "5m",
    start_ms: int = None,
    end_ms: int = None,
    max_requests: int = 500,
) -> list[list]:
    """Fetch candles from Binance with pagination. Returns raw kline data."""
    if end_ms is None:
        end_ms = int(time.time() * 1000)
    if start_ms is None:
        start_ms = end_ms - 365 * 24 * 3600 * 1000

    all_candles = []
    current_end = end_ms
    request_count = 0

    print(f"  [Binance] Fetching {symbol} {interval}...")
    print(f"  [Binance] Range: {datetime.fromtimestamp(start_ms/1000, tz=timezone.utc).strftime('%Y-%m-%d')} "
          f"-> {datetime.fromtimestamp(end_ms/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")

    while current_end > start_ms and request_count < max_requests:
        url = (f"https://api.binance.com/api/v3/klines?"
               f"symbol={symbol}&interval={interval}&limit=1000&endTime={current_end}")

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=15)
            batch = json.loads(resp.read())

            if not batch:
                break

            # Filter to requested range
            batch = [c for c in batch if c[0] >= start_ms]
            if not batch:
                break

            all_candles.extend(batch)
            oldest = batch[0][0]
            newest = batch[-1][0]

            if request_count % 50 == 0 or len(batch) < 1000:
                first_dt = datetime.fromtimestamp(oldest / 1000, tz=timezone.utc)
                last_dt = datetime.fromtimestamp(newest / 1000, tz=timezone.utc)
                print(f"  [Binance] req {request_count+1}: {len(batch)} candles, "
                      f"{first_dt.strftime('%Y-%m-%d')} -> {last_dt.strftime('%Y-%m-%d')}, "
                      f"total: {len(all_candles)}")

            current_end = oldest - 1
            request_count += 1
            time.sleep(0.1)

        except Exception as e:
            print(f"  [Binance] ERROR: {e}")
            time.sleep(2)
            continue

    # Deduplicate and sort
    seen = set()
    deduped = []
    for c in all_candles:
        if c[0] not in seen:
            seen.add(c[0])
            deduped.append(c)
    deduped.sort(key=lambda x: x[0])

    print(f"  [Binance] Total: {len(deduped)} candles from {request_count} requests")
    if deduped:
        first = datetime.fromtimestamp(deduped[0][0] / 1000, tz=timezone.utc)
        last = datetime.fromtimestamp(deduped[-1][0] / 1000, tz=timezone.utc)
        print(f"  [Binance] Range: {first.strftime('%Y-%m-%d')} -> {last.strftime('%Y-%m-%d')} "
              f"({(last-first).days} days)")

    return deduped
