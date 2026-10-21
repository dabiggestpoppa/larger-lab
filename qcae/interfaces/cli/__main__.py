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

from qcae.core.errors import QcaeValidationError
from qcae.governance.standalone.typed_outcomes import StepNotReadyOutcome
from qcae.interfaces.cli.app import QcaeApp, build_local_runtime


def _app(db: str) -> QcaeApp:
    return QcaeApp(build_local_runtime(db))


class _Session:
    """One CLI invocation's runtime: committed on success, always closed.

    The CLI owns no domain logic, but it does own the process boundary: a
    decision that reports success must be durable, and the connection must
    not leak (WAL file locks on Windows)."""

    def __init__(self, db: str) -> None:
        self._rt = build_local_runtime(db)
        self.app = QcaeApp(self._rt)

    def close(self) -> None:
        try:
            self._rt.conn.commit()
        finally:
            self._rt.conn.close()


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


def _parse_step_specs(specs):
    """Parse 'id:type[:dep1,dep2]' step specs into canonical dicts."""
    parsed = []
    for spec in specs:
        parts = spec.split(":")
        if len(parts) < 2 or not parts[0] or not parts[1]:
            raise ValueError(
                f"invalid step spec {spec!r}; expected 'id:type[:dep1,dep2]'"
            )
        deps = parts[2].split(",") if len(parts) > 2 and parts[2] else []
        parsed.append({
            "step_id": parts[0], "step_type": parts[1], "dependencies": deps,
        })
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qcae", description="QCAE standalone runtime CLI"
    )
    parser.add_argument("--db", required=True, help="path to the metadata database")
    sub = parser.add_subparsers(dest="command", required=True)

    job = sub.add_parser("job", help="job operations")
    job_sub = job.add_subparsers(dest="job_command", required=True)
    job_sub.add_parser("list", help="list jobs")

    submit = job_sub.add_parser("submit", help="submit a bounded job (canonical)")
    submit.add_argument("--kind", required=True, help="job kind (e.g. discovery)")
    submit.add_argument("--subject", required=True, help="subject capability/candidate id")
    submit.add_argument("--key", required=True, help="submission idempotency key")
    submit.add_argument(
        "--step", action="append", required=True,
        help="step spec 'id:type[:dep1,dep2]' (repeatable; order = graph)",
    )
    submit.add_argument("--submitted-by", default="id-operator-local")
    submit.add_argument("--not-before", default="")

    status = job_sub.add_parser("status", help="inspect a job")
    status.add_argument("job_id")

    events = job_sub.add_parser("events", help="job event log (append-oriented)")
    events.add_argument("job_id")

    resume = job_sub.add_parser("resume", help="recover and resume a job")
    resume.add_argument("job_id")

    cancel = job_sub.add_parser("cancel", help="cancel a job")
    cancel.add_argument("job_id")
    cancel.add_argument("--reason", default="")

    recover = sub.add_parser("recover", help="recover expired leases / resume a job")
    recover.add_argument("job_id", nargs="?", default=None)

    run = job_sub.add_parser("run", help="run one eligible step of a job")
    run.add_argument("job_id")
    run.add_argument("--worker", default="id-worker-runtime")

    approval = sub.add_parser("approval", help="approval operations")
    approval_sub = approval.add_subparsers(dest="approval_command", required=True)
    approval_sub.add_parser("list", help="list pending approvals")

    decide = approval_sub.add_parser("decide", help="grant or deny an approval request")
    decide.add_argument("request_id")
    decide.add_argument("--decision", required=True, choices=("GRANTED", "DENIED"))
    decide.add_argument("--decided-by", required=True)
    decide.add_argument("--job-id", default="")
    decide.add_argument("--reason", default="")

    sub.add_parser("identity", help="show runtime identity")
    return parser


def _known_error_exit(exc: BaseException) -> Optional[int]:
    """Map expected QCAE operator errors to stable exit codes (P2-R3-C05).

    Exit codes: 2 = rejected/unknown (validation), 3 = worker unavailable,
    4 = budget exhausted. Anything unlisted is a programming error and
    must traceback, not be swallowed.
    """
    from qcae.core.errors import QcaeValidationError
    from qcae.orchestration.orchestrator.budgets import BudgetExhaustedError
    from qcae.orchestration.orchestrator.worker_availability import (
        WorkerUnavailableError,
    )

    if isinstance(exc, WorkerUnavailableError):
        return 3
    if isinstance(exc, BudgetExhaustedError):
        return 4
    if isinstance(exc, QcaeValidationError):
        return 2
    return None


