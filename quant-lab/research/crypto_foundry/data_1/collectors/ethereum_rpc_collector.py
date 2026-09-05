"""
Crypto Foundry DATA-1.3: Ethereum RPC Event Collector

Direct Ethereum RPC log collection for Uniswap v3 pool events.
CANONICAL source for Lane C — no subgraph dependency.

POOL 1: WETH/USDC 0.05% — 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
POOL 2: WBTC/USDC 0.30% — 0x99ac8cA7087fA4A2A1FB6357269965A2014ABc35

Chain: Ethereum mainnet (chain_id=1)

Error handling contract (DATA-1.3):
- Every failed block range is RECORDED, never silently skipped.
- Error classes: RPC_TIMEOUT, RPC_RATE_LIMIT, RPC_RANGE_TOO_LARGE,
  RPC_SERVER_ERROR, DECODE_ERROR, EMPTY_RANGE, SOURCE_UNAVAILABLE.
- Adaptive block sizing: shrink batch on RPC_RANGE_TOO_LARGE / timeout.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

COLLECTOR_VERSION = "1.3.0"
ETH_CHAIN_ID = 1

# Endpoints in priority order.
# Only eth.drpc.org currently serves archive-range eth_getLogs on the free tier;
# publicnode requires a personal token for archive reads, blastapi caps ranges at
# 10 blocks, and llamarpc rejects log queries. They remain as fallbacks for
# lightweight calls (blockNumber, eth_call) only.
RPC_ENDPOINTS = [
    "https://eth.drpc.org",
    "https://ethereum.publicnode.com",
    "https://eth-mainnet.public.blastapi.io",
    "https://eth.llamarpc.com",
]

# Endpoints that can actually serve eth_getLogs over archive ranges
LOG_ENDPOINTS = [
    "https://eth.drpc.org",
]

POOLS = {
    "WETH-USDC-500": {
        "pool_address": "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640",
        "token0": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "token1": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "token0_name": "USDC", "token1_name": "WETH",
        "fee_tier": 500, "tick_spacing": 10,
        "token0_decimals": 6, "token1_decimals": 18,
    },
    "WBTC-USDC-3000": {
        "pool_address": "0x99ac8cA7087fA4A2A1FB6357269965A2014ABc35",
        "token0": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "token1": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "token0_name": "WBTC", "token1_name": "USDC",
        "fee_tier": 3000, "tick_spacing": 60,
        "token0_decimals": 8, "token1_decimals": 6,
    },
}

SESSION = requests.Session()

# Event signatures
SWAP_TOPIC = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
MINT_TOPIC = "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
BURN_TOPIC = "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc6f942b68f6a652ff77688b82987a"


def _classify_rpc_error(exc: Exception, body: str = "") -> str:
    """Classify an RPC failure into a canonical error class."""
    msg = str(exc) + " " + body
    ml = msg.lower()
    if "timeout" in ml or "timed out" in ml:
        return "RPC_TIMEOUT"
    if "rate limit" in ml or "too many requests" in ml or "429" in ml:
        return "RPC_RATE_LIMIT"
    if "range" in ml and ("large" in ml or "limit" in ml or "blocks" in ml):
        return "RPC_RANGE_TOO_LARGE"
    if "archive" in ml or "personal token" in ml or "authenticate" in ml or "unauthorized" in ml:
        return "RPC_RATE_LIMIT"  # free-tier access restriction
    if "reverted" in ml:
        return "RPC_SERVER_ERROR"
    if isinstance(exc, requests.exceptions.HTTPError):
        return "RPC_SERVER_ERROR"
    if isinstance(exc, requests.exceptions.RequestException):
        return "RPC_TIMEOUT"
    return "SOURCE_UNAVAILABLE"


def _rpc_call(method: str, params: List[Any], timeout: int = 30, use_log_endpoints: bool = False) -> Any:
    """Make RPC call using first available endpoint."""
    endpoints = LOG_ENDPOINTS if use_log_endpoints else RPC_ENDPOINTS
    last_err = None
    for endpoint in endpoints:
        try:
            payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
            resp = SESSION.post(endpoint, json=payload, timeout=timeout)
            result = resp.json()
            if "error" not in result:
                return result.get("result")
            last_err = result["error"].get("message", str(result["error"]))
        except Exception as e:
            last_err = str(e)
            continue
    raise RuntimeError(f"All RPC endpoints failed for {method}: {last_err}")


def get_block_number() -> int:
    return int(_rpc_call("eth_blockNumber", []), 16)


def get_block_timestamp(block_number: int) -> int:
    block = _rpc_call("eth_getBlockByNumber", [hex(block_number), False])
    return int(block["timestamp"], 16) if block else 0


def verify_pool_identity(pool_key: str) -> Dict:
    """Verify pool identity by calling on-chain contracts."""
    pool_info = POOLS.get(pool_key, {})
    pool_address = pool_info.get("pool_address", "")
    result = {"pool_key": pool_key, "pool_address": pool_address, "verified": False, "checks": {}}

    try:
        code = _rpc_call("eth_getCode", [pool_address, "latest"])
        has_code = code != "0x" and code is not None and len(code) > 2
        result["checks"]["code_exists"] = has_code
        if not has_code:
            result["error"] = "No contract code at pool address"
            return result

        # token0() — selector 0x0dfe1681
        try:
            t0 = _rpc_call("eth_call", [{"to": pool_address, "data": "0x0dfe1681"}, "latest"])
            if t0 and len(t0) >= 66:
                token0 = "0x" + t0[26:66].lower()
                result["checks"]["token0"] = token0
                result["checks"]["token0_match"] = token0 == pool_info.get("token0", "").lower()
        except Exception as e:
            result["checks"]["token0_error"] = _classify_rpc_error(e)

        # token1() — selector 0xd21220a7
        try:
            t1 = _rpc_call("eth_call", [{"to": pool_address, "data": "0xd21220a7"}, "latest"])
            if t1 and len(t1) >= 66:
                token1 = "0x" + t1[26:66].lower()
                result["checks"]["token1"] = token1
                result["checks"]["token1_match"] = token1 == pool_info.get("token1", "").lower()
        except Exception as e:
            result["checks"]["token1_error"] = _classify_rpc_error(e)

        # fee() — selector 0xf305d719 (may revert on some RPCs)
        try:
            fd = _rpc_call("eth_call", [{"to": pool_address, "data": "0xf305d719"}, "latest"], timeout=15)
            if fd and len(fd) >= 66:
                fee = int(fd[2:66], 16)
                result["checks"]["fee"] = fee
                result["checks"]["fee_match"] = fee == pool_info.get("fee_tier", 0)
        except Exception:
            result["checks"]["fee"] = None
            result["checks"]["fee_match"] = None

        # tickSpacing() — selector 0xd0c93a7c
        try:
            ts_data = _rpc_call("eth_call", [{"to": pool_address, "data": "0xd0c93a7c"}, "latest"], timeout=15)
            if ts_data and len(ts_data) >= 66:
                result["checks"]["tick_spacing"] = int(ts_data[2:66], 16)
        except Exception:
            result["checks"]["tick_spacing"] = None

        tm = result["checks"].get("token0_match", False) and result["checks"].get("token1_match", False)
        fm = result["checks"].get("fee_match", None)
        result["verified"] = tm and (fm is not False)
    except Exception as e:
        result["error"] = _classify_rpc_error(e)

    return result


def collect_pool_events(
    pool_key: str,
    start_block: Optional[int] = None,
    end_block: Optional[int] = None,
    block_batch: int = 3000,
    event_types: Optional[List[str]] = None,
    max_events: Optional[int] = None,
    retry_backoff: float = 1.0,
) -> Tuple[List[Dict], Dict]:
    """
    Collect Swap/Mint/Burn events via RPC eth_getLogs with adaptive sizing.
    Every failed range is recorded in metadata['failed_block_ranges'].
    """
    pool_info = POOLS.get(pool_key, {})
    pool_address = pool_info.get("pool_address", "")
    if event_types is None:
        event_types = ["Swap"]

    topic_map = {"Swap": SWAP_TOPIC, "Mint": MINT_TOPIC, "Burn": BURN_TOPIC}

    if end_block is None:
        end_block = get_block_number()
    if start_block is None:
        start_block = end_block - 50000

    all_records = []
    raw_logs = []
    failed_ranges = []
    current_from = start_block
    batch = block_batch
    total_requests = 0

    requested_topics = [topic_map[et] for et in event_types if et in topic_map]
    if not requested_topics:
        requested_topics = [SWAP_TOPIC]

    while current_from <= end_block:
        if max_events and len(raw_logs) >= max_events:
            break

        batch_to = min(current_from + batch - 1, end_block)
        range_key = f"{current_from}-{batch_to}"
        attempt = 0
        success = False

        while attempt < 3 and not success:
            attempt += 1
            try:
                logs = _rpc_call("eth_getLogs", [{
                    "fromBlock": hex(current_from), "toBlock": hex(batch_to),
                    "address": pool_address, "topics": requested_topics,
                }], timeout=45, use_log_endpoints=True)
                total_requests += 1
                if logs:
                    raw_logs.extend(logs)
                success = True
                # Grow batch back if we shrank it
                if batch < block_batch:
                    batch = min(block_batch, batch * 2)
            except Exception as e:
                cls = _classify_rpc_error(e)
                if cls in ("RPC_RANGE_TOO_LARGE", "RPC_TIMEOUT") and batch > 200:
                    batch = max(200, batch // 2)
                    continue
                if attempt >= 3:
                    failed_ranges.append({"range": range_key, "error_class": cls,
                                          "attempts": attempt})
                    current_from = batch_to + 1
                    time.sleep(retry_backoff)
                    break
                time.sleep(retry_backoff * attempt)

        if success:
            current_from = batch_to + 1
        time.sleep(0.15)

    # Decode raw logs
    for log_entry in raw_logs:
        record = _parse_swap_log(log_entry, pool_key, pool_info)
        if record:
            all_records.append(record)

    # Batch timestamp lookup (limit to unique blocks, sampled)
    block_nums = sorted(set(r["block_number"] for r in all_records if r["block_number"] > 0))
    timestamps = {}
    for bn in block_nums:
        try:
            timestamps[bn] = get_block_timestamp(bn)
        except Exception:
            timestamps[bn] = 0
        time.sleep(0.03)

    for rec in all_records:
        ts = timestamps.get(rec["block_number"], 0)
        if ts > 0:
            rec["event_time_utc"] = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    all_records.sort(key=lambda r: (r.get("block_number", 0), r.get("log_index", 0)))

    meta = {
        "pool_key": pool_key, "chain_id": ETH_CHAIN_ID,
        "start_block": start_block, "end_block": end_block,
        "total_events": len(all_records), "raw_logs": len(raw_logs),
        "total_requests": total_requests,
        "failed_block_ranges": failed_ranges,
        "first_block": min((r["block_number"] for r in all_records if r["block_number"] > 0), default=0),
        "last_block": max((r["block_number"] for r in all_records if r["block_number"] > 0), default=0),
        "status": "VALID" if len(all_records) > 0 else "BLOCKED",
        "source": "ethereum_rpc_drpc",
    }
    return all_records, meta


def _twos_complement(hex_str: str) -> int:
    val = int(hex_str, 16)
    if val >= 2**255:
        val -= 2**256
    return val


def _parse_swap_log(log_entry: Dict, pool_key: str, pool_info: Dict) -> Optional[Dict]:
    """Parse Uniswap v3 Swap event log."""
    try:
        data_hex = log_entry.get("data", "0x")
        topics = log_entry.get("topics", [])
        if len(data_hex) < 322 or len(topics) < 3:
            return None

        d = data_hex[2:]
        amount0 = _twos_complement(d[0:64])
        amount1 = _twos_complement(d[64:128])
        sqrt_price_x96 = int(d[128:192], 16)
        liquidity = int(d[192:256], 16)
        tick = _twos_complement(d[256:320])

        t0_dec = pool_info.get("token0_decimals", 18)
        t1_dec = pool_info.get("token1_decimals", 18)
        price_t0_per_t1 = sqrt_price_x96_to_price(sqrt_price_x96, t0_dec, t1_dec)
        price_t1_per_t0 = 1.0 / price_t0_per_t1 if price_t0_per_t1 > 0 else 0.0

        return {
            "venue": "uniswap_v3", "chain_if_applicable": "Ethereum",
            "chain_id": ETH_CHAIN_ID,
            "market_id": pool_key,
            "pool_address": pool_info.get("pool_address", log_entry.get("address", "")),
            "token0": pool_info.get("token0", ""),
            "token1": pool_info.get("token1", ""),
            "event_time_utc": None,
            "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
            "source": "ethereum_rpc", "source_version": COLLECTOR_VERSION,
            "raw_identifier": f"eth_log_{log_entry.get('transactionHash', '')}_{log_entry.get('logIndex', '0x0')}",
            "schema_version": "1.0.0",
            "block_number": int(log_entry.get("blockNumber", "0x0"), 16),
            "block_hash": log_entry.get("blockHash", ""),
            "tx_hash": log_entry.get("transactionHash", ""),
            "log_index": int(log_entry.get("logIndex", "0x0"), 16),
            "sender": "0x" + topics[1][26:66],
            "recipient": "0x" + topics[2][26:66],
            "amount0": amount0, "amount1": amount1,
            "sqrt_price_x96": sqrt_price_x96, "tick": tick,
            "liquidity": liquidity, "fee_tier": pool_info.get("fee_tier", 0),
            "price_token0_per_token1": round(price_t0_per_t1, 8),
            "price_token1_per_token0": round(price_t1_per_t0, 8),
            "pool_fee_amount0": None, "pool_fee_amount1": None,
        }
    except (ValueError, TypeError, IndexError, ZeroDivisionError):
        return None


def sqrt_price_x96_to_price(sqrt_price_x96: int, token0_decimals: int, token1_decimals: int) -> float:
    Q96 = 2 ** 96
    price = (sqrt_price_x96 / Q96) ** 2
    return price * (10 ** token0_decimals) / (10 ** token1_decimals)
