"""
CRYPTO-MECH-2: Preregistered Base AMM 30d extension collector (resumable).

Uses ONLY the frozen DATA-1 base_amm_collector (1.3.0) code path for
fetching and decoding swap logs (_rpc_call / _parse_swap_log / SWAP_TOPIC /
CANONICAL_POOLS) for the preregistered window:

    base_weth_usdc_swap_30d
    window: 2026-07-21 00:00 UTC .. 2026-08-21 23:59:59 UTC
    start_block: 48901327 (frozen before download; recorded in _base_window.json)

Steps (resumable; progress in _base_collect_progress.json):
  fetch   -> paced eth_getLogs walk; appends raw logs to _base_raw_logs.jsonl
  finalize-> batch eth_getBlockByNumber timestamps + decode -> final JSON

Operational additions, all recorded in output metadata:
  1. User-Agent header on the frozen collector's requests.Session
     (mainnet.base.org rejects bare JSON-RPC POSTs with HTTP 403).
  2. Window end block resolved by binary search on block timestamps for
     2026-08-21T23:59:59 UTC so the range matches the frozen DATE window.
  3. Block timestamps resolved in JSON-RPC batches (80/call) instead of one
     call per block, for practical runtime. Same eth_getBlockByNumber data.

max_events cap bounds sample size for storage; if hit, metadata
['truncated']=True and the recorded sample covers the EARLIEST part of the
window (oldest events retained) — honest and reproducible. No window is
chosen after observing results.

Usage:
  python collect_base_extension.py fetch [--chunk N]
  python collect_base_extension.py finalize
Output: mech_2/base_weth_usdc_swap_30d.json
No alpha intent.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "data_1" / "collectors"))
import base_amm_collector as base  # noqa: E402

OUT = Path(__file__).resolve().parent

WINDOW_START_BLOCK = 48901327
WINDOW_END_UTC = datetime(2026, 8, 21, 23, 59, 59, tzinfo=timezone.utc)
MAX_RAW_LOGS = 150000   # bound for storage; truncation recorded if hit
POOL_KEY = "WETH-USDC-500"
DATASET = "base_weth_usdc_swap_30d"
CHAIN_ID = 8453
BATCH_BLOCKS = 5000
TS_BATCH = 100  # publicnode accepts 100-call batches; mainnet.base.org caps at 10
TS_ENDPOINT = base.BASE_RPC_ENDPOINTS[1]  # https://base-rpc.publicnode.com
SLEEP = 0.3
MAX_ATTEMPTS = 4

RAW_JSONL = OUT / "_base_raw_logs.jsonl"
PROGRESS = OUT / "_base_collect_progress.json"
TS_CACHE = OUT / "_base_ts_cache.jsonl"


def resolve_end_block() -> int:
    """Binary search for the last block with timestamp <= window end.

    Chain head (get_block_number) is always AFTER the frozen window end for
    this run, so it is a safe upper bound.
    """
    lo, hi = WINDOW_START_BLOCK, base.get_block_number()
    while lo < hi:
        mid = (lo + hi + 1) // 2
        ts = base.get_block_timestamp(mid)
        if ts <= WINDOW_END_UTC.timestamp():
            lo = mid
        else:
            hi = mid - 1
        time.sleep(0.02)
    return lo


def load_progress() -> Dict[str, Any]:
    if PROGRESS.exists():
        return json.load(open(PROGRESS, encoding="utf-8"))
    return {"last_block_covered": WINDOW_START_BLOCK - 1, "failed_ranges": [],
            "raw_logs_written": 0, "done": False}


def save_progress(p: Dict[str, Any]) -> None:
    json.dump(p, open(PROGRESS, "w", encoding="utf-8"))


def cmd_fetch(chunk: int = 0) -> None:
    base.SESSION.headers.update({"User-Agent": "crypto-quant-foundry/1.0 (research)"})
    end_block = resolve_end_block()
    pool_info = base.CANONICAL_POOLS[POOL_KEY]
    prog = load_progress()
    cur = prog["last_block_covered"] + 1
    raw_count = prog["raw_logs_written"]
    truncated = False

    # optional chunk limit for resumable runs within bounded wall time
    limit = None
    if chunk and chunk > 0:
        limit = cur + chunk * BATCH_BLOCKS

    print(f"{DATASET}: fetch {cur}..{end_block} (cap {MAX_RAW_LOGS}, "
          f"raw so far {raw_count})", flush=True)
    t0 = time.time()
    f = open(RAW_JSONL, "a", encoding="utf-8")
    try:
        while cur <= end_block:
            if raw_count >= MAX_RAW_LOGS:
                truncated = True
                break
            if limit and cur >= limit:
                break
            to = min(cur + BATCH_BLOCKS - 1, end_block)
            logs = None
            for attempt in range(MAX_ATTEMPTS):
                try:
                    logs = base._rpc_call("eth_getLogs", [{
                        "fromBlock": hex(cur), "toBlock": hex(to),
                        "address": pool_info["pool_address"],
                        "topics": [base.SWAP_TOPIC],
                    }], timeout=45)
                    break
                except Exception as e:
                    if attempt == MAX_ATTEMPTS - 1:
                        prog["failed_ranges"].append(
                            {"range": f"{cur}-{to}", "error": str(e)[:120],
                             "attempts": attempt + 1})
                    time.sleep(SLEEP * (attempt + 2))
            if logs:
                for lg in logs:
                    f.write(json.dumps(lg) + "\n")
                raw_count += len(logs)
            prog["last_block_covered"] = to
            prog["raw_logs_written"] = raw_count
            prog["truncated"] = truncated
            save_progress(prog)
            cur = to + 1
            time.sleep(SLEEP)
            if raw_count % 40000 == 0 and raw_count > 0:
                print(f"  {raw_count} raw logs, at block {cur} "
                      f"({time.time()-t0:.0f}s)", flush=True)
    finally:
        f.close()
    prog["truncated"] = truncated or (raw_count >= MAX_RAW_LOGS)
    prog["done"] = bool(cur > end_block)
    save_progress(prog)
    print(f"  fetch step done: {raw_count} raw logs, "
          f"last_block={prog['last_block_covered']}, "
          f"done={prog['done']}, truncated={prog['truncated']}, "
          f"failed={len(prog['failed_ranges'])} ({time.time()-t0:.0f}s)", flush=True)


def load_ts_cache() -> Dict[int, int]:
    cache: Dict[int, int] = {}
    if TS_CACHE.exists():
        with open(TS_CACHE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                cache[int(rec["block"])] = int(rec["ts"])
    return cache


def save_ts_batch(cache: Dict[int, int], batch: Dict[int, int]) -> None:
    with open(TS_CACHE, "a", encoding="utf-8") as f:
        for b, ts in batch.items():
            if b not in cache:
                f.write(json.dumps({"block": b, "ts": ts}) + "\n")


def cmd_timestamps(chunk_blocks: int = 0) -> None:
    """Resume-able timestamp resolution; appends to _base_ts_cache.jsonl."""
    base.SESSION.headers.update({"User-Agent": "crypto-quant-foundry/1.0 (research)"})
    raw_logs: List[Dict] = []
    with open(RAW_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                raw_logs.append(json.loads(line))
    blocks = sorted({int(lg.get("blockNumber", "0x0"), 16) for lg in raw_logs})
    cache = load_ts_cache()
    todo = [b for b in blocks if b not in cache]
    print(f"timestamps: {len(cache)} cached, {len(todo)} todo", flush=True)
    if chunk_blocks and chunk_blocks > 0:
        todo = todo[:chunk_blocks]
    t0 = time.time()
    for i in range(0, len(todo), TS_BATCH):
        chunk = todo[i:i + TS_BATCH]
        batch = [{"jsonrpc": "2.0", "id": j, "method": "eth_getBlockByNumber",
                  "params": [hex(b), False]} for j, b in enumerate(chunk)]
        got: Dict[int, int] = {}
        for attempt in range(3):
            try:
                resp = base.SESSION.post(TS_ENDPOINT, json=batch,
                                         timeout=60)
                for item in resp.json():
                    res = item.get("result")
                    if res:
                        got[int(res["number"], 16)] = int(res["timestamp"], 16)
                break
            except Exception:
                time.sleep(1.0 * (attempt + 1))
        if len(got) < len(chunk):
            # fallback: per-block via frozen collector for the missing ones
            for b in chunk:
                if b not in got:
                    try:
                        got[b] = base.get_block_timestamp(b)
                    except Exception:
                        pass
                    time.sleep(0.05)
        save_ts_batch(cache, got)
        cache.update(got)
        time.sleep(0.1)
        if (i // TS_BATCH) % 50 == 0:
            print(f"  resolved {len(cache)} blocks ({time.time()-t0:.0f}s)", flush=True)
    print(f"timestamps step done: {len(cache)} cached ({time.time()-t0:.0f}s)", flush=True)


def cmd_finalize() -> None:
    base.SESSION.headers.update({"User-Agent": "crypto-quant-foundry/1.0 (research)"})
    prog = load_progress()
    raw_logs: List[Dict] = []
    with open(RAW_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                raw_logs.append(json.loads(line))
    print(f"finalize: {len(raw_logs)} raw logs", flush=True)

    ts_map = load_ts_cache()
    blocks = sorted({int(lg.get("blockNumber", "0x0"), 16) for lg in raw_logs})
    missing = [b for b in blocks if b not in ts_map]
    print(f"  timestamps cached: {len(ts_map)}/{len(blocks)} (missing {len(missing)})", flush=True)

    pool_info = base.CANONICAL_POOLS[POOL_KEY]
    records: List[Dict] = []
    for lg in raw_logs:
        rec = base._parse_swap_log(lg, POOL_KEY, pool_info)
        if rec:
            bn = int(lg.get("blockNumber", "0x0"), 16)
            ts = ts_map.get(bn)
            if ts:
                rec["event_time_utc"] = (
                    datetime.fromtimestamp(ts, tz=timezone.utc).isoformat())
            records.append(rec)
    records.sort(key=lambda r: (r.get("block_number", 0), r.get("log_index", 0)))

    first_ts = records[0].get("event_time_utc") if records else None
    last_ts = records[-1].get("event_time_utc") if records else None
    out = {
        "records": records,
        "metadata": {
            "dataset": DATASET,
            "pool": pool_info["pool_address"],
            "chain_id": CHAIN_ID,
            "window_start_utc": "2026-07-21T00:00:00+00:00",
            "window_end_utc": "2026-08-21T23:59:59+00:00",
            "start_block": WINDOW_START_BLOCK,
            "end_block": prog.get("end_block"),
            "last_block_covered": prog.get("last_block_covered"),
            "truncated": prog.get("truncated", False),
            "max_raw_logs_cap": MAX_RAW_LOGS,
            "collector": "base_amm_collector 1.3.0 (frozen) via paced loop",
            "failed_block_ranges": prog.get("failed_ranges", []),
            "raw_logs": len(raw_logs),
            "unique_blocks": len(ts_map),
            "missing_timestamps": len(missing),
            "first_event_utc": first_ts,
            "last_event_utc": last_ts,
            "note": ("Sample starts at the frozen window start (2026-07-21); if "
                     "truncated, oldest events retained, later window events "
                     "not collected."),
        },
    }
    out_path = OUT / f"{DATASET}.json"
    json.dump(out, open(out_path, "w"), default=str)
    print(f"  -> {out_path}: {len(records)} records, "
          f"truncated={prog.get('truncated')}, "
          f"failed={len(prog.get('failed_ranges', []))}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "fetch"
    chunk = 0
    if "--chunk" in sys.argv:
        chunk = int(sys.argv[sys.argv.index("--chunk") + 1])
    if cmd == "finalize":
        cmd_finalize()
    elif cmd == "timestamps":
        cmd_timestamps(chunk)
    else:
        cmd_fetch(chunk)
