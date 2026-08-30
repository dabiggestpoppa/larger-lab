"""Minimal B2 runtime worker process (B2-R6).

Claims pending jobs from PostgreSQL through the authenticated worker
protocol, simulates execution, and commits results with lease-token
fencing. Part of the complete local runtime (scripts/start-local.sh):

    python -m oce_control.worker_loop --worker-id worker-1 --token <token>

--capabilities accepts a comma-separated list; "*" (default) claims any
job. Admission is idempotent with the same token.
"""
from __future__ import annotations
import argparse
import os
import time

DEFAULT_DSN = "postgresql://oce_control_admin:test-secret-b2-pg-001@127.0.0.1:5433/oce_control"


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="OCE B2 runtime worker")
    parser.add_argument("--worker-id", default=os.environ.get("OCE_WORKER_ID", "worker-local01"))
    parser.add_argument("--token", default=os.environ.get("OCE_WORKER_TOKEN", "worker-local-token"))
    parser.add_argument("--dsn", default=os.environ.get("POSTGRES_DSN", DEFAULT_DSN))
    parser.add_argument("--interval", type=float, default=3.0)
    parser.add_argument("--lease-ttl", type=int, default=60)
    parser.add_argument("--capabilities", default="*")
    parser.add_argument("--max-per-cycle", type=int, default=5)
    args = parser.parse_args(argv)

    import psycopg2
    from .pg_store import PgJobStore
    from .pg_worker import PgWorkerProtocol

    conn = psycopg2.connect(args.dsn)
    conn.autocommit = False
    store = PgJobStore(conn)
    worker = PgWorkerProtocol(store, conn)
    caps = [c.strip() for c in args.capabilities.split(",") if c.strip()]
    worker.admit_worker(worker_id=args.worker_id, token=args.token, capabilities=caps)
    print(f"worker '{args.worker_id}' admitted (capabilities={caps})", flush=True)

    while True:
        pending = store.jobs_by_status("pending")[: args.max_per_cycle]
        for job in pending:
            try:
                claimed = worker.claim_work(args.worker_id, args.token, job.job_id,
                                            lease_ttl=args.lease_ttl)
                time.sleep(0.5)  # simulated execution
                done = worker.submit_result(args.worker_id, args.token, job.job_id,
                                            {"result": "ok", "worker": args.worker_id})
                print(f"completed {job.job_id} -> {done['status']}", flush=True)
            except Exception as exc:  # keep the loop alive on transient failures
                print(f"failed {job.job_id}: {exc}", flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
