"""
Hyperliquid Historical Data Fetcher
====================================
Fetches OHLCV candlestick data from Hyperliquid API → CSV files.

Hyperliquid candle format:
  t = open time (ms), T = close time (ms), s = symbol, i = interval
  o, c, h, l = prices (strings), v = volume (string), n = trade count

Usage:
    python quant-lab/data/hyperliquid_fetcher.py --coins BTC ETH SOL --interval 5m --days 365
    python quant-lab/data/hyperliquid_fetcher.py --all-perps --interval 1h --days 90
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Path Setup ────────────────────────────────────────────────────────────
REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
DATA_DIR = REPO_ROOT / "quant-lab" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Hyperliquid SDK ───────────────────────────────────────────────────────
from hyperliquid.info import Info
from hyperliquid.utils.constants import MAINNET_API_URL

# ── All available Hyperliquid perp coins ─────────────────────────────────
ALL_PERP_COINS = [
    "BTC", "ETH", "SOL", "AVAX", "BNB", "DOGE", "XRP", "LTC",
    "ARB", "OP", "LINK", "INJ", "SUI", "kPEPE", "CRV", "LDO",
    "STX", "CFX", "GMX", "SNX", "UNI", "AAVE", "MKR", "RUNE",
    "DYDX", "SEI", "JUP", "WIF", "ONDO", "ENA", "W", "TON",
    "ADA", "DOT", "MATIC", "FIL", "NEAR", "APT", "TRX", "BONK",
]

# Interval mapping: user-friendly → Hyperliquid format
INTERVAL_MAP = {
    "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m",
    "30m": "30m", "1h": "1h", "2h": "2h", "4h": "4h",
    "8h": "8h", "12h": "12h", "1d": "1d", "1w": "1w",
}


def fetch_candles(
    info: Info,
    coin: str,
    interval: str,
    start_ms: int,
    end_ms: int,
    chunk_days: int = 30,
) -> list[dict]:
    """
    Fetch candles in chunks (Hyperliquid has per-request limits).
    Returns list of candle dicts sorted by time.
    """
    all_candles = []
    chunk_ms = chunk_days * 24 * 3600 * 1000
    current_start = start_ms

    while current_start < end_ms:
        current_end = min(current_start + chunk_ms, end_ms)
        try:
            batch = info.candles_snapshot(coin, interval, current_start, current_end)
            if batch:
                all_candles.extend(batch)
                print(f"  [{coin}] {interval}: fetched {len(batch)} candles "
                      f"({datetime.fromtimestamp(current_start/1000, tz=timezone.utc).strftime('%Y-%m-%d')} "
                      f"→ {datetime.fromtimestamp(current_end/1000, tz=timezone.utc).strftime('%Y-%m-%d')})")
            else:
                print(f"  [{coin}] {interval}: no data for chunk "
                      f"{datetime.fromtimestamp(current_start/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")
        except Exception as e:
            print(f"  [{coin}] ERROR: {e}")
            time.sleep(2)  # Rate limit backoff
            continue

        current_start = current_end
        time.sleep(0.3)  # Rate limit: ~3 req/sec

    # Deduplicate by open time
    seen = set()
    deduped = []
    for c in all_candles:
        if c["t"] not in seen:
            seen.add(c["t"])
            deduped.append(c)

    deduped.sort(key=lambda x: x["t"])
    return deduped


def fetch_candles_paginated(
    info: Info,
    coin: str,
    interval: str,
    start_ms: int,
    end_ms: int,
    max_per_request: int = 5000,
) -> list[dict]:
    """
    Fetch candles by paginating backwards from end_ms.
    Hyperliquid API returns max ~5000 candles per request regardless of time range.
    This function paginates backwards using the oldest candle's timestamp as the new end.
    """
    all_candles = []
    current_end = end_ms
    oldest_seen = end_ms
    request_count = 0
    max_requests = 200  # Safety limit

    while current_end > start_ms and request_count < max_requests:
        try:
            batch = info.candles_snapshot(coin, interval, start_ms, current_end)
            if not batch:
                print(f"  [{coin}] no data before {datetime.fromtimestamp(current_end/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")
                break

            # Deduplicate
            new_candles = [c for c in batch if c["t"] not in [x["t"] for x in all_candles]]
            all_candles.extend(new_candles)

            oldest_in_batch = min(c["t"] for c in batch)
            newest_in_batch = max(c["t"] for c in batch)

            print(f"  [{coin}] req {request_count+1}: {len(batch)} candles, "
                  f"range {datetime.fromtimestamp(oldest_in_batch/1000, tz=timezone.utc).strftime('%Y-%m-%d')} "
                  f"→ {datetime.fromtimestamp(newest_in_batch/1000, tz=timezone.utc).strftime('%Y-%m-%d')}, "
                  f"total unique: {len(all_candles)}")

            # If we got fewer than max_per_request, we've reached the end of available data
            if len(batch) < max_per_request:
                print(f"  [{coin}] reached end of available data")
                break

            # Move the end pointer back to the oldest candle in this batch
            current_end = oldest_in_batch

            # If we're not making progress, stop
            if current_end >= oldest_seen:
                print(f"  [{coin}] no further progress, stopping")
                break
            oldest_seen = current_end

            request_count += 1
            time.sleep(0.3)  # Rate limit

        except Exception as e:
            print(f"  [{coin}] ERROR: {e}")
            time.sleep(2)
            continue

    # Final dedup and sort
    seen = set()
    deduped = []
    for c in all_candles:
        if c["t"] not in seen:
            seen.add(c["t"])
            deduped.append(c)
    deduped.sort(key=lambda x: x["t"])

    # Filter to requested range
    deduped = [c for c in deduped if start_ms <= c["t"] <= end_ms]

    print(f"  [{coin}] total: {len(deduped)} candles over {request_count} requests")
    return deduped


def candles_to_csv(candles: list[dict], output_path: Path) -> int:
    """Write candles to CSV. Returns number of rows written."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "open", "high", "low", "close", "volume", "trades"])
        for c in candles:
            dt = datetime.fromtimestamp(c["t"] / 1000, tz=timezone.utc)
            writer.writerow([
                dt.isoformat(),
                float(c["o"]),
                float(c["h"]),
                float(c["l"]),
                float(c["c"]),
                float(c["v"]),
                int(c["n"]),
            ])
    return len(candles)


