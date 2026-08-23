"""
CRYPTO-MECH-2: Preregistered AMM research extension collector (30d window),
bounded by a max-log cap for git/practicality.

Phase 1: raw eth_getLogs with paced batches, oldest-first from the frozen
window start (2026-07-21 00:00 UTC). Phase 2: batch JSON-RPC block
timestamps. Phase 3: decode with frozen collector parsers.

Cap: MAX_RAW_LOGS per pool. If the cap is hit, the manifest records
"truncated": true — the sample covers the earliest part of the frozen
window (oldest events retained), which is honest and reproducible.

eth: 25577000 .. latest
base: 48901327 .. latest

Usage: python collect_amm_extension.py [eth|base|all]
Output: mech_2/{dataset}_30d.json
No alpha intent.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "data_1" / "collectors"))
import ethereum_rpc_collector as eth  # noqa: E402
import base_amm_collector as base     # noqa: E402

OUT = Path(__file__).resolve().parent

SLEEP = 0.5
BATCH = 5000
MAX_ATTEMPTS = 4
TS_BATCH = 80
MAX_RAW_LOGS = 120000   # bounded sample; truncation recorded if hit

ETH_START = 25577000
BASE_START = 48901327


def fetch_raw_logs(rpc_module, pool_address: str, start_block: int,
                   end_block: int, dataset: str) -> Dict[str, Any]:
    raw_logs = []
    failed = []
    cur = start_block
    truncated = False
    while cur <= end_block:
        if len(raw_logs) >= MAX_RAW_LOGS:
            truncated = True
            break
        to = min(cur + BATCH - 1, end_block)
        for attempt in range(MAX_ATTEMPTS):
            try:
                logs = rpc_module._rpc_call("eth_getLogs", [{
                    "fromBlock": hex(cur), "toBlock": hex(to),
                    "address": pool_address,
                    "topics": [rpc_module.SWAP_TOPIC]}],
                    timeout=45, use_log_endpoints=True)
                raw_logs.extend(logs or [])
                break
            except Exception as e:
                if attempt == MAX_ATTEMPTS - 1:
                    failed.append({"range": f"{cur}-{to}",
                                   "error": str(e)[:120], "attempts": attempt + 1})
                time.sleep(SLEEP * (attempt + 2))
        cur = to + 1
        time.sleep(SLEEP)
        if len(raw_logs) % 30000 == 0 and len(raw_logs) > 0:
            print(f"  {dataset}: {len(raw_logs)} raw logs, at block {cur}")
    return {"raw_logs": raw_logs, "failed_block_ranges": failed,
            "truncated": truncated, "last_block_covered": cur - 1}


def resolve_timestamps_batch(rpc_module, raw_logs: List[Dict]) -> Dict[int, int]:
    blocks = sorted({int(lg.get("blockNumber", "0x0"), 16) for lg in raw_logs})
    ts_map: Dict[int, int] = {}
    endpoints = getattr(rpc_module, "LOG_ENDPOINTS", None) or rpc_module.RPC_ENDPOINTS
    endpoint = endpoints[0]
    for i in range(0, len(blocks), TS_BATCH):
        chunk = blocks[i:i + TS_BATCH]
        batch = [{"jsonrpc": "2.0", "id": j, "method": "eth_getBlockByNumber",
                  "params": [hex(b), False]} for j, b in enumerate(chunk)]
        for attempt in range(3):
            try:
                resp = requests.post(endpoint, json=batch, timeout=45)
                for item in resp.json():
                    res = item.get("result")
                    if res:
                        ts_map[int(res["number"], 16)] = int(res["timestamp"], 16)
                break
            except Exception:
                time.sleep(1.0 * (attempt + 1))
        time.sleep(0.15)
    return ts_map


def decode_logs(raw_logs: List[Dict], ts_map: Dict[int, int],
                parser) -> List[Dict]:
    records = []
    for lg in raw_logs:
        rec = parser(lg)
        if rec:
            bn = int(lg.get("blockNumber", "0x0"), 16)
            ts = ts_map.get(bn)
            if ts:
                rec["event_time_utc"] = (
                    datetime.fromtimestamp(ts, tz=timezone.utc).isoformat())
            records.append(rec)
    return records


def run_pool(rpc_module, pool_key: str, start_block: int, dataset: str,
             chain_id: int) -> None:
    info = rpc_module.POOLS[pool_key]
    end_block = rpc_module.get_block_number()
    print(f"{dataset}: {pool_key} window {start_block}..{end_block} "
          f"(cap {MAX_RAW_LOGS})")
    raw = fetch_raw_logs(rpc_module, info["pool_address"], start_block,
                         end_block, dataset)
    print(f"  raw logs: {len(raw['raw_logs'])}, failed: "
          f"{len(raw['failed_block_ranges'])}, truncated: {raw['truncated']}")
    ts_map = resolve_timestamps_batch(rpc_module, raw["raw_logs"])
    print(f"  resolved timestamps: {len(ts_map)} unique blocks")
    records = decode_logs(raw["raw_logs"], ts_map,
                          lambda lg, k=pool_key: rpc_module._parse_swap_log(lg, k, rpc_module.POOLS[k]))
    first_ts = records[0]["event_time_utc"] if records else None
    last_ts = records[-1]["event_time_utc"] if records else None
    res = {
        "records": records,
        "metadata": {
            "dataset": dataset, "pool": info["pool_address"], "chain_id": chain_id,
            "window_start_utc": "2026-07-21T00:00:00+00:00",
            "window_end_utc": "2026-08-21T23:59:59+00:00",
            "start_block": start_block, "end_block": end_block,
            "last_block_covered": raw["last_block_covered"],
            "truncated": raw["truncated"],
            "max_raw_logs_cap": MAX_RAW_LOGS,
            "collector": "frozen DATA-1 collector via bounded extension loop",
            "failed_block_ranges": raw["failed_block_ranges"],
            "raw_logs": len(raw["raw_logs"]),
            "unique_blocks": len(ts_map),
            "first_event_utc": first_ts, "last_event_utc": last_ts,
            "note": ("Sample starts at the frozen window start (2026-07-21); "
                     "if truncated, oldest events retained, later window "
                     "events not collected."),
        },
    }
    out = OUT / f"{dataset}.json"
    json.dump(res, open(out, "w"))
    print(f"  -> {out}: {len(records)} records, {len(raw['failed_block_ranges'])} "
          f"failed ranges, truncated={raw['truncated']}")


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "eth"):
        run_pool(eth, "WETH-USDC-500", ETH_START, "eth_weth_usdc_swap_30d", 1)
        run_pool(eth, "WBTC-USDC-3000", ETH_START, "eth_wbtc_usdc_swap_30d", 1)
    if which in ("all", "base"):
        run_pool(base, "WETH-USDC-500", BASE_START, "base_weth_usdc_swap_30d", 8453)


if __name__ == "__main__":
    main()
