#!/usr/bin/env python3
"""ALT-DATA-0 Hyperliquid funding-history batch.

For every coin in the CURRENT Hyperliquid meta universe, fetch the OLDEST
funding records (startTime=0 -> first 500 hourly funding rows). This yields
the first-funding timestamp per coin = INFERRED_FIRST_DATA_TIMESTAMP
(lower bound on listing).

Persists:
  probes/raw/hl_funding/<COIN>.json            raw API response
  probes/raw/hl_funding_first_history.json     composite summary

Read-only. No keys.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

HL = "https://api.hyperliquid.xyz/info"
S = requests.Session()
S.headers.update({"Content-Type": "application/json"})
SCHEMA_VERSION = "1.0.0"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> None:
    raw_dir = (Path(__file__).resolve().parent.parent / "probes" / "raw")
    meta_raw = raw_dir / "hyperliquid_meta.json"
    meta = json.loads(meta_raw.read_text(encoding="utf-8"))
    universe = meta["universe"]
    print(f"HL universe: {len(universe)} coins", flush=True)

    out_dir = raw_dir / "hl_funding"
    out_dir.mkdir(exist_ok=True)

    rows = []
    t0 = time.time()
    for i, u in enumerate(universe, 1):
        coin = u["name"]
        body = json.dumps({"type": "fundingHistory", "coin": coin,
                           "startTime": 0, "endTime": 2000000000000}).encode()
        rec = {"coin": coin, "is_delisted": bool(u.get("isDelisted", False)),
               "max_leverage": u.get("maxLeverage"),
               "sz_decimals": u.get("szDecimals"),
               "http_status": None, "ok": False, "error": None,
               "n_rows": 0, "first_funding_ts": None,
               "last_funding_ts": None, "sha256": None, "bytes": 0,
               "retrieved_at": datetime.now(timezone.utc).isoformat(
                   timespec="seconds")}
        try:
            r = S.post(HL, data=body, timeout=20)
            raw = r.content
            rec["http_status"] = r.status_code
            rec["ok"] = r.status_code == 200
            rec["sha256"] = sha256_bytes(raw)
            rec["bytes"] = len(raw)
            if r.status_code == 200:
                rows_data = json.loads(raw.decode("utf-8"))
                rec["n_rows"] = len(rows_data)
                if rows_data:
                    rec["first_funding_ts"] = rows_data[0]["time"]
                    rec["last_funding_ts"] = rows_data[-1]["time"]
                (out_dir / f"{coin}.json").write_bytes(raw)
        except Exception as e:  # noqa: BLE001
            rec["error"] = f"{type(e).__name__}: {e}"
        rows.append(rec)
        if i % 25 == 0:
            print(f"  {i}/{len(universe)} elapsed={time.time()-t0:.0f}s",
                  flush=True)
        time.sleep(0.35)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "probe": "hyperliquid_funding_first_history",
        "description": "first funding timestamp per HL coin (oldest funding "
                       "window via startTime=0)",
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "access_class": "PUBLIC",
        "n_coins": len(rows),
        "n_ok": sum(1 for r in rows if r["ok"]),
        "n_with_data": sum(1 for r in rows if r["n_rows"] > 0),
        "known_limitations": "startTime=0 returns the oldest 500 hourly rows; "
                             "first_funding_ts is an INFERRED first-data "
                             "timestamp (lower bound), not official listing "
                             "metadata. HTTP 500 on fundingHistory = coin "
                             "never listed or purged from index.",
        "coins": rows,
    }
    (raw_dir / "hyperliquid_funding_first_history.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8")
    print(f"done: {payload['n_ok']}/{len(rows)} ok, "
          f"{payload['n_with_data']} with data")


if __name__ == "__main__":
    sys.exit(main())
