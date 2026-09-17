"""
Crypto Foundry DATA-1: Hyperliquid Public Collector

Collects public perp state data from Hyperliquid REST API.
NO EXECUTION. PUBLIC DATA ONLY. U.S. EXECUTION = RESTRICTED.

Endpoints used:
- POST /info with type: candleSnapshot (candles)
- POST /info with type: fundingHistory (funding)
- POST /info with type: metaAndAssetCtxs (OI, mark, index)
- POST /info with type: l2Book (book snapshots)
- POST /info with type: recentTrades (recent trades)

WebSocket (live only):
- {type: 'trades', coin: 'BTC'}
- {type: 'l2Book', coin: 'BTC'}
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

COLLECTOR_VERSION = "1.1.0"
API_BASE = "https://api.hyperliquid.xyz"

# Hyperliquid market specs from frozen contract
MARKETS = {
    "BTC": {
        "market_id": "BTC-PERP",
        "base_asset": "BTC",
        "quote_asset": "USD",
        "tick_size": 0.1,
    },
    "ETH": {
        "market_id": "ETH-PERP",
        "base_asset": "ETH",
        "quote_asset": "USD",
        "tick_size": 0.01,
    },
}

SESSION = requests.Session()
SESSION.headers.update({"Content-Type": "application/json"})


def _post_info(payload: Dict[str, Any], timeout: int = 30) -> Any:
    """POST to /info endpoint."""
    resp = SESSION.post(f"{API_BASE}/info", json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


# ── Candles ─────────────────────────────────────────────────────────

def fetch_candles(
    coin: str,
    interval: str = "5m",
    start_time_ms: Optional[int] = None,
    end_time_ms: Optional[int] = None,
    limit: int = 500,
) -> List[Dict]:
    """
    Fetch candle data from Hyperliquid.

    Returns list of normalized SPOT_BAR_REFERENCE records.

    interval options: 1m, 5m, 15m, 1h, 4h, 1d
    NOTE: API requires `req` wrapper for candleSnapshot.
    """
    req = {
        "coin": coin,
        "interval": interval,
    }
    if start_time_ms is not None:
        req["startTime"] = start_time_ms
    if end_time_ms is not None:
        req["endTime"] = end_time_ms
    payload = {
        "type": "candleSnapshot",
        "req": req,
    }

    try:
        data = _post_info(payload)
    except Exception as e:
        return [{"error": str(e), "source": "hyperliquid", "market_id": coin}]

    records = []
    for candle in data:
        try:
            # HL candle fields: t=open_time_ms, T=close_time_ms, s=symbol, i=interval
            # o=open, c=close, h=high, l=low, v=volume, n=trade_count
            open_time_ms = candle.get("t", 0)
            ts = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc).isoformat()
            record = {
                "venue": "hyperliquid",
                "chain_if_applicable": "Hyperliquid L1",
                "market_id": MARKETS.get(coin, {}).get("market_id", f"{coin}-PERP"),
                "instrument_id": f"{coin}-PERP",
                "event_time_utc": ts,
                "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
                "source": "hyperliquid_rest",
                "source_version": COLLECTOR_VERSION,
                "raw_identifier": f"hl_candle_{coin}_{interval}_{open_time_ms}",
                "schema_version": "1.0.0",
                "open": float(candle.get("o", 0)),
                "high": float(candle.get("h", 0)),
                "low": float(candle.get("l", 0)),
                "close": float(candle.get("c", 0)),
                "volume": float(candle.get("v", 0)),
                "trades_count": int(candle.get("n", 0)),
                "interval": candle.get("i", interval),
            }
            records.append(record)
        except (KeyError, ValueError, TypeError) as e:
            continue

    return records


# ── Funding History ────────────────────────────────────────────────

def fetch_funding_history(
    coin: str,
    start_time_ms: Optional[int] = None,
    end_time_ms: Optional[int] = None,
) -> List[Dict]:
    """Fetch funding history. Returns normalized PERP_FUNDING records.

    API NOTES (DATA-1.1):
    - Flat format required: {type: 'fundingHistory', coin: 'BTC', startTime: <ms>}
    - req wrapper returns HTTP 422
    - Omitting startTime returns HTTP 422
    - Max 500 records per request
    """
    if start_time_ms is None:
        import time as _time
        start_time_ms = int((_time.time() - 86400 * 7) * 1000)

    payload: Dict[str, Any] = {
        "type": "fundingHistory",
        "coin": coin,
        "startTime": start_time_ms,
    }
    if end_time_ms is not None:
        payload["endTime"] = end_time_ms

    try:
        data = _post_info(payload)
    except Exception as e:
        return [{"error": str(e), "source": "hyperliquid", "market_id": coin}]

    if not isinstance(data, list):
        return [{"error": f"unexpected response type: {type(data).__name__}",
                 "source": "hyperliquid", "market_id": coin}]

    records = []
    for entry in data:
        try:
            t = entry.get("time", 0)
            ts = datetime.fromtimestamp(t / 1000, tz=timezone.utc).isoformat()
            record = {
                "venue": "hyperliquid",
                "chain_if_applicable": "Hyperliquid L1",
                "market_id": MARKETS.get(coin, {}).get("market_id", f"{coin}-PERP"),
                "instrument_id": f"{coin}-PERP",
                "event_time_utc": ts,
                "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
                "source": "hyperliquid_rest",
                "source_version": COLLECTOR_VERSION,
                "raw_identifier": f"hl_funding_{coin}_{t}",
                "schema_version": "1.0.0",
                "funding_rate": float(entry.get("fundingRate", 0)),
                "funding_time_utc": ts,
                "mark_price": None,
                "index_price": None,
                "premium": _safe_float(entry.get("premium")),
            }
            records.append(record)
        except (KeyError, ValueError, TypeError):
            continue

    return records


# ── Meta and Asset Contexts (OI, Mark, Index) ─────────────────────

def fetch_meta_and_contexts() -> Dict[str, List[Dict]]:
    """
    Fetch meta info and per-asset contexts.
    Returns dict of coin -> [PERP_MARK_INDEX, PERP_OPEN_INTEREST] records.
    NOTE: metaAndAssetCtxs does NOT use req wrapper (different endpoint type).
    """
    payload = {"type": "metaAndAssetCtxs"}

    try:
        data = _post_info(payload)
    except Exception as e:
        return {"_error": [{"error": str(e), "source": "hyperliquid"}]}

    # data is [meta, assetContexts]
    if not isinstance(data, list) or len(data) < 2:
        return {"_error": [{"error": "unexpected response format", "source": "hyperliquid"}]}

    meta = data[0]
    contexts = data[1]

    # Build coin lookup from meta
    universe = meta.get("universe", [])
    coin_to_info = {}
    for asset in universe:
        coin = asset.get("name", "")
        coin_to_info[coin] = {
            "market_id": f"{coin}-PERP",
            "max_leverage": asset.get("maxLeverage"),
            "tick_size": asset.get("tickSize"),
        }

    now = datetime.now(timezone.utc).isoformat()
    result = {}

    for i, ctx in enumerate(contexts):
        if i >= len(universe):
            break
        coin = universe[i].get("name", "")
        info = coin_to_info.get(coin, {})

        # Mark/Index
        midx_record = {
            "venue": "hyperliquid",
            "chain_if_applicable": "Hyperliquid L1",
            "market_id": info.get("market_id", f"{coin}-PERP"),
            "instrument_id": f"{coin}-PERP",
            "event_time_utc": now,
            "ingest_time_utc": now,
            "source": "hyperliquid_rest",
            "source_version": COLLECTOR_VERSION,
            "raw_identifier": f"hl_context_{coin}",
            "schema_version": "1.0.0",
            "mark_price": _safe_float(ctx.get("markPx")),
            "index_price": _safe_float(ctx.get("midPx")),
            "oracle_price": _safe_float(ctx.get("oraclePx")),
            "premium": None,
        }

        # OI
        oi_record = {
            "venue": "hyperliquid",
            "chain_if_applicable": "Hyperliquid L1",
            "market_id": info.get("market_id", f"{coin}-PERP"),
            "instrument_id": f"{coin}-PERP",
            "event_time_utc": now,
            "ingest_time_utc": now,
            "source": "hyperliquid_rest",
            "source_version": COLLECTOR_VERSION,
            "raw_identifier": f"hl_oi_{coin}",
            "schema_version": "1.0.0",
            "open_interest": _safe_float(ctx.get("openInterest")),
            "open_interest_value_usd": None,
        }

        result[coin] = [midx_record, oi_record]

    return result


# ── L2 Book Snapshot ───────────────────────────────────────────────

def fetch_l2_book(coin: str) -> Dict:
    """Fetch L2 order book snapshot. Returns PERP_BOOK_SNAPSHOT record.
    NOTE: l2Book endpoint does NOT use req wrapper (flat format).
    Response: {coin, time, levels: [bids, asks]} where each level is {px, sz, n}.
    """
    payload = {"type": "l2Book", "coin": coin}

    try:
        data = _post_info(payload)
    except Exception as e:
        return {"error": str(e), "source": "hyperliquid", "market_id": coin}

    now = datetime.now(timezone.utc).isoformat()
    levels = data.get("levels", [[], []])
    # levels is [bids_list, asks_list] where each item is {px, sz, n}
    bids_raw = levels[0] if len(levels) > 0 else []
    asks_raw = levels[1] if len(levels) > 1 else []

    return {
        "venue": "hyperliquid",
        "chain_if_applicable": "Hyperliquid L1",
        "market_id": MARKETS.get(coin, {}).get("market_id", f"{coin}-PERP"),
        "instrument_id": f"{coin}-PERP",
        "event_time_utc": now,
        "ingest_time_utc": now,
        "source": "hyperliquid_rest",
        "source_version": COLLECTOR_VERSION,
        "raw_identifier": f"hl_l2book_{coin}_{data.get('time', int(time.time() * 1000))}",
        "schema_version": "1.0.0",
        "bids": [[float(b.get("px", 0)), float(b.get("sz", 0))] for b in bids_raw],
        "asks": [[float(a.get("px", 0)), float(a.get("sz", 0))] for a in asks_raw],
        "checksum": None,
    }


# ── Recent Trades ──────────────────────────────────────────────────

def fetch_recent_trades(coin: str, max_trades: int = 100) -> List[Dict]:
    """
    Fetch recent trades snapshot (REST endpoint).
    For historical trade backfill, WebSocket is required.
    NOTE: recentTrades endpoint does NOT use req wrapper (flat format).
    Response fields: coin, side (A/B), px, sz, time, hash, tid, users.
    """
    payload = {"type": "recentTrades", "coin": coin, "n": min(max_trades, 1000)}

    try:
        data = _post_info(payload)
    except Exception as e:
        return [{"error": str(e), "source": "hyperliquid", "market_id": coin}]

    records = []
    for t in data:
        try:
            ts_ms = t.get("time", 0)
            ts = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()
            # HL recentTrades: side is 'A' (aggressor sell) or 'B' (aggressor buy)
            hl_side = t.get("side", "")
            record = {
                "venue": "hyperliquid",
                "chain_if_applicable": "Hyperliquid L1",
                "market_id": MARKETS.get(coin, {}).get("market_id", f"{coin}-PERP"),
                "instrument_id": f"{coin}-PERP",
                "event_time_utc": ts,
                "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
                "source": "hyperliquid_rest",
                "source_version": COLLECTOR_VERSION,
                "raw_identifier": f"hl_trade_{coin}_{ts_ms}_{t.get('tid', '')}",
                "schema_version": "1.0.0",
                "trade_id": str(t.get("tid", "")),
                "price": float(t.get("px", 0)),
                "size": float(t.get("sz", 0)),
                "side": "BUY" if hl_side == "B" else "SELL",
                "liquidation_flag": t.get("liquidation", False),
                "matching_engine_id": None,
            }
            records.append(record)
        except (KeyError, ValueError, TypeError):
            continue

    return records


# ── Batch Candle Collection with Pagination ────────────────────────

def collect_full_candle_history(
    coin: str,
    interval: str = "5m",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    delay_between_requests: float = 0.1,
) -> Tuple[List[Dict], Dict]:
    """
    Paginate through full candle history for a coin.
    Returns (records, metadata).
    """
    if start_date is None:
        # Hyperliquid BTC-PERP launched ~2023-05, ETH similar
        start_date = "2023-05-01"
    if end_date is None:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    start_ms = int(datetime.strptime(start_date, "%Y-%m-%d").replace(
        tzinfo=timezone.utc
    ).timestamp() * 1000)
    end_ms = int(datetime.strptime(end_date, "%Y-%m-%d").replace(
        tzinfo=timezone.utc
    ).timestamp() * 1000)

    all_records = []
    current_end = end_ms
    request_count = 0

    while current_end > start_ms:
        records = fetch_candles(
            coin=coin,
            interval=interval,
            start_time_ms=start_ms,
            end_time_ms=current_end,
        )

        if not records or (len(records) == 1 and "error" in records[0]):
            break

        request_count += 1
        all_records.extend(records)

        # Move end before earliest record in this batch
        earliest_ts = min(
            (r.get("event_time_utc", "") for r in records if "error" not in r),
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

    # Deduplicate by event_time_utc
    seen = set()
    unique_records = []
    for r in all_records:
        key = (r.get("event_time_utc"), r.get("market_id"))
        if key not in seen:
            seen.add(key)
            unique_records.append(r)

    # Sort by time
    unique_records.sort(key=lambda r: r.get("event_time_utc", ""))

    metadata = {
        "coin": coin,
        "interval": interval,
        "start_date": start_date,
        "end_date": end_date,
        "total_records": len(unique_records),
        "requests_made": request_count,
        "status": "VALID" if len(unique_records) > 0 else "PARTIAL",
    }

    return unique_records, metadata


def _safe_float(val) -> Optional[float]:
    """Safely convert to float."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def collect_full_funding_history(
    coin: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    delay_between_requests: float = 0.15,
) -> Tuple[List[Dict], Dict]:
    """
    Paginate through full funding history using forward pagination.
    """
    if start_date is None:
        start_date = "2023-05-01"
    if end_date is None:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    start_ms = int(datetime.strptime(start_date, "%Y-%m-%d").replace(
        tzinfo=timezone.utc
    ).timestamp() * 1000)
    end_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    all_records = []
    current_start = start_ms
    request_count = 0
    empty_strikes = 0

    while current_start < end_ms:
        records = []
        # Retry on empty/error pages (rate limiting) with backoff
        for attempt in range(4):
            records = fetch_funding_history(coin=coin, start_time_ms=current_start, end_time_ms=end_ms)
            if records and "error" not in records[0] and len(records) > 0:
                break
            time.sleep(1.0 * (attempt + 1))
        if not records or ("error" in records[0] if records else False):
            empty_strikes += 1
            if empty_strikes >= 3:
                break
            current_start += 500 * 3600 * 1000  # advance 500h if stuck
            time.sleep(1.0)
            continue

        empty_strikes = 0
        request_count += 1
        all_records.extend(records)

        # Extract latest timestamp from raw_identifier
        latest_ms = 0
        for r in records:
            if "error" not in r:
                raw_id = r.get("raw_identifier", "")
                parts = raw_id.split("_")
                if len(parts) >= 4:
                    try:
                        latest_ms = max(latest_ms, int(parts[-1]))
                    except ValueError:
                        pass

        if latest_ms == 0:
            break
        current_start = latest_ms + 1

        if len(records) < 500:
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
        "coin": coin,
        "start_date": start_date,
        "end_date": end_date,
        "total_records": len(unique_records),
        "requests_made": request_count,
        "first_timestamp": unique_records[0]["event_time_utc"] if unique_records else None,
        "last_timestamp": unique_records[-1]["event_time_utc"] if unique_records else None,
        "status": "VALID" if len(unique_records) > 10 else "PARTIAL" if unique_records else "FAILED",
        "funding_interval": "1h (hourly)",
    }
    return unique_records, metadata
