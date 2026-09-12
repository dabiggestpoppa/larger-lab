#!/usr/bin/env python3
"""LF (LOWER FIELD) — daily CMC point-in-time ranks 1-2000 snapshot collection.

For every canonical panel date (2020-06-01 .. 2026-08-23, 2,196 dates), fetch one
dated snapshot of ranks 1-2000 from the empirically verified internal web endpoint
used by the canonical ALT-DATA-1 collector:

  https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listings/historical
  ?date=YYYY-MM-DD&start=1&limit=2000&convertId=2781

Panel usage: ranks 501-2000 (lower-field universe). Rows 1-500 are kept for the
parity audit against the frozen canonical Top-500 panel and enter NO analysis.

Design mirrors ALT-DATA-1 collector: checkpointed/resumable, raw JSON bodies
persisted (gitignored), per-date .meta.json provenance sidecar (committed) with
SHA256, adaptive rate limiting, bounded retries. lastUpdated 23:59Z snapshot
semantics; snapshot date key = t.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})

SCHEMA_VERSION = "1.0.0"
URL = ("https://api.coinmarketcap.com/data-api/v3/cryptocurrency/"
       "listings/historical")
EXPECTED_ROWS = 2000
MIN_ACCEPT_ROWS = 1000  # persist partial snapshots above this; below = gap
BASE_SLEEP = 0.45
MAX_RETRIES = 2  # row-count mismatches are deterministic; only retry transport errors

# Canonical panel dates come from the frozen ALT-DATA-1.1 PIT universe.
CANONICAL_PANEL = (Path(__file__).resolve().parent.parent.parent.parent /
                   "alt_rotation" / "data_1_1" / "ALT_DATA_1_1_PIT_UNIVERSE.parquet")


def load_dates() -> list[str]:
    import pandas as pd
    pu = pd.read_parquet(CANONICAL_PANEL, columns=["historical_date"])
    dates = sorted(pu["historical_date"].dt.date.astype(str).unique().tolist())
    return dates


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--sleep", type=float, default=BASE_SLEEP)
    ap.add_argument("--limit-dates", type=int, default=0,
                    help="collect only the first N dates (testing)")
    ap.add_argument("--limit", type=int, default=2000)
    args = ap.parse_args()

    out = Path(args.out) if args.out else (
        Path(__file__).resolve().parent.parent / "DATA_TRUTH" / "raw")
    out.mkdir(parents=True, exist_ok=True)

    dates = load_dates()
    if args.limit_dates:
        dates = dates[: args.limit_dates]
    print(f"dates from canonical panel: {len(dates)} "
          f"({dates[0]} .. {dates[-1]})", flush=True)

    ckpt_path = out / ".checkpoint.json"
    ckpt = {"completed": [], "failed": {}, "gaps": {}, "sleep": args.sleep}
    if ckpt_path.exists():
        try:
            ckpt = json.loads(ckpt_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            ckpt = {"completed": [], "failed": {}, "gaps": {},
                    "sleep": args.sleep}
    completed = set(ckpt.get("completed", []))
    failed = dict(ckpt.get("failed", {}))
    gaps = dict(ckpt.get("gaps", {}))
    sleep_s = float(ckpt.get("sleep", args.sleep))

    todo = [d for d in dates if d not in completed]
    print(f"total={len(dates)} done={len(completed)} todo={len(todo)} "
          f"sleep={sleep_s:.2f}s", flush=True)

    t_start = time.time()
    n_ok = 0
    n_fail = 0
    n_429 = 0
    for d in todo:
        dt = d
        name = f"lf_snapshot_{dt.replace('-', '')}_r1_2000"
        body = None
        status = None
        err = None
        n_rows = -1
        for attempt in range(MAX_RETRIES + 1):
            try:
                r = S.get(URL, params={"date": dt, "start": 1,
                                       "limit": args.limit,
                                       "convertId": 2781}, timeout=60)
                body = r.content
                status = r.status_code
                if status == 200:
                    try:
                        n_rows = len(json.loads(body.decode("utf-8"))["data"])
                    except Exception:  # noqa: BLE001
                        n_rows = -1
                    if n_rows >= MIN_ACCEPT_ROWS:
                        err = None
                        break
                    err = f"row count {n_rows} < {MIN_ACCEPT_ROWS}"
                    # deterministic source gap: do not retry
                    break
                else:
                    if status == 429:
                        n_429 += 1
                    err = f"http {status}"
            except Exception as e:  # noqa: BLE001
                err = f"exc {e}"
            # backoff before retry (transport/5xx only)
            time.sleep(sleep_s * (2 ** attempt) * (0.5 + random.random()))
        if status == 200 and err is None and n_rows >= MIN_ACCEPT_ROWS:
            sha = hashlib.sha256(body).hexdigest()
            (out / f"{name}.json").write_bytes(body)
            meta = {
                "schema_version": SCHEMA_VERSION,
                "probe": name,
                "method": "GET",
                "url": (f"{URL}?date={dt}&start=1&limit={args.limit}"
                        f"&convertId=2781"),
                "request_params": {"date": dt, "start": 1,
                                   "limit": args.limit, "convertId": 2781},
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "historical_date": dt,
                "http_status": status,
                "ok": n_rows == args.limit,
                "complete": n_rows == args.limit,
                "rows": n_rows,
                "error": None if n_rows == args.limit else
                f"partial snapshot rows={n_rows}",
                "sha256": sha,
                "bytes": len(body),
                "access_class": "WEB_ONLY",
                "source_authority":
                    "PRIMARY_EMPIRICALLY_VERIFIED_WEB_ENDPOINT",
                "notes": ("daily PIT ranks 1-2000 snapshot; lastUpdated 23:59Z "
                          "semantics; rows 501-2000 = lower-field panel, "
                          "rows 1-500 = parity audit only; partial rows "
                          "persisted as PIT truth with complete flag"),
                "known_limitations": ("internal web endpoint; TOS review "
                                      "required for long-term operation; NOT "
                                      "official documented API"),
            }
            (out / f"{name}.meta.json").write_text(
                json.dumps(meta, indent=2), encoding="utf-8")
            completed.add(dt)
            n_ok += 1
            if n_rows < args.limit:
                gaps[dt] = {"rows": n_rows,
                            "note": "partial snapshot persisted"}
        else:
            failed[dt] = {"status": status, "error": err,
                          "attempts": MAX_RETRIES + 1}
            n_fail += 1
            print(f"FAIL {dt}: {err}", flush=True)
        # persist checkpoint with current state (fix: serialize the actual sets)
        ckpt["completed"] = sorted(completed)
        ckpt["failed"] = failed
        ckpt["gaps"] = gaps
        ckpt_path.write_text(json.dumps(ckpt, indent=2), encoding="utf-8")
        if (n_ok + n_fail) % 50 == 0:
            el = time.time() - t_start
            print(f"progress ok={n_ok} fail={n_fail} gaps={len(gaps)} "
                  f"elapsed={el:.0f}s", flush=True)
        time.sleep(sleep_s)

    ckpt_path.write_text(json.dumps(ckpt, indent=2), encoding="utf-8")
    print(f"DONE ok={n_ok} fail={n_fail} n429={n_429} "
          f"elapsed={time.time()-t_start:.0f}s", flush=True)
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
