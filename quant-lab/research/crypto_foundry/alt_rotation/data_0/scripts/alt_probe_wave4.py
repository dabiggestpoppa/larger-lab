#!/usr/bin/env python3
"""ALT-DATA-0 wave-4 probes.

- Retry the 20 HL coins that hit HTTP 429 in the funding batch (backoff)
- CoinPaprika in-window cross-checks for a handful of snapshot coins at
  2026-08-20 (rank/mcap consistency evidence)
- CMC snapshot tags drift test across dates (sector PIT vs current)
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

S = requests.Session()
S.headers.update({"Content-Type": "application/json"})
SCHEMA_VERSION = "1.0.0"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> None:
    raw_dir = Path(__file__).resolve().parent.parent / "probes" / "raw"
    hist = json.loads(
        (raw_dir / "hyperliquid_funding_first_history.json")
        .read_text(encoding="utf-8"))
    retry_coins = [r["coin"] for r in hist["coins"] if r["http_status"] == 429]
    print(f"retrying {len(retry_coins)} HL coins", flush=True)
    retried = []
    out_dir = raw_dir / "hl_funding"
    for coin in retry_coins:
        for attempt in range(3):
            body = json.dumps({"type": "fundingHistory", "coin": coin,
                               "startTime": 0,
                               "endTime": 2000000000000}).encode()
            try:
                r = S.post("https://api.hyperliquid.xyz/info", data=body,
                           timeout=20)
            except Exception as e:  # noqa: BLE001
                r = None
                err = f"{type(e).__name__}: {e}"
            if r is not None and r.status_code == 200:
                rows_data = json.loads(r.content.decode("utf-8"))
                rec = {"coin": coin, "ok": True, "http_status": 200,
                       "n_rows": len(rows_data),
                       "first_funding_ts": rows_data[0]["time"] if rows_data
                       else None,
                       "last_funding_ts": rows_data[-1]["time"] if rows_data
                       else None,
                       "sha256": sha256_bytes(r.content),
                       "bytes": len(r.content),
                       "retrieved_at": datetime.now(timezone.utc).isoformat(
                           timespec="seconds")}
                (out_dir / f"{coin}.json").write_bytes(r.content)
                retried.append(rec)
                print(f"  {coin} OK first={rec['first_funding_ts']}",
                      flush=True)
                break
            time.sleep(2 + attempt * 2)
        else:
            retried.append({"coin": coin, "ok": False, "http_status":
                            r.status_code if r else None,
                            "error": locals().get("err", "retry failed")})
    for rec in retried:
        hit = next(x for x in hist["coins"] if x["coin"] == rec["coin"])
        for k, v in rec.items():
            hit[k] = v
    hist["n_ok"] = sum(1 for r in hist["coins"] if r["ok"] and r["n_rows"] > 0)
    hist["retried_at"] = datetime.now(timezone.utc).isoformat(
        timespec="seconds")
    (raw_dir / "hyperliquid_funding_first_history.json").write_text(
        json.dumps(hist, indent=2), encoding="utf-8")
    still_bad = [r["coin"] for r in hist["coins"]
                 if not (r.get("ok") and r.get("n_rows", 0) > 0)]
    print(f"after retry: n_ok_with_data={hist['n_ok']} "
          f"still_bad={still_bad}", flush=True)

    # ---- CoinPaprika in-window cross-checks at 2026-08-20 ----
    CP = "https://api.coinpaprika.com/v1"
    cross = {}
    for cid, label in [("btc-bitcoin", "BTC"), ("eth-ethereum", "ETH"),
                       ("luna-terra", "LUNC"), ("ftt-ftx-token", "FTT"),
                       ("hot-holo", "HOT")]:
        try:
            r = S.get(f"{CP}/tickers/{cid}/historical",
                      params={"start": "2026-08-19", "end": "2026-08-21",
                              "interval": "1d"}, timeout=20)
            body = json.loads(r.content.decode("utf-8"))
            cross[label] = {"http_status": r.status_code,
                            "rows": body if isinstance(body, list) else body}
            print(f"CP cross {label}: {r.status_code} rows="
                  f"{len(body) if isinstance(body, list) else 'err'}"
                  f" mcap={body[-1]['market_cap'] if isinstance(body, list) and body else None}",
                  flush=True)
        except Exception as e:  # noqa: BLE001
            cross[label] = {"error": str(e)}
        time.sleep(0.5)
    (raw_dir / "coinpaprika_crosscheck_20260820.json").write_text(
        json.dumps({"schema_version": SCHEMA_VERSION,
                    "probe": "coinpaprika_crosscheck_20260820",
                    "retrieved_at": datetime.now(timezone.utc).isoformat(
                        timespec="seconds"),
                    "coins": cross}, indent=2), encoding="utf-8")

    # ---- CMC tag drift test ----
    tags_by_date = {}
    for dt in ["20240601", "20260820"]:
        snap = json.loads((raw_dir / f"cmc_snapshot_{dt}_top500.json")
                          .read_text(encoding="utf-8"))["data"]
        by_id = {r["id"]: r for r in snap}
        for cid in [1, 1027, 2, 1839]:
            tags_by_date.setdefault(cid, {})[dt] = by_id.get(cid, {}).get(
                "tags", [])
    (raw_dir / "cmc_tags_drift_test.json").write_text(
        json.dumps({"schema_version": SCHEMA_VERSION,
                    "probe": "cmc_tags_drift_test",
                    "note": "do snapshot responses carry current or "
                            "snapshot-time tags?",
                    "tags_by_date": tags_by_date}, indent=2),
        encoding="utf-8")
    for cid, d in tags_by_date.items():
        t1 = d.get("20240601", [])
        t2 = d.get("20260820", [])
        print(f"CMC id {cid}: tags 2024={len(t1)} 2026={len(t2)} "
              f"identical={t1 == t2}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
