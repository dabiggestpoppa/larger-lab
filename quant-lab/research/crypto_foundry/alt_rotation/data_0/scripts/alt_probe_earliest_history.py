#!/usr/bin/env python3
"""ALT-DATA-0.1 — probe older CMC snapshot dates.

Establishes the empirically verified earliest rank-history date. Each date
is a single cheap GET; raw body + provenance sidecar persisted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
SCHEMA_VERSION = "1.0.0"
URL = ("https://api.coinmarketcap.com/data-api/v3/cryptocurrency/"
       "listings/historical")

DATES = ["2022-06-01", "2021-06-01", "2020-06-01"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = Path(args.out) if args.out else (
        Path(__file__).resolve().parent.parent / "probes" / "raw")
    out.mkdir(exist_ok=True)
    for dt in DATES:
        name = f"cmc_snapshot_{dt.replace('-', '')}_top500"
        try:
            r = S.get(URL, params={"date": dt, "start": 1, "limit": 500,
                                   "convertId": 2781}, timeout=40)
            raw = r.content
            status = r.status_code
        except Exception as e:  # noqa: BLE001
            raw = b""
            status = None
            err = f"{type(e).__name__}: {e}"
        else:
            err = None
        meta = {"schema_version": SCHEMA_VERSION, "probe": name,
                "method": "GET", "url": r.url if status is not None else URL,
                "request_params": {"date": dt, "start": 1, "limit": 500,
                                   "convertId": 2781},
                "retrieved_at": datetime.now(timezone.utc).isoformat(
                    timespec="seconds"),
                "http_status": status, "ok": status == 200,
                "error": err,
                "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                "access_class": "WEB_ONLY",
                "notes": f"earliest-history probe for {dt}",
                "known_limitations": "internal web endpoint; TOS review "
                                     "required for long-term operation"}
        (out / f"{name}.json").write_bytes(raw)
        (out / f"{name}.meta.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8")
        n = 0
        if status == 200:
            try:
                n = len(json.loads(raw.decode("utf-8"))["data"])
            except Exception:  # noqa: BLE001
                pass
        print(f"[{status}] {name} rows={n} sha={meta['sha256'][:12]}"
              f" {err or ''}", flush=True)
        time.sleep(1.0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
