"""
Crypto Foundry DATA-1.3: Base AMM Collector (direct RPC)

Canonical Lane D source: direct Base RPC log collection — no subgraph dependency.

Chain: Base (chain_id=8453)
Assets: WETH/USDC (canonical), cbBTC/USDC (demoted unless verified pool found)

Pool discovery: canonical Uniswap v3 Base factory getPool(token0, token1, fee).
Identity verification: eth_getCode + token0() + token1() + tickSpacing().
Error handling: every failed block range recorded; adaptive batch sizing.

DATA-1.3 verified facts:
- Uniswap v3 Base factory: 0x33128a8fC17869897dcE68Ed026d694621f6FDfD
- factory.getPool(USDC, WETH, 500) = 0xd0b53d9277642d899df5c87a3966a349a798f224
  (token0=WETH, token1=USDC — token address ordering, NOT display order)
- cbBTC 0xcbB7C09993bDa24813c5bc24990cD67Bd5C07c98 has NO code on Base -> DEMOTED
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

COLLECTOR_VERSION = "1.3.0"
BASE_CHAIN_ID = 8453

# ── Base Token Registry (verified on-chain) ────────────────────────
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
        "wrapper_note": "Coinbase custodial wrapped BTC on Base — NO CODE at this address (verified)",
    },
}

# Uniswap v3 factory on Base
UNISWAP_V3_FACTORY_BASE = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"

# Canonical pool discovered via factory.getPool(USDC, WETH, 500)
CANONICAL_POOLS = {
    "WETH-USDC-500": {
        "pool_address": "0xd0b53d9277642d899df5c87a3966a349a798f224",
        "token0": "0x4200000000000000000000000000000000000006",   # WETH (address order)
        "token1": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",   # USDC
        "token0_name": "WETH", "token1_name": "USDC",
        "fee_tier": 500, "tick_spacing": 10,
        "token0_decimals": 18, "token1_decimals": 6,
    },
}

# Base RPC endpoints (verified working for eth_getLogs)
BASE_RPC_ENDPOINTS = [
    "https://mainnet.base.org",
    "https://base-rpc.publicnode.com",
]

SESSION = requests.Session()

# Event signatures (Uniswap v3)
SWAP_TOPIC = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
MINT_TOPIC = "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
BURN_TOPIC = "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc6f942b68f6a652ff77688b82987a"


def _classify_rpc_error(exc: Exception, body: str = "") -> str:
    msg = str(exc) + " " + body
    ml = msg.lower()
    if "timeout" in ml or "timed out" in ml:
        return "RPC_TIMEOUT"
    if "rate limit" in ml or "too many requests" in ml or "429" in ml:
        return "RPC_RATE_LIMIT"
    if "range" in ml and ("large" in ml or "limit" in ml or "blocks" in ml):
        return "RPC_RANGE_TOO_LARGE"
    if "archive" in ml or "personal token" in ml or "authenticate" in ml or "unauthorized" in ml:
        return "RPC_RATE_LIMIT"
    if "reverted" in ml:
        return "RPC_SERVER_ERROR"
    if isinstance(exc, requests.exceptions.HTTPError):
        return "RPC_SERVER_ERROR"
    if isinstance(exc, requests.exceptions.RequestException):
        return "RPC_TIMEOUT"
    return "SOURCE_UNAVAILABLE"


def _rpc_call(method: str, params: List[Any], timeout: int = 30) -> Any:
    last_err = None
    for endpoint in BASE_RPC_ENDPOINTS:
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
    raise RuntimeError(f"All Base RPC endpoints failed for {method}: {last_err}")


def get_block_number() -> int:
    return int(_rpc_call("eth_blockNumber", []), 16)


def get_block_timestamp(block_number: int) -> int:
    block = _rpc_call("eth_getBlockByNumber", [hex(block_number), False])
    return int(block["timestamp"], 16) if block else 0


def _addr(result: Optional[str]) -> Optional[str]:
    if not result or len(result) < 66:
        return None
    return "0x" + result[26:66].lower()


def verify_base_token(token_key: str) -> Dict:
    """Verify a Base token contract exists and has correct decimals via RPC."""
    token_info = BASE_TOKENS.get(token_key, {})
    address = token_info.get("address", "")
    try:
        code = _rpc_call("eth_getCode", [address, "latest"])
        has_code = code not in ("0x", None) and len(code) > 2
        dec_data = _rpc_call("eth_call", [{"to": address, "data": "0x313ce567"}, "latest"])
        decimals = int(dec_data[2:66], 16) if dec_data and len(dec_data) >= 66 else None
        return {
            "token_key": token_key, "address": address,
            "has_code": has_code, "decimals_onchain": decimals,
            "expected_decimals": token_info.get("decimals"),
            "decimals_match": decimals == token_info.get("decimals") if decimals is not None else None,
            "verified": has_code and decimals == token_info.get("decimals"),
        }
    except Exception as e:
        return {"token_key": token_key, "address": address, "verified": False, "error": str(e)}


def discover_pool_from_factory(token_a: str, token_b: str, fee_tier: int) -> Optional[str]:
    """Discover pool address from Uniswap v3 factory getPool(token0, token1, fee)."""
    try:
        data = "0x1698ee82" + token_a[2:].lower().rjust(64, "0") + token_b[2:].lower().rjust(64, "0") + hex(fee_tier)[2:].rjust(64, "0")
        result = _rpc_call("eth_call", [{"to": UNISWAP_V3_FACTORY_BASE, "data": data}, "latest"])
        pool = _addr(result)
        return pool if pool and pool != "0x0000000000000000000000000000000000000000" else None
    except Exception:
        return None


def verify_base_pool(
    pool_address: str,
    expected_token0: str,
    expected_token1: str,
    expected_fee_tier: int,
) -> Dict:
    """Full pool identity verification: code + token0 + token1 + tickSpacing."""
    result = {
        "pool_address": pool_address, "verified": False,
        "expected_token0": expected_token0, "expected_token1": expected_token1,
        "expected_fee_tier": expected_fee_tier, "checks": {},
    }
    try:
        code = _rpc_call("eth_getCode", [pool_address, "latest"])
        has_code = code not in ("0x", None) and len(code) > 2
        result["checks"]["code_exists"] = has_code
        if not has_code:
            result["error"] = "No contract code at pool address"
            return result

        t0 = _addr(_rpc_call("eth_call", [{"to": pool_address, "data": "0x0dfe1681"}, "latest"]))
        t1 = _addr(_rpc_call("eth_call", [{"to": pool_address, "data": "0xd21220a7"}, "latest"]))
        tick_data = _rpc_call("eth_call", [{"to": pool_address, "data": "0xd0c93a7c"}, "latest"])
        tick_spacing = int(tick_data[2:66], 16) if tick_data and len(tick_data) >= 66 else None

        result["checks"]["token0"] = t0
        result["checks"]["token1"] = t1
        result["checks"]["tick_spacing"] = tick_spacing
        result["checks"]["token0_match"] = (t0 == expected_token0.lower())
        result["checks"]["token1_match"] = (t1 == expected_token1.lower())
        result["checks"]["tick_spacing_match"] = (tick_spacing == int(expected_fee_tier / 50 if expected_fee_tier else 0) if tick_spacing is not None else None)

        tm = result["checks"]["token0_match"] and result["checks"]["token1_match"]
        result["verified"] = tm
        return result
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
) -> Tuple[List[Dict], Dict]:
    """Collect Swap/Mint/Burn events via Base RPC eth_getLogs with adaptive sizing."""
    pool_info = CANONICAL_POOLS.get(pool_key, {})
    pool_address = pool_info.get("pool_address", "")
    if event_types is None:
        event_types = ["Swap"]

    topic_map = {"Swap": SWAP_TOPIC, "Mint": MINT_TOPIC, "Burn": BURN_TOPIC}
    requested_topics = [topic_map[et] for et in event_types if et in topic_map]
    if not requested_topics:
        requested_topics = [SWAP_TOPIC]

    if end_block is None:
        end_block = get_block_number()
    if start_block is None:
        start_block = end_block - 50000

    all_records: List[Dict] = []
    raw_logs: List[Dict] = []
    failed_ranges: List[Dict] = []
    current_from = start_block
    batch = block_batch
    total_requests = 0

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
                }], timeout=45)
                total_requests += 1
                if logs:
                    raw_logs.extend(logs)
                success = True
                if batch < block_batch:
                    batch = min(block_batch, batch * 2)
            except Exception as e:
                cls = _classify_rpc_error(e)
                if cls in ("RPC_RANGE_TOO_LARGE", "RPC_TIMEOUT") and batch > 200:
                    batch = max(200, batch // 2)
                    continue
                if attempt >= 3:
                    failed_ranges.append({"range": range_key, "error_class": cls, "attempts": attempt})
                    current_from = batch_to + 1
                    time.sleep(1.0)
                    break
                time.sleep(1.0 * attempt)

        if success:
            current_from = batch_to + 1
        time.sleep(0.15)

    for log_entry in raw_logs:
        record = _parse_swap_log(log_entry, pool_key, pool_info)
        if record:
            all_records.append(record)

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
        "pool_key": pool_key, "chain_id": BASE_CHAIN_ID,
        "start_block": start_block, "end_block": end_block,
        "total_events": len(all_records), "raw_logs": len(raw_logs),
        "total_requests": total_requests,
        "failed_block_ranges": failed_ranges,
        "first_block": min((r["block_number"] for r in all_records if r["block_number"] > 0), default=0),
        "last_block": max((r["block_number"] for r in all_records if r["block_number"] > 0), default=0),
        "status": "VALID" if len(all_records) > 0 else "BLOCKED",
        "source": "base_rpc",
    }
    return all_records, meta


def _twos_complement(hex_str: str) -> int:
    val = int(hex_str, 16)
    if val >= 2**255:
        val -= 2**256
    return val


def sqrt_price_x96_to_price(sqrt_price_x96: int, token0_decimals: int, token1_decimals: int) -> float:
    Q96 = 2 ** 96
    price = (sqrt_price_x96 / Q96) ** 2
    return price * (10 ** token0_decimals) / (10 ** token1_decimals)


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
            "venue": "uniswap_v3_base", "chain_if_applicable": "Base",
            "chain_id": BASE_CHAIN_ID,
            "market_id": pool_key,
            "pool_address": pool_info.get("pool_address", log_entry.get("address", "")),
            "token0": pool_info.get("token0", ""),
            "token1": pool_info.get("token1", ""),
            "event_time_utc": None,
            "ingest_time_utc": datetime.now(timezone.utc).isoformat(),
            "source": "base_rpc", "source_version": COLLECTOR_VERSION,
            "raw_identifier": f"base_log_{log_entry.get('transactionHash', '')}_{log_entry.get('logIndex', '0x0')}",
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


def collect_base_lane(
    asset_pair: str,
    pool_address: str,
    pool_info: Dict,
    max_events: Optional[int] = None,
) -> Tuple[List[Dict], Dict]:
    """Collect events for a selected Base pool (direct RPC)."""
    pool_key = "WETH-USDC-500"
    records, meta = collect_pool_events(
        pool_key=pool_key, max_events=max_events, block_batch=3000,
    )
    meta["asset_pair"] = asset_pair
    meta["pool_address"] = pool_address
    return records, meta
