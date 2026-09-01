"""Minimal B2 runtime worker process (B2-R6 / B4-CXR5R1).

Claims pending jobs from PostgreSQL through the authenticated worker
protocol, simulates execution, and commits results with lease-token
fencing. Part of the complete local runtime (scripts/start-local.sh):

    python -m oce_control.worker_loop --worker-id worker-1

B4-CXR5R1: there is NO --token argument and NO ambient worker-token env
surface — worker authentication material is read from the approved store
(read-only at runtime; initialized once by `oce_local configure`). A
password/token never appears in process argv.

--capabilities accepts a comma-separated list; "*" (default) claims any
job. Admission is idempotent with the same token.
"""
from __future__ import annotations
import argparse
import os
import sys
import time


def _reject_secret_flags(argv) -> None:
    """Reject secret-bearing CLI flags WITHOUT echoing their values.

    B4-CXR5R1: --token/--dsn/--secret/--password are NOT OCE worker options.
    argparse would echo the raw value in an "unrecognized arguments" message,
    so we intercept BEFORE parsing and print a redacted denial naming only
    the option. Worker authentication material comes from the approved
    store — never from the command line.
    """
    if not argv:
        return
    bad = {"--token", "--dsn", "--secret", "--password",
           "--worker-secret", "--worker-token"}
    import sys as _sys
    for tok in argv:
        opt = tok.split("=", 1)[0]
        if opt in bad:
            print(f"{opt} is not a valid OCE worker option — worker "
                  "authentication material is read from the approved store; "
                  "secret material is never accepted on the command line "
                  "(B4-CXR5R1)", file=_sys.stderr)
            raise SystemExit(2)


def main(argv=None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    # B4-CXR5R1: reject secret-bearing flags before argparse (which would
    # echo the raw value). Never print or accept a token/DSN on argv.
    _reject_secret_flags(argv)
    parser = argparse.ArgumentParser(description="OCE B2 runtime worker")
    parser.add_argument("--worker-id", default=os.environ.get("OCE_WORKER_ID", "worker-local01"))
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
    #
    # B4-CXR3R2: there is NO public --dsn argument. The database target is
    # always derived from the governed secret boundary (EffectiveConfig ->>
    # postgres.password_ref -> approved store -> ephemeral DSN); an arbitrary
    # DSN can never redirect this worker's connection elsewhere.
    #
    # B4-CXR4R3: the worker freezes ONE immutable ActivationContext (the full
    # gate: posture + secret resolution) and derives its DSN from the PINNED
    # context — environment mutation after activation cannot redirect it.
    #
    # B4-CXR5R1: the worker token comes from the approved store via
    # read_worker_token() — NEVER from argv or ambient environment. An
    # uninitialized store fails closed (never materializes on the fly).
    from .config_startup import create_activation_context
    from . import local_secrets as ls
    ctx = create_activation_context()
    token = ls.read_worker_token()  # read-only; raises when not initialized

    import psycopg2
    from .pg_store import PgJobStore
    from .pg_worker import PgWorkerProtocol

    conn = psycopg2.connect(ctx.runtime_dsn())
    conn.autocommit = False
    store = PgJobStore(conn)
    worker = PgWorkerProtocol(store, conn)
    caps = [c.strip() for c in args.capabilities.split(",") if c.strip()]
    worker.admit_worker(worker_id=args.worker_id, token=token, capabilities=caps)
    print(f"worker '{args.worker_id}' admitted (capabilities={caps})", flush=True)

    while True:
        pending = store.jobs_by_status("pending")[: args.max_per_cycle]
        for job in pending:
            try:
                claimed = worker.claim_work(args.worker_id, token, job.job_id,
                                            lease_ttl=args.lease_ttl)
                time.sleep(0.5)  # simulated execution
                done = worker.submit_result(args.worker_id, token, job.job_id,
                                            {"result": "ok", "worker": args.worker_id})
                print(f"completed {job.job_id} -> {done['status']}", flush=True)
            except Exception as exc:  # keep the loop alive on transient failures
                print(f"failed {job.job_id}: {exc}", flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
