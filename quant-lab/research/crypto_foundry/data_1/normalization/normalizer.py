"""
Crypto Foundry DATA-1: Normalization Pipeline

Converts raw API responses to schema-compliant normalized records.
All normalization is deterministic and future-independent.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

NORMALIZER_VERSION = "1.0.0"


class Normalizer:
    """Deterministic normalization pipeline for all data lanes."""

    def __init__(self):
        self.version = NORMALIZER_VERSION

    def normalize_hyperliquid_candles(
        self, raw_candles: List[Dict], coin: str
    ) -> List[Dict]:
        """Normalize raw Hyperliquid candle data to SPOT_BAR_REFERENCE."""
        records = []
        for candle in raw_candles:
            if "error" in candle:
                continue

            try:
                t = candle.get("t", candle.get("T", 0))
                if isinstance(t, (int, float)) and t > 1e12:
                    ts = datetime.fromtimestamp(t / 1000, tz=timezone.utc).isoformat()
                elif isinstance(t, str):
                    ts = t
                else:
                    ts = datetime.fromtimestamp(t, tz=timezone.utc).isoformat()

                record = {
                    "venue": "hyperliquid",
                    "chain_if_applicable": "Hyperliquid L1",
                    "market_id": f"{coin}-PERP",
                    "instrument_id": f"{coin}-PERP",
                    "event_time_utc": ts,
                    "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
                    "source": "hyperliquid_rest",
                    "source_version": NORMALIZER_VERSION,
                    "raw_identifier": f"hl_norm_{coin}_{t}",
                    "schema_version": "1.0.0",
                    "open": float(candle.get("o", 0)),
                    "high": float(candle.get("h", 0)),
                    "low": float(candle.get("l", 0)),
                    "close": float(candle.get("c", 0)),
                    "volume": float(candle.get("v", 0)),
                    "trades_count": None,
                    "interval": candle.get("interval", "5m"),
                }
                records.append(record)
            except (KeyError, ValueError, TypeError):
                continue

        return records

    def normalize_binance_klines(
        self, raw_klines: List[Any], symbol: str, interval: str = "1m"
    ) -> List[Dict]:
        """Normalize raw Binance kline data to SPOT_BAR_REFERENCE."""
        records = []
        for kline in raw_klines:
            try:
                if isinstance(kline, dict) and "error" in kline:
                    continue

                if isinstance(kline, (list, tuple)) and len(kline) >= 7:
                    open_time_ms = kline[0]
                    ts = datetime.fromtimestamp(
                        open_time_ms / 1000, tz=timezone.utc
                    ).isoformat()

                    record = {
                        "venue": "binance",
                        "chain_if_applicable": None,
                        "market_id": symbol,
                        "instrument_id": symbol,
                        "event_time_utc": ts,
                        "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
                        "source": "binance_rest",
                        "source_version": NORMALIZER_VERSION,
                        "raw_identifier": f"binance_norm_{symbol}_{interval}_{open_time_ms}",
                        "schema_version": "1.0.0",
                        "open": float(kline[1]),
                        "high": float(kline[2]),
                        "low": float(kline[3]),
                        "close": float(kline[4]),
                        "volume": float(kline[5]),
                        "trades_count": int(kline[8]) if len(kline) > 8 else None,
                        "interval": interval,
                    }
                    records.append(record)
                elif isinstance(kline, dict):
                    # Already dict format
                    ts = kline.get("event_time_utc", "")
                    record = {
                        "venue": "binance",
                        "chain_if_applicable": None,
                        "market_id": symbol,
                        "instrument_id": symbol,
                        "event_time_utc": ts,
                        "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
                        "source": "binance_rest",
                        "source_version": NORMALIZER_VERSION,
                        "raw_identifier": kline.get("raw_identifier", f"binance_norm_{symbol}"),
                        "schema_version": "1.0.0",
                        "open": float(kline.get("open", 0)),
                        "high": float(kline.get("high", 0)),
                        "low": float(kline.get("low", 0)),
                        "close": float(kline.get("close", 0)),
                        "volume": float(kline.get("volume", 0)),
                        "trades_count": kline.get("trades_count"),
                        "interval": kline.get("interval", interval),
                    }
                    records.append(record)
            except (IndexError, ValueError, TypeError):
                continue

        return records

    def normalize_uniswap_swaps(
        self, raw_swaps: List[Dict], pool_key: str
    ) -> List[Dict]:
        """Normalize raw Uniswap swap data to AMM_SWAP schema."""
        records = []
        for swap in raw_swaps:
            if "error" in swap:
                continue

            try:
                record = {
                    "venue": "uniswap_v3",
                    "chain_if_applicable": "Ethereum",
                    "market_id": pool_key,
                    "pool_address": swap.get("pool_address", ""),
                    "event_time_utc": swap.get("event_time_utc", ""),
                    "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
                    "source": "uniswap_v3_subgraph",
                    "source_version": NORMALIZER_VERSION,
                    "raw_identifier": swap.get("raw_identifier", ""),
                    "schema_version": "1.0.0",
                    "block_number": int(swap.get("block_number", 0)),
                    "tx_hash": swap.get("tx_hash", ""),
                    "log_index": int(swap.get("log_index", 0)),
                    "sender": swap.get("sender", ""),
                    "recipient": swap.get("recipient", ""),
                    "amount0": int(swap.get("amount0", 0)),
                    "amount1": int(swap.get("amount1", 0)),
                    "sqrt_price_x96": int(swap.get("sqrt_price_x96", 0)),
                    "tick": int(swap.get("tick", 0)),
                    "fee_tier": int(swap.get("fee_tier", 0)),
                    "pool_fee_amount0": swap.get("pool_fee_amount0"),
                    "pool_fee_amount1": swap.get("pool_fee_amount1"),
                }
                records.append(record)
            except (KeyError, ValueError, TypeError):
                continue

        return records

    def normalize_hyperliquid_funding(
        self, raw_funding: List[Dict], coin: str
    ) -> List[Dict]:
        """Normalize Hyperliquid funding to PERP_FUNDING."""
        records = []
        for f in raw_funding:
            if "error" in f:
                continue

            try:
                record = {
                    "venue": "hyperliquid",
                    "chain_if_applicable": "Hyperliquid L1",
                    "market_id": f"{coin}-PERP",
                    "instrument_id": f"{coin}-PERP",
                    "event_time_utc": f.get("event_time_utc", ""),
                    "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
                    "source": "hyperliquid_rest",
                    "source_version": NORMALIZER_VERSION,
                    "raw_identifier": f.get("raw_identifier", ""),
                    "schema_version": "1.0.0",
                    "funding_rate": float(f.get("funding_rate", 0)),
                    "funding_time_utc": f.get("funding_time_utc", f.get("event_time_utc", "")),
                    "mark_price": f.get("mark_price"),
                    "index_price": f.get("index_price"),
                }
                records.append(record)
            except (KeyError, ValueError, TypeError):
                continue

        return records

    def normalize_hyperliquid_mark_index(
        self, raw_records: List[Dict], coin: str
    ) -> List[Dict]:
        """Normalize Hyperliquid mark/index to PERP_MARK_INDEX."""
        records = []
        for r in raw_records:
            if "error" in r:
                continue

            try:
                record = {
                    "venue": "hyperliquid",
                    "chain_if_applicable": "Hyperliquid L1",
                    "market_id": f"{coin}-PERP",
                    "instrument_id": f"{coin}-PERP",
                    "event_time_utc": r.get("event_time_utc", datetime.now(timezone.utc).isoformat()),
                    "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
                    "source": "hyperliquid_rest",
                    "source_version": NORMALIZER_VERSION,
                    "raw_identifier": r.get("raw_identifier", ""),
                    "schema_version": "1.0.0",
                    "mark_price": r.get("mark_price"),
                    "index_price": r.get("index_price"),
                    "oracle_price": r.get("oracle_price"),
                    "premium": None,
                }
                records.append(record)
            except (KeyError, ValueError, TypeError):
                continue

        return records

    def normalize_hyperliquid_oi(
        self, raw_records: List[Dict], coin: str
    ) -> List[Dict]:
        """Normalize Hyperliquid OI to PERP_OPEN_INTEREST."""
        records = []
        for r in raw_records:
            if "error" in r:
                continue

            try:
                record = {
                    "venue": "hyperliquid",
                    "chain_if_applicable": "Hyperliquid L1",
                    "market_id": f"{coin}-PERP",
                    "instrument_id": f"{coin}-PERP",
                    "event_time_utc": r.get("event_time_utc", datetime.now(timezone.utc).isoformat()),
                    "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
                    "source": "hyperliquid_rest",
                    "source_version": NORMALIZER_VERSION,
                    "raw_identifier": r.get("raw_identifier", ""),
                    "schema_version": "1.0.0",
                    "open_interest": r.get("open_interest"),
                    "open_interest_value_usd": r.get("open_interest_value_usd"),
                }
                records.append(record)
            except (KeyError, ValueError, TypeError):
                continue

        return records
