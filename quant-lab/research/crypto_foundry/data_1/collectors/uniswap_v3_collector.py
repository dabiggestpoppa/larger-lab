"""
Crypto Foundry DATA-1: Uniswap v3 Ethereum Event Collector

Collects raw swap, mint, burn events from Uniswap v3 pools on Ethereum mainnet.
Uses The Graph subgraph as index/convenience layer, with provenance path to raw RPC.

POOL 1: WETH/USDC 0.05% — 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
POOL 2: WBTC/USDC 0.30% — 0x99ac8cA7087fA4A2A1FB6357269965A2014ABc35

Chain: Ethereum mainnet (chain_id=1)
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

COLLECTOR_VERSION = "1.0.0"

# Frozen pool contracts from preregistration
POOLS = {
    "WETH-USDC-500": {
        "pool_address": "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640",
        "token0": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC (6 decimals)
        "token1": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH (18 decimals)
        "token0_name": "USDC",
        "token1_name": "WETH",
        "fee_tier": 500,
        "fee_tick_spacing": 10,
        "token0_decimals": 6,
        "token1_decimals": 18,
    },
    "WBTC-USDC-3000": {
        "pool_address": "0x99ac8cA7087fA4A2A1FB6357269965A2014ABc35",
        "token0": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC (8 decimals)
        "token1": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC (6 decimals)
        "token0_name": "WBTC",
        "token1_name": "USDC",
        "fee_tier": 3000,
        "fee_tick_spacing": 60,
        "token0_decimals": 8,
        "token1_decimals": 6,
    },
}

# The Graph subgraph endpoint (deprecated free, use gateway)
SUBGRAPH_URL = "https://gateway-arbitrum.network.thegraph.com/api/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"

SESSION = requests.Session()
SESSION.headers.update({"Content-Type": "application/json"})


# ── Subgraph Queries ───────────────────────────────────────────────

SWAP_QUERY = """
query Swaps($pool: String!, $first: Int!, $skip: Int!, $orderBy: String!, $orderDirection: String!, $blockGte: BigInt, $blockLte: BigInt) {
  swaps(
    first: $first,
    skip: $skip,
    orderBy: $orderBy,
    orderDirection: $orderDirection,
    where: { pool: $pool, block_gte: $blockGte, block_lte: $blockLte }
  ) {
    id
    blockNumber
    timestamp
    transaction { id }
    pool { id token0 { id symbol decimals } token1 { id symbol decimals } }
    sender
    recipient
    amount0
    amount1
    amountUSD
    sqrtPrice
    tick
    logIndex
  }
}
"""

MINT_BURN_QUERY = """
query LiquidityEvents($pool: String!, $first: Int!, $skip: Int!, $orderBy: String!, $orderDirection: String!, $eventTypes: [String!], $blockGte: BigInt, $blockLte: BigInt) {
  mints: events(
    first: $first,
    skip: $skip,
    orderBy: $orderBy,
    orderDirection: $orderDirection,
    where: { pool: $pool, type_in: $eventTypes, block_gte: $blockGte, block_lte: $blockLte }
  ) {
    id
    type
    blockNumber
    timestamp
    transaction { id }
    pool { id }
    owner
    amount
    amount0
    amount1
    tickLower
    tickUpper
    logIndex
  }
}
"""


def _subgraph_query(query: str, variables: Dict, timeout: int = 30) -> Any:
    """Execute a subgraph query."""
    payload = {"query": query, "variables": variables}
    try:
        resp = SESSION.post(SUBGRAPH_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        result = resp.json()
        if "errors" in result:
            return {"error": result["errors"], "source": "subgraph"}
        return result.get("data", {})
    except Exception as e:
        return {"error": str(e), "source": "subgraph"}


# ── Swap Collection ────────────────────────────────────────────────

def fetch_swaps(
    pool_id: str,
    pool_key: str,
    first: int = 1000,
    skip: int = 0,
    block_gte: Optional[int] = None,
    block_lte: Optional[int] = None,
) -> List[Dict]:
    """Fetch swap events from subgraph. Returns normalized AMM_SWAP records."""
    variables = {
        "pool": pool_id.lower(),
        "first": min(first, 1000),
        "skip": skip,
        "orderBy": "timestamp",
        "orderDirection": "asc",
        "blockGte": block_gte,
        "blockLte": block_lte,
    }

    data = _subgraph_query(SWAP_QUERY, variables)
    if "error" in data:
        return [{"error": str(data["error"]), "source": "subgraph", "market_id": pool_key}]

    swaps = data.get("swaps", [])
    pool_info = POOLS.get(pool_key, {})

    records = []
    for s in swaps:
        try:
            ts = datetime.fromtimestamp(int(s["timestamp"]), tz=timezone.utc).isoformat()
            record = {
                "venue": "uniswap_v3",
                "chain_if_applicable": "Ethereum",
                "market_id": pool_key,
                "pool_address": pool_info.get("pool_address", pool_id),
                "event_time_utc": ts,
                "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
                "source": "uniswap_v3_subgraph",
                "source_version": COLLECTOR_VERSION,
                "raw_identifier": f"uni3_swap_{pool_key}_{s['id']}",
                "schema_version": "1.0.0",
                "block_number": int(s["blockNumber"]),
                "tx_hash": s.get("transaction", {}).get("id", ""),
                "log_index": int(s.get("logIndex", 0)),
                "sender": s.get("sender", ""),
                "recipient": s.get("recipient", ""),
                "amount0": _safe_int(s.get("amount0", "0")),
                "amount1": _safe_int(s.get("amount1", "0")),
                "sqrt_price_x96": _safe_int(s.get("sqrtPrice", "0")),
                "tick": int(s.get("tick", 0)),
                "fee_tier": pool_info.get("fee_tier", 0),
                "pool_fee_amount0": None,
                "pool_fee_amount1": None,
            }
            records.append(record)
        except (KeyError, ValueError, TypeError, AttributeError):
            continue

    return records


def collect_full_swaps(
    pool_key: str,
    block_gte: Optional[int] = None,
    block_lte: Optional[int] = None,
    delay_between_requests: float = 0.2,
) -> Tuple[List[Dict], Dict]:
    """Paginate through all swaps for a pool."""
    pool_info = POOLS.get(pool_key, {})
    pool_address = pool_info.get("pool_address", "")

    all_records = []
    skip = 0
    page_size = 1000
    request_count = 0

    while True:
        records = fetch_swaps(
            pool_id=pool_address,
            pool_key=pool_key,
            first=page_size,
            skip=skip,
            block_gte=block_gte,
            block_lte=block_lte,
        )

        if records and "error" in records[0]:
            break

        if not records:
            break

        request_count += 1
        all_records.extend(records)

        if len(records) < page_size:
            break

        skip += page_size
        time.sleep(delay_between_requests)

    metadata = {
        "pool_key": pool_key,
        "pool_address": pool_address,
        "total_swaps": len(all_records),
        "requests_made": request_count,
        "status": "VALID" if len(all_records) > 0 else "PARTIAL",
        "note": "Subgraph is index layer. Raw path: Ethereum RPC + event logs.",
    }

    return all_records, metadata


# ── Liquidity Events (Mint/Burn) ──────────────────────────────────

def fetch_liquidity_events(
    pool_id: str,
    pool_key: str,
    event_types: List[str] = None,
    first: int = 1000,
    skip: int = 0,
    block_gte: Optional[int] = None,
    block_lte: Optional[int] = None,
) -> List[Dict]:
    """Fetch mint/burn events from subgraph."""
    if event_types is None:
        event_types = ["Mint", "Burn"]

    variables = {
        "pool": pool_id.lower(),
        "first": min(first, 1000),
        "skip": skip,
        "orderBy": "timestamp",
        "orderDirection": "asc",
        "eventTypes": event_types,
        "blockGte": block_gte,
        "blockLte": block_lte,
    }

    data = _subgraph_query(MINT_BURN_QUERY, variables)
    if "error" in data:
        return [{"error": str(data["error"]), "source": "subgraph", "market_id": pool_key}]

    events = data.get("mints", [])
    pool_info = POOLS.get(pool_key, {})

    records = []
    for e in events:
        try:
            ts = datetime.fromtimestamp(int(e["timestamp"]), tz=timezone.utc).isoformat()
            record = {
                "venue": "uniswap_v3",
                "chain_if_applicable": "Ethereum",
                "market_id": pool_key,
                "pool_address": pool_info.get("pool_address", pool_id),
                "event_time_utc": ts,
                "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
                "source": "uniswap_v3_subgraph",
                "source_version": COLLECTOR_VERSION,
                "raw_identifier": f"uni3_{e.get('type', 'unknown').lower()}_{pool_key}_{e['id']}",
                "schema_version": "1.0.0",
                "block_number": int(e["blockNumber"]),
                "tx_hash": e.get("transaction", {}).get("id", ""),
                "log_index": int(e.get("logIndex", 0)),
                "event_type": e.get("type", "unknown"),
                "owner": e.get("owner", ""),
                "amount": _safe_int(e.get("amount", "0")),
                "amount0": _safe_int(e.get("amount0", "0")),
                "amount1": _safe_int(e.get("amount1", "0")),
                "tick_lower": int(e.get("tickLower", 0)),
                "tick_upper": int(e.get("tickUpper", 0)),
                "liquidity": None,
            }
            records.append(record)
        except (KeyError, ValueError, TypeError, AttributeError):
            continue

    return records


# ── Price Conversion Utilities ─────────────────────────────────────

def sqrt_price_x96_to_price(
    sqrt_price_x96: int,
    token0_decimals: int,
    token1_decimals: int,
) -> float:
    """
    Convert sqrtPriceX96 to human-readable price.
    price = (sqrtPriceX96 / 2^96)^2 * (10^token0_decimals / 10^token1_decimals)

    For WETH/USDC (token0=USDC 6dec, token1=WETH 18dec):
    price in USDC per WETH
    """
    Q96 = 2 ** 96
    price = (sqrt_price_x96 / Q96) ** 2
    price = price * (10 ** token0_decimals) / (10 ** token1_decimals)
    return price


def amount_to_human(amount_raw: int, decimals: int) -> float:
    """Convert raw token amount to human-readable."""
    return amount_raw / (10 ** decimals)


# ── Verification Helpers ───────────────────────────────────────────

def verify_pool_identity(pool_key: str) -> Dict:
    """
    Verify pool identity by querying subgraph for pool contract data.
    Returns verification result.
    """
    pool_info = POOLS.get(pool_key, {})
    pool_address = pool_info.get("pool_address", "")

    query = """
    query Pool($id: String!) {
      pool(id: $id) {
        id
        token0 { id symbol decimals }
        token1 { id symbol decimals }
        feeTier
        liquidity
        sqrtPrice
        tick
      }
    }
    """
    data = _subgraph_query(query, {"id": pool_address.lower()})

    if "error" in data:
        return {
            "pool_key": pool_key,
            "verified": False,
            "error": str(data.get("error", "unknown")),
        }

    pool_data = data.get("pool")
    if not pool_data:
        return {
            "pool_key": pool_key,
            "verified": False,
            "error": "Pool not found in subgraph",
        }

    # Verify token ordering
    token0_addr = pool_data.get("token0", {}).get("id", "").lower()
    token1_addr = pool_data.get("token1", {}).get("id", "").lower()
    expected_t0 = pool_info.get("token0", "").lower()
    expected_t1 = pool_info.get("token1", "").lower()

    token_match = (token0_addr == expected_t0 and token1_addr == expected_t1)
    fee_match = int(pool_data.get("feeTier", 0)) == pool_info.get("fee_tier", 0)

    return {
        "pool_key": pool_key,
        "verified": token_match and fee_match,
        "subgraph_token0": token0_addr,
        "subgraph_token1": token1_addr,
        "expected_token0": expected_t0,
        "expected_token1": expected_t1,
        "token_order_match": token_match,
        "fee_tier_match": fee_match,
        "subgraph_fee_tier": pool_data.get("feeTier"),
        "current_liquidity": pool_data.get("liquidity"),
        "current_sqrt_price": pool_data.get("sqrtPrice"),
    }


def _safe_int(val) -> int:
    """Safely convert to int."""
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0
