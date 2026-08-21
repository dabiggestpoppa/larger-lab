"""
Crypto Foundry DATA-1: Binance Historical Backfill Collector

Collects deep historical OHLCV data from Binance public REST API.
RESEARCH DATA ONLY. NO EXECUTION.

Endpoints:
- GET /api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1000

Known limitations:
- Rate limited at ~1200 req/min
- Per-request limit 1000 candles
- Backward pagination by endTime
- Historical coverage: 2017-07 for BTCUSDT/ETHUSDT spot
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

COLLECTOR_VERSION = "1.0.0"
API_BASE = "https://api.binance.com"

# Supported intervals and their durations in seconds
INTERVALS = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}

SESSION = requests.Session()


def fetch_klines(
    symbol: str,
    interval: str = "1m",
    start_time_ms: Optional[int] = None,
    end_time_ms: Optional[int] = None,
    limit: int = 1000,
) -> List[Dict]:
    """
    Fetch klines (OHLCV) from Binance REST API.

    Returns normalized SPOT_BAR_REFERENCE records.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": min(limit, 1000),
    }
    if start_time_ms is not None:
        params["startTime"] = start_time_ms
    if end_time_ms is not None:
        params["endTime"] = end_time_ms

    try:
        resp = SESSION.get(
            f"{API_BASE}/api/v3/klines",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        return [{"error": str(e), "source": "binance", "market_id": symbol}]

    records = []
    for kline in data:
        try:
            open_time_ms = kline[0]
            ts = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc).isoformat()

            record = {
                "venue": "binance",
                "chain_if_applicable": None,
                "market_id": symbol,
                "instrument_id": symbol,
                "event_time_utc": ts,
                "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
                "source": "binance_rest",
                "source_version": COLLECTOR_VERSION,
                "raw_identifier": f"binance_kline_{symbol}_{interval}_{open_time_ms}",
                "schema_version": "1.0.0",
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
                "trades_count": int(kline[8]),
                "interval": interval,
            }
            records.append(record)
        except (IndexError, ValueError, TypeError):
            continue

    return records


def collect_full_history(
    symbol: str,
    interval: str = "1m",
    start_date: str = "2017-07-14",
    end_date: Optional[str] = None,
    delay_between_requests: float = 0.08,
    max_requests: Optional[int] = None,
) -> Tuple[List[Dict], Dict]:
    """
    Paginate through full Binance kline history.

    Uses backward pagination from end_date to start_date.
    Returns (records, metadata).
    """
    if end_date is None:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    start_ms = int(datetime.strptime(start_date, "%Y-%m-%d").replace(
        tzinfo=timezone.utc
    ).timestamp() * 1000)
    end_ms = int(
        datetime.strptime(end_date, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        ).timestamp() * 1000
    ) + 86400000 - 1  # end of day

    interval_sec = INTERVALS.get(interval, 60)
    expected_count = max(0, (end_ms - start_ms) // (interval_sec * 1000))

    all_records = []
    current_end = end_ms
    request_count = 0
    errors = 0

    while current_end > start_ms:
        if max_requests and request_count >= max_requests:
            break

        records = fetch_klines(
            symbol=symbol,
            interval=interval,
            start_time_ms=start_ms,
            end_time_ms=current_end,
            limit=1000,
        )

        if records and "error" in records[0]:
            errors += 1
            if errors > 5:
                break
            time.sleep(1)
            continue

        if not records:
            break

        request_count += 1
        all_records.extend(records)

        # Move end before earliest record
        earliest_ts = min(
            (r.get("event_time_utc", "") for r in records),
            default=""
        )
        if not earliest_ts:
            break

        try:
            earliest_dt = datetime.fromisoformat(earliest_ts.replace("Z", "+00:00"))
            current_end = int(earliest_dt.timestamp() * 1000) - 1
        except (ValueError, TypeError):
            break

        time.sleep(delay_between_requests)

    # Deduplicate
    seen = set()
    unique_records = []
    for r in all_records:
        key = r.get("raw_identifier", "")
        if key not in seen:
            seen.add(key)
            unique_records.append(r)

    unique_records.sort(key=lambda r: r.get("event_time_utc", ""))

    metadata = {
        "symbol": symbol,
        "interval": interval,
        "start_date": start_date,
        "end_date": end_date,
        "expected_count": expected_count,
        "actual_count": len(unique_records),
        "requests_made": request_count,
        "errors": errors,
        "coverage_ratio": len(unique_records) / expected_count if expected_count > 0 else 0,
        "status": "VALID" if len(unique_records) > expected_count * 0.5 else
                  "PARTIAL" if len(unique_records) > 0 else "FAILED",
    }

    return unique_records, metadata


def parse_existing_local_file(
    filepath: str,
    symbol: str,
    interval: str = "5m",
) -> Tuple[List[Dict], Dict]:
    """
    Parse existing local Binance JSON files (btc_usdt_1460d.json etc).
    Returns normalized records + metadata.
    """
    with open(filepath, "r") as f:
        data = json.load(f)

    records = []
    for candle in data:
        try:
            ts_ms = candle[0]
            ts = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()

            record = {
                "venue": "binance",
                "chain_if_applicable": None,
                "market_id": symbol,
                "instrument_id": symbol,
                "event_time_utc": ts,
                "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
                "source": "binance_local_file",
                "source_version": COLLECTOR_VERSION,
                "raw_identifier": f"binance_local_{symbol}_{interval}_{ts_ms}",
                "schema_version": "1.0.0",
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5]),
                "trades_count": int(candle[8]) if len(candle) > 8 else None,
                "interval": interval,
            }
            records.append(record)
        except (IndexError, ValueError, TypeError):
            continue

    metadata = {
        "symbol": symbol,
        "interval": interval,
        "source_file": filepath,
        "record_count": len(records),
        "status": "VALID" if len(records) > 0 else "FAILED",
    }

    return records, metadata
