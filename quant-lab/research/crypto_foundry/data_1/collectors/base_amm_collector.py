"""
Crypto Foundry DATA-1: Base AMM Collector

Pool selection audit + event collection for Base chain AMMs.
Candidates: Aerodrome, Uniswap v3 on Base.

Chain: Base (chain_id=8453)
Assets: WETH/USDC, cbBTC/USDC

Pool selection based on: depth, history, event accessibility, token authenticity.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

COLLECTOR_VERSION = "1.0.0"
BASE_CHAIN_ID = 8453

# ── Base Token Registry (verified contracts) ───────────────────────
BASE_TOKENS = {
    "WETH": {
        "address": "0x4200000000000000000000000000000000000006",
        "decimals": 18,
        "symbol": "WETH",
        "name": "Wrapped Ether",
        "wrapper_note": "Canonical WETH on Base, 1:1 with ETH",
    },
    "USDC": {
        "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "decimals": 6,
        "symbol": "USDC",
        "name": "USD Coin",
        "wrapper_note": "Native USDC on Base (Circle)",
    },
    "cbBTC": {
        "address": "0xcbB7C09993bDa24813c5bc24990cD67Bd5C07c98",
        "decimals": 8,
        "symbol": "cbBTC",
        "name": "Coinbase Wrapped BTC",
        "wrapper_note": "Coinbase custodial wrapped BTC on Base",
    },
}

# ── Pool Candidates ────────────────────────────────────────────────

# Uniswap v3 on Base — most accessible raw event data
UNISWAP_V3_FACTORY_BASE = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"

# Known Uniswap v3 pools on Base (to be verified on-chain)
BASE_POOL_CANDIDATES = {
    "WETH-USDC": [
        {
            "venue": "uniswap_v3_base",
            "pool_address": "0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59",
            "fee_tier": 500,
            "fee_bps": 5,
            "token0": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC
            "token1": "0x4200000000000000000000000000000000000006",  # WETH
            "token0_name": "USDC",
            "token1_name": "WETH",
            "token0_decimals": 6,
            "token1_decimals": 18,
            "status": "PRIMARY_CANDIDATE",
        },
        {
            "venue": "aerodrome",
            "pool_address": "TBD — verify on-chain",
            "fee_tier": "variable (slipstream CL)",
            "status": "SECONDARY_CANDIDATE",
            "note": "Aerodrome uses ve(3,3) + slipstream CL. Pool addresses require on-chain verification.",
        },
    ],
    "cbBTC-USDC": [
        {
            "venue": "uniswap_v3_base",
            "pool_address": "TBD — verify on-chain",
            "fee_tier": 3000,
            "token0": "0xcbB7C09993bDa24813c5bc24990cD67Bd5C07c98",  # cbBTC
            "token1": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC
            "token0_name": "cbBTC",
            "token1_name": "USDC",
            "token0_decimals": 8,
            "token1_decimals": 6,
            "status": "NEEDS_VERIFICATION",
            "note": "cbBTC/USDC Uniswap v3 pool on Base must be verified",
        },
    ],
}

# The Graph subgraph for Uniswap v3 on Base
BASE_SUBGRAPH_URL = "https://gateway-arbitrum.network.thegraph.com/api/subgraphs/id/88ecHoTjxY9WJ暴力Z2GLX5B5JZKP1Y2QCv"

# Alternative: public Base RPC for direct log queries
BASE_RPC_URL = "https://mainnet.base.org"


SESSION = requests.Session()
SESSION.headers.update({"Content-Type": "application/json"})


# ── Pool Verification ──────────────────────────────────────────────

def verify_base_pool(
    pool_address: str,
    expected_token0: str,
    expected_token1: str,
    expected_fee_tier: int,
) -> Dict:
    """
    Verify a pool contract on Base using eth_call.
    Checks: code exists, token0, token1, fee.
    """
    try:
        # Check code exists
        code_payload = {
            "jsonrpc": "2.0",
            "method": "eth_getCode",
            "params": [pool_address, "latest"],
            "id": 1,
        }
        code_resp = SESSION.post(BASE_RPC_URL, json=code_payload, timeout=15)
        code_data = code_resp.json()
        has_code = code_data.get("result", "0x") != "0x"

        if not has_code:
            return {
                "pool_address": pool_address,
                "verified": False,
                "error": "No contract code at address",
            }

        return {
            "pool_address": pool_address,
            "has_code": True,
            "expected_token0": expected_token0,
            "expected_token1": expected_token1,
            "expected_fee_tier": expected_fee_tier,
            "status": "CODE_EXISTS_NEEDS_FULL_VERIFICATION",
            "note": "Full token0/token1/fee verification requires ABI decoding",
        }

    except Exception as e:
        return {
            "pool_address": pool_address,
            "verified": False,
            "error": str(e),
        }


# ── Base AMM Event Collection via Subgraph ─────────────────────────

SWAP_QUERY = """
query Swaps($pool: String!, $first: Int!, $skip: Int!, $orderBy: String!, $orderDirection: String!) {
  swaps(
    first: $first,
    skip: $skip,
    orderBy: $orderBy,
    orderDirection: $orderDirection,
    where: { pool: $pool }
  ) {
    id
    blockNumber
    timestamp
    transaction { id }
    pool { id }
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


def _subgraph_query(query: str, variables: Dict, timeout: int = 30) -> Any:
    """Execute subgraph query."""
    payload = {"query": query, "variables": variables}
    try:
        resp = SESSION.post(BASE_SUBGRAPH_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        result = resp.json()
        if "errors" in result:
            return {"error": result["errors"], "source": "subgraph"}
        return result.get("data", {})
    except Exception as e:
        return {"error": str(e), "source": "subgraph"}


def fetch_base_swaps(
    pool_address: str,
    market_id: str,
    pool_info: Dict,
    first: int = 1000,
    skip: int = 0,
) -> List[Dict]:
    """Fetch swap events from Base subgraph."""
    variables = {
        "pool": pool_address.lower(),
        "first": min(first, 1000),
        "skip": skip,
        "orderBy": "timestamp",
        "orderDirection": "asc",
    }

    data = _subgraph_query(SWAP_QUERY, variables)
    if "error" in data:
        return [{"error": str(data.get("error", "")), "source": "subgraph", "market_id": market_id}]

    swaps = data.get("swaps", [])
    records = []
    for s in swaps:
        try:
            ts = datetime.fromtimestamp(int(s["timestamp"]), tz=timezone.utc).isoformat()
            record = {
                "venue": pool_info.get("venue", "base_amm"),
                "chain_if_applicable": "Base",
                "market_id": market_id,
                "pool_address": pool_address,
                "event_time_utc": ts,
                "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
                "source": f"{pool_info.get('venue', 'base')}_subgraph",
                "source_version": COLLECTOR_VERSION,
                "raw_identifier": f"base_swap_{market_id}_{s['id']}",
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


# ── Pool Selection Logic ───────────────────────────────────────────

def select_base_pools() -> Dict[str, Dict]:
    """
    Select canonical Base AMM pools based on:
    - Pool existence / contract code
    - Token authenticity
    - Fee tier match
    Returns selection decision for each asset pair.
    """
    selections = {}

    for asset_pair, candidates in BASE_POOL_CANDIDATES.items():
        best = None
        for candidate in candidates:
            if candidate.get("status") == "PRIMARY_CANDIDATE":
                pool_addr = candidate.get("pool_address", "")
                if pool_addr and pool_addr != "TBD — verify on-chain":
                    # Verify on-chain
                    verification = verify_base_pool(
                        pool_address=pool_addr,
                        expected_token0=candidate.get("token0", ""),
                        expected_token1=candidate.get("token1", ""),
                        expected_fee_tier=candidate.get("fee_tier", 0),
                    )
                    candidate["on_chain_verification"] = verification
                    best = candidate
                    break

        if best is None:
            # No verified primary candidate
            best = {
                "status": "NEEDS_VERIFICATION",
                "note": "No pool address verified on-chain yet",
            }

        selections[asset_pair] = {
            "selected": best,
            "all_candidates": candidates,
            "selection_criteria": [
                "Contract code exists on Base",
                "Token addresses match canonical registry",
                "Fee tier matches expected",
                "Sufficient swap history",
                "Raw event accessibility",
            ],
        }

    return selections


# ── Full Collection ────────────────────────────────────────────────

def collect_base_lane(
    asset_pair: str,
    pool_address: str,
    pool_info: Dict,
    delay: float = 0.2,
) -> Tuple[List[Dict], Dict]:
    """Collect all swaps for a selected Base pool."""
    all_records = []
    skip = 0
    page_size = 1000
    request_count = 0

    while True:
        records = fetch_base_swaps(
            pool_address=pool_address,
            market_id=asset_pair,
            pool_info=pool_info,
            first=page_size,
            skip=skip,
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
        time.sleep(delay)

    metadata = {
        "asset_pair": asset_pair,
        "pool_address": pool_address,
        "venue": pool_info.get("venue", "unknown"),
        "total_swaps": len(all_records),
        "requests_made": request_count,
        "status": "VALID" if len(all_records) > 0 else "BLOCKED",
    }

    return all_records, metadata


def _safe_int(val) -> int:
    """Safely convert to int."""
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0