def _print_operator_error(exc: BaseException) -> None:
    print(json.dumps(
        {"error": type(exc).__name__, "message": str(exc)}, indent=2,
    ), file=sys.stderr)


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # Runtime construction is inside the boundary on purpose: an unopenable
    # database is an operator error, and it must reach the same typed-exit
    # mapping as every other expected failure instead of surfacing as a
    # driver traceback.
    session: Optional[_Session] = None
    try:
        session = _Session(args.db)
        return _dispatch(session.app, args)
    except Exception as exc:
        code = _known_error_exit(exc)
        if code is None:
            raise  # unexpected: a programming error must traceback
        _print_operator_error(exc)
        return code
    finally:
        if session is not None:
            session.close()


def _dispatch(app: QcaeApp, args) -> int:

    if args.command == "job":  # noqa: SIM114 - readable argparse dispatch
        if args.job_command == "list":
            _print(app.job_list())
        elif args.job_command == "submit":
            try:
                steps = _parse_step_specs(args.step)
                from qcae.interfaces.submission import JobSubmission

                job = app.job_submit(JobSubmission(
                    job_kind=args.kind, subject_ref=args.subject,
                    idempotency_key=args.key, steps=steps,
                    submitted_by=args.submitted_by,
                    not_before=args.not_before,
                ), submitted_by=args.submitted_by)
                _print(job)
            except (QcaeValidationError, ValueError) as exc:
                # Expected rejection (malformed input / duplicate identity).
                # Programming errors propagate to main's typed mapping.
                print(f"submission rejected: {exc}", file=sys.stderr)
                return 2
        elif args.job_command == "status":
            view = app.job_status(args.job_id)
            if view is None:
                print(f"unknown job {args.job_id}", file=sys.stderr)
                return 2
            _print(view)
        elif args.job_command == "events":
            try:
                _print(app.job_events(args.job_id))
            except QcaeValidationError:
                print(f"unknown job {args.job_id}", file=sys.stderr)
                return 2
        elif args.job_command == "resume":
            _print(app.job_resume(args.job_id))
        elif args.job_command == "cancel":
            job = app.job_cancel(args.job_id, reason=args.reason)
            _print(job)
        elif args.job_command == "run":
            result = app.job_run_step(args.job_id, args.worker)
            # P2-R5: an unknown job carries the same standing `job status`
            # answers (exit 2) — never "no eligible step to run", which
            # would claim a nonexistent job exists but has nothing to do.
            if getattr(result, "reason", "") == "JOB_NOT_FOUND":
                print(result.message(), file=sys.stderr)
                return 2
            if isinstance(result, StepNotReadyOutcome):
                # Typed NOT_READY (canon 15.12 CONTRACT_NOT_READY standing):
                # structured output, stable exit code, nothing mutated.
                print(json.dumps({
                    "error": "NOT_READY",
                    "standing": result.standing,
                    "job_id": result.job_id,
                    "reason": result.reason,
                }, indent=2), file=sys.stderr)
                return 1
            if result is None:
                print("no eligible step to run", file=sys.stderr)
                return 1
            if getattr(result, "reason", "") == "WORKER_UNAVAILABLE":
                # Typed operator outcome (P2-R3-C02/C05): deterministic exit
                # code, structured output, no traceback, nothing leased.
                print(json.dumps({
                    "error": "WORKER_UNAVAILABLE",
                    "job_id": result.job_id,
                    "missing_step_types": list(result.missing_step_types),
                }, indent=2), file=sys.stderr)
                return 3
            _print(result)
        return 0

    if args.command == "recover":
        _print(app.recover(args.job_id))
        return 0

    if args.command == "approval":
        if args.approval_command == "list":
            _print(app.approval_list())
        elif args.approval_command == "decide":
            try:
                _print(app.approval_decide(
                    request_id=args.request_id, decision=args.decision,
                    decided_by=args.decided_by, job_id=args.job_id,
                    reason=args.reason,
                ))
            except QcaeValidationError as exc:
                print(f"approval decision rejected: {exc}", file=sys.stderr)
                return 2
        return 0

    if args.command == "identity":
        _print(app.runtime_identity())
        return 0

    # Unreachable with the current argparse set (subparsers are required and
    # every job/approval subcommand is handled above); kept as the boundary's
    # fail-closed tail so a future unhandled command cannot exit 0.
    raise SystemExit(2)


if __name__ == "__main__":
    sys.exit(main())
