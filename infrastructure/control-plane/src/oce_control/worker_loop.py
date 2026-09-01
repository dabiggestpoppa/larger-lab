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

def _default_dsn() -> str:
    """Fail-closed DSN: never a predictable default (B2-R7)."""
    from .config_startup import governed_runtime_dsn
    return governed_runtime_dsn()


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="OCE B2 runtime worker")
    parser.add_argument("--worker-id", default=os.environ.get("OCE_WORKER_ID", "worker-local01"))
    parser.add_argument("--token", default=os.environ.get("OCE_WORKER_TOKEN"))
    parser.add_argument("--dsn", default=_default_dsn())
    parser.add_argument("--interval", type=float, default=3.0)
    parser.add_argument("--lease-ttl", type=int, default=60)
    parser.add_argument("--capabilities", default="*")
    parser.add_argument("--max-per-cycle", type=int, default=5)
    args = parser.parse_args(argv)
    # B4-R3R2/R3: every real process activation entrypoint passes the startup
    # gate first, INCLUDING the secret-resolution proof. A worker cannot
    # bypass Book 4 by launching this module directly — no worker session
    # starts under a malformed / incomplete / forbidden effective config, and
    # no worker connects to PostgreSQL through an unbacked secret reference.
    from .config_startup import require_startable, require_secret_resolvable
    require_startable()
    require_secret_resolvable()
    if not args.token:
        raise SystemExit("worker requires --token or OCE_WORKER_TOKEN (no predictable default, B2-R7)")

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
