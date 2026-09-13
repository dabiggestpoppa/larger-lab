"""qcae CLI (P2-C11; Book V 13.7).

Thin interface over ``QcaeApp``. No domain logic lives here: argparse
handlers parse arguments, call the application service, and print results.
Design: ``python -m qcae.interfaces.cli <command> ...`` with a ``--db``
pointing at the local metadata database.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from qcae.interfaces.cli.app import QcaeApp, build_local_runtime


def _app(db: str) -> QcaeApp:
    return QcaeApp(build_local_runtime(db))


def _print(payload) -> None:
    import dataclasses

    if dataclasses.is_dataclass(payload) and not isinstance(payload, type):
        payload = dataclasses.asdict(payload)
    if hasattr(payload, "to_dict"):
        payload = payload.to_dict()
    if isinstance(payload, dict) and "job" in payload:
        payload = {
            **payload,
            "job": payload["job"].to_dict(),
            "steps": [s.to_dict() for s in payload["steps"]],
        }
    if isinstance(payload, list):
        payload = [
            p.to_dict() if hasattr(p, "to_dict") else p for p in payload
        ]
    print(json.dumps(payload, indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qcae", description="QCAE standalone runtime CLI"
    )
    parser.add_argument("--db", required=True, help="path to the metadata database")
    sub = parser.add_subparsers(dest="command", required=True)

    job = sub.add_parser("job", help="job operations")
    job_sub = job.add_subparsers(dest="job_command", required=True)
    job_sub.add_parser("list", help="list jobs")

    status = job_sub.add_parser("status", help="inspect a job")
    status.add_argument("job_id")

    resume = job_sub.add_parser("resume", help="recover and resume a job")
    resume.add_argument("job_id")

    cancel = job_sub.add_parser("cancel", help="cancel a job")
    cancel.add_argument("job_id")
    cancel.add_argument("--reason", default="")

    run = job_sub.add_parser("run", help="run one eligible step of a job")
    run.add_argument("job_id")
    run.add_argument("--worker", default="id-runtime-local")

    approval = sub.add_parser("approval", help="approval operations")
    approval_sub = approval.add_subparsers(dest="approval_command", required=True)
    approval_sub.add_parser("list", help="list pending approvals")

    identity = sub.add_parser("identity", help="show runtime identity")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    app = _app(args.db)

    if args.command == "job":
        if args.job_command == "list":
            _print(app.job_list())
        elif args.job_command == "status":
            view = app.job_status(args.job_id)
            if view is None:
                print(f"unknown job {args.job_id}", file=sys.stderr)
                return 2
            _print(view)
        elif args.job_command == "resume":
            _print(app.job_resume(args.job_id))
        elif args.job_command == "cancel":
            job = app.job_cancel(args.job_id, reason=args.reason)
            _print(job)
        elif args.job_command == "run":
            result = app.job_run_step(args.job_id, args.worker)
            if result is None:
                print("no eligible step to run", file=sys.stderr)
                return 1
            _print(result)
        return 0

    if args.command == "approval":
        if args.approval_command == "list":
            _print(app.approval_list())
        return 0

    if args.command == "identity":
        _print(app.runtime_identity())
        return 0

    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
