#!/usr/bin/env python3
"""ALT-DATA-1 — daily CMC point-in-time top-500 snapshot collection.

Collects one dated snapshot per calendar day from
2020-06-01 .. 2026-08-23 (inclusive) using the empirically verified
internal web data endpoint:

  https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listings/historical

Design:
  - checkpointed / resumable (completed dates recorded in .checkpoint.json)
  - raw JSON body preserved on disk (gitignored; too large to commit)
  - per-date .meta.json provenance sidecar (committed) with SHA256 of body
  - adaptive rate limiting (backoff on 429/5xx), bounded retries
  - every row is the ranked top-500 as of end-of-UTC-day t (lastUpdated
    23:59Z semantics; snapshot date key = t)

Authority:
  PRIMARY_EMPIRICALLY_VERIFIED_WEB_ENDPOINT (NOT official documented API;
  TOS review required for long-term operation; stability risk INTERNAL_ENDPOINT)
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
START = date(2020, 6, 1)
END = date(2026, 8, 23)
EXPECTED_ROWS = 500
BASE_SLEEP = 0.45
MAX_RETRIES = 6


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--start", default=None)
    ap.add_argument("--end", default=None)
    ap.add_argument("--sleep", type=float, default=BASE_SLEEP)
    ap.add_argument("--limit-dates", type=int, default=0,
                    help="collect only the first N dates (testing)")
    args = ap.parse_args()

    out = Path(args.out) if args.out else (
        Path(__file__).resolve().parent.parent / "probes" / "raw")
    out.mkdir(parents=True, exist_ok=True)
    start = date.fromisoformat(args.start) if args.start else START
    end = date.fromisoformat(args.end) if args.end else END

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

    dates = list(daterange(start, end))
    if args.limit_dates:
        dates = dates[: args.limit_dates]
    todo = [d for d in dates if d.isoformat() not in completed]
    print(f"total={len(dates)} done={len(completed)} todo={len(todo)} "
          f"sleep={sleep_s:.2f}s", flush=True)

    t_start = time.time()
    n_ok = 0
    n_fail = 0
    n_429 = 0
    for d in todo:
        dt = d.isoformat()
        name = f"cmc_snapshot_{dt.replace('-', '')}_top500"
        body = None
        status = None
        err = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                r = S.get(URL, params={"date": dt, "start": 1, "limit": 500,
                                       "convertId": 2781}, timeout=45)
                body = r.content
                status = r.status_code
                if status == 200:
                    try:
                        n = len(json.loads(body.decode("utf-8"))["data"])
                    except Exception:  # noqa: BLE001
                        n = -1
                    if n == EXPECTED_ROWS:
                        err = None
                        break
                    err = f"unexpected row count {n}"
                    deterministic = True
                else:
                    deterministic = False
                    if status == 429:
                        n_429 += 1
                        sleep_s = min(sleep_s * 2, 8.0)
                        err = "429 rate limited"
                    else:
                        err = f"http {status}"
            except Exception as e:  # noqa: BLE001
                err = f"{type(e).__name__}: {e}"
                body = b""
                status = None
                deterministic = False
            # deterministic row-count mismatch: one re-confirm, then
            # proceed to reconstruction (no long backoff)
            if err is not None and deterministic and attempt >= 1:
                break
            if attempt < MAX_RETRIES:
                wait = (2 ** attempt) + random.uniform(0, 1)
                if status == 429:
                    wait = max(wait, sleep_s)
                print(f"  retry {dt} ({err}) in {wait:.1f}s "
                      f"[{attempt + 1}/{MAX_RETRIES}]", flush=True)
                time.sleep(wait)
        # attempt narrow-window reconstruction when the direct fetch
        # returns SUCCESS but fewer than EXPECTED_ROWS (CMC-side data
        # incidents return truncated listings, e.g. 2021-09-28)
        reconstructed = None
        if status == 200 and err is not None and body:
            try:
                best = json.loads(body.decode("utf-8"))["data"]
                by_rank = {int(x["cmcRank"]): x for x in best}
                for start in range(1, EXPECTED_ROWS + 1, 50):
                    rr = S.get(URL, params={"date": dt, "start": start,
                                            "limit": 50,
                                            "convertId": 2781}, timeout=45)
                    if rr.status_code == 200:
                        for x in rr.json().get("data", []):
                            by_rank[int(x["cmcRank"])] = x
                    time.sleep(0.35)
                rec = [by_rank[k] for k in sorted(by_rank)]
                if len(rec) > len(best):
                    reconstructed = json.dumps(
                        {"data": rec, "status": {"error_message": "SUCCESS"}},
                        separators=(",", ":")).encode("utf-8")
            except Exception:  # noqa: BLE001
                reconstructed = None
        if reconstructed is not None:
            body = reconstructed
            rec_rows = len(json.loads(body.decode("utf-8"))["data"])
        else:
            rec_rows = None

        # persist result (even failures keep a meta record)
        meta = {
            "schema_version": SCHEMA_VERSION,
            "probe": name,
            "method": "GET",
            "url": r.url if "r" in dir() and status is not None else URL,
            "request_params": {"date": dt, "start": 1, "limit": 500,
                               "convertId": 2781},
            "retrieved_at": datetime.now(timezone.utc).isoformat(
                timespec="seconds"),
            "historical_date": dt,
            "http_status": status,
            "ok": status == 200 and err is None,
            "error": err,
            "rows": rec_rows if rec_rows is not None else (
                len(json.loads(body.decode("utf-8"))["data"])
                if body and status == 200 else -1),
            "sha256": hashlib.sha256(body or b"").hexdigest(),
            "bytes": len(body or b""),
            "access_class": "WEB_ONLY",
            "source_authority": "PRIMARY_EMPIRICALLY_VERIFIED_WEB_ENDPOINT",
            "notes": "daily PIT top-500 snapshot; lastUpdated 23:59Z semantics",
            "known_limitations": ("internal web endpoint; TOS review required "
                                  "for long-term operation; NOT official "
                                  "documented API"),
        }
        if body is not None and status == 200:
            (out / f"{name}.json").write_bytes(body)
        (out / f"{name}.meta.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8")
        is_gap = (status == 200 and err is not None
                  and meta["rows"] > 0 and meta["rows"] < EXPECTED_ROWS)
        if is_gap:
            completed.add(dt)
            failed.pop(dt, None)
            gaps[dt] = {"rows": meta["rows"], "error": err,
                        "sha256": meta["sha256"]}
            n_ok += 1
            tag = f"GAP rows={meta['rows']} (CMC-side incomplete listing)"
        elif err is None and status == 200:
            completed.add(dt)
            failed.pop(dt, None)
            n_ok += 1
            tag = "ok"
        else:
            failed[dt] = {"error": err, "attempts": MAX_RETRIES + 1}
            n_fail += 1
            tag = f"FAIL {err}"
        if n_ok % 100 == 0 or tag.startswith("FAIL"):
            elapsed = time.time() - t_start
            print(f"[{n_ok}/{len(todo)}] {dt} {tag} elapsed={elapsed:.0f}s "
                  f"rate={(n_ok + n_fail) / max(elapsed, 1):.2f} req/s",
                  flush=True)
        ckpt = {"completed": sorted(completed), "failed": failed,
                "gaps": gaps, "sleep": sleep_s, "last_date": dt,
                "last_updated": datetime.now(timezone.utc).isoformat(
                    timespec="seconds")}
        ckpt_path.write_text(json.dumps(ckpt, indent=2), encoding="utf-8")
        time.sleep(sleep_s + random.uniform(0, 0.2))

    elapsed = time.time() - t_start
    print(f"DONE ok={n_ok} fail={n_fail} gaps={len(gaps)} 429s={n_429} "
          f"elapsed={elapsed:.0f}s ({elapsed / 60:.1f} min)", flush=True)
    if gaps:
        print("GAPS:", json.dumps(gaps, indent=2)[:2000], flush=True)
    if failed:
        print("FAILURES:", json.dumps(failed, indent=2)[:2000], flush=True)
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