def fetch_coin_metadata(info: Info, coin: str) -> dict:
    """Get metadata for a specific coin."""
    try:
        meta = info.meta_and_asset_ctxs()
        universe = meta[0].get("universe", [])
        for asset in universe:
            if asset["name"] == coin:
                return asset
    except Exception:
        pass
    return {}


def main():
    parser = argparse.ArgumentParser(description="Fetch Hyperliquid historical data")
    parser.add_argument("--coins", nargs="+", default=["BTC", "ETH"],
                        help="Coin symbols to fetch (e.g., BTC ETH SOL)")
    parser.add_argument("--all-perps", action="store_true",
                        help="Fetch all available perp coins")
    parser.add_argument("--interval", default="5m",
                        choices=list(INTERVAL_MAP.keys()),
                        help="Candle interval (default: 5m)")
    parser.add_argument("--days", type=int, default=365,
                        help="Number of days of history (default: 365)")
    parser.add_argument("--start-date", type=str, default=None,
                        help="Start date YYYY-MM-DD (overrides --days)")
    parser.add_argument("--end-date", type=str, default=None,
                        help="End date YYYY-MM-DD (default: now)")
    parser.add_argument("--output-dir", type=str, default=str(DATA_DIR),
                        help="Output directory for CSV files")
    parser.add_argument("--metadata", action="store_true",
                        help="Also save coin metadata JSON")
    args = parser.parse_args()

    coins = ALL_PERP_COINS if args.all_perps else args.coins
    interval = INTERVAL_MAP[args.interval]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Time range
    now_ms = int(time.time() * 1000)
    if args.start_date:
        start_dt = datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        start_ms = int(start_dt.timestamp() * 1000)
    else:
        start_ms = now_ms - args.days * 24 * 3600 * 1000

    if args.end_date:
        end_dt = datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_ms = int(end_dt.timestamp() * 1000)
    else:
        end_ms = now_ms

    print(f"Hyperliquid Data Fetcher")
    print(f"  Coins:    {', '.join(coins)}")
    print(f"  Interval: {interval}")
    print(f"  Range:    {datetime.fromtimestamp(start_ms/1000, tz=timezone.utc).strftime('%Y-%m-%d')} "
          f"→ {datetime.fromtimestamp(end_ms/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")
    print(f"  Output:   {output_dir}")
    print()

    info = Info(MAINNET_API_URL)
    total_rows = 0

    for coin in coins:
        print(f"Fetching {coin}...")
        candles = fetch_candles(info, coin, interval, start_ms, end_ms)

        if not candles:
            print(f"  [{coin}] No data fetched, skipping.")
            continue

        # Save CSV
        csv_name = f"{coin}USD_M5.csv" if interval == "5m" else f"{coin}USD_{interval}.csv"
        csv_path = output_dir / csv_name
        rows = candles_to_csv(candles, csv_path)
        total_rows += rows
        print(f"  [{coin}] Saved {rows} candles → {csv_path}")

        # Save metadata
        if args.metadata:
            meta = fetch_coin_metadata(info, coin)
            if meta:
                meta_path = output_dir / f"{coin}USD_meta.json"
                with open(meta_path, "w") as f:
                    json.dump(meta, f, indent=2)
                print(f"  [{coin}] Metadata → {meta_path}")

        print()

    print(f"Done. Total: {total_rows} candles across {len(coins)} coins.")


if __name__ == "__main__":
    main()
